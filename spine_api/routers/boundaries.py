"""
spine_api/routers/boundaries.py — Scoped capability tokens, trust zone contracts, and Human-AI Authority Matrix.

Grounding doctrine:
- PER-0933 (Boundary Systems Architect): Boundary contracts, cryptographically signed capability tokens.
- PER-0927 (Human-AI Authority Architect): Authority tier validation and multi-role access gates.
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from spine_api.contract import (
    AuthorityMatrixItem,
    AuthorityMatrixResponse,
    IssueCapabilityTokenRequest,
    IssueCapabilityTokenResponse,
    RevokeCapabilityTokenResponse,
    VerifyCapabilityTokenResponse,
)
from spine_api.core.auth import get_current_agency_id
from src.schemas.boundary_contracts import CapabilityScope
from src.services.boundary_engine import AuthorityGateKeeper, BoundaryEngine

logger = logging.getLogger("spine_api.boundaries")

router = APIRouter(prefix="/api/v1/boundaries", tags=["boundaries"])


@router.post("/tokens/issue", response_model=IssueCapabilityTokenResponse)
def issue_capability_token(
    request: IssueCapabilityTokenRequest,
    agency_id: str = Depends(get_current_agency_id),
) -> IssueCapabilityTokenResponse:
    """
    Issue a cryptographically signed HMAC SHA-256 capability token with granular permissions.
    """
    engine = BoundaryEngine.get_instance()
    try:
        scopes = [CapabilityScope(s.upper()) for s in request.scopes]
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid capability scope: {exc}")

    token_obj = engine.issue_token(
        trip_id=request.trip_id,
        agency_id=agency_id,
        scopes=scopes,
        traveler_id=request.traveler_id,
        traveler_role=request.traveler_role,
        ttl_hours=request.ttl_hours,
        metadata=request.metadata,
    )

    return IssueCapabilityTokenResponse(
        token_id=token_obj.token_id,
        token_string=token_obj.token_string,
        trip_id=token_obj.trip_id,
        agency_id=token_obj.agency_id,
        traveler_id=token_obj.traveler_id,
        traveler_role=token_obj.traveler_role,
        allowed_scopes=[s.value for s in token_obj.allowed_scopes],
        expires_at=token_obj.expires_at,
        issued_at=token_obj.issued_at,
    )


@router.get("/tokens/{token}/verify", response_model=VerifyCapabilityTokenResponse)
def verify_capability_token(
    token: str,
    required_scope: Optional[str] = Query(default=None),
) -> VerifyCapabilityTokenResponse:
    """
    Verify the validity, expiration, revocation status, and allowed scopes of a capability token.
    """
    engine = BoundaryEngine.get_instance()
    req_scope_enum = None
    if required_scope:
        try:
            req_scope_enum = CapabilityScope(required_scope.upper())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid required scope: {required_scope}")

    is_valid, token_obj, message = engine.verify_token(token, required_scope=req_scope_enum)

    if token_obj is None:
        return VerifyCapabilityTokenResponse(
            is_valid=False,
            message=message,
        )

    return VerifyCapabilityTokenResponse(
        is_valid=is_valid,
        token_id=token_obj.token_id,
        trip_id=token_obj.trip_id,
        agency_id=token_obj.agency_id,
        traveler_id=token_obj.traveler_id,
        traveler_role=token_obj.traveler_role,
        allowed_scopes=[s.value for s in token_obj.allowed_scopes],
        expires_at=token_obj.expires_at,
        revoked=token_obj.revoked,
        message=message,
    )


@router.post("/tokens/{token}/revoke", response_model=RevokeCapabilityTokenResponse)
def revoke_capability_token(
    token: str,
    agency_id: str = Depends(get_current_agency_id),
) -> RevokeCapabilityTokenResponse:
    """
    Revoke an active capability token.
    """
    engine = BoundaryEngine.get_instance()
    token_id = token.split(".")[0] if "." in token else token
    success = engine.revoke_token(token)
    if not success:
        raise HTTPException(status_code=404, detail="Token not found or already removed")

    return RevokeCapabilityTokenResponse(
        token_id=token_id,
        revoked=True,
        message="Capability token revoked successfully",
    )


@router.get("/authority-matrix", response_model=AuthorityMatrixResponse)
def get_authority_matrix() -> AuthorityMatrixResponse:
    """
    Return the complete 5-Tier Human-AI Authority Matrix.
    """
    catalog = AuthorityGateKeeper.get_authority_catalog()
    items = [
        AuthorityMatrixItem(
            action_name=action,
            tier=data["tier"],
            description=data["description"],
            allowed_roles=data["allowed_roles"],
            requires_dual_approval=data["requires_dual_approval"],
        )
        for action, data in catalog.items()
    ]
    return AuthorityMatrixResponse(actions=items, total_actions=len(items))
