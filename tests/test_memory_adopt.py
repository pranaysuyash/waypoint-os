"""Operator-adopted memory facts (inv-2 tranche / U13 convergence, 2026-11-03).

The hydrate surface stays display-only (ADR-008 §7 row 4); the adopt endpoint
is the explicit operator opt-in that writes on-file preference facts into the
trip packet as explicit_owner slots — below explicit_user, above derived —
through the authority-ranked fact store.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from starlette.testclient import TestClient

import spine_api.routers.customer_memory as customer_memory
from spine_api.server import app

client = TestClient(app)

AGENCY = "agency_adopt"


class _FakeProfileRow(SimpleNamespace):
    """Attribute surface of the CustomerMemoryProfile row the endpoint reads."""


def _fresh_trip() -> dict:
    return {
        "id": "trip_adopt_1",
        "destination": "Kerala",
        "customer_contact": "ravi@example.com",
        "extracted": {"facts": {}},
    }


@pytest.fixture(autouse=True)
def adopt_env(monkeypatch):
    monkeypatch.setenv("SPINE_API_DISABLE_AUTH", "1")
    profile = _FakeProfileRow(
        customer_id="cust_1",
        name="Ravi",
        dietary_requirements="jain meals",
        seating_preference="window",
        room_preference="high floor",
        last_confirmed_at=None,
    )
    trip = _fresh_trip()
    updates: dict = {}
    audit: list = []

    monkeypatch.setattr(
        customer_memory.TripStore,
        "get_trip_for_agency",
        lambda trip_id, agency_id: trip if trip_id == "trip_adopt_1" else None,
    )

    def _update(trip_id, agency_id, fields):
        if trip_id == "trip_adopt_1":
            updates.update(fields)
            trip.update(fields)
            return trip
        return None

    monkeypatch.setattr(customer_memory.TripStore, "update_trip_for_agency", _update)

    async def _noop_ensure():
        return None

    monkeypatch.setattr(customer_memory, "_ensure_profiles_table", _noop_ensure)

    class _FakeSession:
        async def __aenter__(self):
            return None

        async def __aexit__(self, *exc):
            return False

    async def _find(db, agency_id, email=None, phone=None, name=None):
        return profile

    monkeypatch.setattr(customer_memory, "rls_session", lambda agency_id: _FakeSession())
    monkeypatch.setattr(customer_memory, "_find_customer_profile_db", _find)

    monkeypatch.setattr(
        customer_memory.AuditStore,
        "log_event",
        lambda event_type, user_id, details: audit.append((event_type, details)),
    )

    yield {"profile": profile, "trip": trip, "updates": updates, "audit": audit}


_HEADERS = {"X-Agency-ID": AGENCY}


def test_adopt_writes_explicit_owner_slots_with_memory_provenance(adopt_env):
    res = client.post(
        "/api/v1/customers/hydrate-trip/trip_adopt_1/adopt", headers=_HEADERS
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["ok"] is True
    assert sorted(body["adopted"]) == [
        "dietary_requirements", "room_preference", "seat_preference",
    ]
    assert body["skipped"] == []

    facts = adopt_env["updates"]["extracted"]["facts"]
    assert facts["dietary_requirements"]["value"] == "jain meals"
    assert facts["dietary_requirements"]["authority_level"] == "explicit_owner"
    assert facts["dietary_requirements"]["extraction_mode"] == "adopted_from_memory"
    # seating_preference canonicalizes to seat_preference
    assert facts["seat_preference"]["value"] == "window"
    assert facts["room_preference"]["value"] == "high floor"

    audit = adopt_env["audit"]
    assert audit and audit[0][0] == "memory_facts_adopted"


def test_adopt_respects_field_selection(adopt_env):
    res = client.post(
        "/api/v1/customers/hydrate-trip/trip_adopt_1/adopt",
        json={"fields": ["room_preference"]},
        headers=_HEADERS,
    )
    assert res.status_code == 200
    body = res.json()
    assert body["adopted"] == ["room_preference"]
    facts = adopt_env["updates"]["extracted"]["facts"]
    assert "seat_preference" not in facts
    assert facts["room_preference"]["value"] == "high floor"


def test_adopt_skips_when_higher_authority_holds_the_slot(adopt_env):
    trip = adopt_env["trip"]
    trip["extracted"] = {
        "facts": {
            "dietary_requirements": {
                "value": "no onion no garlic (operator-corrected)",
                "confidence": 1.0,
                "authority_level": "manual_override",
                "extraction_mode": "manual_entry",
            },
        },
    }
    res = client.post(
        "/api/v1/customers/hydrate-trip/trip_adopt_1/adopt", headers=_HEADERS
    )
    assert res.status_code == 200
    body = res.json()
    assert "dietary_requirements" not in body["adopted"]
    dietary_skip = next(s for s in body["skipped"] if s["field_name"] == "dietary_requirements")
    assert "manual_override" in dietary_skip["reason"]
    facts = adopt_env["updates"]["extracted"]["facts"]
    assert facts["dietary_requirements"]["value"] == "no onion no garlic (operator-corrected)"


def test_adopt_404_without_profile(adopt_env, monkeypatch):
    async def _find_none(db, agency_id, **kw):
        return None

    monkeypatch.setattr(customer_memory, "_find_customer_profile_db", _find_none)
    res = client.post(
        "/api/v1/customers/hydrate-trip/trip_adopt_1/adopt", headers=_HEADERS
    )
    assert res.status_code == 404
    assert "No customer memory profile" in res.json()["detail"]
