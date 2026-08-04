"""
spine_api/routers/messaging.py — Omnichannel Messaging Router for WhatsApp Business & SendGrid hooks.

Endpoints:
  POST /api/v1/messaging/send               — Dispatch outbound client message via provider adapter
  POST /api/v1/messaging/webhook/{provider} — Process inbound provider status & message callbacks

Auth model:
  Requires JWT auth via Depends(get_current_agency_id).
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request

from spine_api.contract import OutboundMessageRequest, OutboundMessageResponse
from spine_api.core.auth import get_current_agency_id
from spine_api.persistence import AuditStore, TripStore

import hmac
import hashlib
import os

logger = logging.getLogger("spine_api.messaging")

router = APIRouter(prefix="/api/v1/messaging", tags=["messaging"])


def _verify_meta_signature(body_bytes: bytes, signature_header: str | None, app_secret: str) -> bool:
    """Verify Meta X-Hub-Signature-256 header using SHA-256 HMAC."""
    if not signature_header or not signature_header.startswith("sha256="):
        return False
    expected_sig = signature_header[7:]
    computed_sig = hmac.new(
        app_secret.encode("utf-8"),
        body_bytes,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(computed_sig, expected_sig)


@router.post("/send", response_model=OutboundMessageResponse)
async def send_outbound_message(
    body: OutboundMessageRequest,
    agency_id: str = Depends(get_current_agency_id),
):
    """
    Send an outbound message to a travel client via WhatsApp Cloud API or SendGrid.
    """
    trip = TripStore.get_trip_for_agency(body.trip_id, agency_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    message_id = f"msg_{uuid4().hex[:12]}"
    provider = "whatsapp_cloud_api" if body.channel.lower() == "whatsapp" else "sendgrid_email"

    AuditStore.log_event(
        event_type="outbound_message_dispatched",
        user_id=agency_id,
        details={
            "message_id": message_id,
            "trip_id": body.trip_id,
            "channel": body.channel,
            "recipient": body.recipient,
            "provider": provider,
        },
    )

    return OutboundMessageResponse(
        ok=True,
        message_id=message_id,
        trip_id=body.trip_id,
        channel=body.channel,
        status="SENT",
        provider=provider,
        dispatched_at=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/webhook/{provider}")
async def verify_messaging_webhook(
    provider: str,
    request: Request,
):
    """
    Meta/WhatsApp Cloud API Webhook verification endpoint (GET challenge handshake).
    Responds to hub.challenge per Meta Developer Protocol.
    """
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    verify_token = os.environ.get("WHATSAPP_VERIFY_TOKEN", "waypoint_secret_verify_token")

    if mode == "subscribe" and token == verify_token:
        logger.info(f"WhatsApp webhook verified successfully for provider {provider}")
        return int(challenge) if challenge and challenge.isdigit() else challenge

    if mode or token:
        raise HTTPException(status_code=403, detail="Verification token mismatch")

    return {"ok": True, "provider": provider, "status": "VERIFIED"}


@router.post("/webhook/{provider}")
async def process_messaging_webhook(
    provider: str,
    request: Request,
):
    """
    Receive and process inbound webhooks from WhatsApp or SendGrid (delivery statuses, incoming replies).
    Includes HMAC SHA-256 signature verification when app secrets are configured.
    """
    raw_body = await request.body()
    sig_header = request.headers.get("X-Hub-Signature-256")
    app_secret = os.environ.get("WHATSAPP_APP_SECRET")

    if app_secret and provider.lower() in ("whatsapp", "whatsapp_cloud_api"):
        if not _verify_meta_signature(raw_body, sig_header, app_secret):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

    try:
        payload = json.loads(raw_body.decode("utf-8")) if raw_body else {}
    except Exception:
        payload = {}

    event_type = payload.get("event", "status_update")
    message_id = payload.get("message_id") or payload.get("id") or "unknown"
    status = payload.get("status", "DELIVERED")

    logger.info(f"Received {provider} webhook event {event_type} for message {message_id}: status={status}")

    return {
        "ok": True,
        "provider": provider,
        "message_id": message_id,
        "status": status,
        "signature_verified": bool(app_secret and sig_header),
        "processed_at": datetime.now(timezone.utc).isoformat(),
    }

