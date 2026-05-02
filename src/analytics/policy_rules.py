from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional


CRITICAL_DECISION_STATES = {"STOP_NEEDS_REVIEW"}


def _extract_overall_confidence(decision: Dict[str, Any]) -> Optional[float]:
    confidence = decision.get("confidence")
    if isinstance(confidence, (int, float)):
        return float(confidence)
    if isinstance(confidence, dict):
        overall = confidence.get("overall")
        if isinstance(overall, (int, float)):
            return float(overall)
    return None


def _critical_flags(decision: Dict[str, Any]) -> List[Dict[str, Any]]:
    flags = decision.get("suitability_flags") or []
    if not isinstance(flags, list):
        return []
    return [
        f for f in flags
        if isinstance(f, dict) and str(f.get("severity", "")).lower() == "critical"
    ]


def _flag_key(flag: Dict[str, Any]) -> str:
    return str(flag.get("flag") or flag.get("flag_type") or "").strip()


def _is_flag_resolved_by_override(
    flag: Dict[str, Any],
    overrides_by_flag: Optional[Dict[str, List[Dict[str, Any]]]] = None,
) -> bool:
    key = _flag_key(flag)
    if not key or not overrides_by_flag:
        return False
    entries = overrides_by_flag.get(key, [])
    if not entries:
        return False

    for ov in entries:
        action = str(ov.get("action", "")).lower()
        if action in {"acknowledge", "suppress"}:
            return True
        if action == "downgrade":
            new_sev = str(ov.get("new_severity", "")).lower()
            if new_sev and new_sev != "critical":
                return True
    return False


def ready_gate_failures(
    trip: Dict[str, Any],
    overrides_by_flag: Optional[Dict[str, List[Dict[str, Any]]]] = None,
) -> List[str]:
    """
    Ready gate for P1 flow.
    Returns a list of user-facing failure reasons; empty list means pass.
    """
    failures: List[str] = []

    raw_input = trip.get("raw_input") or {}
    customer_message = raw_input.get("raw_note") or trip.get("customerMessage") or trip.get("customer_message")
    if not isinstance(customer_message, str) or not customer_message.strip():
        failures.append("Customer message is missing.")

    decision = trip.get("decision") or {}
    decision_state = str(decision.get("decision_state") or "").strip()
    if decision_state in {"ASK_FOLLOWUP", "STOP_NEEDS_REVIEW"}:
        failures.append(f"Decision state '{decision_state}' is not ready.")

    traveler_bundle = trip.get("traveler_bundle")
    if traveler_bundle is None:
        failures.append("Traveler-safe output is missing.")

    unresolved_critical = []
    for flag in _critical_flags(decision):
        if not _is_flag_resolved_by_override(flag, overrides_by_flag):
            unresolved_critical.append(_flag_key(flag) or "critical_flag")
    if unresolved_critical:
        failures.append(
            "Critical suitability flags unresolved: " + ", ".join(unresolved_critical)
        )

    analytics = trip.get("analytics") or {}
    if analytics.get("requires_review") is True and analytics.get("review_status") != "approved":
        failures.append("Owner approval is required before marking ready.")

    return failures


def apply_owner_escalation_policy(
    trip: Dict[str, Any],
    analytics: Dict[str, Any],
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    """
    P2 escalation policy:
    - Critical suitability unresolved -> owner review + 2h SLA
    - STOP_NEEDS_REVIEW -> owner review + 2h SLA
    - margin < 8% -> owner review + 6h SLA
    - revision_count >= 2 -> owner review + 6h SLA
    """
    out = dict(analytics)
    decision = trip.get("decision") or {}
    decision_state = str(decision.get("decision_state") or "")
    critical_flags = _critical_flags(decision)
    revision_count = int(out.get("revision_count") or 0)
    margin = out.get("margin_pct")

    reasons: List[str] = []
    severity = "high"
    hours = 6

    if decision_state in CRITICAL_DECISION_STATES:
        reasons.append(f"Decision state {decision_state} requires owner review")
        severity = "critical"
        hours = 2

    if critical_flags:
        reasons.append("Critical suitability flags present")
        severity = "critical"
        hours = 2

    try:
        if margin is not None and float(margin) < 8.0:
            reasons.append(f"Margin below owner threshold ({float(margin):.1f}%)")
            if severity != "critical":
                severity = "high"
                hours = 6
    except (TypeError, ValueError):
        pass

    if revision_count >= 2:
        reasons.append("Repeated revisions (>=2) require owner escalation")
        if severity != "critical":
            severity = "high"
            hours = 6

    if not reasons:
        return out

    ts = now or datetime.now(timezone.utc)
    out["requires_review"] = True
    out["is_escalated"] = True
    out["review_status"] = "escalated"
    out["escalation_severity"] = severity
    out["owner_review_deadline"] = (ts + timedelta(hours=hours)).isoformat()
    out["review_reason"] = "; ".join(reasons)
    out["sla_status"] = out.get("sla_status") or "on_track"
    return out


def compute_send_policy(
    trip: Dict[str, Any],
    *,
    confidence_threshold: float = 0.75,
    role: str = "junior_agent",
) -> Dict[str, Any]:
    """
    Junior-send policy for P2:
    - require owner approval for low confidence, critical flags, or review-required states.
    """
    decision = trip.get("decision") or {}
    analytics = trip.get("analytics") or {}
    decision_state = str(decision.get("decision_state") or "")
    confidence = _extract_overall_confidence(decision)
    critical_flags_present = len(_critical_flags(decision)) > 0

    reasons: List[str] = []
    owner_approval_required = False

    if role == "junior_agent":
        if analytics.get("requires_review") is True:
            owner_approval_required = True
            reasons.append("Trip is in review-required state")
        if decision_state in CRITICAL_DECISION_STATES:
            owner_approval_required = True
            reasons.append(f"Decision state {decision_state}")
        if critical_flags_present:
            owner_approval_required = True
            reasons.append("Critical suitability flag present")
        if confidence is None or confidence < confidence_threshold:
            owner_approval_required = True
            reasons.append(
                f"Confidence below threshold ({confidence_threshold:.2f})"
                if confidence is not None
                else "Confidence unavailable"
            )

    return {
        "role": role,
        "owner_approval_required": owner_approval_required,
        "send_allowed": not owner_approval_required,
        "reason": "; ".join(reasons) if reasons else "Eligible for direct send",
        "confidence": confidence,
        "confidence_threshold": confidence_threshold,
    }

