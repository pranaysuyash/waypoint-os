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


# ---------------------------------------------------------------------------
# FND-0375: carrier/client-supplied call_sid is format-validated BEFORE any
# Twilio URL is constructed (FND-0372 class). A crafted sid ("../Accounts/
# ACevil/Calls", "CA%00", shell metachars) must be rejected at the router
# boundary and never reach provider URL interpolation.
# ---------------------------------------------------------------------------

def test_poll_rejects_malformed_call_sid(client):
    for crafted in (
        "CA%00",
        "not-a-sid",
        "CAshort",
        "ZZ" + "a" * 32,
    ):
        resp = client.get(f"/api/v1/ivr/calls/{crafted}/status")
        assert resp.status_code == 200, crafted
        data = resp.json()
        assert data["status"] == "INVALID_CALL_SID", crafted
        assert data["provider_connected"] is False, crafted
        assert data["reality_tier"] == "deterministic_preview", crafted
    # Path-traversal shapes never reach the handler at all (route mismatch).
    for crafted in ("CA../../Accounts/ACattacker/Calls", "CA%2e%2e%2fACattacker"):
        resp = client.get(f"/api/v1/ivr/calls/{crafted}/status")
        assert resp.status_code == 404, crafted


def test_poll_preview_sentinel_still_short_circuits(client):
    from spine_api.routers.ivr_gateway import _preview_call_sid

    sid = _preview_call_sid("trip_x", "6E", "+911234567890")
    resp = client.get(f"/api/v1/ivr/calls/{sid}/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "PREVIEW_ONLY"
    assert data["provider_connected"] is False


def test_sid_format_helpers():
    from spine_api.routers.ivr_gateway import (
        _account_sid_is_wellformed,
        _call_sid_is_wellformed,
    )

    assert _call_sid_is_wellformed("CA" + "a" * 32)
    assert _call_sid_is_wellformed("CA-PREVIEW-0123456789ABCDEF")
    assert not _call_sid_is_wellformed("CA" + "g" * 32)  # non-hex
    assert not _call_sid_is_wellformed("CA" + "a" * 31)  # short
    assert not _call_sid_is_wellformed("")
    assert _account_sid_is_wellformed("AC" + "a" * 32)
    assert not _account_sid_is_wellformed("CA" + "a" * 32)
