"""
Async SQLAlchemy engine and session factory for SideloadOS.

Default DATABASE_URL uses localhost:5434 for host-machine dev.
Inside Docker, the env var overrides to postgres:5432 (container networking).
"""

import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://sideload:sideload_password@localhost:5434/sideload_db",
)

engine = create_async_engine(DATABASE_URL, echo=False, future=True)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency — yields an async DB session, auto-closes on exit."""
    async with AsyncSessionLocal() as session:
        yield session
