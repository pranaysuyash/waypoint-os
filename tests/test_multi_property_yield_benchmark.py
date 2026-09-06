"""Tests for Multi-Property Multi-Season Yield Benchmark Engine."""

from datetime import datetime, timezone, timedelta
from src.yield_arbitrage.multi_property_benchmark import (
    MultiPropertyYieldBenchmark,
    PropertyRateOption,
)


def test_property_rate_disparity_analysis():
    now = datetime.now(timezone.utc)
    rates = [
        PropertyRateOption("Sabre GDS", "flexible", 5000.0, False, now + timedelta(days=14), 1200.0),
        PropertyRateOption("Hotelbeds", "wholesale_net", 4200.0, True, now + timedelta(days=10), 900.0),
    ]

    score = MultiPropertyYieldBenchmark.analyze_property_disparities(
        property_name="The Ritz-Carlton Paris",
        nights=4,
        guests=2,
        rates=rates,
    )

    # 4 nights * 2 guests * $45 = $360 breakfast value
    # $5000 - $4200 = $800 gross savings
    # Total net margin = $800 + $360 = $1160
    assert score.optimal_supplier == "Hotelbeds"
    assert score.gross_savings_usd == 800.0
    assert score.breakfast_value_adjustment_usd == 360.0
    assert score.net_captured_margin_usd == 1160.0
    assert score.is_safe_to_reticket is True


def test_100_property_benchmark_simulation():
    res = MultiPropertyYieldBenchmark.run_100_property_benchmark()
    assert res["status"] == "success"
    assert res["properties_analyzed_count"] >= 4
    assert res["total_captured_margin_usd"] > 0
    assert res["average_margin_lift_percent"] > 10.0
