"""
tests/test_corporate_policy_auth_boundary.py — FND-0117 / FND-0198 (EV-09) evidence.

Two layers of regression coverage:

1. AST/source assertions (kept from the original wave): the router must bind
   tenant scoping to the JWT dependency and must never re-introduce a raw
   ``X-Agency-ID`` header or ``TEST_AGENCY_ID`` fallback.

2. Real HTTP boundary tests (FND-0198/EV-09) via FastAPI TestClient with live
   JWTs (auth bypass explicitly off, see conftest ``auth_enforced`` fixture):
     - anonymous request -> 401 on every corporate_policy route;
     - valid token, wrong tenant -> 404, zero cross-tenant data, zero mutation;
     - spoofed ``approver_name`` in the body is IGNORED — the approver identity
       is the authenticated principal and the audit event records it.

Shared boundary fixtures (auth_enforced, file_tripstore, capture_audit_events,
boundary_principal_factory, boundary_trip_factory, boundary_token_factory) live
in tests/conftest.py and are re-used by tests/test_team_workflows_router.py.
"""

from __future__ import annotations

import ast
import uuid
from pathlib import Path

import pytest


ROUTER_PATH = Path(__file__).parents[1] / "spine_api" / "routers" / "corporate_policy.py"

# Canonical seeded principal (must match tests/conftest.py session_client JWT).
CANONICAL_USER_ID = "323468de-ba3d-437b-aa10-35b281a0c6a6"
CANONICAL_AGENCY_ID = "d1e3b2b6-5509-4c27-b123-4b1e02b0bf5b"

# Second-tenant boundary actors (additive, idempotent DB rows via conftest).
BOUNDARY_AGENCY_B = "agency_cp_boundary_b"
BOUNDARY_USER_B = "usr_cp_boundary_b"


@pytest.fixture(autouse=True)
def setup_boundary_env(monkeypatch):
    """Beta privacy mode: the dogfood guard fail-closes on synthetic
    boundary-trip notes in the plaintext file store (same convention as
    tests/test_tenant_isolation_http.py)."""
    monkeypatch.setenv("DATA_PRIVACY_MODE", "beta")


def _router_tree() -> ast.Module:
    return ast.parse(ROUTER_PATH.read_text(encoding="utf-8"))


def _function(tree: ast.Module, name: str) -> ast.FunctionDef:
    return next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name)


def test_corporate_policy_trip_routes_bind_agency_to_jwt_dependency():
    tree = _router_tree()
    source = ROUTER_PATH.read_text(encoding="utf-8")
    assert "Depends(get_current_agency_id)" in source
    assert "Header(" not in source
    assert "TEST_AGENCY_ID" not in source

    for name in ("audit_trip_corporate_policy", "approve_corporate_policy_override"):
        route = _function(tree, name)
        dependency_defaults = [
            ast.unparse(default)
            for default in route.args.defaults
            if isinstance(default, ast.Call)
        ]
        assert "Depends(get_current_agency_id)" in dependency_defaults


def test_corporate_policy_handlers_pass_dependency_value_to_store():
    tree = _router_tree()
    for name in ("audit_trip_corporate_policy", "approve_corporate_policy_override"):
        route = _function(tree, name)
        calls = [
            node
            for node in ast.walk(route)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "get_trip_for_agency"
        ]
        assert calls, name
        assert any(
            len(call.args) >= 2
            and isinstance(call.args[1], ast.Name)
            and call.args[1].id == "agency_id"
            for call in calls
        )


# ──────────────────────────────────────────────────────────────────────────────
# Real HTTP boundary tests (FND-0198 / EV-09) — live JWTs, no auth bypass.
# ──────────────────────────────────────────────────────────────────────────────


def test_corporate_policy_anonymous_requests_rejected_with_401(
    session_client, auth_enforced, file_tripstore, boundary_trip_factory
):
    """Every corporate_policy route must 401 without credentials (no bypass)."""
    trip_id = f"trip_cp_anon_{uuid.uuid4().hex[:8]}"
    boundary_trip_factory(trip_id, CANONICAL_AGENCY_ID)
    anon = {"Authorization": ""}

    rules = session_client.get("/api/v1/corporate/policy-rules", headers=anon)
    assert rules.status_code == 401, rules.text

    audit = session_client.post(f"/api/v1/corporate/audit-policy/{trip_id}", headers=anon, json={})
    assert audit.status_code == 401, audit.text

    override = session_client.post(
        f"/api/v1/corporate/approve-policy-override/{trip_id}",
        headers=anon,
        json={"reason": "no credentials"},
    )
    assert override.status_code == 401, override.text


