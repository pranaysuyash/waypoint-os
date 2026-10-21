"""
tests/test_privacy_guard_http.py — FND-0320 regression test.

Defect: a fail-closed ``PrivacyGuardError`` raised inside
``POST /api/v1/inbound/parse`` (real-user PII in the request while the
persistence mode refuses plaintext storage) escaped as a naked HTTP 500
"Internal Server Error" with no body detail. Fail-closed blocking is the
CORRECT behavior; only the error contract was wrong.

Fix: canonical exception handler in spine_api/server.py maps
``PrivacyGuardError`` → HTTP 422 with ``{"detail": {"reason", "remediation"}}``
(matching the IllegalTripStatusTransition handler pattern at server.py).
"""

from __future__ import annotations

import os

import pytest

os.environ["RUNNING_TESTS"] = "1"


@pytest.fixture(autouse=True)
def dogfood_guard_env(monkeypatch):
    """Force the guard to fail closed: dogfood mode blocks real-user PII
    regardless of backend. The mode is read at call time (is_dogfood_mode),
    so a monkeypatched env var is sufficient."""
    monkeypatch.setenv("DATA_PRIVACY_MODE", "dogfood")
    monkeypatch.setenv("SPINE_API_DISABLE_AUTH", "1")
    monkeypatch.setenv("TRIPSTORE_BACKEND", "file")


def test_inbound_parse_with_real_pii_returns_422_not_500():
    from fastapi.testclient import TestClient
    from spine_api.server import app

    client = TestClient(app)
    resp = client.post(
        "/api/v1/inbound/parse",
        json={
            "channel": "email",
            "raw_text": "Trip to Kyoto in March for 2 people.",
            "customer_name": "Real Person",
            "customer_contact": "real.person@gmail.com",
        },
        headers={"X-Agency-ID": "agency_custmem_test"},
    )
    assert resp.status_code == 422, (
        f"guarded request must be a client error, got {resp.status_code}: {resp.text}"
    )
    body = resp.json()
    assert "detail" in body
    detail = body["detail"]
    # The guard's reason string must surface (not be swallowed):
    assert detail["reason"], "reason must carry the guard's block message"
    assert "Real user trip data" in detail["reason"]
    assert "ENCRYPTION_KEY" in detail["remediation"]


def test_run_meta_with_none_fixture_id_does_not_bypass_privacy_guard():
    """AUD-01 / FND-0315 regression: RunMeta serializes ``fixture_id: None`` on
    every live ``/run`` trip. It must NOT be classified as a known fixture."""
    from src.security.privacy_guard import (
        PrivacyGuardError,
        _is_known_fixture,
        check_trip_data,
    )

    live_run_trip = {
        "source": "spine_api",
        "raw_input": {
            "stage": "discovery",
            "operating_mode": "normal_intake",
            "fixture_id": None,
            "execution_ms": 42.0,
        },
        "extracted": {
            "facts": {
                "contact_email": {
                    "value": "real.traveler@gmail.com",
                    "authority_level": "explicit_owner",
                }
            }
        },
    }
    assert _is_known_fixture(live_run_trip) is False
    with pytest.raises(PrivacyGuardError):
        check_trip_data(live_run_trip)
