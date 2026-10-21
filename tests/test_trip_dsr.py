"""T14: trip data-subject rights — Art. 15/20 export + Art. 17 structural erasure.

Covers: portable export composition (personal + messages + planning context),
erasure scrubbing (trip fields + packet fields + raw_input tombstone), message
tombstoning by phone match, signed certificates (fail-closed without a key),
explicit-confirm gate, and tenant scoping.
"""

import json

import pytest
from starlette.testclient import TestClient

from spine_api.server import app

client = TestClient(app)

TRIP = {
    "id": "trip_dsr_1",
    "agency_id": "agency_dsr",
    "contact_name": "Meera Sharma",
    "contact_phone": "+91 98200 00111",
    "contact_email": "meera@example.com",
    "customer_name": "Meera Sharma",
    "raw_input": {"encrypted": "blob"},
    "created_at": "2026-09-20T10:00:00+00:00",
    "packet": {
        "destination": "Kerala",
        "party_size": 4,
        "start_date": "2026-12-15",
        "end_date": "2026-12-20",
        "customer_contact": "meera@example.com",
    },
    "decision": {},
    "strategy": {},
}


@pytest.fixture()
def message_store(tmp_path, monkeypatch):
    monkeypatch.setenv("WAYPOINT_MESSAGES_DIR", str(tmp_path / "messages"))
    from spine_api.services import message_store

    return message_store


@pytest.fixture(autouse=True)
def _env(monkeypatch, tmp_path):
    from types import SimpleNamespace

    monkeypatch.setenv("SPINE_API_DISABLE_AUTH", "1")
    monkeypatch.setenv("GDPR_SIGNING_KEY", "dsr-test-signing-key-0123456789abcdef")
    monkeypatch.setenv("WAYPOINT_MESSAGES_DIR", str(tmp_path / "messages"))
    original = dict(app.dependency_overrides)
    app.dependency_overrides[
        __import__("spine_api.core.auth", fromlist=["get_current_agency"]).get_current_agency
    ] = lambda: SimpleNamespace(id="agency_dsr")
    try:
        yield
    finally:
        app.dependency_overrides = original


def _wire(monkeypatch, trip=TRIP):
    import spine_api.routers.dsr as dsr

    monkeypatch.setattr(
        dsr.TripStore,
        "get_trip_for_agency",
        lambda trip_id, agency_id: trip if trip_id == "trip_dsr_1" and agency_id == "agency_dsr" else None,
    )
    updates = {}

    def _update(trip_id_, agency_id_, fields):
        updates.update(fields)
        trip.update(fields)
        return trip

    monkeypatch.setattr(dsr.TripStore, "update_trip_for_agency", _update)
    return updates


def _seed_messages(message_store):
    message_store.append_message(
        agency_id="agency_dsr",
        channel="whatsapp",
        direction="inbound",
        from_party="+919820000111",
        to_party="919820000000",
        body="Mid December works for us.",
        trip_id="trip_dsr_1",
    )
    message_store.append_message(
        agency_id="agency_dsr",
        channel="whatsapp",
        direction="inbound",
        from_party="+919999990000",
        to_party="919820000000",
        body="Another traveler.",
    )


def test_export_contains_personal_data_and_messages(message_store, monkeypatch):
    _wire(monkeypatch)
    _seed_messages(message_store)
    res = client.get("/api/v1/trips/trip_dsr_1/data-export")
    assert res.status_code == 200
    data = res.json()
    assert data["personal_data"]["contact_name"] == "Meera Sharma"
    assert data["personal_data"]["contact_email"] == "meera@example.com"
    assert data["planning_context"]["destination"] == "Kerala"  # non-personal context survives
    assert any("Mid December" in (m.get("body") or "") for m in data["channel_messages"])


def test_erasure_scrubs_pii_and_tombstones_messages(message_store, monkeypatch):
    _wire(monkeypatch)
    _seed_messages(message_store)
    res = client.post("/api/v1/trips/trip_dsr_1/erasure", json={"confirm": True})
    assert res.status_code == 200
    cert = res.json()["certificate"]
    assert "contact_name" in cert["scrubbed_fields"]
    assert "packet.customer_contact" in cert["scrubbed_fields"]
    assert "raw_input" in cert["scrubbed_fields"]
    assert len(cert["tombstoned_message_ids"]) == 1  # phone-matched only
    assert cert["verification_signature"]

    # The trip record is scrubbed in place (structural tombstone).
    assert TRIP["contact_name"] == "[ERASED - GDPR ARTICLE 17]"
    assert TRIP["raw_input"]["status"] == "tombstoned"

    # Message file: matched record redacted, other traveler's record intact.
    path = message_store._agency_path("agency_dsr")
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    mine = [r for r in rows if "Mid December" in (r.get("body") or "") or r.get("gdpr_tombstone")]
    other = [r for r in rows if "Another traveler" in (r.get("body") or "")]
    assert any(r.get("gdpr_tombstone") for r in mine)
    assert other and not other[0].get("gdpr_tombstone")


