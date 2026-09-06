"""
Tests for the canonical field-merge precedence + provenance contract on
`/api/v1/inbound/optimistic-sync` (register N-3 / FINDINGS_REGISTER F-27 class).

Contract under test:
- Preference fields: customer > operator.
- Commercial/structured fields: operator > customer; unknown fields default operator.
- Precedence rejections surface as `conflicts` with the kept value (nothing silently lost).
- Every applied overwrite records provenance (actor, at, superseded).
- `expected_packet_version` mismatch → 409 (no last-write-wins corruption).
- No silent state regression: a shallow missing-field re-check cannot demote
  READY_FOR_STRATEGY unless this update itself cleared a required field.
"""

import os

os.environ["RUNNING_TESTS"] = "1"
if not os.environ.get("JWT_SECRET"):
    os.environ["JWT_SECRET"] = "test-jwt-secret-for-pytest-only-32byt"

import uuid

import pytest

from spine_api import persistence

TripStore = persistence.TripStore

AGENCY = "test_agency_merge"


@pytest.fixture(autouse=True)
def merge_test_env(monkeypatch):
    monkeypatch.setenv("DATA_PRIVACY_MODE", "beta")
    monkeypatch.setenv("SPINE_API_DISABLE_AUTH", "1")
    monkeypatch.setenv("TRIPSTORE_BACKEND", "file")


def _headers() -> dict:
    return {"X-Agency-ID": AGENCY}


def _make_trip(
    packet: dict | None = None,
    status: str = "active",
    decision_state: str = "NEEDS_INFO",
    missing_fields: list | None = None,
) -> str:
    trip_id = f"trip_{uuid.uuid4().hex[:12]}"
    TripStore.save_trip(
        {
            "id": trip_id,
            "agency_id": AGENCY,
            "channel": "whatsapp",
            "status": status,
            "decision_state": decision_state,
            "packet": packet or {},
            "missing_fields": missing_fields if missing_fields is not None else ["budget", "dates", "destination"],
            "created_at": "2026-09-01T00:00:00+00:00",
            "updated_at": "2026-09-01T00:00:00+00:00",
        },
        agency_id=AGENCY,
    )
    return trip_id


def _sync(client, trip_id: str, field_updates: dict, actor_role: str | None = None, expected_version: int | None = None):
    body: dict = {"trip_id": trip_id, "field_updates": field_updates}
    if actor_role is not None:
        body["actor_role"] = actor_role
    if expected_version is not None:
        body["expected_packet_version"] = expected_version
    return client.post(f"/api/v1/inbound/optimistic-sync/{trip_id}", json=body, headers=_headers())


def test_customer_preference_update_applies_over_operator(session_client):
    trip_id = _make_trip(packet={"accommodation": "4-star downtown"}, decision_state="READY_FOR_STRATEGY", missing_fields=[])

    resp = _sync(session_client, trip_id, {"accommodation": "boutique near the beach"}, actor_role="customer")

    assert resp.status_code == 200
    data = resp.json()
    assert data["conflicts"] == []
    assert data["packet"]["accommodation"] == "boutique near the beach"


def test_customer_commercial_update_rejected_keeps_operator_value(session_client):
    trip_id = _make_trip(packet={"budget_max": 8000}, decision_state="READY_FOR_STRATEGY", missing_fields=[])

    # Operator corrected the budget...
    resp1 = _sync(session_client, trip_id, {"budget_max": 9500}, actor_role="operator")
    assert resp1.status_code == 200

    # ...then a customer restatement must NOT silently clobber it.
    resp2 = _sync(session_client, trip_id, {"budget_max": 12000}, actor_role="customer")
    assert resp2.status_code == 200
    data = resp2.json()
    assert data["packet"]["budget_max"] == 9500
    assert len(data["conflicts"]) == 1
    conflict = data["conflicts"][0]
    assert conflict["field"] == "budget_max"
    assert conflict["requested_value"] == 12000
    assert conflict["kept_value"] == 9500
    assert conflict["kept_actor"] == "operator"


def test_operator_overrides_customer_commercial_field(session_client):
    trip_id = _make_trip(packet={"budget_max": 5000}, decision_state="NEEDS_INFO", missing_fields=["budget"])

    resp = _sync(session_client, trip_id, {"budget_max": 7250}, actor_role="operator", expected_version=0)

    assert resp.status_code == 200
    data = resp.json()
    assert data["reconciled_fields"] == ["budget_max"]
    assert data["packet"]["budget_max"] == 7250
    provenance = data["packet"]["_field_provenance"]["budget_max"]
    assert provenance["actor"] == "operator"
    assert provenance["superseded"] == 5000


def test_provenance_records_superseded_value(session_client):
    trip_id = _make_trip(packet={"accommodation": "4-star"}, decision_state="READY_FOR_STRATEGY", missing_fields=[])

    _sync(session_client, trip_id, {"accommodation": "5-star"}, actor_role="operator")
    saved = TripStore.get_trip(trip_id)
    prov = saved["packet"]["_field_provenance"]["accommodation"]
    assert prov["actor"] == "operator"
    assert prov["superseded"] == "4-star"
    assert prov["at"]


def test_reserved_provenance_key_never_writable(session_client):
    trip_id = _make_trip(packet={"budget_max": 8000}, decision_state="READY_FOR_STRATEGY", missing_fields=[])

    resp = _sync(session_client, trip_id, {"_field_provenance": {"budget_max": {"actor": "customer"}}})

    assert resp.status_code == 200
    data = resp.json()
    assert data["packet"]["_field_provenance"] == {}  # injection not applied
    assert any(c["reason"] == "provenance metadata key is system-owned" for c in data["conflicts"])


