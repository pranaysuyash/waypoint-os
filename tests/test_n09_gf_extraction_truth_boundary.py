"""Focused regressions for N-09 and the GF-01/GF-03 extraction fixes.

These tests exercise only the deterministic helper boundary.  They deliberately
cover the small, user-shaped forms that previously caused a salutation to leak
into destinations or a parenthetical/multi-city label to bypass the city-set
path.  Provider, database, and external-service behavior is out of scope.
"""

from src.intake.extractors import _extract_budget, _extract_destination_candidates


def test_gf01_salutation_name_is_not_a_destination():
    candidates, status, _raw = _extract_destination_candidates(
        "Hi Sam! we want to go to Bali in June"
    )

    assert candidates == ["Bali"]
    assert status == "definite"


def test_gf01_honorific_salutation_name_is_not_a_destination():
    candidates, status, _raw = _extract_destination_candidates(
        "Hello Dr. Rao! we want to go to Bali in June"
    )

    assert candidates == ["Bali"]
    assert status == "definite"


def test_gf02_colon_budget_connective_preserves_amount_and_currency():
    result = _extract_budget("Budget: Around $14,000 total")

    assert result == {
        "raw_text": "budget: around $14,000",
        "min": 14000,
        "max": 14000,
        "currency": "USD",
    }


def test_gf03_parenthetical_nights_feed_the_city_set_without_night_tokens():
    candidates, status, raw = _extract_destination_candidates(
        "Destinations: Tokyo (4 nights) and Kyoto (6 nights)"
    )

    assert candidates == ["Tokyo", "Kyoto"]
    assert status == "semi_open"
    assert raw == "tokyo, kyoto"


def test_gf03_parenthetical_label_does_not_duplicate_later_city_set():
    candidates, status, _raw = _extract_destination_candidates(
        "Destinations: Tokyo (4 nights) and Kyoto (6 nights)\n"
        "Also covering Osaka and Nara"
    )

    # The explicit label is authoritative for this pass; it must not be
    # merged with a second scan and produce an accidental duplicate/union.
    assert candidates == ["Tokyo", "Kyoto"]
    assert status == "semi_open"


def test_n09_city_set_keeps_member_before_trailing_season_phrase():
    candidates, status, _raw = _extract_destination_candidates(
        "We are covering Tokyo and Kyoto next spring"
    )

    assert candidates == ["Tokyo", "Kyoto"]
    assert status == "semi_open"
