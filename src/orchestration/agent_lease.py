"""
src/orchestration/agent_lease.py — Durable Agent Lease & Distributed Fencing Token State Machine.

Prevents split-brain state mutations and double-booking race conditions across concurrent
AI agents and human operators (R-11). Implements monotonic fencing token validation.

Backends (IMP-07):
- ``memory`` (default): in-process, thread-safe with RLock for single-worker deployments and tests.
- ``sql``: distributed durable locking via ``agent_leases`` table with row locks.
- ``auto``: ``sql`` when DATABASE_URL is present, else ``memory``.
"""

from __future__ import annotations

import logging
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from threading import RLock
from typing import Any, Dict, Optional

logger = logging.getLogger("src.orchestration.agent_lease")

AGENT_LEASE_BACKEND_ENV = "SPINE_API_AGENT_LEASE_BACKEND"


@dataclass(slots=True)
class AgentLeaseRecord:
    trip_id: str
    holder_id: str
    lease_token: str
    fencing_token: int
    acquired_at: datetime
    expires_at: datetime
    ttl_seconds: int
    is_active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) >= self.expires_at

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trip_id": self.trip_id,
            "holder_id": self.holder_id,
            "lease_token": self.lease_token,
            "fencing_token": self.fencing_token,
            "acquired_at": self.acquired_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "ttl_seconds": self.ttl_seconds,
            "is_active": self.is_active and not self.is_expired(),
            "metadata": self.metadata,
        }


