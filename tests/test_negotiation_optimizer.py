"""
Negotiation & Dynamic Margin Engine Tests (PER-950888, PER-20690, PER-0482).
"""

from src.negotiation.bargaining_engine import BargainingEngine
from src.negotiation.margin_optimizer import MarginOptimizer
from src.negotiation.fee_waiver_bot import FeeWaiverBot
from src.negotiation.models import NegotiationStatus


def test_bargaining_session_start_and_counter():
    session = BargainingEngine.start_session(
        trip_id="TRIP-9901",
        supplier_id="SUP-DMC-BALI",
        supplier_name="Bali Luxury Destination Services",
        initial_quote=10_000.0,
        target_budget=8_800.0,
        agency_tier_name="PLATINUM",
    )

    assert session.status == NegotiationStatus.INITIATED
    assert session.initial_quote == 10_000.0
    assert session.current_offered_quote == 9_200.0  # 8% volume discount ask
    assert len(session.concessions) == 2

    # Supplier counters with 9,300 (Within 3% tolerance of target gap)
    res = BargainingEngine.evaluate_supplier_counter(
        session=session,
        supplier_counter_quote=9_050.0,
    )
    assert res["decision"] == "ACCEPT"
    assert session.status == NegotiationStatus.ACCEPTED


def test_dynamic_margin_optimizer():
    # Urgent last minute quote (<3 days lead time)
    urgent_result = MarginOptimizer.calculate_optimal_margin(
        net_supplier_cost=3_000.0,
        lead_time_days=2,
        is_peak_season=True,
        customer_price_sensitivity=0.2,  # Luxury / insensitive
    )
    assert urgent_result.urgency_multiplier == 1.35
    assert urgent_result.effective_margin_percent > 16.0  # High margin
    assert urgent_result.optimized_selling_price > 3_500.0

    # Advance early bird sensitive customer (120 days lead time)
    early_bird = MarginOptimizer.calculate_optimal_margin(
        net_supplier_cost=3_000.0,
        lead_time_days=120,
        is_peak_season=False,
        customer_price_sensitivity=0.9,  # Hyper-sensitive
    )
    assert early_bird.urgency_multiplier == 0.90
    assert early_bird.effective_margin_percent < urgent_result.effective_margin_percent


def test_fee_waiver_bot_generation():
    waiver = FeeWaiverBot.generate_waiver_request(
        booking_ref="BK-88491",
        supplier_name="Marriott International Trade Desk",
        original_penalty_amount=450.0,
        reason="Family medical emergency with doctor letter",
        supplier_fault_incidents=["2026-06-15: 3-hour HVAC failure on Res #49102"],
        agency_annual_volume=600_000.0,
    )

    assert waiver["penalty_amount"] == 450.0
    assert waiver["expected_waiver_probability"] >= 0.80
    assert "HVAC failure" in waiver["waiver_letter"]
    assert "USD 600,000" in waiver["waiver_letter"]
