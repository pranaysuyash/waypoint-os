"""
Frontier Features Router for Waypoint OS.

Tenant isolation: agency_id is ALWAYS sourced from the authenticated user's JWT
membership via get_current_agency_id — never from caller-supplied request body.
This prevents cross-tenant data injection by any authenticated user.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from spine_api.core.auth import get_current_agency_id, require_permission
from spine_api.core.database import get_db
from spine_api.models.frontier import GhostWorkflow, EmotionalStateLog, IntelligencePoolRecord
from pydantic import BaseModel, Field

router = APIRouter(prefix="/frontier", tags=["Frontier"])

# =============================================================================
# Pydantic Models
# Note: agency_id is intentionally absent from all request schemas.
# It is injected via the get_current_agency_id dependency so that callers
# cannot target another tenant's data.
# =============================================================================

class GhostWorkflowCreate(BaseModel):
    trip_id: str
    task_type: str
    action_payload: Optional[Dict[str, Any]] = None
    autonomic_level: int = 0


class GhostWorkflowResponse(BaseModel):
    id: str
    agency_id: str
    trip_id: str
    task_type: str
    status: str
    autonomic_level: int
    started_at: datetime
    completed_at: Optional[datetime] = None


class EmotionalLogRequest(BaseModel):
    traveler_id: str
    trip_id: str
    sentiment_score: float = Field(..., ge=0.0, le=1.0)
    anxiety_trigger: Optional[str] = None
    mitigation_action_id: Optional[str] = None


class IntelligencePoolRequest(BaseModel):
    """Federated cross-agency risk intelligence — anonymized by design, no agency_id."""
    incident_type: str
    anonymized_data: Dict[str, Any]
    severity: int = Field(1, ge=1, le=5)
    confidence: float = Field(1.0, ge=0.0, le=1.0)
    source_agency_hash: str


# =============================================================================
# Routes
# =============================================================================

@router.post("/ghost/workflows", response_model=GhostWorkflowResponse)
async def create_ghost_workflow(
    request: GhostWorkflowCreate,
    agency_id: str = Depends(get_current_agency_id),
    membership=require_permission("ai_workforce:manage"),
    db: AsyncSession = Depends(get_db),
):
    """Start a new autonomic Ghost Concierge workflow scoped to the caller's agency."""
    workflow = GhostWorkflow(
        id=str(uuid.uuid4()),
        agency_id=agency_id,
        trip_id=request.trip_id,
        task_type=request.task_type,
        action_payload=request.action_payload,
        autonomic_level=request.autonomic_level,
        status="pending",
        started_at=datetime.now(timezone.utc),
    )
    db.add(workflow)
    await db.commit()
    await db.refresh(workflow)
    return workflow


@router.get("/ghost/workflows/{workflow_id}", response_model=GhostWorkflowResponse)
async def get_ghost_workflow(
    workflow_id: str,
    agency_id: str = Depends(get_current_agency_id),
    membership=require_permission("trips:read"),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve a Ghost workflow — returns 404 if not found or not owned by caller's agency."""
    result = await db.execute(
        select(GhostWorkflow).where(GhostWorkflow.id == workflow_id)
    )
    workflow = result.scalar_one_or_none()

    # 404 (not 403) to avoid confirming whether the workflow exists for another tenant.
    if not workflow or workflow.agency_id != agency_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")

    return workflow


@router.post("/emotions/log")
async def log_emotional_state(
    request: EmotionalLogRequest,
    agency_id: str = Depends(get_current_agency_id),
    membership=require_permission("trips:write"),
    db: AsyncSession = Depends(get_db),
):
    """Log traveler emotional state scoped to the caller's agency."""
    log = EmotionalStateLog(
        id=str(uuid.uuid4()),
        agency_id=agency_id,
        traveler_id=request.traveler_id,
        trip_id=request.trip_id,
        sentiment_score=request.sentiment_score,
        anxiety_trigger=request.anxiety_trigger,
        mitigation_action_id=request.mitigation_action_id,
        recorded_at=datetime.now(timezone.utc),
    )
    db.add(log)
    await db.commit()
    return {"ok": True, "log_id": log.id}


@router.post("/intelligence/report")
async def report_intelligence(
    request: IntelligencePoolRequest,
    _agency_id: str = Depends(get_current_agency_id),  # Auth required; data is anonymized
    membership=require_permission("trips:write"),
    db: AsyncSession = Depends(get_db),
):
    """Submit anonymized risk data to the federated intelligence pool.

    The intelligence pool is cross-agency by design (source_agency_hash instead of
    agency_id). The _agency_id dependency is retained to enforce authentication without
    storing the caller's identity in the pooled record.
    """
    record = IntelligencePoolRecord(
        id=str(uuid.uuid4()),
        incident_type=request.incident_type,
        anonymized_data=request.anonymized_data,
        severity=request.severity,
        confidence=request.confidence,
        source_agency_hash=request.source_agency_hash,
        verified_at=datetime.now(timezone.utc),
    )
    db.add(record)
    await db.commit()
    return {"ok": True, "record_id": record.id}
