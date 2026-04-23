"""
Async Alembic environment configuration.

Supports autogenerate with SQLAlchemy 2.0 async models.
"""

import asyncio
import sys
import importlib
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Hardcode project root - adjust if project structure changes
PROJECT_ROOT = Path("/Users/pranay/Projects/travel_agency_agent")
SPINE_API_PATH = PROJECT_ROOT / "spine-api"
sys.path.insert(0, str(SPINE_API_PATH))

# Import Base directly from the tenant module
tenant_path = SPINE_API_PATH / "models" / "tenant.py"
spec = importlib.util.spec_from_file_location("tenant_module", tenant_path)
tenant_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tenant_mod)
Base = tenant_mod.Base

# This is the Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for autogenerate
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode with async engine."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
