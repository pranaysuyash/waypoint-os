"""
Async SQLAlchemy database configuration for Waypoint OS.

Provides:
- Async engine creation
- Async session factory
- get_db() dependency for FastAPI
- Base declarative class for all models
"""

import asyncio
import os
from typing import AsyncGenerator

from sqlalchemy import event
from sqlalchemy.exc import DisconnectionError
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from spine_api.core.env import load_project_env

# A-18: no committed credential defaults in code. DATABASE_URL must come from
# the environment — shell, .env (gitignored), or CI. The runner
# (scripts/run_backend_tests.sh) and CI set it explicitly.
load_project_env()
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set. Provide it via the environment or .env "
        "(see .env.example). Local test runs: scripts/run_backend_tests.sh "
        "sets it for you."
    )

# Create async engine.
#
# NOTE (2026-09-04): ``pool_pre_ping`` must remain disabled for this asyncpg
# engine. SQLAlchemy performs pre-ping before dispatching checkout listeners;
# a pooled connection from a closed TestClient loop would therefore fail its
# ping before the loop-affinity guard below could invalidate it. Readiness
# probes provide explicit dependency health, while normal queries surface
# broken connections through the existing request error handling. Keeping a
# queue pool (rather than NullPool) preserves the measured endpoint latency.
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL logging during development
    future=True,
    pool_size=30,
    max_overflow=20,
    pool_pre_ping=False,
    pool_recycle=3600,
)


@event.listens_for(engine.sync_engine, "checkout")
def _reject_asyncpg_connection_from_other_loop(
    dbapi_connection: object,
    connection_record: object,
    connection_proxy: object,
) -> None:
    """Keep pooled asyncpg connections on the event loop that owns them.

    ``TestClient`` and other ASGI harnesses can create several short-lived
    event loops in one process.  asyncpg connections are loop-affine, so a
    pooled connection created by an earlier loop must not be handed to a new
    one.  Raising ``DisconnectionError`` at checkout tells SQLAlchemy to
    invalidate that one record and retry with a fresh connection.  Drivers
    without asyncpg's private ``_loop`` attribute are intentionally ignored.
    """
    try:
        running_loop = asyncio.get_running_loop()
    except RuntimeError:
        return

    driver_connection = getattr(dbapi_connection, "driver_connection", None)
    owner_loop = getattr(driver_connection, "_loop", None)
    if owner_loop is None or owner_loop is running_loop:
        return

    # Do not close the driver object directly here: asyncpg.close() is itself
    # loop-affine.  SQLAlchemy owns invalidation/reconnect after this signal.
    del connection_record, connection_proxy
    raise DisconnectionError(
        "pooled asyncpg connection belongs to a different event loop; "
        "discarding it and retrying checkout"
    )

# Async session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


# Force clear any stale tables on module reload (uvicorn --reload safety)
Base.metadata.clear()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields an async database session.
    Usage:
        @app.get("/items")
        async def read_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()
