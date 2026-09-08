"""
spine_api/routers/boundaries.py — Scoped capability tokens, trust zone contracts, and Human-AI Authority Matrix.

Grounding doctrine:
- PER-0933 (Boundary Systems Architect): Boundary contracts, cryptographically signed capability tokens.
- PER-0927 (Human-AI Authority Architect): Authority tier validation and multi-role access gates.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from spine_api.contract import (
    AuthorityMatrixItem,
    AuthorityMatrixResponse,
    IssueCapabilityTokenRequest,
    IssueCapabilityTokenResponse,
    RevokeCapabilityTokenResponse,
    VerifyCapabilityTokenResponse,
)
from spine_api.core.auth import get_current_agency_id, get_current_membership
from spine_api.services.authority_approval_service import (
    AuthorityApprovalLedger,
    ApprovalConflict,
    ApprovalNotAuthorized,
)
from src.schemas.boundary_contracts import CapabilityScope
from src.services.boundary_engine import AuthorityGateKeeper, BoundaryEngine

logger = logging.getLogger("spine_api.boundaries")

router = APIRouter(prefix="/api/v1/boundaries", tags=["boundaries"])


# ---------------------------------------------------------------------------
# PA-08: durable dual-control authority approvals
# ---------------------------------------------------------------------------


class RequestAuthorityApprovalBody(BaseModel):
    action: str = Field(..., description="Governance action being ratified, e.g. fulfill_accepted_proposal")
    subject_type: str = Field(..., description="Subject kind, e.g. trip or payout")
    subject_id: str = Field(..., description="Subject identifier the approval applies to")
    amount_usd: Optional[float] = Field(None, description="Dollar amount being authorized, when known")
    reason: Optional[str] = Field(None, max_length=500, description="Why the over-cap action is needed")
    requested_by: Optional[str] = Field(None, description="Requester identity; defaults to the current user")


class ApproveAuthorityApprovalBody(BaseModel):
    reason: Optional[str] = Field(None, max_length=500, description="Denial rationale (deny endpoint only)")


def _approval_error(exc: Exception) -> HTTPException:
    if isinstance(exc, ApprovalNotAuthorized):
        return HTTPException(status_code=403, detail=str(exc))
    if isinstance(exc, ApprovalConflict):
        return HTTPException(status_code=409, detail=str(exc))
    return HTTPException(status_code=404, detail=str(exc))


@router.post("/authority-approvals")
def request_authority_approval(
    body: RequestAuthorityApprovalBody,
    agency_id: str = Depends(get_current_agency_id),
    membership=Depends(get_current_membership),
) -> Dict[str, Any]:
    """Open a dual-control authority approval request (PA-08).

    Created in ``pending_second`` status; two DISTINCT owner/admin approvals
    via ``POST /authority-approvals/{id}/approve`` ratify it. Execution paths
    consult the ratified record via ``AuthorityApprovalLedger.get_approved``.
    """
    try:
        record = AuthorityApprovalLedger.request_approval(
            agency_id=agency_id,
            action=body.action,
            subject_type=body.subject_type,
            subject_id=body.subject_id,
            requested_by=body.requested_by or membership.user_id,
            amount_usd=body.amount_usd,
            reason=body.reason,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return record.to_dict()


@router.get("/authority-approvals")
def list_authority_approvals(
    status: Optional[str] = Query(default=None),
    action: Optional[str] = Query(default=None),
    subject_id: Optional[str] = Query(default=None),
    agency_id: str = Depends(get_current_agency_id),
) -> Dict[str, Any]:
    """List authority approvals for the current agency (operators' queue)."""
    approvals = AuthorityApprovalLedger.list_approvals(
        agency_id=agency_id, action=action, subject_id=subject_id, status=status
    )
    return {"approvals": approvals, "total": len(approvals), "storage_backend": _ledger_backend()}


def _ledger_backend() -> str:
    try:
        from spine_api.services.authority_approval_service import _backend

        return _backend()
    except Exception:  # pragma: no cover - defensive, backend import always succeeds
        return "memory"


@router.get("/authority-approvals/{approval_id}")
def get_authority_approval(
    approval_id: str,
    agency_id: str = Depends(get_current_agency_id),
) -> Dict[str, Any]:
    record = AuthorityApprovalLedger.get_approval(agency_id=agency_id, approval_id=approval_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Approval '{approval_id}' not found.")
    return record


@router.post("/authority-approvals/{approval_id}/approve")
def approve_authority_approval(
    approval_id: str,
    body: ApproveAuthorityApprovalBody,
    agency_id: str = Depends(get_current_agency_id),
    membership=Depends(get_current_membership),
) -> Dict[str, Any]:
    """Record one leg of the dual-control approval (owner/admin roles only).

    First distinct approval fills the first slot; a second DISTINCT owner/admin
    approval ratifies the record. Same-person double approval is a 409.
    """
    try:
        record = AuthorityApprovalLedger.approve(
            agency_id=agency_id,
            approval_id=approval_id,
            approver_user_id=membership.user_id,
            approver_role=membership.role,
        ).to_dict()
    except (ApprovalNotAuthorized, ApprovalConflict) as exc:
        raise _approval_error(exc)
    except ValueError as exc:
        raise _approval_error(exc)
    logger.info(
        "Authority approval %s advanced to '%s' by %s", approval_id, record["status"], membership.user_id
    )
    return record


@router.post("/authority-approvals/{approval_id}/deny")
def deny_authority_approval(
    approval_id: str,
    body: ApproveAuthorityApprovalBody,
    agency_id: str = Depends(get_current_agency_id),
    membership=Depends(get_current_membership),
) -> Dict[str, Any]:
    """Deny a pending authority approval (owner/admin roles only)."""
    try:
        record = AuthorityApprovalLedger.deny(
            agency_id=agency_id,
            approval_id=approval_id,
            approver_user_id=membership.user_id,
            approver_role=membership.role,
            reason=body.reason,
        )
    except (ApprovalNotAuthorized, ApprovalConflict) as exc:
        raise _approval_error(exc)
    except ValueError as exc:
        raise _approval_error(exc)
    return record.to_dict()


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
