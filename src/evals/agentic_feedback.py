"""Agentic feedback contracts for extraction review and fallback outcomes."""

from __future__ import annotations

from dataclasses import dataclass
import math
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


def _safe_divide(numerator: int, denominator: int) -> float:
    """Return a safe float ratio rounded to 3 decimals."""
    if denominator <= 0:
        return 0.0
    return round(numerator / denominator, 3)


def _safe_percentile(values: list[int], q: float) -> int | None:
    """Compute a percentile using linear interpolation."""
    if not values:
        return None
    if len(values) == 1:
        return int(values[0])

    ordered = sorted(values)
    idx = (len(ordered) - 1) * q
    lower = math.floor(idx)
    upper = math.ceil(idx)
    if lower == upper:
        return ordered[lower]
    weight = idx - lower
    return int(round(ordered[lower] * (1.0 - weight) + ordered[upper] * weight))


def build_routing_metrics(
    events: list[ExecutionEvent],
    *,
    review_events: list[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Compute execution-route metrics used by agentic eval loops."""
    candidates = filter_eval_candidates(events)
    total_candidates = len(candidates)
    fallback_trigger_count = 0
    fallback_success_count = 0
    fallback_exhausted_count = 0
    review_trigger_count = 0
    review_outcomes: dict[str, int] = {}
    escalation_outcomes: dict[str, int] = _collect_review_outcomes(review_events)

    latency_ms_values: list[int] = []
    cost_values: list[float] = []

    for event in candidates:
        metadata = event.event_metadata or {}

        if metadata.get("fallback_trigger_reason"):
            fallback_trigger_count += 1

        fallback_result = metadata.get("fallback_result")
        if fallback_result == "succeeded_after_fallback":
            fallback_success_count += 1
        elif fallback_result == "exhausted":
            fallback_exhausted_count += 1

        if metadata.get("review_trigger_reason"):
            review_trigger_count += 1

        review_outcome = metadata.get("review_outcome")
        if isinstance(review_outcome, str):
            review_outcomes[review_outcome] = review_outcomes.get(review_outcome, 0) + 1

        escalation_outcome = metadata.get("escalation_outcome")
        if isinstance(escalation_outcome, str):
            escalation_outcomes[escalation_outcome] = escalation_outcomes.get(escalation_outcome, 0) + 1

        latency_ms = metadata.get("latency_ms")
        if isinstance(latency_ms, int):
            latency_ms_values.append(latency_ms)
        elif isinstance(latency_ms, float):
            latency_ms_values.append(int(latency_ms))

        cost = metadata.get("cost_estimate_usd")
        if isinstance(cost, (int, float)):
            cost_values.append(float(cost))

    review_applied_count = review_outcomes.get("applied", 0) + review_outcomes.get("manual_apply", 0)
    review_rejected_count = review_outcomes.get("rejected", 0) + review_outcomes.get("manual_reject", 0)
    total_review_count = review_applied_count + review_rejected_count
    false_escalation_count = escalation_outcomes.get("false_escalation", 0)
    missed_escalation_count = escalation_outcomes.get("missed_escalation", 0)
    correct_escalation_count = escalation_outcomes.get("correct_escalation", 0)
    explicit_escalation_count = false_escalation_count + missed_escalation_count + correct_escalation_count
    total_cost = sum(cost_values) if cost_values else 0.0

    return {
        "fallback_trigger_rate": _safe_divide(fallback_trigger_count, total_candidates),
        "fallback_trigger_count": fallback_trigger_count,
        "useful_fallback_count": fallback_success_count,
        "wasteful_fallback_count": fallback_exhausted_count,
        "useful_fallback_rate": _safe_divide(fallback_success_count, max(1, fallback_trigger_count)),
        "review_trigger_rate": _safe_divide(review_trigger_count, total_candidates),
        "review_trigger_count": review_trigger_count,
        "review_accept_count": review_applied_count,
        "review_reject_count": review_rejected_count,
        "review_correction_rate": _safe_divide(review_rejected_count, max(1, total_review_count)),
        "false_escalation_rate": _safe_divide(false_escalation_count, explicit_escalation_count) if explicit_escalation_count else None,
        "false_escalation_count": false_escalation_count if explicit_escalation_count else None,
        "missed_escalation_rate": _safe_divide(missed_escalation_count, explicit_escalation_count) if explicit_escalation_count else None,
        "missed_escalation_count": missed_escalation_count if explicit_escalation_count else None,
        "correct_escalation_count": correct_escalation_count if explicit_escalation_count else None,
        "escalation_outcome_count": explicit_escalation_count if explicit_escalation_count else None,
        "latency_by_candidates": {
            "count": len(latency_ms_values),
            "avg_ms": round(sum(latency_ms_values) / len(latency_ms_values), 2) if latency_ms_values else None,
            "p50_ms": _safe_percentile(latency_ms_values, 0.5),
            "p95_ms": _safe_percentile(latency_ms_values, 0.95),
        },
        "cost_usd": {
            "total": round(total_cost, 4),
            "avg_per_eval_event": round(total_cost / total_candidates, 4) if total_candidates else None,
            "event_count_with_cost": len(cost_values),
        },
        "notes": [
            "false_escalation and missed_escalation are populated when review events log escalation_outcome."
        ],
    }


def build_repeated_failure_signal(
    events: list[ExecutionEvent],
    min_occurrences: int = 3,
) -> list[AgenticEvalWorkItem]:
    """Build repeated-failure work items from event history.

    The reducer only emits work items when the same failure_signature appears
    at least ``min_occurrences`` times, because that is the point where
    one-off flukes stop being noise and become curriculum material.
    """
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
                "escalation_outcome",
            )
        )
    ]


def _collect_review_outcomes(review_events: list[Mapping[str, Any]] | None) -> dict[str, int]:
    """Collect escalation outcome counts from audit/review events."""
    outcomes: dict[str, int] = {}
    if not review_events:
        return outcomes

    for event in review_events:
        if not isinstance(event, Mapping):
            continue
        if event.get("type") != "review_action":
            continue
        details = event.get("details")
        if not isinstance(details, Mapping):
            continue
        escalation_outcome = details.get("escalation_outcome")
        if isinstance(escalation_outcome, str):
            outcomes[escalation_outcome] = outcomes.get(escalation_outcome, 0) + 1
    return outcomes


def _parse_event_timestamp(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None
    return None


def aggregate_eval_records(
    events: list[ExecutionEvent],
    min_occurrences: int = 3,
    window_minutes: int = 24 * 60,
    *,
    reference_time: datetime | None = None,
    review_events: list[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Return a compact eval summary object for dashboards or CI gating.

    The summary currently returns only repeated failure work items with enough
    occurrences to indicate signal instead of noise.
    """
    candidates = filter_eval_candidates(events)
    now = reference_time or datetime.now(timezone.utc)
    filtered_review_events = review_events
    if window_minutes > 0:
        window_start = now - timedelta(minutes=window_minutes)
        candidates = [event for event in candidates if event.created_at >= window_start]
        if review_events:
            filtered_review_events = [
                event
                for event in review_events
                if (timestamp := _parse_event_timestamp(event.get("timestamp") if isinstance(event, Mapping) else None))
                and timestamp >= window_start
            ]

    work_items = build_repeated_failure_signal(
        candidates,
        min_occurrences=min_occurrences,
    )
    return {
        "total_events_considered": len(candidates),
        "window_minutes": window_minutes,
        "generated_at": now.isoformat(),
        "routing_metrics": build_routing_metrics(candidates, review_events=filtered_review_events),
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
