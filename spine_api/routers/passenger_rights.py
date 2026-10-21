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
from spine_api.services import claim_disposition
from spine_api.services.claim_framework import (
    AIRPORT_COUNTRY,
    MONTREAL_ARTICLE_19,
    EU_EEA_COUNTRIES,
    resolve_carrier_country,
    resolve_framework,
    statutory_amount,
)
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
    # FND-0312 (2026-10-05): optional route geography. Absent fields are
    # never guessed — classification falls back to the flight-number carrier
    # prefix for the carrier-license rule only, else NONE + Montreal Art. 19.
    departure_country: Optional[str] = None
    arrival_country: Optional[str] = None
    carrier_country: Optional[str] = None


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
        departure_country=body.departure_country,
        arrival_country=body.arrival_country,
        carrier_country=body.carrier_country,
        disruption_type=body.disruption_type,
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


def _trip_claim_geography(trip: dict) -> dict:
    """Derive claim geography from the trip's flight facts — never guessed.

    Priority: flight_status_updates airport codes → trip origin/destination
    free text (matched against known country names only) → flight-number
    carrier prefix (carrier-license rule only). Anything still unknown is
    ``None`` and the resolver treats it honestly.
    """
    updates = [u for u in (trip.get("flight_status_updates") or []) if isinstance(u, dict)]
    fact = next((u for u in updates if u.get("flight_number")), None)
    fact = fact or {}

    dep = AIRPORT_COUNTRY.get(str(fact.get("origin_iata", "")).upper())
    arr = AIRPORT_COUNTRY.get(str(fact.get("destination_iata", "")).upper())

    if dep is None:
        dep = _country_text_hint(trip.get("origin"))
    if arr is None:
        arr = _country_text_hint(trip.get("destination"))

    flight_number = str(fact.get("flight_number") or "")
    carrier = resolve_carrier_country(fact.get("carrier"), flight_number)

    return {
        "departure_country": dep,
        "arrival_country": arr,
        "carrier_country": carrier,
        "flight_number": flight_number,
        "disruption_type": str(fact.get("status", "")).upper() or None,
        "delay_hours": (float(fact.get("delay_minutes", 0) or 0) / 60.0) if fact else 0.0,
    }


def _country_text_hint(text: object) -> Optional[str]:
    """Match free-text origin/destination against known country names only."""
    t = str(text or "").strip().lower()
    if not t:
        return None
    for name in ("united kingdom", "united states", "united arab emirates", "czech republic"):
        if name in t:
            return name
    for name in EU_EEA_COUNTRIES:
        if name in t:
            return name
    return None


def _claim_letter(framework: str, trip_id: str, body: "GenerateClaimRequest", now_iso: str) -> str:
    """Framework-specific statutory claim letter (FND-0312).

    The letter's legal basis must match the resolved framework — for NONE it
    is an honest Montreal Convention Art. 19 / carrier-policy demand, never a
    fabricated EU261 heading.
    """
    header = (
        "FORMAL STATUTORY COMPENSATION CLAIM UNDER EU261/2004\n"
        if framework == "EU261"
        else "FORMAL STATUTORY COMPENSATION CLAIM UNDER UK261\n"
        if framework == "UK261"
        else "FORMAL STATUTORY COMPENSATION CLAIM UNDER US DOT PASSENGER PROTECTION RULES\n"
        if framework == "US_DOT"
        else f"FORMAL CLAIM FOR FLIGHT DISRUPTION DAMAGES UNDER THE {MONTREAL_ARTICLE_19.upper()}\n"
    )
    if framework == "NONE":
        demands = (
            f"We acknowledge this disruption falls outside the EU261/UK261/US DOT statutory "
            f"compensation regimes. Our claim is therefore brought under the "
            f"{MONTREAL_ARTICLE_19} for damages caused by delay/cancellation, subject to the "
            f"convention's liability limits, and under the airline's own customer-care policy. "
            f"Please provide the carrier's claims reference and settlement process for the "
            f"passengers' documented losses."
        )
    else:
        demands = (
            "Pursuant to the applicable statutory passenger-protection regime, we formally "
            "request statutory compensation on behalf of the passengers listed above for "
            "flight disruption exceeding statutory thresholds. Please remit compensation "
            "directly to the affected passengers within 14 days."
        )
    return (
        f"{header}"
        f"Date: {now_iso[:10]}\n"
        f"Trip ID: {trip_id}\n"
        f"Booking Reference: {body.booking_reference}\n"
        f"Passengers: {', '.join(body.passenger_names)}\n\n"
        f"Dear Airline Customer Relations,\n"
        f"{demands}"
    )


