"""
tests/test_team_workflows_router.py — Unit & Integration tests for Agency Team Workflows Engine.

Coverage:
  - Functional tests under the dev-only auth-bypass mode (original wave).
  - Real HTTP boundary tests (FND-0198/EV-09, FND-0220) with live JWTs and the
    auth bypass explicitly off (shared conftest boundary fixtures):
      * anonymous request -> 401;
      * valid token, wrong tenant -> 404 with zero cross-tenant mutation;
      * spoofed reviewer_id in the body is IGNORED — the reviewer identity is
        the authenticated principal and audit events record principal + agency.
"""

import os
import uuid

import pytest

os.environ["RUNNING_TESTS"] = "1"

from spine_api.persistence import TripStore

# Canonical seeded principal (must match tests/conftest.py session_client JWT).
CANONICAL_USER_ID = "323468de-ba3d-437b-aa10-35b281a0c6a6"
CANONICAL_AGENCY_ID = "d1e3b2b6-5509-4c27-b123-4b1e02b0bf5b"

# Second-tenant boundary actors (additive, idempotent DB rows via conftest).
BOUNDARY_AGENCY_B = "agency_team_boundary_b"
BOUNDARY_USER_B = "usr_team_boundary_b"


@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    monkeypatch.setenv("DATA_PRIVACY_MODE", "beta")
    monkeypatch.setenv("SPINE_API_DISABLE_AUTH", "1")
    monkeypatch.setenv("TRIPSTORE_BACKEND", "file")


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
    # F-03 (FND-0040): Reviewer identity is derived from authenticated session principal
    assert data["reviewer_id"] in ("323468de-ba3d-437b-aa10-35b281a0c6a6", "mgr_compliance_lead")
    assert data["decision"] == "APPROVED"

    trip = TripStore.get_trip(trip_id)
    assert trip["review_decision"] == "APPROVED"
    assert trip["reviewer_id"] == data["reviewer_id"]


# ──────────────────────────────────────────────────────────────────────────────
# Real HTTP boundary tests (FND-0198 / EV-09) — live JWTs, no auth bypass.
# Shared seam (auth_enforced / file_tripstore / capture_audit_events /
# boundary_principal_factory / boundary_trip_factory / boundary_token_factory)
# lives in tests/conftest.py.
# ──────────────────────────────────────────────────────────────────────────────


def test_team_workflows_anonymous_requests_rejected_with_401(
    session_client, auth_enforced, file_tripstore, boundary_trip_factory
):
    trip_id = f"trip_team_anon_{uuid.uuid4().hex[:8]}"
    boundary_trip_factory(trip_id, CANONICAL_AGENCY_ID)
    anon = {"Authorization": ""}

    assign = session_client.post(
        "/api/v1/team/assign",
        headers=anon,
        json={"trip_id": trip_id, "assignee_id": "usr_x", "assignee_role": "primary_agent"},
    )
    assert assign.status_code == 401, assign.text

    signoff = session_client.post(
        "/api/v1/team/review-signoff",
        headers=anon,
        json={"trip_id": trip_id, "decision": "APPROVED"},
    )
    assert signoff.status_code == 401, signoff.text


def test_team_workflows_wrong_tenant_token_cannot_mutate_foreign_trip(
    session_client,
    auth_enforced,
    file_tripstore,
    boundary_principal_factory,
    boundary_trip_factory,
    boundary_token_factory,
):
    """Valid JWT from another agency must get 404 and leave the trip untouched.

    No X-Agency-ID header is sent: scoping must come from the JWT membership.
    """
    boundary_principal_factory(BOUNDARY_USER_B, BOUNDARY_AGENCY_B)
    trip_id = f"trip_team_xt_{uuid.uuid4().hex[:8]}"
    boundary_trip_factory(trip_id, CANONICAL_AGENCY_ID)
    headers = {"Authorization": f"Bearer {boundary_token_factory(BOUNDARY_USER_B, BOUNDARY_AGENCY_B)}"}

    assign = session_client.post(
        "/api/v1/team/assign",
        headers=headers,
        json={"trip_id": trip_id, "assignee_id": "usr_intruder", "assignee_role": "primary_agent"},
    )
    assert assign.status_code == 404, assign.text

    signoff = session_client.post(
        "/api/v1/team/review-signoff",
        headers=headers,
        json={"trip_id": trip_id, "reviewer_id": "usr_intruder", "decision": "APPROVED"},
    )
    assert signoff.status_code == 404, signoff.text

    trip = TripStore.get_trip_for_agency(trip_id, CANONICAL_AGENCY_ID)
    assert trip is not None
    assert not trip.get("assigned_agent_id")
    assert not trip.get("review_decision")


def test_team_workflows_review_signoff_ignores_spoofed_reviewer_and_records_principal(
    session_client,
    auth_enforced,
    file_tripstore,
    boundary_trip_factory,
    capture_audit_events,
):
    """FND-0220: body.reviewer_id is ignored under real auth; the reviewer is
    the JWT principal and the audit event records principal + agency."""
    trip_id = f"trip_team_spoof_{uuid.uuid4().hex[:8]}"
    boundary_trip_factory(trip_id, CANONICAL_AGENCY_ID)

    resp = session_client.post(
        "/api/v1/team/review-signoff",
        json={
            "trip_id": trip_id,
            "reviewer_id": "SPOOFED_REVIEWER",
            "decision": "APPROVED",
            "feedback_notes": "spoof attempt",
        },
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["reviewer_id"] == CANONICAL_USER_ID

    trip = TripStore.get_trip_for_agency(trip_id, CANONICAL_AGENCY_ID)
    assert trip["reviewer_id"] == CANONICAL_USER_ID

    events = [e for e in capture_audit_events if e["event_type"] == "proposal_review_signoff"]
    assert events, "review signoff audit event was not emitted"
    event = events[-1]
    assert event["user_id"] == CANONICAL_AGENCY_ID
    assert event["details"]["reviewer_id"] == CANONICAL_USER_ID
    assert event["details"]["reviewer_principal_id"] == CANONICAL_USER_ID
    assert event["details"]["agency_id"] == CANONICAL_AGENCY_ID
    assert event["details"]["auth_verified"] is True


def test_team_workflows_assign_records_principal_actor_in_audit(
    session_client,
    auth_enforced,
    file_tripstore,
    boundary_trip_factory,
    capture_audit_events,
):
    """FND-0220: the assign audit event records the authenticated principal
    (actor) and the agency, and the save is agency-bound."""
    trip_id = f"trip_team_actor_{uuid.uuid4().hex[:8]}"
    boundary_trip_factory(trip_id, CANONICAL_AGENCY_ID)

    resp = session_client.post(
        "/api/v1/team/assign",
        json={
            "trip_id": trip_id,
            "assignee_id": "usr_luxury_expert_09",
            "assignee_role": "primary_agent",
            "notes": "real-auth assignment",
        },
    )
    assert resp.status_code == 200, resp.text

    trip = TripStore.get_trip_for_agency(trip_id, CANONICAL_AGENCY_ID)
    assert trip["assigned_agent_id"] == "usr_luxury_expert_09"

    events = [e for e in capture_audit_events if e["event_type"] == "trip_team_assigned"]
    assert events, "assign audit event was not emitted"
    event = events[-1]
    assert event["user_id"] == CANONICAL_AGENCY_ID
    assert event["details"]["actor_id"] == CANONICAL_USER_ID
    assert event["details"]["agency_id"] == CANONICAL_AGENCY_ID
