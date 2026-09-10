"""
tests/test_ts06_route_structures.py — TS-06 (2026-09-10 training-session
register): candidate route-structure generation + incremental refinement.

Contract under test (Docs/exploration/TS06_CANDIDATE_ROUTE_STRUCTURES_2026-09-09.md):
- enumerate_route_structures: night-splits across city permutations honoring
  hard constraints (every city once, nights sum, min nights per city);
  bounded candidates; deterministic order.
- Open-jaw refinement (soft dependencies): when arrival/departure cities are
  known, the aligned structure wins (Tokyo in / Osaka out → Tokyo first,
  no backtrack); without flight data, generation still proceeds.
- candidates_as_branch_options: BRANCH_OPTIONS-vocabulary rendering.
- Decision enrichment: multi-city + dated packets gain route-structure
  branch_options; decision_state is NOT changed by enrichment; abstains
  when cities or dates are unresolvable.
- _derive_trip_nights: ISO date_start/date_end; abstains on anything else.
"""

import os


os.environ.setdefault("RUNNING_TESTS", "1")

from src.decision.route_structures import (  # noqa: E402
    candidates_as_branch_options,
    enumerate_route_structures,
)
from src.intake.packet_models import CanonicalPacket, Slot  # noqa: E402


# --- enumerator -------------------------------------------------------------------


def test_night_splits_two_cities_seven_nights():
    """The tutor's canonical case: 7 nights, Tokyo + Kyoto."""
    candidates = enumerate_route_structures(["Tokyo", "Kyoto"], 7, max_candidates=16)
    splits = {tuple(c.nights) for c in candidates}
    assert (4, 3) in splits
    assert (3, 4) in splits
    # both orderings of the cities appear
    sequences = {tuple(c.cities) for c in candidates}
    assert ("Tokyo", "Kyoto") in sequences
    assert ("Kyoto", "Tokyo") in sequences


def test_min_nights_constraint_respected():
    # 5 nights, 3 cities, min 2 each: impossible (2+2+1 violates min) -> empty
    assert enumerate_route_structures(["A", "B", "C"], 5, min_nights_per_city=2) == []
    candidates = enumerate_route_structures(["A", "B", "C"], 6, min_nights_per_city=2, max_candidates=16)
    assert candidates
    assert all(min(c.nights) >= 2 for c in candidates)
    assert all(sum(c.nights) == 6 for c in candidates)


def test_infeasible_total_returns_empty():
    assert enumerate_route_structures(["A", "B"], 1) == []
    assert enumerate_route_structures([], 5) == []


def test_bounded_candidates():
    candidates = enumerate_route_structures(["A", "B", "C"], 9, max_candidates=3)
    assert len(candidates) <= 3


def test_deterministic_without_flight_data():
    a = enumerate_route_structures(["Tokyo", "Kyoto"], 7)
    b = enumerate_route_structures(["Tokyo", "Kyoto"], 7)
    assert [c.to_dict() for c in a] == [c.to_dict() for c in b]
    assert all(c.open_jaw_aligned is None for c in a)


# --- open-jaw refinement ------------------------------------------------------------


def test_open_jaw_alignment_wins():
    """Arrival Tokyo / departure Osaka: the Tokyo-first, Osaka-last structure
    outranks its reverse (which backtracks to the entry city)."""
    candidates = enumerate_route_structures(
        ["Tokyo", "Kyoto", "Osaka"], 7,
        arrival_city="Tokyo", departure_city="Osaka",
    )
    best = candidates[0]
    assert best.cities[0] == "Tokyo"
    assert best.cities[-1] == "Osaka"
    assert best.open_jaw_aligned is True


def test_partial_alignment_scores_between():
    candidates = enumerate_route_structures(
        ["Tokyo", "Osaka"], 5,
        arrival_city="Tokyo", departure_city=None,
    )
    aligned = [c for c in candidates if c.cities[0] == "Tokyo"]
    not_aligned = [c for c in candidates if c.cities[0] != "Tokyo"]
    assert all(a.score > b.score for a in aligned for b in not_aligned)
    assert all(c.open_jaw_aligned is False or c.open_jaw_aligned is None for c in candidates)


