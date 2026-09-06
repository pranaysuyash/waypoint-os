"""
Crisis Operations & Emergency Evacuation API Router (PER-950889, PER-950898, PER-950890).

Provides REST endpoints for crisis geofence event registration, multi-modal
evacuation manifest planning, ground-dispatch request previews, and consular
registry submission drafts. No external crisis provider is connected here.
"""

from __future__ import annotations

import hashlib
from typing import Any, Dict, List
from fastapi import APIRouter
from pydantic import BaseModel

from src.crisis.evacuation_engine import EvacuationRouter
from src.crisis.models import CrisisIncident, CrisisSeverity, GeofenceArea
from spine_api.core.reality_tier import RealityTier, TierMetadata

router = APIRouter(prefix="/api/v1/crisis", tags=["crisis_ops"])

_PREVIEW_TIER = RealityTier.DETERMINISTIC_PREVIEW


def _preview_metadata(feature_name: str, missing_for_upgrade: List[str]) -> Dict[str, Any]:
    """Return the common contract for crisis previews.

    Crisis, dispatch, beacon, and consular providers are not connected in this
    local implementation. Keeping provenance at the router boundary prevents
    a deterministic engine result from being mistaken for an external action.
    """
    metadata = TierMetadata.for_response(
        _PREVIEW_TIER,
        feature_name,
        computation_method="local deterministic preview; no external provider call or operational write",
        missing_for_upgrade=missing_for_upgrade,
    )
    metadata.update(
        {
            "source": "local_deterministic_preview",
            "simulation": True,
            "provider_connected": False,
            "external_reference": None,
            "external_action": False,
            "operational_write": False,
            "effects": [],
        }
    )
    return {
        "reality_tier": _PREVIEW_TIER.value,
        "simulation": True,
        "provider_connected": False,
        "external_action": False,
        "operational_write": False,
        "effects": [],
        "metadata": metadata,
    }


def _preview_id(prefix: str, *parts: str) -> str:
    """Create a stable, visibly non-operational identifier for a preview."""
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:10].upper()
    return f"PREVIEW-{prefix}-{digest}"


class GeofenceAlertRequest(BaseModel):
    incident_id: str
    headline: str
    severity: str = "critical_evacuation"
    latitude: float = 35.6762
    longitude: float = 139.6503
    radius_km: float = 150.0
    country_code: str = "JP"
    region_name: str = "Kanto / Tokyo"


class EvacuationPlanRequest(BaseModel):
    incident_id: str
    trip_id: str
    passengers: List[str]
    current_location: str
    safe_destination: str = "LHR"
    severity: str = "critical_evacuation"


class DispatchDriverRequest(BaseModel):
    passenger_name: str
    pickup_location: str
    dropoff_location: str
    vehicle_type: str = "Armored SUV / Close Protection"


class BeaconCheckInRequest(BaseModel):
    trip_id: str
    passenger_name: str
    status: str = "SAFE_IN_SHELTER"
    gps_coordinates: str = "35.6762° N, 139.6503° E"
    battery_level: int = 85


class ConsularManifestRequest(BaseModel):
    incident_id: str
    country: str
    affected_passengers: List[Dict[str, Any]]


@router.post("/incidents/declare")
def declare_crisis_incident(payload: GeofenceAlertRequest) -> Dict[str, Any]:
    """Declares a crisis incident with geofenced containment boundaries."""
    severity = CrisisSeverity.CRITICAL_EVACUATION
    try:
        severity = CrisisSeverity(payload.severity)
    except ValueError:
        severity = CrisisSeverity.CRITICAL_EVACUATION

    geofence = GeofenceArea(
        center_latitude=payload.latitude,
        center_longitude=payload.longitude,
        radius_km=payload.radius_km,
        country_code=payload.country_code,
        region_name=payload.region_name,
    )

    incident = CrisisIncident(
        incident_id=payload.incident_id,
        headline=payload.headline,
        severity=severity,
        geofence=geofence,
        # No trip or passenger registry is connected to this preview route.
        affected_trips=[],
        active_passengers_count=0,
        consular_advisory_level=0,
    )

    incident_data = incident.to_dict()
    incident_data["evidence_status"] = "UNVERIFIED_LOCAL_INPUT"
    return {
        "status": "PREVIEW_ONLY",
        "incident": incident_data,
        **_preview_metadata(
            "crisis_incident_declaration",
            ["connected incident feed", "trip/passenger registry", "authorized operator acknowledgement"],
        ),
    }


