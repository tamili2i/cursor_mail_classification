import os
import logging
import time
from typing import Optional, Any, Dict
from uuid import uuid4, UUID
from datetime import datetime, timedelta

from fastapi import (
    FastAPI, Depends, HTTPException, status, Request, Response, Header, BackgroundTasks
)
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, constr, ValidationError
from sqlalchemy.ext.asyncio import (
    AsyncSession, create_async_engine, async_sessionmaker
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy import (
    Column, String, DateTime, Boolean, ForeignKey, func, select, update
)
from passlib.context import CryptContext
import jwt
import aioredis
from pydantic import validator
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send
from shared.models import ErrorResponse, Token, UserBase
from shared.utils import create_access_token, create_refresh_token, decode_token, error_response

# --- Configuration Management ---

class Settings(BaseModel):
    PROJECT_NAME: str = "User Service"
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "supersecretkey")
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    POSTGRES_DSN: str = os.getenv("POSTGRES_DSN", "postgresql+asyncpg://user:password@localhost:5432/userdb")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    RATE_LIMIT_ATTEMPTS: int = 5
    RATE_LIMIT_WINDOW: int = 60  # seconds
    ACCOUNT_LOCKOUT_ATTEMPTS: int = 10
    ACCOUNT_LOCKOUT_DURATION: int = 900  # seconds (15 min)
    CORS_ALLOW_ORIGINS: str = os.getenv("CORS_ALLOW_ORIGINS", "http://localhost,http://127.0.0.1")

settings = Settings()

# --- Logging Setup ---

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s"
)
logger = logging.getLogger("user_service")

# --- Database Setup ---

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    deleted = Column(Boolean, default=False)

# --- SQLAlchemy Async Engine & Session ---

engine = create_async_engine(settings.POSTGRES_DSN, echo=False, future=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session

# --- Redis Setup ---

redis = None

async def get_redis():
    global redis
    if not redis:
        redis = await aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    return redis

# --- Password Hashing ---

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# --- JWT Token Utilities ---

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.JWT_REFRESH_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

# --- Pydantic Schemas ---

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: constr(min_length=8, max_length=128)

    @validator('password')
    def password_complexity(cls, v):
        import re
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter.')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter.')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit.')
        if not re.search(r'[^A-Za-z0-9]', v):
            raise ValueError('Password must contain at least one special character.')
        return v

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    password: Optional[constr(min_length=8, max_length=128)] = None

    @validator('password')
    def password_complexity(cls, v):
        if v is None:
            return v
        import re
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter.')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter.')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit.')
        if not re.search(r'[^A-Za-z0-9]', v):
            raise ValueError('Password must contain at least one special character.')
        return v

class UserOut(UserBase):
    id: str
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenRefreshRequest(BaseModel):
    refresh_token: str

class ErrorResponse(BaseModel):
    code: str
    message: str
    details: Optional[Any] = None

# --- Rate Limiting Utilities ---

async def is_rate_limited(redis, key: str) -> bool:
    attempts = await redis.get(key)
    if attempts and int(attempts) >= settings.RATE_LIMIT_ATTEMPTS:
        return True
    return False

async def increment_rate_limit(redis, key: str):
    tx = redis.pipeline()
    tx.incr(key)
    tx.expire(key, settings.RATE_LIMIT_WINDOW)
    await tx.execute()

async def reset_rate_limit(redis, key: str):
    await redis.delete(key)

# --- Account Lockout Utilities ---
async def is_account_locked(redis, user_email: str) -> bool:
    lock_key = f"lockout:{user_email}"
    locked = await redis.get(lock_key)
    return bool(locked)

async def lock_account(redis, user_email: str):
    lock_key = f"lockout:{user_email}"
    await redis.set(lock_key, "1", ex=settings.ACCOUNT_LOCKOUT_DURATION)

async def unlock_account(redis, user_email: str):
    lock_key = f"lockout:{user_email}"
    await redis.delete(lock_key)

# --- Enhanced Rate Limiting Decorator ---
def get_client_ip(request: Request) -> str:
    x_forwarded_for = request.headers.get("x-forwarded-for")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"

async def check_rate_limit_and_lockout(redis, email: str, ip: str, endpoint: str, logger, request: Request):
    # Per-email and per-IP keys
    email_key = f"rl:{endpoint}:email:{email}"
    ip_key = f"rl:{endpoint}:ip:{ip}"
    # Check account lockout
    if await is_account_locked(redis, email):
        logger.warning(f"Account locked: {email} from IP {ip} on {endpoint}")
        raise HTTPException(status_code=423, detail="Account is temporarily locked due to too many failed attempts.")
    # Check rate limits
    if await is_rate_limited(redis, email_key) or await is_rate_limited(redis, ip_key):
        logger.warning(f"Rate limit exceeded: {email} from IP {ip} on {endpoint}")
        raise HTTPException(status_code=429, detail="Too many attempts. Please try again later.")
    return email_key, ip_key

