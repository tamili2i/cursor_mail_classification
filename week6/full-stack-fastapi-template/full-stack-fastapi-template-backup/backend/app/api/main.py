from fastapi import APIRouter

from app.api.routes import items, login, private, users, utils
from app.api.routes import teams
from app.api.routes import projects
from app.api.routes import dashboard
from app.api.routes import realtime
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(login.router)
api_router.include_router(users.router)
api_router.include_router(utils.router)
api_router.include_router(items.router)
api_router.include_router(teams.router)
api_router.include_router(projects.router)
api_router.include_router(dashboard.router)
api_router.include_router(realtime.router)


if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)
