"""Tests for Journey Dependency Graph (JDG) and Co-Terminal Ripple Engine."""

from datetime import datetime, timedelta, timezone
from src.schemas.journey_graph import (
    JourneyDependencyGraph,
    JourneyNode,
    NodeType,
    DependencyRelation,
    CO_TERMINAL_TRANSFER_MINUTES,
)


def test_co_terminal_transfer_lookup():
    assert CO_TERMINAL_TRANSFER_MINUTES[("NRT", "HND")] == 120
    assert CO_TERMINAL_TRANSFER_MINUTES[("LHR", "LGW")] == 180
    assert CO_TERMINAL_TRANSFER_MINUTES[("JFK", "EWR")] == 150


def test_journey_graph_topological_sort():
    graph = JourneyDependencyGraph("TRIP-TEST-001")
    t0 = datetime(2027, 4, 10, 8, 0, tzinfo=timezone.utc)

    # Node 1: Inbound Flight JFK -> NRT
    n1 = JourneyNode("node_flt_1", NodeType.FLIGHT, "JFK -> NRT Flight", t0, t0 + timedelta(hours=14), "NRT")
    # Node 2: Transfer NRT -> Tokyo Hotel
    n2 = JourneyNode("node_trf_1", NodeType.TRANSFER, "NRT to Hotel Transfer", t0 + timedelta(hours=14, minutes=45), t0 + timedelta(hours=16), "Tokyo")
    # Node 3: Hotel Check-in
    n3 = JourneyNode("node_htl_1", NodeType.HOTEL_CHECKIN, "Aman Tokyo Check-in", t0 + timedelta(hours=16, minutes=30), t0 + timedelta(hours=17), "Tokyo")

    graph.add_node(n1)
    graph.add_node(n2)
    graph.add_node(n3)

    graph.add_edge("node_flt_1", "node_trf_1", DependencyRelation.TRANSFER_CONNECTS, min_connection_minutes=45)
    graph.add_edge("node_trf_1", "node_htl_1", DependencyRelation.REQUIRES_ARRIVAL_BEFORE, min_connection_minutes=30)

    sorted_nodes = graph.topological_sort()
    assert [n.node_id for n in sorted_nodes] == ["node_flt_1", "node_trf_1", "node_htl_1"]


def test_disruption_ripple_propagation():
    graph = JourneyDependencyGraph("TRIP-TEST-002")
    t0 = datetime(2027, 4, 10, 8, 0, tzinfo=timezone.utc)

    # Flight 1: Dep 08:00, Arr 12:00
    n1 = JourneyNode("flight_1", NodeType.FLIGHT, "Flight 101", t0, t0 + timedelta(hours=4), "LHR")
    # Connecting Flight 2: Dep 13:30, Arr 16:00 (Buffer: 90m, MCT: 60m)
    n2 = JourneyNode("flight_2", NodeType.FLIGHT, "Flight 202", t0 + timedelta(hours=5, minutes=30), t0 + timedelta(hours=8), "CDG")
    # Dinner Reservation: Dep 19:00 (Buffer: 3h)
    n3 = JourneyNode("dinner", NodeType.RESTAURANT, "Michelin Dinner", t0 + timedelta(hours=11), t0 + timedelta(hours=13), "Paris")

    graph.add_node(n1)
    graph.add_node(n2)
    graph.add_node(n3)

    graph.add_edge("flight_1", "flight_2", DependencyRelation.REQUIRES_ARRIVAL_BEFORE, min_connection_minutes=60)
    graph.add_edge("flight_2", "dinner", DependencyRelation.SAME_DAY_ACTIVITY, min_connection_minutes=60)

    # Case A: Small delay (+15m) -> Absorbed by existing 90m buffer
    report_small = graph.evaluate_disruption("flight_1", delay_minutes=15)
    assert len(report_small.impacted_nodes) == 0

    # Case B: Severe delay (+60m) -> Arrival at 13:00 + 60m MCT = 14:00 feasible start > 13:30 scheduled
    report_severe = graph.evaluate_disruption("flight_1", delay_minutes=60)
    assert len(report_severe.impacted_nodes) >= 1
    assert report_severe.impacted_nodes[0].impacted_node_id == "flight_2"
    assert report_severe.impacted_nodes[0].impact_severity == "critical"
    assert report_severe.impacted_nodes[0].time_deficit_minutes == 30
