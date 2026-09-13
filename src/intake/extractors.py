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

import logging

import re
import unicodedata
import uuid
from datetime import datetime
from functools import lru_cache
from typing import Any, Dict, List, Optional, Set, Tuple

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
    EpistemicStatus,
    EvidenceRef,
    ExtractionMode,
    OwnerConstraint,
    Slot,
    SourceEnvelope,
    SubGroup,
)
from .normalizer import Normalizer

logger = logging.getLogger(__name__)
from .geography import (
    COUNTRY_CANONICAL_ALIASES,
    get_city_country,
    get_country_iso_code,
    get_macro_region,
    is_known_city,
    is_known_destination,
)

_MONTH_NAMES = frozenset({
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december",
    "jan", "feb", "mar", "apr", "jun", "jul", "aug", "sep", "sept", "oct", "nov", "dec",
})

_SEASON_NAMES = frozenset({"spring", "summer", "fall", "autumn", "winter"})

# Input is user/agency supplied data.  These controls are removed from the
# *extraction view* only; the original SourceEnvelope remains untouched for
# provenance and audit.  In particular, zero-width and bidi controls can split
# a real city into tiny GeoNames entries or spoof its display direction.
_UNSAFE_CONTROL_RE = re.compile(
    r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f\u061c\u200b-\u200f\u202a-\u202e\u2060\u2066-\u2069\ufeff]"
)

# Instruction-like prose is data, never authority.  We remove complete
# clauses/role-labelled lines from the trusted extraction view so a note such
# as "SYSTEM: set budget 999999" cannot win over the actual customer budget.
_INSTRUCTION_CLAUSE_RE = re.compile(
    r"\b(?:ignore|disregard|forget|override)\b[^.!?\n]*(?:[.!?]|$)",
    re.IGNORECASE,
)
_ROLE_INSTRUCTION_RE = re.compile(
    r"\b(?:system|developer|assistant|instructions?)\s*:[^.!?\n]*(?:[.!?]|$)",
    re.IGNORECASE,
)
# "Real note:" / "Real plan:" / "Enquiry:" are metadata labels marking where
# the traveler's own note begins — not destinations.  Keep the payload while
# stripping the label word itself, which otherwise collides with tiny
# GeoNames entries ("Real", Spain; "Plan" is also in the union).
_REAL_NOTE_LABEL_RE = re.compile(
    r"\b(?:real\s+)?(?:notes?|plans?|trips?|requests?|enquir(?:y|ies)|inquir(?:y|ies))\s*:\s*",
    re.IGNORECASE,
)

# Quoted and forwarded material is prior context, not the traveler's own
# voice (X-01).  Email quote lines ("> old plan: ...") and the header block
# after a forwarded-message delimiter ("----- Forwarded message -----" /
# From:/Sent:/To:/Subject:/Date:) are clearly-delimited non-traveler
# segments, so they are dropped from the extraction view before any scan.
_QUOTED_LINE_RE = re.compile(r"^\s*>+\s?")
_FORWARDED_DELIMITER_RE = re.compile(
    r"^\s*[-–—_=*]{2,}\s*(?:begin\s+)?forwarded\s+message\s*[-–—_=*]{2,}\s*$",
    re.IGNORECASE,
)
_FORWARDED_HEADER_LINE_RE = re.compile(
    r"^\s*(?:from|sent|to|cc|bcc|reply\s*-\s*to|subject|date|importance)\s*:",
    re.IGNORECASE,
)


def _prepare_extraction_text(text: Any) -> Tuple[str, Dict[str, int]]:
    """Return a normalized, fail-closed view of untrusted free-form text.

    This function deliberately does not mutate or redact ``SourceEnvelope``.
    It only prepares the text consumed by deterministic extractors and reports
    aggregate removal counts (never the hostile content itself) for audit
    metadata.  Non-string inputs become an empty extraction view.
    """
    if not isinstance(text, str):
        return "", {"control_chars_removed": 0, "instruction_spans_removed": 0}

    normalized = unicodedata.normalize("NFKC", text)
    control_count = len(_UNSAFE_CONTROL_RE.findall(normalized))
    normalized = _UNSAFE_CONTROL_RE.sub("", normalized)

    # Role-labelled lines are untrusted instruction channels.  Drop the line
    # before the inline pass so a multi-line prompt cannot leak through.
    # Quoted lines ("> ...") and forwarded-message header blocks are prior
    # context rather than the traveler's voice and are demoted the same way;
    # the quoted/forwarded BODY that follows a blank line is kept so a
    # legitimate note pasted inside a forward still extracts (adv_struct_003).
    lines = normalized.splitlines(keepends=True)
    kept_lines: List[str] = []
    removed_spans = 0
    in_forwarded_headers = False
    for line in lines:
        if _QUOTED_LINE_RE.match(line):
            removed_spans += 1
            continue
        if _FORWARDED_DELIMITER_RE.match(line):
            in_forwarded_headers = True
            removed_spans += 1
            continue
        if in_forwarded_headers:
            if not line.strip():
                # Blank line ends the header block; the forwarded body follows.
                in_forwarded_headers = False
                kept_lines.append(line)
                continue
            if _FORWARDED_HEADER_LINE_RE.match(line):
                removed_spans += 1
                continue
            in_forwarded_headers = False
        if re.match(r"^\s*(?:system|developer|assistant|instructions?)\s*:", line, re.IGNORECASE):
            removed_spans += 1
            continue
        # FND-0274 (Sim #2): speaker-label prefixes ("[arjun]: text",
        # "[forwarded voice note from X]: text") leak into packet fields when
        # the label is concatenated with the constraint text. Strip the
        # label, keep the content — the speaker attribution is handled
        # separately by src/intake/attribution.py.
        chat_label = re.match(r"^\s*\[[^\]]{1,60}\]:\s*(.+)", line)
        if chat_label:
            kept_lines.append(chat_label.group(1).lstrip() + "\n")
            continue
        kept_lines.append(line)
    normalized = "".join(kept_lines)

    normalized, instruction_count = _INSTRUCTION_CLAUSE_RE.subn(" ", normalized)
    removed_spans += instruction_count
    normalized, role_count = _ROLE_INSTRUCTION_RE.subn(" ", normalized)
    removed_spans += role_count

    # "Real note:" is a metadata label, not a destination.  Keep its payload
    # while preventing common red-team fixtures from minting the city "Real".
    normalized = _REAL_NOTE_LABEL_RE.sub(" ", normalized)
    return normalized, {
        "control_chars_removed": control_count,
        "instruction_spans_removed": removed_spans,
    }

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
    # Negation tokens: "No" and "Not" are real GeoNames entries (No is an
    # alternate name of Ho, Ghana), so geography validation alone cannot
    # filter them. Blocking them here closes every destination pass
    # (VA-07, review cycle 1 2026-09-09).
    "no", "not",
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

_LEADING_ORIGIN_HINTS = frozenset({
    "family", "families", "couple", "couples", "group", "groups",
    "traveler", "travelers", "traveller", "travellers",
    "client", "clients", "customer", "customers", "agency",
    "request", "quote", "lead", "leads", "office", "market", "branch",
    "trip", "travel", "planning", "planned", "looking", "want", "wants",
    "need", "needs", "going", "visit", "holiday", "vacation",
    "corporate", "leisure", "honeymoon", "wedding",
    "to", "for",
})

_NON_DESTINATION_PLACEHOLDERS = frozenset({
    "beach",
    "hotel",
    "resort",
    "villa",
})


# =============================================================================
# SECTION 1: DESTINATION DETECTION
# =============================================================================

# Regex for destination extraction - uses broad pattern to capture place names
# Validation happens via geography.py, not hardcoded lists
# Matches capitalized place names (single or multi-word)
_DESTINATION_RE = re.compile(
    # Do not treat the "Let" prefix of the contraction "Let's" as a city.
    # Hyphenated place names ("Winston-Salem") join as one token, mirroring
    # the spaced multi-word alternative — without the hyphen branch the name
    # fragments into two independent candidates ("Winston" + "Salem").
    r"\b[A-Z][a-z]+(?:[-][A-Z][a-z]+|\s+[A-Z][a-z]+)*(?!['’][A-Za-z])\b",
)

# Travel-context patterns for lowercase destination extraction.
# Only match destinations that appear in travel-intent context, not globally.
# This prevents false positives like "got" in "I got your number".

# Pattern 2: "somewhere" + destination (open intent)
_SOMEWHERE_DEST_RE = re.compile(
    r"somewhere\s+(?:with|for|that)\s+(\w+)",
    re.IGNORECASE,
)

# Pattern 3: "or"/"and" pattern (semi-open destination). Hyphenated names
# ("Winston-Salem and Charlotte") must stay whole — a split yields "Salem",
# which is a real validating city and silently poisons candidates.
_OR_DESTINATION_RE = re.compile(
    r"\b([A-Z][a-z]+(?:-[A-Z][a-z]+)*(?:\s+[A-Z][a-z]+(?:-[A-Z][a-z]+)*)*)(?:\s+(?:or|and)\s+([A-Z][a-z]+(?:-[A-Z][a-z]+)*(?:\s+[A-Z][a-z]+)*).*?)\b",
)

# Destination metadata labels to exclude (caller, referral, etc.)
_DESTINATION_METADATA_LABELS_RE = re.compile(
    r"^\s*(call\s+received|caller|referral|party|pace(?:\s+reference)?|budget|interests?|follow[\s-]*up|toddler\s+needs?|elderly\s+needs?|origin(?:\s+city)?|departure(?:\s+city)?|departing\s+from|from\s+city)\s*:",
    re.IGNORECASE,
)

# Salutations / greetings to exclude from destination parsing
_SALUTATION_RE = re.compile(
    r"^\s*(?:hi|hello|hey|dear|good\s+(?:morning|afternoon|evening))\s+"
    r"(?:(?:mr|mrs|ms|miss|mx|dr|prof)\.?\s+)?[A-Za-z]+[!,.\s]*",
    re.IGNORECASE | re.MULTILINE,
)

# Common inline patterns - pre-compiled for performance
_YEAR_RE = re.compile(r"\b(20\d{2})\b")
_FROM_STARTING_DEPARTING_RE = re.compile(r'\b(from|starting|departing)\s+$', re.IGNORECASE)
_SE_RU_SIDE_RE = re.compile(r'^\s+(se|ru|side)\b', re.IGNORECASE)
_SIDE_TRIP_NOUN_RE = re.compile(
    r"\s+(?:trip|tours?|visit|excursion|quest|detour|adventure|getaway|holiday|vacation|outing)\b",
    re.IGNORECASE,
)


def _side_is_trip_compound(context_after_postposition: str) -> bool:
    """True when "side" is an adjective on a following trip-noun ("okinawa
    side trip?"), not the Hinglish origin postposition ("bangalore side" =
    "from bangalore"). FND-0273-family, Sim #2: this distinction fabricated
    Origin City: okinawa in two independent extraction paths."""
    return bool(
        _SIDE_TRIP_NOUN_RE.search(context_after_postposition[:40])
    )

