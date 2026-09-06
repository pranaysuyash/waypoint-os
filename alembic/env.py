"""
Async Alembic environment configuration.

Supports autogenerate with SQLAlchemy 2.0 async models.
"""

import asyncio
import os
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Resolve project root from this file's location (alembic/ lives at repo root).
# Must stay environment-agnostic — a hardcoded absolute path breaks CI and containers.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# This is the Alembic Config object
config = context.config

# Never use alembic.ini for credentials. Every invocation must name its target
# database explicitly, matching the runtime application's DATABASE_URL.
database_url = os.environ.get("DATABASE_URL", "").strip()
if not database_url:
    raise RuntimeError(
        "DATABASE_URL is required for Alembic. Refusing to migrate an implicit "
        "or local default database."
    )
# ConfigParser treats '%' as interpolation syntax; preserve URL-encoded values.
config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))

from spine_api.models import Base  # noqa: E402

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for autogenerate
target_metadata = Base.metadata


def include_object(object_, name, type_, reflected, compare_to):
    """Keep Alembic diffs honest while excluding one raw-SQL-owned table.

    ``agent_requeue_jobs`` is intentionally created and maintained by the
    raw-SQL ``RequeueJobStore`` plus its dedicated migration.  It is not part
    of the ORM metadata, so autogenerate must exclude only this known table;
    broad unknown-table suppression would hide genuine schema drift.
    """
    if type_ == "table" and name == "agent_requeue_jobs" and reflected:
        return False
    return True


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        include_object=include_object,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        include_object=include_object,
    )

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
