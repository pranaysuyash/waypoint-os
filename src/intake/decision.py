"""
intake.decision — NB02 v0.2: Gap and Decision (Agency Judgment Engine).

Consumes CanonicalPacket v0.2 from NB01, returns DecisionResult.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Tuple

from .packet_models import (
    Ambiguity,
    CanonicalPacket,
    LifecycleInfo,
    Slot,
    AuthorityLevel,
)
from src.intake.config.agency_settings import AgencySettings
from src.intake.telemetry import emit_ambiguity_synthesis

# =============================================================================
# HYBRID DECISION ENGINE INTEGRATION
# =============================================================================

# Feature flag to enable hybrid decision engine
# Set via environment variable: USE_HYBRID_DECISION_ENGINE=1
_HYBRID_ENGINE_ENABLED = os.environ.get("USE_HYBRID_DECISION_ENGINE", "1") == "1"

# Lazy-load hybrid engine only when enabled
_hybrid_engine_instance = None


def _get_hybrid_engine():
    """Get or create the hybrid decision engine instance."""
    global _hybrid_engine_instance
    if not _HYBRID_ENGINE_ENABLED:
        return None

    if _hybrid_engine_instance is None:
        try:
            from src.decision.hybrid_engine import create_hybrid_engine
            _hybrid_engine_instance = create_hybrid_engine(
                enable_cache=True,
                enable_rules=True,
                enable_llm=True,
            )
        except ImportError:
            # Hybrid engine not available
            return None
        except Exception as e:
            # Log but don't fail - fall back to rule engine
            print(f"Warning: Failed to initialize hybrid engine: {e}")
            return None

    return _hybrid_engine_instance


def _generate_risk_flags_with_hybrid_engine(
    packet: CanonicalPacket,
    stage: str,
    cached_feasibility: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Generate risk flags using the hybrid decision engine.

    This function uses the hybrid engine's rules + cache + LLM to generate
    contextual risk flags. Falls back to empty list if engine unavailable.

    Args:
        packet: CanonicalPacket with travel information
        stage: Current stage (discovery, shortlist, proposal, booking)
        cached_feasibility: Optional pre-computed feasibility result

    Returns:
        List of risk flag dictionaries
    """
    engine = _get_hybrid_engine()
    if not engine:
        return []

    risks = []

    # Decision types to check
    decision_types = [
        "elderly_mobility_risk",
        "toddler_pacing_risk",
        "composition_risk",
        "visa_timeline_risk",
    ]

    # Add budget_feasibility for booking stage
    if stage == "booking":
        decision_types.append("budget_feasibility")

    for decision_type in decision_types:
        try:
            result = engine.decide(decision_type, packet)

            # Convert hybrid engine result to risk flag format
            if result and result.decision:
                risk_level = result.decision.get("risk_level", "low")

                # Map risk level to severity
                severity_map = {"low": "low", "medium": "medium", "high": "high"}
                severity = severity_map.get(risk_level, "low")

                # Build reasoning from hybrid engine output
                reasoning = result.decision.get("reasoning", "")

                # Map decision type to flag name
                flag_map = {
                    "elderly_mobility_risk": "elderly_mobility_risk",
                    "toddler_pacing_risk": "toddler_pacing_risk",
                    "composition_risk": "composition_risk",
                    "visa_timeline_risk": "visa_timeline_risk",
                    "budget_feasibility": "margin_risk",
                }

                flag = flag_map.get(decision_type, decision_type)

                # Add risk flag if not low risk
                if risk_level != "low":
                    risks.append({
                        "flag": flag,
                        "severity": severity,
                        "message": reasoning,
                        "source": result.source,  # "rule", "llm", or "cache"
                        "recommendations": result.decision.get("recommendations", []),
                    })

        except Exception as e:
            # Log but continue with other decision types
            print(f"Warning: Hybrid engine failed for {decision_type}: {e}")
            continue

    return risks


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


COST_BUCKET_NAMES = (
    "flights",
    "stay",
    "food",
    "local_transport",
    "activities",
    "visa_insurance",
    "shopping",
    "buffer",
)


@dataclass
class CostBucketEstimate:
    bucket: str
    low: int
    high: int
    covered: bool
    notes: Optional[str] = None


@dataclass
class BudgetBreakdownResult:
    verdict: Literal["realistic", "borderline", "not_realistic"]
    buckets: List[CostBucketEstimate] = field(default_factory=list)
    missing_buckets: List[str] = field(default_factory=list)
    total_estimated_low: int = 0
    total_estimated_high: int = 0
    budget_stated: Optional[int] = None
    gap: Optional[int] = None
    risks: List[str] = field(default_factory=list)
    critical_changes: List[str] = field(default_factory=list)
    must_confirm: List[str] = field(default_factory=list)
    alternative: Optional[str] = None
    maturity: str = "heuristic"


@dataclass
class AmbiguityRef:
    """A reference to a packet ambiguity, with severity classification."""
    field_name: str
    ambiguity_type: str
    raw_value: str
    severity: str  # "blocking" | "advisory"


@dataclass
class ConfidenceScorecard:
    """Structured confidence across three orthogonal axes."""
    data_quality: float = 0.0          # Evidence density and extraction confidence
    judgment_confidence: float = 0.0    # Rule-hit strength and LLM consistency
    commercial_confidence: float = 0.0 # Budget alignment and feasibility
    overall: float = 0.0               # Weighted average

    def calculate_overall(self) -> float:
        """Simple weighted average for backward compatibility."""
        self.overall = (self.data_quality * 0.4) + (self.judgment_confidence * 0.4) + (self.commercial_confidence * 0.2)
        return self.overall


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
    confidence: ConfidenceScorecard = field(default_factory=ConfidenceScorecard)
    risk_flags: List[Dict[str, Any]] = field(default_factory=list)
    suitability_profile: Optional[Any] = None  # Shadow field — zero breakage
    commercial_decision: str = "NONE"          # One of COMMERCIAL_DECISIONS
    intent_scores: Dict[str, float] = field(default_factory=dict)
    next_best_action: Optional[str] = None
    budget_breakdown: Optional[BudgetBreakdownResult] = None


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
    ("destination_candidates", "value_vague"): "blocking",
    ("party_size", "value_vague"): "blocking",
    ("party_size", "composition_unclear"): "advisory",
    # Advisory: field exists, extra context needed but not blocking
    ("budget_raw_text", "budget_stretch_present"): "advisory",
    ("budget_raw_text", "budget_unclear_scope"): "advisory",
    ("budget_min", "budget_stretch_present"): "advisory",
    ("date_window", "date_window_only"): "advisory",
}


