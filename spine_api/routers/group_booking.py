"""
spine_api/routers/group_booking.py — Group Multi-Payer Split Deposit & Passenger Collection Engine.

Provides agency-first multi-passenger deposit splitting, custom payment link distribution,
public attendee preference/payment notification portal, and manual advisor status override controls.
"""

import os
import secrets
import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException

from spine_api.core.auth import get_current_agency_id
from spine_api.persistence import AuditStore, TripStore

router = APIRouter(prefix="/api/v1/group", tags=["Group Booking"])

FRONTEND_PUBLIC_URL = os.environ.get("FRONTEND_PUBLIC_URL", "https://waypoint-os.com")


class PassengerInviteSpec(BaseModel):
    name: str
    email: Optional[str] = None
    custom_share_cents: Optional[int] = None
    share_note: Optional[str] = None  # itemization line (Chloe JTBD: single-supplement etc.)


class ScheduleMilestoneSpec(BaseModel):
    label: str
    due_at: str  # ISO-8601 timestamp
    amount_cents: Optional[int] = Field(default=None, ge=0)


class GroupInviteRequest(BaseModel):
    trip_id: str
    passengers: List[PassengerInviteSpec]
    total_deposit_cents: Optional[int] = Field(default=0, ge=0)
    agency_payment_url: Optional[str] = None
    payment_instructions: Optional[str] = None
    schedule: Optional[List[ScheduleMilestoneSpec]] = None  # FND-0409: deposit/final milestones


class ScheduleUpdateRequest(BaseModel):
    milestones: List[ScheduleMilestoneSpec]


class RecordPaymentRequest(BaseModel):
    passenger_id: str
    amount_cents: int = Field(gt=0)
    method: str = "BANK_TRANSFER"  # BANK_TRANSFER | UPI | CARD | CASH | OTHER
    reference: Optional[str] = None
    note: Optional[str] = None


class LogReminderRequest(BaseModel):
    passenger_id: str
    channel: str = "operator_manual"  # honest floor: operator sends over their own channel
    note: Optional[str] = None


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
    # FND-0409 additive: money truth + schedule for the traveler portal.
    # Tracking-only (ADR-008) — no card capture, ever; the portal shows what
    # the agency recorded, never implying a charge happened here.
    share_note: Optional[str] = None
    paid_cents: int = 0
    outstanding_cents: int = 0
    settlement: str = "unpaid"  # paid | partial | unpaid
    schedule: List[Dict[str, Any]] = Field(default_factory=list)


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


# ---------------------------------------------------------------------------
# FND-0409 derived helpers — single source of the per-passenger money view.
# ---------------------------------------------------------------------------


def _paid_cents_for(invite: dict) -> int:
    """Sum recorded observed payments for one invite (tracking-only)."""
    return int(sum(int(p.get("amount_cents", 0)) for p in (invite.get("recorded_payments") or [])))


def _invite_operator_view(invite: dict, group_state: dict) -> dict:
    """Full operator view of one passenger share: consent status + money truth
    + derived schedule statuses + reminder history."""
    from spine_api.services.group_payments import derive_milestone_status, derive_settlement

    share_cents = int(invite.get("deposit_share_cents", 0))
    paid_cents = _paid_cents_for(invite)
    settlement = derive_settlement(share_cents, paid_cents, invite.get("status", "UNPAID"))
    return {
        "passenger_id": invite.get("passenger_id"),
        "name": invite.get("name"),
        "email": invite.get("email"),
        "share_note": invite.get("share_note"),
        "deposit_share_cents": share_cents,
        "paid_cents": paid_cents,
        "outstanding_cents": max(0, share_cents - paid_cents),
        "settlement": settlement,
        "status": invite.get("status", "UNPAID"),
        "advisor_note": invite.get("advisor_note"),
        "token_hash_prefix": invite.get("token_hash_prefix"),
        "schedule": [
            {
                "label": m.get("label", "Payment"),
                "due_at": m.get("due_at"),
                "amount_cents": m.get("amount_cents"),
                "status": derive_milestone_status(m, settled=settlement == "paid"),
            }
            for m in (invite.get("schedule") or [])
        ],
        "recorded_payments": invite.get("recorded_payments") or [],
        "reminders": invite.get("reminders") or [],
    }


