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
    assert data["status"] == "SENT"
    assert data["provider"] == "whatsapp_cloud_api"
    assert data["message_id"].startswith("msg_")


def test_process_messaging_webhook(session_client):
    """Verify processing incoming provider webhook status callbacks."""
    response = session_client.post(
        "/api/v1/messaging/webhook/whatsapp",
        json={
            "event": "message_delivered",
            "message_id": "msg_89a7f201",
            "status": "DELIVERED",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["provider"] == "whatsapp"
    assert data["status"] == "DELIVERED"
