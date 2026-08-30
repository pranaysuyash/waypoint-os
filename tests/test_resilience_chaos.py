"""
tests/test_resilience_chaos.py — Chaos fault injection and multi-supplier failover tests.
"""

from src.services.resilience_engine import ResilienceEngine


def test_multi_supplier_failover_succession():
    """Verify automatic failover from failing primary supplier to healthy secondary supplier."""
    engine = ResilienceEngine()
    chain = ["amadeus", "sabre", "duffel"]

    # Mock operation: amadeus fails, sabre succeeds
    def mock_flight_search(supplier_name: str) -> dict:
        if supplier_name == "amadeus":
            raise ConnectionError("Amadeus NDC HTTP 503 Gateway Timeout")
        return {"supplier": supplier_name, "flight": "BA112", "price_usd": 850.0}

    fallback = {"supplier": "static_cache", "flight": "BA112", "price_usd": 900.0}

    result, winning_supplier, was_fallback = engine.execute_with_supplier_failover(
        supplier_chain=chain,
        operation=mock_flight_search,
        fallback_data=fallback,
    )

    assert result["price_usd"] == 850.0
    assert winning_supplier == "sabre"
    assert was_fallback is False


def test_multi_supplier_all_fail_to_static_fallback():
    """Verify that when all suppliers in chain fail, engine serves static fallback with flag."""
    engine = ResilienceEngine()
    chain = ["amadeus", "sabre"]

    def mock_all_fail(supplier_name: str):
        raise TimeoutError(f"Supplier {supplier_name} timed out")

    fallback = {"supplier": "static_cache", "flight": "AF22", "price_usd": 1200.0}

    result, winning_supplier, was_fallback = engine.execute_with_supplier_failover(
        supplier_chain=chain,
        operation=mock_all_fail,
        fallback_data=fallback,
    )

    assert result["flight"] == "AF22"
    assert winning_supplier == "fallback_cache"
    assert was_fallback is True
