"""
intake.decision — NB02 v0.2: Gap and Decision (Agency Judgment Engine).

Consumes CanonicalPacket v0.2 from NB01, returns DecisionResult.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from .packet_models import (
    Ambiguity,
    CanonicalPacket,
    LifecycleInfo,
    Slot,
    AuthorityLevel,
)


# =============================================================================
# SECTION 1: DECISION RESULT
# =============================================================================

DECISION_STATES = (
    "ASK_FOLLOWUP",
    "PROCEED_INTERNAL_DRAFT",
    "PROCEED_TRAVELER_SAFE",
    "BRANCH_OPTIONS",
    "STOP_NEEDS_REVIEW",
)

COMMERCIAL_DECISIONS = (
    "NONE",
    "SEND_FOLLOWUP",
    "SET_BOUNDARY",
    "REQUEST_TOKEN",
    "MOVE_TO_NURTURE",
    "REACTIVATE_REPEAT",
    "CLOSE_LOST",
    "ESCALATE_RECOVERY",
)


@dataclass
class AmbiguityRef:
    """A reference to a packet ambiguity, with severity classification."""
    field_name: str
    ambiguity_type: str
    raw_value: str
    severity: str  # "blocking" | "advisory"


@dataclass
class DecisionResult:
    """The complete output of the NB02 gap and decision pipeline."""
    packet_id: str
    current_stage: str                          # discovery | shortlist | proposal | booking
    operating_mode: str                         # normal_intake | audit | emergency | ...
    decision_state: str                         # One of DECISION_STATES
    hard_blockers: List[str] = field(default_factory=list)
    soft_blockers: List[str] = field(default_factory=list)
    ambiguities: List[AmbiguityRef] = field(default_factory=list)
    contradictions: List[Dict[str, Any]] = field(default_factory=list)
    follow_up_questions: List[Dict[str, Any]] = field(default_factory=list)
    branch_options: List[Dict[str, Any]] = field(default_factory=list)
    rationale: Dict[str, Any] = field(default_factory=dict)
    confidence_score: float = 0.0
    risk_flags: List[Dict[str, Any]] = field(default_factory=list)
    commercial_decision: str = "NONE"          # One of COMMERCIAL_DECISIONS
    intent_scores: Dict[str, float] = field(default_factory=dict)
    next_best_action: Optional[str] = None


# =============================================================================
# SECTION 2: MVB DEFINITIONS (v0.2)
# =============================================================================

MVB_BY_STAGE = {
    "discovery": {
        "hard_blockers": [
            "destination_candidates",
            "origin_city",
            "date_window",
            "party_size",
        ],
        "soft_blockers": [
            "budget_raw_text",
            "budget_min",
            "trip_purpose",
            "soft_preferences",
        ],
    },
    "shortlist": {
        "hard_blockers": [
            "destination_candidates",
            "resolved_destination",  # Must have a single active planning target
            "origin_city",
            "date_window",
            "party_size",
        ],
        "soft_blockers": [
            "budget_min",
            "trip_style",
        ],
    },
    "proposal": {
        "hard_blockers": [
            "resolved_destination",  # Single target, not candidates
            "origin_city",
            "date_window",
            "party_size",
            "selected_itinerary",
        ],
        "soft_blockers": [
            "special_requests",
            "dietary_restrictions",
        ],
    },
    "booking": {
        "hard_blockers": [
            "resolved_destination",  # Single target, not candidates
            "origin_city",
            "date_window",
            "party_size",
            "selected_itinerary",
            "passport_status",
            "visa_status",
            "payment_method",
        ],
        "soft_blockers": [],
    },
}

# Legacy aliases for backward compat with existing fixtures.
# DEPRECATED: These will be removed in a future version.
# All code should use canonical v0.2 field names directly.
# Migration: destination_city → destination_candidates, travel_dates → date_window,
# budget_range → budget_min, traveler_count → party_size,
# traveler_details → passport_status, traveler_preferences → soft_preferences
import warnings as _warnings

LEGACY_ALIASES = {
    "destination_city": "destination_candidates",
    "travel_dates": "date_window",
    "budget_range": "budget_min",
    "traveler_count": "party_size",
    "traveler_details": "passport_status",
    "traveler_preferences": "soft_preferences",
}


# =============================================================================
# SECTION 3: CONTRADICTION CLASSIFICATION
# =============================================================================

# Field name → contradiction type mapping (v0.2 field names + legacy)
CONTRADICTION_FIELD_MAP = {
    "destination_candidates": "destination_conflict",
    "destination_city": "destination_conflict",
    "date_window": "date_conflict",
    "travel_dates": "date_conflict",
    "date_start": "date_conflict",
    "date_end": "date_conflict",
    "budget_min": "budget_conflict",
    "budget_max": "budget_conflict",
    "budget_range": "budget_conflict",
    "budget_raw_text": "budget_conflict",
    "party_size": "party_conflict",
    "traveler_count": "party_conflict",
    "origin_city": "origin_conflict",
    "passport_status": "document_conflict",
    "visa_status": "document_conflict",
}

CONTRADICTION_ACTIONS = {
    "date_conflict":        {"decision": "STOP_NEEDS_REVIEW",  "priority": "critical"},
    "destination_conflict": {"decision": "ASK_FOLLOWUP",       "priority": "critical"},
    "budget_conflict":      {"decision": "BRANCH_OPTIONS",     "priority": "medium"},
    # Budget feasibility is stage-gated in run_gap_and_decision:
    # discovery/shortlist -> non-critical contradiction + soft blocker,
    # proposal/booking -> hard blocker.
    "budget_feasibility":   {"decision": "ASK_FOLLOWUP",       "priority": "high"},
    "party_conflict":       {"decision": "ASK_FOLLOWUP",       "priority": "high"},
    "origin_conflict":      {"decision": "ASK_FOLLOWUP",       "priority": "high"},
    "document_conflict":    {"decision": "STOP_NEEDS_REVIEW",  "priority": "critical"},
    "general_conflict":     {"decision": "ASK_FOLLOWUP",       "priority": "medium"},
}


def classify_contradiction(field_name: str) -> str:
    """Map a field name to a contradiction type."""
    return CONTRADICTION_FIELD_MAP.get(field_name, "general_conflict")


def get_contradiction_action(ctype: str) -> Dict[str, Any]:
    """Get the action for a contradiction type."""
    return CONTRADICTION_ACTIONS.get(
        ctype,
        {"decision": "ASK_FOLLOWUP", "priority": "medium"},
    )


# =============================================================================
# SECTION 4: AMBIGUITY SEVERITY CLASSIFICATION
# =============================================================================

AMBIGUITY_SEVERITY: Dict[str, str] = {
    # Blocking: field exists but cannot be used for decision
    ("destination_candidates", "unresolved_alternatives"): "blocking",
    ("destination_candidates", "destination_open"): "blocking",
    ("party_size", "value_vague"): "blocking",
    ("party_size", "composition_unclear"): "advisory",
    # Advisory: field exists, extra context needed but not blocking
    ("budget_raw_text", "budget_stretch_present"): "advisory",
    ("budget_raw_text", "budget_unclear_scope"): "advisory",
    ("budget_min", "budget_stretch_present"): "advisory",
    ("date_window", "date_window_only"): "advisory",
}


def classify_ambiguity_severity(field_name: str, ambiguity_type: str) -> str:
    """
    Classify whether an ambiguity blocks progression or is advisory.
    Defaults to advisory (conservative).
    """
    return AMBIGUITY_SEVERITY.get(
        (field_name, ambiguity_type),
        "advisory",
    )


def classify_ambiguities(packet: CanonicalPacket) -> List[AmbiguityRef]:
    """Convert packet ambiguities into DecisionResult AmbiguityRefs with severity."""
    refs = []
    for amb in packet.ambiguities:
        severity = classify_ambiguity_severity(amb.field_name, amb.ambiguity_type)
        refs.append(AmbiguityRef(
            field_name=amb.field_name,
            ambiguity_type=amb.ambiguity_type,
            raw_value=amb.raw_value,
            severity=severity,
        ))
    return refs


# =============================================================================
# SECTION 5: FIELD RESOLUTION & BLOCKER EVALUATION
# =============================================================================

def resolve_field(packet: CanonicalPacket, canonical_field: str) -> Optional[Slot]:
    """
    Look up a canonical field in the packet.
    Checks: facts → derived_signals (NOT hypotheses for blocker resolution).
    Also checks legacy aliases.
    """
    # Direct match in facts
    if canonical_field in packet.facts:
        return packet.facts[canonical_field]
    # Direct match in derived_signals
    if canonical_field in packet.derived_signals:
        return packet.derived_signals[canonical_field]
    # Legacy alias (DEPRECATED)
    if canonical_field in LEGACY_ALIASES:
        aliased = LEGACY_ALIASES[canonical_field]
        _warnings.warn(
            f"LEGACY_ALIASES lookup: '{canonical_field}' → '{aliased}'. "
            f"Use the canonical v0.2 field name directly. "
            f"Legacy aliases will be removed in a future version.",
            DeprecationWarning,
            stacklevel=3,
        )
        if aliased in packet.facts:
            return packet.facts[aliased]
        if aliased in packet.derived_signals:
            return packet.derived_signals[aliased]
    # Reverse: if the canonical_field is an alias, check the original
    for legacy, canonical in LEGACY_ALIASES.items():
        if canonical == canonical_field and legacy in packet.facts:
            return packet.facts[legacy]
    return None


def field_fills_blocker(
    slot: Optional[Slot],
    ambiguities: List[AmbiguityRef],
    field_name: str,
) -> bool:
    """
    A field fills a blocker ONLY if:
    1. It exists as a fact or derived_signal
    2. It has fact-level authority or derived_signal authority
    3. It is NOT ambiguous with "blocking" severity

    CRITICAL: hypotheses do NOT fill blockers.
    """
    if slot is None or slot.value is None:
        return False
    # Must be fact or derived_signal authority
    if not AuthorityLevel.is_fact(slot.authority_level) and \
       slot.authority_level != AuthorityLevel.DERIVED_SIGNAL:
        return False
    # Check for blocking ambiguities
    for amb in ambiguities:
        if amb.field_name == field_name and amb.severity == "blocking":
            return False
    return True


# =============================================================================
# SECTION 6: BUDGET FEASIBILITY (stub/heuristic)
# =============================================================================

# Coarse destination tier costs (INR per person, minimum viable)
# These are heuristic placeholders — marked as such.
BUDGET_FEASIBILITY_TABLE = {
    "Singapore": {"min_per_person": 60000, "maturity": "heuristic"},
    "Japan": {"min_per_person": 120000, "maturity": "heuristic"},
    "Dubai": {"min_per_person": 80000, "maturity": "heuristic"},
    "Thailand": {"min_per_person": 50000, "maturity": "heuristic"},
    "Maldives": {"min_per_person": 100000, "maturity": "heuristic"},
    "Europe": {"min_per_person": 150000, "maturity": "heuristic"},
    "Sri Lanka": {"min_per_person": 40000, "maturity": "heuristic"},
    "Andaman": {"min_per_person": 35000, "maturity": "heuristic"},
    "Andamans": {"min_per_person": 35000, "maturity": "heuristic"},
    "Goa": {"min_per_person": 15000, "maturity": "heuristic"},
    "Kerala": {"min_per_person": 20000, "maturity": "heuristic"},
    "Kashmir": {"min_per_person": 25000, "maturity": "heuristic"},
    "Bangkok": {"min_per_person": 50000, "maturity": "heuristic"},
    "Bali": {"min_per_person": 60000, "maturity": "heuristic"},
    "Vietnam": {"min_per_person": 50000, "maturity": "heuristic"},
    "Nepal": {"min_per_person": 20000, "maturity": "heuristic"},
    "Bhutan": {"min_per_person": 40000, "maturity": "heuristic"},
    "Mauritius": {"min_per_person": 100000, "maturity": "heuristic"},
    "Seychelles": {"min_per_person": 120000, "maturity": "heuristic"},
    "Turkey": {"min_per_person": 80000, "maturity": "heuristic"},
    "Istanbul": {"min_per_person": 80000, "maturity": "heuristic"},
    "Paris": {"min_per_person": 150000, "maturity": "heuristic"},
    "London": {"min_per_person": 150000, "maturity": "heuristic"},
    "Tokyo": {"min_per_person": 120000, "maturity": "heuristic"},
    "Osaka": {"min_per_person": 120000, "maturity": "heuristic"},
    "New York": {"min_per_person": 180000, "maturity": "heuristic"},
    # Domestic fallback
    "__default_domestic__": {"min_per_person": 15000, "maturity": "heuristic"},
    "__default_international__": {"min_per_person": 50000, "maturity": "heuristic"},
}


def get_numeric_budget(packet: CanonicalPacket) -> Optional[int]:
    """Extract numeric budget_min from packet facts."""
    slot = packet.facts.get("budget_min")
    if slot and isinstance(slot.value, (int, float)):
        return int(slot.value)
    # Fallback: try to parse from budget_raw_text
    raw_slot = packet.facts.get("budget_raw_text")
    if raw_slot and isinstance(raw_slot.value, str):
        import re
        match = re.search(r"(\d+(?:\.\d+)?)\s*([LlKk])?", raw_slot.value)
        if match:
            val = float(match.group(1))
            unit = (match.group(2) or "").lower()
            if unit == "l":
                val *= 100000
            elif unit == "k":
                val *= 1000
            return int(val)
    return None


def check_budget_feasibility(
    packet: CanonicalPacket,
    feasibility_table: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Compare stated budget against minimum viable cost for destination + party.

    Conservative under destination ambiguity: if destination is unresolved
    (multiple candidates), feasibility stays "unknown" rather than guessing
    from the first candidate.

    Returns: {"status": "feasible"|"tight"|"infeasible"|"unknown",
              "gap": int|None,
              "maturity": "stub"|"heuristic"|"verified"}
    """
    table = feasibility_table or BUDGET_FEASIBILITY_TABLE
    budget_min = get_numeric_budget(packet)
    if budget_min is None:
        return {"status": "unknown", "gap": None, "maturity": "heuristic"}

    # Prefer resolved_destination (single target) over destination_candidates
    resolved = packet.facts.get("resolved_destination")
    if resolved and resolved.value:
        dests = [resolved.value]
    else:
        dest_slot = packet.facts.get("destination_candidates")
        if not dest_slot or not dest_slot.value:
            return {"status": "unknown", "gap": None, "maturity": "heuristic"}
        dests = dest_slot.value
        if not isinstance(dests, list):
            dests = [dests]

    # If multiple unresolved candidates, stay conservative — do not guess
    if len(dests) > 1:
        return {"status": "unknown", "gap": None, "maturity": "heuristic",
                "reason": "Destination unresolved — feasibility cannot be determined"}

    if not dests:
        return {"status": "unknown", "gap": None, "maturity": "heuristic"}

    party_slot = packet.facts.get("party_size")
    if not party_slot or not party_slot.value:
        return {"status": "unknown", "gap": None, "maturity": "heuristic"}

    party_size = party_slot.value
    dest = dests[0]
    entry = table.get(dest)
    if not entry:
        intl_slot = packet.derived_signals.get("domestic_or_international")
        if intl_slot and intl_slot.value == "domestic":
            entry = table.get("__default_domestic__")
        else:
            entry = table.get("__default_international__")

    if not entry:
        return {"status": "unknown", "gap": None, "maturity": "heuristic"}

    min_per_person = entry.get("min_per_person", 0)
    estimated_minimum = min_per_person * party_size

    gap = budget_min - estimated_minimum
    if gap < -0.3 * estimated_minimum:
        return {"status": "infeasible", "gap": gap, "maturity": entry.get("maturity", "heuristic")}
    elif gap < 0:
        return {"status": "tight", "gap": gap, "maturity": entry.get("maturity", "heuristic")}
    return {"status": "feasible", "gap": gap, "maturity": entry.get("maturity", "heuristic")}