def classify_ambiguity_severity(field_name: str, ambiguity_type: str, stage: str = "discovery") -> str:
    """
    Classify whether an ambiguity blocks progression or is advisory.
    Defaults to advisory (conservative).

    Stage-aware escalation: destination vagueness is advisory at discovery,
    blocking at shortlist/proposal/booking.
    """
    # Base severity from table
    base_severity = AMBIGUITY_SEVERITY.get(
        (field_name, ambiguity_type),
        "advisory",
    )

    # Stage-aware escalation for destination_candidates value_vague
    if field_name == "destination_candidates" and ambiguity_type == "value_vague":
        if stage in ("shortlist", "proposal", "booking"):
            return "blocking"
        return "advisory"

    return base_severity


def classify_ambiguities(packet: CanonicalPacket) -> List[AmbiguityRef]:
    """Convert packet ambiguities into DecisionResult AmbiguityRefs with severity."""
    refs = []
    stage = packet.stage
    for amb in packet.ambiguities:
        severity = classify_ambiguity_severity(amb.field_name, amb.ambiguity_type, stage)
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

from src.decision.rules import BUDGET_FEASIBILITY_TABLE


BUDGET_BUCKET_RANGES: Dict[str, Dict[str, Tuple[int, int, float]]] = {
    "__default_international__": {
        "flights": (25000, 50000, 0.40),
        "stay": (20000, 45000, 0.30),
        "food": (5000, 10000, 0.10),
        "local_transport": (3000, 8000, 0.06),
        "activities": (5000, 12000, 0.08),
        "visa_insurance": (3000, 8000, 0.04),
        "shopping": (3000, 10000, 0.04),
        "buffer": (5000, 12000, 0.06),
    },
    "__default_domestic__": {
        "flights": (5000, 15000, 0.35),
        "stay": (4000, 10000, 0.25),
        "food": (2000, 5000, 0.10),
        "local_transport": (1000, 3000, 0.06),
        "activities": (2000, 5000, 0.08),
        "visa_insurance": (0, 500, 0.01),
        "shopping": (1000, 4000, 0.06),
        "buffer": (2000, 5000, 0.06),
    },
    "Dubai": {
        "flights": (18000, 40000, 0.38),
        "stay": (15000, 35000, 0.28),
        "food": (5000, 12000, 0.10),
        "local_transport": (3000, 8000, 0.06),
        "activities": (6000, 15000, 0.08),
        "visa_insurance": (3000, 6000, 0.04),
        "shopping": (5000, 15000, 0.05),
        "buffer": (5000, 12000, 0.05),
    },
    "Maldives": {
        "flights": (25000, 55000, 0.35),
        "stay": (30000, 70000, 0.32),
        "food": (8000, 18000, 0.10),
        "local_transport": (5000, 15000, 0.07),
        "activities": (5000, 12000, 0.06),
        "visa_insurance": (2000, 5000, 0.02),
        "shopping": (2000, 8000, 0.03),
        "buffer": (8000, 18000, 0.07),
    },
    "Singapore": {
        "flights": (18000, 40000, 0.36),
        "stay": (18000, 40000, 0.28),
        "food": (5000, 10000, 0.10),
        "local_transport": (2000, 6000, 0.06),
        "activities": (5000, 12000, 0.08),
        "visa_insurance": (1000, 3000, 0.02),
        "shopping": (5000, 12000, 0.05),
        "buffer": (5000, 10000, 0.05),
    },
    "Thailand": {
        "flights": (15000, 30000, 0.35),
        "stay": (10000, 25000, 0.28),
        "food": (3000, 8000, 0.10),
        "local_transport": (2000, 5000, 0.06),
        "activities": (3000, 10000, 0.08),
        "visa_insurance": (1000, 3000, 0.02),
        "shopping": (3000, 10000, 0.05),
        "buffer": (3000, 8000, 0.06),
    },
    "Japan": {
        "flights": (30000, 60000, 0.38),
        "stay": (25000, 50000, 0.28),
        "food": (10000, 20000, 0.12),
        "local_transport": (5000, 12000, 0.06),
        "activities": (8000, 15000, 0.07),
        "visa_insurance": (2000, 5000, 0.03),
        "shopping": (5000, 15000, 0.04),
        "buffer": (5000, 12000, 0.05),
    },
    "Europe": {
        "flights": (40000, 80000, 0.38),
        "stay": (30000, 60000, 0.28),
        "food": (8000, 18000, 0.10),
        "local_transport": (5000, 12000, 0.06),
        "activities": (8000, 15000, 0.07),
        "visa_insurance": (5000, 12000, 0.05),
        "shopping": (5000, 15000, 0.04),
        "buffer": (8000, 18000, 0.06),
    },
    "Bali": {
        "flights": (18000, 38000, 0.36),
        "stay": (15000, 35000, 0.28),
        "food": (3000, 8000, 0.10),
        "local_transport": (2000, 6000, 0.06),
        "activities": (4000, 10000, 0.08),
        "visa_insurance": (1500, 4000, 0.03),
        "shopping": (3000, 10000, 0.05),
        "buffer": (4000, 10000, 0.06),
    },
    "Goa": {
        "flights": (3000, 8000, 0.30),
        "stay": (3000, 8000, 0.25),
        "food": (2000, 5000, 0.12),
        "local_transport": (1000, 3000, 0.06),
        "activities": (2000, 5000, 0.08),
        "visa_insurance": (0, 0, 0.00),
        "shopping": (1000, 3000, 0.06),
        "buffer": (2000, 5000, 0.07),
    },
    "Kerala": {
        "flights": (3000, 8000, 0.28),
        "stay": (3000, 8000, 0.26),
        "food": (2000, 5000, 0.12),
        "local_transport": (2000, 5000, 0.08),
        "activities": (2000, 5000, 0.08),
        "visa_insurance": (0, 0, 0.00),
        "shopping": (1000, 3000, 0.04),
        "buffer": (2000, 5000, 0.08),
    },
    "Kashmir": {
        "flights": (4000, 10000, 0.30),
        "stay": (4000, 10000, 0.25),
        "food": (2000, 6000, 0.12),
        "local_transport": (2000, 5000, 0.08),
        "activities": (3000, 6000, 0.08),
        "visa_insurance": (0, 0, 0.00),
        "shopping": (1000, 3000, 0.04),
        "buffer": (2000, 6000, 0.08),
    },
    "Sri Lanka": {
        "flights": (10000, 25000, 0.35),
        "stay": (8000, 18000, 0.26),
        "food": (3000, 8000, 0.12),
        "local_transport": (2000, 5000, 0.06),
        "activities": (3000, 8000, 0.08),
        "visa_insurance": (1000, 3000, 0.02),
        "shopping": (2000, 6000, 0.04),
        "buffer": (3000, 8000, 0.06),
    },
    "Vietnam": {
        "flights": (15000, 30000, 0.36),
        "stay": (8000, 18000, 0.26),
        "food": (3000, 8000, 0.12),
        "local_transport": (1500, 5000, 0.06),
        "activities": (3000, 8000, 0.08),
        "visa_insurance": (1000, 3000, 0.02),
        "shopping": (2000, 6000, 0.04),
        "buffer": (3000, 8000, 0.06),
    },
    "Andaman": {
        "flights": (6000, 15000, 0.32),
        "stay": (6000, 15000, 0.28),
        "food": (3000, 6000, 0.10),
        "local_transport": (2000, 5000, 0.06),
        "activities": (3000, 8000, 0.08),
        "visa_insurance": (0, 0, 0.00),
        "shopping": (1000, 3000, 0.04),
        "buffer": (3000, 7000, 0.06),
    },
    "Andamans": {
        "flights": (6000, 15000, 0.32),
        "stay": (6000, 15000, 0.28),
        "food": (3000, 6000, 0.10),
        "local_transport": (2000, 5000, 0.06),
        "activities": (3000, 8000, 0.08),
        "visa_insurance": (0, 0, 0.00),
        "shopping": (1000, 3000, 0.04),
        "buffer": (3000, 7000, 0.06),
    },
    "Nepal": {
        "flights": (5000, 12000, 0.32),
        "stay": (4000, 10000, 0.26),
        "food": (2000, 5000, 0.12),
        "local_transport": (1000, 4000, 0.08),
        "activities": (2000, 6000, 0.08),
        "visa_insurance": (0, 500, 0.01),
        "shopping": (1000, 4000, 0.04),
        "buffer": (2000, 6000, 0.06),
    },
    "Bhutan": {
        "flights": (8000, 18000, 0.34),
        "stay": (10000, 22000, 0.30),
        "food": (3000, 6000, 0.10),
        "local_transport": (2000, 6000, 0.06),
        "activities": (3000, 8000, 0.08),
        "visa_insurance": (0, 500, 0.01),
        "shopping": (1000, 4000, 0.04),
        "buffer": (3000, 7000, 0.06),
    },
    "Mauritius": {
        "flights": (25000, 50000, 0.36),
        "stay": (25000, 55000, 0.30),
        "food": (6000, 12000, 0.10),
        "local_transport": (3000, 8000, 0.06),
        "activities": (4000, 10000, 0.06),
        "visa_insurance": (1500, 4000, 0.02),
        "shopping": (3000, 10000, 0.04),
        "buffer": (5000, 12000, 0.06),
    },
    "Seychelles": {
        "flights": (30000, 60000, 0.37),
        "stay": (30000, 65000, 0.30),
        "food": (6000, 12000, 0.10),
        "local_transport": (3000, 8000, 0.06),
        "activities": (4000, 10000, 0.06),
        "visa_insurance": (0, 2000, 0.01),
        "shopping": (2000, 8000, 0.04),
        "buffer": (6000, 14000, 0.06),
    },
    "Turkey": {
        "flights": (25000, 50000, 0.36),
        "stay": (18000, 38000, 0.28),
        "food": (5000, 12000, 0.10),
        "local_transport": (3000, 8000, 0.06),
        "activities": (5000, 12000, 0.08),
        "visa_insurance": (3000, 6000, 0.04),
        "shopping": (3000, 10000, 0.04),
        "buffer": (5000, 12000, 0.05),
    },
    "Istanbul": {
        "flights": (25000, 50000, 0.36),
        "stay": (18000, 38000, 0.28),
        "food": (5000, 12000, 0.10),
        "local_transport": (3000, 8000, 0.06),
        "activities": (5000, 12000, 0.08),
        "visa_insurance": (3000, 6000, 0.04),
        "shopping": (3000, 10000, 0.04),
        "buffer": (5000, 12000, 0.05),
    },
    "Paris": {
        "flights": (40000, 80000, 0.38),
        "stay": (30000, 55000, 0.28),
        "food": (8000, 18000, 0.10),
        "local_transport": (5000, 12000, 0.06),
        "activities": (8000, 15000, 0.07),
        "visa_insurance": (5000, 12000, 0.05),
        "shopping": (5000, 15000, 0.04),
        "buffer": (8000, 18000, 0.06),
    },
    "London": {
        "flights": (40000, 80000, 0.38),
        "stay": (30000, 55000, 0.28),
        "food": (8000, 18000, 0.10),
        "local_transport": (5000, 12000, 0.06),
        "activities": (8000, 15000, 0.07),
        "visa_insurance": (5000, 12000, 0.05),
        "shopping": (5000, 15000, 0.04),
        "buffer": (8000, 18000, 0.06),
    },
    "Tokyo": {
        "flights": (30000, 60000, 0.38),
        "stay": (25000, 50000, 0.28),
        "food": (10000, 20000, 0.12),
        "local_transport": (5000, 12000, 0.06),
        "activities": (8000, 15000, 0.07),
        "visa_insurance": (2000, 5000, 0.03),
        "shopping": (5000, 15000, 0.04),
        "buffer": (5000, 12000, 0.05),
    },
    "Osaka": {
        "flights": (30000, 60000, 0.38),
        "stay": (25000, 50000, 0.28),
        "food": (10000, 20000, 0.12),
        "local_transport": (5000, 12000, 0.06),
        "activities": (8000, 15000, 0.07),
        "visa_insurance": (2000, 5000, 0.03),
        "shopping": (5000, 15000, 0.04),
        "buffer": (5000, 12000, 0.05),
    },
    "New York": {
        "flights": (50000, 95000, 0.38),
        "stay": (35000, 70000, 0.28),
        "food": (10000, 22000, 0.10),
        "local_transport": (5000, 12000, 0.06),
        "activities": (8000, 18000, 0.07),
        "visa_insurance": (8000, 15000, 0.05),
        "shopping": (5000, 15000, 0.04),
        "buffer": (8000, 18000, 0.06),
    },
    "Bangkok": {
        "flights": (15000, 30000, 0.35),
        "stay": (10000, 25000, 0.28),
        "food": (3000, 8000, 0.10),
        "local_transport": (2000, 5000, 0.06),
        "activities": (3000, 10000, 0.08),
        "visa_insurance": (1000, 3000, 0.02),
        "shopping": (3000, 10000, 0.05),
        "buffer": (3000, 8000, 0.06),
    },
}

