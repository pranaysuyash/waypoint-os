"""Exercise the signed webhook, inbox, staff dispatch and supplier routes locally."""

import hashlib
import hmac
import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event
from time import time

import httpx
import pytest
from cryptography.fernet import Fernet

from spine_api.services import message_dispatch, whatsapp_cloud

AGENCY = "d1e3b2b6-5509-4c27-b123-4b1e02b0bf5b"
INBOX = "100000000001"
TRAVELER = "15550100123"
SECRET = "fictional-whatsapp-hmac-key"
TEST_ENCRYPTION_KEY = Fernet.generate_key().decode()
WEBHOOK = "/api/v1/messaging/webhook/whatsapp"
CONVERSATIONS = "/api/v1/messaging/whatsapp"
SUPPLIER = "/api/v1/supplier/availability/evidence"


@pytest.fixture
def managed_channel(monkeypatch, tmp_path, auth_enforced, capture_audit_events):
    monkeypatch.setenv("TRIPSTORE_BACKEND", "sql")
    monkeypatch.setenv("DATA_PRIVACY_MODE", "beta")
    monkeypatch.setenv("WAYPOINT_WHATSAPP_MANAGED_ENABLED", "1")
    monkeypatch.setenv("WHATSAPP_PHONE_NUMBER_ID", INBOX)
    monkeypatch.setenv("WHATSAPP_APP_SECRET", SECRET)
    monkeypatch.setenv("WHATSAPP_VERIFY_TOKEN", "fixture-verify-token")
    monkeypatch.setenv("WHATSAPP_ACCESS_TOKEN", "fixture-transport-token")
    monkeypatch.setenv("ENCRYPTION_KEY", TEST_ENCRYPTION_KEY)
    monkeypatch.setenv("MESSAGING_WEBHOOK_AGENCY_ID", AGENCY)
    monkeypatch.setenv("WAYPOINT_MESSAGES_DIR", str(tmp_path / "messages"))
    monkeypatch.setenv("WAYPOINT_WORK_ITEMS_DIR", str(tmp_path / "work"))

    def unexpected_network(*args, **kwargs):
        pytest.fail("A local workflow test reached transport without a test double")

    monkeypatch.setattr(message_dispatch.httpx, "post", unexpected_network)
    return tmp_path / "messages" / "whatsapp.sqlite3"


def _message(provider_id: str, *, traveler=TRAVELER, timestamp=None):
    return {
        "id": provider_id, "from": traveler, "type": "text", "timestamp": str(timestamp or int(time())),
        "text": {"body": "Two adults travelling from London to Lisbon in April 2027. Our budget is GBP 2,000."},
    }


def _post(client, *, messages=(), statuses=(), inbox=INBOX, secret=SECRET):
    value = {
        "messaging_product": "whatsapp", "metadata": {"phone_number_id": inbox, "display_phone_number": "15550100999"},
        "messages": list(messages), "statuses": list(statuses),
    }
    payload = {"object": "whatsapp_business_account", "entry": [{"changes": [{"field": "messages", "value": value}]}]}
    raw = json.dumps(payload).encode()
    digest = hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()
    return client.post(WEBHOOK, content=raw, headers={"X-Hub-Signature-256": f"sha256={digest}"})


def _conversation(client, provider_id: str):
    feed = client.get("/api/v1/messages?channel=whatsapp")
    assert feed.status_code == 200, feed.text
    inbound = next(row for row in feed.json()["messages"] if row["provider_message_id"] == provider_id)
    url = f"{CONVERSATIONS}/{inbound['conversation_id']}"
    response = client.get(url)
    assert response.status_code == 200, response.text
    return inbound, url, response.json()


