"""
spine_api/routers/financial_ops.py — deterministic FX preview + payment mandate ledger.

FX conversion is a local arithmetic preview: no market-data or payment provider
is connected, and the API must not present it as a live quote or a financial
effect.

The payment-mandate endpoints (F-04) are different in kind: they are durable
consent-artifact RECORDS (who authorized money movement, for how much, until
when). The record-keeping itself is real; the downstream execution those
mandates authorize is still sim-tier (see booking_fulfillment's reality tier).
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from spine_api.contract import FXConversionRequest
from spine_api.core.auth import get_current_agency_id, get_current_user
from spine_api.core.reality_tier import RealityTier, TierMetadata
from spine_api.core.startup_assertions import auth_bypass_enabled
from spine_api.services.payment_mandate_service import PaymentMandateLedger
from src.fees.currency import CurrencyService

logger = logging.getLogger("spine_api.financial_ops")

router = APIRouter(prefix="/api/v1/financial-ops", tags=["financial_ops"])

_FINANCIAL_PREVIEW_MISSING = [
    "authenticated market-data provider",
    "quote freshness and expiry policy",
    "authorized payment or treasury provider",
    "external confirmation and reconciliation",
]


def _preview_metadata(feature_name: str) -> Dict[str, Any]:
    """Return canonical provenance for local financial arithmetic."""
    metadata = TierMetadata.for_response(
        RealityTier.DETERMINISTIC_PREVIEW,
        feature_name,
        computation_method="local deterministic conversion and fee arithmetic; no provider call or financial write",
        missing_for_upgrade=_FINANCIAL_PREVIEW_MISSING,
    )
    metadata.update(
        {
            "source": "local_deterministic_preview",
            "simulation": True,
            "provider_connected": False,
            "external_reference": None,
            "external_action": False,
            "operational_write": False,
            "effects": [],
        }
    )
    return metadata


@router.post("/convert-currency")
def convert_currency_endpoint(request: FXConversionRequest) -> Dict[str, Any]:
    """Calculate a deterministic conversion preview; no quote is issued."""
    res = CurrencyService.convert_currency(
        amount_in_target=request.amount_in_target,
        target_currency=request.target_currency,
        agency_base_currency=request.agency_base_currency,
        custom_slippage_buffer_pct=request.custom_slippage_buffer_pct,
    )

    return {
        "base_currency": res.base_currency,
        "target_currency": res.target_currency,
        "mid_market_rate": res.mid_market_rate,
        "slippage_buffer_pct": res.slippage_buffer_pct,
        "effective_rate": res.effective_rate,
        "base_amount": res.base_amount,
        "target_amount": res.target_amount,
        "slippage_cost_base": res.slippage_cost_base,
        "payment_gateway_fee_base": res.payment_gateway_fee_base,
        "total_cost_in_base_currency": res.total_cost_in_base_currency,
        "status": "COMPUTED_PREVIEW",
        "reality_tier": RealityTier.DETERMINISTIC_PREVIEW.value,
        "provider_connected": False,
        "external_reference": None,
        "effects": [],
        "metadata": _preview_metadata("financial_currency_conversion"),
    }


# ---------------------------------------------------------------------------
# Payment mandate ledger (F-04) — durable consent-artifact records
# ---------------------------------------------------------------------------


class RegisterMandateRequest(BaseModel):
    """Body for mandate registration. A durable evidence artifact is REQUIRED
    (``consent_artifact_ref`` or its FND-0221 alias ``evidence_ref``) and must
    reference the consent artifact (e-sign acceptance token / proposal id /
    approval event) — a mandate without one is refused (F-04 anti-decoration).

    FND-0221: ``scope`` is deposit | balance | fee | payout (default derived
    from ``purpose``); ``payer_ref`` is the authenticated principal who
    granted the mandate (bound from the JWT at this router; a client-supplied
    value is honored only under the repo's test auth-bypass posture, mirroring
    the sanctioned X-Agency-ID test escape); ``idempotency_key`` makes
    granting idempotent — the same key returns the SAME mandate.
    """

    trip_id: str = Field(..., min_length=1)
    customer_id: str = Field(..., min_length=1)
    max_authorized_cents: int = Field(..., gt=0)
    purpose: str = Field(
        "",
        description=(
            "INITIAL_DEPOSIT | SPLIT_INSTALLMENT | FINAL_BALANCE | SUPPLIER_INCIDENTAL_HOLD. "
            "Optional when scope is given (scope-driven mandates, e.g. payout, are purpose-free)."
        ),
    )
    consent_text: str = Field(..., min_length=1, description="Only its SHA-256 digest is stored.")
    consent_artifact_ref: Optional[str] = Field(
        None, description="Durable consent artifact (alias: evidence_ref). One of the two is required."
    )
    currency: str = "USD"
    customer_name: str = ""
    customer_email: str = ""
    client_ip_address: str = ""
    validity_days: int = Field(60, ge=1, le=365)
    # FND-0221 payer-authorization shape.
    scope: Optional[str] = Field(
        None, description="deposit | balance | fee | payout. Default: derived from purpose."
    )
    evidence_ref: Optional[str] = Field(
        None, description="Alias for consent_artifact_ref (proposal id / approval event)."
    )
    payer_ref: Optional[str] = Field(
        None,
        description="Test-only override of the granting principal; production binds it from the JWT.",
    )
    granted_by: Optional[str] = None
    idempotency_key: Optional[str] = Field(
        None, description="Grant idempotency: same key returns the same mandate."
    )


class RevokeMandateRequest(BaseModel):
    reason: str = Field(..., min_length=1, max_length=500)


def _bound_payer_ref(user: Any) -> str:
    """JWT-bound granting principal, matching the fulfillment router's
    ``user:<email>`` money-principal binding (ADR-008)."""
    return f"user:{getattr(user, 'email', None) or getattr(user, 'id', 'unknown')}"


@router.post("/payment-mandates")
def register_payment_mandate(
    request: RegisterMandateRequest,
    agency_id: str = Depends(get_current_agency_id),
    user: Any = Depends(get_current_user),
) -> Dict[str, Any]:
    """Record a payment authorization mandate for a trip (tenant-scoped)."""
    payer_ref = _bound_payer_ref(user)
    if request.payer_ref and auth_bypass_enabled():
        # Test posture only (FND-0259 hardening: bypass-gated only, no
        # standalone PYTEST env escape): production always binds the JWT
        # principal.
        payer_ref = request.payer_ref
    try:
        record = PaymentMandateLedger.register_mandate(
            agency_id=agency_id,
            trip_id=request.trip_id,
            customer_id=request.customer_id,
            max_authorized_cents=request.max_authorized_cents,
            purpose=request.purpose,
            consent_text=request.consent_text,
            consent_artifact_ref=request.consent_artifact_ref or "",
            currency=request.currency,
            customer_name=request.customer_name,
            customer_email=request.customer_email,
            client_ip_address=request.client_ip_address,
            validity_days=request.validity_days,
            scope=request.scope or "",
            payer_ref=payer_ref,
            granted_by=request.granted_by or "",
            idempotency_key=request.idempotency_key,
            evidence_ref=request.evidence_ref or "",
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {
        "ok": True,
        "mandate": record.to_dict(),
        "reality_tier": RealityTier.REAL.value,
        "note": (
            "Durable consent-artifact record. Execution authorized against this "
            "mandate is currently sim-tier (see fulfillment reality tier)."
        ),
    }


@router.get("/payment-mandates")
def list_payment_mandates(
    trip_id: Optional[str] = None,
    status: Optional[str] = None,
    agency_id: str = Depends(get_current_agency_id),
) -> Dict[str, Any]:
    """List mandates for the caller's agency (optionally filtered)."""
    items = PaymentMandateLedger.list_mandates(agency_id=agency_id, trip_id=trip_id, status=status)
    return {
        "ok": True,
        "items": items,
        "total": len(items),
        "reality_tier": RealityTier.REAL.value,
    }


