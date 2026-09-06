"""
tests/test_split_ticketing.py — Tests for Split-Ticketing Arbitrage Analyzer.
"""

from src.distribution.split_ticketing import FlightFareSegment, SplitTicketingAnalyzer


def test_split_ticketing_arbitrage_discovery():
    """Verify split ticketing identifies cross-airline savings and flags self-transfer risk."""
    outbound = [
        FlightFareSegment(carrier_code="BA", flight_number="BA178", origin_iata="JFK", destination_iata="LHR", fare_usd=380.0, fare_basis_code="OLN0", ticket_type="outbound"),
        FlightFareSegment(carrier_code="VS", flight_number="VS004", origin_iata="JFK", destination_iata="LHR", fare_usd=450.0, fare_basis_code="RLN0", ticket_type="outbound"),
    ]
    inbound = [
        FlightFareSegment(carrier_code="AF", flight_number="AF022", origin_iata="LHR", destination_iata="JFK", fare_usd=390.0, fare_basis_code="TLN0", ticket_type="return"),
        FlightFareSegment(carrier_code="BA", flight_number="BA179", origin_iata="LHR", destination_iata="JFK", fare_usd=550.0, fare_basis_code="YLN0", ticket_type="return"),
    ]

    analysis = SplitTicketingAnalyzer.evaluate_arbitrage(
        origin_iata="JFK",
        destination_iata="LHR",
        unified_roundtrip_fare_usd=1050.0,
        outbound_options=outbound,
        return_options=inbound,
    )

    assert analysis.total_split_fare_usd == 770.0  # 380 + 390
    assert analysis.savings_usd == 280.0  # 1050 - 770
    assert analysis.is_arbitrage_profitable is True
    assert analysis.self_transfer_risk_warning is True  # BA outbound + AF inbound
