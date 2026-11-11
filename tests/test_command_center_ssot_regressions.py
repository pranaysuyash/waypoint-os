"""Regression tests for Command Center SSOT data truth and review presentation."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

from spine_api.routers import analytics as analytics_router
from src.analytics.review import trip_to_review
from src.services.dashboard_aggregator import DashboardAggregator


def _make_trip_record(
    trip_id: str,
    status: str,
    *,
    requires_review: bool = False,
    review_reason: str | None = None,
    estimated_value: float = 0.0,
    currency: str = "INR",
) -> dict:
    extracted: dict = {"destination": "Paris", "currency": currency}
    if estimated_value > 0:
        extracted["budget"] = {"value": estimated_value, "currency": currency}
    return {
        "id": trip_id,
        "trip_id": trip_id,
        "status": status,
        "analytics": {
            "requires_review": requires_review,
            "review_reason": review_reason,
            "estimated_value": estimated_value,
            "currency": currency,
            "updated_at": "2026-11-11T08:00:00Z",
        },
        "extracted": extracted,
    }


def test_unified_state_counts_all_lifecycle_statuses_without_false_orphans():
    records = [
        _make_trip_record("t-new", "new"),
        _make_trip_record("t-inc", "incomplete"),
        _make_trip_record("t-inprog", "in_progress"),
        _make_trip_record("t-active", "active"),
        _make_trip_record("t-blocked", "blocked"),
        _make_trip_record("t-rtq", "ready_to_quote"),
        _make_trip_record("t-rtb", "ready_to_book"),
        _make_trip_record("t-fu", "needs_followup"),
        _make_trip_record("t-comp", "completed"),
        _make_trip_record("t-rev", "active", requires_review=True, estimated_value=125000.0, currency="INR"),
    ]

    with (
        patch("src.services.dashboard_aggregator.TripStore.list_unified_state_projections", return_value=records),
        patch("src.services.dashboard_aggregator.TripStore.count_trips_by_status", return_value={}),
        patch("src.services.dashboard_aggregator.TripStore.count_trips", return_value=len(records)),
    ):
        state = DashboardAggregator.get_unified_state(agency_id="agency-ssot")

    assert state["canonical_total"] == len(records)
    assert state["integrity_meta"]["orphan_count"] == 0
    assert state["integrity_meta"]["consistent"] is True
    assert state["inbox_lead_count"] == 3
    assert state["workspace_trip_count"] == 6
    assert state["pending_review_count"] == 1
    assert state["pending_review_value_by_currency"] == {"INR": 125000.0}
    assert state["primary_review_currency"] == "INR"


def test_trip_to_review_humanizes_stop_needs_review_and_uses_extracted_budget():
    raw_trip = {
        "trip_id": "TRIP-POLICY-1",
        "status": "active",
        "destination": "Kyoto",
        "extracted": {
            "customer_name": "Asha Nair",
            "budget": {"value": 4200, "currency": "USD"},
        },
        "analytics": {
            "requires_review": True,
            "review_reason": "Decision state STOP_NEEDS_REVIEW requires owner review",
            "estimated_value": 0,
            "currency": "USD",
            "updated_at": "2026-11-10T10:00:00Z",
        },
    }

    review = trip_to_review(raw_trip)
    assert review["reason"] == "Policy hold: requires owner review"
    assert review["value"] == 4200
    assert review["currency"] == "USD"


def test_get_pending_reviews_does_not_truncate_at_1000():
    many_reviews = [
        {
            "trip_id": f"TRIP-{i}",
            "status": "in_progress",
            "destination": "Goa",
            "extracted": {"customer_name": f"Guest {i}", "currency": "INR"},
            "analytics": {
                "requires_review": True,
                "review_reason": "Decision state STOP_NEEDS_REVIEW requires owner review",
                "estimated_value": 50000.0,
                "currency": "INR",
                "updated_at": "2026-11-10T10:00:00Z",
            },
        }
        for i in range(1050)
    ]

    with (
        patch("spine_api.routers.analytics.TripStore.list_pending_review_trips", return_value=many_reviews),
        patch("spine_api.routers.analytics.TripStore.count_trips", return_value=2000),
    ):
        body = analytics_router.get_pending_reviews(agency=SimpleNamespace(id="agency-ssot"))

    assert body["total"] == 1050
    assert len(body["items"]) == 1050
    assert body["items"][0]["reason"] == "Policy hold: requires owner review"
