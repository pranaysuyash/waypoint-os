"""
Analytics router.

Owns the Wave 1 governance analytics, review analytics, escalation, funnel,
and export endpoints. Product-B analytics remains in product_b_analytics.py.
"""

from __future__ import annotations

import logging
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from spine_api.contract import ExportRequest, ExportResponse
from spine_api.core.auth import get_current_agency
from spine_api.core.database import get_db
from spine_api.models.tenant import Agency
from spine_api.services import membership_service
from src.analytics.metrics import (
    BottleneckAnalysis,
    OperationalAlert,
    RevenueMetrics,
    TeamMemberMetrics,
    aggregate_insights,
    compute_alerts,
    compute_bottlenecks,
    compute_pipeline_metrics,
    compute_revenue_metrics,
    compute_team_metrics,
)
from src.analytics.models import InsightsSummary, StageMetrics
from src.analytics.review import process_review_action, trip_to_review

try:
    from spine_api import persistence
except (ImportError, ValueError):
    import persistence

logger = logging.getLogger("spine_api.analytics")

TripStore = persistence.TripStore

router = APIRouter()


@router.get("/analytics/summary", response_model=InsightsSummary)
def get_analytics_summary(
    range: str = "30d",
    agency: Agency = Depends(get_current_agency),
):
    trips = TripStore.list_trips(limit=10000, agency_id=agency.id)
    canonical_trips = [t for t in trips if t.get("id")]
    return aggregate_insights(canonical_trips)


@router.get("/analytics/pipeline", response_model=List[StageMetrics])
def get_analytics_pipeline(
    range: str = "30d",
    agency: Agency = Depends(get_current_agency),
):
    trips = TripStore.list_trips(limit=10000, agency_id=agency.id)
    canonical_trips = [t for t in trips if t.get("id")]
    return compute_pipeline_metrics(canonical_trips)


@router.get("/analytics/team", response_model=List[TeamMemberMetrics])
async def get_analytics_team(
    range: str = "30d",
    agency: Agency = Depends(get_current_agency),
    db: AsyncSession = Depends(get_db),
):
    trips = TripStore.list_trips(limit=1000, agency_id=agency.id)
    members = await membership_service.list_members(db, agency_id=agency.id)
    return compute_team_metrics(trips, members)


@router.get("/analytics/bottlenecks", response_model=List[BottleneckAnalysis])
def get_analytics_bottlenecks(
    range: str = "30d",
    agency: Agency = Depends(get_current_agency),
):
    trips = TripStore.list_trips(limit=1000, agency_id=agency.id)
    return compute_bottlenecks(trips)


@router.get("/analytics/revenue", response_model=RevenueMetrics)
def get_analytics_revenue(
    range: str = "30d",
    agency: Agency = Depends(get_current_agency),
):
    trips = TripStore.list_trips(limit=1000, agency_id=agency.id)
    return compute_revenue_metrics(trips)


@router.get("/analytics/agent/{agent_id}/drill-down")
def get_agent_drill_down(
    agent_id: str,
    metric: str = "conversion",
    agency: Agency = Depends(get_current_agency),
):
    """Return trips and metrics for a specific agent."""
    trips = TripStore.list_trips(limit=1000, agency_id=agency.id)
    agent_trips = [
        t for t in trips
        if t.get("assigned_to") == agent_id or t.get("agent_id") == agent_id
    ]

    return {
        "agent_id": agent_id,
        "metric": metric,
        "trips": agent_trips,
        "count": len(agent_trips),
    }


@router.get("/analytics/alerts", response_model=List[OperationalAlert])
def get_analytics_alerts(agency: Agency = Depends(get_current_agency)):
    """List pending operational alerts (Wave 10)."""
    trips = TripStore.list_trips(limit=1000, agency_id=agency.id)
    return compute_alerts(trips)


@router.post("/analytics/alerts/{alert_id}/dismiss")
def post_dismiss_alert(alert_id: str, agency: Agency = Depends(get_current_agency)):
    """Dismiss an operational alert by flagging the source trip."""
    # Alert ID format is alert_{trip_id}
    trip_id = alert_id.replace("alert_", "")
    trip = TripStore.get_trip(trip_id)
    if not trip or trip.get("agency_id") != agency.id:
        raise HTTPException(status_code=404, detail=f"Target trip for alert {alert_id} not found")

    analytics = trip.get("analytics") or {}
    analytics["feedback_dismissed"] = True

    TripStore.update_trip(trip_id, {"analytics": analytics})
    return {"success": True}


