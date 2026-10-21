"""
Followups router for Phase 3 Slice D extraction.

Scope: move only
- GET /followups/dashboard
- PATCH /followups/{trip_id}/mark-complete
- PATCH /followups/{trip_id}/snooze
- PATCH /followups/{trip_id}/reschedule
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from spine_api.core.auth import get_current_agency
from spine_api.models.tenant import Agency

# Import persistence logic
try:
    from spine_api import persistence
except (ImportError, ValueError):
    import persistence

TripStore = persistence.TripStore
AuditStore = persistence.AuditStore

router = APIRouter()


@router.get("/followups/dashboard")
def get_followups_dashboard(
    status: Optional[str] = None,
    filter: Optional[str] = None,
    agency: Agency = Depends(get_current_agency),
):
    """
    Get all trips with follow-up reminders.

    Query params:
    - status: pending|completed|snoozed
    - filter: due_today|overdue|upcoming

    Returns: List of trips with follow-up info sorted by due date
    """
    # Keep route semantics identical to prior server.py behavior:
    # resolve to repo-root/data/trips (not spine_api/data/trips).
    trips_dir = Path(__file__).resolve().parents[2] / "data" / "trips"
    followups = []

    if trips_dir.exists():
        for trip_file in trips_dir.glob("*.json"):
            try:
                with open(trip_file, "r") as f:
                    trip = json.load(f)

                # Only include trips for this agency
                if trip.get("agency_id") != agency.id:
                    continue

                # Only include trips with follow_up_due_date
                due_date_str = trip.get("follow_up_due_date")
                if not due_date_str:
                    continue

                try:
                    due_date = datetime.fromisoformat(due_date_str.replace("Z", "+00:00"))
                except (ValueError, AttributeError):
                    continue

                # Extract follow-up status
                follow_up_status = trip.get("follow_up_status", "pending")
                trip_status = trip.get("status", "new")

                # Filter by status if provided
                if status and follow_up_status != status:
                    continue

                # Apply filter if provided
                now = datetime.now(timezone.utc)
                if filter == "due_today":
                    if due_date.date() != now.date():
                        continue
                elif filter == "overdue":
                    if due_date > now:
                        continue
                elif filter == "upcoming":
                    if due_date <= now:
                        continue

                followups.append(
                    {
                        "trip_id": trip.get("id"),
                        "traveler_name": trip.get("traveler_name", "Unknown"),
                        "agent_name": trip.get("agent_name", "Unassigned"),
                        "due_date": due_date_str,
                        "status": follow_up_status,
                        "trip_status": trip_status,
                        "days_until_due": (due_date.date() - now.date()).days,
                    }
                )
            except (json.JSONDecodeError, IOError):
                continue

    # Sort by due_date ascending
    followups.sort(key=lambda x: x["due_date"])

    return {
        "items": followups,
        "total": len(followups),
    }


@router.patch("/followups/{trip_id}/mark-complete")
def mark_followup_complete(
    trip_id: str,
    agency: Agency = Depends(get_current_agency),
):
    """Mark a follow-up as completed."""
    trip = TripStore.get_trip_for_agency(trip_id, agency.id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    if not trip.get("follow_up_due_date"):
        raise HTTPException(status_code=400, detail="Trip has no follow-up scheduled")

    updated = TripStore.update_trip(
        trip_id,
        {
            "follow_up_status": "completed",
            "follow_up_completed_at": datetime.now(timezone.utc).isoformat(),
        },
    )

    AuditStore.log_event(
        "followup_completed",
        "operator",
        {
            "trip_id": trip_id,
            "due_date": trip.get("follow_up_due_date"),
            "completed_at": datetime.now(timezone.utc).isoformat(),
        },
    )

    return updated


@router.patch("/followups/{trip_id}/snooze")
def snooze_followup(
    trip_id: str,
    days: int = 1,
    agency: Agency = Depends(get_current_agency),
):
    """
    Snooze a follow-up reminder.

    Query params:
    - days: 1, 3, or 7 (default: 1)
    """
    trip = TripStore.get_trip_for_agency(trip_id, agency.id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    if not trip.get("follow_up_due_date"):
        raise HTTPException(status_code=400, detail="Trip has no follow-up scheduled")

    # Validate days parameter
    if days not in [1, 3, 7]:
        raise HTTPException(status_code=400, detail="days must be 1, 3, or 7")

    # Parse current due_date and add days
    try:
        current_due = datetime.fromisoformat(trip.get("follow_up_due_date", "").replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        raise HTTPException(status_code=400, detail="Invalid follow_up_due_date format")

    new_due_date = (current_due + timedelta(days=days)).isoformat()

    updated = TripStore.update_trip(
        trip_id,
        {
            "follow_up_due_date": new_due_date,
            "follow_up_status": "snoozed",
        },
    )

    AuditStore.log_event(
        "followup_snoozed",
        "operator",
        {
            "trip_id": trip_id,
            "original_due_date": trip.get("follow_up_due_date"),
            "new_due_date": new_due_date,
            "snooze_days": days,
        },
    )

    return updated


@router.patch("/followups/{trip_id}/reschedule")
def reschedule_followup(
    trip_id: str,
    new_date: str,
    agency: Agency = Depends(get_current_agency),
):
    """
    Reschedule a follow-up to a new date.

    Body: {"new_date": "2026-05-15T14:00:00Z"}
    """
    trip = TripStore.get_trip_for_agency(trip_id, agency.id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    if not trip.get("follow_up_due_date"):
        raise HTTPException(status_code=400, detail="Trip has no follow-up scheduled")

    # Validate new_date format
    try:
        datetime.fromisoformat(new_date.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        raise HTTPException(status_code=400, detail="Invalid date format. Use ISO-8601")

    updated = TripStore.update_trip(
        trip_id,
        {
            "follow_up_due_date": new_date,
            "follow_up_status": "pending",
        },
    )

    AuditStore.log_event(
        "followup_rescheduled",
        "operator",
        {
            "trip_id": trip_id,
            "old_due_date": trip.get("follow_up_due_date"),
            "new_due_date": new_date,
        },
    )

    return updated


class GenerateFollowUpRequest(BaseModel):
    pass

@router.post("/followups/generate")
def generate_followup_prompt(
    body: dict,
    agency: Agency = Depends(get_current_agency),
):
    """
    Priority #2: Automated Client Re-engagement Copy Generator.

    Generates personalized re-engagement copy for stale leads or pending proposals.
    Calibrated by channel (WhatsApp vs Email) and tone (friendly, urgent, professional).
    """
    trip_id = body.get("trip_id")
    channel = body.get("channel", "whatsapp")
    tone = body.get("tone", "friendly")

    if not trip_id:
        raise HTTPException(status_code=400, detail="trip_id is required")

    trip = TripStore.get_trip_for_agency(trip_id, agency.id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    traveler_name = trip.get("traveler_name", "there")
    destination = trip.get("destination") or trip.get("packet", {}).get("destination", "your destination")

    if channel == "whatsapp":
        if tone == "urgent":
            copy = f"Hi {traveler_name}! ⏰ Quick update on your {destination} itinerary — hotel rates lock in 24 hours. Would you like me to hold your dates today?"
        else:
            copy = f"Hi {traveler_name}! 🌴 Hope you're having a great week. I've prepared your custom {destination} travel proposal with guaranteed rates. Let me know if you'd like to review!"
    else: # email
        copy = (
            f"Dear {traveler_name},\n\n"
            f"Following up on your upcoming trip to {destination}. We have finalized your custom itinerary "
            f"including exclusive resort perks and flexible cancellation options.\n\n"
            f"You can view and confirm your itinerary online at your convenience.\n\n"
            f"Warm regards,\nYour Waypoint OS Concierge Team"
        )

    return {
        "ok": True,
        "trip_id": trip_id,
        "channel": channel,
        "tone": tone,
        "generated_copy": copy,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


class SendAskRequest(BaseModel):
    """Operator action: send the trip's open follow-up questions to the traveler."""
    recipient: str  # phone (E.164) for whatsapp, email address for email
    channel: str = "whatsapp"  # whatsapp | email
    ttl_hours: int = 168


