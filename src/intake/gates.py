"""
intake.gates — Quality gates for the agentic pipeline.

Formalizes the transition requirements between pipeline stages:
NB01 (Extraction) → NB02 (Judgment) → NB03 (Strategy/Output)

D1 Architecture:
- NB01CompletionGate: structural validation (unchanged)
- NB02JudgmentGate: autonomy policy gate — reads DecisionResult, produces AutonomyOutcome
  WITHOUT mutating DecisionResult.decision_state
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from .packet_models import CanonicalPacket
    from .validation import PacketValidationReport
    from .decision import DecisionResult
    from .config.agency_settings import AgencySettings


class GateVerdict(Enum):
    """Possible outcomes of a quality gate check."""
    PROCEED = "proceed"   # Quality meets threshold, continue to next stage
    RETRY = "retry"       # Minor issues, can be fixed by re-running previous stage
    ESCALATE = "escalate" # Major issues, requires human intervention (STOP_NEEDS_REVIEW)
    DEGRADE = "degrade"   # Issues detected, but can proceed in a limited/safe mode


@dataclass(slots=True)
class GateResult:
    """The result of a single quality gate evaluation."""
    verdict: GateVerdict
    score: float
    reasons: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# D1 Autonomy Outcome — first-class separation of policy from judgment
# =============================================================================

@dataclass(slots=True)
class AutonomyOutcome:
    """
    The result of applying the agency autonomy policy to an NB02 verdict.

    This object preserves the RAW NB02 decision_state and separately records
    what the agency autonomy policy allows.  Downstream consumers (API, UI, D2,
    D5) consume both fields independently.

    Three-layer model (from D1 ADR):
      1. Judgment layer    → decision.decision_state (raw NB02 verdict)
      2. Policy layer      → autonomy_outcome.effective_action
      3. Human action layer → future override / approval events
    """
    raw_verdict: str                    # What NB02 originally decided
    effective_action: str               # "auto" | "review" | "block"
    approval_required: bool             # True for "review" or "block"
    rule_source: str                    # Which rule produced this outcome
    safety_invariant_applied: bool      # True if STOP_NEEDS_REVIEW → forced block
    mode_override_applied: Optional[str] = None
    warning_override_applied: bool = False
    reasons: List[str] = field(default_factory=list)

    @property
    def is_auto(self) -> bool:
        return self.effective_action == "auto"

    @property
    def is_review(self) -> bool:
        return self.effective_action == "review"

    @property
    def is_blocked(self) -> bool:
        return self.effective_action == "block"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "raw_verdict": self.raw_verdict,
            "effective_action": self.effective_action,
            "approval_required": self.approval_required,
            "rule_source": self.rule_source,
            "safety_invariant_applied": self.safety_invariant_applied,
            "mode_override_applied": self.mode_override_applied,
            "warning_override_applied": self.warning_override_applied,
            "reasons": self.reasons,
        }


class PipelineGate(Protocol):
    """Protocol for a quality gate that evaluates pipeline state."""
    def evaluate(self, **kwargs) -> GateResult:
        ...


class NB01CompletionGate:
    """
    Gate between NB01 (Extraction) and NB02 (Judgment).
    Checks structural validity and MVB completeness.

    Verdicts:
    - PROCEED: All structural checks pass AND full QUOTE_READY fields present
    - DEGRADE: Structural checks pass (INTAKE_MINIMUM met) but QUOTE_READY fields
      are incomplete — trip can be saved but quote generation is blocked
    - ESCALATE: Structural checks failed or INTAKE_MINIMUM not met — cannot save
    """
    def evaluate(
        self,
        packet: CanonicalPacket,
        validation: PacketValidationReport
    ) -> GateResult:
        reasons: List[str] = []

        # 1. Structural validity
        if not validation.is_valid:
            reasons.append(f"Structural validation failed ({validation.error_count} errors)")
            return GateResult(verdict=GateVerdict.ESCALATE, score=0.0, reasons=reasons)

        # 2. Check for QUOTE_READY_INCOMPLETE warnings — these are warnings that
        #    indicate the trip can be saved but not quoted
        has_incomplete_warnings = any(
            w.code == "QUOTE_READY_INCOMPLETE" for w in validation.warnings
        )
        if has_incomplete_warnings:
            completeness_score = 0.5
            reasons.append("Intake minimum met — trip can be saved for later enrichment")
            reasons.append("Quote-ready fields are incomplete — quote generation blocked")
            return GateResult(
                verdict=GateVerdict.DEGRADE,
                score=completeness_score,
                reasons=reasons,
            )

        # 3. Data density (simple heuristic)
        density = len(packet.facts) / 10.0

        return GateResult(
            verdict=GateVerdict.PROCEED,
            score=min(1.0, density),
            reasons=["Structural validation passed", f"Data density: {density:.2f}"]
        )


class NB02JudgmentGate:
    """
    Gate between NB02 (Judgment) and NB03 (Strategy).

    D1 Architecture:
    - Reads the raw NB02 verdict (decision.decision_state)
    - Looks up the agency autonomy policy
    - Computes effective_action WITHOUT mutating decision.decision_state
    - Returns an AutonomyOutcome for downstream delivery/approval logic
    """
    def evaluate(
        self,
        decision: DecisionResult,
        agency_settings: AgencySettings,
    ) -> AutonomyOutcome:
        policy = agency_settings.autonomy
        try:
            raw_verdict = decision.decision_state or "unknown"
            operating_mode = decision.operating_mode
            risk_flags = decision.risk_flags
        except AttributeError:
            raw_verdict = "unknown"
            operating_mode = "normal_intake"
            risk_flags = []

        reasons: List[str] = []
        mode_override = None
        safety_invariant = False
        warning_override = False

        # 1. Base gate from policy
        effective_action = policy.effective_gate(raw_verdict, operating_mode)

        # 2. Check if a mode override was applied
        if operating_mode in policy.mode_overrides:
            overrides = policy.mode_overrides[operating_mode]
            if raw_verdict in overrides:
                mode_override = operating_mode
                reasons.append(
                    f"Mode override ({operating_mode}): {raw_verdict} → {effective_action}"
                )
        else:
            reasons.append(
                f"Mode '{operating_mode}' has no override; using base gate for {raw_verdict}"
            )

        # 3. Safety invariant — STOP_NEEDS_REVIEW must always block
        if raw_verdict == "STOP_NEEDS_REVIEW":
            effective_action = "block"
            safety_invariant = True
            # Ensure reason is present
            safety_reason = "STOP_NEEDS_REVIEW safety invariant (always block)"
            if safety_reason not in reasons:
                reasons.append(safety_reason)

        # 4. Warning override: if auto_proceed_with_warnings is False and
        #    risk flags exist, downgrade auto → review
        if not policy.auto_proceed_with_warnings and risk_flags:
            if effective_action == "auto":
                effective_action = "review"
                warning_override = True
                reasons.append(
                    "Risk flags present with auto_proceed_with_warnings=False"
                )

        # 5. Approval required for review or block
        approval_required = effective_action in ("review", "block")

        # 6. Determine rule_source for D5 telemetry / traceability
        if safety_invariant:
            rule_source = "safety_invariant"
        elif mode_override:
            rule_source = f"mode_override:{mode_override}"
        elif warning_override:
            rule_source = "warning_policy"
        else:
            rule_source = f"approval_gates:{raw_verdict}"

        # Catch-all reason if nothing else set
        if not reasons:
            reasons.append(f"Default gate for {raw_verdict}: {effective_action}")

        return AutonomyOutcome(
            raw_verdict=raw_verdict,
            effective_action=effective_action,
            approval_required=approval_required,
            rule_source=rule_source,
            safety_invariant_applied=safety_invariant,
            mode_override_applied=mode_override,
            warning_override_applied=warning_override,
            reasons=reasons,
        )
