"""T4 (FND-0303): real quote read model — derivation from persisted spine data.

Covers: quote derivation from strategy.recommended_option + fee_matrix margin
provenance, real review/proposal status mapping, explicit not-ready contract
(no fabricated prices), and branch prompts surfaced unpriced.
"""

import pytest
from starlette.testclient import TestClient

from spine_api.server import app

client = TestClient(app)


BASE_TRIP = {
    "id": "trip_quote_1",
    "agency_id": "agency_quotes",
    "destination": "Kyoto",
    "created_at": "2026-09-20T10:00:00+00:00",
    "proposal_link_token": None,
    "analytics": {"review_status": "pending"},
    "strategy": {
        "recommended_option": {
            "name": "Kyoto Garden Villa",
            "cost": 7500,
            "currency": "USD",
            "highlights": ["Private garden suite", "Tea ceremony"],
            "summary": "Seven days in Kyoto.",
        },
    },
    "decision": {
        "branch_options": [
            {"label": "Budget-tier options", "description": "Different budget interpretations suggest different trip tiers."},
        ],
        "budget_breakdown": {
            "verdict": "realistic",
            "buckets": [{"bucket": "stay", "low": 3000, "high": 3600, "covered": True}],
            "missing_buckets": ["flights"],
        },
    },
}


@pytest.fixture(autouse=True)
def _agency_override(monkeypatch):
    from types import SimpleNamespace

    # Local-only auth bypass (mirrors sibling router test modules) so the
    # mounted _auth_or_skip gate lets the TestClient through.
    monkeypatch.setenv("SPINE_API_DISABLE_AUTH", "1")
    original = dict(app.dependency_overrides)
    app.dependency_overrides[
        __import__("spine_api.core.auth", fromlist=["get_current_agency"]).get_current_agency
    ] = lambda: SimpleNamespace(id="agency_quotes")
    from spine_api.core.auth import get_current_membership, get_current_user
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id="operator-server-id", email="operator@example.test")
    app.dependency_overrides[get_current_membership] = lambda: SimpleNamespace(agency_id="agency_quotes", role="owner")
    try:
        yield
    finally:
        app.dependency_overrides = original


def _wire(monkeypatch, trip):
    import spine_api.routers.quotes as quotes_router

    monkeypatch.setattr(
        quotes_router.TripStore,
        "get_trip_for_agency",
        lambda trip_id, agency_id: trip if trip_id == "trip_quote_1" and agency_id == "agency_quotes" else None,
    )


def test_quote_derived_from_persisted_strategy(monkeypatch):
    _wire(monkeypatch, BASE_TRIP)
    res = client.get("/api/v1/trips/trip_quote_1/quotes")
    assert res.status_code == 200
    data = res.json()
    assert data["quote_ready"] is True
    quote = data["quotes"][0]
    assert quote["title"] == "Kyoto Garden Villa"
    assert quote["net_cost"] == 7500
    assert quote["net_cost_basis"] == "persisted_modeled_cost"
    # Margin comes from fee_matrix with applied-rule provenance (FND-0268).
    assert quote["margin_percent"] > 0
    assert "@" in quote["margin_provenance"]["applied_rule_id"]
    assert quote["rack_price"] > quote["net_cost"]
    assert quote["rack_price_basis"] == "computed_preview"
    # No tax producer exists — never a fabricated default.
    assert quote["tax_percent"] is None
    # Draft status (pending review, no proposal link).
    assert quote["status"] == "draft"


def test_quote_returns_trip_version_for_reviewed_retail_approval(monkeypatch):
    version = "2026-10-23T09:00:00.123456+00:00"
    _wire(monkeypatch, {**BASE_TRIP, "updated_at": version})
    response = client.get("/api/v1/trips/trip_quote_1/quotes")
    assert response.status_code == 200
    assert response.json()["trip_version"] == version


