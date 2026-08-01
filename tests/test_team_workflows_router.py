"""
tests/test_team_workflows_router.py — Unit & Integration tests for Agency Team Workflows Engine.
"""

import os
import pytest
from starlette.testclient import TestClient

os.environ["RUNNING_TESTS"] = "1"
os.environ["TRIPSTORE_BACKEND"] = "file"

from spine_api.persistence import TripStore
from spine_api.server import app


@pytest.fixture
def session_client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    monkeypatch.setenv("DATA_PRIVACY_MODE", "beta")
    monkeypatch.setenv("SPINE_API_DISABLE_AUTH", "1")


def test_assign_trip_to_team_member(session_client):
    """Verify assigning a trip packet to an agency team member."""
    inbound_res = session_client.post(
        "/api/v1/inbound/parse",
        json={
            "channel": "whatsapp_web",
            "raw_text": "Safari in Kenya in August.",
            "customer_name": "David Miller",
        },
        headers={"X-Agency-ID": "agency_team_test"},
    ).json()

    trip_id = inbound_res["trip_id"]

    response = session_client.post(
        "/api/v1/team/assign",
        json={
            "trip_id": trip_id,
            "assignee_id": "usr_luxury_expert_09",
            "assignee_role": "primary_agent",
            "notes": "Assigning to luxury safari specialist",
        },
        headers={"X-Agency-ID": "agency_team_test"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["trip_id"] == trip_id
    assert data["assigned_to"] == "usr_luxury_expert_09"
    assert data["role"] == "primary_agent"

    trip = TripStore.get_trip(trip_id)
    assert trip["assigned_agent_id"] == "usr_luxury_expert_09"


def test_submit_review_signoff(session_client):
    """Verify submitting a manager review signoff decision on a trip proposal."""
    inbound_res = session_client.post(
        "/api/v1/inbound/parse",
        json={
            "channel": "whatsapp_web",
            "raw_text": "Safari in Kenya in August.",
            "customer_name": "David Miller",
        },
        headers={"X-Agency-ID": "agency_team_test"},
    ).json()

    trip_id = inbound_res["trip_id"]

    response = session_client.post(
        "/api/v1/team/review-signoff",
        json={
            "trip_id": trip_id,
            "reviewer_id": "mgr_compliance_lead",
            "decision": "APPROVED",
            "feedback_notes": "All safety scores & supplier margins verified",
        },
        headers={"X-Agency-ID": "agency_team_test"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["trip_id"] == trip_id
    assert data["reviewer_id"] == "mgr_compliance_lead"
    assert data["decision"] == "APPROVED"

    trip = TripStore.get_trip(trip_id)
    assert trip["review_decision"] == "APPROVED"
