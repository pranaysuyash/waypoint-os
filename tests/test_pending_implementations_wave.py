"""
Tests for the 2026-09-05 pending-implementations wave (I-6, I-7, I-8, F-30 runtime proof).

- I-6: messaging concierge no longer fabricates itinerary facts (Rome/hotel/
  fake hotline); urgency routes to a human; trip-scoped requests log honestly.
- I-8: SYNC_PROMOTABLE_FROM_STATUSES lives in core/trip_status.py (excludes
  escalated) and inbound optimistic-sync promotes only from that set.
- F-30 (runtime proof remaining from the parallel agent's remediation): the
  corporate-policy routes under a running app — auth bypass honored for test
  isolation, and (with bypass disabled) anonymous requests rejected.

The file-store keeps rows across runs, so every scan test uses a fresh agency.
"""

import asyncio
import os
import uuid

os.environ["RUNNING_TESTS"] = "1"
if not os.environ.get("JWT_SECRET"):
    os.environ["JWT_SECRET"] = "test-jwt-secret-for-pytest-only-32byt"

import pytest

from spine_api import persistence
from spine_api.core.trip_status import SYNC_PROMOTABLE_FROM_STATUSES
from spine_api.services.messaging_webhooks import InboundMessage, process_inbound_traveler_message

TripStore = persistence.TripStore

AGENCY = "test_agency_pending"


def _seed_corporate_trip(agency: str) -> str:
    trip_id = f"trip_{uuid.uuid4().hex[:12]}"
    TripStore.save_trip(
        {
            "id": trip_id,
            "agency_id": agency,
            "status": "assigned",
            "destination": "Tokyo",
            "strategy": {"recommended_option": {"cost": 3000.0}},
        },
        agency_id=agency,
    )
    return trip_id


_cross_trip_id_value = None


def cross_trip_id():
    global _cross_trip_id_value
    if _cross_trip_id_value is None:
        _cross_trip_id_value = _seed_corporate_trip(AGENCY)
    return _cross_trip_id_value


@pytest.fixture(autouse=True)
def pending_wave_env(monkeypatch):
    monkeypatch.setenv("DATA_PRIVACY_MODE", "beta")
    monkeypatch.setenv("TRIPSTORE_BACKEND", "file")


# ---------------------------------------------------------------- I-6


def _msg(body: str) -> InboundMessage:
    return InboundMessage(
        message_id=f"SM-{uuid.uuid4().hex[:10]}",
        channel="whatsapp",
        from_phone="whatsapp:+15550009001",
        to_phone="+15550009002",
        body=body,
    )


def test_i6_no_fabricated_itinerary_facts():
    for probe in (
        "what gate is my flight from",
        "what's my hotel address and check-in time",
        "my flight is delayed",
    ):
        reply = process_inbound_traveler_message(_msg(probe))
        assert "Rome" not in reply.reply_text
        assert "AZ601" not in reply.reply_text
        assert "Hotel de Russie" not in reply.reply_text
        assert "WAYPOINT" not in reply.reply_text.upper().replace("_", "")
        assert "Terminal 4" not in reply.reply_text


def test_i6_urgency_routes_to_human_without_fake_number():
    reply = process_inbound_traveler_message(_msg("this is an emergency, I need help"))
    assert reply.action_taken == "escalated_to_human_advisor"
    assert "advisor" in reply.reply_text.lower()
    assert "555-WAYPOINT" not in reply.reply_text
    assert "10 minutes" not in reply.reply_text


def test_i6_trip_scoped_logging_is_honest():
    reply = process_inbound_traveler_message(
        _msg("what gate is my flight from"), active_trip_lookup={"+15550009001": "trip_real42"}
    )
    assert reply.action_taken == "logged_for_advisor"
    assert "trip_real42" in reply.reply_text
    assert "not connected" in reply.reply_text


# ---------------------------------------------------------------- I-8


def test_i8_promotable_set_excludes_escalated():
    assert "escalated" not in SYNC_PROMOTABLE_FROM_STATUSES
    assert "incomplete" in SYNC_PROMOTABLE_FROM_STATUSES
    assert "needs_followup" in SYNC_PROMOTABLE_FROM_STATUSES
    assert "new" in SYNC_PROMOTABLE_FROM_STATUSES


