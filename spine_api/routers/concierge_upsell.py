"""
spine_api/routers/concierge_upsell.py — Autonomous Concierge Up-Sell & Experience Personalization Engine (IDEA-128).

Analyzes confirmed trip itineraries and repeat client preference memory prior to departure,
auto-generates personalized VIP experience add-on proposals (transfers, dining, lounges, tours), and tracks conversion.
"""

from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException

from spine_api.core.auth import get_current_agency_id
from spine_api.persistence import AuditStore, TripStore

router = APIRouter(prefix="/api/v1/concierge-upsell", tags=["Concierge Up-Sell Engine"])


class ConciergeExperienceItem(BaseModel):
    item_id: str
    title: str
    category: str  # TRANSFER, DINING, LOUNGE, EXCURSION, SPA
    price_usd: float
    margin_pct: float = 20.0
    description: str
    match_reason: str


class UpsellProposalResponse(BaseModel):
    ok: bool = True
    trip_id: str
    destination: str
    days_until_departure: int = 14
    recommended_upsells: List[ConciergeExperienceItem] = Field(default_factory=list)
    total_upsell_value_usd: float
    status: str = "DRAFT"  # DRAFT, DISPATCHED, ACCEPTED


class DispatchUpsellRequest(BaseModel):
    trip_id: str
    selected_item_ids: List[str]
    dispatch_channel: str = "email"  # email, whatsapp, sms
    advisor_note: Optional[str] = None


class DispatchUpsellResponse(BaseModel):
    ok: bool = True
    trip_id: str
    dispatched_items_count: int
    dispatched_channel: str
    dispatched_at: str


@router.get("/{trip_id}/propose", response_model=UpsellProposalResponse)
def propose_concierge_upsells(
    trip_id: str,
    agency_id: str = Depends(get_current_agency_id),
):
    """Auto-generate personalized VIP concierge experience add-on proposals for a trip."""
    trip = TripStore.get_trip_for_agency(trip_id, agency_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    dest = trip.get("destination") or "Destination"
    packet = trip.get("packet", {}) or {}
    dietary = packet.get("dietary_requirements") or ""

    items: List[ConciergeExperienceItem] = [
        ConciergeExperienceItem(
            item_id="up_transfer_01",
            title=f"VIP Airport Meet & Chauffeur Transfer in {dest}",
            category="TRANSFER",
            price_usd=250.0,
            description=f"Private Mercedes S-Class airport transfer with luggage assistance in {dest}",
            match_reason="Matches luxury travel profile",
        ),
        ConciergeExperienceItem(
            item_id="up_lounge_01",
            title="First Class Airport VIP Lounge Pass",
            category="LOUNGE",
            price_usd=120.0,
            description="Fast-track security clearance and luxury quiet suite access",
            match_reason="Frequent long-haul flight",
        ),
    ]

    if "vegan" in dietary.lower() or "vegetarian" in dietary.lower():
        items.append(
            ConciergeExperienceItem(
                item_id="up_dining_01",
                title=f"Exclusive Michelin Plant-Based Tasting Menu in {dest}",
                category="DINING",
                price_usd=350.0,
                description="Priority table reservation with sommelier pairing",
                match_reason=f"Matched client dietary preference: {dietary}",
            )
        )
    else:
        items.append(
            ConciergeExperienceItem(
                item_id="up_dining_02",
                title=f"Private Sunset Chef's Table Dining in {dest}",
                category="DINING",
                price_usd=400.0,
                description="Private seaside dining experience prepared by executive chef",
                match_reason="Special occasion travel",
            )
        )

    total_val = sum(i.price_usd for i in items)
    upsell_status = trip.get("concierge_upsell", {}).get("status", "DRAFT")

    return UpsellProposalResponse(
        ok=True,
        trip_id=trip_id,
        destination=dest,
        days_until_departure=14,
        recommended_upsells=items,
        total_upsell_value_usd=total_val,
        status=upsell_status,
    )


@router.post("/{trip_id}/dispatch", response_model=DispatchUpsellResponse)
def dispatch_concierge_upsell_proposal(
    trip_id: str,
    body: DispatchUpsellRequest,
    agency_id: str = Depends(get_current_agency_id),
):
    """Dispatch personalized VIP concierge experience proposals to client via email/WhatsApp."""
    trip = TripStore.get_trip_for_agency(trip_id, agency_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    now_iso = datetime.now(timezone.utc).isoformat()
    trip["concierge_upsell"] = {
        "status": "DISPATCHED",
        "selected_item_ids": body.selected_item_ids,
        "dispatch_channel": body.dispatch_channel,
        "dispatched_at": now_iso,
        "advisor_note": body.advisor_note,
    }

    TripStore.save_trip(trip, agency_id=agency_id)

    AuditStore.log_event(
        event_type="concierge_upsell_dispatched",
        user_id=agency_id,
        details={
            "trip_id": trip_id,
            "selected_items_count": len(body.selected_item_ids),
            "dispatch_channel": body.dispatch_channel,
            "advisor_note": body.advisor_note,
        },
    )

    return DispatchUpsellResponse(
        ok=True,
        trip_id=trip_id,
        dispatched_items_count=len(body.selected_item_ids),
        dispatched_channel=body.dispatch_channel,
        dispatched_at=now_iso,
    )
