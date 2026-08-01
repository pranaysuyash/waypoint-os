"""
tests/test_concierge_router.py — Unit & Integration tests for Autonomic Ghost Concierge Engine.
"""

import os
import pytest
from starlette.testclient import TestClient

os.environ["RUNNING_TESTS"] = "1"
os.environ["TRIPSTORE_BACKEND"] = "file"

from spine_api.server import app


@pytest.fixture
def session_client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    monkeypatch.setenv("DATA_PRIVACY_MODE", "beta")
    monkeypatch.setenv("SPINE_API_DISABLE_AUTH", "1")


def test_monitor_trip_status(session_client):
    """Verify actively monitoring trip flight status for disruptions."""
    inbound_res = session_client.post(
        "/api/v1/inbound/parse",
        json={
            "channel": "email",
            "raw_text": "Flight AF128 from SFO to CDG.",
            "customer_name": "Oliver Queen",
            "agent_notes": "Client flight delay expected due to strike",
        },
        headers={"X-Agency-ID": "agency_concierge_test"},
    ).json()

    trip_id = inbound_res["trip_id"]

    response = session_client.post(
        f"/api/v1/concierge/monitor/{trip_id}",
        headers={"X-Agency-ID": "agency_concierge_test"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["trip_id"] == trip_id
    assert data["disruption_detected"] is True
    assert data["disruption_type"] == "FLIGHT_DELAY"
    assert "Auto-rebook" in data["recommended_action"]


def test_execute_auto_rebook(session_client):
    """Verify executing autonomous rebooking for a disrupted segment."""
    inbound_res = session_client.post(
        "/api/v1/inbound/parse",
        json={
            "channel": "email",
            "raw_text": "Flight AF128 from SFO to CDG.",
            "customer_name": "Oliver Queen",
        },
        headers={"X-Agency-ID": "agency_concierge_test"},
    ).json()

    trip_id = inbound_res["trip_id"]

    response = session_client.post(
        f"/api/v1/concierge/auto-rebook/{trip_id}",
        json={
            "trip_id": trip_id,
            "disruption_event_id": "evt_delay_9921",
            "auto_approve": True,
        },
        headers={"X-Agency-ID": "agency_concierge_test"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["trip_id"] == trip_id
    assert data["status"] == "REBOOKED"
    assert data["new_confirmation_code"].startswith("PNR_")
    assert "Flight AF128" in data["rebooked_segment"]
