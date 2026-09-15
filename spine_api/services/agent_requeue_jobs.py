"""
Durable SQL-backed job store and worker for recovery requeue.

Jobs are enqueued by SQLSpineJobQueueRequeuePort and processed by the
worker service.  The recovery agent itself only enqueues — it never
executes the spine pipeline inside the recovery loop.
"""

from __future__ import annotations

import json
import logging
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Optional
from uuid import uuid4

from sqlalchemy import text

from spine_api.persistence import _run_async_blocking, tripstore_session_maker

logger = logging.getLogger("agent_requeue_jobs")

JOB_STATUS_PENDING = "pending"
JOB_STATUS_RUNNING = "running"
JOB_STATUS_COMPLETED = "completed"
JOB_STATUS_FAILED = "failed"
JOB_STATUS_POISONED = "poisoned"

# Durable marker written by redact_poisoned().  Replay refuses jobs whose
# payload carries this key: the operator explicitly stripped the contents, so
# the original work context is gone and re-execution would act on nothing.
REDACTED_PAYLOAD_FLAG = "__redacted__"


class PoisonedJobRedactedError(ValueError):
    """Raised when replay is attempted on a job whose payload was redacted.

    Redaction is a deliberate operator destruction of the payload; replaying
    such a job is a contract violation, not a transient condition.
    """


@dataclass
class RequeueJob:
    id: str
    idempotency_key: str
    trip_id: str
    reason: str
    mode: str
    status: str
    attempts: int
    max_attempts: int
    payload: dict[str, Any]
    last_error: str
    created_at: str
    updated_at: str


@dataclass(frozen=True, slots=True)
class PoisonedJobSummary:
    """Bounded operator projection for a poisoned queue item.

    The durable payload is intentionally absent.  Inspection must not become
    an accidental credential/traveler-data export, and replay remains a
    separate authorization/execution contract.
    """

    job_id: str
    trip_id: str
    reason: str
    attempts: int
    max_attempts: int
    last_error: str
    created_at: str
    updated_at: str


