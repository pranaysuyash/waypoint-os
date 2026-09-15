"""
Product-agent runtime router.

Owns HTTP introspection/admin surfaces for the in-process product-agent runtime.
The FastAPI app shell still owns supervisor/recovery lifecycle wiring.
"""

from __future__ import annotations

import logging
from dataclasses import asdict
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from spine_api.core.audit import AuditContext, audit_logger
from spine_api.core.auth import get_current_agency, require_permission
from spine_api.core.platform_auth import require_platform_role
from spine_api.models.tenant import Agency
from spine_api.models.tenant import User
from spine_api.services.agent_requeue_jobs import (
    PoisonedJobRedactedError,
    RequeueJobStore,
)

try:
    from spine_api import persistence
except (ImportError, ValueError):
    import persistence

AuditStore = persistence.AuditStore

router = APIRouter()

logger = logging.getLogger("spine_api.agent_runtime")

_agent_supervisor: Any = None
_recovery_agent: Any = None
_requeue_worker_service: Any = None
_runtime_config: dict[str, Any] | None = None
_requeue_job_store: RequeueJobStore | None = None


def configure_runtime(
    *,
    agent_supervisor: Any,
    recovery_agent: Any,
    requeue_worker_service: Any = None,
    runtime_config: dict[str, Any] | None = None,
    requeue_job_store: RequeueJobStore | None = None,
) -> None:
    """Wire runtime singletons created by the FastAPI application shell."""
    global _agent_supervisor, _recovery_agent, _requeue_worker_service, _runtime_config
    global _requeue_job_store
    _agent_supervisor = agent_supervisor
    _recovery_agent = recovery_agent
    _requeue_worker_service = requeue_worker_service
    _runtime_config = runtime_config
    _requeue_job_store = requeue_job_store


def _supervisor() -> Any:
    if _agent_supervisor is None:
        raise RuntimeError("Agent runtime supervisor is not configured")
    return _agent_supervisor


def _recovery() -> Any:
    if _recovery_agent is None:
        raise RuntimeError("Recovery agent is not configured")
    return _recovery_agent


def _job_store() -> RequeueJobStore:
    """Return the configured durable requeue job store, or a default handle.

    RequeueJobStore is a stateless facade over the shared tripstore session
    maker; a default-constructed handle is safe for read/admin operations
    (only leasing cares about lease_seconds, and admin routes never lease).
    """
    return _requeue_job_store if _requeue_job_store is not None else RequeueJobStore()


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
        "requeue_worker": _requeue_worker_service.health() if _requeue_worker_service else None,
        "recovery_agent": {
            "name": "recovery_agent",
            "running": recovery.is_running,
            "trigger_contract": "Trips stuck beyond configured stage thresholds.",
            "input_contract": "Active trip with id, stage/state, and updated_at/updatedAt.",
            "output_contract": "Re-queue through runner when configured, else escalate review_status.",
            "idempotency_contract": "Durable queue-backed retry/poison ownership when sql_queue is enabled; in-memory fallback only for non-durable modes.",
            "failure_contract": "Fail closed by emitting agent_failed audit events.",
        },
    }
    if _runtime_config:
        result["config"] = _runtime_config
    # FND-0224: durable requeue poison stats on the canonical runtime surface.
    try:
        result["requeue_jobs"] = _job_store().snapshot()
    except Exception:
        logger.exception("Failed to read requeue job snapshot for runtime surface")
        result["requeue_jobs"] = None
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


# ── Poisoned-job DLQ admin surface (FND-0224) ─────────────────────────────
#
# Extends the canonical agent-runtime admin surface; no parallel ops route.
# Auth follows the canonical platform-admin contract (require_platform_role):
# tenant owner/admin never grants cross-workspace DLQ visibility, and raw
# header trust is never used.  Payloads are redacted by default because
# durable requeue payloads may carry traveler PII or credentials.


@router.get("/agents/runtime/poisoned", tags=["platform-admin"])
def list_poisoned_jobs(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    trip_id: Optional[str] = Query(default=None),
    platform_admin: User = require_platform_role("ops_admin", "super_admin"),
):
    """List poisoned requeue jobs — bounded page, payload redacted by default.

    Rows are bounded operator projections (no durable payload), so listing can
    never become an accidental PII export.
    """
    _ = platform_admin
    try:
        rows = _job_store().list_poisoned(limit=limit, offset=offset, trip_id=trip_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    snapshot = _job_store().snapshot()
    return {
        "jobs": [asdict(row) for row in rows],
        "total": len(rows),
        "limit": limit,
        "offset": offset,
        "poisoned_count": snapshot.get("poisoned_count", 0),
        "oldest_poisoned_age_seconds": snapshot.get("oldest_poisoned_age_seconds", 0.0),
    }


@router.get("/agents/runtime/poisoned/{job_id}", tags=["platform-admin"])
def inspect_poisoned_job(
    job_id: str,
    platform_admin: User = require_platform_role("ops_admin", "super_admin"),
):
    """Inspect one poisoned job — sensitive payload fields redacted in place."""
    _ = platform_admin
    detail = _job_store().inspect_poisoned(job_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Poisoned job not found")
    return detail


@router.post("/agents/runtime/poisoned/{job_id}/redact", tags=["platform-admin"])
async def redact_poisoned_job(
    job_id: str,
    platform_admin: User = require_platform_role("ops_admin", "super_admin"),
    audit: AuditContext = Depends(audit_logger()),
):
    """Strip a poisoned job's payload contents, preserving row + reason.

    The durable marker left behind makes later replay an explicit error.
    """
    _ = platform_admin
    if not _job_store().redact_poisoned(job_id):
        raise HTTPException(status_code=404, detail="Poisoned job not found")
    await audit.log(
        "dlq_job_redacted",
        resource_type="requeue_job",
        resource_id=job_id,
        changes={"note": "payload contents stripped; row, reason, and error preserved"},
    )
    return {"job_id": job_id, "status": "REDACTED"}


@router.post("/agents/runtime/poisoned/{job_id}/replay", tags=["platform-admin"])
async def replay_poisoned_job(
    job_id: str,
    platform_admin: User = require_platform_role("ops_admin", "super_admin"),
    audit: AuditContext = Depends(audit_logger()),
):
    """Requeue a poisoned job as a fresh attempt (attempt counter incremented).

    Refuses redacted jobs with an explicit error: their payload is gone, so
    replay would execute an empty job.
    """
    _ = platform_admin
    try:
        replayed = _job_store().replay_poisoned(job_id)
    except PoisonedJobRedactedError as exc:
        raise HTTPException(
            status_code=409,
            detail=f"Job {job_id} was redacted; payload is gone and cannot be replayed",
        ) from exc
    if not replayed:
        raise HTTPException(status_code=404, detail="Poisoned job not found")
    await audit.log(
        "dlq_job_replayed",
        resource_type="requeue_job",
        resource_id=job_id,
        changes={"note": "requeued as pending with incremented attempt counter"},
    )
    return {"job_id": job_id, "status": "REQUEUED"}
