"""
src/services/resilience_engine.py — Circuit breaker, graceful degradation hierarchy, and quarantine manager.

Grounding doctrine:
- PER-0924 (Failure Mode Architect): Bounded failures, canary probes, compensating actions.
- PER-0925 (Graceful Degradation Designer): Explicit degradation hierarchy with watermark transparency.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any, Callable, Optional, TypeVar
from uuid import uuid4

from src.schemas.failure_modes import (
    CircuitBreakerConfig,
    CircuitState,
    DegradationLevel,
    DegradedResult,
    FailureDomain,
    FailureIncident,
)

T = TypeVar("T")

logger = logging.getLogger("waypoint.resilience")


class CircuitBreaker:
    """Deterministic circuit breaker protecting external provider and agent integrations."""

    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None) -> None:
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.failure_timestamps: list[float] = []
        self.last_tripped_at: Optional[float] = None
        self.half_open_success_count: int = 0
        self.total_failures_recorded: int = 0
        self.total_successes_recorded: int = 0

    def can_execute(self) -> bool:
        """Evaluate if an outbound request is permitted through the circuit."""
        now = time.monotonic()
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            if self.last_tripped_at is not None and (now - self.last_tripped_at) >= self.config.recovery_timeout_seconds:
                logger.info("CircuitBreaker[%s]: Recovery timeout elapsed. Transitioning OPEN -> HALF_OPEN (canary probe).", self.name)
                self.state = CircuitState.HALF_OPEN
                self.half_open_success_count = 0
                return True
            return False

        if self.state == CircuitState.HALF_OPEN:
            # Allow canary calls in HALF_OPEN
            return True

        return False

    def record_success(self) -> None:
        """Record a successful execution."""
        self.total_successes_recorded += 1
        if self.state == CircuitState.HALF_OPEN:
            self.half_open_success_count += 1
            if self.half_open_success_count >= self.config.half_open_success_threshold:
                logger.info("CircuitBreaker[%s]: Canary threshold met (%d successes). Transitioning HALF_OPEN -> CLOSED.", self.name, self.half_open_success_count)
                self.state = CircuitState.CLOSED
                self.failure_timestamps.clear()
                self.half_open_success_count = 0
        elif self.state == CircuitState.CLOSED:
            # Clean up old failures
            now = time.monotonic()
            self.failure_timestamps = [t for t in self.failure_timestamps if now - t <= self.config.sliding_window_seconds]

    def record_failure(self, error: Optional[Exception | str] = None) -> None:
        """Record a failure event and trip circuit if threshold is exceeded."""
        now = time.monotonic()
        self.total_failures_recorded += 1
        self.failure_timestamps.append(now)

        # Prune failures outside the sliding window
        self.failure_timestamps = [t for t in self.failure_timestamps if now - t <= self.config.sliding_window_seconds]

        if self.state == CircuitState.HALF_OPEN:
            logger.warning("CircuitBreaker[%s]: Canary probe failed (%s). Transitioning HALF_OPEN -> OPEN.", self.name, error)
            self.state = CircuitState.OPEN
            self.last_tripped_at = now
            self.half_open_success_count = 0
        elif self.state == CircuitState.CLOSED:
            if len(self.failure_timestamps) >= self.config.failure_threshold:
                logger.warning(
                    "CircuitBreaker[%s]: Failure threshold reached (%d in %.1fs). Tripping CLOSED -> OPEN.",
                    self.name, len(self.failure_timestamps), self.config.sliding_window_seconds
                )
                self.state = CircuitState.OPEN
                self.last_tripped_at = now

    def reset(self) -> None:
        """Manually reset the circuit breaker to nominal CLOSED state."""
        logger.info("CircuitBreaker[%s]: Manual reset triggered. Transitioning to CLOSED.", self.name)
        self.state = CircuitState.CLOSED
        self.failure_timestamps.clear()
        self.last_tripped_at = None
        self.half_open_success_count = 0

    def get_status(self) -> dict[str, Any]:
        """Return operational telemetry for the circuit breaker."""
        now = time.monotonic()
        active_failures = len([t for t in self.failure_timestamps if now - t <= self.config.sliding_window_seconds])
        cooldown_remaining = 0.0
        if self.state == CircuitState.OPEN and self.last_tripped_at is not None:
            elapsed = now - self.last_tripped_at
            cooldown_remaining = max(0.0, round(self.config.recovery_timeout_seconds - elapsed, 2))

        return {
            "name": self.name,
            "state": self.state.value,
            "recent_failure_count": active_failures,
            "failure_threshold": self.config.failure_threshold,
            "recovery_timeout_seconds": self.config.recovery_timeout_seconds,
            "cooldown_remaining_seconds": cooldown_remaining,
            "total_successes": self.total_successes_recorded,
            "total_failures": self.total_failures_recorded,
        }


class ResilienceEngine:
    """Central resilience coordinator managing circuit breakers, degradation fallbacks, and quarantine storage."""

    _instance: Optional[ResilienceEngine] = None

    def __init__(self) -> None:
        self._circuits: dict[str, CircuitBreaker] = {}
        self._incidents: list[FailureIncident] = []
        self._bootstrap_default_circuits()

    @classmethod
    def get_instance(cls) -> ResilienceEngine:
        """Singleton accessor for process-wide resilience engine."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _bootstrap_default_circuits(self) -> None:
        """Initialize standard Waypoint OS integration circuit breakers."""
        defaults = [
            ("supplier_ndc", CircuitBreakerConfig(failure_threshold=4, recovery_timeout_seconds=30.0)),
            ("whatsapp_api", CircuitBreakerConfig(failure_threshold=5, recovery_timeout_seconds=45.0)),
            ("sendgrid_email", CircuitBreakerConfig(failure_threshold=5, recovery_timeout_seconds=45.0)),
            ("payment_gateway", CircuitBreakerConfig(failure_threshold=3, recovery_timeout_seconds=60.0)),
            ("llm_guard", CircuitBreakerConfig(failure_threshold=3, recovery_timeout_seconds=30.0)),
        ]
        for name, config in defaults:
            self._circuits[name] = CircuitBreaker(name, config)

    def get_circuit(self, name: str) -> CircuitBreaker:
        """Retrieve or lazily create a named circuit breaker."""
        if name not in self._circuits:
            self._circuits[name] = CircuitBreaker(name)
        return self._circuits[name]

    def list_circuits(self) -> list[dict[str, Any]]:
        """List telemetry status across all registered circuit breakers."""
        return [circuit.get_status() for circuit in self._circuits.values()]

    def reset_circuit(self, name: str) -> bool:
        """Manually reset a named circuit breaker."""
        if name in self._circuits:
            self._circuits[name].reset()
            return True
        return False

    def execute_with_fallback(
        self,
        circuit_name: str,
        live_callable: Callable[[], Any],
        fallback_callable: Optional[Callable[[], Any]] = None,
        cached_data: Optional[Any] = None,
        cache_timestamp: Optional[str] = None,
        domain: FailureDomain = FailureDomain.SUPPLIER_API,
    ) -> DegradedResult:
        """Execute an operation with multi-level graceful degradation and circuit protection."""
        circuit = self.get_circuit(circuit_name)

        if circuit.can_execute():
            try:
                result = live_callable()
                circuit.record_success()
                return DegradedResult(
                    data=result,
                    degradation_level=DegradationLevel.LEVEL_0_NOMINAL,
                    is_fallback=False,
                )
            except Exception as exc:
                circuit.record_failure(exc)
                logger.warning("ResilienceEngine: Live execution failed on '%s': %s", circuit_name, exc)
                self.record_incident(
                    domain=domain,
                    error_code="CALLABLE_EXCEPTION",
                    message=str(exc),
                    degradation_level=DegradationLevel.LEVEL_1_CACHED_FALLBACK if (cached_data is not None or fallback_callable is not None) else DegradationLevel.LEVEL_2_OPERATOR_ASSISTED,
                    circuit_state=circuit.state,
                    target_resource=circuit_name,
                )

        # Level 1: Cached Fallback or Fallback Callable
        if cached_data is not None:
            return DegradedResult(
                data=cached_data,
                degradation_level=DegradationLevel.LEVEL_1_CACHED_FALLBACK,
                is_fallback=True,
                watermark_timestamp=cache_timestamp or datetime.now(timezone.utc).isoformat(),
                advisory_message=f"Live connection to {circuit_name} unavailable (circuit={circuit.state.value}). Serving cached snapshot.",
            )

        if fallback_callable is not None:
            try:
                fallback_result = fallback_callable()
                return DegradedResult(
                    data=fallback_result,
                    degradation_level=DegradationLevel.LEVEL_1_CACHED_FALLBACK,
                    is_fallback=True,
                    advisory_message=f"Serving secondary fallback response for {circuit_name}.",
                )
            except Exception as fb_exc:
                logger.error("ResilienceEngine: Secondary fallback failed on '%s': %s", circuit_name, fb_exc)

        # Level 2: Operator Assisted Fallback
        return DegradedResult(
            data=None,
            degradation_level=DegradationLevel.LEVEL_2_OPERATOR_ASSISTED,
            is_fallback=True,
            advisory_message=f"Upstream provider {circuit_name} is currently degraded (circuit={circuit.state.value}). Please initiate manual quotation.",
        )

    def execute_with_supplier_failover(
        self,
        supplier_chain: list[str],
        operation: Callable[[str], T],
        fallback_data: T,
    ) -> tuple[T, str, bool]:
        """
        Execute an operation across a chain of suppliers with automatic circuit-aware failover.
        Returns (result, winning_supplier_name, was_fallback).
        """
        errors = []
        for supplier in supplier_chain:
            circuit = self.get_circuit(f"supplier_{supplier}")
            if circuit.state == CircuitState.OPEN:
                logger.warning("Skipping supplier '%s': circuit is OPEN", supplier)
                continue

            try:
                result = operation(supplier)
                circuit.record_success()
                return result, supplier, False
            except Exception as exc:
                circuit.record_failure()
                errors.append(f"{supplier}: {str(exc)}")
                logger.warning("Supplier '%s' failed, failing over to next supplier: %s", supplier, exc)

        logger.error("All suppliers in chain %s failed. Serving static fallback.", supplier_chain)
        return fallback_data, "fallback_cache", True

    def record_incident(
        self,
        domain: FailureDomain,
        error_code: str,
        message: str,
        degradation_level: DegradationLevel,
        circuit_state: CircuitState,
        target_resource: Optional[str] = None,
        compensating_action: Optional[str] = None,
        quarantined_payload: Optional[dict[str, Any]] = None,
    ) -> FailureIncident:
        """Log a failure incident or quarantined payload."""
        incident = FailureIncident(
            incident_id=f"inc_{uuid4().hex[:10]}",
            domain=domain,
            error_code=error_code,
            message=message,
            degradation_level=degradation_level,
            circuit_state=circuit_state,
            target_resource=target_resource,
            compensating_action=compensating_action,
            quarantined_payload=quarantined_payload,
            resolved=False,
        )
        self._incidents.append(incident)
        # Cap memory retained incidents
        if len(self._incidents) > 500:
            self._incidents = self._incidents[-500:]
        return incident

    def list_incidents(self, resolved: Optional[bool] = None) -> list[FailureIncident]:
        """List recorded failure incidents and quarantined items."""
        if resolved is None:
            return list(self._incidents)
        return [inc for inc in self._incidents if inc.resolved == resolved]

    def get_incident(self, incident_id: str) -> Optional[FailureIncident]:
        """Retrieve a specific incident by ID."""
        for inc in self._incidents:
            if inc.incident_id == incident_id:
                return inc
        return None

    def resolve_incident(self, incident_id: str) -> bool:
        """Mark an incident as resolved."""
        incident = self.get_incident(incident_id)
        if incident:
            incident.resolved = True
            return True
        return False

    def quarantine_intake(self, raw_input: str, reason: str, metadata: Optional[dict[str, Any]] = None) -> FailureIncident:
        """Quarantine a poisoned or malformed inbound payload to isolate the worker."""
        payload = {
            "raw_input": raw_input,
            "metadata": metadata or {},
            "quarantined_at": datetime.now(timezone.utc).isoformat(),
        }
        return self.record_incident(
            domain=FailureDomain.INTAKE_INGESTION,
            error_code="INTAKE_POISONED_OR_MALFORMED",
            message=reason,
            degradation_level=DegradationLevel.LEVEL_3_FAIL_CLOSED_QUARANTINE,
            circuit_state=CircuitState.CLOSED,
            target_resource="intake_pipeline",
            compensating_action="ISOLATE_AND_NOTIFY_OPERATOR",
            quarantined_payload=payload,
        )


class CompensatingTransactionHandler:
    """Handles commercial rollbacks and safe compensations when distributed actions fail."""

    @staticmethod
    def compensate_booking_failure(
        trip_id: str,
        payment_id: str,
        amount: float,
        reason: str,
    ) -> dict[str, Any]:
        """Execute compensation plan when supplier inventory hold fails after payment authorization."""
        resilience = ResilienceEngine.get_instance()
        incident = resilience.record_incident(
            domain=FailureDomain.STATE_CONSISTENCY,
            error_code="INVENTORY_HOLD_FAILED_AFTER_PAYMENT",
            message=f"Inventory hold failed for trip {trip_id} after payment {payment_id} captured: {reason}",
            degradation_level=DegradationLevel.LEVEL_3_FAIL_CLOSED_QUARANTINE,
            circuit_state=CircuitState.OPEN,
            target_resource=trip_id,
            compensating_action="INITIATE_PAYMENT_REFUND_AND_ESCALATE",
        )

        return {
            "status": "COMPENSATING_HOLD_INITIATED",
            "incident_id": incident.incident_id,
            "trip_id": trip_id,
            "payment_id": payment_id,
            "refund_amount": amount,
            "recommended_action": "Payment refund authorization queued. Operator ticket created.",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
