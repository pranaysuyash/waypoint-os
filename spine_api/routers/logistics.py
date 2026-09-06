"""
spine_api/routers/logistics.py — Operations & Logistics Intelligence Router (Area #17).

Endpoints:
- POST /api/v1/logistics/rooming-list        — Group rooming list & single supplement engine
- POST /api/v1/logistics/fleet-allocation   — Vehicle capacity & fleet matching
- POST /api/v1/logistics/timed-entry-audit  — Timed admission window & transit buffer audit
- POST /api/v1/logistics/connection-risk    — Flight connection MCT & transfer risk evaluation
- POST /api/v1/logistics/accessibility-plan — Airline SSR code generator & hotel accessibility audit
"""

from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter

from src.logistics.rooming_list import (
    RoomingListEngine,
    TravelerRoomingProfile,
)
from src.logistics.fleet_allocation import (
    FleetAllocationEngine,
)
from src.logistics.timed_entry import (
    TimedEntryScheduler,
    TimedEntrySlot,
)
from src.logistics.connection_risk import (
    ConnectionRiskScorer,
)
from src.logistics.accessibility import (
    AccessibilityPlanner,
    AccessibilityProfile,
    WheelchairMobilityLevel,
)
from src.logistics.route_geometry import (
    GeodesicPathOptimizer,
    detect_backtracking,
    detect_open_jaw_surface_segments,
)

router = APIRouter(prefix="/api/v1/logistics", tags=["Operations & Logistics Intelligence"])


# ---------------------------------------------------------------------------
# Schema Models
# ---------------------------------------------------------------------------

class TravelerRoomingInput(BaseModel):
    traveler_id: str
    name: str
    gender: str = "M"
    age: int = 35
    family_group_id: Optional[str] = None
    preferred_roommate_id: Optional[str] = None
    requires_single_room: bool = False
    needs_crib: bool = False


class RoomingListRequest(BaseModel):
    trip_id: str
    hotel_name: str
    travelers: List[TravelerRoomingInput]
    custom_single_supplement_usd: Optional[float] = None


class FleetAllocationRequest(BaseModel):
    trip_id: str
    passenger_count: int
    standard_luggage_count: int
    child_seats_count: int = 0
    oversized_bags_count: int = 0


class TimedEntryAuditRequest(BaseModel):
    slot_id: str
    venue_name: str
    entry_window_start: str
    entry_window_end: str
    prior_activity_end_time: str
    transit_duration_minutes: float
    recommended_arrival_buffer_minutes: int = 20


class ConnectionRiskRequest(BaseModel):
    connection_airport: str
    inbound_flight: str
    outbound_flight: str
    layover_minutes: int
    inbound_terminal: str = "T1"
    outbound_terminal: str = "T1"
    is_self_transfer: bool = False
    requires_immigration_reclear: bool = False
    custom_self_transfer_penalty_mins: Optional[int] = None


class AccessibilityPlanRequest(BaseModel):
    trip_id: str
    traveler_id: str
    traveler_name: str
    wheelchair_level: WheelchairMobilityLevel = WheelchairMobilityLevel.NONE
    requires_medical_oxygen: bool = False
    is_visually_impaired: bool = False
    is_hearing_impaired: bool = False
    requires_step_free_room: bool = False
    requires_roll_in_shower: bool = False
    hotel_name: str = "Grand Hotel Central"
    hotel_has_step_free: bool = True
    hotel_has_elevator: bool = True
    hotel_has_roll_in_shower: bool = True


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/rooming-list")
def generate_rooming_list_endpoint(payload: RoomingListRequest):
    """Allocate travelers to hotel rooms and compute single supplement totals."""
    domain_travelers = [
        TravelerRoomingProfile(
            traveler_id=t.traveler_id,
            name=t.name,
            gender=t.gender,
            age=t.age,
            family_group_id=t.family_group_id,
            preferred_roommate_id=t.preferred_roommate_id,
            requires_single_room=t.requires_single_room,
            needs_crib=t.needs_crib,
        )
        for t in payload.travelers
    ]

    res = RoomingListEngine.generate_rooming_list(
        trip_id=payload.trip_id,
        hotel_name=payload.hotel_name,
        travelers=domain_travelers,
        custom_single_supplement_usd=payload.custom_single_supplement_usd,
    )

    return {
        "trip_id": res.trip_id,
        "hotel_name": res.hotel_name,
        "total_travelers": res.total_travelers,
        "total_rooms": res.total_rooms,
        "total_single_supplements_usd": res.total_single_supplements_usd,
        "allocations": [
            {
                "room_number": a.room_number,
                "room_type": a.room_type.value,
                "bedding": a.bedding.value,
                "assigned_travelers": a.assigned_traveler_names,
                "single_supplement_applied": a.is_single_supplement_applied,
                "single_supplement_cost_usd": a.single_supplement_cost_usd,
                "notes": a.notes,
            }
            for a in res.allocations
        ],
        "audit_notes": res.audit_notes,
    }


