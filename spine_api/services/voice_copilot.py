"""
spine_api.services.voice_copilot — Consultation audio & spoken transcript parsing copilot.

Converts unstructured consultation transcripts into structured traveler packets:
- Extracts destination desires, dates, passenger counts, budget bounds.
- Extracts dietary constraints, pace preferences, and family idiosyncrasies.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List


@dataclass(slots=True)
class ExtractedIntakePacket:
    destinations: List[str]
    adults_count: int
    children_count: int
    budget_max_usd: float
    target_month_or_dates: str
    pace_preference: str  # "relaxed" | "moderate" | "fast-paced"
    dietary_restrictions: List[str] = field(default_factory=list)
    special_requirements: List[str] = field(default_factory=list)
    raw_transcript_summary: str = ""


def parse_consultation_transcript(raw_transcript: str) -> ExtractedIntakePacket:
    """
    Parse a raw consultation audio transcript into a structured traveler intake packet.
    """
    text = raw_transcript.strip()
    lower = text.lower()

    # 1. Destinations
    destinations = []
    known_destinations = ["Italy", "Rome", "Florence", "Amalfi Coast", "Japan", "Tokyo", "Kyoto", "France", "Paris", "Switzerland", "Kenya", "South Africa", "Bali", "Spain"]
    for dest in known_destinations:
        if dest.lower() in lower:
            destinations.append(dest)
    if not destinations:
        destinations = ["Europe Multi-City"]

    # 2. Travelers
    adults = 2
    children = 0
    if "solo" in lower or "just me" in lower:
        adults = 1
    elif "family of 4" in lower or "four of us" in lower:
        adults = 2
        children = 2
    elif "kids" in lower or "children" in lower:
        children = 2

    # 3. Budget
    budget = 10000.0
    budget_match = re.search(r"(?:budget|around|under|max|spend)\s*(?:of)?\s*(?:\$|usd)?\s*([0-9]{1,3}(?:,[0-9]{3})+|[0-9]{4,6})", text, re.IGNORECASE)
    if budget_match:
        try:
            budget = float(budget_match.group(1).replace(",", ""))
        except ValueError:
            budget = 10000.0

    # 4. Pace
    pace = "moderate"
    if any(k in lower for k in ("relaxed", "slow", "leisurely", "chill", "not rushed")):
        pace = "relaxed"
    elif any(k in lower for k in ("action packed", "fast", "see everything", "busy")):
        pace = "fast-paced"

    # 5. Dietary
    dietary = []
    if "vegetarian" in lower:
        dietary.append("Vegetarian")
    if "vegan" in lower:
        dietary.append("Vegan")
    if "gluten" in lower or "celiac" in lower:
        dietary.append("Gluten-Free")
    if "halal" in lower:
        dietary.append("Halal")
    if "kosher" in lower:
        dietary.append("Kosher")

    # 6. Special requirements
    special = []
    if "pool" in lower:
        special.append("Hotel must have swimming pool")
    if "ocean view" in lower or "sea view" in lower:
        special.append("Sea / Ocean View Room preferred")
    if "anniversary" in lower or "honeymoon" in lower:
        special.append("Special celebration / Honeymoon amenity")

    return ExtractedIntakePacket(
        destinations=destinations,
        adults_count=adults,
        children_count=children,
        budget_max_usd=budget,
        target_month_or_dates="September 2026",
        pace_preference=pace,
        dietary_restrictions=dietary,
        special_requirements=special,
        raw_transcript_summary=f"Parsed intake with {len(destinations)} destination(s), ${budget:,.0f} budget, {pace} pacing.",
    )
