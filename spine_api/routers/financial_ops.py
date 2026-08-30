"""
spine_api/routers/financial_ops.py — Multi-currency conversions, FX slippage buffers, and fee netting router.

Grounding doctrine:
- Travel Financial Systems Architect: Deterministic multi-currency pricing and interchange protection.
"""

from __future__ import annotations

import logging
from fastapi import APIRouter

from spine_api.contract import FXConversionRequest, FXConversionResponse
from src.fees.currency import CurrencyService

logger = logging.getLogger("spine_api.financial_ops")

router = APIRouter(prefix="/api/v1/financial-ops", tags=["financial_ops"])


@router.post("/convert-currency", response_model=FXConversionResponse)
def convert_currency_endpoint(request: FXConversionRequest) -> FXConversionResponse:
    """
    Calculate foreign currency conversion with volatility slippage buffer and payment gateway interchange fees.
    """
    res = CurrencyService.convert_currency(
        amount_in_target=request.amount_in_target,
        target_currency=request.target_currency,
        agency_base_currency=request.agency_base_currency,
        custom_slippage_buffer_pct=request.custom_slippage_buffer_pct,
    )

    return FXConversionResponse(
        base_currency=res.base_currency,
        target_currency=res.target_currency,
        mid_market_rate=res.mid_market_rate,
        slippage_buffer_pct=res.slippage_buffer_pct,
        effective_rate=res.effective_rate,
        base_amount=res.base_amount,
        target_amount=res.target_amount,
        slippage_cost_base=res.slippage_cost_base,
        payment_gateway_fee_base=res.payment_gateway_fee_base,
        total_cost_in_base_currency=res.total_cost_in_base_currency,
    )
