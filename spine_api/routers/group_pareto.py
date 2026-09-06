"""
Group Travel Pareto Consensus & Split-Payment Router (PER-GRP, GRP-01..12).

Provides endpoints for multi-traveler preference modeling, harmonic consensus solving,
and split-payment ledger generation.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter
from pydantic import BaseModel, Field

from src.decision.group_pareto_engine import (
    GroupParetoEngine,
    ItineraryProposalOption,
    TravelerPreferenceProfile,
)

router = APIRouter(prefix="/api/v1/group-pareto", tags=["group-pareto"])


class TravelerInput(BaseModel):
    traveler_id: str
    name: str
    max_budget: float = 3000.0
    preferred_pace: str = "MODERATE"
    activity_interests: List[str] = Field(default_factory=lambda: ["CULTURE", "CULINARY"])
    dietary_needs: List[str] = Field(default_factory=list)
    requires_private_room: bool = False


class OptionInput(BaseModel):
    option_id: str
    title: str
    cost_per_person: float
    pace: str
    activities: List[str]


class SolveConsensusRequest(BaseModel):
    travelers: List[TravelerInput]
    options: List[OptionInput]


class SplitLedgerRequest(BaseModel):
    trip_id: str
    total_shared_cost: float
    travelers: List[TravelerInput]
    single_room_supplement_amount: float = 350.0
    activity_opt_ins: Optional[Dict[str, float]] = None


@router.post("/consensus/solve")
def solve_group_consensus(payload: SolveConsensusRequest) -> Dict[str, Any]:
    """Computes Pareto frontier consensus with harmonic dissatisfaction penalties across group members."""
    domain_travelers = [
        TravelerPreferenceProfile(
            traveler_id=t.traveler_id,
            name=t.name,
            max_budget=t.max_budget,
            preferred_pace=t.preferred_pace,
            activity_interests=t.activity_interests,
            dietary_needs=t.dietary_needs,
            requires_private_room=t.requires_private_room,
        )
        for t in payload.travelers
    ]
    domain_options = [
        ItineraryProposalOption(
            option_id=o.option_id,
            title=o.title,
            cost_per_person=o.cost_per_person,
            pace=o.pace,
            activities=o.activities,
        )
        for o in payload.options
    ]
    return GroupParetoEngine.solve_pareto_consensus(domain_travelers, domain_options)


@router.post("/ledger/build")
def build_split_ledger(payload: SplitLedgerRequest) -> Dict[str, Any]:
    """Generates an itemized split payment ledger with custom rooming and activity opt-ins."""
    domain_travelers = [
        TravelerPreferenceProfile(
            traveler_id=t.traveler_id,
            name=t.name,
            max_budget=t.max_budget,
            preferred_pace=t.preferred_pace,
            activity_interests=t.activity_interests,
            dietary_needs=t.dietary_needs,
            requires_private_room=t.requires_private_room,
        )
        for t in payload.travelers
    ]
    ledger = GroupParetoEngine.generate_split_payment_ledger(
        trip_id=payload.trip_id,
        total_shared_cost=payload.total_shared_cost,
        travelers=domain_travelers,
        single_room_supplement_amount=payload.single_room_supplement_amount,
        activity_opt_ins=payload.activity_opt_ins,
    )
    return {
        "status": "success",
        "trip_id": payload.trip_id,
        "shares": [
            {
                "traveler_id": s.traveler_id,
                "name": s.name,
                "base_share": s.base_share,
                "room_supplement": s.room_supplement,
                "opt_in_activities_amount": s.opt_in_activities_amount,
                "total_owed": s.total_owed,
                "amount_paid": s.amount_paid,
                "payment_status": s.payment_status,
                "payment_link": s.payment_link,
            }
            for s in ledger
        ],
    }
