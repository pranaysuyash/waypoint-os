"""
Behavior tests for Slice E team router extraction.

Covers:
- preserved unscoped get_member handler dependency profile
- list members agency scoping
- invite uses agency.id and user.id
- permission dependency presence on update/deactivate handlers
- workload agency trip filtering
"""

from __future__ import annotations

import inspect
from types import SimpleNamespace

import pytest

from server import app
from routers import team


@pytest.fixture(autouse=True)
def override_team_dependencies():
    """Run team routes with deterministic deps and no DB/network reliance."""
    from spine_api.core.auth import get_current_membership

    original = dict(app.dependency_overrides)
    app.dependency_overrides[team.get_current_agency] = lambda: SimpleNamespace(id="agency_test")
    app.dependency_overrides[team.get_current_user] = lambda: SimpleNamespace(id="user_test")
    app.dependency_overrides[team.get_db] = lambda: SimpleNamespace(name="db_test")
    app.dependency_overrides[get_current_membership] = lambda: SimpleNamespace(
        role="owner", agency_id="agency_test", user_id="user_test"
    )
    try:
        yield
    finally:
        app.dependency_overrides = original


def _get_route(path: str, method: str):
    method = method.upper()
    for route in app.routes:
        if getattr(route, "path", None) == path and method in getattr(route, "methods", set()):
            return route
    raise AssertionError(f"Route not found: {method} {path}")


def test_get_member_handler_preserves_unscoped_dependency_profile():
    """
    Preserve extraction behavior: handler stays unscoped (no agency dependency added).
    This checks handler signature/dependency profile, not global middleware auth semantics.
    """
    params = list(inspect.signature(team.get_team_member).parameters.keys())
    assert "agency" not in params
    assert params == ["member_id", "db"]

    route = _get_route("/api/team/members/{member_id}", "GET")
    dependency_calls = [dep.call for dep in route.dependant.dependencies]
    assert team.get_db in dependency_calls
    assert team.get_current_agency not in dependency_calls


def test_list_members_is_agency_scoped(session_client, monkeypatch):
    captured = {}

    async def _list_members(db, agency_id, active_only=False):
        captured["agency_id"] = agency_id
        captured["active_only"] = active_only
        return [{"id": "m1"}, {"id": "m2"}]

    monkeypatch.setattr(team.membership_service, "list_members", _list_members)

    resp = session_client.get("/api/team/members")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 2
    assert captured["agency_id"] == "agency_test"
    assert captured["active_only"] is False


def test_invite_uses_agency_and_user_ids(session_client, monkeypatch):
    captured = {}

    async def _invite_member(**kwargs):
        captured.update(kwargs)
        return {"id": "membership-1", "email": kwargs["email"]}

    monkeypatch.setattr(team.membership_service, "invite_member", _invite_member)

    payload = {
        "email": "new.member@example.com",
        "name": "New Member",
        "role": "agent",
        "capacity": 4,
        "specializations": ["europe"],
    }
    resp = session_client.post("/api/team/invite", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True

    assert captured["agency_id"] == "agency_test"
    assert captured["invited_by"] == "user_test"
    assert captured["email"] == "new.member@example.com"
    assert captured["name"] == "New Member"
    assert captured["role"] == "agent"
    assert captured["capacity"] == 4
    assert captured["specializations"] == ["europe"]


def test_update_and_deactivate_preserve_permission_dependency_presence():
    update_params = list(inspect.signature(team.update_team_member).parameters.keys())
    deactivate_params = list(inspect.signature(team.deactivate_team_member).parameters.keys())

    assert "_perm" in update_params
    assert "_perm" in deactivate_params


def test_workload_uses_agency_trip_filtering(session_client, monkeypatch):
    async def _list_members(db, agency_id, active_only=False):
        assert agency_id == "agency_test"
        assert active_only is True
        return [
            {"id": "member-1", "name": "Alice", "role": "agent", "capacity": 3},
            {"id": "member-2", "name": "Bob", "role": "agent", "capacity": 2},
        ]

    monkeypatch.setattr(team.membership_service, "list_members", _list_members)

    assignments = {
        "a1": {"agent_id": "member-1", "trip_id": "trip-agency"},
        "a2": {"agent_id": "member-1", "trip_id": "trip-other"},
        "a3": {"agent_id": "member-2", "trip_id": "trip-agency"},
    }
    monkeypatch.setattr(team.AssignmentStore, "_load_assignments", lambda: assignments)
    monkeypatch.setattr(team.TripStore, "list_trips", lambda agency_id, limit=10000: [{"id": "trip-agency"}])

    resp = session_client.get("/api/team/workload")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 2

    by_member = {item["member_id"]: item for item in body["items"]}
    assert by_member["member-1"]["assigned"] == 1
    assert by_member["member-1"]["available"] == 2
    assert by_member["member-2"]["assigned"] == 1
    assert by_member["member-2"]["available"] == 1
