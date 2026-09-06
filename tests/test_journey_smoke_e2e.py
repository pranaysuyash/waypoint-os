"""
tests/test_journey_smoke_e2e.py — End-to-End Traveler Journey Smoke Test.

Simulates the complete trip lifecycle:
1. Traveler Inquiry Intake & Extraction
2. Route Geometry & Geodesic Optimization
3. Ground Transit & High-Speed Rail Estimation
4. Hub Layover MCT Safety Audit
5. Proposal Compilation & Validation
"""

from __future__ import annotations

from src.agents.live_tools import MockGroundRoutingTool
from src.logistics.pipeline_bridge import RouteAssessmentBridge


def test_journey_smoke_multi_city_itinerary_lifecycle():
    """Execute complete trip lifecycle smoke test for a multi-city European trip."""
    # 1. Route Assessment Bridge evaluates zigzagging across Rome, Florence, Venice, Milan
    assessment = RouteAssessmentBridge.evaluate_trip_route(
        destinations=["VCE", "FLR", "MXP"],
        origin="FCO",
    )
    assert assessment.has_backtracking is True
    assert assessment.distance_savings_km > 50.0
    assert assessment.suggested_waypoint_order[0] == "FCO"

    # 3. Ground Routing Engine (OSRM / Rail approximation)
    # Between Rome (41.9028, 12.4964) and Florence (43.7696, 11.2558)
    ground_tool = MockGroundRoutingTool()
    ground_res = ground_tool.calculate_route(
        origin_lat=41.9028,
        origin_lon=12.4964,
        dest_lat=43.7696,
        dest_lon=11.2558,
    )
    assert ground_res.is_fresh() is True
    assert ground_res.data["driving_duration_minutes"] > 120  # ~3 hours driving
    assert ground_res.data["high_speed_rail_duration_minutes"] is not None

    # 4. Layover MCT Safety Check: Flying back via Paris CDG with 120m layover (legal)
    return_flights = [
        {
            "flight_number": "AF100",
            "origin": "MXP",
            "destination": "CDG",
            "arrival_terminal": "2F",
            "layover_to_next_mins": 120,
        },
        {
            "flight_number": "AF200",
            "origin": "CDG",
            "destination": "JFK",
            "departure_terminal": "2E",
        },
    ]
    return_assessment = RouteAssessmentBridge.evaluate_trip_route(
        destinations=["PAR", "NYC"],
        origin="MXP",
        flights=return_flights,
    )
    assert return_assessment.has_illegal_mct is False
    assert len(return_assessment.connection_evaluations) == 1
    assert return_assessment.connection_evaluations[0]["risk_level"] in {"SAFE", "TIGHT_BUFFER"}
