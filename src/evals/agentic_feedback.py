"""Agentic feedback contracts for extraction review and fallback outcomes."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping

from spine_api.models.tenant import ExecutionEvent


@dataclass(slots=True)
class AgenticEvalRecord:
    """Normalized eval signal distilled from execution events."""

    workflow: str
    trip_id: str
    subject_type: str
    subject_id: str
    event_type: str
    event_id: str
    failure_signature: str | None
    failure_layer: str | None
    next_fix_layer: str | None
    fallback_trigger_reason: str | None
    fallback_result: str | None
    review_trigger_reason: str | None
    review_outcome: str | None
    provider: str | None
    model: str | None
    failure_cost_placeholder: float | None
    created_at: datetime

    @classmethod
    def from_event(cls, event: ExecutionEvent) -> "AgenticEvalRecord":
        metadata = event.event_metadata or {}
        return cls(
            workflow=str(event.event_category),
            trip_id=event.trip_id,
            subject_type=event.subject_type,
            subject_id=event.subject_id,
            event_type=event.event_type,
            event_id=event.id,
            failure_signature=metadata.get("failure_signature"),
            failure_layer=metadata.get("failure_layer"),
            next_fix_layer=metadata.get("next_fix_layer"),
            fallback_trigger_reason=metadata.get("fallback_trigger_reason"),
            fallback_result=metadata.get("fallback_result"),
            review_trigger_reason=metadata.get("review_trigger_reason"),
            review_outcome=metadata.get("review_outcome"),
            provider=metadata.get("provider"),
            model=metadata.get("model"),
            failure_cost_placeholder=None,
            created_at=event.created_at,
        )


@dataclass(slots=True)
class AgenticEvalWorkItem:
    """Actionable work item produced from repeated eval failures."""

    failure_signature: str
    failure_layer: str
    next_fix_layer: str
    occurrences: int
    first_seen: datetime
    last_seen: datetime
    sample_events: list[str]


def build_repeated_failure_signal(
    events: list[ExecutionEvent],
    min_occurrences: int = 3,
) -> list[AgenticEvalWorkItem]:
    """Build repeated-failure work items from event history.

    The reducer only emits work items when the same failure_signature appears
    at least ``min_occurrences`` times, because that is the point where
    one-off flukes stop being noise and become curriculum material.
    """
    groups: dict[str, list[AgenticEvalWorkItem]] = {}
    by_signature: dict[str, list[AgenticEvalRecord]] = {}
    for event in events:
        record = AgenticEvalRecord.from_event(event)
        if not record.failure_signature:
            continue
        by_signature.setdefault(record.failure_signature, []).append(record)

    work_items: list[AgenticEvalWorkItem] = []
    for signature, records in by_signature.items():
        if len(records) < min_occurrences:
            continue

        sorted_records = sorted(records, key=lambda r: r.created_at)
        sample_events = [r.event_id for r in sorted_records[-3:]]
        work_items.append(
            AgenticEvalWorkItem(
                failure_signature=signature,
                failure_layer=records[-1].failure_layer or "unknown",
                next_fix_layer=records[-1].next_fix_layer or "unknown",
                occurrences=len(records),
                first_seen=sorted_records[0].created_at,
                last_seen=sorted_records[-1].created_at,
                sample_events=sample_events,
            )
        )

    work_items.sort(key=lambda item: item.occurrences, reverse=True)
    return work_items


def extract_metadata_signature(payload: Mapping[str, Any]) -> str | None:
    """Build a stable signature from raw event metadata (for ad-hoc reducers)."""
    document_type = payload.get("document_type", "unknown")
    provider = payload.get("provider", "unknown")
    model = payload.get("model", "unknown")
    error_code = payload.get("error_code", "unknown")
    attempt = payload.get("attempt_number", "unknown")
    fallback_rank = payload.get("fallback_rank", "unknown")
    return f"{document_type}|{provider}|{model}|{error_code}|{attempt}|{fallback_rank}"


def filter_eval_candidates(events: list[ExecutionEvent]) -> list[ExecutionEvent]:
    """Return events that can contribute to evaluation loops."""
    return [
        event
        for event in events
        if any(
            key in (event.event_metadata or {})
            for key in (
                "failure_signature",
                "fallback_trigger_reason",
                "review_trigger_reason",
                "review_outcome",
            )
        )
    ]


def aggregate_eval_records(
    events: list[ExecutionEvent],
    min_occurrences: int = 3,
) -> dict[str, Any]:
    """Return a compact eval summary object for dashboards or CI gating."""
    candidates = filter_eval_candidates(events)
    work_items = build_repeated_failure_signal(candidates, min_occurrences=min_occurrences)
    now = datetime.now(timezone.utc)
    return {
        "total_events_considered": len(candidates),
        "window_minutes": 60 * 24,
        "generated_at": now.isoformat(),
        "work_items": [
            {
                "failure_signature": item.failure_signature,
                "failure_layer": item.failure_layer,
                "next_fix_layer": item.next_fix_layer,
                "occurrences": item.occurrences,
                "first_seen": item.first_seen.isoformat(),
                "last_seen": item.last_seen.isoformat(),
                "sample_events": item.sample_events,
            }
            for item in work_items
        ],
    }

