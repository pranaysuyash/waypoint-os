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
        _run_async_blocking(self._terminal(job_id, status, error))

    async def _terminal(self, job_id: str, status: str, error: str) -> None:
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
                    text("SELECT attempts FROM agent_requeue_jobs WHERE id = :id FOR UPDATE"),
                    {"id": job_id},
                )
                row = result.mappings().first()
                if row is None:
                    return
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
        counts: dict[str, int] = {}
        for row in rows:
            counts[row["status"]] = row["cnt"]
        return {
            "backend": "sql",
            "total": sum(counts.values()),
            "counts": counts,
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
            self._stop_event.wait(timeout=self._interval_seconds)

    def health(self) -> dict[str, Any]:
        return {
            "running": self.is_running,
            "interval_seconds": self._interval_seconds,
            "max_jobs_per_pass": self._max_jobs_per_pass,
            "last_results_count": len(self._last_results),
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
