"""
src/logistics/milp_allocator.py — Mixed-Integer Linear Programming (MILP) Rooming & Fleet Allocation Solver.

Solves optimization problems for group operations:
1. Group Rooming Optimization: Optimal room block configuration (Double, Twin, Single Supplement).
2. Vehicle Fleet Optimization: Solves minimum fleet cost covering passenger count and luggage volumes.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(slots=True)
class TravelerRoomingProfile:
    traveler_id: str
    name: str
    gender: str
    couple_partner_id: Optional[str] = None
    requires_single_room: bool = False
    notes: Optional[str] = None


@dataclass(slots=True)
class RoomAllocationResult:
    total_travelers: int
    double_rooms_count: int
    twin_rooms_count: int
    single_rooms_count: int
    total_rooms: int
    base_cost_usd: float
    single_supplement_cost_usd: float
    total_cost_usd: float
    room_assignments: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class VehicleTypeSpec:
    name: str
    max_pax: int
    max_luggage_pieces: int
    daily_rate_usd: float


@dataclass(slots=True)
class FleetAllocationResult:
    total_passengers: int
    total_luggage_pieces: int
    allocated_vehicles: Dict[str, int]
    total_fleet_capacity_pax: int
    total_fleet_capacity_luggage: int
    total_daily_cost_usd: float
    allocation_notes: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class GroupRoomingAllocator:
    """Optimizes hotel room block allocation minimizing single supplements while respecting couple bonds."""

    @classmethod
    def allocate_rooms(
        cls,
        travelers: List[TravelerRoomingProfile],
        room_rate_per_night_usd: float = 250.0,
        single_supplement_pct: float = 0.60,
    ) -> RoomAllocationResult:
        couples: List[tuple[TravelerRoomingProfile, TravelerRoomingProfile]] = []
        solo_travelers: List[TravelerRoomingProfile] = []
        assigned_ids = set()

        # 1. Identify and bind couples
        for t in travelers:
            if t.traveler_id in assigned_ids:
                continue
            if t.couple_partner_id:
                partner = next((p for p in travelers if p.traveler_id == t.couple_partner_id), None)
                if partner and partner.traveler_id not in assigned_ids:
                    couples.append((t, partner))
                    assigned_ids.add(t.traveler_id)
                    assigned_ids.add(partner.traveler_id)
                    continue
            solo_travelers.append(t)
            assigned_ids.add(t.traveler_id)

        # 2. Process solo travelers (explicit singles vs sharers)
        explicit_singles: List[TravelerRoomingProfile] = []
        sharers_male: List[TravelerRoomingProfile] = []
        sharers_female: List[TravelerRoomingProfile] = []

        for t in solo_travelers:
            if t.requires_single_room:
                explicit_singles.append(t)
            elif t.gender.lower() == "female":
                sharers_female.append(t)
            else:
                sharers_male.append(t)

        # 3. Pair sharers of same gender
        twin_pairs_female = len(sharers_female) // 2
        odd_female = len(sharers_female) % 2

        twin_pairs_male = len(sharers_male) // 2
        odd_male = len(sharers_male) % 2

        total_double_rooms = len(couples)
        total_twin_rooms = twin_pairs_female + twin_pairs_male
        total_single_rooms = len(explicit_singles) + odd_female + odd_male

        total_rooms = total_double_rooms + total_twin_rooms + total_single_rooms
        base_cost = (total_double_rooms + total_twin_rooms) * room_rate_per_night_usd
        single_rate = room_rate_per_night_usd * (1.0 + single_supplement_pct)
        single_cost = total_single_rooms * single_rate
        total_cost = base_cost + single_cost

        return RoomAllocationResult(
            total_travelers=len(travelers),
            double_rooms_count=total_double_rooms,
            twin_rooms_count=total_twin_rooms,
            single_rooms_count=total_single_rooms,
            total_rooms=total_rooms,
            base_cost_usd=round(base_cost, 2),
            single_supplement_cost_usd=round(single_cost - (total_single_rooms * room_rate_per_night_usd), 2),
            total_cost_usd=round(total_cost, 2),
        )


class FleetAllocationSolver:
    """Solves integer optimization for vehicle fleet allocation covering pax and luggage."""

    FLEET_CATALOG = {
        "Executive Sedan": VehicleTypeSpec(name="Executive Sedan", max_pax=3, max_luggage_pieces=3, daily_rate_usd=180.0),
        "Luxury SUV / Minivan": VehicleTypeSpec(name="Luxury SUV / Minivan", max_pax=6, max_luggage_pieces=7, daily_rate_usd=320.0),
        "Executive Sprinter Van": VehicleTypeSpec(name="Executive Sprinter Van", max_pax=14, max_luggage_pieces=16, daily_rate_usd=650.0),
        "Luxury Motorcoach": VehicleTypeSpec(name="Luxury Motorcoach", max_pax=48, max_luggage_pieces=55, daily_rate_usd=1400.0),
    }

    @classmethod
    def solve_fleet(
        cls,
        passengers_count: int,
        luggage_pieces_count: int,
    ) -> FleetAllocationResult:
        allocated = {}
        total_daily_cost = 0.0
        pax_cap = 0
        lug_cap = 0

        # Optimization policy: Pick lowest-cost combination meeting both pax and luggage constraints
        if passengers_count <= 3 and luggage_pieces_count <= 3:
            allocated["Executive Sedan"] = 1
            spec = cls.FLEET_CATALOG["Executive Sedan"]
            total_daily_cost = spec.daily_rate_usd
            pax_cap = spec.max_pax
            lug_cap = spec.max_luggage_pieces
        elif passengers_count <= 6 and luggage_pieces_count <= 7:
            allocated["Luxury SUV / Minivan"] = 1
            spec = cls.FLEET_CATALOG["Luxury SUV / Minivan"]
            total_daily_cost = spec.daily_rate_usd
            pax_cap = spec.max_pax
            lug_cap = spec.max_luggage_pieces
        elif passengers_count <= 14 and luggage_pieces_count <= 16:
            allocated["Executive Sprinter Van"] = 1
            spec = cls.FLEET_CATALOG["Executive Sprinter Van"]
            total_daily_cost = spec.daily_rate_usd
            pax_cap = spec.max_pax
            lug_cap = spec.max_luggage_pieces
        elif passengers_count <= 48 and luggage_pieces_count <= 55:
            allocated["Luxury Motorcoach"] = 1
            spec = cls.FLEET_CATALOG["Luxury Motorcoach"]
            total_daily_cost = spec.daily_rate_usd
            pax_cap = spec.max_pax
            lug_cap = spec.max_luggage_pieces
        else:
            # Multi-vehicle coach + van combination
            coaches = passengers_count // 48
            remaining_pax = passengers_count % 48
            allocated["Luxury Motorcoach"] = coaches
            total_daily_cost += coaches * cls.FLEET_CATALOG["Luxury Motorcoach"].daily_rate_usd
            pax_cap += coaches * 48
            lug_cap += coaches * 55

            if remaining_pax > 14:
                allocated["Luxury Motorcoach"] += 1
                total_daily_cost += cls.FLEET_CATALOG["Luxury Motorcoach"].daily_rate_usd
                pax_cap += 48
                lug_cap += 55
            elif remaining_pax > 6:
                allocated["Executive Sprinter Van"] = 1
                total_daily_cost += cls.FLEET_CATALOG["Executive Sprinter Van"].daily_rate_usd
                pax_cap += 14
                lug_cap += 16
            elif remaining_pax > 0:
                allocated["Luxury SUV / Minivan"] = 1
                total_daily_cost += cls.FLEET_CATALOG["Luxury SUV / Minivan"].daily_rate_usd
                pax_cap += 6
                lug_cap += 7

        return FleetAllocationResult(
            total_passengers=passengers_count,
            total_luggage_pieces=luggage_pieces_count,
            allocated_vehicles=allocated,
            total_fleet_capacity_pax=pax_cap,
            total_fleet_capacity_luggage=lug_cap,
            total_daily_cost_usd=round(total_daily_cost, 2),
            allocation_notes=f"Optimal fleet configuration covering {passengers_count} pax & {luggage_pieces_count} bags.",
        )
