from __future__ import annotations

from datetime import datetime, timedelta, timezone

from src.agents.tool_contracts import ToolFreshnessPolicy, ToolResult
from src.agents.runtime import (
    AgentSupervisor,
    DocumentReadinessAgent,
    FrontDoorAgent,
    FollowUpAgent,
    InMemoryWorkCoordinator,
    QualityEscalationAgent,
    SalesActivationAgent,
    WorkItem,
    WorkStatus,
    build_default_registry,
)


class _Repo:
    def __init__(self, trips):
        self.trips = {trip["id"]: dict(trip) for trip in trips}
        self.update_calls = []
        self.fail_updates_for: set[str] = set()

    def list_active(self):
        return list(self.trips.values())

    def update_trip(self, trip_id: str, updates: dict):
        self.update_calls.append((trip_id, updates))
        if trip_id in self.fail_updates_for:
            return None
        trip = self.trips.get(trip_id)
        if not trip:
            return None
        trip.update(updates)
        return trip


class _Audit:
    def __init__(self):
        self.events = []

    def log(self, event_type: str, trip_id: str, payload: dict, user_id: str | None = None):
        self.events.append({"event_type": event_type, "trip_id": trip_id, "payload": payload, "user_id": user_id})


def test_default_registry_exposes_operational_product_agents_beyond_recovery():
    definitions = build_default_registry().definitions()
    names = {definition["name"] for definition in definitions}

    assert {
        "front_door_agent",
        "sales_activation_agent",
        "document_readiness_agent",
        "follow_up_agent",
        "quality_escalation_agent",
    } <= names
    for definition in definitions:
        assert definition["trigger_contract"]
        assert definition["input_contract"]
        assert definition["output_contract"]
        assert definition["idempotency_contract"]
        assert definition["failure_contract"]


def test_happy_path_orchestration_runs_both_product_agents():
    now = datetime.now(timezone.utc)
    repo = _Repo([
        {"id": "trip_follow", "status": "in_progress", "follow_up_due_date": (now - timedelta(hours=1)).isoformat()},
        {"id": "trip_quality", "status": "new", "decision_state": "ESCALATED", "front_door_assessment": {"assessed_at": "2026-05-04T00:00:00+00:00"}},
    ])
    audit = _Audit()
    supervisor = AgentSupervisor(build_default_registry(), repo, audit, interval_seconds=1)

    results = supervisor.run_once()

    assert len(results) == 2
    assert {result.work_item.agent_name for result in results} == {"follow_up_agent", "quality_escalation_agent"}
    assert repo.trips["trip_follow"]["follow_up_status"] == "due"
    assert repo.trips["trip_quality"]["review_status"] == "escalated"
    assert {event["payload"]["event_type"] for event in audit.events} >= {"agent_decision", "agent_action"}


def test_front_door_agent_classifies_incomplete_inquiry_and_drafts_acknowledgment():
    repo = _Repo([
        {
            "id": "trip_front",
            "status": "new",
            "raw_input": {"raw_note": "Need Singapore trip for family next month"},
            "extracted": {"facts": {"destination": {"value": "Singapore"}}},
        },
    ])
    agent = FrontDoorAgent()

    result = agent.execute(next(agent.scan(repo)), repo)

    assert result.success is True
    assessment = repo.trips["trip_front"]["front_door_assessment"]
    assert assessment["is_real_lead"] is True
    assert assessment["priority"] == "high"
    assert "budget" in assessment["missing_fields"]
    assert repo.trips["trip_front"]["recommended_next_action"] == "clarify_missing_trip_details"
    assert "Singapore" in assessment["acknowledgment_draft"]


def test_sales_activation_agent_schedules_follow_up_for_idle_lead():
    repo = _Repo([
        {
            "id": "trip_sales",
            "status": "quoted",
            "updated_at": (datetime.now(timezone.utc) - timedelta(hours=60)).isoformat(),
        },
    ])
    agent = SalesActivationAgent()

    result = agent.execute(next(agent.scan(repo)), repo)

    assert result.success is True
    assert repo.trips["trip_sales"]["follow_up_status"] == "pending"
    assert repo.trips["trip_sales"]["follow_up_due_date"]
    assert "proposal" in repo.trips["trip_sales"]["follow_up_draft"].lower()


