"""Agentic destination context resolver — real-provider contract tests.

Doctrine grounding (OPERATING_DOCTRINE.md §2/§3): model output is a labeled
hypothesis (ASSUMED, provider/model provenance), never converted into a
definite assertion; an unconfigured or failing provider degrades HONESTLY to
the deterministic pass. These tests verify exactly that boundary:

- Tier 2 (targeted): kill-switch, unconfigured-provider honest outcome,
  and the pure response-contract validator (valid, malformed, unknown
  status, non-string candidates).
- Tier 5 (live external service): a REAL provider call through the
  canonical src.llm stack, asserted on the honesty contract (availability,
  provenance fields, valid status enum) — not on specific destination
  content, which is model-dependent. Skipped honestly when no provider key
  is configured; never faked.

The deterministic golden gate (tests/evals/test_d6_gate_snapshot.py) pins
the deterministic pass with EXTRACTION_CONTEXT_RESOLVER=0; the agentic pass
is owned by this module.
"""

import os

import pytest

os.environ.setdefault("RUNNING_TESTS", "1")

from src.intake import context_resolver


def test_kill_switch_disables_resolver(monkeypatch):
    monkeypatch.setenv("EXTRACTION_CONTEXT_RESOLVER", "0")
    assert context_resolver.resolver_enabled() is False


def test_resolver_enabled_by_default(monkeypatch):
    monkeypatch.delenv("EXTRACTION_CONTEXT_RESOLVER", raising=False)
    assert context_resolver.resolver_enabled() is True


def test_validate_accepts_contract_conforming_response():
    outcome = context_resolver.validate_resolver_response(
        {
            "destination_candidates": ["Reading"],
            "destination_status": "semi_open",
            "reasoning": "'reading' is a verb here, not the town",
        }
    )
    assert outcome is not None
    assert outcome["available"] is True
    assert outcome["candidates"] == ["Reading"]
    assert outcome["status"] == "semi_open"


@pytest.mark.parametrize(
    "payload",
    [
        None,
        "not a dict",
        {},
        {"destination_candidates": "Reading", "destination_status": "semi_open"},
        {"destination_candidates": [42], "destination_status": "semi_open"},
        {"destination_candidates": ["Japan"], "destination_status": "totally-sure"},
        {"destination_candidates": [], "destination_status": ""},
    ],
)
def test_validate_rejects_contract_violations(payload):
    assert context_resolver.validate_resolver_response(payload) is None


def test_unavailable_provider_degrades_honestly(monkeypatch):
    """No provider configured → available=False with the reason; the caller
    keeps the deterministic result. Never a synthesized destination."""
    from src.llm import LLMUnavailableError

    def _raise():
        raise LLMUnavailableError("no provider available")

    monkeypatch.delenv("EXTRACTION_CONTEXT_RESOLVER", raising=False)
    monkeypatch.setattr(context_resolver, "get_default_client", _raise)

    outcome = context_resolver.resolve_destination_from_context(
        "we are reading up on our options for the trip", ["Reading"], "semi_open"
    )
    assert outcome["available"] is False
    assert outcome["reason"].startswith("no_llm_provider")


def test_provider_call_failure_degrades_honestly(monkeypatch):
    """A failing provider call degrades honestly — no invented candidates."""

    class _FailingClient:
        model = "test-model"

        def decide(self, prompt, schema, temperature=None):
            raise RuntimeError("provider down")

    monkeypatch.delenv("EXTRACTION_CONTEXT_RESOLVER", raising=False)
    monkeypatch.setattr(context_resolver, "get_default_client", lambda: _FailingClient())

    outcome = context_resolver.resolve_destination_from_context(
        "party of 4 to japan", ["Japan"], "semi_open"
    )
    assert outcome["available"] is False
    assert outcome["reason"].startswith("llm_call_failed")


def test_contract_violating_response_is_rejected_not_trusted(monkeypatch):
    """A provider response that violates the contract is discarded with the
    reason carrying the offending payload — never partially trusted."""

    class _BadClient:
        model = "test-model"

        def decide(self, prompt, schema, temperature=None):
            return {"destination_candidates": "Japan", "destination_status": "definite"}

    monkeypatch.delenv("EXTRACTION_CONTEXT_RESOLVER", raising=False)
    monkeypatch.setattr(context_resolver, "get_default_client", lambda: _BadClient())

    outcome = context_resolver.resolve_destination_from_context(
        "party of 4 to japan", ["Japan"], "semi_open"
    )
    assert outcome["available"] is False
    assert outcome["reason"].startswith("resolver_response_violated_contract")


@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY") and not os.getenv("GEMINI_API_KEY"),
    reason="Tier-5 live-provider test: no LLM provider key configured "
    "(honest skip — the deterministic suites fully cover the pipeline)",
)
def test_live_provider_real_call_honesty_contract(monkeypatch):
    """REAL provider call through the canonical src.llm stack.

    Re-enables the resolver explicitly (conftest pins it off suite-wide).
    Asserts the honesty contract, not destination content: an available
    outcome must carry candidates list + valid status enum + provider/model
    provenance; an unavailable outcome must carry a reason. Either is
    honest; a contract violation is not.
    """
    monkeypatch.delenv("EXTRACTION_CONTEXT_RESOLVER", raising=False)
    outcome = context_resolver.resolve_destination_from_context(
        "we are reading up on our options for the trip", ["Reading"], "semi_open"
    )
    assert outcome.get("available") in (True, False)
    if outcome["available"] is True:
        assert isinstance(outcome["candidates"], list)
        assert all(isinstance(c, str) for c in outcome["candidates"])
        assert outcome["status"] in {"definite", "semi_open", "open", "undecided"}
        assert outcome["provider"]
        assert outcome["model"]
    else:
        assert outcome["reason"]
