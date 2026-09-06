"""
tests/test_irrops_healer.py — Tests for Autonomous IRROPS Disruption Healer & EU261 Compensation.
"""

from src.logistics.irrops_healer import DisruptionEvent, IRROPSHealerEngine


def test_irrops_healer_eu261_compensation_eligible():
    """Verify long delay on transatlantic route qualifies for €600 EU261 compensation."""
    event = DisruptionEvent(
        flight_number="BA178",
        carrier_code="BA",
        origin_iata="JFK",
        destination_iata="LHR",
        scheduled_departure_iso="2026-09-10T08:00:00Z",
        disruption_type="delay",
        delay_minutes=240,  # 4 hours
        reason="technical",
    )

    plan = IRROPSHealerEngine.heal_disruption(event)
    assert plan.compensation.eligible is True
    assert plan.compensation.amount_eur == 600.0
    assert plan.hotel_accommodation_required is False
    assert plan.meal_voucher_amount_usd == 50.0
    assert len(plan.alternate_options) >= 1
    assert plan.alternate_options[0].mct_safe is True


def test_irrops_healer_weather_exemption():
    """Verify weather disruption exempts airline from cash compensation while providing care."""
    event = DisruptionEvent(
        flight_number="AF022",
        carrier_code="AF",
        origin_iata="CDG",
        destination_iata="JFK",
        scheduled_departure_iso="2026-09-10T10:00:00Z",
        disruption_type="cancellation",
        delay_minutes=480,
        reason="weather",
    )

    plan = IRROPSHealerEngine.heal_disruption(event)
    assert plan.compensation.eligible is False
    assert plan.compensation.amount_eur == 0.0
    assert "extraordinary circumstance" in plan.compensation.reason
    assert plan.hotel_accommodation_required is True
