"""Decision-lane model policy — ADR-008 §8 (owner-ratified 2026-09-16).

Resolves WHICH model serves the hybrid decision engine's LLM rung. This is the
wiring for the owner-ratified policy recorded in
``Docs/architecture/adr/ADR-008-AGENCY_BOUNDARY_AND_AUTONOMY_RUNGS_2026-09-06.md``
§8, with final evidence in ``Docs/exploration/KDD_MODEL_COMPARISON_2026-09-12.md``
(2026-09-16 FINAL RESULTS, 284-model clean-rerun ladder).

Scope (ADR-008 §8): this module picks the model when the lane is ON. It does
NOT touch posture — envelopes keep ``USE_HYBRID_DECISION_ENGINE`` explicit per
ADR-008 §7 item 2; prod stays ``"0"`` until the X-09 PII-egress gate closes.

Policy:
    1. Primary:  openai/gpt-4.1-nano (F1 0.909, sev-agreement 0.92, $0.09/1M)
    2. Ratified equal: openai/gpt-5.4-nano ($0.28/1M; deprecation drop-in) —
       selectable via the override env (same credential, so it is an explicit
       ops choice, not an automatic rung).
    3. Fallback ladder (first rung with a present credential wins):
       HF router llama-3.1-8B:fastest → OpenRouter gpt-4.1-nano →
       OpenRouter llama-3.2-1b → local Ollama llama3.2:3b (terminal,
       credential-less).
    4. Blacklist: flagship-class model ids are barred from this lane
       (227/284 ladder arms graded < 0.40; champion class is ≤ 8B/nano in
       every venue tested). Overrides are rejected loudly and the ratified
       ladder applies.

Override: ``DECISION_LANE_MODEL="provider/model"`` (first slash splits
provider from model, matching the experiment harness convention — e.g.
``openai/gpt-5.4-nano``, ``local-ollama/llama3.2:3b``).
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)

OVERRIDE_ENV = "DECISION_LANE_MODEL"

# (provider, model, credential_env). Order IS the ratified fallback ladder.
# Model ids are the exact strings graded in the experiment harness — do not
# "normalize" them without re-grading.
MODEL_LADDER: Tuple[Tuple[str, str, Optional[str]], ...] = (
    ("openai", "gpt-4.1-nano", "OPENAI_API_KEY"),
    ("hf-router", "llama-3.1-8B:fastest", "HF_TOKEN"),
    ("openrouter", "openai/gpt-4.1-nano", "OPENROUTER_API_KEY"),
    ("openrouter", "meta-llama/llama-3.2-1b-instruct", "OPENROUTER_API_KEY"),
    ("local-ollama", "llama3.2:3b", None),
)

# ADR-008 §8 blacklist — the flagship tiers named in the ratification.
# Prefixes are matched against the normalized "provider/model" id.
BLACKLISTED_ID_PREFIXES: Tuple[str, ...] = (
    "deepseek/",
    "z-ai/",  # GLM family
    "moonshotai/",  # Kimi family
    "x-ai/",  # Grok family
    "google/gemini",  # Gemini tier (small gemma-class stays allowed)
    "mistralai/mistral-large",
    "qwen/qwen3-max",
    "anthropic/claude-opus",
    "anthropic/claude-sonnet",
)

# provider → credential env used when validating DECISION_LANE_MODEL overrides
_PROVIDER_CREDENTIAL_ENV: Dict[str, Optional[str]] = {
    "openai": "OPENAI_API_KEY",
    "hf-router": "HF_TOKEN",
    "openrouter": "OPENROUTER_API_KEY",
    "local-ollama": None,
    "gemini": "GEMINI_API_KEY",
    "local": None,
}


@dataclass(frozen=True, slots=True)
class LaneSelection:
    """The resolved decision-lane model plus why it was chosen."""

    provider: str
    model: str
    position: int  # 1-based ladder position; 0 for an env override
    reason: str  # "env-override" | "ratified-primary" | "fallback:<ENV>"
    credential_env: Optional[str]

    @property
    def model_id(self) -> str:
        return f"{self.provider}/{self.model}"


def is_blacklisted(model_id: str) -> bool:
    """True if a normalized model id is barred from the decision lane."""
    normalized = model_id.strip().lower()
    return any(normalized.startswith(p) for p in BLACKLISTED_ID_PREFIXES)


def _provider_for(credential_env: Optional[str]) -> str:
    """Inverse of the credential map, used for status reporting only."""
    for provider, env in _PROVIDER_CREDENTIAL_ENV.items():
        if env == credential_env:
            return provider
    return "unknown"


def resolve_decision_lane_model() -> Tuple[Optional[LaneSelection], Dict[str, object]]:
    """Resolve the decision-lane model per ADR-008 §8.

    Returns ``(selection, status)``. ``selection`` is None only if an explicit
    override was rejected AND every ladder rung's credential is absent — the
    terminal local-ollama rung is credential-less by design, so in practice a
    selection always exists.
    """
    status: Dict[str, object] = {
        "policy": "ADR-008 §8 (ratified 2026-09-16)",
        "primary": f"{MODEL_LADDER[0][0]}/{MODEL_LADDER[0][1]}",
        "override": os.environ.get(OVERRIDE_ENV, "").strip(),
        "override_rejected": None,
        "ladder_credentials": {
            f"{prov}/{model}": bool(cred is None or os.environ.get(cred))
            for prov, model, cred in MODEL_LADDER
        },
    }

    override = str(status["override"])
    if override:
        if "/" not in override:
            status["override_rejected"] = f"malformed (need provider/model): {override!r}"
            logger.warning(
                "decision lane: ignoring %s=%r — expected provider/model",
                OVERRIDE_ENV,
                override,
            )
        elif is_blacklisted(override):
            status["override_rejected"] = "blacklisted (ADR-008 §8 flagship bar)"
            logger.warning(
                "decision lane: ignoring %s=%r — flagship-class models are "
                "blacklisted for this lane (ADR-008 §8)",
                OVERRIDE_ENV,
                override,
            )
        else:
            provider, _, model = override.partition("/")
            cred_env = _PROVIDER_CREDENTIAL_ENV.get(provider.lower())
            if provider.lower() not in _PROVIDER_CREDENTIAL_ENV:
                status["override_rejected"] = f"unknown provider: {provider!r}"
                logger.warning(
                    "decision lane: ignoring %s=%r — unsupported provider",
                    OVERRIDE_ENV,
                    override,
                )
            elif cred_env is None or os.environ.get(cred_env):
                selection = LaneSelection(
                    provider=provider.lower(),
                    model=model,
                    position=0,
                    reason="env-override",
                    credential_env=cred_env,
                )
                status["resolved"] = selection.model_id
                status["resolved_reason"] = selection.reason
                return selection, status
            else:
                status["override_rejected"] = (
                    f"credential {cred_env} absent for override provider"
                )
                logger.warning(
                    "decision lane: %s=%r provider credential %s absent — "
                    "falling through to the ratified ladder",
                    OVERRIDE_ENV,
                    override,
                    cred_env,
                )

    for position, (provider, model, credential_env) in enumerate(MODEL_LADDER, start=1):
        if credential_env is None or os.environ.get(credential_env):
            selection = LaneSelection(
                provider=provider,
                model=model,
                position=position,
                reason=(
                    "ratified-primary"
                    if position == 1
                    else f"fallback:{credential_env or 'local'}"
                ),
                credential_env=credential_env,
            )
            status["resolved"] = selection.model_id
            status["resolved_position"] = position
            status["resolved_reason"] = selection.reason
            return selection, status

    status["resolved"] = None
    return None, status


def build_decision_lane_client() -> Tuple[Optional[object], Dict[str, object]]:
    """Build an LLM client for the resolved decision-lane model.

    Returns ``(client, status)``; ``client`` is None when the lane cannot be
    served (callers must degrade to the deterministic core and log loudly —
    ADR-008 §4.1 observability contract).
    """
    selection, status = resolve_decision_lane_model()
    if selection is None:
        return None, status

    provider, model = selection.provider, selection.model
    try:
        if provider == "openai":
            from src.llm import create_llm_client

            return create_llm_client(provider="openai", model=model), status
        if provider == "hf-router":
            from src.llm.openai_client import OpenAIClient

            # Reasoning-family models burn completion budget on reasoning;
            # the experiment harness used 4096 for the same reason.
            return (
                OpenAIClient(
                    model=model,
                    api_key=os.environ.get("HF_TOKEN", ""),
                    base_url=os.environ.get(
                        "HF_ROUTER_BASE_URL", "https://router.huggingface.co/v1"
                    ),
                    max_tokens=4096,
                ),
                status,
            )
        if provider == "openrouter":
            from src.llm.openai_client import OpenAIClient

            return (
                OpenAIClient(
                    model=model,
                    api_key=os.environ.get("OPENROUTER_API_KEY", ""),
                    base_url=os.environ.get(
                        "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
                    ),
                ),
                status,
            )
        if provider == "local-ollama":
            from src.llm.openai_client import OpenAIClient

            return (
                OpenAIClient(
                    model=model,
                    api_key="ollama",
                    base_url=os.environ.get(
                        "OLLAMA_BASE_URL", "http://127.0.0.1:11434/v1"
                    ),
                ),
                status,
            )
        # gemini / local via the shared factory (allowed by override; the
        # ratified ladder itself never selects them)
        from src.llm import create_llm_client

        return create_llm_client(provider=provider, model=model), status
    except (RuntimeError, ValueError, OSError) as exc:
        logger.error(
            "decision lane: failed to build client for %s: %s — "
            "deterministic core will serve",
            selection.model_id,
            exc,
        )
        status["build_error"] = str(exc)
        return None, status


def decision_lane_policy_status() -> Dict[str, object]:
    """Status payload for the startup rung log (ADR-008 §4.1 observability)."""
    _, status = resolve_decision_lane_model()
    return status
