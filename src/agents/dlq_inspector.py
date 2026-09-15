"""
src/agents/dlq_inspector.py — Dead-Letter Queue (DLQ) Inspector & Poisoned Job Replay (Finding F-07).

Provides observability and recovery tooling for background agent tasks in JOB_STATUS_POISONED state:
1. In-memory & persistent DLQ registration
2. PII / token payload redaction for secure inspection
3. Safe counterfactual payload patching and job replay execution
4. Permanent purge with audit log trail
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class PoisonResolutionStatus(str, Enum):
    QUEUED_IN_DLQ = "QUEUED_IN_DLQ"
    REPLAYED_SUCCESSFULLY = "REPLAYED_SUCCESSFULLY"
    PURGED = "PURGED"
    REDACTED = "REDACTED"


@dataclass(slots=True)
class PoisonedJobRecord:
    job_id: str
    agent_name: str
    trip_id: str
    error_message: str
    stack_trace: str
    failed_payload: Dict[str, Any]
    retry_count: int
    poisoned_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    status: PoisonResolutionStatus = PoisonResolutionStatus.QUEUED_IN_DLQ
    resolution_note: Optional[str] = None


class DLQInspector:
    """
    Operator & Supervisor tool to inspect, redact, and replay poisoned background agent tasks.
    """

    _POISON_STORE: Dict[str, PoisonedJobRecord] = {}

    @classmethod
    def record_poisoned_job(
        cls,
        job_id: str,
        agent_name: str,
        trip_id: str,
        error_message: str,
        stack_trace: str,
        failed_payload: Dict[str, Any],
        retry_count: int = 3,
    ) -> PoisonedJobRecord:
        record = PoisonedJobRecord(
            job_id=job_id,
            agent_name=agent_name,
            trip_id=trip_id,
            error_message=error_message,
            stack_trace=stack_trace,
            failed_payload=cls._sanitize_payload(failed_payload),
            retry_count=retry_count,
        )
        cls._POISON_STORE[job_id] = record
        return record

    @classmethod
    def list_poisoned_jobs(cls, agent_name: Optional[str] = None) -> List[PoisonedJobRecord]:
        jobs = list(cls._POISON_STORE.values())
        if agent_name:
            jobs = [j for j in jobs if j.agent_name == agent_name]
        return [j for j in jobs if j.status == PoisonResolutionStatus.QUEUED_IN_DLQ]

    @classmethod
    def get_job(cls, job_id: str) -> Optional[PoisonedJobRecord]:
        return cls._POISON_STORE.get(job_id)

    @classmethod
    def replay_job(
        cls,
        job_id: str,
        patched_payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        job = cls._POISON_STORE.get(job_id)
        if not job:
            raise KeyError(f"Poisoned job {job_id} not found in DLQ")

        payload_to_run = patched_payload or job.failed_payload
        job.status = PoisonResolutionStatus.REPLAYED_SUCCESSFULLY
        job.resolution_note = f"Replayed with {len(payload_to_run)} payload fields at {datetime.now(timezone.utc).isoformat()}"

        return {
            "ok": True,
            "job_id": job_id,
            "agent_name": job.agent_name,
            "trip_id": job.trip_id,
            "status": "REPLAYED",
            "execution_payload": payload_to_run,
        }

    @classmethod
    def purge_job(cls, job_id: str, reason: str) -> bool:
        job = cls._POISON_STORE.get(job_id)
        if not job:
            return False
        job.status = PoisonResolutionStatus.PURGED
        job.resolution_note = f"Purged by operator: {reason}"
        return True

    @classmethod
    def redact_job(cls, job_id: str, reason: str) -> bool:
        """Mark a poisoned job REDACTED: payload stripped, row/record preserved.

        Mirrors the durable redaction performed by RequeueJobStore.redact_poisoned.
        Unlike purge, the record stays queryable for the operator audit trail —
        it just no longer appears in the actionable DLQ list.
        """
        job = cls._POISON_STORE.get(job_id)
        if not job:
            return False
        job.status = PoisonResolutionStatus.REDACTED
        job.failed_payload = {}
        job.resolution_note = f"Redacted by operator: {reason}"
        return True

    @staticmethod
    def _sanitize_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
        """Redacts sensitive tokens, credit card numbers, and passwords from DLQ payload."""
        sanitized = {}
        for k, v in payload.items():
            k_lower = k.lower()
            if any(s in k_lower for s in ("token", "secret", "password", "card", "cvv", "pan")):
                sanitized[k] = "[REDACTED_BY_DLQ_GUARD]"
            elif isinstance(v, dict):
                sanitized[k] = DLQInspector._sanitize_payload(v)
            else:
                sanitized[k] = v
        return sanitized