def test_status_maps_review_state_and_proposal_link(monkeypatch):
    trip = dict(BASE_TRIP)
    trip["analytics"] = {"review_status": "approved", "review_metadata": {"reviewed_at": "2026-09-25T12:00:00+00:00"}}
    _wire(monkeypatch, trip)
    data = client.get("/api/v1/trips/trip_quote_1/quotes").json()
    assert data["quotes"][0]["status"] == "approved"
    assert data["quotes"][0]["updated_at"] == "2026-09-25T12:00:00+00:00"

    trip2 = dict(BASE_TRIP)
    trip2["analytics"] = {"review_status": "pending"}
    trip2["proposal_link_token"] = "prop_real"
    _wire(monkeypatch, trip2)
    data2 = client.get("/api/v1/trips/trip_quote_1/quotes").json()
    assert data2["quotes"][0]["status"] == "sent"


def test_branches_surfaced_unpriced(monkeypatch):
    _wire(monkeypatch, BASE_TRIP)
    data = client.get("/api/v1/trips/trip_quote_1/quotes").json()
    assert len(data["branches"]) == 1
    assert data["branches"][0]["priced"] is False
    # Branch objects carry labels/descriptions only — no monetary fields.
    for branch in data["branches"]:
        assert set(branch.keys()) == {"label", "description", "priced"}
        # bools (priced) are fine; no numeric money fields on a branch.
        assert not any(
            isinstance(v, (int, float)) and not isinstance(v, bool) for v in branch.values()
        )


def test_not_ready_contract_when_no_persisted_option(monkeypatch):
    trip = dict(BASE_TRIP)
    trip["strategy"] = {}
    trip["decision"] = {}
    _wire(monkeypatch, trip)
    res = client.get("/api/v1/trips/trip_quote_1/quotes")
    assert res.status_code == 200
    data = res.json()
    assert data["quote_ready"] is False
    assert data["quotes"] == []
    assert any("strategy.recommended_option" in m for m in data["missing"])
    # No fabricated numbers anywhere in the response.
    import json

    body = json.dumps(data)
    assert "7500" not in body
    assert "4200" not in body


def test_not_ready_when_cost_missing_even_with_option(monkeypatch):
    trip = dict(BASE_TRIP)
    trip["strategy"] = {"recommended_option": {"name": "Kyoto Garden Villa", "cost": None}}
    _wire(monkeypatch, trip)
    data = client.get("/api/v1/trips/trip_quote_1/quotes").json()
    assert data["quote_ready"] is False
    assert any("cost" in m for m in data["missing"])


def test_cross_agency_trip_is_404(monkeypatch):
    _wire(monkeypatch, BASE_TRIP)
    res = client.get("/api/v1/trips/trip_other/quotes")
    assert res.status_code == 404


def test_native_currency_keeps_known_cost_without_inventing_dollar_fees(monkeypatch):
    from copy import deepcopy

    trip = deepcopy(BASE_TRIP)
    trip["strategy"]["recommended_option"].update(cost=100_000, currency="INR")
    _wire(monkeypatch, trip)
    response = client.get("/api/v1/trips/trip_quote_1/quotes")
    assert response.status_code == 200
    data = response.json()
    assert data["quote_ready"] is False
    quote = data["quotes"][0]
    assert quote["net_cost"] == 100_000
    assert quote["currency"] == "INR"
    assert quote["rack_price"] is None
    assert quote["margin_percent"] is None
    assert quote["pricing_status"] == "pricing_review"
    assert any("currency" in item.lower() for item in data["missing"])


def test_native_currency_retail_requires_same_currency_approval_evidence(monkeypatch):
    from copy import deepcopy

    trip = deepcopy(BASE_TRIP)
    trip["strategy"]["recommended_option"].update(cost=100_000, currency="INR")
    trip["commercial_pricing"] = {
        "retail_amount": 125_000,
        "currency": "INR",
        "approved_by": "user:operator@example.test",
        "approved_at": "2026-10-23T10:00:00+05:30",
        "evidence_ref": "agency-quote-approved-1",
    }
    _wire(monkeypatch, trip)
    response = client.get("/api/v1/trips/trip_quote_1/quotes").json()
    assert response["quote_ready"] is True
    assert response["quotes"][0]["rack_price"] == 125_000
    assert response["quotes"][0]["rack_price_basis"] == "operator_approved_retail"
    trip["commercial_pricing"]["currency"] = "USD"
    changed = client.get("/api/v1/trips/trip_quote_1/quotes").json()
    assert changed["quote_ready"] is False


