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
