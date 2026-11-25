"""
spine_api.services.group_payments — Multi-traveler payment splitting and escrow ledger.

Canonical domain math for group payment collection (FND-0409). The WIRED
surface is ``spine_api.routers.group_booking`` (invite links, traveler
portal, advisor overrides, schedules, reminders) which persists per-trip
state through ``TripStore``; this module owns the pure split/settlement
math both the router and the in-memory preview consume, so the remainder
allocation and derived statuses exist in exactly one place.

Allows travel organizers to split package costs across multiple travelers,
generate personalized payment URLs, and track live settlement progress.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional


@dataclass(slots=True)
class TravelerPaymentShare:
    traveler_id: str
    name: str
    email: str
    share_amount_usd: float
    paid_amount_usd: float = 0.0
    status: str = "unpaid"  # "unpaid" | "partially_paid" | "paid"
    payment_link_token: str = ""
    paid_at: Optional[str] = None


@dataclass(slots=True)
class GroupPaymentSplit:
    trip_id: str
    total_package_usd: float
    split_mode: str  # "EQUAL" | "CUSTOM"
    shares: List[TravelerPaymentShare]
    total_paid_usd: float
    outstanding_balance_usd: float
    all_settled: bool


def create_group_payment_split(
    trip_id: str,
    total_package_usd: float,
    travelers: List[Dict[str, str]],  # [{"name": "...", "email": "..."}, ...]
    custom_amounts: Optional[Dict[str, float]] = None,
) -> GroupPaymentSplit:
    """
    Split trip total across travelers and generate payment tracking shares.
    """
    count = len(travelers)
    if count == 0:
        raise ValueError("Cannot split group payment with zero travelers.")

    shares: List[TravelerPaymentShare] = []
    split_mode = "CUSTOM" if custom_amounts else "EQUAL"

    if split_mode == "EQUAL":
        per_person = round(total_package_usd / count, 2)
        # Adjust remainder on first traveler to ensure exact sum
        remainder = round(total_package_usd - (per_person * count), 2)
        for i, t in enumerate(travelers):
            amt = per_person + (remainder if i == 0 else 0.0)
            token = f"pay_{trip_id}_{i+1}_{t['email'].split('@')[0]}"
            shares.append(
                TravelerPaymentShare(
                    traveler_id=f"trav_{i+1}",
                    name=t["name"],
                    email=t["email"],
                    share_amount_usd=amt,
                    paid_amount_usd=0.0,
                    status="unpaid",
                    payment_link_token=token,
                )
            )
    else:
        for i, t in enumerate(travelers):
            amt = custom_amounts.get(t["email"], 0.0)
            token = f"pay_{trip_id}_{i+1}_{t['email'].split('@')[0]}"
            shares.append(
                TravelerPaymentShare(
                    traveler_id=f"trav_{i+1}",
                    name=t["name"],
                    email=t["email"],
                    share_amount_usd=amt,
                    paid_amount_usd=0.0,
                    status="unpaid",
                    payment_link_token=token,
                )
            )

    return GroupPaymentSplit(
        trip_id=trip_id,
        total_package_usd=total_package_usd,
        split_mode=split_mode,
        shares=shares,
        total_paid_usd=0.0,
        outstanding_balance_usd=total_package_usd,
        all_settled=False,
    )


def record_traveler_payment(
    split: GroupPaymentSplit,
    payment_link_token: str,
    amount_paid_usd: float,
) -> GroupPaymentSplit:
    """
    Record an incoming payment against a traveler's payment share.
    """
    total_paid = 0.0
    for share in split.shares:
        if share.payment_link_token == payment_link_token:
            share.paid_amount_usd += amount_paid_usd
            if share.paid_amount_usd >= share.share_amount_usd:
                share.status = "paid"
                share.paid_at = datetime.now(timezone.utc).isoformat()
            else:
                share.status = "partially_paid"
        total_paid += share.paid_amount_usd

    split.total_paid_usd = round(total_paid, 2)
    split.outstanding_balance_usd = max(0.0, round(split.total_package_usd - total_paid, 2))
    split.all_settled = split.outstanding_balance_usd <= 0.0
    return split


# ---------------------------------------------------------------------------
# FND-0409 — cents-based domain math for the wired group_booking router.
# Tracking-only money posture (ADR-008): amounts are integer cents, the
# router persists state via TripStore, and nothing here moves money.
# Settlement derivation and schedule statuses intentionally live here so the
# router, the traveler portal payload, and any future backend agree on the
# same numbers.
# ---------------------------------------------------------------------------

DU_SOON_WINDOW_DAYS = 7

SETTLEMENT_PAID = "paid"
SETTLEMENT_PARTIAL = "partial"
SETTLEMENT_UNPAID = "unpaid"


def compute_equal_split_cents(total_cents: int, count: int) -> List[int]:
    """Split ``total_cents`` across ``count`` travelers exactly.

    The remainder (total % count) is spread one cent across the first
    travelers so the shares always sum to the total — the router's previous
    ``total // count`` silently lost cents on odd divisions (e.g. 100/3), a
    real money-truth defect absorbed here from the unwired preview math.
    """
    if count <= 0:
        raise ValueError("Cannot split group payment with zero travelers.")
    if total_cents < 0:
        raise ValueError("Total cannot be negative.")
    base = total_cents // count
    remainder = total_cents - base * count
    return [base + (1 if i < remainder else 0) for i in range(count)]


def derive_settlement(
    share_cents: int,
    paid_cents: int,
    invite_status: str,
) -> str:
    """Derive the money settlement state from recorded payments.

    Independent of the consent status machine (UNPAID/NOTIFIED_PAID/
    CONFIRMED/WAIVED): settlement tracks observed money (ADR-008
    tracking-only), consent tracks what the advisor has accepted. A waived
    share settles as ``paid`` — the group no longer needs the money.
    """
    if invite_status == "WAIVED" or paid_cents >= share_cents:
        return SETTLEMENT_PAID
    if paid_cents > 0:
        return SETTLEMENT_PARTIAL
    return SETTLEMENT_UNPAID


def derive_milestone_status(
    milestone: Dict[str, Any],
    settled: bool,
    now: Optional[datetime] = None,
) -> str:
    """Derive one schedule milestone's status for display and reminders.

    Milestones carry ``label``, ``due_at`` (ISO-8601) and optional
    ``amount_cents``. Status vocabulary: ``paid`` | ``overdue`` |
    ``due_soon`` | ``upcoming``. Invalid/missing due dates derive honestly
    as ``upcoming`` rather than fabricating urgency.
    """
    if settled:
        return "paid"
    due_raw = milestone.get("due_at")
    if not due_raw:
        return "upcoming"
    try:
        due = datetime.fromisoformat(str(due_raw).replace("Z", "+00:00"))
    except ValueError:
        return "upcoming"
    if due.tzinfo is None:
        due = due.replace(tzinfo=timezone.utc)
    current = now or datetime.now(timezone.utc)
    if due < current:
        return "overdue"
    if due <= current + timedelta(days=DU_SOON_WINDOW_DAYS):
        return "due_soon"
    return "upcoming"


def build_reminder_draft(
    traveler_name: str,
    destination: str,
    amount_cents: int,
    currency: str,
    due_label: str,
    payment_instructions: Optional[str],
    payment_url: Optional[str],
) -> str:
    """Build one polite reminder draft for an outstanding share.

    Honest floor: the draft is copyable text for the operator to send over
    their own channel — auto-dispatch is DP-04b-gated (no Meta credentials
    wired), so nothing here sends anything.
    """
    major = amount_cents // 100
    minor = amount_cents % 100
    amount_str = f"{currency} {major:,}.{minor:02d}"
    lines = [
        f"Hi {traveler_name}, a friendly reminder about your share for the "
        f"{destination} trip.",
        f"Outstanding amount: {amount_str} ({due_label}).",
    ]
    if payment_url:
        lines.append(f"You can review your share and payment details here: {payment_url}")
    if payment_instructions:
        lines.append(f"Payment instructions: {payment_instructions}")
    lines.append("Let us know once you've sent it and we'll confirm right away. Thank you!")
    return "\n".join(lines)
