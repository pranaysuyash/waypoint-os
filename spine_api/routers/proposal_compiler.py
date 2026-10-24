"""
Autonomous Proposal Compiler API Router (PER-INT-E2E).

Provides endpoints for one-click compilation of raw customer intakes into verified,
margin-optimized, and legally feasibility-checked proposal packages.
"""

from __future__ import annotations

from datetime import date
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from src.orchestration.proposal_compiler import AutonomousProposalCompiler
from spine_api.core.auth import get_current_agency
from spine_api.models.tenant import Agency
from spine_api.persistence import TripStore

router = APIRouter(prefix="/api/v1/proposal-compiler", tags=["proposal-compiler"])


class CompileProposalRequest(BaseModel):
    trip_id: str = Field(..., description="Existing trip identifier; compiler will not invent LIVE ids")
    raw_intake_text: str = Field(..., description="Conversational text or lead notes")
    destination: str = "Paris"
    departure_date: date
    return_date: date
    traveler_count: int = 2
    price_sensitivity: float = 0.2
    peak_season: bool = True


@router.post("/compile")
def compile_autonomous_proposal(
    payload: CompileProposalRequest,
    agency: Agency = Depends(get_current_agency),
) -> Dict[str, Any]:
    """Compiles intake text, GDS/NDC inventory, margin optimization, and Journey DAG into a proposal."""
    # FND-0337 (Sim #4): feed the trip's persisted budget through so the
    # FINANCIAL_BOUND engine can judge the compiled economics against what the
    # customer actually said — a compile that never saw the budget could (and
    # did) pass "feasibility" at 2x the customer's number.
    budget_amount: Optional[float] = None
    budget_currency: Optional[str] = None
    try:
        trip = TripStore.get_trip_for_agency(payload.trip_id, agency.id)
    except Exception:
        trip = None
    if trip:
        extracted = trip.get("extracted") if isinstance(trip.get("extracted"), dict) else {}
        facts = extracted.get("facts") if isinstance(extracted.get("facts"), dict) else {}

        def _fact_value(key: str):
            slot = facts.get(key)
            return slot.get("value") if isinstance(slot, dict) else slot

        for key in ("budget_max", "budget_min", "budget_amount"):
            v = _fact_value(key)
            if isinstance(v, (int, float)) and v > 0:
                budget_amount = float(v)
                break
        cur = _fact_value("budget_currency")
        if isinstance(cur, str) and cur.strip():
            budget_currency = cur.strip().upper()

    package = AutonomousProposalCompiler.compile_from_intake(
        trip_id=payload.trip_id,
        raw_intake_text=payload.raw_intake_text,
        destination=payload.destination,
        departure_date=payload.departure_date,
        return_date=payload.return_date,
        traveler_count=payload.traveler_count,
        price_sensitivity=payload.price_sensitivity,
        peak_season=payload.peak_season,
        budget_amount=budget_amount,
        budget_currency=budget_currency,
    )
    return {
        "status": "success",
        "proposal_package": package.to_dict(),
    }
