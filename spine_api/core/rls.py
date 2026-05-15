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
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import AsyncGenerator, Optional, Sequence

from fastapi import Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession

from spine_api.core.database import get_db

# Per-request agency_id — set once by get_current_membership, read by get_rls_db.
_current_agency_id: ContextVar[Optional[str]] = ContextVar("_current_agency_id", default=None)

RLS_TENANT_TABLES: tuple[str, ...] = (
    # Phase 5A: original RLS tables
    "trips",
    "memberships",
    "workspace_codes",
    "booking_collection_tokens",
    # Phase 5A migration (had RLS but was missing from registry)
    "trip_routing_states",
    # Phase 4-5 tables (previously unprotected)
    "booking_documents",
    "document_extractions",
    "document_extraction_attempts",
    "booking_tasks",
    "booking_confirmations",
    "execution_events",
)

RLS_EXCLUDED_AGENCY_TABLES: dict[str, str] = {
    "audit_logs": "admin/audit surface; query-scoped; separate hardening task",
    "emotional_state_logs": "frontier/experimental feature; not in Phase 5E scope",
    "ghost_workflows": "frontier/experimental feature; not in Phase 5E scope",
    "legacy_aspirations": "frontier/experimental feature; not in Phase 5E scope",
}

# Tables with ENABLE RLS but intentionally WITHOUT FORCE RLS.
# These are queried during login/join before app.current_agency_id is known
# (chicken-and-egg: the auth flow needs memberships/workspace_codes to discover
# the agency, but FORCE RLS requires the agency to be set first).
# The table owner still bypasses ENABLE RLS; only non-owner roles are restricted.
RLS_FORCE_EXEMPT_TABLES: frozenset[str] = frozenset({"memberships", "workspace_codes"})


@dataclass(frozen=True, slots=True)
class RlsTablePosture:
    """Live RLS posture for one tenant-scoped PostgreSQL table."""

    table_name: str
    owner: str
    rls_enabled: bool
    force_rls: bool


@dataclass(frozen=True, slots=True)
class RlsRuntimePosture:
    """Runtime role posture for tenant RLS enforcement."""

    current_user: str
    is_superuser: bool
    bypasses_rls: bool
    tables: tuple[RlsTablePosture, ...]
    expected_tables: tuple[str, ...] = RLS_TENANT_TABLES

    @property
    def risks(self) -> tuple[str, ...]:
        """Return concrete reasons RLS is not enforceable for this runtime role."""
        risks: list[str] = []
        if self.is_superuser:
            risks.append(f"runtime role {self.current_user} is a superuser")
        if self.bypasses_rls:
            risks.append(f"runtime role {self.current_user} has BYPASSRLS")

        tables_by_name = {table.table_name: table for table in self.tables}
        for table_name in sorted(set(self.expected_tables) - set(tables_by_name)):
            risks.append(f"{table_name} is missing from the live database")

        for table in sorted(self.tables, key=lambda item: item.table_name):
            if not table.rls_enabled:
                risks.append(f"{table.table_name} has row-level security disabled")
            if table.owner == self.current_user and not table.force_rls:
                # Auth-exempt tables intentionally skip FORCE RLS (chicken-and-egg
                # during login/join). ENABLE RLS still protects against non-owners.
                if table.table_name not in RLS_FORCE_EXEMPT_TABLES:
                    risks.append(
                        f"{table.table_name} is owned by runtime role "
                        f"{self.current_user} and FORCE RLS is disabled"
                )
        return tuple(risks)

    @property
    def is_enforced_for_runtime_role(self) -> bool:
        """True when the runtime role cannot bypass tenant RLS policies."""
        return not self.risks


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


async def inspect_rls_runtime_posture(
    session: AsyncConnection | AsyncSession,
    expected_tables: Sequence[str] = RLS_TENANT_TABLES,
) -> RlsRuntimePosture:
    """Inspect whether the current PostgreSQL role is subject to tenant RLS."""
    role_row = (
        await session.execute(
            text(
                """
                SELECT current_user AS current_user,
                       r.rolsuper AS is_superuser,
                       r.rolbypassrls AS bypasses_rls
                FROM pg_roles r
                WHERE r.rolname = current_user
                """
            )
        )
    ).mappings().one()

    table_rows = (
        await session.execute(
            text(
                """
                SELECT c.relname AS table_name,
                       pg_get_userbyid(c.relowner) AS owner,
                       c.relrowsecurity AS rls_enabled,
                       c.relforcerowsecurity AS force_rls
                FROM pg_class c
                JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE n.nspname = 'public'
                  AND c.relname = ANY(:tables)
                ORDER BY c.relname
                """
            ),
            {"tables": list(expected_tables)},
        )
    ).mappings().all()

    return RlsRuntimePosture(
        current_user=str(role_row["current_user"]),
        is_superuser=bool(role_row["is_superuser"]),
        bypasses_rls=bool(role_row["bypasses_rls"]),
        tables=tuple(
            RlsTablePosture(
                table_name=str(row["table_name"]),
                owner=str(row["owner"]),
                rls_enabled=bool(row["rls_enabled"]),
                force_rls=bool(row["force_rls"]),
            )
            for row in table_rows
        ),
        expected_tables=tuple(expected_tables),
    )


async def get_rls_db(
    db: AsyncSession = Depends(get_db),
) -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency: yields a DB session with RLS applied.

    Uses the agency_id stored in the ContextVar (set by get_current_membership).
    Falls through to a plain session if no agency_id is set (e.g. in test fixtures
    that bypass auth, or public endpoints).

    Uses session-level set_config so the RLS context survives commits within
    the request. Resets the value on exit to prevent pool bleeding.

    Usage in routes:
        @router.get("/items")
        async def list_items(db: AsyncSession = Depends(get_rls_db)):
            ...
    """
    agency_id = _current_agency_id.get()
    if agency_id:
        await db.execute(
            text("SELECT set_config('app.current_agency_id', :agency_id, false)"),
            {"agency_id": agency_id},
        )
    try:
        yield db
    finally:
        if agency_id:
            try:
                await db.execute(
                    text("SELECT set_config('app.current_agency_id', '', false)"),
                )
            except Exception:
                pass


@asynccontextmanager
async def rls_session(agency_id: str):
    """
    Context manager: yields a DB session with RLS applied for the given agency.

    Use this when an endpoint needs direct session control (e.g., document upload)
    but still requires tenant isolation. Prefer get_rls_db() for standard routes;
    use this for async_session_maker() replacements.

    Uses set_config(..., false) (session-level, not transaction-level) so the
    RLS context survives commits/rollbacks within the same session. Resets the
    value to empty on exit to prevent cross-request bleeding through the pool.
    """
    from spine_api.core.database import async_session_maker

    async with async_session_maker() as session:
        # Session-level so it survives commits within this session
        await session.execute(
            text("SELECT set_config('app.current_agency_id', :agency_id, false)"),
            {"agency_id": agency_id},
        )
        try:
            yield session
        finally:
            # Clear the session-level setting to prevent pool bleeding
            await session.execute(
                text("SELECT set_config('app.current_agency_id', '', false)"),
            )
