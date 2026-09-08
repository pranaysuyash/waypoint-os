"""
Tests for the escalated queue endpoint (register I-1).

GET /api/assignments/queue/escalated returns routing states currently in
status='escalated' for the caller's agency, oldest escalation first, server-
side accurate (the frontend chip previously sliced the workspace list
client-side and missed routing-escalated trips).
"""

import os

os.environ["RUNNING_TESTS"] = "1"
if not os.environ.get("JWT_SECRET"):
    os.environ["JWT_SECRET"] = "test-jwt-secret-for-pytest-only-32byt"

import pytest

pytestmark = [pytest.mark.require_postgres]


def test_escalated_queue_requires_db_and_returns_contract(session_client):
    """Contract test against the live SQL routing table. Uses the canonical
    test agency; read-only."""
    resp = session_client.get(
        "/api/assignments/queue/escalated",
        headers={"X-Agency-ID": "d1e3b2b6-5509-4c27-b123-4b1e02b0bf5b"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert isinstance(data["items"], list)
    assert isinstance(data["total"], int)
    for entry in data["items"]:
        assert entry["status"] == "escalated"
        assert "sla" in entry
