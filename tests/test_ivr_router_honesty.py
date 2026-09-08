"""
tests/test_ivr_router_honesty.py — PA-28 S2 evidence (2026-09-06).

FAILED BEFORE: the IVR bypass router reported ``"status": "success"`` for
synthesized in-memory DTMF/hold/bridge actions — a telephony simulation
presented as if a live call had been placed.

PASSES AFTER: action endpoints report ``"status": "simulated"`` plus the
repo's canonical preview/reality metadata (``reality_tier``,
``provider_connected: false``, ``effects: []``), with the ``call_session``
payload shape unchanged (additive schema change). The static carrier-profile
listing remains ``success`` (it is config data, not a telephony action).

Frontend note: the IVR panel reads ``call_session.status``
(on_hold_listening / bridged_to_advisor) — not the router's top-level
``status`` — so this change does not affect UI rendering.
"""

from __future__ import annotations

import pytest


@pytest.fixture()
def client(session_client):
    """Authenticated client: the router mount is protected (PA-09 posture)."""
    return session_client


def test_dispatch_reports_simulated_not_success(client):
    resp = client.post(
        "/api/v1/ivr-bypass/calls/dispatch",
        json={"carrier_code": "BA", "pnr_locator": "6XY7ZQ"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "simulated"
    assert data["status"] != "success"
    # Reality metadata per the repo preview pattern.
    assert data["reality_tier"] == "deterministic_preview"
    assert data["provider_connected"] is False
    assert data["effects"] == []
    assert data["metadata"]["simulation"] is True
    assert data["metadata"]["external_action"] is False
    # Engine payload shape is unchanged (additive schema change).
    assert data["call_session"]["carrier_code"] == "BA"
    assert data["call_session"]["pnr_locator"] == "6XY7ZQ"


def test_bridge_reports_simulated_not_success(client):
    resp = client.post(
        "/api/v1/ivr-bypass/calls/bridge",
        json={"session_id": "CALL-TEST-PA28", "carrier_agent_name": "Test Agent"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "simulated"
    assert data["reality_tier"] == "deterministic_preview"
    assert data["provider_connected"] is False
    assert data["effects"] == []
    assert data["call_session"]["session_id"] == "CALL-TEST-PA28"


def test_carrier_profiles_listing_is_static_config(client):
    resp = client.get("/api/v1/ivr-bypass/carriers/supported")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"  # config read, not a telephony action
    assert len(data["supported_carriers"]) >= 3
