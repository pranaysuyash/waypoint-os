from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional, Sequence

from spine_api.persistence import TripStore

PAYMENT_QUEUE_STATUSES = (
    "not_configured",
    "unknown",
    "overdue",
    "due_soon",
    "due_later",
    "paid_complete",
    "refund_in_progress",
)

PAYMENT_STATUSES = (
    "not_started",
    "deposit_paid",
    "partially_paid",
    "paid",
    "overdue",
    "waived",
    "refunded",
    "unknown",
)

REFUND_STATUSES = (
    "not_applicable",
    "not_requested",
    "pending_review",
    "approved",
    "processing",
    "paid",
    "rejected",
    "cancelled",
)

DUE_BUCKETS = (
    "none",
    "overdue",
    "due_0_3",
    "due_4_7",
    "due_8_14",
)


def _safe_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _parse_iso_date(value: Any) -> Optional[date]:
    if not value or not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _compute_balance_due(tracking: dict[str, Any]) -> Optional[float]:
    agreed_amount = _safe_float(tracking.get("agreed_amount"))
    amount_paid = _safe_float(tracking.get("amount_paid"))

    if agreed_amount is None and amount_paid is None:
        return _safe_float(tracking.get("balance_due"))

    agreed_amount = agreed_amount or 0.0
    amount_paid = amount_paid or 0.0
    return round(max(agreed_amount - amount_paid, 0.0), 2)


def _derive_due_bucket(final_payment_due: Optional[date], today: date) -> str:
    if final_payment_due is None:
        return "none"
    days = (final_payment_due - today).days
    if days < 0:
        return "overdue"
    if days <= 3:
        return "due_0_3"
    if days <= 7:
        return "due_4_7"
    if days <= 14:
        return "due_8_14"
    return "none"


def _tail_trip_reference(trip_id: str) -> str:
    tail = trip_id.split("_")[-1].strip()
    if not tail:
        return "unknown"
    if len(tail) <= 4:
        return tail.upper()
    return tail[-4:].upper()


def _derive_trip_name(
    trip: dict[str, Any],
    booking_data: dict[str, Any],
    destination: Optional[str],
    trip_id: str,
) -> str:
    candidate = str(trip.get("trip_name") or booking_data.get("trip_name") or "").strip()
    if candidate:
        return candidate
    if destination:
        return f"{destination} trip"
    return f"Trip details incomplete · {_tail_trip_reference(trip_id)}"


def _derive_queue_status(
    payment_status: str,
    refund_status: str,
    final_payment_due: Optional[date],
    balance_due: Optional[float],
    has_tracking: bool,
    today: date,
) -> str:
    if not has_tracking:
        return "not_configured"

    if refund_status in {"pending_review", "approved", "processing"}:
        return "refund_in_progress"

    if payment_status in {"paid", "waived", "refunded"} and (balance_due is None or balance_due <= 0):
        return "paid_complete"

    if final_payment_due is not None and (balance_due is None or balance_due > 0):
        days = (final_payment_due - today).days
        if days < 0:
            return "overdue"
        if days <= 7:
            return "due_soon"
        return "due_later"

    if payment_status == "overdue":
        return "overdue"

    if payment_status == "unknown":
        return "unknown"

    if balance_due is None:
        return "unknown"

    if balance_due > 0:
        return "due_later"

    return "unknown"