@router.post("/evacuation/plan")
def generate_evacuation_manifest(payload: EvacuationPlanRequest) -> Dict[str, Any]:
    """Generates an end-to-end multi-modal evacuation manifest."""
    severity = CrisisSeverity.CRITICAL_EVACUATION
    try:
        severity = CrisisSeverity(payload.severity)
    except ValueError:
        severity = CrisisSeverity.CRITICAL_EVACUATION

    incident = CrisisIncident(
        incident_id=payload.incident_id,
        headline="Unverified local crisis planning input",
        severity=severity,
        geofence=GeofenceArea(0, 0, 50, "GLOBAL", "Hazard Zone"),
    )

    manifest = EvacuationRouter.generate_evacuation_manifest(
        incident=incident,
        trip_id=payload.trip_id,
        passengers=payload.passengers,
        current_location=payload.current_location,
        safe_destination=payload.safe_destination,
    )

    manifest_data = manifest.to_dict()
    # The engine computes candidate legs, but no carrier, charter, rail, or
    # consular system has confirmed them. Make every operational-looking field
    # explicitly non-operational at the API boundary.
    manifest_data["assembly_point"] = (
        f"Unverified planning assembly point near {payload.current_location}"
    )
    manifest_data["is_charter_confirmed"] = False
    manifest_data["consular_case_number"] = None
    for leg in manifest_data["evacuation_legs"]:
        leg["carrier"] = "UNVERIFIED_PROVIDER_PREVIEW"
        leg["status"] = "PREVIEW_ONLY"
    return {
        "status": "PREVIEW_ONLY",
        "manifest": manifest_data,
        **_preview_metadata(
            "crisis_evacuation_plan",
            [
                "provider availability and booking references",
                "licensed ground/air/rail operator confirmation",
                "consular case creation",
            ],
        ),
    }


@router.post("/ground/dispatch")
def dispatch_emergency_driver(payload: DispatchDriverRequest) -> Dict[str, Any]:
    """Build a driver-dispatch request preview without sending it anywhere."""
    dispatch_id = _preview_id(
        "DRV",
        payload.passenger_name,
        payload.pickup_location,
        payload.dropoff_location,
        payload.vehicle_type,
    )
    res = {
        "dispatch_id": dispatch_id,
        "driver_name": None,
        "driver_phone": None,
        "vehicle_plate": None,
        "vehicle_type": payload.vehicle_type,
        "pickup_location": payload.pickup_location,
        "dropoff_location": payload.dropoff_location,
        "status": "PREVIEW_ONLY",
        "emergency_contact_notified": False,
        "notification_status": "NOT_SENT",
        "message_preview": "No driver, SMS, WhatsApp, or emergency contact was notified.",
        "external_reference": None,
    }
    return {
        "status": "PREVIEW_ONLY",
        "dispatch": res,
        **_preview_metadata(
            "crisis_ground_dispatch",
            [
                "licensed dispatch provider",
                "driver/vehicle assignment",
                "notification provider and delivery receipt",
            ],
        ),
    }


@router.post("/beacon/check-in")
def record_passenger_safety_beacon(payload: BeaconCheckInRequest) -> Dict[str, Any]:
    """Reflect a submitted beacon payload without persisting or asserting safety."""
    res = {
        "beacon_id": _preview_id("BCN", payload.trip_id, payload.passenger_name),
        "trip_id": payload.trip_id,
        "passenger_name": payload.passenger_name,
        "requested_status": payload.status,
        "gps_coordinates": payload.gps_coordinates,
        "battery_level": payload.battery_level,
        "status": "PREVIEW_ONLY",
        "check_in_recorded": False,
        "duty_of_care_acknowledged": False,
        "timestamp": None,
        "external_reference": None,
        "notice": "Payload was not persisted or transmitted to a safety provider.",
    }
    return {
        "status": "PREVIEW_ONLY",
        "beacon": res,
        **_preview_metadata(
            "crisis_safety_beacon",
            ["durable trip record", "authenticated beacon/device evidence", "operator acknowledgement"],
        ),
    }


@router.post("/consular/step-manifest")
def generate_consular_step_manifest(payload: ConsularManifestRequest) -> Dict[str, Any]:
    """Build a local STEP submission draft; never transmit it as official."""
    entries = [
        {
            "full_name": passenger.get("name"),
            "passport_number": passenger.get("passport"),
            "nationality": passenger.get("nationality"),
            "emergency_phone": passenger.get("phone"),
            "current_known_hotel": passenger.get("hotel"),
        }
        for passenger in payload.affected_passengers
    ]
    res = {
        "registry_id": _preview_id("STEP", payload.incident_id, payload.country),
        "incident_id": payload.incident_id,
        "destination_country": payload.country,
        "passengers_registered_count": len(entries),
        "manifest_entries": entries,
        "consular_status": "DRAFT_NOT_TRANSMITTED",
        "submission_status": "NOT_SUBMITTED",
        "transmitted_at": None,
        "external_reference": None,
        "notice": "Draft was not transmitted to an embassy, consulate, or STEP provider.",
    }
    return {
        "status": "PREVIEW_ONLY",
        "consular_manifest": res,
        **_preview_metadata(
            "crisis_step_manifest",
            [
                "authenticated consular/STEP integration",
                "official registry acceptance",
                "operator review and transmission receipt",
            ],
        ),
    }
