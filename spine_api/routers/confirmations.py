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
import re
from dataclasses import asdict
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from spine_api.core.rls import get_rls_db
from spine_api.core.auth import get_current_agency_id, require_permission, get_current_membership
from spine_api.models.tenant import EVENT_CATEGORIES, Membership
from spine_api.services import confirmation_service, execution_event_service, agentic_eval_service
from src.evals.agentic_feedback import check_routing_health
from src.evals.audit.public_authority import resolve_routing_health_authority
from src.analytics.logger import TripEventLogger

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


class ExtractConfirmationRequest(BaseModel):
    raw_text: str = Field(..., min_length=5, description="Raw email, voucher, or ticket text to extract from")
    document_name: Optional[str] = None
    auto_record: bool = False
    task_id: Optional[str] = None


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
    actor_type: Optional[str] = None,
    agency_id: str = Depends(get_current_agency_id),
    membership=require_permission("trips:read"),
    db: AsyncSession = Depends(get_rls_db),
):
    if actor_type is not None and actor_type not in ("agent", "system"):
        raise HTTPException(status_code=422, detail=f"Invalid actor_type: {actor_type}")
    if category is not None and category not in EVENT_CATEGORIES:
        raise HTTPException(status_code=422, detail=f"Invalid category: {category}")
    result = await execution_event_service.get_timeline(
        db, trip_id, agency_id, category=category, actor_type=actor_type,
    )
    return {
        "ok": True,
        "events": [_timeline_event_to_dict(e) for e in result.events],
        "summary": result.summary,
    }


@router.get("/{trip_id}/agentic-eval")
async def get_agentic_eval(
    trip_id: str,
    workflow: str | None = None,
    workflow_unit_id: str | None = None,
    min_occurrences: int = Query(3, ge=1, le=20),
    window_minutes: int = Query(24 * 60, ge=1, le=60 * 24 * 14),
    agency_id: str = Depends(get_current_agency_id),
    membership=require_permission("trips:read"),
    db: AsyncSession = Depends(get_rls_db),
):
    if workflow is not None and workflow not in EVENT_CATEGORIES:
        raise HTTPException(status_code=422, detail=f"Invalid workflow: {workflow}")
    summary = await agentic_eval_service.get_trip_agentic_eval_summary(
        db,
        trip_id=trip_id,
        agency_id=agency_id,
        workflow=workflow,
        workflow_unit_id=workflow_unit_id,
        min_occurrences=min_occurrences,
        window_minutes=window_minutes,
    )

    routing_metrics = summary.get("routing_metrics")
    if not isinstance(routing_metrics, dict):
        routing_metrics = {}

    routing_health_authority = resolve_routing_health_authority()
    routing_health_report = check_routing_health(
        routing_metrics,
        thresholds=routing_health_authority.thresholds or None,
    )
    routing_health = {
        **routing_health_report.summary(),
        "metrics_snapshot": routing_health_report.metrics_snapshot,
        "authority": asdict(routing_health_authority),
    }

    if routing_health["status"] in {"warning", "critical"}:
        try:
            TripEventLogger.log_routing_health_alert(
                trip_id=trip_id,
                routing_health=routing_health,
                authority=routing_health["authority"],
                workflow=workflow,
                workflow_unit_id=workflow_unit_id,
                min_occurrences=min_occurrences,
                window_minutes=window_minutes,
                metrics_snapshot=routing_health["metrics_snapshot"],
            )
        except Exception:
            logger.exception("Failed to log routing health alert for trip=%s", trip_id)

    return {
        "ok": True,
        "trip_id": trip_id,
        "workflow": workflow,
        "summary": summary,
        "routing_health": routing_health,
    }


