from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from .models import UserCreate, UserRead
from .services import create_user, get_user, authenticate_user
from .core.security import create_access_token
from .config import ACCESS_TOKEN_EXPIRE_MINUTES, SECRET_KEY, ALGORITHM
from datetime import datetime, timedelta
from jose import jwt, JWTError
from .redis_client import redis_client
import logging

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")

logger = logging.getLogger(__name__)

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email = payload.get("sub")
        if user_email is None:
            logger.warning("JWT payload missing 'sub' claim.")
            raise HTTPException(status_code=401, detail="Could not validate credentials")
        try:
            session_token = redis_client.get(f"session:{user_email}")
        except Exception as e:
            logger.error(f"Redis error during session lookup: {e}")
            raise HTTPException(status_code=500, detail="Session store error")
        if session_token != token:
            logger.info(f"Session token mismatch for user {user_email}.")
            raise HTTPException(status_code=401, detail="Session expired or invalid")
        return user_email
    except JWTError as e:
        logger.warning(f"JWT decode error: {e}")
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    except Exception as e:
        logger.error(f"Unexpected error in get_current_user: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/", response_model=UserRead)
async def register_user(user: UserCreate):
    try:
        return create_user(user)
    except Exception as e:
        logger.error(f"Error registering user: {e}")
        raise HTTPException(status_code=500, detail="User registration failed")

@router.get("/{user_id}", response_model=UserRead)
async def read_user(user_id: int):
    try:
        user = get_user(user_id)
        if not user:
            logger.info(f"User not found: {user_id}")
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reading user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch user")

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        user = authenticate_user(form_data.username, form_data.password)
        if not user:
            logger.info(f"Failed login attempt for {form_data.username}")
            raise HTTPException(status_code=400, detail="Incorrect username or password")
        access_token = create_access_token(
            user.email, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        try:
            redis_client.set(f"session:{user.email}", access_token, ex=ACCESS_TOKEN_EXPIRE_MINUTES*60)
        except Exception as e:
            logger.error(f"Redis error during session set: {e}")
            raise HTTPException(status_code=500, detail="Session store error")
        return {"access_token": access_token, "token_type": "bearer"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during login: {e}")
        raise HTTPException(status_code=500, detail="Login failed")

@router.post("/logout")
async def logout(current_user: str = Depends(get_current_user)):
    try:
        redis_client.delete(f"session:{current_user}")
        return {"msg": "Logged out"}
    except Exception as e:
        logger.error(f"Error during logout for {current_user}: {e}")
        raise HTTPException(status_code=500, detail="Logout failed")