def _build_item(
    trip: dict[str, Any],
    booking_data: Optional[dict[str, Any]],
    today: date,
) -> dict[str, Any]:
    booking_data = booking_data or {}
    payment_tracking_raw = booking_data.get("payment_tracking")
    payment_tracking = payment_tracking_raw if isinstance(payment_tracking_raw, dict) else None
    has_tracking = payment_tracking is not None
    tracking = payment_tracking or {}

    payment_status = str(tracking.get("payment_status") or "unknown")
    refund_status = str(tracking.get("refund_status") or "not_applicable")
    final_payment_due = _parse_iso_date(tracking.get("final_payment_due"))
    balance_due = _compute_balance_due(tracking)

    queue_status = _derive_queue_status(
        payment_status=payment_status,
        refund_status=refund_status,
        final_payment_due=final_payment_due,
        balance_due=balance_due,
        has_tracking=has_tracking,
        today=today,
    )

    destination = None
    destination_details = trip.get("destination")
    if isinstance(destination_details, dict):
        destination = destination_details.get("destination") or destination_details.get("city") or destination_details.get("country")
    if not destination:
        booking_destination = booking_data.get("destination")
        if isinstance(booking_destination, dict):
            destination = (
                booking_destination.get("destination")
                or booking_destination.get("city")
                or booking_destination.get("country")
            )
        if not destination:
            destination = trip.get("destination_raw") or booking_data.get("destination_raw")

    start_date = trip.get("start_date") or booking_data.get("start_date")
    trip_name = _derive_trip_name(trip, booking_data, destination, str(trip.get("id") or ""))

    return {
        "trip_id": str(trip.get("id") or ""),
        "trip_name": trip_name,
        "destination": destination,
        "start_date": start_date,
        "status": trip.get("status"),
        "queue_status": queue_status,
        "payment_status": payment_status if payment_status in PAYMENT_STATUSES else "unknown",
        "refund_status": refund_status if refund_status in REFUND_STATUSES else "not_applicable",
        "agreed_amount": _safe_float(tracking.get("agreed_amount")),
        "amount_paid": _safe_float(tracking.get("amount_paid")),
        "balance_due": balance_due,
        "currency": tracking.get("currency") or "INR",
        "final_payment_due": final_payment_due.isoformat() if final_payment_due else None,
        "due_bucket": _derive_due_bucket(final_payment_due, today),
        "payment_reference_present": bool(tracking.get("payment_reference")),
        "payment_proof_url_present": bool(tracking.get("payment_proof_url")),
        "refund_paid_by_agency": bool(tracking.get("refund_paid_by_agency", False)),
        "updated_at": trip.get("updated_at"),
    }


def _matches_filters(
    item: dict[str, Any],
    *,
    queue_status: Optional[str] = None,
    payment_status: Optional[str] = None,
    refund_status: Optional[str] = None,
    due_bucket: Optional[str] = None,
) -> bool:
    if queue_status and item["queue_status"] != queue_status:
        return False
    if payment_status and item["payment_status"] != payment_status:
        return False
    if refund_status and item["refund_status"] != refund_status:
        return False
    if due_bucket and item["due_bucket"] != due_bucket:
        return False
    return True


def _strip_internal_fields(item: dict[str, Any]) -> dict[str, Any]:
    item_copy = dict(item)
    item_copy.pop("due_bucket", None)
    return item_copy


def build_payment_queue_response(
    *,
    trips: Sequence[dict[str, Any]],
    booking_data_by_trip_id: dict[str, Optional[dict[str, Any]]],
    limit: int,
    offset: int,
    queue_status: Optional[str] = None,
    payment_status: Optional[str] = None,
    refund_status: Optional[str] = None,
    due_bucket: Optional[str] = None,
    today: Optional[date] = None,
) -> dict[str, Any]:
    today = today or datetime.now().date()

    projected: list[dict[str, Any]] = []
    for trip in trips:
        trip_id = str(trip.get("id") or "")
        if not trip_id:
            continue
        item = _build_item(trip, booking_data_by_trip_id.get(trip_id), today)

        if not _matches_filters(
            item,
            queue_status=queue_status,
            payment_status=payment_status,
            refund_status=refund_status,
            due_bucket=due_bucket,
        ):
            continue

        projected.append(item)

    total_filtered = len(projected)

    paginated = projected[offset : offset + limit]
    has_more = offset + len(paginated) < total_filtered

    by_queue_status = {status: 0 for status in PAYMENT_QUEUE_STATUSES}
    for item in projected:
        by_queue_status[item["queue_status"]] = by_queue_status.get(item["queue_status"], 0) + 1

    due_within_7_days = 0
    for item in projected:
        if item["final_payment_due"] is None:
            continue
        due_date = _parse_iso_date(item["final_payment_due"])
        if due_date is None:
            continue
        balance_due = _safe_float(item.get("balance_due"))
        if balance_due is not None and balance_due <= 0:
            continue
        days = (due_date - today).days
        if 0 <= days <= 7:
            due_within_7_days += 1

    summary = {
        "total": total_filtered,
        "by_queue_status": by_queue_status,
        "overdue_count": by_queue_status.get("overdue", 0),
        "due_soon_count": by_queue_status.get("due_soon", 0),
        "not_configured_count": by_queue_status.get("not_configured", 0),
        "paid_complete_count": by_queue_status.get("paid_complete", 0),
        "refund_in_progress_count": by_queue_status.get("refund_in_progress", 0),
        "due_within_7_days_count": due_within_7_days,
    }

    pagination = {
        "limit": limit,
        "offset": offset,
        "returned": len(paginated),
        "total": total_filtered,
        "has_more": has_more,
    }

    items = [_strip_internal_fields(item) for item in paginated]

    return {
        "summary": summary,
        "pagination": pagination,
        "items": items,
    }


