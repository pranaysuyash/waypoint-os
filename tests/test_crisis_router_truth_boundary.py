"""Truth-boundary tests for the local crisis operations API router.

The lower-level crisis engines retain their historical unit contracts. These
tests exercise the API surface, where operational-looking simulator output must
be downgraded to a clearly non-operative preview until real providers exist.
"""

from spine_api.routers.crisis_ops import (
    BeaconCheckInRequest,
    ConsularManifestRequest,
    DispatchDriverRequest,
    EvacuationPlanRequest,
    GeofenceAlertRequest,
    declare_crisis_incident,
    dispatch_emergency_driver,
    generate_consular_step_manifest,
    generate_evacuation_manifest,
    record_passenger_safety_beacon,
)


def _assert_preview_contract(response: dict) -> None:
    assert response["status"] == "PREVIEW_ONLY"
    assert response["reality_tier"] == "deterministic_preview"
    assert response["simulation"] is True
    assert response["provider_connected"] is False
    assert response["external_action"] is False
    assert response["operational_write"] is False
    assert response["effects"] == []
    assert response["metadata"]["source"] == "local_deterministic_preview"
    assert response["metadata"]["simulation"] is True
    assert response["metadata"]["external_reference"] is None


def test_crisis_declaration_has_no_fabricated_registry_state() -> None:
    response = declare_crisis_incident(
        GeofenceAlertRequest(incident_id="INC-1", headline="Unverified alert")
    )

    _assert_preview_contract(response)
    assert response["incident"]["affected_trips"] == []
    assert response["incident"]["active_passengers_count"] == 0
    assert response["incident"]["evidence_status"] == "UNVERIFIED_LOCAL_INPUT"


def test_evacuation_plan_downgrades_booking_like_leg_statuses() -> None:
    response = generate_evacuation_manifest(
        EvacuationPlanRequest(
            incident_id="INC-1",
            trip_id="TRIP-1",
            passengers=["Alex Morgan"],
            current_location="Unknown shelter",
        )
    )

    _assert_preview_contract(response)
    manifest = response["manifest"]
    assert manifest["is_charter_confirmed"] is False
    assert manifest["consular_case_number"] is None
    assert "Verified Safe Zone" not in manifest["assembly_point"]
    assert all(leg["status"] == "PREVIEW_ONLY" for leg in manifest["evacuation_legs"])
    assert all(leg["carrier"] == "UNVERIFIED_PROVIDER_PREVIEW" for leg in manifest["evacuation_legs"])


def test_ground_dispatch_preview_does_not_assign_driver_or_notify() -> None:
    response = dispatch_emergency_driver(
        DispatchDriverRequest(
            passenger_name="Alex Morgan",
            pickup_location="Unknown shelter",
            dropoff_location="Unknown airfield",
        )
    )

    _assert_preview_contract(response)
    dispatch = response["dispatch"]
    assert dispatch["dispatch_id"].startswith("PREVIEW-DRV-")
    assert dispatch["status"] == "PREVIEW_ONLY"
    assert dispatch["driver_name"] is None
    assert dispatch["driver_phone"] is None
    assert dispatch["vehicle_plate"] is None
    assert dispatch["emergency_contact_notified"] is False
    assert dispatch["notification_status"] == "NOT_SENT"
    assert dispatch["external_reference"] is None


def test_beacon_preview_does_not_assert_safety_or_persist_telemetry() -> None:
    response = record_passenger_safety_beacon(
        BeaconCheckInRequest(trip_id="TRIP-1", passenger_name="Alex Morgan")
    )

    _assert_preview_contract(response)
    beacon = response["beacon"]
    assert beacon["status"] == "PREVIEW_ONLY"
    assert beacon["requested_status"] == "SAFE_IN_SHELTER"
    assert beacon["check_in_recorded"] is False
    assert beacon["duty_of_care_acknowledged"] is False
    assert beacon["timestamp"] is None
    assert beacon["external_reference"] is None


def test_step_manifest_is_a_draft_and_never_transmitted() -> None:
    response = generate_consular_step_manifest(
        ConsularManifestRequest(
            incident_id="INC-1",
            country="Japan",
            affected_passengers=[{"name": "Alex Morgan"}],
        )
    )

    _assert_preview_contract(response)
    manifest = response["consular_manifest"]
    assert manifest["registry_id"].startswith("PREVIEW-STEP-")
    assert manifest["consular_status"] == "DRAFT_NOT_TRANSMITTED"
    assert manifest["submission_status"] == "NOT_SUBMITTED"
    assert manifest["transmitted_at"] is None
    assert manifest["external_reference"] is None
    # Missing fields remain unknown instead of being filled with fake passport,
    # phone, nationality, or hotel values by the old engine.
    entry = manifest["manifest_entries"][0]
    assert entry["passport_number"] is None
    assert entry["emergency_phone"] is None
    assert entry["nationality"] is None
    assert entry["current_known_hotel"] is None
