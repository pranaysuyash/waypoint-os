"""
tests/test_logistics_operations_suite.py — Unit and REST API Tests for Operations & Logistics Intelligence (Area #17).

Tests:
1. Group Rooming List & Single Supplement Allocation (Area #17.11)
2. Vehicle Fleet & Luggage Capacity Allocation (Area #17.12)
3. Timed Entry Admission Window & Pacing Audit (Area #17.13)
4. Hub Flight Connection MCT & Transit Risk Scorer (Area #17.18)
5. Traveler Accessibility & Airline SSR Code Generation (Area #17.16)
6. Logistics REST Router API Integration
"""

import os

import pytest
from datetime import timedelta
from fastapi.testclient import TestClient

from spine_api.server import app
from spine_api.core.security import create_access_token
from src.logistics.rooming_list import (
    BeddingType,
    RoomingListEngine,
    RoomType,
    TravelerRoomingProfile,
)
from src.logistics.fleet_allocation import (
    FleetAllocationEngine,
    VehicleCategory,
)
from src.logistics.timed_entry import (
    SlotStatus,
    TimedEntryScheduler,
    TimedEntrySlot,
)
from src.logistics.connection_risk import (
    ConnectionRiskLevel,
    ConnectionRiskScorer,
)
from src.logistics.accessibility import (
    AccessibilityPlanner,
    AccessibilityProfile,
    WheelchairMobilityLevel,
)

os.environ["RUNNING_TESTS"] = "1"


# SPINE_API_DISABLE_AUTH must NOT be set at module level: pytest imports every
# test module during collection, so a module-level write disabled authentication
# for the ENTIRE process (it silently broke the auth-middleware 401 tests).
# Scope it per-test instead; middleware reads the flag at request time.
@pytest.fixture(autouse=True)
def _disable_auth_for_this_module(monkeypatch):
    monkeypatch.setenv("SPINE_API_DISABLE_AUTH", "1")
    monkeypatch.setenv("DATA_PRIVACY_MODE", "beta")


token = create_access_token(
    user_id="usr_logistics_test",
    agency_id="agency_logistics_test",
    role="owner",
    expires_delta=timedelta(hours=12),
)
client = TestClient(app, headers={"Authorization": f"Bearer {token}", "X-Agency-ID": "agency_logistics_test"})


# ---------------------------------------------------------------------------
# 1. Rooming List Engine Tests
# ---------------------------------------------------------------------------

def test_rooming_list_single_supplement_and_couples():
    """Verify single supplement calculation and couple room pairing."""
    travelers = [
        TravelerRoomingProfile(traveler_id="t1", name="Alice Smith", gender="F", age=34, requires_single_room=True),
        TravelerRoomingProfile(traveler_id="t2", name="Bob Jones", gender="M", age=40, family_group_id="fam1", preferred_roommate_id="t3"),
        TravelerRoomingProfile(traveler_id="t3", name="Carol Jones", gender="F", age=38, family_group_id="fam1", preferred_roommate_id="t2"),
        TravelerRoomingProfile(traveler_id="t4", name="David Miller", gender="M", age=29),
        TravelerRoomingProfile(traveler_id="t5", name="Eric Davis", gender="M", age=31),
    ]

    res = RoomingListEngine.generate_rooming_list(
        trip_id="trip_room_1",
        hotel_name="Grand Hotel Rome",
        travelers=travelers,
        custom_single_supplement_usd=400.0,
    )

    assert res.total_travelers == 5
    assert res.total_rooms == 3
    assert res.total_single_supplements_usd == 400.0  # Alice's single room

    # Check Alice's single room
    alice_room = next(r for r in res.allocations if "Alice Smith" in r.assigned_traveler_names)
    assert alice_room.room_type == RoomType.SINGLE
    assert alice_room.is_single_supplement_applied is True

    # Check Jones couple room
    jones_room = next(r for r in res.allocations if "Bob Jones" in r.assigned_traveler_names)
    assert jones_room.room_type == RoomType.DOUBLE
    assert "Carol Jones" in jones_room.assigned_traveler_names

    # Check David & Eric twin sharing room
    male_room = next(r for r in res.allocations if "David Miller" in r.assigned_traveler_names)
    assert male_room.room_type == RoomType.TWIN_SHARING
    assert male_room.bedding == BeddingType.TWIN_SEPARATE


