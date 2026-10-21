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
