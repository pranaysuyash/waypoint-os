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
    severity: str = "medium"
    proposed_change: str | None = None
    expected_improvement: str | None = None
    regression_risk: str | None = None
    rerun_subset: str | None = None
    keep_if: str | None = None
    revert_if: str | None = None
    owner: str | None = None


_LAYER_RECOMMENDATIONS = {
    "model": {
        "owner": "model-routing-team",
        "proposed_change": "Review model selection, routing, and confidence thresholds for this workflow family.",
        "expected_improvement": "Reduce avoidable retries and improve acceptance on borderline cases.",
        "regression_risk": "Potential cost increase and higher timeout if routing moves toward larger models.",
        "rerun_subset": "Re-run last 10 failed inputs with same routing/fallback policy.",
    },
    "prompt": {
        "owner": "prompt-engineering",
        "proposed_change": "Version prompts and add schema-aware guidance at constrained fields.",
        "expected_improvement": "Increase extraction completeness and reduce downstream manual fixups.",
        "regression_risk": "Prompt edits may overfit to one artifact subset.",
        "rerun_subset": "Re-run the last 10 failed signatures in shadow mode.",
    },
    "parser": {
        "owner": "data-quality-engineering",
        "proposed_change": "Harden parsing boundary checks and fallback normalizers.",
        "expected_improvement": "Fewer hard parsing exceptions and missing required fields.",
        "regression_risk": "Over-normalization could mask invalid inputs.",
        "rerun_subset": "Re-run samples currently tagged with parser-layer extraction failures.",
    },
    "schema": {
        "owner": "schema-platform",
        "proposed_change": "Adjust schema constraints, optionality, and failure messaging.",
        "expected_improvement": "Lower false failures and better path classification for recoverable inputs.",
        "regression_risk": "Loosening constraints may increase acceptance of malformed data.",
        "rerun_subset": "Re-run samples with same failure signature under schema policy variant.",
    },
    "routing": {
        "owner": "platform-autonomy",
        "proposed_change": "Retune routing or fallback triggers for this edge case.",
        "expected_improvement": "Reduce avoidable fallback and improve first-pass quality.",
        "regression_risk": "Changed routing can shift load to less reliable fallback providers.",
        "rerun_subset": "Replay affected workflow units in both default and candidate routing rules.",
    },
    "fallback": {
        "owner": "platform-autonomy",
        "proposed_change": "Review fallback trigger and stop conditions for repeated misses.",
        "expected_improvement": "Decrease wasteful fallback and avoid unnecessary cost.",
        "regression_risk": "Tightening fallback may increase unresolved first-pass misses.",
        "rerun_subset": "Re-run failed units with revised fallback thresholds.",
    },
    "review": {
        "owner": "owner-ops",
        "proposed_change": "Refine review criteria and escalation conditions.",
        "expected_improvement": "Lower avoidable review load and clearer escalation outcomes.",
        "regression_risk": "Changing review policy can miss quality regressions.",
        "rerun_subset": "Reassess the same sample set across review outcomes.",
    },
    "dictionary": {
        "owner": "data-quality-engineering",
        "proposed_change": "Patch dictionary normalization entries and conflict handling.",
        "expected_improvement": "Improve raw-value recognition and reduce hallucination.",
        "regression_risk": "Added dictionary terms can introduce false matches.",
        "rerun_subset": "Re-run the signature cohort after dictionary update.",
    },
    "normalization": {
        "owner": "data-quality-engineering",
        "proposed_change": "Align normalization output schema and missing-value states.",
        "expected_improvement": "Better differentiation of missing/unknown/inferred for downstream policy.",
        "regression_risk": "New normalization behavior can break existing dashboards expecting old tokens.",
        "rerun_subset": "Replay failed cohort through normalization policy revision.",
    },
    "unknown": {
        "owner": "agentic-eval-loop",
        "proposed_change": "Improve observability first; add missing failure-layer labels and workflow metadata.",
        "expected_improvement": "Future work items become deterministic and cheaper to act on.",
        "regression_risk": "None immediate; this is an instrumentation improvement.",
        "rerun_subset": "Collect richer traces and replay last 15 ambiguous failures.",
    },
}


def _estimate_severity(occurrences: int) -> str:
    """Estimate severity from repeat count only."""
    if occurrences >= 10:
        return "high"
    if occurrences >= 5:
        return "medium"
    return "low"


def _recommendation_profile(layer: str) -> tuple[str, dict[str, str]]:
    normalized = layer if layer in _LAYER_RECOMMENDATIONS else "unknown"
    return normalized, _LAYER_RECOMMENDATIONS[normalized]


