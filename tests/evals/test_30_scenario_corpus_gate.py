"""
tests/evals/test_30_scenario_corpus_gate.py — 30-Scenario CI Quality & Regression Gate.

Asserts zero regressions across complex traveler inquiries, multi-destination routing,
anti-zigzagging optimization, layover MCT risk scoring, and open-jaw surface detection.
"""

from __future__ import annotations

import pytest

from src.logistics.pipeline_bridge import RouteAssessmentBridge
from src.evals.audit.rules.scenarios import load_scenario_fixtures, run_scenario_eval


CANONICAL_30_SCENARIOS = [
    # 1. Classic Italy Zigzag
    {
        "id": "SCEN_01_ITALY_ZIGZAG",
        "origin": "FCO",
        "destinations": ["VCE", "FLR", "MXP"],
        "expect_backtracking": True,
        "min_savings_pct": 5.0,
    },
    # 2. Linear Japan Corridor
    {
        "id": "SCEN_02_JAPAN_GOLDEN_ROUTE",
        "origin": "HND",
        "destinations": ["KIX", "FUK"],
        "expect_backtracking": False,
        "min_savings_pct": 0.0,
    },
    # 3. US Transcontinental Triangle
    {
        "id": "SCEN_03_US_TRIANGLE",
        "origin": "JFK",
        "destinations": ["SFO", "ORD", "LAX"],
        "expect_backtracking": True,
        "min_savings_pct": 10.0,
    },
    # 4. Europe Alpine Hubs
    {
        "id": "SCEN_04_ALPINE_HUBS",
        "origin": "ZRH",
        "destinations": ["VIE", "GVA", "MUC"],
        "expect_backtracking": True,
        "min_savings_pct": 10.0,
    },
    # 5. Nordic Circuit
    {
        "id": "SCEN_05_NORDIC_CIRCUIT",
        "origin": "CPH",
        "destinations": ["HEL", "ARN", "OSL"],
        "expect_backtracking": True,
        "min_savings_pct": 5.0,
    },
]


def test_decision_gate_loads_complete_independent_30_scenario_corpus():
    """The D6 decision lane must execute every corpus fixture, not a sample.

    The route checks below are focused domain regressions.  They are not a
    substitute for the independent NB02 decision corpus consumed by the gate
    snapshot.  This assertion protects against silently shrinking that lane
    when fixtures are added, renamed, or accidentally omitted from loading.
    """
    fixtures = load_scenario_fixtures()
    assert len(fixtures) == 30
    fixture_ids = [fixture.fixture_id for fixture in fixtures]
    assert len(fixture_ids) == len(set(fixture_ids))
    assert all(fixture.expected_decision_state for fixture in fixtures)

    report = run_scenario_eval(fixtures)
    assert report.total_fixtures == len(fixtures)
    assert len(report.results) == len(fixtures)
    assert all(result.fixture_id in fixture_ids for result in report.results)


@pytest.mark.parametrize("scen", CANONICAL_30_SCENARIOS)
def test_scenario_route_geometry_optimization(scen):
    """Verify route assessment bridge correctly optimizes waypoint ordering."""
    assessment = RouteAssessmentBridge.evaluate_trip_route(
        destinations=scen["destinations"],
        origin=scen["origin"],
    )
    if scen["expect_backtracking"]:
        assert assessment.has_backtracking is True
        assert assessment.distance_savings_km > 0.0
        assert assessment.savings_percent >= scen["min_savings_pct"]
    else:
        assert assessment.has_backtracking is False


def test_scenario_open_jaw_surface_connection_corpus():
    """Verify open-jaw detection across multi-city airline segments."""
    flight_legs = [
        {"flight_number": "BA112", "origin": "LHR", "destination": "JFK"},
        {"flight_number": "AA100", "origin": "BOS", "destination": "LHR"},  # Surface gap: JFK -> BOS
    ]
    assessment = RouteAssessmentBridge.evaluate_trip_route(
        destinations=["NYC", "BOS"],
        origin="LON",
        flights=flight_legs,
    )
    assert assessment.has_open_jaw is True
    assert assessment.open_jaw_surface_segments_count == 1
    assert assessment.total_surface_distance_km > 200.0  # JFK to BOS is ~300 km
    assert any("Open-jaw surface connection" in w for w in assessment.warnings)


def test_scenario_tight_hub_connection_mct_violation():
    """Verify illegal MCT layovers are caught and flagged by the pipeline bridge."""
    flight_legs = [
        {
            "flight_number": "AF123",
            "origin": "JFK",
            "destination": "CDG",
            "arrival_terminal": "2E",
            "layover_to_next_mins": 45,  # 45m is below CDG 2E->2G MCT of 105m!
        },
        {
            "flight_number": "AF456",
            "origin": "CDG",
            "destination": "NCE",
            "departure_terminal": "2G",
        },
    ]
    assessment = RouteAssessmentBridge.evaluate_trip_route(
        destinations=["PAR", "NCE"],
        origin="NYC",
        flights=flight_legs,
    )
    assert assessment.has_illegal_mct is True
    assert any("Illegal connection at CDG" in w for w in assessment.warnings)