@router.get("/analytics/reviews")
def get_pending_reviews(agency: Agency = Depends(get_current_agency)):
    """List all trips currently flagged for owner review."""
    trips = TripStore.list_trips(limit=1000, agency_id=agency.id)
    # Filter for trips requiring review (per engine.py / review.py logic)
    pending = []
    for t in trips:
        analytics = t.get("analytics")
        if not isinstance(analytics, dict):
            continue
        if analytics.get("requires_review") is True:
            pending.append(trip_to_review(t))
    return {"items": pending, "total": len(pending)}


@router.get("/analytics/reviews/{review_id}")
def get_review(review_id: str, agency: Agency = Depends(get_current_agency)):
    """Get a single review by trip ID."""
    trip = TripStore.get_trip(review_id)
    if not trip or trip.get("agency_id") != agency.id:
        raise HTTPException(status_code=404, detail="Review not found")

    return trip_to_review(trip)


@router.post("/analytics/reviews/bulk-action")
def bulk_review_action(actions: List[dict]):
    """Apply review actions in bulk."""
    processed = 0
    failed = 0
    results = []

    for action in actions:
        try:
            trip_id = action.get("trip_id") or action.get("review_id")
            if not trip_id:
                failed += 1
                continue

            process_review_action(
                trip_id=trip_id,
                action=action.get("action", "approve"),
                notes=action.get("notes", ""),
                user_id="owner",
                reassign_to=action.get("reassign_to"),
                error_category=action.get("error_category"),
            )
            processed += 1
            results.append({"trip_id": trip_id, "status": "processed"})
        except Exception as e:
            logger.error(f"Bulk review action failed for {action}: {e}")
            failed += 1
            results.append({"trip_id": action.get("trip_id"), "status": "failed", "error": str(e)})

    return {"success": failed == 0, "processed": processed, "failed": failed, "results": results}


@router.get("/analytics/escalations")
def get_escalation_heatmap(agency: Agency = Depends(get_current_agency)):
    """Return escalation heatmap data."""
    def analytics_payload(trip: dict) -> dict:
        payload = trip.get("analytics")
        return payload if isinstance(payload, dict) else {}

    trips = TripStore.list_trips(limit=1000, agency_id=agency.id)

    heatmap = defaultdict(lambda: {"total": 0, "escalated": 0})
    for trip in trips:
        agent = trip.get("assigned_to") or trip.get("agent_id") or "unassigned"
        heatmap[agent]["total"] += 1
        if analytics_payload(trip).get("escalation_severity") in ("high", "critical"):
            heatmap[agent]["escalated"] += 1

    return {
        "items": [
            {"agent_id": k, "total": v["total"], "escalated": v["escalated"]}
            for k, v in heatmap.items()
        ],
        "total": len(heatmap),
    }


@router.get("/analytics/funnel")
def get_conversion_funnel(agency: Agency = Depends(get_current_agency)):
    """Return conversion funnel metrics."""
    trips = TripStore.list_trips(limit=1000, agency_id=agency.id)

    stages = ["new", "assigned", "in_progress", "review", "completed", "cancelled"]
    funnel = {stage: 0 for stage in stages}

    for trip in trips:
        status = trip.get("status", "new")
        if status in funnel:
            funnel[status] += 1

    return {
        "items": [
            {"stage": stage, "count": count}
            for stage, count in funnel.items()
        ],
        "total": len(trips),
    }


@router.post("/analytics/export")
def export_insights(request: ExportRequest):
    """Export insights data. Returns a mock export URL for now."""
    export_id = f"export_{uuid.uuid4().hex[:12]}"
    expires = datetime.now(timezone.utc).isoformat()

    # In production this would generate a real file and return a signed URL.
    return ExportResponse(
        download_url=f"/api/exports/{export_id}.{request.format}",
        expires_at=expires,
    )
