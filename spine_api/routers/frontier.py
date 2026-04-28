"""
Frontier Features Router for Waypoint OS.
"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from spine_api.core.database import get_db
from spine_api.models.frontier import GhostWorkflow, EmotionalStateLog, IntelligencePoolRecord, LegacyAspiration
from spine_api.contract import (
    SpineRunResponse, # Fallback if needed
)
from pydantic import BaseModel, Field

router = APIRouter(prefix="/frontier", tags=["Frontier"])

# =============================================================================
# Pydantic Models (Internal to Frontier Router for now)
# =============================================================================

class GhostWorkflowCreate(BaseModel):
    agency_id: str
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
    agency_id: str
    traveler_id: str
    trip_id: str
    sentiment_score: float = Field(..., ge=0.0, le=1.0)
    anxiety_trigger: Optional[str] = None
    mitigation_action_id: Optional[str] = None

class IntelligencePoolRequest(BaseModel):
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
    db: AsyncSession = Depends(get_db)
):
    """Start a new autonomic Ghost Concierge workflow."""
    workflow = GhostWorkflow(
        id=str(uuid.uuid4()),
        agency_id=request.agency_id,
        trip_id=request.trip_id,
        task_type=request.task_type,
        action_payload=request.action_payload,
        autonomic_level=request.autonomic_level,
        status="pending",
        started_at=datetime.now(timezone.utc)
    )
    db.add(workflow)
    await db.commit()
    await db.refresh(workflow)
    return workflow

@router.get("/ghost/workflows/{workflow_id}", response_model=GhostWorkflowResponse)
async def get_ghost_workflow(
    workflow_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Retrieve the status of a Ghost workflow."""
    result = await db.execute(select(GhostWorkflow).where(GhostWorkflow.id == workflow_id))
    workflow = result.scalar_one_or_none()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow

@router.post("/emotions/log")
async def log_emotional_state(
    request: EmotionalLogRequest,
    db: AsyncSession = Depends(get_db)
):
    """Log traveler emotional state for sentiment tracking."""
    log = EmotionalStateLog(
        id=str(uuid.uuid4()),
        agency_id=request.agency_id,
        traveler_id=request.traveler_id,
        trip_id=request.trip_id,
        sentiment_score=request.sentiment_score,
        anxiety_trigger=request.anxiety_trigger,
        mitigation_action_id=request.mitigation_action_id,
        recorded_at=datetime.now(timezone.utc)
    )
    db.add(log)
    await db.commit()
    return {"ok": True, "log_id": log.id}

@router.post("/intelligence/report")
async def report_intelligence(
    request: IntelligencePoolRequest,
    db: AsyncSession = Depends(get_db)
):
    """Submit anonymized risk data to the federated intelligence pool."""
    record = IntelligencePoolRecord(
        id=str(uuid.uuid4()),
        incident_type=request.incident_type,
        anonymized_data=request.anonymized_data,
        severity=request.severity,
        confidence=request.confidence,
        source_agency_hash=request.source_agency_hash,
        verified_at=datetime.now(timezone.utc)
    )
    db.add(record)
    await db.commit()
    return {"ok": True, "record_id": record.id}
