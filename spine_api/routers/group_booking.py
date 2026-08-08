"""
spine_api/routers/group_booking.py — Group Multi-Payer Split Deposit & Passenger Collection Engine.

Provides agency-first multi-passenger deposit splitting, custom payment link distribution,
public attendee preference/payment notification portal, and manual advisor status override controls.
"""

import os
import secrets
import hashlib
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Header, HTTPException

from spine_api.persistence import TEST_AGENCY_ID, AuditStore, TripStore

router = APIRouter(prefix="/api/v1/group", tags=["Group Booking"])

FRONTEND_PUBLIC_URL = os.environ.get("FRONTEND_PUBLIC_URL", "https://waypoint-os.com")


class PassengerInviteSpec(BaseModel):
    name: str
    email: Optional[str] = None
    custom_share_cents: Optional[int] = None


class GroupInviteRequest(BaseModel):
    trip_id: str
    passengers: List[PassengerInviteSpec]
    total_deposit_cents: Optional[int] = Field(default=0, ge=0)
    agency_payment_url: Optional[str] = None
    payment_instructions: Optional[str] = None


class PassengerInviteItem(BaseModel):
    passenger_id: str
    name: str
    email: Optional[str] = None
    token: str
    web_url: str
    deposit_share_cents: int
    status: str


class GroupInviteResponse(BaseModel):
    ok: bool = True
    trip_id: str
    total_deposit_cents: int
    passenger_count: int
    deposit_per_passenger_cents: int
    agency_payment_url: Optional[str] = None
    payment_instructions: Optional[str] = None
    passenger_invites: List[PassengerInviteItem]


class PassengerShareSummaryResponse(BaseModel):
    ok: bool = True
    trip_id: str
    destination: str
    passenger_id: str
    passenger_name: str
    deposit_share_cents: int
    agency_payment_url: Optional[str] = None
    payment_instructions: Optional[str] = None
    status: str
    collected_preferences: Dict[str, Any] = Field(default_factory=dict)


class PassengerPayRequest(BaseModel):
    payment_reference: Optional[str] = None
    dietary_requirements: Optional[str] = None
    room_preference: Optional[str] = None
    passport_country: Optional[str] = None


class ManualOverrideRequest(BaseModel):
    trip_id: str
    passenger_id: str
    status: str  # CONFIRMED, WAIVED, UNPAID, NOTIFIED_PAID
    advisor_note: Optional[str] = None


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


