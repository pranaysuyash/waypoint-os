"""
intake.route_analysis — lightweight canonical route complexity analysis.

This is an additive, deterministic analysis layer used by runtime feasibility
checks. It intentionally avoids external calls and works with partially
structured trip payloads.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import re


@dataclass(frozen=True, slots=True)
class RouteAnalysis:
    total_legs: int
    transfer_like_items: int
    activity_count: int
    complexity_score: float
    fatigue_indicators: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_legs": self.total_legs,
            "transfer_like_items": self.transfer_like_items,
            "activity_count": self.activity_count,
            "complexity_score": self.complexity_score,
            "fatigue_indicators": list(self.fatigue_indicators),
        }


def analyze_route_complexity(
    *,
    flight_legs: int,
    transfer_like_items: int,
    activity_count: int,
    elderly_count: int = 0,
    toddler_count: int = 0,
) -> RouteAnalysis:
    """
    Build deterministic route complexity/fatigue signals for NB02/runtime use.
    """
    indicators: list[str] = []
    score = 0.0

    if flight_legs >= 2:
        score += min(0.45, flight_legs * 0.1)
    if transfer_like_items >= 2:
        score += min(0.25, transfer_like_items * 0.06)
    if activity_count >= 5:
        score += 0.1

    if flight_legs >= 4:
        indicators.append("multi_leg_flight_fatigue")
    if transfer_like_items >= 3:
        indicators.append("high_transfer_density")
    if activity_count >= 6:
        indicators.append("dense_itinerary")

    if elderly_count > 0 and (flight_legs >= 3 or transfer_like_items >= 3):
        score += 0.2
        indicators.append("elderly_route_tolerance_exceeded")
    if toddler_count > 0 and (flight_legs >= 3 or activity_count >= 5):
        score += 0.15
        indicators.append("toddler_route_pacing_pressure")

    return RouteAnalysis(
        total_legs=max(0, int(flight_legs)),
        transfer_like_items=max(0, int(transfer_like_items)),
        activity_count=max(0, int(activity_count)),
        complexity_score=round(min(1.0, score), 3),
        fatigue_indicators=sorted(set(indicators)),
    )


def parse_itinerary_text(itinerary_text: str) -> dict[str, int]:
    """
    Heuristic parser for free-text itinerary notes.

    Returns counts used by feasibility route checks:
    - inferred_flight_legs
    - inferred_transfer_like_items
    - inferred_activity_count
    """
    text = (itinerary_text or "").strip()
    if not text:
        return {
            "inferred_flight_legs": 0,
            "inferred_transfer_like_items": 0,
            "inferred_activity_count": 0,
        }

    lowered = text.lower()
    # City hop separators / flow words.
    arrow_hops = len(re.findall(r"(->|→| to | then | next | after that )", lowered))
    # Flight-like cues.
    flight_mentions = len(
        re.findall(r"\b(flight|fly|depart|arrival|airline|layover|connection)\b", lowered)
    )
    # Transfer cues.
    transfer_mentions = len(
        re.findall(r"\b(transfer|airport|ferry|boat|rail|train|drive|car pickup|pickup)\b", lowered)
    )
    # Activity cues.
    activity_mentions = len(
        re.findall(
            r"\b(trek|hike|snorkel|scuba|city tour|walking tour|museum|beach|safari|ski|excursion|theme park)\b",
            lowered,
        )
    )

    inferred_flight_legs = max(flight_mentions, arrow_hops)
    return {
        "inferred_flight_legs": inferred_flight_legs,
        "inferred_transfer_like_items": max(transfer_mentions, arrow_hops // 2),
        "inferred_activity_count": activity_mentions,
    }
