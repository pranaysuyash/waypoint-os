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
from typing import Any, Dict, List
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request

from spine_api.contract import OutboundMessageRequest, OutboundMessageResponse
from spine_api.core.auth import get_current_agency_id
from spine_api.persistence import AuditStore, TripStore
from spine_api.services.message_dispatch import dispatch_outbound_message

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

    # T1 slice (FND-0301): real provider dispatch when credentials exist;
    # honest NOT_CONFIGURED / FAILED otherwise. The response never claims
    # SENT without a provider accepting the message.
    result = dispatch_outbound_message(
        recipient=body.recipient,
        channel=body.channel,
        content=body.content,
    )
    dispatch_status = result["dispatch_status"]
    provider = result["provider"]

    AuditStore.log_event(
        event_type="outbound_message_dispatch",
        user_id=agency_id,
        details={
            "message_id": message_id,
            "trip_id": body.trip_id,
            "channel": body.channel,
            "recipient": body.recipient,
            "provider": provider,
            "dispatch_status": dispatch_status,
            "dispatch_detail": result["detail"],
        },
    )

    return OutboundMessageResponse(
        ok=dispatch_status in ("SENT", "NOT_CONFIGURED"),
        message_id=message_id,
        trip_id=body.trip_id,
        channel=body.channel,
        status=dispatch_status,
        provider=provider,
        dispatched_at=datetime.now(timezone.utc).isoformat(),
        dispatch_status=dispatch_status,
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

    verify_token = os.environ.get("WHATSAPP_VERIFY_TOKEN")

    # Refuse the handshake if the verify token is unset — do not fall back to a
    # hardcoded secret that would authenticate a forged verification request.
    if provider.lower() in ("whatsapp", "whatsapp_cloud_api") and not verify_token:
        raise HTTPException(
            status_code=401,
            detail="WHATSAPP_VERIFY_TOKEN is not configured; refusing webhook verification handshake",
        )

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

    # Default-deny: a webhook that mutates or records state must not accept
    # unauthenticated payloads. If the provider secret is unset, refuse rather
    # than silently processing a body that may be forged.
    if provider.lower() in ("whatsapp", "whatsapp_cloud_api"):
        if not app_secret:
            raise HTTPException(
                status_code=401,
                detail="WHATSAPP_APP_SECRET is not configured; refusing unauthenticated webhook payload",
            )
        if not _verify_meta_signature(raw_body, sig_header, app_secret):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

    try:
        payload = json.loads(raw_body.decode("utf-8")) if raw_body else {}
    except Exception:
        payload = {}

    event_type = payload.get("event", "status_update")
    message_id = payload.get("message_id") or payload.get("id") or "unknown"
    status = payload.get("status", "DELIVERED")

    # T6 (FND-0305): persist actual inbound traveler messages so operators can
    # consume them. Meta Cloud API shape (entry[].changes[].value.messages[]) is
    # the production format; the flat {event:"message", from, body} shape is
    # accepted for provider adapters/tests. Agency attribution: Meta webhooks
    # carry no JWT — the phone-number-id env binding names the agency that
    # configured this webhook; unconfigured -> messages are stored under the
    # webhook-scope agency id rather than dropped.
    stored = 0
    inbound_records: List[Dict[str, Any]] = []
    for value in _extract_meta_message_values(payload):
        for m in value.get("messages") or []:
            if not isinstance(m, dict):
                continue
            body = ""
            mime = None
            filename = None
            text_obj = m.get("text") or {}
            if isinstance(text_obj, dict):
                body = str(text_obj.get("body") or "")
            media_obj = m.get(m.get("type") or "") if isinstance(m.get("type"), str) else None
            if isinstance(media_obj, dict):
                mime = media_obj.get("mime_type")
                filename = media_obj.get("filename")
            from_phone = str(((m.get("from") or "") if isinstance(m.get("from"), str) else "") or value.get("metadata", {}).get("display_phone_number", ""))
            if not body and not mime:
                continue
            inbound_records.append(
                {
                    "provider_message_id": str(m.get("id") or "") or None,
                    "channel": "whatsapp",
                    "from_party": from_phone,
                    "to_party": str(value.get("metadata", {}).get("display_phone_number") or ""),
                    "body": body,
                    "mime": mime,
                    "filename": filename,
                    "received_at": None,
                }
            )
    flat_from = payload.get("from")
    if not inbound_records and isinstance(flat_from, str) and (payload.get("body") or payload.get("text")):
        inbound_records.append(
            {
                "provider_message_id": message_id if message_id != "unknown" else None,
                "channel": str(provider or "whatsapp").lower(),
                "from_party": flat_from,
                "to_party": str(payload.get("to") or ""),
                "body": str(payload.get("body") or payload.get("text") or ""),
                "mime": None,
                "filename": None,
                "received_at": None,
            }
        )

    if inbound_records:
        from spine_api.services import message_store
        from spine_api.services.messaging_webhooks import InboundMessage, process_inbound_traveler_message
        from spine_api.services.message_dispatch import dispatch_outbound_message

        webhook_agency = os.getenv("MESSAGING_WEBHOOK_AGENCY_ID", "").strip() or "webhook-unattributed"
        for rec in inbound_records:
            trip_id = message_store.match_trip_by_phone(webhook_agency, rec["from_party"])
            message_store.append_message(
                agency_id=webhook_agency,
                channel=rec["channel"],
                direction="inbound",
                from_party=rec["from_party"],
                to_party=rec["to_party"],
                body=rec["body"],
                trip_id=trip_id,
                mime=rec["mime"],
                filename=rec["filename"],
                provider_message_id=rec["provider_message_id"],
                received_at=rec["received_at"],
            )
            stored += 1

            # A1 work-intake classification: one WorkItem per inbound channel
            # message (authority = explicit_user — these are the traveler's
            # own words; C3 identity + C2 returning-guest ride the same call).
            # Best-effort: classification never fails the webhook.
            try:
                from spine_api.services.work_intake import classify_and_record

                classify_and_record(
                    "channel_webhook",
                    agency_id=webhook_agency,
                    text=rec["body"],
                    contact=rec["from_party"],
                    channel=rec["channel"],
                    trip_id=trip_id,
                )
            except Exception as work_item_err:
                logger.debug(
                    "Work-item classification skipped for webhook message: %s",
                    work_item_err,
                )

            # FND-0126 wiring: the concierge reply engine (honesty-hardened,
            # idempotent per provider message id) now runs on real ingested
            # messages, and its reply is dispatched through the same honest
            # provider adapter (NOT_CONFIGURED without creds) and stored so
            # the operator sees both sides of the conversation.
            if rec["body"]:
                reply = process_inbound_traveler_message(
                    InboundMessage(
                        message_id=rec["provider_message_id"] or f"local_{stored}",
                        channel=rec["channel"],
                        from_phone=rec["from_party"],
                        to_phone=rec["to_party"],
                        body=rec["body"],
                    ),
                    active_trip_lookup=({rec["from_party"]: trip_id} if trip_id else None),
                )
                if reply.reply_text:
                    dispatch_outbound_message(
                        recipient=reply.to_phone,
                        channel=reply.channel,
                        content=reply.reply_text,
                    )
                    message_store.append_message(
                        agency_id=webhook_agency,
                        channel=reply.channel,
                        direction="outbound",
                        from_party=rec["to_party"],
                        to_party=reply.to_phone,
                        body=reply.reply_text,
                        trip_id=reply.trip_id,
                        provider_message_id=reply.reply_to_message_id,
                    )

        if stored:
            AuditStore.log_event(
                event_type="inbound_messages_stored",
                user_id=webhook_agency,
                details={"provider": provider, "stored": stored},
            )

    logger.info(f"Received {provider} webhook event {event_type} for message {message_id}: status={status}")

    return {
        "ok": True,
        "provider": provider,
        "message_id": message_id,
        "status": status,
        "signature_verified": bool(app_secret and sig_header),
        "inbound_messages_stored": stored,
        "processed_at": datetime.now(timezone.utc).isoformat(),
    }


def _extract_meta_message_values(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Pull changes[].value dicts out of the Meta Cloud API webhook envelope."""
    values: List[Dict[str, Any]] = []
    for entry in payload.get("entry") or []:
        if not isinstance(entry, dict):
            continue
        for change in entry.get("changes") or []:
            if not isinstance(change, dict):
                continue
            value = change.get("value")
            if isinstance(value, dict) and value.get("messages"):
                values.append(value)
    return values

