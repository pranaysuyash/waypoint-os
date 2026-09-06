"""
Multi-Supplier Rate Parity & Re-Ticketing Arbitrage Tests (PER-YLD-ARB).
"""

from src.yield_arbitrage.rate_parity_engine import MultiSupplierRateParityEngine


def test_rate_parity_arbitrage_detection():
    opps = MultiSupplierRateParityEngine.scan_for_arbitrage(
        booking_id="BKG-PARIS-001",
        hotel_name="The Ritz-Carlton Paris",
        current_cost_usd=2250.0,
        current_supplier="Sabre GDS",
    )

    assert len(opps) >= 1
    best_opp = opps[0]
    assert best_opp.current_supplier == "Sabre GDS"
    assert best_opp.target_cost_usd < 2250.0
    assert best_opp.gross_savings_usd > 0
    assert best_opp.spread_percent > 0
    assert best_opp.can_auto_reticket is True


def test_auto_reticketing_execution():
    result = MultiSupplierRateParityEngine.execute_auto_reticketing(
        booking_id="BKG-PARIS-001",
        target_opportunity_id="ARB-001",
        supplier_from="Sabre GDS",
        supplier_to="Hotelbeds",
        savings_captured=405.0,
    )

    assert result.booking_id == "BKG-PARIS-001"
    assert result.supplier_from == "Sabre GDS"
    assert result.supplier_to == "Hotelbeds"
    assert result.net_savings_captured_usd == 405.0
    assert result.status == "SUCCESS_CONFIRMED"