class RequeueJobStore:
    """SQL-backed durable storage for recovery requeue jobs."""

    def __init__(self, lease_seconds: int = 60):
        self._lease_seconds = lease_seconds

    # ── Schema ────────────────────────────────────────────────────────────

    def ensure_schema(self) -> None:
        _run_async_blocking(self._ensure_schema())

    async def _ensure_schema(self) -> None:
        async with tripstore_session_maker() as session:
            async with session.begin():
                await session.execute(
                    text(
                        """
                        CREATE TABLE IF NOT EXISTS agent_requeue_jobs (
                            id VARCHAR(36) PRIMARY KEY,
                            idempotency_key VARCHAR(500) NOT NULL,
                            trip_id VARCHAR(255) NOT NULL,
                            reason TEXT NOT NULL DEFAULT '',
                            mode VARCHAR(40) NOT NULL DEFAULT 'sql_queue',
                            status VARCHAR(40) NOT NULL DEFAULT 'pending',
                            attempts INTEGER NOT NULL DEFAULT 0,
                            max_attempts INTEGER NOT NULL DEFAULT 3,
                            payload TEXT NOT NULL DEFAULT '{}',
                            last_error TEXT NOT NULL DEFAULT '',
                            leased_until TIMESTAMP WITH TIME ZONE NULL,
                            locked_by VARCHAR(120) NOT NULL DEFAULT '',
                            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
                            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
                        )
                        """
                    )
                )
                await session.execute(text("CREATE INDEX IF NOT EXISTS ix_agent_requeue_jobs_status ON agent_requeue_jobs (status)"))
                await session.execute(text("CREATE INDEX IF NOT EXISTS ix_agent_requeue_jobs_trip_id ON agent_requeue_jobs (trip_id)"))
                await session.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_agent_requeue_jobs_idempotency ON agent_requeue_jobs (idempotency_key)"))

    # ── Enqueue ───────────────────────────────────────────────────────────

    def enqueue(
        self,
        trip_id: str,
        idempotency_key: str,
        reason: str,
        payload: dict[str, Any] | None = None,
        max_attempts: int = 3,
    ) -> tuple[bool, str]:
        """Insert a pending job. Returns (accepted, job_id).

        Idempotent: same idempotency_key returns (False, existing_job_id)
        rather than inserting a duplicate.
        """
        return _run_async_blocking(
            self._enqueue(trip_id, idempotency_key, reason, payload or {}, max_attempts)
        )

    async def _enqueue(
        self,
        trip_id: str,
        idempotency_key: str,
        reason: str,
        payload: dict[str, Any],
        max_attempts: int,
    ) -> tuple[bool, str]:
        job_id = str(uuid4())
        now = datetime.now(timezone.utc)
        async with tripstore_session_maker() as session:
            async with session.begin():
                existing = await session.execute(
                    text("SELECT id FROM agent_requeue_jobs WHERE idempotency_key = :key"),
                    {"key": idempotency_key},
                )
                row = existing.mappings().first()
                if row is not None:
                    return False, row["id"]

                await session.execute(
                    text(
                        """
                        INSERT INTO agent_requeue_jobs
                            (id, idempotency_key, trip_id, reason, mode, status, attempts,
                             max_attempts, payload, last_error, leased_until, locked_by,
                             created_at, updated_at)
                        VALUES
                            (:id, :key, :trip_id, :reason, 'sql_queue', :status, 0,
                             :max_attempts, :payload, '', NULL, '',
                             :now, :now)
                        """
                    ),
                    {
                        "id": job_id,
                        "key": idempotency_key,
                        "trip_id": trip_id,
                        "reason": reason,
                        "status": JOB_STATUS_PENDING,
                        "max_attempts": max_attempts,
                        "payload": json.dumps(payload),
                        "now": now,
                    },
                )
                return True, job_id

    # ── Lease ─────────────────────────────────────────────────────────────

    def lease_pending(self, owner: str = "requeue_worker") -> Optional[RequeueJob]:
        """Lease one pending job for processing."""
        return _run_async_blocking(self._lease_pending_async(owner))

    async def _lease_pending_async(self, owner: str) -> Optional[RequeueJob]:
        now = datetime.now(timezone.utc)
        async with tripstore_session_maker() as session:
            async with session.begin():
                row = await session.execute(
                    text(
                        """
                        SELECT id, idempotency_key, trip_id, reason, mode, status,
                               attempts, max_attempts, payload, last_error,
                               created_at, updated_at
                        FROM agent_requeue_jobs
                        WHERE status = :pending
                           OR (status = :failed AND attempts < max_attempts
                               AND (leased_until IS NULL OR leased_until <= :now))
                        ORDER BY created_at ASC
                        LIMIT 1
                        FOR UPDATE SKIP LOCKED
                        """
                    ),
                    {
                        "pending": JOB_STATUS_PENDING,
                        "failed": JOB_STATUS_FAILED,
                        "now": now,
                    },
                )
                row_data = dict(row.mappings().first() or {})

                if not row_data:
                    return None

                await session.execute(
                    text(
                        """
                        UPDATE agent_requeue_jobs
                        SET status = :status,
                            locked_by = :owner,
                            leased_until = :leased_until,
                            updated_at = :now
                        WHERE id = :id
                        """
                    ),
                    {
                        "id": row_data["id"],
                        "status": JOB_STATUS_RUNNING,
                        "owner": owner,
                        "leased_until": now + timedelta(seconds=self._lease_seconds),
                        "now": now,
                    },
                )
                row_data["status"] = JOB_STATUS_RUNNING
                return _job_from_row(row_data)

    def lease_by_id(self, job_id: str, owner: str = "requeue_worker") -> Optional[RequeueJob]:
        """Lease a specific job."""
        return _run_async_blocking(self._lease_by_id(job_id, owner))

    async def _lease_by_id(self, job_id: str, owner: str) -> Optional[RequeueJob]:
        now = datetime.now(timezone.utc)
        async with tripstore_session_maker() as session:
            async with session.begin():
                result = await session.execute(
                    text(
                        """
                        SELECT id, idempotency_key, trip_id, reason, mode, status,
                               attempts, max_attempts, payload, last_error,
                               created_at, updated_at
                        FROM agent_requeue_jobs
                        WHERE id = :id
                        FOR UPDATE
                        """
                    ),
                    {"id": job_id},
                )
                row_data = dict(result.mappings().first() or {})

                if not row_data:
                    return None

                await session.execute(
                    text(
                        """
                        UPDATE agent_requeue_jobs
                        SET status = :status, locked_by = :owner,
                            leased_until = :leased_until, updated_at = :now
                        WHERE id = :id
                        """
                    ),
                    {
                        "id": row_data["id"],
                        "status": JOB_STATUS_RUNNING,
                        "owner": owner,
                        "leased_until": now + timedelta(seconds=self._lease_seconds),
                        "now": now,
                    },
                )
                row_data["status"] = JOB_STATUS_RUNNING
                return _job_from_row(row_data)

    # ── Complete / Fail ───────────────────────────────────────────────────

    def complete(self, job_id: str, reason: str = "") -> None:
        _run_async_blocking(self._terminal(job_id, JOB_STATUS_COMPLETED, reason))

    def fail(self, job_id: str, error: str, poison: bool = False) -> None:
        status = JOB_STATUS_POISONED if poison else JOB_STATUS_FAILED
        info = _run_async_blocking(self._terminal(job_id, status, error))
        if status == JOB_STATUS_POISONED and info is not None:
            _emit_poisoned_side_effects(job_id=job_id, error=error, info=info)

    async def _terminal(self, job_id: str, status: str, error: str) -> Optional[dict[str, Any]]:
        """Write the terminal state.  Returns row info for post-commit side
        effects; poison alerting/audit/mirroring run in the sync caller so the
        audit bridge is never nested inside the SQL bridge loop."""
        now = datetime.now(timezone.utc)
        # Retryable failed jobs get a backoff window equal to lease_seconds so they
        # are not immediately re-leased by the same worker pass.  Terminal states
        # (completed, poisoned) clear leased_until since those jobs are never leased again.
        next_leased_until = (
            now + timedelta(seconds=self._lease_seconds)
            if status == JOB_STATUS_FAILED
            else None
        )
        async with tripstore_session_maker() as session:
            async with session.begin():
                result = await session.execute(
                    text("SELECT attempts, trip_id, payload FROM agent_requeue_jobs WHERE id = :id FOR UPDATE"),
                    {"id": job_id},
                )
                row = result.mappings().first()
                if row is None:
                    return None
                attempts = int(row["attempts"]) + 1
                await session.execute(
                    text(
                        """
                        UPDATE agent_requeue_jobs
                        SET status = :status, attempts = :attempts,
                            last_error = :error, locked_by = '',
                            leased_until = :leased_until, updated_at = :now
                        WHERE id = :id
                        """
                    ),
                    {
                        "id": job_id,
                        "status": status,
                        "attempts": attempts,
                        "error": error,
                        "leased_until": next_leased_until,
                        "now": now,
                    },
                )
        return {
            "trip_id": str(row["trip_id"] or ""),
            "attempts": attempts,
            "payload": str(row.get("payload") or "{}"),
        }

    # ── Snapshot ──────────────────────────────────────────────────────────

    def snapshot(self) -> dict[str, Any]:
        return _run_async_blocking(self._snapshot())

    async def _snapshot(self) -> dict[str, Any]:
        async with tripstore_session_maker() as session:
            rows = (await session.execute(
                text(
                    """
                    SELECT status, COUNT(*) as cnt
                    FROM agent_requeue_jobs
                    GROUP BY status
                    """
                )
            )).mappings().all()
            poison_row = (await session.execute(
                text(
                    """
                    SELECT COUNT(*) AS cnt, MIN(updated_at) AS oldest
                    FROM agent_requeue_jobs
                    WHERE status = :poisoned
                    """
                ),
                {"poisoned": JOB_STATUS_POISONED},
            )).mappings().first()
        counts: dict[str, int] = {}
        for row in rows:
            counts[row["status"]] = row["cnt"]
        poisoned_count = int(poison_row["cnt"]) if poison_row else 0
        oldest = poison_row["oldest"] if poison_row else None
        if oldest is not None:
            if isinstance(oldest, str):
                try:
                    oldest = datetime.fromisoformat(oldest)
                except ValueError:
                    oldest = None
            if oldest is not None and oldest.tzinfo is None:
                oldest = oldest.replace(tzinfo=timezone.utc)
        oldest_age_seconds = (
            max(0.0, (datetime.now(timezone.utc) - oldest).total_seconds())
            if oldest is not None
            else 0.0
        )
        return {
            "backend": "sql",
            "total": sum(counts.values()),
            "counts": counts,
            # FND-0224: poison must be visible in every operational snapshot,
            # not only after an operator thinks to ask for the DLQ list.
            "poisoned_count": poisoned_count,
            "oldest_poisoned_age_seconds": round(oldest_age_seconds, 1),
        }

    def trip_stats(self, trip_id: str) -> dict[str, Any]:
        """Durable per-trip retry/poison introspection for recovery decisions."""
        return _run_async_blocking(self._trip_stats(trip_id))

    async def _trip_stats(self, trip_id: str) -> dict[str, Any]:
        async with tripstore_session_maker() as session:
            rows = (await session.execute(
                text(
                    """
                    SELECT status, attempts, max_attempts
                    FROM agent_requeue_jobs
                    WHERE trip_id = :trip_id
                    ORDER BY updated_at DESC
                    """
                ),
                {"trip_id": trip_id},
            )).mappings().all()
        if not rows:
            return {"attempts": 0, "poisoned": False, "active": False, "max_attempts": 0}
        attempts = max(int(row.get("attempts") or 0) for row in rows)
        poisoned = any(str(row.get("status")) == JOB_STATUS_POISONED for row in rows)
        active = any(str(row.get("status")) in {JOB_STATUS_PENDING, JOB_STATUS_RUNNING, JOB_STATUS_FAILED} for row in rows)
        max_attempts = max(int(row.get("max_attempts") or 0) for row in rows)
        return {
            "attempts": attempts,
            "poisoned": poisoned,
            "active": active,
            "max_attempts": max_attempts,
        }

    def list_poisoned(
        self, *, limit: int = 50, offset: int = 0, trip_id: str | None = None
    ) -> list[PoisonedJobSummary]:
        """Return a deterministic, redacted page of poisoned jobs.

        This is intentionally a service-level inspection primitive.  The
        queue has no agency_id, so an authenticated tenant-facing route must
        not be inferred from this method until an ownership contract exists.
        """
        if not 1 <= limit <= 100:
            raise ValueError("limit must be between 1 and 100")
        if offset < 0:
            raise ValueError("offset must be non-negative")
        return _run_async_blocking(self._list_poisoned(limit, offset, trip_id))

    async def _list_poisoned(
        self, limit: int, offset: int, trip_id: str | None
    ) -> list[PoisonedJobSummary]:
        filters = "status = :status"
        params: dict[str, Any] = {
            "status": JOB_STATUS_POISONED,
            "limit": limit,
            "offset": offset,
        }
        if trip_id is not None:
            filters += " AND trip_id = :trip_id"
            params["trip_id"] = trip_id
        async with tripstore_session_maker() as session:
            result = await session.execute(
                text(
                    f"""
                    SELECT id, trip_id, reason, attempts, max_attempts,
                           last_error, created_at, updated_at
                    FROM agent_requeue_jobs
                    WHERE {filters}
                    ORDER BY updated_at DESC, id DESC
                    LIMIT :limit OFFSET :offset
                    """
                ),
                params,
            )
            rows = result.mappings().all()
        return [
            PoisonedJobSummary(
                job_id=str(row["id"]),
                trip_id=str(row["trip_id"]),
                reason=str(row["reason"] or ""),
                attempts=int(row["attempts"] or 0),
                max_attempts=int(row["max_attempts"] or 0),
                last_error=str(row["last_error"] or "")[:2048],
                created_at=str(row["created_at"]),
                updated_at=str(row["updated_at"]),
            )
            for row in rows
        ]

    def inspect_poisoned(self, job_id: str) -> Optional[dict[str, Any]]:
        """Return a redacted detail view of a poisoned job, or None if not found/not poisoned."""
        return _run_async_blocking(self._inspect_poisoned(job_id))

    async def _inspect_poisoned(self, job_id: str) -> Optional[dict[str, Any]]:
        from src.agents.dlq_inspector import DLQInspector

        async with tripstore_session_maker() as session:
            result = await session.execute(
                text(
                    """
                    SELECT id, trip_id, reason, mode, status, attempts, max_attempts,
                           payload, last_error, created_at, updated_at
                    FROM agent_requeue_jobs
                    WHERE id = :id AND status = :status
                    """
                ),
                {"id": job_id, "status": JOB_STATUS_POISONED},
            )
            row = result.mappings().first()
            if not row:
                return None
            raw_payload = _safe_json_loads(str(row.get("payload") or "{}"))
            redacted_payload = DLQInspector._sanitize_payload(raw_payload)
            return {
                "job_id": str(row["id"]),
                "trip_id": str(row["trip_id"]),
                "reason": str(row["reason"]),
                "mode": str(row["mode"]),
                "status": str(row["status"]),
                "attempts": int(row["attempts"]),
                "max_attempts": int(row["max_attempts"]),
                "redacted_payload": redacted_payload,
                "last_error": str(row["last_error"]),
                "created_at": str(row["created_at"]),
                "updated_at": str(row["updated_at"]),
            }

    def replay_poisoned(
        self, job_id: str, patched_payload: Optional[dict[str, Any]] = None
    ) -> bool:
        """Unpoison and re-queue a job as a fresh pending attempt.

        The attempt counter is incremented (not reset) so poison history stays
        observable downstream.  Raises PoisonedJobRedactedError when the job's
        payload was redacted by an operator: the work context is gone and
        replay would silently execute an empty job.
        """
        info = _run_async_blocking(self._replay_poisoned(job_id, patched_payload))
        if info is None:
            return False
        # Audit + DLQ projection run in the sync caller so the audit bridge is
        # never nested inside the SQL bridge loop.
        _emit_replayed_side_effects(job_id, info)
        return True
    async def _replay_poisoned(
        self, job_id: str, patched_payload: Optional[dict[str, Any]]
    ) -> Optional[dict[str, Any]]:
        now = datetime.now(timezone.utc)
        async with tripstore_session_maker() as session:
            async with session.begin():
                result = await session.execute(
                    text("SELECT id, status, attempts, trip_id, payload FROM agent_requeue_jobs WHERE id = :id FOR UPDATE"),
                    {"id": job_id},
                )
                row = result.mappings().first()
                if not row or row["status"] != JOB_STATUS_POISONED:
                    return None

                raw_payload = str(row.get("payload") or "{}")
                existing_payload = _safe_json_loads(raw_payload)
                if isinstance(existing_payload, dict) and existing_payload.get(REDACTED_PAYLOAD_FLAG):
                    raise PoisonedJobRedactedError(
                        f"Job {job_id} was redacted; its payload is gone and cannot be replayed"
                    )

                new_payload = (
                    json.dumps(patched_payload)
                    if patched_payload is not None
                    else raw_payload
                )
                attempts = int(row.get("attempts") or 0) + 1

                await session.execute(
                    text(
                        """
                        UPDATE agent_requeue_jobs
                        SET status = :status,
                            attempts = :attempts,
                            last_error = '',
                            locked_by = '',
                            leased_until = NULL,
                            payload = :payload,
                            updated_at = :now
                        WHERE id = :id
                        """
                    ),
                    {
                        "id": job_id,
                        "status": JOB_STATUS_PENDING,
                        "attempts": attempts,
                        "payload": new_payload,
                        "now": now,
                    },
                )
        return {
            "trip_id": str(row["trip_id"] or ""),
            "attempts": attempts,
            "payload_patched": patched_payload is not None,
        }

    def redact_poisoned(self, job_id: str) -> bool:
        """Strip a poisoned job's payload contents, preserving the row.

        The durable row (id, trip_id, reason, error, counters, timestamps)
        survives so the operator audit trail stays intact; only the payload —
        which may carry traveler PII or credentials — is replaced with a
        durable redaction marker that replay refuses.
        """
        info = _run_async_blocking(self._redact_poisoned(job_id))
        if info is None:
            return False
        # Audit + DLQ projection run in the sync caller (bridge nesting).
        _emit_redacted_side_effects(job_id, info)
        return True

    async def _redact_poisoned(self, job_id: str) -> Optional[dict[str, Any]]:
        now = datetime.now(timezone.utc)
        async with tripstore_session_maker() as session:
            async with session.begin():
                result = await session.execute(
                    text("SELECT id, status, trip_id FROM agent_requeue_jobs WHERE id = :id FOR UPDATE"),
                    {"id": job_id},
                )
                row = result.mappings().first()
                if not row or row["status"] != JOB_STATUS_POISONED:
                    return None
                await session.execute(
                    text(
                        """
                        UPDATE agent_requeue_jobs
                        SET payload = :payload, updated_at = :now
                        WHERE id = :id
                        """
                    ),
                    {
                        "id": job_id,
                        "payload": json.dumps(
                            {REDACTED_PAYLOAD_FLAG: True, "redacted_at": now.isoformat()}
                        ),
                        "now": now,
                    },
                )
        return {"trip_id": str(row["trip_id"] or "")}

    def reclaim_stale_running(self, *, grace_seconds: int = 0) -> int:
        """Requeue RUNNING jobs whose lease expired (dead worker / lost lease).

        A RUNNING row with an expired lease is an orphan: no worker owns it and
        nothing will ever complete or fail it.  Returning it to pending reuses
        the store's existing automatic re-lease path (the same one already
        applied to retryable failed jobs); poison is never auto-replayed here.
        Returns the number of reclaimed rows.
        """
        return _run_async_blocking(self._reclaim_stale_running(grace_seconds))

    async def _reclaim_stale_running(self, grace_seconds: int) -> int:
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(seconds=max(0, grace_seconds))
        async with tripstore_session_maker() as session:
            async with session.begin():
                result = await session.execute(
                    text(
                        """
                        UPDATE agent_requeue_jobs
                        SET status = :pending, locked_by = '', leased_until = NULL,
                            updated_at = :now
                        WHERE status = :running AND leased_until IS NOT NULL
                          AND leased_until <= :cutoff
                        """
                    ),
                    {
                        "pending": JOB_STATUS_PENDING,
                        "running": JOB_STATUS_RUNNING,
                        "cutoff": cutoff,
                        "now": now,
                    },
                )
                reclaimed = int(result.rowcount or 0)
        if reclaimed:
            logger.warning(
                "requeue_stale_leases_reclaimed count=%d — orphaned RUNNING jobs returned to pending",
                reclaimed,
            )
        return reclaimed

    def dead_trips(self, *, limit: int = 100) -> list[dict[str, Any]]:
        """Return trips whose durable work is dead (poisoned), bounded page.

        Poison means the pipeline already exhausted its retry ladder for these
        jobs; recovery never fires for them because the requeue worker never
        leases terminal states.  This surface lets the recovery loop log+count
        dead trips each pass and operators replay them deliberately.
        """
        if not 1 <= limit <= 500:
            raise ValueError("limit must be between 1 and 500")
        return _run_async_blocking(self._dead_trips(limit))

    async def _dead_trips(self, limit: int) -> list[dict[str, Any]]:
        async with tripstore_session_maker() as session:
            rows = (await session.execute(
                text(
                    """
                    SELECT trip_id, COUNT(*) AS poisoned_jobs,
                           MAX(attempts) AS max_attempts_seen
                    FROM agent_requeue_jobs
                    WHERE status = :poisoned
                    GROUP BY trip_id
                    ORDER BY MAX(updated_at) DESC
                    LIMIT :limit
                    """
                ),
                {"poisoned": JOB_STATUS_POISONED, "limit": limit},
            )).mappings().all()
        return [
            {
                "trip_id": str(row["trip_id"]),
                "poisoned_jobs": int(row["poisoned_jobs"]),
                "max_attempts": int(row["max_attempts_seen"] or 0),
            }
            for row in rows
        ]


