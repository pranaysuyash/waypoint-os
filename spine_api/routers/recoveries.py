"""
spine_api/routers/recoveries.py — Recoveries Ledger API (T10, phase 1).

  GET  /api/v1/recoveries                     — agency feed (filters)
  GET  /api/v1/trips/{trip_id}/recoveries     — trip-scoped
  POST /api/v1/trips/{trip_id}/recoveries     — record a recovery
  POST /api/v1/recoveries/{id}/transition     — CAS lifecycle transition

Tracking-only: the ledger never moves money (permanent boundary). Amounts
carry honesty bases — modeled (statutory estimate) vs confirmed
(counterparty-acknowledged).
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from spine_api.core.auth import get_current_agency, require_permission
from spine_api.models.recovery import RECOVERY_STATUSES, SOURCE_TYPES
from spine_api.models.tenant import Agency
from spine_api.persistence import AuditStore, TripStore
from spine_api.services.recovery_store import RecoveryStore

logger = logging.getLogger("spine_api.recoveries")

router = APIRouter(prefix="/api/v1", tags=["recoveries"])


class CreateRecoveryRequest(BaseModel):
    source_type: str
    counterparty: Optional[str] = Field(default=None, max_length=255)
    traveler_ref: Optional[str] = Field(default=None, max_length=255)
    amount: Optional[float] = Field(default=None, gt=0)
    currency: str = "USD"
    amount_basis: Optional[str] = Field(default=None, max_length=20)
    status: str = "detected"
    details: Optional[Dict[str, Any]] = None
    deadline_at: Optional[str] = Field(default=None, max_length=40)


class TransitionRecoveryRequest(BaseModel):
    to_status: str
    amount: Optional[float] = Field(default=None, gt=0)
    amount_basis: Optional[str] = Field(default=None, max_length=20)
    note: Optional[str] = Field(default=None, max_length=2000)


@router.get("/recoveries")
def list_recoveries(
    status: Optional[str] = None,
    source_type: Optional[str] = None,
    limit: int = Query(default=200, ge=1, le=500),
    agency: Agency = Depends(get_current_agency),
) -> dict:
    if status is not None and status not in RECOVERY_STATUSES:
        raise HTTPException(status_code=422, detail=f"Invalid status: {status}")
    if source_type is not None and source_type not in SOURCE_TYPES:
        raise HTTPException(status_code=422, detail=f"Invalid source_type: {source_type}")
    messages = RecoveryStore.list_recoveries(
        agency_id=agency.id, status=status, source_type=source_type, limit=limit
    )
    return {"ok": True, "recoveries": messages, "count": len(messages)}


@router.get("/trips/{trip_id}/recoveries")
def list_trip_recoveries(
    trip_id: str,
    status: Optional[str] = None,
    agency: Agency = Depends(get_current_agency),
) -> dict:
    trip = TripStore.get_trip_for_agency(trip_id, agency.id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    recoveries = RecoveryStore.list_recoveries(agency_id=agency.id, trip_id=trip_id, status=status)
    return {"ok": True, "trip_id": trip_id, "recoveries": recoveries, "count": len(recoveries)}


@router.post("/trips/{trip_id}/recoveries", status_code=201)
def create_trip_recovery(
    trip_id: str,
    request: CreateRecoveryRequest,
    agency: Agency = Depends(get_current_agency),
    membership=require_permission("trips:write"),
) -> dict:
    trip = TripStore.get_trip_for_agency(trip_id, agency.id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    try:
        record = RecoveryStore.create_recovery(
            agency_id=agency.id,
            source_type=request.source_type,
            created_by=membership.user_id,
            trip_id=trip_id,
            traveler_ref=request.traveler_ref,
            counterparty=request.counterparty,
            amount=request.amount,
            currency=request.currency,
            amount_basis=request.amount_basis,
            status=request.status,
            details=request.details,
            deadline_at=request.deadline_at,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    AuditStore.log_event(
        event_type="recovery_recorded",
        user_id=agency.id,
        details={
            "trip_id": trip_id,
            "recovery_id": record["recovery_id"],
            "source_type": record["source_type"],
            "status": record["status"],
            "amount_basis": record["amount_basis"],
        },
    )
    return {"ok": True, "recovery": record}


@router.post("/recoveries/{recovery_id}/transition")
def transition_recovery(
    recovery_id: str,
    request: TransitionRecoveryRequest,
    agency: Agency = Depends(get_current_agency),
    membership=require_permission("trips:write"),
) -> dict:
    try:
        updated = RecoveryStore.transition_recovery(
            agency_id=agency.id,
            recovery_id=recovery_id,
            to_status=request.to_status,
            actor=membership.user_id,
            amount=request.amount,
            amount_basis=request.amount_basis,
            note=request.note,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    AuditStore.log_event(
        event_type="recovery_transitioned",
        user_id=agency.id,
        details={
            "recovery_id": recovery_id,
            "to_status": updated["status"],
            "amount_basis": updated.get("amount_basis"),
        },
    )
    return {"ok": True, "recovery": updated}
