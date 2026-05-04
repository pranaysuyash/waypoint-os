"""
Assignments router — routing state machine REST endpoints.

All mutations transition the TripRoutingState through the state machine
defined in routing_service.py. Each action emits an audit event.

Endpoints:
  GET  /api/assignments/{trip_id}         — current routing state + SLA
  POST /api/assignments/{trip_id}/assign  — admin assigns trip
  POST /api/assignments/{trip_id}/claim   — senior agent self-assigns
  POST /api/assignments/{trip_id}/escalate
  POST /api/assignments/{trip_id}/reassign
  POST /api/assignments/{trip_id}/return
  POST /api/assignments/{trip_id}/unassign

Auth model:
  All routes require JWT authentication (via router-level Depends).
  Tenant scoping: agency_id is always sourced from the JWT membership,
  never from the request body.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from spine_api.core.rls import get_rls_db
from spine_api.core.auth import get_current_agency_id, require_permission
from spine_api.services import routing_service
from spine_api.services.routing_service import RoutingError
from spine_api.services.sla_service import compute_sla

logger = logging.getLogger("spine_api.assignments")

router = APIRouter(prefix="/api/assignments", tags=["assignments"])


# ── Request models ────────────────────────────────────────────────────────────

class AssignRequest(BaseModel):
    assignee_id: str = Field(min_length=1)


class EscalateRequest(BaseModel):
    escalation_owner_id: str = Field(min_length=1)
    reason: Optional[str] = Field(default=None, max_length=1000)


class ReassignRequest(BaseModel):
    new_assignee_id: str = Field(min_length=1)
    reason: Optional[str] = Field(default=None, max_length=1000)


class ReturnRequest(BaseModel):
    reason: Optional[str] = Field(default=None, max_length=1000)


class UnassignRequest(BaseModel):
    reason: Optional[str] = Field(default=None, max_length=1000)


# ── Response helper ───────────────────────────────────────────────────────────

def _routing_response(state: dict) -> dict:
    return {"ok": True, "routing_state": state, "sla": compute_sla(state)}


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/{trip_id}")
async def get_routing_state(
    trip_id: str,
    agency_id: str = Depends(get_current_agency_id),
    membership=require_permission("trips:read"),
    db: AsyncSession = Depends(get_rls_db),
):
    state = await routing_service.get_routing_state(db, trip_id, agency_id)
    if state is None:
        # Trip exists but has no routing record yet — return a virtual unassigned state.
        return {
            "ok": True,
            "routing_state": {
                "trip_id": trip_id,
                "agency_id": agency_id,
                "status": "unassigned",
                "primary_assignee_id": None,
                "reviewer_id": None,
                "escalation_owner_id": None,
                "assigned_at": None,
                "escalated_at": None,
                "handoff_history": [],
            },
            "sla": compute_sla({"assigned_at": None, "escalated_at": None}),
        }
    return _routing_response(state)


@router.post("/{trip_id}/assign", status_code=status.HTTP_200_OK)
async def post_assign(
    trip_id: str,
    request: AssignRequest,
    membership=require_permission("trips:assign"),
    db: AsyncSession = Depends(get_rls_db),
):
    try:
        state = await routing_service.assign_trip(
            db,
            trip_id=trip_id,
            agency_id=membership.agency_id,
            assignee_id=request.assignee_id,
            assigned_by=membership.user_id,
        )
    except RoutingError as e:
        raise HTTPException(status_code=409, detail=str(e))

    logger.info("Trip assigned: trip=%s assignee=%s by=%s", trip_id, request.assignee_id, membership.user_id)
    return _routing_response(state)


@router.post("/{trip_id}/claim", status_code=status.HTTP_200_OK)
async def post_claim(
    trip_id: str,
    membership=require_permission("trips:claim"),
    db: AsyncSession = Depends(get_rls_db),
):
    try:
        state = await routing_service.claim_trip(
            db,
            trip_id=trip_id,
            agency_id=membership.agency_id,
            claimer_id=membership.user_id,
        )
    except RoutingError as e:
        raise HTTPException(status_code=409, detail=str(e))

    logger.info("Trip claimed: trip=%s by=%s", trip_id, membership.user_id)
    return _routing_response(state)


@router.post("/{trip_id}/escalate", status_code=status.HTTP_200_OK)
async def post_escalate(
    trip_id: str,
    request: EscalateRequest,
    membership=require_permission("trips:escalate"),
    db: AsyncSession = Depends(get_rls_db),
):
    try:
        state = await routing_service.escalate_trip(
            db,
            trip_id=trip_id,
            agency_id=membership.agency_id,
            escalation_owner_id=request.escalation_owner_id,
            escalated_by=membership.user_id,
            reason=request.reason,
        )
    except RoutingError as e:
        raise HTTPException(status_code=409, detail=str(e))

    logger.info("Trip escalated: trip=%s escalation_owner=%s", trip_id, request.escalation_owner_id)
    return _routing_response(state)


@router.post("/{trip_id}/reassign", status_code=status.HTTP_200_OK)
async def post_reassign(
    trip_id: str,
    request: ReassignRequest,
    membership=require_permission("trips:reassign"),
    db: AsyncSession = Depends(get_rls_db),
):
    try:
        state = await routing_service.reassign_trip(
            db,
            trip_id=trip_id,
            agency_id=membership.agency_id,
            new_assignee_id=request.new_assignee_id,
            reassigned_by=membership.user_id,
            reason=request.reason,
        )
    except RoutingError as e:
        raise HTTPException(status_code=409, detail=str(e))

    logger.info("Trip reassigned: trip=%s new_assignee=%s", trip_id, request.new_assignee_id)
    return _routing_response(state)


@router.post("/{trip_id}/return", status_code=status.HTTP_200_OK)
async def post_return(
    trip_id: str,
    request: ReturnRequest,
    membership=require_permission("trips:write"),
    db: AsyncSession = Depends(get_rls_db),
):
    try:
        state = await routing_service.return_for_changes(
            db,
            trip_id=trip_id,
            agency_id=membership.agency_id,
            returned_by=membership.user_id,
            reason=request.reason,
        )
    except RoutingError as e:
        raise HTTPException(status_code=409, detail=str(e))

    logger.info("Trip returned for changes: trip=%s by=%s", trip_id, membership.user_id)
    return _routing_response(state)


@router.post("/{trip_id}/unassign", status_code=status.HTTP_200_OK)
async def post_unassign(
    trip_id: str,
    request: UnassignRequest,
    membership=require_permission("trips:assign"),
    db: AsyncSession = Depends(get_rls_db),
):
    try:
        state = await routing_service.unassign_trip(
            db,
            trip_id=trip_id,
            agency_id=membership.agency_id,
            unassigned_by=membership.user_id,
            reason=request.reason,
        )
    except RoutingError as e:
        raise HTTPException(status_code=409, detail=str(e))

    logger.info("Trip unassigned: trip=%s by=%s", trip_id, membership.user_id)
    return _routing_response(state)