def _build_work_item_routing(
    layer: str,
    occurrence_count: int,
    next_fix_layer: str,
) -> dict[str, str]:
    layer_key, cfg = _recommendation_profile(layer)
    keep_threshold = max(occurrence_count, 1) * 10
    return {
        "severity": _estimate_severity(occurrence_count),
        "proposed_change": cfg["proposed_change"],
        "expected_improvement": cfg["expected_improvement"],
        "regression_risk": cfg["regression_risk"],
        "rerun_subset": cfg["rerun_subset"],
        "keep_if": (
            f"Keep if {keep_threshold}% of sampled reruns are accepted "
            f"or review corrections drop below {min(occurrence_count, 2)} per 20 samples."
        ),
        "revert_if": (
            "Revert if false_escalation or rejected_review_rate rises by >5pp "
            f"within 200 rerun samples for {next_fix_layer or layer_key}."
        ),
        "owner": cfg["owner"],
    }


@dataclass(slots=True)
class CanonicalAgenticEvidenceRecord:
    """Canonical record used for cross-system evaluation consumers."""

    workflow_unit_id: str
    workflow_type: str
    input_artifact_id: str
    provider: str | None
    model: str | None
    prompt_version: str | None
    prompt_hash: str | None
    schema_version: str | None
    routing_version: str | None
    dictionary_version: str | None
    normalization_version: str | None
    fallback_trigger_reason: str | None
    fallback_result: str | None
    review_trigger_reason: str | None
    review_outcome: str | None
    review_workflow_unit_id: str | None
    escalation_outcome: str | None
    final_acceptance_status: str | None
    failure_signature: str | None
    failure_layer: str | None
    next_fix_layer: str | None
    latency_ms: float | None
    cost_usd: float | None
    created_at: datetime

    @classmethod
    def from_event(
        cls,
        event: ExecutionEvent,
        review_escalation_outcome: str | None = None,
    ) -> "CanonicalAgenticEvidenceRecord":
        metadata = event.event_metadata or {}
        escalation_outcome = (
            metadata.get("escalation_outcome")
            if review_escalation_outcome is None
            else review_escalation_outcome
        )
        final_status = _infer_final_acceptance_status(event)
        return cls(
            workflow_unit_id=str(event.id),
            workflow_type=str(event.event_category),
            input_artifact_id=metadata.get("input_artifact_id", event.subject_id),
            provider=metadata.get("provider"),
            model=metadata.get("model"),
            prompt_version=metadata.get("prompt_version"),
            prompt_hash=metadata.get("prompt_hash"),
            schema_version=metadata.get("schema_version"),
            routing_version=metadata.get("routing_version"),
            dictionary_version=metadata.get("dictionary_version"),
            normalization_version=metadata.get("normalization_version"),
            fallback_trigger_reason=metadata.get("fallback_trigger_reason"),
            fallback_result=metadata.get("fallback_result"),
            review_trigger_reason=metadata.get("review_trigger_reason"),
            review_outcome=metadata.get("review_outcome"),
            review_workflow_unit_id=metadata.get("review_workflow_unit_id"),
            escalation_outcome=escalation_outcome,
            final_acceptance_status=final_status,
            failure_signature=metadata.get("failure_signature"),
            failure_layer=metadata.get("failure_layer"),
            next_fix_layer=metadata.get("next_fix_layer"),
            latency_ms=metadata.get("latency_ms") if isinstance(metadata.get("latency_ms"), (int, float)) else None,
            cost_usd=metadata.get("cost_estimate_usd") if isinstance(metadata.get("cost_estimate_usd"), (int, float)) else None,
            created_at=event.created_at,
        )


def _safe_divide(numerator: int, denominator: int) -> float:
    """Return a safe float ratio rounded to 3 decimals."""
    if denominator <= 0:
        return 0.0
    return round(numerator / denominator, 3)


def _infer_final_acceptance_status(event: ExecutionEvent) -> str | None:
    """Infer a coarse final status from event type and terminal state."""
    if event.event_type == "extraction_applied":
        return "accepted"
    if event.event_type == "extraction_rejected":
        return "rejected"
    if event.event_type == "extraction_run_failed":
        return "failed"
    if event.event_type == "extraction_run_completed":
        return "pending_review"
    if event.event_type == "document_accepted":
        return "accepted"
    if event.event_type == "document_rejected":
        return "rejected"
    if event.event_type == "confirmation_recorded":
        return "accepted"
    if event.event_type == "confirmation_voided":
        return "rejected"
    if event.event_type == "task_completed":
        return "accepted"
    if event.event_type == "task_cancelled":
        return "rejected"
    if event.event_type == "task_blocked":
        return "pending_review"
    return None


