"""
intake — Agency-OS intake engine (NB01 v0.2, NB02 v0.2, NB03 v0.2).

Core modules:
- packet_models: CanonicalPacket, Slot, EvidenceRef, Ambiguity, OwnerConstraint, SubGroup
- normalizer: Normalizer with ambiguity detection, budget/date parsing
- extractors: ExtractionPipeline with pattern-based extraction
- validation: validate_packet + PacketValidationReport
- decision: NB02 v0.2 — Gap and decision engine (run_gap_and_decision)
- strategy: NB03 v0.2 — Session strategy and SEPARATE internal/traveler builders
- safety: NB03 v0.2 — Structural traveler-safe sanitization
"""

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
    higher_authority,
)
from .normalizer import Normalizer
from .extractors import ExtractionPipeline
from .validation import PacketValidationReport, validate_packet

__version__ = "0.4.0"

# NB02 v0.2
from .decision import (
    DecisionResult,
    AmbiguityRef,
    run_gap_and_decision,
    check_budget_feasibility,
    classify_ambiguity_severity,
)

# NB03 v0.2
from .strategy import (
    SessionStrategy,
    PromptBundle,
    QuestionWithIntent,
    build_session_strategy,
    build_traveler_safe_bundle,
    build_internal_bundle,
    build_session_strategy_and_bundle,
    determine_tone,
    get_tonal_guardrails,
    sort_questions_by_priority,
    get_mode_specific_goal,
    get_mode_specific_opening,
    get_branch_conversational_approach,
)
from .safety import (
    SanitizedPacketView,
    sanitize_for_traveler,
    check_no_leakage,
    validate_traveler_safe_output,
    has_blocking_ambiguities,
    is_field_traveler_safe,
    is_field_internal_only,
    audit_packet_internal_data,
    sanitize_text_output,
)
