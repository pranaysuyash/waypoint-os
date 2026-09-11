"""A2 + A4 consolidation guards (2026-09-11).

A2: statutory compensation math has ONE canonical home
(spine_api.services.passenger_rights_claims); the legacy
src/logistics/irrops_healer.py module stays dead, and the passenger-rights
router delegates instead of carrying its own arithmetic.

A4: the plaintext trip lane and operator payload no longer carry raw VCC ids
or e-ticket numbers — the durable encrypted copy lives in
booking_confirmations (confirmation_service).
"""



# --- A2: canonical calculator contract --------------------------------------


def test_eu261_distance_tiers_and_threshold():
    from spine_api.services.passenger_rights_claims import evaluate_statutory_compensation

    short = evaluate_statutory_compensation("BA123", 1000, 3.0, 2)
    assert short["regulatory_framework"] == "EU261"
    assert short["compensation_per_passenger_eur"] == 250.0

    mid = evaluate_statutory_compensation("BA123", 3000, 5.0, 1)
    assert mid["compensation_per_passenger_eur"] == 400.0

    long_ = evaluate_statutory_compensation("BA123", 5000, 5.0, 1)
    assert long_["compensation_per_passenger_eur"] == 600.0

    below = evaluate_statutory_compensation("BA123", 1000, 2.5, 1)
    assert below["is_eligible"] is False
    assert below["regulatory_framework"] == "NONE"


def test_us_dot_branch_matches_historical_router_contract():
    from spine_api.services.passenger_rights_claims import evaluate_statutory_compensation

    eligible = evaluate_statutory_compensation("DL456", 8000, 4.0, 3)
    assert eligible["regulatory_framework"] == "US_DOT"
    assert eligible["compensation_per_passenger_eur"] == 300.0
    assert eligible["total_claim_amount_usd"] == round(300.0 * 3 * 1.09, 2)

    below = evaluate_statutory_compensation("DL456", 8000, 3.9, 1)
    assert below["is_eligible"] is False


def test_router_delegates_to_canonical_service():
    """The router response must equal the canonical service output 1:1."""
    from spine_api.routers.passenger_rights import (
        ClaimEvaluationRequest,
        evaluate_passenger_rights_claim,
    )
    from spine_api.services.passenger_rights_claims import evaluate_statutory_compensation

    body = ClaimEvaluationRequest(
        trip_id="trip_x",
        flight_number="AF220",
        disruption_type="DELAYED",
        delay_hours=4.0,
        distance_km=3000,
        passengers_count=2,
    )
    response = evaluate_passenger_rights_claim(body)
    expected = evaluate_statutory_compensation(
        flight_number="AF220", distance_km=3000, delay_hours=4.0, passengers_count=2
    )
    assert response.is_eligible == expected["is_eligible"]
    assert response.regulatory_framework == expected["regulatory_framework"]
    assert response.compensation_per_passenger_eur == expected["compensation_per_passenger_eur"]
    assert response.total_statutory_compensation_eur == expected["total_statutory_compensation_eur"]
    assert response.total_claim_amount_usd == expected["total_claim_amount_usd"]
    assert response.claim_reason == expected["claim_reason"]


def test_legacy_irrops_healer_module_stays_dead():
    """A2 supersession is complete: the legacy healer module must not return."""
    import importlib.util

    assert importlib.util.find_spec("src.logistics.irrops_healer") is None


def test_router_has_no_inline_compensation_arithmetic():
    """Guard against the duplicate-calculator pattern reappearing in the router."""
    from pathlib import Path

    source = (
        Path(__file__).resolve().parents[1]
        / "spine_api"
        / "routers"
        / "passenger_rights.py"
    ).read_text(encoding="utf-8")
    assert "_calculate_eu261_compensation" not in source
    assert 'startswith("BA")' not in source


# --- A4: secret minimization on the trip lane --------------------------------


def test_fulfillment_payload_excludes_raw_vcc_and_eticket():
    from src.orchestration.booking_fulfillment import FulfillmentResult

    result = FulfillmentResult(
        trip_id="trip_a4",
        proposal_token="tok",
        status="CONFIRMED",
        pnr_locator="PNR123",
        e_ticket_number="057-1234567890",
        vcc_card_id="vcc_secret_123",
        vcc_last4="4242",
        total_charged_usd=4200.0,
    ).to_dict()

    assert "vcc_card_id" not in result
    assert "e_ticket_number" not in result
    # Display-safe fields stay.
    assert result["vcc_last4"] == "4242"
    assert result["pnr_locator"] == "PNR123"


def test_fulfillment_source_does_not_write_secrets_to_trip_lane():
    from pathlib import Path

    source = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "orchestration"
        / "booking_fulfillment.py"
    ).read_text(encoding="utf-8")

    # The trip-lane booking_confirmation dict must not carry the raw secrets.
    confirmation_block = source.split('"booking_confirmation": {')[1].split("}")[0]
    assert "vcc_card_id" not in confirmation_block
    assert "e_ticket_number" not in confirmation_block
