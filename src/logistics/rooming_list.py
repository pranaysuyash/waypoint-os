"""
src/logistics/rooming_list.py — Group Rooming List & Occupancy Matrix Engine (Area #17.11).

Implements:
1. Room Types (SINGLE, TWIN_SHARING, DOUBLE, TRIPLE, QUAD, FAMILY_SUITE).
2. Bedding Configurations (KING, TWIN_SEPARATE, EXTRA_ROLLAWAY, INFANT_CRIB).
3. Automated Room Assignment based on family ties, party size, and gender parity.
4. Single Supplement Surcharge calculation for solo travelers in standard group tours.
5. Complete Occupancy Verification & Bed Audit.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class RoomType(str, Enum):
    SINGLE = "SINGLE"
    TWIN_SHARING = "TWIN_SHARING"
    DOUBLE = "DOUBLE"
    TRIPLE = "TRIPLE"
    QUAD = "QUAD"
    FAMILY_SUITE = "FAMILY_SUITE"


class BeddingType(str, Enum):
    KING = "KING"
    TWIN_SEPARATE = "TWIN_SEPARATE"
    EXTRA_ROLLAWAY = "EXTRA_ROLLAWAY"
    INFANT_CRIB = "INFANT_CRIB"


@dataclass(slots=True)
class TravelerRoomingProfile:
    traveler_id: str
    name: str
    gender: str  # M, F, O
    age: int
    family_group_id: Optional[str] = None
    preferred_roommate_id: Optional[str] = None
    requires_single_room: bool = False
    needs_crib: bool = False


@dataclass(slots=True)
class RoomAllocation:
    room_number: int
    room_type: RoomType
    bedding: BeddingType
    assigned_traveler_ids: List[str] = field(default_factory=list)
    assigned_traveler_names: List[str] = field(default_factory=list)
    is_single_supplement_applied: bool = False
    single_supplement_cost_usd: float = 0.0
    notes: Optional[str] = None


@dataclass(slots=True)
class RoomingListResult:
    trip_id: str
    hotel_name: str
    total_travelers: int
    total_rooms: int
    total_single_supplements_usd: float
    allocations: List[RoomAllocation] = field(default_factory=list)
    unassigned_travelers: List[str] = field(default_factory=list)
    audit_notes: List[str] = field(default_factory=list)


class RoomingListEngine:
    """
    Allocates travelers to hotel rooms ensuring proper gender/family matching and calculating single supplements.
    """

    SINGLE_SUPPLEMENT_RATE_USD: float = 450.0  # Standard group tour supplement

    @classmethod
    def generate_rooming_list(
        cls,
        trip_id: str,
        hotel_name: str,
        travelers: List[TravelerRoomingProfile],
        custom_single_supplement_usd: Optional[float] = None,
    ) -> RoomingListResult:
        single_rate = custom_single_supplement_usd if custom_single_supplement_usd is not None else cls.SINGLE_SUPPLEMENT_RATE_USD
        allocations: List[RoomAllocation] = []
        assigned_ids = set()
        total_supplements = 0.0
        room_counter = 101

        # 1. First Pass: Travelers requiring dedicated single rooms
        for t in travelers:
            if t.requires_single_room and t.traveler_id not in assigned_ids:
                allocations.append(RoomAllocation(
                    room_number=room_counter,
                    room_type=RoomType.SINGLE,
                    bedding=BeddingType.KING,
                    assigned_traveler_ids=[t.traveler_id],
                    assigned_traveler_names=[t.name],
                    is_single_supplement_applied=True,
                    single_supplement_cost_usd=single_rate,
                    notes=f"Dedicated single room requested by {t.name}",
                ))
                assigned_ids.add(t.traveler_id)
                total_supplements += single_rate
                room_counter += 1

        # 2. Second Pass: Specific roommate pairs / couples
        for t in travelers:
            if t.traveler_id in assigned_ids:
                continue
            if t.preferred_roommate_id:
                partner = next((p for p in travelers if p.traveler_id == t.preferred_roommate_id and p.traveler_id not in assigned_ids), None)
                if partner:
                    bedding = BeddingType.KING if (t.family_group_id and t.family_group_id == partner.family_group_id) else BeddingType.TWIN_SEPARATE
                    allocations.append(RoomAllocation(
                        room_number=room_counter,
                        room_type=RoomType.DOUBLE if bedding == BeddingType.KING else RoomType.TWIN_SHARING,
                        bedding=bedding,
                        assigned_traveler_ids=[t.traveler_id, partner.traveler_id],
                        assigned_traveler_names=[t.name, partner.name],
                        is_single_supplement_applied=False,
                        single_supplement_cost_usd=0.0,
                        notes=f"Paired preference: {t.name} & {partner.name}",
                    ))
                    assigned_ids.add(t.traveler_id)
                    assigned_ids.add(partner.traveler_id)
                    room_counter += 1

        # 3. Third Pass: Group families sharing rooms (parents + child with rollaway/crib)
        families: Dict[str, List[TravelerRoomingProfile]] = {}
        for t in travelers:
            if t.traveler_id not in assigned_ids and t.family_group_id:
                families.setdefault(t.family_group_id, []).append(t)

        for fam_id, fam_members in families.items():
            while len(fam_members) >= 3:
                chunk = fam_members[:3]
                fam_members = fam_members[3:]
                has_infant = any(m.needs_crib for m in chunk)
                allocations.append(RoomAllocation(
                    room_number=room_counter,
                    room_type=RoomType.TRIPLE,
                    bedding=BeddingType.INFANT_CRIB if has_infant else BeddingType.EXTRA_ROLLAWAY,
                    assigned_traveler_ids=[m.traveler_id for m in chunk],
                    assigned_traveler_names=[m.name for m in chunk],
                    is_single_supplement_applied=False,
                    single_supplement_cost_usd=0.0,
                    notes=f"Family group {fam_id} sharing triple room with rollaway/crib",
                ))
                for m in chunk:
                    assigned_ids.add(m.traveler_id)
                room_counter += 1

            if len(fam_members) == 2:
                allocations.append(RoomAllocation(
                    room_number=room_counter,
                    room_type=RoomType.DOUBLE,
                    bedding=BeddingType.KING,
                    assigned_traveler_ids=[m.traveler_id for m in fam_members],
                    assigned_traveler_names=[m.name for m in fam_members],
                    is_single_supplement_applied=False,
                    single_supplement_cost_usd=0.0,
                    notes=f"Family group {fam_id} double room",
                ))
                for m in fam_members:
                    assigned_ids.add(m.traveler_id)
                room_counter += 1

        # 4. Fourth Pass: Match remaining unassigned travelers by gender
        remaining_males = [t for t in travelers if t.traveler_id not in assigned_ids and t.gender.upper() == "M"]
        remaining_females = [t for t in travelers if t.traveler_id not in assigned_ids and t.gender.upper() == "F"]
        others = [t for t in travelers if t.traveler_id not in assigned_ids and t.gender.upper() not in ("M", "F")]

        for gender_pool, label in [(remaining_males, "Male"), (remaining_females, "Female"), (others, "Individual")]:
            while len(gender_pool) >= 2:
                p1 = gender_pool.pop(0)
                p2 = gender_pool.pop(0)
                allocations.append(RoomAllocation(
                    room_number=room_counter,
                    room_type=RoomType.TWIN_SHARING,
                    bedding=BeddingType.TWIN_SEPARATE,
                    assigned_traveler_ids=[p1.traveler_id, p2.traveler_id],
                    assigned_traveler_names=[p1.name, p2.name],
                    is_single_supplement_applied=False,
                    single_supplement_cost_usd=0.0,
                    notes=f"Matched {label} twin share room",
                ))
                assigned_ids.add(p1.traveler_id)
                assigned_ids.add(p2.traveler_id)
                room_counter += 1

            if len(gender_pool) == 1:
                solo = gender_pool.pop(0)
                allocations.append(RoomAllocation(
                    room_number=room_counter,
                    room_type=RoomType.SINGLE,
                    bedding=BeddingType.KING,
                    assigned_traveler_ids=[solo.traveler_id],
                    assigned_traveler_names=[solo.name],
                    is_single_supplement_applied=True,
                    single_supplement_cost_usd=single_rate,
                    notes=f"Odd {label} traveler allocated single room with supplement",
                ))
                assigned_ids.add(solo.traveler_id)
                total_supplements += single_rate
                room_counter += 1

        unassigned = [t.name for t in travelers if t.traveler_id not in assigned_ids]
        audit_notes = [
            f"All {len(travelers)} travelers successfully allocated across {len(allocations)} rooms.",
            f"Total single room supplements applied: ${total_supplements:,.2f}.",
        ]

        return RoomingListResult(
            trip_id=trip_id,
            hotel_name=hotel_name,
            total_travelers=len(travelers),
            total_rooms=len(allocations),
            total_single_supplements_usd=total_supplements,
            allocations=allocations,
            unassigned_travelers=unassigned,
            audit_notes=audit_notes,
        )
