"""
tests/test_messaging_router.py — Unit & Integration tests for Omnichannel Messaging Router.
"""

import os
import pytest

os.environ["RUNNING_TESTS"] = "1"




@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    monkeypatch.setenv("DATA_PRIVACY_MODE", "beta")
    monkeypatch.setenv("SPINE_API_DISABLE_AUTH", "1")
    monkeypatch.setenv("TRIPSTORE_BACKEND", "file")


def test_send_outbound_message(session_client):
    """Verify sending an outbound message via WhatsApp Cloud API adapter."""
    # Ingest a trip first
    inbound_res = session_client.post(
        "/api/v1/inbound/parse",
        json={
            "channel": "whatsapp_web",
            "raw_text": "Honeymoon to Maldives in Dec.",
            "customer_name": "Carlos Ruiz",
        },
        headers={"X-Agency-ID": "agency_msg_test"},
    ).json()

    trip_id = inbound_res["trip_id"]

    response = session_client.post(
        "/api/v1/messaging/send",
        json={
            "trip_id": trip_id,
            "recipient": "+1555019922",
            "channel": "whatsapp",
            "content": "Hi Carlos! Your Maldives resort quote is ready.",
        },
        headers={"X-Agency-ID": "agency_msg_test"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["trip_id"] == trip_id
    assert data["channel"] == "whatsapp"
    # FND-0301 contract evolution: without provider credentials the dispatch
    # is honestly NOT_CONFIGURED (was the fake-progress "QUEUED"). SENT only
    # ever appears after a real provider acceptance.
    assert data["status"] in ("NOT_CONFIGURED", "SENT")
    assert data["dispatch_status"] == data["status"]
    assert data["provider"] == "whatsapp_cloud_api"
    assert data["message_id"].startswith("msg_")


def test_process_messaging_webhook(session_client, monkeypatch):
    """Verify processing incoming provider webhook status callbacks."""
    import hashlib
    import hmac
    secret = "test_meta_app_secret"
    monkeypatch.setenv("WHATSAPP_APP_SECRET", secret)
    body = b'{"event": "message_delivered", "message_id": "msg_89a7f201", "status": "DELIVERED"}'
    sig = "sha256=" + hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()

    response = session_client.post(
        "/api/v1/messaging/webhook/whatsapp",
        content=body,
        headers={"X-Hub-Signature-256": sig, "Content-Type": "application/json"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["provider"] == "whatsapp"
    assert data["status"] == "DELIVERED"


# ---------------------------------------------------------------------------
# B1 readiness (2026-10-26): idempotent ingestion, delivery-truth persistence,
# dispatch pre-flight guards, operator flip-check endpoint.
# ---------------------------------------------------------------------------

def _signed_webhook(session_client, monkeypatch, payload: dict) -> dict:
    import hashlib
    import hmac
    import json

    secret = "test_meta_app_secret"
    monkeypatch.setenv("WHATSAPP_APP_SECRET", secret)
    body = json.dumps(payload).encode("utf-8")
    sig = "sha256=" + hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    response = session_client.post(
        "/api/v1/messaging/webhook/whatsapp",
        content=body,
        headers={"X-Hub-Signature-256": sig, "Content-Type": "application/json"},
    )
    assert response.status_code == 200
    return response.json()


def test_duplicate_webhook_delivery_is_idempotent(session_client, monkeypatch, tmp_path):
    """B1 at-least-once: the same provider message id delivered twice stores
    ONE row, records ONE work item, and skips the duplicate honestly."""
    monkeypatch.setenv("WAYPOINT_MESSAGES_DIR", str(tmp_path / "messages"))
    monkeypatch.setenv("WAYPOINT_WORK_ITEMS_DIR", str(tmp_path / "work_items"))
    monkeypatch.setenv("MESSAGING_WEBHOOK_AGENCY_ID", "agency_b1_idem")

    payload = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "metadata": {"display_phone_number": "15550001"},
                            "messages": [
                                {
                                    "id": "wamid.dedupe1",
                                    "from": "919876543210",
                                    "type": "text",
                                    "text": {"body": "Is the Bali quote ready?"},
                                }
                            ],
                        }
                    }
                ]
            }
        ]
    }
    first = _signed_webhook(session_client, monkeypatch, payload)
    assert first["inbound_messages_stored"] == 1
    assert first["duplicates_skipped"] == 0

    second = _signed_webhook(session_client, monkeypatch, payload)
    assert second["inbound_messages_stored"] == 0
    assert second["duplicates_skipped"] == 1

    from spine_api.services import message_store, work_intake

    rows = message_store.list_for_agency("agency_b1_idem")
    inbound_rows = [
        r
        for r in rows
        if r.get("provider_message_id") == "wamid.dedupe1" and r.get("direction") == "inbound"
    ]
    assert len(inbound_rows) == 1, "duplicate delivery must not store a second inbound row"
    # The concierge reply threads via reply_to, never by claiming the inbound id
    assert all(
        r.get("direction") != "outbound" or r.get("reply_to_provider_message_id") == "wamid.dedupe1"
        for r in rows
    )
    queue = work_intake.ranked_queue("agency_b1_idem")
    items = [i for i in queue["items"] if i.get("channel") == "whatsapp"]
    assert len(items) == 1, "duplicate delivery must not create a second work item"


