"""
intake.readiness — Computed readiness model for pipeline stage progression.

Readiness is a PURE COMPUTATION — it reads the packet and pipeline outputs and
returns a readiness assessment. It NEVER mutates stage or any other field.

Tiers (ordered from lowest to highest readiness):
  1. intake_minimum — enough to save a trip (destination + dates)
  2. quote_ready    — enough to generate a quote (6 MVB fields with usable values)
  3. proposal_ready — quote_ready + traveler_bundle + internal_bundle + fees + safety pass
  4. booking_ready  — proposal_ready + booking_data (always false until booking_data exists)

Each tier lists met/unmet fields so the UI can show what's missing.
`highest_ready_tier` is the highest tier where ALL conditions are met.
`suggested_next_stage` maps to the stage the trip SHOULD be in (non-mutating recommendation).
`should_auto_advance_stage` is always False — stage transitions require explicit action.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional

from .packet_models import CanonicalPacket, Slot
from .validation import INTAKE_MINIMUM, QUOTE_READY


# --- Delta definitions (additional fields per tier beyond the previous tier) ---

PROPOSAL_READY_DELTA = [
    "trip_priorities",      # Must-haves / preferences
    "date_flexibility",     # How rigid are the dates
]

BOOKING_READY_DELTA = [
    "booking_data",         # Per-traveler legal info + payer + contacts
]

ReadinessTier = Literal["intake_minimum", "quote_ready", "proposal_ready", "booking_ready"]

TIER_ORDER: List[ReadinessTier] = [
    "intake_minimum",
    "quote_ready",
    "proposal_ready",
    "booking_ready",
]

# Cumulative field lists for intake_minimum and quote_ready (packet-fact-based tiers).
# proposal_ready and booking_ready use pipeline-output checks instead.
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

# Pipeline-output keys for proposal_ready checks
PROPOSAL_PIPELINE_OUTPUTS = [
    "traveler_bundle",
    "internal_bundle",
    "fees",
    "safety",
]


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
    signals: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        result = {
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
        if self.signals:
            result["signals"] = self.signals
        return result


def _has_usable_fact(facts: Dict[str, Any], field_name: str) -> bool:
    """Check that a field exists AND has a usable value."""
    if field_name not in facts:
        return False
    slot = facts[field_name]
    # Support both Slot objects and raw values
    value = getattr(slot, "value", slot)
    if value is None:
        return False
    if isinstance(value, str) and not value.strip():
        return False
    if isinstance(value, (list, dict)) and len(value) == 0:
        return False
    return True


def _check_tier(facts: Dict[str, Any], required_fields: List[str], tier: ReadinessTier) -> TierDetail:
    """Check which fields in a tier are met vs unmet using usable-value checks."""
    met = [f for f in required_fields if _has_usable_fact(facts, f)]
    unmet = [f for f in required_fields if not _has_usable_fact(facts, f)]
    return TierDetail(
        tier=tier,
        ready=len(unmet) == 0,
        met=met,
        unmet=unmet,
    )


def _has_usable_pipeline_output(data: Any) -> bool:
    """Check that a pipeline output exists and is non-empty."""
    if data is None:
        return False
    if isinstance(data, dict) and len(data) == 0:
        return False
    if isinstance(data, (list, str)) and len(data) == 0:
        return False
    return True


def _check_proposal_ready(
    facts: Dict[str, Any],
    traveler_bundle: Any = None,
    internal_bundle: Any = None,
    safety: Any = None,
    fees: Any = None,
    decision: Any = None,
) -> TierDetail:
    """
    Proposal-ready requires:
    - All quote_ready fields with usable values
    - trip_priorities and date_flexibility in facts
    - traveler_bundle exists
    - internal_bundle exists
    - fees exists
    - safety/leakage result exists and is_safe
    - decision has no critical hard blocker preventing proposal
    """
    all_fields = list(QUOTE_READY) + PROPOSAL_READY_DELTA
    met: List[str] = []
    unmet: List[str] = []

    # Check fact-based fields
    for f in all_fields:
        if _has_usable_fact(facts, f):
            met.append(f)
        else:
            unmet.append(f)

    # Check pipeline outputs
    if not _has_usable_pipeline_output(traveler_bundle):
        unmet.append("traveler_bundle")
    else:
        met.append("traveler_bundle")

    if not _has_usable_pipeline_output(internal_bundle):
        unmet.append("internal_bundle")
    else:
        met.append("internal_bundle")

    if not _has_usable_pipeline_output(fees):
        unmet.append("fees")
    else:
        met.append("fees")

    # Safety must exist AND be safe
    if not _has_usable_pipeline_output(safety):
        unmet.append("safety")
    else:
        # Check is_safe from leakage result dict
        safety_dict = safety if isinstance(safety, dict) else {}
        if safety_dict.get("is_safe") is not True:
            unmet.append("safety_pass")
        else:
            met.append("safety_pass")

    # Decision should not have critical hard blockers blocking proposal
    if decision is not None:
        decision_dict = decision if isinstance(decision, dict) else {}
        hard_blockers = decision_dict.get("hard_blockers", [])
        suitability_critical = any(
            "suitability" in str(b).lower() or "critical" in str(b).lower()
            for b in hard_blockers
        )
        if suitability_critical:
            unmet.append("no_critical_blockers")
        else:
            met.append("no_critical_blockers")

    return TierDetail(
        tier="proposal_ready",
        ready=len(unmet) == 0,
        met=met,
        unmet=unmet,
    )


def _check_booking_ready(
    facts: Dict[str, Any],
    booking_data: Any = None,
) -> TierDetail:
    """
    Booking-ready requires booking_data to exist.
    Always false until booking_data is provided.
    """
    unmet: List[str] = ["booking_data"]
    met: List[str] = []

    if booking_data is not None and _has_usable_pipeline_output(booking_data):
        met.append("booking_data")
        unmet = []

    return TierDetail(
        tier="booking_ready",
        ready=len(unmet) == 0,
        met=met,
        unmet=unmet,
    )


def compute_readiness(
    packet: CanonicalPacket,
    validation: Any = None,
    decision: Any = None,
    traveler_bundle: Any = None,
    internal_bundle: Any = None,
    safety: Any = None,
    fees: Any = None,
    booking_data: Any = None,
) -> ReadinessResult:
    """
    Compute readiness from a CanonicalPacket and pipeline outputs.

    This is a pure function — it reads inputs and returns a readiness
    assessment without modifying anything.

    intake_minimum and quote_ready are based on packet facts with usable-value checks.
    proposal_ready requires quote_ready + pipeline outputs (bundles, fees, safety pass).
    booking_ready requires booking_data to exist.
    """
    facts = packet.facts

    # Evaluate intake_minimum and quote_ready from packet facts
    tiers: Dict[ReadinessTier, TierDetail] = {
        "intake_minimum": _check_tier(facts, TIER_FIELDS["intake_minimum"], "intake_minimum"),
        "quote_ready": _check_tier(facts, TIER_FIELDS["quote_ready"], "quote_ready"),
        "proposal_ready": _check_proposal_ready(
            facts,
            traveler_bundle=traveler_bundle,
            internal_bundle=internal_bundle,
            safety=safety,
            fees=fees,
            decision=decision,
        ),
        "booking_ready": _check_booking_ready(facts, booking_data=booking_data),
    }

    # Find highest ready tier (walk from highest to lowest)
    highest: Optional[ReadinessTier] = None
    for tier in reversed(TIER_ORDER):
        if tiers[tier].ready:
            highest = tier
            break

    # Suggested stage = stage the highest ready tier unlocks
    suggested_stage = TIER_STAGE_MAP[highest] if highest else "discovery"

    # Fields blocking the next tier (show only the delta items that are missing)
    missing_for_next: List[str] = []
    if highest is not None:
        next_idx = TIER_ORDER.index(highest) + 1
        if next_idx < len(TIER_ORDER):
            next_tier = TIER_ORDER[next_idx]
            missing_for_next = tiers[next_tier].unmet
    else:
        missing_for_next = tiers["intake_minimum"].unmet

    # Auxiliary signals from facts + derived_signals
    signals: Dict[str, Any] = {}
    all_slots = {**packet.facts, **packet.derived_signals}
    if _has_usable_fact(all_slots, "visa_concerns_present"):
        slot = all_slots["visa_concerns_present"]
        signals["visa_concerns_present"] = bool(getattr(slot, "value", slot))

    return ReadinessResult(
        tiers=tiers,
        highest_ready_tier=highest,
        suggested_next_stage=suggested_stage,
        should_auto_advance_stage=False,
        missing_for_next=missing_for_next,
        signals=signals,
    )
