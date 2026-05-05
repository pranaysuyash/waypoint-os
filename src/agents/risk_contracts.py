"""
agents.risk_contracts — shared structured risk payload helpers.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def to_structured_risk(
    *,
    flag: str,
    severity: str,
    category: str,
    message: str,
    details: dict[str, Any] | None = None,
    detected_by: str = "agent_runtime",
) -> dict[str, Any]:
    normalized_severity = severity if severity in {"low", "medium", "high", "critical"} else "medium"
    normalized_category = category if category in {
        "budget", "document", "weather", "routing", "activity", "composition", "visa", "timing", "safety", "flight_disruption"
    } else "routing"
    return {
        "flag": flag,
        "severity": normalized_severity,
        "category": normalized_category,
        "message": message,
        "details": details or {},
        "detected_at": datetime.now(timezone.utc).isoformat(),
        "detected_by": detected_by,
    }


def feasibility_constraint_to_structured(constraint: dict[str, Any], detected_by: str) -> dict[str, Any]:
    category = str(constraint.get("category") or "routing")
    severity = "high" if str(constraint.get("severity") or "").lower() == "hard" else "medium"
    flag = f"{category}_risk"
    return to_structured_risk(
        flag=flag,
        severity=severity,
        category=category,
        message=str(constraint.get("message") or ""),
        details={"recommendation": constraint.get("recommendation"), "metadata": constraint.get("metadata")},
        detected_by=detected_by,
    )

