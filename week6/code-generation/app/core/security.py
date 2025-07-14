from datetime import datetime, timedelta
from typing import Optional
from jose import jwt
from passlib.context import CryptContext

from ..config import SECRET_KEY, ALGORITHM
from ..models import UserCreate, UserRead, UserInDB

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=30))
    to_encode = {"exp": expire, "sub": str(subject)}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def authenticate_user(email: str, password: str):
    # Replace this with your actual user lookup logic
    for user in fake_db.values():
        if user.email == email and verify_password(password, user.hashed_password):
            return user
    return None