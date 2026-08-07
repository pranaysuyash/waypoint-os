"""
tests/test_trust_scorecard_router.py — Unit & Integration tests for Visual Trust Scorecard Engine.
"""

import os
import pytest

os.environ["RUNNING_TESTS"] = "1"



@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    monkeypatch.setenv("DATA_PRIVACY_MODE", "beta")
    monkeypatch.setenv("SPINE_API_DISABLE_AUTH", "1")
    monkeypatch.setenv("TRIPSTORE_BACKEND", "file")


def test_get_proposal_trust_scorecard(session_client):
    """Verify visual trust scorecard generation for an active trip proposal."""
    inbound_res = session_client.post(
        "/api/v1/inbound/parse",
        json={
            "channel": "email",
            "raw_text": "Family trip to Bali for 4 people from Dec 20 to Dec 30. Budget 12000 USD. Need resort with kids pool.",
            "customer_name": "Elena Rostova",
            "agent_notes": "Client requested high-floor suite",
        },
        headers={"X-Agency-ID": "agency_scorecard_test"},
    ).json()
    trip_id = inbound_res["trip_id"]

    response = session_client.get(
        f"/api/v1/proposals/{trip_id}/trust-scorecard",
        headers={"X-Agency-ID": "agency_scorecard_test"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["trip_id"] == trip_id
    assert isinstance(data["suitability_match_pct"], float)
    assert data["budget_fit_status"] in ("UNDER_BUDGET", "PERFECT_MATCH")
    assert len(data["highlights"]) >= 1
    # Verify unevidenced badges are absent when safety/supplier checks were not run
    badge_names = [b["badge"] for b in data["transparency_badges"]]
    assert "REALITY_VERIFIED" not in badge_names
    assert "SAFETY_AUDITED" not in badge_names


def test_generate_proposal_link(session_client):
    """Verify generating an interactive proposal link for travel clients."""
    inbound_res = session_client.post(
        "/api/v1/inbound/parse",
        json={
            "channel": "whatsapp_web",
            "raw_text": "Honeymoon to Santorini in September.",
            "customer_name": "Sophia Martinez",
        },
        headers={"X-Agency-ID": "agency_link_test"},
    ).json()

    trip_id = inbound_res["trip_id"]

    response = session_client.post(
        "/api/v1/proposals/generate-link",
        json={
            "trip_id": trip_id,
            "expiry_days": 7,
            "allow_customization": True,
        },
        headers={"X-Agency-ID": "agency_link_test"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["trip_id"] == trip_id
    assert data["proposal_token"].startswith("prop_")
    assert "/proposals/prop_" in data["web_url"]
    assert "select_room_upgrades" in data["interactive_capabilities"]
