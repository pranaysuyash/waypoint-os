"""
Autonomous Proposal Compiler API Router (PER-INT-E2E).

Provides endpoints for one-click compilation of raw customer intakes into verified,
margin-optimized, and legally feasibility-checked proposal packages.
"""

from __future__ import annotations

from datetime import date
from typing import Any, Dict
from fastapi import APIRouter
from pydantic import BaseModel, Field

from src.orchestration.proposal_compiler import AutonomousProposalCompiler

router = APIRouter(prefix="/api/v1/proposal-compiler", tags=["proposal-compiler"])


class CompileProposalRequest(BaseModel):
    trip_id: str = "TRIP-LIVE-772"
    raw_intake_text: str = Field(..., description="Conversational text or lead notes")
    destination: str = "Paris"
    departure_date: date
    return_date: date
    traveler_count: int = 2
    price_sensitivity: float = 0.2
    peak_season: bool = True


@router.post("/compile")
def compile_autonomous_proposal(payload: CompileProposalRequest) -> Dict[str, Any]:
    """Compiles intake text, GDS/NDC inventory, margin optimization, and Journey DAG into a proposal."""
    package = AutonomousProposalCompiler.compile_from_intake(
        trip_id=payload.trip_id,
        raw_intake_text=payload.raw_intake_text,
        destination=payload.destination,
        departure_date=payload.departure_date,
        return_date=payload.return_date,
        traveler_count=payload.traveler_count,
        price_sensitivity=payload.price_sensitivity,
        peak_season=payload.peak_season,
    )
    return {
        "status": "success",
        "proposal_package": package.to_dict(),
    }
