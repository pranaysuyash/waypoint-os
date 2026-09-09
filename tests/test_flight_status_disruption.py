"""
A1/2.3b tests (2026-09-08): FlightStatusAgent evaluates the STORED journey
graph's disruption ripple on medium/high risk evidence, escalates high risk to
the human-review queue, and never synthesizes a graph when none is stored.
No auto-rebook: ripple output is advisory evidence only.
"""

import uuid
from datetime import datetime

import pytest

from spine_api.persistence import TripStore
from src.agents.runtime import FlightStatusAgent
from src.schemas.journey_graph import JourneyDependencyGraph, JourneyNode, NodeType


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("DATA_PRIVACY_MODE", "beta")
    monkeypatch.setenv("TRIPSTORE_BACKEND", "file")


class _StubToolResult:
    def __init__(self, data, fresh=True):
        self._data = data
        self._fresh = fresh

    def is_fresh(self, now=None):
        return self._fresh

    def to_dict(self, now=None):
        return dict(self._data)

    @property
    def data(self):
        return self._data


class _Repo:
    def __init__(self, trip):
        self.trip = trip

    def list_active(self):
        return [self.trip]

    def get_trip(self, trip_id):
        return self.trip

    def update_trip(self, trip_id, updates):
        persisted = TripStore.update_trip(trip_id, updates)
        print("PROBE persisted:", bool(persisted), "| snapshot keys:", sorted((updates.get("flight_status_snapshot") or {}).keys()))
        self.trip.update(updates)
        return self.trip


def _seed_trip_with_graph(trip_id: str, with_graph=True):
    trip = {
        "id": trip_id,
        "agency_id": "system",
        "status": "assigned",
        "destination": "Tokyo",
        "flights": [{"carrier": "BA", "flight_number": "BA107"}],
    }
    if with_graph:
        graph = JourneyDependencyGraph(trip_id=trip_id)
        t = datetime(2026, 11, 3, 8, 0)
        graph.add_node(JourneyNode(
            node_id="N_FLT_1",
            node_type=NodeType.FLIGHT,
            title="Flight BA107 to Tokyo",
            start_time=t,
            end_time=t.replace(hour=14),
            location="Tokyo",
            provider="Amadeus NDC",
            confirmation_code="PNR001",
            commitment_status="ticketed",
        ))
        graph.add_node(JourneyNode(
            node_id="N_HTL_1",
            node_type=NodeType.HOTEL_CHECKIN,
            title="Hotel Excel Tokyo",
            start_time=t.replace(hour=17),
            end_time=t.replace(hour=17),
            location="Tokyo",
            provider="Demo Hotels",
            commitment_status="quoted",
        ))
        stored = graph.to_stored_payload()
        trip["journey_graph_nodes"] = stored["journey_graph_nodes"]
        trip["journey_graph_edges"] = stored["journey_graph_edges"]
    TripStore.save_trip(trip, agency_id="system")
    return trip


def _agent_with_tool(delay_minutes=120, status="in_air", fresh=True):
    captured = {}

    def _tool(flight):
        captured["flight"] = flight
        return _StubToolResult({
            "status": status,
            "delay_minutes": delay_minutes,
        }, fresh=fresh)

    return FlightStatusAgent(flight_tool=type("T", (), {"flight_status": staticmethod(_tool)})())


def _work_item(trip_id):
    from src.agents.runtime import WorkItem
    flights = [{"carrier": "BA", "flight_number": "BA107"}]
    return WorkItem(
        agent_name="flight_status_agent",
        trip_id=trip_id,
        action="check_flight_status",
        idempotency_key=f"flight_status_agent:{trip_id}:BA107",
        payload={"flights": flights, "flight_marker": "BA107"},
    )


def test_high_risk_runs_stored_graph_ripple_and_escalates():
    """A1: medium/high risk evaluates the STORED graph's ripple; high risk
    routes onto the human-review queue. Quoted siblings survive; no rebooking
    claims anywhere in the output."""
    trip_id = f"trip_fsa_{uuid.uuid4().hex[:10]}"
    _seed_trip_with_graph(trip_id, with_graph=True)
    agent = _agent_with_tool(delay_minutes=120, status="in_air")

    result = agent.execute(_work_item(trip_id), _Repo(TripStore.get_trip(trip_id)))

    assert result.success is True
    stored = TripStore.get_trip(trip_id)
    snapshot = stored.get("flight_status_snapshot") or {}
    ripple = snapshot.get("disruption_ripple")
    assert ripple is not None
    assert ripple["reality_tier"] == "deterministic_preview"
    assert ripple["evaluated_node_id"] == "N_FLT_1"
    # Quoted sibling survived (merge contract) and ripple names downstream impact.
    nodes = stored.get("journey_graph_nodes") or []
    assert any(n.get("node_id") == "N_HTL_1" for n in nodes)
    # High risk routes to the human-review queue, never to auto-rebook.
    assert stored.get("review_status") == "escalated"
    assert stored.get("escalation_reason") == "flight_disruption"
    # The authority boundary is asserted, not violated: the agent explicitly
    # disclaims rebooking and the ripple carries no execution claims.
    assert "do not rebook" in str(snapshot.get("authority")).lower()
    assert "rebooked" not in str(snapshot.get("disruption_ripple")).lower()
    # A2 second half: the statutory rights claim rides on the escalation for
    # the operator case, marked provisional (distance unverified).
    claim = stored.get("passenger_rights_claim") or {}
    assert claim.get("provisional") is True
    assert "distance_unverified" in str(claim.get("provisional_reason"))
    assert claim.get("compensation_currency") == "EUR"


def test_no_stored_graph_still_snapshots_without_ripple():
    """AT-01 contract holds: no stored nodes means NO ripple and no synthesis."""
    trip_id = f"trip_fsa_nograph_{uuid.uuid4().hex[:10]}"
    _seed_trip_with_graph(trip_id, with_graph=False)
    agent = _agent_with_tool(delay_minutes=120, status="in_air")

    result = agent.execute(_work_item(trip_id), _Repo(TripStore.get_trip(trip_id)))

    assert result.success is True
    stored = TripStore.get_trip(trip_id)
    snapshot = stored.get("flight_status_snapshot") or {}
    assert "disruption_ripple" not in snapshot
    assert snapshot.get("risk_level") in {"medium", "high"}
    assert not (stored.get("journey_graph_nodes") or [])


def test_low_risk_does_not_escalate_or_evaluate():
    trip_id = f"trip_fsa_low_{uuid.uuid4().hex[:10]}"
    _seed_trip_with_graph(trip_id, with_graph=True)
    agent = _agent_with_tool(delay_minutes=0, status="on_schedule")

    result = agent.execute(_work_item(trip_id), _Repo(TripStore.get_trip(trip_id)))

    assert result.success is True
    stored = TripStore.get_trip(trip_id)
    snapshot = stored.get("flight_status_snapshot") or {}
    assert "disruption_ripple" not in snapshot
    assert stored.get("review_status") != "escalated"