async def increment_rate_limit_and_lockout(redis, email: str, ip: str, endpoint: str, logger):
    email_key = f"rl:{endpoint}:email:{email}"
    ip_key = f"rl:{endpoint}:ip:{ip}"
    await increment_rate_limit(redis, email_key)
    await increment_rate_limit(redis, ip_key)
    # If failed login, increment lockout counter
    if endpoint == "login":
        fail_key = f"fail:{email}"
        fails = await redis.incr(fail_key)
        await redis.expire(fail_key, settings.ACCOUNT_LOCKOUT_DURATION)
        if int(fails) >= settings.ACCOUNT_LOCKOUT_ATTEMPTS:
            await lock_account(redis, email)
            logger.warning(f"Account locked due to failed logins: {email}")

async def reset_rate_limit_and_lockout(redis, email: str, ip: str, endpoint: str):
    email_key = f"rl:{endpoint}:email:{email}"
    ip_key = f"rl:{endpoint}:ip:{ip}"
    await reset_rate_limit(redis, email_key)
    await reset_rate_limit(redis, ip_key)
    if endpoint == "login":
        fail_key = f"fail:{email}"
        await redis.delete(fail_key)
        await unlock_account(redis, email)

# --- Authentication Dependencies ---

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise credentials_exception
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except Exception:
        raise credentials_exception
    user = await db.get(User, user_id)
    if not user or user.deleted or not user.is_active:
        raise credentials_exception
    return user

# --- FastAPI App Setup ---

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="User Service for Collaborative Document System",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# --- Security Headers Middleware ---
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'self';"
        )
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        return response

# --- CORS Middleware ---
allowed_origins = [o.strip() for o in settings.CORS_ALLOW_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Exception Handlers ---

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning(f"HTTPException: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": "HTTP_ERROR",
                "message": exc.detail,
                "details": None
            }
        }
    )

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled Exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred.",
                "details": str(exc)
            }
        }
    )

@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    logger.warning(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Input validation failed.",
                "details": exc.errors()
            }
        }
    )

# --- Health Check Endpoint ---

@app.get("/health", tags=["Health"])
async def health_check():
    return {"success": True, "data": {"status": "ok"}}

# --- User Registration ---

@app.post("/auth/register", response_model=UserOut, tags=["Auth"])
async def register_user(user_in: UserCreate, db: AsyncSession = Depends(get_db), redis=Depends(get_redis), request: Request = None):
    ip = get_client_ip(request)
    email = user_in.email
    await check_rate_limit_and_lockout(redis, email, ip, "register", logger, request)
    stmt = select(User).where(User.email == user_in.email, User.deleted == False)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if user:
        await increment_rate_limit_and_lockout(redis, email, ip, "register", logger)
        audit_log(
            event="register_email_exists",
            user=email,
            ip=ip,
            user_agent=get_user_agent(request),
            details={}
        )
        raise HTTPException(status_code=400, detail="Email already registered.")
    hashed_password = get_password_hash(user_in.password)
    new_user = User(
        email=user_in.email,
        hashed_password=hashed_password,
        full_name=user_in.full_name,
        is_active=True,
        is_superuser=False
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    await reset_rate_limit_and_lockout(redis, email, ip, "register")
    audit_log(
        event="register_success",
        user=new_user.email,
        ip=ip,
        user_agent=get_user_agent(request),
        details={}
    )
    logger.info(f"User registered: {new_user.email} from IP {ip}")
    return new_user

# --- User Login ---

@app.post("/auth/login", response_model=Token, tags=["Auth"])
async def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
    request: Request = None
):
    email = form_data.username
    password = form_data.password
    ip = get_client_ip(request)
    await check_rate_limit_and_lockout(redis, email, ip, "login", logger, request)
    stmt = select(User).where(User.email == email, User.deleted == False)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user or not verify_password(password, user.hashed_password):
        await increment_rate_limit_and_lockout(redis, email, ip, "login", logger)
        audit_log(
            event="login_failed",
            user=email,
            ip=ip,
            user_agent=get_user_agent(request),
            details={}
        )
        logger.info(f"Failed login for {email} from IP {ip}")
        raise HTTPException(status_code=401, detail="Invalid credentials.")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Inactive user.")
    await reset_rate_limit_and_lockout(redis, email, ip, "login")
    access_token = create_access_token({"sub": user.id})
    refresh_token = create_refresh_token({"sub": user.id})
    # Store refresh token in Redis for session management
    await redis.set(f"refresh:{user.id}:{refresh_token}", "1", ex=settings.JWT_REFRESH_TOKEN_EXPIRE_MINUTES * 60)
    audit_log(
        event="login_success",
        user=user.email,
        ip=ip,
        user_agent=get_user_agent(request),
        details={}
    )
    logger.info(f"User logged in: {user.email} from IP {ip}")
    return Token(access_token=access_token, refresh_token=refresh_token)