# ── Post-commit side effects (FND-0224) ─────────────────────────────────
#
# These run in the sync caller of fail()/replay_poisoned()/redact_poisoned()
# — never on the SQL bridge loop — so AuditStore's canonical bridge write
# path stays usable.  Every effect is defensive: an alerting, audit, or DLQ
# mirror failure must never fail the data operation it observes.


def _emit_poisoned_side_effects(*, job_id: str, error: str, info: dict[str, Any]) -> None:
    """A transition INTO poisoned must be observable (FND-0224)."""
    trip_id = str(info.get("trip_id") or "")
    attempts = int(info.get("attempts") or 0)
    # Paging-style structured log event, same shape as ADR-008's route_health
    # alert emission: stable dedup signature + bounded context.
    logger.warning(
        "requeue_job_poisoned job_id=%s trip_id=%s attempts=%d signature=%s error=%.512s",
        job_id,
        trip_id,
        attempts,
        f"requeue_poison:{job_id}",
        error,
    )
    _audit_event(
        event_type="requeue_job_poisoned",
        trip_id=trip_id,
        details={
            "job_id": job_id,
            "trip_id": trip_id,
            "attempts": attempts,
            "alert_signature": f"requeue_poison:{job_id}",
            "error": error[:2048],
        },
    )
    try:
        from src.agents.dlq_inspector import DLQInspector
        payload_dict = _safe_json_loads(str(info.get("payload") or "{}"))
        DLQInspector.record_poisoned_job(
            job_id=job_id,
            agent_name="agent_requeue_jobs",
            trip_id=trip_id,
            error_message=error,
            stack_trace="",
            failed_payload=payload_dict,
            retry_count=attempts,
        )
    except Exception:
        logger.exception("Failed to mirror poisoned job to DLQInspector: %s", job_id)