_DESTINATION_ALIASES: Dict[str, str] = {
    "Andamans": "Andaman",
    "Istanbul": "Turkey",
    "Paris": "Europe",
    "London": "Europe",
    "Tokyo": "Japan",
    "Osaka": "Japan",
    "Bangkok": "Thailand",
    "New York": "New York",
}

_CHILD_SURCHARGE = 0.75
_TODDLER_SURCHARGE = 0.30
_ELDERLY_SURCHARGE = 0.05
_SEASON_MULTIPLIER_SHOULDER = 1.15
_SEASON_MULTIPLIER_PEAK = 1.30
_MULTI_COUNTRY_PENALTY = 1.10
_FAMILY_BUFFER_BUMP = 0.02


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
    agency_settings: Optional[AgencySettings] = None,
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
    base_estimated_minimum = min_per_person * party_size
    
    # Apply agency margin correctly (Base Cost * (1 + Margin% / 100))
    margin_pct = agency_settings.target_margin_pct if agency_settings else 15.0
    estimated_minimum = base_estimated_minimum * (1.0 + margin_pct / 100.0)

    gap = budget_min - estimated_minimum
    if gap < -0.3 * estimated_minimum:
        return {"status": "infeasible", "gap": gap, "maturity": entry.get("maturity", "heuristic")}
    elif gap < 0:
        return {"status": "tight", "gap": gap, "maturity": entry.get("maturity", "heuristic")}
    return {"status": "feasible", "gap": gap, "maturity": entry.get("maturity", "heuristic")}