# ---------------------------------------------------------------------------
# 2. Fleet & Transfer Vehicle Allocation Tests
# ---------------------------------------------------------------------------

def test_fleet_allocation_small_group_sedan():
    """Verify 2 passengers with 2 bags get single executive sedan."""
    res = FleetAllocationEngine.calculate_allocation(
        trip_id="fleet_trip_1",
        passenger_count=2,
        standard_luggage_count=2,
    )
    assert len(res.recommended_vehicles) == 1
    assert res.recommended_vehicles[0].vehicle_category == VehicleCategory.SEDAN
    assert res.is_split_transfer is False


def test_fleet_allocation_upgrade_for_oversized_bags():
    """Verify small party with heavy luggage & golf bags upgrades to Executive Van for 7 luggage units."""
    res = FleetAllocationEngine.calculate_allocation(
        trip_id="fleet_trip_2",
        passenger_count=2,
        standard_luggage_count=3,
        oversized_bags_count=2,  # 2 golf bags = 4 bags equivalent -> total 7 bags
    )
    assert len(res.recommended_vehicles) == 1
    assert res.recommended_vehicles[0].vehicle_category == VehicleCategory.EXECUTIVE_VAN_TEMPO


def test_fleet_allocation_large_group_coach():
    """Verify 35 passengers allocate full touring coach."""
    res = FleetAllocationEngine.calculate_allocation(
        trip_id="fleet_trip_3",
        passenger_count=35,
        standard_luggage_count=35,
    )
    assert len(res.recommended_vehicles) == 1
    assert res.recommended_vehicles[0].vehicle_category == VehicleCategory.FULL_COACH


# ---------------------------------------------------------------------------
# 3. Timed Entry Excursion Slot Scheduler Tests
# ---------------------------------------------------------------------------

def test_timed_entry_on_schedule():
    """Verify sufficient transit buffer returns ON_SCHEDULE."""
    slot = TimedEntrySlot(
        slot_id="slot_louvre",
        venue_name="Musée du Louvre",
        entry_window_start="2026-10-15T10:00:00",
        entry_window_end="2026-10-15T10:30:00",
        recommended_arrival_buffer_minutes=20,
    )
    # Depart hotel at 09:00, 30 min transit -> Arrives at 09:30 (30 min buffer before 10:00)
    res = TimedEntryScheduler.audit_slot_transit(
        slot=slot,
        prior_activity_end_time_str="2026-10-15T09:00:00",
        transit_duration_minutes=30.0,
    )
    assert res.status == SlotStatus.ON_SCHEDULE
    assert res.is_compliant is True
    assert res.buffer_minutes == 30.0


def test_timed_entry_missed_slot_risk():
    """Verify late arrival past gate cutoff flags MISSED_SLOT_RISK."""
    slot = TimedEntrySlot(
        slot_id="slot_colosseum",
        venue_name="Colosseum Underground",
        entry_window_start="2026-10-15T14:00:00",
        entry_window_end="2026-10-15T14:15:00",
    )
    # Depart prior activity at 13:45, 35 min transit -> Arrives at 14:20 (past 14:15 cutoff)
    res = TimedEntryScheduler.audit_slot_transit(
        slot=slot,
        prior_activity_end_time_str="2026-10-15T13:45:00",
        transit_duration_minutes=35.0,
    )
    assert res.status == SlotStatus.MISSED_SLOT_RISK
    assert res.is_compliant is False
    assert len(res.warnings) >= 1


# ---------------------------------------------------------------------------
# 4. Hub Flight Connection Risk Scorer Tests
# ---------------------------------------------------------------------------

