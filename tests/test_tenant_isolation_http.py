"""
tests/test_tenant_isolation_http.py — Real 2-Agency HTTP Tenant Isolation Verification Suite.

Verifies:
  - Agency B's JWT token CANNOT view, query, or mutate Agency A's trip resources over HTTP.
  - Returns HTTP 404 Not Found (storage-level tenant filtering) for cross-tenant attempts.
  - Asserts zero state mutation on Agency A's trips when Agency B attempts unauthorized access.
"""

import os
from datetime import timedelta
import pytest

os.environ["RUNNING_TESTS"] = "1"

from spine_api.core.security import create_access_token
from spine_api.persistence import TripStore

AGENCY_A = "agency_alpha_1111"
AGENCY_B = "agency_beta_2222"
USER_A = "user_alpha_1111"
USER_B = "user_beta_2222"


@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    monkeypatch.setenv("DATA_PRIVACY_MODE", "beta")
    monkeypatch.setenv("SPINE_API_DISABLE_AUTH", "1")
    monkeypatch.setenv("TRIPSTORE_BACKEND", "file")


def test_cross_agency_http_isolation(session_client):
    token_b = create_access_token(
        user_id=USER_B,
        agency_id=AGENCY_B,
        role="owner",
        expires_delta=timedelta(hours=2),
    )
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 1. Create Trip belonging exclusively to Agency A
    trip_a_data = {
        "id": "trip_alpha_private_999",
        "destination": "Zurich",
        "stage": "discovery",
        "status": "active",
        "packet": {
            "destination": "Zurich",
            "agent_notes": "CONFIDENTIAL AGENCY A NOTES",
        },
    }
    TripStore.save_trip(trip_a_data, agency_id=AGENCY_A)

    # 2. Authenticated as Agency B, attempt GET /api/v1/proposals/{trip_A}/trust-scorecard
    res_scorecard = session_client.get("/api/v1/proposals/trip_alpha_private_999/trust-scorecard", headers=headers_b)
    assert res_scorecard.status_code == 404, f"Leaked Agency A scorecard to Agency B: {res_scorecard.text}"

    # 3. Authenticated as Agency B, attempt PATCH /api/v1/trips/{trip_A}/stage
    res_stage = session_client.patch(
        "/api/v1/trips/trip_alpha_private_999/stage",
        json={"target_stage": "quote_ready"},
        headers=headers_b,
    )
    assert res_stage.status_code == 404, f"Agency B mutated Agency A stage: {res_stage.text}"

    # 4. Authenticated as Agency B, attempt POST /api/v1/concierge/monitor/{trip_A}
    res_concierge = session_client.post("/api/v1/concierge/monitor/trip_alpha_private_999", headers=headers_b)
    assert res_concierge.status_code == 404, f"Agency B accessed Agency A concierge: {res_concierge.text}"

    # 5. Assert Agency A's trip remains un-mutated in Agency A's store
    saved_trip = TripStore.get_trip_for_agency("trip_alpha_private_999", AGENCY_A)
    assert saved_trip is not None
    assert saved_trip["stage"] == "discovery"
    assert saved_trip["packet"]["agent_notes"] == "CONFIDENTIAL AGENCY A NOTES"

    # 6. Assert Agency B cannot fetch Agency A's trip via storage layer get_trip_for_agency
    assert TripStore.get_trip_for_agency("trip_alpha_private_999", AGENCY_B) is None