@pytest.mark.parametrize("bad_cost", [True, float("nan"), float("inf"), -1, "Infinity"])
def test_invalid_modeled_cost_is_unpriced_not_serialized_as_money(monkeypatch, bad_cost):
    from copy import deepcopy

    trip = deepcopy(BASE_TRIP)
    trip["strategy"]["recommended_option"]["cost"] = bad_cost
    _wire(monkeypatch, trip)
    response = client.get("/api/v1/trips/trip_quote_1/quotes")
    assert response.status_code == 200
    assert response.json()["quote_ready"] is False


def test_retail_approval_binds_real_operator_and_native_currency_with_cas(monkeypatch):
    from copy import deepcopy
    import spine_api.routers.quotes as quotes_router

    trip = deepcopy(BASE_TRIP)
    trip["updated_at"] = "2026-10-23T09:00:00+00:00"
    trip["strategy"]["recommended_option"].update(cost=100_000, currency="INR")
    _wire(monkeypatch, trip)
    writes = []

    def cas(trip_id, agency_id, updates, expected_updated_at=None):
        assert (trip_id, agency_id, expected_updated_at) == (trip["id"], trip["agency_id"], trip["updated_at"])
        writes.append(updates)
        trip.update(updates)
        return trip

    monkeypatch.setattr(quotes_router.TripStore, "update_trip_if_version_for_agency", cas)
    monkeypatch.setattr(quotes_router, "_audit_retail_approval", lambda *_args, **_kwargs: None, raising=False)
    response = client.post("/api/v1/trips/trip_quote_1/quotes/retail", json={
        "retail_amount": 125_000, "currency": "INR", "evidence_ref": "approved-quote-document",
        "expected_updated_at": trip["updated_at"], "approved_by": "client-spoofed-approver",
    })
    assert response.status_code == 200, response.text
    assert response.json()["trip_version"] == trip["updated_at"]
    assert response.json()["quotes"][0]["rack_price"] == 125_000
    assert writes[0]["commercial_pricing"]["approved_by"] == "user:operator-server-id"
    assert writes[0]["commercial_pricing"]["evidence_ref"] == "approved-quote-document"


def test_retail_approval_rejects_currency_mismatch_and_stale_version(monkeypatch):
    import spine_api.routers.quotes as quotes_router

    _wire(monkeypatch, {**BASE_TRIP, "updated_at": "2026-10-23T09:00:00+00:00"})
    writes = []
    monkeypatch.setattr(quotes_router.TripStore, "update_trip_if_version_for_agency", lambda *_args, **_kwargs: writes.append(True))
    base = {"retail_amount": 125_000, "currency": "INR", "evidence_ref": "quote", "expected_updated_at": "stale"}
    mismatch = client.post("/api/v1/trips/trip_quote_1/quotes/retail", json=base)
    assert mismatch.status_code == 409
    assert writes == []
    stale = client.post("/api/v1/trips/trip_quote_1/quotes/retail", json={**base, "currency": "USD"})
    assert stale.status_code == 409
    assert writes == []


def test_retail_approval_requires_owner_or_admin(monkeypatch):
    from types import SimpleNamespace
    from spine_api.core.auth import get_current_membership

    app.dependency_overrides[get_current_membership] = lambda: SimpleNamespace(agency_id="agency_quotes", role="senior_agent")
    _wire(monkeypatch, {**BASE_TRIP, "updated_at": "2026-10-23T09:00:00+00:00"})
    response = client.post("/api/v1/trips/trip_quote_1/quotes/retail", json={
        "retail_amount": 9000, "currency": "USD", "evidence_ref": "quote", "expected_updated_at": "2026-10-23T09:00:00+00:00",
    })
    assert response.status_code == 403
