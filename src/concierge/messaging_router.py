"""
src/concierge/messaging_router.py — Real-Time Traveler Concierge & Multi-Channel Broadcast Router.

Coordinates traveler communication across SMS, WhatsApp, and email:
- Flight delay and gate change notifications.
- Digital hotel check-in vouchers and transport pickup alerts.
- In-trip conversational request routing (human handoff vs autonomous healing).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional


@dataclass(slots=True)
class OutboundNotification:
    recipient_phone: str
    channel: str  # "whatsapp" | "sms" | "email"
    message_type: str  # "flight_delay" | "gate_change" | "hotel_voucher" | "crisis_alert"
    content: str
    sent_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    delivery_status: str = "queued"  # "queued" | "delivered" | "failed"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class TravelerConciergeRouter:
    """Dispatches proactive alerts and manages in-trip traveler messaging."""

    @classmethod
    def create_flight_disruption_alert(
        cls,
        traveler_name: str,
        phone: str,
        flight_number: str,
        delay_minutes: int,
        alternate_flight: Optional[str] = None,
        channel: str = "whatsapp",
    ) -> OutboundNotification:
        if alternate_flight:
            body = (
                f"Hi {traveler_name}, your flight {flight_number} is delayed by {delay_minutes} mins. "
                f"We have auto-reserved your seat on alternate flight {alternate_flight}. "
                f"Reply YES to confirm or AGENT to chat with your concierge."
            )
        else:
            body = (
                f"Hi {traveler_name}, flight {flight_number} is delayed by {delay_minutes} mins. "
                f"Our concierge team is monitoring your connection and will update you shortly."
            )

        return OutboundNotification(
            recipient_phone=phone,
            channel=channel,
            message_type="flight_delay",
            content=body,
            delivery_status="queued",
            metadata={"flight_number": flight_number, "delay_minutes": delay_minutes},
        )

    @classmethod
    def create_gate_change_alert(
        cls,
        traveler_name: str,
        phone: str,
        flight_number: str,
        airport_code: str,
        new_gate: str,
        channel: str = "sms",
    ) -> OutboundNotification:
        body = f"✈️ Gate Update for {traveler_name}: Flight {flight_number} at {airport_code} has moved to Gate {new_gate}. Boarding begins in 25 mins."
        return OutboundNotification(
            recipient_phone=phone,
            channel=channel,
            message_type="gate_change",
            content=body,
            delivery_status="queued",
            metadata={"flight_number": flight_number, "gate": new_gate},
        )

    @classmethod
    def route_incoming_traveler_message(
        cls,
        sender_phone: str,
        message_text: str,
    ) -> Dict[str, Any]:
        text_lower = message_text.lower().strip()

        if "agent" in text_lower or "human" in text_lower or "help" in text_lower:
            return {
                "action": "ESCALATE_TO_HUMAN_AGENT",
                "priority": "HIGH",
                "auto_reply": "Connecting you with your dedicated travel advisor right now.",
            }
        elif "yes" in text_lower or "confirm" in text_lower:
            return {
                "action": "AUTO_CONFIRM_REBOOKING",
                "priority": "MEDIUM",
                "auto_reply": "Thank you! Your alternate rebooking is confirmed. Updated boarding pass sent below.",
            }
        elif "gate" in text_lower or "terminal" in text_lower:
            return {
                "action": "QUERY_LIVE_GATE",
                "priority": "LOW",
                "auto_reply": "Fetching live terminal and gate info for your flight.",
            }

        return {
            "action": "ROUTED_TO_CONCIERGE_AI",
            "priority": "NORMAL",
            "auto_reply": "We received your message and are assisting you immediately.",
        }
