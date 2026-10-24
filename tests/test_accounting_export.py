"""E08 un-orphan: trip-scoped accounting export serving path.

The AccountingExportBridge (Tally XML / QuickBooks JSON) previously had zero
serving-path callers. This suite pins the derivation: INR-native export from
persisted strategy cost + MarginPolicy margin + statutory TCS/GST, with
explicit not-available contracts (no quote cost / non-INR) and provenance.
"""

import pytest
from starlette.testclient import TestClient

from spine_api.server import app

client = TestClient(app)

INR_TRIP = {
    "id": "trip_acct_1",
    "agency_id": "agency_acct",
    "commercial_pricing": {
        "retail_amount": 1_025_000, "currency": "INR",
        "approved_by": "user:advisor@example.test", "approved_at": "2026-10-23T09:00:00+05:30",
        "evidence_ref": "approved-native-quote-1",
    },
    "packet": {"customer_name": "Meera Sharma", "destination_country": "IN"},
    "strategy": {
        "recommended_option": {
            "name": "Kerala Family Journey",
            "cost": 900000,
            "currency": "INR",
            "highlights": ["Backwater resort"],
        },
    },
    "decision": {
        "budget_breakdown": {
            "buckets": [
                {"bucket": "stay", "low": 480000, "high": 520000, "covered": True},
                {"bucket": "flights", "low": 300000, "high": 330000, "covered": True},
            ],
        },
    },
}


@pytest.fixture(autouse=True)
def _agency_override(monkeypatch):
    from types import SimpleNamespace

    monkeypatch.setenv("SPINE_API_DISABLE_AUTH", "1")
    original = dict(app.dependency_overrides)
    app.dependency_overrides[
        __import__("spine_api.core.auth", fromlist=["get_current_agency"]).get_current_agency
    ] = lambda: SimpleNamespace(id="agency_acct")
    try:
        yield
    finally:
        app.dependency_overrides = original


def _wire(monkeypatch, trip=INR_TRIP):
    import spine_api.routers.accounting_export as acct

    monkeypatch.setattr(
        acct.TripStore,
        "get_trip_for_agency",
        lambda trip_id, agency_id: trip if trip_id == "trip_acct_1" and agency_id == "agency_acct" else None,
    )


def test_tally_export_derives_real_invoice(monkeypatch):
    _wire(monkeypatch)
    res = client.get("/api/v1/trips/trip_acct_1/accounting-export", params={"format": "tally"})
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["basis"] == "operator_approved_retail"
    assert data["provenance"]["net_cost"] == 900000
    assert data["provenance"]["grand_total_payable"] > data["provenance"]["gross_package_price"]
    assert data["provenance"]["evidence_ref"] == "approved-native-quote-1"
    assert data["provenance"]["gross_package_price"] == 1_025_000
    # Tally XML body carries the ledger scaffold and the customer.
    assert "ALLLEDGERENTRIES.LIST" in data["body"]
    assert "Meera Sharma" in data["body"]


def test_quickbooks_export_is_valid_json(monkeypatch):
    _wire(monkeypatch)
    res = client.get("/api/v1/trips/trip_acct_1/accounting-export", params={"format": "quickbooks"})
    assert res.status_code == 200
    import json

    payload = json.loads(res.json()["body"])
    assert payload  # non-empty QB structure


OVERSEAS_TRIP = {
    "id": "trip_acct_1",
    "agency_id": "agency_acct",
    "commercial_pricing": INR_TRIP["commercial_pricing"],
    "packet": {"customer_name": "Meera Sharma", "destination_country": "TH"},
    "strategy": {
        "recommended_option": {
            "name": "Thailand Family Journey",
            "cost": 900000,
            "currency": "INR",
        },
    },
}


def test_tcs_overseas_with_pan_vs_without(monkeypatch):
    """TCS 206C(1G) applies to OVERSEAS packages: non-PAN 20% > PAN 5% tier."""
    _wire(monkeypatch, OVERSEAS_TRIP)
    with_pan = client.get(
        "/api/v1/trips/trip_acct_1/accounting-export", params={"pan_number": "ABCDE1234F"}
    ).json()["provenance"]
    without_pan = client.get("/api/v1/trips/trip_acct_1/accounting-export").json()["provenance"]
    # Non-PAN statutory rule: 20% flat — strictly higher than the 5% PAN tier.
    assert without_pan["tcs_total"] > with_pan["tcs_total"] > 0


def test_tcs_below_lrs_threshold_is_zero(monkeypatch):
    """Under the ₹7,00,000 LRS threshold the engine correctly applies no TCS."""
    trip = {
        "id": "trip_acct_1",
        "agency_id": "agency_acct",
        "commercial_pricing": {**INR_TRIP["commercial_pricing"], "retail_amount": 280_000},
        "packet": {"destination_country": "IN"},
        "strategy": {"recommended_option": {"name": "Short Trip", "cost": 250000, "currency": "INR"}},
    }
    _wire(monkeypatch, trip)
    data = client.get("/api/v1/trips/trip_acct_1/accounting-export").json()
    assert data["provenance"]["tcs_total"] == 0.0
    assert "threshold" in data["provenance"]["tcs_rationale"].lower() or "not applicable" in data["provenance"]["tcs_rationale"].lower()


def test_non_inr_quote_is_refused_without_fx_invention(monkeypatch):
    trip = {
        "id": "trip_acct_1",
        "agency_id": "agency_acct",
        "packet": {},
        "strategy": {"recommended_option": {"name": "Kyoto", "cost": 7500, "currency": "USD"}},
    }
    _wire(monkeypatch, trip)
    res = client.get("/api/v1/trips/trip_acct_1/accounting-export")
    assert res.status_code == 409
    assert "no live FX producer" in res.json()["detail"]


def test_missing_quote_cost_is_explicit_not_available(monkeypatch):
    trip = {"id": "trip_acct_1", "agency_id": "agency_acct", "packet": {}, "strategy": {}}
    _wire(monkeypatch, trip)
    res = client.get("/api/v1/trips/trip_acct_1/accounting-export")
    assert res.status_code == 409
    assert "run the spine" in res.json()["detail"]


def test_cross_tenant_404(monkeypatch):
    _wire(monkeypatch)
    res = client.get("/api/v1/trips/trip_other/accounting-export")
    assert res.status_code == 404


def test_native_net_alone_cannot_be_exported_as_customer_retail(monkeypatch):
    trip = {key: value for key, value in INR_TRIP.items() if key != "commercial_pricing"}
    _wire(monkeypatch, trip)
    response = client.get("/api/v1/trips/trip_acct_1/accounting-export")
    assert response.status_code == 409
    assert "approved INR retail" in response.json()["detail"]