def test_erasure_requires_explicit_confirm(monkeypatch):
    _wire(monkeypatch)
    res = client.post("/api/v1/trips/trip_dsr_1/erasure", json={"confirm": False})
    assert res.status_code == 422


def test_certificate_fails_closed_without_signing_key(message_store, monkeypatch):
    _wire(monkeypatch)
    monkeypatch.delenv("GDPR_SIGNING_KEY", raising=False)
    monkeypatch.delenv("ENCRYPTION_KEY", raising=False)
    res = client.post("/api/v1/trips/trip_dsr_1/erasure", json={"confirm": True})
    assert res.status_code == 503
    assert "refusing to issue unsigned" in res.json()["detail"]


def test_cross_tenant_404(monkeypatch):
    _wire(monkeypatch)
    assert client.get("/api/v1/trips/trip_other/data-export").status_code == 404
    assert client.post("/api/v1/trips/trip_other/erasure", json={"confirm": True}).status_code == 404


def test_deep_erasure_scrubs_all_compartments(message_store, monkeypatch):
    complex_trip = {
        "id": "trip_dsr_1",
        "agency_id": "agency_dsr",
        "contact_name": "Meera Sharma",
        "customer_contact": "meera@example.com",
        "raw_note": "VIP traveler note with sensitive comments",
        "extracted": {
            "destination": "Goa",
            "facts": {
                "customer_name": {"value": "Meera Sharma", "evidence_refs": ["note excerpt"]},
                "destination": {"value": "Goa", "evidence_refs": []},
            },
        },
        "booking_data": {"passenger_names": ["Meera Sharma"], "pnr": "ABC123XYZ"},
        "traveler_answers": [
            {"question_id": "q1", "answer": "I have peanut allergy", "respondent_name": "Meera Sharma"}
        ],
        "passenger_claim": {
            "framework": "EU261",
            "compensation_amount": 600,
            "passenger_name": "Meera Sharma",
            "passengers": [{"name": "Meera Sharma", "email": "meera@example.com"}],
        },
    }
    _wire(monkeypatch, trip=complex_trip)
    res = client.post("/api/v1/trips/trip_dsr_1/erasure", json={"confirm": True})
    assert res.status_code == 200
    cert = res.json()["certificate"]
    assert "booking_data" in cert["scrubbed_fields"]
    assert "traveler_answers" in cert["scrubbed_fields"]
    assert "passenger_claim" in cert["scrubbed_fields"]
    assert "extracted" in cert["scrubbed_fields"]

    # Verify in-place structural scrubbing
    assert complex_trip["booking_data"]["status"] == "tombstoned"
    assert complex_trip["raw_note"] == "[ERASED - GDPR ARTICLE 17]"
    assert complex_trip["extracted"]["facts"]["customer_name"]["value"] == "[ERASED - GDPR ARTICLE 17]"
    assert complex_trip["extracted"]["facts"]["destination"]["value"] == "Goa"  # Non-PII planning fact preserved
    assert complex_trip["traveler_answers"][0]["answer"] == "[ERASED - GDPR ARTICLE 17]"
    assert complex_trip["traveler_answers"][0]["respondent_name"] == "[ERASED - GDPR ARTICLE 17]"
    assert complex_trip["passenger_claim"]["passenger_name"] == "[ERASED - GDPR ARTICLE 17]"
    assert complex_trip["passenger_claim"]["passengers"][0]["name"] == "[ERASED - GDPR ARTICLE 17]"
    assert complex_trip["passenger_claim"]["framework"] == "EU261"  # Statutory framework preserved
    assert complex_trip["passenger_claim"]["compensation_amount"] == 600  # Statutory amount preserved


def test_gdpr_memory_engine_fails_closed_in_production(monkeypatch):
    from src.memory.gdpr_engine import GDPRMemoryEngine
    from src.memory.models import BaseMemoryItem

    monkeypatch.delenv("GDPR_SIGNING_KEY", raising=False)
    monkeypatch.delenv("ENCRYPTION_KEY", raising=False)
    monkeypatch.setenv("ENVIRONMENT", "production")

    item = BaseMemoryItem(
        memory_id="mem_1",
        agency_id="agency_dsr",
        entity_id="cust_1",
        summary="Customer likes window seat",
        tier="episodic",
    )
    with pytest.raises(RuntimeError) as exc:
        GDPRMemoryEngine.erase_entity_memories([item], "agency_dsr", "cust_1")
    assert "requires GDPR_SIGNING_KEY" in str(exc.value)

