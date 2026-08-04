"""
spine_api/routers/inbound.py — Multi-Channel Ingestion & Real-Time Optimistic State Engine.

Endpoints:
  POST /api/v1/inbound/parse                  — Direct multi-channel intake (WhatsApp Web, Email, Chrome Ext)
  POST /api/v1/inbound/optimistic-sync/{trip} — Immediate client-side field reconciliation & state transition
  GET  /api/v1/inbound/stream-events/{trip}   — SSE stream broadcasting real-time trip state reconciliation

Auth model:
  Requires JWT auth via Depends(get_current_agency_id).
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from starlette.responses import StreamingResponse

from spine_api.contract import (
    InboundInquiryRequest,
    InboundInquiryResponse,
    OptimisticSyncRequest,
    OptimisticSyncResponse,
    FollowUpPromptResponse,
    SafetyResult,
)
from spine_api.core.auth import get_current_agency_id

try:
    from spine_api import persistence
except (ImportError, ValueError):
    import persistence

AuditStore = persistence.AuditStore
TripStore = persistence.TripStore

from src.intake.packet_models import SourceEnvelope  # noqa: E402
from src.intake.orchestration import run_spine_once  # noqa: E402

logger = logging.getLogger("spine_api.inbound")

router = APIRouter(prefix="/api/v1/inbound", tags=["inbound"])

# In-memory pub/sub queues for SSE trip state listeners
_TRIP_EVENT_LISTENERS: Dict[str, List[asyncio.Queue]] = {}


def _broadcast_trip_event(trip_id: str, event_type: str, payload: Dict[str, Any]) -> None:
    """Broadcast real-time state reconciliation events to connected SSE clients."""
    listeners = _TRIP_EVENT_LISTENERS.get(trip_id, [])
    if not listeners:
        return
    message = {
        "event": event_type,
        "trip_id": trip_id,
        "payload": payload,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    for queue in list(listeners):
        try:
            queue.put_nowait(message)
        except Exception as e:
            logger.debug(f"Failed to deliver SSE event to queue for trip {trip_id}: {e}")


@router.post("/parse", response_model=InboundInquiryResponse)
def parse_inbound_inquiry(
    body: InboundInquiryRequest,
    agency_id: str = Depends(get_current_agency_id),
) -> InboundInquiryResponse:
    """
    Parse unstructured multi-channel text (WhatsApp Web, Email, Chrome Extension) into a structured trip.

    Runs NB01 Intake -> NB02 Decision -> NB03 Strategy, creates/persists trip packet,
    logs audit trail, and returns instant actionable packet + draft follow-up prompt.
    """
    try:
        source_name = f"channel_{body.channel}"
        envelope = SourceEnvelope.from_freeform(
            text=body.raw_text,
            source=source_name,
            actor="agent",
        )

        spine_result = run_spine_once(
            envelopes=[envelope],
            strict_leakage=body.strict_leakage,
        )

        trip_id = f"trip_{uuid.uuid4().hex[:12]}"
        now_str = datetime.now(timezone.utc).isoformat()

        packet_dict = spine_result.packet.to_dict() if hasattr(spine_result.packet, "to_dict") else dict(spine_result.packet)
        
        if body.customer_name:
            packet_dict["customer_name"] = body.customer_name
        if body.customer_contact:
            packet_dict["customer_contact"] = body.customer_contact

        dec = getattr(spine_result.decision, "decision_state", "UNKNOWN")
        decision_state = dec.value if hasattr(dec, "value") else str(dec)
        missing_fields = getattr(spine_result.decision, "missing_fields", []) or []

        draft_prompt = None
        if hasattr(spine_result, "strategy") and spine_result.strategy:
            draft_prompt = getattr(spine_result.strategy, "traveler_followup_prompt", None)

        trip_record = {
            "id": trip_id,
            "agency_id": agency_id,
            "channel": body.channel,
            "customer_name": body.customer_name,
            "customer_contact": body.customer_contact,
            "status": "new" if missing_fields else "active",
            "decision_state": decision_state,
            "packet": packet_dict,
            "missing_fields": missing_fields,
            "agent_notes": body.agent_notes,
            "created_at": now_str,
            "updated_at": now_str,
        }

        TripStore.save_trip(trip_record)

        AuditStore.log_event(
            event_type="inbound_parse",
            user_id=agency_id,
            details={
                "trip_id": trip_id,
                "agency_id": agency_id,
                "stage": "inbound",
                "status": "success",
                "state_snapshot": decision_state,
                "actor": "chrome_extension" if body.channel == "chrome_extension" else "agency_agent",
                "reason": f"Multi-channel ingestion via {body.channel}",
            },
        )

        _broadcast_trip_event(
            trip_id=trip_id,
            event_type="TRIP_CREATED",
            payload={
                "trip_id": trip_id,
                "decision_state": decision_state,
                "missing_fields": missing_fields,
            },
        )

        leakage_dict = getattr(spine_result, "leakage_result", {}) or {}
        safety_res = SafetyResult(
            strict_leakage=body.strict_leakage,
            leakage_passed=leakage_dict.get("is_safe", True),
            leakage_errors=leakage_dict.get("leaks", []),
        )

        return InboundInquiryResponse(
            ok=True,
            trip_id=trip_id,
            channel=body.channel,
            decision_state=decision_state,
            packet=packet_dict,
            missing_fields=missing_fields,
            draft_followup_prompt=draft_prompt,
            traveler_bundle=spine_result.traveler_bundle.to_dict() if hasattr(spine_result.traveler_bundle, "to_dict") and spine_result.traveler_bundle else None,
            internal_bundle=spine_result.internal_bundle.to_dict() if hasattr(spine_result.internal_bundle, "to_dict") and spine_result.internal_bundle else None,
            safety=safety_res,
            created_at=now_str,
        )
    except Exception as e:
        logger.exception(f"Error during inbound parsing for agency {agency_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Inbound inquiry parsing failed: {str(e)}")


@router.post("/optimistic-sync/{trip_id}", response_model=OptimisticSyncResponse)
def optimistic_sync_trip_fields(
    trip_id: str,
    body: OptimisticSyncRequest,
    agency_id: str = Depends(get_current_agency_id),
) -> OptimisticSyncResponse:
    """
    Optimistically reconcile client-side field updates (budget, dates, preferences) directly
    into trip storage and recalculate state transitions instantly.
    """
    trip = TripStore.get_trip_for_agency(trip_id, agency_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    previous_state = trip.get("decision_state", "UNKNOWN")
    packet = trip.get("packet", {})

    reconciled_fields: List[str] = []
    for key, value in body.field_updates.items():
        packet[key] = value
        reconciled_fields.append(key)

    # Re-evaluate missing fields and state
    missing = []
    if not packet.get("budget_scope") and not packet.get("budget_max"):
        missing.append("budget")
    if not packet.get("start_date") and not packet.get("dates"):
        missing.append("dates")
    if not packet.get("destination"):
        missing.append("destination")

    new_state = "NEEDS_INFO" if missing else "READY_FOR_STRATEGY"
    now_str = datetime.now(timezone.utc).isoformat()

    trip["packet"] = packet
    trip["decision_state"] = new_state
    trip["missing_fields"] = missing
    trip["status"] = "new" if missing else "active"
    trip["updated_at"] = now_str

    TripStore.save_trip(trip)

    AuditStore.log_event(
        event_type="optimistic_sync",
        user_id=agency_id,
        details={
            "trip_id": trip_id,
            "agency_id": agency_id,
            "stage": "optimistic_sync",
            "status": "success",
            "state_snapshot": new_state,
            "actor": body.actor_id or "agency_agent",
            "reason": f"Optimistic field sync: {', '.join(reconciled_fields)}",
        },
    )

    _broadcast_trip_event(
        trip_id=trip_id,
        event_type="TRIP_STATE_UPDATED",
        payload={
            "trip_id": trip_id,
            "previous_state": previous_state,
            "new_state": new_state,
            "reconciled_fields": reconciled_fields,
            "missing_fields": missing,
        },
    )

    return OptimisticSyncResponse(
        ok=True,
        trip_id=trip_id,
        previous_state=previous_state,
        new_state=new_state,
        packet=packet,
        reconciled_fields=reconciled_fields,
        missing_fields=missing,
        synced_at=now_str,
    )


@router.get("/followup-prompt/{trip_id}", response_model=FollowUpPromptResponse)
async def generate_client_followup_prompt(
    trip_id: str,
    channel: str = "whatsapp",
    tone: str = "friendly",
    agency_id: str = Depends(get_current_agency_id),
):
    """
    Generate an automated, client-facing follow-up prompt for missing travel inquiry fields.
    """
    trip = TripStore.get_trip_for_agency(trip_id, agency_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    customer_name = trip.get("customer_name") or trip.get("packet", {}).get("traveler_name") or "Valued Client"
    missing_fields = trip.get("missing_fields") or []

    bullet_map = {
        "dates": "Your preferred travel dates (or approximate month/duration)",
        "destination": "Your desired destination or preferred region/vibe",
        "budget": "Your estimated total budget range (e.g. $5,000 - $8,000)",
        "travelers": "The number of travelers (adults & children)",
        "origin": "Your preferred departure city or airport",
        "accommodation": "Preferred hotel style (e.g. 4-star, luxury resort, boutique)",
    }

    questions = []
    for field in missing_fields:
        field_lower = field.lower()
        matched = False
        for key, text in bullet_map.items():
            if key in field_lower:
                questions.append(text)
                matched = True
                break
        if not matched:
            questions.append(f"Additional details regarding your {field.replace('_', ' ')}")

    if not questions:
        questions = ["Any specific flight, hotel, or activity preferences you'd like us to include?"]

    first_name = customer_name.split()[0] if customer_name else "there"

    if channel.lower() == "whatsapp":
        bullets_str = "\n".join([f"• {q}" for q in questions])
        if tone == "formal":
            formatted_msg = (
                f"Dear {customer_name},\n\n"
                f"Thank you for contacting us regarding your upcoming travel plans.\n\n"
                f"To prepare a tailored itinerary, could you please confirm:\n{bullets_str}\n\n"
                f"Best regards,\nYour Travel Team"
            )
        else:
            formatted_msg = (
                f"Hi {first_name}! 👋\n\n"
                f"Thanks for reaching out! I'm putting together options for your trip.\n\n"
                f"Could you help me with a few details to get you the best quotes?\n{bullets_str}\n\n"
                f"Looking forward to creating a great trip for you! ✈️"
            )
    else:  # email
        bullets_str = "\n".join([f"  - {q}" for q in questions])
        formatted_msg = (
            f"Dear {customer_name},\n\n"
            f"Thank you for inquiring with our travel team.\n\n"
            f"We are excited to craft your itinerary. To ensure we select the best accommodations and arrangements, could you provide the following details:\n\n"
            f"{bullets_str}\n\n"
            f"Once received, we will deliver your custom proposal.\n\n"
            f"Warm regards,\nTravel Consulting Team"
        )

    quick_replies = [
        "Oct 10-20 from SFO for 2 adults",
        "Budget $8,000 max, 5-star hotel",
        "Flexible dates in November",
    ]

    return FollowUpPromptResponse(
        ok=True,
        trip_id=trip_id,
        customer_name=customer_name,
        channel=channel,
        tone=tone,
        missing_fields=missing_fields,
        formatted_message=formatted_msg,
        quick_replies=quick_replies,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/stream-events/{trip_id}")
async def stream_trip_events(
    trip_id: str,
    agency_id: str = Depends(get_current_agency_id),
):
    """
    Server-Sent Events (SSE) stream for real-time state sync and trip state notifications.
    """
    trip = TripStore.get_trip_for_agency(trip_id, agency_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    queue: asyncio.Queue = asyncio.Queue()
    if trip_id not in _TRIP_EVENT_LISTENERS:
        _TRIP_EVENT_LISTENERS[trip_id] = []
    _TRIP_EVENT_LISTENERS[trip_id].append(queue)

    async def event_generator():
        try:
            # Initial connection heartbeat
            init_msg = json.dumps({"event": "CONNECTED", "trip_id": trip_id, "timestamp": datetime.now(timezone.utc).isoformat()})
            yield f"data: {init_msg}\n\n"

            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=15.0)
                    data_str = json.dumps(event)
                    yield f"data: {data_str}\n\n"
                except asyncio.TimeoutError:
                    # Periodic SSE heartbeat
                    ping_str = json.dumps({"event": "HEARTBEAT", "timestamp": datetime.now(timezone.utc).isoformat()})
                    yield f"data: {ping_str}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            if trip_id in _TRIP_EVENT_LISTENERS and queue in _TRIP_EVENT_LISTENERS[trip_id]:
                _TRIP_EVENT_LISTENERS[trip_id].remove(queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
