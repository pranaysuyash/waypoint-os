"""
spine_api.services.messaging_webhooks — Omnichannel WhatsApp / SMS webhook ingress.

Processes inbound messages from Twilio / Meta Cloud API, matches traveler phone numbers
to active itineraries, and dispatches contextual concierge responses.
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Optional

from src.agents.idempotency import IdempotencyRegistry, IdempotencyStatus

logger = logging.getLogger("spine_api.messaging_webhooks")

# Provider webhooks retry aggressively; without dedup a retried traveler message
# dispatches duplicate concierge replies (register N-1). In-process backend —
# see IdempotencyRegistry docstring for the multi-worker seam.
_IDEMPOTENCY = IdempotencyRegistry.get_instance()


@dataclass(slots=True)
class InboundMessage:
    message_id: str
    channel: str  # "whatsapp" | "sms"
    from_phone: str
    to_phone: str
    body: str
    received_at: Optional[str] = None

    def __post_init__(self):
        if self.received_at is None:
            self.received_at = datetime.now(timezone.utc).isoformat()


@dataclass(slots=True)
class OutboundConciergeReply:
    reply_to_message_id: str
    channel: str
    to_phone: str
    reply_text: str
    trip_id: Optional[str] = None
    action_taken: str = "concierge_reply"


def process_inbound_traveler_message(
    msg: InboundMessage,
    active_trip_lookup: Optional[dict[str, str]] = None,
) -> OutboundConciergeReply:
    """
    Process an inbound traveler message, identify active trip context, and construct reply.

    Idempotent per provider message_id (register N-1): a retried webhook delivery
    replays the original reply instead of dispatching a duplicate. While the first
    delivery is still processing, retries are suppressed with `duplicate_suppressed`.
    """
    idem_payload = {
        "message_id": msg.message_id,
        "channel": msg.channel,
        "from_phone": msg.from_phone,
        "to_phone": msg.to_phone,
        "body": msg.body,
    }
    idem_scope = f"concierge:{msg.to_phone}"
    idem_key = IdempotencyRegistry.generate_key(idem_scope, "traveler_message", idem_payload)
    acquired, existing = _IDEMPOTENCY.try_acquire(
        idem_key,
        trip_id=idem_scope,
        action_name="traveler_message",
        payload=idem_payload,
    )
    fencing_token = existing.fencing_token if acquired and existing is not None else None
    if not acquired:
        if (
            existing is not None
            and existing.status == IdempotencyStatus.COMPLETED
            and existing.response_payload
        ):
            return OutboundConciergeReply(**existing.response_payload)
        return OutboundConciergeReply(
            reply_to_message_id=msg.message_id,
            channel=msg.channel,
            to_phone=msg.from_phone,
            reply_text="",
            action_taken="duplicate_suppressed",
        )

    try:
        phone_clean = msg.from_phone.replace("whatsapp:", "").strip()
        trip_id = (active_trip_lookup or {}).get(phone_clean, "trip_demo_general")

        body_lower = msg.body.lower().strip()

        # Honesty rule (I-6, register F-36 family): the concierge previously
        # answered ANY flight/hotel/emergency wording with hardcoded Rome
        # itinerary facts (AZ601, Hotel de Russie, fake hotline) — fabricated
        # truth at a traveler-facing surface. Replies now state what the
        # system can honestly do, name the resolved trip, and route urgency
        # to a human without inventing a phone number.
        if any(w in body_lower for w in ("emergency", "urgent", "help", "agent", "call", "human")):
            reply_text = (
                "Your message has been flagged URGENT and your travel advisor "
                "has been notified. They will reach out on this number shortly."
            )
            action = "escalated_to_human_advisor"
        elif any(
            w in body_lower
            for w in (
                "flight", "gate", "terminal", "delay",
                "hotel", "check in", "check-in", "address", "room", "booking",
            )
        ):
            reply_text = (
                f"Thanks — your message about your trip ({trip_id}) has been logged "
                "for your travel advisor. Live flight and hotel status are not "
                "connected on this channel yet, so your advisor will confirm the "
                "details personally."
            )
            action = "logged_for_advisor"
        else:
            reply_text = (
                f"Thank you for contacting Waypoint OS. We've logged your request regarding your trip ({trip_id}). "
                f"How can our AI Concierge assist your journey today?"
            )
            action = "general_concierge_query"

        reply = OutboundConciergeReply(
            reply_to_message_id=msg.message_id,
            channel=msg.channel,
            to_phone=msg.from_phone,
            reply_text=reply_text,
            trip_id=trip_id,
            action_taken=action,
        )
        _IDEMPOTENCY.mark_completed(
            idem_key, asdict(reply), fencing_token=fencing_token
        )
        return reply
    except Exception as e:
        _IDEMPOTENCY.mark_failed(idem_key, str(e), fencing_token=fencing_token)
        raise