def _normalize_records(records: list[CanonicalAgenticEvidenceRecord]) -> list[dict[str, Any]]:
    return [
        {
            "workflow_unit_id": record.workflow_unit_id,
            "workflow_type": record.workflow_type,
            "input_artifact_id": record.input_artifact_id,
            "provider": record.provider,
            "model": record.model,
            "prompt_version": record.prompt_version,
            "prompt_hash": record.prompt_hash,
            "schema_version": record.schema_version,
            "routing_version": record.routing_version,
            "dictionary_version": record.dictionary_version,
            "normalization_version": record.normalization_version,
            "fallback_trigger_reason": record.fallback_trigger_reason,
            "fallback_result": record.fallback_result,
            "review_trigger_reason": record.review_trigger_reason,
            "review_outcome": record.review_outcome,
            "escalation_outcome": record.escalation_outcome,
            "final_acceptance_status": record.final_acceptance_status,
            "failure_signature": record.failure_signature,
            "failure_layer": record.failure_layer,
            "next_fix_layer": record.next_fix_layer,
            "latency_ms": record.latency_ms,
            "cost_usd": record.cost_usd,
            "created_at": record.created_at.isoformat(),
        }
        for record in records
    ]


def build_canonical_evidence_records(
    events: list[ExecutionEvent],
    review_events: list[Mapping[str, Any]] | None = None,
    *,
    max_items: int = 200,
) -> list[dict[str, Any]]:
    """Build canonical eval evidence records for downstream loops and tools."""
    candidates = filter_eval_candidates(events)
    if not candidates:
        return []

    review_outcome_index = _build_review_outcome_index(review_events)
    canonical = [
        CanonicalAgenticEvidenceRecord.from_event(
            event,
            review_escalation_outcome=review_outcome_index.get(str(event.id)),
        )
        for event in candidates
    ]
    canonical.sort(key=lambda item: item.created_at, reverse=True)
    return _normalize_records(canonical[:max_items])


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
    workflow_unit_ids: set[str] | None = None,
) -> dict[str, Any]:
    """Compute execution-route metrics used by agentic eval loops."""
    candidates = filter_eval_candidates(events)
    total_candidates = len(candidates)
    fallback_trigger_count = 0
    fallback_success_count = 0
    fallback_exhausted_count = 0
    review_trigger_count = 0
    review_outcomes: dict[str, int] = {}
    escalation_outcomes: dict[str, int] = _collect_review_outcomes(
        review_events,
        workflow_unit_ids=workflow_unit_ids,
    )

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
        failure_layer = records[-1].failure_layer or "unknown"
        next_fix_layer = records[-1].next_fix_layer or "unknown"
        recommendation = _build_work_item_routing(
            layer=failure_layer,
            occurrence_count=len(records),
            next_fix_layer=next_fix_layer,
        )
        sample_events = [r.event_id for r in sorted_records[-3:]]
        work_items.append(
            AgenticEvalWorkItem(
                failure_signature=signature,
                failure_layer=failure_layer,
                next_fix_layer=next_fix_layer,
                occurrences=len(records),
                first_seen=sorted_records[0].created_at,
                last_seen=sorted_records[-1].created_at,
                sample_events=sample_events,
                severity=recommendation["severity"],
                proposed_change=recommendation["proposed_change"],
                expected_improvement=recommendation["expected_improvement"],
                regression_risk=recommendation["regression_risk"],
                rerun_subset=recommendation["rerun_subset"],
                keep_if=recommendation["keep_if"],
                revert_if=recommendation["revert_if"],
                owner=recommendation["owner"],
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


def _collect_review_outcomes(
    review_events: list[Mapping[str, Any]] | None,
    workflow_unit_ids: set[str] | None = None,
) -> dict[str, int]:
    """Collect escalation outcome counts from audit/review events."""
    outcomes: dict[str, int] = {}
    if not review_events:
        return outcomes

    target_ids = set(workflow_unit_ids or [])
    explicit_matches: list[tuple[str, str]] = []
    legacy_outcomes: list[str] = []

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
            if target_ids and not details.get("review_workflow_unit_id"):
                legacy_outcomes.append(escalation_outcome)
                continue

            workflow_unit_id = details.get("review_workflow_unit_id")
            if isinstance(workflow_unit_id, str):
                explicit_matches.append((workflow_unit_id, escalation_outcome))
            elif not target_ids:
                outcomes[escalation_outcome] = outcomes.get(escalation_outcome, 0) + 1

    if not target_ids:
        return outcomes

    if not explicit_matches:
        for escalation_outcome in legacy_outcomes:
            outcomes[escalation_outcome] = outcomes.get(escalation_outcome, 0) + 1
        return outcomes

    for workflow_unit_id, escalation_outcome in explicit_matches:
        if workflow_unit_id in target_ids:
            outcomes[escalation_outcome] = outcomes.get(escalation_outcome, 0) + 1
    return outcomes


def _build_review_outcome_index(
    review_events: list[Mapping[str, Any]] | None,
) -> dict[str, str]:
    """Build a mapping of workflow_unit_id -> review escalation outcome."""
    index: dict[str, str] = {}
    if not review_events:
        return index

    for event in review_events:
        if not isinstance(event, Mapping):
            continue
        if event.get("type") != "review_action":
            continue
        details = event.get("details")
        if not isinstance(details, Mapping):
            continue
        workflow_unit_id = details.get("review_workflow_unit_id")
        escalation_outcome = details.get("escalation_outcome")
        if not isinstance(workflow_unit_id, str) or not isinstance(escalation_outcome, str):
            continue
        index[workflow_unit_id] = escalation_outcome

    return index


def _parse_event_timestamp(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None
    return None


# ---------------------------------------------------------------------------
# Routing health checks
# ---------------------------------------------------------------------------

DEFAULT_ROUTING_HEALTH_THRESHOLDS: dict[str, float] = {
    "fallback_trigger_rate_warning": 0.3,
    "fallback_trigger_rate_critical": 0.5,
    "false_escalation_rate_warning": 0.2,
    "false_escalation_rate_critical": 0.4,
    "missed_escalation_rate_warning": 0.2,
    "missed_escalation_rate_critical": 0.4,
    "review_correction_rate_warning": 0.3,
    "review_correction_rate_critical": 0.5,
    "latency_p50_ms_warning": 5_000,
    "latency_p50_ms_critical": 10_000,
    "latency_p95_ms_warning": 15_000,
    "latency_p95_ms_critical": 30_000,
}


@dataclass(slots=True)
class RoutingHealthAlert:
    """A single routing health alert when a metric exceeds a threshold."""

    metric: str
    severity: str  # "warning" | "critical"
    actual_value: float | None
    threshold: float
    message: str


@dataclass(slots=True)
class RoutingHealthReport:
    """Aggregated routing health status with per-metric alerts."""

    status: str  # "healthy" | "warning" | "critical"
    alerts: list[RoutingHealthAlert]
    checked_at: datetime
    metrics_snapshot: dict[str, Any]

    def summary(self) -> dict[str, Any]:
        """Return a JSON-serialisable summary."""
        return {
            "status": self.status,
            "alert_count": len(self.alerts),
            "alerts": [
                {
                    "metric": a.metric,
                    "severity": a.severity,
                    "actual_value": a.actual_value,
                    "threshold": a.threshold,
                    "message": a.message,
                }
                for a in self.alerts
            ],
            "checked_at": self.checked_at.isoformat(),
        }


def _check_threshold_alert(
    metric_name: str,
    actual: float | int | None,
    warning_threshold: float,
    critical_threshold: float,
    unit: str = "",
) -> RoutingHealthAlert | None:
    """Check a metric against warning/critical thresholds.

    Parameters
    ----------
    unit
        Suffix for the message (e.g. ``"ms"`` for latency).  If empty the
        value is formatted as a raw float.
    """
    if actual is None:
        return None
    actual_f = float(actual)
    if actual_f >= critical_threshold:
        return RoutingHealthAlert(
            metric=metric_name,
            severity="critical",
            actual_value=actual_f,
            threshold=critical_threshold,
            message=f"{metric_name}={actual_f:g}{unit} >= critical threshold {critical_threshold:g}{unit}",
        )
    if actual_f >= warning_threshold:
        return RoutingHealthAlert(
            metric=metric_name,
            severity="warning",
            actual_value=actual_f,
            threshold=warning_threshold,
            message=f"{metric_name}={actual_f:g}{unit} >= warning threshold {warning_threshold:g}{unit}",
        )
    return None


def check_routing_health(
    routing_metrics: dict[str, Any],
    *,
    thresholds: dict[str, float] | None = None,
    reference_time: datetime | None = None,
) -> RoutingHealthReport:
    """Check routing health against configurable alert thresholds.

    Consumes the output of :func:`build_routing_metrics` and evaluates
    each metric against warning / critical thresholds.  Returns a
    :class:`RoutingHealthReport` with per-metric alerts and an overall
    status ("healthy", "warning", or "critical").

    Parameters
    ----------
    routing_metrics
        Dict returned by :func:`build_routing_metrics`.
    thresholds
        Override default thresholds.  Keys match
        :data:`DEFAULT_ROUTING_HEALTH_THRESHOLDS`.
    reference_time
        Timestamp for the report (defaults to ``datetime.now(timezone.utc)``).
    """
    t = {**DEFAULT_ROUTING_HEALTH_THRESHOLDS, **(thresholds or {})}
    alerts: list[RoutingHealthAlert] = []

    # --- rate checks ---
    for metric_name, warn_key, crit_key in [
        ("fallback_trigger_rate", "fallback_trigger_rate_warning", "fallback_trigger_rate_critical"),
        ("false_escalation_rate", "false_escalation_rate_warning", "false_escalation_rate_critical"),
        ("missed_escalation_rate", "missed_escalation_rate_warning", "missed_escalation_rate_critical"),
        ("review_correction_rate", "review_correction_rate_warning", "review_correction_rate_critical"),
    ]:
        alert = _check_threshold_alert(
            metric_name,
            routing_metrics.get(metric_name),
            t[warn_key],
            t[crit_key],
        )
        if alert:
            alerts.append(alert)

    # --- latency checks ---
    latency = routing_metrics.get("latency_by_candidates") or {}
    for key, warn_key, crit_key in [
        ("p50_ms", "latency_p50_ms_warning", "latency_p50_ms_critical"),
        ("p95_ms", "latency_p95_ms_warning", "latency_p95_ms_critical"),
    ]:
        alert = _check_threshold_alert(
            f"latency_{key}",
            latency.get(key),
            t[warn_key],
            t[crit_key],
            unit="ms",
        )
        if alert:
            alerts.append(alert)

    # --- overall status ---
    if any(a.severity == "critical" for a in alerts):
        status = "critical"
    elif alerts:
        status = "warning"
    else:
        status = "healthy"

    return RoutingHealthReport(
        status=status,
        alerts=alerts,
        checked_at=reference_time or datetime.now(timezone.utc),
        metrics_snapshot=routing_metrics,
    )


def aggregate_eval_records(
    events: list[ExecutionEvent],
    min_occurrences: int = 3,
    window_minutes: int = 24 * 60,
    *,
    reference_time: datetime | None = None,
    review_events: list[Mapping[str, Any]] | None = None,
    workflow_unit_ids: set[str] | None = None,
) -> dict[str, Any]:
    """Return a compact eval summary object for dashboards or CI gating.

    The summary currently returns only repeated failure work items with enough
    occurrences to indicate signal instead of noise.
    """
    candidates = filter_eval_candidates(events)
    now = reference_time or datetime.now(timezone.utc)
    filtered_review_events = review_events
    candidate_unit_ids: set[str] = set()
    if window_minutes > 0:
        window_start = now - timedelta(minutes=window_minutes)
        candidates = [event for event in candidates if event.created_at >= window_start]
        candidate_unit_ids = {str(event.id) for event in candidates}
        if review_events:
            filtered_review_events = [
                event
                for event in review_events
                if (timestamp := _parse_event_timestamp(event.get("timestamp") if isinstance(event, Mapping) else None))
                and timestamp >= window_start
            ]
    else:
        candidate_unit_ids = {str(event.id) for event in candidates}

    if workflow_unit_ids is not None:
        candidate_unit_ids = candidate_unit_ids.intersection(workflow_unit_ids)

    work_items = build_repeated_failure_signal(
        candidates,
        min_occurrences=min_occurrences,
    )
    return {
        "total_events_considered": len(candidates),
        "window_minutes": window_minutes,
        "generated_at": now.isoformat(),
        "routing_metrics": build_routing_metrics(
            candidates,
            review_events=filtered_review_events,
            workflow_unit_ids=candidate_unit_ids,
        ),
        "canonical_evidence_records": build_canonical_evidence_records(
            candidates,
            review_events=filtered_review_events,
            max_items=200,
        ),
        "work_items": [
            {
                "failure_signature": item.failure_signature,
                "failure_layer": item.failure_layer,
                "next_fix_layer": item.next_fix_layer,
                "occurrences": item.occurrences,
                "first_seen": item.first_seen.isoformat(),
                "last_seen": item.last_seen.isoformat(),
                "sample_events": item.sample_events,
                "severity": item.severity,
                "proposed_change": item.proposed_change,
                "expected_improvement": item.expected_improvement,
                "regression_risk": item.regression_risk,
                "rerun_subset": item.rerun_subset,
                "keep_if": item.keep_if,
                "revert_if": item.revert_if,
                "owner": item.owner,
            }
            for item in work_items
        ],
    }
