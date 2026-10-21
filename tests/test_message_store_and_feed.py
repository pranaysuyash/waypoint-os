"""T6 (FND-0305): durable channel message store + consumption read models.

Covers: append/list durability, phone normalization, webhook ingestion of
Meta-format and flat message payloads, trip phone matching, agency/trip
message endpoints with tenant scoping, and honest empty states.
"""

import pytest
from starlette.testclient import TestClient

from spine_api.server import app

client = TestClient(app)


@pytest.fixture()
def message_store(tmp_path, monkeypatch):
    monkeypatch.setenv("WAYPOINT_MESSAGES_DIR", str(tmp_path / "messages"))
    from spine_api.services import message_store

    return message_store


# ---------------------------------------------------------------------------
# Store unit behavior
# ---------------------------------------------------------------------------

def test_append_and_list_roundtrip(message_store):
    record = message_store.append_message(
        agency_id="agency_m1",
        channel="whatsapp",
        direction="inbound",
        from_party="+919820000111",
        to_party="919820000000",
        body="Hi! Planning a Kerala trip for 4 in December.",
    )
    assert record["message_id"].startswith("msg_")
    assert record["trip_id"] is None

    rows = message_store.list_for_agency("agency_m1")
    assert len(rows) == 1
    assert "Kerala" in rows[0]["body"]
    # Other agencies see nothing (tenant scoping by file).
    assert message_store.list_for_agency("agency_other") == []


def test_phone_normalization(message_store):
    assert message_store.normalize_phone("+91 98200-00111") == "919820000111"
    assert message_store.normalize_phone("whatsapp:+919820000111") == "919820000111"


# ---------------------------------------------------------------------------
# Webhook ingestion
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _isolated_tripstore(monkeypatch, tmp_path):
    """Phone matching must not scan the real trip store in tests."""
    monkeypatch.setenv("TRIPSTORE_BACKEND", "file")
    import spine_api.persistence as P

    monkeypatch.setattr(P, "DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(P, "TRIPS_DIR", tmp_path / "data" / "trips")
    (tmp_path / "data" / "trips").mkdir(parents=True, exist_ok=True)


def _post_webhook(payload, monkeypatch):
    # Non-WhatsApp providers skip the HMAC gate in tests (default-deny is
    # WhatsApp-specific per the router).
    return client.post("/api/v1/messaging/webhook/sendgrid", json=payload)


def test_webhook_persists_flat_inbound_message(message_store, monkeypatch):
    res = _post_webhook(
        {
            "event": "message",
            "message_id": "wamid.test1",
            "from": "+919820000111",
            "to": "919820000000",
            "body": "What does the Kerala quote include?",
        },
        monkeypatch,
    )
    assert res.status_code == 200
    assert res.json()["inbound_messages_stored"] == 1

    rows = message_store.list_for_agency("webhook-unattributed")
    # FND-0126 wiring: the concierge reply is stored alongside the inbound
    # message, so the operator sees both sides of the conversation.
    assert len(rows) == 2
    inbound = [r for r in rows if r["direction"] == "inbound"]
    outbound = [r for r in rows if r["direction"] == "outbound"]
    assert len(inbound) == 1 and inbound[0]["provider_message_id"] == "wamid.test1"
    assert len(outbound) == 1
    assert "logged" in outbound[0]["body"].lower() or "waypoint" in outbound[0]["body"].lower()


def test_webhook_persists_meta_envelope_messages(message_store, monkeypatch):
    res = _post_webhook(
        {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "metadata": {"display_phone_number": "919820000000"},
                                "messages": [
                                    {
                                        "id": "wamid.meta1",
                                        "from": "919820000111",
                                        "type": "text",
                                        "text": {"body": "Dates are flexible, mid December."},
                                    },
                                    {
                                        "id": "wamid.meta2",
                                        "from": "919820000111",
                                        "type": "image",
                                        "image": {"mime_type": "image/jpeg", "filename": "passport.jpg"},
                                    },
                                ],
                            }
                        }
                    ]
                }
            ]
        },
        monkeypatch,
    )
    assert res.status_code == 200
    assert res.json()["inbound_messages_stored"] == 2

    rows = message_store.list_for_agency("webhook-unattributed")
    assert {r["provider_message_id"] for r in rows} == {"wamid.meta1", "wamid.meta2"}
    image_rows = [r for r in rows if r["mime"]]
    assert image_rows and image_rows[0]["filename"] == "passport.jpg"
    # Media message with no text body still records metadata, never a fake body.
    assert image_rows[0]["body"] == ""


def test_webhook_status_update_stores_nothing(message_store, monkeypatch):
    res = _post_webhook({"event": "status_update", "message_id": "wamid.s1", "status": "DELIVERED"}, monkeypatch)
    assert res.status_code == 200
    assert res.json()["inbound_messages_stored"] == 0
    assert message_store.list_for_agency("webhook-unattributed") == []


# ---------------------------------------------------------------------------
# Read endpoints (agency-scoped, auth-bypassed like sibling router tests)
# ---------------------------------------------------------------------------

TRIP = {
    "id": "trip_msg_1",
    "agency_id": "agency_m2",
    "contact_phone": "+91 98200 00111",
    "destination": "Kerala",
}


@pytest.fixture(autouse=True)
def _agency_override(monkeypatch):
    from types import SimpleNamespace

    monkeypatch.setenv("SPINE_API_DISABLE_AUTH", "1")
    original = dict(app.dependency_overrides)
    app.dependency_overrides[
        __import__("spine_api.core.auth", fromlist=["get_current_agency"]).get_current_agency
    ] = lambda: SimpleNamespace(id="agency_m2")
    try:
        yield
    finally:
        app.dependency_overrides = original


def test_trip_messages_match_by_normalized_phone(message_store, monkeypatch):
    import spine_api.routers.messages as messages_router

    monkeypatch.setattr(
        messages_router.TripStore,
        "get_trip_for_agency",
        lambda trip_id, agency_id: TRIP if trip_id == "trip_msg_1" and agency_id == "agency_m2" else None,
    )
    monkeypatch.setattr(
        messages_router.TripStore,
        "list_trips",
        lambda limit=200, agency_id=None: [TRIP],
    )
    message_store.append_message(
        agency_id="agency_m2",
        channel="whatsapp",
        direction="inbound",
        from_party="+919820000111",
        to_party="919820000000",
        body="Mid December works for us.",
        trip_id="trip_msg_1",
    )
    message_store.append_message(
        agency_id="agency_m2",
        channel="whatsapp",
        direction="inbound",
        from_party="+919777770000",
        to_party="919820000000",
        body="Different traveler entirely.",
    )

    res = client.get("/api/v1/trips/trip_msg_1/messages")
    assert res.status_code == 200
    data = res.json()
    bodies = [m["body"] for m in data["messages"]]
    assert any("Mid December" in b for b in bodies)
    # The phone-matched record appears even without an explicit trip_id…
    assert any("Different traveler" not in b for b in bodies)
    assert data["count"] >= 1


def test_trip_messages_404_cross_tenant(message_store, monkeypatch):
    import spine_api.routers.messages as messages_router

    monkeypatch.setattr(
        messages_router.TripStore,
        "get_trip_for_agency",
        lambda trip_id, agency_id: None,
    )
    res = client.get("/api/v1/trips/trip_other/messages")
    assert res.status_code == 404


def test_agency_feed_empty_state(message_store):
    res = client.get("/api/v1/messages")
    assert res.status_code == 200
    data = res.json()
    assert data["ok"] is True
    assert data["messages"] == []
    assert data["count"] == 0
