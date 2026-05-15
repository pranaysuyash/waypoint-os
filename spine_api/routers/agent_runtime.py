"""
Product-agent runtime router.

Owns HTTP introspection/admin surfaces for the in-process product-agent runtime.
The FastAPI app shell still owns supervisor/recovery lifecycle wiring.
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from spine_api.core.auth import get_current_agency, require_permission
from spine_api.models.tenant import Agency

try:
    from spine_api import persistence
except (ImportError, ValueError):
    import persistence

AuditStore = persistence.AuditStore

router = APIRouter()

_agent_supervisor: Any = None
_recovery_agent: Any = None
_runtime_config: dict[str, Any] | None = None


def configure_runtime(*, agent_supervisor: Any, recovery_agent: Any, runtime_config: dict[str, Any] | None = None) -> None:
    """Wire runtime singletons created by the FastAPI application shell."""
    global _agent_supervisor, _recovery_agent, _runtime_config
    _agent_supervisor = agent_supervisor
    _recovery_agent = recovery_agent
    _runtime_config = runtime_config


def _supervisor() -> Any:
    if _agent_supervisor is None:
        raise RuntimeError("Agent runtime supervisor is not configured")
    return _agent_supervisor


def _recovery() -> Any:
    if _recovery_agent is None:
        raise RuntimeError("Recovery agent is not configured")
    return _recovery_agent


@router.get("/agents/runtime")
def get_agent_runtime(
    agency: Agency = Depends(get_current_agency),
):
    """
    Return canonical backend product-agent registry and supervisor health.

    This is the single runtime introspection surface for backend product agents;
    it intentionally exposes static in-repo registry contracts instead of
    dynamic plugin metadata.
    """
    _ = agency
    supervisor = _supervisor()
    recovery = _recovery()
    result = {
        "registry": supervisor.registry.definitions(),
        "supervisor": supervisor.health(),
        "recovery_agent": {
            "name": "recovery_agent",
            "running": recovery.is_running,
            "trigger_contract": "Trips stuck beyond configured stage thresholds.",
            "input_contract": "Active trip with id, stage/state, and updated_at/updatedAt.",
            "output_contract": "Re-queue through runner when configured, else escalate review_status.",
            "idempotency_contract": "Per-trip in-memory requeue count with max attempts before escalation.",
            "failure_contract": "Fail closed by emitting agent_failed audit events.",
        },
    }
    if _runtime_config:
        result["config"] = _runtime_config
    return result


@router.post("/agents/runtime/run-once")
def run_agent_runtime_once(
    agent_name: Optional[str] = Query(default=None),
    agency: Agency = Depends(get_current_agency),
    _perm=require_permission("ai_workforce:manage"),
):
    """Synchronously run one supervisor pass for testing/admin operations."""
    _ = agency
    supervisor = _supervisor()
    if agent_name and agent_name not in supervisor.health()["registered_agents"]:
        raise HTTPException(status_code=404, detail="Agent not found")
    results = supervisor.run_once(agent_name=agent_name)
    return {
        "agent_name": agent_name,
        "results": [result.to_dict() for result in results],
        "total": len(results),
        "supervisor": supervisor.health(),
    }


@router.get("/agents/runtime/events")
def get_agent_runtime_events(
    limit: int = Query(default=100, ge=1, le=1000),
    agent_name: Optional[str] = Query(default=None),
    correlation_id: Optional[str] = Query(default=None),
    agency: Agency = Depends(get_current_agency),
):
    """Return canonical backend product-agent events across trips."""
    _ = agency
    events = AuditStore.get_agent_events(limit=limit, agent_name=agent_name, correlation_id=correlation_id)
    return {"events": events, "total": len(events)}
