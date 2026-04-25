"""
intake.checker_agent — Redundancy service for high-stakes autonomic decisions.
"""

from __future__ import annotations
import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional

from .packet_models import CanonicalPacket
from .decision import DecisionResult

logger = logging.getLogger("orchestration.checker")

@dataclass
class CheckerAuditResult:
    """Result of a secondary agent audit."""
    is_valid: bool
    requires_manual: bool
    reason: str
    confidence_delta: float = 0.0

class CheckerAgent:
    """
    Simulates a 'Checker' agent that audits decisions when confidence is low.
    In a production system, this would call a different LLM model (e.g. Claude 3.5 -> GPT-4o)
    or use a more rigorous chain-of-thought prompt.
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
