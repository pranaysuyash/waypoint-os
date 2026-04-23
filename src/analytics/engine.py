from typing import Any, Dict, Optional
from src.analytics.models import AnalyticsPayload
from src.analytics.policy_rules import apply_owner_escalation_policy, compute_send_policy


def calculate_completeness_score(packet: Dict[str, Any]) -> float:
    score = 0.0
    if not packet:
        return 0.0

    metadata = packet.get("trip_metadata", {})
    if metadata.get("destination"):
        score += 25
    if metadata.get("primary_intent"):
        score += 20
    if metadata.get("date_window"):
        score += 15

    party = packet.get("party_profile", {})
    if party.get("size"):
        score += 15
    if party.get("composition_tags"):
        score += 10

    budget = packet.get("budget", {})
    if budget.get("value"):
        score += 15

    return min(100.0, score)


def calculate_feasibility_score(packet: Dict[str, Any], decision: Dict[str, Any]) -> float:
    # A mix of decision validity and rationale confidence
    if decision and decision.get("action") == "PROCEED":
        return 100.0
    elif decision and decision.get("action") == "CLARIFY":
        return 60.0
    elif decision and decision.get("action") == "BLOCK":
        return 20.0
    return 50.0  # Default unknown


def calculate_risk_score(decision: Dict[str, Any], safety: Dict[str, Any]) -> float:
    # 100 is "no risk", 0 is "extreme risk"
    score = 100.0
    
    if safety:
        if not safety.get("leakage_passed", True):
            score -= 50
        errors = safety.get("leakage_errors", [])
        score -= (len(errors) * 10)

    if decision:
        blockers = decision.get("blockers", [])
        score -= (len(blockers) * 15)

    return max(0.0, score)


def calculate_margin(packet: Dict[str, Any], decision: Dict[str, Any]) -> float:
    """Calculate base margin and adjustments (15-25% range + adjustments)."""
    base_margin = 18.0
    if not packet:
        return base_margin

    # Add margin for larger parties
    party = packet.get("party_profile", {})
    size = party.get("size", 1)
    if size >= 4:
        base_margin += 2.0
    if size >= 8:
        base_margin += 3.0

    # Destination-based premium (example)
    metadata = packet.get("trip_metadata", {})
    dest = str(metadata.get("destination", "")).lower()
    if any(x in dest for x in ["maldives", "switzerland", "bora bora", "safari"]):
        base_margin += 5.0
    
    # Complexity
    if packet.get("ambiguities", []):
        base_margin -= 1.0  # harder execution reduces realized margin target slightly

    return round(max(5.0, min(35.0, base_margin)), 1)


def calculate_profitability_score(margin: float) -> float:
    # 0 -> 100 mapping depending on margin. (10% = 50, 20% = 80, 25% = 100)
    if margin < 10:
        return max(0.0, margin * 5)
    elif margin >= 25:
        return 100.0
    else:
        # linear interpolate 10-25 to 50-100
        return 50.0 + ((margin - 10) / 15) * 50.0


def process_trip_analytics(trip: dict) -> AnalyticsPayload:
    """Entry point to calculate all analytics metrics for a single trip."""
    packet = trip.get("extracted", {})
    decision = trip.get("decision", {})
    safety = trip.get("safety", {})  # Assume safety check results might be saved

    margin_pct = calculate_margin(packet, decision)
    
    completeness = calculate_completeness_score(packet)
    feasibility = calculate_feasibility_score(packet, decision)
    risk = calculate_risk_score(decision, safety)
    profitability = calculate_profitability_score(margin_pct)

    overall = (completeness * 0.2 + feasibility * 0.3 + risk * 0.2 + profitability * 0.3)
    
    # Simple thresholds for review
    requires_review = False
    review_reason = None
    
    budget_val = packet.get("budget", {}).get("value", 0)
    if budget_val > 500000:
        requires_review = True
        review_reason = f"High value trip: {budget_val}"

    if margin_pct < 15:
        requires_review = True
        review_reason = f"Low margin detected ({margin_pct}%)"

    # Wave 10: Detection of critical feedback
    feedback = packet.get("feedback")
    feedback_reopen = False
    feedback_severity = None
    followup_needed = False
    recovery_status = None
    
    # Wave 11: SLA Tracking
    existing_analytics = trip.get("analytics") or {}
    recovery_started_at = existing_analytics.get("recovery_started_at")
    recovery_deadline = existing_analytics.get("recovery_deadline")
    is_escalated = existing_analytics.get("is_escalated", False)
    sla_status = existing_analytics.get("sla_status")

    if feedback and isinstance(feedback, dict):
        rating = feedback.get("rating")
        if rating and isinstance(rating, (int, float)) and rating <= 2:
            requires_review = True
            review_reason = f"Critical Negative Feedback ({rating}/5)"
            feedback_reopen = True
            feedback_severity = "critical" if rating == 1 else "high"
            followup_needed = True
            recovery_status = existing_analytics.get("recovery_status") or "PENDING_NOTIFY"
            
            # Wave 11: Initialize SLA if not already set
            if not recovery_deadline:
                from datetime import datetime, timedelta, timezone
                now = datetime.now(timezone.utc)
                hours = 2 if rating == 1 else 6
                recovery_deadline = (now + timedelta(hours=hours)).isoformat()
                sla_status = "on_track"

    revision_count = 0
    if isinstance(existing_analytics, dict):
        try:
            revision_count = int(existing_analytics.get("revision_count") or 0)
        except (TypeError, ValueError):
            revision_count = 0

    payload = AnalyticsPayload(
        margin_pct=round(margin_pct, 1),
        quality_score=round(overall, 1),
        quality_breakdown={
            "completeness": round(completeness, 1),
            "feasibility": round(feasibility, 1),
            "risk": round(risk, 1),
            "profitability": round(profitability, 1),
        },
        requires_review=requires_review,
        review_reason=review_reason,
        feedback_reopen=feedback_reopen,
        feedback_severity=feedback_severity,
        followup_needed=followup_needed,
        recovery_status=recovery_status,
        recovery_started_at=recovery_started_at,
        recovery_deadline=recovery_deadline,
        is_escalated=is_escalated,
        sla_status=sla_status,
        revision_count=revision_count,
    )

    # Apply owner-escalation policy for onboarding/review operations.
    escalated = apply_owner_escalation_policy(trip, payload.model_dump())
    payload = AnalyticsPayload(**escalated)

    # Compute customer-send policy (stored as guidance for FE/BE flow checks).
    send_policy = compute_send_policy(
        {
            "decision": decision,
            "analytics": payload.model_dump(),
        },
        role="junior_agent",
    )
    payload.approval_required_for_send = bool(send_policy["owner_approval_required"])
    payload.send_policy_reason = str(send_policy["reason"])

    return payload
