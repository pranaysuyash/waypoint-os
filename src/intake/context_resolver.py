"""Agentic destination context resolver — a real LLM second opinion.

Doctrine grounding (OPERATING_DOCTRINE.md §2 Truth taxonomy, §3 evidence
tiers): model output is a labeled hypothesis. It is never converted into a
definite assertion and never synthesized when the provider is unavailable —
an unconfigured/failed resolver degrades HONESTLY to the deterministic pass
(candidates + semi_open reaching the operator), with the reason recorded.

This is not a simulated extractor. It calls the canonical real LLM stack
(``src.llm`` — OpenAI/Gemini/local clients) and its outcomes carry full
provenance (provider, model, reasoning) so an operator can audit every
override. The trigger is deliberately narrow: deterministic semi_open
states — the collision/low-confidence class where whole-message context
adds signal a token-level gazetteer cannot have.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

from src.llm import LLMUnavailableError, get_default_client

logger = logging.getLogger(__name__)

# Kill switch: EXTRACTION_CONTEXT_RESOLVER=0 disables the agentic pass
# entirely (deterministic result stands untouched). Default is enabled —
# collision-triggered only, one small call per affected note.
_KILL_SWITCH_ENV = "EXTRACTION_CONTEXT_RESOLVER"

_VALID_STATUSES = {"definite", "semi_open", "open", "undecided"}

_RESPONSE_SCHEMA: Dict[str, Any] = {
    "destination_candidates": "array of strings (proper-noun place names; empty if the message names no destination)",
    "destination_status": "one of: definite, semi_open, open, undecided",
    "reasoning": "one short sentence citing the message context for the decision",
}


def resolver_enabled() -> bool:
    """Kill-switch check: enabled unless EXTRACTION_CONTEXT_RESOLVER=0."""
    return os.getenv(_KILL_SWITCH_ENV, "").strip().lower() != "0"


def validate_resolver_response(payload: Any) -> Optional[Dict[str, Any]]:
    """Pure validation of a provider response against the resolver contract.

    Returns the normalized outcome dict, or None when the payload does not
    satisfy the contract (wrong shape, unknown status, non-string entries).
    Kept pure so the contract is testable without any provider call.
    """
    if not isinstance(payload, dict):
        return None
    candidates = payload.get("destination_candidates")
    status = payload.get("destination_status")
    if not isinstance(candidates, list):
        return None
    if not all(isinstance(c, str) and c.strip() for c in candidates):
        return None
    if status not in _VALID_STATUSES:
        return None
    reasoning = payload.get("reasoning")
    return {
        "available": True,
        "candidates": [c.strip() for c in candidates],
        "status": status,
        "reasoning": reasoning.strip() if isinstance(reasoning, str) else "",
    }


def resolve_destination_from_context(
    raw_text: str,
    current_candidates: List[str],
    current_status: str,
) -> Dict[str, Any]:
    """Whole-message contextual read of the destination question.

    Calls the canonical real LLM stack (src.llm factory — OpenAI/Gemini/
    local per provider availability). Returns one of:

    - ``{"available": True, "candidates": [...], "status": ...,
       "reasoning": ..., "provider": ..., "model": ...}``
    - ``{"available": False, "reason": ...}`` — provider unconfigured,
      call failed, or response violated the contract. Callers must treat
      this as "deterministic result stands", never as a silent pass.
    """
    if not resolver_enabled():
        return {"available": False, "reason": "resolver_disabled_by_env"}

    try:
        client = get_default_client()
    except Exception as exc:
        return {"available": False, "reason": f"no_llm_provider: {exc}"}

    prompt = (
        "You are resolving whether a travel note names a travel destination. "
        "Read the WHOLE message. A word that is also a place name may be an "
        "ordinary word (e.g. 'reading', 'nice'); a place named in an "
        "explicit travel context is a destination. Current token-level "
        f"extraction guessed candidates={current_candidates!r} with "
        f"status={current_status!r}. Decide from full context.\n\n"
        f"MESSAGE:\n{raw_text}\n\n"
        "Return JSON with keys: destination_candidates (array of strings), "
        "destination_status (definite|semi_open|open|undecided), reasoning."
    )
    try:
        payload = client.decide(prompt, _RESPONSE_SCHEMA)
    except LLMUnavailableError as exc:
        return {"available": False, "reason": f"llm_unavailable: {exc}"}
    except Exception as exc:
        return {"available": False, "reason": f"llm_call_failed: {exc}"}

    outcome = validate_resolver_response(payload)
    if outcome is None:
        return {
            "available": False,
            "reason": f"resolver_response_violated_contract: {payload!r:.200}",
        }
    outcome["provider"] = type(client).__name__
    outcome["model"] = getattr(client, "model", "unknown")
    return outcome
