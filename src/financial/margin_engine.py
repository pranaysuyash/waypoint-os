"""
src/financial/margin_engine.py — Dynamic Wholesale Margin & Financial Engineering Engine.

Calculates:
- Net wholesale cost to Gross client quote pricing.
- Tiered agency commission markups (percentage and fixed per pax).
- Credit card processing fee pass-through / absorption.
- Multi-currency Foreign Exchange (FX) volatility hedging buffers.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional


@dataclass(slots=True)
class PricingBreakdown:
    net_cost_usd: float
    agency_markup_usd: float
    agency_markup_percent: float
    credit_card_surcharge_usd: float
    fx_hedging_buffer_usd: float
    gross_quoted_price_usd: float
    effective_margin_percent: float
    currency: str = "USD"
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class DynamicMarginEngine:
    """Computes transparent wholesale-to-retail pricing structures."""

    # Default payment card processing rate (Stripe standard: 2.9% + $0.30)
    CC_VARIABLE_RATE = 0.029
    CC_FIXED_USD = 0.30

    # Default FX volatility buffer for non-USD supplier contracts
    DEFAULT_FX_BUFFER_PCT = 0.015  # 1.5%

    @classmethod
    def calculate_quote_pricing(
        cls,
        net_supplier_cost_usd: float,
        target_markup_pct: float = 0.15,
        target_fixed_fee_usd: float = 0.0,
        absorb_cc_fee: bool = True,
        is_foreign_currency_supplier: bool = False,
    ) -> PricingBreakdown:
        if net_supplier_cost_usd < 0:
            raise ValueError("Net supplier cost cannot be negative.")

        # 1. Calculate base markup
        base_markup = (net_supplier_cost_usd * target_markup_pct) + target_fixed_fee_usd

        # 2. Calculate FX hedging buffer if foreign supplier contract
        fx_buffer = (net_supplier_cost_usd * cls.DEFAULT_FX_BUFFER_PCT) if is_foreign_currency_supplier else 0.0

        # 3. Subtotal before card processing
        subtotal = net_supplier_cost_usd + base_markup + fx_buffer

        # 4. Calculate card processing fee
        if absorb_cc_fee:
            # Agency absorbs: quote is subtotal; fee reduces agency net margin
            cc_fee = (subtotal * cls.CC_VARIABLE_RATE) + cls.CC_FIXED_USD
            gross_price = subtotal
            net_agency_profit = base_markup - cc_fee
        else:
            # Client pays: gross is scaled so payout matches subtotal
            gross_price = (subtotal + cls.CC_FIXED_USD) / (1.0 - cls.CC_VARIABLE_RATE)
            cc_fee = gross_price - subtotal
            net_agency_profit = base_markup

        effective_margin = (net_agency_profit / gross_price * 100.0) if gross_price > 0 else 0.0

        return PricingBreakdown(
            net_cost_usd=round(net_supplier_cost_usd, 2),
            agency_markup_usd=round(base_markup, 2),
            agency_markup_percent=round(target_markup_pct * 100.0, 2),
            credit_card_surcharge_usd=round(cc_fee, 2),
            fx_hedging_buffer_usd=round(fx_buffer, 2),
            gross_quoted_price_usd=round(gross_price, 2),
            effective_margin_percent=round(effective_margin, 2),
            notes="Credit card fee absorbed by agency." if absorb_cc_fee else "Card fee passed through.",
        )
