"""Durable SQL coordinator for backend product-agent work leases."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from spine_api.persistence import _run_async_blocking, tripstore_session_maker
from src.agents.runtime import RetryPolicy, WorkItem, WorkStatus


class SQLWorkCoordinator:
    """SQL-backed single-owner lease and durable idempotency boundary."""

    def __init__(self, lease_seconds: int = 60):
        self._lease_seconds = lease_seconds

    def ensure_schema(self) -> None:
        """Create the lease table when migrations have not yet run locally."""
        _run_async_blocking(self._ensure_schema())

    async def _ensure_schema(self) -> None:
        async with tripstore_session_maker() as session:
            async with session.begin():
                await session.execute(
                    text(
                        """
                        CREATE TABLE IF NOT EXISTS agent_work_leases (
                            idempotency_key VARCHAR(500) PRIMARY KEY,
                            agent_name VARCHAR(120) NOT NULL,
                            trip_id VARCHAR(255) NOT NULL,
                            action VARCHAR(120) NOT NULL,
                            owner VARCHAR(120) NOT NULL,
                            status VARCHAR(40) NOT NULL,
                            attempts INTEGER NOT NULL DEFAULT 0,
                            leased_until TIMESTAMP WITH TIME ZONE NULL,
                            last_reason TEXT NOT NULL DEFAULT '',
                            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
                            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
                        )
                        """
                    )
                )
                await session.execute(text("CREATE INDEX IF NOT EXISTS ix_agent_work_leases_agent_name ON agent_work_leases (agent_name)"))
                await session.execute(text("CREATE INDEX IF NOT EXISTS ix_agent_work_leases_trip_id ON agent_work_leases (trip_id)"))
                await session.execute(text("CREATE INDEX IF NOT EXISTS ix_agent_work_leases_status ON agent_work_leases (status)"))
                await session.execute(text("CREATE INDEX IF NOT EXISTS ix_agent_work_leases_leased_until ON agent_work_leases (leased_until)"))

    def acquire(self, work_item: WorkItem, owner: str, retry_policy: RetryPolicy) -> tuple[bool, str, int]:
        return _run_async_blocking(self._acquire(work_item, owner, retry_policy))

    async def _acquire(self, work_item: WorkItem, owner: str, retry_policy: RetryPolicy) -> tuple[bool, str, int]:
        now = datetime.now(timezone.utc)
        async with tripstore_session_maker() as session:
            async with session.begin():
                row = await self._locked_row(session, work_item.idempotency_key)
                if row is None:
                    try:
                        await session.execute(
                            text(
                                """
                                INSERT INTO agent_work_leases
                                  (idempotency_key, agent_name, trip_id, action, owner, status, attempts, leased_until, last_reason, created_at, updated_at)
                                VALUES
                                  (:key, :agent_name, :trip_id, :action, :owner, :status, :attempts, :leased_until, '', :now, :now)
                                """
                            ),
                            {
                                "key": work_item.idempotency_key,
                                "agent_name": work_item.agent_name,
                                "trip_id": work_item.trip_id,
                                "action": work_item.action,
                                "owner": owner,
                                "status": WorkStatus.RUNNING.value,
                                "attempts": 1,
                                "leased_until": now + timedelta(seconds=self._lease_seconds),
                                "now": now,
                            },
                        )
                    except IntegrityError:
                        await session.rollback()
                        return await self._acquire(work_item, owner, retry_policy)
                    return True, "acquired", 1

                status = str(row["status"])
                attempts = int(row["attempts"] or 0)
                leased_until = row["leased_until"]
                if status == WorkStatus.COMPLETED.value:
                    return False, "idempotent_reentry_completed", 0
                if status == WorkStatus.POISONED.value:
                    return False, "poisoned_fail_closed", 0
                if status == WorkStatus.RUNNING.value and leased_until and leased_until > now:
                    return False, f"owned_by:{row['owner']}", attempts

                next_attempt = attempts + 1
                if next_attempt > retry_policy.max_attempts:
                    await self._update(session, work_item, owner, WorkStatus.POISONED, attempts, now, "retry_policy_exhausted", now)
                    return False, "retry_policy_exhausted", attempts

                await self._update(
                    session,
                    work_item,
                    owner,
                    WorkStatus.RUNNING,
                    next_attempt,
                    now + timedelta(seconds=self._lease_seconds),
                    "",
                    now,
                )
                return True, "acquired", next_attempt

    def complete(self, work_item: WorkItem, reason: str = "") -> None:
        _run_async_blocking(self._terminal_update(work_item, WorkStatus.COMPLETED, reason))

    def fail(self, work_item: WorkItem, status: WorkStatus, reason: str) -> None:
        _run_async_blocking(self._terminal_update(work_item, status, reason))

    async def _terminal_update(self, work_item: WorkItem, status: WorkStatus, reason: str) -> None:
        now = datetime.now(timezone.utc)
        async with tripstore_session_maker() as session:
            async with session.begin():
                row = await self._locked_row(session, work_item.idempotency_key)
                attempts = int(row["attempts"] or 1) if row else 1
                await self._update(session, work_item, work_item.agent_name, status, attempts, now, reason, now)

    def snapshot(self) -> dict[str, Any]:
        return _run_async_blocking(self._snapshot())

    async def _snapshot(self) -> dict[str, Any]:
        async with tripstore_session_maker() as session:
            result = await session.execute(
                text(
                    """
                    SELECT idempotency_key, owner, status, attempts, last_reason
                    FROM agent_work_leases
                    ORDER BY updated_at DESC
                    LIMIT 200
                    """
                )
            )
            rows = result.mappings().all()
        leases = {
            row["idempotency_key"]: {
                "owner": row["owner"],
                "status": row["status"],
                "attempts": row["attempts"],
                "last_reason": row["last_reason"],
            }
            for row in rows
        }
        return {
            "backend": "sql",
            "completed": sum(1 for row in rows if row["status"] == WorkStatus.COMPLETED.value),
            "poisoned": sum(1 for row in rows if row["status"] == WorkStatus.POISONED.value),
            "leases": leases,
        }

    async def _locked_row(self, session: Any, key: str) -> Any:
        result = await session.execute(
            text(
                """
                SELECT idempotency_key, owner, status, attempts, leased_until, last_reason
                FROM agent_work_leases
                WHERE idempotency_key = :key
                FOR UPDATE
                """
            ),
            {"key": key},
        )
        return result.mappings().first()

    async def _update(
        self,
        session: Any,
        work_item: WorkItem,
        owner: str,
        status: WorkStatus,
        attempts: int,
        leased_until: datetime,
        reason: str,
        now: datetime,
    ) -> None:
        await session.execute(
            text(
                """
                UPDATE agent_work_leases
                SET owner = :owner,
                    status = :status,
                    attempts = :attempts,
                    leased_until = :leased_until,
                    last_reason = :reason,
                    agent_name = :agent_name,
                    trip_id = :trip_id,
                    action = :action,
                    updated_at = :now
                WHERE idempotency_key = :key
                """
            ),
            {
                "key": work_item.idempotency_key,
                "owner": owner,
                "status": status.value,
                "attempts": attempts,
                "leased_until": leased_until,
                "reason": reason,
                "agent_name": work_item.agent_name,
                "trip_id": work_item.trip_id,
                "action": work_item.action,
                "now": now,
            },
        )
