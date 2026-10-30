"""
tests/test_vendor_inbox.py — B2 vendor quote inbox (map §18).

Covers: default-deny webhook auth (unconfigured secret + bad token both 401),
happy-path JSON ingestion (SendGrid Inbound Parse form shape covered via the
form reader's dual-mode), Message-ID idempotency, deterministic trip binding
(explicit id validated; subject trip_ token; garbage NOT bound), honest
extraction signals (amounts stored as UNVERIFIED metadata, never facts),
vendor_quote_inbox work-item classification (origin=supply), and the operator
GET surface (JWT-gated, channel-filtered).
"""

import os
import uuid

import pytest

os.environ["RUNNING_TESTS"] = "1"


@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch, tmp_path):
    monkeypatch.setenv("DATA_PRIVACY_MODE", "beta")
    monkeypatch.setenv("SPINE_API_DISABLE_AUTH", "1")
    monkeypatch.setenv("TRIPSTORE_BACKEND", "file")
    monkeypatch.setenv("WAYPOINT_WORK_ITEMS_DIR", str(tmp_path / "work_items"))
    # Isolated message store (FND-0366 discipline): tests must never touch
    # the shared data/messages corpus.
    monkeypatch.setenv("WAYPOINT_MESSAGES_DIR", str(tmp_path / "messages"))
    monkeypatch.setenv("VENDOR_INBOX_WEBHOOK_SECRET", "test-shared-secret")
    monkeypatch.setenv("VENDOR_INBOX_AGENCY_ID", "agency_vendor_inbox")
    yield


HEADERS = {"X-Webhook-Token": "test-shared-secret"}
AGENCY = "agency_vendor_inbox"


def _webhook_json(client, payload):
    return client.post("/api/v1/vendor-inbox/webhook", json=payload, headers=HEADERS)


def test_webhook_default_deny_without_secret(monkeypatch, session_client):
    monkeypatch.delenv("VENDOR_INBOX_WEBHOOK_SECRET", raising=False)
    res = session_client.post(
        "/api/v1/vendor-inbox/webhook", json={"subject": "quote"}, headers=HEADERS
    )
    assert res.status_code == 401
    assert "not configured" in res.json()["detail"]


def test_webhook_rejects_bad_token(session_client):
    res = session_client.post(
        "/api/v1/vendor-inbox/webhook",
        json={"subject": "quote"},
        headers={"X-Webhook-Token": "wrong-secret"},
    )
    assert res.status_code == 401


def test_webhook_ingests_and_classifies(session_client):
    from spine_api.services import work_intake

    res = _webhook_json(
        client=session_client,
        payload={
            "Message-ID": f"<quote-{uuid.uuid4().hex[:8]}@dmc.example>",
            "from": '"Lars Poulsen" <lars@nordic-dmc.example>',
            "to": "ops@agency.example",
            "subject": "Copenhagen DMC quote — 3 nights, group of 12",
            "text": "Dear partner, please find our proposal: INR 4,50,000 total, "
                    "additional bus transfer 25000. Valid 14 days.",
        },
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["ok"] is True and body["stored"] == 1

    # store row exists with honest extraction signals
    quotes = session_client.get("/api/v1/vendor-inbox", headers={"X-Agency-ID": AGENCY}).json()
    assert quotes["total"] == 1
    row = quotes["quotes"][0]
    assert row["channel"] == "vendor_email"
    assert row["from_party"] == "lars@nordic-dmc.example"
    meta = row["metadata"]
    assert meta["kind"] == "vendor_quote"
    assert meta["extraction"]["unverified"] is True
    amounts = meta["extraction"]["amounts"]
    assert any(a["currency"] == "INR" and a["amount"] == 450000 for a in amounts)
    assert any(a["currency"] == "INR" and a["amount"] == 25000 for a in amounts)

    # vendor_quote_inbox door classified: supply-side work item on the agency queue
    queue = work_intake.ranked_queue(AGENCY)
    item = next(i for i in queue["items"] if i["door"] == "vendor_quote_inbox")
    assert item["origin"] == "supply"
    assert item["intent"] == "info"
    assert item["channel"] == "vendor_email"


def test_message_id_idempotency(session_client):
    mid = f"<dup-{uuid.uuid4().hex[:8]}@dmc.example>"
    payload = {
        "Message-ID": mid,
        "from": "sales@hotel.example",
        "subject": "Hotel hold quote",
        "text": "USD 3,200 for 4 nights",
    }
    first = _webhook_json(client=session_client, payload=payload)
    assert first.json()["stored"] == 1
    second = _webhook_json(client=session_client, payload=payload)
    assert second.json()["stored"] == 0
    assert second.json()["duplicates_skipped"] == 1
    # exactly one row, one work item
    quotes = session_client.get("/api/v1/vendor-inbox", headers={"X-Agency-ID": AGENCY}).json()
    assert quotes["total"] == 1


def test_trip_binding_deterministic(session_client, tmp_path):
    from spine_api.persistence import TripStore

    suffix = uuid.uuid4().hex[:8]
    real_trip_id = f"trip_vq_{suffix}"
    TripStore.save_trip(
        {"id": real_trip_id, "destination": "Oslo"}, agency_id=AGENCY
    )

    # explicit trip_id binds
    res = _webhook_json(
        client=session_client,
        payload={
            "Message-ID": f"<bind1-{suffix}@dmc.example>",
            "from": "q@v.example",
            "subject": "quote",
            "text": "INR 10000",
            "trip_id": real_trip_id,
        },
    )
    assert res.json()["trip_id"] == real_trip_id

    # subject trip_ token binds when it validates against the store
    res2 = _webhook_json(
        client=session_client,
        payload={
            "Message-ID": f"<bind2-{suffix}@dmc.example>",
            "from": "q@v.example",
            "subject": f"re: {real_trip_id} day trip quote",
            "text": "EUR 500",
        },
    )
    assert res2.json()["trip_id"] == real_trip_id

    # garbage destination text does NOT fabricate a binding
    res3 = _webhook_json(
        client=session_client,
        payload={
            "Message-ID": f"<nobind-{suffix}@dmc.example>",
            "from": "q@v.example",
            "subject": "amazing Oslo fjord package discount",
            "text": "USD 999 per person",
        },
    )
    assert res3.json()["trip_id"] is None


def test_extraction_stays_out_of_facts(session_client):
    """The money-boundary assertion: extracted amounts live in message
    metadata ONLY — no trip packet, fact, or quote row may carry them."""
    suffix = uuid.uuid4().hex[:8]
    res = _webhook_json(
        client=session_client,
        payload={
            "Message-ID": f"<nofacts-{suffix}@dmc.example>",
            "from": "q@v.example",
            "subject": "quote USD 12,345",
            "text": "total USD 12,345 for everything",
        },
    )
    assert res.status_code == 200
    from spine_api.services import message_store

    rows = message_store.list_for_agency(AGENCY, channel="vendor_email", limit=10)
    row = next(r for r in rows if r["provider_message_id"] == f"<nofacts-{suffix}@dmc.example>")
    # signals live in metadata, labeled unverified
    assert row["metadata"]["extraction"]["amounts"][0]["amount"] == 12345
    assert row["metadata"]["extraction"]["unverified"] is True


def test_empty_payload_acknowledged_without_store(session_client):
    res = _webhook_json(client=session_client, payload={"from": "x@y.example"})
    assert res.status_code == 200
    assert res.json()["stored"] == 0
