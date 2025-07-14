import time
from fastapi import FastAPI, Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from collections import defaultdict
from app.api.main import api_router
from app.core.config import settings
from app.api.routes import users, projects, dashboard, login
import logging

# Simple in-memory rate limiter (for demo; use Redis in prod)
RATE_LIMIT = 100  # requests
RATE_PERIOD = 60  # seconds
user_requests = defaultdict(list)

logger = logging.getLogger("gateway")
logging.basicConfig(level=logging.INFO)

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Only check for protected routes
        if request.url.path.startswith("/api/v1/projects") or request.url.path.startswith("/api/v1/dashboard"):
            auth = request.headers.get("Authorization")
            if not auth or not auth.startswith("Bearer "):
                return JSONResponse({"detail": "Not authenticated"}, status_code=status.HTTP_401_UNAUTHORIZED)
            # Optionally, validate JWT here
        return await call_next(request)

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        user = request.headers.get("Authorization", "public")
        now = time.time()
        reqs = user_requests[user]
        # Remove old requests
        user_requests[user] = [t for t in reqs if now - t < RATE_PERIOD]
        if len(user_requests[user]) >= RATE_LIMIT:
            return JSONResponse({"detail": "Rate limit exceeded"}, status_code=429)
        user_requests[user].append(now)
        return await call_next(request)

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        logger.info(f"Request: {request.method} {request.url.path}")
        response = await call_next(request)
        logger.info(f"Response: {response.status_code} {request.url.path}")
        return response

app = FastAPI(title="API Gateway", openapi_url=f"{settings.API_V1_STR}/openapi.json")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.all_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(AuthMiddleware)

# Route /api/v1/auth/* to user service (login, users)
app.include_router(login.router, prefix=f"{settings.API_V1_STR}/auth")
app.include_router(users.router, prefix=f"{settings.API_V1_STR}/auth")
# Route /api/v1/projects/* to project service
app.include_router(projects.router, prefix=f"{settings.API_V1_STR}/projects")
# Route /api/v1/dashboard/* to dashboard service
app.include_router(dashboard.router, prefix=f"{settings.API_V1_STR}/dashboard") 