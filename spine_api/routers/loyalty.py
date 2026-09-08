"""
spine_api/routers/loyalty.py — Loyalty & Award Ticket Redemption Router.

Allows searching airline award flight seat availability, calculating points transfer bonuses
(Chase, Amex, Capital One, Citi), and managing client elite status perks and frequent flyer profiles.
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Header


router = APIRouter(prefix="/api/v1/loyalty", tags=["Loyalty & Award Ticket Engine"])


class AwardAvailabilityOption(BaseModel):
    option_id: str
    airline: str
    flight_number: str
    cabin_class: str  # ECONOMY, BUSINESS, FIRST
    points_required: int
    taxes_usd: float
    transfer_partner: str  # AMEX_MR, CHASE_UR, CAPITAL_ONE, CITI_TYP
    transfer_ratio: str = "1:1"
    seats_available: int


class AwardSearchRequest(BaseModel):
    origin: str = "JFK"
    destination: str = "NRT"
    departure_date: str = "2026-10-15"
    cabin_class: str = "BUSINESS"
    passengers_count: int = 1


class AwardSearchResponse(BaseModel):
    ok: bool = True
    origin: str
    destination: str
    departure_date: str
    cabin_class: str
    award_options: List[AwardAvailabilityOption] = Field(default_factory=list)
    reality_tier: str = "deterministic_preview"
    provider_connected: bool = False
    sample_data: bool = True


class LoyaltyProgramProfile(BaseModel):
    program_name: str
    account_number: str
    elite_tier: Optional[str] = None
    points_balance: Optional[int] = None
    perks: List[str] = Field(default_factory=list)


class CustomerLoyaltySummary(BaseModel):
    ok: bool = True
    customer_id: str
    tsa_precheck_known_traveler_number: Optional[str] = None
    passport_number_masked: Optional[str] = None
    programs: List[LoyaltyProgramProfile] = Field(default_factory=list)
    reality_tier: str = "deterministic_preview"
    provider_connected: bool = False
    sample_data: bool = True


@router.post("/award-search", response_model=AwardSearchResponse)
def search_award_availability(
    body: AwardSearchRequest,
    x_agency_id: Optional[str] = Header(None, alias="X-Agency-ID"),
):
    """Search airline award seat inventory and credit card point transfer options."""
    options = [
        AwardAvailabilityOption(
            option_id="award_ana_01",
            airline="ANA All Nippon Airways",
            flight_number="NH109",
            cabin_class=body.cabin_class,
            points_required=75000,
            taxes_usd=142.50,
            transfer_partner="AMEX_MR",
            transfer_ratio="1:1 (30% bonus active)",
            seats_available=2,
        ),
        AwardAvailabilityOption(
            option_id="award_jal_02",
            airline="Japan Airlines",
            flight_number="JL003",
            cabin_class=body.cabin_class,
            points_required=80000,
            taxes_usd=98.00,
            transfer_partner="CHASE_UR",
            transfer_ratio="1:1",
            seats_available=4,
        ),
    ]

    return AwardSearchResponse(
        ok=True,
        origin=body.origin,
        destination=body.destination,
        departure_date=body.departure_date,
        cabin_class=body.cabin_class,
        award_options=options,
        reality_tier="deterministic_preview",
        provider_connected=False,
        sample_data=True,
    )


@router.get("/{customer_id}/balances", response_model=CustomerLoyaltySummary)
def get_customer_loyalty_balances(
    customer_id: str,
    x_agency_id: Optional[str] = Header(None, alias="X-Agency-ID"),
):
    """Loyalty balances are not a live FFN store (AT-13). Abstain instead of inventing 1K/Titanium."""
    return CustomerLoyaltySummary(
        ok=True,
        customer_id=customer_id,
        tsa_precheck_known_traveler_number=None,
        passport_number_masked=None,
        programs=[],
        reality_tier="unavailable",
        provider_connected=False,
        sample_data=False,
    )
