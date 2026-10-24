"""
FND-0329 (Sim #4): destination extraction must read sentence context, not
gazetteer membership alone.

- "solo trip to japan (tokyo + kyoto)" → Japan / Tokyo / Kyoto, never 'Solo'
  (the Indonesian city) — the modifier reading wins.
- "kids are too young for that drive" never sweeps 'Young'.
- "we want kerala in october" → Kerala; "add 2 nights in coorg" → Coorg;
  "scrap coorg … just kerala" → both regions surface (operator sees the
  contradiction) instead of nothing.
- Regression guards: the previously-correct voices keep their results
  (Sim #2/#3/#4 fixtures became gates).
"""

from __future__ import annotations

import pytest

from src.intake.extractors import _extract_destination_candidates


@pytest.mark.parametrize(
    "text,expected",
    [
        # Sim #4-E: 'Solo' must lose to the cued, explicit destinations.
        (
            "solo trip to japan (tokyo + kyoto) for 12 days at the end of march "
            "for the cherry blossoms. budget 2.2 lakh.",
            (["Japan"], "definite"),
        ),
        # Sim #4-J: regions are destinations.
        ("we want kerala in october, 6 nights, flying from pune.", (["Kerala"], "definite")),
        ("actually make it 7 nights, and add 2 nights in coorg at the end.", (["Coorg"], "definite")),
        # Contradiction ("scrap coorg … just kerala") surfaces both for the
        # operator — semi_open, never a silent pick.
        (
            "scrap coorg, the kids are too young for that drive. just kerala please.",
            (["Kerala", "Coorg"], "semi_open"),
        ),
        # Established voices keep their results (regression gates).
        (
            "need a quick bachelor trip to goa for 6 guys, 2 nights next weekend, budget 60k total.",
            (["Goa"], "definite"),
        ),
        ("they want varanasi for their 45th anniversary on november 18th, 3 nights", (["Varanasi"], "definite")),
        (
            "12 people from bangalore, 3 nights, jaipur + udaipur (2 nights jaipur, "
            "1 night udaipur), mid-february.",
            (["Jaipur", "Udaipur"], "semi_open"),
        ),
    ],
)
def test_destination_candidates(text, expected):
    candidates, status, _raw = _extract_destination_candidates(text)
    assert candidates == expected[0]
    assert status == expected[1]


def test_solo_is_never_a_destination_candidate():
    candidates, _status, raw = _extract_destination_candidates(
        "solo trip to japan for 12 days in march."
    )
    assert "Solo" not in candidates
    assert "solo" not in (raw or "").lower().split("|")[0].split(",")[0].strip()


def test_young_is_never_a_destination_candidate():
    candidates, _status, _raw = _extract_destination_candidates(
        "scrap coorg, the kids are too young for that drive. just kerala please."
    )
    assert "Young" not in candidates
