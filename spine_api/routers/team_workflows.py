"""
spine_api/routers/team_workflows.py — Agency Team Workflows & Multi-Agent Collaboration Engine.

Endpoints:
  POST /api/v1/team/assign         — Assign trip to agent/reviewer with role
  POST /api/v1/team/review-signoff — Submit manager/senior advisor signoff decision on proposal

Auth model:
  Requires JWT auth via Depends(get_current_agency_id).
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from spine_api.contract import (
    ReviewSignoffRequest,
    ReviewSignoffResponse,
    TeamAssignmentRequest,
    TeamAssignmentResponse,
)
from spine_api.core.auth import get_current_agency_id
from spine_api.persistence import AuditStore, TripStore

logger = logging.getLogger("spine_api.team_workflows")

router = APIRouter(prefix="/api/v1/team", tags=["team_workflows"])


@router.post("/assign", response_model=TeamAssignmentResponse)
async def assign_trip_to_team_member(
    body: TeamAssignmentRequest,
    agency_id: str = Depends(get_current_agency_id),
):
    """
    Assign a trip packet to an agency team member or specialized sub-agent role.
    """
    trip = TripStore.get_trip_for_agency(body.trip_id, agency_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    now_str = datetime.now(timezone.utc).isoformat()
    trip["assigned_agent_id"] = body.assignee_id
    trip["assigned_role"] = body.assignee_role
    trip["updated_at"] = now_str

    TripStore.save_trip(trip)

    AuditStore.log_event(
        event_type="trip_team_assigned",
        user_id=agency_id,
        details={
            "trip_id": body.trip_id,
            "assigned_to": body.assignee_id,
            "role": body.assignee_role,
            "notes": body.notes,
        },
    )

    return TeamAssignmentResponse(
        ok=True,
        trip_id=body.trip_id,
        assigned_to=body.assignee_id,
        role=body.assignee_role,
        assigned_at=now_str,
    )


@router.post("/review-signoff", response_model=ReviewSignoffResponse)
async def submit_review_signoff(
    body: ReviewSignoffRequest,
    agency_id: str = Depends(get_current_agency_id),
):
    """
    Submit a formal review signoff or change request decision on a travel proposal.
    """
    trip = TripStore.get_trip_for_agency(body.trip_id, agency_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    now_str = datetime.now(timezone.utc).isoformat()
    trip["review_decision"] = body.decision
    trip["reviewer_id"] = body.reviewer_id
    trip["updated_at"] = now_str

    TripStore.save_trip(trip)

    AuditStore.log_event(
        event_type="proposal_review_signoff",
        user_id=agency_id,
        details={
            "trip_id": body.trip_id,
            "reviewer_id": body.reviewer_id,
            "decision": body.decision,
            "notes": body.feedback_notes,
        },
    )

    return ReviewSignoffResponse(
        ok=True,
        trip_id=body.trip_id,
        reviewer_id=body.reviewer_id,
        decision=body.decision,
        signoff_at=now_str,
    )


@router.get("/high-value-gate-check/{trip_id}")
async def check_high_value_signoff_gate(
    trip_id: str,
    agency_id: str = Depends(get_current_agency_id),
):
    """
    Priority #8: Senior Planner High-Value Signoff Gate (> $10,000).

    Enforces agency review policy: quotes exceeding $10,000 require formal
    senior planner approval before proposal export/dispatch to traveler.
    """
    trip = TripStore.get_trip_for_agency(trip_id, agency_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    packet = trip.get("packet", {}) or {}
    quote_amount = float(packet.get("budget_max") or 0.0)
    requires_approval = quote_amount >= 10000.0

    review_decision = trip.get("review_decision")
    approved = review_decision == "APPROVED" or not requires_approval

    return {
        "ok": True,
        "trip_id": trip_id,
        "quote_amount": quote_amount,
        "high_value_threshold": 10000.0,
        "requires_senior_signoff": requires_approval,
        "review_decision": review_decision or "PENDING",
        "gate_passed": approved,
        "status_message": (
            "Gate Passed: Approved for dispatch" if approved
            else "Gate Blocked: Quotes >= $10,000 require senior planner approval before sending."
        ),
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }

