#!/usr/bin/env python3
"""TypeSafe System One (Jev) client — calibrated-decision adapter for the
hybrid decision engine's LLM client contract.

Jev (jev-1.13.0) is a "System One Model": text state in, typed probabilistic
decisions out (noul / choice / score). It cannot generate text, so this
adapter maps the engine's JSON decision schema onto Jev primitives:

  - enum-string properties  -> Choice questions (criteria parsed from the
    engine prompt's own `- "low" risk: ...` definition lines when present,
    generic risk wording otherwise)
  - boolean properties      -> Noul questions (threshold 0.5)
  - string/int/array props  -> not mappable (Jev cannot generate); required
    string fields like `reasoning` are synthesized as deterministic
    provenance strings built from the actual Jev answers, never model prose.

Benchmark lane only (KDD G1 gate, expedition doc §5). Production wiring stays
blocked behind G2 (PII/DPA) — until then this client is exercised by the KDD
harness and eval tooling, not the serving path.

Pricing (docs.typesafe.ai/models, 2026-09-19): $0.042/MTok input, output
tokens free. Versioned model IDs are pinned deliberately — `jev-latest`
aliases move under tuned thresholds (jaggedness doc §cross-primitive).
"""

from __future__ import annotations

import logging
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, Optional

import httpx

from .base import record_llm_call

logger = logging.getLogger(__name__)

def _resolve_api_key(explicit_key: Optional[str] = None) -> str:
    if explicit_key:
        return explicit_key
    key = os.environ.get("TYPESAFE_API_KEY", "") or os.environ.get("JEV_API_KEY", "")
    if key:
        return key
    # Global Agent Control Plane & AUD-05: Local/CI runs must never fire live
    # external Jev calls by default. Only read fallback from .env/.env.local
    # when ENABLE_LIVE_JEV_SERVING is explicitly truthy.
    live_serving = os.environ.get("ENABLE_LIVE_JEV_SERVING", "").strip().lower()
    if live_serving not in ("1", "true", "yes"):
        return ""
    root = Path(__file__).resolve().parents[2]
    for filename in (".env.local", ".env"):
        env_file = root / filename
        if env_file.is_file():
            try:
                for line in env_file.read_text().splitlines():
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, _, v = line.partition("=")
                    k, v = k.strip(), v.strip().strip("'\"")
                    if k in ("TYPESAFE_API_KEY", "JEV_API_KEY") and v:
                        return v
            except Exception:
                pass
    return ""

# docs.typesafe.ai/models (2026-09-19): $42 per billion input tokens,
# output "too cheap to meter" (free). 1 USD ≈ 83 INR, matching the
# convention in openai_client.py pricing tables.
_INPUT_USD_PER_MTOK = 0.042
_USD_TO_INR = 83.0

_DEFAULT_BASE_URL = "https://api.typesafe.ai/v1"
_DEFAULT_MODEL = "jev-1.13.0"

_NOUL_YES_THRESHOLD = 0.5

# Prompt bullets the engine prompt template emits, e.g.
# `- "low" risk: Plenty of time for visa processing` or
# `- "PROCEED": The destination and at least timing...` — parsed so Choice
# criteria mirror what the prompt defined.
_CRITERIA_BULLET_RE = re.compile(
    r'-\s*"([A-Za-z0-9_]+)"(?:\s*risk)?:\s*([^\n\r"]+)'
)

# Generic criteria when the prompt carries no per-level definitions
# (composition_risk, budget_feasibility risk_level).
_GENERIC_RISK_CRITERIA = {
    "low": "No significant risk present in the described travel situation",
    "medium": "Some concerns are present but they are manageable",
    "high": "Significant risk that warrants action or an alternative plan",
}

_QUESTION_INSTRUCTIONS = {
    "risk_level": (
        "Given the travel context in this message, what risk level should "
        "the assessment assign?"
    ),
    "feasible": (
        "Given the travel context in this message, is the stated budget "
        "feasible for this trip?"
    ),
}


