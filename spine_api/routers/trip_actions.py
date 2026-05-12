"""
Trip action router extracted from server shell.

Scope:
- POST /trips/{trip_id}/review/action
- GET  /trips/{trip_id}/activities/provenance
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException

from spine_api.contract import ReviewActionRequest
from spine_api.core.auth import get_current_agency, get_current_user, require_permission
from spine_api.models.tenant import Agency, User

from src.analytics.review import process_review_action

try:
    from spine_api import persistence
except (ImportError, ValueError):
    import persistence

TripStore = persistence.TripStore

logger = logging.getLogger("spine_api.trip_actions")
router = APIRouter()


@router.post("/trips/{trip_id}/review/action")
def post_review_action(
    trip_id: str,
    request: ReviewActionRequest,
    agency: Agency = Depends(get_current_agency),
    user: User = Depends(get_current_user),
    _perm=require_permission("trips:write"),
):
    """Apply a review action (approve/reject/request_changes/escalate) to a trip."""
    trip = TripStore.get_trip(trip_id)
    if not trip or trip.get("agency_id") != agency.id:
        raise HTTPException(status_code=404, detail="Trip not found")

    try:
        updated_trip = process_review_action(
            trip_id=trip_id,
            action=request.action,
            notes=request.notes,
            user_id=user.id,
            reassign_to=request.reassign_to,
            error_category=request.error_category,
        )
        return {"success": True, "trip": updated_trip}
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Review action failed: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error during review action")


@router.get("/trips/{trip_id}/activities/provenance")
def get_activities_provenance(
    trip_id: str,
    agency: Agency = Depends(get_current_agency),
):
    """
    Retrieve activity provenance for a trip.
    """
    trip = TripStore.get_trip(trip_id)
    if not trip or trip.get("agency_id") != agency.id:
        raise HTTPException(status_code=404, detail=f"Trip not found: {trip_id}")

    activities = []
    activity_provenance = trip.get("activity_provenance", "")
    if activity_provenance:
        activity_names = [a.strip() for a in activity_provenance.split(",")]
        for activity_name in activity_names:
            if activity_name:
                activities.append(
                    {
                        "name": activity_name,
                        "source": "suggested",
                        "confidence": 85,
                    }
                )

    return {"trip_id": trip_id, "activities": activities}