@router.get("/payment-mandates/{mandate_id}")
def get_payment_mandate(
    mandate_id: str,
    agency_id: str = Depends(get_current_agency_id),
) -> Dict[str, Any]:
    mandate = PaymentMandateLedger.get_mandate(agency_id=agency_id, mandate_id=mandate_id)
    if mandate is None:
        raise HTTPException(status_code=404, detail="Payment mandate not found.")
    return {"ok": True, "mandate": mandate, "reality_tier": RealityTier.REAL.value}


@router.post("/payment-mandates/{mandate_id}/revoke")
def revoke_payment_mandate(
    mandate_id: str,
    request: RevokeMandateRequest,
    agency_id: str = Depends(get_current_agency_id),
    user: Any = Depends(get_current_user),
) -> Dict[str, Any]:
    """CAS revocation: only an ACTIVE mandate can be revoked (idempotent 409 otherwise).

    FND-0221: the revoking principal and timestamp are recorded with the
    mandate so the authorization chain stays auditable end to end.
    """
    revoked_by = _bound_payer_ref(user)
    revoked = PaymentMandateLedger.revoke_mandate(
        agency_id=agency_id, mandate_id=mandate_id, reason=request.reason, revoked_by=revoked_by
    )
    if not revoked:
        raise HTTPException(
            status_code=409,
            detail="Mandate not found, not owned by this agency, or not in ACTIVE status.",
        )
    mandate = PaymentMandateLedger.get_mandate(agency_id=agency_id, mandate_id=mandate_id) or {}
    return {
        "ok": True,
        "mandate_id": mandate_id,
        "status": "REVOKED",
        "mandate_state": mandate.get("mandate_state", "revoked"),
        "revoked_at": mandate.get("revoked_at"),
        "revoked_by": mandate.get("revoked_by", revoked_by),
        "reality_tier": RealityTier.REAL.value,
    }
