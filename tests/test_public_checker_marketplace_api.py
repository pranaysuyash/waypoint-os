"""WOBS 2026-09-09 P2 — marketplace endpoints through the app.

/matches and /route-request are public (they are the consent close), must
respect the checker kill switch, and must isolate their store to tmp in tests.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from spine_api.services.agency_marketplace import (
    AgencyMarketplaceStore,
)


@pytest.fixture()
def isolated_marketplace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    data_dir = tmp_path / "agency_marketplace"
    monkeypatch.setattr(AgencyMarketplaceStore, "DATA_DIR", data_dir)
    monkeypatch.setattr(AgencyMarketplaceStore, "PROFILES_FILE", data_dir / "profiles.json")
    monkeypatch.setattr(AgencyMarketplaceStore, "LEADS_FILE", data_dir / "route_leads.jsonl")
    return AgencyMarketplaceStore


def test_matches_requires_trip_id(session_client, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("PUBLIC_CHECKER_ENABLED", raising=False)
    resp = session_client.post("/api/public-checker/matches", json={})
    assert resp.status_code == 422


def test_matches_unknown_trip_404(session_client, monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    monkeypatch.delenv("PUBLIC_CHECKER_ENABLED", raising=False)
    monkeypatch.setenv("PUBLIC_CHECKER_AGENCY_ID", "agency-x")
    resp = session_client.post(
        "/api/public-checker/matches", json={"trip_id": "trip_missing"}
    )
    assert resp.status_code == 404


def test_matches_returns_empty_supply_gracefully(session_client, monkeypatch: pytest.MonkeyPatch):
    """Supply=0: the interaction degrades to the demand-capture signal."""
    monkeypatch.delenv("PUBLIC_CHECKER_ENABLED", raising=False)
    monkeypatch.setenv("PUBLIC_CHECKER_AGENCY_ID", "agency-x")

    import spine_api.persistence as persistence
    from spine_api import persistence as persistence_module

    trip_id = "trip_matchtest01"
    monkeypatch.setattr(
        persistence_module.TripStore,
        "get_trip_for_agency",
        classmethod(
            lambda cls, trip_id_arg, agency_id: {
                "id": trip_id_arg,
                "source": "public_checker",
                "packet": {"resolved_destination": "Kerala"},
                "decision": {"hard_blockers": ["visa not arranged"], "soft_blockers": []},
            }
        ),
    )
    _ = persistence

    resp = session_client.post(
        "/api/public-checker/matches", json={"trip_id": trip_id}
    )
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["matches"] == []
    assert payload["needs"]["destination"] == "Kerala"


def test_route_request_requires_consent(session_client, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("PUBLIC_CHECKER_ENABLED", raising=False)
    resp = session_client.post(
        "/api/public-checker/route-request",
        json={"trip_id": "trip_x", "contact": "a@b.com", "consent": False},
    )
    assert resp.status_code == 422


def test_route_request_requires_valid_contact(session_client, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("PUBLIC_CHECKER_ENABLED", raising=False)
    resp = session_client.post(
        "/api/public-checker/route-request",
        json={"trip_id": "trip_x", "contact": "nope", "consent": True},
    )
    assert resp.status_code == 422


def test_route_request_captures_waitlist_lead(
    session_client, monkeypatch: pytest.MonkeyPatch, isolated_marketplace
):
    monkeypatch.delenv("PUBLIC_CHECKER_ENABLED", raising=False)
    monkeypatch.setenv("PUBLIC_CHECKER_AGENCY_ID", "agency-x")

    import spine_api.persistence as persistence
    from spine_api import persistence as persistence_module

    monkeypatch.setattr(
        persistence_module.TripStore,
        "get_trip_for_agency",
        classmethod(
            lambda cls, trip_id_arg, agency_id: {
                "id": trip_id_arg,
                "source": "public_checker",
                "packet": {"resolved_destination": "Kerala"},
                "decision": {"hard_blockers": [], "soft_blockers": ["monsoon window"]},
            }
        ),
    )
    _ = persistence

    resp = session_client.post(
        "/api/public-checker/route-request",
        json={
            "trip_id": "trip_kerala01",
            "contact": "traveler@example.com",
            "consent": True,
        },
    )
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["status"] == "captured"
    leads = isolated_marketplace.list_route_leads()
    assert len(leads) == 1
    assert leads[0]["needs"]["destination"] == "Kerala"


def test_marketplace_endpoints_respect_kill_switch(
    session_client, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setenv("PUBLIC_CHECKER_ENABLED", "0")
    assert (
        session_client.post("/api/public-checker/matches", json={"trip_id": "t"}).status_code
        == 503
    )
    assert (
        session_client.post(
            "/api/public-checker/route-request",
            json={"trip_id": "t", "contact": "a@b.com", "consent": True},
        ).status_code
        == 503
    )
