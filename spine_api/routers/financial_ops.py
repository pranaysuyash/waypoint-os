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
from spine_api.core.auth import get_current_agency_id
from spine_api.core.reality_tier import RealityTier, TierMetadata
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
    """Body for mandate registration. ``consent_artifact_ref`` is REQUIRED and
    must reference the durable consent artifact (e-sign acceptance token /
    audit event) — a mandate without one is refused (F-04 anti-decoration)."""

    trip_id: str = Field(..., min_length=1)
    customer_id: str = Field(..., min_length=1)
    max_authorized_cents: int = Field(..., gt=0)
    purpose: str = Field(..., description="INITIAL_DEPOSIT | SPLIT_INSTALLMENT | FINAL_BALANCE | SUPPLIER_INCIDENTAL_HOLD")
    consent_text: str = Field(..., min_length=1, description="Only its SHA-256 digest is stored.")
    consent_artifact_ref: str = Field(..., min_length=1)
    currency: str = "USD"
    customer_name: str = ""
    customer_email: str = ""
    client_ip_address: str = ""
    validity_days: int = Field(60, ge=1, le=365)


class RevokeMandateRequest(BaseModel):
    reason: str = Field(..., min_length=1, max_length=500)


@router.post("/payment-mandates")
def register_payment_mandate(
    request: RegisterMandateRequest,
    agency_id: str = Depends(get_current_agency_id),
) -> Dict[str, Any]:
    """Record a payment authorization mandate for a trip (tenant-scoped)."""
    try:
        record = PaymentMandateLedger.register_mandate(
            agency_id=agency_id,
            trip_id=request.trip_id,
            customer_id=request.customer_id,
            max_authorized_cents=request.max_authorized_cents,
            purpose=request.purpose,
            consent_text=request.consent_text,
            consent_artifact_ref=request.consent_artifact_ref,
            currency=request.currency,
            customer_name=request.customer_name,
            customer_email=request.customer_email,
            client_ip_address=request.client_ip_address,
            validity_days=request.validity_days,
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
) -> Dict[str, Any]:
    """CAS revocation: only an ACTIVE mandate can be revoked (idempotent 409 otherwise)."""
    revoked = PaymentMandateLedger.revoke_mandate(
        agency_id=agency_id, mandate_id=mandate_id, reason=request.reason
    )
    if not revoked:
        raise HTTPException(
            status_code=409,
            detail="Mandate not found, not owned by this agency, or not in ACTIVE status.",
        )
    return {"ok": True, "mandate_id": mandate_id, "status": "REVOKED", "reality_tier": RealityTier.REAL.value}