# =============================================================================
# SECTION 7: URGENCY-AWARE BLOCKER SUPPRESSION
# =============================================================================

def apply_urgency(urgency: str, soft_blockers: List[str]) -> List[str]:
    """
    If urgency is "high" (travel < 7 days), suppress low-value soft blockers.
    If urgency is "medium" (< 21 days), downgrade soft blockers to advisory.
    """
    if urgency == "high":
        return [b for b in soft_blockers if b in ("budget_min", "budget_raw_text")]
    elif urgency == "medium":
        return []
    return soft_blockers


# =============================================================================
# SECTION 8: RISK FLAG GENERATION
# =============================================================================

def generate_risk_flags(
    packet: CanonicalPacket,
    stage: str,
    cached_feasibility: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Generate contextual risk flags based on actual packet data.
    NOT static templates — these emerge from fact combinations.

    Accepts optional cached_feasibility to avoid recomputation.
    """
    risks = []

    # Composition risk
    comp = packet.facts.get("party_composition")
    dest = packet.facts.get("destination_candidates")
    if comp and comp.value:
        composition = comp.value
        if composition.get("elderly") and dest:
            dests = dest.value
            if isinstance(dests, list):
                risky_dests = {"Maldives", "Andaman", "Andamans", "Bhutan", "Nepal"}
                if any(d in risky_dests for d in dests):
                    risks.append({
                        "flag": "elderly_mobility_risk",
                        "severity": "high",
                        "message": f"Elderly travelers + {dests[0]} — verify medical access and mobility",
                    })
        if composition.get("children") and dest:
            ages = packet.facts.get("child_ages")
            if ages and ages.value:
                young_ages = [a for a in ages.value if a < 4]
                if young_ages:
                    risks.append({
                        "flag": "toddler_pacing_risk",
                        "severity": "medium",
                        "message": f"Toddler ({min(young_ages)}yo) — flag pacing and transfer complexity",
                    })

    # Document risk
    passport = packet.facts.get("passport_status")
    visa = packet.facts.get("visa_status")
    date_end = packet.facts.get("date_end")
    urgency = packet.derived_signals.get("urgency")
    if stage == "booking":
        if passport and isinstance(passport.value, dict):
            for traveler, info in passport.value.items():
                if isinstance(info, dict) and info.get("status") in ("expired", "expiring_soon"):
                    risks.append({
                        "flag": "document_risk",
                        "severity": "critical",
                        "message": f"{traveler}: passport {info.get('status')} — cannot book without valid passport",
                    })
        if visa and isinstance(visa.value, dict) and visa.value.get("requirement") == "required" \
           and visa.value.get("status") == "not_applied":
            risks.append({
                "flag": "visa_not_applied",
                "severity": "critical",
                "message": "Visa required but not applied — booking blocked",
            })
    if urgency and urgency.value == "high" and visa and isinstance(visa.value, dict) \
       and visa.value.get("requirement") == "required":
        risks.append({
            "flag": "visa_timeline_risk",
            "severity": "high",
            "message": "High urgency + visa required — timeline risk",
        })

    # Margin risk (from budget feasibility — reuse cached if available)
    feasibility = cached_feasibility if cached_feasibility is not None else check_budget_feasibility(packet)
    if feasibility["status"] == "infeasible":
        gap = feasibility["gap"]
        risks.append({
            "flag": "margin_risk",
            "severity": "high",
            "message": f"Budget infeasible — gap of ₹{abs(gap):,} below minimum viable cost",
            "maturity": feasibility.get("maturity", "heuristic"),
        })

    # Coordination risk (multi-party)
    sub_groups = packet.facts.get("sub_groups")
    if sub_groups and isinstance(sub_groups.value, dict):
        groups = sub_groups.value
        budget_slot = packet.facts.get("budget_min")
        if budget_slot and budget_slot.value:
            total_budget = budget_slot.value
            budget_shares = [
                g.budget_share if hasattr(g, 'budget_share') else g.get('budget_share', 0)
                for g in groups.values()
            ]
            budget_shares = [b for b in budget_shares if b]
            if budget_shares and total_budget:
                spread = max(budget_shares) - min(budget_shares)
                if spread > 0.3 * total_budget:
                    risks.append({
                        "flag": "coordination_risk",
                        "severity": "medium",
                        "message": f"Budget spread of ₹{spread:,} across groups — coordination risk",
                    })

    # Traveler-safe leakage risk
    # Triggered by: hypotheses, contradictions, ambiguities, or internal-only owner fields
    has_internal_data = bool(packet.hypotheses) or bool(packet.contradictions)
    has_blocking_ambiguities = any(
        a.ambiguity_type in ("unresolved_alternatives", "destination_open", "value_vague")
        for a in packet.ambiguities
    )
    has_internal_owner = False
    oc = packet.facts.get("owner_constraints")
    if oc and oc.value:
        constraints = oc.value
        if isinstance(constraints, list):
            has_internal_owner = any(
                getattr(c, 'visibility', None) == "internal_only" or
                (isinstance(c, dict) and c.get("visibility") == "internal_only")
                for c in constraints
            )

    if has_internal_data or has_blocking_ambiguities or has_internal_owner:
        internal = packet.derived_signals.get("internal_data_present")
        reasons = []
        if packet.hypotheses:
            reasons.append(f"{len(packet.hypotheses)} hypotheses")
        if packet.contradictions:
            reasons.append(f"{len(packet.contradictions)} contradictions")
        if has_blocking_ambiguities:
            reasons.append("blocking ambiguities")
        if has_internal_owner:
            reasons.append("internal-only owner constraints")

        risks.append({
            "flag": "traveler_safe_leakage_risk",
            "severity": "critical",
            "message": f"Internal data present ({', '.join(reasons)}) — ensure traveler-safe boundary",
        })

    return risks


# =============================================================================
# SECTION 9: LIFECYCLE SCORING & COMMERCIAL DECISION
# =============================================================================

def _signal_set(lifecycle: Optional[LifecycleInfo]) -> set[str]:
    if not lifecycle:
        return set()
    return set(lifecycle.commitment_signals) | set(lifecycle.risk_signals)


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _derive_lifecycle(packet: CanonicalPacket) -> Optional[LifecycleInfo]:
    if packet.lifecycle:
        return packet.lifecycle
    return None


def score_ghost_risk(lifecycle: Optional[LifecycleInfo]) -> float:
    if not lifecycle:
        return 0.0
    score = 0.0
    signals = _signal_set(lifecycle)

    if lifecycle.quote_opened and (lifecycle.days_since_last_reply or 0) >= 3:
        score += 0.35
    if lifecycle.options_viewed_count == 1 and lifecycle.quote_open_count >= 2:
        score += 0.15
    if lifecycle.links_clicked_count > 0:
        score += 0.10
    if "follow_up_sent_no_reply_48h" in signals:
        score += 0.15

    if "asked_concrete_booking_question" in signals:
        score -= 0.25
    if "shared_passport" in signals or "shared_traveler_docs" in signals:
        score -= 0.30
    if "requested_hold" in signals or "asked_payment_plan" in signals:
        score -= 0.20
    return _clamp01(score)


def score_window_shopper_risk(lifecycle: Optional[LifecycleInfo]) -> float:
    if not lifecycle:
        return 0.0
    score = 0.0
    signals = _signal_set(lifecycle)

    if lifecycle.revision_count >= 3:
        score += 0.20
    if "destination_flipped_2plus" in signals:
        score += 0.20
    if "budget_contradiction_unresolved" in signals:
        score += 0.15
    if lifecycle.options_viewed_count >= 5 and lifecycle.revision_count >= 3:
        score += 0.15
    if lifecycle.payment_stage == "none" and lifecycle.revision_count >= 5:
        score += 0.20
    if (lifecycle.days_since_last_reply or 0) > 14:
        score += 0.10

    if "planning_fee_paid" in signals:
        score -= 0.30
    if "fixed_dates_origin_confirmed" in signals:
        score -= 0.25
    if "shared_traveler_docs" in signals:
        score -= 0.20
    return _clamp01(score)


def score_repeat_likelihood(lifecycle: Optional[LifecycleInfo]) -> float:
    if not lifecycle:
        return 0.0
    score = 0.0
    signals = _signal_set(lifecycle)
    has_prior_trip = lifecycle.repeat_trip_count > 0 or lifecycle.last_trip_completed_at is not None

    if has_prior_trip:
        score += 0.30
    if "positive_feedback" in signals or "positive_review" in signals:
        score += 0.15
    if "fast_response_history" in signals:
        score += 0.10
    if "seasonal_repeat_pattern" in signals:
        score += 0.15
    if "profile_on_file" in signals or "family_preferences_on_file" in signals:
        score += 0.10
    if "referral_made" in signals:
        score += 0.10

    if "unresolved_complaint" in signals:
        score -= 0.25
    if "cancellation_dispute" in signals:
        score -= 0.20
    if "price_sensitive_no_win" in signals:
        score -= 0.15
    return _clamp01(score)


def score_churn_risk(lifecycle: Optional[LifecycleInfo]) -> float:
    if not lifecycle:
        return 0.0
    has_prior_trip = lifecycle.repeat_trip_count > 0 or lifecycle.last_trip_completed_at is not None
    if not has_prior_trip:
        return 0.0

    score = 0.0
    signals = _signal_set(lifecycle)
    if "no_engagement_next_trip_window" in signals:
        score += 0.30
    if "no_feedback_captured" in signals:
        score += 0.20
    if "last_trip_issue" in signals:
        score += 0.15
    if "no_reactivation_sent" in signals:
        score += 0.15
    if "price_objections_last_quote" in signals:
        score += 0.10

    if "positive_review" in signals:
        score -= 0.25
    if "referral_made" in signals:
        score -= 0.20
    if "anniversary_intent_observed" in signals or "seasonal_intent_observed" in signals:
        score -= 0.20
    return _clamp01(score)


def compute_intent_scores(packet: CanonicalPacket) -> Dict[str, float]:
    lifecycle = _derive_lifecycle(packet)
    return {
        "ghost_risk": round(score_ghost_risk(lifecycle), 3),
        "window_shopper_risk": round(score_window_shopper_risk(lifecycle), 3),
        "repeat_likelihood": round(score_repeat_likelihood(lifecycle), 3),
        "churn_risk": round(score_churn_risk(lifecycle), 3),
    }


def decide_commercial_action(
    packet: CanonicalPacket,
    intent_scores: Dict[str, float],
) -> Tuple[str, Optional[str]]:
    lifecycle = _derive_lifecycle(packet)
    if lifecycle and (lifecycle.status == "LOST" or lifecycle.loss_reason):
        return "CLOSE_LOST", "CLOSE_LOST"

    ghost = intent_scores.get("ghost_risk", 0.0)
    window = intent_scores.get("window_shopper_risk", 0.0)
    repeat = intent_scores.get("repeat_likelihood", 0.0)
    churn = intent_scores.get("churn_risk", 0.0)

    if ghost >= 0.70:
        return "SEND_FOLLOWUP", "SEND_TARGETED_FOLLOWUP"
    if window >= 0.75:
        if lifecycle and lifecycle.payment_stage == "none":
            return "REQUEST_TOKEN", "REQUEST_TOKEN_OR_PLANNING_FEE"
        return "SET_BOUNDARY", "SET_REVISION_BOUNDARY"
    if churn >= 0.65:
        return "REACTIVATE_REPEAT", "CHURN_RECOVERY_REACHOUT"
    if repeat >= 0.70:
        return "REACTIVATE_REPEAT", "PERSONALIZED_REACTIVATION"
    if ghost >= 0.40:
        return "MOVE_TO_NURTURE", "MOVE_TO_NURTURE"
    if window >= 0.50:
        return "SET_BOUNDARY", "SET_REVISION_BOUNDARY"
    if churn >= 0.40:
        return "MOVE_TO_NURTURE", "MOVE_TO_NURTURE"
    return "NONE", None


# =============================================================================
# SECTION 10: OPERATING MODE ROUTING
# =============================================================================

def apply_operating_mode(
    packet: CanonicalPacket,
    hard_blockers: List[str],
    soft_blockers: List[str],
    contradictions: List[Dict[str, Any]],
    feasibility: Dict[str, Any],
) -> Tuple[List[str], List[Dict[str, Any]], Optional[str]]:
    """
    Apply operating-mode-specific routing rules.
    Returns (modified_soft_blockers, modified_contradictions, forced_decision_state or None).
    """
    mode = packet.operating_mode
    urgency = packet.derived_signals.get("urgency")
    urgency_level = urgency.value if urgency else None

    if mode == "emergency":
        # Suppress all soft blockers — urgency is already high
        soft_blockers = []
        # Check for critical contradictions → STOP
        for c in contradictions:
            ctype = classify_contradiction(c.get("field_name", ""))
            action = get_contradiction_action(ctype)
            if action["priority"] == "critical" and ctype == "date_conflict":
                return soft_blockers, contradictions, "STOP_NEEDS_REVIEW"
        # Otherwise continue with emergency intake
        return soft_blockers, contradictions, None

    elif mode == "audit":
        # Add value_gap check — flag both infeasible and tight budgets
        if feasibility["status"] in ("infeasible", "tight"):
            contradictions.append({
                "field_name": "budget_feasibility",
                "values": [f"budget_min vs estimated_minimum_cost (gap: {feasibility['gap']})"],
                "sources": ["budget_feasibility_check"],
            })
        return soft_blockers, contradictions, None

    elif mode == "follow_up":
        # Follow-up mode: if all hard blockers are filled, prefer PROCEED over ASK
        # (the point is to re-engage, not re-collect). Also skip soft blocker follow-ups
        # that were already asked in the original intake.
        if not hard_blockers and soft_blockers:
            # Demote soft blockers to advisory — we're re-engaging, not starting fresh
            soft_blockers = []
        return soft_blockers, contradictions, None

    elif mode == "cancellation":
        # Cancellation mode: suppress soft blockers (not relevant for cancellation).
        # Hard blockers remain but cancellation-relevant fields take priority.
        # Add cancellation policy as a tracked item.
        if "cancellation_policy" not in [c.get("field_name") for c in contradictions]:
            contradictions.append({
                "field_name": "cancellation_policy",
                "values": ["pending_policy_lookup"],
                "sources": ["cancellation_mode_routing"],
            })
        return [], contradictions, None

    elif mode == "post_trip":
        # Skip blocker logic entirely
        return [], [], None

    elif mode == "coordinator_group":
        # Per-sub-group logic — for now, aggregate soft blockers
        # In production, this would check each sub-group's readiness
        return soft_blockers, contradictions, None

    elif mode == "owner_review":
        # Flag margin risks
        if feasibility["status"] in ("infeasible", "tight"):
            contradictions.append({
                "field_name": "budget_feasibility",
                "values": [f"Budget {feasibility['status']} (gap: {feasibility['gap']})"],
                "sources": ["owner_review_check"],
            })
        return soft_blockers, contradictions, None

    # normal_intake: apply urgency suppression
    if urgency_level:
        soft_blockers = apply_urgency(urgency_level, soft_blockers)

    return soft_blockers, contradictions, None


# =============================================================================
# SECTION 10: CONFIDENCE SCORING
# =============================================================================

def calculate_confidence(packet: CanonicalPacket) -> float:
    """
    Authority-weighted confidence based on:
    - Fact confidence (authority-weighted)
    - Hypothesis confidence (discounted)
    - Unknown penalties
    """
    AUTHORITY_WEIGHTS = {
        "manual_override": 1.0,
        "explicit_user": 0.95,
        "imported_structured": 0.85,
        "explicit_owner": 0.80,
        "derived_signal": 0.60,
        "soft_hypothesis": 0.0,
        "unknown": 0.0,
    }

    # Authority-weighted fact confidence
    fact_weight = 0.0
    fact_count = 0
    for slot in packet.facts.values():
        auth_weight = AUTHORITY_WEIGHTS.get(slot.authority_level, 0.0)
        fact_weight += slot.confidence * auth_weight
        fact_count += 1

    if fact_count > 0:
        fact_weight /= fact_count

    # Hypothesis confidence (discounted)
    hypothesis_weight = 0.0
    hyp_count = 0
    for slot in packet.hypotheses.values():
        hypothesis_weight += slot.confidence * 0.5
        hyp_count += 1

    if hyp_count > 0:
        hypothesis_weight /= hyp_count

    # Unknown penalty
    unknown_penalty = len(packet.unknowns) * 0.1

    # Combine
    raw = fact_weight + (hypothesis_weight * 0.2) - unknown_penalty
    return min(1.0, max(0.0, raw))


# =============================================================================
# SECTION 11: QUESTION GENERATION
# =============================================================================

QUESTIONS = {
    "destination_candidates": "Where would you like to go? (Any specific destinations or are you open?)",
    "origin_city": "Which city will you be departing from?",
    "date_window": "When are you planning to travel? Are the dates fixed or flexible?",
    "party_size": "How many people will be traveling?",
    "budget_raw_text": "What's your approximate budget for this trip?",
    "budget_min": "Could you confirm the budget in numeric terms?",
    "trip_purpose": "What's the main purpose of this trip? (leisure, business, pilgrimage, etc.)",
    "soft_preferences": "Any specific preferences or must-haves for this trip?",
    "budget_feasibility": "The current budget may be too low for your destination and group size. Can we adjust?",
    "selected_itinerary": "Which itinerary option do you prefer?",
    "passport_status": "We'll need passport details for booking. Are all passports valid?",
    "visa_status": "Do you have the required visas, or do you need help with that?",
    "payment_method": "How would you like to handle payment? (card, transfer, etc.)",
}


def generate_question(field_name: str) -> str:
    """Generate a human-readable question for a missing field."""
    return QUESTIONS.get(field_name, f"Can you provide details for: {field_name}?")


# =============================================================================
# SECTION 12: MAIN ENTRY POINT
# =============================================================================

def run_gap_and_decision(
    packet: CanonicalPacket,
    feasibility_table: Optional[Dict[str, Any]] = None,
    _cached_feasibility: Optional[Dict[str, Any]] = None,
) -> DecisionResult:
    """
    Main entry point: CanonicalPacket v0.2 → DecisionResult.

    This is the NB02 judgment engine. It:
    1. Classifies ambiguities (blocking vs advisory)
    2. Applies operating-mode routing
    3. Evaluates urgency-aware blocker suppression
    4. Checks budget feasibility (cached per call)
    5. Evaluates contradictions
    6. Computes decision state
    7. Generates follow-up questions
    8. Generates risk flags

    Confidence formula (authoritative):
        confidence = avg(fact_weight) + 0.2 * avg(hypothesis_weight) - unknown_penalty
    where:
        fact_weight    = slot.confidence * authority_weight(slot.authority_level)
        authority_weight = {manual_override: 1.0, explicit_user: 0.95,
                            imported_structured: 0.85, explicit_owner: 0.80}
        hypothesis_weight = slot.confidence * 0.5
        unknown_penalty  = len(packet.unknowns) * 0.1
    Result clamped to [0.0, 1.0].
    """
    stage = packet.stage
    mode = packet.operating_mode
    mvb = MVB_BY_STAGE.get(stage, MVB_BY_STAGE["discovery"])

    # --- Phase 1: Classify ambiguities ---
    ambiguities = classify_ambiguities(packet)

    # --- Phase 2: Budget feasibility (computed once, reused downstream) ---
    feasibility = _cached_feasibility if _cached_feasibility is not None else check_budget_feasibility(packet, feasibility_table)

    # --- Phase 3: Evaluate blockers ---
    hard_blockers = []
    soft_blockers = []

    for field_name in mvb["hard_blockers"]:
        slot = resolve_field(packet, field_name)
        if not field_fills_blocker(slot, ambiguities, field_name):
            if field_name not in hard_blockers:
                hard_blockers.append(field_name)

    for field_name in mvb["soft_blockers"]:
        slot = resolve_field(packet, field_name)
        if not field_fills_blocker(slot, ambiguities, field_name):
            soft_blockers.append(field_name)

    # --- Phase 4: Operating mode routing ---
    contradictions = list(packet.contradictions)
    soft_blockers, contradictions, forced_decision = apply_operating_mode(
        packet, hard_blockers, soft_blockers, contradictions, feasibility,
    )

    # --- Phase 5: Budget feasibility stage gating ---
    if feasibility["status"] == "infeasible":
        strict_budget_stages = {"proposal", "booking"}
        if stage in strict_budget_stages:
            if "budget_feasibility" not in hard_blockers:
                hard_blockers.append("budget_feasibility")
        else:
            if "budget_feasibility" not in soft_blockers:
                soft_blockers.append("budget_feasibility")
        contradictions.append({
            "field_name": "budget_feasibility",
            "values": [
                f"budget_min={get_numeric_budget(packet)} vs estimated_minimum (gap: {feasibility['gap']})"
            ],
            "sources": ["budget_feasibility_check"],
        })

    # --- Phase 6: Urgency suppression (for normal_intake) ---
    if mode == "normal_intake":
        urgency = packet.derived_signals.get("urgency")
        if urgency and urgency.value:
            soft_blockers = apply_urgency(urgency.value, soft_blockers)

    # --- Phase 7: Contradiction evaluation ---
    critical_contradictions = []
    for c in contradictions:
        ctype = classify_contradiction(c.get("field_name", ""))
        action = get_contradiction_action(ctype)
        if action["priority"] == "critical":
            critical_contradictions.append({**c, "action": action, "type": ctype})

    # --- Phase 8: Confidence ---
    confidence = calculate_confidence(packet)

    # --- Phase 9: Decision state machine ---
    follow_up_questions = []
    branch_options = []
    decision_state: Optional[str] = forced_decision

    if decision_state is None:
        # Critical contradictions → STOP or ASK
        if critical_contradictions:
            for cc in critical_contradictions:
                follow_up_questions.append({
                    "field_name": cc["field_name"],
                    "question": generate_question(cc["field_name"]),
                    "priority": "critical",
                    "can_infer": False,
                    "inference_confidence": 0.0,
                })
            has_date_conflict = any(cc["type"] == "date_conflict" for cc in critical_contradictions)
            has_document_conflict = any(cc["type"] == "document_conflict" for cc in critical_contradictions)
            if has_date_conflict or has_document_conflict:
                decision_state = "STOP_NEEDS_REVIEW"
            else:
                decision_state = "ASK_FOLLOWUP"

        # Hard blockers → ASK_FOLLOWUP
        elif hard_blockers:
            for blocker in hard_blockers:
                slot = resolve_field(packet, blocker)
                # Check if a hypothesis exists (can't fill but can suggest)
                hyp_slot = packet.hypotheses.get(blocker)
                suggested = [hyp_slot.value] if hyp_slot and hyp_slot.value else []
                can_infer = hyp_slot is not None
                inference_conf = round(hyp_slot.confidence * 0.3, 2) if hyp_slot else 0.0

                follow_up_questions.append({
                    "field_name": blocker,
                    "question": generate_question(blocker),
                    "priority": "critical",
                    "can_infer": can_infer,
                    "inference_confidence": inference_conf,
                    "suggested_values": suggested,
                })
            decision_state = "ASK_FOLLOWUP"

        # Budget contradictions that suggest branching
        elif any(classify_contradiction(c.get("field_name", "")) == "budget_conflict" for c in contradictions):
            branch_options.append({
                "label": "Budget-tier options",
                "description": "Different budget interpretations suggest different trip tiers.",
                "contradictions": [c for c in contradictions if classify_contradiction(c.get("field_name", "")) == "budget_conflict"],
            })
            decision_state = "BRANCH_OPTIONS"

        else:
            # All blockers filled — check ambiguities and soft blockers
            blocking_ambiguities = [a for a in ambiguities if a.severity == "blocking"]
            if not blocking_ambiguities and not soft_blockers:
                decision_state = "PROCEED_TRAVELER_SAFE"
            elif soft_blockers:
                # Soft blockers only → PROCEED_INTERNAL_DRAFT
                for blocker in soft_blockers:
                    slot = resolve_field(packet, blocker)
                    can_infer = slot is not None and not AuthorityLevel.is_fact(slot.authority_level)
                    inference_conf = round(slot.confidence * 0.5, 2) if slot else 0.0
                    suggested = [slot.value] if slot and slot.value else []

                    follow_up_questions.append({
                        "field_name": blocker,
                        "question": generate_question(blocker),
                        "priority": "high" if not can_infer else "medium",
                        "can_infer": can_infer,
                        "inference_confidence": inference_conf,
                        "suggested_values": suggested,
                    })
                decision_state = "PROCEED_INTERNAL_DRAFT"
            elif blocking_ambiguities:
                # Blocking ambiguities → ASK_FOLLOWUP
                for amb in blocking_ambiguities:
                    follow_up_questions.append({
                        "field_name": amb.field_name,
                        "question": generate_question(amb.field_name),
                        "priority": "critical",
                        "can_infer": False,
                        "inference_confidence": 0.0,
                    })
                decision_state = "ASK_FOLLOWUP"
            else:
                # Confidence below threshold but no blockers
                if confidence < 0.6:
                    decision_state = "PROCEED_INTERNAL_DRAFT"
                else:
                    decision_state = "PROCEED_TRAVELER_SAFE"

    # --- Phase 10: Risk flags (reuse cached feasibility) ---
    risk_flags = generate_risk_flags(packet, stage, cached_feasibility=feasibility)

    # --- Phase 11: Post-trip mode skips blocker logic ---
    if mode == "post_trip":
        decision_state = "PROCEED_TRAVELER_SAFE"
        hard_blockers = []
        soft_blockers = []
        follow_up_questions = []

    # --- Invariant check: blocking ambiguities prevent PROCEED_TRAVELER_SAFE ---
    blocking_ambiguities = [a for a in ambiguities if a.severity == "blocking"]
    if decision_state == "PROCEED_TRAVELER_SAFE" and blocking_ambiguities:
        decision_state = "ASK_FOLLOWUP"

    # --- Invariant check: infeasible budget never PROCEED_TRAVELER_SAFE ---
    if feasibility["status"] == "infeasible" and decision_state == "PROCEED_TRAVELER_SAFE":
        decision_state = "ASK_FOLLOWUP"

    intent_scores = compute_intent_scores(packet)
    commercial_decision, next_best_action = decide_commercial_action(packet, intent_scores)

    rationale = {
        "hard_blockers": hard_blockers,
        "soft_blockers": soft_blockers,
        "contradictions": [c.get("field_name", "unknown") for c in contradictions],
        "confidence": round(confidence, 3),
        "feasibility": feasibility["status"],
        "operating_mode": mode,
        "commercial_decision": commercial_decision,
    }

    return DecisionResult(
        packet_id=packet.packet_id,
        current_stage=stage,
        operating_mode=mode,
        decision_state=decision_state or "ASK_FOLLOWUP",
        hard_blockers=hard_blockers,
        soft_blockers=soft_blockers,
        ambiguities=ambiguities,
        contradictions=contradictions,
        follow_up_questions=follow_up_questions,
        branch_options=branch_options,
        rationale=rationale,
        confidence_score=round(confidence, 3),
        risk_flags=risk_flags,
        commercial_decision=commercial_decision,
        intent_scores=intent_scores,
        next_best_action=next_best_action,
    )