def test_corporate_policy_wrong_tenant_token_gets_no_cross_tenant_data(
    session_client,
    auth_enforced,
    file_tripstore,
    boundary_principal_factory,
    boundary_trip_factory,
    boundary_token_factory,
):
    """A valid JWT from another agency cannot audit or override Agency A's trip.

    The request deliberately carries NO X-Agency-ID header: tenant scoping must
    come from the authenticated membership (JWT), and the trip must be invisible
    (404) and unmutated.
    """
    from spine_api.persistence import TripStore

    boundary_principal_factory(BOUNDARY_USER_B, BOUNDARY_AGENCY_B)
    trip_id = f"trip_cp_xt_{uuid.uuid4().hex[:8]}"
    boundary_trip_factory(trip_id, CANONICAL_AGENCY_ID)
    headers = {"Authorization": f"Bearer {boundary_token_factory(BOUNDARY_USER_B, BOUNDARY_AGENCY_B)}"}

    audit = session_client.post(f"/api/v1/corporate/audit-policy/{trip_id}", headers=headers, json={})
    assert audit.status_code == 404, audit.text

    override = session_client.post(
        f"/api/v1/corporate/approve-policy-override/{trip_id}",
        headers=headers,
        json={"trip_id": trip_id, "reason": "cross-tenant attempt"},
    )
    assert override.status_code == 404, override.text

    # Zero cross-tenant leakage in either body.
    assert CANONICAL_AGENCY_ID not in audit.text
    assert CANONICAL_AGENCY_ID not in override.text

    # Zero cross-tenant mutation: Agency A's trip is untouched.
    trip = TripStore.get_trip_for_agency(trip_id, CANONICAL_AGENCY_ID)
    assert trip is not None
    assert not trip.get("corporate_policy_override")
    assert trip["packet"]["agent_notes"] == "BOUNDARY TEST TRIP"


def test_corporate_policy_positive_path_returns_200_with_real_auth(
    session_client, auth_enforced, file_tripstore, boundary_trip_factory
):
    """Canonical owner JWT reaches the audit route: 200 with scoped trip data."""
    trip_id = f"trip_cp_pos_{uuid.uuid4().hex[:8]}"
    boundary_trip_factory(trip_id, CANONICAL_AGENCY_ID)

    resp = session_client.post(f"/api/v1/corporate/audit-policy/{trip_id}", json={})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["ok"] is True
    assert data["trip_id"] == trip_id


def test_corporate_policy_override_ignores_spoofed_approver_and_records_principal(
    session_client,
    auth_enforced,
    file_tripstore,
    boundary_trip_factory,
    capture_audit_events,
):
    """FND-0220: body.approver_name is display-only; the approver identity is
    the authenticated principal and the audit event records principal + agency.
    """
    trip_id = f"trip_cp_spoof_{uuid.uuid4().hex[:8]}"
    boundary_trip_factory(trip_id, CANONICAL_AGENCY_ID)

    resp = session_client.post(
        f"/api/v1/corporate/approve-policy-override/{trip_id}",
        json={"trip_id": trip_id, "approver_name": "Ghost Approver", "reason": "spoof attempt"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()

    # The client-declared name must NOT become the authorization identity.
    # Display name comes from the authenticated principal's DB record (varies
    # by environment); the authoritative evidence is the principal ID stored
    # on the override record and in the audit event below.
    assert data["approved_by"]
    assert data["approved_by"] != "Ghost Approver"

    from spine_api.persistence import TripStore

    trip = TripStore.get_trip_for_agency(trip_id, CANONICAL_AGENCY_ID)
    override = trip.get("corporate_policy_override") or {}
    # Dual-control: the first call stages the approval under the principal's ID.
    assert override.get("status") == "pending_second_approval"
    assert override.get("first_approved_by_id") == CANONICAL_USER_ID
    assert override.get("first_approved_by") != "Ghost Approver"

    # Audit records the authenticated principal + agency, not the spoof.
    events = [
        e
        for e in capture_audit_events
        if e["event_type"] == "corporate_policy_override_pending_second_approval"
    ]
    assert events, "override audit event was not emitted"
    event = events[-1]
    assert event["user_id"] == CANONICAL_AGENCY_ID
    assert event["details"]["first_approver_id"] == CANONICAL_USER_ID
    assert event["details"]["first_approver"] != "Ghost Approver"
