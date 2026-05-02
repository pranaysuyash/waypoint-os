"""
decision.health — Health checks and circuit breaker for hybrid decision engine.

Provides health status, circuit breaker for LLM failures, and graceful degradation.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
import threading

from .telemetry import get_telemetry, TelemetrySnapshot


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # LLM failing, circuit open
    HALF_OPEN = "half_open"  # Testing if LLM recovered


@dataclass(slots=True)
class HealthStatus:
    """Health status of the hybrid decision engine."""
    healthy: bool
    status: str  # "healthy", "degraded", "unhealthy"
    timestamp: datetime

    # Component status
    cache_healthy: bool = True
    rules_healthy: bool = True
    llm_healthy: bool = True
    llm_available: bool = False

    # Circuit breaker status
    circuit_state: str = "closed"
    llm_failure_count: int = 0
    llm_last_failure: Optional[datetime] = None

    # Metrics snapshot
    metrics: Optional[TelemetrySnapshot] = None

    # Issues detected
    issues: List[str] = field(default_factory=list)


class CircuitBreaker:
    """
    Circuit breaker for LLM calls.

    Opens after consecutive failures, closes after successful recovery test.
    Prevents cascading failures and wasted API calls.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        timeout_seconds: int = 60,
        half_open_max_calls: int = 3,
    ):
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Consecutive failures before opening circuit
            timeout_seconds: Seconds to wait before attempting recovery
            half_open_max_calls: Max LLM calls in half-open state
        """
        self._failure_threshold = failure_threshold
        self._timeout_seconds = timeout_seconds
        self._half_open_max_calls = half_open_max_calls

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time: Optional[datetime] = None
        self._half_open_calls = 0
        self._lock = threading.Lock()

    def record_success(self) -> None:
        """Record a successful LLM call."""
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._half_open_calls += 1
                # After successful calls in half-open, close circuit
                if self._half_open_calls >= self._half_open_max_calls:
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
                    self._half_open_calls = 0
            elif self._state == CircuitState.OPEN:
                # Shouldn't happen, but reset if we get success in open state
                self._state = CircuitState.CLOSED
                self._failure_count = 0

    def record_failure(self) -> None:
        """Record a failed LLM call."""
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = datetime.now()

            if self._failure_count >= self._failure_threshold:
                self._state = CircuitState.OPEN

    def can_attempt(self) -> bool:
        """
        Check if LLM call can be attempted.

        Returns:
            True if circuit is closed or half-open (and can try)
        """
        with self._lock:
            if self._state == CircuitState.CLOSED:
                return True

            if self._state == CircuitState.OPEN:
                # Check if timeout has passed
                if self._last_failure_time:
                    elapsed = (datetime.now() - self._last_failure_time).total_seconds()
                    if elapsed >= self._timeout_seconds:
                        self._state = CircuitState.HALF_OPEN
                        self._half_open_calls = 0
                        return True
                return False

            if self._state == CircuitState.HALF_OPEN:
                return self._half_open_calls < self._half_open_max_calls

            return False

    def get_state(self) -> CircuitState:
        """Get current circuit state."""
        with self._lock:
            return self._state

    def reset(self) -> None:
        """Reset circuit breaker to closed state."""
        with self._lock:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._last_failure_time = None
            self._half_open_calls = 0


class HybridEngineHealth:
    """
    Health checker for hybrid decision engine.

    Monitors cache, rules, and LLM components for production readiness.
    """

    def __init__(
        self,
        circuit_breaker: Optional[CircuitBreaker] = None,
    ):
        """
        Initialize health checker.

        Args:
            circuit_breaker: Circuit breaker instance (creates default if None)
        """
        self._circuit_breaker = circuit_breaker or CircuitBreaker()
        self._lock = threading.Lock()
        self._llm_available = False
        self._llm_last_check: Optional[datetime] = None

    def check_llm_available(self) -> bool:
        """
        Check if LLM is available.

        Returns:
            True if LLM can be called
        """
        # Check circuit breaker first
        if not self._circuit_breaker.can_attempt():
            self._llm_available = False
            return False

        # TODO: Add actual LLM ping/health check
        # For now, assume available if circuit allows
        self._llm_available = True
        self._llm_last_check = datetime.now()
        return True

    def record_llm_success(self) -> None:
        """Record successful LLM call."""
        self._circuit_breaker.record_success()
        self._llm_available = True

    def record_llm_failure(self, error: str) -> None:
        """Record failed LLM call."""
        self._circuit_breaker.record_failure()
        self._llm_available = False

    def get_health_status(self) -> HealthStatus:
        """
        Get comprehensive health status.

        Returns:
            HealthStatus with component status and metrics
        """
        with self._lock:
            telemetry = get_telemetry()
            metrics = telemetry.get_snapshot(window_seconds=300)  # 5 min window

            issues = []
            status = "healthy"
            healthy = True

            # Check cache
            cache_healthy = True  # Cache is always healthy (disk-backed)

            # Check rules
            rules_healthy = True  # Rules are deterministic, always healthy

            # Check LLM
            llm_available = self._llm_available
            circuit_state = self._circuit_breaker.get_state().value

            if circuit_state == "open":
                llm_healthy = False
                issues.append("LLM circuit breaker is OPEN - LLM calls blocked")
                status = "degraded"
            elif circuit_state == "half_open":
                llm_healthy = True
                issues.append("LLM circuit breaker is HALF-OPEN - testing recovery")
                status = "degraded" if healthy else "unhealthy"
            else:
                llm_healthy = True

            if not llm_available:
                issues.append("LLM not available or not configured")

            # Check error rate
            if metrics.error_rate > 0.05:  # 5% error rate threshold
                healthy = False
                status = "unhealthy"
                issues.append(f"High error rate: {metrics.error_rate:.1%}")

            # Check latency
            if metrics.p99_latency_ms > 5000:  # 5 second threshold
                issues.append(f"High P99 latency: {metrics.p99_latency_ms:.0f}ms")
                status = "degraded" if status == "healthy" else status

            return HealthStatus(
                healthy=healthy,
                status=status,
                timestamp=datetime.now(),
                cache_healthy=cache_healthy,
                rules_healthy=rules_healthy,
                llm_healthy=llm_healthy,
                llm_available=llm_available,
                circuit_state=circuit_state,
                llm_failure_count=self._circuit_breaker._failure_count,
                llm_last_failure=self._circuit_breaker._last_failure_time,
                metrics=metrics,
                issues=issues,
            )

    def reset_circuit_breaker(self) -> None:
        """Reset the circuit breaker (admin action)."""
        self._circuit_breaker.reset()


# Global singleton
_global_health: Optional[HybridEngineHealth] = None


def get_health_checker() -> HybridEngineHealth:
    """Get the global health checker instance."""
    global _global_health
    if _global_health is None:
        _global_health = HybridEngineHealth()
    return _global_health


def health_check_dict() -> Dict[str, Any]:
    """
    Get health status as a dictionary (for API responses).

    Returns:
        Dict with health status suitable for JSON serialization
    """
    health = get_health_checker()
    status = health.get_health_status()

    return {
        "healthy": status.healthy,
        "status": status.status,
        "timestamp": status.timestamp.isoformat(),
        "components": {
            "cache": {
                "healthy": status.cache_healthy,
            },
            "rules": {
                "healthy": status.rules_healthy,
            },
            "llm": {
                "healthy": status.llm_healthy,
                "available": status.llm_available,
                "circuit_state": status.circuit_state,
                "failure_count": status.llm_failure_count,
                "last_failure": status.llm_last_failure.isoformat() if status.llm_last_failure else None,
            },
        },
        "metrics": {
            "total_decisions": status.metrics.total_decisions if status.metrics else 0,
            "cache_hit_rate": status.metrics.cache_hit_rate if status.metrics else 0,
            "rule_hit_rate": status.metrics.rule_hit_rate if status.metrics else 0,
            "llm_call_rate": status.metrics.llm_call_rate if status.metrics else 0,
            "avg_latency_ms": status.metrics.avg_latency_ms if status.metrics else 0,
            "error_rate": status.metrics.error_rate if status.metrics else 0,
        } if status.metrics else None,
        "issues": status.issues,
    }
