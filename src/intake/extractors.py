"""
intake.extractors — ExtractionPipeline v0.2.

Pattern-based (not mock/keyword) extraction that populates the v0.2 CanonicalPacket.
Not an LLM — but honest regex parsing that handles the 30+ fact fields.

Geography handling (v0.2.1):
- Uses geography.py for city validation (590k+ cities from GeoNames + world-cities)
- Separates concerns: is_known_city vs likely_origin vs likely_destination vs historical_mention
- Origin/destination are determined by context patterns, not city list membership
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple

# Month name → number mapping (module-level, created once)
_MONTH_MAP = {
    "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
    "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6,
    "jul": 7, "july": 7, "aug": 8, "august": 8, "sep": 9, "sept": 9, "september": 9,
    "oct": 10, "october": 10, "nov": 11, "november": 11, "dec": 12, "december": 12,
}

from .packet_models import (
    Ambiguity,
    AuthorityLevel,
    CanonicalPacket,
    EvidenceRef,
    ExtractionMode,
    OwnerConstraint,
    Slot,
    SourceEnvelope,
    SubGroup,
    UnknownField,
)
from .normalizer import Normalizer
from .geography import is_known_city, is_known_destination, get_city_country

_MONTH_NAMES = frozenset({
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december",
    "jan", "feb", "mar", "apr", "jun", "jul", "aug", "sep", "sept", "oct", "nov", "dec",
})

_RELATION_WORDS = frozenset({
    "wife", "husband", "spouse", "parents", "mother", "father", "mom", "dad",
    "kid", "child", "baby", "toddler", "son", "daughter", "grandparents",
    "grandmother", "grandfather", "colleague", "friend", "partner", "boss",
    "caller", "client", "agent",
})

_STOP_WORDS = frozenset({
    "we", "i", "my", "our", "the", "this", "that", "it", "they",
    "he", "she", "us", "me", "him", "her", "and", "or", "to",
    "with", "for", "from", "in", "on", "at", "by",
    # Hinglish/common false positives (often match obscure GeoNames entries)
    "se", "ru", "side", "jana", "jaana", "hai", "ho", "ka", "ki", "ke",
    "ko", "ye", "wo", "jo", "tha", "thee", "hain", "log", "aur", "nahi",
    # English words that match obscure cities in GeoNames
    "are", "is", "was", "be", "been", "being", "have", "has", "had",
    "do", "does", "did", "will", "would", "can", "could", "shall", "should",
    "may", "might", "must", "need", "dare", "ought", "used",
    "about", "above", "across", "after", "against", "along", "among",
    "around", "before", "behind", "below", "beneath", "beside", "between",
    "beyond", "but", "by", "concerning", "considering", "despite",
    "down", "during", "except", "following", "inside", "into",
    "like", "near", "onto", "outside", "over", "past", "plus",
    "since", "through", "throughout", "toward", "towards", "under",
    "underneath", "until", "upon", "via", "within", "without",
})

_DESTINATION_HINT_VERBS = frozenset({
    "visit", "travel", "trip", "holiday", "vacation", "go", "going",
    "flying", "fly", "planning", "plan", "explore", "see", "tour",
    "honeymoon", "getaway", "weekend",
})


# =============================================================================
# SECTION 1: DESTINATION DETECTION
# =============================================================================

# Regex for destination extraction - uses broad pattern to capture place names
# Validation happens via geography.py, not hardcoded lists
# Matches capitalized place names (single or multi-word)
_DESTINATION_RE = re.compile(
    r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b",
)

# Travel-context patterns for lowercase destination extraction.
# Only match destinations that appear in travel-intent context, not globally.
# This prevents false positives like "got" in "I got your number".

# Pattern 1: English travel verbs followed by destination.
# "go to singapore", "want to go singapore", "travel to singapore", etc.
_TRAVEL_VERB_DEST_RE = re.compile(
    r"(?:want to go|go to|travel to|visit|flying to|trip to|holiday in|vacation in"
    r"|planning to go to|planning to visit|head to|going to)\s+"
    r"([a-z]+(?:\s+[a-z]+)*)",
    re.IGNORECASE,
)

# Pattern 2: "somewhere" + destination (open intent)
_SOMEWHERE_DEST_RE = re.compile(
    r"somewhere\s+(?:with|for|that)\s+(\w+)",
    re.IGNORECASE,
)

# Pattern 3: "or" pattern (semi-open destination)
_OR_DESTINATION_RE = re.compile(
    r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)(?:\s+(?:or|and)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*).*?)\b",
)

# Destination metadata labels to exclude (caller, referral, etc.)
_DESTINATION_METADATA_LABELS_RE = re.compile(
    r"^\s*(call\s+received|caller|referral|party|pace(?:\s+reference)?|budget|interests?|follow[\s-]*up|toddler\s+needs?|elderly\s+needs?)\s*:",
    re.IGNORECASE,
)

# Common inline patterns - pre-compiled for performance
_YEAR_RE = re.compile(r"\b(20\d{2})\b")
_FROM_STARTING_DEPARTING_RE = re.compile(r'\b(from|starting|departing)\s+$', re.IGNORECASE)
_SE_RU_SIDE_RE = re.compile(r'^\s+(se|ru|side)\b', re.IGNORECASE)
_MAYBE_RE = re.compile(r"\bmaybe\s+(\w+)", re.IGNORECASE)
_THIS_WEEKEND_RE = re.compile(
    r"\bthis\s+(weekend|friday|saturday|sunday|monday|tuesday|wednesday|thursday)\b",
    re.IGNORECASE,
)
_MONTH_WINDOW_RE = re.compile(
    r"((?:January|February|March|April|May|June|July|August|September|October|November|December)\w*)"
    r"\s*(?:or|ya|(?:-|–|—|\bto\b))\s*"
    r"((?:January|February|March|April|May|June|July|August|September|October|November|December)\w*)"
    r"(?:\s+(\d{4}))?",
    re.IGNORECASE,
)
_SINGLE_MONTH_RE = re.compile(
    r"(?:in|during|for)\s+"
    r"(?:January|February|March|April|May|June|July|August|September|October|November|December)\w*"
    r"\s+(\d{4})",
    re.IGNORECASE,
)
_FUZZY_MONTH_RE = re.compile(
    r"(?:around|sometime\s+in|during)\s+((?:January|February|March|April|May|June|July|August|September|October|November|December)\w*)",
    re.IGNORECASE,
)
_FLEXIBLE_BUDGET_RE = re.compile(r"\bflexible\s+budget\b|\bbudget\s+is\s+flexible\b", re.IGNORECASE)
_TOTAL_GROUP_RE = re.compile(r"\b(?:total|for\s+(?:the\s+)?(?:whole\s+)?(?:trip|family|group))\b", re.IGNORECASE)

# Month abbreviations for day range patterns
_MONTH_ABBR = r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*"

# Day range patterns (module level)
_DAY_RANGE_TEXT_RE = re.compile(
    r"\b(?:around|tentative(?:ly)?|dates?\s+around)?\s*"
    r"(\d{1,2})(?:st|nd|rd|th)?\s*(?:to|-|–|—|\bto\b)\s*(\d{1,2})(?:st|nd|rd|th)?\s+"
    r"(" + _MONTH_ABBR + r")\b"
    r"(?:\s+(\d{4}))?",
)

# Date range pattern
_DAY_RANGE_RE = re.compile(
    r"(\d{4}-\d{2}-\d{2})\s+(?:to|–|-)\s+(\d{4}-\d{2}-\d{2})"
)

# Past trip indicators
_PAST_TRIP_INDICATORS_RE = re.compile(
    r"\b(?:last\s+(?:time|year|month|summer|winter)|recently\s+visited|we\s+went\s+to|"
    r"came\s+back\s+from|returned\s+from|their\s+last|earlier\s+trip|past\s+trip)\b",
    re.IGNORECASE,
)

# Hedging words (maybe, perhaps, etc.)
_HEDGING_RE = re.compile(
    r"\b(?:maybe|perhaps|considering|looking\s+at|thinking\s+about)\s+(\w+)",
    re.IGNORECASE,
)

# People count patterns
_ADULTS_RE = re.compile(r"(\d+)\s+adults?", re.IGNORECASE)
_CHILDREN_RE = re.compile(r"(?:(\d+)\s+)?(?:kids?|children?|child|bachhe|baccha)", re.IGNORECASE)
_TODDLER_RE = re.compile(r"\b(?:a\s+)?(?:toddler|toddlers?)\b", re.IGNORECASE)
_TODDLER_AGE_RE = re.compile(r"toddler\s+(?:age\s+)?(\d+)", re.IGNORECASE)
_ELDERLY_RE = re.compile(r"(?:(\d+)\s+)?(?:elderly|seniors?|grandparents?|grandma|grandpa|grandmother|grandfather)", re.IGNORECASE)
_ELDERLY_AGE_RE = re.compile(r"\b(?:elderly|seniors?)\b", re.IGNORECASE)
_PEOPLE_RE = re.compile(r"(\d+)\s+(?:people|persons?|pax|travelers?)", re.IGNORECASE)

# Age patterns
_AGE_RE = re.compile(r"(\d+\.?\d*)\s*(?:years?|yr|y)[\s-]*(?:old|aged?)\s+(\w+)", re.IGNORECASE)
_AGES_RE = re.compile(r"(\d+)\s*(?:years?|yr|y)[\s-]*(?:old|aged?)", re.IGNORECASE)
_MULTI_AGE_RE = re.compile(r"(\d+)\s*(?:,|and)\s*(\d+)\s*(?:,|and)?\s*(\d+)?\s*(?:years?|yr|y)", re.IGNORECASE)

# Family/group patterns
_FAMILY_RE = re.compile(r"(?:family|they|customer)\s+(?:always\s+)?(?:prefers?|likes?)\s+([^.,]+)", re.IGNORECASE)
_GROUP_SIZE_RE = re.compile(r"(?:family|group)\s+\w+\s*(?:of\s+)?(\d+)", re.IGNORECASE)

# Food preference patterns
_FOOD_PREFERENCE_RE = re.compile(
    r"((?:vegetarian|vegan|jain|halal|kosher|non(?:-\s*)?veg|food\s+preference)[^.]*?)",
    re.IGNORECASE,
)
_NO_FOOD_RE = re.compile(r"(?:no|don'?t\s+(?:want|need|book)|avoid|never)\s+([^.,]+)", re.IGNORECASE)
_WANT_FOOD_RE = re.compile(r"(?:want|prefer|like|interested\s+in)\s+([^.,]+)", re.IGNORECASE)

# Passport patterns
_PASSPORT_EXPIRED_RE = re.compile(r"(\d)\s*(?:/|out\s+of)\s*5", re.IGNORECASE)
_PASSPORT_VALID_RE = re.compile(r"valid\s+(?:until|till|through)\s+([A-Za-z]+\s+\d{4})", re.IGNORECASE)
_EXISTING_ITINERARY_RE = re.compile(r"(?:have|existing|current)\s+(?:an\s+)?itinerary[^.]*\.", re.IGNORECASE)

# Hotel/star rating
_HOTEL_STAR_RE = re.compile(r"((?:5|4|3)[\s-]*star\s+(?:resort|hotel)?(?:[^.]*?))", re.IGNORECASE)
_STAR_RATING_RE = re.compile(r"(\d)\s*star", re.IGNORECASE)

# Mobility/accessibility
_MOBILITY_RE = re.compile(
    r"(?:can'?t\s+walk|wheelchair|mobility|slow\s+pace|limited\s+mobility|"
    r"disabled|handicapped|accessible)\s*(?:\s*\d+)?\s*(?:people|persons?|pax)?",
    re.IGNORECASE,
)

# Medical conditions
_MEDICAL_RE = re.compile(
    r"(?:hypertension|diabetes|heart\s+condition|medical\s+condition|"
    r"pregnant|asthma|allergy|medication)[^.]*?(?:doctor|medical)?",
    re.IGNORECASE,
)

# Customer/client patterns
_CUSTOMER_ID_RE = re.compile(r"(?:customer|client)\s+(?:id|name|ref)[:\s]+(\w+)", re.IGNORECASE)

# Revision/past trip
_REVISION_RE = re.compile(r"\brevision\s*(?:#|number\s*)(\d+)", re.IGNORECASE)
_PAST_TRIP_RE = re.compile(r"(?:past|previous)\s+trip[^.,:]*", re.IGNORECASE)

# Pace patterns (compile once at module level)
_PACE_PATTERNS = [
    (re.compile(r"\b(?:it\s+)?rushed\b", re.IGNORECASE), "relaxed pace"),
    (re.compile(r"\b(?:it\s+)?rush\b", re.IGNORECASE), "relaxed pace"),
    (re.compile(r"\b(?:be\s+)?too\s+packed\b", re.IGNORECASE), "relaxed pace"),
    (re.compile(r"\b(?:be\s+)?too\s+busy\b", re.IGNORECASE), "relaxed pace"),
    (re.compile(r"\bhurried\b", re.IGNORECASE), "relaxed pace"),
]
# Travel-context patterns for lowercase destination extraction.
# Only match destinations that appear in travel-intent context, not globally.
# This prevents false positives like "got" in "I got your number".

# Pattern 1: English travel verbs followed by destination.
# "go to singapore", "want to go singapore", "travel to singapore", etc.
_TRAVEL_VERB_DEST_RE = re.compile(
    r"(?:want to go|go to|travel to|visit|flying to|trip to|holiday in|vacation in"
    r"|planning to go to|planning to visit|head to|going to)\s+"
    r"([a-z]+(?:\s+[a-z]+)*)",
)

# Pattern 2: Destination before Hinglish/Odia travel verbs.
# "singapore jana hai", "bali jaiba"
_HINGLISH_DEST_RE = re.compile(
    r"([a-z]+(?:\s+[a-z]+)*)\s+"
    r"(?:jana hai|jaana hai|jao|jana|janahi|jiba|jib)",
)

# Pattern 3: After origin marker ("se"/"ru") before travel verb.
# "bangalore se singapore jana hai", "bangalore ru sri lanka jiba"
_ORIGIN_DEST_RE = re.compile(
    r"(?:se |ru )\s*([a-z]+(?:\s+[a-z]+)*)\s+"
    r"(?:jana hai|jana|jiba|jib|go|travel|visit)",
)


@lru_cache(maxsize=32)
def _month_to_num(month_str: str) -> Optional[int]:
    return _MONTH_MAP.get(month_str.lower()[:3].rstrip("e")) or _MONTH_MAP.get(month_str.lower())


def _infer_year_from_context(text: str) -> str:
    year_match = _YEAR_RE.search(text)
    if year_match:
        return year_match.group(1)
    return str(datetime.now().year)


def _normalize_constraint(raw: str) -> str:
    """Normalize a raw constraint fragment into a clean canonical form."""
    lower = raw.lower().strip()
    _PACE_PATTERNS = [
        (r"\b(?:it\s+)?rushed\b", "relaxed pace"),
        (r"\b(?:it\s+)?rush\b", "relaxed pace"),
        (r"\b(?:be\s+)?too\s+packed\b", "relaxed pace"),
        (r"\b(?:be\s+)?too\s+busy\b", "relaxed pace"),
        (r"\bhurried\b", "relaxed pace"),
    ]
    for pattern, replacement in _PACE_PATTERNS:
        if re.search(pattern, lower):
            return replacement
    return raw


def _extract_relevant_span(text: str, match_str: str, window: int = 80) -> str:
    """
    Extract a context window around the first occurrence of match_str in text.
    Returns the span of text (up to `window` chars before and after match).
    If match_str not found, returns empty string.
    """
    idx = text.lower().find(match_str.lower())
    if idx < 0:
        return ""
    start = max(0, idx - window)
    end = min(len(text), idx + len(match_str) + window)
    return text[start:end]


_PAST_TRIP_INDICATORS = frozenset({
    "last time", "previous trip", "past trip", "went to", "visited last",
    "came back from", "returned from", "their last", "earlier trip",
    "last year", "last month", "last summer", "last winter",
    "recently visited", "we went to",
})


def _is_past_trip_mention(sentence: str, dest_match: str) -> bool:
    """Check if a destination mention is in the context of a past trip (not current intent).

    Uses a narrow clause-level check: looks for past-trip indicators in the
    same clause as the destination (comma-delimited or sentence-delimited),
    not just a broad character window.
    """
    lowered = sentence.lower()
    match_idx = lowered.find(dest_match.lower())
    if match_idx < 0:
        return False

    # Extract the clause containing the destination.
    # A clause is bounded by commas, periods, semicolons, or the start/end of the text.
    # Search backward from the match for the nearest clause boundary.
    text_before_match = lowered[:match_idx]
    last_clause_boundary = 0
    for boundary_char in [',', '.', ';', '!', '?']:
        idx = text_before_match.rfind(boundary_char)
        if idx >= last_clause_boundary:
            last_clause_boundary = idx + 1

    clause_context = lowered[last_clause_boundary:match_idx + len(dest_match)]

    for indicator in _PAST_TRIP_INDICATORS:
        if indicator in clause_context:
            return True
    return False


def _is_likely_origin(text: str, dest_match: str) -> bool:
    """Check if a destination mention is actually the origin city.

    Looks for patterns like "from Bangalore" where Bangalore would be
    extracted as destination but is actually the origin.

    Also handles Hinglish/Odia postpositions: "Bangalore se", "Bangalore ru",
    "Bangalore side" where the postposition comes AFTER the city name.
    """
    lowered = text.lower()
    match_idx = lowered.find(dest_match.lower())
    if match_idx < 0:
        return False

    # English preposition before: "from Bangalore"
    context_before = lowered[max(0, match_idx - 10):match_idx]
    if _FROM_STARTING_DEPARTING_RE.search(context_before):
        return True

    # Hinglish/Odia postposition after: "Bangalore se", "Bangalore ru", "Bangalore side"
    context_after = lowered[match_idx + len(dest_match):match_idx + len(dest_match) + 15]
    if _SE_RU_SIDE_RE.search(context_after):
        return True

    return False


def _is_valid_destination_candidate(span: str, context: str) -> bool:
    """Type-check a destination candidate before accepting it.

    Rejects months, relation words, person-role words.
    Accepts known destinations and contextually likely place names.
    """
    lower = span.lower().strip()

    if lower in _MONTH_NAMES:
        return False

    if lower in _RELATION_WORDS:
        return False

    # Common stop words that should never be destinations
    if lower in _STOP_WORDS:
        return False

    if is_known_destination(lower):
        return True

    context_lower = context.lower()
    for verb in _DESTINATION_HINT_VERBS:
        if verb in context_lower and span[0].isupper():
            return is_known_city(lower) if lower not in _RELATION_WORDS else False

    return False


def _extract_destination_candidates(text: str) -> Tuple[List[str], str, Optional[str]]:
    """
    Returns (candidates, status, raw_match).
    status: "definite" | "semi_open" | "open"

    Past-trip destination mentions are excluded to prevent contamination
    of current destination intent.

    Extraction order matters: hedging patterns ("maybe", "or") are checked
    before the general destination regex so that hedging context is
    preserved in status and raw_match.
    """
    # Remove call-log metadata lines that frequently contain capitalized labels
    # (Caller, Referral, Pace, Budget, etc.) and pollute destination extraction.
    destination_text = "\n".join(
        line for line in text.splitlines()
        if not _DESTINATION_METADATA_LABELS_RE.match(line)
    )
    destination_text = "\n".join(
        line for line in text.splitlines()
        if not _DESTINATION_METADATA_LABELS_RE.match(line)
    )
    if not destination_text.strip():
        destination_text = text

    text_lower = destination_text.lower()
    candidates: List[str] = []
    excluded_by_past_trip: List[str] = []

    # Check for "or" pattern (semi-open)
    or_match = _OR_DESTINATION_RE.search(destination_text)
    if or_match:
        c1 = or_match.group(1).title()
        c2 = or_match.group(2).title()
        c1_ok = _is_valid_destination_candidate(c1, text)
        c2_ok = _is_valid_destination_candidate(c2, text)
        if (c1_ok or c2_ok) and not _is_past_trip_mention(destination_text, or_match.group(0)):
            valid = []
            if c1_ok:
                valid.append(c1)
            if c2_ok:
                valid.append(c2)
            if valid:
                return valid, "semi_open", or_match.group(0)

    # Check for "maybe" pattern (semi-open) — before general regex
    maybe_match = _MAYBE_RE.search(text_lower)
    if maybe_match:
        dest = maybe_match.group(1).title()
        if is_known_destination(dest):
            return [dest], "semi_open", maybe_match.group(0)

    # Check for "thinking about" / "perhaps" / hedging patterns (semi-open)
    hedging_match = _HEDGING_RE.search(text_lower)
    if hedging_match:
        dest = hedging_match.group(1).title()
        if is_known_destination(dest):
            return [dest], "semi_open", hedging_match.group(0)

    # Check for "somewhere with/for" (open)
    open_match = _SOMEWHERE_DEST_RE.search(text_lower)
    if open_match:
        return [], "open", open_match.group(0)

    # Check for "open to suggestions"
    if "open to suggestions" in text_lower or ("suggestions" in text_lower and "destination" in text_lower):
        return [], "open", "suggestions"

    # Single/multiple destination match — filter past-trip mentions AND origin patterns
    # Validate against geography database to filter out non-city capitalized words.
    # Also filter common pronouns and stop words that should never be destinations.
    _DESTINATION_STOP_WORDS = {"we", "i", "my", "our", "the", "this", "that", "it", "they", "he", "she", "us", "me", "him", "her"}

    raw_matches: List[str] = []
    matches = [m.group(0) for m in _DESTINATION_RE.finditer(destination_text)]
    if matches:
        seen = set()
        for m in matches:
            words = m.split()
            # Multi-word over-capture: try right-to-left truncation.
            # "Andaman Sri Lanka Bangalore" → fail → "Andaman Sri Lanka" → fail → "Andaman" → pass
            # If that hits, remaining words get their own chance.
            start = 0
            while start < len(words):
                best = None
                for end in range(len(words), start, -1):
                    candidate = " ".join(words[start:end])
                    title = candidate.title()
                    if (is_known_destination(title)
                        and title.lower() not in _MONTH_NAMES
                        and title.lower() not in _DESTINATION_STOP_WORDS):
                        best = (candidate, title, end)
                        break
                if best is None:
                    start += 1
                    continue
                candidate, title, end = best
                if title in seen:
                    start = end
                    continue
                if title.lower() in {"caller", "referral", "party", "pace", "budget", "interests", "follow-up", "follow_up", "toddler", "elderly", "promised", "not"}:
                    start = end
                    continue
                if _is_likely_origin(destination_text, candidate):
                    start = end
                    continue
                if _is_past_trip_mention(destination_text, candidate):
                    excluded_by_past_trip.append(title)
                else:
                    seen.add(title)
                    candidates.append(title)
                    raw_matches.append(candidate)
                start = end
        if len(candidates) == 1:
            return candidates, "definite", raw_matches[0]
        elif len(candidates) > 1:
            return candidates, "semi_open", ", ".join(raw_matches)

    # Fallback: context-gated lowercase destination extraction.
    # Only matches destinations appearing after travel verbs or before Hinglish/Odia
    # travel terms. Prevents false positives like "got" in "I got your number".
    if not candidates:
        seen_lower: Set[str] = set()
        for pattern in (_TRAVEL_VERB_DEST_RE, _HINGLISH_DEST_RE, _ORIGIN_DEST_RE):
            for match in pattern.finditer(text):
                dest = match.group(1)
                if not dest:
                    continue
                dest = dest.strip()
                dest_lower = dest.lower()
                if dest_lower in seen_lower:
                    continue
                title = dest.title()
                if dest_lower in _STOP_WORDS or dest_lower in _MONTH_NAMES:
                    seen_lower.add(dest_lower)
                    continue
                if (is_known_destination(title)
                    and not _is_likely_origin(destination_text, dest)
                    and not _is_past_trip_mention(destination_text, dest)):
                    candidates.append(title)
                    raw_matches.append(dest)
                    seen_lower.add(dest_lower)
        if len(candidates) >= 1:
            status = "definite" if len(candidates) == 1 else "semi_open"
            return candidates, status, ", ".join(raw_matches)

    return [], "open" if ("somewhere" in text_lower or "any" in text_lower) else "undecided", None


# =============================================================================
# SECTION 2: DATE EXTRACTION
# =============================================================================

def _extract_dates(text: str) -> Optional[Tuple[str, Optional[str], Optional[str], str]]:
    """
    Returns (window, start, end, confidence) or None.
    """
    text_lower = text.lower()

    # Exact ISO range
    iso_match = _DAY_RANGE_RE.search(text)
    if iso_match:
        raw = iso_match.group(0)
        return raw, iso_match.group(1), iso_match.group(2), "exact"

    # Day range: "9th to 14th Feb", "around 9th to 14th Feb 2025"
    day_range = _DAY_RANGE_TEXT_RE.search(text_lower)
    if day_range:
        start_day = day_range.group(1)
        end_day = day_range.group(2)
        month_str = day_range.group(3)
        explicit_year = day_range.group(4)
        year = explicit_year or _infer_year_from_context(text)
        month_num = _month_to_num(month_str)
        if month_num:
            start_iso = f"{year}-{month_num:02d}-{int(start_day):02d}"
            end_iso = f"{year}-{month_num:02d}-{int(end_day):02d}"
            raw = day_range.group(0).strip()
            return raw, start_iso, end_iso, "tentative"

    # "This weekend" / "this Friday"
    weekend_match = _THIS_WEEKEND_RE.search(text_lower)
    if weekend_match:
        raw = weekend_match.group(0)
        return raw, None, None, "flexible"

    # Month window: "June-July 2026", "March or April 2026", "March ya April 2026"
    month_window = _MONTH_WINDOW_RE.search(text_lower)
    if month_window:
        raw = month_window.group(0)
        return raw, None, None, "window"

    # Single month: "March 2026"
    single_month = _SINGLE_MONTH_RE.search(text_lower)
    if single_month:
        raw = single_month.group(0)
        return raw, None, None, "flexible"

    # "around March 2026", "sometime in May 2026"
    fuzzy = _FUZZY_MONTH_RE.search(text_lower)
    if fuzzy:
        raw = fuzzy.group(0)
        return raw, None, None, "flexible"

    return None


# =============================================================================
# SECTION 3: BUDGET EXTRACTION
# =============================================================================

def _extract_budget(text: str) -> Optional[Dict[str, Any]]:
    """
    Returns structured budget dict or None.
    """
    text_lower = text.lower()

    def _looks_like_date_token(raw_val: str) -> bool:
        token = raw_val.strip()
        return bool(
            re.fullmatch(r"\d{4}\s*[-/]\s*\d{1,2}(?:\s*[-/]\s*\d{1,2})?", token)
            or re.fullmatch(r"\d{4}-\d{2}-\d{2}", token)
        )

    # Look for budget-like patterns
    patterns = [
        # Explicit budget with numeric range and optional unit suffix.
        r"\bbudget\b(?:\s+(?:of|is|around|about|approx(?:imately)?))?\s*[:\-]?\s*(\d+(?:\.\d+)?\s*(?:-|–|—|\bto\b)\s*\d+(?:\.\d+)?\s*(?:l|k|lac|lakh|lakhs|thousand)?)\b",
        # Explicit budget with single value + unit.
        r"\bbudget\b(?:\s+(?:of|is|around|about|approx(?:imately)?))?\s*[:\-]?\s*(\d+(?:\.\d+)?\s*(?:l|k|lac|lakh|lakhs|thousand))\b",
        # Budget-like value with unit when budget keyword may be omitted.
        r"\b(?:around|about|approx(?:imately)?)\s+(\d+(?:\.\d+)?\s*(?:l|k|lac|lakh|lakhs|thousand))\b",
        # Plain number only accepted with explicit budget keyword.
        r"\bbudget\b(?:\s+(?:of|is|around|about|approx(?:imately)?))?\s*[:\-]?\s*(\d{4,})\b",
        # Bare number with L/K suffix (no keyword needed).
        r"\b((?:\d+(?:\.\d+)?)\s*(?:l|k|lac|lakh|lakhs|thousand))\b",
    ]
    for pat in patterns:
        m = re.search(pat, text_lower)
        if m:
            raw = m.group(1).strip()
            if _looks_like_date_token(raw):
                continue
            parsed = Normalizer.parse_budget(raw)
            parsed["raw_text"] = raw
            return parsed

    # "flexible" budget
    if _FLEXIBLE_BUDGET_RE.search(text_lower):
        return {"raw_text": "flexible", "min": None, "max": None, "currency": "INR"}

    return None


def _extract_date_flexibility(text: str) -> Optional[str]:
    text_lower = text.lower()
    if any(phrase in text_lower for phrase in [
        "dates are firm", "exact dates", "cannot change",
        "fixed dates", "no flexibility", "must travel on",
        "specific dates", "dates are fixed",
    ]):
        return "firm"
    if any(phrase in text_lower for phrase in [
        "flexible dates", "dates are flexible", "date flexible",
        "flexible on date", "anytime in", "flexible within",
        "can shift", "+/-", "+-", "plus minus", "give or take",
        "approximately", "roughly around", "some flexibility",
    ]):
        return "flexible"
    if any(phrase in text_lower for phrase in [
        "moderate flexibility", "slightly flexible",
    ]):
        return "moderate"
    return None


def _extract_budget_flexibility(text: str) -> str:
    if any(phrase in text.lower() for phrase in [
        "can stretch", "flexible budget", "budget is flexible",
        "if it's good", "can go higher", "flexible on budget",
    ]):
        return "stretch"
    return "unknown"


def _extract_budget_scope(text: str) -> str:
    text_lower = text.lower()
    if "per person" in text_lower or "per head" in text_lower:
        return "per_person"
    if "per night" in text_lower:
        return "per_night"
    if _TOTAL_GROUP_RE.search(text_lower):
        return "total"
    return "unknown"


def _extract_budget_stretch_max(text: str) -> Optional[int]:
    """
    Extract explicit maximum budget from stretch phrases.
    
    Case A: "2L, can stretch" → returns None (no explicit max)
    Case B: "2L, can stretch to 2.5L" → returns 250000
    
    Returns: max budget in base units (e.g., rupees), or None if not specified.
    """
    text_lower = text.lower()
    
    # Pattern: "stretch to/up to/until X" or "go up to X"
    patterns = [
        # "stretch to 2.5L", "can stretch up to 250000"
        r"(?:stretch|flexible|go)\s+(?:up\s+)?(?:to|until)\s*(\d+(?:\.\d+)?)\s*(l|lac|lakh|lakhs|k|thousand)?",
        # "can stretch to 2.5", "goes up to 3L"
        r"(?:to|up\s+to)\s*(\d+(?:\.\d+)?)\s*(l|lac|lakh|lakhs|k|thousand)?",
    ]
    
    for pat in patterns:
        match = re.search(pat, text_lower)
        if match:
            amount_str = match.group(1)
            unit = (match.group(2) or "").lower()
            
            try:
                amount = float(amount_str)
                
                # Apply unit multipliers
                if unit in ("l", "lac", "lakh", "lakhs"):
                    return int(amount * 100000)
                elif unit in ("k", "thousand"):
                    return int(amount * 1000)
                elif amount < 10000:  # Assume lakhs if reasonable
                    return int(amount * 100000)
                else:
                    return int(amount)
                    
            except (ValueError, IndexError):
                continue
    
    return None


# =============================================================================
# SECTION 4: PARTY EXTRACTION
# =============================================================================

def _extract_party(text: str) -> Dict[str, Any]:
    """
    Returns {party_size, party_composition, child_ages}.
    """
    composition: Dict[str, int] = {}
    child_ages: List[float] = []
    text_lower = text.lower()

    # Family composition from natural language
    _FAMILY_PATTERNS = [
        (r"\b(?:me|myself|i)\b", "adults", 1),
        (r"\bmy\s+(?:wife|husband|spouse)\b", "adults", 1),
        (r"\bmy\s+(?:parents|mom\s+and\s+dad|mum\s+and\s+dad)\b", "adults", 2),
        (r"\bmy\s+(?:mother|father|mom|mum|dad)\b", "adults", 1),
        (r"\bmy\s+(?:grandparents?)\b", "elderly", 1),
    ]
    for pattern, group, count in _FAMILY_PATTERNS:
        if re.search(pattern, text_lower):
            composition[group] = composition.get(group, 0) + count

    # Child with decimal age: "1.7 year old kid", "2.5yr old"
    dec_age = re.search(r"(\d+\.?\d*)\s*(?:years?|yr|y)[\s-]*(?:old|aged?)\s+(?:kid|child|baby|toddler|son|daughter)", text_lower)
    if dec_age:
        composition["children"] = composition.get("children", 0) + 1
        child_ages.append(float(dec_age.group(1)))
    elif not dec_age:
        # Singular child without number: "our kid", "a toddler", or bare "bachha"
        singular_child = re.search(r"\b(?:(?:my|our|a)\s+)?(?:kid|child|baby|toddler|son|daughter|bachha)\b", text_lower)
        if singular_child:
            composition["children"] = composition.get("children", 0) + 1
            if not child_ages:
                if "toddler" in singular_child.group(0):
                    child_ages.append(2.0)
                elif "baby" in singular_child.group(0):
                    child_ages.append(0.5)
                else:
                    child_ages.append(5.0)

    # Adults
    adult_match = _ADULTS_RE.search(text_lower)
    if adult_match:
        composition["adults"] = int(adult_match.group(1))

    # Children — match "2 children" or bare "child/kid" or Hinglish "bachhe"/"bache"/"baccha"
    child_match = re.search(r"(?:(\d+)\s+)?(?:kids?|children?|child|bachhe|bache|baccha)", text_lower)
    if child_match and child_match.group(1):
        composition["children"] = int(child_match.group(1))
    # Try to extract ages: "kids ages 8 and 12", "children aged 5, 7", "child age 3"
    ages_match = re.search(
        r"(?:kids?|children?|child|ages?|bachhe|bache|baccha)\s+(?:ages?\s+)?(\d+(?:\s+(?:and|,)\s*\d+)*)",
        text_lower,
    )
    if ages_match:
        found_ages = [int(a) for a in re.findall(r"\d+", ages_match.group(1))]
        child_ages.extend(found_ages)

    # Toddler — "toddler age 2", "a toddler", "toddlers"
    has_toddler = bool(_TODDLER_RE.search(text_lower))
    if has_toddler:
        if "toddlers" not in composition and "children" not in composition:
            composition["children"] = 1
        if 0 not in child_ages and not any(a < 3 for a in child_ages):
            toddler_age_match = _TODDLER_AGE_RE.search(text_lower)
            child_ages.append(int(toddler_age_match.group(1)) if toddler_age_match else 2)

    # Elderly — "1 elderly", "an elderly grandmother", "grandma age 78", "senior"
    elderly_match = _ELDERLY_RE.search(text_lower)
    if elderly_match:
        composition["elderly"] = int(elderly_match.group(1)) if elderly_match.group(1) else 1
    elif _ELDERLY_RE.search(text_lower):
        composition.setdefault("elderly", 1)

    # Total party size
    party_size = sum(composition.values())

    # Prefer explicit stated headcount when present (e.g., "6 pax", "6 people").
    # If explicit and inferred counts conflict, explicit caller-provided count wins.
    explicit_size_match = _PEOPLE_RE.search(text_lower)
    explicit_party_size = int(explicit_size_match.group(1)) if explicit_size_match else None
    if explicit_party_size and explicit_party_size > 0:
        party_size = explicit_party_size

    # Fallback: "family of N", "group of N", "N people"
    if party_size == 0:
        size_match = re.search(
            r"(?:family|group)\s+(?:of\s+)?(\d+)", text_lower
        )
        if size_match:
            party_size = int(size_match.group(1))
        else:
            pax_match = re.search(r"(\d+)\s+(?:people|persons|pax|travelers)", text_lower)
            if pax_match:
                party_size = int(pax_match.group(1))

    return {
        "party_size": party_size,
        "party_composition": composition,
        "child_ages": child_ages,
    }


# =============================================================================
# SECTION 5: TRIP INTENT EXTRACTION
# =============================================================================

def _extract_trip_intent(text: str) -> Dict[str, Any]:
    results: Dict[str, Any] = {}

    text_lower = text.lower()

    # Trip purpose
    purpose_patterns = {
        "pilgrimage": r"\b(pilgrimage|yatra|char dham|temple\s+visit)\b",
        "family leisure": r"\b(family\s+(?:leisure|vacation|holiday|trip))\b",
        "honeymoon": r"\b(honeymoon|romantic)\b",
        "business": r"\b(business|conference|meeting)\b",
        "adventure": r"\b(adventure|trekking|rafting)\b",
        "beach": r"\b(beach\s+(?:vacation|holiday|trip))\b",
        "cultural": r"\b(cultural|heritage|sightseeing)\b",
    }
    for purpose, pattern in purpose_patterns.items():
        if re.search(pattern, text_lower):
            results["trip_purpose"] = purpose
            break

    if "trip_purpose" not in results:
        _LEISURE_HINTS = {"universal studios", "disney", "sentosa", "nature park",
                          "theme park", "aquarium", "zoo", "safari", "gardens",
                          "sightseeing", "attractions", "landmarks", "tourist"}
        _FAMILY_HINTS = {"kid", "kids", "child", "children", "toddler", "baby",
                         "parents", "family", "wife", "husband",
                         "bachhe", "bache", "baccha"}
        hints_found = sum(1 for h in _LEISURE_HINTS if h in text_lower)
        family_found = any(h in text_lower for h in _FAMILY_HINTS)
        if hints_found >= 1 and family_found:
            results["trip_purpose"] = "family leisure"
        elif hints_found >= 1:
            results["trip_purpose"] = "leisure"

    # Trip style
    style_patterns = {
        "luxury resort": r"\b(5[\s-]*star|luxury\s+resort|luxury)\b",
        "backpacking": r"\b(backpacking|budget\s+travel)\b",
        "cultural": r"\b(cultural|heritage|historical)\b",
        "adventure": r"\b(adventure|thrill)\b",
    }
    for style, pattern in style_patterns.items():
        if re.search(pattern, text_lower):
            results["trip_style"] = style
            break

    # Hotel preferences
    hotel_match = re.search(r"((?:5|4|3)[\s-]*star\s+(?:resort|hotel)?(?:[^.]*?))", text_lower)
    if hotel_match:
        results["hotel_preferences"] = hotel_match.group(1).strip()

    # Meal preferences
    meal_match = re.search(r"((?:vegetarian|vegan|jain|halal|kosher|non(?:-\s*)?veg|food\s+preferences)[^.]*?)", text_lower)
    if meal_match:
        results["meal_preferences"] = meal_match.group(1).strip()

    # Constraints
    hard = []
    no_match = re.findall(r"(?:no|don'?t\s+(?:want|need|book)|avoid|never)\s+([^.,]+)", text_lower)
    for constraint in no_match:
        normalized = _normalize_constraint(constraint.strip())
        if normalized:
            hard.append(normalized)
    if hard:
        results["hard_constraints"] = hard

    soft = []
    want_match = re.findall(r"(?:want|prefer|like|interested\s+in)\s+([^.,]+)", text_lower)
    for pref in want_match:
        candidate = pref.strip()
        normalized = _normalize_constraint(candidate)
        # Guard against negation bleed-through from phrases like
        # "don't want it rushed", which should stay a hard constraint.
        if normalized == "relaxed pace":
            continue
        soft.append(candidate)
    if soft:
        results["soft_preferences"] = soft

    # Trip priorities — explicit must-haves and preference signals
    priorities: List[str] = []

    _MUST_HAVE_RE = re.compile(
        r"\b(?:must[-\s]*(?:have|visit|see|do)|must\s+(?:have|visit|see|do)|can'?t\s+miss)\s+([^.,;]+)",
        re.IGNORECASE,
    )
    for m in _MUST_HAVE_RE.finditer(text):
        priorities.append(m.group(1).strip())

    _PRIORITY_SIGNALS = {
        "kid-friendly": r"\b(kid[-\s]?friendly|family[-\s]?friendly|child[-\s]?friendly|toddler[-\s]?friendly)\b",
        "luxury experience": r"\b(luxury\s+(?:experience|stay|resort|hotel)|premium\s+(?:experience|stay))\b",
        "budget conscious": r"\b(budget[-\s]?(?:conscious|friendly|travel)|cheapest?\s+(?:option|flight|stay))\b",
        "beach access": r"\b(beach[-\s]?(?:front|side|access|resort)|sea[-\s]?facing|ocean[-\s]?view)\b",
        "direct flights": r"\b(direct\s+flights?|non[-\s]?stop|no\s+layover)\b",
        "vegetarian food": r"\b(vegetarian|vegan|jain\s+food|halal\s+food|pure\s+veg)\b",
        "adventure activities": r"\b(adventure\s+(?:activities|sports)|trekking|rafting|paragliding|scuba|snorkeling)\b",
        "relaxed pace": r"\b(relaxed\s+pace|slow\s+pace|leisurely|not\s+rushed|chilled?)\b",
        "quick trip": r"\b(quick\s+trip|short\s+trip|weekend\s+getaway|tight\s+schedule)\b",
        "cultural experience": r"\b(cultural\s+(?:experience|tour|visit)|heritage|temple\s+visit|pilgrimage)\b",
        "honeymoon special": r"\b(honeymoon\s+(?:special|package|suite)|romantic\s+(?:dinner|getaway|setup))\b",
        "accessibility needs": r"\b(accessible|wheelchair[-\s]?(?:friendly|accessible)|senior[-\s]?friendly|elderly)\b",
    }
    for label, pattern in _PRIORITY_SIGNALS.items():
        if re.search(pattern, text_lower):
            priorities.append(label)

    if priorities:
        results["trip_priorities"] = priorities

    _ATTRACTION_RE = re.compile(
        r"\b((?:Universal\s+Studios|Sentosa|Gardens\s+by\s+the\s+Bay|Disney|Sea\s+World|Legoland|Marina\s+Bay|Sanctuary|National\s+Park|Nature\s+Park|Safari|Aquarium|Zoo|Waterpark|Theme\s+Park)\b)"
        , re.IGNORECASE
    )
    attractions = [m.group(1).strip() for m in _ATTRACTION_RE.finditer(text)]
    if attractions:
        results.setdefault("soft_preferences", [])
        results["soft_preferences"].extend(attractions)

    return results


# =============================================================================
# SECTION 6: OWNER / AGENCY CONTEXT EXTRACTION
# =============================================================================

def _extract_owner_context(text: str) -> Dict[str, Any]:
    results: Dict[str, Any] = {}
    text_lower = text.lower()

    # Owner constraints
    constraints: List[OwnerConstraint] = []

    # "never use X", "don't book X" → internal_only
    never_matches = re.findall(r"\bnever\s+(?:book|use|suggest|recommend)\s+([^.,]+)", text_lower)
    for c in never_matches:
        constraints.append(OwnerConstraint(text=c.strip(), visibility="internal_only"))

    # "avoid X" → internal_only
    avoid_matches = re.findall(r"\bavoid\s+([^.,]+)", text_lower)
    for c in avoid_matches:
        constraints.append(OwnerConstraint(text=c.strip(), visibility="internal_only"))

    # "family prefers X" → traveler_safe_transformable
    prefer_matches = re.findall(r"(?:family|they|customer)\s+(?:always\s+)?(?:prefers?|likes?)\s+([^.,]+)", text_lower)
    for c in prefer_matches:
        constraints.append(OwnerConstraint(text=c.strip(), visibility="traveler_safe_transformable"))

    if constraints:
        results["owner_constraints"] = constraints

    # Agency notes
    if any(phrase in text_lower for phrase in [
        "past customer", "they've been", "previously went", "last time",
        "repeat customer", "returning customer",
    ]):
        notes_match = re.search(r"((?:past|previous|last\s+time)[^.,]+)", text_lower)
        if notes_match:
            results["agency_notes"] = notes_match.group(1).strip()
        else:
            results["agency_notes"] = "repeat customer context detected"

    # Customer ID / repeat customer hook
    cust_match = re.search(r"(?:customer|client)\s+(?:id|name|ref)[:\s]+(\w+)", text_lower)
    if cust_match:
        results["customer_id"] = cust_match.group(1)

    return results


# =============================================================================
# SECTION 7: MULTI-PARTY EXTRACTION
# =============================================================================

def _extract_sub_groups(text: str) -> Dict[str, SubGroup]:
    sub_groups: Dict[str, SubGroup] = {}

    # Pattern: "Family A: 4 people, 3L budget"
    family_patterns = re.findall(
        r"((?:family|group)\s+\w+)\s*[:;]?\s*(\d+)\s*(?:people|persons|pax)"
        r"(?:.*?budget.*?(\d+(?:\.\d+)?)\s*([LlKk]))?",
        text, re.IGNORECASE,
    )
    for label, size, budget_val, budget_unit in family_patterns:
        group_id = label.lower().replace(" ", "_")
        budget_int = None
        if budget_val and budget_unit:
            parsed = Normalizer.parse_budget(f"{budget_val}{budget_unit}")
            budget_int = parsed.get("min") or parsed.get("max")
        sub_groups[group_id] = SubGroup(
            group_id=group_id,
            label=label,
            size=int(size),
            budget_share=budget_int,
        )

    return sub_groups


# =============================================================================
# SECTION 8: OPERATING MODE CLASSIFIER
# =============================================================================

def _classify_operating_mode(texts: List[str]) -> str:
    for text in texts:
        t = text.lower()
        if any(kw in t for kw in ["emergency", "urgent", "medical", "hospital", "evacuate", "chest pain"]):
            return "emergency"
        if any(kw in t for kw in ["cancel", "cancellation", "refund"]):
            return "cancellation"
        if any(kw in t for kw in ["review quote", "check this quote", "audit", "what did we send"]):
            return "audit"
        if any(kw in t for kw in ["follow up", "no response", "ghost", "not responding"]):
            return "follow_up"
        if any(kw in t for kw in ["post trip", "how was", "feedback", "review request"]):
            return "post_trip"
        if any(kw in t for kw in ["owner review", "quote disaster", "margin erosion"]):
            return "owner_review"
        if any(kw in t for kw in ["coordinat", "3 families", "multiple families"]):
            return "coordinator_group"
    return "normal_intake"


def _extract_feedback(text: str) -> Optional[Dict[str, Any]]:
    """
    Extract satisfaction rating (1-5) and feedback notes.
    """
    text_lower = text.lower()
    
    rating = None
    # 5/5, 4/5, 5 out of 5
    score_match = re.search(r"(\d)\s*(?:/|out of)\s*5", text_lower)
    if score_match:
        rating = int(score_match.group(1))
    
    # 5 star, 4 stars
    if not rating:
        star_match = re.search(r"(\d)\s*star", text_lower)
        if star_match:
            rating = int(star_match.group(1))
            
    # Keywords: "great", "excellent" (5), "bad", "terrible" (1)
    if not rating:
        if any(kw in text_lower for kw in ["excellent", "amazing", "perfect", "loved it"]):
            rating = 5
        elif any(kw in text_lower for kw in ["good", "great", "nice"]):
            rating = 4
        elif any(kw in text_lower for kw in ["okay", "average", "fine"]):
            rating = 3
        elif any(kw in text_lower for kw in ["poor", "bad", "disappointed"]):
            rating = 2
        elif any(kw in text_lower for kw in ["terrible", "awful", "horrible"]):
            rating = 1
            
    if rating:
        # Clamp between 1 and 5
        rating = max(1, min(5, rating))
        
    return {
        "rating": rating,
        "notes": text.strip() if rating else None,
        "is_simulated": False
    }


# =============================================================================
# SECTION 9: PASSPORT / VISA EXTRACTION
# =============================================================================

def _extract_passport_visa(text: str) -> Dict[str, Any]:
    """
    Extract passport/visa status as per-traveler structured maps.
    Format: {"adult_1": {"status": "valid_until_2029"}, "adult_2": {"status": "expired"}}
    If no per-traveler info is available, uses "all" as key.
    """
    results: Dict[str, Any] = {}
    text_lower = text.lower()

    # Passport status extraction (per-traveler)
    if "passport" in text_lower:
        passport_status: Dict[str, Any] = {}

        # Check for per-traveler mentions: "adult 1 passport valid until March 2029"
        per_traveler = re.findall(
            r"(adult|child|elderly)\s*(\d+)\s+passport\s+(expired|valid|renew)",
            text_lower,
        )
        if per_traveler:
            for traveler_type, num, status_word in per_traveler:
                key = f"{traveler_type}_{num}"
                detail: Dict[str, Any] = {"status": status_word}
                # Try to extract expiry date
                date_match = re.search(
                    rf"{traveler_type}\s*{num}[^.]*?(?:until|till|thru|expir)\s+([A-Za-z]+\s+\d{{4}})",
                    text_lower,
                )
                if date_match:
                    detail["expires"] = date_match.group(1)
                passport_status[key] = detail
        else:
            # No per-traveler detail — use "all" key
            if "expired" in text_lower:
                exp_match = re.search(r"expired\s+([A-Za-z]+\s+\d{4})", text_lower)
                status = {"status": "expired"}
                if exp_match:
                    status["expired_date"] = exp_match.group(1)
            elif "valid" in text_lower:
                val_match = re.search(r"valid\s+(?:until|till|thru)\s+([A-Za-z]+\s+\d{4})", text_lower)
                status = {"status": "valid"}
                if val_match:
                    status["valid_until"] = val_match.group(1)
            elif "renew" in text_lower or "renewal" in text_lower:
                status = {"status": "renewal_in_progress"}
            else:
                status = {"status": "unknown"}
            passport_status["all"] = status

        results["passport_status"] = passport_status

    # Visa status extraction
    if "visa" in text_lower:
        if "required" in text_lower or "need visa" in text_lower:
            results["visa_status"] = {"requirement": "required", "status": "not_applied"}
        elif "approved" in text_lower or "got visa" in text_lower:
            results["visa_status"] = {"requirement": "required", "status": "approved"}
        elif "not required" in text_lower or "no visa" in text_lower:
            results["visa_status"] = {"requirement": "not_required"}
        else:
            results["visa_status"] = {"requirement": "unknown"}

    return results


VISA_PASSPORT_CONCERN_TERMS = (
    "visa", "passport", "passports", "expiry", "expired", "expire",
    "renew", "renewal", "validity", "document", "documents", "immigration",
)


def _extract_passport_visa_gated(text: str, stage: str) -> Dict[str, Any]:
    """Stage-gated passport/visa extraction.

    proposal/booking: full per-traveler extraction via _extract_passport_visa().
    discovery/shortlist: lightweight boolean signal only, omitted when no concern
    terms are found.
    """
    if stage in ("proposal", "booking"):
        return _extract_passport_visa(text)
    text_lower = text.lower()
    if any(term in text_lower for term in VISA_PASSPORT_CONCERN_TERMS):
        return {"visa_concerns_present": True}
    return {}


# =============================================================================
# SECTION 10: EXISTING ITINERARY / TRAVELER PLAN
# =============================================================================

def _extract_traveler_plan(text: str) -> Dict[str, Any]:
    results: Dict[str, Any] = {}
    text_lower = text.lower()

    if "already booked" in text_lower:
        if "hotel" in text_lower and "flight" not in text_lower:
            results["traveler_plan"] = "has_hotel_only"
        elif "flight" in text_lower:
            results["traveler_plan"] = "has_flights_booked"
        else:
            results["traveler_plan"] = "has_existing_booking"
    elif "flights booked" in text_lower:
        results["traveler_plan"] = "has_flights_booked"
    elif "hotel booked" in text_lower or "hotel booked" in text_lower:
        results["traveler_plan"] = "has_hotel_only"
    elif "have an itinerary" in text_lower or "existing itinerary" in text_lower:
        itin_match = re.search(r"((?:have|existing|current)\s+(?:an\s+)?itinerary[^.]*\.)", text_lower)
        if itin_match:
            results["existing_itinerary"] = itin_match.group(1).strip()
            results["traveler_plan"] = "has_existing_itinerary"
        else:
            results["traveler_plan"] = "nothing_booked"
    else:
        results["traveler_plan"] = "nothing_booked"

    return results


# =============================================================================
# SECTION 11: EXTRACTION PIPELINE (v0.2)
# =============================================================================

class ExtractionPipeline:
    """
    The core compiler: raw SourceEnvelope(s) → CanonicalPacket v0.2.

    Entry point: ``pipeline.extract([envelope])`` → CanonicalPacket.

    Pattern-based (not LLM) extraction that populates 30+ fact fields.
    Handles freeform text, structured JSON, and hybrid inputs.
    After extraction, computes derived signals and identifies unknowns.
    """

    def __init__(self, model_client=None):
        self.model_client = model_client

    def extract(self, envelopes: List[SourceEnvelope], stage: str = "discovery") -> CanonicalPacket:
        packet = CanonicalPacket(
            packet_id=f"pkt_{uuid.uuid4().hex[:8]}",
        )

        # Collect all text for operating mode classification
        all_texts = []

        for envelope in envelopes:
            packet.source_envelope_ids.append(envelope.envelope_id)
            text = ""
            if isinstance(envelope.content, str):
                text = envelope.content
            elif isinstance(envelope.content, dict):
                text = str(envelope.content.get("text", ""))
            all_texts.append(text)

            if envelope.content_type == "freeform_text":
                self._extract_from_freeform(envelope, packet, stage=stage)
            elif envelope.content_type == "structured_json":
                self._extract_from_structured(envelope, packet)
            elif envelope.content_type == "hybrid":
                self._extract_from_hybrid(envelope, packet, stage=stage)

        # Set operating mode (top-level, NOT in facts)
        packet.operating_mode = _classify_operating_mode(all_texts)

        # Extraction feedback loop signals
        if packet.operating_mode == "post_trip":
            combined_text = "\n".join(all_texts)
            packet.feedback = _extract_feedback(combined_text)

        # After extraction, compute derived signals
        self._compute_derived_signals(packet)

        # Identify unknowns (MVB fields not present)
        self._identify_unknowns(packet)

        return packet

    def _make_slot(self, value: Any, confidence: float, authority: str,
                    excerpt: str, envelope_id: str, extraction_mode: str = "direct_extract",
                    maturity: Optional[str] = None, notes: Optional[str] = None) -> Slot:
        return Slot(
            value=value,
            confidence=confidence,
            authority_level=authority,
            extraction_mode=extraction_mode,
            evidence_refs=[EvidenceRef(
                envelope_id=envelope_id,
                evidence_type="text_span",
                excerpt=excerpt,
            )],
            maturity=maturity,
            notes=notes,
        )

    def _extract_from_freeform(self, envelope: SourceEnvelope, packet: CanonicalPacket, stage: str = "discovery") -> None:
        text = envelope.content
        text_lower = text.lower()
        eid = envelope.envelope_id

        # --- DESTINATION ---
        dest_candidates, dest_status, dest_raw = _extract_destination_candidates(text)
        existing_dest_slot = packet.facts.get("destination_candidates")
        existing_candidates = []
        if existing_dest_slot is not None:
            existing_value = getattr(existing_dest_slot, "value", None)
            if isinstance(existing_value, list):
                existing_candidates = [v for v in existing_value if v]
            elif existing_value:
                existing_candidates = [existing_value]
        if dest_candidates or dest_status in ("open", "undecided"):
            # Prevent weaker later envelopes (often owner/internal notes) from
            # downgrading an already-explicit destination to []/undecided.
            if (
                not dest_candidates
                and dest_status in ("open", "undecided")
                and len(existing_candidates) > 0
            ):
                pass
            else:
                packet.set_fact("destination_candidates", self._make_slot(
                    dest_candidates if dest_candidates else [],
                    0.7 if dest_status == "semi_open" else 0.5,
                    AuthorityLevel.EXPLICIT_USER,
                    dest_raw or "not specified",
                    eid,
                ))
                packet.set_fact("destination_status", self._make_slot(
                    dest_status, 0.8, AuthorityLevel.EXPLICIT_USER,
                    "Derived from destination text", eid,
                ))
            # Check for ambiguities on the ORIGINAL source phrasing, not just extracted values.
            # Using the source span catches natural-language vagueness that
            # normalization can lose (e.g., "maybe somewhere like Andaman?").
            if dest_raw:
                for amb in Normalizer.detect_ambiguities("destination_candidates", dest_raw):
                    packet.add_ambiguity(amb)
            # Also run ambiguity detection on the relevant source text span
            # around the destination mention for richer detection.
            dest_context = _extract_relevant_span(text, dest_raw or "", window=80)
            if dest_context and dest_context != dest_raw:
                for amb in Normalizer.detect_ambiguities("destination_candidates", dest_context):
                    # Avoid duplicate ambiguity types
                    if not any(a.ambiguity_type == amb.ambiguity_type for a in packet.ambiguities):
                        packet.add_ambiguity(amb)

            # Value-structural ambiguity synthesis:
            # If destination_candidates has 2+ items but no unresolved_alternatives
            # ambiguity was flagged (e.g., text-pattern missed it, or packet
            # constructed from structured import), synthesize one from the value
            # structure itself. A multi-element destination list IS the ambiguity.
            if dest_candidates and len(dest_candidates) >= 2:
                if not any(
                    a.ambiguity_type == "unresolved_alternatives"
                    and a.field_name == "destination_candidates"
                    for a in packet.ambiguities
                ):
                    packet.add_ambiguity(Ambiguity(
                        field_name="destination_candidates",
                        ambiguity_type="unresolved_alternatives",
                        raw_value=" or ".join(dest_candidates),
                        confidence=0.8,
                    ))

        # --- DATES ---
        date_result = _extract_dates(text)
        if date_result:
            raw, start, end, conf = date_result
            packet.set_fact("date_window", self._make_slot(
                raw, 0.8, AuthorityLevel.EXPLICIT_USER, raw, eid,
            ))
            if start:
                packet.set_fact("date_start", self._make_slot(
                    start, 0.95, AuthorityLevel.EXPLICIT_USER, raw, eid,
                ))
            if end:
                packet.set_fact("date_end", self._make_slot(
                    end, 0.95, AuthorityLevel.EXPLICIT_USER, raw, eid,
                ))
            packet.set_fact("date_confidence", self._make_slot(
                conf, 0.9, AuthorityLevel.EXPLICIT_USER,
                "Derived from date parsing", eid,
            ))

        # --- BUDGET ---
        budget_result = _extract_budget(text)
        if budget_result:
            packet.set_fact("budget_raw_text", self._make_slot(
                budget_result.get("raw_text", text), 0.8,
                AuthorityLevel.EXPLICIT_USER, budget_result.get("raw_text", ""), eid,
            ))
            if budget_result.get("min") is not None:
                packet.set_fact("budget_min", self._make_slot(
                    budget_result["min"], 0.9, AuthorityLevel.EXPLICIT_USER,
                    budget_result.get("raw_text", ""), eid,
                ))
            if budget_result.get("max") is not None:
                packet.set_fact("budget_max", self._make_slot(
                    budget_result["max"], 0.9, AuthorityLevel.EXPLICIT_USER,
                    budget_result.get("raw_text", ""), eid,
                ))
            packet.set_fact("budget_currency", self._make_slot(
                "INR", 0.9, AuthorityLevel.EXPLICIT_USER,
                "Default currency", eid,
            ))

        date_flex = _extract_date_flexibility(text)
        if date_flex is not None:
            packet.set_fact("date_flexibility", self._make_slot(
                date_flex, 0.75, AuthorityLevel.EXPLICIT_USER,
                date_flex, eid,
            ))

        budget_flex = _extract_budget_flexibility(text)
        if budget_flex != "unknown":
            packet.set_fact("budget_flexibility", self._make_slot(
                budget_flex, 0.85, AuthorityLevel.EXPLICIT_USER,
                budget_flex, eid,
            ))

        budget_scope = _extract_budget_scope(text)
        if budget_scope != "unknown":
            packet.set_fact("budget_scope", self._make_slot(
                budget_scope, 0.7, AuthorityLevel.EXPLICIT_USER,
                "Derived from budget context", eid,
            ))

        # Check for budget stretch ambiguity and extract explicit max if present
        if "stretch" in text_lower or "flexible" in text_lower:
            # Use full text for stretch extraction (don't truncate at punctuation)
            stretch_text = text_lower
            
            # Extract stretch ambiguity
            for amb in Normalizer.detect_ambiguities("budget_flexibility", stretch_text):
                packet.add_ambiguity(amb)
            
            # Extract explicit stretch maximum (Case B: "to 2.5L")
            stretch_max = _extract_budget_stretch_max(stretch_text)
            if stretch_max is not None:
                packet.set_fact("budget_soft_ceiling", self._make_slot(
                    stretch_max, 0.85, AuthorityLevel.EXPLICIT_USER,
                    stretch_text, eid,
                ))

        # --- PARTY ---
        party = _extract_party(text)
        if party["party_size"] > 0:
            packet.set_fact("party_size", self._make_slot(
                party["party_size"], 0.9, AuthorityLevel.EXPLICIT_USER,
                str(party["party_size"]), eid,
            ))
        if party["party_composition"]:
            packet.set_fact("party_composition", self._make_slot(
                party["party_composition"], 0.85, AuthorityLevel.EXPLICIT_USER,
                str(party["party_composition"]), eid,
            ))
        if party["child_ages"]:
            packet.set_fact("child_ages", self._make_slot(
                party["child_ages"], 0.85, AuthorityLevel.EXPLICIT_USER,
                str(party["child_ages"]), eid,
            ))

        # --- ORIGIN ---
        # Bounded extraction: limit to ~3 words after "from/starting/departing"
        # to prevent conversational spillover into unrelated sentence parts.
        airport_match = re.search(r"\b(from|starting|departing)\s+([A-Z]{3})\b", text)
        if airport_match:
            city, was_normalized = Normalizer.normalize_city(airport_match.group(2))
            mode = ExtractionMode.NORMALIZED if was_normalized else ExtractionMode.DIRECT_EXTRACT
            packet.set_fact("origin_city", self._make_slot(
                city, 0.95, AuthorityLevel.EXPLICIT_USER,
                airport_match.group(0), eid, extraction_mode=mode,
            ))
        else:
            # Match max 3 words after "from" before hitting a delimiter
            # Delimiters: to, comma, period, newline, or sentence-ending patterns
            origin_match = re.search(
                r"\b(from|starting|departing)\s+((?:[A-Za-z]+\s*){1,3}?)(?:\bto\b|,|\.|\$|\n)",
                text,
                re.IGNORECASE,
            )
            if origin_match:
                city_raw = origin_match.group(2).strip()
                # Validate as a plausible city name using geography.py
                # NOTE: A city being in destination lists doesn't disqualify it as origin.
                # People can take trips FROM destinations. What matters is the pattern.
                city, was_normalized = Normalizer.normalize_city(city_raw)
                mode = ExtractionMode.NORMALIZED if was_normalized else ExtractionMode.DIRECT_EXTRACT

                # Basic validation: must be a known city (or close enough) or multi-word
                # Multi-word names like "New York" should be accepted even if not in city DB
                if is_known_city(city) or len(city_raw.split()) > 1:
                    packet.set_fact("origin_city", self._make_slot(
                        city, 0.9, AuthorityLevel.EXPLICIT_USER,
                        origin_match.group(0), eid, extraction_mode=mode,
                    ))

        # Hinglish/Odia origin: "Bangalore se", "Bangalore ru", "Bangalore side"
        # Only try if origin not already set.
        # Single-word city only (multi-word like "New York se" is unlikely in Hinglish).
        if not packet.facts.get("origin_city"):
            postposition_match = re.search(
                r"\b([A-Za-z]+)\s+(se|ru|side)\b",
                text,
                re.IGNORECASE,
            )
            if postposition_match:
                city_raw = postposition_match.group(1).strip()
                city, was_normalized = Normalizer.normalize_city(city_raw)
                mode = ExtractionMode.NORMALIZED if was_normalized else ExtractionMode.DIRECT_EXTRACT
                if is_known_city(city) or len(city_raw.split()) > 1:
                    packet.set_fact("origin_city", self._make_slot(
                        city, 0.8, AuthorityLevel.EXPLICIT_USER,
                        postposition_match.group(0), eid, extraction_mode=mode,
                    ))

        # --- MOBILITY / MEDICAL CONSTRAINTS ---
        mobility_match = re.search(r"((?:can'?t\s+walk|wheelchair|mobility|slow\s+pace|limited\s+mobility|ground\s+floor)[^.,]*)", text_lower)
        if mobility_match:
            packet.set_fact("mobility_constraints", self._make_slot(
                mobility_match.group(1).strip(), 0.9, AuthorityLevel.EXPLICIT_USER,
                mobility_match.group(1), eid,
            ))

        medical_match = re.search(r"((?:hypertension|diabetes|heart\s+condition|medical\s+condition|medical\s+issue)[^.,]*)", text_lower)
        if medical_match:
            packet.set_fact("medical_constraints", self._make_slot(
                medical_match.group(1).strip(), 0.9, AuthorityLevel.EXPLICIT_USER,
                medical_match.group(1), eid,
            ))

        # --- TRIP INTENT ---
        intent = _extract_trip_intent(text)
        for field_name, value in intent.items():
            if isinstance(value, list):
                packet.set_fact(field_name, self._make_slot(
                    value, 0.8, AuthorityLevel.EXPLICIT_USER,
                    str(value), eid,
                ))
            else:
                packet.set_fact(field_name, self._make_slot(
                    value, 0.8, AuthorityLevel.EXPLICIT_USER,
                    value, eid,
                ))

        # --- OWNER / AGENCY CONTEXT ---
        owner_ctx = _extract_owner_context(text)
        for field_name, value in owner_ctx.items():
            if field_name == "owner_constraints" and isinstance(value, list):
                packet.set_fact("owner_constraints", self._make_slot(
                    value, 0.9, AuthorityLevel.EXPLICIT_OWNER,
                    "Owner constraints from text", eid,
                ))
            else:
                packet.set_fact(field_name, self._make_slot(
                    value, 0.8, AuthorityLevel.EXPLICIT_OWNER,
                    str(value), eid,
                ))

        # --- SUB GROUPS ---
        sub_groups = _extract_sub_groups(text)
        if sub_groups:
            packet.set_fact("sub_groups", self._make_slot(
                sub_groups, 0.8, AuthorityLevel.EXPLICIT_OWNER,
                "Sub-groups from text", eid,
            ))

        # --- COORDINATOR ---
        coord_match = re.search(r"((?:Mr|Mrs|Ms|Dr)\.\s+\w+)\s+(?:coordinat)", text, re.IGNORECASE)
        if coord_match:
            packet.set_fact("coordinator_id", self._make_slot(
                coord_match.group(1), 0.8, AuthorityLevel.EXPLICIT_OWNER,
                coord_match.group(0), eid,
            ))

        # --- PASSPORT / VISA (stage-gated) ---
        pv = _extract_passport_visa_gated(text, stage)
        if stage in ("proposal", "booking"):
            for field_name, value in pv.items():
                packet.set_fact(field_name, self._make_slot(
                    value, 0.9, AuthorityLevel.EXPLICIT_USER,
                    value, eid,
                ))
        elif pv:
            for field_name, value in pv.items():
                packet.set_derived_signal(field_name, Slot(
                    value=value, confidence=0.7,
                    authority_level="derived_signal",
                ))

        # --- TRAVELER PLAN ---
        plan = _extract_traveler_plan(text)
        for field_name, value in plan.items():
            packet.set_fact(field_name, self._make_slot(
                value, 0.85, AuthorityLevel.EXPLICIT_USER,
                value, eid,
            ))

        # --- REVISION COUNT ---
        revision_match = re.search(r"revision\s*(?:#|number\s*)(\d+)", text, re.IGNORECASE)
        if revision_match:
            packet.revision_count = int(revision_match.group(1))

        # --- PAST TRIPS (hook) ---
        if "past trip" in text_lower or "previous trip" in text_lower:
            trip_match = re.search(r"(past|previous)\s+trip[^.,:]*", text_lower)
            if trip_match:
                packet.set_fact("past_trips", self._make_slot(
                    [{"context": trip_match.group(0)}], 0.6,
                    AuthorityLevel.EXPLICIT_OWNER, trip_match.group(0), eid,
                ))

    def _extract_from_structured(self, envelope: SourceEnvelope, packet: CanonicalPacket) -> None:
        """Extract from structured JSON input."""
        data = envelope.content
        eid = envelope.envelope_id

        field_mappings = {
            "destination": "destination_candidates",
            "origin": "origin_city",
            "origin_city": "origin_city",
            "travelers": "party_size",
            "budget": "budget_raw_text",
            "budget_raw_text": "budget_raw_text",
            "dates": "date_window",
            "date_window": "date_window",
            "duration": "duration",
            "party_composition": "party_composition",
            "child_ages": "child_ages",
            "trip_purpose": "trip_purpose",
            "trip_priorities": "trip_priorities",
            "date_flexibility": "date_flexibility",
            "activities": "soft_preferences",
            "follow_up_due_date": "follow_up_due_date",
            "pace_preference": "pace_preference",
            "lead_source": "lead_source",
            "activity_provenance": "activity_provenance",
            "date_year_confidence": "date_year_confidence",
        }

        for src_field, canonical_field in field_mappings.items():
            if src_field in data:
                value = data[src_field]
                if canonical_field in ("origin_city", "destination_candidates"):
                    if isinstance(value, str):
                        value, was_normalized = Normalizer.normalize_city(value)
                        mode = ExtractionMode.NORMALIZED if was_normalized else ExtractionMode.IMPORTED
                    else:
                        mode = ExtractionMode.IMPORTED
                elif canonical_field == "budget_raw_text":
                    parsed = Normalizer.parse_budget(str(value))
                    packet.set_fact("budget_raw_text", self._make_slot(
                        str(value), 1.0, AuthorityLevel.IMPORTED_STRUCTURED,
                        str(value), eid, extraction_mode=ExtractionMode.IMPORTED,
                    ))
                    if parsed.get("min"):
                        packet.set_fact("budget_min", self._make_slot(
                            parsed["min"], 1.0, AuthorityLevel.IMPORTED_STRUCTURED,
                            str(value), eid, extraction_mode=ExtractionMode.IMPORTED,
                        ))
                    if parsed.get("max"):
                        packet.set_fact("budget_max", self._make_slot(
                            parsed["max"], 1.0, AuthorityLevel.IMPORTED_STRUCTURED,
                            str(value), eid, extraction_mode=ExtractionMode.IMPORTED,
                        ))
                    # Skip generic set_fact for budget_raw_text since we've already
                    # set budget_raw_text, budget_min, and budget_max above.
                    continue
                elif canonical_field == "party_size":
                    if isinstance(value, list):
                        value = len(value)
                    mode = ExtractionMode.IMPORTED
                elif canonical_field == "party_composition":
                    if isinstance(value, dict):
                        mode = ExtractionMode.IMPORTED
                    else:
                        continue
                elif canonical_field == "child_ages":
                    if isinstance(value, list):
                        mode = ExtractionMode.IMPORTED
                    else:
                        continue
                else:
                    mode = ExtractionMode.IMPORTED

                packet.set_fact(canonical_field, self._make_slot(
                    value, 1.0, AuthorityLevel.IMPORTED_STRUCTURED,
                    str(value), eid, extraction_mode=mode,
                ))

        if "travelers" in data and isinstance(data["travelers"], list):
            if "party_composition" not in data:
                composition: Dict[str, int] = {}
                child_ages: List[int] = []
                for t in data["travelers"]:
                    age = t.get("age")
                    rel = (t.get("relationship") or "").lower()
                    if age is not None:
                        if age < 4:
                            composition["toddlers"] = composition.get("toddlers", 0) + 1
                            child_ages.append(age)
                        elif age < 12:
                            composition["children"] = composition.get("children", 0) + 1
                            child_ages.append(age)
                        elif age < 18:
                            composition["teens"] = composition.get("teens", 0) + 1
                        elif age >= 65:
                            composition["elderly"] = composition.get("elderly", 0) + 1
                        else:
                            composition["adults"] = composition.get("adults", 0) + 1
                    elif "elderly" in rel or "grandparent" in rel or "senior" in rel:
                        composition["elderly"] = composition.get("elderly", 0) + 1
                    elif "child" in rel or "kid" in rel:
                        composition["children"] = composition.get("children", 0) + 1
                    elif "toddler" in rel or "infant" in rel or "baby" in rel:
                        composition["toddlers"] = composition.get("toddlers", 0) + 1
                    else:
                        composition["adults"] = composition.get("adults", 0) + 1
                if composition:
                    packet.set_fact("party_composition", self._make_slot(
                        composition, 1.0, AuthorityLevel.IMPORTED_STRUCTURED,
                        str(composition), eid, extraction_mode=ExtractionMode.IMPORTED,
                    ))
                if child_ages:
                    packet.set_fact("child_ages", self._make_slot(
                        child_ages, 1.0, AuthorityLevel.IMPORTED_STRUCTURED,
                        str(child_ages), eid, extraction_mode=ExtractionMode.IMPORTED,
                    ))

    def _extract_from_hybrid(self, envelope: SourceEnvelope, packet: CanonicalPacket, stage: str = "discovery") -> None:
        """Handle hybrid input: text + structured data."""
        text = envelope.content.get("text", "")
        structured = envelope.content.get("structured", {})

        # Extract from text first
        text_envelope = SourceEnvelope(
            envelope_id=envelope.envelope_id,
            source_system=envelope.source_system,
            actor_type=envelope.actor_type,
            received_at=envelope.received_at,
            content=text,
            content_type="freeform_text",
        )
        self._extract_from_freeform(text_envelope, packet, stage=stage)

        # Then overlay structured (higher authority for overlapping fields)
        struct_envelope = SourceEnvelope(
            envelope_id=f"{envelope.envelope_id}_struct",
            source_system=envelope.source_system,
            actor_type=envelope.actor_type,
            received_at=envelope.received_at,
            content=structured,
            content_type="structured_json",
        )
        self._extract_from_structured(struct_envelope, packet)

    # ------------------------------------------------------------------
    # DERIVED SIGNALS
    # ------------------------------------------------------------------

    def _compute_derived_signals(self, packet: CanonicalPacket) -> None:
        """Compute derived signals from facts only — never from hypotheses."""

        # domestic_or_international
        # Uses geography.py for country lookup (from GeoNames)
        # Falls back to "unknown" if country info unavailable
        if "destination_candidates" in packet.facts and "origin_city" in packet.facts:
            dests = packet.facts["destination_candidates"].value
            origin = packet.facts["origin_city"].value

            # Get country codes for origin and destinations
            origin_country = get_city_country(str(origin)) if origin else None

            signal = "unknown"
            confidence = 0.3  # Low default confidence when geography unavailable

            if origin_country:
                dest_list = dests if isinstance(dests, list) else [dests]
                countries_known = []
                countries_match_origin = []

                for d in dest_list:
                    d_country = get_city_country(str(d))
                    if d_country:
                        countries_known.append(d)
                        countries_match_origin.append(d_country == origin_country)

                if countries_known:
                    # All known destinations are in same country as origin
                    if all(countries_match_origin):
                        signal = "domestic"
                        confidence = 0.9
                    # All known destinations are in different countries from origin
                    elif all(not cm for cm in countries_match_origin):
                        signal = "international"
                        confidence = 0.9
                    else:
                        signal = "mixed"
                        confidence = 0.8
                else:
                    # No country info for any destination
                    signal = "unknown"
                    confidence = 0.3

            packet.set_derived_signal("domestic_or_international", self._make_slot(
                signal, confidence, AuthorityLevel.DERIVED_SIGNAL,
                f"Computed from destination_candidates={dests}, origin={origin}, origin_country={origin_country}",
                "derived", extraction_mode="derived", maturity="heuristic",
            ))

        # is_repeat_customer (derived ONLY, never in facts)
        if "customer_id" in packet.facts or "agency_notes" in packet.facts:
            agency_notes_val = ""
            if "agency_notes" in packet.facts:
                agency_notes_val = str(packet.facts["agency_notes"].value or "")
            has_repeat_signal = ("customer_id" in packet.facts) or (
                any(phrase in agency_notes_val.lower() for phrase in [
                    "past", "previous", "repeat", "returning", "last time",
                ])
            )
            if has_repeat_signal:
                packet.set_derived_signal("is_repeat_customer", self._make_slot(
                    True, 0.7, AuthorityLevel.DERIVED_SIGNAL,
                    "customer_id or agency_notes indicate repeat customer",
                    "derived", extraction_mode="derived", maturity="heuristic",
                ))

        # urgency (from date_end)
        if "date_end" in packet.facts:
            date_end_val = packet.facts["date_end"].value
            urgency = Normalizer.compute_urgency(str(date_end_val))
            if urgency:
                packet.set_derived_signal("urgency", self._make_slot(
                    urgency["level"], urgency["confidence"],
                    AuthorityLevel.DERIVED_SIGNAL,
                    f"Computed from date_end={date_end_val}, days_until={urgency['days_until']}",
                    "derived", extraction_mode="derived", maturity="verified",
                    notes=f"{urgency['days_until']} days until travel",
                ))

        # internal_data_present
        if packet.hypotheses or packet.contradictions or packet.ambiguities:
            packet.set_derived_signal("internal_data_present", self._make_slot(
                True, 1.0, AuthorityLevel.DERIVED_SIGNAL,
                "Hypotheses, contradictions, or ambiguities present",
                "derived", extraction_mode="derived", maturity="verified",
            ))

        # sourcing_path — routing through SourcingPathResolver (single extension point)
        if "destination_candidates" in packet.facts:
            from .sourcing_path import resolve_sourcing_path

            result = resolve_sourcing_path(packet)
            resolver_used = not result.metadata.get("stub", False)
            maturity = "heuristic" if resolver_used else "stub"
            confidence = min(result.confidence, 0.7) if not resolver_used else result.confidence

            notes = result.reason
            if result.supplier_hints:
                notes += f" | Hints: {', '.join(result.supplier_hints)}"

            packet.set_derived_signal("sourcing_path", self._make_slot(
                result.tier.value, confidence, AuthorityLevel.DERIVED_SIGNAL,
                f"Sourcing tier resolved via SourcingPathResolver: {result.reason}",
                "derived", extraction_mode="derived", maturity=maturity,
                notes=notes,
            ))

    # ------------------------------------------------------------------
    # UNKNOWN IDENTIFICATION
    # ------------------------------------------------------------------

    def _identify_unknowns(self, packet: CanonicalPacket) -> None:
        """Mark expected MVB fields that are not present."""
        discovery_mvb = [
            "destination_candidates", "origin_city", "date_window",
            "party_size", "budget_raw_text", "trip_purpose",
        ]
        for field_name in discovery_mvb:
            if field_name not in packet.facts:
                packet.add_unknown(field_name, "not_present_in_source")
