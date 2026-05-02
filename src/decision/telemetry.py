"""
decision.telemetry — Metrics and observability for hybrid decision engine.

Tracks decision metrics, cache performance, and LLM usage for production monitoring.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from collections import defaultdict
import threading

from .cache_schema import CacheStats


@dataclass(slots=True)
class DecisionMetrics:
    """Metrics for a single decision."""
    decision_type: str
    source: str  # "cache", "rule", "llm", "default"
    latency_ms: float
    timestamp: datetime
    cache_hit: bool = False
    llm_used: bool = False
    error: Optional[str] = None
    cost_inr: float = 0.0


@dataclass(slots=True)
class TelemetrySnapshot:
    """Snapshot of telemetry data for export."""
    snapshot_time: datetime
    window_duration_seconds: int

    # Counters
    total_decisions: int
    decisions_by_type: Dict[str, int]
    decisions_by_source: Dict[str, int]

    # Rates
    cache_hit_rate: float
    rule_hit_rate: float
    llm_call_rate: float
    default_fallback_rate: float

    # Performance
    avg_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float

    # Cost
    total_cost_inr: float
    cost_per_decision: float

    # Errors
    error_count: int
    error_rate: float

    # Cache stats
    cache_entries: int
    cache_hit_rate_overall: float


class DecisionTelemetry:
    """
    Telemetry collector for hybrid decision engine.

    Thread-safe singleton that tracks all decisions and provides
    metrics for monitoring systems (Prometheus, statsd, etc.).
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self._metrics: List[DecisionMetrics] = []
        self._start_time = datetime.now()
        self._metrics_lock = threading.Lock()
        self._max_metrics = 10000  # Rotate after this many

        # Per-decision-type counters
        self._decision_counts: Dict[str, int] = defaultdict(int)
        self._source_counts: Dict[str, int] = defaultdict(int)
        self._error_counts: Dict[str, int] = defaultdict(int)

    def record_decision(
        self,
        decision_type: str,
        source: str,
        latency_ms: float,
        cache_hit: bool = False,
        llm_used: bool = False,
        error: Optional[str] = None,
        cost_inr: float = 0.0,
    ) -> None:
        """Record a decision metric."""
        metric = DecisionMetrics(
            decision_type=decision_type,
            source=source,
            latency_ms=latency_ms,
            timestamp=datetime.now(),
            cache_hit=cache_hit,
            llm_used=llm_used,
            error=error,
            cost_inr=cost_inr,
        )

        with self._metrics_lock:
            self._metrics.append(metric)
            self._decision_counts[decision_type] += 1
            self._source_counts[source] += 1

            if error:
                self._error_counts[error] += 1

            # Rotate metrics if too many
            if len(self._metrics) > self._max_metrics:
                self._metrics = self._metrics[-self._max_metrics:]

    def get_snapshot(
        self,
        window_seconds: int = 300,  # 5 minutes default
    ) -> TelemetrySnapshot:
        """
        Get a snapshot of metrics for the given time window.

        Args:
            window_seconds: Time window in seconds (default: 300 = 5 minutes)

        Returns:
            TelemetrySnapshot with current metrics
        """
        cutoff_time = datetime.now() - timedelta(seconds=window_seconds)

        with self._metrics_lock:
            window_metrics = [
                m for m in self._metrics
                if m.timestamp >= cutoff_time
            ]

        if not window_metrics:
            return self._empty_snapshot(window_seconds)

        # Calculate stats
        total = len(window_metrics)
        by_type = defaultdict(int)
        by_source = defaultdict(int)
        latencies = []
        costs = []
        errors = 0

        for m in window_metrics:
            by_type[m.decision_type] += 1
            by_source[m.source] += 1
            latencies.append(m.latency_ms)
            costs.append(m.cost_inr)
            if m.error:
                errors += 1

        # Sort latencies for percentiles
        latencies.sort()

        return TelemetrySnapshot(
            snapshot_time=datetime.now(),
            window_duration_seconds=window_seconds,
            total_decisions=total,
            decisions_by_type=dict(by_type),
            decisions_by_source=dict(by_source),
            cache_hit_rate=by_source.get("cache", 0) / total,
            rule_hit_rate=by_source.get("rule", 0) / total,
            llm_call_rate=by_source.get("llm", 0) / total,
            default_fallback_rate=by_source.get("default", 0) / total,
            avg_latency_ms=sum(latencies) / len(latencies),
            p50_latency_ms=latencies[len(latencies) // 2],
            p95_latency_ms=latencies[int(len(latencies) * 0.95)] if len(latencies) >= 20 else latencies[-1],
            p99_latency_ms=latencies[int(len(latencies) * 0.99)] if len(latencies) >= 100 else latencies[-1],
            total_cost_inr=sum(costs),
            cost_per_decision=sum(costs) / len(costs) if costs else 0,
            error_count=errors,
            error_rate=errors / total,
            cache_entries=0,  # Will be filled by engine
            cache_hit_rate_overall=by_source.get("cache", 0) / total,
        )

    def _empty_snapshot(self, window_seconds: int) -> TelemetrySnapshot:
        """Return empty snapshot when no metrics available."""
        return TelemetrySnapshot(
            snapshot_time=datetime.now(),
            window_duration_seconds=window_seconds,
            total_decisions=0,
            decisions_by_type={},
            decisions_by_source={},
            cache_hit_rate=0.0,
            rule_hit_rate=0.0,
            llm_call_rate=0.0,
            default_fallback_rate=0.0,
            avg_latency_ms=0.0,
            p50_latency_ms=0.0,
            p95_latency_ms=0.0,
            p99_latency_ms=0.0,
            total_cost_inr=0.0,
            cost_per_decision=0.0,
            error_count=0,
            error_rate=0.0,
            cache_entries=0,
            cache_hit_rate_overall=0.0,
        )

    def export_prometheus(self, snapshot: TelemetrySnapshot) -> str:
        """
        Export metrics in Prometheus text format.

        Returns:
            String in Prometheus exposition format
        """
        lines = [
            f"# HELP hybrid_decision_total Total number of decisions",
            f"# TYPE hybrid_decision_total counter",
            f"hybrid_decision_total {snapshot.total_decisions}",
            "",
            f"# HELP hybrid_decision_cache_hit_rate Cache hit rate (0-1)",
            f"# TYPE hybrid_decision_cache_hit_rate gauge",
            f"hybrid_decision_cache_hit_rate {snapshot.cache_hit_rate:.4f}",
            "",
            f"# HELP hybrid_decision_rule_hit_rate Rule hit rate (0-1)",
            f"# TYPE hybrid_decision_rule_hit_rate gauge",
            f"hybrid_decision_rule_hit_rate {snapshot.rule_hit_rate:.4f}",
            "",
            f"# HELP hybrid_decision_llm_call_rate LLM call rate (0-1)",
            f"# TYPE hybrid_decision_llm_call_rate gauge",
            f"hybrid_decision_llm_call_rate {snapshot.llm_call_rate:.4f}",
            "",
            f"# HELP hybrid_decision_latency_ms Decision latency in milliseconds",
            f"# TYPE hybrid_decision_latency_ms gauge",
            f"hybrid_decision_latency_ms {{quantile=\"0.5\"}} {snapshot.p50_latency_ms:.2f}",
            f"hybrid_decision_latency_ms {{quantile=\"0.95\"}} {snapshot.p95_latency_ms:.2f}",
            f"hybrid_decision_latency_ms {{quantile=\"0.99\"}} {snapshot.p99_latency_ms:.2f}",
            f"hybrid_decision_latency_ms {{quantile=\"avg\"}} {snapshot.avg_latency_ms:.2f}",
            "",
            f"# HELP hybrid_decision_cost_inr_total Total cost in INR",
            f"# TYPE hybrid_decision_cost_inr_total counter",
            f"hybrid_decision_cost_inr_total {snapshot.total_cost_inr:.2f}",
            "",
            f"# HELP hybrid_decision_error_rate Error rate (0-1)",
            f"# TYPE hybrid_decision_error_rate gauge",
            f"hybrid_decision_error_rate {snapshot.error_rate:.4f}",
        ]

        # Per-decision-type metrics
        for decision_type, count in snapshot.decisions_by_type.items():
            safe_name = decision_type.replace("_", "_")
            lines.append(f"hybrid_decision_by_type{{type=\"{safe_name}\"}} {count}")

        return "\n".join(lines)

    def export_statsd(self, snapshot: TelemetrySnapshot) -> List[str]:
        """
        Export metrics in statsd format.

        Returns:
            List of statsd-formatted strings
        """
        metrics = [
            f"hybrid_decision.total:{snapshot.total_decisions}|c",
            f"hybrid_decision.cache_hit_rate:{snapshot.cache_hit_rate:.4f}|g",
            f"hybrid_decision.rule_hit_rate:{snapshot.rule_hit_rate:.4f}|g",
            f"hybrid_decision.llm_call_rate:{snapshot.llm_call_rate:.4f}|g",
            f"hybrid_decision.latency.avg:{snapshot.avg_latency_ms:.2f}|ms",
            f"hybrid_decision.latency.p95:{snapshot.p95_latency_ms:.2f}|ms",
            f"hybrid_decision.cost.inr:{snapshot.total_cost_inr:.2f}|c",
            f"hybrid_decision.error_rate:{snapshot.error_rate:.4f}|g",
        ]

        return metrics

    def reset(self) -> None:
        """Clear all metrics (useful for testing)."""
        with self._metrics_lock:
            self._metrics.clear()
            self._decision_counts.clear()
            self._source_counts.clear()
            self._error_counts.clear()


# Global singleton
_global_telemetry: Optional[DecisionTelemetry] = None


def get_telemetry() -> DecisionTelemetry:
    """Get the global telemetry instance."""
    global _global_telemetry
    if _global_telemetry is None:
        _global_telemetry = DecisionTelemetry()
    return _global_telemetry
