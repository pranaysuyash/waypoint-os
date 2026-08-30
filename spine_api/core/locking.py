"""
spine_api.core.locking — Distributed advisory lock fencing for trip mutations.

Provides:
- `trip_advisory_lock(db, trip_id, timeout_seconds=5.0)`: Async context manager.
- PostgreSQL `pg_try_advisory_xact_lock` for transaction-bound multi-worker mutual exclusion.
- In-memory `asyncio.Lock` fallback for SQLite / local development and unit tests.
- `TripConcurrencyConflictError`: Raised on lock acquisition timeout (HTTP 409 Conflict).
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict, Optional

from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("spine_api.locking")

# In-memory lock registry for local SQLite / test runs
_in_memory_locks: Dict[str, asyncio.Lock] = {}
_registry_lock = asyncio.Lock()


class TripConcurrencyConflictError(HTTPException):
    """Raised when a trip is concurrently being modified by another operation/agent."""

    def __init__(self, trip_id: str, detail: Optional[str] = None):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail or f"Trip {trip_id} is currently locked by another operation. Please retry.",
        )


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
    
    If connected to PostgreSQL, uses `pg_try_advisory_xact_lock(bigint)`.
    If connected to SQLite or db is None, falls back to in-memory `asyncio.Lock`.
    """
    if not trip_id:
        yield
        return

    # Check if database is PostgreSQL
    is_postgres = False
    if db is not None:
        try:
            bind = db.bind
            dialect_name = getattr(getattr(bind, "dialect", None), "name", "")
            is_postgres = "postgres" in dialect_name
        except Exception:
            is_postgres = False

    if is_postgres and db is not None:
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
    else:
        # In-memory lock fallback
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
