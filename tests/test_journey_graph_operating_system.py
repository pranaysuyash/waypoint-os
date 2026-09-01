"""
Journey Graph & Travel Operating System Engine Tests (PER-0442, PER-0964).
"""

from datetime import datetime, timedelta
import pytest

from src.schemas.journey_graph import (
    JourneyDependencyGraph,
    JourneyNode,
    NodeType,
    DependencyRelation,
    CO_TERMINAL_TRANSFER_MINUTES,
)


def test_topological_sort_and_cycle_detection():
    graph = JourneyDependencyGraph(trip_id="TRIP-DAG-001")
    t0 = datetime(2026, 10, 1, 10, 0)

    n1 = JourneyNode("N1", NodeType.FLIGHT, "LHR -> JFK", t0, t0 + timedelta(hours=8), "LHR")
    n2 = JourneyNode("N2", NodeType.TRANSFER, "JFK Transfer", t0 + timedelta(hours=8, minutes=30), t0 + timedelta(hours=9, minutes=30), "JFK")
    n3 = JourneyNode("N3", NodeType.HOTEL_CHECKIN, "Manhattan Hotel", t0 + timedelta(hours=10), t0 + timedelta(hours=11), "NYC")

    graph.add_node(n1)
    graph.add_node(n2)
    graph.add_node(n3)

    graph.add_edge("N1", "N2", DependencyRelation.TRANSFER_CONNECTS, min_connection_minutes=30)
    graph.add_edge("N2", "N3", DependencyRelation.HOTEL_NIGHT_FOR, min_connection_minutes=30)

    sorted_nodes = graph.topological_sort()
    assert [n.node_id for n in sorted_nodes] == ["N1", "N2", "N3"]

    # Introduce a cycle N3 -> N1
    graph.add_edge("N3", "N1", DependencyRelation.REQUIRES_ARRIVAL_BEFORE)
    with pytest.raises(ValueError, match="Cycle detected"):
        graph.topological_sort()


def test_co_terminal_transfer_cushion():
    assert CO_TERMINAL_TRANSFER_MINUTES[("LHR", "LGW")] == 180
    assert CO_TERMINAL_TRANSFER_MINUTES[("JFK", "EWR")] == 150
    assert CO_TERMINAL_TRANSFER_MINUTES[("NRT", "HND")] == 120

    graph = JourneyDependencyGraph(trip_id="TRIP-COTERM-002")
    t0 = datetime(2026, 10, 1, 8, 0)
    leg1 = JourneyNode("L1", NodeType.FLIGHT, "EDI -> LHR", t0, t0 + timedelta(hours=1, minutes=30), "LHR")
    leg2 = JourneyNode("L2", NodeType.FLIGHT, "LGW -> BCN", t0 + timedelta(hours=5), t0 + timedelta(hours=7), "LGW")

    graph.add_node(leg1)
    graph.add_node(leg2)
    graph.add_edge("L1", "L2", DependencyRelation.REQUIRES_ARRIVAL_BEFORE, min_connection_minutes=180)

    cushion = graph.compute_cushion_variance("L1", "L2")
    # Total available: 5h - 1.5h = 3.5h = 210 min. Min required: 180 min. Cushion: +30 min
    assert cushion == 30.0


def test_disruption_ripple_propagation():
    graph = JourneyDependencyGraph(trip_id="TRIP-DISRUPT-003")
    t0 = datetime(2026, 10, 1, 10, 0)

    f1 = JourneyNode("F1", NodeType.FLIGHT, "Inbound Flight", t0, t0 + timedelta(hours=4), "LHR")
    f2 = JourneyNode("F2", NodeType.FLIGHT, "Connecting Flight", t0 + timedelta(hours=5), t0 + timedelta(hours=9), "JFK")
    act = JourneyNode("ACT", NodeType.ACTIVITY, "Broadway Show", t0 + timedelta(hours=10), t0 + timedelta(hours=12), "NYC")

    graph.add_node(f1)
    graph.add_node(f2)
    graph.add_node(act)

    graph.add_edge("F1", "F2", DependencyRelation.TRANSFER_CONNECTS, min_connection_minutes=60)
    graph.add_edge("F2", "ACT", DependencyRelation.SAME_DAY_ACTIVITY, min_connection_minutes=45)

    # Inbound flight delayed by 90 minutes (violates 60m connection buffer)
    report = graph.evaluate_disruption("F1", delay_minutes=90)
    assert len(report.impacted_nodes) >= 1
    assert report.impacted_nodes[0].impacted_node_id == "F2"
    assert report.impacted_nodes[0].impact_severity == "critical"
    assert "Connection window violated" in report.impacted_nodes[0].reason