def _resolve_bucket_table(dest: str, packet: CanonicalPacket) -> Dict[str, Tuple[int, int, float]]:
    primary = _DESTINATION_ALIASES.get(dest, dest)
    if primary in BUDGET_BUCKET_RANGES:
        return BUDGET_BUCKET_RANGES[primary]
    intl_slot = packet.derived_signals.get("domestic_or_international")
    if intl_slot and intl_slot.value == "domestic":
        return BUDGET_BUCKET_RANGES["__default_domestic__"]
    return BUDGET_BUCKET_RANGES["__default_international__"]


def _get_composition_modifiers(packet: CanonicalPacket) -> Tuple[float, float]:
    adult_equivalents = 0.0
    has_toddler = False
    has_elderly = False
    comp = packet.facts.get("party_composition")
    if comp and isinstance(comp.value, dict):
        has_toddler = bool(comp.value.get("toddlers", 0))
        has_elderly = bool(comp.value.get("elderly", 0))
        adults = comp.value.get("adults", 0)
        teens = comp.value.get("teens", 0)
        children = comp.value.get("children", 0)
        toddlers = comp.value.get("toddlers", 0)
        elderly = comp.value.get("elderly", 0)
        adult_equivalents = (
            adults
            + teens * _CHILD_SURCHARGE
            + children * _CHILD_SURCHARGE
            + toddlers * _TODDLER_SURCHARGE
        )
        if has_elderly:
            adult_equivalents += elderly * _ELDERLY_SURCHARGE
    else:
        party_slot = packet.facts.get("party_size")
        adult_equivalents = float(party_slot.value) if party_slot and party_slot.value else 1.0
    if has_toddler:
        adult_equivalents = adult_equivalents * (1 + _FAMILY_BUFFER_BUMP)
    return adult_equivalents, has_toddler


def _is_multi_destination(packet: CanonicalPacket) -> bool:
    dest_slot = packet.facts.get("destination_candidates")
    if dest_slot and isinstance(dest_slot.value, list):
        return len(dest_slot.value) > 1
    return False


