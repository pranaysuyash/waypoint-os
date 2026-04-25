"""
intake.frontier_orchestrator — Advanced agentic orchestration for Waypoint OS.

This module integrates 'Frontier' features:
1. Ghost Concierge (Autonomic Workflows)
2. Emotional State Monitoring (Sentiment Analysis)
3. Intelligence Pool Integration (Federated Risks)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import logging

from .packet_models import CanonicalPacket
from .decision import DecisionResult
from .federated_intelligence import intelligence_service
from .negotiation_engine import negotiation_service
from .checker_agent import checker_agent
from .specialty_knowledge import SpecialtyKnowledgeService

logger = logging.getLogger("orchestration.frontier")

@dataclass
class FrontierOrchestrationResult:
    """Result of the frontier orchestration pass."""
    ghost_triggered: bool = False
    ghost_workflow_id: Optional[str] = None
    sentiment_score: float = 0.5
    anxiety_alert: bool = False
    intelligence_hits: List[Dict[str, Any]] = field(default_factory=list)
    specialty_knowledge: List[Any] = field(default_factory=list)
    mitigation_applied: bool = False
    requires_manual_audit: bool = False  # Checker-Agent Redundancy
    audit_reason: Optional[str] = None
    negotiation_active: bool = False
    negotiation_logs: List[Dict[str, Any]] = field(default_factory=list)
    
def run_frontier_orchestration(
    packet: CanonicalPacket,
    decision: DecisionResult,
    agency_settings: Any = None
) -> FrontierOrchestrationResult:
    """
    Analyzes the current packet and decision to trigger advanced agentic workflows.
    """
    result = FrontierOrchestrationResult()
    
    # 1. Emotional State Monitoring
    # In a real system, this would call an LLM-based sentiment analyzer
    # Here we use a heuristic based on packet clues (e.g., urgency, question count)
    result.sentiment_score = _calculate_sentiment_heuristic(packet)
    if result.sentiment_score < 0.3:
        result.anxiety_alert = True
        logger.warning(f"CRITICAL: High anxiety detected for trip {packet.packet_id}")
    
    # 2. Ghost Concierge Trigger
    # Triggered if decision state is ESCALATE_RECOVERY or manual emergency
    if decision.commercial_decision == "ESCALATE_RECOVERY" or packet.operating_mode == "emergency":
        result.ghost_triggered = True
        result.ghost_workflow_id = f"ghost_{packet.packet_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        logger.info(f"Ghost Concierge triggered for recovery: {result.ghost_workflow_id}")
        
        # --- Checker-Agent Redundancy Logic ---
        threshold = agency_settings.autonomy.checker_audit_threshold if agency_settings else 0.9
        if decision.confidence.overall < threshold:
            audit_result = checker_agent.audit(packet, decision)
            result.requires_manual_audit = audit_result.requires_manual
            result.audit_reason = audit_result.reason

            if audit_result.requires_manual:
                logger.warning(f"AUDIT REQUIRED: Checker Agent flagged Ghost Workflow {result.ghost_workflow_id}: {audit_result.reason}")
            else:
                logger.info(f"Checker Agent verified Ghost Workflow {result.ghost_workflow_id}: {audit_result.reason}")

    # 3. Intelligence Pool Lookup
    dest = str(packet.facts.get("destination_candidates", "")) or str(packet.facts.get("resolved_destination", ""))
    if dest:
        hits = intelligence_service.query_risks(dest)
        for hit in hits:
            result.intelligence_hits.append(hit)
            logger.info(f"Intelligence Pool hit for {dest}: {hit.get('type')}")

    # 4. Specialty Knowledge Detection
    # Combine raw note, trip purpose, and destination for broader detection
    analysis_text = " ".join([
        packet.raw_note or "",
        str(packet.facts.get("trip_purpose", "")),
        str(packet.facts.get("destination_candidates", "")),
        str(packet.facts.get("resolved_destination", ""))
    ])
    specialty_hits = SpecialtyKnowledgeService.identify_niche(analysis_text)
    if specialty_hits:
        result.specialty_knowledge = specialty_hits
        for hit in specialty_hits:
            logger.info(f"Specialty Knowledge hit: {hit.niche}")
            # Dynamic Urgency Escalation: If a niche hit is CRITICAL, escalate manual audit
            if hit.urgency == "CRITICAL":
                result.requires_manual_audit = True
                result.audit_reason = f"Critical Specialty Niche detected: {hit.niche}"

    # 5. Agentic Negotiation Engine
    # Only trigger if Ghost is enabled or for high-value groups
    negotiation_logs = negotiation_service.analyze_and_trigger(packet, decision)
    if negotiation_logs:
        result.negotiation_active = True
        result.negotiation_logs = negotiation_logs

    return result

def _calculate_sentiment_heuristic(packet: CanonicalPacket) -> float:
    """Simulates sentiment analysis from packet data."""
    raw_text = str(packet.facts.get("budget_raw_text", "")) + " " + str(packet.facts.get("trip_purpose", ""))
    
    stress_keywords = ["urgent", "ASAP", "problem", "wrong", "delay", "failed", "money"]
    calm_keywords = ["looking forward", "excited", "flexible", "relaxed", "happy"]
    
    score = 0.5
    for word in stress_keywords:
        if word.lower() in raw_text.lower():
            score -= 0.05
    for word in calm_keywords:
        if word.lower() in raw_text.lower():
            score += 0.05
            
    return max(0.1, min(0.9, score))
