"""
Durable Agent Lease & Distributed Fencing Token API Router.

Provides endpoints for distributed lease acquisition, heartbeat renewal,
fencing token validation, and stale lock reclamation.

FND-0213: every endpoint is JWT-authenticated and agency-scoped — the trip
must belong to the caller's agency, and the lease carries the owning
``agency_id`` so renew/release/verify/inspect refuse cross-tenant operations
(with a uniform 404 — no cross-tenant oracle).
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from spine_api.core.auth import get_current_agency_id, get_current_user
from spine_api.persistence import TripStore
from src.orchestration.agent_lease import (
    AgentLeaseRecord,
    DurableAgentLeaseManager,
)

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


def _require_trip_in_agency(trip_id: str, agency_id: str) -> None:
    """FND-0213: the trip must exist inside the caller's agency (404 otherwise)."""
    trip = TripStore.get_trip_for_agency(trip_id, agency_id)
    if trip is None:
        raise HTTPException(status_code=404, detail=f"Trip '{trip_id}' not found in agency scope.")


def _require_lease_in_agency(
    lease: Optional[AgentLeaseRecord], trip_id: str, agency_id: str
) -> AgentLeaseRecord:
    """FND-0213: the lease must belong to the caller's agency (uniform 404, no oracle)."""
    if lease is None:
        raise HTTPException(status_code=404, detail=f"No lease found for trip '{trip_id}'.")
    lease_agency = (lease.metadata or {}).get("agency_id")
    if lease_agency is not None and str(lease_agency) != str(agency_id):
        raise HTTPException(status_code=404, detail=f"No lease found for trip '{trip_id}'.")
    if lease_agency is None:
        # Pre-agency-stamp lease: fall back to trip ownership as the authority.
        _require_trip_in_agency(trip_id, agency_id)
    return lease


@router.post("/acquire")
def acquire_trip_lease(
    payload: AcquireLeaseRequest,
    agency_id: str = Depends(get_current_agency_id),
    current_user=Depends(get_current_user),
) -> Dict[str, Any]:
    """Acquire exclusive lease on a trip with a monotonic fencing token."""
    _require_trip_in_agency(payload.trip_id, agency_id)
    resolved_metadata = dict(payload.metadata or {})
    # FND-0213: the lease records its owning agency; explicit caller value
    # cannot override the authenticated tenant.
    resolved_metadata["agency_id"] = agency_id
    try:
        lease = DurableAgentLeaseManager.acquire_lease(
            trip_id=payload.trip_id,
            holder_id=payload.holder_id,
            ttl_seconds=payload.ttl_seconds,
            metadata=resolved_metadata,
        )
        return {
            "status": "acquired",
            "lease": lease.to_dict(),
        }
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.post("/renew")
def renew_trip_lease(
    payload: RenewLeaseRequest,
    agency_id: str = Depends(get_current_agency_id),
    current_user=Depends(get_current_user),
) -> Dict[str, Any]:
    """Renew active lease heartbeat."""
    _require_trip_in_agency(payload.trip_id, agency_id)
    try:
        lease = DurableAgentLeaseManager.renew_lease(
            trip_id=payload.trip_id,
            lease_token=payload.lease_token,
            ttl_seconds=payload.ttl_seconds,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    _require_lease_in_agency(lease, payload.trip_id, agency_id)
    return {
        "status": "renewed",
        "lease": lease.to_dict(),
    }


@router.post("/release")
def release_trip_lease(
    payload: ReleaseLeaseRequest,
    agency_id: str = Depends(get_current_agency_id),
    current_user=Depends(get_current_user),
) -> Dict[str, Any]:
    """Voluntarily release held lease (idempotent: missing lease → not_found)."""
    _require_trip_in_agency(payload.trip_id, agency_id)
    existing = DurableAgentLeaseManager.get_lease(payload.trip_id)
    if existing is None:
        # Idempotent contract: releasing a never-existing lease is a no-op.
        return {
            "status": "not_found",
            "released": False,
            "trip_id": payload.trip_id,
        }
    _require_lease_in_agency(existing, payload.trip_id, agency_id)
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
def verify_fencing_token(
    payload: VerifyFencingTokenRequest,
    agency_id: str = Depends(get_current_agency_id),
    current_user=Depends(get_current_user),
) -> Dict[str, Any]:
    """Verify if a fencing token is current (rejects stale/zombie writes)."""
    _require_trip_in_agency(payload.trip_id, agency_id)
    existing = DurableAgentLeaseManager.get_lease(payload.trip_id)
    if existing is not None:
        # Cross-tenant probing must not distinguish valid/invalid tokens.
        _require_lease_in_agency(existing, payload.trip_id, agency_id)
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
def inspect_trip_lease(
    trip_id: str,
    agency_id: str = Depends(get_current_agency_id),
    current_user=Depends(get_current_user),
) -> Dict[str, Any]:
    """Inspect current lease status for a trip."""
    _require_trip_in_agency(trip_id, agency_id)
    lease = DurableAgentLeaseManager.get_lease(trip_id)
    if lease is None:
        return {"status": "unlocked", "trip_id": trip_id, "lease": None}
    _require_lease_in_agency(lease, trip_id, agency_id)
    return {
        "status": "locked" if (lease.is_active and not lease.is_expired()) else "unlocked",
        "trip_id": trip_id,
        "lease": lease.to_dict(),
    }
