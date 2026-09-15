"""
spine_api.core.locking — Distributed advisory lock fencing for trip mutations.

Provides:
- `trip_advisory_lock(db, trip_id, timeout_seconds=5.0)`: Async context manager.
- PostgreSQL `pg_try_advisory_xact_lock` for transaction-bound multi-worker mutual exclusion.
- In-memory `asyncio.Lock` for explicit memory-backend pinning (tests/local dev).
- `TripConcurrencyConflictError`: Raised on lock acquisition timeout (HTTP 409 Conflict).
- `LockingBackendUnavailableError`: Raised (fail-closed) when the configured
  locking backend cannot serve the critical section — the section is REFUSED,
  never silently downgraded (FND-0225).

Backend selection (FND-0225 — pinned by config, never by accident)
------------------------------------------------------------------
``SPINE_API_LOCKING_BACKEND`` controls which mutual-exclusion implementation
guards trip critical sections. Parsing follows the explicit
``SPINE_API_DISABLE_AUTH`` boolean pattern (startup_assertions.auth_bypass_enabled):
environment variables are strings, so unknown values fail closed.

    - ``sql`` / ``postgres`` / ``postgresql``: Postgres
      ``pg_try_advisory_xact_lock``. The bound session MUST be Postgres; if it
      is not (session is None, dialect mismatch, or dialect-detection failure)
      the critical section is refused with ``LockingBackendUnavailableError``
      instead of silently degrading to process-local locks.
    - ``memory``: in-process ``asyncio.Lock``. Single-process semantics by
      construction — legitimate only for tests and single-worker local dev,
      and only when pinned explicitly through this config key.
    - ``auto`` (default when unset): derived from the live session dialect.
      Postgres sessions use advisory locks; a non-Postgres session may fall
      back to in-memory locks ONLY in development/test (logged). In
      production-like environments an auto-resolved non-Postgres dialect
      refuses the critical section — a misconfigured production deployment
      must not silently change mutual-exclusion semantics.

``startup_assertions._check_locking_backend`` additionally requires
production-like deployments to pin the backend to sql/postgres so that a
process-local lock can never be selected by accident at boot.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict, Optional

from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("spine_api.locking")

# In-memory lock registry for explicitly-pinned memory backend runs
_in_memory_locks: Dict[str, asyncio.Lock] = {}
_registry_lock = asyncio.Lock()

# Backend vocabulary (explicit string parsing — see module docstring).
_SQL_BACKEND_VALUES = frozenset({"sql", "postgres", "postgresql"})
_MEMORY_BACKEND_VALUES = frozenset({"memory"})
_AUTO_BACKEND_VALUES = frozenset({"", "auto"})
_PRODUCTION_LIKE_ENVIRONMENTS = frozenset({"production", "staging"})


class TripConcurrencyConflictError(HTTPException):
    """Raised when a trip is concurrently being modified by another operation/agent."""

    def __init__(self, trip_id: str, detail: Optional[str] = None):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail or f"Trip {trip_id} is currently locked by another operation. Please retry.",
        )


class LockingBackendMisconfiguredError(RuntimeError):
    """Raised when SPINE_API_LOCKING_BACKEND holds an unrecognized value.

    Unknown env values fail closed (same doctrine as SPINE_API_DISABLE_AUTH):
    a typoed backend name must never select an implementation by accident.
    """

    def __init__(self, raw_value: str):
        self.raw_value = raw_value
        super().__init__(
            f"SPINE_API_LOCKING_BACKEND={raw_value!r} is not recognized. "
            "Valid values: sql, postgres, postgresql, memory, auto (unset)."
        )


class LockingBackendUnavailableError(RuntimeError):
    """Raised when the configured locking backend cannot serve a critical section.

    FND-0225: the previous behavior silently downgraded to in-process locks
    whenever the session dialect was not Postgres — giving dev/tests and a
    misconfigured production deployment different (unobservable)
    mutual-exclusion semantics. This error refuses the critical section
    instead: callers fail loudly (HTTP 500) rather than silently losing
    cross-worker mutual exclusion.
    """

    def __init__(self, configured_backend: str, observed: str, trip_id: str):
        self.configured_backend = configured_backend
        self.observed_backend = observed
        super().__init__(
            f"Locking backend '{configured_backend}' cannot guard trip "
            f"{trip_id!r}: observed backend/dialect is {observed!r}. "
            "Refusing the critical section rather than silently downgrading "
            "to process-local locks. Fix SPINE_API_LOCKING_BACKEND / the "
            "database session binding."
        )


def configured_locking_backend() -> str:
    """Parse SPINE_API_LOCKING_BACKEND into a canonical backend name.

    Returns one of ``"postgres"``, ``"memory"``, ``"auto"``. Unset/empty means
    ``"auto"``. Any other value raises ``LockingBackendMisconfiguredError``
    (fail closed).
    """
    raw = os.environ.get("SPINE_API_LOCKING_BACKEND", "").strip().lower()
    if raw in _AUTO_BACKEND_VALUES:
        return "auto"
    if raw in _SQL_BACKEND_VALUES:
        return "postgres"
    if raw in _MEMORY_BACKEND_VALUES:
        return "memory"
    raise LockingBackendMisconfiguredError(raw)


def _environment_allows_memory_fallback() -> bool:
    """Memory-lock fallback (auto mode) is dev/test-only; prod-like envs refuse."""
    env = os.environ.get("ENVIRONMENT", "development").strip().lower()
    return env not in _PRODUCTION_LIKE_ENVIRONMENTS


def _session_backend_label(db: Optional[AsyncSession]) -> str:
    """Return a best-effort label of what backend the bound session provides.

    Returns ``"<no-session>"`` when db is None and ``"<unknown>"`` when the
    dialect cannot be proven (detection failure never counts as Postgres).
    """
    if db is None:
        return "<no-session>"
    try:
        dialect_name = getattr(getattr(db.bind, "dialect", None), "name", "") or ""
    except Exception:
        return "<unknown>"
    return dialect_name


def _trip_id_to_bigint(trip_id: str) -> int:
    """Hash a trip_id string into a signed 64-bit integer for Postgres advisory locks."""
    digest = hashlib.sha256(trip_id.encode("utf-8")).hexdigest()
    # Take first 15 hex chars -> 60 bits (fits easily in signed 64-bit int)
    uint60 = int(digest[:15], 16)
    # Signed 64-bit range: -2^63 to 2^63-1
    return uint60 - (1 << 59)


async def _get_in_memory_lock(trip_id: str) -> asyncio.Lock:
    async with _registry_lock:
        if trip_id not in _in_memory_locks:
            _in_memory_locks[trip_id] = asyncio.Lock()
        return _in_memory_locks[trip_id]


@asynccontextmanager
async def trip_advisory_lock(
    db: Optional[AsyncSession],
    trip_id: str,
    timeout_seconds: float = 5.0,
) -> AsyncGenerator[None, None]:
    """
    Acquire a distributed advisory lock for the given trip_id.

    Backend resolution (FND-0225, see module docstring):
      - SPINE_API_LOCKING_BACKEND=sql/postgres → Postgres advisory lock;
        refuses (LockingBackendUnavailableError) unless the bound session is
        provably Postgres.
      - SPINE_API_LOCKING_BACKEND=memory → in-process asyncio lock (explicit
        pin, tests/local dev).
      - unset/auto → Postgres advisory lock for Postgres sessions; memory
        fallback otherwise, but only in development/test — production-like
        environments refuse the critical section.
    """
    if not trip_id:
        yield
        return

    backend = configured_locking_backend()
    dialect_name = _session_backend_label(db)
    is_postgres = "postgres" in dialect_name

    if backend == "postgres":
        if not is_postgres or db is None:
            raise LockingBackendUnavailableError(backend, dialect_name, trip_id)
        async with _postgres_advisory_lock(db, trip_id, timeout_seconds):
            yield
        return

    if backend == "memory":
        async with _in_memory_advisory_lock(trip_id, timeout_seconds):
            yield
        return

    # auto: derive from the live session dialect.
    if is_postgres and db is not None:
        async with _postgres_advisory_lock(db, trip_id, timeout_seconds):
            yield
        return

    if _environment_allows_memory_fallback():
        logger.debug(
            "trip_advisory_lock: non-Postgres session (dialect=%r, db=%s) for "
            "trip %s — using in-process locks in a non-production environment "
            "(pin SPINE_API_LOCKING_BACKEND to make this explicit).",
            dialect_name,
            "absent" if db is None else "bound",
            trip_id,
        )
        async with _in_memory_advisory_lock(trip_id, timeout_seconds):
            yield
        return

    raise LockingBackendUnavailableError("auto/postgres", dialect_name, trip_id)


@asynccontextmanager
async def _postgres_advisory_lock(db: AsyncSession, trip_id: str, timeout_seconds: float) -> AsyncGenerator[None, None]:
    """Hold a Postgres transaction-scoped advisory lock for the critical section."""
    lock_key = _trip_id_to_bigint(trip_id)
    start_time = asyncio.get_event_loop().time()
    acquired = False

    while not acquired:
        result = await db.execute(
            text("SELECT pg_try_advisory_xact_lock(:key)"),
            {"key": lock_key},
        )
        acquired = bool(result.scalar())

        if acquired:
            break

        elapsed = asyncio.get_event_loop().time() - start_time
        if elapsed >= timeout_seconds:
            logger.warning(
                "Timeout waiting for Postgres advisory lock on trip %s (key=%s, elapsed=%.2fs)",
                trip_id,
                lock_key,
                elapsed,
            )
            raise TripConcurrencyConflictError(trip_id)

        await asyncio.sleep(0.1)

    try:
        yield
    finally:
        # Transaction-scoped locks in Postgres (xact_lock) automatically release on commit/rollback.
        pass


@asynccontextmanager
async def _in_memory_advisory_lock(trip_id: str, timeout_seconds: float) -> AsyncGenerator[None, None]:
    """Hold an in-process asyncio lock for the critical section (explicit memory pin)."""
    mem_lock = await _get_in_memory_lock(trip_id)
    try:
        await asyncio.wait_for(mem_lock.acquire(), timeout=timeout_seconds)
    except asyncio.TimeoutError:
        logger.warning(
            "Timeout waiting for in-memory lock on trip %s",
            trip_id,
        )
        raise TripConcurrencyConflictError(trip_id)

    try:
        yield
    finally:
        if mem_lock.locked():
            mem_lock.release()
