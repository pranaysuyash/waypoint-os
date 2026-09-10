"""
src/decision/route_structures.py — Candidate Route-Structure Enumerator (TS-06).

Deterministic generator of trip-structure candidates (night-splits across
city sequences) with open-jaw refinement — the tutor's model: hard
dependencies (must-visit cities, total nights) generate candidate structures
BEFORE exact flights exist; soft dependencies (arrival/departure airports)
then refine them dramatically (arrival Tokyo 10:00 / return Osaka 23:00 →
open-jaw Tokyo→Kyoto→Osaka instead of backtracking).

Design boundaries (register TS-06, 2026-09-10):
- Generation is combinatorics over hard constraints — no LLM in generation.
- Candidates are skeletons: city sequences with night allocations, NOT
  scheduled itineraries. Scoring never fabricates travel times; the
  travel-time-matrix hook is a documented seam for the geography lane.
- LLM may narrate trade-offs between candidates; it must never alter the
  skeletons (provider-facts rule).
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import permutations
from typing import Any, Dict, List, Optional

MAX_CITIES_FOR_FULL_PERMUTATION = 4
MAX_CANDIDATES_DEFAULT = 4


@dataclass(slots=True)
class RouteStructureCandidate:
    """One candidate trip structure: an ordered city sequence with nights."""

    cities: List[str]
    nights: List[int]
    # Open-jaw: the journey enters at the first city and exits from the last
    # (no return backtrack). None until scored against arrival/departure.
    open_jaw_aligned: Optional[bool] = None
    score: float = 0.0
    label: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cities": list(self.cities),
            "nights": list(self.nights),
            "open_jaw_aligned": self.open_jaw_aligned,
            "score": self.score,
            "label": self.label,
        }

    @property
    def description(self) -> str:
        parts = [f"{city} {n}N" for city, n in zip(self.cities, self.nights)]
        return " → ".join(parts)


def _night_splits(total: int, parts: int, min_per_part: int) -> List[List[int]]:
    """All ordered compositions of `total` into `parts` parts, each >= min."""
    if parts <= 0:
        return [] if total else [[]]
    if parts == 1:
        return [[total]] if total >= min_per_part else []
    out: List[List[int]] = []
    remaining_parts = parts - 1
    for first in range(min_per_part, total - min_per_part * remaining_parts + 1):
        for rest in _night_splits(total - first, remaining_parts, min_per_part):
            out.append([first] + rest)
    return out


def enumerate_route_structures(
    cities: List[str],
    nights_total: int,
    min_nights_per_city: int = 1,
    max_candidates: int = MAX_CANDIDATES_DEFAULT,
    arrival_city: Optional[str] = None,
    departure_city: Optional[str] = None,
) -> List[RouteStructureCandidate]:
    """Enumerate candidate trip structures (TS-06).

    Hard constraints: every city visited exactly once, nights sum to
    `nights_total`, each city >= `min_nights_per_city`. City sequences come
    from permutations (bounded: above MAX_CITIES_FOR_FULL_PERMUTATION the
    input order is kept — the geography lane owns smarter pruning).

    Soft-dependency refinement: when `arrival_city`/`departure_city` are
    known (flight data arrived), candidates are scored — open-jaw alignment
    (enter first city, exit last city) wins; ties break deterministically on
    fewer-but-longer stays first (fewer hotel changes), then lexicographic.
    Without flight data, candidates are returned in the same deterministic
    order — generation never blocks on soft dependencies.
    """
    cities = [c for c in cities if c]
    if not cities or nights_total < len(cities) * min_nights_per_city:
        return []

    if len(cities) <= MAX_CITIES_FOR_FULL_PERMUTATION:
        sequences: List[List[str]] = [list(p) for p in permutations(cities)]
    else:
        sequences = [list(cities)]

    candidates: List[RouteStructureCandidate] = []
    for sequence in sequences:
        for split in _night_splits(nights_total, len(sequence), min_nights_per_city):
            candidates.append(
                RouteStructureCandidate(cities=list(sequence), nights=list(split))
            )

    scored = [
        _score(c, arrival_city, departure_city, index)
        for index, c in enumerate(candidates)
    ]
    scored.sort(key=lambda c: (-c.score, c.label))
    return scored[:max_candidates]


def _score(
    candidate: RouteStructureCandidate,
    arrival_city: Optional[str],
    departure_city: Optional[str],
    index: int,
) -> RouteStructureCandidate:
    """Deterministic scoring over soft dependencies (TS-06).

    - Open-jaw alignment (+10): arrival city is the first stop and departure
      city is the last stop — the structure absorbs the flight shape instead
      of backtracking to the entry city.
    - Partial alignment (+3): at least the arrival or departure end matches.
    - Fewer-but-longer stays (+1 per city above the minimum stay): fewer
      hotel changes, less packing.
    - Lexicographic tiebreak keeps output stable across runs.
    """
    score = 0.0
    open_jaw: Optional[bool] = None
    if arrival_city or departure_city:
        first_match = bool(arrival_city) and candidate.cities[0].lower() == arrival_city.lower()
        last_match = bool(departure_city) and candidate.cities[-1].lower() == departure_city.lower()
        open_jaw = first_match and last_match
        if open_jaw:
            score += 10.0
        elif first_match or last_match:
            score += 3.0
    score += sum(1 for n in candidate.nights if n > 1)
    candidate.open_jaw_aligned = open_jaw
    candidate.score = score
    candidate.label = candidate.description if not open_jaw else f"{candidate.description} (open-jaw)"
    return candidate


def candidates_as_branch_options(
    candidates: List[RouteStructureCandidate],
) -> List[Dict[str, Any]]:
    """Render candidates as decision.branch_options entries (BRANCH_OPTIONS
    vocabulary): label + description + the skeleton payload. The LLM/operator
    narrates trade-offs; the skeletons themselves are deterministic output.
    """
    return [
        {
            "label": c.label or c.description,
            "description": f"Candidate route structure: {c.description}.",
            "route_structure": c.to_dict(),
        }
        for c in candidates
    ]
