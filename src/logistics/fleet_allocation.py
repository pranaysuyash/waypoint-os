"""
src/logistics/fleet_allocation.py — Transfer Fleet & Vehicle Allocation Engine (Area #17.12).

Implements:
1. Vehicle Classification (SEDAN, SUV_INNOVA, EXECUTIVE_VAN_TEMPO, MINI_COACH, FULL_COACH).
2. Passenger & Luggage Capacity Physics (standard suitcases, carry-ons, oversized gear).
3. Child Safety Seat footprint calculations (infant/toddler seats reduce available passenger slots).
4. Multi-vehicle split recommendations for large groups or heavy baggage profiles.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class VehicleCategory(str, Enum):
    SEDAN = "SEDAN"                          # Mercedes E-Class / Camry / Dzire
    SUV_INNOVA = "SUV_INNOVA"                # Toyota Innova Crysta / Suburban / Land Cruiser
    EXECUTIVE_VAN_TEMPO = "EXECUTIVE_VAN_TEMPO"  # Mercedes Sprinter / Force Tempo Traveller
    MINI_COACH = "MINI_COACH"                # 22-Seater Isuzu / Rosa
    FULL_COACH = "FULL_COACH"                # 45-50 Seater Volvo / Scania / Setra


@dataclass(slots=True)
class VehicleSpec:
    category: VehicleCategory
    display_name: str
    max_passengers: int
    max_standard_bags: int
    base_rate_usd: float
    per_km_rate_usd: float
    description: str


VEHICLE_CATALOG: Dict[VehicleCategory, VehicleSpec] = {
    VehicleCategory.SEDAN: VehicleSpec(
        category=VehicleCategory.SEDAN,
        display_name="Executive Sedan (Mercedes E-Class / Camry)",
        max_passengers=3,
        max_standard_bags=2,
        base_rate_usd=85.0,
        per_km_rate_usd=1.80,
        description="Comfortable transfer for 1-3 passengers with standard luggage.",
    ),
    VehicleCategory.SUV_INNOVA: VehicleSpec(
        category=VehicleCategory.SUV_INNOVA,
        display_name="Premium MPV / SUV (Toyota Innova Crysta / Escalade)",
        max_passengers=5,
        max_standard_bags=4,
        base_rate_usd=135.0,
        per_km_rate_usd=2.40,
        description="Spacious MPV/SUV ideal for families, small groups, and extra bags.",
    ),
    VehicleCategory.EXECUTIVE_VAN_TEMPO: VehicleSpec(
        category=VehicleCategory.EXECUTIVE_VAN_TEMPO,
        display_name="Executive Van / Tempo (Mercedes Sprinter / 12-Seater)",
        max_passengers=10,
        max_standard_bags=10,
        base_rate_usd=240.0,
        per_km_rate_usd=3.20,
        description="High-roof executive van with dedicated luggage compartment.",
    ),
    VehicleCategory.MINI_COACH: VehicleSpec(
        category=VehicleCategory.MINI_COACH,
        display_name="Luxury Mini-Coach (22-Seater)",
        max_passengers=20,
        max_standard_bags=20,
        base_rate_usd=380.0,
        per_km_rate_usd=4.50,
        description="Group touring coach with reclining seats and PA system.",
    ),
    VehicleCategory.FULL_COACH: VehicleSpec(
        category=VehicleCategory.FULL_COACH,
        display_name="Large Touring Coach (45-50 Seater)",
        max_passengers=45,
        max_standard_bags=50,
        base_rate_usd=650.0,
        per_km_rate_usd=6.50,
        description="Full-sized luxury motorcoach with underfloor baggage bays.",
    ),
}


@dataclass(slots=True)
class AllocatedVehicle:
    vehicle_category: VehicleCategory
    display_name: str
    quantity: int
    total_passenger_capacity: int
    total_luggage_capacity: int
    estimated_base_cost_usd: float
    notes: str


@dataclass(slots=True)
class FleetAllocationResult:
    trip_id: str
    passenger_count: int
    total_luggage_count: int
    oversized_bags_count: int
    child_seats_count: int
    recommended_vehicles: List[AllocatedVehicle] = field(default_factory=list)
    total_estimated_cost_usd: float = 0.0
    is_split_transfer: bool = False
    overflow_warning: Optional[str] = None


class FleetAllocationEngine:
    """
    Evaluates passenger and luggage requirements to recommend optimal transfer vehicle allocations.
    """

    @classmethod
    def calculate_allocation(
        cls,
        trip_id: str,
        passenger_count: int,
        standard_luggage_count: int,
        child_seats_count: int = 0,
        oversized_bags_count: int = 0,  # Golf kits, surfboards, skis count as 2 standard bags
    ) -> FleetAllocationResult:
        if passenger_count <= 0:
            raise ValueError("Passenger count must be at least 1")

        # Child seats consume 1 additional physical seat space on small vehicles
        effective_pax = passenger_count + (1 if child_seats_count > 1 else 0)
        effective_bags = standard_luggage_count + (oversized_bags_count * 2)

        recommended: List[AllocatedVehicle] = []
        is_split = False
        warning = None

        # Check single vehicle tiers
        if effective_pax <= 3 and effective_bags <= 2:
            spec = VEHICLE_CATALOG[VehicleCategory.SEDAN]
            recommended.append(AllocatedVehicle(
                vehicle_category=spec.category,
                display_name=spec.display_name,
                quantity=1,
                total_passenger_capacity=spec.max_passengers,
                total_luggage_capacity=spec.max_standard_bags,
                estimated_base_cost_usd=spec.base_rate_usd,
                notes="Single executive sedan fits all passengers and luggage comfortably.",
            ))
        elif effective_pax <= 5 and effective_bags <= 4:
            spec = VEHICLE_CATALOG[VehicleCategory.SUV_INNOVA]
            recommended.append(AllocatedVehicle(
                vehicle_category=spec.category,
                display_name=spec.display_name,
                quantity=1,
                total_passenger_capacity=spec.max_passengers,
                total_luggage_capacity=spec.max_standard_bags,
                estimated_base_cost_usd=spec.base_rate_usd,
                notes="Premium MPV/SUV accommodates party and baggage with rear seat folded.",
            ))
        elif effective_pax <= 10 and effective_bags <= 10:
            spec = VEHICLE_CATALOG[VehicleCategory.EXECUTIVE_VAN_TEMPO]
            recommended.append(AllocatedVehicle(
                vehicle_category=spec.category,
                display_name=spec.display_name,
                quantity=1,
                total_passenger_capacity=spec.max_passengers,
                total_luggage_capacity=spec.max_standard_bags,
                estimated_base_cost_usd=spec.base_rate_usd,
                notes="Executive van/tempo offers dedicated luggage boot and high-roof clearance.",
            ))
        elif effective_pax <= 20 and effective_bags <= 20:
            spec = VEHICLE_CATALOG[VehicleCategory.MINI_COACH]
            recommended.append(AllocatedVehicle(
                vehicle_category=spec.category,
                display_name=spec.display_name,
                quantity=1,
                total_passenger_capacity=spec.max_passengers,
                total_luggage_capacity=spec.max_standard_bags,
                estimated_base_cost_usd=spec.base_rate_usd,
                notes="Luxury 22-seater mini-coach accommodates entire touring group.",
            ))
        elif effective_pax <= 45 and effective_bags <= 50:
            spec = VEHICLE_CATALOG[VehicleCategory.FULL_COACH]
            recommended.append(AllocatedVehicle(
                vehicle_category=spec.category,
                display_name=spec.display_name,
                quantity=1,
                total_passenger_capacity=spec.max_passengers,
                total_luggage_capacity=spec.max_standard_bags,
                estimated_base_cost_usd=spec.base_rate_usd,
                notes="Full touring coach with large undercarriage baggage bays.",
            ))
        else:
            # Multi-vehicle split calculation (e.g. 2 x Full Coach or 2 x Executive Van)
            coaches_needed = (effective_pax + 44) // 45
            spec = VEHICLE_CATALOG[VehicleCategory.FULL_COACH]
            recommended.append(AllocatedVehicle(
                vehicle_category=spec.category,
                display_name=spec.display_name,
                quantity=coaches_needed,
                total_passenger_capacity=spec.max_passengers * coaches_needed,
                total_luggage_capacity=spec.max_standard_bags * coaches_needed,
                estimated_base_cost_usd=spec.base_rate_usd * coaches_needed,
                notes=f"Group size requires convoy of {coaches_needed} full touring coaches.",
            ))
            is_split = True

        # Check special luggage-heavy case for small party (e.g. 3 pax but 6 large bags + golf kits)
        if len(recommended) == 1 and recommended[0].vehicle_category == VehicleCategory.SEDAN and effective_bags > 2:
            spec_suv = VEHICLE_CATALOG[VehicleCategory.SUV_INNOVA]
            recommended = [AllocatedVehicle(
                vehicle_category=spec_suv.category,
                display_name=spec_suv.display_name,
                quantity=1,
                total_passenger_capacity=spec_suv.max_passengers,
                total_luggage_capacity=spec_suv.max_standard_bags,
                estimated_base_cost_usd=spec_suv.base_rate_usd,
                notes=f"Upgraded from Sedan to SUV/MPV due to {effective_bags} total luggage volume.",
            )]
            warning = f"Vehicle upgraded to {spec_suv.display_name} to safely accommodate {effective_bags} luggage units."

        total_cost = sum(v.estimated_base_cost_usd for v in recommended)

        return FleetAllocationResult(
            trip_id=trip_id,
            passenger_count=passenger_count,
            total_luggage_count=standard_luggage_count,
            oversized_bags_count=oversized_bags_count,
            child_seats_count=child_seats_count,
            recommended_vehicles=recommended,
            total_estimated_cost_usd=total_cost,
            is_split_transfer=is_split,
            overflow_warning=warning,
        )
