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


def build_requeue_port(
    mode: str = "disabled",
    *,
    spine_runner: Optional[Callable[[str], Any]] = None,
    run_spine: Optional[Callable[..., Any]] = None,
) -> SpineRequeuePort:
    if mode == "inline" and run_spine is not None:
        return InlineSpineRequeuePort(run_spine=run_spine)
    if spine_runner is not None:
        return _RawCallableRequeuePort(spine_runner=spine_runner)
    return DisabledSpineRequeuePort()
