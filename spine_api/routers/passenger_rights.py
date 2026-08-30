"""
spine_api/routers/passenger_rights.py — EU261 / US DOT Passenger Rights Claim Automation Engine (IDEA-129).

Evaluates flight delays (>3h) and cancellations under EU261, UK261, and US DOT passenger protection regulations,
calculates statutory compensation amounts per passenger, and auto-generates formal airline claim documentation.
"""

from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Header, HTTPException

from spine_api.persistence import TEST_AGENCY_ID, AuditStore, TripStore

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


def _calculate_eu261_compensation(distance_km: float, delay_hours: float) -> float:
    if delay_hours < 3.0:
        return 0.0
    if distance_km <= 1500:
        return 250.0  # €250 for short flights <= 1500 km
    elif distance_km <= 3500:
        return 400.0  # €400 for intra-EU or flights 1500-3500 km
    else:
        return 600.0  # €600 for long-haul flights > 3500 km


@router.post("/evaluate", response_model=ClaimEvaluationResponse)
def evaluate_passenger_rights_claim(
    body: ClaimEvaluationRequest,
    x_agency_id: Optional[str] = Header(None, alias="X-Agency-ID"),
):
    """Evaluate flight delay/cancellation for statutory passenger rights compensation (EU261 / US DOT)."""
    fl = body.flight_number.upper().strip()
    is_eu_or_uk = fl.startswith("BA") or fl.startswith("AF") or fl.startswith("LH") or fl.startswith("KL") or fl.startswith("IB") or fl.startswith("EI")

    if is_eu_or_uk:
        framework = "EU261"
        comp_eur = _calculate_eu261_compensation(body.distance_km, body.delay_hours)
    else:
        framework = "US_DOT"
        comp_eur = 300.0 if body.delay_hours >= 4.0 else 0.0

    is_eligible = comp_eur > 0
    total_eur = comp_eur * body.passengers_count
    total_usd = round(total_eur * 1.09, 2)  # EUR/USD ~ 1.09

    reason = (
        f"Eligible under {framework} for {body.delay_hours}h delay on {fl} ({body.distance_km:.0f} km flight)"
        if is_eligible
        else f"Ineligible under {framework}: delay duration ({body.delay_hours}h) below statutory 3h threshold"
    )

    return ClaimEvaluationResponse(
        ok=True,
        trip_id=body.trip_id,
        flight_number=fl,
        is_eligible=is_eligible,
        regulatory_framework=framework if is_eligible else "NONE",
        compensation_per_passenger_eur=comp_eur,
        total_statutory_compensation_eur=total_eur,
        total_claim_amount_usd=total_usd,
        passengers_count=body.passengers_count,
        claim_reason=reason,
    )


@router.post("/{trip_id}/generate-claim", response_model=GenerateClaimResponse)
def generate_formal_airline_claim(
    trip_id: str,
    body: GenerateClaimRequest,
    x_agency_id: Optional[str] = Header(None, alias="X-Agency-ID"),
):
    """Generate formal statutory airline claim document for delayed/cancelled flight."""
    agency_id = x_agency_id or TEST_AGENCY_ID
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