def _emit_replayed_side_effects(job_id: str, info: dict[str, Any]) -> None:
    from src.agents.dlq_inspector import DLQInspector

    trip_id = str(info.get("trip_id") or "")
    attempts = int(info.get("attempts") or 0)
    _audit_event(
        event_type="requeue_job_replayed",
        trip_id=trip_id,
        details={
            "job_id": job_id,
            "trip_id": trip_id,
            "replay_attempt": attempts,
            "payload_patched": bool(info.get("payload_patched")),
        },
    )
    logger.info(
        "requeue_job_replayed job_id=%s trip_id=%s replay_attempt=%d", job_id, trip_id, attempts
    )
    # Synchronize with in-memory DLQ projection if tracked (defensive).
    try:
        if DLQInspector.get_job(job_id) is not None:
            DLQInspector.replay_job(job_id)
    except Exception:
        logger.exception("Failed to mirror replay to DLQInspector: %s", job_id)


def _emit_redacted_side_effects(job_id: str, info: dict[str, Any]) -> None:
    from src.agents.dlq_inspector import DLQInspector

    trip_id = str(info.get("trip_id") or "")
    # Mirror the resolution into the in-memory DLQ projection (defensive:
    # the durable redaction above is the source of truth).
    try:
        if DLQInspector.get_job(job_id) is not None:
            DLQInspector.redact_job(job_id, reason="payload stripped by operator")
    except Exception:
        logger.exception("Failed to mirror redaction to DLQInspector: %s", job_id)
    _audit_event(
        event_type="requeue_job_redacted",
        trip_id=trip_id,
        details={
            "job_id": job_id,
            "trip_id": trip_id,
            "note": "payload contents stripped; row and reason preserved",
        },
    )
    logger.info("requeue_job_redacted job_id=%s trip_id=%s", job_id, trip_id)