def test_delivery_status_updates_outbound_row(session_client, monkeypatch, tmp_path):
    """Meta statuses[] attach delivery truth to the stored outbound row by
    provider message id; an unmatched id is honestly not-applied."""
    monkeypatch.setenv("WAYPOINT_MESSAGES_DIR", str(tmp_path / "messages"))
    monkeypatch.setenv("MESSAGING_WEBHOOK_AGENCY_ID", "agency_b1_status")
    from spine_api.services import message_store

    message_store.append_message(
        agency_id="agency_b1_status",
        channel="whatsapp",
        direction="outbound",
        from_party="15550001",
        to_party="919876543210",
        body="Your quote is ready.",
        provider_message_id="wamid.out1",
    )

    payload = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "statuses": [
                                {
                                    "id": "wamid.out1",
                                    "status": "failed",
                                    "errors": [{"code": 131047, "title": "Re-engagement message"}],
                                }
                            ]
                        }
                    }
                ]
            }
        ]
    }
    data = _signed_webhook(session_client, monkeypatch, payload)
    assert data["statuses_applied"] == 1

    rows = message_store.list_for_agency("agency_b1_status")
    out_row = next(r for r in rows if r.get("provider_message_id") == "wamid.out1")
    assert out_row["delivery_status"] == "failed"
    assert "Re-engagement" in (out_row.get("delivery_detail") or "")

    # Unmatched id: honest miss, counted as not-applied, no fabricated row
    payload2 = {
        "entry": [
            {
                "changes": [
                    {"value": {"statuses": [{"id": "wamid.never_sent", "status": "delivered"}]}}
                ]
            }
        ]
    }
    data2 = _signed_webhook(session_client, monkeypatch, payload2)
    assert data2["statuses_applied"] == 0


def test_whatsapp_dispatch_preflight_guards(monkeypatch):
    """Oversize body and digit-less recipient fail BEFORE the network call —
    the operator sees the real reason, creds or not."""
    from spine_api.services.message_dispatch import dispatch_outbound_message

    oversize = dispatch_outbound_message(
        recipient="+1555000111", channel="whatsapp", content="x" * 4097
    )
    assert oversize["dispatch_status"] == "FAILED"
    assert "4096" in oversize["detail"]

    bad_recipient = dispatch_outbound_message(
        recipient="not-a-phone", channel="whatsapp", content="hello"
    )
    assert bad_recipient["dispatch_status"] == "FAILED"
    assert "digits" in bad_recipient["detail"]


def test_channel_status_endpoint_is_the_flip_check(session_client):
    """GET /channel-status reports per-channel config truth with the exact
    missing env names — the operator verifies B1 readiness with no live send
    and no secret echo."""
    response = session_client.get(
        "/api/v1/messaging/channel-status", headers={"X-Agency-ID": "agency_msg_test"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    by_channel = {c["channel"]: c for c in data["channels"]}
    assert by_channel["whatsapp"]["provider"] == "whatsapp_cloud_api"
    assert by_channel["whatsapp"]["status"] in ("CONFIGURED", "NOT_CONFIGURED")
    if by_channel["whatsapp"]["status"] == "NOT_CONFIGURED":
        assert "WHATSAPP_ACCESS_TOKEN" in by_channel["whatsapp"]["missing_env"]
    assert "app_secret_set" in data["webhook"]
    assert "checked_at" in data
