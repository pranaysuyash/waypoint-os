"""
Private Aviation & Charter Models (PER-AV-CHARTER).

Defines typed schemas for aircraft categories, runway feasibility,
empty-leg ferry flight arbitrage, FBO handling, and eAPIS customs filings.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class JetCategory(str, Enum):
    VERY_LIGHT_JET = "very_light_jet"      # Phenom 100, 4 pax, ~1,100 nm
    LIGHT_JET = "light_jet"                # Citation CJ3, 6-7 pax, ~1,800 nm
    MIDSIZE_JET = "midsize_jet"            # Hawker 800XP, 8 pax, ~2,600 nm
    SUPER_MIDSIZE = "super_midsize"        # Challenger 350, 9-10 pax, ~3,200 nm
    HEAVY_JET = "heavy_jet"                # Falcon 900LX, 12-14 pax, ~4,500 nm
    ULTRA_LONG_RANGE = "ultra_long_range"  # Gulfstream G650 / Global 7500, 14-16 pax, ~7,500 nm


@dataclass(slots=True)
class AircraftSpecification:
    """Performance parameters of specific aircraft airframe."""
    model_name: str
    category: JetCategory
    max_passengers: int
    max_range_nm: int
    min_runway_length_ft: int
    hourly_charter_rate_usd: float
    fuel_burn_gph: float
    baggage_capacity_cuft: int


@dataclass(slots=True)
class EmptyLegOffer:
    """Repositioning ferry leg available at discount."""
    offer_id: str
    aircraft_model: str
    category: JetCategory
    origin_icao: str
    destination_icao: str
    departure_window_start: str
    departure_window_end: str
    standard_charter_price_usd: float
    empty_leg_discounted_price_usd: float
    discount_percent: float
    operator_name: str
    fbo_origin: str
    fbo_destination: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "offer_id": self.offer_id,
            "aircraft_model": self.aircraft_model,
            "category": self.category.value,
            "origin_icao": self.origin_icao,
            "destination_icao": self.destination_icao,
            "departure_window_start": self.departure_window_start,
            "departure_window_end": self.departure_window_end,
            "standard_charter_price_usd": self.standard_charter_price_usd,
            "empty_leg_discounted_price_usd": self.empty_leg_discounted_price_usd,
            "discount_percent": self.discount_percent,
            "operator_name": self.operator_name,
            "fbo_origin": self.fbo_origin,
            "fbo_destination": self.fbo_destination,
        }


@dataclass(slots=True)
class CharterQuotePackage:
    """Complete private aviation quote and operational feasibility."""
    quote_id: str
    origin_icao: str
    destination_icao: str
    distance_nm: int
    passengers_count: int
    recommended_aircraft: AircraftSpecification
    flight_time_hours: float
    standard_cost_usd: float
    empty_leg_match: Optional[EmptyLegOffer] = None
    runway_origin_feasible: bool = True
    runway_dest_feasible: bool = True
    origin_runway_length_ft: int = 0
    dest_runway_length_ft: int = 0
    origin_effective_runway_required_ft: int = 0
    dest_effective_runway_required_ft: int = 0
    performance_warnings: List[str] = field(default_factory=list)
    payload_reduction_percent: float = 0.0
    is_hot_and_high_restricted: bool = False
    fbo_origin: str = "Signature Flight Support"
    fbo_destination: str = "Jet Aviation"
    eapis_manifest_status: str = "PRE_APPROVED"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def effective_cost_usd(self) -> float:
        if self.empty_leg_match:
            return self.empty_leg_match.empty_leg_discounted_price_usd
        return self.standard_cost_usd

    @property
    def savings_usd(self) -> float:
        if self.empty_leg_match:
            return round(self.standard_cost_usd - self.empty_leg_match.empty_leg_discounted_price_usd, 2)
        return 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "quote_id": self.quote_id,
            "origin_icao": self.origin_icao,
            "destination_icao": self.destination_icao,
            "distance_nm": self.distance_nm,
            "passengers_count": self.passengers_count,
            "aircraft": {
                "model_name": self.recommended_aircraft.model_name,
                "category": self.recommended_aircraft.category.value,
                "max_passengers": self.recommended_aircraft.max_passengers,
                "hourly_rate_usd": self.recommended_aircraft.hourly_charter_rate_usd,
            },
            "flight_time_hours": self.flight_time_hours,
            "standard_cost_usd": self.standard_cost_usd,
            "empty_leg_match": self.empty_leg_match.to_dict() if self.empty_leg_match else None,
            "effective_cost_usd": self.empty_leg_match.empty_leg_discounted_price_usd if self.empty_leg_match else self.standard_cost_usd,
            "savings_usd": (self.standard_cost_usd - self.empty_leg_match.empty_leg_discounted_price_usd) if self.empty_leg_match else 0.0,
            "runway_feasibility": {
                "origin_pass": self.runway_origin_feasible,
                "destination_pass": self.runway_dest_feasible,
                "origin_runway_length_ft": self.origin_runway_length_ft,
                "dest_runway_length_ft": self.dest_runway_length_ft,
                "origin_effective_required_ft": self.origin_effective_runway_required_ft,
                "dest_effective_required_ft": self.dest_effective_runway_required_ft,
                "is_hot_and_high_restricted": self.is_hot_and_high_restricted,
                "payload_reduction_percent": self.payload_reduction_percent,
                "performance_warnings": self.performance_warnings,
            },
            "fbo_handling": {
                "origin": self.fbo_origin,
                "destination": self.fbo_destination,
            },
            "eapis_customs_status": self.eapis_manifest_status,
            "created_at": self.created_at,
        }
