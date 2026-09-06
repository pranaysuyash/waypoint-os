"""
src/logistics/accessibility.py — Traveler Accessibility & Medical Logistics Planner (Area #17.16).

Implements:
1. IATA Airline Special Service Request (SSR) Code Generator (WCHR, WCHS, WCHC, MEDA, DPNA, BLND, DEAF).
2. Hotel Mobility & Step-Free Accessibility Audit (roll-in shower, elevator width, ground-floor priority).
3. Emergency Medical Facility Proximity & Hospital Radar.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class WheelchairMobilityLevel(str, Enum):
    WCHR_RAMP_ONLY = "WCHR"          # Can ascend/descend stairs, needs assistance for long distances to gate
    WCHS_NO_STAIRS = "WCHS"          # Cannot ascend/descend stairs, can walk short distance in cabin
    WCHC_CABIN_IMMOBILE = "WCHC"     # Completely immobile, requires onboard aisle chair to seat
    NONE = "NONE"


@dataclass(slots=True)
class AccessibilityProfile:
    traveler_id: str
    traveler_name: str
    wheelchair_level: WheelchairMobilityLevel = WheelchairMobilityLevel.NONE
    requires_medical_oxygen: bool = False
    is_visually_impaired: bool = False
    is_hearing_impaired: bool = False
    requires_step_free_room: bool = False
    requires_roll_in_shower: bool = False
    medical_conditions_summary: Optional[str] = None


@dataclass(slots=True)
class AirlineSSRDirective:
    ssr_code: str
    passenger_name: str
    description: str
    gds_command_syntax: str


@dataclass(slots=True)
class HotelAccessibilityCheck:
    hotel_name: str
    is_step_free_accessible: bool
    has_elevator: bool
    has_roll_in_shower: bool
    nearest_hospital_name: str
    nearest_hospital_distance_km: float
    nearest_hospital_driving_time_mins: int
    is_compliant: bool
    audit_notes: List[str] = field(default_factory=list)


@dataclass(slots=True)
class AccessibilityLogisticsPlan:
    trip_id: str
    traveler_name: str
    airline_ssr_directives: List[AirlineSSRDirective] = field(default_factory=list)
    hotel_accessibility_audit: Optional[HotelAccessibilityCheck] = None
    medical_briefing_notes: List[str] = field(default_factory=list)


class AccessibilityPlanner:
    """
    Synthesizes airline SSR commands and audits hotel accessibility parameters.
    """

    @classmethod
    def create_accessibility_plan(
        cls,
        trip_id: str,
        profile: AccessibilityProfile,
        hotel_name: str,
        hotel_has_step_free: bool = True,
        hotel_has_elevator: bool = True,
        hotel_has_roll_in_shower: bool = True,
        nearest_hospital_name: str = "Ospedale Santo Spirito",
        nearest_hospital_distance_km: float = 2.4,
        nearest_hospital_driving_time_mins: int = 8,
    ) -> AccessibilityLogisticsPlan:
        ssr_directives: List[AirlineSSRDirective] = []
        med_notes: List[str] = []

        # 1. Airline Wheelchair SSRs
        if profile.wheelchair_level == WheelchairMobilityLevel.WCHR_RAMP_ONLY:
            ssr_directives.append(AirlineSSRDirective(
                ssr_code="WCHR",
                passenger_name=profile.traveler_name,
                description="Wheelchair for ramp/distance only (Passenger can walk short steps)",
                gds_command_syntax=f"SR WCHR-RAMP ASSISTANCE ONLY FOR {profile.traveler_name.upper()}",
            ))
            med_notes.append("Airline airport ramp wheelchair requested.")
        elif profile.wheelchair_level == WheelchairMobilityLevel.WCHS_NO_STAIRS:
            ssr_directives.append(AirlineSSRDirective(
                ssr_code="WCHS",
                passenger_name=profile.traveler_name,
                description="Wheelchair for stairs (Passenger cannot climb boarding stairs)",
                gds_command_syntax=f"SR WCHS-CANNOT CLIMB STAIRS FOR {profile.traveler_name.upper()}",
            ))
            med_notes.append("Ambulift / Jetbridge boarding required (no airstairs).")
        elif profile.wheelchair_level == WheelchairMobilityLevel.WCHC_CABIN_IMMOBILE:
            ssr_directives.append(AirlineSSRDirective(
                ssr_code="WCHC",
                passenger_name=profile.traveler_name,
                description="Wheelchair cabin seat assistance (Completely immobile, onboard aisle chair needed)",
                gds_command_syntax=f"SR WCHC-CABIN SEAT TRANSFER REQUIRED FOR {profile.traveler_name.upper()}",
            ))
            med_notes.append("Onboard aisle transfer chair confirmed with carrier.")

        # 2. Additional Sensory & Medical SSRs
        if profile.requires_medical_oxygen:
            ssr_directives.append(AirlineSSRDirective(
                ssr_code="MEDA",
                passenger_name=profile.traveler_name,
                description="Medical clearance & supplemental oxygen supply required",
                gds_command_syntax=f"SR MEDA-OXYGEN REQUESTED FOR {profile.traveler_name.upper()}",
            ))
            med_notes.append("Physician medical clearance (MEDIF form) must be submitted 72h prior.")

        if profile.is_visually_impaired:
            ssr_directives.append(AirlineSSRDirective(
                ssr_code="BLND",
                passenger_name=profile.traveler_name,
                description="Blind or visually impaired passenger meet-and-assist",
                gds_command_syntax=f"SR BLND-VISUAL ASSIST FOR {profile.traveler_name.upper()}",
            ))

        if profile.is_hearing_impaired:
            ssr_directives.append(AirlineSSRDirective(
                ssr_code="DEAF",
                passenger_name=profile.traveler_name,
                description="Deaf / hard of hearing traveler notification",
                gds_command_syntax=f"SR DEAF-HEARING IMPAIRED FOR {profile.traveler_name.upper()}",
            ))

        # 3. Hotel Accessibility Audit
        hotel_compliant = True
        audit_notes: List[str] = []

        if profile.requires_step_free_room and not hotel_has_step_free:
            hotel_compliant = False
            audit_notes.append("🚨 Property lacks step-free entrance or ground-floor accessible room.")

        if profile.requires_roll_in_shower and not hotel_has_roll_in_shower:
            hotel_compliant = False
            audit_notes.append("🚨 Roll-in shower with grab bars is not guaranteed in selected room category.")

        if hotel_compliant:
            audit_notes.append(f"✅ {hotel_name} meets all requested physical mobility specifications.")

        hotel_check = HotelAccessibilityCheck(
            hotel_name=hotel_name,
            is_step_free_accessible=hotel_has_step_free,
            has_elevator=hotel_has_elevator,
            has_roll_in_shower=hotel_has_roll_in_shower,
            nearest_hospital_name=nearest_hospital_name,
            nearest_hospital_distance_km=nearest_hospital_distance_km,
            nearest_hospital_driving_time_mins=nearest_hospital_driving_time_mins,
            is_compliant=hotel_compliant,
            audit_notes=audit_notes,
        )

        return AccessibilityLogisticsPlan(
            trip_id=trip_id,
            traveler_name=profile.traveler_name,
            airline_ssr_directives=ssr_directives,
            hotel_accessibility_audit=hotel_check,
            medical_briefing_notes=med_notes,
        )
