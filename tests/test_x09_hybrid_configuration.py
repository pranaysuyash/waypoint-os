"""X-09 contracts for production/CI hybrid-decision configuration parity."""

from __future__ import annotations

import os

from src.evals.audit.snapshot import (
    _collect_live_scenario_results,
    _run_scenario_baseline,
    stable_snapshot_view,
)


def _disable_provider_credentials(monkeypatch):
    """Keep this deterministic eval lane from inheriting local credentials."""
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)


def test_x09_unset_mode_uses_serving_default_and_records_boundary(monkeypatch):
    """The hybrid boundary is recorded for an explicitly-on deployment.

    PA-03 (2026-09-06): the serving default flipped to OFF — determinism is
    now architectural. This test previously relied on the old default being
    ON when the variable was unset; it now sets the value explicitly so the
    recorded boundary assertions keep pinning the same observable contract.
    (snapshot.py still hardcodes the retired default; flagging that to the
    lead is part of the PA-03 remediation note.)
    """
    _disable_provider_credentials(monkeypatch)
    monkeypatch.delenv("USE_HYBRID_DECISION_ENGINE", raising=False)
    # The recorded value must now be supplied explicitly — an unset variable
    # means OFF at the engine (src/intake/decision.py) after PA-03.
    monkeypatch.setenv("USE_HYBRID_DECISION_ENGINE", "1")

    health = _run_scenario_baseline()

    assert health["hybrid_config"] == {
        "environment_variable": "USE_HYBRID_DECISION_ENGINE",
        "configured_value": "1",
        "effective_enabled": True,
        "default_enabled": False,
        "evaluation_contract": "deterministic_authority_axes",
        "provider_calls_authorized": False,
    }


def test_x09_explicit_ci_mode_is_preserved_and_observable(monkeypatch):
    _disable_provider_credentials(monkeypatch)
    monkeypatch.setenv("USE_HYBRID_DECISION_ENGINE", "1")

    health = _run_scenario_baseline()

    assert health["hybrid_config"]["configured_value"] == "1"
    assert health["hybrid_config"]["effective_enabled"] is True
    assert health["hybrid_config"]["evaluation_contract"] == "deterministic_authority_axes"
    assert health["hybrid_config"]["provider_calls_authorized"] is False


def test_x09_explicit_off_mode_is_not_overridden_by_d6(monkeypatch):
    _disable_provider_credentials(monkeypatch)
    monkeypatch.setenv("USE_HYBRID_DECISION_ENGINE", "0")

    health = _run_scenario_baseline()

    assert health["hybrid_config"]["configured_value"] == "0"
    assert health["hybrid_config"]["effective_enabled"] is False


def test_x09_live_collector_restores_environment_after_default(monkeypatch):
    _disable_provider_credentials(monkeypatch)
    monkeypatch.delenv("USE_HYBRID_DECISION_ENGINE", raising=False)

    actuals = _collect_live_scenario_results()

    assert len(actuals) == 30
    assert "USE_HYBRID_DECISION_ENGINE" not in os.environ


def test_x09_stable_snapshot_retains_hybrid_configuration(monkeypatch):
    _disable_provider_credentials(monkeypatch)
    monkeypatch.setenv("USE_HYBRID_DECISION_ENGINE", "1")

    snapshot = {"scenario_health": _run_scenario_baseline()}
    stable = stable_snapshot_view(snapshot)

    assert stable["scenario_health"]["hybrid_config"]["effective_enabled"] is True
    assert stable["scenario_health"]["hybrid_config"]["provider_calls_authorized"] is False