def _strip_pii_for_egress(text: str) -> str:
    try:
        from spine_api.core.llm_egress import strip_pii
        cleaned, _ = strip_pii(text)
        return cleaned
    except Exception:
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL_REDACTED]', text)
        text = re.sub(r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}', '[PHONE_REDACTED]', text)
        return text


def _delimit_prompt(text: str) -> str:
    try:
        from spine_api.core.llm_egress import add_prompt_delimiters
        return add_prompt_delimiters(text)
    except Exception:
        return f"=== BEGIN USER CONTEXT ===\n{text}\n=== END USER CONTEXT ==="


class TypesafeJevClient:
    """Duck-typed hybrid-engine LLM client backed by POST /v1/systemone.

    Satisfies the same surface the harness/engine expect from an LLM client:
    ``model`` attribute, ``is_available()``, ``count_tokens()``,
    ``estimate_cost(prompt_tokens, completion_tokens)`` and
    ``decide(prompt, schema, temperature=None) -> dict``.
    """

    def __init__(
        self,
        model: str = _DEFAULT_MODEL,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout_s: float = 30.0,
        max_retries: int = 3,
    ):
        self.model = model
        self._api_key = _resolve_api_key(api_key)
        self._base_url = (base_url or os.environ.get(
            "TYPESAFE_BASE_URL", _DEFAULT_BASE_URL
        )).rstrip("/")
        self._timeout_s = timeout_s
        self._max_retries = max_retries

    def is_available(self) -> bool:
        return bool(self._api_key)

    def count_tokens(self, text: str) -> int:
        """Rough estimate; Jev charges input tokens only, and the engine uses
        this purely for cost estimation. 4 chars/token is the same heuristic
        the other clients apply to non-tiktoken text."""
        return max(1, len(text) // 4)

    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        usd = prompt_tokens * _INPUT_USD_PER_MTOK / 1_000_000
        return usd * _USD_TO_INR

    def decide(
        self,
        prompt: str,
        schema: Dict[str, Any],
        temperature: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Map the decision schema onto Jev questions and return a decision
        dict shaped like what the generative lanes return (risk_level /
        feasible keys filled from typed answers; reasoning = provenance)."""
        questions: Dict[str, Dict[str, Any]] = {}
        mapping: Dict[str, str] = {}  # schema property -> question key

        props = (schema or {}).get("properties", {}) or {}
        parsed_criteria = self._criteria_from_prompt(prompt)
        for prop, spec in props.items():
            if not isinstance(spec, dict):
                continue
            question_instructions = (
                spec.get("instructions")
                or spec.get("question")
                or (schema or {}).get("instructions")
                or (schema or {}).get("question")
                or _QUESTION_INSTRUCTIONS.get(
                    prop,
                    f"Given the travel context in this message, evaluate: {prop}",
                )
            )
            if spec.get("type") == "string" and "enum" in spec:
                qkey = f"q_{prop}"
                spec_criteria = spec.get("criteria", {}) or {}
                choice_criteria: Dict[str, str] = {}
                for choice in spec["enum"]:
                    if choice in spec_criteria:
                        choice_criteria[choice] = spec_criteria[choice]
                    elif choice in parsed_criteria:
                        choice_criteria[choice] = parsed_criteria[choice]
                    elif choice in _GENERIC_RISK_CRITERIA:
                        choice_criteria[choice] = _GENERIC_RISK_CRITERIA[choice]
                    else:
                        # Meaningful fallback description if prompt did not define it
                        choice_criteria[choice] = (
                            f"The context strongly indicates {choice.replace('_', ' ').lower()} "
                            f"for {prop.replace('_', ' ')}."
                        )

                questions[qkey] = {
                    "type": "choice",
                    "instructions": question_instructions,
                    "criteria": choice_criteria,
                }
                mapping[prop] = qkey
            elif spec.get("type") == "boolean":
                qkey = f"q_{prop}"
                questions[qkey] = {
                    "type": "noul",
                    "instructions": question_instructions,
                }
                mapping[prop] = qkey
            # string/int/array properties are skipped: Jev cannot generate
            # them, and the engine's consumers read only the typed fields.

        if not questions:
            # Nothing in this schema Jev can answer — fail loudly so the
            # engine's fallback path records an abstention instead of a
            # silent empty decision.
            raise ValueError(
                "TypesafeJevClient.decide: schema has no enum/boolean "
                "properties to map onto Jev primitives"
            )

        response = self._post(payload={
            "state": prompt,
            "model": self.model,
            "questions": questions,
        })

        answers = response.get("answers", {})
        decision: Dict[str, Any] = {}
        provenance: list[str] = []
        confidences: list[float] = []
        for prop, qkey in mapping.items():
            answer = answers.get(qkey, {})
            if answer.get("type") == "choice" and "choice" in answer:
                choice = answer["choice"]
                decision[prop] = choice
                probs = answer.get("probabilities", {}) or {}
                confidence = answer.get("confidence")
                decision.setdefault("jev_probabilities", {})[prop] = probs
                if confidence is not None:
                    decision.setdefault("jev_confidences", {})[prop] = confidence
                    confidences.append(float(confidence))
                provenance.append(
                    f"{prop}={choice} (p={probs.get(choice)}, conf={confidence})"
                )
            elif answer.get("type") == "noul" and "noul" in answer:
                noul = float(answer["noul"])
                decision[prop] = noul >= _NOUL_YES_THRESHOLD
                decision.setdefault("jev_nouls", {})[prop] = noul
                conf = answer.get("confidence")
                if conf is not None:
                    decision.setdefault("jev_confidences", {})[prop] = conf
                    confidences.append(float(conf))
                provenance.append(f"{prop}={decision[prop]} (noul={noul})")

        if confidences:
            decision["jev_confidence"] = min(confidences)

        decision["reasoning"] = "[jev] " + ("; ".join(provenance) if provenance else "no mapped answers")
        decision["jev_model"] = response.get("model", self.model)
        return decision

    @staticmethod
    def _criteria_from_prompt(prompt: str) -> Dict[str, str]:
        return {
            level: description.strip().rstrip(".")
            for level, description in _CRITERIA_BULLET_RE.findall(prompt)
        }

    def raw_query(self, state: str, questions: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Execute a raw System One query with arbitrary questions (choice, noul, score)."""
        return self._post(payload={
            "state": state,
            "model": self.model,
            "questions": questions,
        })

    def _post(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if isinstance(payload.get("state"), str):
            payload = dict(payload)
            payload["state"] = _delimit_prompt(_strip_pii_for_egress(payload["state"]))

        url = f"{self._base_url}/systemone"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        last_error: Optional[Exception] = None
        for attempt in range(self._max_retries + 1):
            try:
                started = time.perf_counter()
                with httpx.Client(timeout=self._timeout_s) as client:
                    response = client.post(url, json=payload, headers=headers)
                latency_ms = (time.perf_counter() - started) * 1000.0
                if response.status_code == 429 or response.status_code >= 500:
                    last_error = RuntimeError(
                        f"typesafe: transient HTTP {response.status_code}: "
                        f"{response.text[:200]}"
                    )
                elif response.status_code == 200:
                    # Jev (System One) exposes no sampling knob — calibrated
                    # primitives, provider-controlled — so temperature is
                    # recorded as None, not as a number we never sent.
                    record_llm_call(
                        provider="typesafe",
                        model=str(payload.get("model") or self.model),
                        prompt=payload.get("state"),
                        response_text=response.text,
                        temperature_requested=None,
                        temperature_effective=None,
                        latency_ms=latency_ms,
                        client=self,
                    )
                    return response.json()
                else:
                    raise RuntimeError(
                        f"typesafe: HTTP {response.status_code}: "
                        f"{response.text[:300]}"
                    )
            except httpx.HTTPError as exc:
                last_error = exc

            if attempt < self._max_retries:
                backoff = 0.5 * (2 ** attempt)
                logger.warning(
                    "typesafe request retry %d/%d after %.1fs (%s)",
                    attempt + 1, self._max_retries, backoff, last_error,
                )
                time.sleep(backoff)

        raise RuntimeError(f"typesafe: request failed after retries: {last_error}")
