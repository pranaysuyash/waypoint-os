"""
src/agents/idempotency.py — Idempotency key reservation and execution deduplication engine.

Grounding doctrine:
- PER-0700 (Agentic Systems Architect): Prevent duplicate side-effects during agent lease transitions or network retries.

Backends (PT-08, Docs/review/SPINE_AUDIT_NEW_FINDINGS_2026-09-02.md):
- ``memory`` (default): in-process, correct for single-worker deployments and
  tests. Selected via ``SPINE_API_IDEMPOTENCY_BACKEND=memory`` or by
  constructing ``IdempotencyRegistry()`` directly.
- ``sql``: durable ``idempotency_keys`` table (spine_api/models/idempotency.py)
  on the app's async engine. Cross-worker / cross-replica duplicate protection
  holds because the table's primary key is the idempotency key — concurrent
  acquirers race one INSERT and the PK conflict decides the winner.
- ``auto``: ``sql`` when DATABASE_URL is set, else ``memory``.

Production / multi-worker deployments MUST run with ``sql`` (pinned in
docker-compose.yml). Acquirers must pass the returned record's
``fencing_token`` to ``mark_completed``/``mark_failed``; an unfenced or stale
terminal transition is rejected. The backend choice does not change the
acquisition/replay tuple returned by ``IdempotencyRegistry``.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import secrets
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger("src.agents.idempotency")

IDEMPOTENCY_BACKEND_ENV = "SPINE_API_IDEMPOTENCY_BACKEND"


class IdempotencyStatus(str, Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    # TS-08 (2026-09-10): the provider call ended WITHOUT a definitive
    # outcome (timeout, dropped connection). UNKNOWN is NOT retryable —
    # re-executing could duplicate the side effect. Callers must resolve it
    # via verification (replay stored confirmations / provider recheck) and
    # then transition it to COMPLETED or FAILED via resolve_unknown().
    # UNKNOWN records are exempt from TTL reclaim for the same reason.
    UNKNOWN = "UNKNOWN"


@dataclass(slots=True)
class IdempotencyRecord:
    """Stored execution record for an idempotent operation."""
    key: str
    trip_id: str
    action_name: str
    request_hash: str
    status: IdempotencyStatus
    # Opaque generation fence. A new token is minted for every acquisition
    # (including TTL/FAILED reclaim); completion must present the token it was
    # handed, so a stale owner cannot close a newer owner's row.
    fencing_token: str = field(default_factory=lambda: secrets.token_urlsafe(32))
    created_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None
    response_payload: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    ttl_seconds: int = 86400  # 24-hour default retention


class SqlIdempotencyBackend:
    """Durable SQL backend for the idempotency registry (PT-08).

    Presents the same synchronous interface as the in-memory path; async
    SQLAlchemy operations are executed on the repo's canonical sync→async
    bridge (``spine_api.persistence._run_async_blocking``), the same pattern
    TripStore/agent_work_coordinator use.

    All engine/model imports are lazy so that merely importing this module
    (or running with the memory backend) never requires DATABASE_URL.
    """

    def __init__(self, engine=None, session_maker=None):
        self._engine = engine
        self._session_maker = session_maker
        self._table_ready = False

    # ------------------------------------------------------------------
    # Lazy wiring
    # ------------------------------------------------------------------

    def _get_engine(self):
        if self._engine is None:
            from spine_api.core.database import engine as app_engine

            self._engine = app_engine
        return self._engine

    def _get_session_maker(self):
        if self._session_maker is None:
            from spine_api.core.database import async_session_maker

            self._session_maker = async_session_maker
        return self._session_maker

    def _run(self, coro):
        from spine_api.persistence import _run_async_blocking

        return _run_async_blocking(coro)

    async def _ensure_table(self) -> None:
        if self._table_ready:
            return
        from spine_api.core.database import Base
        from spine_api.models.idempotency import IdempotencyKey

        async with self._get_engine().begin() as conn:
            await conn.run_sync(
                lambda sync_conn: Base.metadata.create_all(
                    sync_conn, tables=[IdempotencyKey.__table__], checkfirst=True
                )
            )
        self._table_ready = True

    # ------------------------------------------------------------------
    # Row ↔ record mapping
    # ------------------------------------------------------------------

    @staticmethod
    def _as_utc(dt: datetime) -> datetime:
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt

    @staticmethod
    def _record_from_row(
        key: str, trip_id: str, action_name: str, request_hash: str, row: Any
    ) -> IdempotencyRecord:
        return IdempotencyRecord(
            key=key,
            trip_id=trip_id,
            action_name=action_name,
            request_hash=request_hash,
            status=IdempotencyStatus(row.status),
            fencing_token=getattr(row, "fencing_token", None)
            or secrets.token_urlsafe(32),
            created_at=SqlIdempotencyBackend._as_utc(row.created_at).timestamp(),
            completed_at=(
                SqlIdempotencyBackend._as_utc(row.completed_at).timestamp()
                if row.completed_at is not None
                else None
            ),
            response_payload=row.response_payload,
            error_message=row.error_message,
            ttl_seconds=row.ttl_seconds,
        )

    # ------------------------------------------------------------------
    # Public synchronous interface (mirrors the in-memory registry)
    # ------------------------------------------------------------------

    def try_acquire(
        self,
        key: str,
        trip_id: str,
        action_name: str,
        payload: Dict[str, Any],
        ttl_seconds: int = 86400,
    ) -> Tuple[bool, Optional[IdempotencyRecord]]:
        return self._run(
            self._try_acquire_async(key, trip_id, action_name, payload, ttl_seconds)
        )

    async def _try_acquire_async(
        self,
        key: str,
        trip_id: str,
        action_name: str,
        payload: Dict[str, Any],
        ttl_seconds: int = 86400,
        _retries: int = 0,
    ) -> Tuple[bool, Optional[IdempotencyRecord]]:
        from sqlalchemy import select, update
        from sqlalchemy.exc import IntegrityError, OperationalError

        from spine_api.models.idempotency import IdempotencyKey

        await self._ensure_table()
        now = datetime.now(timezone.utc)
        payload_hash = hashlib.sha256(
            json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()
        fencing_token = secrets.token_urlsafe(32)

        # Enter a session from the maker (async_sessionmaker must be CALLED;
        # the maker object itself is not an async context manager).
        session_maker = self._get_session_maker()
        async with session_maker() as session:
            # Atomic acquire: the PK on `key` makes concurrent INSERTs from any
            # number of workers decide exactly one winner.
            session.add(
                IdempotencyKey(
                    key=key,
                    status=IdempotencyStatus.PENDING.value,
                    trip_id=trip_id,
                    action_name=action_name,
                    request_hash=payload_hash,
                    fencing_token=fencing_token,
                    created_at=now,
                    ttl_seconds=ttl_seconds,
                )
            )
            try:
                await session.commit()
                record = IdempotencyRecord(
                    key=key,
                    trip_id=trip_id,
                    action_name=action_name,
                    request_hash=payload_hash,
                    status=IdempotencyStatus.PENDING,
                    fencing_token=fencing_token,
                    created_at=now.timestamp(),
                    ttl_seconds=ttl_seconds,
                )
                return True, record
            except (IntegrityError, OperationalError):
                # Someone else holds the key. Replay their state.
                await session.rollback()

            row = (
                await session.execute(select(IdempotencyKey).where(IdempotencyKey.key == key))
            ).scalar_one_or_none()
            if row is None:
                # The holder's row expired/vanished between our failed INSERT
                # and this SELECT. Retry the whole acquire a bounded number of
                # times instead of busy-looping.
                if _retries >= 3:
                    raise RuntimeError(
                        f"Idempotency key {key!r} vanished while acquiring after retries"
                    )
                return await self._try_acquire_async(
                    key, trip_id, action_name, payload, ttl_seconds, _retries + 1
                )

            record = self._record_from_row(key, trip_id, action_name, row.request_hash, row)
            age_seconds = (now - self._as_utc(row.created_at)).total_seconds()

            if age_seconds > row.ttl_seconds and row.status != IdempotencyStatus.UNKNOWN.value:
                # Expired: reclaim with a guarded UPDATE so concurrent reclaims
                # cannot both win (only one caller sees rowcount=1).
                # UNKNOWN rows are exempt (TS-08): an expired-but-unresolved
                # outcome must never be silently reset to PENDING — that is
                # the duplicate-side-effect hazard UNKNOWN exists to prevent.
                fencing_token = secrets.token_urlsafe(32)
                result = await session.execute(
                    update(IdempotencyKey)
                    .where(IdempotencyKey.key == key)
                    .where(IdempotencyKey.created_at == row.created_at)
                    .values(
                        status=IdempotencyStatus.PENDING.value,
                        trip_id=trip_id,
                        action_name=action_name,
                        request_hash=payload_hash,
                        fencing_token=fencing_token,
                        response_payload=None,
                        error_message=None,
                        completed_at=None,
                        created_at=now,
                        ttl_seconds=ttl_seconds,
                    )
                )
                await session.commit()
                if result.rowcount == 1:
                    record = IdempotencyRecord(
                        key=key,
                        trip_id=trip_id,
                        action_name=action_name,
                        request_hash=payload_hash,
                        status=IdempotencyStatus.PENDING,
                        fencing_token=fencing_token,
                        created_at=now.timestamp(),
                        ttl_seconds=ttl_seconds,
                    )
                    return True, record
                if _retries >= 3:
                    raise RuntimeError(f"Idempotency key {key!r} reclaim raced past retry budget")
                return await self._try_acquire_async(
                    key, trip_id, action_name, payload, ttl_seconds, _retries + 1
                )

            if record.status == IdempotencyStatus.COMPLETED:
                logger.info("Idempotent hit: returning cached result for key=%s", key)
                return False, record
            if record.status == IdempotencyStatus.UNKNOWN:
                # TS-08: outcome unresolved — never re-execute. The caller
                # must verify (replay/recheck) and resolve_unknown() the row.
                logger.warning(
                    "Idempotency outcome UNKNOWN for key=%s: verification required before any retry",
                    key,
                )
                return False, record
            if record.status == IdempotencyStatus.PENDING:
                logger.warning(
                    "Idempotent conflict: action currently in-flight for key=%s", key
                )
                return False, record

            # FAILED → allow retry, exactly like the in-memory backend. The
            # reclaim uses the same guarded UPDATE as TTL expiry: two concurrent
            # retries of the same payload must not both win — both proceeding
            # would mint duplicate effects, the exact N-1 defect (review cycle 2, C).
            logger.info("Idempotent retry: previous attempt failed for key=%s", key)
            fencing_token = secrets.token_urlsafe(32)
            result = await session.execute(
                update(IdempotencyKey)
                .where(IdempotencyKey.key == key)
                .where(IdempotencyKey.created_at == row.created_at)
                .where(IdempotencyKey.status == IdempotencyStatus.FAILED.value)
                .values(
                    status=IdempotencyStatus.PENDING.value,
                    trip_id=trip_id,
                    action_name=action_name,
                    request_hash=payload_hash,
                    fencing_token=fencing_token,
                    response_payload=None,
                    error_message=None,
                    completed_at=None,
                    created_at=now,
                    ttl_seconds=ttl_seconds,
                )
            )
            await session.commit()
            if result.rowcount == 1:
                record = IdempotencyRecord(
                    key=key,
                    trip_id=trip_id,
                    action_name=action_name,
                    request_hash=payload_hash,
                    status=IdempotencyStatus.PENDING,
                    fencing_token=fencing_token,
                    created_at=now.timestamp(),
                    error_message=row.error_message,
                    ttl_seconds=ttl_seconds,
                )
                return True, record
            if _retries >= 3:
                raise RuntimeError(f"Idempotency key {key!r} retry raced past retry budget")
            return await self._try_acquire_async(
                key, trip_id, action_name, payload, ttl_seconds, _retries + 1
            )

    def mark_completed(
        self,
        key: str,
        response_payload: Dict[str, Any],
        *,
        fencing_token: Optional[str] = None,
    ) -> bool:
        """Complete only the acquisition identified by ``fencing_token``.

        Returning ``False`` is intentional and safe: it means this owner lost
        the race to a reclaim/other terminal transition. Callers must not
        treat a stale completion as authoritative.
        """
        return self._run(
            self._mark_async(
                key,
                IdempotencyStatus.COMPLETED,
                response_payload,
                None,
                fencing_token,
            )
        )

    def mark_failed(
        self,
        key: str,
        error_message: str,
        *,
        fencing_token: Optional[str] = None,
    ) -> bool:
        return self._run(
            self._mark_async(
                key,
                IdempotencyStatus.FAILED,
                None,
                error_message,
                fencing_token,
            )
        )

    def mark_unknown(
        self,
        key: str,
        error_message: str,
        *,
        fencing_token: Optional[str] = None,
    ) -> bool:
        """Transition PENDING -> UNKNOWN (outcome unresolved, TS-08).

        Used when a provider call ends without a definitive answer (timeout,
        dropped connection). UNKNOWN blocks re-execution until resolved.
        """
        return self._run(
            self._mark_async(
                key,
                IdempotencyStatus.UNKNOWN,
                None,
                error_message,
                fencing_token,
            )
        )

    def resolve_unknown(
        self,
        key: str,
        *,
        response_payload: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        fencing_token: Optional[str] = None,
    ) -> bool:
        """Resolve an UNKNOWN record to COMPLETED or FAILED (TS-08).

        Exactly one of ``response_payload`` (verified success) or
        ``error_message`` (verified non-occurrence) must be provided.
        The transition is a fenced CAS on the UNKNOWN status so a stale
        owner cannot close a newer owner's row.
        """
        if bool(response_payload) == bool(error_message):
            raise ValueError(
                "resolve_unknown requires exactly one of response_payload or error_message"
            )
        target = (
            IdempotencyStatus.COMPLETED if response_payload else IdempotencyStatus.FAILED
        )
        return self._run(
            self._resolve_unknown_async(key, target, response_payload, error_message, fencing_token)
        )

    async def _resolve_unknown_async(
        self,
        key: str,
        target: IdempotencyStatus,
        response_payload: Optional[Dict[str, Any]],
        error_message: Optional[str],
        fencing_token: Optional[str],
    ) -> bool:
        from sqlalchemy import update

        from spine_api.models.idempotency import IdempotencyKey

        await self._ensure_table()
        now = datetime.now(timezone.utc)
        session_maker = self._get_session_maker()
        async with session_maker() as session:
            if not fencing_token:
                logger.warning("Rejected unfenced idempotency resolution key=%s", key)
                return False
            result = await session.execute(
                update(IdempotencyKey)
                .where(IdempotencyKey.key == key)
                .where(IdempotencyKey.status == IdempotencyStatus.UNKNOWN.value)
                .where(IdempotencyKey.fencing_token == fencing_token)
                .values(
                    status=target.value,
                    completed_at=now,
                    response_payload=response_payload,
                    error_message=error_message,
                )
            )
            await session.commit()
            return result.rowcount == 1

    async def _mark_async(
        self,
        key: str,
        status: IdempotencyStatus,
        response_payload: Optional[Dict[str, Any]],
        error_message: Optional[str],
        fencing_token: Optional[str],
    ) -> bool:
        from sqlalchemy import update

        from spine_api.models.idempotency import IdempotencyKey

        await self._ensure_table()
        now = datetime.now(timezone.utc)
        # Maker must be CALLED (see _try_acquire_async note).
        session_maker = self._get_session_maker()
        async with session_maker() as session:
            # Compare-and-set on the acquisition generation. ``PENDING`` alone
            # is insufficient: both a stale owner and a reclaimed owner can be
            # pending at the same time. Missing tokens fail closed.
            if not fencing_token:
                logger.warning("Rejected unfenced idempotency completion key=%s", key)
                return False
            result = await session.execute(
                update(IdempotencyKey)
                .where(IdempotencyKey.key == key)
                .where(IdempotencyKey.status == IdempotencyStatus.PENDING.value)
                .where(IdempotencyKey.fencing_token == fencing_token)
                .values(
                    status=status.value,
                    completed_at=now,
                    response_payload=response_payload,
                    error_message=error_message,
                )
            )
            await session.commit()
            return result.rowcount == 1


class IdempotencyRegistry:
    """Thread-safe registry with pluggable backend for idempotency keys.

    Backend selection: constructing ``IdempotencyRegistry()`` directly (tests,
    in-process use) always uses the in-memory backend. ``get_instance()``
    resolves the process-wide backend from ``SPINE_API_IDEMPOTENCY_BACKEND``
    (see module docstring). Multi-worker deployments (uvicorn workers, celery,
    replicas) need the ``sql`` backend before cross-process dedup holds.
    """

    _instance: Optional[IdempotencyRegistry] = None
    _instance_lock = threading.Lock()

    def __init__(self, backend: Optional[Any] = None):
        self._backend = backend
        self._records: Dict[str, IdempotencyRecord] = {}
        self._lock = threading.Lock()

    @classmethod
    def get_instance(cls) -> IdempotencyRegistry:
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    backend_name = (
                        os.environ.get(IDEMPOTENCY_BACKEND_ENV, "memory").strip().lower()
                    )
                    if backend_name == "sql":
                        cls._instance = cls(backend=SqlIdempotencyBackend())
                    elif backend_name == "auto":
                        database_url = os.environ.get("DATABASE_URL")
                        cls._instance = cls(
                            backend=SqlIdempotencyBackend() if database_url else None
                        )
                    else:
                        cls._instance = cls()
        return cls._instance

    @staticmethod
    def generate_key(trip_id: str, action_name: str, payload: Dict[str, Any]) -> str:
        """Generate a deterministic idempotency key from trip_id, action, and payload hash."""
        serialized = json.dumps(payload, sort_keys=True, default=str)
        payload_hash = hashlib.sha256(serialized.encode("utf-8")).hexdigest()[:16]
        return f"idem:{trip_id}:{action_name}:{payload_hash}"

    def try_acquire(
        self,
        key: str,
        trip_id: str,
        action_name: str,
        payload: Dict[str, Any],
        ttl_seconds: int = 86400,
    ) -> tuple[bool, Optional[IdempotencyRecord]]:
        """
        Attempt to acquire an idempotency key.
        Returns:
            (True, record) if acquired (new execution allowed).
            (False, record) if already exists (should return cached response or reject concurrent run).
        """
        if self._backend is not None:
            return self._backend.try_acquire(
                key,
                trip_id=trip_id,
                action_name=action_name,
                payload=payload,
                ttl_seconds=ttl_seconds,
            )

        now = time.time()
        with self._lock:
            record = self._records.get(key)

            # Check if existing record expired. UNKNOWN is exempt (TS-08):
            # an unresolved outcome must never be silently dropped and
            # re-executed — that is the duplicate-side-effect hazard.
            if (
                record
                and record.status != IdempotencyStatus.UNKNOWN
                and (now - record.created_at) > record.ttl_seconds
            ):
                del self._records[key]
                record = None

            if record is not None:
                if record.status == IdempotencyStatus.COMPLETED:
                    logger.info("Idempotent hit: returning cached result for key=%s", key)
                    return False, record
                elif record.status == IdempotencyStatus.UNKNOWN:
                    # Outcome unresolved: never re-execute without verification.
                    logger.warning(
                        "Idempotency outcome UNKNOWN for key=%s: verification required before any retry",
                        key,
                    )
                    return False, record
                elif record.status == IdempotencyStatus.PENDING:
                    # Concurrent in-flight execution
                    logger.warning("Idempotent conflict: action currently in-flight for key=%s", key)
                    return False, record
                elif record.status == IdempotencyStatus.FAILED:
                    logger.info("Idempotent retry: previous attempt failed for key=%s", key)
                    # Allow retry on failure

            payload_hash = hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()
            new_record = IdempotencyRecord(
                key=key,
                trip_id=trip_id,
                action_name=action_name,
                request_hash=payload_hash,
                status=IdempotencyStatus.PENDING,
                created_at=now,
                ttl_seconds=ttl_seconds,
            )
            self._records[key] = new_record
            return True, new_record

    def mark_completed(
        self,
        key: str,
        response_payload: Dict[str, Any],
        *,
        fencing_token: Optional[str] = None,
    ) -> bool:
        """Mark an operation complete only if its acquisition fence matches."""
        if self._backend is not None:
            return self._backend.mark_completed(
                key, response_payload, fencing_token=fencing_token
            )
        with self._lock:
            record = self._records.get(key)
            if (
                record is None
                or record.status != IdempotencyStatus.PENDING
                or not fencing_token
                or not hmac.compare_digest(record.fencing_token, fencing_token)
            ):
                return False
            record.status = IdempotencyStatus.COMPLETED
            record.completed_at = time.time()
            record.response_payload = response_payload
            return True

    def mark_failed(
        self,
        key: str,
        error_message: str,
        *,
        fencing_token: Optional[str] = None,
    ) -> bool:
        """Mark an operation failed only if its acquisition fence matches."""
        if self._backend is not None:
            return self._backend.mark_failed(
                key, error_message, fencing_token=fencing_token
            )
        with self._lock:
            record = self._records.get(key)
            if (
                record is None
                or record.status != IdempotencyStatus.PENDING
                or not fencing_token
                or not hmac.compare_digest(record.fencing_token, fencing_token)
            ):
                return False
            record.status = IdempotencyStatus.FAILED
            record.completed_at = time.time()
            record.error_message = error_message
            return True

    def mark_unknown(
        self,
        key: str,
        error_message: str,
        *,
        fencing_token: Optional[str] = None,
    ) -> bool:
        """PENDING -> UNKNOWN: outcome unresolved, not retryable (TS-08)."""
        if self._backend is not None:
            return self._backend.mark_unknown(
                key, error_message, fencing_token=fencing_token
            )
        with self._lock:
            record = self._records.get(key)
            if (
                record is None
                or record.status != IdempotencyStatus.PENDING
                or not fencing_token
                or not hmac.compare_digest(record.fencing_token, fencing_token)
            ):
                return False
            record.status = IdempotencyStatus.UNKNOWN
            record.completed_at = time.time()
            record.error_message = error_message
            return True

    def resolve_unknown(
        self,
        key: str,
        *,
        response_payload: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        fencing_token: Optional[str] = None,
    ) -> bool:
        """Resolve UNKNOWN -> COMPLETED or FAILED after verification (TS-08)."""
        if self._backend is not None:
            return self._backend.resolve_unknown(
                key,
                response_payload=response_payload,
                error_message=error_message,
                fencing_token=fencing_token,
            )
        if bool(response_payload) == bool(error_message):
            raise ValueError(
                "resolve_unknown requires exactly one of response_payload or error_message"
            )
        with self._lock:
            record = self._records.get(key)
            if (
                record is None
                or record.status != IdempotencyStatus.UNKNOWN
                or not fencing_token
                or not hmac.compare_digest(record.fencing_token, fencing_token)
            ):
                return False
            if response_payload is not None:
                record.status = IdempotencyStatus.COMPLETED
                record.response_payload = response_payload
            else:
                record.status = IdempotencyStatus.FAILED
                record.error_message = error_message
            record.completed_at = time.time()
            return True
