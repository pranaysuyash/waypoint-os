"""
Crisis Evacuation & Irregular Operations Models (PER-950889, PER-950898, PER-950890).

Defines typed schemas for geopolitical/natural disaster alerts, geofenced hazard zones,
emergency multi-modal evacuation routing manifests, and ground dispatch.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class CrisisSeverity(str, Enum):
    CRITICAL_EVACUATION = "critical_evacuation"  # Immediate life-safety threat
    HIGH_SHELTER = "high_shelter"               # Geopolitical unrest / Category 4+ hurricane
    MODERATE_DISRUPTION = "moderate_disruption"   # Airspace closure / widespread strikes
    LOW_MONITOR = "low_monitor"                 # Weather advisory


class EvacuationMode(str, Enum):
    AIR_CHARTER = "air_charter"
    COMMERCIAL_REBOOK = "commercial_rebook"
    OVERLAND_CONVOY = "overland_convoy"
    HIGH_SPEED_RAIL = "high_speed_rail"
    MARITIME_FERRY = "maritime_ferry"


class PassengerBeaconStatus(str, Enum):
    SAFE_IN_SHELTER = "SAFE_IN_SHELTER"
    EN_ROUTE_EVACUATION = "EN_ROUTE_EVACUATION"
    ASSISTANCE_REQUESTED = "ASSISTANCE_REQUESTED"
    UNACCOUNTED = "UNACCOUNTED"
    EVACUATED_CLEARED = "EVACUATED_CLEARED"


@dataclass(slots=True)
class GeofenceArea:
    """Geographical circle or boundary for crisis containment."""
    center_latitude: float
    center_longitude: float
    radius_km: float
    country_code: str
    region_name: str


@dataclass(slots=True)
class CrisisIncident:
    """Real-time crisis alert event."""
    incident_id: str
    headline: str
    severity: CrisisSeverity
    geofence: GeofenceArea
    affected_trips: List[str] = field(default_factory=list)
    active_passengers_count: int = 0
    consular_advisory_level: int = 4
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "incident_id": self.incident_id,
            "headline": self.headline,
            "severity": self.severity.value,
            "geofence": {
                "latitude": self.geofence.center_latitude,
                "longitude": self.geofence.center_longitude,
                "radius_km": self.geofence.radius_km,
                "country_code": self.geofence.country_code,
                "region_name": self.geofence.region_name,
            },
            "affected_trips": self.affected_trips,
            "active_passengers_count": self.active_passengers_count,
            "consular_advisory_level": self.consular_advisory_level,
            "created_at": self.created_at,
        }


@dataclass(slots=True)
class EvacuationLeg:
    """A single leg in an emergency evacuation route."""
    leg_number: int
    mode: EvacuationMode
    origin: str
    destination: str
    departure_time: str
    carrier_or_provider: str
    capacity_passengers: int
    estimated_cost_usd: float
    status: str = "CONFIRMED"


@dataclass(slots=True)
class EvacuationManifest:
    """Comprehensive evacuation itinerary for affected travelers."""
    manifest_id: str
    incident_id: str
    trip_id: str
    passengers: List[str]
    assembly_point: str
    evacuation_legs: List[EvacuationLeg]
    total_evacuation_cost: float
    is_charter_confirmed: bool = False
    consular_case_number: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "manifest_id": self.manifest_id,
            "incident_id": self.incident_id,
            "trip_id": self.trip_id,
            "passengers": self.passengers,
            "assembly_point": self.assembly_point,
            "evacuation_legs": [
                {
                    "leg_number": leg.leg_number,
                    "mode": leg.mode.value,
                    "origin": leg.origin,
                    "destination": leg.destination,
                    "departure_time": leg.departure_time,
                    "carrier": leg.carrier_or_provider,
                    "cost_usd": leg.estimated_cost_usd,
                    "status": leg.status,
                }
                for leg in self.evacuation_legs
            ],
            "total_evacuation_cost": self.total_evacuation_cost,
            "is_charter_confirmed": self.is_charter_confirmed,
            "consular_case_number": self.consular_case_number,
            "created_at": self.created_at,
        }


@dataclass(slots=True)
class GroundTransferDispatch:
    """Live ground transfer / emergency driver dispatch state."""
    dispatch_id: str
    driver_name: str
    driver_phone: str
    vehicle_plate: str
    vehicle_type: str
    pickup_location: str
    dropoff_location: str
    status: str = "EN_ROUTE"  # ASSIGNED, EN_ROUTE, ARRIVED, COMPLETED
    emergency_contact_notified: bool = True
