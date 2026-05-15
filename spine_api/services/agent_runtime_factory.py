"""
Testable construction of agent runtime components.

Replaces the module-level singleton construction in server.py with an explicit,
env-var-resolved factory. All env vars are read at build-time, never at import
time, so tests can monkeypatch freely without importlib.reload().
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Any, Optional

from src.agents.recovery_agent import RecoveryAgent
from src.agents.requeue import build_requeue_port
from src.agents.runtime import AgentSupervisor, build_default_registry
from spine_api.services.agent_runtime_adapters import TripStoreAdapter, AuditStoreAdapter
from spine_api.services.agent_work_coordinator import SQLWorkCoordinator

logger = logging.getLogger("agent_runtime_factory")

# ---------------------------------------------------------------------------
# Env-var constants
# ---------------------------------------------------------------------------

ENV_COORDINATOR = "AGENT_WORK_COORDINATOR"
ENV_LEASE_SECONDS = "AGENT_WORK_LEASE_SECONDS"
ENV_SUPERVISOR_INTERVAL = "AGENT_SUPERVISOR_INTERVAL_S"
ENV_DEPLOYMENT_MODE = "DEPLOYMENT_MODE"
ENV_RECOVERY_REQUEUE_MODE = "AGENT_RECOVERY_REQUEUE_MODE"
ENV_RECOVERY_INTERVAL = "RECOVERY_INTERVAL_S"

# ---------------------------------------------------------------------------
# Valid values
# ---------------------------------------------------------------------------

VALID_COORDINATORS = {"memory", "sql"}
VALID_DEPLOYMENT_MODES = {"local", "test", "dogfood", "beta", "production"}
VALID_REQUEUE_MODES = {"disabled", "inline"}

# ---------------------------------------------------------------------------
# Config snapshot
# ---------------------------------------------------------------------------


@dataclass
class AgentRuntimeConfig:
    deployment_mode: str = "local"
    coordinator_backend: str = "memory"
    lease_seconds: int = 60
    supervisor_interval_seconds: int = 300
    recovery_requeue_mode: str = "disabled"
    recovery_interval_seconds: int = 300

    def to_dict(self) -> dict[str, Any]:
        return {
            "deployment_mode": self.deployment_mode,
            "coordinator_backend": self.coordinator_backend,
            "lease_seconds": self.lease_seconds,
            "supervisor_interval_seconds": self.supervisor_interval_seconds,
            "recovery_requeue_mode": self.recovery_requeue_mode,
            "recovery_interval_seconds": self.recovery_interval_seconds,
        }


# ---------------------------------------------------------------------------
# Bundle of constructed runtime objects
# ---------------------------------------------------------------------------


@dataclass
class AgentRuntimeBundle:
    config: AgentRuntimeConfig
    coordinator: Any  # WorkCoordinator | None
    recovery_agent: RecoveryAgent
    supervisor: AgentSupervisor

    def health(self) -> dict[str, Any]:
        return {
            "config": self.config.to_dict(),
            "supervisor": self.supervisor.health(),
            "recovery_agent": {
                "name": "recovery_agent",
                "running": self.recovery_agent.is_running,
            },
        }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _int_env(name: str, default: int) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        logger.warning("%s=%r is not an integer, using default %s", name, raw, default)
        return default


def _str_env(name: str, default: str) -> str:
    return os.environ.get(name, "").strip() or default


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------


def build_agent_runtime_config() -> AgentRuntimeConfig:
    """Read env vars and return a validated config snapshot.

    All env vars are read at call time.  The function never mutates os.environ
    and never triggers side effects (no imports of heavy modules).
    """
    deployment_mode = _str_env(ENV_DEPLOYMENT_MODE, "local").lower()
    if deployment_mode not in VALID_DEPLOYMENT_MODES:
        raise ValueError(
            f"Invalid {ENV_DEPLOYMENT_MODE}={deployment_mode!r}. "
            f"Must be one of: {', '.join(sorted(VALID_DEPLOYMENT_MODES))}"
        )

    coordinator_raw = _str_env(ENV_COORDINATOR, "memory").lower()
    if coordinator_raw not in VALID_COORDINATORS:
        raise ValueError(
            f"Invalid {ENV_COORDINATOR}={coordinator_raw!r}. "
            f"Must be one of: {', '.join(sorted(VALID_COORDINATORS))}"
        )

    requeue_raw = _str_env(ENV_RECOVERY_REQUEUE_MODE, "disabled").lower()
    if requeue_raw not in VALID_REQUEUE_MODES:
        raise ValueError(
            f"Invalid {ENV_RECOVERY_REQUEUE_MODE}={requeue_raw!r}. "
            f"Must be one of: {', '.join(sorted(VALID_REQUEUE_MODES))}"
        )

    return AgentRuntimeConfig(
        deployment_mode=deployment_mode,
        coordinator_backend=coordinator_raw,
        lease_seconds=_int_env(ENV_LEASE_SECONDS, 60),
        supervisor_interval_seconds=_int_env(ENV_SUPERVISOR_INTERVAL, 300),
        recovery_requeue_mode=requeue_raw,
        recovery_interval_seconds=_int_env(ENV_RECOVERY_INTERVAL, 300),
    )


def _validate_config(config: AgentRuntimeConfig) -> None:
    """Reject direct construction with invalid values (bypasses env validation)."""
    if config.coordinator_backend not in VALID_COORDINATORS:
        raise ValueError(
            f"Invalid coordinator_backend={config.coordinator_backend!r}. "
            f"Must be one of: {', '.join(sorted(VALID_COORDINATORS))}"
        )
    if config.deployment_mode not in VALID_DEPLOYMENT_MODES:
        raise ValueError(
            f"Invalid deployment_mode={config.deployment_mode!r}. "
            f"Must be one of: {', '.join(sorted(VALID_DEPLOYMENT_MODES))}"
        )
    if config.recovery_requeue_mode not in VALID_REQUEUE_MODES:
        raise ValueError(
            f"Invalid recovery_requeue_mode={config.recovery_requeue_mode!r}. "
            f"Must be one of: {', '.join(sorted(VALID_REQUEUE_MODES))}"
        )


def build_agent_runtime_from_config(
    config: AgentRuntimeConfig,
    *,
    _trip_repo: Any = None,
    _audit_sink: Any = None,
    _spine_runner: Any = None,
    _run_spine_fn: Any = None,
) -> AgentRuntimeBundle:
    """Construct runtime objects from a validated config.

    Accepts optional overrides for trip_repo, audit_sink, spine_runner, and
    run_spine_fn so that the caller (server.py or tests) can inject adapters
    without the factory knowing about server internals.

    _spine_runner is deprecated — use _run_spine_fn for the inline requeue
    port, or pass a pre-built requeue_port to RecoveryAgent directly.
    """
    _validate_config(config)

    if _trip_repo is not None:
        trip_repo = _trip_repo
    else:
        trip_repo = TripStoreAdapter()

    if _audit_sink is not None:
        audit_sink = _audit_sink
    else:
        audit_sink = AuditStoreAdapter()

    coordinator = None
    if config.coordinator_backend == "sql":
        coordinator = SQLWorkCoordinator(lease_seconds=config.lease_seconds)
    elif config.coordinator_backend == "memory":
        coordinator = None  # AgentSupervisor uses InMemoryWorkCoordinator by default

    requeue_port = build_requeue_port(
        config.recovery_requeue_mode,
        spine_runner=_spine_runner,
        run_spine=_run_spine_fn,
    )
    recovery_agent = RecoveryAgent(
        audit_store=audit_sink,
        trip_repo=trip_repo,
        requeue_port=requeue_port,
    )

    supervisor = AgentSupervisor(
        registry=build_default_registry(),
        trip_repo=trip_repo,
        audit=audit_sink,
        interval_seconds=config.supervisor_interval_seconds,
        coordinator=coordinator,
    )

    return AgentRuntimeBundle(
        config=config,
        coordinator=coordinator,
        recovery_agent=recovery_agent,
        supervisor=supervisor,
    )


def build_agent_runtime(
    *,
    _trip_repo: Any = None,
    _audit_sink: Any = None,
    _spine_runner: Any = None,
    _run_spine_fn: Any = None,
) -> AgentRuntimeBundle:
    """Convenience: read env, build config, construct runtime, return bundle.

    This is the single call site server.py should use.
    """
    config = build_agent_runtime_config()
    return build_agent_runtime_from_config(
        config,
        _trip_repo=_trip_repo,
        _audit_sink=_audit_sink,
        _spine_runner=_spine_runner,
        _run_spine_fn=_run_spine_fn,
    )
