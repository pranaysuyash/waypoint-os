"""Tests for the ADR-008 §8 decision-lane model policy wiring.

Covers: ratified default resolution, fallback-ladder ordering by credential
presence, DECISION_LANE_MODEL override (including the ratified-equal pick),
flagship blacklist rejection, client build, singleton injection in
src/intake/decision.py, and the startup rung-log status payload.
"""

from __future__ import annotations

import logging
from unittest.mock import patch

import pytest

from src.decision.model_policy import (
    MODEL_LADDER,
    OVERRIDE_ENV,
    build_decision_lane_client,
    decision_lane_policy_status,
    is_blacklisted,
    resolve_decision_lane_model,
)

_CRED_ENVS = ("OPENAI_API_KEY", "HF_TOKEN", "OPENROUTER_API_KEY")


@pytest.fixture(autouse=True)
def _clean_lane_env(monkeypatch):
    """Isolate every credential + override env the policy reads."""
    for env in (*_CRED_ENVS, OVERRIDE_ENV, "LLM_PROVIDER", "OPENAI_MODEL"):
        monkeypatch.delenv(env, raising=False)
    yield


class TestResolution:
    def test_default_resolves_ratified_primary(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk_test")
        selection, status = resolve_decision_lane_model()
        assert selection is not None
        assert (selection.provider, selection.model) == ("openai", "gpt-4.1-nano")
        assert selection.position == 1
        assert selection.reason == "ratified-primary"
        assert status["resolved"] == "openai/gpt-4.1-nano"

    def test_ladder_falls_through_absent_credentials(self, monkeypatch):
        monkeypatch.setenv("HF_TOKEN", "hf_test")
        selection, _ = resolve_decision_lane_model()
        assert selection is not None
        assert (selection.provider, selection.model) == (
            "hf-router",
            "llama-3.1-8B:fastest",
        )
        assert selection.position == 2
        assert selection.reason == "fallback:HF_TOKEN"

    def test_openrouter_rung_selected_only_when_openrouter_cred_only(self, monkeypatch):
        monkeypatch.setenv("OPENROUTER_API_KEY", "or_test")
        selection, _ = resolve_decision_lane_model()
        assert selection is not None
        assert selection.provider == "openrouter"
        assert selection.model == "openai/gpt-4.1-nano"
        assert selection.position == 3

    def test_terminal_local_rung_needs_no_credential(self):
        monkeypatch_none = None  # no creds set by fixture
        assert monkeypatch_none is None
        selection, status = resolve_decision_lane_model()
        assert selection is not None
        assert (selection.provider, selection.model) == ("local-ollama", "llama3.2:3b")
        assert selection.position == len(MODEL_LADDER)

    def test_override_selects_ratified_equal(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk_test")
        monkeypatch.setenv(OVERRIDE_ENV, "openai/gpt-5.4-nano")
        selection, status = resolve_decision_lane_model()
        assert selection is not None
        assert (selection.provider, selection.model) == ("openai", "gpt-5.4-nano")
        assert selection.position == 0
        assert selection.reason == "env-override"
        assert status["override_rejected"] is None

    def test_override_with_missing_credential_falls_to_ladder(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk_test")
        monkeypatch.setenv(OVERRIDE_ENV, "openrouter/openai/gpt-4.1-nano")
        selection, status = resolve_decision_lane_model()
        assert selection is not None
        assert selection.position == 1  # ratified primary
        assert status["override_rejected"] is not None
        assert "OPENROUTER_API_KEY" in str(status["override_rejected"])

    def test_malformed_override_rejected(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk_test")
        monkeypatch.setenv(OVERRIDE_ENV, "gpt-4.1-nano")
        selection, _ = resolve_decision_lane_model()
        assert selection is not None
        assert selection.position == 1


class TestBlacklist:
    def test_ratified_flagship_tiers_are_blacklisted(self):
        for model_id in (
            "deepseek/deepseek-v4-pro",
            "z-ai/glm-5.3",
            "moonshotai/kimi-k2.7",
            "x-ai/grok-4.6",
            "google/gemini-3.8-flash",
            "mistralai/mistral-large-2512",
            "qwen/qwen3-max",
            "anthropic/claude-sonnet-5",
        ):
            assert is_blacklisted(model_id), model_id

    def test_small_class_is_not_blacklisted(self):
        for model_id in (
            "openai/gpt-4.1-nano",
            "meta-llama/llama-3.2-1b-instruct",
            "google/gemma-3-4b-it",
            "tencent/hy-mt2-1.8b",
        ):
            assert not is_blacklisted(model_id), model_id

    def test_blacklisted_override_rejected_and_primary_serves(
        self, monkeypatch, caplog
    ):
        monkeypatch.setenv("OPENAI_API_KEY", "sk_test")
        monkeypatch.setenv(OVERRIDE_ENV, "z-ai/glm-5.3")
        with caplog.at_level(logging.WARNING):
            selection, status = resolve_decision_lane_model()
        assert selection is not None
        assert selection.model == "gpt-4.1-nano"
        assert status["override_rejected"] == "blacklisted (ADR-008 §8 flagship bar)"
        assert "blacklisted" in caplog.text

    def test_ratified_ladder_contains_no_blacklisted_models(self):
        for provider, model, _cred in MODEL_LADDER:
            assert not is_blacklisted(f"{provider}/{model}")


class TestClientBuild:
    def test_build_openai_primary(self):
        monkeypatch_patch = patch.dict("os.environ", {"OPENAI_API_KEY": "sk_test"})
        with monkeypatch_patch:
            client, status = build_decision_lane_client()
        assert client is not None
        assert client.model == "gpt-4.1-nano"
        assert status["resolved"] == "openai/gpt-4.1-nano"

    def test_build_ladder_fallback_to_hf(self, monkeypatch):
        monkeypatch.setenv("HF_TOKEN", "hf_test")
        client, status = build_decision_lane_client()
        assert client is not None
        assert client.model == "llama-3.1-8B:fastest"
        assert client.api_key == "hf_test"
        assert "huggingface.co" in str(client._client.base_url)


class TestSingletonInjection:
    def test_get_hybrid_engine_uses_policy_client(self, monkeypatch):
        from src.intake import decision as decision_mod

        monkeypatch.setenv("USE_HYBRID_DECISION_ENGINE", "1")
        monkeypatch.setenv("OPENAI_API_KEY", "sk_test")
        decision_mod._reset_hybrid_engine()
        try:
            engine = decision_mod._get_hybrid_engine()
            assert engine is not None
            assert engine.llm_client is not None
            assert engine.llm_client.model == "gpt-4.1-nano"
        finally:
            decision_mod._reset_hybrid_engine()

    def test_get_hybrid_engine_none_when_flag_off(self, monkeypatch):
        from src.intake import decision as decision_mod

        monkeypatch.setenv("USE_HYBRID_DECISION_ENGINE", "0")
        decision_mod._reset_hybrid_engine()
        try:
            assert decision_mod._get_hybrid_engine() is None
        finally:
            decision_mod._reset_hybrid_engine()


class TestRungLogStatus:
    def test_status_payload_shape(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk_test")
        status = decision_lane_policy_status()
        assert status["primary"] == "openai/gpt-4.1-nano"
        assert status["resolved"] == "openai/gpt-4.1-nano"
        ladder = status["ladder_credentials"]
        assert ladder["openai/gpt-4.1-nano"] is True
        assert ladder["hf-router/llama-3.1-8B:fastest"] is False
        assert ladder["local-ollama/llama3.2:3b"] is True  # credential-less rung
