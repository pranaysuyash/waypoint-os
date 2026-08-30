"""
src/schemas/failure_modes.py — Failure mode taxonomy, circuit states, and graceful degradation models.

Grounding doctrine:
- PER-0924 (Failure Mode Architect): Explicit failure taxonomy, blast-radius containment, safe states.
- PER-0925 (Graceful Degradation Designer): Multi-tier degradation hierarchy without silent damage.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class FailureDomain(str, Enum):
    """Domains where failures can originate in Waypoint OS."""
    SUPPLIER_API = "SUPPLIER_API"
    PAYMENT_GATEWAY = "PAYMENT_GATEWAY"
    MESSAGING_CHANNEL = "MESSAGING_CHANNEL"
    INTAKE_INGESTION = "INTAKE_INGESTION"
    AGENT_EXECUTION = "AGENT_EXECUTION"
    STATE_CONSISTENCY = "STATE_CONSISTENCY"


class DegradationLevel(str, Enum):
    """Graceful degradation tiers from nominal to fail-closed quarantine."""
    LEVEL_0_NOMINAL = "LEVEL_0_NOMINAL"              # Live real-time liquidity and dynamic execution
    LEVEL_1_CACHED_FALLBACK = "LEVEL_1_CACHED_FALLBACK"  # Cached data with explicit staleness watermark
    LEVEL_2_OPERATOR_ASSISTED = "LEVEL_2_OPERATOR_ASSISTED"  # Pre-filled operator draft requesting human verification
    LEVEL_3_FAIL_CLOSED_QUARANTINE = "LEVEL_3_FAIL_CLOSED_QUARANTINE"  # Isolated state with audit incident log


class CircuitState(str, Enum):
    """Operational states for resilience circuit breakers."""
    CLOSED = "CLOSED"        # Normal operation: requests pass through
    OPEN = "OPEN"            # Tripped: requests immediately routed to fallback/degraded path
    HALF_OPEN = "HALF_OPEN"  # Probing: canary requests testing upstream health


@dataclass(slots=True)
class CircuitBreakerConfig:
    """Configuration tuning for a circuit breaker instance."""
    failure_threshold: int = 5          # Number of failures before tripping OPEN
    recovery_timeout_seconds: float = 30.0  # Seconds to wait in OPEN before transitioning to HALF_OPEN
    half_open_success_threshold: int = 2   # Consecutive successes in HALF_OPEN to close circuit
    sliding_window_seconds: float = 60.0    # Time window for failure counting


@dataclass(slots=True)
class FailureIncident:
    """Record of a detected failure, quarantine event, or degradation transition."""
    incident_id: str
    domain: FailureDomain
    error_code: str
    message: str
    degradation_level: DegradationLevel
    circuit_state: CircuitState
    target_resource: Optional[str] = None
    compensating_action: Optional[str] = None
    quarantined_payload: Optional[dict[str, Any]] = None
    resolved: bool = False
    occurred_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass(slots=True)
class DegradedResult:
    """Wrapper holding degraded response data with epistemic transparency."""
    data: Any
    degradation_level: DegradationLevel
    is_fallback: bool
    watermark_timestamp: Optional[str] = None
    advisory_message: Optional[str] = None
