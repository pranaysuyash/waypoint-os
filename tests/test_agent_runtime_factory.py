"""Tests for the agent runtime config factory.

All env vars are read at call time, so tests can monkeypatch freely
without importlib.reload().  No tests in this file require PostgreSQL.
"""

from __future__ import annotations

import pytest

from src.agents.runtime import AgentSupervisor
from spine_api.services.agent_work_coordinator import SQLWorkCoordinator


class TestBuildAgentRuntimeConfig:
    """Env-var parsing and validation."""

    def test_default_config_is_local_memory_disabled(self):
        from spine_api.services.agent_runtime_factory import build_agent_runtime_config

        config = build_agent_runtime_config()

        assert config.deployment_mode == "local"
        assert config.coordinator_backend == "memory"
        assert config.recovery_requeue_mode == "disabled"
        assert config.lease_seconds == 60
        assert config.supervisor_interval_seconds == 300

    def test_sql_coordinator_env(self, monkeypatch):
        from spine_api.services.agent_runtime_factory import build_agent_runtime_config

        monkeypatch.setenv("AGENT_WORK_COORDINATOR", "sql")
        config = build_agent_runtime_config()

        assert config.coordinator_backend == "sql"

    def test_memory_coordinator_env(self, monkeypatch):
        from spine_api.services.agent_runtime_factory import build_agent_runtime_config

        monkeypatch.setenv("AGENT_WORK_COORDINATOR", "memory")
        config = build_agent_runtime_config()

        assert config.coordinator_backend == "memory"

    def test_tripstore_backend_sql_no_longer_forces_sql_coordinator(self, monkeypatch):
        from spine_api.services.agent_runtime_factory import build_agent_runtime_config

        monkeypatch.setenv("TRIPSTORE_BACKEND", "sql")
        config = build_agent_runtime_config()

        assert config.coordinator_backend == "memory"

    def test_deployment_mode_env(self, monkeypatch):
        from spine_api.services.agent_runtime_factory import build_agent_runtime_config

        monkeypatch.setenv("DEPLOYMENT_MODE", "production")
        config = build_agent_runtime_config()

        assert config.deployment_mode == "production"

    def test_recovery_requeue_mode_inline(self, monkeypatch):
        from spine_api.services.agent_runtime_factory import build_agent_runtime_config

        monkeypatch.setenv("AGENT_RECOVERY_REQUEUE_MODE", "inline")
        config = build_agent_runtime_config()

        assert config.recovery_requeue_mode == "inline"

    def test_invalid_coordinator_fails(self, monkeypatch):
        from spine_api.services.agent_runtime_factory import build_agent_runtime_config

        monkeypatch.setenv("AGENT_WORK_COORDINATOR", "unsupported")
        with pytest.raises(ValueError, match="AGENT_WORK_COORDINATOR"):
            build_agent_runtime_config()

    def test_invalid_deployment_mode_fails(self, monkeypatch):
        from spine_api.services.agent_runtime_factory import build_agent_runtime_config

        monkeypatch.setenv("DEPLOYMENT_MODE", "staging")
        with pytest.raises(ValueError, match="DEPLOYMENT_MODE"):
            build_agent_runtime_config()

    def test_invalid_recovery_requeue_mode_fails(self, monkeypatch):
        from spine_api.services.agent_runtime_factory import build_agent_runtime_config

        monkeypatch.setenv("AGENT_RECOVERY_REQUEUE_MODE", "sql_queue")
        with pytest.raises(ValueError, match="AGENT_RECOVERY_REQUEUE_MODE"):
            build_agent_runtime_config()

    def test_lease_seconds_custom(self, monkeypatch):
        from spine_api.services.agent_runtime_factory import build_agent_runtime_config

        monkeypatch.setenv("AGENT_WORK_LEASE_SECONDS", "120")
        config = build_agent_runtime_config()

        assert config.lease_seconds == 120

    def test_supervisor_interval_custom(self, monkeypatch):
        from spine_api.services.agent_runtime_factory import build_agent_runtime_config

        monkeypatch.setenv("AGENT_SUPERVISOR_INTERVAL_S", "60")
        config = build_agent_runtime_config()

        assert config.supervisor_interval_seconds == 60

    def test_invalid_coordinator_with_mocked_env(self, monkeypatch):
        from spine_api.services.agent_runtime_factory import build_agent_runtime_config

        monkeypatch.setenv("AGENT_WORK_COORDINATOR", "invalid")
        with pytest.raises(ValueError, match="AGENT_WORK_COORDINATOR"):
            build_agent_runtime_config()


class TestBuildAgentRuntimeFromConfig:
    """Object construction from a config."""

    def test_memory_coordinator_yields_no_sql_coordinator(self, monkeypatch):
        from spine_api.services.agent_runtime_factory import (
            AgentRuntimeConfig,
            build_agent_runtime_from_config,
        )

        config = AgentRuntimeConfig(coordinator_backend="memory")
        bundle = build_agent_runtime_from_config(config)

        assert bundle.coordinator is None  # supervisor uses InMemoryWorkCoordinator default

    def test_sql_coordinator_yields_sql_work_coordinator(self, monkeypatch):
        from spine_api.services.agent_runtime_factory import (
            AgentRuntimeConfig,
            build_agent_runtime_from_config,
        )

        config = AgentRuntimeConfig(coordinator_backend="sql", lease_seconds=60)
        bundle = build_agent_runtime_from_config(config)

        assert isinstance(bundle.coordinator, SQLWorkCoordinator)

    def test_default_config_behavior_local(self, monkeypatch):
        from spine_api.services.agent_runtime_factory import (
            AgentRuntimeConfig,
            build_agent_runtime_from_config,
        )

        config = AgentRuntimeConfig(deployment_mode="local")
        bundle = build_agent_runtime_from_config(config)

        assert bundle.config.deployment_mode == "local"
        assert isinstance(bundle.supervisor, AgentSupervisor)
        assert bundle.recovery_agent is not None

    def test_bundle_health_contains_config_and_supervisor(self, monkeypatch):
        from spine_api.services.agent_runtime_factory import (
            AgentRuntimeConfig,
            build_agent_runtime_from_config,
        )

        config = AgentRuntimeConfig(deployment_mode="test")
        bundle = build_agent_runtime_from_config(config)

        health = bundle.health()
        assert "config" in health
        assert health["config"]["deployment_mode"] == "test"
        assert "supervisor" in health
        assert "recovery_agent" in health

    def test_health_config_dict_format(self, monkeypatch):
        from spine_api.services.agent_runtime_factory import (
            AgentRuntimeConfig,
            build_agent_runtime_from_config,
            build_agent_runtime_config,
        )

        config = build_agent_runtime_config()
        d = config.to_dict()
        assert isinstance(d, dict)
        assert "deployment_mode" in d
        assert "coordinator_backend" in d
        assert "lease_seconds" in d
        assert "recovery_requeue_mode" in d
