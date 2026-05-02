"""
intake.readiness — Computed readiness model for pipeline stage progression.

Readiness is a PURE COMPUTATION — it reads the packet and returns a readiness
assessment. It NEVER mutates stage or any other field.

Tiers (ordered from lowest to highest readiness):
  1. intake_minimum — enough to save a trip (destination + dates)
  2. quote_ready    — enough to generate a quote (6 MVB fields)
  3. proposal_ready — enough to build a proposal (quote_ready + preferences)
  4. booking_ready  — enough to proceed to booking (proposal_ready + identities)

Each tier lists met/unmet fields so the UI can show what's missing.
`highest_ready_tier` is the highest tier where ALL fields are present.
`suggested_next_stage` maps to the stage the trip SHOULD be in (non-mutating recommendation).
`should_auto_advance_stage` is always False — stage transitions require explicit action.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional

from .packet_models import CanonicalPacket
from .validation import INTAKE_MINIMUM, QUOTE_READY


# --- Delta definitions (additional fields per tier beyond the previous tier) ---

PROPOSAL_READY_DELTA = [
    "trip_priorities",      # Must-haves / preferences
    "date_flexibility",     # How rigid are the dates
]

BOOKING_READY_DELTA = [
    "traveler_identities",  # Per-traveler legal info
    "primary_payer",        # Who pays
    "emergency_contacts",   # At least one per party
]

ReadinessTier = Literal["intake_minimum", "quote_ready", "proposal_ready", "booking_ready"]

TIER_ORDER: List[ReadinessTier] = [
    "intake_minimum",
    "quote_ready",
    "proposal_ready",
    "booking_ready",
]

# Cumulative field lists — each tier includes all fields from lower tiers.
# INTAKE_MINIMUM ⊂ QUOTE_READY ⊂ PROPOSAL_READY ⊂ BOOKING_READY.
TIER_FIELDS: Dict[ReadinessTier, List[str]] = {
    "intake_minimum": list(INTAKE_MINIMUM),
    "quote_ready": list(QUOTE_READY),
    "proposal_ready": list(QUOTE_READY) + PROPOSAL_READY_DELTA,
    "booking_ready": list(QUOTE_READY) + PROPOSAL_READY_DELTA + BOOKING_READY_DELTA,
}

# Delta fields (only the NEW fields for each tier — useful for UI "what's missing for next")
TIER_DELTA: Dict[ReadinessTier, List[str]] = {
    "intake_minimum": list(INTAKE_MINIMUM),
    "quote_ready": [f for f in QUOTE_READY if f not in INTAKE_MINIMUM],
    "proposal_ready": PROPOSAL_READY_DELTA,
    "booking_ready": BOOKING_READY_DELTA,
}

# Map readiness tier → the stage this tier unlocks
TIER_STAGE_MAP: Dict[ReadinessTier, str] = {
    "intake_minimum": "discovery",
    "quote_ready": "shortlist",
    "proposal_ready": "proposal",
    "booking_ready": "booking",
}


@dataclass(slots=True)
class TierDetail:
    """Readiness assessment for a single tier."""
    tier: ReadinessTier
    ready: bool
    met: List[str]
    unmet: List[str]


@dataclass(slots=True)
class ReadinessResult:
    """Full readiness assessment — pure computation, no side effects."""
    tiers: Dict[ReadinessTier, TierDetail]
    highest_ready_tier: Optional[ReadinessTier]
    suggested_next_stage: str
    should_auto_advance_stage: bool  # Always False
    missing_for_next: List[str]  # Fields blocking the next tier

    def to_dict(self) -> Dict[str, Any]:
        return {
            "highest_ready_tier": self.highest_ready_tier,
            "suggested_next_stage": self.suggested_next_stage,
            "should_auto_advance_stage": self.should_auto_advance_stage,
            "missing_for_next": self.missing_for_next,
            "tiers": {
                name: {
                    "tier": detail.tier,
                    "ready": detail.ready,
                    "met": detail.met,
                    "unmet": detail.unmet,
                }
                for name, detail in self.tiers.items()
            },
        }


def _check_tier(facts: Dict[str, Any], required_fields: List[str], tier: ReadinessTier) -> TierDetail:
    """Check which fields in a tier are met vs unmet."""
    met = [f for f in required_fields if f in facts]
    unmet = [f for f in required_fields if f not in facts]
    return TierDetail(
        tier=tier,
        ready=len(unmet) == 0,
        met=met,
        unmet=unmet,
    )


def compute_readiness(packet: CanonicalPacket) -> ReadinessResult:
    """
    Compute readiness from a CanonicalPacket.

    This is a pure function — it reads packet.facts and returns a readiness
    assessment without modifying anything.
    """
    facts = packet.facts

    # Evaluate each tier (cumulative — each includes all lower tier fields)
    tiers: Dict[ReadinessTier, TierDetail] = {}
    for tier in TIER_ORDER:
        tiers[tier] = _check_tier(facts, TIER_FIELDS[tier], tier)

    # Find highest ready tier (walk from highest to lowest)
    highest: Optional[ReadinessTier] = None
    for tier in reversed(TIER_ORDER):
        if tiers[tier].ready:
            highest = tier
            break

    # Suggested stage = stage the highest ready tier unlocks
    suggested_stage = TIER_STAGE_MAP[highest] if highest else "discovery"

    # Fields blocking the next tier (show only the DELTA fields, not cumulative)
    missing_for_next: List[str] = []
    if highest is not None:
        next_idx = TIER_ORDER.index(highest) + 1
        if next_idx < len(TIER_ORDER):
            next_tier = TIER_ORDER[next_idx]
            # Show only the delta fields that are missing (not re-listing already-met fields)
            delta = TIER_DELTA[next_tier]
            missing_for_next = [f for f in delta if f not in facts]
    else:
        # No tier is ready — show what intake_minimum needs
        missing_for_next = tiers["intake_minimum"].unmet

    return ReadinessResult(
        tiers=tiers,
        highest_ready_tier=highest,
        suggested_next_stage=suggested_stage,
        should_auto_advance_stage=False,
        missing_for_next=missing_for_next,
    )
