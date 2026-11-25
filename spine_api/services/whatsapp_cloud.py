"""Normalize signed Meta events and run the Waypoint inquiry and reply workflow."""

import logging
from time import time

from spine_api.contract import InboundInquiryRequest
from spine_api.routers.inbound import ingest_inquiry
from spine_api.services import whatsapp_journal as journal
from spine_api.services.message_dispatch import dispatch_outbound_message
from spine_api.services.message_store import match_trip_by_phone
from spine_api.services.work_intake import classify_and_record

logger = logging.getLogger(__name__)


def _records(value):
    return (item for item in value if isinstance(item, dict)) if isinstance(value, list) else ()


def message_values(payload: dict):
    if payload.get("object") != "whatsapp_business_account":
        return
    for entry in _records(payload.get("entry")):
        for change in _records(entry.get("changes")):
            value = change.get("value")
            if change.get("field") == "messages" and isinstance(value, dict) and value.get("messaging_product") == "whatsapp":
                yield value


def receive(agency_id: str, inbox_id: str, payload: dict) -> dict:
    counts = {"inbound_messages_stored": 0, "duplicates_skipped": 0, "statuses_applied": 0, "events_ignored": 0}
    for value in message_values(payload):
        metadata = value.get("metadata")
        if not isinstance(metadata, dict) or metadata.get("phone_number_id") != inbox_id:
            counts["events_ignored"] += 1
            continue
        for message in _records(value.get("messages")):
            event = _normalize_message(message, metadata)
            if event is None:
                counts["events_ignored"] += 1
                continue
            claim = journal.claim_event(agency_id, inbox_id, event)
            if claim is None:
                counts["duplicates_skipped"] += 1
                continue
            counts["inbound_messages_stored"] += 1
            if claim["process"]:
                _handle_event(claim, event)
        for status in _records(value.get("statuses")):
            if isinstance(status.get("id"), str) and status["id"] and isinstance(status.get("status"), str):
                counts["statuses_applied"] += journal.apply_status(agency_id, inbox_id, {
                    "provider_message_id": status["id"], "status": status["status"],
                    "callback_id": status.get("biz_opaque_callback_data") if isinstance(status.get("biz_opaque_callback_data"), str) else None,
                    "error": _provider_error(status),
                })
    return counts


def _provider_error(status: dict) -> str | None:
    errors = [str(error["code"]) for error in _records(status.get("errors")) if isinstance(error.get("code"), int)]
    return f"Meta error {', '.join(errors)}" if errors else None


def _text(value, limit: int) -> str:
    return value[:limit] if isinstance(value, str) else ""


def _normalize_message(message: dict, metadata: dict) -> dict | None:
    provider_id = message.get("id")
    traveler = message.get("from")
    if not isinstance(provider_id, str) or not provider_id.strip() or len(provider_id) > 512:
        return None
    if not isinstance(traveler, str) or not 7 <= len(traveler) <= 15 or not traveler.isascii() or not traveler.isdecimal():
        return None
    kind = message.get("type")
    data = message.get(kind) if isinstance(kind, str) else None
    data = data if isinstance(data, dict) else {}
    timestamp = _text(message.get("timestamp"), 16)
    occurred_at = int(timestamp) if timestamp.isascii() and timestamp.isdecimal() else None
    if occurred_at is not None and not 0 < occurred_at <= int(time()):
        occurred_at = None
    return {
        "provider_id": provider_id, "traveler": traveler, "occurred_at": occurred_at,
        "body": _text(data.get("body"), 4096).strip() if kind == "text" else "",
        "display_phone": _text(metadata.get("display_phone_number"), 64),
        "mime": _text(data.get("mime_type"), 120) or None,
        "filename": _text(data.get("filename"), 255) or None,
    }


def _handle_event(claim: dict, event: dict) -> None:
    agency_id = claim["agency_id"]
    body = event["body"]
    traveler = event["traveler"]
    trip_id = None
    draft = None
    review = bool(claim["staff_id"]) or len(body) < 3
    try:
        trip_id = match_trip_by_phone(agency_id, traveler, unique_active=True)
        if not trip_id and not review:
            inquiry = ingest_inquiry(
                InboundInquiryRequest(channel="whatsapp", raw_text=body, customer_contact=traveler, strict_leakage=True),
                agency_id,
                journal_event_id=claim["event_id"],
            )
            trip_id = inquiry.trip_id
        else:
            classify_and_record("channel_webhook", agency_id=agency_id, text=body,
                                contact=traveler, channel="whatsapp", trip_id=trip_id)
        if not review:
            draft = "Thanks for sharing your enquiry. A travel advisor can review the details and follow up here."
    except Exception as exc:
        # A prior extraction might have incurred spend or saved a trip. A retry
        # must not silently repeat it. The original message is visible to staff.
        logger.warning("WhatsApp inbound needs review, event=%s error=%s", claim["event_id"], type(exc).__name__)
        review = True
    journal.finish_event(claim, trip_id=trip_id, draft=draft, review=review)


def dispatch(agency_id: str, conversation_id: str, actor_id: str, **kwargs) -> dict:
    reply, acquired = journal.prepare_dispatch(agency_id, conversation_id, actor_id, **kwargs)
    if not acquired:
        return {key: value for key, value in reply.items() if key not in {"inbox_id", "traveler"}}
    try:
        result = dispatch_outbound_message(
            recipient=reply["traveler"], channel="whatsapp", content=reply["body"],
            agency_id=agency_id, whatsapp_inbox_id=reply["inbox_id"], callback_id=reply["id"],
        )
    except Exception:
        result = {"dispatch_status": "DELIVERY_UNKNOWN", "detail": "Transport result was unavailable"}
    return journal.finish_dispatch(reply["id"], result)