@router.post("/fleet-allocation")
def allocate_fleet_endpoint(payload: FleetAllocationRequest):
    """Recommend vehicle fleet by passenger and luggage capacity."""
    res = FleetAllocationEngine.calculate_allocation(
        trip_id=payload.trip_id,
        passenger_count=payload.passenger_count,
        standard_luggage_count=payload.standard_luggage_count,
        child_seats_count=payload.child_seats_count,
        oversized_bags_count=payload.oversized_bags_count,
    )

    return {
        "trip_id": res.trip_id,
        "passenger_count": res.passenger_count,
        "total_luggage_count": res.total_luggage_count,
        "total_estimated_cost_usd": res.total_estimated_cost_usd,
        "is_split_transfer": res.is_split_transfer,
        "overflow_warning": res.overflow_warning,
        "recommended_vehicles": [
            {
                "category": v.vehicle_category.value,
                "display_name": v.display_name,
                "quantity": v.quantity,
                "passenger_capacity": v.total_passenger_capacity,
                "luggage_capacity": v.total_luggage_capacity,
                "cost_usd": v.estimated_base_cost_usd,
                "notes": v.notes,
            }
            for v in res.recommended_vehicles
        ],
    }


@router.post("/timed-entry-audit")
def audit_timed_entry_endpoint(payload: TimedEntryAuditRequest):
    """Audit timed admission slot against preceding activity transit times."""
    slot = TimedEntrySlot(
        slot_id=payload.slot_id,
        venue_name=payload.venue_name,
        entry_window_start=payload.entry_window_start,
        entry_window_end=payload.entry_window_end,
        recommended_arrival_buffer_minutes=payload.recommended_arrival_buffer_minutes,
    )

    res = TimedEntryScheduler.audit_slot_transit(
        slot=slot,
        prior_activity_end_time_str=payload.prior_activity_end_time,
        transit_duration_minutes=payload.transit_duration_minutes,
    )

    return {
        "slot_id": res.slot_id,
        "venue_name": res.venue_name,
        "scheduled_arrival_time": res.scheduled_arrival_time,
        "status": res.status.value,
        "buffer_minutes": res.buffer_minutes,
        "is_compliant": res.is_compliant,
        "warnings": res.warnings,
        "recommended_departure_time": res.recommended_departure_time,
    }


@router.post("/connection-risk")
def evaluate_connection_risk_endpoint(payload: ConnectionRiskRequest):
    """Evaluate flight layover transit risk against IATA Minimum Connection Times."""
    res = ConnectionRiskScorer.evaluate_connection(
        connection_airport=payload.connection_airport,
        inbound_flight=payload.inbound_flight,
        outbound_flight=payload.outbound_flight,
        layover_minutes=payload.layover_minutes,
        inbound_terminal=payload.inbound_terminal,
        outbound_terminal=payload.outbound_terminal,
        is_self_transfer=payload.is_self_transfer,
        requires_immigration_reclear=payload.requires_immigration_reclear,
        custom_self_transfer_penalty_mins=payload.custom_self_transfer_penalty_mins,
    )

    return {
        "connection_airport": res.connection_airport,
        "layover_minutes": res.layover_minutes,
        "required_mct_minutes": res.required_mct_minutes,
        "risk_level": res.risk_level.value,
        "is_same_terminal": res.is_same_terminal,
        "is_self_transfer": res.is_self_transfer,
        "warnings": res.warnings,
        "recommendation": res.recommendation,
    }


