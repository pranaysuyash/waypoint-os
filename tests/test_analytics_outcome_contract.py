"""HTTP contract checks use real reducers/models and effect-free store readers."""

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from spine_api.routers import analytics


@pytest.fixture
def analytics_client(monkeypatch):
    now = datetime.now(timezone.utc)
    state = {"trips": [], "payments": [], "reads": [], "now": now}

    def paged(kind):
        def reader(*, agency_id, limit, offset=0):
            state["reads"].append((kind, agency_id, offset))
            return state[kind][offset:offset + limit]
        return reader

    monkeypatch.setattr(analytics.TripStore, "list_trips", paged("trips"))
    monkeypatch.setattr(analytics.TripStore, "list_trip_payment_records_for_agency", paged("payments"))
    app = FastAPI()
    app.include_router(analytics.router)
    app.dependency_overrides[analytics.get_current_agency] = lambda: SimpleNamespace(id="agency-outcomes-only")
    with TestClient(app) as client:
        yield client, state


def _receipt(now):
    return {
        "fulfilled_at": (now - timedelta(minutes=5)).isoformat(),
        "total_charged_usd": 1200,
        "fulfillment_provider_key": "synthetic-real-provenance-fixture",
        "pnr_locator": "SYNTHETIC",
        "reality_tier": "real",
        "provider_connected": True,
    }


def test_revenue_reads_beyond_first_thousand_and_uses_scoped_payment_batch(analytics_client):
    client, state = analytics_client
    state["trips"] = [{
        "id": f"trip-{index}",
        "created_at": (state["now"] - timedelta(hours=1)).isoformat(),
        "status": "in_progress",
    } for index in range(1001)]
    state["trips"][-1]["booking_confirmation"] = _receipt(state["now"])
    state["payments"] = [{
        "id": "trip-1000",
        "booking_data": {
            "travelers": [{"passport_number": "SECRET-PII-MUST-NOT-LEAK"}],
            "payment_tracking": {"currency": "EUR", "amount_paid": 600, "tracking_only": True},
        },
    }]

    response = client.get("/analytics/revenue?range=30d")

    assert response.status_code == 200
    data = response.json()
    assert data["commercial"]["bookedCustomerValue"]["totals"][0]["amount"] == 1200
    assert data["commercial"]["recordedCustomerCollections"]["totals"][0]["currency"] == "EUR"
    assert "SECRET-PII" not in response.text
    assert "travelers" not in response.text
    assert ("trips", "agency-outcomes-only", 1000) in state["reads"]
    assert all(agency == "agency-outcomes-only" for _, agency, _ in state["reads"])


def test_summary_uses_full_receipt_record_and_lifetime_activation(analytics_client):
    client, state = analytics_client
    state["trips"] = [{
        "id": "old-approved-brief",
        "status": "in_progress",
        "created_at": (state["now"] - timedelta(days=100)).isoformat(),
        "packet": {"budget": {"value": 2000, "currency": "EUR"}},
        "analytics": {
            "review_status": "approved",
            "review_metadata": {"owner_approved": True, "reviewed_by": "real-owner-id", "reviewed_at": (state["now"] - timedelta(days=90)).isoformat()},
        },
        "booking_confirmation": _receipt(state["now"]),
    }]

    summary = client.get("/analytics/summary?range=7d").json()
    revenue = client.get("/analytics/revenue?range=7d").json()

    assert summary["totalInquiries"] == 0
    assert summary["activation"]["firstValueAchieved"] is True
    assert summary["gmv"] == 1200
    assert revenue["commercial"]["bookedCustomerValue"]["evidenceTripCount"] == 1
    assert revenue["periodStart"] is not None
    assert revenue["periodEnd"] is not None


@pytest.mark.parametrize("query", ["range=custom", "range=unknown", "range=custom&start=2026-10-23&end=2026-10-01"])
def test_invalid_or_incomplete_range_returns_422_before_store_access(analytics_client, query):
    client, state = analytics_client
    response = client.get(f"/analytics/revenue?{query}")
    assert response.status_code == 422
    assert state["reads"] == []


def test_explicit_custom_range_applies_receipt_event_dates(analytics_client):
    client, state = analytics_client
    state["trips"] = [{"id": "older-inquiry", "created_at": "2020-01-01T00:00:00Z", "booking_confirmation": _receipt(state["now"])}]
    response = client.get("/analytics/revenue", params={
        "range": "custom",
        "start": (state["now"] - timedelta(hours=1)).isoformat(),
        "end": state["now"].isoformat(),
    })
    assert response.status_code == 200
    monthly = response.json()["revenueByMonth"]
    assert monthly[0]["booked"] == 1
    assert monthly[0]["inquiries"] == 0
    assert monthly[0]["currency"] == "USD"


def test_nonadvancing_store_reader_fails_explicitly(analytics_client, monkeypatch):
    client, _ = analytics_client
    monkeypatch.setattr(analytics.TripStore, "list_trips", lambda **kwargs: [{"id": "same"}] * 500)
    response = client.get("/analytics/summary")
    assert response.status_code == 503
    assert "did not advance" in response.json()["detail"]
