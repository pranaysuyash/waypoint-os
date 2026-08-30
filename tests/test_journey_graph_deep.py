"""
tests/test_journey_graph_deep.py — Unit tests for PER-0442 topological sorting, cushion variance, and GeoJSON.
"""

from datetime import datetime, timedelta, timezone
import pytest

from src.schemas.journey_graph import (
    CO_TERMINAL_TRANSFER_MINUTES,
    DependencyRelation,
    JourneyDependencyGraph,
    JourneyNode,
    NodeType,
)


def test_topological_sort_kahn_algorithm():
    """Verify topological sorting orders journey nodes in correct causal sequence."""
    now = datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc)
    graph = JourneyDependencyGraph(trip_id="trip_topo_001")

    n1 = JourneyNode("fl_1", NodeType.FLIGHT, "JFK-LHR", now, now + timedelta(hours=7), "JFK", "Delta")
    n2 = JourneyNode("trn_1", NodeType.TRANSFER, "Heathrow Express", now + timedelta(hours=7, minutes=30), now + timedelta(hours=8), "LHR", "Heathrow Express")
    n3 = JourneyNode("hot_1", NodeType.HOTEL_STAY, "The Savoy", now + timedelta(hours=9), now + timedelta(days=2), "London", "Savoy")

    # Add in reverse order to ensure sort is doing real topological resolution
    graph.add_node(n3)
    graph.add_node(n2)
    graph.add_node(n1)

    graph.add_edge("fl_1", "trn_1", DependencyRelation.TRANSFER_CONNECTS, min_connection_minutes=30)
    graph.add_edge("trn_1", "hot_1", DependencyRelation.HOTEL_NIGHT_FOR, min_connection_minutes=60)

    sorted_nodes = graph.topological_sort()
    assert [n.node_id for n in sorted_nodes] == ["fl_1", "trn_1", "hot_1"]


def test_cycle_detection_raises_error():
    """Verify cycles in journey graph are detected and rejected."""
    now = datetime.now(timezone.utc)
    graph = JourneyDependencyGraph(trip_id="trip_cycle_001")

    graph.add_node(JourneyNode("A", NodeType.FLIGHT, "Leg A", now, now, "JFK"))
    graph.add_node(JourneyNode("B", NodeType.FLIGHT, "Leg B", now, now, "LHR"))

    # Create cycle A -> B -> A
    graph.add_edge("A", "B")
    graph.add_edge("B", "A")

    with pytest.raises(ValueError, match="Cycle detected"):
        graph.topological_sort()


def test_cushion_variance_and_co_terminals():
    """Verify cushion variance calculation and co-terminal transit constants."""
    now = datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc)
    graph = JourneyDependencyGraph(trip_id="trip_cushion_001")

    # 12:00 -> 14:00 (End 14:00)
    graph.add_node(JourneyNode("leg_1", NodeType.FLIGHT, "Inbound", now, now + timedelta(hours=2), "LHR"))
    # Next leg departs 16:30 (150m buffer)
    graph.add_node(JourneyNode("leg_2", NodeType.FLIGHT, "Outbound", now + timedelta(hours=4, minutes=30), now + timedelta(hours=7), "LHR"))

    # Edge requires 90m MCT
    graph.add_edge("leg_1", "leg_2", DependencyRelation.REQUIRES_ARRIVAL_BEFORE, min_connection_minutes=90)

    # 150m available - 90m MCT = +60m surplus cushion
    cushion = graph.compute_cushion_variance("leg_1", "leg_2")
    assert cushion == 60.0

    # Verify Co-Terminal table
    assert CO_TERMINAL_TRANSFER_MINUTES[("LHR", "LGW")] == 180
    assert CO_TERMINAL_TRANSFER_MINUTES[("JFK", "EWR")] == 150


def test_geojson_and_graph_diff():
    """Verify GeoJSON serialization and graph diff comparison."""
    now = datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc)
    g1 = JourneyDependencyGraph(trip_id="trip_diff_001")
    g1.add_node(JourneyNode("n1", NodeType.FLIGHT, "Flight 1", now, now + timedelta(hours=2), "JFK"))
    g1.add_node(JourneyNode("n2", NodeType.HOTEL_STAY, "Hotel 1", now + timedelta(hours=3), now + timedelta(days=1), "Paris"))

    # Serialize to GeoJSON
    geojson = g1.to_geojson()
    assert geojson["type"] == "FeatureCollection"
    assert len(geojson["features"]) == 2

    # Modified graph g2
    g2 = JourneyDependencyGraph(trip_id="trip_diff_001")
    g2.add_node(JourneyNode("n1", NodeType.FLIGHT, "Flight 1 Modified", now, now + timedelta(hours=3), "JFK"))  # Modified
    g2.add_node(JourneyNode("n3", NodeType.ACTIVITY, "Tour", now + timedelta(hours=4), now + timedelta(hours=6), "Paris"))  # Added, n2 removed

    diff_report = g1.diff(g2)
    assert diff_report["added_nodes_count"] == 1
    assert diff_report["removed_nodes_count"] == 1
    assert diff_report["modified_nodes_count"] == 1
