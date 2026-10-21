"""Tests for OpenTelemetry trace correlation reader and CI event flow assertions (R-16 / FND-0214)."""

import pytest
from datetime import datetime, timedelta, timezone

from src.analytics.trace_reader import (
    TraceCorrelationReader,
    assert_trace_event_flow,
)


def test_trace_correlation_hierarchical_dag():
    t0 = datetime.now(timezone.utc)
    events = [
        {
            "trace_id": "tr_001",
            "span_id": "sp_root",
            "event_type": "pipeline.run.started",
            "timestamp": t0.isoformat(),
            "agency_id": "agency_1",
        },
        {
            "trace_id": "tr_001",
            "span_id": "sp_child_1",
            "parent_span_id": "sp_root",
            "event_type": "intake.extracted",
            "timestamp": (t0 + timedelta(milliseconds=50)).isoformat(),
            "agency_id": "agency_1",
        },
        {
            "trace_id": "tr_001",
            "span_id": "sp_child_2",
            "parent_span_id": "sp_root",
            "event_type": "decision.evaluated",
            "timestamp": (t0 + timedelta(milliseconds=100)).isoformat(),
            "agency_id": "agency_1",
        },
        {
            "trace_id": "tr_001",
            "span_id": "sp_subchild",
            "parent_span_id": "sp_child_2",
            "event_type": "strategy.synthesized",
            "timestamp": (t0 + timedelta(milliseconds=150)).isoformat(),
            "agency_id": "agency_1",
        },
    ]

    reader = TraceCorrelationReader()
    reader.ingest_events(events)

    roots = reader.get_trace_roots("tr_001")
    assert len(roots) == 1
    root = roots[0]
    assert root.span_id == "sp_root"
    assert len(root.children) == 2
    assert {c.span_id for c in root.children} == {"sp_child_1", "sp_child_2"}

    child_2 = next(c for c in root.children if c.span_id == "sp_child_2")
    assert len(child_2.children) == 1
    assert child_2.children[0].span_id == "sp_subchild"


def test_validate_event_flow_sequence_pass_and_fail():
    t0 = datetime.now(timezone.utc)
    events = [
        {"trace_id": "tr_002", "span_id": "s1", "event_type": "INTAKE", "timestamp": t0.isoformat(), "agency_id": "a1"},
        {"trace_id": "tr_002", "span_id": "s2", "event_type": "DECISION", "timestamp": (t0 + timedelta(seconds=1)).isoformat(), "agency_id": "a1"},
        {"trace_id": "tr_002", "span_id": "s3", "event_type": "OUTPUT", "timestamp": (t0 + timedelta(seconds=2)).isoformat(), "agency_id": "a1"},
    ]

    reader = TraceCorrelationReader()
    reader.ingest_events(events)

    # Valid sequence
    errors = reader.validate_event_flow("tr_002", required_sequence=["INTAKE", "DECISION", "OUTPUT"])
    assert not errors

    # Missing/invalid sequence
    errors_fail = reader.validate_event_flow("tr_002", required_sequence=["DECISION", "INTAKE"])
    assert len(errors_fail) == 1
    assert "Required event 'INTAKE' was missing or out of sequence" in errors_fail[0]


def test_cross_tenant_pollution_detection():
    t0 = datetime.now(timezone.utc)
    events = [
        {"trace_id": "tr_polluted", "span_id": "s1", "event_type": "START", "timestamp": t0.isoformat(), "agency_id": "agency_A"},
        {"trace_id": "tr_polluted", "span_id": "s2", "event_type": "WORK", "timestamp": (t0 + timedelta(seconds=1)).isoformat(), "agency_id": "agency_B"},
    ]

    reader = TraceCorrelationReader()
    reader.ingest_events(events)
    errors = reader.validate_event_flow("tr_polluted")
    assert any("Cross-tenant pollution detected" in err for err in errors)


def test_assert_trace_event_flow_helper():
    t0 = datetime.now(timezone.utc)
    events = [
        {"trace_id": "tr_ci", "span_id": "s1", "event_type": "PASS", "timestamp": t0.isoformat(), "agency_id": "a1"},
    ]
    # Should pass without error
    assert_trace_event_flow(events, "tr_ci", required_sequence=["PASS"])

    # Should raise AssertionError on mismatch
    with pytest.raises(AssertionError, match="Trace event flow assertion failed"):
        assert_trace_event_flow(events, "tr_ci", required_sequence=["MISSING"])
