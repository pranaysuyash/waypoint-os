"""
Private Aviation & Empty-Leg Arbitrage Tests (PER-AV-CHARTER).
"""

from src.charter.aviation_engine import PrivateAviationEngine
from src.charter.models import JetCategory


def test_private_charter_quote_calculation():
    quote = PrivateAviationEngine.calculate_charter_quote(
        origin_icao="KTEB",
        destination_icao="KOPF",
        passengers_count=4,
        distance_nm=1100,
    )

    assert quote.origin_icao == "KTEB"
    assert quote.destination_icao == "KOPF"
    assert quote.flight_time_hours > 0
    assert quote.standard_cost_usd > 0
    assert quote.runway_origin_feasible is True
    assert quote.runway_dest_feasible is True
    # Test Empty-Leg matching for TEB -> OPF
    assert quote.empty_leg_match is not None
    assert quote.empty_leg_match.discount_percent > 60.0
    assert quote.effective_cost_usd < quote.standard_cost_usd
    assert quote.savings_usd > 0


def test_empty_legs_catalog():
    legs = PrivateAviationEngine.list_available_empty_legs()
    assert len(legs) >= 2
    assert legs[0].category in [JetCategory.SUPER_MIDSIZE, JetCategory.LIGHT_JET]


def test_mountain_altiport_aspen_hot_and_high_penalties():
    """Verify Aspen KASE (7,820 ft MSL) imposes density altitude runway increase and payload reduction."""
    # Phenom 300E (3,209 ft sea-level baseline) into Aspen KASE
    quote = PrivateAviationEngine.calculate_charter_quote(
        origin_icao="KTEB",
        destination_icao="KASE",
        passengers_count=4,
        distance_nm=1600,
    )

    assert quote.destination_icao == "KASE"
    assert quote.is_hot_and_high_restricted is True
    assert quote.dest_runway_length_ft == 8006
    # Effective required runway must be substantially higher than sea-level baseline (3,209 ft)
    assert quote.dest_effective_runway_required_ft > 5000
    assert quote.payload_reduction_percent == 25.0
    assert quote.runway_dest_feasible is True
    assert any("Mountain Airfield Penalty" in w for w in quote.performance_warnings)


def test_mountain_altiport_samedan_and_infeasible_runway():
    """Verify Samedan LSZS (5,600 ft MSL, 5,905 ft runway) and Courchevel LFLJ runway constraints."""
    # Ultra long range jet (G650ER, 5,858 ft sea-level requirement) attempting Samedan LSZS (5,905 ft physical runway)
    # Elevation (+56% penalty) pushes effective required runway to ~9,000+ ft, making it infeasible.
    quote = PrivateAviationEngine.calculate_charter_quote(
        origin_icao="OMDW",
        destination_icao="LSZS",
        passengers_count=12,  # Selects G650ER
        distance_nm=2600,
    )

    assert quote.destination_icao == "LSZS"
    assert quote.dest_runway_length_ft == 5905
    assert quote.dest_effective_runway_required_ft > 8000
    assert quote.runway_dest_feasible is False
    assert any("Infeasible Runway Length" in w for w in quote.performance_warnings)
