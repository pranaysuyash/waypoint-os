"""
PostgreSQL Row Level Security (RLS) integration for Waypoint OS.

Defense-in-depth tenant isolation: even if application code forgets a WHERE clause,
the database enforces that queries only see rows for the current agency.

Architecture:
  1. A ContextVar holds the current agency_id for the duration of each request.
  2. set_rls_agency() is called by get_current_membership() after the JWT is validated.
  3. get_rls_db() is a FastAPI dependency that reads the ContextVar and issues
     transaction-local app.current_agency_id before yielding the session to the route handler.
  4. Routes that touch tenant-scoped tables use `db: AsyncSession = get_rls_db()`
     instead of `Depends(get_db)`.

Why transaction-local config (not plain SET):
  - set_config(..., true) is transaction-scoped, equivalent in scope to SET LOCAL.
    It expires when the transaction ends.
  - Connections are pooled and reused across requests. A plain SET would bleed
    the previous request's agency_id into the next request on the same connection.
  - A bound parameter keeps the agency_id out of interpolated SQL.

Why ContextVar (not a thread-local):
  - asyncio tasks share a thread. Thread-locals would bleed between concurrent
    requests on the same event-loop thread.
  - ContextVar is per-asyncio-task, which maps 1:1 with FastAPI request handling.

Migration:
  alembic/versions/add_rls_tenant_isolation.py enables RLS on trips, memberships,
  workspace_codes, and creates SELECT/ALL policies keyed on app.current_agency_id.
"""

from contextvars import ContextVar
from typing import AsyncGenerator, Optional

from fastapi import Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from spine_api.core.database import get_db

# Per-request agency_id — set once by get_current_membership, read by get_rls_db.
_current_agency_id: ContextVar[Optional[str]] = ContextVar("_current_agency_id", default=None)


def set_rls_agency(agency_id: str) -> None:
    """Set the current request's agency_id for RLS enforcement."""
    _current_agency_id.set(agency_id)


def get_rls_agency() -> Optional[str]:
    """Read the current request's agency_id (None if not yet set)."""
    return _current_agency_id.get()


async def apply_rls(session: AsyncSession, agency_id: str) -> None:
    """
    Issue transaction-local app.current_agency_id within the current transaction.

    Must be called after a transaction has begun (i.e., after any DML or
    explicit BEGIN). SQLAlchemy's lazy-begin means this executes inside the
    same implicit transaction that the subsequent query will use.

    Uses PostgreSQL set_config(..., true) instead of a literal SET LOCAL string
    so the agency_id can remain a bound parameter.
    """
    await session.execute(
        text("SELECT set_config('app.current_agency_id', :agency_id, true)"),
        {"agency_id": agency_id},
    )


async def get_rls_db(
    db: AsyncSession = Depends(get_db),
) -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency: yields a DB session with RLS applied.

    Uses the agency_id stored in the ContextVar (set by get_current_membership).
    Falls through to a plain session if no agency_id is set (e.g. in test fixtures
    that bypass auth, or public endpoints).

    Usage in routes:
        @router.get("/items")
        async def list_items(db: AsyncSession = Depends(get_rls_db)):
            ...
    """
    agency_id = _current_agency_id.get()
    if agency_id:
        await apply_rls(db, agency_id)
    yield db
