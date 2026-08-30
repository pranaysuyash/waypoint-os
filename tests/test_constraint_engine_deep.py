"""
tests/test_constraint_engine_deep.py — Unit tests for PER-0711 deep constraint rules (blank pages, driver age).
"""

from datetime import datetime, timedelta, timezone
from src.decision.constraint_engine import ConstraintEngine
from src.schemas.journey_graph import JourneyDependencyGraph, JourneyNode, NodeType


def test_passport_blank_pages_constraint():
    """Verify deficit in blank passport visa pages produces a hard blocking violation."""
    now = datetime(2026, 10, 1, 10, 0, tzinfo=timezone.utc)
    graph = JourneyDependencyGraph(trip_id="trip_pages_001")
    graph.add_node(JourneyNode("fl_1", NodeType.FLIGHT, "JFK-NBO", now, now + timedelta(hours=14), "Nairobi"))

    travelers = [
        {"name": "David", "passport_expiry": "2028-10-01", "blank_visa_pages": 1}  # Deficit (<2)!
    ]

    report = ConstraintEngine.evaluate_itinerary_graph(graph, travelers=travelers)
    assert report.is_feasible is False
    assert any(hv.constraint_id == "PASSPORT_BLANK_PAGES_DEFICIT" for hv in report.hard_violations)


def test_underage_driver_car_rental_constraint():
    """Verify car rental with driver under 21 produces a hard blocking violation."""
    now = datetime(2026, 10, 1, 10, 0, tzinfo=timezone.utc)
    graph = JourneyDependencyGraph(trip_id="trip_driver_001")
    graph.add_node(JourneyNode("car_1", NodeType.TRANSFER, "Car Rental Hertz", now, now + timedelta(days=3), "Rome"))

    travelers = [
        {"name": "Young Driver", "passport_expiry": "2028-10-01", "blank_visa_pages": 4, "age": 19}  # Underage (<21)!
    ]

    report = ConstraintEngine.evaluate_itinerary_graph(graph, travelers=travelers)
    assert report.is_feasible is False
    assert any(hv.constraint_id == "DRIVER_UNDERAGE_VIOLATION" for hv in report.hard_violations)
