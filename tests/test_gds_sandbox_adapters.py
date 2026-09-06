"""
Unit & Integration Tests for GDS Sandbox Adapters (Milestone 3).
"""

from src.distribution.amadeus_sandbox_adapter import AmadeusSandboxAdapter
from src.distribution.sabre_sandbox_adapter import SabreSandboxAdapter
from src.distribution.sandbox_models import GDSProvider


def test_amadeus_sandbox_search_and_booking():
    offers = AmadeusSandboxAdapter.search_flight_offers(
        origin_iata="JFK",
        destination_iata="LHR",
        departure_date="2026-10-15",
    )

    assert len(offers) >= 2
    first_offer = offers[0]
    assert first_offer.provider == GDSProvider.AMADEUS
    assert first_offer.total_price_usd > 0

    booking = AmadeusSandboxAdapter.create_flight_order(
        offer_id=first_offer.offer_id,
        traveler_name="Alex Morgan",
    )

    assert booking.provider == GDSProvider.AMADEUS
    assert booking.pnr_locator is not None
    assert booking.e_ticket_number.startswith("057-")
    assert booking.status == "TICKETED_CONFIRMED"


def test_sabre_sandbox_bfm_and_booking():
    offers = SabreSandboxAdapter.bargain_finder_max(
        origin_iata="JFK",
        destination_iata="LHR",
        departure_date="2026-10-15",
    )

    assert len(offers) >= 2
    first_offer = offers[0]
    assert first_offer.provider == GDSProvider.SABRE
    assert first_offer.total_price_usd > 0

    booking = SabreSandboxAdapter.create_passenger_name_record(
        offer_id=first_offer.offer_id,
        traveler_name="Alex Morgan",
    )

    assert booking.provider == GDSProvider.SABRE
    assert booking.pnr_locator is not None
    assert booking.e_ticket_number.startswith("001-")
    assert booking.status == "TICKETED_CONFIRMED"
