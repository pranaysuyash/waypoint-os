"""
SLA service — deadline computation for routing states.

Three SLA types track elapsed time for operational accountability:
  ownership_sla  — time since trip was assigned (primary_assignee set)
  escalation_sla — time since trip was escalated (escalated_at set)
  total_sla      — time since routing record was created

Each SLA has thresholds:
  on_track  — under warning threshold
  at_risk   — between warning and breach
  breached  — over breach threshold

Thresholds are in hours and can be overridden at call time or via agency
settings (future). Defaults are conservative for a travel agency context
where same-day response is expected.
"""

from datetime import datetime, timezone
from typing import Optional

_DEFAULT_OWNERSHIP_WARN_HRS = 4
_DEFAULT_OWNERSHIP_BREACH_HRS = 24

_DEFAULT_ESCALATION_WARN_HRS = 2
_DEFAULT_ESCALATION_BREACH_HRS = 8


def _hours_since(ts: Optional[datetime]) -> Optional[float]:
    if ts is None:
        return None
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    delta = datetime.now(timezone.utc) - ts
    return delta.total_seconds() / 3600


def _classify(
    hours: Optional[float],
    warn_hrs: float,
    breach_hrs: float,
) -> str:
    if hours is None:
        return "not_started"
    if hours >= breach_hrs:
        return "breached"
    if hours >= warn_hrs:
        return "at_risk"
    return "on_track"


def compute_sla(
    routing_state: dict,
    ownership_warn_hrs: float = _DEFAULT_OWNERSHIP_WARN_HRS,
    ownership_breach_hrs: float = _DEFAULT_OWNERSHIP_BREACH_HRS,
    escalation_warn_hrs: float = _DEFAULT_ESCALATION_WARN_HRS,
    escalation_breach_hrs: float = _DEFAULT_ESCALATION_BREACH_HRS,
) -> dict:
    """
    Compute SLA status for a routing state dict (as returned by routing_service._to_dict).

    Returns:
      {
        "ownership": { "status": "on_track|at_risk|breached|not_started", "hours_elapsed": float|null },
        "escalation": { "status": ..., "hours_elapsed": float|null },
        "worst": "on_track|at_risk|breached|not_started"
      }
    """
    assigned_at_raw = routing_state.get("assigned_at")
    assigned_at: Optional[datetime] = None
    if assigned_at_raw:
        try:
            assigned_at = datetime.fromisoformat(assigned_at_raw)
        except (ValueError, TypeError):
            pass

    escalated_at_raw = routing_state.get("escalated_at")
    escalated_at: Optional[datetime] = None
    if escalated_at_raw:
        try:
            escalated_at = datetime.fromisoformat(escalated_at_raw)
        except (ValueError, TypeError):
            pass

    ownership_hrs = _hours_since(assigned_at)
    escalation_hrs = _hours_since(escalated_at)

    ownership_status = _classify(ownership_hrs, ownership_warn_hrs, ownership_breach_hrs)
    escalation_status = _classify(escalation_hrs, escalation_warn_hrs, escalation_breach_hrs)

    severity_rank = {"breached": 3, "at_risk": 2, "on_track": 1, "not_started": 0}
    worst_status = max(ownership_status, escalation_status, key=lambda s: severity_rank.get(s, 0))

    return {
        "ownership": {
            "status": ownership_status,
            "hours_elapsed": round(ownership_hrs, 2) if ownership_hrs is not None else None,
            "warn_threshold_hrs": ownership_warn_hrs,
            "breach_threshold_hrs": ownership_breach_hrs,
        },
        "escalation": {
            "status": escalation_status,
            "hours_elapsed": round(escalation_hrs, 2) if escalation_hrs is not None else None,
            "warn_threshold_hrs": escalation_warn_hrs,
            "breach_threshold_hrs": escalation_breach_hrs,
        },
        "worst": worst_status,
    }
