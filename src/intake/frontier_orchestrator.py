"""
intake.frontier_orchestrator — Advanced agentic orchestration for Waypoint OS.

This module integrates 'Frontier' features:
1. Ghost Concierge (Autonomic Workflows)
2. Emotional State Monitoring (Sentiment Analysis)
3. Intelligence Pool Integration (Federated Risks)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import logging
import uuid

from .packet_models import CanonicalPacket
from .decision import DecisionResult
from .federated_intelligence import intelligence_service
from .negotiation_engine import negotiation_service
from .checker_agent import checker_agent
from .specialty_knowledge import SpecialtyKnowledgeService

logger = logging.getLogger("orchestration.frontier")

ANXIETY_ALERT_THRESHOLD = 0.3
DEFAULT_CHECKER_AUDIT_THRESHOLD = 0.9


@dataclass(slots=True)
class FrontierOrchestrationResult:
    """Result of the frontier orchestration pass."""
    ghost_triggered: bool = False
    ghost_workflow_id: Optional[str] = None
    sentiment_score: float = 0.5
    anxiety_alert: bool = False
    intelligence_hits: List[Dict[str, Any]] = field(default_factory=list)
    specialty_knowledge: List[Any] = field(default_factory=list)
    requires_manual_audit: bool = False
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
    All frontier subsystems are best-effort: failures are logged but do not
    break the orchestration pass.
    """
    result = FrontierOrchestrationResult()

    # 1. Emotional State Monitoring
    # In a real system, this would call an LLM-based sentiment analyzer.
    # Current heuristic is advisory only — do not use for production decisions.
    result.sentiment_score = _calculate_sentiment_heuristic(packet)
    if result.sentiment_score < ANXIETY_ALERT_THRESHOLD:
        result.anxiety_alert = True
        logger.warning("High anxiety heuristic triggered for packet %s", packet.packet_id)

    # 2. Ghost Concierge Trigger
    # Triggered if decision state is ESCALATE_RECOVERY or manual emergency
    commercial_decision = str(decision.commercial_decision).upper()
    operating_mode = str(packet.operating_mode).lower()
    if commercial_decision == "ESCALATE_RECOVERY" or operating_mode == "emergency":
        result.ghost_triggered = True
        result.ghost_workflow_id = f"ghost_{packet.packet_id}_{uuid.uuid4().hex[:12]}"
        logger.info("Ghost Concierge triggered: %s", result.ghost_workflow_id)

        # --- Checker-Agent Redundancy Logic ---
        threshold = _resolve_checker_threshold(agency_settings)
        overall_confidence = _resolve_overall_confidence(decision)
        if overall_confidence is None or overall_confidence < threshold:
            try:
                audit_result = checker_agent.audit(packet, decision)
                result.requires_manual_audit = audit_result.requires_manual
                result.audit_reason = audit_result.reason
                if audit_result.requires_manual:
                    logger.warning(
                        "AUDIT REQUIRED: Checker flagged Ghost Workflow %s: %s",
                        result.ghost_workflow_id, audit_result.reason,
                    )
                else:
                    logger.info(
                        "Checker Agent verified Ghost Workflow %s: %s",
                        result.ghost_workflow_id, audit_result.reason,
                    )
            except Exception:
                logger.exception("Checker Agent audit failed for packet %s", packet.packet_id)
                result.requires_manual_audit = True
                result.audit_reason = "Checker Agent audit failed — defaulting to manual review"

    # 3. Intelligence Pool Lookup
    dest = _extract_destination(packet)
    if dest:
        try:
            hits = intelligence_service.query_risks(dest)
            result.intelligence_hits = list(hits)
            logger.info(
                "Intelligence Pool returned %d hits for packet %s",
                len(result.intelligence_hits), packet.packet_id,
            )
        except Exception:
            logger.exception("Intelligence Pool lookup failed for packet %s", packet.packet_id)

    # 4. Specialty Knowledge Detection
    analysis_text = " ".join([
        packet.raw_note or "",
        str(packet.facts.get("trip_purpose", "")),
        str(packet.facts.get("destination_candidates", "")),
        str(packet.facts.get("resolved_destination", "")),
    ])
    try:
        specialty_hits = SpecialtyKnowledgeService.identify_niche(analysis_text)
        if specialty_hits:
            result.specialty_knowledge = specialty_hits
            logger.info(
                "Specialty Knowledge returned %d hits for packet %s",
                len(specialty_hits), packet.packet_id,
            )
            for hit in specialty_hits:
                urgency = getattr(hit, "urgency", None)
                logger.debug("Specialty Knowledge hit for packet %s", packet.packet_id)
                if urgency == "CRITICAL":
                    result.requires_manual_audit = True
                    result.audit_reason = "Critical Specialty Niche detected"
    except Exception:
        logger.exception("Specialty Knowledge detection failed for packet %s", packet.packet_id)

    # 5. Agentic Negotiation Engine
    try:
        negotiation_logs = negotiation_service.analyze_and_trigger(packet, decision)
        if negotiation_logs:
            result.negotiation_active = True
            result.negotiation_logs = list(negotiation_logs)
    except Exception:
        logger.exception("Negotiation engine failed for packet %s", packet.packet_id)

    return result


