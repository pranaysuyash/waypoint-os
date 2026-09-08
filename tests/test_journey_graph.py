"""
tests/test_journey_graph.py — Verification suite for Journey Dependency Graph (JDG).
"""

from datetime import datetime
from src.schemas.journey_graph import (
    JourneyDependencyGraph,
    JourneyNode,
    NodeType,
    DependencyRelation,
)
from spine_api.routers.journey_graph import (
    EvaluateDisruptionRequest,
    evaluate_journey_disruption,
)


def test_journey_graph_disruption_ripple_propagation():
    graph = JourneyDependencyGraph("trip_test_001")

    # Leg 1: London to Dubai flight (Arrives 14:00)
    t0 = datetime(2026, 10, 1, 8, 0)
    t1 = datetime(2026, 10, 1, 14, 0)
    flight1 = JourneyNode(
        node_id="leg_flight_1",
        node_type=NodeType.FLIGHT,
        title="Flight BA107 (LHR -> DXB)",
        start_time=t0,
        end_time=t1,
        location="DXB Airport",
    )

    # Leg 2: Airport Private Transfer (Scheduled 15:00)
    t2_start = datetime(2026, 10, 1, 15, 0)
    t2_end = datetime(2026, 10, 1, 15, 45)
    transfer = JourneyNode(
        node_id="leg_transfer_1",
        node_type=NodeType.TRANSFER,
        title="Private Transfer to Jumeirah",
        start_time=t2_start,
        end_time=t2_end,
        location="Jumeirah Beach Hotel",
    )

    # Leg 3: Luxury Sunset Yacht Tour (Scheduled 17:00)
    t3_start = datetime(2026, 10, 1, 17, 0)
    t3_end = datetime(2026, 10, 1, 19, 0)
    yacht = JourneyNode(
        node_id="leg_activity_1",
        node_type=NodeType.ACTIVITY,
        title="Sunset Yacht Tour",
        start_time=t3_start,
        end_time=t3_end,
        location="Dubai Marina",
    )

    graph.add_node(flight1)
    graph.add_node(transfer)
    graph.add_node(yacht)

    # Flight -> Transfer requires 45m min buffer
    graph.add_edge("leg_flight_1", "leg_transfer_1", DependencyRelation.REQUIRES_ARRIVAL_BEFORE, min_connection_minutes=45)
    # Transfer -> Yacht requires 30m buffer
    graph.add_edge("leg_transfer_1", "leg_activity_1", DependencyRelation.SAME_DAY_ACTIVITY, min_connection_minutes=30)

    # Case A: Minor 10m delay (absorbed in 60m buffer)
    report_minor = graph.evaluate_disruption("leg_flight_1", delay_minutes=10)
    assert len(report_minor.impacted_nodes) == 0

    # Case B: Major 90m delay (arrives 15:30 -> transfer missed -> yacht impacted)
    report_major = graph.evaluate_disruption("leg_flight_1", delay_minutes=90)
    assert len(report_major.impacted_nodes) >= 1
    transfer_impact = [i for i in report_major.impacted_nodes if i.impacted_node_id == "leg_transfer_1"][0]
    assert transfer_impact.impact_severity in ("critical", "high")
    assert transfer_impact.time_deficit_minutes == 75  # 15:30 + 45m = 16:15 vs 15:00 scheduled

    report_dict = report_major.to_dict()
    assert report_dict["root_disrupted_node_id"] == "leg_flight_1"
    assert len(report_dict["impacted_nodes"]) >= 1