def test_signed_duplicate_claim_precedes_real_inquiry_and_inbox_projection(session_client, managed_channel, monkeypatch):
    challenge = session_client.get(WEBHOOK, params={"hub.mode": "subscribe", "hub.verify_token": "fixture-verify-token", "hub.challenge": "00123"})
    assert challenge.status_code == 200 and challenge.text == "00123"
    message = _message("wamid.durable-claim")
    assert _post(session_client, messages=[message], secret="wrong-secret").status_code == 401
    assert _post(session_client, messages=[message], inbox="999").json()["inbound_messages_stored"] == 0
    assert not managed_channel.exists()

    entered, release = Event(), Event()
    calls = []
    failures = []
    real_ingest = whatsapp_cloud.ingest_inquiry

    def tracked_ingest(*args, **kwargs):
        calls.append(kwargs["journal_event_id"])
        entered.set()
        assert release.wait(20)
        try:
            return real_ingest(*args, **kwargs)
        except Exception as exc:
            failures.append(exc)
            raise

    monkeypatch.setattr(whatsapp_cloud, "ingest_inquiry", tracked_ingest)
    with ThreadPoolExecutor(max_workers=8) as pool:
        primary = pool.submit(_post, session_client, messages=[message])
        try:
            assert entered.wait(20)
            retries = [pool.submit(_post, session_client, messages=[message]) for _ in range(7)]
            assert all(response.result(timeout=20).json()["duplicates_skipped"] == 1 for response in retries)
        finally:
            release.set()
        assert primary.result(timeout=20).json()["inbound_messages_stored"] == 1

    inbound, _, conversation = _conversation(session_client, message["id"])
    assert not failures
    assert calls == [inbound["message_id"]]
    assert inbound["trip_id"] and inbound["processing_state"] == "processed"
    inbox = session_client.get("/inbox")
    assert inbox.status_code == 200 and inbound["trip_id"] in inbox.text, inbox.text
    lead = next(item for item in inbox.json()["items"] if item["id"] == inbound["trip_id"])
    assert lead["partySize"] == 2 and lead["destination"] == "Lisbon"
    assert conversation["replies"][0]["state"] == "QUEUED"
    assert message["text"]["body"].encode() not in managed_channel.read_bytes()
    assert message["from"].encode() not in managed_channel.read_bytes()
    assert _post(session_client, messages=[message]).json()["duplicates_skipped"] == 1


def test_takeover_persists_suppression_release_and_staff_reply(session_client, managed_channel, monkeypatch):
    message = _message("wamid.takeover", traveler="15550100124")
    assert _post(session_client, messages=[message]).json()["inbound_messages_stored"] == 1
    inbound, url, conversation = _conversation(session_client, message["id"])
    draft = f"{url}/replies/{conversation['replies'][0]['id']}/dispatch"
    assert session_client.post(f"{url}/ownership", json={"action": "takeover"}).json()["staff_id"]
    with sqlite3.connect(managed_channel) as conn:
        assert conn.execute("SELECT state FROM whatsapp_replies WHERE id=?", (conversation["replies"][0]["id"],)).fetchone() == ("SUPPRESSED",)
        # Model a stale queued record reaching a worker after takeover. The
        # send claim independently checks the current owner before transport.
        conn.execute("UPDATE whatsapp_replies SET state='QUEUED' WHERE id=?", (conversation["replies"][0]["id"],))
    assert session_client.post(draft).json()["state"] == "SUPPRESSED"
    followup = _message("wamid.staff-owned", traveler=message["from"])
    assert _post(session_client, messages=[followup]).json()["inbound_messages_stored"] == 1
    new_message, _, same = _conversation(session_client, followup["id"])
    assert new_message["trip_id"] == inbound["trip_id"]
    assert len(same["replies"]) == 1 and new_message["processing_state"] == "review_required"

    calls = []

    def accepted(url, **kwargs):
        calls.append(kwargs["json"])
        return httpx.Response(200, json={"messages": [{"id": "wamid.staff-out"}]})

    monkeypatch.setattr(message_dispatch.httpx, "post", accepted)
    reply = {"request_id": "staff-request-123", "content": "I can help with your Lisbon enquiry."}
    response = session_client.post(f"{url}/replies", json=reply)
    assert response.status_code == 200 and response.json()["state"] == "SENT", response.text
    assert session_client.post(f"{url}/replies", json=reply).json()["id"] == response.json()["id"]
    assert len(calls) == 1 and calls[0]["to"] == message["from"]
    assert session_client.post(f"{url}/ownership", json={"action": "release"}).json()["staff_id"] is None
    assert session_client.post(draft).json()["state"] == "SUPPRESSED"