def decompose_budget(
    packet: CanonicalPacket,
    bucket_table: Optional[Dict[str, Dict[str, Tuple[int, int, float]]]] = None,
    cached_feasibility: Optional[Dict[str, Any]] = None,
    agency_settings: Optional[AgencySettings] = None,
) -> BudgetBreakdownResult:
    """
    Decompose a trip budget into cost buckets with per-destination estimates.

    Architecture:
      1. Resolve destination -> bucket range table
      2. Scale per-person ranges by effective party size (adult-equivalents)
      3. Apply composition modifiers (toddler, elderly)
      4. Apply multi-destination penalty
      5. Compare total estimated range against stated budget
      6. Determine covered/missing buckets, verdict, risks, and alternatives
    """
    budget_min = get_numeric_budget(packet)
    if budget_min is None:
        return BudgetBreakdownResult(
            verdict="not_realistic",
            maturity="heuristic",
            risks=["budget_unknown"],
            critical_changes=["Provide a numeric budget for decomposition"],
        )

    resolved = packet.facts.get("resolved_destination")
    dests = []
    if resolved and resolved.value:
        dests = [resolved.value]
    else:
        dest_slot = packet.facts.get("destination_candidates")
        if dest_slot and dest_slot.value:
            dests = dest_slot.value if isinstance(dest_slot.value, list) else [dest_slot.value]

    if len(dests) > 1:
        primary_dest = dests[0]
    elif len(dests) == 1:
        primary_dest = dests[0]
    else:
        return BudgetBreakdownResult(
            verdict="not_realistic",
            budget_stated=budget_min,
            maturity="heuristic",
            risks=["destination_unknown"],
            critical_changes=["Specify a destination for budget decomposition"],
        )

    table_source = bucket_table or BUDGET_BUCKET_RANGES
    primary_key = _DESTINATION_ALIASES.get(primary_dest, primary_dest)
    if primary_key not in table_source:
        intl_slot = packet.derived_signals.get("domestic_or_international")
        if intl_slot and intl_slot.value == "domestic":
            bucket_ranges = table_source["__default_domestic__"]
        else:
            bucket_ranges = table_source["__default_international__"]
    else:
        bucket_ranges = table_source[primary_key]

    adult_equiv, has_toddler = _get_composition_modifiers(packet)
    is_multi = _is_multi_destination(packet)

    buckets: List[CostBucketEstimate] = []
    total_low = 0
    total_high = 0
    missing: List[str] = []

    for bname in COST_BUCKET_NAMES:
        if bname not in bucket_ranges:
            missing.append(bname)
            continue
        low_pp, high_pp, weight = bucket_ranges[bname]
        low = round(low_pp * adult_equiv)
        high = round(high_pp * adult_equiv)
        if is_multi and bname in ("flights", "local_transport", "buffer"):
            low = round(low * _MULTI_COUNTRY_PENALTY)
            high = round(high * _MULTI_COUNTRY_PENALTY)
        if has_toddler and bname in ("activities", "local_transport", "buffer"):
            high = round(high * 1.15)
            
        margin_pct = agency_settings.target_margin_pct if agency_settings else 15.0
        margin_mult = 1.0 + margin_pct / 100.0
        low = round(low * margin_mult)
        high = round(high * margin_mult)

        if bname == "visa_insurance" and low == 0 and high == 0:
            buckets.append(CostBucketEstimate(
                bucket=bname, low=0, high=0, covered=True, notes="Not applicable (domestic)",
            ))
        else:
            covered = budget_min >= low
            buckets.append(CostBucketEstimate(bucket=bname, low=low, high=high, covered=covered))
        total_low += low
        total_high += high

    gap = budget_min - total_low
    if budget_min >= total_high:
        verdict: str = "realistic"
    elif budget_min >= total_low:
        verdict = "borderline"
    elif gap >= -0.2 * total_low:
        verdict = "borderline"
    else:
        verdict = "not_realistic"

    for b in buckets:
        if not b.covered:
            missing.append(b.bucket)

    risks: List[str] = []
    critical_changes: List[str] = []
    must_confirm: List[str] = []

    flight_b = next((b for b in buckets if b.bucket == "flights"), None)
    if flight_b and budget_min < flight_b.low:
        risks.append("flight_inflation")
        must_confirm.append("flight_quote_for_party")

    stay_b = next((b for b in buckets if b.bucket == "stay"), None)
    if stay_b and budget_min < stay_b.high and "Maldives" in dests:
        risks.append("resort_premium")
        critical_changes.append("Consider 3-night Maldives stay instead of 4")

    ins_b = next((b for b in buckets if b.bucket == "visa_insurance"), None)
    if ins_b and ins_b.high > 0 and not ins_b.covered:
        risks.append("insurance_gap")
        must_confirm.append("travel_insurance_premium")

    if "visa_insurance" in missing and len(dests) > 1:
        risks.append("visa_fee_omission")
        must_confirm.append("visa_fees_for_all_destinations")

    if "shopping" in missing:
        risks.append("shopping_underbudget")
        critical_changes.append("Add explicit shopping allowance")

    if "buffer" in missing:
        risks.append("tight_buffer")
        critical_changes.append("Add 10-15% contingency buffer")

    if "food" in missing:
        risks.append("food_underbudget")
        critical_changes.append("Add explicit food and daily meal allowance")

    if "local_transport" in missing:
        risks.append("transport_gap")
        critical_changes.append("Budget for airport transfers and local mobility")

    if is_multi:
        risks.append("transfer_complexity")
        must_confirm.append("inter-destination_transfer_cost")

    if has_toddler:
        risks.append("toddler_addons")
        must_confirm.append("child_seat_and_transfer_cost")

    alternative = None
    if verdict in ("borderline", "not_realistic") and len(dests) > 1:
        alt_parts = [d for d in dests if d != dests[-1]]
        alternative = f"{' + '.join(alt_parts)} only, same dates — fewer transfers and lower resort costs"

    return BudgetBreakdownResult(
        verdict=verdict,
        buckets=buckets,
        missing_buckets=missing,
        total_estimated_low=total_low,
        total_estimated_high=total_high,
        budget_stated=budget_min,
        gap=gap,
        risks=risks,
        critical_changes=critical_changes,
        must_confirm=must_confirm,
        alternative=alternative,
        maturity="heuristic",
    )


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
    agency_settings: Optional[AgencySettings] = None,
) -> List[Dict[str, Any]]:
    """
    Generate contextual risk flags based on actual packet data.
    NOT static templates — these emerge from fact combinations.

    Accepts optional cached_feasibility to avoid recomputation.

    Uses hybrid decision engine when enabled (USE_HYBRID_DECISION_ENGINE=1),
    falling back to original rule-based logic for compatibility.
    """
    risks = []

    # --- HYBRID ENGINE: Handle supported decision types ---
    if _HYBRID_ENGINE_ENABLED:
        hybrid_risks = _generate_risk_flags_with_hybrid_engine(packet, stage, cached_feasibility)
        risks.extend(hybrid_risks)

        # If hybrid engine handled all risk types, skip the original logic
        # (except for critical document/visa status which must always be checked)
        # Continue to document risk checks below...
    else:
        # --- ORIGINAL RULES: Use when hybrid engine disabled ---
        # Composition risk (elderly mobility, toddler pacing)
        comp = packet.facts.get("party_composition")
        dest = packet.facts.get("destination_candidates")
        if comp and comp.value:
            composition = comp.value
            # Handle both dict format (from structured input) and string format (from free text)
            if isinstance(composition, dict) and composition.get("elderly") and dest:
                dests = dest.value
                if isinstance(dests, list):
                    risky_dests = {"Maldives", "Andaman", "Andamans", "Bhutan", "Nepal"}
                    if any(d in risky_dests for d in dests):
                        risks.append({
                            "flag": "elderly_mobility_risk",
                            "severity": "high",
                            "message": f"Elderly travelers + {dests[0]} — verify medical access and mobility",
                        })
            if isinstance(composition, dict) and composition.get("children") and dest:
                ages = packet.facts.get("child_ages")
                if ages and ages.value:
                    young_ages = [a for a in ages.value if a < 4]
                    if young_ages:
                        risks.append({
                            "flag": "toddler_pacing_risk",
                            "severity": "medium",
                            "message": f"Toddler ({min(young_ages)}yo) — flag pacing and transfer complexity",
                        })

    # --- CRITICAL DOCUMENT RISKS: Always check (not in hybrid engine) ---
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

    # --- VISA TIMELINE RISK: Check if not already handled by hybrid engine ---
    visa_flags = [r for r in risks if r["flag"] == "visa_timeline_risk"]
    if not visa_flags and urgency and urgency.value == "high" and visa and isinstance(visa.value, dict) \
       and visa.value.get("requirement") == "required":
        risks.append({
            "flag": "visa_timeline_risk",
            "severity": "high",
            "message": "High urgency + visa required — timeline risk",
        })

    # --- MARGIN RISK: Check if not already handled by hybrid engine ---
    margin_flags = [r for r in risks if r["flag"] == "margin_risk"]
    if not margin_flags:
        feasibility = cached_feasibility if cached_feasibility is not None else check_budget_feasibility(packet, agency_settings=agency_settings)
        if feasibility["status"] == "infeasible":
            gap = feasibility["gap"]
            risks.append({
                "flag": "margin_risk",
                "severity": "high",
                "message": f"Budget infeasible — gap of ₹{abs(gap):,} below minimum viable cost",
                "maturity": feasibility.get("maturity", "heuristic"),
            })

    # --- COORDINATION RISK: Multi-party budget spread (not in hybrid engine) ---
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

    # --- TRAVELER-SAFE LEAKAGE RISK: Always check (not in hybrid engine) ---
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
    
    # --- SUITABILITY RISK FLAGS: Activity suitability scoring ---
    # Only run suitability checks in shortlist/proposal/booking stages
    if stage in ("shortlist", "proposal", "booking"):
        try:
            from src.suitability.integration import generate_suitability_risks
            suitability_risks = generate_suitability_risks(packet)
            risks.extend(suitability_risks)
        except ImportError:
            # Suitability module not available yet
            pass
        except Exception as e:
            # Don't fail risk generation if suitability has issues
            print(f"Warning: Suitability risk generation failed: {e}")

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


