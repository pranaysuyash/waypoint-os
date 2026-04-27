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
from typing import Any, Dict, List, Optional, Tuple

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


# =============================================================================
# SECTION 1: DESTINATION DETECTION
# =============================================================================

# Regex for destination extraction - uses broad pattern to capture place names
# Validation happens via geography.py, not hardcoded lists
# Matches capitalized place names (single or multi-word)
_DESTINATION_RE = re.compile(
    r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b",
)


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
    """
    lowered = text.lower()
    match_idx = lowered.find(dest_match.lower())
    if match_idx < 0:
        return False

    # Check if preceded by "from" within 10 chars
    context_before = lowered[max(0, match_idx - 10):match_idx]
    if re.search(r'\b(from|starting|departing)\s+$', context_before):
        return True

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
    text_lower = text.lower()
    candidates: List[str] = []
    excluded_by_past_trip: List[str] = []

    # Check for "or" pattern (semi-open)
    or_match = re.search(
        r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)(?:\s+(?:or|and)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*).*?)\b",
        text,
    )
    if or_match:
        c1 = or_match.group(1).title()
        c2 = or_match.group(2).title()
        combined = []
        if not _is_past_trip_mention(text, or_match.group(0)):
            combined = [c1, c2]
        if combined:
            return combined, "semi_open", or_match.group(0)
        else:
            return [], "open", None

    # Check for "maybe" pattern (semi-open) — before general regex
    # so "maybe Singapore" is captured as semi_open, not definite.
    maybe_match = re.search(r"\bmaybe\s+(\w+)", text_lower)
    if maybe_match:
        dest = maybe_match.group(1).title()
        if is_known_destination(dest):
            return [dest], "semi_open", maybe_match.group(0)

    # Check for "thinking about" / "perhaps" / hedging patterns (semi-open)
    hedging_match = re.search(
        r"\b(?:thinking\s+about|perhaps|considering|looking\s+at)\s+(\w+)",
        text_lower,
    )
    if hedging_match:
        dest = hedging_match.group(1).title()
        if is_known_destination(dest):
            return [dest], "semi_open", hedging_match.group(0)

    # Check for "somewhere with/for" (open)
    open_match = re.search(r"somewhere\s+(?:with|for|that)\s+(\w+)", text_lower)
    if open_match:
        return [], "open", open_match.group(0)

    # Check for "open to suggestions"
    if "open to suggestions" in text_lower or ("suggestions" in text_lower and "destination" in text_lower):
        return [], "open", "suggestions"

    # Single/multiple destination match — filter past-trip mentions AND origin patterns
    # Validate against geography database to filter out non-city capitalized words.
    # Also filter common pronouns and stop words that should never be destinations.
    _DESTINATION_STOP_WORDS = {"we", "i", "my", "our", "the", "this", "that", "it", "they", "he", "she", "us"}

    matches = [m.group(0) for m in _DESTINATION_RE.finditer(text)]
    if matches:
        seen = []
        for m in matches:
            title = m.title()
            if title not in seen:
                # Skip common pronouns and stop words
                if title.lower() in _DESTINATION_STOP_WORDS:
                    continue
                # Skip if not a known destination (city or country)
                # geography.py is the filter, not hardcoded lists
                if not is_known_destination(title):
                    continue
                # Skip if this looks like an origin (preceded by "from")
                if _is_likely_origin(text, m):
                    continue
                if _is_past_trip_mention(text, m):
                    excluded_by_past_trip.append(title)
                else:
                    seen.append(title)
        if len(seen) == 1:
            return seen, "definite", matches[0]
        elif len(seen) > 1:
            return seen, "semi_open", ", ".join(matches)

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
    iso_match = re.search(r"(\d{4}-\d{2}-\d{2})\s+(?:to|–|-)\s+(\d{4}-\d{2}-\d{2})", text)
    if iso_match:
        raw = iso_match.group(0)
        return raw, iso_match.group(1), iso_match.group(2), "exact"

    # "This weekend" / "this Friday"
    weekend_match = re.search(r"\bthis\s+(weekend|friday|saturday|sunday|monday|tuesday|wednesday|thursday)\b", text_lower)
    if weekend_match:
        raw = weekend_match.group(0)
        return raw, None, None, "flexible"

    # Month window: "June-July 2026", "March or April 2026"
    month_window = re.search(
        r"((?:January|February|March|April|May|June|July|August|September|October|November|December)\w*)"
        r"\s*(?:or|(?:-|–|—|\bto\b))\s*"
        r"((?:January|February|March|April|May|June|July|August|September|October|November|December)\w*)"
        r"\s+(\d{4})",
        text_lower,
        re.IGNORECASE,
    )
    if month_window:
        raw = month_window.group(0)
        return raw, None, None, "window"

    # Single month: "March 2026"
    single_month = re.search(
        r"((?:January|February|March|April|May|June|July|August|September|October|November|December)\w*)"
        r"\s+(\d{4})",
        text_lower,
        re.IGNORECASE,
    )
    if single_month:
        raw = single_month.group(0)
        return raw, None, None, "flexible"

    # "around March 2026", "sometime in May 2026"
    fuzzy = re.search(
        r"(?:around|sometime\s+in|during)\s+"
        r"((?:January|February|March|April|May|June|July|August|September|October|November|December)\w*)"
        r"\s+(\d{4})",
        text_lower,
        re.IGNORECASE,
    )
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
    if re.search(r"\bflexible\s+budget\b|\bbudget\s+is\s+flexible\b", text_lower):
        return {"raw_text": "flexible", "min": None, "max": None, "currency": "INR"}

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
    if re.search(r"\b(?:total|for\s+(?:the\s+)?(?:whole\s+)?(?:trip|family|group))\b", text_lower):
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
    child_ages: List[int] = []
    text_lower = text.lower()

    # Adults
    adult_match = re.search(r"(\d+)\s+adults?", text_lower)
    if adult_match:
        composition["adults"] = int(adult_match.group(1))

    # Children — match "2 children" or bare "child/kid"
    child_match = re.search(r"(?:(\d+)\s+)?(?:kids?|children?|child)", text_lower)
    if child_match and child_match.group(1):
        composition["children"] = int(child_match.group(1))
    # Try to extract ages: "kids ages 8 and 12", "children aged 5, 7", "child age 3"
    ages_match = re.search(
        r"(?:kids?|children?|child|ages?)\s+(?:ages?\s+)?(\d+(?:\s+(?:and|,)\s*\d+)*)",
        text_lower,
    )
    if ages_match:
        found_ages = [int(a) for a in re.findall(r"\d+", ages_match.group(1))]
        child_ages.extend(found_ages)

    # Toddler — "toddler age 2", "a toddler", "toddlers"
    has_toddler = bool(re.search(r"\b(?:a\s+)?toddler|toddlers?\b", text_lower))
    if has_toddler:
        if "toddlers" not in composition and "children" not in composition:
            composition["children"] = 1
        if 0 not in child_ages and not any(a < 3 for a in child_ages):
            toddler_age_match = re.search(r"toddler\s+(?:age\s+)?(\d+)", text_lower)
            child_ages.append(int(toddler_age_match.group(1)) if toddler_age_match else 2)

    # Elderly — "1 elderly", "an elderly grandmother", "grandma age 78", "senior"
    elderly_match = re.search(r"(?:(\d+)\s+)?(?:elderly|seniors?|grandparents?|grandma|grandpa|grandmother|grandfather)", text_lower)
    if elderly_match:
        composition["elderly"] = int(elderly_match.group(1)) if elderly_match.group(1) else 1
    elif re.search(r"\b(?:elderly|seniors?)\b", text_lower):
        composition.setdefault("elderly", 1)

    # Total party size
    party_size = sum(composition.values())

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
        hard.append(constraint.strip())
    if hard:
        results["hard_constraints"] = hard

    soft = []
    want_match = re.findall(r"(?:want|prefer|like)\s+([^.,]+)", text_lower)
    for pref in want_match:
        soft.append(pref.strip())
    if soft:
        results["soft_preferences"] = soft

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

    def extract(self, envelopes: List[SourceEnvelope]) -> CanonicalPacket:
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
                self._extract_from_freeform(envelope, packet)
            elif envelope.content_type == "structured_json":
                self._extract_from_structured(envelope, packet)
            elif envelope.content_type == "hybrid":
                self._extract_from_hybrid(envelope, packet)

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

    def _extract_from_freeform(self, envelope: SourceEnvelope, packet: CanonicalPacket) -> None:
        text = envelope.content
        text_lower = text.lower()
        eid = envelope.envelope_id

        # --- DESTINATION ---
        dest_candidates, dest_status, dest_raw = _extract_destination_candidates(text)
        if dest_candidates or dest_status in ("open", "undecided"):
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

        # --- PASSPORT / VISA ---
        pv = _extract_passport_visa(text)
        for field_name, value in pv.items():
            packet.set_fact(field_name, self._make_slot(
                value, 0.9, AuthorityLevel.EXPLICIT_USER,
                value, eid,
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
            "activities": "soft_preferences",
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

    def _extract_from_hybrid(self, envelope: SourceEnvelope, packet: CanonicalPacket) -> None:
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
        self._extract_from_freeform(text_envelope, packet)

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

        # sourcing_path (stub)
        if "destination_candidates" in packet.facts:
            dests = packet.facts["destination_candidates"].value
            default_path = "open_market"
            if "owner_constraints" in packet.facts:
                default_path = "network"
            packet.set_derived_signal("sourcing_path", self._make_slot(
                default_path, 0.3, AuthorityLevel.DERIVED_SIGNAL,
                "Stub — enrich with internal package lookup and preferred supplier data",
                "derived", extraction_mode="derived", maturity="stub",
                notes="Stub signal — no real supplier data available yet",
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
