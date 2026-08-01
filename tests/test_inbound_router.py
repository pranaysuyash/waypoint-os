"""
Unit and integration tests for Multi-Channel Inbound Router and Optimistic Sync Engine.

Tests:
  - Multi-channel parsing (Chrome extension, WhatsApp Web, Email)
  - Trip packet creation and persistence in TripStore
  - Optimistic field updates and instant decision state reconciliation
  - Tenant isolation and safety envelope handling
"""

import os

os.environ["RUNNING_TESTS"] = "1"
os.environ["TRIPSTORE_BACKEND"] = "file"
if not os.environ.get("JWT_SECRET"):
    os.environ["JWT_SECRET"] = "test-jwt-secret-for-pytest-only-32byt"

import pytest

from spine_api import persistence

TripStore = persistence.TripStore
AuditStore = persistence.AuditStore


@pytest.fixture(autouse=True)
def setup_test_privacy(monkeypatch):
    monkeypatch.setenv("DATA_PRIVACY_MODE", "beta")
    monkeypatch.setenv("SPINE_API_DISABLE_AUTH", "1")


def test_inbound_parse_chrome_extension(session_client):
    """Verify inbound text parsing from Chrome Extension creates trip packet & follow-up prompt."""
    payload = {
        "channel": "chrome_extension",
        "raw_text": "Family of 4 traveling from San Francisco to Paris from Oct 10 to Oct 20. Budget around 12000 USD. Need family-friendly hotel and non-smoking rooms.",
        "customer_name": "John Doe",
        "customer_contact": "+1-555-0199",
        "agent_notes": "Client prefers direct flights if possible",
        "strict_leakage": False,
    }

    response = session_client.post(
        "/api/v1/inbound/parse",
        json=payload,
        headers={"X-Agency-ID": "test_agency_inbound"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["channel"] == "chrome_extension"
    assert data["trip_id"].startswith("trip_")
    assert "packet" in data
    assert data["packet"]["customer_name"] == "John Doe"

    # Verify trip was persisted in TripStore
    saved_trip = TripStore.get_trip(data["trip_id"])
    assert saved_trip is not None
    assert saved_trip["agency_id"] == "test_agency_inbound"
    assert saved_trip["channel"] == "chrome_extension"


def test_inbound_parse_whatsapp_web(session_client):
    """Verify inbound WhatsApp Web text parsing creates valid trip structure."""
    payload = {
        "channel": "whatsapp_web",
        "raw_text": "Need a honeymoon trip to Maldives for 2 adults in December. Budget max $8000.",
        "customer_name": "Priya Sharma",
        "strict_leakage": False,
    }

    response = session_client.post(
        "/api/v1/inbound/parse",
        json=payload,
        headers={"X-Agency-ID": "agency_whatsapp_test"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["channel"] == "whatsapp_web"
    assert data["packet"]["customer_name"] == "Priya Sharma"


def test_optimistic_sync_trip_fields(session_client):
    """Verify client-side field updates reconcile state instantly from NEEDS_INFO to READY_FOR_STRATEGY."""
    # First create a trip with missing fields
    inbound_res = session_client.post(
        "/api/v1/inbound/parse",
        json={
            "channel": "manual_paste",
            "raw_text": "Want to visit Tokyo in November.",
        },
        headers={"X-Agency-ID": "agency_sync_test"},
    ).json()

    trip_id = inbound_res["trip_id"]

    # Perform optimistic sync with missing budget & dates
    sync_payload = {
        "trip_id": trip_id,
        "field_updates": {
            "budget_max": 15000,
            "budget_scope": "15000 USD",
            "start_date": "2026-11-01",
            "end_date": "2026-11-10",
            "destination": "Tokyo, Japan",
        },
        "actor_id": "agent_alex",
    }

    response = session_client.post(
        f"/api/v1/inbound/optimistic-sync/{trip_id}",
        json=sync_payload,
        headers={"X-Agency-ID": "agency_sync_test"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["new_state"] == "READY_FOR_STRATEGY"
    assert "budget_max" in data["reconciled_fields"]
    assert len(data["missing_fields"]) == 0

    # Verify persistent state in TripStore
    updated_trip = TripStore.get_trip(trip_id)
    assert updated_trip["decision_state"] == "READY_FOR_STRATEGY"
    assert updated_trip["packet"]["budget_max"] == 15000


def test_generate_client_followup_prompt(session_client):
    """Verify automated client follow-up prompt generation for missing inquiry fields."""
    inbound_res = session_client.post(
        "/api/v1/inbound/parse",
        json={
            "channel": "whatsapp_web",
            "raw_text": "Need a trip to Paris.",
            "customer_name": "Sarah Connor",
        },
        headers={"X-Agency-ID": "agency_prompt_test"},
    ).json()

    trip_id = inbound_res["trip_id"]

    response = session_client.get(
        f"/api/v1/inbound/followup-prompt/{trip_id}?channel=whatsapp&tone=friendly",
        headers={"X-Agency-ID": "agency_prompt_test"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["customer_name"] == "Sarah Connor"
    assert "Hi Sarah!" in data["formatted_message"]
    assert isinstance(data["missing_fields"], list)
    assert len(data["formatted_message"]) > 0
    assert len(data["quick_replies"]) > 0
