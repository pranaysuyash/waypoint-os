"""
Requeue port and implementations for agent recovery.

SpineRequeuePort is the boundary between the recovery agent and the pipeline
execution infrastructure.  Implementations decouple requeue mechanism from
recovery logic.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Optional, Protocol

logger = logging.getLogger("agent_requeue")


# ---------------------------------------------------------------------------
# Result
# ---------------------------------------------------------------------------


@dataclass
class RequeueResult:
    accepted: bool
    mode: str = "disabled"
    job_id: Optional[str] = None
    reason: str = ""
    retryable: bool = False


# ---------------------------------------------------------------------------
# Port
# ---------------------------------------------------------------------------


class SpineRequeuePort(Protocol):
    def requeue_trip(self, trip_id: str, trip_record: dict[str, Any], reason: str, attempt: int) -> RequeueResult:
        ...


# ---------------------------------------------------------------------------
# Disabled implementation
# ---------------------------------------------------------------------------


class DisabledSpineRequeuePort:
    """Default safest behavior: requeue not configured, escalate."""

    def requeue_trip(self, trip_id: str, trip_record: dict[str, Any], reason: str, attempt: int) -> RequeueResult:
        logger.info("Requeue disabled for trip %s (attempt %d): %s", trip_id, attempt, reason)
        return RequeueResult(
            accepted=False,
            mode="disabled",
            reason="Requeue not configured. Set AGENT_RECOVERY_REQUEUE_MODE=inline to enable.",
        )


# ---------------------------------------------------------------------------
# Adapter wrapping a raw callable (backward compatibility for tests)
# ---------------------------------------------------------------------------


class _RawCallableRequeuePort:
    """Wraps a spine_runner(trip_id) callable into a port.

    Internal compatibility adapter.  Do not use for new code.
    """

    def __init__(self, spine_runner: Callable[[str], Any]):
        self._spine_runner = spine_runner

    def requeue_trip(self, trip_id: str, trip_record: dict[str, Any], reason: str, attempt: int) -> RequeueResult:
        try:
            self._spine_runner(trip_id)
            return RequeueResult(
                accepted=True,
                mode="inline",
                reason=reason,
            )
        except Exception as exc:
            logger.exception("Raw callable requeue failed for trip %s", trip_id)
            return RequeueResult(
                accepted=False,
                mode="inline",
                reason=f"Re-queue failed: {exc}",
                retryable=True,
            )


# ---------------------------------------------------------------------------
# Inline implementation
# ---------------------------------------------------------------------------


class InlineSpineRequeuePort:
    """Re-queues a trip by reconstructing pipeline context from the trip record.

    Requires the trip record to have enough source/request data to rebuild a
    valid pipeline execution.  Returns unsupported/not-accepted if context
    is insufficient.

    The injected run_spine callable must accept at minimum:
        envelopes (list[SourceEnvelope]), stage (str)
    Additional keyword arguments may be accepted but are not required.
    """

    def __init__(self, run_spine: Callable[..., Any]):
        self._run_spine = run_spine

    def requeue_trip(self, trip_id: str, trip_record: dict[str, Any], reason: str, attempt: int) -> RequeueResult:
        raw_input = trip_record.get("raw_input") or {}
        if not raw_input or not isinstance(raw_input, dict):
            return RequeueResult(
                accepted=False,
                mode="inline",
                reason=f"Trip {trip_id} has no raw_input data; cannot reconstruct pipeline context.",
            )
        stage = str(trip_record.get("stage") or trip_record.get("status") or "discovery")
        try:
            self._run_spine(
                envelopes=[raw_input],
                stage=stage,
            )
            return RequeueResult(
                accepted=True,
                mode="inline",
                reason=reason,
                retryable=False,
            )
        except Exception as exc:
            logger.exception("Inline requeue failed for trip %s", trip_id)
            return RequeueResult(
                accepted=False,
                mode="inline",
                reason=f"Re-queue failed: {exc}",
                retryable=True,
            )


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# SQL Queue implementation
# ---------------------------------------------------------------------------


class SQLSpineJobQueueRequeuePort:
    """Enqueues a durable recovery job for later execution by RequeueWorker.

    The recovery agent only enqueues.  The worker processes the job outside
    the recovery loop, keeping recovery scans fast and decoupled from spine
    execution.
    """

    def __init__(self, job_store: Any):
        self._job_store = job_store

    def requeue_trip(self, trip_id: str, trip_record: dict[str, Any], reason: str, attempt: int) -> RequeueResult:
        # Attempt count comes from RecoveryAgent's in-memory counter; use it
        # along with trip info to build a stable idempotency key
        idempotency_key = f"requeue:{trip_id}:{reason[:80]}"
        accepted, job_id = self._job_store.enqueue(
            trip_id=trip_id,
            idempotency_key=idempotency_key,
            reason=reason,
            payload={"trip_record_keys": list(trip_record.keys())},
            max_attempts=3,
        )
        if accepted:
            return RequeueResult(accepted=True, mode="sql_queue", job_id=job_id, reason=reason, retryable=False)
        return RequeueResult(accepted=True, mode="sql_queue", job_id=job_id, reason="Duplicate requeue already enqueued", retryable=False)

    def get_trip_attempts(self, trip_id: str) -> int:
        stats = self._job_store.trip_stats(trip_id)
        return int(stats.get("attempts") or 0)

    def is_trip_poisoned(self, trip_id: str) -> bool:
        stats = self._job_store.trip_stats(trip_id)
        return bool(stats.get("poisoned"))


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------


def build_requeue_port(
    mode: str = "disabled",
    *,
    spine_runner: Optional[Callable[[str], Any]] = None,
    run_spine: Optional[Callable[..., Any]] = None,
    job_store: Any = None,
) -> SpineRequeuePort:
    if mode == "sql_queue" and job_store is not None:
        return SQLSpineJobQueueRequeuePort(job_store=job_store)
    if mode == "inline" and run_spine is not None:
        return InlineSpineRequeuePort(run_spine=run_spine)
    if spine_runner is not None:
        return _RawCallableRequeuePort(spine_runner=spine_runner)
    return DisabledSpineRequeuePort()
