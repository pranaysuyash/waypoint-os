from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from src.agents.recovery_agent import RecoveryAgent
from spine_api.persistence import AuditStore


@dataclass
class _Trip:
    id: str
    stage: str
    updated_at: datetime


class _TripRepo:
    def __init__(self, trips):
        self._trips = trips
        self.review_updates = []

    def list_active(self):
        return self._trips

    def set_review_status(self, trip_id: str, status: str):
        self.review_updates.append((trip_id, status))


class _Audit:
    def __init__(self):
        self.events = []

    def log(self, event_type: str, trip_id: str, payload: dict):
        self.events.append({"event_type": event_type, "trip_id": trip_id, "payload": payload})


def test_recovery_agent_requeues_when_under_limit(monkeypatch):
    monkeypatch.setenv("RECOVERY_STUCK_INTAKE_H", "1")
    monkeypatch.setenv("RECOVERY_MAX_REQUEUE", "2")
    now = datetime.now(timezone.utc)
    repo = _TripRepo([_Trip(id="t1", stage="intake", updated_at=now - timedelta(hours=3))])
    audit = _Audit()
    seen = []

    def _runner(trip_id: str):
        seen.append(trip_id)

    agent = RecoveryAgent(interval_seconds=1, audit_store=audit, trip_repo=repo, spine_runner=_runner)
    results = agent.run_once()

    assert len(results) == 1
    assert results[0].action == "re_queue"
    assert results[0].success is True
    assert seen == ["t1"]
    assert any(
        e["payload"].get("event_type") == "agent_decision" and e["payload"].get("agent_name") == "recovery_agent"
        for e in audit.events
    )
    assert any(
        e["payload"].get("event_type") == "agent_action" and e["payload"]["payload"].get("action") == "re_queue"
        for e in audit.events
    )


def test_recovery_agent_escalates_after_requeue_limit(monkeypatch):
    monkeypatch.setenv("RECOVERY_STUCK_INTAKE_H", "1")
    monkeypatch.setenv("RECOVERY_MAX_REQUEUE", "1")
    now = datetime.now(timezone.utc)
    repo = _TripRepo([_Trip(id="t2", stage="intake", updated_at=now - timedelta(hours=4))])
    audit = _Audit()
    calls = []

    def _runner(trip_id: str):
        calls.append(trip_id)

    agent = RecoveryAgent(interval_seconds=1, audit_store=audit, trip_repo=repo, spine_runner=_runner)
    agent.run_once()  # first pass re-queue
    results = agent.run_once()  # second pass escalate

    assert len(results) == 1
    assert results[0].action == "escalate"
    assert results[0].success is True
    assert repo.review_updates == [("t2", "escalated")]
    assert calls == ["t2"]
    assert any(
        e["payload"].get("event_type") == "agent_action" and e["payload"]["payload"].get("action") == "escalate"
        for e in audit.events
    )


def test_recovery_agent_fail_closed_on_runner_error(monkeypatch):
    monkeypatch.setenv("RECOVERY_STUCK_INTAKE_H", "1")
    monkeypatch.setenv("RECOVERY_MAX_REQUEUE", "2")
    now = datetime.now(timezone.utc)
    repo = _TripRepo([_Trip(id="t3", stage="intake", updated_at=now - timedelta(hours=5))])
    audit = _Audit()

    def _runner(_trip_id: str):
        raise RuntimeError("queue offline")

    agent = RecoveryAgent(interval_seconds=1, audit_store=audit, trip_repo=repo, spine_runner=_runner)
    results = agent.run_once()

    assert len(results) == 1
    assert results[0].action == "re_queue"
    assert results[0].success is False
    assert "failed" in results[0].reason.lower()
    assert any(
        e["payload"].get("event_type") == "agent_failed" and "queue offline" in e["payload"]["payload"].get("reason", "")
        for e in audit.events
    )


def test_recovery_agent_detects_dict_trip_records(monkeypatch):
    monkeypatch.setenv("RECOVERY_STUCK_REVIEW_H", "1")
    now = datetime.now(timezone.utc)

    class _DictRepo:
        def list_active(self):
            return [{"id": "t_dict", "stage": "review", "updated_at": (now - timedelta(hours=3)).isoformat()}]

        def set_review_status(self, trip_id: str, status: str):
            self.updated = (trip_id, status)

    repo = _DictRepo()
    audit = _Audit()
    agent = RecoveryAgent(interval_seconds=1, audit_store=audit, trip_repo=repo, spine_runner=None)

    results = agent.run_once()

    assert len(results) == 1
    assert results[0].trip_id == "t_dict"
    assert results[0].action == "escalate"
    assert repo.updated == ("t_dict", "escalated")


def test_audit_store_agent_events_for_trip_filters_by_type_and_trip(monkeypatch):
    raw_events = [
        {"type": "trip_created", "details": {"trip_id": "t4"}},
        {"type": "agent_event", "details": {"trip_id": "t4", "event_type": "agent_decision"}},
        {"type": "agent_event", "details": {"trip_id": "t9", "event_type": "agent_action"}},
        {"type": "agent_event", "details": {"trip_id": "t4", "event_type": "agent_action"}},
    ]
    monkeypatch.setattr(AuditStore, "_read_events", staticmethod(lambda: raw_events))
    events = AuditStore.get_agent_events_for_trip("t4", limit=10)
    assert len(events) == 2
    assert {e["details"]["event_type"] for e in events} == {"agent_decision", "agent_action"}
