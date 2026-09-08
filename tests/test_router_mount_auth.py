"""
tests/test_router_mount_auth.py — PA-09 S2 evidence (2026-09-06).

FAILED BEFORE: ``distribution``, ``negotiation``, ``crisis_ops``, and
``subagent_payouts`` were included in spine_api/server.py with NO include-level
auth dependency — subagent_payouts is the advisor-payout (money-adjacent)
surface, reachable with zero credentials.

PASSES AFTER: all four mounts carry ``dependencies=[Depends(_auth_or_skip)]``
(the same include-level pattern as every other protected router), so the
AuthMiddleware's 401 applies to an unauthenticated request. One endpoint per
router is probed below with no bearer token while the local auth-bypass env
is explicitly cleared.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from spine_api.server import app


@pytest.fixture()
def auth_enforced_client(monkeypatch):
    """Ensure the local-only auth bypass is OFF for these requests."""
    monkeypatch.delenv("SPINE_API_DISABLE_AUTH", raising=False)
    return TestClient(app, raise_server_exceptions=False)


@pytest.mark.parametrize(
    "method,path",
    [
        ("GET", "/api/v1/subagent-payouts/ADV-PA09/ledger"),
        ("POST", "/api/v1/negotiation/sessions/start"),
        ("POST", "/api/v1/crisis/incidents/declare"),
        ("POST", "/api/v1/distribution/gds/parse-edifact"),
    ],
)
def test_pa09_mounts_reject_unauthenticated(auth_enforced_client, method, path):
    resp = auth_enforced_client.request(method, path, json={})
    assert resp.status_code == 401, f"{method} {path} -> {resp.status_code}"
    assert resp.json()["detail"] in {
        "Not authenticated",
        "Invalid or expired token",
    }