def test_connection_risk_safe_layover():
    """Verify comfortable layover at DXB returns SAFE."""
    res = ConnectionRiskScorer.evaluate_connection(
        connection_airport="DXB",
        inbound_flight="EK-501",
        outbound_flight="EK-077",
        layover_minutes=120,
        inbound_terminal="T3",
        outbound_terminal="T3",
    )
    assert res.risk_level == ConnectionRiskLevel.SAFE
    assert res.is_same_terminal is True


def test_connection_risk_self_transfer_penalty():
    """Verify separate PNR self-transfer flags +90m penalty and high risk on short layover."""
    # LHR requires 95m for T5->T3 terminal change + 90m self-transfer = 185m required
    res = ConnectionRiskScorer.evaluate_connection(
        connection_airport="LHR",
        inbound_flight="BA-112",
        outbound_flight="VS-003",
        layover_minutes=130,
        inbound_terminal="T5",
        outbound_terminal="T3",
        is_self_transfer=True,
    )
    assert res.risk_level == ConnectionRiskLevel.HIGH_MISCONNECT_RISK
    assert res.is_self_transfer is True
    assert res.required_mct_minutes == 185
    assert any("Self-Transfer" in w for w in res.warnings)


def test_connection_risk_fine_grained_terminal_pairs():
    """Verify terminal-pair lookups for CDG 2E->2G, LHR T2->T5, and JFK T4->T8."""
    # CDG 2E -> 2G (105m fine-grained MCT)
    cdg_res = ConnectionRiskScorer.evaluate_connection(
        connection_airport="CDG",
        inbound_flight="AF-007",
        outbound_flight="AF-1234",
        layover_minutes=110,
        inbound_terminal="2E",
        outbound_terminal="2G",
    )
    assert cdg_res.required_mct_minutes == 105
    assert cdg_res.risk_level == ConnectionRiskLevel.TIGHT_BUFFER
    assert any("2E ➔ 2G" in w for w in cdg_res.warnings)

    # LHR T2 -> T5 (105m fine-grained MCT)
    lhr_res = ConnectionRiskScorer.evaluate_connection(
        connection_airport="LHR",
        inbound_flight="UA-904",
        outbound_flight="BA-207",
        layover_minutes=120,
        inbound_terminal="T2",
        outbound_terminal="T5",
    )
    assert lhr_res.required_mct_minutes == 105
    assert lhr_res.risk_level == ConnectionRiskLevel.TIGHT_BUFFER

    # JFK T4 -> T8 (120m fine-grained MCT + 60m immigration = 180m)
    jfk_res = ConnectionRiskScorer.evaluate_connection(
        connection_airport="JFK",
        inbound_flight="DL-401",
        outbound_flight="AA-100",
        layover_minutes=150,
        inbound_terminal="T4",
        outbound_terminal="T8",
        requires_immigration_reclear=True,
    )
    assert jfk_res.required_mct_minutes == 180
    assert jfk_res.risk_level == ConnectionRiskLevel.HIGH_MISCONNECT_RISK
    assert any("Passport Control" in w for w in jfk_res.warnings)


# ---------------------------------------------------------------------------
# 5. Traveler Accessibility & SSR Code Generator Tests
# ---------------------------------------------------------------------------

def test_accessibility_plan_wchs_and_medical_oxygen():
    """Verify WCHS, MEDA SSR codes and hotel step-free audit."""
    profile = AccessibilityProfile(
        traveler_id="p_acc_1",
        traveler_name="Robert Vance",
        wheelchair_level=WheelchairMobilityLevel.WCHS_NO_STAIRS,
        requires_medical_oxygen=True,
        requires_step_free_room=True,
        requires_roll_in_shower=True,
    )

    plan = AccessibilityPlanner.create_accessibility_plan(
        trip_id="acc_trip_1",
        profile=profile,
        hotel_name="Waldorf Cavalieri Rome",
        hotel_has_step_free=True,
        hotel_has_roll_in_shower=True,
    )

    ssr_codes = [d.ssr_code for d in plan.airline_ssr_directives]
    assert "WCHS" in ssr_codes
    assert "MEDA" in ssr_codes
    assert plan.hotel_accessibility_audit.is_compliant is True
    assert plan.hotel_accessibility_audit.nearest_hospital_driving_time_mins > 0