def test_in_flight_provider_attempt_is_visible_during_takeover_and_never_replayed(session_client, managed_channel, monkeypatch):
    message = _message("wamid.in-flight", traveler="15550100127")
    _post(session_client, messages=[message]).raise_for_status()
    _, url, conversation = _conversation(session_client, message["id"])
    path = f"{url}/replies/{conversation['replies'][0]['id']}/dispatch"
    entered, release = Event(), Event()
    calls = []

    def accepted(graph_url, **kwargs):
        calls.append(graph_url)
        entered.set()
        assert release.wait(20)
        return httpx.Response(200, json={"messages": [{"id": "wamid.in-flight-out"}]})

    monkeypatch.setattr(message_dispatch.httpx, "post", accepted)
    with ThreadPoolExecutor(max_workers=1) as pool:
        dispatch = pool.submit(session_client.post, path)
        try:
            assert entered.wait(20)
            taken = session_client.post(f"{url}/ownership", json={"action": "takeover"}).json()
            assert taken["staff_id"] and taken["replies"][0]["state"] == "SENDING"
            assert session_client.post(path).json()["state"] == "SENDING"
        finally:
            release.set()
        assert dispatch.result(timeout=20).json()["state"] == "SENT"
    assert len(calls) == 1


def test_timeout_is_not_retried_and_only_matching_inbox_receipt_can_reconcile(session_client, managed_channel, monkeypatch):
    message = _message("wamid.timeout", traveler="15550100125")
    _post(session_client, messages=[message]).raise_for_status()
    _, url, conversation = _conversation(session_client, message["id"])
    reply_id = conversation["replies"][0]["id"]
    dispatch = f"{url}/replies/{reply_id}/dispatch"
    calls = []

    def timeout(graph_url, **kwargs):
        calls.append((graph_url, kwargs["json"]))
        raise httpx.ReadTimeout("fixture timed out after sending the request")

    monkeypatch.setattr(message_dispatch.httpx, "post", timeout)
    assert session_client.post(dispatch).json()["state"] == "DELIVERY_UNKNOWN"
    assert session_client.post(dispatch).json()["state"] == "DELIVERY_UNKNOWN"
    assert len(calls) == 1 and calls[0][0] == f"https://graph.facebook.com/v25.0/{INBOX}/messages"
    assert calls[0][1]["biz_opaque_callback_data"] == reply_id
    status = {"id": "wamid.out-reconciled", "status": "delivered", "biz_opaque_callback_data": reply_id}
    assert _post(session_client, statuses=[status], inbox="999").json()["statuses_applied"] == 0
    assert _post(session_client, statuses=[status]).json()["statuses_applied"] == 1
    status["status"] = "sent"
    _post(session_client, statuses=[status]).raise_for_status()
    stored_reply = session_client.get(url).json()["replies"][0]
    assert stored_reply["state"] == "SENT" and stored_reply["delivery_status"] == "delivered"


def test_interrupted_claim_remains_reviewable_and_cannot_start_extraction_twice(session_client, managed_channel, monkeypatch):
    message = _message("wamid.interrupted", traveler="15550100126")
    with monkeypatch.context() as interrupted:
        interrupted.setattr(whatsapp_cloud, "_handle_event", lambda *_: None)
        _post(session_client, messages=[message]).raise_for_status()
    with sqlite3.connect(managed_channel) as conn:
        conn.execute("UPDATE whatsapp_events SET received_at=? WHERE provider_id=?", (int(time()) - 121, message["id"]))
    assert _post(session_client, messages=[message]).json()["duplicates_skipped"] == 1
    inbound, _, conversation = _conversation(session_client, message["id"])
    assert inbound["processing_state"] == "review_required"
    assert conversation["replies"] == []