# ── Worker ──────────────────────────────────────────────────────────────


class RequeueWorker:
    """Processes pending/retryable requeue jobs outside the recovery loop.

    The recovery agent enqueues jobs.  The worker executes them.  This
    keeps the recovery loop fast and the spine execution path decoupled.
    """

    def __init__(
        self,
        job_store: RequeueJobStore,
        spine_runner: Optional[Callable[..., Any]] = None,
        trip_repo: Any = None,
    ):
        self._job_store = job_store
        self._spine_runner = spine_runner
        self._trip_repo = trip_repo

    def run_once(self, max_jobs: int = 5) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for _ in range(max_jobs):
            job = self._job_store.lease_pending()
            if job is None:
                break
            result = self._execute_job(job)
            results.append(result)
        return results

    def _execute_job(self, job: RequeueJob) -> dict[str, Any]:
        if self._spine_runner is None or self._trip_repo is None:
            self._job_store.fail(job.id, "Worker not configured with spine_runner or trip_repo", poison=True)
            return {"job_id": job.id, "trip_id": job.trip_id, "status": "poisoned"}

        trip_record = self._lookup_trip(job.trip_id)
        if trip_record is None:
            self._job_store.fail(job.id, f"Trip {job.trip_id} not found", poison=True)
            return {"job_id": job.id, "trip_id": job.trip_id, "status": "poisoned"}

        raw_input = trip_record.get("raw_input") if isinstance(trip_record, dict) else {}
        if not raw_input or not isinstance(raw_input, dict):
            self._job_store.fail(job.id, f"Trip {job.trip_id} has no raw_input data; cannot reconstruct pipeline context.", poison=True)
            return {"job_id": job.id, "trip_id": job.trip_id, "status": "poisoned", "error": "unsupported_missing_context"}

        stage = str(trip_record.get("stage") or trip_record.get("status") or "discovery")
        try:
            self._spine_runner(envelopes=[raw_input], stage=stage)
            self._job_store.complete(job.id, reason=job.reason)
            return {"job_id": job.id, "trip_id": job.trip_id, "status": "completed"}
        except Exception as exc:
            err = str(exc)
            poison = job.attempts + 1 >= job.max_attempts
            self._job_store.fail(job.id, err, poison=poison)
            return {"job_id": job.id, "trip_id": job.trip_id, "status": "poisoned" if poison else "failed", "error": err}

    def _lookup_trip(self, trip_id: str) -> Optional[dict[str, Any]]:
        if self._trip_repo is None:
            return None
        try:
            for t in self._trip_repo.list_active():
                tid = str(t.get("id") if isinstance(t, dict) else getattr(t, "id", ""))
                if tid == trip_id:
                    return t if isinstance(t, dict) else None
        except Exception:
            logger.exception("Failed to look up trip %s", trip_id)
        return None


