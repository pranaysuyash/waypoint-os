"""Commercial metrics must follow evidence, never internal workflow activity.

The fixtures are synthetic and the tests patch every persistence effect. They
do not create bookings, contact providers, or write the developer database.
"""

from copy import deepcopy

import pytest

from src.analytics.metrics import aggregate_insights, compute_revenue_metrics


def _trip(trip_id: str = "inquiry-1", **updates) -> dict:
    return {
        "id": trip_id,
        "status": "in_progress",
        "created_at": "2026-10-23T10:00:00Z",
        "packet": {"budget": {"value": 300000, "currency": "INR"}},
        **updates,
    }


def _live_booking(amount: object = 1500, **updates) -> dict:
    return {
        "fulfilled_at": "2026-10-23T11:00:00Z",
        "total_charged_usd": amount,
        "fulfillment_provider_key": "provider-operation-1",
        "pnr_locator": "SYNTHETIC",
        "reality_tier": "real",
        "provider_connected": True,
        **updates,
    }


def _totals(measure) -> dict[str, float]:
    return {total.currency: total.amount for total in measure.totals}


@pytest.mark.parametrize("status", ["new", "delivered", "completed", "booked"])
def test_internal_status_and_quality_never_synthesize_a_commercial_outcome(status):
    trip = _trip(status=status, analytics={"quality_score": 99})
    summary = aggregate_insights([trip])
    revenue = compute_revenue_metrics([trip])

    assert summary.convertedToBooked == 0
    assert summary.gmv is None
    assert revenue.bookedRevenue is None
    assert revenue.commercial.bookedCustomerValue.availability == "unavailable"
    assert revenue.commercial.agencyEarnedRevenue.availability == "unavailable"
    assert revenue.commercial.agencyRealizedRevenue.availability == "unavailable"


def test_live_booking_value_is_customer_value_and_not_agency_revenue():
    trip = _trip(booking_confirmation=_live_booking())
    revenue = compute_revenue_metrics([trip])

    assert _totals(revenue.commercial.bookedCustomerValue) == {"USD": 1500.0}
    assert revenue.bookedRevenue == 1500.0
    assert aggregate_insights([trip]).convertedToBooked == 1
    assert revenue.commercial.agencyEarnedRevenue.totals == []
    assert revenue.commercial.agencyRealizedRevenue.totals == []


@pytest.mark.parametrize("tier", ["deterministic_preview", "connected_sandbox", "planned"])
def test_preview_fulfillment_is_excluded_from_real_booking_metrics(tier):
    trip = _trip(booking_confirmation=_live_booking(reality_tier=tier))
    revenue = compute_revenue_metrics([trip])

    assert aggregate_insights([trip]).convertedToBooked == 0
    assert revenue.commercial.bookedCustomerValue.excludedPreviewTripCount == 1
    assert revenue.commercial.bookedCustomerValue.totals == []


@pytest.mark.parametrize("amount", [float("nan"), float("inf"), -1, True, "broken"])
def test_invalid_booking_amount_never_enters_money_totals(amount):
    revenue = compute_revenue_metrics([_trip(booking_confirmation=_live_booking(amount))])

    assert revenue.commercial.bookedCustomerValue.totals == []
    assert revenue.commercial.bookedCustomerValue.missingAmountTripCount == 1
    assert revenue.bookedRevenue is None


def test_pipeline_currency_totals_never_get_added_or_assumed_to_be_dollars():
    trips = [
        _trip("inr"),
        _trip("usd", packet={"budget": {"value": 1000, "currency": "USD"}}),
        _trip("unknown", packet={"budget": {"value": 500}}),
        _trip("lost", status="lost"),
        _trip("cancelled", status="cancelled"),
    ]
    revenue = compute_revenue_metrics(trips)

    assert _totals(revenue.commercial.budgetPipeline) == {"INR": 300000.0, "USD": 1000.0}
    assert revenue.commercial.budgetPipeline.missingCurrencyTripCount == 1
    assert revenue.commercial.budgetPipeline.availability == "partial"
    assert revenue.totalPipelineValue is None
    assert revenue.currency is None


