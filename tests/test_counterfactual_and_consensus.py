"""
tests/test_counterfactual_and_consensus.py — Tests for IROPS Counterfactual Replanning and Group Pareto Consensus.
"""

import os
import pytest

from src.decision.counterfactual_recovery import (
    CounterfactualReplanningEngine,
    RecoveryStrategy,
)
from src.decision.group_consensus import (
    GroupConsensusOptimizer,
    ItineraryOptionProposal,
    TravelerPreferenceProfile,
)
from src.schemas.journey_graph import JourneyDependencyGraph, JourneyNode, NodeType

os.environ["RUNNING_TESTS"] = "1"


@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    monkeypatch.setenv("DATA_PRIVACY_MODE", "beta")
    monkeypatch.setenv("SPINE_API_DISABLE_AUTH", "1")
    monkeypatch.setenv("TRIPSTORE_BACKEND", "file")


def test_counterfactual_replanning_alternatives():
    """Verify 3 ranked recovery alternatives generated for a disrupted journey node."""
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    graph = JourneyDependencyGraph(trip_id="trip_irops_001")
    graph.add_node(
        JourneyNode(
            node_id="flight_cdg_jfk",
            node_type=NodeType.FLIGHT,
            title="AF22 CDG-JFK",
            start_time=now,
            end_time=now,
            location="CDG",
            provider="Air France",
        )
    )

    report = CounterfactualReplanningEngine.generate_alternatives(
        graph=graph,
        disrupted_node_id="flight_cdg_jfk",
        delay_minutes=240,  # 4 hours
    )

    assert report.trip_id == "trip_irops_001"
    assert report.disrupted_node_id == "flight_cdg_jfk"
    assert len(report.alternatives) == 3
    strategies = [a.strategy for a in report.alternatives]
    assert RecoveryStrategy.MINIMUM_DELAY in strategies
    assert RecoveryStrategy.SAME_CARRIER in strategies
    assert RecoveryStrategy.PREMIUM_COMFORT in strategies


def test_group_consensus_pareto_scoring():
    """Verify group consensus Pareto optimization across conflicting budgets."""
    travelers = [
        TravelerPreferenceProfile(
            traveler_id="t1",
            name="Alice",
            max_budget_usd=1500.0,
            preferred_pacing="RELAXED",
            priority_activities=["beach", "culinary"],
        ),
        TravelerPreferenceProfile(
            traveler_id="t2",
            name="Bob",
            max_budget_usd=3000.0,
            preferred_pacing="BALANCED",
            priority_activities=["historical", "culinary"],
        ),
    ]

    options = [
        ItineraryOptionProposal(
            option_id="opt_cheap_beach",
            title="Relaxed Coastal Resort",
            total_cost_per_person_usd=1200.0,
            pacing="RELAXED",
            included_activities=["beach", "culinary"],
            rooming_configuration="2x single",
        ),
        ItineraryOptionProposal(
            option_id="opt_expensive_luxury",
            title="Ultra Luxury Heritage Tour",
            total_cost_per_person_usd=2800.0,  # Exceeds Alice's budget!
            pacing="INTENSE",
            included_activities=["historical", "culinary"],
            rooming_configuration="2x suite",
        ),
    ]

    scores = GroupConsensusOptimizer.evaluate_group_consensus(travelers, options)
    assert len(scores) == 2
    # The affordable option should rank higher due to no budget violations
    assert scores[0].option_id == "opt_cheap_beach"
    assert scores[0].recommendation_tier == "STRONG_MATCH"
    assert len(scores[0].budget_violations) == 0

    assert scores[1].option_id == "opt_expensive_luxury"
    assert len(scores[1].budget_violations) > 0


def test_counterfactual_and_consensus_api_endpoints(session_client):
    """Verify API endpoints for counterfactual replanning and group consensus."""
    # Test replan endpoint
    res_replan = session_client.post(
        "/api/v1/counterfactual/replan-disruption",
        json={
            "trip_id": "trip_test_replan",
            "disrupted_node_id": "node_fl_01",
            "delay_minutes": 180,
        },
        headers={"X-Agency-ID": "agency_cf_test"},
    )
    assert res_replan.status_code == 200
    assert len(res_replan.json()["alternatives"]) == 3

    # Test group consensus endpoint
    res_group = session_client.post(
        "/api/v1/counterfactual/group-consensus",
        json={
            "travelers": [
                {
                    "traveler_id": "t_01",
                    "name": "David",
                    "max_budget_usd": 2000.0,
                    "preferred_pacing": "BALANCED",
                    "priority_activities": ["sightseeing"],
                }
            ],
            "candidate_options": [
                {
                    "option_id": "opt_01",
                    "title": "City Explorer",
                    "total_cost_per_person_usd": 1500.0,
                    "pacing": "BALANCED",
                    "included_activities": ["sightseeing"],
                }
            ],
        },
        headers={"X-Agency-ID": "agency_cf_test"},
    )
    assert res_group.status_code == 200
    assert res_group.json()["total_options_evaluated"] == 1
