"""
Crisis Evacuation & Irregular Operations Engine Tests (PER-950889, PER-950898, PER-950890).
"""

from src.crisis.models import CrisisIncident, CrisisSeverity, GeofenceArea, EvacuationMode
from src.crisis.evacuation_engine import EvacuationRouter
from src.crisis.ground_dispatch import GroundDispatchEngine
from src.crisis.safety_beacon import SafetyBeaconEngine


def test_critical_evacuation_routing():
    incident = CrisisIncident(
        incident_id="CRISIS-JP-001",
        headline="Typhoon Category 5 Grounding Commercial Flights",
        severity=CrisisSeverity.CRITICAL_EVACUATION,
        geofence=GeofenceArea(
            center_latitude=35.6762,
            center_longitude=139.6503,
            radius_km=150.0,
            country_code="JP",
            region_name="Tokyo / Kanto",
        ),
    )

    manifest = EvacuationRouter.generate_evacuation_manifest(
        incident=incident,
        trip_id="TRIP-JP-901",
        passengers=["Alex Morgan", "Taylor Morgan"],
        current_location="Park Hyatt Tokyo",
        safe_destination="LHR",
    )

    assert manifest.manifest_id.startswith("EVAC-")
    assert manifest.is_charter_confirmed is True
    assert len(manifest.evacuation_legs) == 2
    assert manifest.evacuation_legs[0].mode == EvacuationMode.OVERLAND_CONVOY
    assert manifest.evacuation_legs[1].mode == EvacuationMode.AIR_CHARTER
    assert manifest.total_evacuation_cost > 15_000.0


def test_ground_driver_dispatch():
    dispatch = GroundDispatchEngine.dispatch_driver(
        passenger_name="Alex Morgan",
        pickup_location="Hotel Safe Zone",
        dropoff_location="Private Airfield Hangar 4",
    )

    assert dispatch["status"] == "EN_ROUTE"
    assert "driver_name" in dispatch
    assert "SEC-" in dispatch["vehicle_plate"]
    assert "EMERGENCY DISPATCH" in dispatch["sms_alert_dispatched"]


def test_safety_beacon_and_consular_step():
    beacon = SafetyBeaconEngine.process_check_in(
        trip_id="TRIP-JP-901",
        passenger_name="Alex Morgan",
        status="SAFE_IN_SHELTER",
    )
    assert beacon["duty_of_care_acknowledged"] is True
    assert beacon["status"] == "SAFE_IN_SHELTER"

    manifest = SafetyBeaconEngine.generate_consular_step_manifest(
        incident_id="CRISIS-JP-001",
        country="Japan",
        affected_passengers=[
            {"name": "Alex Morgan", "passport": "A12345678", "nationality": "USA"},
            {"name": "Taylor Morgan", "passport": "A87654321", "nationality": "USA"},
        ],
    )
    assert manifest["passengers_registered_count"] == 2
    assert manifest["consular_status"] == "TRANSMITTED_TO_EMBASSY_DESK"
