"""
tests/test_constraint_engine.py — Verification suite for Spatial-Temporal Constraint Satisfaction Engine.

Grounding: PER-0711 (Constraint-Satisfaction Designer) & PER-0706.
"""

from datetime import datetime
from src.schemas.journey_graph import JourneyDependencyGraph, JourneyNode, NodeType
from src.decision.constraint_engine import ConstraintEngine
from src.schemas.constraints import ConstraintType, ConstraintCategory


def test_mct_connection_deficit_and_feasible():
    graph = JourneyDependencyGraph("trip_test_mct")

    # Flight 1: Arrives 14:00
    f1 = JourneyNode(
        node_id="f1",
        node_type=NodeType.FLIGHT,
        title="Domestic Flight A -> B",
        start_time=datetime(2026, 11, 1, 10, 0),
        end_time=datetime(2026, 11, 1, 14, 0),
        location="Airport B",
    )

    # Flight 2: Departs 14:20 (Only 20m layover, Domestic MCT requires 45m)
    f2 = JourneyNode(
        node_id="f2",
        node_type=NodeType.FLIGHT,
        title="Domestic Flight B -> C",
        start_time=datetime(2026, 11, 1, 14, 20),
        end_time=datetime(2026, 11, 1, 16, 0),
        location="Airport C",
    )

    graph.add_node(f1)
    graph.add_node(f2)

    report = ConstraintEngine.evaluate_itinerary_graph(graph)
    assert not report.is_feasible
    assert len(report.hard_violations) == 1
    v = report.hard_violations[0]
    assert v.category == ConstraintCategory.TEMPORAL_MCT
    assert v.constraint_type == ConstraintType.HARD
    assert "MCT_DEFICIT" in v.constraint_id
    assert v.relaxation_option is not None
    assert len(report.relaxation_hierarchy) >= 1

    # Now shift f2 to 15:00 (60m layover >= 45m MCT)
    f2_valid = JourneyNode(
        node_id="f2_valid",
        node_type=NodeType.FLIGHT,
        title="Domestic Flight B -> C",
        start_time=datetime(2026, 11, 1, 15, 0),
        end_time=datetime(2026, 11, 1, 17, 0),
        location="Airport C",
    )
    graph_valid = JourneyDependencyGraph("trip_test_mct_valid")
    graph_valid.add_node(f1)
    graph_valid.add_node(f2_valid)

    report_valid = ConstraintEngine.evaluate_itinerary_graph(graph_valid)
    assert report_valid.is_feasible
    assert len(report_valid.hard_violations) == 0


def test_passport_validity_rule():
    graph = JourneyDependencyGraph("trip_test_passport")
    f1 = JourneyNode(
        node_id="f1",
        node_type=NodeType.FLIGHT,
        title="Flight to Tokyo",
        start_time=datetime(2026, 11, 1, 10, 0),
        end_time=datetime(2026, 11, 10, 18, 0),
        location="Tokyo",
    )
    graph.add_node(f1)

    # Traveler with passport expiring only 60 days after return
    travelers = [
        {
            "name": "Alice Wonderland",
            "passport_expiry": "2027-01-09",  # 60 days after 2026-11-10
        }
    ]

    report = ConstraintEngine.evaluate_itinerary_graph(graph, travelers=travelers)
    assert not report.is_feasible
    assert len(report.hard_violations) == 1
    assert report.hard_violations[0].category == ConstraintCategory.REGULATORY_PASSPORT
    assert "Alice Wonderland" in report.hard_violations[0].affected_elements


def test_schengen_90_day_limit():
    graph = JourneyDependencyGraph("trip_test_schengen")
    # 100-day stay in France
    f1 = JourneyNode(
        node_id="f_in",
        node_type=NodeType.FLIGHT,
        title="Flight into Paris",
        start_time=datetime(2026, 6, 1, 10, 0),
        end_time=datetime(2026, 6, 1, 18, 0),
        location="Paris, France",
    )
    f2 = JourneyNode(
        node_id="f_out",
        node_type=NodeType.FLIGHT,
        title="Flight out of Nice",
        start_time=datetime(2026, 9, 15, 10, 0),
        end_time=datetime(2026, 9, 15, 18, 0),
        location="Nice, France",
    )
    graph.add_node(f1)
    graph.add_node(f2)

    report = ConstraintEngine.evaluate_itinerary_graph(graph)
    assert not report.is_feasible
    assert any(v.category == ConstraintCategory.REGULATORY_VISA_SCHENGEN for v in report.hard_violations)
