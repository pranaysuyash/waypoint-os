"""
intake.gates — Quality gates for the agentic pipeline.

Formalizes the transition requirements between pipeline stages:
NB01 (Extraction) → NB02 (Judgment) → NB03 (Strategy/Output)
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


@dataclass
class GateResult:
    """The result of a single quality gate evaluation."""
    verdict: GateVerdict
    score: float
    reasons: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class PipelineGate(Protocol):
    """Protocol for a quality gate that evaluates pipeline state."""
    def evaluate(self, **kwargs) -> GateResult:
        ...


class NB01CompletionGate:
    """
    Gate between NB01 (Extraction) and NB02 (Judgment).
    Checks structural validity and MVB completeness.
    """
    def evaluate(
        self, 
        packet: CanonicalPacket, 
        validation: PacketValidationReport
    ) -> GateResult:
        reasons = []
        
        # 1. Structural validity
        if not validation.is_valid:
            reasons.append(f"Structural validation failed ({validation.error_count} errors)")
            return GateResult(verdict=GateVerdict.ESCALATE, score=0.0, reasons=reasons)

        # 2. MVB completeness
        # Already checked by validation, but we can add specific logic here if needed
        
        # 3. Data density (simple heuristic)
        density = len(packet.facts) / 10.0 # simple baseline
        
        return GateResult(
            verdict=GateVerdict.PROCEED,
            score=min(1.0, density),
            reasons=["Structural validation passed", f"Data density: {density:.2f}"]
        )


class NB02JudgmentGate:
    """
    Gate between NB02 (Judgment) and NB03 (Strategy).
    Checks confidence scorecard against agency autonomy policy.
    """
    def evaluate(
        self, 
        decision: DecisionResult, 
        agency_settings: AgencySettings
    ) -> GateResult:
        policy = agency_settings.autonomy
        scorecard = decision.confidence
        reasons = []

        # 1. Check for hard blockers
        if decision.hard_blockers:
            reasons.append(f"Hard blockers present: {', '.join(decision.hard_blockers)}")
            return GateResult(verdict=GateVerdict.DEGRADE, score=0.0, reasons=reasons)

        # 2. Check proceed threshold
        if scorecard.overall >= policy.min_proceed_confidence:
            return GateResult(
                verdict=GateVerdict.PROCEED,
                score=scorecard.overall,
                reasons=["Confidence exceeds proceed threshold"]
            )

        # 3. Check draft threshold
        if scorecard.overall >= policy.min_draft_confidence:
            return GateResult(
                verdict=GateVerdict.DEGRADE,
                score=scorecard.overall,
                reasons=["Confidence below proceed threshold, but allows internal draft"]
            )

        # 4. Otherwise escalate
        reasons.append(f"Confidence score {scorecard.overall:.2f} below minimum policy threshold")
        return GateResult(verdict=GateVerdict.ESCALATE, score=scorecard.overall, reasons=reasons)