@router.post("/{trip_id}/generate-claim", response_model=GenerateClaimResponse)
def generate_formal_airline_claim(
    trip_id: str,
    body: GenerateClaimRequest,
    agency_id: str = Depends(get_current_agency_id),
):
    """Generate formal statutory airline claim document for delayed/cancelled flight.

    FND-0312 (2026-10-05): the claim's regulatory framework is resolved
    through the SAME canonical resolver as /evaluate (previously this
    endpoint hard-coded an EU261 letter for every flight, including
    non-EU routes with no EU touchpoint). Framework NONE produces an
    honest Montreal Convention Art. 19 / carrier-policy demand.
    """
    trip = TripStore.get_trip_for_agency(trip_id, agency_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    geo = _trip_claim_geography(trip)
    resolved = resolve_framework(
        departure_country=geo["departure_country"],
        arrival_country=geo["arrival_country"],
        carrier_country=geo["carrier_country"],
        distance_km=0.0,
        delay_hours=geo["delay_hours"],
        disruption_type=geo["disruption_type"] or "CANCELLED",
    )
    framework = resolved["framework"]
    amount, currency = statutory_amount(framework, 0.0)

    now_iso = datetime.now(timezone.utc).isoformat()
    claim_id = f"claim_{trip_id[:8]}_{datetime.now().strftime('%M%S')}"

    letter = _claim_letter(framework, trip_id, body, now_iso)

    trip["passenger_claim"] = {
        "claim_id": claim_id,
        "booking_reference": body.booking_reference,
        "passenger_names": body.passenger_names,
        "status": "SUBMITTED",
        "generated_at": now_iso,
        "regulatory_framework": framework,
        "statutory_compensation_per_passenger": amount if framework != "NONE" else 0.0,
        "compensation_currency": currency if framework != "NONE" else "NONE",
        "framework_basis": resolved["basis"],
        "montreal_applies": resolved["montreal_applies"],
        # T10 (FND-0233, decided 2026-09-30): the claim starts a disposition
        # ledger tracking the airline→traveler outcome. This system never
        # initiates, holds, or receives money — it records where the claim
        # stands and what the airline ultimately paid the traveler directly.
        "disposition": claim_disposition.new_disposition(claim_id, initial_state="SUBMITTED"),
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
            "regulatory_framework": framework,
            "framework_basis": resolved["basis"],
        },
    )

    return GenerateClaimResponse(
        ok=True,
        trip_id=trip_id,
        claim_id=claim_id,
        regulatory_framework=framework,
        claim_letter_text=letter,
        generated_at=now_iso,
    )


class DispositionResponse(BaseModel):
    ok: bool = True
    trip_id: str
    claim_id: str
    disposition: dict


class DispositionUpdateRequest(BaseModel):
    new_state: str
    note: str = ""
    # Recorded outcome of airline→traveler payment (amount/channel/date).
    # Informational only — this system moves no money.
    outcome: Optional[dict] = None


@router.get("/{trip_id}/claims/{claim_id}/disposition", response_model=DispositionResponse)
def get_claim_disposition(
    trip_id: str,
    claim_id: str,
    agency_id: str = Depends(get_current_agency_id),
):
    """Operator view of a claim's disposition (parcel-tracking model).

    Records outcomes of airline→traveler payments; the system itself never
    initiates, holds, or receives money (owner invariant, 2026-09-30).
    """
    trip = TripStore.get_trip_for_agency(trip_id, agency_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    claim = trip.get("passenger_claim") or {}
    if claim.get("claim_id") != claim_id:
        raise HTTPException(status_code=404, detail=f"Claim not found: {claim_id}")

    disposition = dict(claim.get("disposition") or {})
    if not disposition:
        # Pre-T10 claims have no ledger yet — surface DRAFTED rather than 500.
        disposition = claim_disposition.new_disposition(claim_id, initial_state="DRAFTED")
    if disposition.get("state") in ("SUBMITTED", "ESCALATED"):
        disposition["overdue"] = claim_disposition.compute_overdue(
            _submitted_at(disposition)
        )
    return DispositionResponse(
        ok=True, trip_id=trip_id, claim_id=claim_id, disposition=disposition
    )


def _submitted_at(disposition: dict) -> Optional[str]:
    for entry in reversed(disposition.get("history") or []):
        if entry.get("state") in ("SUBMITTED", "ESCALATED"):
            return entry.get("at")
    return None


@router.patch("/{trip_id}/claims/{claim_id}/disposition", response_model=DispositionResponse)
def update_claim_disposition(
    trip_id: str,
    claim_id: str,
    body: DispositionUpdateRequest,
    agency_id: str = Depends(get_current_agency_id),
):
    """Advance a claim's disposition one legal step (operator-entered).

    The operator records what the airline actually did — the airline's
    real-world reply changes reality; only a human reads it. Illegal
    transitions are rejected with 409. This endpoint moves a STATUS, never
    money (owner invariant).
    """
    trip = TripStore.get_trip_for_agency(trip_id, agency_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    claim = trip.get("passenger_claim") or {}
    if claim.get("claim_id") != claim_id:
        raise HTTPException(status_code=404, detail=f"Claim not found: {claim_id}")

    disposition = claim.get("disposition")
    if not disposition:
        raise HTTPException(status_code=409, detail="Claim has no disposition ledger")

    try:
        claim_disposition.apply_transition(
            disposition,
            body.new_state,
            by=agency_id,
            note=body.note,
            outcome=body.outcome,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))

    TripStore.save_trip(trip, agency_id=agency_id)
    AuditStore.log_event(
        event_type="passenger_rights_claim_disposition_updated",
        user_id=agency_id,
        details={
            "trip_id": trip_id,
            "claim_id": claim_id,
            "new_state": body.new_state,
        },
    )
    return DispositionResponse(
        ok=True, trip_id=trip_id, claim_id=claim_id, disposition=disposition
    )
