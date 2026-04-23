"""
suitability.integration — Integration point for suitability scoring in the decision pipeline.

This module provides functions to extract participant information from packets
and generate suitability-based risk flags for intake orchestration.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .models import ParticipantRef, SuitabilityContext
from .scoring import evaluate_activity
from .catalog import get_activity, STATIC_ACTIVITIES


def extract_participants_from_packet(packet) -> List[ParticipantRef]:
    """
    Extract participant information from a CanonicalPacket.
    
    Returns a list of ParticipantRef objects for suitability scoring.
    """
    participants = []
    
    # Extract party composition
    party_comp = packet.facts.get("party_composition")
    if not party_comp or not isinstance(party_comp.value, dict):
        return participants
    
    composition = party_comp.value
    
    # Handle adults
    adults = composition.get("adults", 0)
    if isinstance(adults, int) and adults > 0:
        for i in range(adults):
            participants.append(ParticipantRef(
                kind="person",
                ref_id=f"adult_{i+1}",
                label="adult",
                age=None,  # Age not specified for adults
            ))
    
    # Handle elderly
    elderly = composition.get("elderly", 0)
    if isinstance(elderly, int) and elderly > 0:
        for i in range(elderly):
            participants.append(ParticipantRef(
                kind="person",
                ref_id=f"elderly_{i+1}",
                label="elderly",
                age=None,  # Age not specified, but label is elderly
            ))
    
    # Handle children with ages
    child_ages = packet.facts.get("child_ages")
    if child_ages and isinstance(child_ages.value, list):
        for i, age in enumerate(child_ages.value):
            if isinstance(age, (int, float)):
                label = "toddler" if age < 5 else "child"
                participants.append(ParticipantRef(
                    kind="person",
                    ref_id=f"child_{i+1}",
                    label=label,
                    age=int(age),
                ))
    
    return participants


def evaluate_itinerary_coherence(
    activities: List[ActivityDefinition],
    participants: List[ParticipantRef],
    context: SuitabilityContext,
) -> List[Dict[str, Any]]:
    """
    Tier 2 coherence check for an itinerary.
    
    Checks for sequence-based risks like activity overload for specific cohorts.
    """
    coherence_risks = []
    
    # 1. Elderly Overload Check
    elderly_participants = [p for p in participants if p.label == "elderly"]
    if elderly_participants:
        high_intensity_count = sum(1 for a in activities if a.intensity in ["high", "extreme"])
        if high_intensity_count >= 2:
            coherence_risks.append({
                "flag": "suitability_overload_elderly",
                "severity": "medium",
                "message": f"Potential overload: {high_intensity_count} high-intensity activities in one day for elderly travelers.",
                "category": "pacing",
                "details": {
                    "high_intensity_count": high_intensity_count,
                    "affected_cohort": "elderly",
                },
                "maturity": "heuristic",
            })

    # 2. Toddler Pacing Check
    toddler_participants = [p for p in participants if p.label == "toddler"]
    if toddler_participants:
        if len(activities) > 3:
            coherence_risks.append({
                "flag": "suitability_pacing_toddler",
                "severity": "medium",
                "message": f"High density: {len(activities)} activities in one day may exceed toddler stamina.",
                "category": "pacing",
                "details": {
                    "activity_count": len(activities),
                    "affected_cohort": "toddler",
                },
                "maturity": "heuristic",
            })

    return coherence_risks


def generate_suitability_risks(
    packet,
    activity_ids: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Generate suitability-based risk flags for activities.
    
    Args:
        packet: CanonicalPacket with traveler information
        activity_ids: Optional list of specific activity IDs to check.
                     If None, checks all activities in the static catalog.
    
    Returns:
        List of risk flag dictionaries suitable for DecisionResult.risk_flags
    """
    risks = []
    
    # Extract participants from packet
    participants = extract_participants_from_packet(packet)
    if not participants:
        return risks
    
    # Determine which activities to check
    if activity_ids:
        activities = [get_activity(aid) for aid in activity_ids if get_activity(aid)]
    else:
        # For now, check a subset of common activities
        activities = STATIC_ACTIVITIES[:5]
    
    # Create suitability context
    destination = packet.facts.get("destination_candidates")
    destination_keys = []
    if destination and isinstance(destination.value, list):
        destination_keys = destination.value
    elif destination and isinstance(destination.value, str):
        destination_keys = [destination.value]
    
    # Extract budget preference
    budget_pref_slot = packet.facts.get("budget_preference")
    budget_preference = budget_pref_slot.value if budget_pref_slot else None
    
    context = SuitabilityContext(
        destination_keys=destination_keys,
        budget_preference=budget_preference,
        day_activities=activities,
    )
    
    # Tier 1: Score each activity for each participant
    for activity in activities:
        for participant in participants:
            result = evaluate_activity(activity, participant, context)
            
            # Convert suitability result to risk flag if there are issues
            if result.tier == "exclude":
                risks.append({
                    "flag": f"suitability_exclusion_{activity.activity_id}",
                    "severity": "high",
                    "message": f"{participant.label.title()} participant excluded from {activity.canonical_name}: {'; '.join(result.hard_exclusion_reasons)}",
                    "category": "activity",
                    "details": {
                        "activity_id": activity.activity_id,
                        "participant_ref": participant.ref_id,
                        "participant_label": participant.label,
                        "hard_exclusion_reasons": result.hard_exclusion_reasons,
                        "score": result.score,
                        "confidence": result.confidence,
                    },
                    "maturity": "heuristic",
                })
            elif result.tier == "discourage":
                risks.append({
                    "flag": f"suitability_discouraged_{activity.activity_id}",
                    "severity": "medium",
                    "message": f"{participant.label.title()} participant discouraged from {activity.canonical_name}: {'; '.join(result.warnings)}",
                    "category": "activity",
                    "details": {
                        "activity_id": activity.activity_id,
                        "participant_ref": participant.ref_id,
                        "participant_label": participant.label,
                        "warnings": result.warnings,
                        "score": result.score,
                        "confidence": result.confidence,
                    },
                    "maturity": "heuristic",
                })
    
    # Tier 2: Check itinerary coherence
    coherence_risks = evaluate_itinerary_coherence(activities, participants, context)
    risks.extend(coherence_risks)
    
    return risks


