"""
Private Aviation & Empty-Leg Arbitrage Engine (PER-AV-CHARTER).

Solves private jet fleet selection, runway distance feasibility,
hot-and-high mountain airstrip performance penalties, empty-leg repositioning matching,
and FBO / eAPIS customs filings.
"""

from __future__ import annotations

import math
import uuid
from dataclasses import dataclass
from typing import Dict, List, Optional

from src.charter.models import (
    AircraftSpecification,
    CharterQuotePackage,
    EmptyLegOffer,
    JetCategory,
)


@dataclass(slots=True)
class AirportPerformanceSpec:
    """Airport runway performance characteristics and elevation profile."""
    icao_code: str
    name: str
    runway_length_ft: int
    elevation_ft: int = 0
    is_mountain_altiport: bool = False
    density_altitude_penalty_factor: float = 0.10  # ~10% runway penalty per 1,000 ft elevation
    max_payload_reduction_percent: float = 0.0
    special_departure_procedure: str = ""


# Detailed Airport Runway & Performance Database
AIRPORT_PERFORMANCE_DATABASE: Dict[str, AirportPerformanceSpec] = {
    "KTEB": AirportPerformanceSpec("KTEB", "Teterboro Airport (NYC)", 7000, 9),
    "KHPN": AirportPerformanceSpec("KHPN", "Westchester County Airport (NYC)", 6549, 439),
    "KVNY": AirportPerformanceSpec("KVNY", "Van Nuys Airport (LA)", 8001, 802),
    "KOPF": AirportPerformanceSpec("KOPF", "Miami Opa-Locka Executive", 8002, 9),
    "KASE": AirportPerformanceSpec(
        icao_code="KASE",
        name="Aspen Pitkin County Airport",
        runway_length_ft=8006,
        elevation_ft=7820,
        is_mountain_altiport=True,
        density_altitude_penalty_factor=0.10,
        max_payload_reduction_percent=25.0,
        special_departure_procedure="High altitude hot-and-high mountain airstrip (7,820 ft MSL). Severe climb gradient and MTOW payload limitations.",
    ),
    "LSZS": AirportPerformanceSpec(
        icao_code="LSZS",
        name="Samedan Engadin Airport (St. Moritz)",
        runway_length_ft=5905,
        elevation_ft=5600,
        is_mountain_altiport=True,
        density_altitude_penalty_factor=0.10,
        max_payload_reduction_percent=20.0,
        special_departure_procedure="Europe's highest commercial jet airport (5,600 ft MSL). Alpine valley terrain with strict single-engine climb requirements.",
    ),
    "KTEX": AirportPerformanceSpec(
        icao_code="KTEX",
        name="Telluride Regional Airport",
        runway_length_ft=7111,
        elevation_ft=9078,
        is_mountain_altiport=True,
        density_altitude_penalty_factor=0.10,
        max_payload_reduction_percent=30.0,
        special_departure_procedure="Highest commercial airport in North America (9,078 ft MSL). Cliffside plateau with severe density altitude penalties.",
    ),
    "KEGE": AirportPerformanceSpec(
        icao_code="KEGE",
        name="Eagle County Regional Airport (Vail)",
        runway_length_ft=9000,
        elevation_ft=6548,
        is_mountain_altiport=True,
        density_altitude_penalty_factor=0.10,
        max_payload_reduction_percent=15.0,
        special_departure_procedure="Hot-and-high mountain valley operations.",
    ),
    "LOWI": AirportPerformanceSpec(
        icao_code="LOWI",
        name="Innsbruck Airport",
        runway_length_ft=6562,
        elevation_ft=1906,
        is_mountain_altiport=True,
        density_altitude_penalty_factor=0.08,
        max_payload_reduction_percent=10.0,
        special_departure_procedure="Steep valley approach (Inn Valley) with strict climb performance requirements.",
    ),
    "LFLJ": AirportPerformanceSpec(
        icao_code="LFLJ",
        name="Courchevel Altiport",
        runway_length_ft=1762,
        elevation_ft=6588,
        is_mountain_altiport=True,
        density_altitude_penalty_factor=0.12,
        max_payload_reduction_percent=50.0,
        special_departure_procedure="Mountain altiport with 18.6% upward sloped runway; turboprops and mountain-rated crew only.",
    ),
    "KTRK": AirportPerformanceSpec(
        icao_code="KTRK",
        name="Truckee Tahoe Airport",
        runway_length_ft=7000,
        elevation_ft=5900,
        is_mountain_altiport=True,
        density_altitude_penalty_factor=0.10,
        max_payload_reduction_percent=15.0,
        special_departure_procedure="Sierra Nevada high-elevation airfield.",
    ),
    "EGLF": AirportPerformanceSpec("EGLF", "TAG Farnborough Airport (London)", 8000, 238),
    "LFPB": AirportPerformanceSpec("LFPB", "Paris Le Bourget", 9842, 218),
    "LSGG": AirportPerformanceSpec("LSGG", "Geneva Airport", 12795, 1411),
    "OMDW": AirportPerformanceSpec("OMDW", "Dubai Al Maktoum", 14764, 171),
    "KJFK": AirportPerformanceSpec("KJFK", "New York JFK", 14511, 13),
    "EGLL": AirportPerformanceSpec("EGLL", "London Heathrow", 12799, 83),
}

