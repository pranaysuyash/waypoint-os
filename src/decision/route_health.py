"""decision.route_health — decision-route health evaluation and alert emission.

Closes the routing_health phantom (ADR-008 item 6, Addendum 9): the alerting
pipeline (log_routing_health_alert → dedup/paging → legacy_ops triage) had
zero automatic producers, while the decision path recorded rich per-decision
telemetry in memory (src/decision/telemetry.py) that never reached it.

This module is the single seam between the two: after each hybrid-engine
decision, evaluate the rolling decision-route metrics against the existing
threshold vocabulary and emit a decision_route_health alert (deduped) when
thresholds trip. Renamed honestly from "routing_health": the metric measures
decision-EXECUTION route quality (rules/cache/llm/default), not model-router
health.
"""

from __future__ import annotations

import logging
from collections import deque
from typing import Any, Deque, Dict, Optional

logger = logging.getLogger("spine_api.decision.route_health")

# Rolling window: evaluate over the last N decisions; require a minimum
# sample size so single-decision noise never pages anyone.
_WINDOW_SIZE = 50
_MIN_SAMPLES = 10

# Thresholds mirror DEFAULT_ROUTING_HEALTH_THRESHOLDS (agentic_feedback)
# for the metrics this seam can compute from decision telemetry.
_FALLBACK_RATE_WARNING = 0.3
_FALLBACK_RATE_CRITICAL = 0.5
_ERROR_RATE_WARNING = 0.2
_ERROR_RATE_CRITICAL = 0.4

_recent: Deque[Dict[str, Any]] = deque(maxlen=_WINDOW_SIZE)


def _percent(numerator: int, total: int) -> float:
    return numerator / total if total else 0.0


def record_and_evaluate(
    decision_type: str,
    source: str,
    latency_ms: float,
    error: Optional[str] = None,
    trip_id: Optional[str] = None,
) -> None:
    """Record one decision outcome into the rolling window and emit a
    deduped decision_route_health alert when thresholds trip.

    Called from the hybrid decision path after telemetry.record_decision.
    Never raises: an alerting failure must not fail the decision.
    """
    try:
        _recent.append(
            {
                "decision_type": decision_type,
                "source": source,
                "latency_ms": latency_ms,
                "error": bool(error),
            }
        )
        if len(_recent) < _MIN_SAMPLES:
            return
        _evaluate(decision_type, trip_id)
    except Exception:  # pragma: no cover - alerting must never break decisions
        logger.exception("route_health evaluation failed; continuing")


def _evaluate(decision_type: str, trip_id: Optional[str]) -> None:
    total = len(_recent)
    default_fallbacks = sum(1 for m in _recent if m["source"] == "default")
    errors = sum(1 for m in _recent if m["error"])
    fallback_rate = _percent(default_fallbacks, total)
    error_rate = _percent(errors, total)

    status = "healthy"
    alerts: Dict[str, str] = {}
    if fallback_rate >= _FALLBACK_RATE_CRITICAL:
        status = "critical"
        alerts["default_fallback_rate"] = "critical"
    elif fallback_rate >= _FALLBACK_RATE_WARNING:
        status = "warning"
        alerts["default_fallback_rate"] = "warning"
    if error_rate >= _ERROR_RATE_CRITICAL:
        status = "critical"
        alerts["error_rate"] = "critical"
    elif error_rate >= _ERROR_RATE_WARNING and status != "critical":
        status = "warning"
        alerts["error_rate"] = "warning"

    if status == "healthy":
        return

    _emit_alert(
        trip_id=trip_id,
        status=status,
        alert_count=len(alerts),
        metrics={
            "default_fallback_rate": round(fallback_rate, 4),
            "error_rate": round(error_rate, 4),
            "window_size": total,
            "alerts": alerts,
            "decision_type": decision_type,
        },
    )


def _emit_alert(trip_id: Optional[str], status: str,
                alert_count: int, metrics: Dict[str, Any]) -> None:
    """Emit through the existing dedup/paging logger (alias keeps the old
    event consumers working during the rename cycle)."""
    from src.analytics.logger import TripEventLogger

    try:
        TripEventLogger.log_decision_route_health_alert(
            trip_id=trip_id or "unattributed-decision-route",
            routing_health={
                "status": status,
                "alert_count": alert_count,
            },
            authority={"source": "decision_path_telemetry"},
            metrics_snapshot=metrics,
        )
    except RuntimeError:
        # AuditStore unavailable (unit-test / early-boot context): log only.
        logger.warning(
            "decision_route_health %s: %s (audit store unavailable, not persisted)",
            status, metrics,
        )
