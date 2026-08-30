"""
Unit and integration tests for Wave B: Agentic Expansion
- CommunicatorAgent (Autonomous Clarification Drafting)
- OperatorRefinementAgent (Refinement Loops)
"""

from src.agents.runtime import (
     AgentSupervisor,
     WorkStatus,
     build_default_registry,
)
from src.agents.communicator_agent import CommunicatorAgent
from src.agents.operator_refinement_agent import OperatorRefinementAgent


class DictTripRepository:
    def __init__(self, trips: list[dict]):
        self._trips = {str(t["id"]): dict(t) for t in trips}

    def list_active(self) -> list[dict]:
        return list(self._trips.values())

    def get_trip(self, trip_id: str) -> dict | None:
        return self._trips.get(str(trip_id))

    def update_trip(self, trip_id: str, updates: dict) -> dict | None:
        trip = self._trips.get(str(trip_id))
        if not trip:
            return None
        trip.update(updates)
        return trip


def test_registry_includes_wave_b_agents():
    """Verify that default agent registry includes Communicator and OperatorRefinement agents."""
    registry = build_default_registry()
    agent_names = [a.definition.name for a in registry.agents()]

    assert "communicator_agent" in agent_names
    assert "operator_refinement_agent" in agent_names


def test_communicator_agent_scans_and_drafts():
    """Verify that CommunicatorAgent identifies blocked trips and drafts multi-tonal messages."""
    trip = {
        "id": "trip_blocked_1",
        "status": "intake",
        "decision": {
            "decision_state": "ASK_FOLLOWUP",
            "follow_up_questions": [
                {"field_name": "origin", "question": "Where will you be departing from?"},
                {"field_name": "budget", "question": "What is your target budget for the trip?"},
            ],
            "hard_blockers": ["origin_missing"],
        },
        "packet": {
            "facts": {
                "destination_candidates": {"value": ["Tokyo", "Kyoto"]},
            }
        },
        "created_at": "2026-08-30T10:00:00Z",
        "updated_at": "2026-08-30T10:00:00Z",
    }
    repo = DictTripRepository([trip])
    agent = CommunicatorAgent()

    work_items = list(agent.scan(repo))
    assert len(work_items) == 1
    assert work_items[0].trip_id == "trip_blocked_1"
    assert work_items[0].action == "draft_clarification_messages"

    result = agent.execute(work_items[0], repo)
    assert result.status == WorkStatus.COMPLETED
    assert result.success is True

    updated_trip = repo.get_trip("trip_blocked_1")
    drafts = updated_trip.get("clarification_drafts")
    assert len(drafts) == 3
    tones = [d["tone"] for d in drafts]
    assert "concise" in tones
    assert "consultative" in tones
    assert "formal" in tones
    assert any("departing from" in d["body"] for d in drafts)


def test_operator_refinement_agent_scans_and_synthesizes():
    """Verify that OperatorRefinementAgent identifies trips requiring revision and computes alternatives."""
    trip = {
        "id": "trip_review_1",
        "status": "review",
        "last_review_action": "request_changes",
        "analytics": {
            "requires_review": True,
            "review_reason": "Traveler requested lower cost accommodation and less intense daily schedule",
        },
        "packet": {
            "facts": {
                "duration_nights": {"value": 6},
                "budget_stated": {"value": 4500},
            }
        },
        "created_at": "2026-08-30T10:00:00Z",
        "updated_at": "2026-08-30T10:00:00Z",
    }
    repo = DictTripRepository([trip])
    agent = OperatorRefinementAgent()

    work_items = list(agent.scan(repo))
    assert len(work_items) == 1
    assert work_items[0].trip_id == "trip_review_1"
    assert work_items[0].action == "synthesize_refinements"

    result = agent.execute(work_items[0], repo)
    assert result.status == WorkStatus.COMPLETED
    assert result.success is True

    updated_trip = repo.get_trip("trip_review_1")
    suggestions = updated_trip.get("refinement_suggestions")
    assert len(suggestions) == 3
    option_ids = [s["option_id"] for s in suggestions]
    assert "opt_value_optimized" in option_ids
    assert "opt_pacing_adjusted" in option_ids
    assert "opt_supplier_swap" in option_ids


def test_supervisor_runs_wave_b_agents():
    """Verify end-to-end supervisor execution of Wave B agents."""
    trip = {
        "id": "trip_supervisor_1",
        "status": "intake",
        "decision": {
            "decision_state": "ASK_FOLLOWUP",
            "follow_up_questions": ["Please confirm travel dates."],
        },
        "packet": {"facts": {}},
        "created_at": "2026-08-30T10:00:00Z",
        "updated_at": "2026-08-30T10:00:00Z",
    }
    repo = DictTripRepository([trip])
    registry = build_default_registry()
    supervisor = AgentSupervisor(registry=registry, trip_repo=repo, audit=None)

    results = supervisor.run_once(agent_name="communicator_agent")
    assert len(results) == 1
    assert results[0].success is True
    assert repo.get_trip("trip_supervisor_1").get("clarification_drafts") is not None
