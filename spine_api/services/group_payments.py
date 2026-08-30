"""
spine_api.services.group_payments — Multi-traveler payment splitting and escrow ledger.

Allows travel organizers to split package costs across multiple travelers,
generate personalized payment URLs, and track live settlement progress.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional


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
