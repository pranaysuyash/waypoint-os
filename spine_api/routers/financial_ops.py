"""
spine_api/routers/financial_ops.py — deterministic FX calculation preview.

No market-data or payment provider is connected in this local implementation.
The arithmetic remains useful for planning, but the API must not present it as
a live quote or a financial effect.
"""

from __future__ import annotations

import logging
from typing import Any, Dict
from fastapi import APIRouter

from spine_api.contract import FXConversionRequest
from spine_api.core.reality_tier import RealityTier, TierMetadata
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
