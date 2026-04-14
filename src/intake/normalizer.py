"""
intake.normalizer — Normalizer v0.2 with ambiguity detection, budget parsing, and date parsing.

Does NOT speculate. Only transforms known patterns.
"""

from __future__ import annotations

import re
from dataclasses import asdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from .packet_models import Ambiguity, EvidenceRef


# =============================================================================
# SECTION 1: NORMALIZATION TABLES
# =============================================================================

class Normalizer:
    """Standardizes values — does NOT speculate. Only transforms known mappings."""

    CITY_NORMALIZATIONS = {
        "blr": "Bangalore",
        "bengaluru": "Bangalore",
        "nyc": "New York",
        "del": "Delhi",
        "deli": "Delhi",
        "nrt": "Narita",
        "hnd": "Haneda",
        "lax": "Los Angeles",
        "sfo": "San Francisco",
        "maa": "Chennai",
        "bom": "Mumbai",
        "ccu": "Kolkata",
    }

    BUDGET_TIER_NORMALIZATIONS = {
        "mid-range": "mid_range",
        "mid range": "mid_range",
        "budget": "budget",
        "economy": "budget",
        "luxury": "luxury",
        "premium": "luxury",
        "high-end": "luxury",
    }

    # Currency indicators
    BUDGET_UNITS = {
        "l": 100000,
        "k": 1000,
        "lac": 100000,
        "lakh": 100000,
        "lakhs": 100000,
        "thousand": 1000,
    }

    # Ambiguity detection patterns
    AMBIGUITY_PATTERNS: Dict[str, List[str]] = {
        "unresolved_alternatives": [
            r"\b(\w+)\s+or\s+(\w+)\b",
            r"\beither\s+(.+?)\s+or\s+(.+?)\b",
        ],
        "value_vague": [
            r"\b(?:big|large|huge)\s+family\b",
            r"\bsome(?:where)?\s+(?:with|for|place)",
            r"\bmaybe\b",
            r"\bthinking\s+about\b",
            r"\bkinda\b",
            r"\bsort\s+of\b",
        ],
        "date_window_only": [
            r"\b(?:around|sometime\s+in|during)\s+",
        ],
        "budget_stretch_present": [
            r"\bcan\s+stretch\b",
            r"\bbudget\s+is\s+flexible\b",
            r"\bif\s+it'?s?\s+good\b",
            r"\bcan\s+go\s+higher\b",
        ],
        "budget_unclear_scope": [
            r"\baround\s+[\d.]+\s*[LlKk]?\b",
            r"\bapprox\.?\b",
        ],
        "composition_unclear": [
            r"\b(?:I\s+think|about|around|roughly|approximately)\s+\d+\b",
            r"\b(?:big|large|huge)\s+family\b",
        ],
        "destination_open": [
            r"\bsomewhere\s+(?:with|for|that)\b",
            r"\bany\s+(?:place|destination|where)",
            r"\bopen\s+to\s+suggestions\b",
        ],
    }

    # ------------------------------------------------------------------
    # City normalization
    # ------------------------------------------------------------------

    @classmethod
    def normalize_city(cls, raw: str) -> Tuple[str, bool]:
        normalized = cls.CITY_NORMALIZATIONS.get(raw.lower(), raw)
        was_normalized = normalized.lower() != raw.lower()
        return normalized, was_normalized

    @classmethod
    def normalize_budget_tier(cls, raw: str) -> Tuple[str, bool]:
        normalized = cls.BUDGET_TIER_NORMALIZATIONS.get(raw.lower(), raw.lower().replace(" ", "_"))
        was_normalized = normalized.lower() != raw.lower()
        return normalized, was_normalized

    # ------------------------------------------------------------------
    # Budget parsing (structured numeric)
    # ------------------------------------------------------------------

    @classmethod
    def parse_budget(cls, raw: str) -> Dict[str, Any]:
        """
        Parse budget text into structured form.
        "4-5L" → {"raw": "4-5L", "min": 400000, "max": 500000, "currency": "INR"}
        "around 2L" → {"raw": "around 2L", "min": None, "max": None, "currency": "INR"}
        "flexible" → {"raw": "flexible", "min": None, "max": None, "currency": "INR"}
        """
        result: Dict[str, Any] = {"raw": raw, "min": None, "max": None, "currency": "INR"}

        # Try range: "4-5L", "4 to 5L", "400K-500K", "4–5L"
        range_match = re.search(
            r"(\d+(?:\.\d+)?)\s*(?:-|–|—|\bto\b)\s*(\d+(?:\.\d+)?)\s*(l|k|lac|lakh|lakhs|thousand)?\b",
            raw,
            re.IGNORECASE,
        )
        if range_match:
            low = float(range_match.group(1))
            high = float(range_match.group(2))
            unit_str = (range_match.group(3) or "").lower()
            multiplier = cls.BUDGET_UNITS.get(unit_str, 1)
            result["min"] = int(low * multiplier)
            result["max"] = int(high * multiplier)
            return result

        # Try single value: "2L", "400000", "4L"
        single_match = re.search(
            r"(\d+(?:\.\d+)?)\s*(l|k|lac|lakh|lakhs|thousand)\b",
            raw,
            re.IGNORECASE,
        )
        if single_match:
            val = float(single_match.group(1))
            unit_str = single_match.group(2).lower()
            multiplier = cls.BUDGET_UNITS.get(unit_str, 1)
            result["min"] = int(val * multiplier)
            result["max"] = int(val * multiplier)
            return result

        # Plain number (no unit) — assume INR if >= 1000
        plain_match = re.search(r"(\d{4,}(?:\.\d+)?)", raw)
        if plain_match:
            val = int(float(plain_match.group(1)))
            result["min"] = val
            result["max"] = val
            return result

        return result

    # ------------------------------------------------------------------
    # Date parsing (structured)
    # ------------------------------------------------------------------

    @classmethod
    def parse_date_window(cls, raw: str) -> Dict[str, Any]:
        """
        Parse date window text into structured form.
        "2026-03-15 to 2026-03-22" → {"window": ..., "start": "2026-03-15", "end": "2026-03-22", "confidence": "exact"}
        "March or April 2026" → {"window": ..., "start": None, "end": None, "confidence": "window"}
        """
        result: Dict[str, Any] = {
            "window": raw,
            "start": None,
            "end": None,
            "confidence": "unknown",
        }

        # Exact ISO range: "2026-03-15 to 2026-03-22"
        iso_range = re.search(
            r"(\d{4}-\d{2}-\d{2})\s+(?:to|–|-)\s+(\d{4}-\d{2}-\d{2})", raw
        )
        if iso_range:
            result["start"] = iso_range.group(1)
            result["end"] = iso_range.group(2)
            result["confidence"] = "exact"
            return result

        # Month window: "March or April 2026", "June-July 2026"
        month_window = re.search(
            r"((?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\w*)"
            r"\s*(?:or|(?:-|–|—|\bto\b))\s*"
            r"((?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\w*)"
            r"\s+(\d{4})",
            raw, re.IGNORECASE,
        )
        if month_window:
            result["confidence"] = "window"
            return result

        # Single month: "March 2026"
        single_month = re.search(
            r"((?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\w*)"
            r"\s+(\d{4})",
            raw, re.IGNORECASE,
        )
        if single_month:
            result["confidence"] = "flexible"
            return result

        # Fuzzy: "around March 2026", "sometime in May 2026"
        fuzzy = re.search(
            r"(?:around|sometime\s+in|during)\s+"
            r"((?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\w*)"
            r"\s+(\d{4})",
            raw, re.IGNORECASE,
        )
        if fuzzy:
            result["confidence"] = "flexible"
            return result

        return result

    # ------------------------------------------------------------------
    # Urgency computation (from date_end)
    # ------------------------------------------------------------------

    @classmethod
    def compute_urgency(cls, date_end_str: str) -> Optional[Dict[str, Any]]:
        """
        Compute urgency from a date_end string (ISO 8601).
        Returns {"level": "high"|"medium"|"low", "days_until": int, "confidence": float}
        or None if date_end is not parseable.
        """
        try:
            end_date = datetime.fromisoformat(date_end_str).replace(tzinfo=None)
            now = datetime.now()
            days = (end_date - now).days
            if days < 0:
                return {"level": "high", "days_until": 0, "confidence": 0.9}
            elif days <= 7:
                return {"level": "high", "days_until": days, "confidence": 0.95}
            elif days <= 21:
                return {"level": "medium", "days_until": days, "confidence": 0.9}
            else:
                return {"level": "low", "days_until": days, "confidence": 0.9}
        except (ValueError, TypeError):
            return None

    # ------------------------------------------------------------------
    # Ambiguity detection
    # ------------------------------------------------------------------

    @classmethod
    def detect_ambiguities(cls, field_name: str, raw_value: str) -> List[Ambiguity]:
        """Scan a raw value for ambiguity patterns."""
        ambiguities = []
        for amb_type, patterns in cls.AMBIGUITY_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, raw_value, re.IGNORECASE):
                    ambiguities.append(Ambiguity(
                        field_name=field_name,
                        ambiguity_type=amb_type,  # type: ignore
                        raw_value=raw_value,
                        confidence=0.8,
                    ))
                    break  # One match per type is enough
        return ambiguities
