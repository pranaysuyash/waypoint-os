from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from src.evals.agentic_feedback import (
    AgenticEvalRecord,
    aggregate_eval_records,
    build_repeated_failure_signal,
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
