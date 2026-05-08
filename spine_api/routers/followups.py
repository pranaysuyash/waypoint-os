"""
Followups router for Phase 3 Slice D extraction.

Scope: move only
- GET /followups/dashboard
- PATCH /followups/{trip_id}/mark-complete
- PATCH /followups/{trip_id}/snooze
- PATCH /followups/{trip_id}/reschedule
"""

from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

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
    trip = TripStore.get_trip(trip_id)
    if not trip or trip.get("agency_id") != agency.id:
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
    trip = TripStore.get_trip(trip_id)
    if not trip or trip.get("agency_id") != agency.id:
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
    trip = TripStore.get_trip(trip_id)
    if not trip or trip.get("agency_id") != agency.id:
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
