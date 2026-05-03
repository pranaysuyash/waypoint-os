"""
intake.constants — Canonical type definitions shared across NB01-NB03.

All modules that reference decision_state must import from here.
No local redefinitions of DECISION_STATES permitted.

Pipeline identity model (three-layer):
  1. Internal stage code (NB01-NB06)  — kept as historical/debug identifiers
  2. Semantic stage/gate keys         — used in API contracts, logs, FE lookup
  3. User-facing labels               — FE-only, never emitted from backend
"""

from __future__ import annotations

from enum import Enum
from typing import Literal, cast


# =============================================================================
# Pipeline Stage + Gate Identifiers (semantic contract layer)
# =============================================================================

class PipelineStage(str, Enum):
    """Semantic identifiers for pipeline stages — used in API contracts.

    These are the canonical replacement for legacy NB01-NB06 codes in
    API payloads, log messages, and frontend type definitions.
    NB class names (NB01CompletionGate, etc.) and test filenames remain unchanged.
    """
    INTAKE_EXTRACTION = "intake_extraction"
    DECISION_JUDGMENT = "decision_judgment"
    SESSION_STRATEGY = "session_strategy"
    TRAVELER_PROPOSAL = "traveler_proposal"
    GOLDEN_PATH_EVALUATION = "golden_path_evaluation"
    SHADOW_REPLAY = "shadow_replay"


class GateIdentifier(str, Enum):
    """Semantic identifiers for quality gates — used in API contracts."""
    INTAKE_COMPLETION = "intake_completion"
    DECISION_READINESS = "decision_readiness"
    STRATEGY_SAFETY = "strategy_safety"
    PROPOSAL_QUALITY = "proposal_quality"
    DEMO_REGRESSION = "demo_regression"
    SHADOW_QUALITY = "shadow_quality"


# Legacy NB code → semantic stage key (degradation-only, for reading old payloads)
_LEGACY_NB_TO_STAGE: dict[str, PipelineStage] = {
    "NB01": PipelineStage.INTAKE_EXTRACTION,
    "NB02": PipelineStage.DECISION_JUDGMENT,
    "NB03": PipelineStage.SESSION_STRATEGY,
    "NB04": PipelineStage.TRAVELER_PROPOSAL,
    "NB05": PipelineStage.GOLDEN_PATH_EVALUATION,
    "NB06": PipelineStage.SHADOW_REPLAY,
}

# Legacy NB code → semantic gate key
_LEGACY_NB_TO_GATE: dict[str, GateIdentifier] = {
    "NB01": GateIdentifier.INTAKE_COMPLETION,
    "NB02": GateIdentifier.DECISION_READINESS,
    "NB03": GateIdentifier.STRATEGY_SAFETY,
    "NB04": GateIdentifier.PROPOSAL_QUALITY,
    "NB05": GateIdentifier.DEMO_REGRESSION,
    "NB06": GateIdentifier.SHADOW_QUALITY,
}


def resolve_stage(raw_gate: str | None) -> PipelineStage | None:
    """Resolve a gate string (legacy NB01 or semantic intake_completion) to a PipelineStage."""
    if not raw_gate:
        return None
    if raw_gate in _LEGACY_NB_TO_STAGE:
        return _LEGACY_NB_TO_STAGE[raw_gate]
    try:
        return PipelineStage(raw_gate)
    except ValueError:
        return None


def resolve_gate(raw_gate: str | None) -> GateIdentifier | None:
    """Resolve a gate string (legacy NB01 or semantic intake_completion) to a GateIdentifier."""
    if not raw_gate:
        return None
    if raw_gate in _LEGACY_NB_TO_GATE:
        return _LEGACY_NB_TO_GATE[raw_gate]
    try:
        return GateIdentifier(raw_gate)
    except ValueError:
        return None

DecisionState = Literal[
    "ASK_FOLLOWUP",
    "PROCEED_INTERNAL_DRAFT",
    "PROCEED_TRAVELER_SAFE",
    "BRANCH_OPTIONS",
    "STOP_NEEDS_REVIEW",
]

DECISION_STATES: tuple[str, ...] = (
    "ASK_FOLLOWUP",
    "PROCEED_INTERNAL_DRAFT",
    "PROCEED_TRAVELER_SAFE",
    "BRANCH_OPTIONS",
    "STOP_NEEDS_REVIEW",
)

DECISION_STATES_FROZENSET = frozenset(DECISION_STATES)


def assert_valid_decision_state(value: str) -> DecisionState:
    if value not in DECISION_STATES_FROZENSET:
        raise ValueError(
            f"Invalid decision_state={value!r}. Expected one of {DECISION_STATES}"
        )
    return cast(DecisionState, value)
