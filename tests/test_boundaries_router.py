"""
tests/test_boundaries_router.py — Integration tests for PER-0933 / PER-0927 Boundary Endpoints.
"""

import os
import pytest

os.environ["RUNNING_TESTS"] = "1"


@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    monkeypatch.setenv("DATA_PRIVACY_MODE", "beta")
    monkeypatch.setenv("SPINE_API_DISABLE_AUTH", "1")
    monkeypatch.setenv("TRIPSTORE_BACKEND", "file")


def test_issue_capability_token_endpoint(session_client):
    """Verify issuing a scoped capability token via API."""
    response = session_client.post(
        "/api/v1/boundaries/tokens/issue",
        json={
            "trip_id": "trip_bnd_101",
            "scopes": ["VIEW_ONLY", "PROPOSE_EDIT"],
            "traveler_role": "companion",
            "ttl_hours": 48,
        },
        headers={"X-Agency-ID": "agency_bnd_test"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["token_id"].startswith("cap_")
    assert "VIEW_ONLY" in data["allowed_scopes"]
    assert "PROPOSE_EDIT" in data["allowed_scopes"]
    assert data["traveler_role"] == "companion"
    assert data["agency_id"] == "agency_bnd_test"


def test_verify_capability_token_endpoint(session_client):
    """Verify validating a capability token and checking scope compliance."""
    # Issue a token first
    issue_res = session_client.post(
        "/api/v1/boundaries/tokens/issue",
        json={
            "trip_id": "trip_bnd_102",
            "scopes": ["VIEW_ONLY", "ACCEPT_QUOTE"],
            "traveler_role": "primary_booker",
        },
        headers={"X-Agency-ID": "agency_bnd_test"},
    ).json()

    token_str = issue_res["token_string"]

    # Verify without scope
    verify_res = session_client.get(f"/api/v1/boundaries/tokens/{token_str}/verify")
    assert verify_res.status_code == 200
    v_data = verify_res.json()
    assert v_data["is_valid"] is True
    assert v_data["trip_id"] == "trip_bnd_102"
    assert "ACCEPT_QUOTE" in v_data["allowed_scopes"]

    # Verify with allowed scope
    scope_ok_res = session_client.get(
        f"/api/v1/boundaries/tokens/{token_str}/verify",
        params={"required_scope": "ACCEPT_QUOTE"},
    )
    assert scope_ok_res.status_code == 200
    assert scope_ok_res.json()["is_valid"] is True

    # Verify with disallowed scope
    scope_fail_res = session_client.get(
        f"/api/v1/boundaries/tokens/{token_str}/verify",
        params={"required_scope": "AUTHORIZE_PAYMENT"},
    )
    assert scope_fail_res.status_code == 200
    assert scope_fail_res.json()["is_valid"] is False
    assert "lacks required scope" in scope_fail_res.json()["message"]


def test_revoke_capability_token_endpoint(session_client):
    """Verify revoking an active capability token."""
    issue_res = session_client.post(
        "/api/v1/boundaries/tokens/issue",
        json={
            "trip_id": "trip_bnd_103",
            "scopes": ["VIEW_ONLY"],
        },
        headers={"X-Agency-ID": "agency_bnd_test"},
    ).json()

    token_id = issue_res["token_id"]
    token_str = issue_res["token_string"]

    revoke_res = session_client.post(
        f"/api/v1/boundaries/tokens/{token_id}/revoke",
        headers={"X-Agency-ID": "agency_bnd_test"},
    )
    assert revoke_res.status_code == 200
    assert revoke_res.json()["revoked"] is True

    # Verify that token is now invalid
    verify_res = session_client.get(f"/api/v1/boundaries/tokens/{token_str}/verify")
    assert verify_res.status_code == 200
    assert verify_res.json()["is_valid"] is False
    assert verify_res.json()["revoked"] is True


def test_get_authority_matrix_endpoint(session_client):
    """Verify retrieving the 5-Tier Human-AI Authority Matrix catalog."""
    response = session_client.get(
        "/api/v1/boundaries/authority-matrix",
        headers={"X-Agency-ID": "agency_bnd_test"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_actions"] >= 5
    action_names = [a["action_name"] for a in data["actions"]]
    assert "dispatch_proposal_to_client" in action_names
    assert "issue_refund_above_threshold" in action_names