def _resolve_checker_threshold(agency_settings: Any) -> float:
    """Extract and clamp checker audit threshold from agency settings."""
    threshold = DEFAULT_CHECKER_AUDIT_THRESHOLD
    if agency_settings is not None:
        autonomy = getattr(agency_settings, "autonomy", None)
        if autonomy is not None:
            raw = getattr(autonomy, "checker_audit_threshold", None)
            if raw is not None:
                try:
                    threshold = float(raw)
                except (TypeError, ValueError):
                    logger.warning(
                        "Invalid checker_audit_threshold value %r, using default %s",
                        raw, threshold,
                    )
    return max(0.0, min(1.0, threshold))


def _resolve_overall_confidence(decision: DecisionResult) -> Optional[float]:
    """Extract and clamp overall confidence from decision result."""
    raw = getattr(getattr(decision, "confidence", None), "overall", None)
    if raw is None:
        return None
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    return max(0.0, min(1.0, value))


def _extract_destination(packet: CanonicalPacket) -> Optional[str]:
    """Extract a usable destination string from packet facts."""
    resolved = packet.facts.get("resolved_destination")
    if isinstance(resolved, str) and resolved.strip():
        return resolved.strip()

    candidates = packet.facts.get("destination_candidates")
    if isinstance(candidates, str) and candidates.strip():
        return candidates.strip()

    if isinstance(candidates, list):
        for candidate in candidates:
            if isinstance(candidate, str) and candidate.strip():
                return candidate.strip()
            if isinstance(candidate, dict):
                name = (
                    candidate.get("name")
                    or candidate.get("destination")
                    or candidate.get("city")
                )
                if isinstance(name, str) and name.strip():
                    return name.strip()

    return None


def _calculate_sentiment_heuristic(packet: CanonicalPacket) -> float:
    """Simulates sentiment analysis from packet data.

    This is an advisory heuristic only. Do not use for production decisions.
    """
    raw_text = " ".join([
        packet.raw_note or "",
        str(packet.facts.get("budget_raw_text", "")),
        str(packet.facts.get("trip_purpose", "")),
    ])
    normalized = raw_text.casefold()

    stress_keywords = ["urgent", "asap", "problem", "wrong", "delay", "failed", "money"]
    calm_keywords = ["looking forward", "excited", "flexible", "relaxed", "happy"]

    score = 0.5
    for word in stress_keywords:
        if word in normalized:
            score -= 0.05
    for word in calm_keywords:
        if word in normalized:
            score += 0.05

    return max(0.1, min(0.9, score))
