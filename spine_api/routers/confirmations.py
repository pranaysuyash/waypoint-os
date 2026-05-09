"""
Confirmations router — CRUD, state transitions, execution timeline.

Endpoints:
  GET    /api/trips/{trip_id}/confirmations             — list (summary)
  GET    /api/trips/{trip_id}/confirmations/{id}         — detail
  POST   /api/trips/{trip_id}/confirmations              — create
  PATCH  /api/trips/{trip_id}/confirmations/{id}         — update
  POST   /api/trips/{trip_id}/confirmations/{id}/record  — draft→recorded
  POST   /api/trips/{trip_id}/confirmations/{id}/verify  — recorded→verified
  POST   /api/trips/{trip_id}/confirmations/{id}/void    — any→voided
  GET    /api/trips/{trip_id}/execution-timeline          — timeline

Auth model:
  All routes require JWT auth (router-level Depends).
  Tenant scoping: agency_id from JWT membership, never from request body.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from spine_api.core.rls import get_rls_db
from spine_api.core.auth import get_current_agency_id, require_permission, get_current_membership
from spine_api.models.tenant import Membership
from spine_api.services import confirmation_service, execution_event_service

logger = logging.getLogger("spine_api.confirmations")

router = APIRouter(prefix="/api/trips", tags=["confirmations"])


# ── Request models ────────────────────────────────────────────────────────────

class CreateConfirmationRequest(BaseModel):
    confirmation_type: str = Field(min_length=1, max_length=20)
    task_id: Optional[str] = None
    supplier_name: Optional[str] = Field(default=None, max_length=200)
    confirmation_number: Optional[str] = Field(default=None, max_length=100)
    notes: Optional[str] = Field(default=None, max_length=2000)
    external_ref: Optional[str] = Field(default=None, max_length=200)
    evidence_refs: Optional[list[dict]] = None


class UpdateConfirmationRequest(BaseModel):
    confirmation_type: Optional[str] = Field(default=None, max_length=20)
    task_id: Optional[str] = None
    supplier_name: Optional[str] = Field(default=None, max_length=200)
    confirmation_number: Optional[str] = Field(default=None, max_length=100)
    notes: Optional[str] = Field(default=None, max_length=2000)
    external_ref: Optional[str] = Field(default=None, max_length=200)
    evidence_refs: Optional[list[dict]] = None


# ── Summary response helper ──────────────────────────────────────────────────

def _summary_to_dict(s: confirmation_service.ConfirmationSummary) -> dict:
    return {
        "id": s.id,
        "trip_id": s.trip_id,
        "task_id": s.task_id,
        "confirmation_type": s.confirmation_type,
        "confirmation_status": s.confirmation_status,
        "has_supplier": s.has_supplier,
        "has_confirmation_number": s.has_confirmation_number,
        "external_ref_present": s.external_ref_present,
        "notes_present": s.notes_present,
        "evidence_ref_count": s.evidence_ref_count,
        "recorded_at": s.recorded_at.isoformat() if s.recorded_at else None,
        "verified_at": s.verified_at.isoformat() if s.verified_at else None,
        "voided_at": s.voided_at.isoformat() if s.voided_at else None,
        "created_by": s.created_by,
        "created_at": s.created_at.isoformat() if s.created_at else None,
    }


def _detail_to_dict(d: confirmation_service.ConfirmationDetail) -> dict:
    return {
        "id": d.id,
        "trip_id": d.trip_id,
        "task_id": d.task_id,
        "confirmation_type": d.confirmation_type,
        "confirmation_status": d.confirmation_status,
        "has_supplier": d.has_supplier,
        "has_confirmation_number": d.has_confirmation_number,
        "external_ref_present": d.external_ref_present,
        "notes_present": d.notes_present,
        "evidence_refs": d.evidence_refs,
        "evidence_ref_count": d.evidence_ref_count,
        "supplier_name": d.supplier_name,
        "confirmation_number": d.confirmation_number,
        "notes": d.notes,
        "external_ref": d.external_ref,
        "recorded_by": d.recorded_by,
        "recorded_at": d.recorded_at.isoformat() if d.recorded_at else None,
        "verified_by": d.verified_by,
        "verified_at": d.verified_at.isoformat() if d.verified_at else None,
        "voided_by": d.voided_by,
        "voided_at": d.voided_at.isoformat() if d.voided_at else None,
        "created_by": d.created_by,
        "created_at": d.created_at.isoformat() if d.created_at else None,
        "updated_at": d.updated_at.isoformat() if d.updated_at else None,
    }


def _timeline_event_to_dict(e: execution_event_service.TimelineEvent) -> dict:
    return {
        "event_type": e.event_type,
        "event_category": e.event_category,
        "subject_type": e.subject_type,
        "subject_id": e.subject_id,
        "status_from": e.status_from,
        "status_to": e.status_to,
        "actor_type": e.actor_type,
        "actor_id": e.actor_id,
        "source": e.source,
        "event_metadata": e.event_metadata,
        "timestamp": e.created_at.isoformat() if e.created_at else None,
    }


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/{trip_id}/confirmations")
async def list_confirmations(
    trip_id: str,
    agency_id: str = Depends(get_current_agency_id),
    membership=require_permission("trips:read"),
    db: AsyncSession = Depends(get_rls_db),
):
    summaries = await confirmation_service.list_confirmations(db, trip_id, agency_id)
    return {
        "ok": True,
        "confirmations": [_summary_to_dict(s) for s in summaries],
    }


@router.get("/{trip_id}/confirmations/{confirmation_id}")
async def get_confirmation(
    trip_id: str,
    confirmation_id: str,
    agency_id: str = Depends(get_current_agency_id),
    membership=require_permission("trips:read"),
    db: AsyncSession = Depends(get_rls_db),
):
    try:
        detail = await confirmation_service.get_confirmation(db, confirmation_id, agency_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"ok": True, "confirmation": _detail_to_dict(detail)}


@router.post("/{trip_id}/confirmations", status_code=201)
async def create_confirmation(
    trip_id: str,
    request: CreateConfirmationRequest,
    agency_id: str = Depends(get_current_agency_id),
    membership: Membership = Depends(get_current_membership),
    db: AsyncSession = Depends(get_rls_db),
):
    data = request.model_dump(exclude_none=True)
    try:
        detail = await confirmation_service.create_confirmation(
            db,
            trip_id=trip_id,
            agency_id=agency_id,
            created_by=membership.user_id,
            data=data,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    logger.info(
        "confirmation created: id=%s type=%s by=%s",
        detail.id, detail.confirmation_type, membership.user_id,
    )
    return {"ok": True, "confirmation": _detail_to_dict(detail)}


@router.patch("/{trip_id}/confirmations/{confirmation_id}")
async def update_confirmation(
    trip_id: str,
    confirmation_id: str,
    request: UpdateConfirmationRequest,
    agency_id: str = Depends(get_current_agency_id),
    membership: Membership = Depends(get_current_membership),
    db: AsyncSession = Depends(get_rls_db),
):
    data = request.model_dump(exclude_none=True)
    if not data:
        raise HTTPException(status_code=400, detail="No fields to update")

    try:
        detail = await confirmation_service.update_confirmation(
            db,
            confirmation_id=confirmation_id,
            agency_id=agency_id,
            data=data,
            updated_by=membership.user_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    logger.info(
        "confirmation updated: id=%s type=%s fields=%s",
        detail.id, detail.confirmation_type, ",".join(data.keys()),
    )
    return {"ok": True, "confirmation": _detail_to_dict(detail)}


@router.post("/{trip_id}/confirmations/{confirmation_id}/record")
async def record_confirmation(
    trip_id: str,
    confirmation_id: str,
    agency_id: str = Depends(get_current_agency_id),
    membership: Membership = Depends(get_current_membership),
    db: AsyncSession = Depends(get_rls_db),
):
    try:
        summary = await confirmation_service.record_confirmation(
            db,
            confirmation_id=confirmation_id,
            agency_id=agency_id,
            recorded_by=membership.user_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    logger.info("confirmation recorded: id=%s by=%s", confirmation_id, membership.user_id)
    return {"ok": True, "confirmation": _summary_to_dict(summary)}


@router.post("/{trip_id}/confirmations/{confirmation_id}/verify")
async def verify_confirmation(
    trip_id: str,
    confirmation_id: str,
    agency_id: str = Depends(get_current_agency_id),
    membership: Membership = Depends(get_current_membership),
    db: AsyncSession = Depends(get_rls_db),
):
    try:
        summary = await confirmation_service.verify_confirmation(
            db,
            confirmation_id=confirmation_id,
            agency_id=agency_id,
            verified_by=membership.user_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    logger.info("confirmation verified: id=%s by=%s", confirmation_id, membership.user_id)
    return {"ok": True, "confirmation": _summary_to_dict(summary)}


@router.post("/{trip_id}/confirmations/{confirmation_id}/void")
async def void_confirmation(
    trip_id: str,
    confirmation_id: str,
    agency_id: str = Depends(get_current_agency_id),
    membership: Membership = Depends(get_current_membership),
    db: AsyncSession = Depends(get_rls_db),
):
    try:
        summary = await confirmation_service.void_confirmation(
            db,
            confirmation_id=confirmation_id,
            agency_id=agency_id,
            voided_by=membership.user_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    logger.info("confirmation voided: id=%s by=%s", confirmation_id, membership.user_id)
    return {"ok": True, "confirmation": _summary_to_dict(summary)}


@router.get("/{trip_id}/execution-timeline")
async def get_execution_timeline(
    trip_id: str,
    category: Optional[str] = None,
    agency_id: str = Depends(get_current_agency_id),
    membership=require_permission("trips:read"),
    db: AsyncSession = Depends(get_rls_db),
):
    result = await execution_event_service.get_timeline(db, trip_id, agency_id, category)
    return {
        "ok": True,
        "events": [_timeline_event_to_dict(e) for e in result.events],
        "summary": result.summary,
    }
