"""
spine_api/routers/passenger_rights.py — EU261 / US DOT Passenger Rights Claim Automation Engine (IDEA-129).

Evaluates flight delays (>3h) and cancellations under EU261, UK261, and US DOT passenger protection regulations,
calculates statutory compensation amounts per passenger, and auto-generates formal airline claim documentation.
"""

from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException

from spine_api.core.auth import get_current_agency_id
from spine_api.persistence import AuditStore, TripStore
from spine_api.services.passenger_rights_claims import evaluate_statutory_compensation

router = APIRouter(prefix="/api/v1/passenger-rights", tags=["Passenger Rights Claim Engine"])


class ClaimEvaluationRequest(BaseModel):
    trip_id: Optional[str] = None
    flight_number: str
    disruption_type: str  # CANCELLED, DELAYED
    delay_hours: float
    distance_km: float = 3500.0
    passengers_count: int = 1
    airline_name: Optional[str] = None


class ClaimEvaluationResponse(BaseModel):
    ok: bool = True
    trip_id: Optional[str] = None
    flight_number: str
    is_eligible: bool
    regulatory_framework: str  # EU261, UK261, US_DOT, NONE
    compensation_per_passenger_eur: float
    total_statutory_compensation_eur: float
    total_claim_amount_usd: float
    passengers_count: int
    claim_reason: str


class GenerateClaimRequest(BaseModel):
    trip_id: str
    passenger_names: List[str]
    booking_reference: str
    advisor_notes: Optional[str] = None


class GenerateClaimResponse(BaseModel):
    ok: bool = True
    trip_id: str
    claim_id: str
    regulatory_framework: str
    claim_letter_text: str
    generated_at: str


@router.post("/evaluate", response_model=ClaimEvaluationResponse)
def evaluate_passenger_rights_claim(
    body: ClaimEvaluationRequest,
):
    """Evaluate flight delay/cancellation for statutory passenger rights compensation (EU261 / US DOT).

    A2 (2026-09-11): the statutory math is delegated to the canonical
    ``evaluate_statutory_compensation`` in
    ``spine_api.services.passenger_rights_claims`` — the router carries no
    compensation arithmetic of its own.
    """
    result = evaluate_statutory_compensation(
        flight_number=body.flight_number,
        distance_km=body.distance_km,
        delay_hours=body.delay_hours,
        passengers_count=body.passengers_count,
    )

    return ClaimEvaluationResponse(
        ok=True,
        trip_id=body.trip_id,
        flight_number=result["flight_number"],
        is_eligible=result["is_eligible"],
        regulatory_framework=result["regulatory_framework"],
        compensation_per_passenger_eur=result["compensation_per_passenger_eur"],
        total_statutory_compensation_eur=result["total_statutory_compensation_eur"],
        total_claim_amount_usd=result["total_claim_amount_usd"],
        passengers_count=result["passengers_count"],
        claim_reason=result["claim_reason"],
    )


@router.post("/{trip_id}/generate-claim", response_model=GenerateClaimResponse)
def generate_formal_airline_claim(
    trip_id: str,
    body: GenerateClaimRequest,
    agency_id: str = Depends(get_current_agency_id),
):
    """Generate formal statutory airline claim document for delayed/cancelled flight."""
    trip = TripStore.get_trip_for_agency(trip_id, agency_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    now_iso = datetime.now(timezone.utc).isoformat()
    claim_id = f"claim_{trip_id[:8]}_{datetime.now().strftime('%M%S')}"

    letter = (
        f"FORMAL STATUTORY COMPENSATION CLAIM UNDER EU261/2004\n"
        f"Date: {now_iso[:10]}\n"
        f"Trip ID: {trip_id}\n"
        f"Booking Reference: {body.booking_reference}\n"
        f"Passengers: {', '.join(body.passenger_names)}\n\n"
        f"Dear Airline Customer Relations,\n"
        f"Pursuant to Regulation (EC) No 261/2004, we formally request statutory compensation on behalf of the passengers listed above "
        f"for flight disruption exceeding statutory delay thresholds. Please process payment to agency trust ledger within 14 days."
    )

    trip["passenger_claim"] = {
        "claim_id": claim_id,
        "booking_reference": body.booking_reference,
        "passenger_names": body.passenger_names,
        "status": "SUBMITTED",
        "generated_at": now_iso,
    }

    TripStore.save_trip(trip, agency_id=agency_id)

    AuditStore.log_event(
        event_type="passenger_rights_claim_generated",
        user_id=agency_id,
        details={
            "trip_id": trip_id,
            "claim_id": claim_id,
            "booking_reference": body.booking_reference,
            "passengers_count": len(body.passenger_names),
        },
    )

    return GenerateClaimResponse(
        ok=True,
        trip_id=trip_id,
        claim_id=claim_id,
        regulatory_framework="EU261",
        claim_letter_text=letter,
        generated_at=now_iso,
    )
