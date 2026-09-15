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
from spine_api.core.auth import get_current_agency_id, get_current_user
from spine_api.core.startup_assertions import auth_bypass_enabled
from spine_api.models.tenant import User
from spine_api.persistence import AuditStore, TripStore

logger = logging.getLogger("spine_api.team_workflows")

router = APIRouter(prefix="/api/v1/team", tags=["team_workflows"])


@router.post("/assign", response_model=TeamAssignmentResponse)
async def assign_trip_to_team_member(
    body: TeamAssignmentRequest,
    agency_id: str = Depends(get_current_agency_id),
    current_user: User = Depends(get_current_user),
):
    """
    Assign a trip packet to an agency team member or specialized sub-agent role.

    FND-0220: the audit actor is the authenticated principal (JWT user), the
    tenant scope is the authenticated membership, and the save is agency-bound
    so cross-agency overwrite protection stays active.
    """
    trip = TripStore.get_trip_for_agency(body.trip_id, agency_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    now_str = datetime.now(timezone.utc).isoformat()
    trip["assigned_agent_id"] = body.assignee_id
    trip["assigned_role"] = body.assignee_role
    trip["updated_at"] = now_str

    TripStore.save_trip(trip, agency_id=agency_id)

    AuditStore.log_event(
        event_type="trip_team_assigned",
        user_id=agency_id,
        details={
            "trip_id": body.trip_id,
            "assigned_to": body.assignee_id,
            "role": body.assignee_role,
            "notes": body.notes,
            # Authenticated principal + agency (FND-0220): who authorized the
            # assignment is derived from the JWT, never from the request body.
            "actor_id": current_user.id,
            "agency_id": agency_id,
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
    current_user: User = Depends(get_current_user),
):
    """
    Submit a formal review signoff or change request decision on a travel proposal.

    F-03 (FND-0040): Reviewer identity is derived from the authenticated JWT principal
    (current_user.id or current_user.email), preventing self-asserted signoffs.
    Client-supplied body.reviewer_id is ignored unless running in explicit auth-bypass test mode.

    FND-0220: the bypass fallback is now gated on ``auth_bypass_enabled()`` (fail-closed
    in production) instead of a magic ``"test_user"`` id, and the audit event records
    both the authenticated principal and the agency.
    """
    trip = TripStore.get_trip_for_agency(body.trip_id, agency_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    principal_id = current_user.id if current_user else None
    synthetic_principal = auth_bypass_enabled() and (
        not principal_id or principal_id == "test_user"
    )

    if principal_id and not synthetic_principal:
        # Authoritative reviewer identity: the authenticated JWT principal.
        reviewer_identity = principal_id
    elif auth_bypass_enabled() and body.reviewer_id:
        # Dev/test auth-bypass only: no resolvable principal exists, so the
        # client-declared reviewer is tolerated as a display identity. This
        # branch is unreachable in production (bypass fails closed at boot).
        reviewer_identity = body.reviewer_id
    else:
        reviewer_identity = principal_id or "verified_reviewer"

    now_str = datetime.now(timezone.utc).isoformat()
    trip["review_decision"] = body.decision
    trip["reviewer_id"] = reviewer_identity
    trip["updated_at"] = now_str

    TripStore.save_trip(trip, agency_id=agency_id)

    AuditStore.log_event(
        event_type="proposal_review_signoff",
        user_id=agency_id,
        details={
            "trip_id": body.trip_id,
            "reviewer_id": reviewer_identity,
            "decision": body.decision,
            "notes": body.feedback_notes,
            "auth_verified": True,
            # Authenticated principal + agency (FND-0220): the audit trail
            # records who signed off (principal id) and for which tenant.
            "reviewer_principal_id": principal_id,
            "agency_id": agency_id,
        },
    )

    return ReviewSignoffResponse(
        ok=True,
        trip_id=body.trip_id,
        reviewer_id=reviewer_identity,
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

