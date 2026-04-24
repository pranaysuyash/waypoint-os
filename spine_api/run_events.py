"""
run_events.py — Append-only run event log for Waypoint OS spine_api.

Events are written to data/runs/{run_id}/events.jsonl (one JSON object per line).
Reading events back is done via get_run_events(run_id).

Event types
-----------
    run_started              emitted when the run transitions to RUNNING
    pipeline_stage_entered   emitted when a named stage begins execution
    pipeline_stage_completed emitted when a named stage finishes successfully
    run_completed            emitted on ok=True terminal
    run_failed               emitted on unexpected error terminal
    run_blocked              emitted on strict leakage terminal

All events share a common envelope:
    {
        "event_id":  str,          # evt_{hex8}
        "event_type": str,         # one of the types above
        "run_id":     str,
        "trip_id":    str | null,
        "timestamp":  str,         # ISO-8601 UTC
        <event-specific fields>
    }

Usage
-----
    from spine_api.run_events import emit, get_run_events, EventType

    emit(EventType.RUN_STARTED, run_id="abc123", trip_id="trip_xyz",
         stage="discovery", operating_mode="normal_intake")

    events = get_run_events("abc123")
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

# ---------------------------------------------------------------------------
# Storage root — data/runs/{run_id}/events.jsonl
# ---------------------------------------------------------------------------

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
RUNS_DIR = DATA_DIR / "runs"


def _run_dir(run_id: str) -> Path:
    d = RUNS_DIR / run_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def _events_file(run_id: str) -> Path:
    return _run_dir(run_id) / "events.jsonl"


# ---------------------------------------------------------------------------
# Event types
# ---------------------------------------------------------------------------


class EventType(str, Enum):
    RUN_STARTED              = "run_started"
    PIPELINE_STAGE_ENTERED   = "pipeline_stage_entered"
    PIPELINE_STAGE_COMPLETED = "pipeline_stage_completed"
    RUN_COMPLETED            = "run_completed"
    RUN_FAILED               = "run_failed"
    RUN_BLOCKED              = "run_blocked"

    def __str__(self) -> str:
        return self.value


# ---------------------------------------------------------------------------
# Emit
# ---------------------------------------------------------------------------


def emit(
    event_type: EventType,
    run_id: str,
    trip_id: Optional[str] = None,
    **payload: Any,
) -> dict[str, Any]:
    """
    Append one event to data/runs/{run_id}/events.jsonl.

    Returns the event dict that was written.

    Thread-safety note: each call opens, appends, and closes the file.
    Sufficient for single-worker uvicorn. Add file locking if moving to
    multi-worker or async writes in a future version.
    """
    event: dict[str, Any] = {
        "event_id":   f"evt_{uuid4().hex[:8]}",
        "event_type": str(event_type),
        "run_id":     run_id,
        "trip_id":    trip_id,
        "timestamp":  datetime.now(timezone.utc).isoformat(),
        **payload,
    }

    events_path = _events_file(run_id)
    with events_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(event, default=str) + "\n")

    return event


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------


def get_run_events(run_id: str) -> list[dict[str, Any]]:
    """
    Return all events for a run in chronological order.

    Returns [] if no events exist yet (run not started, or unknown run_id).
    """
    path = _events_file(run_id)
    if not path.exists():
        return []

    events: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    # Corrupted line — skip silently, log nothing (avoid import cycle)
                    pass
    return events


# ---------------------------------------------------------------------------
# Convenience emitters (avoid repeating keyword args at call sites)
# ---------------------------------------------------------------------------


def emit_run_started(
    run_id: str,
    trip_id: Optional[str],
    stage: str,
    operating_mode: str,
) -> dict[str, Any]:
    return emit(
        EventType.RUN_STARTED,
        run_id=run_id,
        trip_id=trip_id,
        stage=stage,
        operating_mode=operating_mode,
    )


def emit_stage_entered(
    run_id: str,
    stage_name: str,
    trip_id: Optional[str] = None,
) -> dict[str, Any]:
    return emit(
        EventType.PIPELINE_STAGE_ENTERED,
        run_id=run_id,
        trip_id=trip_id,
        stage_name=stage_name,
    )


def emit_stage_completed(
    run_id: str,
    stage_name: str,
    execution_ms: float,
    trip_id: Optional[str] = None,
) -> dict[str, Any]:
    return emit(
        EventType.PIPELINE_STAGE_COMPLETED,
        run_id=run_id,
        trip_id=trip_id,
        stage_name=stage_name,
        execution_ms=round(execution_ms, 2),
    )


def emit_run_completed(
    run_id: str,
    trip_id: Optional[str],
    total_ms: float,
) -> dict[str, Any]:
    return emit(
        EventType.RUN_COMPLETED,
        run_id=run_id,
        trip_id=trip_id,
        total_ms=round(total_ms, 2),
    )


def emit_run_failed(
    run_id: str,
    error_type: str,
    error_message: str,
    stage_at_failure: Optional[str] = None,
    trip_id: Optional[str] = None,
) -> dict[str, Any]:
    return emit(
        EventType.RUN_FAILED,
        run_id=run_id,
        trip_id=trip_id,
        error_type=error_type,
        error_message=error_message,
        stage_at_failure=stage_at_failure,
    )


def emit_run_blocked(
    run_id: str,
    block_reason: str,
    stage_at_block: Optional[str] = None,
    trip_id: Optional[str] = None,
) -> dict[str, Any]:
    return emit(
        EventType.RUN_BLOCKED,
        run_id=run_id,
        trip_id=trip_id,
        block_reason=block_reason,
        stage_at_block=stage_at_block,
    )
