"""
Durable Agent Lease & Distributed Fencing Token API Router.

Provides endpoints for distributed lease acquisition, heartbeat renewal,
fencing token validation, and stale lock reclamation.
"""

from __future__ import annotations

from typing import Any, Dict
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.orchestration.agent_lease import DurableAgentLeaseManager

router = APIRouter(prefix="/api/v1/orchestration/leases", tags=["agent-leases"])


class AcquireLeaseRequest(BaseModel):
    trip_id: str
    holder_id: str
    ttl_seconds: int = Field(30, ge=5, le=300)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RenewLeaseRequest(BaseModel):
    trip_id: str
    lease_token: str
    ttl_seconds: int = Field(30, ge=5, le=300)


class ReleaseLeaseRequest(BaseModel):
    trip_id: str
    lease_token: str


class VerifyFencingTokenRequest(BaseModel):
    trip_id: str
    fencing_token: int


@router.post("/acquire")
def acquire_trip_lease(payload: AcquireLeaseRequest) -> Dict[str, Any]:
    """Acquire exclusive lease on a trip with a monotonic fencing token."""
    try:
        lease = DurableAgentLeaseManager.acquire_lease(
            trip_id=payload.trip_id,
            holder_id=payload.holder_id,
            ttl_seconds=payload.ttl_seconds,
            metadata=payload.metadata,
        )
        return {
            "status": "acquired",
            "lease": lease.to_dict(),
        }
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.post("/renew")
def renew_trip_lease(payload: RenewLeaseRequest) -> Dict[str, Any]:
    """Renew active lease heartbeat."""
    try:
        lease = DurableAgentLeaseManager.renew_lease(
            trip_id=payload.trip_id,
            lease_token=payload.lease_token,
            ttl_seconds=payload.ttl_seconds,
        )
        return {
            "status": "renewed",
            "lease": lease.to_dict(),
        }
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/release")
def release_trip_lease(payload: ReleaseLeaseRequest) -> Dict[str, Any]:
    """Voluntarily release held lease."""
    released = DurableAgentLeaseManager.release_lease(
        trip_id=payload.trip_id,
        lease_token=payload.lease_token,
    )
    return {
        "status": "released" if released else "not_found",
        "released": released,
        "trip_id": payload.trip_id,
    }


@router.post("/verify-fencing")
def verify_fencing_token(payload: VerifyFencingTokenRequest) -> Dict[str, Any]:
    """Verify if a fencing token is current (rejects stale/zombie writes)."""
    valid = DurableAgentLeaseManager.verify_fencing_token(
        trip_id=payload.trip_id,
        fencing_token=payload.fencing_token,
    )
    return {
        "status": "valid" if valid else "stale_or_invalid",
        "is_valid": valid,
        "trip_id": payload.trip_id,
        "fencing_token": payload.fencing_token,
    }


@router.get("/{trip_id}")
def inspect_trip_lease(trip_id: str) -> Dict[str, Any]:
    """Inspect current lease status for a trip."""
    lease = DurableAgentLeaseManager.get_lease(trip_id)
    if not lease:
        return {"status": "unlocked", "trip_id": trip_id, "lease": None}
    return {
        "status": "locked" if (lease.is_active and not lease.is_expired()) else "unlocked",
        "trip_id": trip_id,
        "lease": lease.to_dict(),
    }
