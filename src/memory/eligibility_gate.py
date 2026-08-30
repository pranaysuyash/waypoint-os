"""
src/memory/eligibility_gate.py — Write Eligibility & Curation Gate.

Enforces strict write curation rules for Agent Memory:
- Blocks unstructured conversational chatter and low-signal noise.
- Evaluates source-of-truth hierarchy and assigns authoritative weights.
- Enforces strict confidence thresholds (default min 0.75 for persistence).
- Categorizes candidate facts into the correct memory tier.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional, Tuple

from src.memory.models import (
    MemorySourceType,
    MemoryTier,
    SOURCE_CONFIDENCE_WEIGHTS,
)

# Minimum confidence required to persist a memory fact
DEFAULT_WRITE_CONFIDENCE_THRESHOLD = 0.75

# Low-signal conversational chatter phrases to reject
CHATTER_PATTERNS = [
    r"^(hello|hi|hey|thanks|thank you|ok|okay|got it|cool|sounds good)[\.!]*$",
    r"^(bye|goodbye|see you|have a good day)[\.!]*$",
    r"^(can you help me|i have a question)[\?!]*$",
    r"^(what time is it|tell me a joke)[\?!]*$",
]

# High-signal memory keywords that warrant curation
SEMANTIC_SIGNAL_KEYWORDS = {
    "dietary", "vegan", "vegetarian", "gluten", "halal", "kosher", "allergy", "allergic",
    "aisle", "window", "business class", "first class", "economy", "seating",
    "passport", "loyalty", "frequent flyer", "marriott", "hilton", "delta", "united",
    "wheelchair", "accessible", "infant", "pet", "anniversary", "honeymoon", "birthday",
}

PROCEDURAL_SIGNAL_KEYWORDS = {
    "policy", "markup", "commission", "approval", "discount", "cancellation", "refund",
    "vip threshold", "emergency contact", "escalation", "supplier agreement",
}


@dataclass(slots=True)
class EligibilityResult:
    is_eligible: bool
    tier: MemoryTier
    confidence_score: float
    rejection_reason: Optional[str] = None
    extracted_category: str = "general"
    sanitized_summary: str = ""


class MemoryEligibilityGate:
    """Evaluates raw inputs or agent assertions for long-term memory write eligibility."""

    def __init__(self, min_confidence: float = DEFAULT_WRITE_CONFIDENCE_THRESHOLD):
        self.min_confidence = min_confidence

    def evaluate(
        self,
        raw_text: str,
        source_type: MemorySourceType,
        explicit_confidence: Optional[float] = None,
        category_hint: Optional[str] = None,
        entity_id: str = "",
    ) -> EligibilityResult:
        cleaned = raw_text.strip()

        # 1. Reject empty or trivially short strings
        if len(cleaned) < 4:
            return EligibilityResult(
                is_eligible=False,
                tier=MemoryTier.WORKING,
                confidence_score=0.0,
                rejection_reason="Text too short (<4 chars) to contain durable memory signal",
            )

        # 2. Reject conversational chatter
        for pattern in CHATTER_PATTERNS:
            if re.match(pattern, cleaned, re.IGNORECASE):
                return EligibilityResult(
                    is_eligible=False,
                    tier=MemoryTier.WORKING,
                    confidence_score=0.1,
                    rejection_reason="Conversational chatter filtered by anti-noise gate",
                )

        # 3. Compute base confidence from source hierarchy
        source_weight = SOURCE_CONFIDENCE_WEIGHTS.get(source_type, 0.6)
        if explicit_confidence is not None:
            # Blend explicit confidence with source authority
            confidence = round(0.5 * explicit_confidence + 0.5 * source_weight, 3)
        else:
            confidence = source_weight

        # 4. Check confidence threshold
        if confidence < self.min_confidence:
            return EligibilityResult(
                is_eligible=False,
                tier=MemoryTier.WORKING,
                confidence_score=confidence,
                rejection_reason=f"Confidence {confidence:.2f} below minimum write threshold {self.min_confidence:.2f}",
            )

        # 5. Classify memory tier and category
        tier, category = self._classify_tier_and_category(cleaned, category_hint)

        return EligibilityResult(
            is_eligible=True,
            tier=tier,
            confidence_score=confidence,
            extracted_category=category,
            sanitized_summary=cleaned[:250],
        )

    def _classify_tier_and_category(
        self, text: str, category_hint: Optional[str]
    ) -> Tuple[MemoryTier, str]:
        lower_text = text.lower()

        if category_hint:
            hint_lower = category_hint.lower()
            if hint_lower in ("policy", "rule", "procedure", "guideline"):
                return MemoryTier.PROCEDURAL, "procedural_rule"
            if hint_lower in ("preference", "autonomy", "settings"):
                return MemoryTier.PREFERENCE, "agency_preference"
            if hint_lower in ("disruption", "incident", "interaction", "trip_milestone"):
                return MemoryTier.EPISODIC, "trip_event"
            return MemoryTier.SEMANTIC, hint_lower

        # Keyword matching heuristics
        for word in PROCEDURAL_SIGNAL_KEYWORDS:
            if word in lower_text:
                return MemoryTier.PROCEDURAL, "agency_policy"

        for word in SEMANTIC_SIGNAL_KEYWORDS:
            if word in lower_text:
                if any(w in lower_text for w in ("dietary", "vegan", "vegetarian", "gluten", "allergy", "allergic")):
                    return MemoryTier.SEMANTIC, "dietary_safety"
                if any(w in lower_text for w in ("aisle", "window", "business class", "seating")):
                    return MemoryTier.SEMANTIC, "seating_preference"
                if any(w in lower_text for w in ("passport", "loyalty", "frequent flyer")):
                    return MemoryTier.SEMANTIC, "credentials_loyalty"
                return MemoryTier.SEMANTIC, "traveler_preference"

        return MemoryTier.SEMANTIC, "general_affinity"