def _build_suitability_profile(
    risk_flags: List[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """Map raw risk flags to structured SuitabilityProfile for frontend.

    Only dimensions flagged by the suitability subsystem are included.
    Zero-breakage: if no suitability flags are present, returns None so the
    frontend falls back to the generic risk_flags list.
    """
    # Filter flags that originated from the suitability subsystem.
    # The ``flag`` field uses a ``suitability_<tier>_`` prefix for those.
    suitability_prefixes = ("suitability_",)
    dimensions = []
    processed_flags = set()
    for flag in risk_flags:
        flag_name = flag.get("flag", "")
        flag_lower = flag_name.lower()

        # Skip flags already processed
        if flag_name in processed_flags:
            continue
        processed_flags.add(flag_name)

        # Map standard risk flags to suitability dimensions
        standard_flag_dimensions = {
            "elderly_mobility_risk": "mobility",
            "toddler_pacing_risk": "recovery",
            "composition_risk": "recovery",
            "visa_timeline_risk": "documentation",
            "visa_not_applied": "documentation",
            "document_risk": "documentation",
            "margin_risk": "budget",
            "budget_risk": "budget",
        }

        if flag_name.startswith(suitability_prefixes):
            intensity_keywords = {"scuba", "snorkeling", "skydiving", "bungy", "bungee", "white_water_rafting", "rafting", "paragliding", "zip_line"}
            mobility_keywords = {"trekking", "hiking", "city_walk", "walking_tour", "walking", "cycling", "biking", "stairs"}
            climate_keywords = {"sauna", "hot_spring", "desert_safari", "desert", "snow", "skiing", "cold"}
            pacing_keywords = {"pacing", "overload", "coherence"}

            dimension_type = "other"
            if any(kw in flag_lower for kw in intensity_keywords):
                dimension_type = "intensity"
            elif any(kw in flag_lower for kw in mobility_keywords):
                dimension_type = "mobility"
            elif any(kw in flag_lower for kw in climate_keywords):
                dimension_type = "climate"
            elif any(kw in flag_lower for kw in pacing_keywords):
                dimension_type = "recovery"
        elif flag_name in standard_flag_dimensions:
            dimension_type = standard_flag_dimensions[flag_name]
        else:
            continue

        severity_map = {
            "low": "low",
            "medium": "medium",
            "high": "high",
            "critical": "high",
        }
        dimensions.append({
            "type": dimension_type,
            "severity": severity_map.get(flag.get("severity", "low"), "low"),
            "score": round(flag.get("confidence", 0.5) * 100, 1),
            "reason": flag.get("message", ""),
            "evidence_id": flag.get("details", {}).get("activity_id"),
        })

    if not dimensions:
        return None

    # Derive summary.status from the highest severity present.
    severity_order = {"low": 0, "medium": 1, "high": 2}
    max_severity = max(
        dimensions, key=lambda d: severity_order.get(d["severity"], 0)
    )["severity"]
    status_map = {
        "low": "suitable",
        "medium": "caution",
        "high": "unsuitable",
    }
    # Derive overallScore: average of dimension scores, clamped 0-100.
    avg_score = sum(d["score"] for d in dimensions) / len(dimensions)
    primary_reason = "Multiple suitability concerns detected."
    if max_severity == "high":
        primary_reason = "One or more activities unsuitable for traveler profile."
    elif max_severity == "medium":
        primary_reason = "Some activities require additional review."
    else:
        primary_reason = "All activities suitable for traveler profile."

    return {
        "summary": {
            "status": status_map.get(max_severity, "caution"),
            "primaryReason": primary_reason,
            "overallScore": round(avg_score, 1),
        },
        "dimensions": dimensions,
        "overrides": [],
    }


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

def calculate_confidence(
    packet: CanonicalPacket, 
    feasibility: Optional[Dict[str, Any]] = None
) -> ConfidenceScorecard:
    """
    Authority-weighted confidence across three layers:
    - Data Quality: Fact density and authority weights
    - Judgment: Hypothesis strength and rule applicability
    - Commercial: Budget feasibility alignment
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

    # 1. Data Quality (Fact density and authority)
    data_quality = 0.0
    fact_count = 0
    for slot in packet.facts.values():
        auth_weight = AUTHORITY_WEIGHTS.get(slot.authority_level, 0.0)
        data_quality += slot.confidence * auth_weight
        fact_count += 1

    if fact_count > 0:
        data_quality /= fact_count

    # Apply penalty for unknowns
    unknown_penalty = len(packet.unknowns) * 0.1
    data_quality = max(0.0, data_quality - unknown_penalty)

    # 2. Judgment Confidence (Hypothesis strength)
    judgment_confidence = 0.0
    hyp_count = 0
    for slot in packet.hypotheses.values():
        judgment_confidence += slot.confidence * 0.5
        hyp_count += 1

    if hyp_count > 0:
        judgment_confidence /= hyp_count
    else:
        # If no hypotheses, and facts are high quality, judgment is stronger
        judgment_confidence = data_quality

    # 3. Commercial Confidence (Feasibility alignment)
    commercial_confidence = 0.0
    if feasibility:
        if feasibility.get("status") == "healthy":
            commercial_confidence = 1.0
        elif feasibility.get("status") == "borderline":
            commercial_confidence = 0.6
        else:
            commercial_confidence = 0.2
    else:
        # Default if feasibility not provided
        commercial_confidence = 0.5

    scorecard = ConfidenceScorecard(
        data_quality=round(data_quality, 3),
        judgment_confidence=round(judgment_confidence, 3),
        commercial_confidence=round(commercial_confidence, 3),
    )
    scorecard.calculate_overall()
    return scorecard


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


def generate_budget_question(
    packet: CanonicalPacket,
    budget_min: Optional[int] = None,
) -> str:
    """
    Generate budget question that preserves stretch semantics.
    
    Case A: "2L, can stretch" → ask for absolute upper limit
    Case B: "2L, can stretch to 2.5L" → confirm the stretch amount is correct
    """
    # Check for budget_stretch_present ambiguity
    stretch_ambiguity = None
    for amb in packet.ambiguities:
        if amb.field_name in ("budget_min", "budget_raw_text") and \
           amb.ambiguity_type == "budget_stretch_present":
            stretch_ambiguity = amb
            break
    
    if not stretch_ambiguity:
        # No stretch detected, use generic budget question
        return QUESTIONS.get("budget_min", "Could you confirm the budget in numeric terms?")
    
    # Check if explicit max was provided in raw value
    raw_value = stretch_ambiguity.raw_value if stretch_ambiguity else ""
    
    # Parse for "to X" pattern (e.g., "2L, can stretch to 2.5L")
    import re
    stretch_to_match = re.search(r"(?:to|up to|until)\s*(\d+(?:\.\d+)?)\s*(L|lakh|k|K)?", raw_value, re.IGNORECASE)
    
    if stretch_to_match:
        # Case B: Explicit upper bound mentioned
        amount = stretch_to_match.group(1)
        unit = stretch_to_match.group(2) or ""
        unit_str = unit if unit else ""
        return f"You mentioned {budget_min or 'a budget'} with flexibility up to {amount}{unit_str}. Is that the hard limit, or is there any wiggle room?"
    else:
        # Case A: Stretch mentioned but no explicit max
        base = budget_min if budget_min else "this amount"
        return f"You mentioned {base} with flexibility. What's the absolute upper limit you're comfortable with?"


def generate_candidate_question(
    packet: CanonicalPacket,
    candidates: List[str],
) -> str:
    """Generate candidate-specific question for multi-value destinations."""
    if len(candidates) == 2:
        return f"Between {candidates[0]} and {candidates[1]}, which are you leaning toward?"
    elif len(candidates) == 3:
        return f"Between {candidates[0]}, {candidates[1]}, and {candidates[2]}, which do you prefer?"
    else:
        candidates_str = ", ".join(candidates[:3])
        return f"From {candidates_str}, which destination interests you most?"


# =============================================================================
# SECTION 12: DESTINATION AMBIGUITY SYNTHESIS
# =============================================================================

def _synthesize_destination_ambiguity(
    packet: CanonicalPacket,
    ambiguities: List[AmbiguityRef],
) -> None:
    """
    Synthesize unresolved_alternatives ambiguity from destination value structure.

    If destination_candidates is a list with 2+ items but no blocking
    unresolved_alternatives ambiguity exists, create one. This handles packets
    from structured imports or API calls that bypass NB01 text extraction.

    Also mutates the packet to add the Ambiguity object so downstream
    consumers (NB03) have access to it.
    """
    has_unresolved = any(
        a.field_name == "destination_candidates"
        and a.ambiguity_type == "unresolved_alternatives"
        and a.severity == "blocking"
        for a in ambiguities
    )
    if has_unresolved:
        return

    dest_slot = resolve_field(packet, "destination_candidates")
    if not dest_slot or not isinstance(dest_slot.value, list) or len(dest_slot.value) < 2:
        return

    candidates = dest_slot.value[:3]
    raw_value = " or ".join(candidates)

    from .packet_models import Ambiguity as AmbiguityModel
    packet.add_ambiguity(AmbiguityModel(
        field_name="destination_candidates",
        ambiguity_type="unresolved_alternatives",
        raw_value=raw_value,
        confidence=0.8,
    ))

    # Emit telemetry for upstream extraction quality tracking
    emit_ambiguity_synthesis(
        field_name="destination_candidates",
        reason="multi_value_without_ambiguity",
        stage=packet.stage,
        candidates=candidates,
        packet_id=packet.packet_id,
    )

    ambiguities.append(AmbiguityRef(
        field_name="destination_candidates",
        ambiguity_type="unresolved_alternatives",
        raw_value=raw_value,
        severity="blocking",
    ))


# SECTION 13: MAIN ENTRY POINT
# =============================================================================

def run_gap_and_decision(
    packet: CanonicalPacket,
    feasibility_table: Optional[Dict[str, Any]] = None,
    _cached_feasibility: Optional[Dict[str, Any]] = None,
    agency_settings: Optional[AgencySettings] = None,
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

    # Value-structural ambiguity synthesis:
    # If destination_candidates has 2+ items but no unresolved_alternatives
    # ambiguity was flagged by NB01, synthesize one here. This handles packets
    # constructed from structured import or API calls that bypass extraction.
    _synthesize_destination_ambiguity(packet, ambiguities)

    # --- Phase 2: Budget feasibility (computed once, reused downstream) ---
    feasibility = _cached_feasibility if _cached_feasibility is not None else check_budget_feasibility(packet, feasibility_table, agency_settings=agency_settings)

    # --- Phase 2b: Budget decomposition ---
    budget_breakdown = decompose_budget(packet, cached_feasibility=feasibility, agency_settings=agency_settings)

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
    confidence_scorecard = calculate_confidence(packet, feasibility=feasibility)
    overall_confidence = confidence_scorecard.overall

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

                question_text = generate_question(blocker)
                if blocker == "destination_candidates":
                    dest_slot = resolve_field(packet, "destination_candidates")
                    if dest_slot and isinstance(dest_slot.value, list) and len(dest_slot.value) >= 2:
                        candidates = dest_slot.value[:3]
                        question_text = f"Between {' and '.join(candidates)}, which are you leaning toward?"
                        suggested = candidates
                    elif not suggested and dest_slot and isinstance(dest_slot.value, list) and len(dest_slot.value) == 1:
                        suggested = dest_slot.value

                elif blocker == "budget_min":
                    # Check for budget stretch ambiguity and generate appropriate question
                    budget_slot = resolve_field(packet, "budget_min")
                    budget_value = budget_slot.value if budget_slot and hasattr(budget_slot, 'value') else None
                    stretch_question = generate_budget_question(packet, budget_value)
                    if stretch_question != question_text:  # Only override if stretch detected
                        question_text = stretch_question

                follow_up_questions.append({
                    "field_name": blocker,
                    "question": question_text,
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
                    question_text = generate_question(amb.field_name)
                    suggested = []
                    if amb.field_name == "destination_candidates" and amb.ambiguity_type == "unresolved_alternatives":
                        dest_slot = resolve_field(packet, "destination_candidates")
                        if dest_slot and isinstance(dest_slot.value, list) and len(dest_slot.value) >= 2:
                            candidates = dest_slot.value[:3]
                            question_text = f"Between {' and '.join(candidates)}, which are you leaning toward?"
                            suggested = candidates
                    follow_up_questions.append({
                        "field_name": amb.field_name,
                        "question": question_text,
                        "priority": "critical",
                        "can_infer": False,
                        "inference_confidence": 0.0,
                        "suggested_values": suggested,
                    })
                decision_state = "ASK_FOLLOWUP"
            else:
                # Confidence below threshold but no blockers
                if overall_confidence < 0.6:
                    decision_state = "PROCEED_INTERNAL_DRAFT"
                else:
                    decision_state = "PROCEED_TRAVELER_SAFE"

    # --- Phase 10: Risk flags (reuse cached feasibility) ---
    risk_flags = generate_risk_flags(packet, stage, cached_feasibility=feasibility)

    # --- Phase 10b: SuitabilityProfile (structured output for frontend) ---
    suitability_profile = _build_suitability_profile(risk_flags)

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
        "confidence": round(overall_confidence, 3),
        "confidence_scorecard": {
            "data": confidence_scorecard.data_quality,
            "judgment": confidence_scorecard.judgment_confidence,
            "commercial": confidence_scorecard.commercial_confidence,
        },
        "feasibility": feasibility["status"],
        "operating_mode": mode,
        "commercial_decision": commercial_decision,
        "budget_verdict": budget_breakdown.verdict if budget_breakdown else None,
        "budget_total_low": budget_breakdown.total_estimated_low if budget_breakdown else None,
        "budget_total_high": budget_breakdown.total_estimated_high if budget_breakdown else None,
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
        confidence=confidence_scorecard,
        risk_flags=risk_flags,
        suitability_profile=suitability_profile,
        commercial_decision=commercial_decision,
        intent_scores=intent_scores,
        next_best_action=next_best_action,
        budget_breakdown=budget_breakdown,
    )