def test_journey_graph_roundtrip_preserves_commitment_and_edges():
    t0 = datetime(2026, 10, 1, 8, 0)
    t1 = datetime(2026, 10, 1, 14, 0)
    graph = JourneyDependencyGraph("trip_roundtrip")
    graph.add_node(
        JourneyNode(
            node_id="leg_flight_1",
            node_type=NodeType.FLIGHT,
            title="Flight BA107 (LHR -> DXB)",
            start_time=t0,
            end_time=t1,
            location="DXB Airport",
        )
    )
    graph.add_node(
        JourneyNode(
            node_id="leg_transfer_1",
            node_type=NodeType.TRANSFER,
            title="Private Transfer",
            start_time=datetime(2026, 10, 1, 15, 0),
            end_time=datetime(2026, 10, 1, 15, 45),
            location="Hotel",
        )
    )
    graph.add_edge(
        "leg_flight_1",
        "leg_transfer_1",
        DependencyRelation.REQUIRES_ARRIVAL_BEFORE,
        min_connection_minutes=45,
    )
    payload = graph.to_stored_payload()
    restored = JourneyDependencyGraph.from_stored(
        "trip_roundtrip",
        payload["journey_graph_nodes"],
        payload["journey_graph_edges"],
    )
    assert "leg_flight_1" in restored.nodes
    assert restored.nodes["leg_flight_1"].commitment_status == "quoted"
    assert len(restored.edges) == 1
    restored.nodes["leg_flight_1"].commitment_status = "ticketed"
    again = JourneyDependencyGraph.from_stored(
        "trip_roundtrip",
        restored.to_stored_payload()["journey_graph_nodes"],
        restored.to_stored_payload()["journey_graph_edges"],
    )
    assert again.nodes["leg_flight_1"].commitment_status == "ticketed"


def test_evaluate_abstains_without_nodes_or_stored_graph():
    # 2026-09-06 tenant-scoping fix: the handler resolves the caller's agency
    # (Depends) and reads via get_trip_for_agency — direct callers pass the
    # agency explicitly.
    result = evaluate_journey_disruption(
        EvaluateDisruptionRequest(
            trip_id="trip_no_graph_xyz",
            delayed_node_id="n1",
        ),
        agency_id="agency_test",
    )
    assert result["status"] == "abstain"
    assert result["reality_tier"] == "unavailable"
    assert result["provider_connected"] is False


def test_from_dict_tolerates_undated_nodes_and_preserves_unknown_types():
    """Part-H P2: stored nodes without schedule times must hydrate instead of
    crashing, and unknown node types keep their operational meaning instead of
    being silently re-labeled FLIGHT."""
    import pytest

    node = JourneyNode.from_dict(
        {"node_id": "n_hov_1", "node_type": "HOVERCRAFT", "title": "Channel crossing"}
    )
    assert node.start_time is None
    assert node.end_time is None
    assert node.node_type == "HOVERCRAFT"

    graph = JourneyDependencyGraph.from_stored(
        "trip_hov",
        [{"node_id": "n_hov_1", "node_type": "HOVERCRAFT", "title": "Channel crossing"}],
        [],
    )
    assert graph.get_node("n_hov_1") is not None

    # Disruption evaluation honestly abstains on a node with no schedule.
    with pytest.raises(ValueError, match="no scheduled end time"):
        graph.evaluate_disruption("n_hov_1", 30)

    # Serialization round-trips without inventing datetimes.
    payload = graph.to_stored_payload()
    assert payload["journey_graph_nodes"][0]["start_time"] is None
    assert payload["journey_graph_nodes"][0]["node_type"] == "HOVERCRAFT"


def test_parse_dt_normalizes_naive_to_utc_for_mixed_sorting():
    """Part-J #7: naive and aware timestamps must coexist — mixed-provenance
    nodes previously crashed topological_sort with a naive/aware TypeError."""
    naive = JourneyNode.from_dict(
        {
            "node_id": "n_naive",
            "node_type": "FLIGHT",
            "title": "Naive legacy leg",
            "start_time": "2026-10-01T08:00:00",
            "end_time": "2026-10-01T10:00:00",
        }
    )
    aware = JourneyNode.from_dict(
        {
            "node_id": "n_aware",
            "node_type": "FLIGHT",
            "title": "Aware leg",
            "start_time": "2026-10-01T12:00:00+00:00",
            "end_time": "2026-10-01T14:00:00+00:00",
        }
    )
    assert naive.start_time is not None and naive.start_time.tzinfo is not None

    graph = JourneyDependencyGraph("trip_mixed_tz")
    graph.add_node(naive)
    graph.add_node(aware)
    graph.add_edge(
        "n_naive",
        "n_aware",
        relation=DependencyRelation.REQUIRES_ARRIVAL_BEFORE,
        min_connection_minutes=60,
    )
    ordered = graph.topological_sort()
    assert [n.node_id for n in ordered] == ["n_naive", "n_aware"]
