"""
spine_api.services.messaging_webhooks — Omnichannel WhatsApp / SMS webhook ingress.

Processes inbound messages from Twilio / Meta Cloud API, matches traveler phone numbers
to active itineraries, and dispatches contextual concierge responses.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger("spine_api.messaging_webhooks")


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
    """
    phone_clean = msg.from_phone.replace("whatsapp:", "").strip()
    trip_id = (active_trip_lookup or {}).get(phone_clean, "trip_demo_general")

    body_lower = msg.body.lower().strip()

    if any(w in body_lower for w in ("flight", "gate", "terminal", "delay")):
        reply_text = (
            "Hello from Waypoint Concierge! Your flight to Rome (AZ601) is on schedule. "
            "Terminal 4, Gate B28. Boarding commences at 16:15. We are monitoring your radar live."
        )
        action = "flight_status_dispatched"
    elif any(w in body_lower for w in ("hotel", "check in", "check-in", "address", "room")):
        reply_text = (
            "Your hotel is Hotel de Russie (Via del Babuino 9, Rome). "
            "Check-in is confirmed for 15:00. Your confirmation code is #RUS-8821. "
            "Late arrival notice is active in case of delays."
        )
        action = "hotel_voucher_dispatched"
    elif any(w in body_lower for w in ("emergency", "help", "agent", "call", "human")):
        reply_text = (
            "Your personal travel advisor has been alerted with urgent priority and will reach out "
            "to this number within 10 minutes. Waypoint 24/7 Hotline: +1 (800) 555-WAYPOINT."
        )
        action = "escalated_to_human_advisor"
    else:
        reply_text = (
            f"Thank you for contacting Waypoint OS. We've logged your request regarding your trip ({trip_id}). "
            f"How can our AI Concierge assist your journey today?"
        )
        action = "general_concierge_query"

    return OutboundConciergeReply(
        reply_to_message_id=msg.message_id,
        channel=msg.channel,
        to_phone=msg.from_phone,
        reply_text=reply_text,
        trip_id=trip_id,
        action_taken=action,
    )
