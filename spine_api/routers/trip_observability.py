"""
Trip observability router extracted from server shell.

Scope:
- GET /trips/{trip_id}/agent-events
- GET /api/trips/{trip_id}/timeline
"""

from __future__ import annotations

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from spine_api.contract import TimelineEvent, TimelineResponse
from spine_api.core.auth import get_current_agency
from spine_api.models.tenant import Agency

try:
    from spine_api import persistence
except (ImportError, ValueError):
    import persistence

AuditStore = persistence.AuditStore
TripStore = persistence.TripStore

try:
    from src.analytics.logger import TimelineEventMapper
except ImportError:
    TimelineEventMapper = None

logger = logging.getLogger("spine_api.trip_observability")
router = APIRouter()


@router.get("/trips/{trip_id}/agent-events")
def get_trip_agent_events(
    trip_id: str,
    limit: int = Query(default=100, ge=1, le=1000),
    agency: Agency = Depends(get_current_agency),
):
    """
    Return product-agent observability events for a single trip.
    """
    trip = TripStore.get_trip(trip_id)
    if not trip or trip.get("agency_id") != agency.id:
        raise HTTPException(status_code=404, detail="Trip not found")

    events = AuditStore.get_agent_events_for_trip(trip_id=trip_id, limit=limit)
    return {"trip_id": trip_id, "events": events, "total": len(events)}


@router.get("/api/trips/{trip_id}/timeline", response_model=TimelineResponse)
def get_trip_timeline(
    trip_id: str,
    stage: Optional[str] = None,
) -> TimelineResponse:
    """
    Retrieve the unified timeline for a trip from AuditStore.
    """
    if stage:
        valid_stages = {"intake", "packet", "decision", "strategy", "safety"}
        if stage.lower() not in valid_stages:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid stage parameter. Must be one of: {', '.join(valid_stages)}",
            )

    try:
        audit_events = AuditStore.get_events_for_trip(trip_id)
        if TimelineEventMapper:
            mapped_events = TimelineEventMapper.map_events_for_trip(audit_events, stage_filter=stage)
            events: List[TimelineEvent] = []
            for mapped_event in mapped_events:
                confidence = mapped_event.confidence
                if confidence is not None:
                    if isinstance(confidence, (int, float)):
                        confidence = max(0, min(100, float(confidence)))
                    else:
                        logger.error("Invalid confidence type %s for trip %s, using None", type(confidence), trip_id)
                        confidence = None

                event_dict = {
                    "trip_id": mapped_event.trip_id,
                    "timestamp": mapped_event.timestamp,
                    "stage": mapped_event.stage,
                    "status": mapped_event.status,
                    "state_snapshot": mapped_event.state_snapshot,
                }
                if mapped_event.decision is not None:
                    event_dict["decision"] = mapped_event.decision
                if confidence is not None:
                    event_dict["confidence"] = confidence
                if mapped_event.reason is not None:
                    event_dict["reason"] = mapped_event.reason
                if mapped_event.actor is not None:
                    event_dict["actor"] = mapped_event.actor
                if mapped_event.pre_state is not None:
                    event_dict["pre_state"] = mapped_event.pre_state
                if mapped_event.post_state is not None:
                    event_dict["post_state"] = mapped_event.post_state
                events.append(TimelineEvent(**event_dict))
        else:
            events = []
            for audit_event in audit_events:
                details = audit_event.get("details", {})
                if details.get("trip_id") != trip_id:
                    continue

                resolved_state = details.get("state")
                if not resolved_state and isinstance(details.get("post_state"), dict):
                    resolved_state = details.get("post_state", {}).get("state")

                event_dict = {
                    "trip_id": trip_id,
                    "timestamp": audit_event.get("timestamp", ""),
                    "stage": details.get("stage", "unknown"),
                    "status": resolved_state or "unknown",
                    "state_snapshot": {"stage": details.get("stage", "unknown")},
                }
                actor = audit_event.get("user_id")
                if actor is not None:
                    event_dict["actor"] = actor
                if details.get("decision_type"):
                    event_dict["decision"] = details.get("decision_type")
                if details.get("reason"):
                    event_dict["reason"] = details.get("reason")
                if details.get("confidence") is not None:
                    try:
                        confidence = float(details.get("confidence"))
                        event_dict["confidence"] = max(0, min(100, confidence))
                    except (ValueError, TypeError):
                        logger.error("Invalid confidence value in fallback: %s", details.get("confidence"))
                if stage and event_dict.get("stage") != stage:
                    continue
                events.append(TimelineEvent(**event_dict))

        return TimelineResponse(trip_id=trip_id, events=events)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to retrieve timeline for trip %s: %s", trip_id, e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve trip timeline")
