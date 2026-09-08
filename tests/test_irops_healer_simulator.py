"""
Live IROPS Auto-Healer Simulator Tests (PER-IROPS-SIM / AT-06).

The engine must operate on a stored journey graph. A missing graph abstains
rather than synthesizing BA178 / Four Seasons.
"""

import uuid
from datetime import datetime, timezone

import pytest

from spine_api.persistence import TripStore
from src.orchestration.irops_healer import IROPSAutoHealerEngine
from src.schemas.journey_graph import JourneyDependencyGraph, JourneyNode, NodeType


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("DATA_PRIVACY_MODE", "beta")
    monkeypatch.setenv("TRIPSTORE_BACKEND", "file")


def _seed_stored_flight(trip_id: str, node_id: str = "N_FLT_STORED") -> str:
    now = datetime.now(timezone.utc)
    graph = JourneyDependencyGraph(trip_id=trip_id)
    graph.add_node(
        JourneyNode(
            node_id=node_id,
            node_type=NodeType.FLIGHT,
            title="Stored flight AA100 JFK-LHR",
            start_time=now,
            end_time=now,
            location="JFK",
            provider="American Airlines",
            confirmation_code="AA100PNR",
            commitment_status="ticketed",
        )
    )
    TripStore.save_trip(
        {
            "id": trip_id,
            "agency_id": "system",
            "destination": "London",
            **graph.to_stored_payload(),
        },
        agency_id="system",
    )
    return node_id


def test_irops_abstains_without_stored_graph():
    trip_id = f"trip_irops_empty_{uuid.uuid4().hex[:8]}"
    TripStore.save_trip(
        {"id": trip_id, "agency_id": "system", "destination": "Paris"},
        agency_id="system",
    )
    with pytest.raises(ValueError, match="No stored journey graph"):
        IROPSAutoHealerEngine.execute_healing_protocol(
            trip_id=trip_id,
            delayed_node_id="N_FLT_178",
            delay_minutes=180,
        )


def test_irops_auto_healing_execution_uses_stored_graph():
    trip_id = f"trip_irops_heal_{uuid.uuid4().hex[:8]}"
    node_id = _seed_stored_flight(trip_id)

    plan = IROPSAutoHealerEngine.execute_healing_protocol(
        trip_id=trip_id,
        delayed_node_id=node_id,
        delay_minutes=180,
    )

    assert plan.trip_id == trip_id
    assert plan.delay_minutes == 180
    assert plan.delayed_node_title == "Stored flight AA100 JFK-LHR"
    assert plan.statutory_compensation_amount_eur == 600.0
    assert "EU261" in plan.statutory_law_cited
    assert len(plan.counterfactual_options) == 3
    assert plan.counterfactual_options[0]["tier"] == "OPTION_A_MIN_DELAY"
    assert plan.counterfactual_options[0]["status"] == "PREVIEW_ONLY"
    assert plan.counterfactual_options[0]["provider_connected"] is False
    assert "BA178" not in plan.waiver_dispute_letter
    assert "Stored flight AA100" in plan.waiver_dispute_letter
    assert plan.emergency_lodging_vcc is not None
    assert "Request for Full Penalty Waiver" in plan.waiver_dispute_letter
