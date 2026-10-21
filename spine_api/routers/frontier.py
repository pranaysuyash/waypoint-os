"""
Frontier Features Router for Waypoint OS.

Tenant isolation: agency_id is ALWAYS sourced from the authenticated user's JWT
membership via get_current_agency_id — never from caller-supplied request body.
This prevents cross-tenant data injection by any authenticated user.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from spine_api.core.auth import get_current_agency_id, require_permission
from spine_api.core.rls import get_rls_db
from spine_api.models.frontier import EmotionalStateLog, IntelligencePoolRecord
from spine_api.core.reality_tier import RealityTier, TierMetadata
from pydantic import BaseModel, Field

router = APIRouter(prefix="/frontier", tags=["Frontier"])

# =============================================================================
# Pydantic Models
# Note: agency_id is intentionally absent from all request schemas.
# It is injected via the get_current_agency_id dependency so that callers
# cannot target another tenant's data.
# =============================================================================

class GhostWorkflowResponse(BaseModel):
    id: str
    agency_id: str
    trip_id: str
    task_type: str
    status: str
    autonomic_level: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    # ADR-008 item 5 (Addendum 9): every frontier surface declares its
    # reality tier — these are simulated/dev surfaces, never operator authority.
    # Default uses the canonical spine_api/core/reality_tier vocabulary.
    reality_tier: str = "planned"
    tier_metadata: Optional[Dict[str, Any]] = None


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

@router.post("/emotions/log")
async def log_emotional_state(
    request: EmotionalLogRequest,
    agency_id: str = Depends(get_current_agency_id),
    membership=require_permission("trips:write"),
    db: AsyncSession = Depends(get_rls_db),
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
    # ADR-008 item 5 (Addendum 9): the write itself is real, but the
    # mitigation-action semantics have no downstream consumer — declared
    # data-dependent so the surface never claims more than storage.
    return {
        "ok": True,
        "log_id": log.id,
        "reality_tier": RealityTier.DATA_DEPENDENT.value,
        "tier_metadata": TierMetadata.for_response(
            RealityTier.DATA_DEPENDENT,
            feature_name="frontier.emotional_state_log",
            data_sufficient=True,
            computation_method="durable storage of operator-reported sentiment; no inference",
            missing_for_upgrade=["downstream consumer for mitigation actions"],
        ),
    }


@router.post("/intelligence/report")
async def report_intelligence(
    request: IntelligencePoolRequest,
    _agency_id: str = Depends(get_current_agency_id),  # Auth required; data is anonymized
    membership=require_permission("trips:write"),
    db: AsyncSession = Depends(get_rls_db),
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
    # ADR-008 item 5 (Addendum 9): the pool has no retrieval consumer yet —
    # architecture built, capability not connected (PLANNED).
    return {
        "ok": True,
        "record_id": record.id,
        "reality_tier": RealityTier.PLANNED.value,
        "tier_metadata": TierMetadata.for_response(
            RealityTier.PLANNED,
            feature_name="frontier.intelligence_pool",
            data_sufficient=True,
            computation_method="durable pool write; no retrieval consumer",
            missing_for_upgrade=["pool retrieval consumer", "anonymization verification contract"],
        ),
    }