@router.post("/{trip_id}/invites", response_model=GroupInviteResponse)
def generate_group_invites(
    trip_id: str,
    body: GroupInviteRequest,
    x_agency_id: Optional[str] = Header(None, alias="X-Agency-ID"),
):
    """Generate passenger deposit invite links for a multi-passenger group trip."""
    agency_id = x_agency_id or TEST_AGENCY_ID
    trip = TripStore.get_trip_for_agency(trip_id, agency_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    passengers = body.passengers
    if not passengers:
        raise HTTPException(status_code=400, detail="Must provide at least one passenger")

    passenger_count = len(passengers)
    total_cents = body.total_deposit_cents or 0
    per_passenger_cents = total_cents // passenger_count if passenger_count > 0 else 0

    group_state = trip.get("group_booking", {}) or {}
    invites_list = []
    invites_response = []

    for idx, p in enumerate(passengers):
        passenger_id = f"p_{idx + 1}_{secrets.token_hex(4)}"
        raw_token = f"grp_{secrets.token_urlsafe(32)}"
        token_hash = _hash_token(raw_token)
        share_cents = p.custom_share_cents if p.custom_share_cents is not None else per_passenger_cents

        item = {
            "passenger_id": passenger_id,
            "name": p.name,
            "email": p.email,
            "token_hash": token_hash,
            "token_hash_prefix": token_hash[:8],
            "deposit_share_cents": share_cents,
            "status": "UNPAID",
            "preferences": {},
            "payment_reference": None,
        }
        invites_list.append(item)

        web_url = f"{FRONTEND_PUBLIC_URL.rstrip('/')}/g/{raw_token}"
        invites_response.append(
            PassengerInviteItem(
                passenger_id=passenger_id,
                name=p.name,
                email=p.email,
                token=raw_token,
                web_url=web_url,
                deposit_share_cents=share_cents,
                status="UNPAID",
            )
        )

    group_state.update(
        {
            "total_deposit_cents": total_cents,
            "agency_payment_url": body.agency_payment_url,
            "payment_instructions": body.payment_instructions,
            "invites": invites_list,
        }
    )

    trip["group_booking"] = group_state
    TripStore.save_trip(trip, agency_id=agency_id)

    AuditStore.log_event(
        event_type="group_invites_generated",
        user_id=agency_id,
        details={
            "trip_id": trip_id,
            "passenger_count": passenger_count,
            "total_deposit_cents": total_cents,
            "has_agency_payment_url": bool(body.agency_payment_url),
        },
    )

    return GroupInviteResponse(
        ok=True,
        trip_id=trip_id,
        total_deposit_cents=total_cents,
        passenger_count=passenger_count,
        deposit_per_passenger_cents=per_passenger_cents,
        agency_payment_url=body.agency_payment_url,
        payment_instructions=body.payment_instructions,
        passenger_invites=invites_response,
    )


@router.get("/token/{token}", response_model=PassengerShareSummaryResponse)
def get_passenger_share_by_token(token: str):
    """Public unauthenticated lookup for a group passenger's deposit share portal."""
    matched_trip = TripStore.get_trip_by_group_token(token)
    if not matched_trip:
        raise HTTPException(status_code=404, detail="Invalid or expired group invite link")

    token_hash = _hash_token(token)
    gb = matched_trip.get("group_booking", {}) or {}
    invites = gb.get("invites", [])
    matched_invite = next(
        (inv for inv in invites if inv.get("token_hash") == token_hash or inv.get("raw_token") == token),
        None,
    )

    if not matched_invite:
        raise HTTPException(status_code=404, detail="Invalid or expired group invite link")

    packet = matched_trip.get("packet", {}) or {}
    destination = packet.get("destination") or matched_trip.get("destination") or "Travel Destination"

    return PassengerShareSummaryResponse(
        ok=True,
        trip_id=matched_trip["id"],
        destination=destination,
        passenger_id=matched_invite["passenger_id"],
        passenger_name=matched_invite["name"],
        deposit_share_cents=matched_invite.get("deposit_share_cents", 0),
        agency_payment_url=gb.get("agency_payment_url"),
        payment_instructions=gb.get("payment_instructions"),
        status=matched_invite.get("status", "UNPAID"),
        collected_preferences=matched_invite.get("preferences", {}),
    )


@router.post("/token/{token}/pay-share")
def notify_passenger_pay_share(token: str, body: PassengerPayRequest):
    """Public unauthenticated endpoint for attendee to record preferences & notify payment sent."""
    matched_trip = TripStore.get_trip_by_group_token(token)
    if not matched_trip:
        raise HTTPException(status_code=404, detail="Invalid or expired group invite link")

    token_hash = _hash_token(token)
    gb = matched_trip.get("group_booking", {}) or {}
    invites = gb.get("invites", [])
    matched_invite = next(
        (inv for inv in invites if inv.get("token_hash") == token_hash or inv.get("raw_token") == token),
        None,
    )

    if not matched_invite:
        raise HTTPException(status_code=404, detail="Invalid or expired group invite link")

    agency_id = matched_trip.get("agency_id", TEST_AGENCY_ID)

    matched_invite["status"] = "NOTIFIED_PAID"
    matched_invite["payment_reference"] = body.payment_reference

    prefs = matched_invite.setdefault("preferences", {})
    if body.dietary_requirements:
        prefs["dietary_requirements"] = body.dietary_requirements
    if body.room_preference:
        prefs["room_preference"] = body.room_preference
    if body.passport_country:
        prefs["passport_country"] = body.passport_country

    TripStore.save_trip(matched_trip, agency_id=agency_id)

    AuditStore.log_event(
        event_type="group_share_notified_paid",
        user_id=agency_id,
        details={
            "trip_id": matched_trip["id"],
            "passenger_id": matched_invite["passenger_id"],
            "token_hash_prefix": token_hash[:8],
            "has_payment_ref": bool(body.payment_reference),
        },
    )

    return {
        "ok": True,
        "message": "Payment notification and preferences received by agency.",
        "passenger_id": matched_invite["passenger_id"],
        "status": "NOTIFIED_PAID",
    }


@router.post("/{trip_id}/manual-override")
def manual_advisor_override_share(
    trip_id: str,
    body: ManualOverrideRequest,
    x_agency_id: Optional[str] = Header(None, alias="X-Agency-ID"),
):
    """Advisor endpoint to manually confirm, waive, or update a passenger's share status."""
    agency_id = x_agency_id or TEST_AGENCY_ID
    trip = TripStore.get_trip_for_agency(trip_id, agency_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    gb = trip.get("group_booking", {}) or {}
    invites = gb.get("invites", [])
    matched_invite = next((inv for inv in invites if inv.get("passenger_id") == body.passenger_id), None)

    if not matched_invite:
        raise HTTPException(status_code=404, detail=f"Passenger {body.passenger_id} not found in group")

    valid_statuses = ("CONFIRMED", "WAIVED", "UNPAID", "NOTIFIED_PAID")
    if body.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Status must be one of {valid_statuses}")

    old_status = matched_invite.get("status")
    matched_invite["status"] = body.status
    if body.advisor_note:
        matched_invite["advisor_note"] = body.advisor_note

    # Check if all invites in group are now satisfied (CONFIRMED or WAIVED)
    all_satisfied = all(inv.get("status") in ("CONFIRMED", "WAIVED") for inv in invites)
    gb["all_satisfied"] = all_satisfied

    TripStore.save_trip(trip, agency_id=agency_id)

    AuditStore.log_event(
        event_type="group_share_manual_override",
        user_id=agency_id,
        details={
            "trip_id": trip_id,
            "passenger_id": body.passenger_id,
            "old_status": old_status,
            "new_status": body.status,
            "all_satisfied": all_satisfied,
        },
    )

    return {
        "ok": True,
        "trip_id": trip_id,
        "passenger_id": body.passenger_id,
        "status": body.status,
        "all_group_shares_satisfied": all_satisfied,
    }