@router.post("/accessibility-plan")
def create_accessibility_plan_endpoint(payload: AccessibilityPlanRequest):
    """Generate airline SSR directives and audit hotel accessibility."""
    profile = AccessibilityProfile(
        traveler_id=payload.traveler_id,
        traveler_name=payload.traveler_name,
        wheelchair_level=payload.wheelchair_level,
        requires_medical_oxygen=payload.requires_medical_oxygen,
        is_visually_impaired=payload.is_visually_impaired,
        is_hearing_impaired=payload.is_hearing_impaired,
        requires_step_free_room=payload.requires_step_free_room,
        requires_roll_in_shower=payload.requires_roll_in_shower,
    )

    res = AccessibilityPlanner.create_accessibility_plan(
        trip_id=payload.trip_id,
        profile=profile,
        hotel_name=payload.hotel_name,
        hotel_has_step_free=payload.hotel_has_step_free,
        hotel_has_elevator=payload.hotel_has_elevator,
        hotel_has_roll_in_shower=payload.hotel_has_roll_in_shower,
    )

    return {
        "trip_id": res.trip_id,
        "traveler_name": res.traveler_name,
        "airline_ssr_directives": [
            {
                "ssr_code": d.ssr_code,
                "description": d.description,
                "gds_syntax": d.gds_command_syntax,
            }
            for d in res.airline_ssr_directives
        ],
        "hotel_accessibility": {
            "hotel_name": res.hotel_accessibility_audit.hotel_name,
            "is_compliant": res.hotel_accessibility_audit.is_compliant,
            "nearest_hospital": res.hotel_accessibility_audit.nearest_hospital_name,
            "distance_km": res.hotel_accessibility_audit.nearest_hospital_distance_km,
            "driving_time_mins": res.hotel_accessibility_audit.nearest_hospital_driving_time_mins,
            "audit_notes": res.hotel_accessibility_audit.audit_notes,
        } if res.hotel_accessibility_audit else None,
        "medical_briefing_notes": res.medical_briefing_notes,
    }


class RouteGeometryRequest(BaseModel):
    trip_id: Optional[str] = None
    stops: List[dict]
    unit: str = "km"
    fix_start: bool = True
    fix_end: bool = True


class OpenJawRequest(BaseModel):
    trip_id: Optional[str] = None
    legs: List[dict]


@router.post("/route-geometry/evaluate")
def evaluate_route_geometry_endpoint(payload: RouteGeometryRequest):
    """Evaluate itinerary stops for zigzagging backtracking and compute 2-opt path optimization."""
    has_backtracking, excess_dist, suggested_order = detect_backtracking(
        payload.stops,
    )

    current_dist = GeodesicPathOptimizer.calculate_total_distance(payload.stops, unit=payload.unit)
    opt_route = GeodesicPathOptimizer.optimize_waypoint_order(
        payload.stops,
        fix_start=payload.fix_start,
        unit=payload.unit,
    )
    opt_dist = GeodesicPathOptimizer.calculate_total_distance(opt_route, unit=payload.unit)

    savings_dist = max(0.0, current_dist - opt_dist)
    savings_pct = round((savings_dist / current_dist * 100.0), 1) if current_dist > 0 else 0.0

    return {
        "has_backtracking": has_backtracking,
        "excess_distance": excess_dist,
        "current_distance": round(current_dist, 2),
        "optimized_distance": round(opt_dist, 2),
        "distance_savings": round(savings_dist, 2),
        "savings_percent": savings_pct,
        "suggested_order": suggested_order,
        "optimized_stops": opt_route,
        "unit": payload.unit,
    }


@router.post("/route-geometry/open-jaw")
def evaluate_open_jaw_endpoint(payload: OpenJawRequest):
    """Identify open-jaw flight gaps and automatically inject required surface segments (//)."""
    enriched_legs = detect_open_jaw_surface_segments(payload.legs)
    surface_segments = [leg for leg in enriched_legs if leg.get("segment_type") == "SURFACE"]
    total_surface_dist = sum(float(seg.get("estimated_surface_distance_km") or 0.0) for seg in surface_segments)

    return {
        "has_open_jaw": len(surface_segments) > 0,
        "open_jaw_segments_count": len(surface_segments),
        "total_surface_distance_km": round(total_surface_dist, 2),
        "legs": enriched_legs,
    }


class GroundTransitRequest(BaseModel):
    origin_lat: float
    origin_lon: float
    dest_lat: float
    dest_lon: float


@router.post("/ground-transit")
def evaluate_ground_transit_endpoint(payload: GroundTransitRequest):
    """Compute driving distance, driving duration, and high-speed rail estimates via OSRM."""
    from src.agents.live_tools import build_ground_routing_tool_from_env
    tool = build_ground_routing_tool_from_env()
    res = tool.calculate_route(
        origin_lat=payload.origin_lat,
        origin_lon=payload.origin_lon,
        dest_lat=payload.dest_lat,
        dest_lon=payload.dest_lon,
    )
    return {
        "status": res.data.get("status", "success"),
        "direct_distance_km": res.data.get("direct_distance_km"),
        "road_distance_km": res.data.get("road_distance_km"),
        "driving_duration_minutes": res.data.get("driving_duration_minutes"),
        "high_speed_rail_duration_minutes": res.data.get("high_speed_rail_duration_minutes"),
        "mode": res.data.get("mode", "mock"),
    }
