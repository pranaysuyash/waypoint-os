"""
Team router for Phase 3 Slice E extraction.

Scope: move only
- GET /api/team/members
- GET /api/team/members/{member_id}
- POST /api/team/invite
- PATCH /api/team/members/{member_id}
- DELETE /api/team/members/{member_id}
- GET /api/team/workload
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from spine_api.contract import InviteTeamMemberRequest
from spine_api.core.auth import get_current_agency, get_current_user, require_permission
from spine_api.core.database import get_db
from spine_api.models.tenant import Agency, User
from spine_api.services import membership_service

# Import persistence logic
try:
    from spine_api import persistence
except (ImportError, ValueError):
    import persistence

AssignmentStore = persistence.AssignmentStore
TripStore = persistence.TripStore

router = APIRouter()


@router.get("/api/team/members", response_model=dict)
async def list_team_members(
    agency: Agency = Depends(get_current_agency),
    db: AsyncSession = Depends(get_db),
):
    """List all team members for the current agency."""
    members = await membership_service.list_members(db, agency_id=agency.id)
    return {"items": members, "total": len(members)}


@router.get("/api/team/members/{member_id}")
async def get_team_member(
    member_id: str,
    agency: Agency = Depends(get_current_agency),
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single team member by membership ID."""
    member = await membership_service.get_member(db, member_id, agency.id)
    if not member:
        raise HTTPException(status_code=404, detail="Team member not found")
    return member


@router.post("/api/team/invite")
async def invite_team_member(
    request: InviteTeamMemberRequest,
    agency: Agency = Depends(get_current_agency),
    user: User = Depends(get_current_user),
    _perm=require_permission("team:manage"),
    db: AsyncSession = Depends(get_db),
):
    """Invite a new team member (creates User + Membership)."""
    try:
        member = await membership_service.invite_member(
            db=db,
            agency_id=agency.id,
            email=request.email,
            name=request.name,
            role=request.role,
            capacity=request.capacity,
            specializations=request.specializations,
            invited_by=user.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return {"success": True, "member": member}


@router.patch("/api/team/members/{member_id}")
async def update_team_member(
    member_id: str,
    request: InviteTeamMemberRequest,
    agency: Agency = Depends(get_current_agency),
    _perm=require_permission("team:manage"),
    db: AsyncSession = Depends(get_db),
):
    """Update a team member's role, capacity, or specializations."""
    updates = request.model_dump(exclude_none=True, include={"role", "capacity", "specializations"})
    member = await membership_service.update_member(db, member_id, agency.id, updates)
    if not member:
        raise HTTPException(status_code=404, detail="Team member not found")
    return member


@router.delete("/api/team/members/{member_id}")
async def deactivate_team_member(
    member_id: str,
    agency: Agency = Depends(get_current_agency),
    _perm=require_permission("team:manage"),
    db: AsyncSession = Depends(get_db),
):
    """Deactivate a team member."""
    success = await membership_service.deactivate_member(db, member_id, agency.id)
    if not success:
        raise HTTPException(status_code=404, detail="Team member not found")
    return {"success": True}


@router.get("/api/team/workload")
async def get_workload_distribution(
    agency: Agency = Depends(get_current_agency),
    db: AsyncSession = Depends(get_db),
):
    """Get workload distribution across active team members."""
    members = await membership_service.list_members(db, agency_id=agency.id, active_only=True)
    assignments = AssignmentStore._load_assignments()

    # Get agency trip IDs to filter assignments
    agency_trips = TripStore.list_trips(agency_id=agency.id, limit=10000)
    agency_trip_ids = {t["id"] for t in agency_trips if t.get("id")}

    distribution = []
    for member in members:
        member_id = member["id"]
        assigned_trips = [
            a
            for a in assignments.values()
            if a.get("agent_id") == member_id and a.get("trip_id") in agency_trip_ids
        ]
        distribution.append(
            {
                "member_id": member_id,
                "name": member.get("name"),
                "role": member.get("role"),
                "capacity": member.get("capacity", 5),
                "assigned": len(assigned_trips),
                "available": max(0, member.get("capacity", 5) - len(assigned_trips)),
            }
        )

    return {"items": distribution, "total": len(distribution)}
