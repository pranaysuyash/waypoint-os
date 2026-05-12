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
from spine_api.core.auth import get_current_agency
from spine_api.models.tenant import Agency
from spine_api.services.inbox_projection import build_inbox_response

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
    agency: Agency = Depends(get_current_agency),
):
    """
    Canonical inbox endpoint — service-level projected, filtered, sorted, paginated.

    Returns a stable {items, total, hasMore, filterCounts} envelope.
    filterCounts are computed over the FULL projected dataset so tab counts
    are accurate regardless of active filter or page size.
    """
    agency_id = agency.id

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
    agency: Agency = Depends(get_current_agency),
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
    agency: Agency = Depends(get_current_agency),
):
    """Return aggregate inbox statistics for Overview cards."""
    def analytics_payload(trip: dict) -> dict:
        payload = trip.get("analytics")
        return payload if isinstance(payload, dict) else {}

    agency_id = agency.id
    total = TripStore.count_trips(status=_INBOX_STATUSES, agency_id=agency_id)

    trips = TripStore.list_trip_summaries(status=_INBOX_STATUSES, limit=500, agency_id=agency_id)

    unassigned = sum(1 for t in trips if not t.get("assigned_to"))
    critical = sum(
        1 for t in trips
        if analytics_payload(t).get("escalation_severity") in ("high", "critical")
    )
    at_risk = sum(
        1 for t in trips
        if analytics_payload(t).get("sla_status") == "at_risk"
    )

    return {"total": total, "unassigned": unassigned, "critical": critical, "atRisk": at_risk}


@router.post("/inbox/bulk")
def bulk_inbox_action(
    request: dict,
    agency: Agency = Depends(get_current_agency),
):
    """Apply bulk actions to inbox items."""
    action = request.get("action")
    trip_ids = request.get("trip_ids", [])

    agency_trips = TripStore.list_trips(agency_id=agency.id, limit=10000)
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