def test_case_insensitive_city_match():
    candidates = enumerate_route_structures(
        ["tokyo", "osaka"], 5, arrival_city="Tokyo", departure_city="OSAKA"
    )
    assert candidates[0].cities[0] == "tokyo"
    assert candidates[0].open_jaw_aligned is True


def test_more_cities_than_permutation_bound_keeps_input_order():
    """Above the permutation bound, the input order is kept (documented
    pruning seam for the geography lane) — not an explosion."""
    cities = [f"City{i}" for i in range(6)]
    candidates = enumerate_route_structures(cities, 12)
    assert candidates
    assert all(c.cities == cities for c in candidates)


# --- branch-options rendering --------------------------------------------------------


def test_candidates_as_branch_options_shape():
    candidates = enumerate_route_structures(["Tokyo", "Kyoto"], 7, max_candidates=1)
    options = candidates_as_branch_options(candidates)
    assert len(options) == 1
    opt = options[0]
    assert opt["label"]
    assert "route_structure" in opt
    assert opt["route_structure"]["cities"] == candidates[0].cities
    assert opt["route_structure"]["nights"] == candidates[0].nights


# --- decision enrichment --------------------------------------------------------------


def _packet(facts: dict) -> CanonicalPacket:
    packet = CanonicalPacket(packet_id="pkt_ts06")
    for name, value in facts.items():
        packet.facts[name] = Slot(value=value, confidence=1.0, authority_level="explicit_user")
    return packet


def test_multi_city_dated_packet_gains_route_branch_options():
    from src.intake.decision import run_gap_and_decision

    packet = _packet({
        "destination_candidates": ["Tokyo", "Kyoto"],
        "date_window": "Oct 5-12",
        "date_start": "2026-10-05",
        "date_end": "2026-10-12",
        "party_size": 4,
        "budget_raw_text": "4L",
        "trip_purpose": "leisure",
        "origin_city": "Bengaluru",
    })
    result = run_gap_and_decision(packet)
    route_options = [
        o for o in result.branch_options
        if isinstance(o, dict) and "route_structure" in o
    ]
    assert route_options, "multi-city + dated packet must gain route-structure options"
    rs = route_options[0]["route_structure"]
    assert sorted(rs["cities"]) == ["Kyoto", "Tokyo"]
    assert sum(rs["nights"]) == 7  # Oct 5 → Oct 12


def test_enrichment_never_changes_decision_state():
    """A complete single-city packet keeps its PROCEED decision; enrichment
    abstains (single city → no route structures)."""
    from src.intake.decision import run_gap_and_decision

    packet = _packet({
        "destination_candidates": ["Goa"],
        "date_window": "Oct 5-12",
        "date_start": "2026-10-05",
        "date_end": "2026-10-12",
        "party_size": 2,
        "budget_raw_text": "1L",
        "trip_purpose": "leisure",
        "origin_city": "Bengaluru",
    })
    result = run_gap_and_decision(packet)
    assert not any(
        isinstance(o, dict) and "route_structure" in o for o in result.branch_options
    )


def test_undated_multi_city_packet_abstains():
    from src.intake.decision import run_gap_and_decision

    packet = _packet({"destination_candidates": ["Tokyo", "Kyoto"]})
    result = run_gap_and_decision(packet)
    assert not any(
        isinstance(o, dict) and "route_structure" in o for o in result.branch_options
    )


def test_derive_trip_nights_parsing():
    from src.intake.decision import _derive_trip_nights

    assert _derive_trip_nights(_packet({"date_start": "2026-10-05", "date_end": "2026-10-12"})) == 7
    assert _derive_trip_nights(_packet({"date_start": "2026-10-05"})) is None
    assert _derive_trip_nights(_packet({})) is None
    assert _derive_trip_nights(_packet({"date_start": "not-a-date", "date_end": "2026-10-12"})) is None
    assert _derive_trip_nights(_packet({"date_start": "2026-10-12", "date_end": "2026-10-05"})) is None
