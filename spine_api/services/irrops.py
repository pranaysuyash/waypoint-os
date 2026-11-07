"""IRROPS signal ingestion (R2-H tranche, 2026-11-04).

Deterministic evaluation of operator-reported disruptions against the closed
trigger taxonomy in Docs/architecture/IRROPS_SEMANTICS_2026-11-04.md. The
output shape feeds the existing disruption radar surface
(``trip["active_disruption"]``), which renders stored alerts with the F-38
honesty rule — nothing is fabricated on an empty state.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

TRIGGER_KINDS = frozenset(
    {"cancellation", "delay", "schedule_change", "diversion", "denial_of_boarding"}
)

# EU261/UK261 compensation-relevance threshold (Art.6): 3 hours at arrival.
COMP_RELEVANT_DELAY_MINUTES = 180


class IrropsReportError(ValueError):
    """Raised for malformed reports — the router maps it to 422."""


def evaluate_irrops_report(
    trip: Dict[str, Any],
    *,
    trigger_kind: str,
    flight_ref: str,
    notes: str = "",
    delay_minutes: Optional[int] = None,
    operator_id: str = "",
    now_iso: Optional[str] = None,
) -> Dict[str, Any]:
    """Build the active_disruption payload for one operator-reported signal.

    Deterministic severity; honest operator_reported source; idempotency
    marker (trip + flight + trigger + report hour) so a duplicate report in
    the same window is detectable by callers."""
    kind = (trigger_kind or "").strip().lower()
    if kind not in TRIGGER_KINDS:
        raise IrropsReportError(
            f"Unknown trigger kind '{trigger_kind}' — expected one of {sorted(TRIGGER_KINDS)}"
        )
    flight = (flight_ref or "").strip()
    if not flight:
        raise IrropsReportError("flight_ref is required for a disruption report")

    stage = str(trip.get("stage") or "")
    if stage in {"closed", "cancelled", "completed", "archived", "lost"}:
        raise IrropsReportError(f"Trip stage '{stage}' is terminal; disruption cannot be reported")

    delay = int(delay_minutes) if delay_minutes is not None else None
    if delay is not None and delay < 0:
        raise IrropsReportError("delay_minutes must be >= 0")
    if kind == "delay" and delay is None:
        raise IrropsReportError("delay reports need delay_minutes")

    severity = _severity(kind, delay)
    comp_relevant = bool(delay is not None and delay >= COMP_RELEVANT_DELAY_MINUTES)

    now = now_iso or datetime.now(timezone.utc).isoformat()
    report_hour = now[:13]  # idempotency window: same trip+flight+trigger+hour
    return {
        "trigger_kind": kind,
        "flight_ref": flight,
        "severity": severity,
        "comp_relevant": comp_relevant,
        "delay_minutes": delay,
        "notes": (notes or "")[:500],
        "source": "operator_reported",
        "source_basis": (
            "operator-reported disruption; deterministic severity per "
            "IRROPS_SEMANTICS_2026-11-04.md §1 — provider feeds (DP-04a) "
            "will supersede with provider_observed rows"
        ),
        "reported_by": operator_id,
        "idempotency_marker": f"irrops:{trip.get('id')}:{flight}:{kind}:{report_hour}",
        "created_at": now,
    }


def _severity(kind: str, delay_minutes: Optional[int]) -> str:
    if kind in ("cancellation", "denial_of_boarding"):
        return "critical"
    if kind == "diversion":
        return "high"
    if kind == "schedule_change":
        if delay_minutes is not None and delay_minutes >= COMP_RELEVANT_DELAY_MINUTES:
            return "high"
        return "medium"
    # delay
    if delay_minutes is None:
        return "unknown"
    if delay_minutes >= COMP_RELEVANT_DELAY_MINUTES:
        return "critical"
    if delay_minutes >= 60:
        return "high"
    return "medium"
