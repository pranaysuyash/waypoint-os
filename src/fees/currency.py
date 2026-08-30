"""
src/fees/currency.py — Dynamic FX slippage buffers, payment gateway fees, and multi-currency pricing.

Grounding doctrine:
- Travel Financial Systems Architect: Protect agency margins against FX volatility and credit card interchange fees.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class FXConversionResult:
    """Calculated conversion between base agency currency and target supplier currency."""
    base_currency: str
    target_currency: str
    mid_market_rate: float
    slippage_buffer_pct: float       # e.g. 0.02 (2.0%)
    effective_rate: float            # mid_market_rate * (1 + slippage_buffer_pct)
    base_amount: float
    target_amount: float
    slippage_cost_base: float
    payment_gateway_fee_base: float  # e.g. Stripe 2.9% + $0.30
    total_cost_in_base_currency: float


class CurrencyService:
    """Calculates multi-currency conversions with deterministic volatility buffers."""

    # Reference benchmark mid-market rates against USD (updated periodically or via live feeds)
    BENCHMARK_RATES_TO_USD: dict[str, float] = {
        "USD": 1.0,
        "EUR": 1.08,
        "GBP": 1.28,
        "JPY": 0.0066,
        "AUD": 0.65,
        "CAD": 0.74,
        "CHF": 1.12,
        "SGD": 0.75,
        "AED": 0.272,
        "INR": 0.012,
    }

    @classmethod
    def convert_currency(
        cls,
        amount_in_target: float,
        target_currency: str,
        agency_base_currency: str = "USD",
        custom_slippage_buffer_pct: float = 0.02,
        gateway_fee_pct: float = 0.029,
        gateway_fixed_fee: float = 0.30,
    ) -> FXConversionResult:
        """
        Convert a foreign supplier amount into the agency base currency, adding volatility buffers and processing fees.
        """
        t_curr = target_currency.upper()
        b_curr = agency_base_currency.upper()

        rate_target_to_usd = cls.BENCHMARK_RATES_TO_USD.get(t_curr, 1.0)
        rate_base_to_usd = cls.BENCHMARK_RATES_TO_USD.get(b_curr, 1.0)

        # 1 Target Currency = X Base Currency
        mid_rate = rate_target_to_usd / rate_base_to_usd
        effective_rate = mid_rate * (1.0 + custom_slippage_buffer_pct)

        base_unadjusted = amount_in_target * mid_rate
        base_with_buffer = amount_in_target * effective_rate
        slippage_cost = base_with_buffer - base_unadjusted

        gateway_fee = (base_with_buffer * gateway_fee_pct) + gateway_fixed_fee
        total_cost = base_with_buffer + gateway_fee

        return FXConversionResult(
            base_currency=b_curr,
            target_currency=t_curr,
            mid_market_rate=round(mid_rate, 6),
            slippage_buffer_pct=custom_slippage_buffer_pct,
            effective_rate=round(effective_rate, 6),
            base_amount=round(base_unadjusted, 2),
            target_amount=round(amount_in_target, 2),
            slippage_cost_base=round(slippage_cost, 2),
            payment_gateway_fee_base=round(gateway_fee, 2),
            total_cost_in_base_currency=round(total_cost, 2),
        )
