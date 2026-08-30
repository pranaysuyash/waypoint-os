"""
Crisis Operations & Emergency Evacuation API Router (PER-950889, PER-950898, PER-950890).

Provides REST endpoints for crisis geofence event registration, multi-modal
evacuation manifest routing, live ground driver dispatch, and consular registry liaison.
"""

from __future__ import annotations

from typing import Any, Dict, List
from fastapi import APIRouter
from pydantic import BaseModel

from src.crisis.evacuation_engine import EvacuationRouter
from src.crisis.ground_dispatch import GroundDispatchEngine
from src.crisis.safety_beacon import SafetyBeaconEngine
from src.crisis.models import CrisisIncident, CrisisSeverity, GeofenceArea

router = APIRouter(prefix="/api/v1/crisis", tags=["crisis_ops"])


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
        affected_trips=["TRIP-8491", "TRIP-9024"],
        active_passengers_count=4,
    )

    return {
        "status": "success",
        "incident": incident.to_dict(),
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
        headline="Active Crisis Event",
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

    return {
        "status": "success",
        "manifest": manifest.to_dict(),
    }


@router.post("/ground/dispatch")
def dispatch_emergency_driver(payload: DispatchDriverRequest) -> Dict[str, Any]:
    """Dispatches a ground transfer driver with emergency notification."""
    res = GroundDispatchEngine.dispatch_driver(
        passenger_name=payload.passenger_name,
        pickup_location=payload.pickup_location,
        dropoff_location=payload.dropoff_location,
        vehicle_type=payload.vehicle_type,
    )
    return {
        "status": "success",
        "dispatch": res,
    }


@router.post("/beacon/check-in")
def record_passenger_safety_beacon(payload: BeaconCheckInRequest) -> Dict[str, Any]:
    """Records real-time passenger safety check-in telemetry."""
    res = SafetyBeaconEngine.process_check_in(
        trip_id=payload.trip_id,
        passenger_name=payload.passenger_name,
        status=payload.status,
        gps_coordinates=payload.gps_coordinates,
        battery_level=payload.battery_level,
    )
    return {
        "status": "success",
        "beacon": res,
    }


@router.post("/consular/step-manifest")
def generate_consular_step_manifest(payload: ConsularManifestRequest) -> Dict[str, Any]:
    """Generates an official State Department / Consular STEP manifest."""
    res = SafetyBeaconEngine.generate_consular_step_manifest(
        incident_id=payload.incident_id,
        country=payload.country,
        affected_passengers=payload.affected_passengers,
    )
    return {
        "status": "success",
        "consular_manifest": res,
    }
