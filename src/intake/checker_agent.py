"""
intake.checker_agent — Redundancy service for high-stakes autonomic decisions.
"""

from __future__ import annotations
import logging
from dataclasses import dataclass

from .packet_models import CanonicalPacket
from .decision import DecisionResult

logger = logging.getLogger("orchestration.checker")

@dataclass(slots=True)
class CheckerAuditResult:
    """Result of a secondary rule-heuristic audit.

    ``confidence_delta`` is the checker's advisory opinion (+0.05 when it
    agrees). It is RECORDED on the frontier result/rationale for the audit
    trail and deliberately never applied to any confidence value: a
    heuristic may not nudge a calibrated number (determinism audit
    2026-10-21, FND-0356 — parked pending a calibrated checker lane).
    """
    is_valid: bool
    requires_manual: bool
    reason: str
    confidence_delta: float = 0.0

class CheckerAgent:
    """
    Deterministic rule-heuristic checker that audits low-confidence
    decisions on the ghost-workflow path (ESCALATE_RECOVERY / emergency).

    This is NOT a model: it runs three fixed checks (budget blindness,
    high-stakes purpose keywords, low confidence without hard blockers).
    A model-backed second-opinion checker (different model family, CoT
    prompt) is the intended future lane; it must enter through the same
    ``audit()`` contract and carry its own provenance/calibration.
    """
    
    def audit(self, packet: CanonicalPacket, decision: DecisionResult) -> CheckerAuditResult:
        """
        Performs a second pass on the decision logic.
        """
        conf = decision.confidence.overall
        logger.info(f"Checker Agent auditing decision for {packet.packet_id} (Initial Confidence: {conf})")
        
        # Heuristic: Check for common failure patterns in low-confidence decisions
        # e.g., Missing budget info, complex multi-leg trips, or high-risk purposed trips.
        
        reasons = []
        requires_manual = False
        
        # 1. Budget Blindness Check
        if not packet.facts.get("budget_raw_text") and decision.decision_state != "ASK_FOLLOWUP":
            reasons.append("Missing budget data in non-followup state.")
            requires_manual = True
            
        # 2. Risk Purposed Audit
        purpose = str(packet.facts.get("trip_purpose", "")).lower()
        if any(word in purpose for word in ["medical", "repatriation", "legal", "urgent"]):
            reasons.append(f"High-stakes purpose detected: '{purpose}'")
            requires_manual = True
            
        # 3. Decision Rationale Verification
        # If the primary agent has 'low confidence' but didn't state a hard blocker, that's a red flag.
        if conf < 0.8 and not decision.hard_blockers:
            reasons.append("Low confidence without explicit hard blockers.")
            requires_manual = True
            
        if not reasons:
            return CheckerAuditResult(
                is_valid=True,
                requires_manual=False,
                reason="Checker pass: Logic appears consistent with packet data.",
                confidence_delta=0.05 # Checker adds a small boost if it agrees
            )
        else:
            reason_str = " | ".join(reasons)
            return CheckerAuditResult(
                is_valid=False,
                requires_manual=requires_manual,
                reason=f"Checker intervention: {reason_str}"
            )

# Singleton instance
checker_agent = CheckerAgent()
