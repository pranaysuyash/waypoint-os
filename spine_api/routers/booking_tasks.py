"""
Booking tasks router — CRUD, generation, reconciliation.

Endpoints:
  GET    /api/booking-tasks/{trip_id}              — list tasks + summary
  POST   /api/booking-tasks/{trip_id}              — manually create a task
  POST   /api/booking-tasks/{trip_id}/generate     — generate system tasks + reconcile
  PATCH  /api/booking-tasks/{trip_id}/{task_id}    — update task fields
  POST   /api/booking-tasks/{trip_id}/{task_id}/complete
  POST   /api/booking-tasks/{trip_id}/{task_id}/cancel

Auth model:
  All routes require JWT auth (router-level Depends).
  Tenant scoping: agency_id from JWT membership, never from request body.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from spine_api.core.rls import get_rls_db
from spine_api.core.auth import get_current_agency_id, require_permission, get_current_membership
from spine_api.models.tenant import Membership
from spine_api.services import booking_task_service

logger = logging.getLogger("spine_api.booking_tasks")

router = APIRouter(prefix="/api/booking-tasks", tags=["booking-tasks"])


# ── Request models ────────────────────────────────────────────────────────────

class CreateTaskRequest(BaseModel):
    task_type: str = Field(min_length=1, max_length=40)
    title: str = Field(min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=500)
    priority: str = Field(default="medium", max_length=20)
    owner_id: Optional[str] = None
    due_at: Optional[str] = None


class UpdateTaskRequest(BaseModel):
    status: Optional[str] = Field(default=None, max_length=20)
    priority: Optional[str] = Field(default=None, max_length=20)
    owner_id: Optional[str] = None
    due_at: Optional[str] = None
    title: Optional[str] = Field(default=None, max_length=200)


class GenerateRequest(BaseModel):
    force: bool = False


# ── Response helpers ─────────────────────────────────────────────────────────

def _task_to_dict(task) -> dict:
    return {
        "id": task.id,
        "trip_id": task.trip_id,
        "agency_id": task.agency_id,
        "task_type": task.task_type,
        "title": task.title,
        "description": task.description,
        "status": task.status,
        "priority": task.priority,
        "owner_id": task.owner_id,
        "due_at": task.due_at.isoformat() if task.due_at else None,
        "blocker_code": task.blocker_code,
        "blocker_refs": task.blocker_refs,
        "source": task.source,
        "generation_hash": task.generation_hash,
        "created_by": task.created_by,
        "completed_by": task.completed_by,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        "cancelled_at": task.cancelled_at.isoformat() if task.cancelled_at else None,
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "updated_at": task.updated_at.isoformat() if task.updated_at else None,
    }


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/{trip_id}")
async def list_booking_tasks(
    trip_id: str,
    agency_id: str = Depends(get_current_agency_id),
    membership=require_permission("trips:read"),
    db: AsyncSession = Depends(get_rls_db),
):
    result = await booking_task_service.list_tasks(db, trip_id, agency_id)
    return {
        "ok": True,
        "tasks": [_task_to_dict(t) for t in result.tasks],
        "summary": result.summary,
    }


@router.post("/{trip_id}", status_code=status.HTTP_201_CREATED)
async def create_booking_task(
    trip_id: str,
    request: CreateTaskRequest,
    agency_id: str = Depends(get_current_agency_id),
    membership: Membership = Depends(get_current_membership),
    db: AsyncSession = Depends(get_rls_db),
):
    data = request.model_dump(exclude_none=True)
    try:
        task = await booking_task_service.create_task(
            db,
            trip_id=trip_id,
            agency_id=agency_id,
            created_by=membership.user_id,
            data=data,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    logger.info("task created: id=%s type=%s source=agent_created by=%s", task.id, task.task_type, membership.user_id)
    return {"ok": True, "task": _task_to_dict(task)}


@router.post("/{trip_id}/generate")
async def generate_booking_tasks(
    trip_id: str,
    request: GenerateRequest = None,
    agency_id: str = Depends(get_current_agency_id),
    membership: Membership = Depends(get_current_membership),
    db: AsyncSession = Depends(get_rls_db),
):
    force = request.force if request else False
    try:
        result = await booking_task_service.generate_tasks(
            db,
            trip_id=trip_id,
            agency_id=agency_id,
            generated_by=membership.user_id,
            force=force,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    logger.info(
        "tasks generated: trip=%s created=%d skipped=%d reconciled=%d by=%s",
        trip_id, len(result.created), len(result.skipped), len(result.reconciled), membership.user_id,
    )
    return {
        "ok": True,
        "created": [_task_to_dict(t) for t in result.created],
        "skipped": result.skipped,
        "reconciled": [
            {"task_id": r.task_id, "old_status": r.old_status, "new_status": r.new_status}
            for r in result.reconciled
        ],
    }


@router.patch("/{trip_id}/{task_id}")
async def update_booking_task(
    trip_id: str,
    task_id: str,
    request: UpdateTaskRequest,
    agency_id: str = Depends(get_current_agency_id),
    membership=require_permission("trips:write"),
    db: AsyncSession = Depends(get_rls_db),
):
    data = request.model_dump(exclude_none=True)
    if not data:
        raise HTTPException(status_code=400, detail="No fields to update")

    try:
        task = await booking_task_service.update_task(
            db,
            task_id=task_id,
            agency_id=agency_id,
            data=data,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    logger.info("task updated: id=%s type=%s fields=%s", task.id, task.task_type, ",".join(data.keys()))
    return {"ok": True, "task": _task_to_dict(task)}


@router.post("/{trip_id}/{task_id}/complete")
async def complete_booking_task(
    trip_id: str,
    task_id: str,
    agency_id: str = Depends(get_current_agency_id),
    membership: Membership = Depends(get_current_membership),
    db: AsyncSession = Depends(get_rls_db),
):
    try:
        task = await booking_task_service.complete_task(
            db,
            task_id=task_id,
            agency_id=agency_id,
            completed_by=membership.user_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    logger.info("task completed: id=%s type=%s by=%s", task.id, task.task_type, membership.user_id)
    return {"ok": True, "task": _task_to_dict(task)}


@router.post("/{trip_id}/{task_id}/cancel")
async def cancel_booking_task(
    trip_id: str,
    task_id: str,
    agency_id: str = Depends(get_current_agency_id),
    membership=require_permission("trips:write"),
    db: AsyncSession = Depends(get_rls_db),
):
    try:
        task = await booking_task_service.cancel_task(
            db,
            task_id=task_id,
            agency_id=agency_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    logger.info("task cancelled: id=%s type=%s", task.id, task.task_type)
    return {"ok": True, "task": _task_to_dict(task)}
