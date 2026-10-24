"""
FND-0349 + FND-0350 (Sim #4): the last cheap extraction wins.

- 0349: the occasion anchor fires in BOTH orders — "married on 6th december
  … honeymoon" (date first) as well as "anniversary on november 18th".
- 0350: "6 guys" sizes the party as 6; "solo trip" is a party of 1 — and
  'solo' still never becomes a destination (0329 regression guard).
"""

from __future__ import annotations

from src.intake.extractors import _extract_destination_candidates, _extract_party, _extract_trip_intent


def test_occasion_date_before_occasion_word():
    intent = _extract_trip_intent(
        "we're getting married on 6th december and want a honeymoon in bali right after."
    )
    assert intent["occasion"] == {"type": "honeymoon", "date": "6th december"}


def test_occasion_occasion_word_before_date_unregressed():
    intent = _extract_trip_intent(
        "they want varanasi for their 45th anniversary on november 18th, 3 nights"
    )
    assert intent["occasion"] == {"type": "anniversary", "date": "november 18th"}


def test_guys_count_sizes_the_party():
    party = _extract_party("goa, 6 guys, next weekend, 2 nights, 60k total max.")
    assert party["party_size"] == 6
    assert party["party_composition"]["adults"] == 6


def test_solo_is_a_party_of_one():
    party = _extract_party("solo trip to japan (tokyo + kyoto) for 12 days in march.")
    assert party["party_size"] == 1
    # 0329 regression guard: solo is a modifier, never a place
    candidates, _status, _raw = _extract_destination_candidates(
        "solo trip to japan for 12 days in march."
    )
    assert "Solo" not in candidates