# Reference airport runway lengths in feet (kept populated for backward compatibility)
AIRPORT_RUNWAY_DATABASE: Dict[str, int] = {
    k: spec.runway_length_ft for k, spec in AIRPORT_PERFORMANCE_DATABASE.items()
}

FLEET_CATALOG: Dict[str, AircraftSpecification] = {
    "Phenom 300E": AircraftSpecification(
        model_name="Phenom 300E",
        category=JetCategory.LIGHT_JET,
        max_passengers=7,
        max_range_nm=2010,
        min_runway_length_ft=3209,
        hourly_charter_rate_usd=3850.0,
        fuel_burn_gph=160.0,
        baggage_capacity_cuft=84,
    ),
    "Citation Latitude": AircraftSpecification(
        model_name="Citation Latitude",
        category=JetCategory.MIDSIZE_JET,
        max_passengers=8,
        max_range_nm=2700,
        min_runway_length_ft=3580,
        hourly_charter_rate_usd=5200.0,
        fuel_burn_gph=210.0,
        baggage_capacity_cuft=127,
    ),
    "Challenger 3500": AircraftSpecification(
        model_name="Challenger 3500",
        category=JetCategory.SUPER_MIDSIZE,
        max_passengers=10,
        max_range_nm=3400,
        min_runway_length_ft=4835,
        hourly_charter_rate_usd=6950.0,
        fuel_burn_gph=260.0,
        baggage_capacity_cuft=106,
    ),
    "Gulfstream G650ER": AircraftSpecification(
        model_name="Gulfstream G650ER",
        category=JetCategory.ULTRA_LONG_RANGE,
        max_passengers=16,
        max_range_nm=7500,
        min_runway_length_ft=5858,
        hourly_charter_rate_usd=11500.0,
        fuel_burn_gph=450.0,
        baggage_capacity_cuft=195,
    ),
}

# Live Empty-Leg Inventory Sample
SAMPLE_EMPTY_LEGS: List[EmptyLegOffer] = [
    EmptyLegOffer(
        offer_id="EL-TEB-MIA-091",
        aircraft_model="Challenger 3500",
        category=JetCategory.SUPER_MIDSIZE,
        origin_icao="KTEB",
        destination_icao="KOPF",
        departure_window_start="2026-10-15T10:00:00Z",
        departure_window_end="2026-10-15T18:00:00Z",
        standard_charter_price_usd=22500.0,
        empty_leg_discounted_price_usd=7800.0,
        discount_percent=65.3,
        operator_name="NetJets Repositioning",
        fbo_origin="Signature Flight Support (Teterboro)",
        fbo_destination="Fontainebleau Aviation (Miami Opa-Locka)",
    ),
    EmptyLegOffer(
        offer_id="EL-FAB-LBG-044",
        aircraft_model="Phenom 300E",
        category=JetCategory.LIGHT_JET,
        origin_icao="EGLF",
        destination_icao="LFPB",
        departure_window_start="2026-10-16T12:00:00Z",
        departure_window_end="2026-10-16T20:00:00Z",
        standard_charter_price_usd=9500.0,
        empty_leg_discounted_price_usd=3200.0,
        discount_percent=66.3,
        operator_name="Air Charter Service UK",
        fbo_origin="TAG Farnborough Airport",
        fbo_destination="Jet Aviation Le Bourget",
    ),
]