def assess_activity_suitability(packet) -> List[Any]:
    """
    Main integration entry point: assess suitability for a packet at intake end.
    
    This function:
    1. Extracts participants from the packet
    2. Runs Tier 1 (deterministic age/intensity combos)
    3. Runs Tier 2 (context rules: composition, pacing)
    4. Returns a list of SuitabilityFlag objects
    
    The calling code in orchestration.py will:
    - Attach flags to packet.suitability_flags
    - Check for CRITICAL flags and set decision_state to "suitability_review_required"
    
    Args:
        packet: CanonicalPacket with traveler information
        
    Returns:
        List of SuitabilityFlag objects (may be empty if no concerns)
    """
    from src.intake.packet_models import SuitabilityFlag
    
    flags: List[Any] = []
    
    # Extract participants from packet
    participants = extract_participants_from_packet(packet)
    if not participants:
        return flags
    
    # Determine destination context
    destination = packet.facts.get("destination_candidates")
    destination_keys = []
    if destination and isinstance(destination.value, list):
        destination_keys = destination.value
    elif destination and isinstance(destination.value, str):
        destination_keys = [destination.value]
    
    # Extract budget preference
    budget_pref_slot = packet.facts.get("budget_preference")
    budget_preference = budget_pref_slot.value if budget_pref_slot else None
    
    # Create suitability context
    context = SuitabilityContext(
        destination_keys=destination_keys,
        budget_preference=budget_preference,
        day_activities=[],
    )
    
    # Tier 1: Score each activity for each participant
    for activity in STATIC_ACTIVITIES[:10]:  # Core activities only
        for participant in participants:
            result = evaluate_activity(activity, participant, context)
            
            # Map tier to severity for flags
            tier_to_severity = {
                "exclude": "critical",
                "discourage": "high",
                "neutral": "low",
                "recommend": "low",
                "strong_recommend": "low",
            }
            
            # Create flags only for exclude and discourage tiers
            if result.tier in ["exclude", "discourage"]:
                severity = tier_to_severity[result.tier]
                reason = "; ".join(result.hard_exclusion_reasons or result.warnings)
                
                flag = SuitabilityFlag(
                    flag_type=f"suitability_{result.tier}_{activity.activity_id}",
                    severity=severity,
                    reason=reason,
                    confidence=result.confidence,
                    details={
                        "activity_id": activity.activity_id,
                        "activity_name": activity.canonical_name,
                        "participant_ref": participant.ref_id,
                        "participant_label": participant.label,
                        "score": result.score,
                        "tier": result.tier,
                    },
                    affected_travelers=[participant.ref_id],
                )
                flags.append(flag)
    
    # Tier 2: Check itinerary coherence
    coherence_risks = evaluate_itinerary_coherence(STATIC_ACTIVITIES[:10], participants, context)
    for risk in coherence_risks:
        severity_map = {
            "low": "low",
            "medium": "high",
            "high": "high",
            "critical": "critical",
        }
        flag = SuitabilityFlag(
            flag_type=risk.get("flag", "suitability_coherence"),
            severity=severity_map.get(risk.get("severity", "low"), "low"),
            reason=risk.get("message", ""),
            confidence=0.8,
            details=risk.get("details", {}),
            affected_travelers=risk.get("affected_travelers", []),
        )
        flags.append(flag)
    
    return flags