def test_provider_ids_are_inbox_scoped_and_viewers_cannot_take_over(
    session_client, managed_channel, monkeypatch, boundary_principal_factory, boundary_token_factory,
):
    other_agency = "wa-boundary-foreign"
    boundary_principal_factory("wa-boundary-owner", other_agency)
    boundary_principal_factory("wa-boundary-viewer", AGENCY, role="viewer")
    other_headers = {"Authorization": f"Bearer {boundary_token_factory('wa-boundary-owner', other_agency)}"}
    viewer_headers = {"Authorization": f"Bearer {boundary_token_factory('wa-boundary-viewer', AGENCY, role='viewer')}"}

    message = {**_message("wamid.cross-tenant", traveler="15550100128"), "type": "image", "image": {"mime_type": "image/jpeg"}}
    assert _post(session_client, messages=[message]).json()["inbound_messages_stored"] == 1
    _, url, _ = _conversation(session_client, message["id"])
    assert session_client.get(url, headers=other_headers).status_code == 404
    assert session_client.post(f"{url}/ownership", json={"action": "takeover"}, headers=other_headers).status_code == 404
    assert session_client.get(url, headers=viewer_headers).status_code == 200
    assert session_client.post(f"{url}/ownership", json={"action": "takeover"}, headers=viewer_headers).status_code == 403

    other_inbox = "100000000002"
    monkeypatch.setenv("WHATSAPP_PHONE_NUMBER_ID", other_inbox)
    assert _post(session_client, inbox=other_inbox, messages=[message]).json()["inbound_messages_stored"] == 1
    same_agency_feed = session_client.get("/api/v1/messages?channel=whatsapp").json()["messages"]
    rows = [row for row in same_agency_feed if row["provider_message_id"] == message["id"]]
    assert len(rows) == 2 and len({row["conversation_id"] for row in rows}) == 2

    monkeypatch.setenv("MESSAGING_WEBHOOK_AGENCY_ID", other_agency)
    assert _post(session_client, inbox=other_inbox, messages=[message]).json()["inbound_messages_stored"] == 1
    other_feed = session_client.get("/api/v1/messages?channel=whatsapp", headers=other_headers).json()["messages"]
    assert len(other_feed) == 1 and other_feed[0]["provider_message_id"] == message["id"]
    assert other_feed[0]["conversation_id"] not in url


def test_expired_customer_service_window_prevents_a_provider_attempt(session_client, managed_channel):
    message = _message("wamid.expired-window", traveler="15550100129", timestamp=int(time()) - 86_401)
    _post(session_client, messages=[message]).raise_for_status()
    _, url, conversation = _conversation(session_client, message["id"])
    response = session_client.post(f"{url}/replies/{conversation['replies'][0]['id']}/dispatch")
    assert response.status_code == 409 and "last 24 hours" in response.json()["detail"]
    assert session_client.get(url).json()["replies"][0]["state"] == "QUEUED"


def test_supplier_evidence_routes_current_expired_missing_busy_and_conflicting_records_to_staff(session_client, auth_enforced, monkeypatch):
    fixture = Path(__file__).parent / "fixtures" / "supplier_evidence_fictional.json"
    monkeypatch.setenv("WAYPOINT_SUPPLIER_EVIDENCE_FILE", str(fixture))
    before = fixture.read_bytes()

    def lookup(service="catamaran-morning", day=17, guests=17):
        response = session_client.get(SUPPLIER, params={
            "supplier_id": "fictional-andaman-charters", "service_id": service,
            "service_date": f"2027-04-{day}", "guests": guests,
        })
        assert response.status_code == 200, response.text
        return response.json()

    active = lookup()
    assert active["state"] == "evidence_found" and active["provenance"] == "fictional_fixture"
    assert active["rate"]["amount"] == "35000" and active["rate"]["basis"] == "per_service"
    assert active["rate"]["sources"][0]["source_record_id"] == "rate-2027-01"
    assert active["calendar"]["sources"][0]["source_url"].endswith("#2027-04-17")
    for result, reasons in (
        (lookup(day=18), ["calendar_unavailable_observed"]),
        (lookup(day=19), ["calendar_stale"]),
        (lookup(day=20), ["calendar_missing"]),
        (lookup(service="catamaran-expired"), ["rate_stale", "calendar_missing"]),
        (lookup(service="catamaran-conflict"), ["rate_conflicting", "calendar_conflicting"]),
        (lookup(guests=21), ["rate_missing", "calendar_unavailable_observed"]),
    ):
        assert result["state"] == "staff_review" and result["review_reasons"] == reasons
    assert fixture.read_bytes() == before