def test_sales_activation_agent_skips_when_follow_up_already_pending():
    repo = _Repo([
        {
            "id": "trip_pending",
            "status": "quoted",
            "updated_at": (datetime.now(timezone.utc) - timedelta(hours=60)).isoformat(),
            "follow_up_due_date": (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat(),
            "follow_up_status": "pending",
        },
    ])

    assert list(SalesActivationAgent().scan(repo)) == []


def test_tool_result_marks_stale_evidence_not_fresh():
    fetched_at = datetime(2026, 5, 4, tzinfo=timezone.utc)
    result = ToolResult.from_static(
        tool_name="document_rules_static_seed",
        query={"destination": "canada"},
        data={"rule_set": "test"},
        source="unit_test",
        freshness=ToolFreshnessPolicy(max_age_seconds=60),
        now=fetched_at,
    )

    assert result.is_fresh(now=fetched_at + timedelta(seconds=30)) is True
    assert result.is_fresh(now=fetched_at + timedelta(seconds=61)) is False
    assert result.to_dict()["evidence"]["source"] == "unit_test"


def test_document_readiness_agent_builds_visa_passport_transit_checklist():
    repo = _Repo([
        {
            "id": "trip_docs",
            "stage": "proposal",
            "raw_input": {"raw_note": "Indian passports, senior traveler, USA and Canada with Amsterdam transit"},
            "extracted": {
                "facts": {
                    "destination_candidates": {"value": ["United States", "Canada"]},
                    "date_window": {"value": "2026-11-05 to 2026-11-18"},
                }
            },
            "traveler_nationalities": ["Indian"],
            "transit_points": ["Doha", "Amsterdam"],
            "travelers": [{"name": "Adult 1"}, {"name": "Senior", "traveler_type": "senior"}],
        },
    ])
    agent = DocumentReadinessAgent()

    result = agent.execute(next(agent.scan(repo)), repo)

    assert result.success is True
    checklist = repo.trips["trip_docs"]["document_readiness_checklist"]
    assert checklist["risk_level"] == "high"
    assert repo.trips["trip_docs"]["document_risk_level"] == "high"
    assert any("united states" in item["message"].lower() for item in checklist["items"])
    assert any("canada" in item["message"].lower() for item in checklist["items"])
    assert any("amsterdam" in item["message"].lower() for item in checklist["items"])
    assert any("passport expiry" in value for value in checklist["must_confirm"])
    assert checklist["tool_evidence"][0]["tool_name"] == "document_rules_static_seed"
    assert "authoritative sources" in checklist["disclaimer"]


def test_document_readiness_agent_skips_when_checklist_exists():
    repo = _Repo([
        {
            "id": "trip_docs_done",
            "stage": "proposal",
            "destination": "Singapore",
            "document_readiness_checklist": {"checked_at": "2026-05-04T00:00:00+00:00"},
        },
    ])

    assert list(DocumentReadinessAgent().scan(repo)) == []


def test_transient_dependency_failure_retries_then_succeeds():
    now = datetime.now(timezone.utc)
    repo = _Repo([
        {"id": "trip_retry", "status": "in_progress", "follow_up_due_date": (now - timedelta(hours=1)).isoformat()},
    ])
    audit = _Audit()
    supervisor = AgentSupervisor(build_default_registry(), repo, audit, interval_seconds=1)

    repo.fail_updates_for.add("trip_retry")
    first = supervisor.run_once(agent_name="follow_up_agent")
    repo.fail_updates_for.clear()
    second = supervisor.run_once(agent_name="follow_up_agent")

    assert first[0].success is False
    assert first[0].status == WorkStatus.RETRY_PENDING
    assert second[0].success is True
    assert second[0].status == WorkStatus.COMPLETED
    assert repo.trips["trip_retry"]["follow_up_status"] == "due"


def test_terminal_failure_poisons_and_escalates_after_retry_budget():
    repo = _Repo([
        {"id": "trip_poison", "status": "new", "decision_state": "ESCALATED"},
    ])
    repo.fail_updates_for.add("trip_poison")
    audit = _Audit()
    supervisor = AgentSupervisor(build_default_registry(), repo, audit, interval_seconds=1)

    first = supervisor.run_once(agent_name="quality_escalation_agent")
    second = supervisor.run_once(agent_name="quality_escalation_agent")
    third = supervisor.run_once(agent_name="quality_escalation_agent")

    assert first[0].status == WorkStatus.RETRY_PENDING
    assert second[0].status == WorkStatus.POISONED
    assert third == []
    assert any(event["payload"]["event_type"] == "agent_escalated" for event in audit.events)


def test_ownership_collision_prevention_and_idempotent_reentry():
    coordinator = InMemoryWorkCoordinator(lease_seconds=60)
    item = WorkItem(
        agent_name="follow_up_agent",
        trip_id="trip_lock",
        action="mark_follow_up_due",
        idempotency_key="follow_up_agent:trip_lock:2026-05-04T00:00:00+00:00",
    )
    policy = FollowUpAgent.definition.retry_policy

    acquired, reason, attempt = coordinator.acquire(item, owner="follow_up_agent", retry_policy=policy)
    second_acquired, second_reason, _ = coordinator.acquire(item, owner="follow_up_agent", retry_policy=policy)
    coordinator.complete(item, "done")
    third_acquired, third_reason, _ = coordinator.acquire(item, owner="follow_up_agent", retry_policy=policy)

    assert acquired is True
    assert reason == "acquired"
    assert attempt == 1
    assert second_acquired is False
    assert second_reason.startswith("owned_by:")
    assert third_acquired is False
    assert third_reason == "idempotent_reentry_completed"


def test_quality_agent_escalates_high_suitability_flags():
    repo = _Repo([
        {
            "id": "trip_flag",
            "status": "new",
            "decision_output": {"suitability_flags": [{"severity": "high", "reason": "mobility"}]},
        },
    ])
    result = QualityEscalationAgent().execute(next(QualityEscalationAgent().scan(repo)), repo)

    assert result.success is True
    assert repo.trips["trip_flag"]["review_status"] == "escalated"
    assert repo.trips["trip_flag"]["escalation_reason"] == "suitability_flag:high"