# --- Get Current User Profile ---

@app.get("/auth/me", response_model=UserOut, tags=["Auth"])
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

# --- Update User Profile ---

@app.put("/auth/profile", response_model=UserOut, tags=["Auth"])
async def update_profile(
    user_update: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    updated = False
    if user_update.full_name is not None:
        current_user.full_name = user_update.full_name
        updated = True
    if user_update.password is not None:
        current_user.hashed_password = get_password_hash(user_update.password)
        updated = True
    if updated:
        current_user.updated_at = datetime.utcnow()
        db.add(current_user)
        await db.commit()
        await db.refresh(current_user)
        audit_log(
            event="password_change",
            user=current_user.email,
            ip=None,
            user_agent=None,
            details={}
        )
        logger.info(f"User profile updated: {current_user.email}")
    return current_user

# --- Refresh JWT Token ---

@app.post("/auth/refresh", response_model=Token, tags=["Auth"])
async def refresh_token(
    req: TokenRefreshRequest,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
    request: Request = None
):
    ip = get_client_ip(request)
    try:
        payload = decode_token(req.refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid refresh token.")
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid refresh token.")
        # Rate limit by user_id and IP
        await check_rate_limit_and_lockout(redis, user_id, ip, "refresh", logger, request)
        exists = await redis.get(f"refresh:{user_id}:{req.refresh_token}")
        if not exists:
            await increment_rate_limit_and_lockout(redis, user_id, ip, "refresh", logger)
            raise HTTPException(status_code=401, detail="Refresh token expired or revoked.")
        user = await db.get(User, user_id)
        if not user or user.deleted or not user.is_active:
            raise HTTPException(status_code=401, detail="User not found or inactive.")
        access_token = create_access_token({"sub": user.id})
        refresh_token = create_refresh_token({"sub": user.id})
        await redis.set(f"refresh:{user.id}:{refresh_token}", "1", ex=settings.JWT_REFRESH_TOKEN_EXPIRE_MINUTES * 60)
        await reset_rate_limit_and_lockout(redis, user_id, ip, "refresh")
        audit_log(
            event="token_refresh",
            user=user.email,
            ip=ip,
            user_agent=get_user_agent(request),
            details={}
        )
        logger.info(f"Refreshed token for user: {user.email} from IP {ip}")
        return Token(access_token=access_token, refresh_token=refresh_token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired.")
    except Exception as e:
        logger.error(f"Refresh token error: {e}")
        raise HTTPException(status_code=401, detail="Invalid refresh token.")

# --- User Logout ---

@app.post("/auth/logout", tags=["Auth"])
async def logout_user(
    req: TokenRefreshRequest,
    current_user: User = Depends(get_current_user),
    redis=Depends(get_redis),
    request: Request = None
):
    ip = get_client_ip(request)
    try:
        payload = decode_token(req.refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid refresh token.")
        user_id = payload.get("sub")
        if user_id != current_user.id:
            raise HTTPException(status_code=401, detail="Token does not belong to current user.")
        await check_rate_limit_and_lockout(redis, user_id, ip, "logout", logger, request)
        # Remove refresh token from Redis
        await redis.delete(f"refresh:{user_id}:{req.refresh_token}")
        await reset_rate_limit_and_lockout(redis, user_id, ip, "logout")
        audit_log(
            event="logout_success",
            user=current_user.email,
            ip=ip,
            user_agent=get_user_agent(request),
            details={}
        )
        logger.info(f"User logged out: {current_user.email} from IP {ip}")
        return {"success": True, "data": {"message": "Logged out successfully."}}
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(status_code=401, detail="Invalid refresh token.")

# --- Sample Data for Testing (Startup Event) ---

@app.on_event("startup")
async def startup_event():
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Connect Redis
    await get_redis()
    # Insert sample user if not exists
    async with AsyncSessionLocal() as db:
        stmt = select(User).where(User.email == "test@example.com")
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            sample_user = User(
                email="test@example.com",
                hashed_password=get_password_hash("TestPassword123"),
                full_name="Test User",
                is_active=True,
                is_superuser=True
            )
            db.add(sample_user)
            await db.commit()
            logger.info("Sample user created: test@example.com")

# --- OpenAPI Security Schemes ---

from fastapi.openapi.utils import get_openapi

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=settings.PROJECT_NAME,
        version="1.0.0",
        description="User Service for Collaborative Document System",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }
    for path in openapi_schema["paths"].values():
        for op in path.values():
            if "security" not in op:
                op["security"] = [{"BearerAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

def get_user_agent(request: Request) -> str:
    return request.headers.get("user-agent", "unknown")

def audit_log(event: str, user: str = None, ip: str = None, user_agent: str = None, details: dict = None):
    logger.info({
        "event": event,
        "user": user,
        "ip": ip,
        "user_agent": user_agent,
        "timestamp": datetime.utcnow().isoformat(),
        "details": details or {}
    })
