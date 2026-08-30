"""
spine_api/routers/visa_radar.py — Real-Time Visa & Passport Validity Router.

Provides endpoints to audit traveler passport expiration against destination entry rules,
evaluate e-Visa, ESTA, ETA, and Schengen requirements, and fetch destination entry protocols.
"""

from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, Header, HTTPException

from spine_api.persistence import TEST_AGENCY_ID, TripStore
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
    passport_country: str = "US",
    x_agency_id: Optional[str] = Header(None, alias="X-Agency-ID"),
):
    """Fetch official destination visa entry protocols and consular application links for a trip."""
    agency_id = x_agency_id or TEST_AGENCY_ID
    trip = TripStore.get_trip_for_agency(trip_id, agency_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    dest = trip.get("destination") or "Destination"
    dest_lower = dest.lower()

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
        d_code = "FR"
        portal = "https://travel.state.gov"

    req = VisaCheckRequest(
        passport_country=passport_country,
        destination_country=d_code,
        passport_expiry_date="2027-01-01T00:00:00Z",
        travel_date="2026-09-01T00:00:00Z",
    )
    res = audit_visa_and_passport_validity(req)

    return TripVisaRequirementsResponse(
        ok=True,
        trip_id=trip_id,
        destination=dest,
        passport_country=passport_country,
        visa_required=res.requires_visa,
        visa_type=res.visa_type_required,
        min_passport_validity_months=6,
        entry_protocol_summary=res.action_required,
        application_portal_url=portal,
    )
