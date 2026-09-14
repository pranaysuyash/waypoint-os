"""P-F airport-code extraction — table membership is the guard (Addendum 9).

"flying into SIN next week" must resolve Singapore; unknown 3-letter words
must never become destinations through the airport path.
"""

from src.intake.airport_codes import resolve_airport_code
from src.intake.extractors import _extract_destination_candidates


def test_table_spot_checks():
    assert resolve_airport_code("DEL")["city"] == "Delhi"
    assert resolve_airport_code("DEL")["country"] == "IN"
    assert resolve_airport_code("sin")["city"] == "Singapore"  # case-insensitive
    assert resolve_airport_code("XYZ") is None
    assert resolve_airport_code("AB") is None  # not 3 letters
    assert resolve_airport_code("12A") is None  # not alpha


def test_iata_only_note_resolves_city():
    candidates, status, _ = _extract_destination_candidates("flying into SIN next week")
    assert "Singapore" in candidates
    assert status == "definite"


def test_iata_pair_keeps_destination_side():
    candidates, _, _ = _extract_destination_candidates("DEL to BKK trip in march")
    assert "Bangkok" in candidates
    # DEL is the origin reference — never a destination here.
    assert "Delhi" not in candidates


def test_unknown_three_letter_words_cannot_become_destinations():
    candidates, _, _ = _extract_destination_candidates("the dog has fleas")
    assert candidates == []


def test_known_city_still_wins_alongside_codes():
    candidates, _, _ = _extract_destination_candidates("tokyo and SIN on the same trip")
    assert "Tokyo" in candidates and "Singapore" in candidates