def test_stale_packet_version_returns_409(session_client):
    trip_id = _make_trip(packet={}, decision_state="NEEDS_INFO", missing_fields=["budget", "dates", "destination"])

    first = _sync(session_client, trip_id, {"budget_max": 8000}, expected_version=0)
    assert first.status_code == 200
    assert first.json()["packet_version"] == 1

    stale = _sync(session_client, trip_id, {"destination": "Tokyo"}, expected_version=0)
    assert stale.status_code == 409
    assert stale.json()["detail"]["reason"] == "stale_packet_version"
    assert stale.json()["detail"]["current"] == 1

    fresh = _sync(session_client, trip_id, {"destination": "Tokyo"}, expected_version=1)
    assert fresh.status_code == 200


def test_no_silent_state_regression_from_shallow_recheck(session_client):
    # Pipeline stored budget under a different key shape; decision state is READY_FOR_STRATEGY.
    # The router's shallow budget/dates/destination re-check must not demote it.
    trip_id = _make_trip(
        packet={"budget_total": 5000, "destination": "Kyoto", "start_date": "2026-11-05"},
        decision_state="READY_FOR_STRATEGY",
        missing_fields=[],
    )

    resp = _sync(session_client, trip_id, {"accommodation": "ryokan"}, actor_role="customer")

    assert resp.status_code == 200
    data = resp.json()
    assert data["new_state"] == "READY_FOR_STRATEGY"
    assert data["missing_fields"] == ["budget"]  # informational, not a demotion
    saved = TripStore.get_trip(trip_id)
    assert saved["decision_state"] == "READY_FOR_STRATEGY"


def test_clearing_required_field_demotes_state(session_client):
    trip_id = _make_trip(
        packet={"budget_max": 8000, "destination": "Kyoto", "start_date": "2026-11-05"},
        decision_state="READY_FOR_STRATEGY",
        missing_fields=[],
    )

    resp = _sync(session_client, trip_id, {"budget_max": None}, actor_role="operator")

    assert resp.status_code == 200
    data = resp.json()
    assert data["new_state"] == "NEEDS_INFO"
    saved = TripStore.get_trip(trip_id)
    assert saved["decision_state"] == "NEEDS_INFO"


def test_incomplete_to_ready_stays_one_trip(session_client):
    trip_id = _make_trip(packet={}, status="new", decision_state="NEEDS_INFO", missing_fields=["budget", "dates", "destination"])

    resp = _sync(
        session_client,
        trip_id,
        {"budget_max": 8000, "start_date": "2026-11-05", "destination": "Tokyo"},
        actor_role="customer",
        expected_version=0,
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["new_state"] == "READY_FOR_STRATEGY"
    assert data["trip_id"] == trip_id  # 1:1 — no new trip minted
    assert data["missing_fields"] == []
    saved = TripStore.get_trip(trip_id)
    assert saved is not None
    assert saved["status"] == "active"
    assert saved["packet_version"] == 1


def test_unknown_field_defaults_operator_precedence(session_client):
    trip_id = _make_trip(packet={"custom_vendor_note": "operator verified"}, decision_state="READY_FOR_STRATEGY", missing_fields=[])

    resp = _sync(session_client, trip_id, {"custom_vendor_note": "customer hears otherwise"}, actor_role="customer")

    assert resp.status_code == 200
    data = resp.json()
    assert data["packet"]["custom_vendor_note"] == "operator verified"
    assert len(data["conflicts"]) == 1


# ---------------------------------------------------- review cycle 2, finding B:
# optimistic-sync must never demote operator-owned statuses. Promotions are
# allowed only from the endpoint's own intake vocabulary (new + intake-blocked).


def test_sync_preserves_escalated_status(session_client):
    trip_id = _make_trip(
        packet={"budget_max": 8000, "destination": "Kyoto", "start_date": "2026-11-05"},
        status="escalated",
        decision_state="READY_FOR_STRATEGY",
        missing_fields=[],
    )

    resp = _sync(session_client, trip_id, {"accommodation": "ryokan"}, actor_role="customer")

    assert resp.status_code == 200
    saved = TripStore.get_trip(trip_id)
    assert saved["status"] == "escalated"  # a field sync must not un-escalate


def test_sync_preserves_quote_ready_status(session_client):
    trip_id = _make_trip(
        packet={"budget_max": 8000, "destination": "Kyoto", "start_date": "2026-11-05"},
        status="ready_to_quote",
        decision_state="READY_FOR_STRATEGY",
        missing_fields=[],
    )

    resp = _sync(session_client, trip_id, {"accommodation": "ryokan"}, actor_role="operator")

    assert resp.status_code == 200
    saved = TripStore.get_trip(trip_id)
    assert saved["status"] == "ready_to_quote"  # must not demote quote-capability


def test_sync_preserves_in_progress_status(session_client):
    trip_id = _make_trip(
        packet={"budget_max": 8000, "destination": "Kyoto", "start_date": "2026-11-05"},
        status="in_progress",
        decision_state="READY_FOR_STRATEGY",
        missing_fields=[],
    )

    resp = _sync(session_client, trip_id, {"accommodation": "ryokan"}, actor_role="operator")

    assert resp.status_code == 200
    saved = TripStore.get_trip(trip_id)
    assert saved["status"] == "in_progress"  # operator progress is not reset