@router.post("/{trip_id}/confirmations/extract")
async def extract_confirmation_data(
    trip_id: str,
    body: ExtractConfirmationRequest,
    agency_id: str = Depends(get_current_agency_id),
    membership=require_permission("trips:write"),
    db: AsyncSession = Depends(get_rls_db),
):
    """Auto-extract PNR, supplier, dates, amounts, and metadata from raw confirmation text."""
    text = body.raw_text
    lower_text = text.lower()

    # Type inference
    conf_type = "other"
    if any(k in lower_text for k in ["flight", "airline", "pnr", "boarding", "ticket", "aircraft", "seat"]):
        conf_type = "flight"
    elif any(k in lower_text for k in ["hotel", "resort", "check-in", "checkout", "room", "suite", "nights"]):
        conf_type = "hotel"
    elif any(k in lower_text for k in ["transfer", "chauffeur", "pickup", "dropoff", "vehicle", "driver"]):
        conf_type = "transfer"
    elif any(k in lower_text for k in ["safari", "tour", "excursion", "helicopter", "cruise", "activity"]):
        conf_type = "activity"
    elif any(k in lower_text for k in ["insurance", "policy", "coverage", "underwriter"]):
        conf_type = "insurance"

    # PNR / Confirmation number extraction
    conf_num = None
    pnr_match = re.search(r"(?:PNR|Booking Ref|Record Locator|Confirmation (?:Number|Code|ID|#)?|Reservation #)[:\s]*([A-Z0-9\-]{5,15})", text, re.IGNORECASE)
    if pnr_match:
        conf_num = pnr_match.group(1).strip()
    else:
        pnr_fallback = re.search(r"\b([A-Z0-9]{6})\b", text)
        if pnr_fallback:
            conf_num = pnr_fallback.group(1).strip()

    # Supplier name detection
    supplier_name = None
    known_suppliers = [
        "Emirates", "Qatar Airways", "Singapore Airlines", "British Airways", "Air India", "Etihad",
        "The Silo Hotel", "The Royal Portfolio", "Wilderness Safaris", "Singita", "Marriott", "Hilton",
        "Four Seasons", "Belmond", "Aman", "NAC Helicopters", "Cape Executive VIP", "Allianz"
    ]
    for s in known_suppliers:
        if s.lower() in lower_text:
            supplier_name = s
            break

    if not supplier_name:
        supp_match = re.search(r"(?:Supplier|Provider|Merchant|Airline|Hotel|Property)[:\s]*([A-Za-z0-9\s&]{3,40})", text, re.IGNORECASE)
        if supp_match:
            supplier_name = supp_match.group(1).strip()

    # Date extraction
    dates = []
    for d_match in re.finditer(r"\b(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4}|\d{4}-\d{2}-\d{2})\b", text, re.IGNORECASE):
        dates.append(d_match.group(1))

    # Amount extraction
    amount = None
    currency = "USD"
    amt_match = re.search(r"(\$|EUR|GBP|INR|AED|USD)\s*([\d,]+(?:\.\d{2})?)", text, re.IGNORECASE)
    if amt_match:
        curr_symbol = amt_match.group(1).upper()
        currency = "USD" if curr_symbol == "$" else curr_symbol
        amount = float(amt_match.group(2).replace(",", ""))

    # Confidence calculation
    confidence = 0.5
    if conf_num:
        confidence += 0.25
    if supplier_name:
        confidence += 0.15
    if conf_type != "other":
        confidence += 0.10
    confidence = min(1.0, confidence)

    extracted_data = {
        "confirmation_type": conf_type,
        "confirmation_number": conf_num or "PENDING-CONF",
        "supplier_name": supplier_name or "Direct Supplier",
        "dates": " - ".join(dates) if dates else "Confirmed Schedule",
        "amount": amount,
        "currency": currency,
        "confidence_score": round(confidence, 2),
        "notes": f"Auto-extracted from {body.document_name or 'document snippet'}",
    }

    created_confirmation = None
    if body.auto_record and conf_num:
        created_confirmation = await confirmation_service.create_confirmation(
            db=db,
            trip_id=trip_id,
            agency_id=agency_id,
            created_by=membership.user_id,
            confirmation_type=conf_type,
            supplier_name=supplier_name or "Direct Supplier",
            confirmation_number=conf_num,
            notes=extracted_data["notes"],
            task_id=body.task_id,
        )

    return {
        "ok": True,
        "trip_id": trip_id,
        "extracted": extracted_data,
        "recorded_confirmation": _detail_to_dict(created_confirmation) if created_confirmation else None,
    }

