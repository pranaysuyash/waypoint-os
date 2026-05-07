"""
intake.risk_action_policy — stage-aware action policy for structured risks.
"""

from __future__ import annotations

from typing import Any


def build_risk_action_plan(stage: str, structured_risks: list[dict[str, Any]]) -> dict[str, Any]:
    current_stage = (stage or "").lower()
    high_or_critical = [r for r in structured_risks if str(r.get("severity")) in {"high", "critical"}]
    medium = [r for r in structured_risks if str(r.get("severity")) == "medium"]

    actions: list[str] = []
    mode = "monitor"

    if current_stage in {"in_progress", "traveling"}:
        if high_or_critical:
            mode = "incident_response"
            actions.append("Trigger immediate human operations review.")
            actions.append("Send internal disruption brief with alternate route/activity options.")
        elif medium:
            mode = "active_watch"
            actions.append("Increase monitoring cadence and prepare contingency options.")
    else:
        if high_or_critical:
            mode = "pre_commit_block"
            actions.append("Block confirmation until hard-risk mitigations are acknowledged.")
            actions.append("Require explicit operator sign-off for risk acceptance.")
        elif medium:
            mode = "pre_commit_review"
            actions.append("Include mitigation assumptions in proposal and obtain operator review.")

    return {
        "mode": mode,
        "actions": actions,
        "high_or_critical_count": len(high_or_critical),
        "medium_count": len(medium),
    }