class MemoryAgentLeaseBackend:
    """Thread-safe in-memory lease backend."""

    def __init__(self) -> None:
        self._leases: Dict[str, AgentLeaseRecord] = {}
        self._trip_fencing_counters: Dict[str, int] = {}
        self._lock = RLock()

    @staticmethod
    def _validate_ttl(ttl_seconds: int) -> None:
        if isinstance(ttl_seconds, bool) or not isinstance(ttl_seconds, int) or ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be a positive integer")

    @staticmethod
    def _expire_if_needed(record: AgentLeaseRecord, now: datetime) -> bool:
        if record.is_active and now >= record.expires_at:
            record.is_active = False
        return not record.is_active

    def acquire_lease(
        self,
        trip_id: str,
        holder_id: str,
        ttl_seconds: int = 30,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AgentLeaseRecord:
        self._validate_ttl(ttl_seconds)
        now = datetime.now(timezone.utc)
        with self._lock:
            current = self._leases.get(trip_id)
            if current:
                self._expire_if_needed(current, now)

            if current and current.is_active:
                raise ValueError(
                    f"Trip '{trip_id}' is currently locked by '{current.holder_id}' "
                    f"until {current.expires_at.isoformat()}."
                )

            self._trip_fencing_counters[trip_id] = self._trip_fencing_counters.get(trip_id, 0) + 1
            fencing_token = self._trip_fencing_counters[trip_id]
            lease_token = f"lease_{uuid.uuid4().hex[:16]}"
            expires_at = now + timedelta(seconds=ttl_seconds)

            record = AgentLeaseRecord(
                trip_id=trip_id,
                holder_id=holder_id,
                lease_token=lease_token,
                fencing_token=fencing_token,
                acquired_at=now,
                expires_at=expires_at,
                ttl_seconds=ttl_seconds,
                is_active=True,
                metadata=dict(metadata or {}),
            )
            self._leases[trip_id] = record
            return record

    def renew_lease(self, trip_id: str, lease_token: str, ttl_seconds: int = 30) -> AgentLeaseRecord:
        self._validate_ttl(ttl_seconds)
        now = datetime.now(timezone.utc)
        with self._lock:
            current = self._leases.get(trip_id)
            if not current or current.lease_token != lease_token or not current.is_active:
                raise ValueError(f"No active lease found matching token for trip '{trip_id}'")

            if self._expire_if_needed(current, now):
                raise ValueError(f"Lease for trip '{trip_id}' has expired and cannot be renewed")

            current.expires_at = now + timedelta(seconds=ttl_seconds)
            current.ttl_seconds = ttl_seconds
            return current

    def release_lease(self, trip_id: str, lease_token: str) -> bool:
        now = datetime.now(timezone.utc)
        with self._lock:
            current = self._leases.get(trip_id)
            if not current or current.lease_token != lease_token:
                return False
            if self._expire_if_needed(current, now):
                return False
            current.is_active = False
            return True

    def verify_fencing_token(self, trip_id: str, fencing_token: int) -> bool:
        with self._lock:
            current = self._leases.get(trip_id)
            if current is None or self._expire_if_needed(current, datetime.now(timezone.utc)):
                return False
            current_counter = self._trip_fencing_counters.get(trip_id, 0)
            return fencing_token == current_counter and current_counter > 0

    def get_lease(self, trip_id: str) -> Optional[AgentLeaseRecord]:
        with self._lock:
            current = self._leases.get(trip_id)
            if current:
                self._expire_if_needed(current, datetime.now(timezone.utc))
            return current

    def sweep_stale_leases(self) -> int:
        swept = 0
        now = datetime.now(timezone.utc)
        with self._lock:
            for record in self._leases.values():
                if record.is_active and now >= record.expires_at:
                    record.is_active = False
                    swept += 1
        return swept

    def clear(self) -> None:
        with self._lock:
            self._leases.clear()
            self._trip_fencing_counters.clear()


class SqlAgentLeaseBackend:
    """Distributed SQL backend for agent leases."""

    def __init__(self, engine=None, session_maker=None):
        self._engine = engine
        self._session_maker = session_maker
        self._table_ready = False

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
        from spine_api.models.agent_lease import AgentLeaseModel
        async with self._get_engine().begin() as conn:
            await conn.run_sync(
                lambda sync_conn: Base.metadata.create_all(
                    sync_conn, tables=[AgentLeaseModel.__table__], checkfirst=True
                )
            )
        self._table_ready = True

    @staticmethod
    def _as_utc(dt: datetime) -> datetime:
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt

    def acquire_lease(
        self,
        trip_id: str,
        holder_id: str,
        ttl_seconds: int = 30,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AgentLeaseRecord:
        MemoryAgentLeaseBackend._validate_ttl(ttl_seconds)

        async def _async_acquire():
            await self._ensure_table()
            from sqlalchemy import select
            from spine_api.models.agent_lease import AgentLeaseModel

            now = datetime.now(timezone.utc)
            expires_at = now + timedelta(seconds=ttl_seconds)
            maker = self._get_session_maker()
            async with maker() as session:
                async with session.begin():
                    stmt = select(AgentLeaseModel).where(AgentLeaseModel.trip_id == trip_id).with_for_update()
                    res = await session.execute(stmt)
                    row = res.scalar_one_or_none()

                    if row is not None:
                        row_exp = self._as_utc(row.expires_at)
                        if row.is_active and now < row_exp:
                            raise ValueError(
                                f"Trip '{trip_id}' is currently locked by '{row.holder_id}' until {row_exp.isoformat()}."
                            )
                        new_fencing = row.fencing_token + 1
                        new_token = f"lease_{uuid.uuid4().hex[:16]}"
                        row.holder_id = holder_id
                        row.lease_token = new_token
                        row.fencing_token = new_fencing
                        row.acquired_at = now
                        row.expires_at = expires_at
                        row.ttl_seconds = ttl_seconds
                        row.is_active = True
                        row.lease_metadata = dict(metadata or {})
                        await session.flush()
                        return AgentLeaseRecord(
                            trip_id=trip_id,
                            holder_id=holder_id,
                            lease_token=new_token,
                            fencing_token=new_fencing,
                            acquired_at=now,
                            expires_at=expires_at,
                            ttl_seconds=ttl_seconds,
                            is_active=True,
                            metadata=dict(metadata or {}),
                        )
                    else:
                        new_token = f"lease_{uuid.uuid4().hex[:16]}"
                        row = AgentLeaseModel(
                            trip_id=trip_id,
                            holder_id=holder_id,
                            lease_token=new_token,
                            fencing_token=1,
                            acquired_at=now,
                            expires_at=expires_at,
                            ttl_seconds=ttl_seconds,
                            is_active=True,
                            lease_metadata=dict(metadata or {}),
                        )
                        session.add(row)
                        await session.flush()
                        return AgentLeaseRecord(
                            trip_id=trip_id,
                            holder_id=holder_id,
                            lease_token=new_token,
                            fencing_token=1,
                            acquired_at=now,
                            expires_at=expires_at,
                            ttl_seconds=ttl_seconds,
                            is_active=True,
                            metadata=dict(metadata or {}),
                        )

        return self._run(_async_acquire())

    def renew_lease(self, trip_id: str, lease_token: str, ttl_seconds: int = 30) -> AgentLeaseRecord:
        MemoryAgentLeaseBackend._validate_ttl(ttl_seconds)

        async def _async_renew():
            await self._ensure_table()
            from sqlalchemy import select
            from spine_api.models.agent_lease import AgentLeaseModel

            now = datetime.now(timezone.utc)
            maker = self._get_session_maker()
            async with maker() as session:
                async with session.begin():
                    stmt = select(AgentLeaseModel).where(AgentLeaseModel.trip_id == trip_id).with_for_update()
                    res = await session.execute(stmt)
                    row = res.scalar_one_or_none()

                    if not row or row.lease_token != lease_token or not row.is_active:
                        raise ValueError(f"No active lease found matching token for trip '{trip_id}'")

                    row_exp = self._as_utc(row.expires_at)
                    if now >= row_exp:
                        row.is_active = False
                        await session.flush()
                        raise ValueError(f"Lease for trip '{trip_id}' has expired and cannot be renewed")

                    row.expires_at = now + timedelta(seconds=ttl_seconds)
                    row.ttl_seconds = ttl_seconds
                    await session.flush()
                    return AgentLeaseRecord(
                        trip_id=trip_id,
                        holder_id=row.holder_id,
                        lease_token=row.lease_token,
                        fencing_token=row.fencing_token,
                        acquired_at=self._as_utc(row.acquired_at),
                        expires_at=self._as_utc(row.expires_at),
                        ttl_seconds=ttl_seconds,
                        is_active=True,
                        metadata=dict(row.lease_metadata or {}),
                    )

        return self._run(_async_renew())

    def release_lease(self, trip_id: str, lease_token: str) -> bool:
        async def _async_release():
            await self._ensure_table()
            from sqlalchemy import select
            from spine_api.models.agent_lease import AgentLeaseModel

            now = datetime.now(timezone.utc)
            maker = self._get_session_maker()
            async with maker() as session:
                async with session.begin():
                    stmt = select(AgentLeaseModel).where(AgentLeaseModel.trip_id == trip_id).with_for_update()
                    res = await session.execute(stmt)
                    row = res.scalar_one_or_none()
                    if not row or row.lease_token != lease_token:
                        return False
                    row_exp = self._as_utc(row.expires_at)
                    if now >= row_exp or not row.is_active:
                        row.is_active = False
                        return False
                    row.is_active = False
                    await session.flush()
                    return True

        return self._run(_async_release())

    def verify_fencing_token(self, trip_id: str, fencing_token: int) -> bool:
        async def _async_verify():
            await self._ensure_table()
            from sqlalchemy import select
            from spine_api.models.agent_lease import AgentLeaseModel

            now = datetime.now(timezone.utc)
            maker = self._get_session_maker()
            async with maker() as session:
                stmt = select(AgentLeaseModel).where(AgentLeaseModel.trip_id == trip_id)
                res = await session.execute(stmt)
                row = res.scalar_one_or_none()
                if not row or not row.is_active or now >= self._as_utc(row.expires_at):
                    return False
                return row.fencing_token == fencing_token and fencing_token > 0

        return self._run(_async_verify())

    def get_lease(self, trip_id: str) -> Optional[AgentLeaseRecord]:
        async def _async_get():
            await self._ensure_table()
            from sqlalchemy import select
            from spine_api.models.agent_lease import AgentLeaseModel

            now = datetime.now(timezone.utc)
            maker = self._get_session_maker()
            async with maker() as session:
                stmt = select(AgentLeaseModel).where(AgentLeaseModel.trip_id == trip_id)
                res = await session.execute(stmt)
                row = res.scalar_one_or_none()
                if not row:
                    return None
                is_active = row.is_active and now < self._as_utc(row.expires_at)
                return AgentLeaseRecord(
                    trip_id=trip_id,
                    holder_id=row.holder_id,
                    lease_token=row.lease_token,
                    fencing_token=row.fencing_token,
                    acquired_at=self._as_utc(row.acquired_at),
                    expires_at=self._as_utc(row.expires_at),
                    ttl_seconds=row.ttl_seconds,
                    is_active=is_active,
                    metadata=dict(row.lease_metadata or {}),
                )

        return self._run(_async_get())

    def sweep_stale_leases(self) -> int:
        async def _async_sweep():
            await self._ensure_table()
            from sqlalchemy import update
            from spine_api.models.agent_lease import AgentLeaseModel

            now = datetime.now(timezone.utc)
            maker = self._get_session_maker()
            async with maker() as session:
                async with session.begin():
                    stmt = (
                        update(AgentLeaseModel)
                        .where(AgentLeaseModel.is_active == True, AgentLeaseModel.expires_at <= now)
                        .values(is_active=False)
                    )
                    res = await session.execute(stmt)
                    return res.rowcount or 0

        return self._run(_async_sweep())

    def clear(self) -> None:
        async def _async_clear():
            await self._ensure_table()
            from sqlalchemy import delete
            from spine_api.models.agent_lease import AgentLeaseModel

            maker = self._get_session_maker()
            async with maker() as session:
                async with session.begin():
                    await session.execute(delete(AgentLeaseModel))

        return self._run(_async_clear())


class DurableAgentLeaseManager:
    """Facade delegating to configured lease backend (memory or durable SQL)."""

    _memory_backend = MemoryAgentLeaseBackend()
    _sql_backend: Optional[SqlAgentLeaseBackend] = None

    @classmethod
    def _get_backend(cls):
        mode = os.environ.get(AGENT_LEASE_BACKEND_ENV, "memory").strip().lower()
        if mode in ("sql", "postgres") or (mode == "auto" and os.environ.get("DATABASE_URL")):
            if cls._sql_backend is None:
                cls._sql_backend = SqlAgentLeaseBackend()
            return cls._sql_backend
        return cls._memory_backend

    @classmethod
    def acquire_lease(cls, trip_id: str, holder_id: str, ttl_seconds: int = 30, metadata: Optional[Dict[str, Any]] = None) -> AgentLeaseRecord:
        return cls._get_backend().acquire_lease(trip_id, holder_id, ttl_seconds, metadata)

    @classmethod
    def renew_lease(cls, trip_id: str, lease_token: str, ttl_seconds: int = 30) -> AgentLeaseRecord:
        return cls._get_backend().renew_lease(trip_id, lease_token, ttl_seconds)

    @classmethod
    def release_lease(cls, trip_id: str, lease_token: str) -> bool:
        return cls._get_backend().release_lease(trip_id, lease_token)

    @classmethod
    def verify_fencing_token(cls, trip_id: str, fencing_token: int) -> bool:
        return cls._get_backend().verify_fencing_token(trip_id, fencing_token)

    @classmethod
    def get_lease(cls, trip_id: str) -> Optional[AgentLeaseRecord]:
        return cls._get_backend().get_lease(trip_id)

    @classmethod
    def sweep_stale_leases(cls) -> int:
        return cls._get_backend().sweep_stale_leases()

    @classmethod
    def clear(cls) -> None:
        cls._memory_backend.clear()
        if cls._sql_backend:
            try:
                cls._sql_backend.clear()
            except Exception:
                pass
