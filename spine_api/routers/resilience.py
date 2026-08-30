"""
spine_api/routers/resilience.py — Router for Circuit Breakers, Graceful Degradation & Failure Quarantine.

Grounding doctrine:
- PER-0924 (Failure Mode Architect): Bounded failures, incident audit trail, state compensation.
- PER-0925 (Graceful Degradation Designer): Operational circuit visibility, manual recovery control.
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from spine_api.contract import (
    CircuitListResponse,
    CircuitResetResponse,
    CircuitStatusItem,
    CompensationRequest,
    CompensationResponse,
    IncidentItem,
    IncidentListResponse,
    QuarantineIntakeRequest,
    QuarantineIntakeResponse,
)
from src.services.resilience_engine import CompensatingTransactionHandler, ResilienceEngine

logger = logging.getLogger("spine_api.resilience")

router = APIRouter(prefix="/api/v1/resilience", tags=["resilience"])


@router.get("/circuits", response_model=CircuitListResponse)
def list_circuits() -> CircuitListResponse:
    """
    List all active integration circuit breakers and their real-time telemetry.
    """
    engine = ResilienceEngine.get_instance()
    raw_circuits = engine.list_circuits()
    items = [CircuitStatusItem(**c) for c in raw_circuits]
    return CircuitListResponse(circuits=items, total_circuits=len(items))


@router.post("/circuits/{circuit_name}/reset", response_model=CircuitResetResponse)
def reset_circuit(circuit_name: str) -> CircuitResetResponse:
    """
    Manually reset a tripped circuit breaker back to nominal CLOSED state.
    """
    engine = ResilienceEngine.get_instance()
    success = engine.reset_circuit(circuit_name)
    if not success:
        raise HTTPException(status_code=404, detail=f"Circuit '{circuit_name}' not found")

    circuit = engine.get_circuit(circuit_name)
    return CircuitResetResponse(
        circuit_name=circuit_name,
        reset_successful=True,
        state=circuit.state.value,
    )


@router.get("/incidents", response_model=IncidentListResponse)
def list_incidents(resolved: Optional[bool] = Query(default=None)) -> IncidentListResponse:
    """
    List recorded failure incidents, degradation events, and quarantined payloads.
    """
    engine = ResilienceEngine.get_instance()
    incidents = engine.list_incidents(resolved=resolved)
    items = [
        IncidentItem(
            incident_id=inc.incident_id,
            domain=inc.domain.value,
            error_code=inc.error_code,
            message=inc.message,
            degradation_level=inc.degradation_level.value,
            circuit_state=inc.circuit_state.value,
            target_resource=inc.target_resource,
            compensating_action=inc.compensating_action,
            quarantined_payload=inc.quarantined_payload,
            resolved=inc.resolved,
            occurred_at=inc.occurred_at,
        )
        for inc in incidents
    ]
    return IncidentListResponse(incidents=items, total_incidents=len(items))


@router.post("/incidents/{incident_id}/resolve")
def resolve_incident(incident_id: str) -> dict[str, bool]:
    """
    Mark an active failure incident as reviewed and resolved.
    """
    engine = ResilienceEngine.get_instance()
    success = engine.resolve_incident(incident_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Incident '{incident_id}' not found")
    return {"resolved": True}


@router.post("/quarantine", response_model=QuarantineIntakeResponse)
def quarantine_intake(request: QuarantineIntakeRequest) -> QuarantineIntakeResponse:
    """
    Isolate a malformed or poisoned inbound payload into quarantine without worker crash.
    """
    engine = ResilienceEngine.get_instance()
    incident = engine.quarantine_intake(
        raw_input=request.raw_input,
        reason=request.reason,
        metadata=request.metadata,
    )
    return QuarantineIntakeResponse(
        incident_id=incident.incident_id,
        status="QUARANTINED",
        quarantined_at=incident.occurred_at,
    )


@router.post("/compensate", response_model=CompensationResponse)
def compensate_transaction(request: CompensationRequest) -> CompensationResponse:
    """
    Execute a compensating state rollback when downstream execution fails after payment capture.
    """
    res = CompensatingTransactionHandler.compensate_booking_failure(
        trip_id=request.trip_id,
        payment_id=request.payment_id,
        amount=request.amount,
        reason=request.reason,
    )
    return CompensationResponse(**res)