def test_i8_inbound_module_uses_shared_constant():
    import spine_api.routers.inbound as inbound_module

    assert inbound_module.SYNC_PROMOTABLE_FROM_STATUSES is SYNC_PROMOTABLE_FROM_STATUSES


def test_i8_sync_on_escalated_trip_still_preserves_status(session_client):
    trip_id = f"trip_{uuid.uuid4().hex[:12]}"
    TripStore.save_trip(
        {
            "id": trip_id,
            "agency_id": AGENCY,
            "status": "escalated",
            "decision_state": "READY_FOR_STRATEGY",
            "packet": {"budget_max": 8000, "destination": "Kyoto", "start_date": "2026-11-05"},
            "missing_fields": [],
        },
        agency_id=AGENCY,
    )
    resp = session_client.post(
        f"/api/v1/inbound/optimistic-sync/{trip_id}",
        json={"trip_id": trip_id, "field_updates": {"accommodation": "ryokan"}, "actor_role": "customer"},
        headers={"X-Agency-ID": AGENCY},
    )
    assert resp.status_code == 200
    assert TripStore.get_trip(trip_id)["status"] == "escalated"


# ---------------------------------------------------------------- F-30 runtime proof
#
# Honest scope note: inside pytest, `PYTEST_CURRENT_TEST` makes
# `get_current_agency_id` honor X-Agency-ID for test isolation, and the shared
# session_client always carries a JWT — so a literal anonymous-HTTP 401 cannot
# be proven through TestClient (this is why the parallel agent's remediation
# doc left runtime/hosted proof open). Proven here instead:
#   1. dependency-level: with the bypass off and no token, the auth dependency
#      itself rejects (401) — the anonymous path exists and is fail-closed;
#   2. runtime: authenticated write scopes to the requested agency and persists;
#   3. runtime: cross-tenant write is an indistinguishable 404 with no write.


@pytest.fixture()
def auth_states(monkeypatch):
    """Turn the auth bypass OFF (startup assertions stay warning-only in dev)."""
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.delenv("SPINE_API_DISABLE_AUTH", raising=False)


def test_f30_dependency_rejects_anonymous_without_bypass(monkeypatch):
    import pytest as _pytest
    from fastapi import HTTPException

    from spine_api.core import auth as auth_module

    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.delenv("SPINE_API_DISABLE_AUTH", raising=False)

    class _State:
        current_user = None

    class _Request:
        state = _State()
        cookies = {}

    with _pytest.raises(HTTPException) as excinfo:
        asyncio.run(
            auth_module.get_current_user(request=_Request(), credentials=None, db=None)
        )
    assert excinfo.value.status_code == 401


def test_f30_authenticated_bypass_write_scopes_to_requested_agency(session_client):
    """Runtime proof 2/3: the write succeeds under test isolation and persists
    scoped to the requested agency."""
    trip_id = _seed_corporate_trip(AGENCY)
    resp = session_client.post(
        f"/api/v1/corporate/approve-policy-override/{trip_id}",
        json={"trip_id": trip_id, "approver_name": "Ops Lead", "reason": "approved exception"},
        headers={"X-Agency-ID": AGENCY},
    )
    assert resp.status_code == 200
    saved = TripStore.get_trip(trip_id)
    assert saved["corporate_policy_override"]["approved"] is True


def test_f30_cross_tenant_write_is_indistinguishable_denial(auth_states, session_client):
    """Runtime proof 3/3: another agency cannot override agency A's trip; the
    response is an indistinguishable 404 and nothing is written."""
    other_trip = _seed_corporate_trip(AGENCY)
    resp = session_client.post(
        f"/api/v1/corporate/approve-policy-override/{other_trip}",
        json={"trip_id": other_trip, "approver_name": "Outsider", "reason": "cross-tenant"},
        headers={"X-Agency-ID": "agency_f30_other"},
    )
    assert resp.status_code == 404
    saved = TripStore.get_trip(other_trip)
    assert "corporate_policy_override" not in saved
