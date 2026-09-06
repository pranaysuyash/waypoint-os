"""
tests/test_margin_engine.py — Tests for Dynamic Wholesale Margin Engine.
"""

from src.financial.margin_engine import DynamicMarginEngine


def test_dynamic_margin_engine_markup_and_card_absorption():
    """Verify net cost properly calculates 15% markup and card fee absorption."""
    breakdown = DynamicMarginEngine.calculate_quote_pricing(
        net_supplier_cost_usd=5000.0,
        target_markup_pct=0.15,
        absorb_cc_fee=True,
        is_foreign_currency_supplier=False,
    )

    assert breakdown.net_cost_usd == 5000.0
    assert breakdown.agency_markup_usd == 750.0
    assert breakdown.gross_quoted_price_usd == 5750.0
    assert breakdown.credit_card_surcharge_usd > 100.0
    assert breakdown.effective_margin_percent > 10.0


def test_dynamic_margin_engine_foreign_currency_fx_buffer():
    """Verify foreign currency supplier activates 1.5% FX hedging buffer."""
    breakdown = DynamicMarginEngine.calculate_quote_pricing(
        net_supplier_cost_usd=10000.0,
        target_markup_pct=0.20,
        absorb_cc_fee=False,
        is_foreign_currency_supplier=True,
    )

    assert breakdown.fx_hedging_buffer_usd == 150.0
    assert breakdown.gross_quoted_price_usd > 12150.0