class RequeueWorkerService:
    """Lifecycle-managed background runner for durable requeue jobs."""

    def __init__(self, worker: RequeueWorker, interval_seconds: int = 5, max_jobs_per_pass: int = 5):
        self._worker = worker
        self._interval_seconds = interval_seconds
        self._max_jobs_per_pass = max_jobs_per_pass
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._last_results: list[dict[str, Any]] = []
        self._last_dead_trips: list[dict[str, Any]] = []
        self._last_reclaimed: int = 0

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        if self._thread is not None:
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="RequeueWorkerService")
        self._thread.start()

    def stop(self) -> None:
        if self._thread is None:
            return
        self._stop_event.set()
        self._thread.join(timeout=10)
        self._thread = None

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                self._last_results = self._worker.run_once(max_jobs=self._max_jobs_per_pass)
            except Exception:
                logger.exception("RequeueWorkerService: unhandled worker pass failure")
            try:
                self._maintenance_pass()
            except Exception:
                logger.exception("RequeueWorkerService: unhandled maintenance pass failure")
            self._stop_event.wait(timeout=self._interval_seconds)

    def _maintenance_pass(self) -> None:
        """FND-0224 dead-trip recovery pass (log + count only).

        Two cheap, bounded operations per cycle:
        1. Reclaim RUNNING rows with expired leases (worker crash orphans) —
           reuses the existing automatic re-lease path for unexecuted work.
        2. Detect trips whose durable work is dead (poisoned) and surface them
           via log + count.  Poison is deliberately NOT auto-replayed: the
           repo's recovery precedent escalates poisoned trips for operator
           review (deterministic failures would loop on auto-replay), and the
           admin replay endpoint on the agent-runtime router is the
           operator-triggered path.
        """
        job_store = self._worker._job_store
        self._last_reclaimed = job_store.reclaim_stale_running()
        self._last_dead_trips = job_store.dead_trips(limit=100)
        if self._last_dead_trips:
            trip_ids = ", ".join(entry["trip_id"] for entry in self._last_dead_trips[:10])
            logger.warning(
                "requeue_dead_trips_detected count=%d sample=[%s] — operator replay required "
                "(poison is not auto-replayed)",
                len(self._last_dead_trips),
                trip_ids,
            )

    def health(self) -> dict[str, Any]:
        return {
            "running": self.is_running,
            "interval_seconds": self._interval_seconds,
            "max_jobs_per_pass": self._max_jobs_per_pass,
            "last_results_count": len(self._last_results),
            "dead_trips": {
                "count": len(self._last_dead_trips),
                "sample": self._last_dead_trips[:10],
            },
            "stale_leases_reclaimed_last_pass": self._last_reclaimed,
        }