class PrivateAviationEngine:
    """Calculates private charter solutions, runway feasibility, and empty-leg savings."""

    @classmethod
    def calculate_effective_runway_required(
        cls,
        aircraft: AircraftSpecification,
        airport_spec: AirportPerformanceSpec,
        ambient_temp_c: float = 25.0,
    ) -> int:
        """
        Calculates effective takeoff/landing runway length required after accounting
        for airfield elevation (density altitude) and hot ambient temperatures.
        """
        base_ft = aircraft.min_runway_length_ft
        if airport_spec.elevation_ft <= 1000:
            return base_ft

        # 1. Density Altitude Elevation Correction (+10% per 1,000 ft elevation)
        elevation_penalty = (airport_spec.elevation_ft / 1000.0) * airport_spec.density_altitude_penalty_factor

        # 2. Temperature delta above standard ISA (ISA at elevation = 15°C - 2°C per 1,000 ft)
        isa_temp = max(-10.0, 15.0 - (2.0 * airport_spec.elevation_ft / 1000.0))
        temp_delta = max(0.0, ambient_temp_c - isa_temp)
        temp_penalty = temp_delta * 0.01  # ~1% per °C above ISA

        total_multiplier = 1.0 + elevation_penalty + temp_penalty
        return int(math.ceil(base_ft * total_multiplier))

    @classmethod
    def calculate_charter_quote(
        cls,
        origin_icao: str,
        destination_icao: str,
        passengers_count: int = 4,
        distance_nm: Optional[int] = None,
        ambient_temp_c: float = 25.0,
    ) -> CharterQuotePackage:
        orig = origin_icao.upper()
        dest = destination_icao.upper()
        dist = distance_nm or 1100  # Default ~2.5 hour leg if not specified

        # 1. Select optimal aircraft based on passenger load and mission range
        if passengers_count > 10 or dist > 3200:
            aircraft = FLEET_CATALOG["Gulfstream G650ER"]
            cruise_speed_kts = 500
        elif passengers_count > 7 or dist > 2000:
            aircraft = FLEET_CATALOG["Challenger 3500"]
            cruise_speed_kts = 460
        elif passengers_count > 6 or dist > 1500:
            aircraft = FLEET_CATALOG["Citation Latitude"]
            cruise_speed_kts = 430
        else:
            aircraft = FLEET_CATALOG["Phenom 300E"]
            cruise_speed_kts = 420

        # Flight duration with taxi and climb/descent padding (0.4 hours)
        flight_hours = round((dist / cruise_speed_kts) + 0.4, 1)
        standard_cost = round(flight_hours * aircraft.hourly_charter_rate_usd, 2)

        # 2. Look up airport performance profiles
        default_spec = AirportPerformanceSpec("DEFAULT", "Standard Regional Airport", 6000, 500)
        orig_spec = AIRPORT_PERFORMANCE_DATABASE.get(orig, default_spec)
        dest_spec = AIRPORT_PERFORMANCE_DATABASE.get(dest, default_spec)

        # 3. Calculate hot-and-high density altitude runway requirements
        orig_effective_runway = cls.calculate_effective_runway_required(aircraft, orig_spec, ambient_temp_c)
        dest_effective_runway = cls.calculate_effective_runway_required(aircraft, dest_spec, ambient_temp_c)

        runway_orig_pass = orig_spec.runway_length_ft >= orig_effective_runway
        runway_dest_pass = dest_spec.runway_length_ft >= dest_effective_runway

        # 4. Payload and operational warnings
        performance_warnings: List[str] = []
        max_payload_reduction = max(
            orig_spec.max_payload_reduction_percent,
            dest_spec.max_payload_reduction_percent,
        )
        is_hot_and_high = (
            orig_spec.is_mountain_altiport
            or dest_spec.is_mountain_altiport
            or orig_spec.elevation_ft >= 4000
            or dest_spec.elevation_ft >= 4000
        )

        for airport_spec, eff_req, is_pass, role in (
            (orig_spec, orig_effective_runway, runway_orig_pass, "Origin"),
            (dest_spec, dest_effective_runway, runway_dest_pass, "Destination"),
        ):
            if airport_spec.is_mountain_altiport or airport_spec.elevation_ft >= 3000:
                pct_increase = int(round((eff_req - aircraft.min_runway_length_ft) / aircraft.min_runway_length_ft * 100))
                performance_warnings.append(
                    f"⚠️ Hot-and-High / Mountain Airfield Penalty at {role} ({airport_spec.icao_code} - {airport_spec.name}, "
                    f"Elevation {airport_spec.elevation_ft} ft MSL): requires {eff_req} ft effective runway "
                    f"(+{pct_increase}% over sea-level baseline {aircraft.min_runway_length_ft} ft). "
                    f"Payload weight capacity reduced by {airport_spec.max_payload_reduction_percent}%."
                )
            if not is_pass:
                performance_warnings.append(
                    f"🚨 Infeasible Runway Length: {role} airport {airport_spec.icao_code} physical runway "
                    f"({airport_spec.runway_length_ft} ft) is insufficient for {aircraft.model_name} "
                    f"effective requirement ({eff_req} ft) under current density altitude."
                )

        # Check passenger limit under hot-and-high MTOW reduction
        if max_payload_reduction > 0.0:
            effective_max_pax = max(1, int(math.floor(aircraft.max_passengers * (1.0 - max_payload_reduction / 100.0))))
            if passengers_count > effective_max_pax:
                performance_warnings.append(
                    f"⚠️ High-Altitude Payload Limitation: {passengers_count} passengers exceeds derated capacity "
                    f"({effective_max_pax} max passengers) for {aircraft.model_name} due to {max_payload_reduction}% "
                    f"mountain takeoff/landing weight penalty."
                )

        # 5. Empty Leg Matching (Route match with complimentary upgrade if higher category)
        empty_match = None
        for el in SAMPLE_EMPTY_LEGS:
            if el.origin_icao == orig and el.destination_icao == dest:
                empty_match = el
                if el.aircraft_model in FLEET_CATALOG:
                    aircraft = FLEET_CATALOG[el.aircraft_model]
                break

        quote_id = f"CHT-{uuid.uuid4().hex[:6].upper()}"

        return CharterQuotePackage(
            quote_id=quote_id,
            origin_icao=orig,
            destination_icao=dest,
            distance_nm=dist,
            passengers_count=passengers_count,
            recommended_aircraft=aircraft,
            flight_time_hours=flight_hours,
            standard_cost_usd=standard_cost,
            empty_leg_match=empty_match,
            runway_origin_feasible=runway_orig_pass,
            runway_dest_feasible=runway_dest_pass,
            origin_runway_length_ft=orig_spec.runway_length_ft,
            dest_runway_length_ft=dest_spec.runway_length_ft,
            origin_effective_runway_required_ft=orig_effective_runway,
            dest_effective_runway_required_ft=dest_effective_runway,
            performance_warnings=performance_warnings,
            payload_reduction_percent=max_payload_reduction,
            is_hot_and_high_restricted=is_hot_and_high,
            fbo_origin=empty_match.fbo_origin if empty_match else f"Signature Flight Support ({orig})",
            fbo_destination=empty_match.fbo_destination if empty_match else f"Jet Aviation ({dest})",
            eapis_manifest_status="PRE_APPROVED",
        )

    @classmethod
    def list_available_empty_legs(cls) -> List[EmptyLegOffer]:
        """Returns all currently indexed empty-leg repositioning flights."""
        return SAMPLE_EMPTY_LEGS