def test_operator_payment_tracking_is_labeled_recorded_collections_only():
    trip = _trip(booking_data={"payment_tracking": {
        "agreed_amount": 4000,
        "amount_paid": 1250,
        "currency": "EUR",
        "payment_status": "deposit_paid",
        "tracking_only": True,
        "refund_status": "not_requested",
    }})
    revenue = compute_revenue_metrics([trip])

    assert _totals(revenue.commercial.recordedCustomerCollections) == {"EUR": 1250.0}
    assert aggregate_insights([trip]).convertedToBooked == 0
    assert revenue.commercial.bookedCustomerValue.totals == []
    assert revenue.commercial.agencyEarnedRevenue.totals == []


def test_currency_registry_and_recorded_precision_are_preserved():
    trips = [
        _trip("jpy", packet={"budget": {"value": "1000", "currency": "JPY"}}),
        _trip("kwd", packet={"budget": {"value": "1.2345", "currency": "KWD"}}),
        _trip("unknown-currency", packet={"budget": {"value": "50", "currency": "XYZ"}}),
    ]
    measure = compute_revenue_metrics(trips).commercial.budgetPipeline
    totals = {item.currency: item for item in measure.totals}
    assert totals["JPY"].minorUnitDigits == 0
    assert totals["KWD"].minorUnitDigits == 3
    assert totals["KWD"].amountDecimal == "1.2345"
    assert measure.missingCurrencyTripCount == 1


def test_approval_preserves_lifecycle_and_emits_no_delivery_or_feedback_claim(monkeypatch):
    from src.analytics import review

    trip = _trip(analytics={"requires_review": True, "review_status": "pending"})
    recorded_events = []
    monkeypatch.setattr(review.TripStore, "get_trip", lambda _id: deepcopy(trip))
    monkeypatch.setattr(review.TripStore, "update_trip", lambda _id, updates: trip.update(deepcopy(updates)))
    monkeypatch.setattr(review.AuditStore, "log_event", lambda *args: recorded_events.append(args))

    result = review.process_review_action(trip["id"], "approve", "Brief verified", "owner-1")

    assert result["status"] == "in_progress"
    assert result["analytics"]["review_status"] == "approved"
    assert result["analytics"]["review_metadata"]["owner_approved"] is True
    assert "delivery_status" not in result["analytics"]
    assert "proactive_feedback_asked" not in result["analytics"]
    assert all(event[0] != "notification_emitted" for event in recorded_events)


def test_activation_keeps_a_blocked_first_inquiry_visible_until_a_brief_is_approved():
    blocked = _trip(status="awaiting_customer_details", missing_fields=["dates"])
    activation = aggregate_insights([blocked]).activation

    assert activation.inquiryCount == 1
    assert activation.firstValueAchieved is False
    assert activation.nextAction == "resolve_details"
    assert activation.nextTripId == blocked["id"]


def test_activation_uses_approved_review_evidence_instead_of_navigation_or_quality():
    trip = _trip(analytics={"quality_score": 99})
    assert aggregate_insights([trip]).activation.firstValueAchieved is False
    assert aggregate_insights([trip]).activation.readyBriefCount == 0

    trip["analytics"].update({
        "review_status": "approved",
        "review_metadata": {
            "owner_approved": True,
            "reviewed_by": "owner-1",
            "reviewed_at": "2026-10-23T11:00:00Z",
        },
    })
    assert aggregate_insights([trip]).activation.firstValueAchieved is True


def test_activation_marks_details_ready_only_with_canonical_readiness_evidence():
    trip = _trip(validation={"readiness": {"tiers": {"quote_ready": {"ready": True}}}})
    activation = aggregate_insights([trip]).activation
    assert activation.readyBriefCount == 1
    assert activation.firstValueAchieved is False
