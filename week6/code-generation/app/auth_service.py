import logging
import time
import asyncio
from typing import Optional
from passlib.context import CryptContext
from pydantic import EmailStr, ValidationError
from app.models import UserInDB
from app.redis_client import redis_client

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
logger = logging.getLogger("auth_service")

# Rate limiting settings
MAX_ATTEMPTS = 5
WINDOW_SECONDS = 300  # 5 minutes

def get_rate_limit_key(email: str) -> str:
    return f"rl:{email}"

async def is_rate_limited(email: str) -> bool:
    key = get_rate_limit_key(email)
    try:
        attempts = await asyncio.to_thread(redis_client.get, key)
        if attempts and int(attempts) >= MAX_ATTEMPTS:
            return True
        return False
    except Exception as e:
        logger.error(f"Redis error during rate limit check: {e}")
        return False  # Fail open for auth, but log

async def increment_rate_limit(email: str):
    key = get_rate_limit_key(email)
    try:
        pipe = redis_client.pipeline()
        pipe.incr(key)
        pipe.expire(key, WINDOW_SECONDS)
        await asyncio.to_thread(pipe.execute)
    except Exception as e:
        logger.error(f"Redis error during rate limit increment: {e}")

async def reset_rate_limit(email: str):
    key = get_rate_limit_key(email)
    try:
        await asyncio.to_thread(redis_client.delete, key)
    except Exception as e:
        logger.error(f"Redis error during rate limit reset: {e}")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.warning(f"Password verification failed: {e}")
        return False

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

async def authenticate_user(
    email: str,
    password: str,
    get_user_by_email_async,  # async function to fetch user from DB
) -> dict:
    """
    Authenticate a user with email and password.
    Returns a dict with 'success', 'user', and 'error' keys.
    """
    start = time.perf_counter()
    try:
        # Input validation
        try:
            email = EmailStr.validate(email)
        except ValidationError:
            logger.info(f"Invalid email format: {email}")
            return {"success": False, "error": "Invalid email format."}

        # Rate limiting
        if await is_rate_limited(email):
            logger.warning(f"Rate limit exceeded for {email}")
            return {"success": False, "error": "Too many login attempts. Please try again later."}

        user: Optional[UserInDB] = await get_user_by_email_async(email)
        if not user:
            await increment_rate_limit(email)
            logger.info(f"Authentication failed: user not found ({email})")
            # Timing attack prevention: hash anyway
            verify_password(password, pwd_context.hash("dummy"))
            return {"success": False, "error": "Invalid credentials."}

        # Password check
        if not verify_password(password, user.hashed_password):
            await increment_rate_limit(email)
            logger.info(f"Authentication failed: bad password ({email})")
            return {"success": False, "error": "Invalid credentials."}

        # Success: reset rate limit
        await reset_rate_limit(email)
        logger.info(f"User authenticated: {email}")
        return {"success": True, "user": user}
    except Exception as e:
        logger.error(f"Unexpected error during authentication: {e}")
        return {"success": False, "error": "Internal server error."}
    finally:
        elapsed = (time.perf_counter() - start) * 1000
        logger.debug(f"authenticate_user for {email} took {elapsed:.2f}ms")