# Past-trip mentions are memories, never current destination intent:
# "we went to japan, korea last year and loved it" must not open the
# destination. The span runs from the past-trip verb to the first
# past-time cue so suppression stays clause-scoped. Consumed by
# _is_past_trip_mention (guard) and _extract_past_trip_places (capture).
_PAST_TRIP_CLAUSE_RE = re.compile(
    r"\b(?:went|visited|been|traveled|travelled)\b[^.!?;]{0,120}?"
    r"(?:last\s+(?:year|month|week|summer|winter|spring|fall|autumn)"
    r"|\b(?:19|20)\d{2}\b|\bago\b)",
    re.IGNORECASE,
)
# Module-level (not per-call): the sweep consults this on every word, so
# building it inside the function violated the constant-recreation rule.
_SWEEP_STOP_WORDS = {
    # English prepositions/conjunctions/articles/pronouns
    "a", "an", "and", "as", "at", "be", "but", "by", "can", "de",
    "do", "for", "from", "had", "has", "have", "he", "her", "him",
    "his", "i", "if", "in", "is", "it", "its", "la", "le", "like",
    "me", "my", "no", "not", "of", "on", "or", "our", "out", "per",
    "she", "so", "the", "their", "them", "then", "there", "they",
    "this", "to", "up", "us", "was", "we", "were", "will", "with",
    "would", "you", "your", "off", "own", "same", "than", "too",
    "very", "just", "also", "now", "get", "got", "one", "two",
    "all", "any", "each", "few", "more", "most", "other", "some",
    "such", "only", "about", "between", "through", "after", "before",
    "being", "both", "did", "does", "doing", "during", "here", "how",
    "into", "itself", "nor", "once", "over", "should", "under",
    "until", "what", "when", "where", "which", "while", "who", "why",
    "am", "are", "been", "was", "were", "been", "have", "having",
    # Gen Z / casual
    "wanna", "gonna", "trynna", "fr", "yall", "vibing", "vibe",
    "lit", "the move", "bussin", "honestly", "literally",
    # Hinglish
    "chahiye", "log", "logon", "mein", "yahan", "wahan", "kar",
    "ka", "ki", "ke", "hai", "hona", "jaldi", "accha", "theek",
    "bhai", "yaar", "niklenge", "dosta",
    # Travel noise
    "trip", "travel", "vacation", "holiday", "tour", "visit",
    "pax", "ppl", "people", "person", "adults", "adult", "kids",
    "children", "child", "family", "friends", "friend", "couple",
    "couples", "group", "budget", "total", "days", "day", "nights",
    "night", "week", "weeks", "dates", "date", "flexible",
    "including", "excluding", "needed", "want", "needs", "must",
    "cover", "max", "min", "hard", "cap", "stuff", "things",
    "dinner", "lunch", "food", "meal", "meals", "veg", "vegan",
    # GeoNames collision words — the 590k-city database contains
    # villages named after common English words; keep them out of
    # the sweep. (True "Side, Turkey" positives go through the
    # pattern paths, not this fallback.) Verified colliders from the
    # KDD gate run 2026-09-13: "any time" swept up the village of
    # Time and fabricated a destination on destination-less notes.
    "need", "old", "side", "parks", "top", "set", "lie", "bad",
    "ever", "let", "long", "made", "make", "man", "many", "much",
    "part", "put", "say", "see", "since", "still", "tell", "time",
    "turn", "well", "yes", "yet",
    # Amenity/preference nouns — same collision class ("resort with a
    # pool" swept up Pool, UK). Preference prose belongs to the
    # interests lane; compound names (bigrams) stay unfiltered.
    "bay", "bridge", "casino", "castle", "cathedral", "cave", "church",
    "fort", "garden", "gym", "harbor", "hill", "island", "lake",
    "market", "mountain", "park", "pool", "port", "ski", "snow",
    "spa", "sun", "sunrise", "sunset", "temple", "valley", "yoga",
}
_MAYBE_RE = re.compile(r"\bmaybe\s+(\w+)", re.IGNORECASE)
# "maybe somewhere like X" / "somewhere like X" — negative lookahead stops at
# common trailing prepositions ("for", "with", etc.) to prevent over-capturing
# context like "goa for a beach vacation" → "goa". Capped at 4 words.
_MAYBE_SOMEWHERE_LIKE_RE = re.compile(r"\bmaybe\s+somewhere\s+like\s+(\w+(?:\s+(?!(?:for|with|that|and|or|but|from|to|in|on|at|by|of|the|a|an)\b)\w+){0,3})", re.IGNORECASE)
_SOMEWHERE_LIKE_RE = re.compile(r"\bsomewhere\s+like\s+(\w+(?:\s+(?!(?:for|with|that|and|or|but|from|to|in|on|at|by|of|the|a|an)\b)\w+){0,3})", re.IGNORECASE)
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
_SINGLE_MONTH_NO_YEAR_RE = re.compile(
    r"(?:in|during|for)\s+"
    r"((?:January|February|March|April|May|June|July|August|September|October|November|December)\w*)\b",
    re.IGNORECASE,
)
_AFTER_MONTH_DAY_RE = re.compile(
    r"\b(?:after|from|post)\s+"
    r"((?:January|February|March|April|May|June|July|August|September|October|November|December)\w*)\s+"
    r"(\d{1,2})(?:st|nd|rd|th)?"
    r"(?:\s+(\d{4}))?\b",
    re.IGNORECASE,
)
_FUZZY_MONTH_RE = re.compile(
    r"(?:around|sometime\s+in|during)\s+((?:January|February|March|April|May|June|July|August|September|October|November|December)\w*)",
    re.IGNORECASE,
)
# "late march" / "early june" / "mid september" — no preposition required.
_MODIFIER_MONTH_RE = re.compile(
    r"\b(?:late|early|mid)[\s-]+"
    r"(?:(?:January|February|March|April|May|June|July|August|September|October|November|December)\w*)\b",
    re.IGNORECASE,
)
# Season windows: "next spring", "this winter", "in fall". A qualifier is
# REQUIRED — bare season words are prose verbs/nouns far too often ("we will
# fall in love", "a spring in her step", "don't want winter") to invent an
# INTAKE_MINIMUM date_window from. Northern-hemisphere month mapping (noted
# for evidence); the raw phrase is kept as date_window — no ISO ends are
# invented for a season-scale window.
_SEASON_MONTHS = {
    "spring": ("Mar", "May"),
    "summer": ("Jun", "Aug"),
    "fall": ("Sep", "Nov"),
    "autumn": ("Sep", "Nov"),
    "winter": ("Dec", "Feb"),
}
_SEASON_RE = re.compile(
    r"\b(?:(?:next|this|in|around|early|late|sometime\s+in)\s+(?:the\s+)?)"
    r"(spring|summer|fall|autumn|winter)\b",
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

# Month-day range patterns like "July 10 to July 16" or "July 10-16".
_MONTH_DAY_RANGE_RE = re.compile(
    r"\b((?:January|February|March|April|May|June|July|August|September|October|November|December)\w*)\s+"
    r"(\d{1,2})(?:st|nd|rd|th)?\s*(?:to|-|–|—|\bto\b)\s*"
    r"(?:(?:((?:January|February|March|April|May|June|July|August|September|October|November|December)\w*)\s+))?"
    r"(\d{1,2})(?:st|nd|rd|th)?"
    r"(?:\s+(\d{4}))?",
    re.IGNORECASE,
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

# Hedging words (maybe, perhaps, etc.) — "thinking about X" and the bare
# colloquial "thinking X" form. The captured span is only accepted when it
# validates as a known destination, so "thinking about the budget" stays clean.
_HEDGING_RE = re.compile(
    r"\b(?:maybe|perhaps|considering|looking\s+at|thinking\s+about|thinking)\s+(\w+)",
    re.IGNORECASE,
)

_NUMBER_WORDS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "ek": 1,
    "do": 2,
    "teen": 3,
    "char": 4,
    "chaar": 4,
    "paanch": 5,
    "panch": 5,
    "chhe": 6,
    "saat": 7,
    "aath": 8,
    "nau": 9,
    "das": 10,
}
_COUNT_TOKEN_RE = r"(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|ek|do|teen|cha{1,2}r|pa{1,2}nch|chhe|saat|aath|nau|das)"

# People count patterns
_ADULTS_RE = re.compile(rf"({_COUNT_TOKEN_RE})\s+adults?", re.IGNORECASE)
_CHILDREN_RE = re.compile(rf"(?:(({_COUNT_TOKEN_RE})\s+))?(?:kids?|children?|child|bachhe|baccha)", re.IGNORECASE)
_TODDLER_RE = re.compile(r"\b(?:a\s+)?(?:toddler|toddlers?)\b", re.IGNORECASE)
_TODDLER_AGE_RE = re.compile(r"toddler\s+(?:age\s+)?(\d+)", re.IGNORECASE)
_ELDERLY_RE = re.compile(rf"(?:(({_COUNT_TOKEN_RE})\s+))?(?:elderly|seniors?|grandparents?|grandma|grandpa|grandmother|grandfather)", re.IGNORECASE)
_ELDERLY_AGE_RE = re.compile(r"\b(?:elderly|seniors?)\b", re.IGNORECASE)
_PEOPLE_RE = re.compile(
    rf"({_COUNT_TOKEN_RE})\s*(?:[-–—]?\s*)?"
    # "guests?" is a party count ("25 guests from Delhi"), but "guest
    # list/house/room/book/bedroom/bathroom" prose is not — the lookahead
    # keeps those clean. _GUEST_PROSE_SUFFIXES below is the shared source.
    r"(?:people|persons?|pax|travelers?|travellers?|ppl|log|loga|jan|bande|bando"
    r"|guests?(?!\s*(?:lists?|houses?|rooms?|books?|bed(?:room)?s?|bath(?:room)?s?)\b))",
    re.IGNORECASE,
)

# Age patterns
_AGE_RE = re.compile(r"(\d+\.?\d*)\s*(?:years?|yr|y)[\s-]*(?:old|aged?)\s+(\w+)", re.IGNORECASE)
_AGES_RE = re.compile(r"(\d+)\s*(?:years?|yr|y)[\s-]*(?:old|aged?)", re.IGNORECASE)
_MULTI_AGE_RE = re.compile(r"(\d+)\s*(?:,|and)\s*(\d+)\s*(?:,|and)?\s*(\d+)?\s*(?:years?|yr|y)", re.IGNORECASE)

# Family/group patterns
_FAMILY_RE = re.compile(r"(?:family|they|customer)\s+(?:always\s+)?(?:prefers?|likes?)\s+([^.,]+)", re.IGNORECASE)
_GROUP_SIZE_RE = re.compile(rf"(?:family|group|party)\s+(?:\w+\s*)?(?:of\s+)?({_COUNT_TOKEN_RE})", re.IGNORECASE)

# Colloquial group-size phrasing (DEMO-02): "me and 3 friends", "4 of us",
# "the four of us", bare "2 friends". Companion counts add to adults; a
# whole-group count is evaluated as a max-fallback like the family/group path.
_SELF_PLUS_FRIENDS_RE = re.compile(
    rf"\b(?P<self>me|us|myself|i)\s+(?:and|n|&|\+|\bplus\b)\s+(?P<count>{_COUNT_TOKEN_RE})\s+(?:friends?|others?|colleagues?|buddies?|mates?|people|persons?|ppl|log|travelers?|travellers?)\b",
    re.IGNORECASE,
)
_FRIENDS_RE = re.compile(
    rf"\b(?P<count>{_COUNT_TOKEN_RE})\s+(?:friends?|others?|colleagues?|buddies?|mates?|ppl|log)\b",
    re.IGNORECASE,
)
_OF_US_RE = re.compile(
    rf"\b(?:the\s+)?(?P<count>{_COUNT_TOKEN_RE})\s+of\s+us\b",
    re.IGNORECASE,
)
# Group phrasings that imply a group exists but may carry no convertible
# count ("one of us is terrified", "3 buddies"). Matched phrases are carried
# as group_signals so validation can warn instead of silently mis-sizing.
# Kinship/social plurals are included even though they are not in the parsed
# vocabulary: "me and my 3 cousins" must leave a raw trace so validation can
# flag PARTY_UNDERDETECTED instead of silently sizing the party as 1.
_PARTY_GROUP_SIGNAL_RE = re.compile(
    r"\b\d+\s+(?:friends?|others?|buddies?|mates?|colleagues?"
    r"|cousins?|siblings?|nephews?|nieces?|aunts?|uncles?|grandparents?"
    r"|kids?|children|sons?|daughters?|parents?|guests?|adults?|teens?|teenagers?"
    r"|families?|classmates?|roommates?|flatmates?|ppl|log)\b"
    r"|\b(?:one|two|three|four|five|six|seven|eight|nine|ten|ek|do|teen|cha{1,2}r|pa{1,2}nch|\d+)\s+of\s+us\b"
    r"|\bparty\s+of\s+\w+"
    r"|\bcouple\s+of\s+(?:friends|colleagues|people|ppl)\b"
    r"|\b(?:the\s+)?(?:squad|gang|boys|girls|crew)\b"
    r"|\b(?:one|some)\s+of\s+us\b",
    re.IGNORECASE,
)

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
# "go to singapore", "want to go singapore", "travel to singapore", plus the
# colloquial verb-object forms ("want to do japan", "hitting bali",
# "covering tokyo", "check out seoul"). Longest alternations first so
# "wanna do"/"hitting"/"covering" win over their prefixes.
_TRAVEL_VERB_DEST_RE = re.compile(
    r"(?:want to go|go to|travel to|visit|flying to|trip to|holiday in|vacation in"
    r"|planning to go to|planning to visit|head to|going to"
    r"|wanna do|do|hitting|hit|covering|cover|check out|keen on|down for)\s+"
    # Hyphen branch keeps hyphenated place names whole ("trip to winston-salem").
    r"([a-z]+(?:-[a-z]+)*(?:\s+[a-z]+(?:-[a-z]+)*)*)",
)

# Colloquial city-set separator: "tokyo + kyoto + osaka", "tokyo, kyoto and
# osaka". Every element must independently validate as a known destination,
# so activity phrases like "a cooking class" can never slip through.
# Hyphens are part of a name ("viña-del-mar" style compounds) — without them
# a hyphenated element silently fails validation and drops from the set.
# (Splitting lives in _extract_city_set, which keeps "or" runs separate.)
_CITY_SET_ELEMENT_RE = re.compile(r"^[a-z]+(?:-[a-z]+)?(?:\s+[a-z]+){0,2}$")

# "somewhere" counts as open destination intent only in a destination-ish
# position — directly after a travel verb/marker, or followed by a place
# qualifier. A bare "somewhere" inside an activity clause ("do a cooking
# class somewhere") must not open the destination status.
_SOMEWHERE_OPEN_RE = re.compile(
    r"\b(?:go|going|goes|travel|traveling|travelling|trip|visit|visiting"
    r"|head|heading|flying|fly|getaway|holiday|vacation|tour)s?"
    r"\s+(?:to\s+|out\s+)?somewhere\b"
    r"|\bsomewhere\s+(?:warm|tropical|beachy|sunny|cool|cold|nice|safe"
    r"|exotic|quiet|different|new|far|close)\b",
    re.IGNORECASE,
)

# Pattern 2: Destination before Hinglish/Odia travel verbs.
# "singapore jana hai", "bali jaiba"
_HINGLISH_DEST_RE = re.compile(
    r"([a-z]+(?:-[a-z]+)*(?:\s+[a-z]+(?:-[a-z]+)*)*)\s+"
    r"(?:jana hai|jaana hai|jao|jana|janahi|jiba|jib)",
)

# Pattern 3: After origin marker ("se"/"ru") before travel verb.
# "bangalore se singapore jana hai", "bangalore ru sri lanka jiba"
_ORIGIN_DEST_RE = re.compile(
    r"(?:se |ru )\s*([a-z]+(?:-[a-z]+)*(?:\s+[a-z]+(?:-[a-z]+)*)*)\s+"
    r"(?:jana hai|jana|jiba|jib|go|travel|visit)",
)

# Bare, travel-shaped notes are common in email and CRM exports.  They are
# destinations when a known place appears immediately before a date/trip
# marker, not origins merely because the note starts with a city.
_VERBLESS_DESTINATION_RE = re.compile(
    r"\b(?P<destination>[a-z][a-z'’-]*(?:\s+[a-z][a-z'’-]*){0,2})\s+"
    r"(?=(?:in|during)\s+(?:the\s+)?(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|"
    r"jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\b"
    r"|(?:next|this|coming)\s+(?:spring|summer|fall|autumn|winter)\b"
    r"|(?:trip|holiday|vacation)\b|for\s+(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten)\b)",
    re.IGNORECASE,
)

_CITY_SET_TRAILING_TIME_RE = re.compile(
    r"\s+(?:at|around|by)\s+\d{1,2}(?::\d{2})?\s*(?:am|pm)?\b.*$",
    re.IGNORECASE,
)
_CITY_SET_TRAILING_SEASON_RE = re.compile(
    r"\s+(?:(?:next|this|coming|in)\s+(?:the\s+)?"
    r"(?:spring|summer|fall|autumn|winter))\b.*$",
    re.IGNORECASE,
)
# A set element ending in a month/season phrase ("thailand in december",
# "kyoto june 2027", "goa next winter") carries a time tail, not a place.
_CITY_SET_TIME_TAIL_RE = re.compile(
    r"(?:\b(?:in|during|for|around|next|this|coming|late|early|mid)\s+)?"
    r"\b(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
    r"jul(?:y)?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|"
    r"dec(?:ember)?|spring|summer|fall|autumn|winter)\b"
    r"(?:\s+(?:20\d{2}))?\s*$",
    re.IGNORECASE,
)

_STRUCTURED_UNSAFE_VALUE_RE = re.compile(
    r"(?:;|--|/\*|\*/|\b(?:drop|delete|insert|update|select)\s+(?:table|from|into)\b|"
    r"\b(?:or|and)\s+\d+\s*=\s*\d+)",
    re.IGNORECASE,
)

# A canonical geo field shorter than this is a fragment, not a place.  The
# geography union contains 1-2 letter GeoNames entries ("Ba", Fiji), so a
# truncated import ("Ba", "B") would otherwise validate at full confidence
# (X-08).  Real structured imports always name a place with 3+ characters.
_MIN_STRUCTURED_PLACE_LEN = 3


def _structured_destination_values(value: Any) -> List[str]:
    """Validate and normalize structured destination input.

    Structured authority does not mean arbitrary strings are destinations.
    Only strings that resolve through the canonical geography layer are
    promoted to ``destination_candidates``; malformed, fragment-length, or
    SQL-shaped values remain absent and therefore visible as an intake
    unknown.
    """
    raw_values: List[Any]
    if isinstance(value, str):
        raw_values = [value]
    elif isinstance(value, list):
        raw_values = value
    else:
        return []

    output: List[str] = []
    for raw in raw_values:
        if (
            not isinstance(raw, str)
            or len(raw.strip()) < _MIN_STRUCTURED_PLACE_LEN
            or _STRUCTURED_UNSAFE_VALUE_RE.search(raw)
        ):
            continue
        # Comma-separated structured exports are common; each candidate still
        # needs independent geography validation.
        for item in re.split(r"\s*,\s*", raw):
            item = item.strip()
            if not item or len(item) < _MIN_STRUCTURED_PLACE_LEN:
                continue
            normalized, _ = Normalizer.normalize_city(item)
            candidate = normalized or item
            if is_known_destination(candidate) and candidate not in output:
                output.append(candidate)
    return output


def _structured_origin_value(value: Any) -> Optional[str]:
    if (
        not isinstance(value, str)
        or len(value.strip()) < _MIN_STRUCTURED_PLACE_LEN
        or _STRUCTURED_UNSAFE_VALUE_RE.search(value)
    ):
        return None
    normalized, _ = Normalizer.normalize_city(value.strip())
    candidate = normalized or value.strip()
    if not candidate or not is_known_city(candidate):
        return None
    return candidate


def _structured_budget_is_safe(value: Any) -> bool:
    return isinstance(value, (str, int, float)) and not isinstance(value, bool) and not _STRUCTURED_UNSAFE_VALUE_RE.search(str(value))


@lru_cache(maxsize=32)
def _month_to_num(month_str: str) -> Optional[int]:
    return _MONTH_MAP.get(month_str.lower()[:3].rstrip("e")) or _MONTH_MAP.get(month_str.lower())


def _count_token_to_int(raw: str | None) -> Optional[int]:
    if not raw:
        return None
    token = raw.strip().lower()
    if token.isdigit():
        value = int(token)
        # A four-digit date must never become a party size.  The upper bound
        # also prevents absurd imported/headcount values from feeding pricing
        # and per-person arithmetic while leaving normal group travel intact.
        return value if 0 < value <= 1000 else None
    return _NUMBER_WORDS.get(token)


def _infer_year_from_context(text: str) -> str:
    year_match = _YEAR_RE.search(text)
    if year_match:
        return year_match.group(1)
    return str(datetime.now().year)


def _classify_date_year(text: str) -> Optional[str]:
    """Classify an explicitly stated travel year without rewriting it.

    The extractor must preserve what the traveler said, even when it is stale
    or implausibly distant.  This side-channel lets validation/policy surface
    the problem instead of silently treating an impossible date as current.
    The sane intake window is the current year through current+3 (X-03):
    quoted years outside it are flagged, never rewritten.
    """
    years = [int(match.group(1)) for match in _YEAR_RE.finditer(text)]
    if not years:
        return None
    current_year = datetime.now().year
    if any(year < current_year for year in years):
        return "past_year"
    if any(year > current_year + 3 for year in years):
        return "implausible_year"
    return None


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


# Phrases like "no idea of the name" / "no clue about dates" report the
# traveler's own missing information, not a prohibition. Checking the capture's
# headword keeps real negations ("no cable cars") while dropping these.
_NEGATION_KNOWLEDGE_HEADWORDS = frozenset({
    "idea", "ideas", "clue", "notion", "recollection",
    # Idiom fragments: "no matter what" is emphasis, not a constraint
    # (Sim #2, Dev: "the trip needs to cover april 14 no matter what").
    "matter", "matter what", "doubt", "question",
})


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

    Two complementary checks, so both paths (pattern extraction and the
    broad sweep) share one implementation:
    1. Clause-level: a past-trip indicator in the same comma/sentence clause
       as the destination ("we went to japan").
    2. Span-level: the destination sits between a past-trip verb and the
       first past-time cue ("we went to japan, korea last year" — "korea"
       shares the verb and the cue but not a clause with either).
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
    return any(
        m.start() <= match_idx < m.end()
        for m in _PAST_TRIP_CLAUSE_RE.finditer(lowered)  # span-level branch
    )


def _extract_past_trip_places(sentence: str) -> List[Dict[str, Any]]:
    """Capture past-trip destinations as travel-history facts — memories,
    never current intent. "We went to japan, korea last year and loved it"
    yields [{place: Japan, ...}, {place: Korea, ...}] with the clause, a
    coarse sentiment cue, and the macro region for preference inference
    ("do they prefer East Asian destinations?")."""
    places: List[Dict[str, Any]] = []
    seen: Set[str] = set()
    _POSITIVE_CUES = re.compile(
        r"\b(loved|enjoyed|amazing|wonderful|great|beautiful|fantastic|had a blast)\b",
        re.IGNORECASE,
    )
    for span_match in _PAST_TRIP_CLAUSE_RE.finditer(sentence):
        span_text = span_match.group(0)
        # Sentiment often trails the time cue ("… last year and loved it"),
        # so look a bounded, sentence-bounded window past the span end too.
        trailing = re.split(r"[.!?]", sentence[span_match.end():span_match.end() + 60])[0]
        sentiment = "positive" if _POSITIVE_CUES.search(span_text + trailing) else None
        for word_match in re.finditer(r"[a-zA-Z][a-zA-Z'-]{1,30}", span_text):
            word_clean = word_match.group(0).strip("'-").lower()
            if len(word_clean) < 3 or word_clean in _SWEEP_STOP_WORDS:
                continue
            # Country-level names ("korea") aren't GeoNames cities but are
            # valid history places when a macro region resolves them.
            region = get_macro_region(word_clean)
            if not is_known_destination(word_clean) and not region:
                continue
            title = word_clean.title()
            if title in seen:
                continue
            seen.add(title)
            places.append({
                "place": title,
                "clause": span_text.strip(),
                "sentiment": sentiment,
                "region": region,
            })
    return places


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

    leading_origin = _extract_leading_origin_city(text)
    if leading_origin:
        normalized_dest, _ = Normalizer.normalize_city(dest_match)
        if leading_origin.lower() == normalized_dest.lower():
            return True

    if leading_origin == dest_match:
        return True

    # English preposition before: "from Bangalore"
    context_before = lowered[max(0, match_idx - 10):match_idx]
    if _FROM_STARTING_DEPARTING_RE.search(context_before):
        return True

    # Explicit origin labels: "Origin city: Nairobi", "Departure city: Delhi",
    # "From city: Mumbai". These are common in structured intake notes and should
    # never be treated as destination candidates.
    label_window = lowered[max(0, match_idx - 30):match_idx]
    if re.search(r"\b(origin(?:\s+city)?|departure(?:\s+city)?|from\s+city|departing\s+from)\s*:\s*$", label_window):
        return True

    # Hinglish/Odia postposition after: "Bangalore se", "Bangalore ru",
    # "Bangalore side". A non-compound "side" marks a location REFERENCE
    # ("we are bangalore side, plan something") — never a destination
    # candidate. This is exclusion only: whether an origin FACT exists is
    # decided by the origin writer's marker semantics (Option 3: bare
    # "side" yields a hypothesis, "side se"/"se"/"ru" yield facts).
    context_after = lowered[match_idx + len(dest_match):match_idx + len(dest_match) + 15]
    side_postposition = _SE_RU_SIDE_RE.search(context_after)
    if side_postposition:
        if not (side_postposition.group(1).lower() == "side"
                and _side_is_trip_compound(context_after[side_postposition.end():])):
            return True

    # Agency/location descriptors like "Nairobi-based agency request" should not
    # be treated as trip destinations. The city is describing the source agency,
    # not the trip intent.
    if re.match(r"^[\s-]*based\b", context_after):
        return True

    # Travel intent phrasing often includes the origin city immediately before
    # the destination ("from Mumbai to Bali"). Treat the source city as origin,
    # not a current destination candidate.
    if re.match(r"^\s*to\b", context_after):
        return True

    # Descriptive phrases like "Mumbai agency" or "Delhi request" are source
    # context, not destination intent.
    if re.match(r"^\s*(agency|request|lead|team|office|market|branch)\b", context_after):
        return True

    return False


def _extract_leading_origin_city(text: str) -> Optional[str]:
    """Check whether a note starts with a likely origin city.

    This catches agency-style notes like "Cape Town family of 4 wants Mauritius"
    where the first city is the departure/origin city and the actual destination
    appears later in the same sentence.
    """
    stripped = text.lstrip()
    if not stripped:
        return None

    tokens = re.findall(r"[A-Za-z][A-Za-z'.-]*", stripped)
    if len(tokens) < 2:
        return None

    for prefix_size in range(min(3, len(tokens)), 0, -1):
        prefix = " ".join(tokens[:prefix_size]).strip()
        city, _ = Normalizer.normalize_city(prefix)
        if not is_known_city(city):
            continue

        remainder = tokens[prefix_size:prefix_size + 8]
        if not remainder:
            continue

        remainder_lower = " ".join(remainder).lower()

        # A city followed only by a trip/date phrase is a destination-shaped
        # note ("Bali in June", "Bali trip 2027"), not evidence of origin.
        # Origin inference from a leading city is reserved for agency/group
        # descriptors that actually establish source context.
        source_descriptor = re.search(
            r"\b(?:agency|office|branch|desk|request|lead|team|family|group|couple|corporate)\b",
            remainder_lower,
        )
        if source_descriptor:
            return city

    return None


def _is_valid_destination_candidate(span: str, context: str) -> bool:
    """Type-check a destination candidate before accepting it.

    Rejects months, relation words, person-role words.
    Accepts known destinations and contextually likely place names.
    """
    lower = span.lower().strip()

    if lower in _MONTH_NAMES or lower in _SEASON_NAMES:
        return False

    if lower in _RELATION_WORDS:
        return False

    # Common stop words that should never be destinations
    if lower in _STOP_WORDS:
        return False

    # Generic amenity nouns often appear in preference phrases like
    # "beach resort" or "hotel stay" and should not be treated as trip
    # destinations even when they are capitalized in the source text.
    if lower in _NON_DESTINATION_PLACEHOLDERS:
        return False

    if is_known_destination(lower):
        return True

    context_lower = context.lower()
    for verb in _DESTINATION_HINT_VERBS:
        if verb in context_lower and span[0].isupper():
            return is_known_city(lower) if lower not in _RELATION_WORDS else False

    return False


# A city-set element ending in "... for safari" / "... in Singapore" is a
# sentence fragment, not a set member; the final city only counts when the
# word before it is not a preposition/stop guard.
_CITY_SET_PRE_GUARD_WORDS = frozenset({
    "for", "with", "in", "at", "from", "to", "into", "near", "by", "of",
    "on", "through", "around", "about", "over", "under",
})


def _last_word_destination(element: str) -> Optional[str]:
    """Resolve a separator element to a destination via its final word.

    Handles verb-led elements like "thinking tokyo" or "covering tokyo" where
    only the trailing token is the place name. Fragments like "kenya for
    safari" or "interested in singapore" are rejected via the preposition
    guard so prose endings can't form city sets.
    """
    words = element.split()
    if not words:
        return None
    last = words[-1]
    # Hyphenated compounds ("winston-salem") are single place names; a plain
    # isalpha() rejects them and silently fragments the city set.
    if not last.replace("-", "").isalpha():
        return None
    if len(words) >= 2 and words[-2].lower() in _CITY_SET_PRE_GUARD_WORDS:
        return None
    title = "-".join(part.title() for part in last.split("-"))
    if not _is_valid_destination_candidate(title, element):
        return None
    return title


def _city_set_lead_destination(element: str) -> Optional[str]:
    """Retry a failed separator element via its LEAD word (N-09b).

    A legitimate set member can carry a trailing time phrase the tail
    strippers do not cover ("thailand in december"); the whole element and
    its final word both fail and the run would silently truncate.  The lead
    word is retried ONLY when the element ends in a month/season tail —
    the actual N-09b failure shape — and under the same guards as the
    verb-pass span candidates (articles, stop words, months and seasons are
    never promoted), so prose and activity elements still cannot form sets.
    """
    if not _CITY_SET_TIME_TAIL_RE.search(element):
        return None
    words = element.split()
    if not words:
        return None
    lead = words[0]
    if not lead.isalpha():
        return None
    lower = lead.lower()
    if lower in _STOP_WORDS or lower in _MONTH_NAMES or lower in _SEASON_NAMES:
        return None
    # A two-word lead that itself resolves is the real member ("abu dhabi in
    # december" → "Abu Dhabi", not the fragment "Abu" via the single-word
    # retry). Mirrors the multi-word element path, which already keeps
    # hyphen/space-separated 2-word destinations intact.
    if len(words) >= 2 and words[1].isalpha():
        pair_title = f"{words[0].title()} {words[1].title()}"
        if _is_valid_destination_candidate(pair_title, element):
            return pair_title
    title = lead.title()
    if not _is_valid_destination_candidate(title, element):
        return None
    return title


def _is_origin_candidate(full_text: str, dest: str) -> bool:
    """True when a resolved destination candidate is actually the trip origin.

    Uses the trailing from-pattern ("...flying from London") — covering
    mid-text origins in destination enumerations. Deliberately excludes
    _is_likely_origin's leading-city heuristic, which misreads pure
    destination lists ("Bali or Thailand?") as "origin + content".

    Differently formatted raw tails ("flying from san francisco usa" vs the
    resolved canonical "Usa"/"San Francisco") never contain the literal
    "from <canonical>" span, so a tail-word fallback matches
    "from ... <last word of dest>" — bounded to two filler words and never
    across a directional "to", so "flying from delhi to boston" can't flag
    Boston as origin.
    """
    words = dest.split()
    if not words:
        return False
    if re.search(rf"\bfrom\s+{re.escape(dest.lower())}\b", full_text, re.IGNORECASE):
        return True
    last_word = re.escape(words[-1].lower())
    tail = (
        rf"\bfrom\s+"
        rf"(?:(?!(?:to|into|till|until)\s)\S+\s+){{0,2}}"
        rf"{last_word}\b"
    )
    return bool(re.search(tail, full_text, re.IGNORECASE))


def _extract_city_set(text_lower: str, full_text: str) -> Optional[Tuple[List[str], str]]:
    """Find a run of 2+ known destinations joined by ``+``, ``,`` or ``and``.

    "or" breaks a run — option semantics stay with the semi-open or-pattern.
    Every element must independently resolve to a known destination (bare
    1-3 word lowercase span, or via its final word), so activity clauses like
    "do a cooking class somewhere" can never form a set. Past-trip mentions
    are excluded like every other destination pass.
    """
    parts = re.split(r"(\+|,|\band\b|\bor\b)", text_lower, flags=re.IGNORECASE)
    best: List[str] = []
    best_raw: List[str] = []
    current: List[str] = []
    current_raw: List[str] = []
    for part in parts:
        sep = part.strip().lower()
        if sep in ("+", ",", "and", "or"):
            if sep == "or":
                if len(current) > len(best):
                    best, best_raw = current, current_raw
                current, current_raw = [], []
            continue
        element = part.strip()
        if not element:
            continue
        # The final member often carries a scheduling tail ("Tokyo + Kyoto
        # at 7pm").  Keep the city, discard only the time clause; otherwise
        # the final element fails validation and the set is silently truncated.
        element = _CITY_SET_TRAILING_TIME_RE.sub("", element).strip(" ,.;:!?\t")
        # A season-scale travel window belongs to date extraction, not to the
        # final city-set member (for example, "Kyoto next spring").
        element = _CITY_SET_TRAILING_SEASON_RE.sub("", element).strip(" ,.;:!?\t")
        if not element:
            continue
        dest: Optional[str] = None
        if _CITY_SET_ELEMENT_RE.match(element):
            title = element.title()
            if _is_valid_destination_candidate(title, element):
                dest = title
        if dest is None:
            dest = _last_word_destination(element)
        if dest is None:
            # Trailing phrase on a real member ("thailand in december"):
            # retry the lead word before breaking the run (N-09b).
            dest = _city_set_lead_destination(element)
        if dest is not None and _is_past_trip_mention(full_text, element):
            dest = None
        if dest is not None and _is_origin_candidate(full_text, dest):
            # Origin protection, same as the verb pass: a set member that is
            # actually the trip's origin city ("friends in London and Paris,
            # flying from London") must not become a destination candidate.
            dest = None
        if dest is None:
            if len(current) > len(best):
                best, best_raw = current, current_raw
            current, current_raw = [], []
        elif dest not in current:
            current.append(dest)
            current_raw.append(element)
    if len(current) > len(best):
        best, best_raw = current, current_raw
    if len(best) >= 2:
        return best, ", ".join(best_raw)
    return None


def _is_direction_side_reference(candidate: str, text_lower: str) -> bool:
    """True when a candidate appears as "<candidate> side" — Indian English
    for "that way / somewhere around <candidate>" (Pranay, 2026-09-14:
    "side jana hai" = heading that direction, destination not committed).

    "okinawa side trip?" stays a destination: the following trip-noun makes
    "side" an adjective on the compound, not the direction marker.
    """
    pattern = re.compile(r"\b" + re.escape(candidate.lower()) + r"\s+side\b")
    match = pattern.search(text_lower)
    if not match:
        return False
    return not _SIDE_TRIP_NOUN_RE.search(text_lower[match.end():match.end() + 40])


_SIDE_INTENT_CUES_RE = re.compile(
    r"\b(?:jaana|jana|jao|jiba|jib|going|plan|planning|trip|travel|visit"
    r"|chahiye|niklenge|ghumne|chale)\b",
    re.IGNORECASE,
)


def _has_bare_side_direction_intent(text_lower: str) -> bool:
    """True when a non-compound "<place> side" reference coexists with a
    travel-intent cue. Upstream exclusion (via _is_likely_origin) removes
    such a place from candidates before this layer — the direction intent
    must still report OPEN, not undecided."""
    for match in re.finditer(r"\b[a-z][a-z'-]+\s+side\b", text_lower):
        if _SIDE_TRIP_NOUN_RE.search(text_lower[match.end():match.end() + 40]):
            continue  # "okinawa side trip?" compound — real destination
        if _SIDE_INTENT_CUES_RE.search(text_lower):
            return True
    return False


def _extract_destination_candidates(text: str) -> Tuple[List[str], str, Optional[str]]:
    """Public extraction entry: applies the direction-reference guard
    ("<place> side" never fabricates a destination) on top of the raw
    extraction, then reports OPEN intent when the guard removed everything —
    the direction is real customer intent, so the intake must ask
    "whereabouts near <place>?" instead of committing or going silent."""
    candidates, status, raw = _extract_destination_candidates_unfiltered(text)
    if not candidates:
        if _has_bare_side_direction_intent(text.lower()):
            return [], "open", None
        return candidates, status, raw
    text_lower = text.lower()
    kept = [c for c in candidates if not _is_direction_side_reference(c, text_lower)]
    if len(kept) == len(candidates):
        return candidates, status, raw
    if kept:
        return kept, status, ", ".join(kept)
    # Every candidate was a "<place> side" direction reference: intent is
    # real, destination is unresolved — open the ask, never fabricate.
    return [], "open", None


def _extract_destination_candidates_unfiltered(text: str) -> Tuple[List[str], str, Optional[str]]:
    """
    Returns (candidates, status, raw_match).
    status: "definite" | "semi_open" | "open"

    Past-trip destination mentions are excluded to prevent contamination
    of current destination intent.

    Extraction order matters: hedging patterns ("maybe", "or") are checked
    before the general destination regex so that hedging context is
    preserved in status and raw_match.
    """
    # Never let raw untrusted text flow directly into the deterministic scans.
    # This is idempotent, so direct helper callers and the pipeline share the
    # same safety boundary.
    text, _ = _prepare_extraction_text(text)

    # Remove call-log metadata lines that frequently contain capitalized labels
    # (Caller, Referral, Pace, Budget, etc.) and pollute destination extraction.
    # Also strip leading salutations/greetings (Hi Sam, Dear Marcus, etc.)
    destination_text = "\n".join(
        line for line in text.splitlines()
        if not _DESTINATION_METADATA_LABELS_RE.match(line)
    )
    destination_text = _SALUTATION_RE.sub("", destination_text)
    if not destination_text.strip():
        destination_text = text

    text_lower = destination_text.lower()
    candidates: List[str] = []
    excluded_by_past_trip: List[str] = []

    # Explicit "Destinations: X, Y" or "Destination: X" pass (inline or multiline)
    dest_line_match = re.search(r"\bdestinations?\s*:\s*([^.\n]+)", destination_text, re.IGNORECASE)
    if dest_line_match:
        explicit_line = re.sub(r"\([^)]*\)", "", dest_line_match.group(1)).strip()
        explicit_candidates, explicit_status, explicit_raw = _extract_destination_candidates(explicit_line)
        if explicit_candidates:
            return explicit_candidates, explicit_status, explicit_raw

    # City-set separator pass: "tokyo + kyoto + osaka", "tokyo, kyoto and
    # osaka", "covering tokyo and kyoto". Every element must resolve to a
    # known destination, so this stays quiet on prose and activity clauses.
    city_set = _extract_city_set(text_lower, destination_text)
    if city_set:
        return city_set[0], "semi_open", city_set[1]

    # Check for "or" pattern (semi-open)
    or_match = _OR_DESTINATION_RE.search(destination_text)
    if or_match:
        c1 = or_match.group(1).title()
        c2 = or_match.group(2).title()
        c1_ok = _is_valid_destination_candidate(c1, text)
        c2_ok = _is_valid_destination_candidate(c2, text)
        if (c1_ok or c2_ok) and not _is_past_trip_mention(destination_text, or_match.group(0)):
            # Origin protection: "London and Paris, flying from London" must
            # not list the origin as a destination option.
            if c1_ok and _is_origin_candidate(text, c1):
                c1_ok = False
            if c2_ok and _is_origin_candidate(text, c2):
                c2_ok = False
            valid = []
            if c1_ok:
                valid.append(c1)
            if c2_ok:
                valid.append(c2)
            if valid:
                return valid, "semi_open", or_match.group(0)

    # Check for "maybe somewhere like X" pattern (semi-open) — before general regex
    maybe_like_match = _MAYBE_SOMEWHERE_LIKE_RE.search(text_lower)
    if maybe_like_match:
        dest = maybe_like_match.group(1).title()
        if is_known_destination(dest):
            return [dest], "semi_open", maybe_like_match.group(0)

    # Check for "somewhere like X" pattern (semi-open) — before general regex
    somewhere_like_match = _SOMEWHERE_LIKE_RE.search(text_lower)
    if somewhere_like_match:
        dest = somewhere_like_match.group(1).title()
        if is_known_destination(dest):
            return [dest], "semi_open", somewhere_like_match.group(0)

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
                        and _is_valid_destination_candidate(title, destination_text)
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
                if title.lower() in {"caller", "referral", "party", "pace", "budget", "interests", "follow-up", "follow_up", "toddler", "elderly", "promised", "not", "no", "date", "dates", "schengen", "visa", "visas", "passport", "passports", "booking", "bookings", "purpose", "purposes", "adult", "adults", "child", "children"}:
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

    # Lowercase/verb-less notes ("Bali in June 2027", "GOA trip for 2
    # adults") are still explicit destination-shaped statements.  Handle this
    # only when the candidate validates geographically and is not an origin or
    # past-trip mention; do not turn arbitrary lowercase prose into a city.
    for bare_match in _VERBLESS_DESTINATION_RE.finditer(destination_text):
        span = bare_match.group("destination").strip()
        words = span.split()
        # The regex is intentionally bounded, but resolve the shortest valid
        # prefix so "Bali trip" cannot become a multi-word false candidate.
        for end in range(min(3, len(words)), 0, -1):
            candidate = " ".join(words[:end])
            title = candidate.title()
            if (
                is_known_destination(title)
                and _is_valid_destination_candidate(title, destination_text)
                and not _is_likely_origin(destination_text, candidate)
                and not _is_past_trip_mention(destination_text, candidate)
            ):
                return [title], "definite", candidate

    # Fallback: context-gated lowercase destination extraction.
    # Only matches destinations appearing after travel verbs or before Hinglish/Odia
    # travel terms. Prevents false positives like "got" in "I got your number".
    if not candidates:
        seen_lower: Set[str] = set()

        def _verb_span_candidates(span: str) -> List[str]:
            """Candidate spans for a verb capture: the whole span, then its lead word.

            Verb-object captures over-terminate ("bali next month" from
            "hitting bali next month"); the leading word is retried because the
            destination directly follows the verb. Articles and stop heads are
            never promoted, so "a cooking class somewhere" stays clean.
            """
            spans = [span]
            words = span.split()
            first = words[0] if words else ""
            if (
                first
                and first != span
                and first.lower() not in _STOP_WORDS
                and first.lower() not in _MONTH_NAMES
                and first.lower() not in ("a", "an")
            ):
                spans.append(first)
            return spans

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
                for span in _verb_span_candidates(dest):
                    span_title = span.title()
                    if (is_known_destination(span_title)
                        and _is_valid_destination_candidate(span_title, destination_text)
                        and not _is_likely_origin(destination_text, span)
                        and not _is_past_trip_mention(destination_text, span)):
                        candidates.append(span_title)
                        raw_matches.append(span)
                        seen_lower.add(dest_lower)
                        break
        if len(candidates) >= 1:
            status = "definite" if len(candidates) == 1 else "semi_open"
            return candidates, status, ", ".join(raw_matches)

    # --- BROAD DESTINATION SWEEP (FND-0286 fallback) ---
    # If no pattern above matched, scan every word and bigram in the text
    # against the geography database. This catches destinations mentioned
    # without a recognized verb pattern — Hinglish ("bali chahiye"),
    # activity-first ("scuba diving is a MUST, maldives"), space-separated
    # ("tokyo kyoto osaka"), and informal party phrasings.
    if not candidates:
        sweep_candidates: List[str] = []
        seen_sweep = set()
        for match in re.finditer(r"[a-zA-Z][a-zA-Z'-]{1,30}", destination_text):
            start = match.start()
            word_clean = match.group(0).strip("'-").lower()
            if len(word_clean) < 3 or word_clean in _SWEEP_STOP_WORDS or word_clean in _SEASON_NAMES:
                continue
            if word_clean in seen_sweep:
                continue
            # Same shared placeholder filter the pattern paths use —
            # "Beach destination preferred" must not sweep up GeoNames'
            # town of Beach (adv_struct_005). Bigrams stay unfiltered:
            # compound names ("Virginia Beach") carry the placeholder as
            # the first word.
            if word_clean in _NON_DESTINATION_PLACEHOLDERS:
                continue
            # Shared past-trip checker (clause + span branches) — memories
            # never become current intent.
            if _is_past_trip_mention(destination_text, word_clean):
                continue
            if _is_likely_origin(destination_text, word_clean):
                continue
            if is_known_destination(word_clean):
                title = word_clean.title()
                if title not in seen_sweep:
                    sweep_candidates.append(title)
                    seen_sweep.add(title)
                    seen_sweep.add(word_clean)
        words = destination_text.split()
        for i in range(len(words) - 1):
            bigram = f"{words[i]} {words[i+1]}".strip(".,;:!?()[]").lower()
            if bigram in seen_sweep:
                continue
            if _is_likely_origin(destination_text, bigram):
                continue
            if is_known_destination(bigram):
                title = bigram.title()
                if title not in seen_sweep:
                    sweep_candidates.append(title)
                    seen_sweep.add(title)
                    seen_sweep.add(bigram)

        if sweep_candidates:
            status = "definite" if len(sweep_candidates) == 1 else "semi_open"
            return sweep_candidates, status, " | ".join(sweep_candidates)

    # Open intent only when "somewhere" sits in a destination-ish position
    # (after a travel verb, or followed by a place qualifier). A bare
    # "somewhere" inside an activity clause ("do a cooking class somewhere")
    # must not open the destination status.
    open_intent = bool(
        _SOMEWHERE_DEST_RE.search(text_lower) or _SOMEWHERE_OPEN_RE.search(text_lower)
    )
    return [], "open" if (open_intent or "any" in text_lower) else "undecided", None


# D-03 (ratified default, option b per D-04 research): a country mention whose
# cities are all inside it becomes a containing fact, never a sibling
# candidate. Longest aliases first so "united kingdom" wins over "uk".
_COUNTRY_MENTION_RE = re.compile(
    r"\b(?:" + "|".join(
        sorted((re.escape(alias) for alias in COUNTRY_CANONICAL_ALIASES), key=len, reverse=True)
    ) + r")\b"
)


def _resolve_destination_country(destination_text: str, candidates: List[str]) -> Optional[str]:
    """D-03 containment resolution: the canonical country name when the text
    names a country AND every geographically-resolvable destination candidate
    sits inside it.

    Returns the canonical country alias ("Japan") or None. None means no
    containment claim:
    - country-only notes keep the country as the destination candidate itself
      (existing contract — "10 days in Japan, you pick" -> ["Japan"]);
    - city candidates spanning another country (or unresolvable via
      ``get_city_country``) are left untouched rather than guessed;
    - city-level country aliases (Dubai / Singapore / Abu Dhabi) are city
      commitments, never containers.
    """
    if len(candidates) < 2:
        return None
    mention = _COUNTRY_MENTION_RE.search(destination_text.lower())
    if not mention:
        return None
    alias = mention.group(0)
    canonical = COUNTRY_CANONICAL_ALIASES.get(alias)
    if not canonical:
        return None
    country_iso = get_country_iso_code(alias)
    if not country_iso:
        return None
    # A second, different country alias among the candidates is genuine
    # multi-country scope — no containment projection. But city-level
    # country aliases (Dubai / Abu Dhabi / Singapore) resolve to no country
    # ISO, and candidates inside the mentioned country resolve to the SAME
    # ISO — neither is a second country, so "UAE trip covering Dubai and
    # Abu Dhabi" stays one contained country instead of misfiring on the
    # aliases these cities share via COUNTRY_CANONICAL_ALIASES.
    for candidate in candidates:
        if candidate == canonical:
            continue
        candidate_iso = get_country_iso_code(candidate)
        if candidate_iso is None or candidate_iso == country_iso:
            continue
        return None
    city_candidates = [c for c in candidates if c != canonical]
    resolved = [get_city_country(c) for c in city_candidates]
    resolving = [iso for iso in resolved if iso]
    if not resolving or any(iso != country_iso for iso in resolving):
        return None
    return canonical


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

    # Month/day range: "July 10 to July 16", "July 10-16", "July 10 to 16"
    month_day_range = _MONTH_DAY_RANGE_RE.search(text)
    if month_day_range:
        start_month = month_day_range.group(1)
        start_day = month_day_range.group(2)
        end_month = month_day_range.group(3) or start_month
        end_day = month_day_range.group(4)
        explicit_year = month_day_range.group(5)
        year = explicit_year or _infer_year_from_context(text)
        start_month_num = _month_to_num(start_month)
        end_month_num = _month_to_num(end_month)
        if start_month_num and end_month_num:
            start_iso = f"{year}-{start_month_num:02d}-{int(start_day):02d}"
            end_iso = f"{year}-{end_month_num:02d}-{int(end_day):02d}"
            raw = month_day_range.group(0).strip()
            return raw, start_iso, end_iso, "tentative"

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

    # Open-ended customer windows: "after July 10", "from July 10".
    # Keep the raw phrase as the canonical date_window even if the end date is unknown.
    after_month_day = _AFTER_MONTH_DAY_RE.search(text_lower)
    if after_month_day:
        raw = after_month_day.group(0).strip()
        month_num = _month_to_num(after_month_day.group(1))
        year = after_month_day.group(3) or _infer_year_from_context(text)
        if month_num:
            start_iso = f"{year}-{month_num:02d}-{int(after_month_day.group(2)):02d}"
            return raw, start_iso, None, "flexible_after"
        return raw, None, None, "flexible_after"

    # Single month: "March 2026"
    single_month = _SINGLE_MONTH_RE.search(text_lower)
    if single_month:
        raw = single_month.group(0)
        return raw, None, None, "flexible"

    # Single month without explicit year: "in July".
    single_month_no_year = _SINGLE_MONTH_NO_YEAR_RE.search(text_lower)
    if single_month_no_year:
        raw = single_month_no_year.group(0)
        return raw, None, None, "flexible"

    # "around March 2026", "sometime in May 2026"
    fuzzy = _FUZZY_MONTH_RE.search(text_lower)
    if fuzzy:
        raw = fuzzy.group(0)
        return raw, None, None, "flexible"

    # Season window: "next spring", "this winter", "in fall" (qualifier
    # required — bare season words are prose too often). A late/early/mid
    # month refinement in the same text is folded into the window
    # ("next spring (Mar-May), late march").
    season_match = _SEASON_RE.search(text_lower)
    if season_match:
        season = season_match.group(1).lower()
        start_abbr, end_abbr = _SEASON_MONTHS[season]
        window = f"{season_match.group(0).strip()} ({start_abbr}-{end_abbr})"
        month_refinement = _MODIFIER_MONTH_RE.search(text_lower)
        if month_refinement:
            window += f", {month_refinement.group(0).strip()}"
        return window, None, None, "flexible"

    # "late march" / "early june" / "mid september" without a preposition.
    modifier_month = _MODIFIER_MONTH_RE.search(text_lower)
    if modifier_month:
        return modifier_month.group(0).strip(), None, None, "flexible"

    return None


# D-01 (ratified default): explicit trip duration stated by the traveler —
# "10-12 days", "10 days", "7 nights", "1-2 weeks", "two weeks". The range
# form is tried first so "10-12 days" is never read as the single form
# "12 days". Number words reuse the party count vocabulary.
_TRIP_DURATION_RANGE_RE = re.compile(
    rf"\b(?P<low>{_COUNT_TOKEN_RE})\s*(?:-|–|—|\bto\b)\s*(?P<high>{_COUNT_TOKEN_RE})"
    r"\s+(?P<unit>days?|nights?|weeks?)\b",
    re.IGNORECASE,
)
_TRIP_DURATION_SINGLE_RE = re.compile(
    rf"\b(?P<count>{_COUNT_TOKEN_RE})\s+(?P<unit>days?|nights?|weeks?)\b",
    re.IGNORECASE,
)
# "within 2 days" / "next 10 days" are relative-time phrases, not trip length.
_TRIP_DURATION_GUARD_RE = re.compile(r"\b(?:within|next)\s+$", re.IGNORECASE)


def _extract_trip_duration(text: str) -> Optional[Dict[str, Any]]:
    """D-01: explicit traveler-stated trip length as a day range.

    Returns ``{"min": int, "max": int, "raw_text": str}`` or None. Only
    explicit "N days / N nights / N weeks" phrasings are parsed — duration is
    never silently projected from ISO date windows (that projection is a
    separate, undecided contract). Weeks convert at 7 days; nights keep the
    stated count.
    """
    if not text:
        return None

    def _count(token: str) -> Optional[int]:
        value = _count_token_to_int(token)
        return value if value and value > 0 else None

    for match in _TRIP_DURATION_RANGE_RE.finditer(text):
        if _TRIP_DURATION_GUARD_RE.search(text[max(0, match.start() - 8):match.start()]):
            continue
        low = _count(match.group("low"))
        high = _count(match.group("high"))
        if low and high and high >= low:
            unit = match.group("unit").lower()
            return {
                "min": low * 7 if unit.startswith("week") else low,
                "max": high * 7 if unit.startswith("week") else high,
                "raw_text": match.group(0).strip(),
            }

    for match in _TRIP_DURATION_SINGLE_RE.finditer(text):
        if _TRIP_DURATION_GUARD_RE.search(text[max(0, match.start() - 8):match.start()]):
            continue
        count = _count(match.group("count"))
        if count:
            unit = match.group("unit").lower()
            day_value = count * 7 if unit.startswith("week") else count
            return {
                "min": day_value,
                "max": day_value,
                "raw_text": match.group(0).strip(),
            }
    return None


# =============================================================================
# SECTION 3: BUDGET EXTRACTION
# =============================================================================

def _extract_budget(text: str) -> Optional[Dict[str, Any]]:
    """
    Returns structured budget dict or None.
    """
    text_lower = text.lower()

    def _currency_code(token: Optional[str]) -> str:
        normalized = (token or "").strip().lower()
        currency_map = {
            "$": "USD",
            "usd": "USD",
            "dollar": "USD",
            "dollars": "USD",
            "buck": "USD",
            "bucks": "USD",
            "€": "EUR",
            "eur": "EUR",
            "euro": "EUR",
            "euros": "EUR",
            "£": "GBP",
            "gbp": "GBP",
            "₹": "INR",
            "rs": "INR",
            "inr": "INR",
            "₦": "NGN",
            "ngn": "NGN",
            "r": "ZAR",
            "zar": "ZAR",
            "kes": "KES",
            "ghs": "GHS",
            "aed": "AED",
            "sar": "SAR",
            "jpy": "JPY",
            "cny": "CNY",
            "npr": "NPR",
            "lkr": "LKR",
            "php": "PHP",
            "myr": "MYR",
            "thb": "THB",
            "idr": "IDR",
            "mxn": "MXN",
            "brl": "BRL",
            "aud": "AUD",
            "cad": "CAD",
            "sgd": "SGD",
        }
        if normalized in currency_map:
            return currency_map[normalized]
        # D1 (RQ-01): unmarked amounts default to USD. Lakh/crore units are an
        # Indian-market signal and resolve to INR via _defaulted_currency,
        # which sees the matched region rather than the whole text.
        return "USD"

    def _defaulted_currency(unit_text: str) -> str:
        if re.search(r"\b(?:l|lac|lakh|lakhs|cr|crore|crores)\b", (unit_text or "").strip().lower()):
            return "INR"
        return "USD"

    def _looks_like_date_token(raw_val: str) -> bool:
        token = raw_val.strip()
        return bool(
            re.fullmatch(r"\d{4}\s*[-/]\s*\d{1,2}(?:\s*[-/]\s*\d{1,2})?", token)
            or re.fullmatch(r"\d{4}-\d{2}-\d{2}", token)
        )

    currency_token_pattern = (
        r"(usd|inr|eur|gbp|ngn|zar|kes|ghs|aed|sar|jpy|cny|npr|lkr|php|myr|thb|idr|mxn|brl|aud|cad|sgd|dollars?|bucks?|euros?|rupees?|₹|\$|€|£|₦|R)"
    )
    # Word-only token set for positions AFTER the amount: requires word
    # boundaries so "auditing"/"insist" can't be read as AUD/INR.
    currency_word_pattern = (
        r"(usd|inr|eur|gbp|ngn|zar|kes|ghs|aed|sar|jpy|cny|npr|lkr|php|myr|thb|idr|mxn|brl|aud|cad|sgd|dollars?|bucks?|euros?|rupees?)"
    )
    # S1 (RQ-01): natural phrasing stacks connectives ("budget is around $3000",
    # "Budget: Around $14,000", "budget is only 3000") — accept colons and connectives in any order.
    budget_connective = (
        r"(?:\s*[:\-]?\s*(?:of|is|was|only|around|about|approx(?:imately)?|roughly|up\s+to|under|at\s+most|no\s+more\s+than|maximum|max(?:imum)?|exactly|between|\s))*"
    )
    trailing_budget_match = re.search(
        r"(?:(?P<currency>" + currency_token_pattern + r")\s*)?"
        r"(?P<amount>\d[\d]*(?:,\d{3})*(?:\.\d+)?)\s*(?P<unit>l|k|m|mn|million|millions|lac|lakh|lakhs|crore|crores|cr|b|bn|billion|billions|thousand)?"
        r"\s*\bbudget\b",
        text_lower,
    )
    if trailing_budget_match:
        raw_amount = trailing_budget_match.group("amount").replace(",", "").strip()
        unit = (trailing_budget_match.group("unit") or "").strip().lower()
        if not _looks_like_date_token(raw_amount):
            parsed_value = float(raw_amount)
            if unit in ("l", "lac", "lakh", "lakhs"):
                parsed_value *= 100000
            elif unit in ("k", "thousand"):
                parsed_value *= 1000
            elif unit in ("m", "mn", "million", "millions"):
                parsed_value *= 1000000
            elif unit in ("cr", "crore", "crores"):
                parsed_value *= 10000000
            elif unit in ("b", "bn", "billion", "billions"):
                parsed_value *= 1000000000
            return {
                "raw_text": trailing_budget_match.group(0).strip(),
                "min": int(parsed_value),
                "max": int(parsed_value),
                "currency": _currency_code(trailing_budget_match.group("currency")),
            }

    range_budget_match = re.search(
        rf"\bbudget\b{budget_connective}\s*[:\-]?\s*"
        r"(?:(?P<currency>" + currency_token_pattern + r")\s*)?"
        r"(?P<low>\d[\d,]*(?:\.\d+)?)\s*"
        r"(?P<low_unit_prefix>l|k|m|mn|million|millions|lac|lakh|lakhs|crore|crores|cr|b|bn|billion|billions|thousand)?\s*"
        r"(?:-|–|—|\bto\b|\band\b)\s*"
        r"(?P<low_unit>l|k|m|mn|million|millions|lac|lakh|lakhs|crore|crores|cr|b|bn|billion|billions|thousand)?\s*"
        r"(?:(?P<currency_high>" + currency_token_pattern + r")\s*)?"
        r"(?P<high>\d[\d,]*(?:\.\d+)?)\s*"
        r"(?P<high_unit>l|k|m|mn|million|millions|lac|lakh|lakhs|crore|crores|cr|b|bn|billion|billions|thousand)?\b"
        r"(?:\s+(?P<currency_after>" + currency_word_pattern + r")\b)?",
        text_lower,
    )
    if range_budget_match:
        currency_tokens = [
            token
            for token in (
                range_budget_match.group("currency"),
                range_budget_match.group("currency_high"),
                range_budget_match.group("currency_after"),
            )
            if token
        ]
        normalized_currencies = {_currency_code(token) for token in currency_tokens}
        # A range with conflicting currency evidence is ambiguous.  Abstain
        # rather than silently treating the low endpoint's currency as the
        # whole range or inventing an exchange-rate conversion.
        if len(normalized_currencies) > 1:
            return None
        low = range_budget_match.group("low").replace(",", "").strip()
        high = range_budget_match.group("high").replace(",", "").strip()
        unit = (
            range_budget_match.group("low_unit_prefix")
            or range_budget_match.group("low_unit")
            or range_budget_match.group("high_unit")
            or ""
        ).strip().lower()
        if not _looks_like_date_token(low) and not _looks_like_date_token(high):
            low_value = float(low)
            high_value = float(high)
            if unit in ("l", "lac", "lakh", "lakhs"):
                low_value *= 100000
                high_value *= 100000
            elif unit in ("k", "thousand"):
                low_value *= 1000
                high_value *= 1000
            elif unit in ("m", "mn", "million", "millions"):
                low_value *= 1000000
                high_value *= 1000000
            elif unit in ("cr", "crore", "crores"):
                low_value *= 10000000
                high_value *= 10000000
            elif unit in ("b", "bn", "billion", "billions"):
                low_value *= 1000000000
                high_value *= 1000000000
            return {
                "raw_text": range_budget_match.group(0).strip(),
                "min": int(low_value),
                "max": int(high_value),
                "currency": (
                    _currency_code(currency_tokens[0])
                    if currency_tokens
                    else _defaulted_currency(unit)
                ),
            }

    explicit_label_match = re.search(
        rf"\bbudget\b{budget_connective}\s*[:\-]?\s*"
        r"(?:(?P<currency>" + currency_token_pattern + r")\s*)?"
        r"(?P<amount>\d[\d,]*(?:\.\d+)?)\s*(?P<unit>l|k|m|mn|million|millions|lac|lakh|lakhs|crore|crores|cr|b|bn|billion|billions|thousand)?\b"
        r"(?:\s+(?P<currency_after>" + currency_word_pattern + r")\b)?",
        text_lower,
    )
    if explicit_label_match:
        raw_amount = explicit_label_match.group("amount").replace(",", "").strip()
        unit = (explicit_label_match.group("unit") or "").strip().lower()
        if not _looks_like_date_token(raw_amount):
            parsed_value = float(raw_amount)
            if unit in ("l", "lac", "lakh", "lakhs"):
                parsed_value *= 100000
            elif unit in ("k", "thousand"):
                parsed_value *= 1000
            elif unit in ("m", "mn", "million", "millions"):
                parsed_value *= 1000000
            elif unit in ("cr", "crore", "crores"):
                parsed_value *= 10000000
            elif unit in ("b", "bn", "billion", "billions"):
                parsed_value *= 1000000000
            return {
                "raw_text": explicit_label_match.group(0).strip(),
                "min": int(parsed_value),
                "max": int(parsed_value),
                "currency": (
                    _currency_code(explicit_label_match.group("currency") or explicit_label_match.group("currency_after"))
                    if (explicit_label_match.group("currency") or explicit_label_match.group("currency_after"))
                    else _defaulted_currency(unit)
                ),
            }

    # Look for budget-like patterns
    patterns = [
        # Explicit budget with numeric range and optional unit suffix.
        rf"\bbudget\b{budget_connective}\s*[:\-]?\s*(\d+(?:\.\d+)?\s*(?:-|–|—|\bto\b)\s*\d+(?:\.\d+)?\s*(?:l|k|m|mn|million|millions|lac|lakh|lakhs|crore|crores|cr|b|bn|billion|billions|thousand)?)\b",
        # Explicit budget with single value + unit.
        rf"\bbudget\b{budget_connective}\s*[:\-]?\s*(\d+(?:\.\d+)?\s*(?:l|k|m|mn|million|millions|lac|lakh|lakhs|crore|crores|cr|b|bn|billion|billions|thousand))\b",
        # Budget-like value with unit when budget keyword may be omitted.
        r"\b(?:around|about|approx(?:imately)?)\s+(\d+(?:\.\d+)?\s*(?:l|k|m|mn|million|millions|lac|lakh|lakhs|crore|crores|cr|b|bn|billion|billions|thousand))\b",
        # Plain number only accepted with explicit budget keyword.
        rf"\bbudget\b{budget_connective}\s*[:\-]?\s*(\d{4,})\b",
        # Bare number with L/K suffix (no keyword needed).
        r"\b((?:\d+(?:\.\d+)?)\s*(?:l|k|m|mn|million|millions|lac|lakh|lakhs|crore|crores|cr|b|bn|billion|billions|thousand))\b",
    ]
    for pat in patterns:
        m = re.search(pat, text_lower)
        if m:
            raw = m.group(1).strip()
            if _looks_like_date_token(raw):
                continue
            parsed = Normalizer.parse_budget(raw)
            # D1 (RQ-01): parse_budget defaults INR; unmarked non-lakh amounts
            # are USD. Lakh/crore-shaped raws keep INR (Indian-market signal).
            if parsed.get("currency") == "INR" and not re.search(
                r"\d(?:\.\d+)?\s*(?:l|lac|lakh|lakhs|crore|crores|cr)\b", raw
            ):
                parsed["currency"] = "USD"
            parsed["raw_text"] = raw
            return parsed

    # S3 (RQ-01): keyword-free anchors — "have 3500 to spend", "between 4000
    # and 6000", "spend about 200 bucks a day". Deliberately NO bare "of"
    # anchor: it false-positives on "family of 4". Amounts under 100 are
    # rejected — "have 2 kids" is not a budget.
    anchor_match = re.search(
        r"(?:\bbetween\b|\bhave\b|\bspend(?:ing)?\b)"
        r"(?:\s+(?:about|around|roughly))?"
        r"\s*[:\-]?\s*"
        r"(?P<amount>\d[\d,]*(?:\.\d+)?)"
        r"(?:\s+(?:and|to|-|\u2013|\u2014)\s+(?P<high>\d[\d,]*(?:\.\d+)?))?"
        r"\s*(?P<unit>l|k|m|mn|million|millions|lac|lakh|lakhs|crore|crores|cr|b|bn|billion|billions|thousand)?\b"
        r"(?:\s+(?P<currency_after>" + currency_word_pattern + r")\b)?",
        text_lower,
    )
    if anchor_match:
        raw_amount = anchor_match.group("amount").replace(",", "").strip()
        unit = (anchor_match.group("unit") or "").strip().lower()
        if not _looks_like_date_token(raw_amount) and float(raw_amount) >= 100:
            parsed_value = float(raw_amount)
            max_value = parsed_value
            if unit in ("l", "lac", "lakh", "lakhs"):
                parsed_value *= 100000
                max_value = parsed_value
            elif unit in ("k", "thousand"):
                parsed_value *= 1000
                max_value = parsed_value
            elif unit in ("m", "mn", "million", "millions"):
                parsed_value *= 1000000
                max_value = parsed_value
            elif unit in ("cr", "crore", "crores"):
                parsed_value *= 10000000
                max_value = parsed_value
            elif unit in ("b", "bn", "billion", "billions"):
                parsed_value *= 1000000000
                max_value = parsed_value
            high = anchor_match.group("high")
            if high:
                max_value = float(high.replace(",", "").strip())
            cur_token = anchor_match.group("currency_after")
            return {
                "raw_text": anchor_match.group(0).strip(),
                "min": int(parsed_value),
                "max": int(max_value),
                "currency": _currency_code(cur_token) if cur_token else _defaulted_currency(unit),
            }

    # "flexible" budget
    if _FLEXIBLE_BUDGET_RE.search(text_lower):
        return {"raw_text": "flexible", "min": None, "max": None, "currency": "USD"}

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
        "dates flexible", "flexible on date", "anytime in", "flexible within",
        "can shift", "+/-", "flexible +/-", "+-", "plus minus",
        "plus or minus", "give or take",
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
    # S5 (RQ-01): firm-budget markers (golden convention).
    if re.search(r"\b(?:max(?:imum)?|only|no\s+more\s+than|exactly|at\s+most)\b", text.lower()):
        return "firm"
    return "unknown"


_AMOUNT_RE = re.compile(r"(?:usd|eur|gbp|inr|chf|sgd|aud|cad|[$€£₹]|\b\d[\d,.]*\s*k?\b|\blakhs?\b|\b Lakhs?\b)", re.IGNORECASE)


def _budget_scope_sentences(text: str) -> List[str]:
    """Split into sentence-like segments, keep only amount-bearing ones.

    Sim #2 (FND-0273): cue phrases like 'a day' scattered through a
    multi-voice thread must not override an explicit total — scope cues are
    only meaningful inside a sentence that carries a budget amount.
    """
    parts = re.split(r"(?<=[.!?])\s+|\n+", text)
    return [p for p in parts if p and _AMOUNT_RE.search(p)]


def _extract_budget_scope(text: str) -> str:
    # Realignment Phase 1 (2026-09-13): scope cues are only evaluated inside
    # amount-bearing segments. Priya's "3.5 lakhs total … hard cap" must keep
    # outranking Arjun's number-free "budget whatever, we'll manage" (Sim #2,
    # FND-0273), and unrelated "a … day" phrases elsewhere in the thread must
    # never flip the scope at all.
    sentences = _budget_scope_sentences(text)
    if not sentences:
        return "unknown"

    def scope_of(segment: str) -> str:
        seg_lower = segment.lower()
        if any(p in seg_lower for p in ("per person", "per head", "per pax", "per traveller", "per traveler", "pp", "p/p", "a head", "a person")):
            return "per_person"
        if "per night" in seg_lower or "a night" in seg_lower:
            return "per_night"
        if re.search(r"\b(?:a|per)\s+day\b", seg_lower):
            return "daily"
        # Explicit trip-total markers outrank a stray "each" elsewhere in the sentence
        if _TOTAL_GROUP_RE.search(seg_lower):
            return "total"
        if re.search(
            r"(?:usd|eur|gbp|inr|chf|sgd|aud|cad|[$€£₹]|\b\d[\d,.]*\s*k?)\s*(?:each|pp|p/p|per\s+pax|per\s+person|per\s+head)\b"
            r"|\beach\s+(?:person|traveler|traveller|adult|guest|of\s+us)\b",
            seg_lower,
        ):
            return "per_person"
        return "unknown"

    # Explicit total with an amount is authoritative: it wins over per-unit
    # cues found in other amount-bearing segments (precedence, not
    # last-writer-wins).
    for segment in sentences:
        scope = scope_of(segment)
        if scope == "total":
            return scope
    for segment in sentences:
        scope = scope_of(segment)
        if scope != "unknown":
            return scope
    return "unknown"



def _extract_flight_hotel_mismatch(text: str) -> Optional[Dict[str, str]]:
    """Detect a likely flight-arrival vs hotel-check-in timing mismatch."""
    text_lower = text.lower()
    if "flight" not in text_lower or "hotel" not in text_lower:
        return None

    flight_match = re.search(
        r"(?:flight|arriv\w+|lands?)\D{0,40}(?:at\s+)?(?P<time>\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\D{0,20}on\s+(?P<date>\d{1,2}\s+[a-z]+)",
        text_lower,
    )
    hotel_patterns = (
        # "hotel check-in is afternoon on 10 july"
        r"(?:hotel|check[- ]?in).*?(?P<label>morning|afternoon|evening|late|same day|later that day).*?on\s+(?P<date>\d{1,2}\s+[a-z]+)",
        # "hotel check-in on 10 july afternoon"
        r"(?:hotel|check[- ]?in).*?on\s+(?P<date>\d{1,2}\s+[a-z]+)(?:\s+(?P<label>morning|afternoon|evening|late|same day|later that day))?",
    )
    hotel_match = None
    for pattern in hotel_patterns:
        hotel_match = re.search(pattern, text_lower)
        if hotel_match:
            break
    if not flight_match or not hotel_match:
        return None

    flight_date = flight_match.group("date")
    hotel_date = hotel_match.group("date")
    if flight_date != hotel_date:
        return None

    label = (hotel_match.group("label") or "").strip()
    if label not in {"afternoon", "evening", "late", "same day", "later that day"}:
        return None

    time_text = flight_match.group("time").strip()
    time_match = re.search(r"(?P<hour>\d{1,2})(?::(?P<minute>\d{2}))?\s*(?P<meridiem>am|pm)?", time_text)
    if not time_match:
        return None

    hour = int(time_match.group("hour"))
    minute = int(time_match.group("minute") or "0")
    meridiem = time_match.group("meridiem")
    if meridiem == "pm" and hour != 12:
        hour += 12
    elif meridiem == "am" and hour == 12:
        hour = 0

    # Flag only clearly late arrivals on same-day check-in requests.
    if hour < 18 and not (hour == 17 and minute >= 30):
        return None

    return {
        "flight_date": flight_date,
        "hotel_date": hotel_date,
        "arrival_time": time_text,
        "hotel_label": label,
    }


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
    Returns {party_size, party_composition, child_ages, group_signals}.
    group_signals carries raw group phrasings seen in the text (converted or
    not) so validation can warn when the headcount looks underdetected.
    """
    composition: Dict[str, int] = {}
    child_ages: List[float] = []
    group_signals: List[str] = []
    text_lower = text.lower()
    family_group_size = 0

    for signal_match in _PARTY_GROUP_SIGNAL_RE.finditer(text_lower):
        group_signals.append(signal_match.group(0))

    # Family composition from natural language
    _FAMILY_PATTERNS = [
        (r"\b(?:me|myself|i)\b", "adults", 1),
        (r"\b(?:my\s+)?(?:wife|husband|spouse|gf|girlfriend|bf|boyfriend|partner|fianc[eé]e?)\b", "adults", 1),
        (r"\bmy\s+(?:parents|mom\s+and\s+dad|mum\s+and\s+dad)\b", "adults", 2),
        (r"\bmy\s+(?:mother|father|mom|mum|dad)\b", "adults", 1),
        (r"\bmy\s+(?:grandparents?)\b", "elderly", 1),
    ]
    has_partner = bool(re.search(r"\b(?:my\s+)?(?:wife|husband|spouse|gf|girlfriend|bf|boyfriend|partner|fianc[eé]e?)\b", text_lower))
    for pattern, group, count in _FAMILY_PATTERNS:
        if re.search(pattern, text_lower):
            composition[group] = composition.get(group, 0) + count

    # Travel with partner/spouse implies speaker + partner (at least 2 adults)
    if has_partner and composition.get("adults", 0) < 2:
        composition["adults"] = 2

    # "me and 3 friends" → self + N companions. The bare-friends variant only
    # runs when the self-joined phrasing is absent, so the same companions are
    # never double-counted ("me and my wife and 2 friends" → wife +1, friends +2).
    self_plus_friends = _SELF_PLUS_FRIENDS_RE.search(text_lower)
    if self_plus_friends:
        companions = _count_token_to_int(self_plus_friends.group("count")) or 0
        if self_plus_friends.group("self") == "us":
            # The me/myself/I self pattern above doesn't match "us" — count
            # the speaker once (conservative: the size of "us" is unknown).
            # "one of us" member references stay signals, never party_size=1.
            composition["adults"] = composition.get("adults", 0) + 1
        composition["adults"] = composition.get("adults", 0) + companions
    else:
        friends_match = _FRIENDS_RE.search(text_lower)
        if friends_match:
            companions = _count_token_to_int(friends_match.group("count")) or 0
            composition["adults"] = composition.get("adults", 0) + companions

    family_size_match = re.search(
        rf"\b(?:family|group|party)\s+(?:of\s+)?(?P<count>{_COUNT_TOKEN_RE})",
        text_lower,
    )
    if family_size_match:
        family_group_size = _count_token_to_int(family_size_match.group("count")) or 0

    # Whole-group colloquial counts: "4 of us", "the four of us".
    # "one of us" references a single member (implies a group without a size),
    # so it stays a signal and never becomes party_size=1.
    of_us_match = _OF_US_RE.search(text_lower)
    if of_us_match:
        of_us_size = _count_token_to_int(of_us_match.group("count")) or 0
        if of_us_size > 1:
            family_group_size = max(family_group_size, of_us_size)

    # Couple / pair / duo phrasing is a common shorthand for two adults.
    # Only infer this when no other party composition has already been stated,
    # so explicit counts or richer composition cues still win.
    if not composition and re.search(r"\b(?:a\s+)?(?:couple|pair|duo)\b", text_lower):
        composition["adults"] = 2

    # Child with decimal age: "1.7 year old kid", "2.5yr old"
    dec_age = re.search(r"(\d+\.?\d*)\s*(?:years?|yr|y)[\s-]*(?:old|aged?)\s+(?:kid|child|baby|toddler|son|daughter)", text_lower)
    if dec_age:
        composition["children"] = composition.get("children", 0) + 1
        child_ages.append(float(dec_age.group(1)))
    elif not dec_age and not family_group_size:
        # Singular child without number: "our kid", "a toddler", or bare "bachha"
        singular_child = re.search(
            r"\b(?:(?:my|our|a)\s+)?(?:kid|child|baby|toddler|son|daughter|bachha)\b(?!\s+ages?\b)(?!\s+age\b)",
            text_lower,
        )
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
        adult_count = _count_token_to_int(adult_match.group(1))
        if adult_count:
            composition["adults"] = adult_count

    # Children — match "2 children" or bare "child/kid" or Hinglish "bachhe"/"bache"/"baccha"
    child_match = re.search(rf"(?:(?P<count>{_COUNT_TOKEN_RE})\s+)?(?:kids?|children?|child|bachhe|bache|baccha)", text_lower)
    if child_match and child_match.group("count"):
        child_count = _count_token_to_int(child_match.group("count"))
        if child_count:
            composition["children"] = child_count
    # Try to extract ages: "kids ages 8 and 12", "children aged 5, 7", "child age 3"
    ages_match = re.search(
        r"(?:kids?|children?|child|ages?|bachhe|bache|baccha)\s+(?:ages?\s+)?(\d+(?:\s*,\s*\d+)*(?:\s*,?\s*and\s*\d+)?)",
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
        composition["elderly"] = _count_token_to_int(elderly_match.group(2)) or 1
    elif _ELDERLY_RE.search(text_lower):
        composition.setdefault("elderly", 1)

    # Total party size
    party_size = sum(composition.values())

    if family_group_size > party_size:
        party_size = family_group_size

    # Prefer explicit stated headcount when present (e.g., "6 pax", "6 people").
    # If explicit and inferred counts conflict, explicit caller-provided count wins.
    explicit_size_match = _PEOPLE_RE.search(text_lower)
    explicit_party_size = _count_token_to_int(explicit_size_match.group(1)) if explicit_size_match else None
    if explicit_party_size and explicit_party_size > 0:
        party_size = explicit_party_size

    # Fallback: "N people" / "N guests"
    if party_size == 0:
        pax_match = re.search(
            rf"(?P<count>{_COUNT_TOKEN_RE})\s*(?:[-–—]?\s*)?(?:people|persons?|pax|travelers?|travellers?"
            r"|guests?(?!\s*(?:lists?|houses?|rooms?|books?|bed(?:room)?s?|bath(?:room)?s?)\b))",
            text_lower,
        )
        if pax_match:
            party_size = _count_token_to_int(pax_match.group("count")) or 0

    return {
        "party_size": party_size,
        "party_composition": composition,
        "child_ages": child_ages,
        "group_signals": group_signals,
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
        # VFR (visiting friends & relatives) is a real travel segment with
        # its own visa/accommodation profile — "visit family in india"
        # means India IS the destination (owner challenge, 2026-09-13).
        "family_visit": r"\b(?:visit|visiting|see|seeing|meet)\s+"
                        r"(?:my\s+|our\s+)?(?:family|relatives|grandparents|"
                        r"grandma|grandparents|in[\s-]?laws|cousins?|parents)\b",
        "honeymoon": r"\b(honeymoon|romantic)\b",
        "business": r"\b(business|conference|meeting|corporate|company|work\s+trip|workshop|training|procurement|offsite|team\s+offsite|incentive)\b",
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
                          "sightseeing", "attractions", "landmarks", "tourist",
                          "beach resort", "kids club", "villa", "resort"}
        _FAMILY_HINTS = {"kid", "kids", "child", "children", "toddler", "baby",
                         "parents", "family", "wife", "husband",
                         "bachhe", "bache", "baccha"}
        hints_found = sum(1 for h in _LEISURE_HINTS if h in text_lower)
        family_found = any(h in text_lower for h in _FAMILY_HINTS)
        if hints_found >= 1 and family_found:
            results["trip_purpose"] = "family leisure"
        elif hints_found >= 1:
            results["trip_purpose"] = "leisure"

    # Activity / experience interests.
    activity_interests: List[str] = []
    _ACTIVITY_SIGNAL_PATTERNS = {
        "sightseeing": r"\b(partial\s+sightseeing|sightseeing|city\s+tour|guided\s+tour|local\s+tour)\b",
        "beach time": r"\b(beach\s+time|beach\s+day|by\s+the\s+beach|seaside)\b",
        "business offsite": r"\b(corporate\s+offsite|offsite|team\s+offsite|procurement|approval[-\s]?ready)\b",
    }
    for label, pattern in _ACTIVITY_SIGNAL_PATTERNS.items():
        if re.search(pattern, text_lower):
            activity_interests.append(label)
    if activity_interests:
        results["activity_interests"] = activity_interests

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
    no_match = re.findall(r"(?:no|don'?t\s+(?:want|need|book)|avoid|never|not\s+interested\s+in|not\s+looking\s+for)\s+([^.,]+)", text_lower)
    for constraint in no_match:
        constraint = constraint.strip()
        headword = constraint.split(None, 1)[0] if constraint else ""
        if headword in _NEGATION_KNOWLEDGE_HEADWORDS:
            # "no idea of the name" / "no clue about dates" — traveler
            # uncertainty about their own note, not a hard constraint.
            continue
        normalized = _normalize_constraint(constraint)
        if normalized:
            hard.append(normalized)

    # Fear-phrased safety constraints (FND-0275, Sim #2): "terrified of
    # heights", "afraid of water", "scared of crowds" — no "no" prefix, so
    # the negation scan never saw them. Safety-critical; must not drop.
    # Terminator stops the object at the fear itself ("heights so please…"
    # must not swallow the whole following clause).
    for fear_match in re.finditer(
        r"(?:terrified|afraid|scared|phobic)\s+of\s+([^.,;()\n]+?)"
        r"(?:\s+(?:so|and|but|because|please|also)\b|[.,;()\n]|$)",
        text_lower,
    ):
        fear_obj = fear_match.group(1).strip()
        if fear_obj and fear_obj.split(None, 1)[0] not in _NEGATION_KNOWLEDGE_HEADWORDS:
            hard.append(f"fear of {fear_obj}")

    if hard:
        results["hard_constraints"] = hard

    # Occasion anchors (Sim #2): "10th anniversary on the trip (april 14th)",
    # "anniversary is april 14" — a hard date the trip must cover, distinct
    # from the travel window.
    # Occasion anchors (Sim #2): "10th anniversary on the trip (april 14th)",
    # "anniversary is april 14" — a hard date the trip must cover, distinct
    # from the travel window. Both "april 14" and "14 april" orders supported.
    _OCCASION_DATE = (
        r"(?:\b(?:january|february|march|april|may|june|july|august|september|"
        r"october|november|december)\s+\d{1,2}(?:st|nd|rd|th)?"
        r"|\b\d{1,2}(?:st|nd|rd|th)?\s+(?:january|february|march|april|may|"
        r"june|july|august|september|october|november|december))"
    )
    occasion_match = re.search(
        r"(anniversary|birthday|honeymoon)\b[^.,;()\n]{0,40}?"
        r"[(\s](" + _OCCASION_DATE + r")\b",
        text_lower,
    )
    if occasion_match:
        results["occasion"] = {
            "type": occasion_match.group(1),
            "date": occasion_match.group(2),
        }

    # Speaker self-identification (L2 attribution v1, Sim #2 FND-0275):
    # "meera here", "it's arjun", "[forwarded voice note from X]" — notes in a
    # delegation thread are per-speaker; captured now so a later travelers[]
    # structure can bind facts to people. Multi-word names allowed.
    speakers: List[str] = []
    seen_lower = set()
    for speaker_match in re.finditer(
        r"(?:\bit'?s\s+([a-z][a-z'\s]{1,25}?)\s+here\b"
        r"|([a-z][a-z'\s]{1,25}?)\s+here\b"
        r"|(?:voice\s+note|message|note)\s+from\s+([a-z][a-z'\s]{1,25}?))\b"
        r"(?=\s*[)\](.,;\n—–]|\s*$)",
        text,
        re.IGNORECASE,
    ):
        name = next(g for g in speaker_match.groups() if g)
        name = re.sub(r"\s+", " ", name.strip().title())
        if name and name.lower() not in seen_lower:
            seen_lower.add(name.lower())
            speakers.append(name)
    if speakers:
        results["speakers"] = speakers

    soft = []
    want_match = re.findall(r"(?:want|prefer|like|love|interested\s+in)\s+([^.,]+)", text_lower)
    for pref in want_match:
        candidate = pref.strip()
        normalized = _normalize_constraint(candidate)
        # Guard against negation bleed-through from phrases like
        # "don't want it rushed", which should stay a hard constraint.
        if normalized == "relaxed pace":
            continue
        # Fragment guard (Sim #2, FND-0275): "that day would mean a lot"
        # produced soft_preferences=['that'] — a single stop-word fragment
        # is noise, not a preference.
        if len(candidate.split()) < 2:
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
        "premium hotel": r"\b(luxury\s+(?:experience|stay|resort|hotel)|premium\s+(?:experience|stay|hotel|resort)|upscale\s+(?:hotel|resort|stay))\b",
        "mid-range hotel": r"\b(mid[-\s]?range\s+(?:hotel|resort|stay|property)|midmarket\s+(?:hotel|resort|stay)|mid\s+range\s+(?:hotel|resort|stay))\b",
        "budget hotel": r"\b(budget\s+(?:hotel|resort|stay|property)|economy\s+(?:hotel|resort|stay))\b",
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
        "airport transfers": r"\b(airport\s+transfers?|airport\s+picks?|airport\s+pickup(?:s)?|airport\s+drop(?:s)?|transfers?\s+from\s+airport)\b",
        "meeting room": r"\b(meeting\s+room(?:s)?|conference\s+room(?:s)?|board\s+room(?:s)?)\b",
        "rooming lists": r"\b(rooming\s+list(?:s)?|room\s+list(?:s)?|rooming\s+separation|separate\s+rooming\s+lists?)\b",
        "fast quote": r"\b(fast\s+quote|quick\s+quote|quote\s+quickly|speedy\s+quote|approval[-\s]?ready\s+summary)\b",
        "hotel blocks": r"\b(hotel\s+block(?:s)?|room\s+block(?:s)?|mid[-\s]?to[-\s]?upscale\s+hotel\s+blocks?|upscale\s+hotel\s+blocks?)\b",
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
        # Negation-aware ordering (VA-06, 2026-09-09): check "no visa
        # required/needed" forms BEFORE the generic "required" substring,
        # which would otherwise invert them; and treat "no visa(s) yet" /
        # "don't have a visa" as required-but-not-applied rather than
        # not_required. Both inversions existed before this fix.
        # Review cycle 1 (2026-09-09): (a) negated "visa-free" phrases
        # ("don't have visa-free transit") must resolve to required, not
        # not_required — a substring ordering alone cannot fix that, so they
        # get an explicit pre-check; (b) "visa pending" means APPLIED and
        # in-process — its own status, distinct from not_applied (which the
        # decision engine treats as a critical booking blocker at
        # decision.py's visa_not_applied check).
        not_required_forms = ("no visa required", "no visa needed", "visa not required", "visa-free", "visa free")
        not_applied_forms = ("no visa yet", "no visas yet", "visa not applied", "haven't got visa", "haven't got a visa", "don't have visa", "don't have a visa")
        negated_visa_free = re.search(r"(?:don'?t|doesn'?t|not|never)\s+(?:have\s+)?(?:a\s+)?visa[-\s]?free", text_lower)
        if negated_visa_free:
            results["visa_status"] = {"requirement": "required", "status": "not_applied"}
        elif "visa pending" in text_lower or "visa is pending" in text_lower:
            results["visa_status"] = {"requirement": "required", "status": "pending"}
        elif any(p in text_lower for p in not_required_forms):
            results["visa_status"] = {"requirement": "not_required"}
        elif "approved" in text_lower or "got visa" in text_lower:
            results["visa_status"] = {"requirement": "required", "status": "approved"}
        elif any(p in text_lower for p in not_applied_forms) or "required" in text_lower or "need visa" in text_lower:
            results["visa_status"] = {"requirement": "required", "status": "not_applied"}
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


def extract_flight_inclusiveness(text: str) -> str:
    """
    Contract D-02: Returns one of:
    - 'INCLUDE_FLIGHTS' (explicitly requesting airfare/flights)
    - 'EXCLUDE_FLIGHTS' (flights already booked / land-only inquiry)
    - 'UNSPECIFIED_AMBIGUOUS' (not stated or ambiguous)
    """
    text_lower = text.lower()

    # 1. Exclusion patterns
    if re.search(r"\b(flights?\s+(?:already\s+)?booked|have\s+(?:our\s+)?own\s+flights?|already\s+have\s+(?:tickets?|flights?)|hotel\s+only|land\s+only|exclude\s+flights?|no\s+flights?\s+needed|flight\s+not\s+required)\b", text_lower):
        return "EXCLUDE_FLIGHTS"

    # 2. Inclusion patterns
    if re.search(r"\b(include\s+flights?|need\s+flights?|flights?\s+needed|with\s+flights?|book\s+flights?|flights?\s*\+\s*hotel|airfare\s+included|flight\s+options?|quote\s+with\s+flights?)\b", text_lower):
        return "INCLUDE_FLIGHTS"

    return "UNSPECIFIED_AMBIGUOUS"


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
            safe_text, safety_counts = _prepare_extraction_text(text)
            all_texts.append(safe_text)
            if any(safety_counts.values()):
                safety_meta = packet.metadata.setdefault("input_safety", {
                    "sanitized": True,
                    "control_chars_removed": 0,
                    "instruction_spans_removed": 0,
                })
                safety_meta["control_chars_removed"] += safety_counts["control_chars_removed"]
                safety_meta["instruction_spans_removed"] += safety_counts["instruction_spans_removed"]

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

    @staticmethod
    def _epistemic_for_authority(authority: str) -> str:
        """Map an AuthorityLevel to an EpistemicStatus.

        FACT: manually overridden or explicitly stated by the traveler/owner.
        INFERRED: derived by NLP or a deterministic signal.
        ASSUMED: defaulted by system business rules or a soft hypothesis.
        UNKNOWN: unresolved or absent authority.
        """
        if AuthorityLevel.is_fact(authority):
            return EpistemicStatus.FACT
        if authority in (AuthorityLevel.DERIVED_SIGNAL, AuthorityLevel.SOFT_HYPOTHESIS):
            return EpistemicStatus.INFERRED if authority == AuthorityLevel.DERIVED_SIGNAL else EpistemicStatus.ASSUMED
        return EpistemicStatus.UNKNOWN

    def _make_slot(self, value: Any, confidence: float, authority: str,
                    excerpt: str, envelope_id: str, extraction_mode: str = "direct_extract",
                    maturity: Optional[str] = None, notes: Optional[str] = None,
                    epistemic_status: Optional[str] = None) -> Slot:
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
            epistemic_status=epistemic_status or self._epistemic_for_authority(authority),
        )

    def _extract_from_freeform(self, envelope: SourceEnvelope, packet: CanonicalPacket, stage: str = "discovery") -> None:
        text, _ = _prepare_extraction_text(envelope.content)
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
                # D-03: a country mention contained by its own cities becomes
                # a separate destination_country fact and is dropped from the
                # flat candidate list. Country-only notes keep the country as
                # the candidate itself (existing contract).
                destination_country_scope = _resolve_destination_country(
                    text, dest_candidates
                )
                if destination_country_scope and destination_country_scope in dest_candidates:
                    dest_candidates = [
                        c for c in dest_candidates if c != destination_country_scope
                    ]
                packet.set_fact("destination_candidates", self._make_slot(
                    dest_candidates if dest_candidates else [],
                    0.7 if dest_status == "semi_open" else 0.5,
                    AuthorityLevel.EXPLICIT_USER,
                    dest_raw or "not specified",
                    eid,
                ))
                if destination_country_scope:
                    country_mention = re.search(
                        rf"\b{re.escape(destination_country_scope)}\b", text, re.IGNORECASE
                    )
                    packet.set_fact("destination_country", self._make_slot(
                        destination_country_scope, 0.85, AuthorityLevel.EXPLICIT_USER,
                        country_mention.group(0) if country_mention else destination_country_scope,
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
                    # D-02 types belong to the budget field family — a city-set
                    # raw element can carry a preceding flights clause
                    # ("...includes flights. thinking tokyo") which must not
                    # be mis-attributed to destination_candidates.
                    if amb.ambiguity_type == "flights_inclusiveness_unknown":
                        continue
                    packet.add_ambiguity(amb)
            # Also run ambiguity detection on the relevant source text span
            # around the destination mention for richer detection.
            #
            # Keep this pass limited to genuinely open destination states.
            # Broad destination context can include unrelated "or" phrases
            # from rooming or logistics requests and should not downgrade an
            # explicit single destination into an unresolved alternative.
            dest_context = _extract_relevant_span(text, dest_raw or "", window=80)
            if dest_status != "definite" and dest_context and dest_context != dest_raw:
                for amb in Normalizer.detect_ambiguities("destination_candidates", dest_context):
                    # D-02 types belong to the budget field family — the
                    # flights clause often precedes the destination span and
                    # must not be mis-attributed to destination_candidates.
                    if amb.ambiguity_type == "flights_inclusiveness_unknown":
                        continue
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
                    # FND-0276 verbatim invariant: quote the input span the
                    # candidates came from when it's a verbatim substring;
                    # otherwise label the rendering as derived — never show
                    # synthesized text as if the traveler wrote it.
                    raw_quote = dest_raw or " or ".join(dest_candidates)
                    if raw_quote.lower() not in text.lower():
                        raw_quote = f"derived from extracted candidates: {raw_quote}"
                    packet.add_ambiguity(Ambiguity(
                        field_name="destination_candidates",
                        ambiguity_type="unresolved_alternatives",
                        raw_value=raw_quote,
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

        # D-01: explicit trip duration ("10-12 days") as an informational
        # traveler-stated fact. Not part of INTAKE_MINIMUM/QUOTE_READY this
        # wave; duration is never silently projected from date windows.
        duration_result = _extract_trip_duration(text)
        if duration_result:
            packet.set_fact("trip_duration_days", self._make_slot(
                {"min": duration_result["min"], "max": duration_result["max"]},
                0.9, AuthorityLevel.EXPLICIT_USER,
                duration_result.get("raw_text", ""), eid,
            ))

        # Year safety is independent of whether the rest of the date phrase
        # was complete enough to form a date_window (for example, "Bali 2099"
        # still requires review).  Preserve the literal date text and expose a
        # derived classification for validation/policy.
        year_status = _classify_date_year(text)
        if year_status:
            packet.set_derived_signal("date_year_status", self._make_slot(
                year_status, 0.95, AuthorityLevel.DERIVED_SIGNAL,
                f"Explicit travel year classified as {year_status}", eid,
                extraction_mode="derived", maturity="verified",
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
                budget_result.get("currency", "INR"), 0.9, AuthorityLevel.EXPLICIT_USER,
                budget_result.get("raw_text", ""), eid,
            ))

        date_flex = _extract_date_flexibility(text)
        if date_flex is not None:
            packet.set_fact("date_flexibility", self._make_slot(
                date_flex, 0.75, AuthorityLevel.EXPLICIT_USER,
                date_flex, eid,
            ))

        budget_flex = _extract_budget_flexibility(text)
        explicit_budget_flex = budget_flex
        is_inferred_flex = False
        if explicit_budget_flex == "unknown" and budget_result is not None:
            # D2 (RQ-01): golden convention — an unmarked budget is negotiable.
            budget_flex = "soft"
            is_inferred_flex = True
        if budget_flex != "unknown":
            packet.set_fact("budget_flexibility", self._make_slot(
                budget_flex, 0.7 if is_inferred_flex else 0.85,
                AuthorityLevel.EXPLICIT_USER,
                budget_flex, eid,
                epistemic_status=EpistemicStatus.ASSUMED if is_inferred_flex else EpistemicStatus.FACT,
            ))

        budget_scope = _extract_budget_scope(text)
        is_inferred_scope = False
        if budget_scope == "unknown" and budget_result is not None:
            # Golden convention (RQ-01): a budget without a scope marker is
            # trip-total. Without a budget, scope stays unset.
            budget_scope = "total"
            is_inferred_scope = True
        if budget_scope != "unknown":
            packet.set_fact("budget_scope", self._make_slot(
                budget_scope, 0.7 if is_inferred_scope else 0.95,
                AuthorityLevel.EXPLICIT_USER,
                "Derived from budget context" if is_inferred_scope else budget_scope, eid,
                epistemic_status=EpistemicStatus.ASSUMED if is_inferred_scope else EpistemicStatus.FACT,
            ))

        # D-02: budget-vs-flights inclusiveness ("not sure if that includes
        # flights" / "including flights" / "excluding flights"). Trigger
        # patterns live in the Normalizer ambiguity table; the clause-scoped
        # span keeps unrelated "maybe"-style patterns from firing on the
        # whole note. This is an ambiguity, never a fact — the operator
        # confirms the flight scope.
        #
        # FND-0276 Sim #2 replay: multi-voice threads contain SEVERAL
        # flights clauses ("including flights" from the organizer,
        # "cheaper flights" from a friend). Check every clause: an explicit
        # assertion anywhere resolves the scope (no ambiguity); the
        # ambiguity fires only if some clause is unresolved AND none
        # asserts. Raw quotes are sliced from the ORIGINAL text (verbatim),
        # not the lowercased scan string.
        flights_clauses = []
        for m in re.finditer(
            r"[^.!?\n]{0,80}\b(?:flights?|airfare|air\s+fares?|airfares?)\b[^.!?\n]{0,80}",
            text_lower,
        ):
            original_span = text[m.start():m.end()]
            flights_clauses.append((m.group(0), original_span))
        if flights_clauses:
            explicit_resolved = False
            first_unresolved_original: Optional[str] = None
            for clause_lower, clause_original in flights_clauses:
                explicit_resolution = re.search(
                    r"\b(?:including|includes?|with)\s+(?:the\s+)?(?:flights?|airfare)"
                    r"|\b(?:flights?|airfare)\s+(?:are\s+|is\s+)?included\b"
                    r"|\bexcluding\s+(?:the\s+)?(?:flights?|airfare)"
                    r"|\b(?:flights?|airfare)\s+(?:are\s+|is\s+)?excluded\b",
                    clause_lower,
                )
                unresolved_marker = re.search(
                    r"\b(?:not\s+sure|unsure|unclear|whether|if\s+that|no\s+idea)\b",
                    clause_lower,
                )
                if explicit_resolution and not unresolved_marker:
                    explicit_resolved = True
                    break
                if first_unresolved_original is None:
                    first_unresolved_original = clause_original
            if not explicit_resolved and flights_clauses:
                for amb in Normalizer.detect_ambiguities(
                    "budget_raw_text",
                    first_unresolved_original or flights_clauses[0][1],
                ):
                    if amb.ambiguity_type == "flights_inclusiveness_unknown" and not any(
                        a.ambiguity_type == "flights_inclusiveness_unknown" for a in packet.ambiguities
                    ):
                        packet.add_ambiguity(amb)




        flight_hotel_mismatch = _extract_flight_hotel_mismatch(text)
        if flight_hotel_mismatch:
            packet.add_contradiction(
                "flight_hotel_mismatch",
                [
                    f"Flight arrives {flight_hotel_mismatch['arrival_time']} on {flight_hotel_mismatch['flight_date']}",
                    f"Hotel check-in is {flight_hotel_mismatch['hotel_label']} on {flight_hotel_mismatch['hotel_date']}",
                ],
                ["flight_arrival", "hotel_check_in"],
            )

        # Check for budget stretch ambiguity and extract explicit max if present.
        # Only run this when the text actually signals budget flexibility, not
        # when "flexible" refers to dates or other non-budget constraints.
        if explicit_budget_flex != "unknown":
            # Use full text for stretch extraction (don't truncate at punctuation)
            stretch_text = text_lower

            # Extract stretch ambiguity. FND-0276 replay fix: this site scans
            # the FULL text, so the detector's flights_inclusiveness pattern
            # fired here too — bypassing the D-02 multi-clause gate above.
            # flights_inclusiveness_unknown is owned exclusively by the D-02
            # scan; unresolved_alternatives is owned by the destination pass.
            _D02_OWNED = {"flights_inclusiveness_unknown"}
            for amb in Normalizer.detect_ambiguities("budget_flexibility", stretch_text):
                if amb.ambiguity_type in _D02_OWNED:
                    continue
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
        group_signals = party.get("group_signals") or []
        if party["party_size"] > 0:
            packet.set_fact("party_size", self._make_slot(
                party["party_size"], 0.9, AuthorityLevel.EXPLICIT_USER,
                str(party["party_size"]), eid,
                notes=(
                    "group_signals: " + "; ".join(group_signals)
                    if group_signals else None
                ),
            ))
        elif group_signals:
            # Group phrasing present but no convertible headcount — record it
            # so validation can raise PARTY_UNPARSED_GROUP_PHRASING instead of
            # silently dropping the group signal (data-loss prevention).
            packet.add_unknown(
                "party_size",
                "not_extracted_yet",
                notes="unparsed_group_phrasing: " + "; ".join(group_signals),
            )
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
        label_origin_match = re.search(
            r"\b(?:origin city|origin|departure city)\b\s*[:\-]\s*([A-Za-z][A-Za-z\s]{0,40}?)(?=,|\.|\n|\||$)",
            text,
            re.IGNORECASE,
        )
        if label_origin_match:
            city_raw = label_origin_match.group(1).strip()
            city, was_normalized = Normalizer.normalize_city(city_raw)
            mode = ExtractionMode.NORMALIZED if was_normalized else ExtractionMode.DIRECT_EXTRACT
            if is_known_city(city) or len(city_raw.split()) > 1:
                packet.set_fact("origin_city", self._make_slot(
                    city, 0.9, AuthorityLevel.EXPLICIT_USER,
                    label_origin_match.group(0), eid, extraction_mode=mode,
                ))

        # Bounded extraction: limit to ~3 words after "from/starting/departing"
        # to prevent conversational spillover into unrelated sentence parts.
        if not packet.facts.get("origin_city"):
            leading_origin = _extract_leading_origin_city(text)
            if leading_origin:
                packet.set_fact("origin_city", self._make_slot(
                    leading_origin, 0.88, AuthorityLevel.EXPLICIT_USER,
                    leading_origin, eid, extraction_mode=ExtractionMode.DIRECT_EXTRACT,
                ))

        if not packet.facts.get("origin_city"):
            airport_match = re.search(r"\b(from|starting|departing)\s+([A-Z]{3})\b", text)
            if airport_match:
                city, was_normalized = Normalizer.normalize_city(airport_match.group(2))
                mode = ExtractionMode.NORMALIZED if was_normalized else ExtractionMode.DIRECT_EXTRACT
                packet.set_fact("origin_city", self._make_slot(
                    city, 0.95, AuthorityLevel.EXPLICIT_USER,
                    airport_match.group(0), eid, extraction_mode=mode,
                ))

        if not packet.facts.get("origin_city"):
            # Match max 3 words after "from" before hitting a delimiter
            # Delimiters: to/for/budget/need or common continuation phrases,
            # plus punctuation/newline, to avoid spillover into the rest of the sentence.
            origin_match = re.search(
                r"\b(from|starting|departing)\s+((?:[A-Za-z]+\s*){1,3}?)(?:\bto\b|\bfor\b|\bbudget\b|\bneed\b|\bplanning\b|\bgoing\b|\btravel(?:ing|ling)?\b|\blooking\b|\bseeking\b|\bstaying\b|\bwith\b|,|\.|\$|\n)",
                text,
                re.IGNORECASE,
            )
            if origin_match:
                city_raw = origin_match.group(2).strip()
                city_raw_lower = city_raw.lower()
                first_token = city_raw_lower.split()[0] if city_raw_lower.split() else ""
                airport_context = "airport" in city_raw_lower or "transfer" in city_raw_lower
                # Validate as a plausible city name using geography.py
                # NOTE: A city being in destination lists doesn't disqualify it as origin.
                # People can take trips FROM destinations. What matters is the pattern.
                city, was_normalized = Normalizer.normalize_city(city_raw)
                mode = ExtractionMode.NORMALIZED if was_normalized else ExtractionMode.DIRECT_EXTRACT

                # Basic validation: must be a known city (or close enough) or multi-word
                # Multi-word names like "New York" should be accepted even if not in city DB
                if not airport_context and first_token not in _STOP_WORDS and (
                    is_known_city(city) or len(city_raw.split()) > 1
                ):
                    packet.set_fact("origin_city", self._make_slot(
                        city, 0.9, AuthorityLevel.EXPLICIT_USER,
                        origin_match.group(0), eid, extraction_mode=mode,
                    ))

        # Out of / Departure patterns: "flying out of blr", "departing from blr", "out of mumbai"
        if not packet.facts.get("origin_city"):
            out_of_match = re.search(
                r"\b(?:flying\s+(?:out\s+of|from)|departing\s+(?:out\s+of|from)|leaving\s+(?:from|out\s+of)|out\s+of)\s+([A-Za-z]{3,})\b",
                text,
                re.IGNORECASE,
            )
            if out_of_match:
                city_raw = out_of_match.group(1).strip()
                city, was_normalized = Normalizer.normalize_city(city_raw)
                if not was_normalized:
                    city = city.title()
                if is_known_city(city) or is_known_destination(city) or len(city_raw) == 3:
                    packet.set_fact("origin_city", self._make_slot(
                        city, 0.92, AuthorityLevel.EXPLICIT_USER,
                        out_of_match.group(0), eid, extraction_mode=ExtractionMode.NORMALIZED if was_normalized else ExtractionMode.DIRECT_EXTRACT,
                    ))

        # Route pattern: "blr to goa", "mumbai to bali", "sfo to tokyo", "delhi -> manali"
        if not packet.facts.get("origin_city"):
            route_match = re.search(
                r"\b([A-Za-z]{3,})\s+(?:to|->|-->)\s+([A-Za-z]{3,})\b",
                text,
                re.IGNORECASE,
            )
            if route_match:
                city1_raw = route_match.group(1).strip()
                city2_raw = route_match.group(2).strip()
                city1, norm1 = Normalizer.normalize_city(city1_raw)
                city2, norm2 = Normalizer.normalize_city(city2_raw)
                if not norm1:
                    city1 = city1.title()
                if not norm2:
                    city2 = city2.title()
                if (is_known_city(city1) or is_known_destination(city1) or len(city1_raw) == 3) and (
                    is_known_city(city2) or is_known_destination(city2) or len(city2_raw) == 3
                ):
                    packet.set_fact("origin_city", self._make_slot(
                        city1, 0.90, AuthorityLevel.EXPLICIT_USER,
                        route_match.group(0), eid, extraction_mode=ExtractionMode.NORMALIZED if norm1 else ExtractionMode.DIRECT_EXTRACT,
                    ))

        # Hinglish/Odia origin: "Bangalore se", "Bangalore ru", "mumbai se goa"
        # Only try if origin not already set.
        # Single-word city only (multi-word like "New York se" is unlikely in Hinglish).
        #
        # Postposition semantics split (owner-ratified Option 3, 2026-09-14):
        #   "se"/"ru" = explicit "from" marker  → FACT (0.85, unchanged).
        #   "side"    = directional reference ("X side jaana hai" = heading
        #               that way / somewhere around X) → SOFT HYPOTHESIS,
        #               never a fact — origin anchors real money math
        #               (flight distance, visa corridor). "X side se" carries
        #               the explicit marker and upgrades to fact.
        # "okinawa side trip?" is a noun compound (proposed destination),
        # not the Hinglish origin postposition (FND-0284-family, Sim #2).
        if not packet.facts.get("origin_city"):
            postposition_match = re.search(
                r"\b([A-Za-z]+)\s+(se|ru|side)\b",
                text,
                re.IGNORECASE,
            )
            if postposition_match and not (
                postposition_match.group(2).lower() == "side"
                and _side_is_trip_compound(text[postposition_match.end():])
            ):
                city_raw = postposition_match.group(1).strip()
                postposition = postposition_match.group(2).lower()
                # Deictic origins like "yahan se" / "wahan se" mean "from here/there", not a city named Yahan
                if city_raw.lower() not in ("yahan", "wahan", "idhar", "udhar", "here", "there"):
                    city, was_normalized = Normalizer.normalize_city(city_raw)
                    if not was_normalized:
                        city = city.title()
                    mode = ExtractionMode.NORMALIZED if was_normalized else ExtractionMode.DIRECT_EXTRACT
                    if is_known_city(city) or len(city_raw.split()) > 1 or len(city_raw) == 3:
                        if postposition in ("se", "ru") or (
                            postposition == "side"
                            and re.match(
                                r"^\s+(?:se|ru)\b",
                                text[postposition_match.end():],
                                re.IGNORECASE,
                            )
                        ):
                            # Explicit "from" marker (also "X side se") → fact.
                            packet.set_fact("origin_city", self._make_slot(
                                city, 0.85, AuthorityLevel.EXPLICIT_USER,
                                postposition_match.group(0), eid, extraction_mode=mode,
                            ))
                        else:
                            # Bare "X side": directional — hypothesis, not fact.
                            packet.set_hypothesis("origin_city", self._make_slot(
                                city, 0.55, AuthorityLevel.SOFT_HYPOTHESIS,
                                postposition_match.group(0), eid, extraction_mode=mode,
                            ))

        # Ensure origin city is never erroneously retained in destination candidates
        if packet.facts.get("origin_city") and packet.facts.get("destination_candidates"):
            origin_name = str(packet.facts["origin_city"].value).lower()
            norm_origin, _ = Normalizer.normalize_city(origin_name)
            norm_origin_lower = norm_origin.lower()
            dest_slot = packet.facts["destination_candidates"]
            current_dests = dest_slot.value
            if isinstance(current_dests, list):
                filtered_dests = []
                for d in current_dests:
                    d_norm, _ = Normalizer.normalize_city(str(d))
                    if str(d).lower() == origin_name or d_norm.lower() == norm_origin_lower or str(d).lower() == norm_origin_lower:
                        continue
                    filtered_dests.append(d)
                if len(filtered_dests) != len(current_dests):
                    dest_slot.value = filtered_dests

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

        # --- TRAVELERS (L2 attribution, Phase 3b / IDEA-134) ---
        # Per-speaker fact bundles from the delegation thread. Personal facts
        # stay bound to the speaker; group facts (budget/window/party) remain
        # packet-level. Only emitted when at least one speaker is identified.
        # Uses envelope.content (RAW text — _prepare_extraction_text may have
        # stripped the speaker labels that attribution.py needs).
        try:
            from src.intake.attribution import build_travelers
            raw_content = envelope.content if isinstance(envelope.content, str) else str(envelope.content)
            travelers = build_travelers(raw_content)
            if travelers:
                packet.set_fact("travelers", self._make_slot(
                    travelers, 0.85, AuthorityLevel.EXPLICIT_USER,
                    f"{len(travelers)} speaker-attributed traveler(s)", eid,
                ))
        except Exception as exc:  # attribution is additive; never crash intake
            logger.warning("travelers attribution skipped: %s", exc)

        # --- GROUP BOOKING / PROCUREMENT SIGNALS ---
        rooming_matches = []
        for rooming_match in re.finditer(
            r"\b(?:(one|two|three|four|five|six|seven|eight|nine|ten|\d+)\s+)?(?:separate\s+)?rooming\s+lists?\b",
            text_lower,
        ):
            count_token = rooming_match.group(1)
            rooming_count = _count_token_to_int(count_token) if count_token else 1
            phrase = rooming_match.group(0).strip()
            rooming_matches.append((
                rooming_count or 1,
                "separate" in phrase,
                len(phrase),
                phrase,
            ))

        if rooming_matches:
            rooming_count, _, _, rooming_phrase = max(
                rooming_matches,
                key=lambda item: (item[0], item[1], item[2]),
            )
            existing_rooming_slot = packet.facts.get("rooming_list_count")
            existing_rooming_count = getattr(existing_rooming_slot, "value", None)
            existing_rooming_count_num = existing_rooming_count if isinstance(existing_rooming_count, int) else None
            should_update_rooming = existing_rooming_count_num is None or rooming_count > existing_rooming_count_num

            if should_update_rooming and rooming_count > 0:
                packet.set_fact("rooming_list_count", self._make_slot(
                    rooming_count, 0.9, AuthorityLevel.EXPLICIT_USER,
                    rooming_phrase, eid,
                ))
                packet.set_fact("rooming_list_requested", self._make_slot(
                    True, 0.9, AuthorityLevel.EXPLICIT_USER,
                    rooming_phrase, eid,
                ))
                packet.set_fact("rooming_requirements", self._make_slot(
                    rooming_phrase, 0.85, AuthorityLevel.EXPLICIT_USER,
                    rooming_phrase, eid,
                ))

        procurement_match = re.search(
            r"\b(procurement|purchasing|approvals?|finance)\b",
            text_lower,
        )
        if procurement_match:
            packet.set_fact("procurement_share_needed", self._make_slot(
                True, 0.85, AuthorityLevel.EXPLICIT_USER,
                procurement_match.group(0), eid,
            ))
            packet.set_fact("procurement_notes", self._make_slot(
                "shareable with procurement", 0.8, AuthorityLevel.EXPLICIT_USER,
                procurement_match.group(0), eid,
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
                packet.set_derived_signal(field_name, self._make_slot(
                    value, 0.7, AuthorityLevel.DERIVED_SIGNAL,
                    f"Stage-gated passport/visa concern detected for {field_name}",
                    eid, extraction_mode="derived", maturity="heuristic",
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

        # --- PAST TRIPS (travel history) ---
        # Structured capture: destinations inside past-trip clauses become
        # memory facts (place, clause, sentiment, macro region) so the
        # decision layer can ask history-informed questions ("you loved
        # Japan and Korea — somewhere similar?") and preference inference
        # has real entities to work with. Memories are never destinations.
        past_places = _extract_past_trip_places(text)
        if past_places:
            packet.set_fact("past_trips", self._make_slot(
                past_places, 0.7,
                AuthorityLevel.EXPLICIT_USER, text[:200], eid,
            ))
            # Region affinity: aggregated preference signal for downstream
            # ranking consumers (suitability/proposal phases). A preference
            # signal, never an extraction fact — destinations and dates are
            # unaffected; consumer contract documented in the realignment
            # blueprint Addendum 5.
            affinity: Dict[str, Dict[str, Any]] = {}
            for place in past_places:
                region = place.get("region")
                if not region:
                    continue
                bucket = affinity.setdefault(
                    region, {"region": region, "trips": 0, "positive": 0, "places": []}
                )
                bucket["trips"] += 1
                if place.get("sentiment") == "positive":
                    bucket["positive"] += 1
                bucket["places"].append(place.get("place"))
            if affinity:
                packet.set_fact("region_affinity", self._make_slot(
                    sorted(affinity.values(), key=lambda b: -b["trips"]), 0.65,
                    AuthorityLevel.EXPLICIT_USER, text[:200], eid,
                ))
        elif "past trip" in text_lower or "previous trip" in text_lower:
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
        if not isinstance(data, dict):
            # The API normally validates this shape, but direct callers and
            # replayed historical envelopes can still be malformed.  A bad
            # import is an unknown input, never a process-wide crash.
            packet.metadata.setdefault("input_safety", {
                "sanitized": False,
                "control_chars_removed": 0,
                "instruction_spans_removed": 0,
            })["structured_shape_rejected"] = True
            return

        field_mappings = {
            "destination": "destination_candidates",
            "destination_candidates": "destination_candidates",
            "origin": "origin_city",
            "origin_city": "origin_city",
            "travelers": "party_size",
            "party_size": "party_size",
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
                if canonical_field == "destination_candidates":
                    values = _structured_destination_values(value)
                    if not values:
                        continue
                    value = values
                    mode = ExtractionMode.NORMALIZED
                elif canonical_field == "origin_city":
                    origin = _structured_origin_value(value)
                    if origin is None:
                        continue
                    value = origin
                    mode = ExtractionMode.NORMALIZED
                elif canonical_field == "budget_raw_text":
                    if not _structured_budget_is_safe(value):
                        continue
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
                        # A list is a party only when every row is a mapping.
                        # Do not turn malformed strings ("2 adults") into a
                        # fabricated count or let them reach the row parser.
                        if not value or not all(isinstance(item, dict) for item in value):
                            continue
                        value = len(value)
                    elif isinstance(value, int) and not isinstance(value, bool):
                        if not 0 < value <= 1000:
                            continue
                    elif isinstance(value, str) and re.fullmatch(r"\d{1,3}", value.strip()):
                        value = int(value.strip())
                    else:
                        continue
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
                travelers = [t for t in data["travelers"] if isinstance(t, dict)]
                # A partially malformed list cannot safely establish a total
                # party count.  Keep any valid rows for diagnostics only when
                # the entire structured collection is well-shaped.
                if len(travelers) != len(data["travelers"]):
                    travelers = []
                for t in travelers:
                    age = t.get("age")
                    if isinstance(age, bool):
                        age = None
                    elif isinstance(age, str) and re.fullmatch(r"\d+(?:\.\d+)?", age.strip()):
                        age = float(age.strip())
                    elif not isinstance(age, (int, float)):
                        age = None
                    rel_raw = t.get("relationship")
                    rel = rel_raw.lower() if isinstance(rel_raw, str) else ""
                    if age is not None and 0 <= age <= 130:
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
        if not isinstance(envelope.content, dict):
            self._extract_from_structured(
                SourceEnvelope(
                    envelope_id=envelope.envelope_id,
                    source_system=envelope.source_system,
                    actor_type=envelope.actor_type,
                    received_at=envelope.received_at,
                    content=envelope.content,
                    content_type="structured_json",
                ),
                packet,
            )
            return
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
        """Mark expected MVB fields that are not present.

        T-O2 (ontology v2): each unknown carries its required_for stage gates
        (TS-07 classifier) in notes, so NEEDS_INFORMATION renders per-stage
        blockers ("blocking for booking") instead of a flat boolean list.
        """
        from .validation import classify_missing_fields

        discovery_mvb = [
            "destination_candidates", "origin_city", "date_window",
            "party_size", "budget_raw_text", "trip_purpose",
        ]
        classified = classify_missing_fields(packet)
        existing_unknown_fields = {u.field_name for u in packet.unknowns}
        for field_name in discovery_mvb:
            if (
                field_name not in packet.facts
                and field_name not in existing_unknown_fields
            ):
                info = classified.get(field_name) or {}
                required_for = info.get("required_for") or []
                note = (
                    f"required_for: {', '.join(required_for)} "
                    f"[{info.get('class', 'OPTIONAL')}]" if required_for else None
                )
                packet.add_unknown(field_name, "not_present_in_source", notes=note)
