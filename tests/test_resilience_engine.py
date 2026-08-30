"""
tests/test_resilience_engine.py — Unit tests for PER-0924/0925 Circuit Breakers & Resilience Engine.
"""

import time
from src.schemas.failure_modes import (
    CircuitBreakerConfig,
    CircuitState,
    DegradationLevel,
    FailureDomain,
)
from src.services.resilience_engine import (
    CircuitBreaker,
    CompensatingTransactionHandler,
    ResilienceEngine,
)


def test_circuit_breaker_trips_to_open_after_threshold():
    """Verify circuit breaker transitions from CLOSED to OPEN after failure threshold."""
    config = CircuitBreakerConfig(failure_threshold=3, recovery_timeout_seconds=1.0)
    cb = CircuitBreaker("test_supplier", config=config)

    assert cb.state == CircuitState.CLOSED
    assert cb.can_execute() is True

    # Record 2 failures -> remains CLOSED
    cb.record_failure("timeout")
    cb.record_failure("503 Service Unavailable")
    assert cb.state == CircuitState.CLOSED
    assert cb.can_execute() is True

    # 3rd failure -> trips OPEN
    cb.record_failure("500 Internal Error")
    assert cb.state == CircuitState.OPEN
    assert cb.can_execute() is False


def test_circuit_breaker_recovers_via_half_open_canary():
    """Verify circuit breaker allows canary request in HALF_OPEN and closes after consecutive successes."""
    config = CircuitBreakerConfig(
        failure_threshold=2,
        recovery_timeout_seconds=0.1,
        half_open_success_threshold=2,
    )
    cb = CircuitBreaker("test_canary", config=config)

    cb.record_failure("error 1")
    cb.record_failure("error 2")
    assert cb.state == CircuitState.OPEN
    assert cb.can_execute() is False

    # Wait for recovery timeout
    time.sleep(0.12)

    # First call after cooldown should transition to HALF_OPEN
    assert cb.can_execute() is True
    assert cb.state == CircuitState.HALF_OPEN

    # 1st success in HALF_OPEN
    cb.record_success()
    assert cb.state == CircuitState.HALF_OPEN

    # 2nd success in HALF_OPEN -> closes circuit
    cb.record_success()
    assert cb.state == CircuitState.CLOSED
    assert cb.can_execute() is True


def test_circuit_breaker_manual_reset():
    """Verify manual reset forces circuit back to CLOSED."""
    config = CircuitBreakerConfig(failure_threshold=2)
    cb = CircuitBreaker("test_reset", config=config)

    cb.record_failure("e1")
    cb.record_failure("e2")
    assert cb.state == CircuitState.OPEN

    cb.reset()
    assert cb.state == CircuitState.CLOSED
    assert cb.can_execute() is True


def test_resilience_engine_execute_with_cached_fallback():
    """Verify graceful degradation to Level 1 cached fallback when circuit trips."""
    engine = ResilienceEngine()
    circuit_name = "test_hotel_supplier"

    cached_rates = [{"hotel": "Four Seasons", "rate": 850}]

    def failing_live_call():
        raise ConnectionResetError("Supplier GDS connection dropped")

    # Trip the circuit with repeated calls
    for _ in range(5):
        result = engine.execute_with_fallback(
            circuit_name=circuit_name,
            live_callable=failing_live_call,
            cached_data=cached_rates,
            cache_timestamp="2026-08-29T10:00:00Z",
        )

    assert result.degradation_level == DegradationLevel.LEVEL_1_CACHED_FALLBACK
    assert result.is_fallback is True
    assert result.data == cached_rates
    assert result.watermark_timestamp == "2026-08-29T10:00:00Z"
    assert "Live connection to test_hotel_supplier unavailable" in result.advisory_message


def test_resilience_engine_operator_assisted_fallback():
    """Verify Level 2 operator assisted fallback when no cached data exists."""
    engine = ResilienceEngine()
    circuit_name = "test_custom_supplier"

    def failing_live_call():
        raise TimeoutError("Supplier API Gateway Timeout")

    result = engine.execute_with_fallback(
        circuit_name=circuit_name,
        live_callable=failing_live_call,
        cached_data=None,
    )

    assert result.degradation_level == DegradationLevel.LEVEL_2_OPERATOR_ASSISTED
    assert result.is_fallback is True
    assert result.data is None
    assert "initiate manual quotation" in result.advisory_message


def test_resilience_engine_quarantine_poisoned_intake():
    """Verify malformed or hostile intake payloads are quarantined without worker crash."""
    engine = ResilienceEngine()
    incident = engine.quarantine_intake(
        raw_input="<script>alert('xss')</script> malformed payload",
        reason="Detected unparseable hostile byte sequence",
        metadata={"channel": "email_inbound", "sender": "untrusted@external.com"},
    )

    assert incident.domain == FailureDomain.INTAKE_INGESTION
    assert incident.degradation_level == DegradationLevel.LEVEL_3_FAIL_CLOSED_QUARANTINE
    assert incident.compensating_action == "ISOLATE_AND_NOTIFY_OPERATOR"
    assert incident.quarantined_payload["raw_input"].startswith("<script>")
    assert incident.resolved is False


def test_compensating_transaction_handler():
    """Verify commercial compensation handler emits structured rollback guidance."""
    res = CompensatingTransactionHandler.compensate_booking_failure(
        trip_id="trip_9921",
        payment_id="ch_8812a",
        amount=1450.00,
        reason="Flight seat inventory exhausted during booking commit",
    )

    assert res["status"] == "COMPENSATING_HOLD_INITIATED"
    assert res["refund_amount"] == 1450.00
    assert "Payment refund authorization queued" in res["recommended_action"]
