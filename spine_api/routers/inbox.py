"""
Inbox router.

Owns the canonical lead inbox read model plus inbox assignment and bulk
operations. Extracted from ``spine_api.server`` without changing public paths
or response envelopes.
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from spine_api.contract import (
    AssignInboxRequest,
    AssignInboxResponse,
    InboxResponse,
    InboxStatsResponse,
)
from spine_api.core.auth import get_current_agency_id
from spine_api.services.inbox_projection import InboxProjectionService, build_inbox_response

try:
    from spine_api import persistence
except (ImportError, ValueError):
    import persistence

logger = logging.getLogger("spine_api.inbox")

AssignmentStore = persistence.AssignmentStore
TripStore = persistence.TripStore

router = APIRouter()

# Canonical inbox statuses — shared source of truth for frontend + backend.
_INBOX_STATUSES = "new,incomplete,needs_followup,awaiting_customer_details,snoozed"


@router.get("/inbox", response_model=InboxResponse)
def get_inbox(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=500),
    filter_key: Optional[str] = Query(None, alias="filter"),
    sort: Optional[str] = Query("priority"),
    dir: Optional[str] = Query("desc"),
    q: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    slaStatus: Optional[str] = Query(None),
    stage: Optional[str] = Query(None),
    assignedTo: Optional[str] = Query(None),
    minValue: Optional[int] = Query(None),
    maxValue: Optional[int] = Query(None),
    minUrgency: Optional[int] = Query(None),
    minImportance: Optional[int] = Query(None),
    agency_id: str = Depends(get_current_agency_id),
):
    """
    Canonical inbox endpoint — service-level projected, filtered, sorted, paginated.

    Returns a stable {items, total, hasMore, filterCounts} envelope.
    filterCounts are computed over the FULL projected dataset so tab counts
    are accurate regardless of active filter or page size.
    """
    raw_trips = TripStore.list_trip_summaries(
        status=_INBOX_STATUSES,
        limit=5000,
        agency_id=agency_id,
    )

    return build_inbox_response(
        raw_trips,
        page=page,
        limit=limit,
        filter_key=filter_key,
        sort_key=sort,
        sort_dir=dir,
        search_query=q,
        priorities=priority.split(",") if priority else None,
        sla_statuses=slaStatus.split(",") if slaStatus else None,
        stages=stage.split(",") if stage else None,
        assigned_to=assignedTo.split(",") if assignedTo else None,
        min_value=minValue,
        max_value=maxValue,
    )


@router.post("/inbox/assign", response_model=AssignInboxResponse)
def assign_inbox_trips(
    body: AssignInboxRequest,
    agency_id: str = Depends(get_current_agency_id),
):
    """
    Assign inbox trips to an agent.

    Sets assigned_to_id and moves each trip from inbox to workspace (status=assigned).
    """
    trip_ids = body.tripIds
    assign_to_id = body.assignTo
    assigned = 0

    for trip_id in trip_ids:
        result = TripStore.update_trip(trip_id, {
            "assigned_to_id": assign_to_id,
            "status": "assigned",
        })
        if result:
            assigned += 1

    return {"success": assigned == len(trip_ids), "assigned": assigned}


@router.get("/inbox/stats", response_model=InboxStatsResponse)
def get_inbox_stats(
    agency_id: str = Depends(get_current_agency_id),
):
    """Return aggregate inbox statistics for Overview cards."""
    def analytics_payload(trip: dict) -> dict:
        payload = trip.get("analytics")
        return payload if isinstance(payload, dict) else {}

    def has_known_value(value: object) -> bool:
        if not isinstance(value, str):
            return value is not None
        cleaned = value.strip().lower()
        return bool(cleaned) and cleaned not in {"tbd", "to confirm", "unknown", "not set", "n/a", "-"}

    def has_customer_identity(value: object) -> bool:
        if not isinstance(value, str):
            return False
        cleaned = value.strip().lower()
        if not cleaned:
            return False
        return not (
            cleaned.startswith("test_fixture")
            or cleaned.startswith("fixture")
            or cleaned.startswith("sample")
            or cleaned.startswith("demo")
            or cleaned.startswith("client ")
        )

    total = TripStore.count_trips(status=_INBOX_STATUSES, agency_id=agency_id)

    raw_trips = TripStore.list_trip_summaries(status=_INBOX_STATUSES, limit=max(1, min(total, 10000)), agency_id=agency_id)
    projected_trips = InboxProjectionService().project_all(raw_trips)

    unassigned = sum(1 for t in projected_trips if not t.get("assignedTo"))
    critical = sum(
        1 for t in raw_trips
        if analytics_payload(t).get("escalation_severity") in ("high", "critical")
    )
    at_risk = sum(
        1 for t in projected_trips
        if t.get("slaStatus") == "at_risk"
    )
    breached = sum(
        1 for t in projected_trips
        if t.get("slaStatus") == "breached"
    )
    incomplete = sum(
        1 for t in projected_trips
        if "incomplete" in t.get("flags", [])
    )
    missing_customer = sum(
        1 for t in projected_trips
        if not has_customer_identity(t.get("customerName"))
    )
    missing_trip_basics = sum(
        1 for t in projected_trips
        if not has_known_value(t.get("destination")) or not has_known_value(t.get("dateWindow"))
    )
    waiting_days = [
        t.get("daysInCurrentStage")
        for t in projected_trips
        if isinstance(t.get("daysInCurrentStage"), int)
    ]
    unassigned_waiting_days = [
        t.get("daysInCurrentStage")
        for t in projected_trips
        if not t.get("assignedTo") and isinstance(t.get("daysInCurrentStage"), int)
    ]
    legacy_at_risk = sum(
        1 for t in raw_trips
        if analytics_payload(t).get("sla_status") == "at_risk"
    )

    return {
        "total": total,
        "unassigned": unassigned,
        "critical": critical,
        "atRisk": max(at_risk, legacy_at_risk),
        "breached": breached,
        "incomplete": incomplete,
        "missingCustomer": missing_customer,
        "missingTripBasics": missing_trip_basics,
        "oldestWaitingDays": max(waiting_days) if waiting_days else None,
        "oldestUnassignedWaitingDays": max(unassigned_waiting_days) if unassigned_waiting_days else None,
        "statsCoverage": len(projected_trips),
    }


@router.post("/inbox/bulk")
def bulk_inbox_action(
    request: dict,
    agency_id: str = Depends(get_current_agency_id),
):
    """Apply bulk actions to inbox items."""
    action = request.get("action")
    trip_ids = request.get("trip_ids", [])

    agency_trips = TripStore.list_trips(agency_id=agency_id, limit=10000)
    agency_trip_ids = {t["id"] for t in agency_trips if t.get("id")}
    trip_ids = [tid for tid in trip_ids if tid in agency_trip_ids]

    if not action or not trip_ids:
        raise HTTPException(status_code=400, detail="action and trip_ids are required")

    processed = 0
    failed = 0

    for trip_id in trip_ids:
        try:
            if action == "assign":
                agent_id = request.get("agent_id", "system")
                AssignmentStore.assign_trip(trip_id, agent_id, agent_id, "bulk")
                TripStore.update_trip(trip_id, {"status": "assigned"})
            elif action == "unassign":
                AssignmentStore.unassign_trip(trip_id, "bulk")
            elif action == "archive":
                TripStore.update_trip(trip_id, {"status": "archived"})
            processed += 1
        except Exception as exc:
            logger.error("Bulk action failed for %s: %s", trip_id, exc)
            failed += 1

    return {"success": failed == 0, "processed": processed, "failed": failed}
