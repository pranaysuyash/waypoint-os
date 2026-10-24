"""Evidence projections for commercial outcomes and first useful agency work.

No producer writes are performed here. Budgets, internal review, preview
fulfillment, customer collections, and agency earnings have distinct meanings.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation, localcontext
from math import isfinite
from typing import Any

from babel.numbers import get_currency_precision, list_currencies

from src.analytics.models import ActivationSummary, CurrencyTotal, MonetaryMeasure

_KNOWN_CURRENCIES = frozenset(list_currencies()) - {"XXX", "XTS"}
_CLOSED_PIPELINE = frozenset({"booked", "change_requested", "in_trip", "returned", "completed", "delivered", "cancelled", "lost", "archived"})
_WAITING_FOR_DETAILS = frozenset({"incomplete", "needs_followup", "awaiting_customer_details"})


def record(value: Any) -> dict:
    return value if isinstance(value, dict) else {}


def parse_timestamp(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value.replace(tzinfo=value.tzinfo or timezone.utc)
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed.replace(tzinfo=parsed.tzinfo or timezone.utc)


def amount(value: Any) -> Decimal | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None
    return parsed if parsed.is_finite() and parsed >= 0 and isfinite(float(parsed)) else None


def currency(value: Any) -> str | None:
    code = value.strip().upper() if isinstance(value, str) else ""
    return code if code in _KNOWN_CURRENCIES else None


def budget(trip: dict) -> tuple[Any, Any]:
    """Read the canonical submission overlay and packet fact shapes.

    Unlike the inbox's integer display helper, preserve recorded decimals and
    an absent currency. A known numeric budget is never an implied USD amount.
    """
    submission = record(record(trip.get("raw_input")).get("submission"))
    structured = record(submission.get("structured_json"))
    packet = record(trip.get("extracted")) or record(trip.get("packet"))
    facts = record(packet.get("facts"))
    packet_budget = record(packet.get("budget"))
    fact_budget = record(facts.get("budget"))
    recorded_currency = (
        record(facts.get("budget_currency")).get("value")
        or packet_budget.get("currency")
        or record(record(packet.get("trip_metadata")).get("budget")).get("currency")
    )
    for source in (structured, submission):
        if source.get("budget") is not None:
            raw_budget = source["budget"]
            if isinstance(raw_budget, dict):
                return raw_budget.get("value"), raw_budget.get("currency") or source.get("currency") or recorded_currency
            return raw_budget, source.get("budget_currency") or source.get("currency") or recorded_currency
    if "value" in fact_budget:
        return fact_budget["value"], recorded_currency or fact_budget.get("currency")
    if "value" in packet_budget:
        return packet_budget["value"], packet_budget.get("currency") or recorded_currency
    metadata_budget = record(record(packet.get("trip_metadata")).get("budget"))
    if "value" in metadata_budget:
        return metadata_budget["value"], metadata_budget.get("currency") or recorded_currency
    if packet.get("budget") is not None and not isinstance(packet.get("budget"), dict):
        return packet["budget"], recorded_currency
    if trip.get("budget") is not None:
        return trip["budget"], trip.get("currency") or recorded_currency
    return None, recorded_currency


def has_real_booking(trip: dict) -> bool:
    """A state label or synthetic provider result is not a successful receipt."""
    receipt = record(trip.get("booking_confirmation"))
    return bool(
        receipt.get("reality_tier") == "real"
        and receipt.get("provider_connected") is True
        and receipt.get("fulfillment_provider_key")
        and parse_timestamp(receipt.get("fulfilled_at")) is not None
        and (receipt.get("pnr_locator") or record(receipt.get("sql_confirmation")).get("id"))
    )


def is_open_pipeline(trip: dict) -> bool:
    return trip.get("status") not in _CLOSED_PIPELINE and not has_real_booking(trip)


def in_window(value: Any, start: datetime | None, end: datetime | None) -> bool:
    if start is None and end is None:
        return True
    timestamp = parse_timestamp(value)
    return timestamp is not None and (start is None or timestamp >= start) and (end is None or timestamp <= end)


def analysis_window(
    period: str,
    *,
    now: datetime | None = None,
    start: Any = None,
    end: Any = None,
) -> tuple[datetime | None, datetime]:
    """UTC inclusive event window; custom ranges require explicit aware bounds."""
    now = now or datetime.now(timezone.utc)
    if period == "all":
        return None, now
    if period in {"7d", "30d", "90d"}:
        return now - timedelta(days=int(period[:-1])), now
    if period == "mtd":
        return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0), now
    if period == "ytd":
        return now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0), now
    if period == "custom":
        first, last = parse_timestamp(start), parse_timestamp(end)
        if first is None or last is None or first > last or last > now:
            raise ValueError("Custom range requires valid start/end timestamps, start <= end, and end <= now.")
        return first, last
    raise ValueError("Unsupported range; use 7d, 30d, 90d, mtd, ytd, all, or custom with start/end.")


@dataclass(slots=True)
class MoneyAccumulator:
    """One linear pass with Decimal arithmetic and explicit evidence gaps."""

    totals: dict[str, Decimal] = field(default_factory=dict)
    trip_counts: dict[str, int] = field(default_factory=dict)
    evidence_count: int = 0
    missing_amount: int = 0
    missing_currency: int = 0
    excluded_preview: int = 0

    def add(self, raw_amount: Any, raw_currency: Any, *, multiplier: Decimal = Decimal(1)) -> None:
        value, code = amount(raw_amount), currency(raw_currency)
        if value is None:
            self.missing_amount += 1
        if code is None:
            self.missing_currency += 1
        if value is None or code is None:
            return
        previous = self.totals.get(code, Decimal(0))
        # Preserve the recorded precision even when small fractional values
        # are added to large totals; the process Decimal context is not a
        # source contract and must not silently round source evidence.
        with localcontext() as context:
            context.prec = max(28, len(previous.as_tuple().digits) + abs(previous.as_tuple().exponent), len(value.as_tuple().digits) + abs(value.as_tuple().exponent)) + len(multiplier.as_tuple().digits) + 4
            self.totals[code] = previous + value * multiplier
        self.trip_counts[code] = self.trip_counts.get(code, 0) + 1
        self.evidence_count += 1

    def result(self, reason: str) -> MonetaryMeasure:
        gap = self.missing_amount or self.missing_currency
        return MonetaryMeasure(
            availability="partial" if self.totals and gap else "available" if self.totals else "unavailable",
            totals=[CurrencyTotal(currency=code, amount=float(value), amountDecimal=str(value), minorUnitDigits=get_currency_precision(code), tripCount=self.trip_counts[code]) for code, value in sorted(self.totals.items())],
            evidenceTripCount=self.evidence_count,
            missingAmountTripCount=self.missing_amount,
            missingCurrencyTripCount=self.missing_currency,
            excludedPreviewTripCount=self.excluded_preview,
            reason=reason,
        )


def single_currency_scalar(measure: MonetaryMeasure) -> tuple[float | None, str | None]:
    if measure.availability != "available" or len(measure.totals) != 1:
        return None, None
    total = measure.totals[0]
    return total.amount, total.currency


def activation_summary(trips: list[dict]) -> ActivationSummary:
    inquiries = [trip for trip in trips if trip.get("id") or trip.get("trip_id")]
    actionable = [trip for trip in inquiries if trip.get("status") not in {"cancelled", "lost", "archived"}]

    def needs_details(trip: dict) -> bool:
        validation = record(trip.get("validation"))
        return bool(trip.get("status") in _WAITING_FOR_DETAILS or trip.get("missing_fields") or validation.get("missing_fields"))

    def approved(trip: dict) -> bool:
        analytics = record(trip.get("analytics"))
        review = record(analytics.get("review_metadata"))
        packet = record(trip.get("extracted")) or record(trip.get("packet"))
        return bool(
            packet and not needs_details(trip)
            and analytics.get("review_status") == "approved"
            and review.get("owner_approved") is True
            and review.get("reviewed_by")
            and parse_timestamp(review.get("reviewed_at")) is not None
        )

    def quote_ready(trip: dict) -> bool:
        readiness = record(record(trip.get("validation")).get("readiness"))
        detail = record(record(readiness.get("tiers")).get("quote_ready"))
        return detail.get("ready") is True

    waiting = [trip for trip in actionable if needs_details(trip)]
    reviewed = [trip for trip in inquiries if approved(trip)]
    ready = [trip for trip in actionable if not needs_details(trip) and (approved(trip) or quote_ready(trip))]
    next_trip = (waiting or actionable or inquiries or [None])[0]
    return ActivationSummary(
        inquiryCount=len(inquiries),
        needsDetailsCount=len(waiting),
        readyBriefCount=len(ready),
        reviewedBriefCount=len(reviewed),
        planningStartedCount=sum(trip.get("status") in {"assigned", "in_progress"} for trip in inquiries),
        firstValueAchieved=bool(reviewed),
        nextAction="continue_work" if reviewed else "resolve_details" if waiting else "review_brief" if actionable else "add_inquiry",
        nextTripId=str(next_trip.get("id") or next_trip.get("trip_id")) if next_trip else None,
    )
