from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine
from logging.config import fileConfig
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from app.models import Base

config = context.config
fileConfig(config.config_file_name)
target_metadata = Base.metadata

DATABASE_URL = os.getenv("POSTGRES_DSN", "postgresql+asyncpg://user:password@db:5432/userdb")

def run_migrations_online():
    connectable = create_async_engine(DATABASE_URL, future=True)
    async def do_run_migrations(connection):
        context.configure(connection=connection, target_metadata=target_metadata, render_as_batch=True)
        async with context.begin_transaction():
            await context.run_migrations()
    import asyncio
    asyncio.run(do_run_migrations(connectable))

run_migrations_online() 