def _reminder_drafts_for(trip: dict) -> list:
    """Derive reminder drafts for outstanding shares (FND-0409).

    Honest floor: drafts are copyable operator text — auto-dispatch is
    DP-04b-gated, so nothing sends itself. Drafts exist only when there is a
    real reason: an overdue/due-soon milestone, or an outstanding share on a
    scheduled group (no urgency language is fabricated without a due date).
    """
    from spine_api.services.group_payments import build_reminder_draft, derive_milestone_status, derive_settlement

    gb = trip.get("group_booking", {}) or {}
    packet = trip.get("packet", {}) or {}
    destination = packet.get("destination") or trip.get("destination") or "your group trip"
    drafts = []
    for invite in gb.get("invites", []):
        share_cents = int(invite.get("deposit_share_cents", 0))
        paid_cents = _paid_cents_for(invite)
        settlement = derive_settlement(share_cents, paid_cents, invite.get("status", "UNPAID"))
        if settlement == "paid":
            continue
        milestones = [
            {
                "label": m.get("label", "Payment"),
                "due_at": m.get("due_at"),
                "amount_cents": m.get("amount_cents"),
                "status": derive_milestone_status(m, settled=False),
            }
            for m in (invite.get("schedule") or [])
        ]
        urgent = [m for m in milestones if m["status"] in ("overdue", "due_soon")]
        if not urgent and not milestones:
            continue  # no schedule → no fabricated urgency
        due_label = (
            f"{urgent[0]['status'].replace('_', ' ')}: {urgent[0]['label']}"
            if urgent
            else "payment due per schedule"
        )
        outstanding = max(0, share_cents - paid_cents)
        drafts.append(
            {
                "passenger_id": invite.get("passenger_id"),
                "passenger_name": invite.get("name"),
                "outstanding_cents": outstanding,
                "trigger": urgent[0]["status"] if urgent else "unscheduled_outstanding",
                "due_label": due_label,
                "draft_text": build_reminder_draft(
                    traveler_name=invite.get("name") or "there",
                    destination=destination,
                    amount_cents=outstanding,
                    currency="INR",
                    due_label=due_label,
                    payment_instructions=gb.get("payment_instructions"),
                    payment_url=gb.get("agency_payment_url"),
                ),
                "dispatch_channel": "operator_manual",  # DP-04b gate: no auto-send
            }
        )
    return drafts


