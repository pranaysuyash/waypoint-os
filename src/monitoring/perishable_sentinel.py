"""
src/monitoring/perishable_sentinel.py — Perishable Timers & Expiry Sentinel (Finding F-14).

Monitors time-sensitive travel perishables to prevent catastrophic drops and financial loss:
1. Visa Submission & Biometric Deadlines (D-30 / D-15 embassy cutoff)
2. Airline Ticketing Time Limits (TTL / ADM penalty avoidance)
3. Travel Insurance 14-Day Pre-Existing Condition & CFAR Waiver Windows
4. Supplier Deposit & Final Balance Payment Milestones
5. Hotel Free-Cancellation Penalty Cutoffs
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional


class PerishableCategory(str, Enum):
    VISA_APPOINTMENT = "VISA_APPOINTMENT"
    AIRLINE_TICKETING_TTL = "AIRLINE_TICKETING_TTL"
    INSURANCE_CFAR_WAIVER_14D = "INSURANCE_CFAR_WAIVER_14D"
    SUPPLIER_PAYMENT_BALANCE = "SUPPLIER_PAYMENT_BALANCE"
    HOTEL_CANCELLATION_CUTOFF = "HOTEL_CANCELLATION_CUTOFF"


class PerishableUrgency(str, Enum):
    HEALTHY = "HEALTHY"                     # > 48 hours remaining
    EXPIRING_SOON = "EXPIRING_SOON"         # 12 to 48 hours remaining
    CRITICAL_URGENT = "CRITICAL_URGENT"     # < 12 hours remaining
    EXPIRED_LAPSED = "EXPIRED_LAPSED"       # Deadline passed


@dataclass(slots=True)
class PerishableItem:
    item_id: str
    trip_id: str
    traveler_name: str
    category: PerishableCategory
    title: str
    deadline_iso: str
    financial_exposure_usd: float = 0.0
    action_url: Optional[str] = None


@dataclass(slots=True)
class PerishableAuditStatus:
    item_id: str
    trip_id: str
    traveler_name: str
    category: PerishableCategory
    title: str
    deadline_iso: str
    hours_remaining: float
    urgency: PerishableUrgency
    financial_exposure_usd: float
    action_required: str


@dataclass(slots=True)
class PerishableSentinelSummary:
    total_tracked_items: int
    critical_urgent_count: int
    expiring_soon_count: int
    expired_count: int
    total_at_risk_exposure_usd: float
    items: List[PerishableAuditStatus] = field(default_factory=list)


class PerishableSentinel:
    """
    Central operational monitor for dated travel perishables (F-14).
    """

    @classmethod
    def audit_perishables(
        cls,
        items: List[PerishableItem],
        now_dt: Optional[datetime] = None,
    ) -> PerishableSentinelSummary:
        now = now_dt or datetime.now(timezone.utc)
        results: List[PerishableAuditStatus] = []

        crit_count = 0
        soon_count = 0
        expired_count = 0
        total_exposure = 0.0

        for item in items:
            try:
                deadline = datetime.fromisoformat(item.deadline_iso.replace("Z", "+00:00"))
            except ValueError:
                deadline = now

            diff_seconds = (deadline - now).total_seconds()
            hours_remaining = round(diff_seconds / 3600.0, 1)

            if hours_remaining <= 0:
                urgency = PerishableUrgency.EXPIRED_LAPSED
                action = "🚨 DEADLINE EXPIRED. Assess penalty exposure and file emergency supplier waiver if applicable."
                expired_count += 1
                total_exposure += item.financial_exposure_usd
            elif hours_remaining <= 12.0:
                urgency = PerishableUrgency.CRITICAL_URGENT
                action = f"🔥 CRITICAL: Less than {hours_remaining:.1f}h remaining! Execute immediate payment or ticket issuance."
                crit_count += 1
                total_exposure += item.financial_exposure_usd
            elif hours_remaining <= 48.0:
                urgency = PerishableUrgency.EXPIRING_SOON
                action = f"⚠️ URGENT: {hours_remaining:.1f}h remaining. Confirm traveler verification or issue payment."
                soon_count += 1
                total_exposure += item.financial_exposure_usd
            else:
                urgency = PerishableUrgency.HEALTHY
                action = f"✅ On schedule ({hours_remaining:.1f}h remaining)."

            results.append(
                PerishableAuditStatus(
                    item_id=item.item_id,
                    trip_id=item.trip_id,
                    traveler_name=item.traveler_name,
                    category=item.category,
                    title=item.title,
                    deadline_iso=item.deadline_iso,
                    hours_remaining=hours_remaining,
                    urgency=urgency,
                    financial_exposure_usd=item.financial_exposure_usd,
                    action_required=action,
                )
            )

        # Sort with most urgent on top
        results.sort(key=lambda x: x.hours_remaining)

        return PerishableSentinelSummary(
            total_tracked_items=len(items),
            critical_urgent_count=crit_count,
            expiring_soon_count=soon_count,
            expired_count=expired_count,
            total_at_risk_exposure_usd=round(total_exposure, 2),
            items=results,
        )