def build_payment_queue_response_for_agency(
    *,
    agency_id: str,
    limit: int,
    offset: int,
    queue_status: Optional[str] = None,
    payment_status: Optional[str] = None,
    refund_status: Optional[str] = None,
    due_bucket: Optional[str] = None,
    today: Optional[date] = None,
    batch_size: int = 1000,
) -> dict[str, Any]:
    """Build payments queue response across full tenant scope.

    Iterates all agency-scoped trip summaries in bounded batches and computes
    filtered totals, summary stats, and requested page over the full tenant set.
    """
    today = today or datetime.now().date()

    by_queue_status = {status: 0 for status in PAYMENT_QUEUE_STATUSES}
    due_within_7_days = 0
    filtered_total = 0
    paginated_items: list[dict[str, Any]] = []

    raw_offset = 0
    while True:
        trips = TripStore.list_trip_payment_records_for_agency(
            agency_id=agency_id,
            limit=batch_size,
            offset=raw_offset,
        )
        if not trips:
            break

        for trip in trips:
            trip_id = str(trip.get("id") or "")
            if not trip_id:
                continue

            item = _build_item(trip, trip.get("booking_data"), today)

            if not _matches_filters(
                item,
                queue_status=queue_status,
                payment_status=payment_status,
                refund_status=refund_status,
                due_bucket=due_bucket,
            ):
                continue

            filtered_total += 1
            by_queue_status[item["queue_status"]] = by_queue_status.get(item["queue_status"], 0) + 1

            if item["final_payment_due"] is not None:
                due_date = _parse_iso_date(item["final_payment_due"])
                if due_date is not None:
                    balance_due = _safe_float(item.get("balance_due"))
                    if balance_due is None or balance_due > 0:
                        days = (due_date - today).days
                        if 0 <= days <= 7:
                            due_within_7_days += 1

            if filtered_total > offset and len(paginated_items) < limit:
                paginated_items.append(_strip_internal_fields(item))

        raw_offset += len(trips)
        if len(trips) < batch_size:
            break

    has_more = offset + len(paginated_items) < filtered_total

    summary = {
        "total": filtered_total,
        "by_queue_status": by_queue_status,
        "overdue_count": by_queue_status.get("overdue", 0),
        "due_soon_count": by_queue_status.get("due_soon", 0),
        "not_configured_count": by_queue_status.get("not_configured", 0),
        "paid_complete_count": by_queue_status.get("paid_complete", 0),
        "refund_in_progress_count": by_queue_status.get("refund_in_progress", 0),
        "due_within_7_days_count": due_within_7_days,
    }

    pagination = {
        "limit": limit,
        "offset": offset,
        "returned": len(paginated_items),
        "total": filtered_total,
        "has_more": has_more,
    }

    return {
        "summary": summary,
        "pagination": pagination,
        "items": paginated_items,
    }
