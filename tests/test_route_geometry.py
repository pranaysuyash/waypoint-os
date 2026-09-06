"""
tests/test_route_geometry.py — Unit tests for Geodesic Path Optimization & Route Geometry Intelligence.

Tests:
1. Haversine great circle distance and initial bearing calculations.
2. GeodesicPathOptimizer sequence distance and waypoint TSP ordering.
3. Suboptimal zigzagging backtracking detection and optimal ordering suggestion.
4. Open-jaw ground sector detection and ARNK surface segment (`//`) tagging.
"""

import pytest
from src.logistics.route_geometry import (
    GeodesicPathOptimizer,
    calculate_initial_bearing,
    detect_backtracking,
    detect_open_jaw_surface_segments,
    haversine_distance,
)


def test_haversine_distance_accuracy():
    """Verify great circle distance between known coordinate pairs."""
    # JFK to LHR: ~5540 km (~2990 nm)
    jfk_lat, jfk_lon = 40.6413, -73.7781
    lhr_lat, lhr_lon = 51.4700, -0.4543

    dist_km = haversine_distance(jfk_lat, jfk_lon, lhr_lat, lhr_lon, unit="km")
    dist_nm = haversine_distance(jfk_lat, jfk_lon, lhr_lat, lhr_lon, unit="nm")
    dist_mi = haversine_distance(jfk_lat, jfk_lon, lhr_lat, lhr_lon, unit="mi")

    assert 5500 < dist_km < 5600
    assert 2950 < dist_nm < 3050
    assert 3400 < dist_mi < 3500

    # Identical point returns 0.0
    assert haversine_distance(jfk_lat, jfk_lon, jfk_lat, jfk_lon) == 0.0


def test_initial_bearing():
    """Verify initial compass bearing between geographic points."""
    # Northwards along meridian
    bearing_n = calculate_initial_bearing(0.0, 0.0, 10.0, 0.0)
    assert pytest.approx(bearing_n, 0.1) == 0.0

    # Eastwards along equator
    bearing_e = calculate_initial_bearing(0.0, 0.0, 0.0, 10.0)
    assert pytest.approx(bearing_e, 0.1) == 90.0


def test_geodesic_path_optimizer_waypoint_ordering():
    """Verify path optimizer sorts zig-zagging multi-city itinerary into optimal sequence."""
    # Suboptimal zigzag: London -> Tokyo -> Paris -> Rome
    unoptimized_stops = [
        {"id": "LHR", "name": "London", "lat": 51.4700, "lng": -0.4543},
        {"id": "HND", "name": "Tokyo", "lat": 35.5494, "lng": 139.7798},
        {"id": "CDG", "name": "Paris", "lat": 49.0097, "lng": 2.5479},
        {"id": "FCO", "name": "Rome", "lat": 41.8003, "lng": 12.2389},
    ]

    optimized = GeodesicPathOptimizer.optimize_waypoint_order(unoptimized_stops, fix_start=True)
    opt_ids = [s["id"] for s in optimized]

    # Optimal sequence starting at LHR should visit CDG then FCO then HND (or LHR -> CDG -> FCO -> HND)
    assert opt_ids[0] == "LHR"
    assert opt_ids[-1] == "HND"
    assert opt_ids == ["LHR", "CDG", "FCO", "HND"]

    # Compare total distances
    orig_dist = GeodesicPathOptimizer.calculate_total_distance(unoptimized_stops)
    opt_dist = GeodesicPathOptimizer.calculate_total_distance(optimized)
    assert opt_dist < orig_dist


def test_detect_backtracking_zigzag():
    """Verify detect_backtracking detects severe zigzagging and suggests optimal order."""
    # Ping-pong route: NYC -> LA -> Boston -> SF
    zigzag_stops = [
        {"airport": "JFK", "name": "New York"},
        {"airport": "LAX", "name": "Los Angeles"},
        {"airport": "BOS", "name": "Boston"},
        {"airport": "SFO", "name": "San Francisco"},
    ]

    has_backtracking, excess_km, suggested_order = detect_backtracking(zigzag_stops)

    assert has_backtracking is True
    assert excess_km > 3000.0  # Transcontinental ping-pong creates massive excess distance
    assert suggested_order[0] in ("JFK", "New York")
    # Suggested order should group East Coast together (JFK -> BOS -> SFO/LAX)
    assert suggested_order[1] in ("BOS", "Boston")


def test_detect_backtracking_clean_linear_route():
    """Verify linear progression has no backtracking."""
    # Linear route: London -> Paris -> Rome
    linear_stops = [
        {"airport": "LHR", "name": "London"},
        {"airport": "CDG", "name": "Paris"},
        {"airport": "FCO", "name": "Rome"},
    ]

    has_backtracking, excess_km, suggested_order = detect_backtracking(linear_stops)

    assert has_backtracking is False
    assert excess_km <= 50.0
    assert suggested_order == ["LHR", "CDG", "FCO"]


def test_detect_open_jaw_surface_segments():
    """Verify open-jaw ground connections are automatically identified and marked with //."""
    legs = [
        {
            "leg_id": "L1",
            "from_airport": "LHR",
            "to_airport": "JFK",
            "flight_number": "BA-175",
        },
        {
            "leg_id": "L2",
            "from_airport": "BOS",
            "to_airport": "LHR",
            "flight_number": "BA-212",
        },
    ]

    enriched = detect_open_jaw_surface_segments(legs)

    assert len(enriched) == 3
    assert enriched[0]["leg_id"] == "L1"
    # Middle segment is inserted surface segment
    surface_seg = enriched[1]
    assert surface_seg["segment_type"] == "SURFACE"
    assert surface_seg["surface_indicator"] == "//"
    assert surface_seg["is_open_jaw_surface"] is True
    assert surface_seg["origin"] == "JFK"
    assert surface_seg["destination"] == "BOS"
    assert surface_seg["estimated_surface_distance_km"] is not None
    assert surface_seg["estimated_surface_distance_km"] > 250.0  # NYC to Boston ~300 km
    assert enriched[2]["leg_id"] == "L2"
