"""Reality-tier contract tests for deterministic GDS/distribution routes."""

from spine_api.routers.distribution import (
    AirShoppingRequest,
    Cat35MarkupRequest,
    OrderCreateRequest,
    create_ndc_order,
    evaluate_cat35_markup,
    request_ndc_air_shopping,
)
from spine_api.routers.gds_sandbox import (
    GDSBookRequest,
    GDSSearchRequest,
    book_gds_order,
    search_gds_offers,
)
from src.distribution.sandbox_models import GDSProvider


def assert_preview_envelope(response: dict) -> None:
    assert response["status"] in {"PREVIEW_ONLY", "COMPUTED_PREVIEW"}
    reality = response["reality"]
    assert reality["reality_tier"] == "deterministic_preview"
    assert reality["provider_connected"] is False
    assert reality["external_reference"] is None
    assert reality["effects"] == []


def test_gds_search_is_explicit_preview_without_provider_effects() -> None:
    response = search_gds_offers(
        GDSSearchRequest(
            provider=GDSProvider.AMADEUS,
            origin_iata="JFK",
            destination_iata="LHR",
        )
    )

    assert_preview_envelope(response)
    assert response["offers_count"] == 2
    assert all(offer["provider"] == "amadeus" for offer in response["flight_offers"])


def test_gds_book_does_not_expose_synthetic_ticket_or_charge() -> None:
    response = book_gds_order(
        GDSBookRequest(provider=GDSProvider.SABRE, offer_id="SBR-BFM-TEST")
    )

    assert_preview_envelope(response)
    booking = response["booking_result"]
    assert booking["status"] == "PREVIEW_ONLY"
    assert booking["booking_reference"] is None
    assert booking["pnr_locator"] is None
    assert booking["e_ticket_number"] is None
    assert booking["total_charged_usd"] is None
    assert booking["provider_confirmation"] is None


def test_ndc_air_shopping_is_request_preview() -> None:
    response = request_ndc_air_shopping(
        AirShoppingRequest(
            origin="JFK",
            destination="LHR",
            departure_date="2026-10-15",
        )
    )

    assert_preview_envelope(response)
    assert response["ndc_payload"]["AirShoppingRQ"]["Document"]["ReferenceVersion"] == "21.3"


def test_ndc_order_preview_cannot_claim_confirmation_or_pnr() -> None:
    response = create_ndc_order(
        OrderCreateRequest(
            offer_id="OFFER-TEST",
            airline_code="BA",
            passengers=["Sample Traveler"],
            segments=[{"origin": "JFK", "destination": "LHR"}],
            total_amount=1000.0,
        )
    )

    assert_preview_envelope(response)
    order = response["order"]
    assert order["status"] == "PREVIEW_ONLY"
    assert order["order_id"] is None
    assert order["pnr_reference"] is None
    assert order["provider_confirmation"] is None


def test_fare_evaluation_is_computed_preview() -> None:
    response = evaluate_cat35_markup(
        Cat35MarkupRequest(net_fare=1000.0, agency_markup_percent=10.0)
    )

    assert_preview_envelope(response)
    assert response["cat35_evaluation"]