def _job_from_row(row: dict[str, Any]) -> RequeueJob:
    return RequeueJob(
        id=str(row["id"]),
        idempotency_key=str(row["idempotency_key"]),
        trip_id=str(row["trip_id"]),
        reason=str(row["reason"]),
        mode=str(row.get("mode", "sql_queue")),
        status=str(row["status"]),
        attempts=int(row["attempts"]),
        max_attempts=int(row["max_attempts"]),
        payload=_safe_json_loads(str(row.get("payload", "{}"))),
        last_error=str(row.get("last_error", "")),
        created_at=str(row.get("created_at", "")),
        updated_at=str(row.get("updated_at", "")),
    )


def _safe_json_loads(value: str) -> dict[str, Any]:
    try:
        return json.loads(value) if value else {}
    except (json.JSONDecodeError, TypeError):
        return {}


def _audit_event(event_type: str, trip_id: str, details: dict[str, Any]) -> None:
    """Persist a canonical audit event via AuditStore.log_event.

    Mirrors the recovery-agent adapter contract (event_type/trip_id/details).
    Degrades silently to a log line: poison handling must never fail because
    the audit sink is unavailable (AuditStore itself already falls back to its
    legacy file chain when SQL is unreachable).
    """
    try:
        from spine_api.persistence import AuditStore

        AuditStore.log_event(event_type=event_type, user_id="agent_requeue_jobs", details={"trip_id": trip_id, **details})
    except Exception:
        logger.exception("Failed to persist %s audit event for job %s", event_type, details.get("job_id"))
