"""
Legacy operations router extracted from server shell.

Scope:
- POST /trips/{trip_id}/assign
- POST /trips/{trip_id}/unassign
- POST /trips/{trip_id}/snooze
- POST /trips/{trip_id}/suitability/acknowledge
- GET  /assignments
- GET  /audit
- POST /trips/{trip_id}/override
- GET  /trips/{trip_id}/overrides
- GET  /overrides/{override_id}
- POST /trips/{trip_id}/reassign
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from spine_api.contract import (
    OverrideRequest,
    OverrideResponse,
    SnoozeRequest,
    SuitabilityAcknowledgeRequest,
)
from spine_api.core.auth import get_current_agency, require_permission
from spine_api.models.tenant import Agency

# Import persistence logic
try:
    from spine_api import persistence
except (ImportError, ValueError):
    import persistence

AuditStore = persistence.AuditStore
AssignmentStore = persistence.AssignmentStore
OverrideStore = persistence.OverrideStore
TripStore = persistence.TripStore

router = APIRouter()


@router.post("/trips/{trip_id}/assign")
def assign_trip(
    trip_id: str,
    agent_id: str,
    agent_name: str,
    assigned_by: str = "system",
    agency: Agency = Depends(get_current_agency),
):
    """Assign a trip to an agent."""
    trip = TripStore.get_trip(trip_id)
    if not trip or trip.get("agency_id") != agency.id:
        raise HTTPException(status_code=404, detail="Trip not found")

    AssignmentStore.assign_trip(trip_id, agent_id, agent_name, assigned_by)
    TripStore.update_trip(trip_id, {"status": "assigned"})
    return {"success": True, "trip_id": trip_id, "assigned_to": agent_id}


@router.post("/trips/{trip_id}/unassign")
def unassign_trip(
    trip_id: str,
    unassigned_by: str = "system",
    agency: Agency = Depends(get_current_agency),
):
    """Remove assignment from a trip."""
    trip = TripStore.get_trip(trip_id)
    if not trip or trip.get("agency_id") != agency.id:
        raise HTTPException(status_code=404, detail="Trip not found")

    AssignmentStore.unassign_trip(trip_id, unassigned_by)
    return {"success": True, "trip_id": trip_id}


@router.post("/trips/{trip_id}/snooze")
def snooze_trip(
    trip_id: str,
    request: SnoozeRequest,
    agency: Agency = Depends(get_current_agency),
):
    """Snooze a trip until a specified time."""
    trip = TripStore.get_trip(trip_id)
    if not trip or trip.get("agency_id") != agency.id:
        raise HTTPException(status_code=404, detail="Trip not found")

    analytics = trip.get("analytics") or {}
    analytics["snooze_until"] = request.snooze_until
    TripStore.update_trip(trip_id, {"analytics": analytics})

    AuditStore.log_event("trip_snoozed", "owner", {
        "trip_id": trip_id,
        "snooze_until": request.snooze_until,
    })
    return {"success": True, "trip_id": trip_id, "snooze_until": request.snooze_until}


@router.post("/trips/{trip_id}/suitability/acknowledge")
def acknowledge_suitability_flags(
    trip_id: str,
    request: SuitabilityAcknowledgeRequest,
    agency: Agency = Depends(get_current_agency),
):
    """Acknowledge suitability flags for a trip, allowing it to proceed."""
    trip = TripStore.get_trip(trip_id)
    if not trip or trip.get("agency_id") != agency.id:
        raise HTTPException(status_code=404, detail="Trip not found")

    analytics = trip.get("analytics") or {}
    existing = analytics.get("acknowledged_flags", [])
    updated = list(set(existing + request.acknowledged_flags))
    analytics["acknowledged_flags"] = updated
    analytics["suitability_acknowledged_at"] = datetime.now(timezone.utc).isoformat()
    TripStore.update_trip(trip_id, {"analytics": analytics})

    AuditStore.log_event("suitability_acknowledged", "owner", {
        "trip_id": trip_id,
        "acknowledged_flags": request.acknowledged_flags,
    })
    return {"success": True, "trip_id": trip_id, "acknowledged_flags": updated}


@router.get("/assignments")
def list_assignments(
    agent_id: Optional[str] = None,
    agency: Agency = Depends(get_current_agency),
):
    """List assignments for trips in the current agency."""
    agency_trips = TripStore.list_trips(agency_id=agency.id, limit=10000)
    agency_trip_ids = {t["id"] for t in agency_trips if t.get("id")}

    if agent_id:
        assignments = AssignmentStore.get_trips_for_agent(agent_id)
    else:
        assignments = list(AssignmentStore._load_assignments().values())

    filtered = [a for a in assignments if a.get("trip_id") in agency_trip_ids]
    return {"items": filtered, "total": len(filtered)}


@router.get("/audit")
def get_audit_events(
    limit: int = 100,
    agency: Agency = Depends(get_current_agency),
):
    """Get recent audit events for the current agency."""
    events = AuditStore.get_events(limit=limit)
    agency_trips = TripStore.list_trips(agency_id=agency.id, limit=10000)
    agency_trip_ids = {t["id"] for t in agency_trips if t.get("id")}

    filtered = [
        e for e in events
        if e.get("details", {}).get("trip_id") in agency_trip_ids
        or e.get("details", {}).get("agency_id") == agency.id
    ]
    return {"items": filtered, "total": len(filtered)}


@router.post("/trips/{trip_id}/override", response_model=OverrideResponse)
def create_override(
    trip_id: str,
    request: OverrideRequest,
    agency: Agency = Depends(get_current_agency),
) -> OverrideResponse:
    """Record an operator override of a risk flag for a trip."""
    trip = TripStore.get_trip(trip_id)
    if not trip or trip.get("agency_id") != agency.id:
        raise HTTPException(status_code=404, detail=f"Trip not found: {trip_id}")

    if not request.reason or len(request.reason.strip()) < 1:
        raise HTTPException(status_code=400, detail="reason field is mandatory and must be non-empty")

    if request.action == "downgrade" and not request.new_severity:
        raise HTTPException(status_code=400, detail="new_severity required for downgrade action")

    current_flags = trip.get("decision", {}).get("suitability_flags", [])
    flag_info = None
    for flag in current_flags:
        if flag.get("flag") == request.flag:
            flag_info = flag
            break

    if request.original_severity and flag_info:
        actual_severity = flag_info.get("severity")
        if actual_severity != request.original_severity:
            raise HTTPException(
                status_code=409,
                detail=f"Stale override: flag '{request.flag}' severity is '{actual_severity}', not '{request.original_severity}'",
            )

    override_data = {
        "flag": request.flag,
        "decision_type": request.decision_type or request.flag,
        "action": request.action,
        "new_severity": request.new_severity,
        "overridden_by": request.overridden_by,
        "reason": request.reason,
        "scope": request.scope,
        "original_severity": request.original_severity or (flag_info.get("severity") if flag_info else None),
        "rescinded": False,
    }
    override_id = OverrideStore.save_override(trip_id, override_data)

    audit_event_id = f"evt_{uuid.uuid4().hex[:12]}"
    AuditStore.log_event("override_created", request.overridden_by, {
        "trip_id": trip_id,
        "override_id": override_id,
        "flag": request.flag,
        "action": request.action,
        "reason": request.reason,
    })

    return OverrideResponse(
        ok=True,
        override_id=override_id,
        trip_id=trip_id,
        flag=request.flag,
        action=request.action,
        new_severity=request.new_severity,
        cache_invalidated=False,
        rule_graduated=False,
        pattern_learning_queued=request.scope == "pattern",
        warnings=[],
        audit_event_id=audit_event_id,
    )


@router.get("/trips/{trip_id}/overrides")
def list_overrides(trip_id: str, agency: Agency = Depends(get_current_agency)) -> dict:
    """List all overrides for a trip."""
    trip = TripStore.get_trip(trip_id)
    if not trip or trip.get("agency_id") != agency.id:
        raise HTTPException(status_code=404, detail=f"Trip not found: {trip_id}")

    overrides = OverrideStore.get_overrides_for_trip(trip_id)
    return {"ok": True, "trip_id": trip_id, "overrides": overrides, "total": len(overrides)}


@router.get("/overrides/{override_id}")
def get_override(override_id: str) -> dict:
    """Get a specific override by ID."""
    override = OverrideStore.get_override(override_id)
    if not override:
        raise HTTPException(status_code=404, detail=f"Override not found: {override_id}")
    return {"ok": True, "override": override}


@router.post("/trips/{trip_id}/reassign")
def reassign_trip(
    trip_id: str,
    agent_id: str,
    agent_name: str,
    reassigned_by: str = "owner",
    agency: Agency = Depends(get_current_agency),
    _perm=require_permission("trips:reassign"),
):
    """Reassign a trip to a different agent."""
    trip = TripStore.get_trip(trip_id)
    if not trip or trip.get("agency_id") != agency.id:
        raise HTTPException(status_code=404, detail="Trip not found")

    existing = AssignmentStore.get_assignment(trip_id)
    if existing:
        AssignmentStore.unassign_trip(trip_id, reassigned_by)

    AssignmentStore.assign_trip(trip_id, agent_id, agent_name, reassigned_by)
    TripStore.update_trip(trip_id, {"status": "assigned"})
    return {"success": True, "trip_id": trip_id, "reassigned_to": agent_id}
