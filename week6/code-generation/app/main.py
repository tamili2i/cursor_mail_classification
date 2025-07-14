import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s %(message)s')

from fastapi import FastAPI
from .routes import router

app = FastAPI(title="User Management Service")

app.include_router(router, prefix="/users")