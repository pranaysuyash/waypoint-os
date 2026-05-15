"""Tests for the requeue port layer: DisabledSpineRequeuePort, InlineSpineRequeuePort,
_RawCallableRequeuePort, build_requeue_port, and RecoveryAgent integration.

All tests are synchronous and do not require PostgreSQL.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

import pytest

from src.agents.recovery_agent import RecoveryAgent, RecoveryResult
from src.agents.requeue import (
    DisabledSpineRequeuePort,
    InlineSpineRequeuePort,
    RequeueResult,
    _RawCallableRequeuePort,
    build_requeue_port,
)


class TestDisabledSpineRequeuePort:
    """Disabled port always returns not-accepted."""

    def test_returns_not_accepted_with_disabled_mode(self):
        port = DisabledSpineRequeuePort()
        result = port.requeue_trip("t1", {}, "stuck", 1)

        assert result.accepted is False
        assert result.mode == "disabled"
        assert "not configured" in result.reason

    def test_does_not_accept_even_with_full_record(self):
        port = DisabledSpineRequeuePort()
        result = port.requeue_trip("t1", {"raw_input": {"raw_note": "test"}}, "stuck", 1)

        assert result.accepted is False


class TestRawCallableRequeuePort:
    """Backward-compat adapter for spine_runner callables."""

    def test_accepts_when_callable_succeeds(self):
        calls = []

        def _runner(tid: str):
            calls.append(tid)

        port = _RawCallableRequeuePort(spine_runner=_runner)
        result = port.requeue_trip("t1", {}, "stuck 10h in intake", 1)

        assert result.accepted is True
        assert result.mode == "inline"
        assert calls == ["t1"]

    def test_rejected_when_callable_raises(self):
        def _runner(tid: str):
            raise RuntimeError("queue offline")

        port = _RawCallableRequeuePort(spine_runner=_runner)
        result = port.requeue_trip("t1", {}, "stuck", 1)

        assert result.accepted is False
        assert result.mode == "inline"
        assert result.retryable is True
        assert "queue offline" in result.reason


class TestInlineSpineRequeuePort:
    """Pipeline-aware requeue port."""

    def test_rejects_when_raw_input_missing(self):
        calls = []

        def _run_spine(**kwargs):
            calls.append(kwargs)

        port = InlineSpineRequeuePort(run_spine=_run_spine)
        result = port.requeue_trip("t1", {"stage": "intake"}, "stuck", 1)

        assert result.accepted is False
        assert result.mode == "inline"
        assert "no raw_input data" in result.reason
        assert calls == []

    def test_rejects_when_raw_input_empty_dict(self):
        calls = []

        def _run_spine(**kwargs):
            calls.append(kwargs)

        port = InlineSpineRequeuePort(run_spine=_run_spine)
        result = port.requeue_trip("t1", {"raw_input": {}}, "stuck", 1)

        assert result.accepted is False
        assert calls == []

    def test_calls_runner_with_envelopes_and_stage(self):
        captured = []

        def _run_spine(**kwargs):
            captured.append(kwargs)
            return {"ok": True}

        port = InlineSpineRequeuePort(run_spine=_run_spine)
        result = port.requeue_trip(
            "t1",
            {"raw_input": {"raw_note": "Singapore trip"}, "stage": "intake"},
            "stuck 10h in intake",
            1,
        )

        assert result.accepted is True
        assert result.mode == "inline"
        assert len(captured) == 1
        assert captured[0]["envelopes"] == [{"raw_note": "Singapore trip"}]
        assert captured[0]["stage"] == "intake"

    def test_uses_status_as_fallback_stage(self):
        captured = []

        def _run_spine(**kwargs):
            captured.append(kwargs)

        port = InlineSpineRequeuePort(run_spine=_run_spine)
        port.requeue_trip("t1", {"raw_input": {"x": "y"}, "status": "proposal"}, "stuck", 1)

        assert captured[0]["stage"] == "proposal"

    def test_defaults_stage_to_discovery(self):
        captured = []

        def _run_spine(**kwargs):
            captured.append(kwargs)

        port = InlineSpineRequeuePort(run_spine=_run_spine)
        port.requeue_trip("t1", {"raw_input": {"x": "y"}}, "stuck", 1)

        assert captured[0]["stage"] == "discovery"

    def test_runner_exception_returns_not_accepted_retryable(self):
        def _run_spine(**kwargs):
            raise RuntimeError("pipeline timeout")

        port = InlineSpineRequeuePort(run_spine=_run_spine)
        result = port.requeue_trip(
            "t1",
            {"raw_input": {"raw_note": "test"}, "stage": "intake"},
            "stuck",
            1,
        )

        assert result.accepted is False
        assert result.mode == "inline"
        assert result.retryable is True
        assert "pipeline timeout" in result.reason


class TestBuildRequeuePort:
    """Builder function mapping."""

    def test_builder_defaults_to_disabled(self):
        port = build_requeue_port()
        assert isinstance(port, DisabledSpineRequeuePort)

    def test_builder_inline_without_runner_returns_disabled(self):
        port = build_requeue_port("inline")
        assert isinstance(port, DisabledSpineRequeuePort)

    def test_builder_inline_with_runner_returns_inline(self):
        port = build_requeue_port("inline", run_spine=lambda **kw: None)
        assert isinstance(port, InlineSpineRequeuePort)

    def test_builder_spine_runner_returns_raw_adapter(self):
        port = build_requeue_port(spine_runner=lambda tid: None)
        assert isinstance(port, _RawCallableRequeuePort)

    def test_builder_spine_runner_takes_precedence_over_bare_mode(self):
        port = build_requeue_port("disabled", spine_runner=lambda tid: None)
        assert isinstance(port, _RawCallableRequeuePort)


class _Audit:
    def __init__(self):
        self.events = []

    def log(self, event_type: str, trip_id: str, payload: dict, user_id: str | None = None):
        self.events.append({"event_type": event_type, "trip_id": trip_id, "payload": payload, "user_id": user_id})


class _TripRepo:
    def __init__(self, trips):
        self._trips = {t["id"]: dict(t) for t in trips}
        self.review_updates = []

    def list_active(self):
        return list(self._trips.values())

    def set_review_status(self, trip_id: str, status: str):
        self.review_updates.append((trip_id, status))


class _FakeInlinePort:
    """A controlled InlineSpineRequeuePort stand-in that accepts or not."""

    def __init__(self, accept: bool = True):
        self._accept = accept
        self.called_with = []

    def requeue_trip(self, trip_id, trip_record, reason, attempt):
        self.called_with.append((trip_id, reason, attempt))
        if self._accept:
            return RequeueResult(accepted=True, mode="inline", reason=reason)
        return RequeueResult(accepted=False, mode="inline", reason="transient error", retryable=True)


class TestRecoveryAgentWithPort:
    """RecoveryAgent integration with explicit requeue_port."""

    def test_disabled_port_escalates(self):
        now = datetime.now(timezone.utc)
        repo = _TripRepo([{"id": "t1", "stage": "intake", "updated_at": (now - timedelta(hours=48)).isoformat()}])
        audit = _Audit()
        agent = RecoveryAgent(
            interval_seconds=1,
            audit_store=audit,
            trip_repo=repo,
            requeue_port=DisabledSpineRequeuePort(),
        )
        results = agent.run_once()

        assert len(results) == 1
        assert results[0].action == "escalate"
        assert results[0].success is True
        assert repo.review_updates == [("t1", "escalated")]

    def test_inline_port_accepted_increments_attempt(self):
        now = datetime.now(timezone.utc)
        repo = _TripRepo([{"id": "t1", "stage": "intake", "updated_at": (now - timedelta(hours=48)).isoformat()}])
        audit = _Audit()
        agent = RecoveryAgent(
            interval_seconds=1,
            audit_store=audit,
            trip_repo=repo,
            requeue_port=_FakeInlinePort(accept=True),
        )

        results = agent.run_once()
        assert len(results) == 1
        assert results[0].action == "re_queue"
        assert results[0].success is True

        # second run: trip already requeued, requeue_attempts=1, under max=2, still re-queue
        results = agent.run_once()
        assert results[0].action == "re_queue"
        assert results[0].success is True

        # third run: requeue_attempts=2, max=2, now escalate
        results = agent.run_once()
        assert results[0].action == "escalate"

    def test_inline_port_rejected_does_not_increment_attempt(self):
        now = datetime.now(timezone.utc)
        repo = _TripRepo([{"id": "t1", "stage": "intake", "updated_at": (now - timedelta(hours=48)).isoformat()}])
        audit = _Audit()
        agent = RecoveryAgent(
            interval_seconds=1,
            audit_store=audit,
            trip_repo=repo,
            requeue_port=_FakeInlinePort(accept=False),
        )

        results = agent.run_once()

        assert len(results) == 1
        assert results[0].action == "re_queue"
        assert results[0].success is False

        # second run: attempt NOT incremented (not accepted), tries again
        results = agent.run_once()
        assert results[0].action == "re_queue"
        assert results[0].success is False

    def test_inline_port_failure_emits_agent_failed_audit(self):
        now = datetime.now(timezone.utc)
        repo = _TripRepo([{"id": "t1", "stage": "intake", "updated_at": (now - timedelta(hours=48)).isoformat()}])
        audit = _Audit()
        agent = RecoveryAgent(
            interval_seconds=1,
            audit_store=audit,
            trip_repo=repo,
            requeue_port=_FakeInlinePort(accept=False),
        )

        agent.run_once()

        failed_events = [
            e for e in audit.events
            if e["payload"].get("event_type") == "agent_failed"
        ]
        assert len(failed_events) == 1
        payload = failed_events[0]["payload"]["payload"]
        assert payload["action"] == "re_queue"
        assert payload["success"] is False

    def test_inline_port_success_emits_agent_action_audit(self):
        now = datetime.now(timezone.utc)
        repo = _TripRepo([{"id": "t1", "stage": "intake", "updated_at": (now - timedelta(hours=48)).isoformat()}])
        audit = _Audit()
        agent = RecoveryAgent(
            interval_seconds=1,
            audit_store=audit,
            trip_repo=repo,
            requeue_port=_FakeInlinePort(accept=True),
        )

        agent.run_once()

        action_events = [
            e for e in audit.events
            if e["payload"].get("event_type") == "agent_action"
        ]
        assert len(action_events) == 1
        payload = action_events[0]["payload"]["payload"]
        assert payload["action"] == "re_queue"
        assert payload["success"] is True