@router.post("/{trip_id}/invites", response_model=GroupInviteResponse)
async def generate_group_invites(
    trip_id: str,
    body: GroupInviteRequest,
    agency_id: str = Depends(get_current_agency_id),
):
    """Generate passenger deposit invite links for a multi-passenger group trip."""
    trip = TripStore.get_trip_for_agency(trip_id, agency_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    passengers = body.passengers
    if not passengers:
        raise HTTPException(status_code=400, detail="Must provide at least one passenger")

    passenger_count = len(passengers)
    total_cents = body.total_deposit_cents or 0

    # FND-0409: money truth — shares must sum exactly to the total. The
    # remainder goes to the first equal share instead of vanishing
    # (compute_equal_split_cents), and custom itemized shares are validated
    # so the ledger can never disagree with the deposit total.
    from spine_api.services.group_payments import compute_equal_split_cents

    if total_cents > 0:
        share_amounts = compute_equal_split_cents(total_cents, passenger_count)
        custom_used = False
        for idx, p in enumerate(passengers):
            if p.custom_share_cents is not None:
                share_amounts[idx] = p.custom_share_cents
                custom_used = True
        if custom_used and sum(share_amounts) != total_cents:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"Custom shares sum to {sum(share_amounts)} cents but the deposit "
                    f"total is {total_cents} cents — itemized shares must balance exactly."
                ),
            )
    else:
        share_amounts = [0] * passenger_count
    per_passenger_cents = share_amounts[0] if share_amounts else 0

    schedule_payload = (
        [
            {"label": m.label, "due_at": m.due_at, "amount_cents": m.amount_cents}
            for m in (body.schedule or [])
        ]
        or None
    )

    group_state = trip.get("group_booking", {}) or {}
    invites_list = []
    invites_response = []

    for idx, p in enumerate(passengers):
        passenger_id = f"p_{idx + 1}_{secrets.token_hex(4)}"
        raw_token = f"grp_{secrets.token_urlsafe(32)}"
        token_hash = _hash_token(raw_token)
        share_cents = share_amounts[idx]

        item: dict = {
            "passenger_id": passenger_id,
            "name": p.name,
            "email": p.email,
            "token_hash": token_hash,
            "token_hash_prefix": token_hash[:8],
            "deposit_share_cents": share_cents,
            "status": "UNPAID",
            "preferences": {},
            "payment_reference": None,
            # FND-0409 additive state (tracking-only, ADR-008):
            "share_note": p.share_note,
            "schedule": schedule_payload,
            "recorded_payments": [],  # [{amount_cents, method, reference, recorded_at, recorded_by, note}]
            "reminders": [],  # [{sent_at, channel, note, recorded_by}]
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

    # FND-0409: derived money truth + schedule for the traveler portal.
    # Clara constraint: minimum traveler PII — name, amounts, schedule,
    # status only. Email/phone and sibling shares never leave the agency.
    from spine_api.services.group_payments import derive_milestone_status, derive_settlement

    share_cents = int(matched_invite.get("deposit_share_cents", 0))
    paid_cents = _paid_cents_for(matched_invite)
    settlement = derive_settlement(share_cents, paid_cents, matched_invite.get("status", "UNPAID"))
    schedule_view = [
        {
            "label": m.get("label", "Payment"),
            "due_at": m.get("due_at"),
            "amount_cents": m.get("amount_cents"),
            "status": derive_milestone_status(m, settled=settlement == "paid"),
        }
        for m in (matched_invite.get("schedule") or [])
    ]

    return PassengerShareSummaryResponse(
        ok=True,
        trip_id=matched_trip["id"],
        destination=destination,
        passenger_id=matched_invite["passenger_id"],
        passenger_name=matched_invite["name"],
        deposit_share_cents=share_cents,
        agency_payment_url=gb.get("agency_payment_url"),
        payment_instructions=gb.get("payment_instructions"),
        status=matched_invite.get("status", "UNPAID"),
        collected_preferences=matched_invite.get("preferences", {}),
        share_note=matched_invite.get("share_note"),
        paid_cents=paid_cents,
        outstanding_cents=max(0, share_cents - paid_cents),
        settlement=settlement,
        schedule=schedule_view,
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

    # FND-0290: fail closed instead of silently attributing the redemption to
    # the legacy test agency. A matched invite whose trip record lacks tenant
    # attribution is a data-integrity fault, not a payable redemption.
    agency_id = matched_trip.get("agency_id")
    if not agency_id:
        raise HTTPException(
            status_code=409,
            detail="Group invite record lacks agency attribution; redemption blocked. Contact support.",
        )

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

    # Work-intake classification (map §2.1 group_share door): a co-traveler's
    # share decision is demand-side work (money tracked, never moved).
    try:
        from spine_api.services.work_intake import classify_and_record

        classify_and_record(
            "group_share",
            agency_id=agency_id,
            text=None,
            trip_id=matched_trip["id"],
            channel="group_share_link",
            actor="group_passenger",
            money_touch=True,
        )
    except Exception:
        pass

    return {
        "ok": True,
        "message": "Payment notification and preferences received by agency.",
        "passenger_id": matched_invite["passenger_id"],
        "status": "NOTIFIED_PAID",
    }


@router.post("/{trip_id}/manual-override")
async def manual_advisor_override_share(
    trip_id: str,
    body: ManualOverrideRequest,
    agency_id: str = Depends(get_current_agency_id),
):
    """Advisor endpoint to manually confirm, waive, or update a passenger's share status."""
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


# ---------------------------------------------------------------------------
# FND-0409 — Group payment collection: schedules, observed-payment ledger,
# reminder drafts + logged sends. Tracking-only posture (ADR-008): recorded
# payments are OBSERVED money (bank transfer/UPI/cash the advisor confirms),
# never charges. Auto-dispatch of reminders is DP-04b-gated — the honest
# floor is operator-copyable drafts plus a logged-send audit trail.
# ---------------------------------------------------------------------------


@router.get("/{trip_id}", response_model=Dict[str, Any])
def get_group_collection_summary(trip_id: str, agency_id: str = Depends(get_current_agency_id)):
    """Operator summary for one trip's group collection: per-passenger money
    truth, derived schedule statuses, reminder drafts."""
    trip = TripStore.get_trip_for_agency(trip_id, agency_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    gb = trip.get("group_booking", {}) or {}
    invites = gb.get("invites", [])
    total_cents = int(gb.get("total_deposit_cents", 0))
    outstanding = sum(
        max(0, int(inv.get("deposit_share_cents", 0)) - _paid_cents_for(inv)) for inv in invites
    )
    return {
        "ok": True,
        "trip_id": trip_id,
        "destination": (trip.get("packet", {}) or {}).get("destination") or trip.get("destination"),
        "total_deposit_cents": total_cents,
        "collected_cents": max(0, total_cents - outstanding),
        "outstanding_cents": outstanding,
        "all_satisfied": gb.get("all_satisfied", False),
        "agency_payment_url": gb.get("agency_payment_url"),
        "payment_instructions": gb.get("payment_instructions"),
        "passengers": [_invite_operator_view(inv, gb) for inv in invites],
        "reminder_drafts": _reminder_drafts_for(trip),
    }


@router.post("/{trip_id}/schedule")
def set_group_schedule(trip_id: str, body: ScheduleUpdateRequest, agency_id: str = Depends(get_current_agency_id)):
    """Set/replace the group payment schedule applied to every invite
    (FND-0409). Per-passenger itemization lives on custom share amounts +
    share notes; the schedule is the group-wide deadline track."""
    trip = TripStore.get_trip_for_agency(trip_id, agency_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    gb = trip.get("group_booking", {}) or {}
    invites = gb.get("invites", [])
    if not invites:
        raise HTTPException(status_code=409, detail="No group invites exist for this trip yet")

    schedule_payload = [
        {"label": m.label, "due_at": m.due_at, "amount_cents": m.amount_cents}
        for m in body.milestones
    ]
    for inv in invites:
        inv["schedule"] = schedule_payload
    gb["schedule_set_at"] = datetime.now(timezone.utc).isoformat()

    trip["group_booking"] = gb
    TripStore.save_trip(trip, agency_id=agency_id)

    AuditStore.log_event(
        event_type="group_schedule_set",
        user_id=agency_id,
        details={"trip_id": trip_id, "milestone_count": len(schedule_payload)},
    )
    return {"ok": True, "trip_id": trip_id, "milestones": schedule_payload}


@router.post("/{trip_id}/record-payment")
def record_group_payment(trip_id: str, body: RecordPaymentRequest, agency_id: str = Depends(get_current_agency_id)):
    """Record an OBSERVED payment against one passenger's share (FND-0409).

    Tracking-only (ADR-008): this logs money the agency actually received
    over its own channels (bank transfer/UPI/cash). It never charges anything.
    The append is one additive write — a payment reference is stored with the
    movement so double-recording is detectable, but unlike the payout ledger
    no unique constraint is enforced (cash payments may legitimately share a
    day-reference; the operator owns the truth here)."""
    from datetime import datetime as _dt

    trip = TripStore.get_trip_for_agency(trip_id, agency_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    gb = trip.get("group_booking", {}) or {}
    invites = gb.get("invites", [])
    matched = next((inv for inv in invites if inv.get("passenger_id") == body.passenger_id), None)
    if not matched:
        raise HTTPException(status_code=404, detail=f"Passenger {body.passenger_id} not found in group")

    movement = {
        "amount_cents": body.amount_cents,
        "method": body.method,
        "reference": body.reference,
        "note": body.note,
        "recorded_at": _dt.now(timezone.utc).isoformat(),
        "recorded_by": agency_id,
    }
    matched.setdefault("recorded_payments", []).append(movement)

    paid = _paid_cents_for(matched)
    if paid >= int(matched.get("deposit_share_cents", 0)) and matched.get("status") == "UNPAID":
        # Observed money at/above share with no traveler notification yet —
        # the consent status stays advisor-controlled, but reflect receipt so
        # the operator sees money truth without overriding their machine.
        matched["status"] = "NOTIFIED_PAID"

    trip["group_booking"] = gb
    TripStore.save_trip(trip, agency_id=agency_id)

    AuditStore.log_event(
        event_type="group_payment_recorded",
        user_id=agency_id,
        details={
            "trip_id": trip_id,
            "passenger_id": body.passenger_id,
            "amount_cents": body.amount_cents,
            "method": body.method,
            "paid_total_cents": paid,
        },
    )
    return {
        "ok": True,
        "trip_id": trip_id,
        "passenger_id": body.passenger_id,
        "paid_cents": paid,
        "outstanding_cents": max(0, int(matched.get("deposit_share_cents", 0)) - paid),
        "movement": movement,
    }


@router.get("/{trip_id}/reminder-drafts")
def get_group_reminder_drafts(trip_id: str, agency_id: str = Depends(get_current_agency_id)):
    """Derived reminder drafts for outstanding shares (FND-0409). Copyable
    operator text; ``dispatch_channel`` is always ``operator_manual`` until a
    dispatch channel is wired (DP-04b owner gate)."""
    trip = TripStore.get_trip_for_agency(trip_id, agency_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    return {"ok": True, "trip_id": trip_id, "drafts": _reminder_drafts_for(trip)}


@router.post("/{trip_id}/log-reminder")
def log_group_reminder(trip_id: str, body: LogReminderRequest, agency_id: str = Depends(get_current_agency_id)):
    """Log that the operator sent a reminder over their own channel
    (FND-0409). The system tracks the send; it does not perform it."""
    from datetime import datetime as _dt

    trip = TripStore.get_trip_for_agency(trip_id, agency_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    gb = trip.get("group_booking", {}) or {}
    invites = gb.get("invites", [])
    matched = next((inv for inv in invites if inv.get("passenger_id") == body.passenger_id), None)
    if not matched:
        raise HTTPException(status_code=404, detail=f"Passenger {body.passenger_id} not found in group")

    entry = {
        "sent_at": _dt.now(timezone.utc).isoformat(),
        "channel": body.channel,
        "note": body.note,
        "recorded_by": agency_id,
    }
    matched.setdefault("reminders", []).append(entry)
    trip["group_booking"] = gb
    TripStore.save_trip(trip, agency_id=agency_id)

    AuditStore.log_event(
        event_type="group_reminder_logged",
        user_id=agency_id,
        details={"trip_id": trip_id, "passenger_id": body.passenger_id, "channel": body.channel},
    )
    return {"ok": True, "trip_id": trip_id, "passenger_id": body.passenger_id, "reminder": entry}
