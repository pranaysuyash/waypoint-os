"""
spine_api/routers/visa_radar.py — Real-Time Visa & Passport Validity Router.

Provides endpoints to audit traveler passport expiration against destination entry rules,
evaluate e-Visa, ESTA, ETA, and Schengen requirements, and fetch destination entry protocols.
"""

from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, Header, HTTPException

from spine_api.persistence import TripStore
from spine_api.services.visa_radar import VisaCheckRequest, VisaCheckResult, audit_visa_and_passport_validity

router = APIRouter(prefix="/api/v1/visa-radar", tags=["Visa & Passport Validity Radar"])


class TripVisaRequirementsResponse(BaseModel):
    ok: bool = True
    trip_id: str
    destination: str
    passport_country: str
    visa_required: bool
    visa_type: str
    min_passport_validity_months: int
    entry_protocol_summary: str
    application_portal_url: Optional[str] = None


@router.post("/check", response_model=VisaCheckResult)
def check_visa_and_passport_validity(
    body: VisaCheckRequest,
    x_agency_id: Optional[str] = Header(None, alias="X-Agency-ID"),
):
    """Audit traveler passport expiry and entry visa requirements for a destination."""
    return audit_visa_and_passport_validity(body)


@router.get("/{trip_id}/requirements", response_model=TripVisaRequirementsResponse)
def get_trip_visa_requirements(
    trip_id: str,
    passport_country: Optional[str] = None,
    x_agency_id: Optional[str] = Header(None, alias="X-Agency-ID"),
):
    """Fetch official destination visa entry protocols and consular application links for a trip.

    AT-11 (2026-09-07): no test-agency fallback — the agency scope must be
    explicit. The traveler's passport country comes from the trip record (or
    an explicit query param); when it is unknown the radar abstains from a
    legal determination instead of assuming US nationality.
    """
    if not x_agency_id:
        raise HTTPException(
            status_code=400,
            detail="X-Agency-ID header is required for trip visa requirements",
        )
    trip = TripStore.get_trip_for_agency(trip_id, x_agency_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    dest = trip.get("destination") or "Destination"
    dest_lower = dest.lower()
    packet = trip.get("packet") or {}

    if "uk" in dest_lower or "london" in dest_lower or "england" in dest_lower:
        d_code = "GB"
        portal = "https://www.gov.uk/electronic-travel-authorisation-eta"
    elif "france" in dest_lower or "paris" in dest_lower:
        d_code = "FR"
        portal = "https://france-visas.gouv.fr"
    elif "japan" in dest_lower or "tokyo" in dest_lower:
        d_code = "JP"
        portal = "https://www.evisa.mofa.go.jp"
    else:
        d_code = dest[:2].upper() if len(dest) >= 2 else "UN"
        portal = None

    resolved_passport_country = (
        passport_country
        or packet.get("passport_country")
        or trip.get("passport_country")
        or packet.get("nationality")
    )

    travel_date = (
        packet.get("start_date")
        or packet.get("departure_date")
        or trip.get("start_date")
    )
    passport_expiry = packet.get("passport_expiry_date") or trip.get("passport_expiry_date")
    inputs_known = bool(resolved_passport_country and travel_date and passport_expiry)

    if inputs_known:
        req = VisaCheckRequest(
            passport_country=str(resolved_passport_country),
            destination_country=d_code,
            passport_expiry_date=str(passport_expiry),
            travel_date=str(travel_date),
        )
        res = audit_visa_and_passport_validity(req)
        summary = res.action_required
        visa_required = res.requires_visa
        visa_type = res.visa_type_required
    else:
        visa_required = False
        visa_type = "UNKNOWN"
        missing = [
            label
            for label, value in (
                ("traveler passport country/nationality", resolved_passport_country),
                ("travel date", travel_date),
                ("passport expiry date", passport_expiry),
            )
            if not value
        ]
        summary = (
            "Visa radar abstains from a legal determination: this trip is "
            "missing " + ", ".join(missing) + "."
        )

    return TripVisaRequirementsResponse(
        ok=True,
        trip_id=trip_id,
        destination=dest,
        passport_country=str(resolved_passport_country or "UNKNOWN"),
        visa_required=visa_required,
        visa_type=visa_type,
        # ICAO-recommended default; the per-rule minimum lives in the visa
        # rules registry and is reflected in `visa_required`/summary.
        min_passport_validity_months=6,
        entry_protocol_summary=summary,
        application_portal_url=portal,
    )
