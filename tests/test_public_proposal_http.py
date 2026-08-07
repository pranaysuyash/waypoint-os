"""
tests/test_public_proposal_http.py — Unauthenticated Traveler Proposal HTTP Access Tests.

Verifies:
  - GET /api/v1/proposals/token/{token} is publicly accessible without Auth header
  - POST /api/v1/proposals/token/{token}/accept is publicly accessible without Auth header
  - Acceptance records acceptance intent without illegally mutating booking stage
"""

import os
import pytest

os.environ["RUNNING_TESTS"] = "1"

from spine_api.persistence import TEST_AGENCY_ID, TripStore


@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    monkeypatch.setenv("TRIPSTORE_BACKEND", "file")


def test_public_proposal_view_and_accept_unauthenticated(session_client):
    # 1. Create a trip with proposal token
    trip_id = TripStore.save_trip(
        {
            "id": "trip_test_public_1",
            "destination": "Kyoto",
            "status": "active",
            "stage": "discovery",
            "proposal_link_token": "prop_test_token_12345",
            "packet": {
                "destination": "Kyoto",
                "start_date": "2026-10-01",
                "end_date": "2026-10-10",
                "party_size": 2,
                "budget_max": 8000,
            },
            "strategy": {
                "recommended_option": {
                    "name": "Kyoto Garden Villa",
                    "cost": 7500,
                    "currency": "USD",
                    "highlights": ["Private tea house", "Ryokan stay"],
                }
            },
        },
        agency_id=TEST_AGENCY_ID,
    )

    # 2. Call GET /api/v1/proposals/token/prop_test_token_12345 without Auth header
    res_view = session_client.get("/api/v1/proposals/token/prop_test_token_12345")
    assert res_view.status_code == 200
    view_data = res_view.json()
    assert view_data["ok"] is True
    assert view_data["trip_id"] == trip_id
    assert view_data["destination"] == "Kyoto"
    assert view_data["party_size"] == 2
    assert view_data["recommended_option"]["name"] == "Kyoto Garden Villa"

    # 3. Call POST /api/v1/proposals/token/prop_test_token_12345/accept without Auth header
    res_accept = session_client.post("/api/v1/proposals/token/prop_test_token_12345/accept")
    assert res_accept.status_code == 200
    accept_data = res_accept.json()
    assert accept_data["ok"] is True
    assert accept_data["intent_recorded"] is True
    assert accept_data["stage"] == "discovery"  # Stage is preserved, not mutated to booking

    # 4. Verify trip in store has proposal_accepted_by_traveler flag set
    saved_trip = TripStore.get_trip_for_agency(trip_id, TEST_AGENCY_ID)
    assert saved_trip["proposal_accepted_by_traveler"] is True
    assert saved_trip["proposal_acceptance_intent"] == "PROPOSAL_ACCEPTED_INTENT"
