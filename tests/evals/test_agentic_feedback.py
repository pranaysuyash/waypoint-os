from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from src.evals.agentic_feedback import (
    AgenticEvalRecord,
    RoutingHealthAlert,
    RoutingHealthReport,
    aggregate_eval_records,
    build_routing_metrics,
    build_repeated_failure_signal,
    build_canonical_evidence_records,
    check_routing_health,
    extract_metadata_signature,
    filter_eval_candidates,
)


def _event(**overrides):
    defaults = {
        "event_category": "extraction",
        "trip_id": "trip_001",
        "subject_type": "document_extraction",
        "subject_id": "doc_ex_001",
        "event_type": "extraction_attempt_failed",
        "id": "evt_base",
        "event_metadata": {},
        "created_at": datetime(2026, 6, 18, 10, 0, tzinfo=timezone.utc),
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def test_agentic_eval_record_reads_eval_metadata():
    event = _event(
        event_category="extraction",
        event_type="extraction_attempt_failed",
        event_metadata={
            "failure_signature": "passport|m1|attempt-1|fb-0|schema_validation_failed",
            "failure_layer": "schema",
            "next_fix_layer": "schema_contract",
            "fallback_trigger_reason": "schema_validation_retry_not_available",
            "fallback_result": "exhausted",
            "review_trigger_reason": "manual_review_required",
            "review_outcome": "rejected",
            "provider": "openai",
            "model": "gpt-4o",
        },
    )

    record = AgenticEvalRecord.from_event(event)

    assert record.workflow == "extraction"
    assert record.failure_layer == "schema"
    assert record.next_fix_layer == "schema_contract"
    assert record.provider == "openai"
    assert record.model == "gpt-4o"


def test_build_repeated_failure_signal_aggregates_once_threshold_is_met():
    base = datetime(2026, 6, 18, 10, 0, tzinfo=timezone.utc)
    events = [
        _event(id="e1", created_at=base - timedelta(minutes=3), event_metadata={"failure_signature": "sig-a", "failure_layer": "schema", "next_fix_layer": "schema_contract"}),
        _event(id="e2", created_at=base - timedelta(minutes=2), event_metadata={"failure_signature": "sig-a", "failure_layer": "schema", "next_fix_layer": "schema_contract"}),
        _event(id="e3", created_at=base, event_metadata={"failure_signature": "sig-a", "failure_layer": "schema", "next_fix_layer": "schema_contract"}),
    ]

    work_items = build_repeated_failure_signal(events, min_occurrences=3)

    assert len(work_items) == 1
    item = work_items[0]
    assert item.occurrences == 3
    assert item.failure_signature == "sig-a"
    assert item.sample_events == ["e1", "e2", "e3"]
    assert item.severity == "low"
    assert item.owner == "schema-platform"
    assert item.proposed_change == "Adjust schema constraints, optionality, and failure messaging."
    assert item.rerun_subset is not None


def test_build_repeated_failure_signal_ignores_sub_threshold_signals():
    base = datetime(2026, 6, 18, 10, 0, tzinfo=timezone.utc)
    events = [
        _event(id="e1", created_at=base - timedelta(minutes=2), event_metadata={"failure_signature": "sig-a"}),
        _event(id="e2", created_at=base, event_metadata={"failure_signature": "sig-a"}),
    ]

    work_items = build_repeated_failure_signal(events, min_occurrences=3)

    assert work_items == []


def test_filter_eval_candidates_selects_eval_ready_events():
    events = [
        _event(id="e1", event_metadata={}),
        _event(id="e2", event_metadata={"failure_signature": "sig-a"}),
        _event(id="e3", event_metadata={"provider": "openai"}),
    ]

    candidates = filter_eval_candidates(events)

    assert [event.id for event in candidates] == ["e2"]


def test_build_repeated_failure_signal_severity_increases_with_repetition():
    base = datetime(2026, 6, 18, 10, 0, tzinfo=timezone.utc)
    events = [
        _event(
            id=f"e{idx}",
            created_at=base + timedelta(minutes=idx),
            event_metadata={"failure_signature": "sig-a", "failure_layer": "routing", "next_fix_layer": "routing"},
        )
        for idx in range(12)
    ]

    work_items = build_repeated_failure_signal(events, min_occurrences=3)

    assert len(work_items) == 1
    assert work_items[0].failure_signature == "sig-a"
    assert work_items[0].severity == "high"
    assert "routing" in (work_items[0].proposed_change or "")


def test_build_canonical_evidence_records_maps_non_extraction_events():
    records = build_canonical_evidence_records(
        [
            _event(
                id="doc-1",
                event_type="document_accepted",
                event_category="document",
                subject_type="booking_document",
                event_metadata={"input_artifact_id": "doc-xyz", "review_outcome": "accepted"},
            )
        ]
    )

    assert len(records) == 1
    assert records[0]["workflow_type"] == "document"
    assert records[0]["final_acceptance_status"] == "accepted"


def test_extract_metadata_signature_is_stable():
    payload = {
        "document_type": "passport",
        "provider": "openai",
        "model": "gpt-4o",
        "error_code": "schema_validation_failed",
        "attempt_number": 2,
        "fallback_rank": 1,
    }

    assert (
        extract_metadata_signature(payload)
        == "passport|openai|gpt-4o|schema_validation_failed|2|1"
    )


def test_aggregate_eval_records_respects_window_minutes():
    now = datetime(2026, 6, 18, 10, 0, tzinfo=timezone.utc)
    events = [
        _event(
            id="e1",
            created_at=now - timedelta(minutes=180),
            event_metadata={"failure_signature": "old"},
        ),
        _event(
            id="e2",
            created_at=now - timedelta(minutes=15),
            event_metadata={"failure_signature": "new", "failure_layer": "schema", "next_fix_layer": "schema_contract"},
        ),
        _event(
            id="e3",
            created_at=now - timedelta(minutes=10),
            event_metadata={"failure_signature": "new", "failure_layer": "schema", "next_fix_layer": "schema_contract"},
        ),
        _event(
            id="e4",
            created_at=now - timedelta(minutes=5),
            event_metadata={"failure_signature": "new", "failure_layer": "schema", "next_fix_layer": "schema_contract"},
        ),
    ]

    summary = aggregate_eval_records(
        events,
        min_occurrences=3,
        window_minutes=120,
        reference_time=now,
    )

    assert summary["window_minutes"] == 120
    assert summary["total_events_considered"] == 3
    assert summary["work_items"][0]["failure_signature"] == "new"
    assert summary["work_items"][0]["occurrences"] == 3


def test_aggregate_eval_records_includes_canonical_evidence_records():
    now = datetime(2026, 6, 18, 10, 0, tzinfo=timezone.utc)
    events = [
        _event(
            id="r1",
            created_at=now,
            event_type="extraction_run_completed",
            event_metadata={
                "failure_signature": "sig-a",
                "failure_layer": "schema",
                "next_fix_layer": "schema_contract",
                "input_artifact_id": "doc-a",
                "prompt_version": "p1",
                "schema_version": "s1",
                "fallback_result": "succeeded_after_fallback",
                "review_trigger_reason": "manual_review_required",
                "review_outcome": "applied",
                "latency_ms": 120,
                "cost_estimate_usd": 0.12,
            },
        )
    ]

    summary = aggregate_eval_records(
        events,
        min_occurrences=1,
        window_minutes=120,
        reference_time=now,
    )

    records = summary["canonical_evidence_records"]
    assert len(records) == 1
    assert records[0]["workflow_unit_id"] == "r1"
    assert records[0]["workflow_type"] == "extraction"
    assert records[0]["input_artifact_id"] == "doc-a"
    assert records[0]["prompt_version"] == "p1"
    assert records[0]["schema_version"] == "s1"
    assert records[0]["final_acceptance_status"] == "pending_review"


def test_build_canonical_evidence_records_limits_output():
    now = datetime(2026, 6, 18, 10, 0, tzinfo=timezone.utc)
    events = [
        _event(
            id=f"evt-{idx}",
            created_at=now,
            event_type="extraction_run_failed",
            event_metadata={"failure_signature": "sig-a", "failure_layer": "schema"},
        )
        for idx in range(201)
    ]

    records = build_canonical_evidence_records(events)

    assert len(records) == 200


def test_build_canonical_evidence_records_uses_review_escalation_outcome_by_workflow_unit():
    now = datetime(2026, 6, 18, 10, 0, tzinfo=timezone.utc)
    events = [
        _event(
            id="r1",
            created_at=now,
            event_type="extraction_run_failed",
            event_metadata={"failure_signature": "sig-a", "failure_layer": "schema", "next_fix_layer": "schema_contract"},
        ),
        _event(
            id="r2",
            created_at=now,
            event_type="extraction_run_failed",
            event_metadata={"failure_signature": "sig-b", "failure_layer": "schema", "next_fix_layer": "schema_contract"},
        ),
    ]
    review_events = [
        {
            "type": "review_action",
            "details": {
                "trip_id": "trip_001",
                "review_workflow_unit_id": "r1",
                "escalation_outcome": "false_escalation",
            },
        },
        {
            "type": "review_action",
            "details": {
                "trip_id": "trip_001",
                "review_workflow_unit_id": "r2",
                "escalation_outcome": "missed_escalation",
            },
        },
    ]

    records = build_canonical_evidence_records(events, review_events=review_events)

    escalations = {row["workflow_unit_id"]: row["escalation_outcome"] for row in records}
    assert escalations["r1"] == "false_escalation"
    assert escalations["r2"] == "missed_escalation"


def test_build_routing_metrics_calculates_fallback_and_review_health():
    events = [
        _event(
            id="r1",
            created_at=datetime(2026, 6, 18, 10, 0, tzinfo=timezone.utc),
            event_metadata={
                "fallback_trigger_reason": "schema_validation_retry_available",
                "fallback_result": "succeeded_after_fallback",
                "latency_ms": 100,
                "cost_estimate_usd": 0.10,
                "review_trigger_reason": "manual_review_required",
                "review_outcome": "applied",
            },
        ),
        _event(
            id="r2",
            created_at=datetime(2026, 6, 18, 10, 2, tzinfo=timezone.utc),
            event_metadata={
                "fallback_trigger_reason": "missing_data_retry_available",
                "fallback_result": "exhausted",
                "latency_ms": 200,
                "cost_estimate_usd": 0.20,
                "review_trigger_reason": "policy_review_required",
                "review_outcome": "rejected",
            },
        ),
        _event(
            id="r3",
            created_at=datetime(2026, 6, 18, 10, 4, tzinfo=timezone.utc),
            event_metadata={
                "review_trigger_reason": "quality_threshold",
                "review_outcome": "manual_reject",
            },
        ),
        _event(
            id="r4",
            created_at=datetime(2026, 6, 18, 10, 6, tzinfo=timezone.utc),
            event_metadata={"failure_signature": "sig-a"},
        ),
    ]

    metrics = build_routing_metrics(events)

    assert metrics["fallback_trigger_count"] == 2
    assert metrics["useful_fallback_count"] == 1
    assert metrics["wasteful_fallback_count"] == 1
    assert metrics["fallback_trigger_rate"] == 0.5
    assert metrics["review_trigger_count"] == 3
    assert metrics["review_accept_count"] == 1
    assert metrics["review_reject_count"] == 2
    assert metrics["review_correction_rate"] == 0.667
    assert metrics["latency_by_candidates"]["count"] == 2
    assert metrics["latency_by_candidates"]["avg_ms"] == 150.0
    assert metrics["cost_usd"]["event_count_with_cost"] == 2
    assert metrics["cost_usd"]["avg_per_eval_event"] == 0.075


def test_build_routing_metrics_includes_explicit_escalation_outcomes_from_review_events():
    events = [
        _event(
            id="r1",
            created_at=datetime(2026, 6, 18, 10, 0, tzinfo=timezone.utc),
            event_metadata={"failure_signature": "sig-a"},
        )
    ]
    review_events = [
        {
            "type": "review_action",
            "details": {"trip_id": "trip_001", "escalation_outcome": "false_escalation"},
        },
        {
            "type": "review_action",
            "details": {"trip_id": "trip_001", "escalation_outcome": "missed_escalation"},
        },
        {
            "type": "review_action",
            "details": {"trip_id": "trip_001", "escalation_outcome": "correct_escalation"},
        },
    ]

    metrics = build_routing_metrics(events, review_events=review_events)

    assert metrics["escalation_outcome_count"] == 3
    assert metrics["false_escalation_count"] == 1
    assert metrics["missed_escalation_count"] == 1
    assert metrics["correct_escalation_count"] == 1
    assert metrics["false_escalation_rate"] == 0.333
    assert metrics["missed_escalation_rate"] == 0.333


def test_build_routing_metrics_scopes_escalation_outcomes_to_candidate_unit_ids():
    events = [
        _event(
            id="r1",
            created_at=datetime(2026, 6, 18, 10, 0, tzinfo=timezone.utc),
            event_metadata={"failure_signature": "sig-a"},
        ),
        _event(
            id="r2",
            created_at=datetime(2026, 6, 18, 10, 2, tzinfo=timezone.utc),
            event_metadata={"failure_signature": "sig-b"},
        ),
    ]
    review_events = [
        {
            "type": "review_action",
            "details": {
                "trip_id": "trip_001",
                "review_workflow_unit_id": "r1",
                "escalation_outcome": "false_escalation",
            },
        },
        {
            "type": "review_action",
            "details": {
                "trip_id": "trip_001",
                "review_workflow_unit_id": "r2",
                "escalation_outcome": "missed_escalation",
            },
        },
        {
            "type": "review_action",
            "details": {
                "trip_id": "trip_001",
                "escalation_outcome": "correct_escalation",
            },
        },
    ]

    metrics = build_routing_metrics(
        events,
        review_events=review_events,
        workflow_unit_ids={"r1"},
    )

    assert metrics["escalation_outcome_count"] == 1
    assert metrics["false_escalation_count"] == 1
    assert metrics["missed_escalation_count"] == 0
    assert metrics["correct_escalation_count"] == 0


# ---------------------------------------------------------------------------
# check_routing_health tests
# ---------------------------------------------------------------------------


def test_check_routing_health_healthy_when_all_normal():
    metrics = {
        "fallback_trigger_rate": 0.1,
        "false_escalation_rate": 0.05,
        "missed_escalation_rate": 0.05,
        "review_correction_rate": 0.1,
        "latency_by_candidates": {"p50_ms": 1000, "p95_ms": 3000},
    }
    report = check_routing_health(metrics)
    assert report.status == "healthy"
    assert report.alerts == []
    assert isinstance(report.checked_at, datetime)
    assert report.metrics_snapshot is metrics


def test_check_routing_health_warning_on_fallback_rate():
    metrics = {
        "fallback_trigger_rate": 0.35,
        "false_escalation_rate": 0.05,
        "latency_by_candidates": {"p50_ms": 1000, "p95_ms": 3000},
    }
    report = check_routing_health(metrics)
    assert report.status == "warning"
    assert len(report.alerts) == 1
    assert report.alerts[0].metric == "fallback_trigger_rate"
    assert report.alerts[0].severity == "warning"
    assert report.alerts[0].actual_value == 0.35


def test_check_routing_health_critical_on_false_escalation():
    metrics = {
        "fallback_trigger_rate": 0.1,
        "false_escalation_rate": 0.45,
        "latency_by_candidates": {"p50_ms": 1000, "p95_ms": 3000},
    }
    report = check_routing_health(metrics)
    assert report.status == "critical"
    assert len(report.alerts) == 1
    assert report.alerts[0].severity == "critical"
    assert report.alerts[0].metric == "false_escalation_rate"


def test_check_routing_health_critical_overrides_warning():
    metrics = {
        "fallback_trigger_rate": 0.35,  # warning
        "false_escalation_rate": 0.45,  # critical
        "latency_by_candidates": {"p50_ms": 1000, "p95_ms": 3000},
    }
    report = check_routing_health(metrics)
    assert report.status == "critical"
    assert len(report.alerts) == 2
    severities = {a.severity for a in report.alerts}
    assert "warning" in severities
    assert "critical" in severities


def test_check_routing_health_latency_alerts():
    metrics = {
        "fallback_trigger_rate": 0.05,
        "latency_by_candidates": {"p50_ms": 12_000, "p95_ms": 35_000},
    }
    report = check_routing_health(metrics)
    assert report.status == "critical"
    latency_alerts = [a for a in report.alerts if "latency" in a.metric]
    assert len(latency_alerts) == 2
    p50_alert = next(a for a in latency_alerts if "p50" in a.metric)
    assert p50_alert.severity == "critical"  # 12000 >= 10000 critical
    p95_alert = next(a for a in latency_alerts if "p95" in a.metric)
    assert p95_alert.severity == "critical"  # 35000 >= 30000 critical


def test_check_routing_health_skips_none_values():
    metrics = {
        "fallback_trigger_rate": 0.1,
        "false_escalation_rate": None,
        "missed_escalation_rate": None,
        "latency_by_candidates": {},
    }
    report = check_routing_health(metrics)
    assert report.status == "healthy"
    assert report.alerts == []


def test_check_routing_health_custom_thresholds():
    metrics = {
        "fallback_trigger_rate": 0.15,
        "latency_by_candidates": {"p50_ms": 3000, "p95_ms": 8000},
    }
    custom = {
        "fallback_trigger_rate_warning": 0.1,
        "fallback_trigger_rate_critical": 0.2,
        "latency_p50_ms_warning": 2000,
        "latency_p50_ms_critical": 5000,
        "latency_p95_ms_warning": 5000,
        "latency_p95_ms_critical": 10000,
    }
    report = check_routing_health(metrics, thresholds=custom)
    assert report.status == "warning"
    assert len(report.alerts) == 3  # fallback + p50 + p95
    alert_metrics = {a.metric for a in report.alerts}
    assert "fallback_trigger_rate" in alert_metrics
    assert "latency_p50_ms" in alert_metrics
    assert "latency_p95_ms" in alert_metrics


def test_check_routing_health_review_correction_rate():
    metrics = {
        "fallback_trigger_rate": 0.05,
        "review_correction_rate": 0.55,
        "latency_by_candidates": {"p50_ms": 1000, "p95_ms": 3000},
    }
    report = check_routing_health(metrics)
    assert report.status == "critical"
    rc_alerts = [a for a in report.alerts if a.metric == "review_correction_rate"]
    assert len(rc_alerts) == 1
    assert rc_alerts[0].severity == "critical"


def test_check_routing_health_missed_escalation_rate():
    metrics = {
        "fallback_trigger_rate": 0.05,
        "missed_escalation_rate": 0.25,
        "latency_by_candidates": {"p50_ms": 1000, "p95_ms": 3000},
    }
    report = check_routing_health(metrics)
    assert report.status == "warning"
    me_alerts = [a for a in report.alerts if a.metric == "missed_escalation_rate"]
    assert len(me_alerts) == 1
    assert me_alerts[0].severity == "warning"


def test_check_routing_health_summary_json_serialisable():
    metrics = {
        "fallback_trigger_rate": 0.6,
        "latency_by_candidates": {"p50_ms": 12_000, "p95_ms": 40_000},
    }
    report = check_routing_health(metrics)
    summary = report.summary()
    serialised = json.dumps(summary)
    assert "critical" in serialised
    assert summary["status"] == "critical"
    assert summary["alert_count"] == 3  # fallback + p50 + p95


def test_build_routing_metrics_uses_legacy_outcomes_without_unit_links():
    events = [
        _event(
            id="r1",
            created_at=datetime(2026, 6, 18, 10, 0, tzinfo=timezone.utc),
            event_metadata={"failure_signature": "sig-a"},
        )
    ]
    review_events = [
        {
            "type": "review_action",
            "details": {
                "trip_id": "trip_001",
                "escalation_outcome": "correct_escalation",
            },
        },
    ]

    metrics = build_routing_metrics(
        events,
        review_events=review_events,
        workflow_unit_ids={"r1"},
    )

    assert metrics["escalation_outcome_count"] == 1
    assert metrics["correct_escalation_count"] == 1