# ---------------------------------------------------------------------------
# 6. Logistics REST Router API Integration Tests
# ---------------------------------------------------------------------------

def test_logistics_api_endpoints():
    """Verify REST API endpoints on /api/v1/logistics/*."""
    # Test Rooming List API
    room_resp = client.post(
        "/api/v1/logistics/rooming-list",
        json={
            "trip_id": "trip_api_room",
            "hotel_name": "Hotel Arts Barcelona",
            "travelers": [
                {"traveler_id": "u1", "name": "John Doe", "gender": "M", "age": 30, "requires_single_room": True},
                {"traveler_id": "u2", "name": "Jane Doe", "gender": "F", "age": 28, "requires_single_room": True},
            ],
            "custom_single_supplement_usd": 350.0,
        },
    )
    assert room_resp.status_code == 200
    room_data = room_resp.json()
    assert room_data["total_rooms"] == 2
    assert room_data["total_single_supplements_usd"] == 700.0

    # Test Fleet Allocation API
    fleet_resp = client.post(
        "/api/v1/logistics/fleet-allocation",
        json={
            "trip_id": "trip_api_fleet",
            "passenger_count": 8,
            "standard_luggage_count": 8,
        },
    )
    assert fleet_resp.status_code == 200
    fleet_data = fleet_resp.json()
    assert len(fleet_data["recommended_vehicles"]) == 1
    assert fleet_data["recommended_vehicles"][0]["category"] == "EXECUTIVE_VAN_TEMPO"

    # Test Connection Risk API
    conn_resp = client.post(
        "/api/v1/logistics/connection-risk",
        json={
            "connection_airport": "CDG",
            "inbound_flight": "AF-123",
            "outbound_flight": "AF-456",
            "layover_minutes": 130,
            "inbound_terminal": "2E",
            "outbound_terminal": "2F",
        },
    )
    assert conn_resp.status_code == 200
    assert conn_resp.json()["risk_level"] in ("SAFE", "TIGHT_BUFFER")

    # Test Route Geometry Evaluate API (Backtracking detection & 2-opt)
    geom_resp = client.post(
        "/api/v1/logistics/route-geometry/evaluate",
        json={
            "stops": [
                {"city": "New York", "airport_code": "JFK"},
                {"city": "Los Angeles", "airport_code": "LAX"},
                {"city": "Boston", "airport_code": "BOS"},
                {"city": "San Francisco", "airport_code": "SFO"},
            ],
            "unit": "km",
            "fix_start": True,
            "fix_end": True,
        },
    )
    assert geom_resp.status_code == 200
    geom_data = geom_resp.json()
    assert geom_data["has_backtracking"] is True
    assert geom_data["distance_savings"] > 0.0
    assert len(geom_data["suggested_order"]) == 4

    # Test Route Geometry Open-Jaw API
    open_jaw_resp = client.post(
        "/api/v1/logistics/route-geometry/open-jaw",
        json={
            "legs": [
                {"origin": "LHR", "destination": "JFK", "mode": "FLIGHT"},
                {"origin": "BOS", "destination": "LHR", "mode": "FLIGHT"},
            ],
        },
    )
    assert open_jaw_resp.status_code == 200
    oj_data = open_jaw_resp.json()
    assert oj_data["has_open_jaw"] is True
    assert oj_data["open_jaw_segments_count"] == 1
    assert len(oj_data["legs"]) == 3
    assert oj_data["legs"][1]["segment_type"] == "SURFACE"
    assert oj_data["legs"][1]["surface_indicator"] == "//"