def _compose_questions_message(trip: dict, ask_path: str) -> tuple[str, list]:
    """Build the traveler-facing message from the trip's open questions."""
    decision = trip.get("decision") or {}
    questions = [
        q for q in (decision.get("follow_up_questions") or [])
        if isinstance(q, dict) and (q.get("question") or q.get("text"))
    ]
    destination = trip.get("destination") or (trip.get("packet") or {}).get("destination") or "your trip"
    lines = [f"A few quick questions about {destination} so we can finish your plan:"]
    for idx, q in enumerate(questions, start=1):
        lines.append(f"{idx}. {q.get('question') or q.get('text')}")
    lines.append(f"Answer here: {ask_path}")
    return "\n".join(lines), questions


@router.post("/followups/{trip_id}/send")
def send_followup_questions(
    trip_id: str,
    body: SendAskRequest,
    agency: Agency = Depends(get_current_agency),
):
    """Send the trip's open follow-up questions to the traveler (FND-0301).

    Composes the questions message, dispatches through the canonical
    messaging provider adapter, and records the ask on the trip. The response
    is honest about dispatch: NOT_CONFIGURED means the ask + link were
    recorded but no provider send occurred (the operator can share the link
    manually).
    """
    from spine_api.routers.public_proposals import generate_signed_proposal_token
    from spine_api.services.message_dispatch import dispatch_outbound_message

    trip = TripStore.get_trip_for_agency(trip_id, agency.id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    token = generate_signed_proposal_token(trip_id, agency_id=agency.id, ttl_hours=body.ttl_hours, purpose="ask")
    base = os.getenv("TRAVELER_LINK_BASE_URL", "").strip().rstrip("/")
    ask_path = f"{base}/a/{token}" if base else f"/a/{token}"
    content, questions = _compose_questions_message(trip, ask_path)

    if not questions:
        raise HTTPException(status_code=409, detail="Trip has no open follow-up questions to send")

    result = dispatch_outbound_message(
        recipient=body.recipient,
        channel=body.channel,
        content=content,
    )

    asks = trip.get("traveler_asks") or []
    ask_record = {
        "asked_at": datetime.now(timezone.utc).isoformat(),
        "channel": body.channel,
        "recipient": body.recipient,
        "token": token,
        "question_count": len(questions),
        "fields": [q.get("field_name") for q in questions],
        "dispatch_status": result["dispatch_status"],
    }
    asks.append(ask_record)
    updated = TripStore.update_trip_for_agency(trip_id, agency.id, {"traveler_asks": asks})
    if updated is None:
        raise HTTPException(status_code=404, detail="Trip not found")

    AuditStore.log_event(
        event_type="traveler_ask_sent",
        user_id=agency.id,
        details={
            "trip_id": trip_id,
            "channel": body.channel,
            "recipient_hash": (
                hashlib.sha256((body.recipient or "").strip().encode("utf-8")).hexdigest()[:16]
                if body.recipient
                else ""
            ),
            "dispatch_status": result["dispatch_status"],
            "question_count": len(questions),
        },
    )

    return {
        "ok": True,
        "trip_id": trip_id,
        "token": token,
        "ask_path": ask_path,
        "dispatch_status": result["dispatch_status"],
        "dispatch_detail": result["detail"],
        "question_count": len(questions),
        "asked_count": len(asks),
    }

