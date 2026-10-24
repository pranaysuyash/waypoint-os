"""
llm.base — Base LLM client interface.

Defines the contract that all LLM clients must implement.
"""

from __future__ import annotations

import hashlib
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

# Per-call forensics record (determinism audit 2026-10-21, recommendation 5).
#
# Every model-backed decision in the serving path is sampled (default
# temperature 0.3; reasoning models are always provider-sampled), so a
# decision cannot be replayed from the run ledger alone. This emits ONE
# structured line per successful call — provider, model, the temperature
# that was actually sent, content hashes, latency — so "same input, different
# output" is detectable after the fact and a decision can be correlated with
# the exact request that produced it.
#
# Privacy contract: hashes only. Prompt and response CONTENT are never logged
# here; the egress guard (prepare_egress_payload / _strip_pii_for_egress)
# runs before the call and this record must not re-leak what it stripped.
_CALL_LOGGER = logging.getLogger("llm.calls")


def content_sha256(text: Any) -> str:
    """Stable content hash for forensics; never raises on odd input."""
    try:
        raw = text if isinstance(text, (bytes, bytearray)) else str(text or "")
        if isinstance(raw, str):
            raw = raw.encode("utf-8", errors="replace")
        return hashlib.sha256(raw).hexdigest()
    except Exception:
        return "unhashable"


def record_llm_call(
    *,
    provider: str,
    model: str,
    prompt: Any,
    response_text: Any,
    temperature_requested: Optional[float],
    temperature_effective: Optional[float],
    latency_ms: Optional[float],
    client: Optional[Any] = None,
    cost_estimate_inr: Optional[float] = None,
) -> Dict[str, Any]:
    """Build and emit the per-call forensics record. Best-effort: never raises.

    ``temperature_effective`` is what the provider actually received —
    ``None`` when the provider controls sampling itself (reasoning models
    reject the parameter; Jev exposes no sampling knob). ``cost_estimate_inr``
    is a char-derived estimate (≈4 chars/token × provider rate) — honest
    naming: it is an ESTIMATE for accounting, never a billed figure. When
    ``client`` is given the record is also kept on ``client.last_call_record``
    so a caller can attach the hashes to its own ledger/telemetry.
    """
    record: Dict[str, Any] = {
        "provider": provider,
        "model": model,
        "temperature_requested": temperature_requested,
        "temperature_effective": temperature_effective,
        "prompt_sha256": content_sha256(prompt),
        "response_sha256": content_sha256(response_text),
        "prompt_chars": len(str(prompt or "")),
        "response_chars": len(str(response_text or "")),
        "latency_ms": round(latency_ms, 1) if isinstance(latency_ms, (int, float)) else None,
    }
    if cost_estimate_inr is not None:
        record["cost_estimate_inr"] = round(cost_estimate_inr, 6)
    try:
        _CALL_LOGGER.info(
            "llm_call provider=%s model=%s temp_requested=%s temp_effective=%s "
            "prompt_sha256=%s response_sha256=%s latency_ms=%s cost_estimate_inr=%s",
            record["provider"],
            record["model"],
            record["temperature_requested"],
            record["temperature_effective"],
            record["prompt_sha256"],
            record["response_sha256"],
            record["latency_ms"],
            record.get("cost_estimate_inr"),
            extra={"llm_call": record},
        )
    except Exception:
        pass
    if client is not None:
        try:
            setattr(client, "last_call_record", record)
        except Exception:
            pass
    return record


class BaseLLMClient(ABC):
    """
    Abstract base class for LLM clients.

    All LLM client implementations (Gemini, OpenAI, Local) must
    inherit from this class and implement the decide() method.
    """

    def __init__(
        self,
        model: str,
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ):
        """
        Initialize the LLM client.

        Args:
            model: Model name/identifier
            temperature: Sampling temperature (0-1, lower = more deterministic)
            max_tokens: Maximum tokens in response
        """
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    @abstractmethod
    def decide(
        self,
        prompt: str,
        schema: Dict[str, Any],
        temperature: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Generate a structured decision from a prompt.

        Args:
            prompt: The input prompt for the LLM
            schema: JSON schema defining expected output structure
            temperature: Override default temperature (optional)

        Returns:
            Dictionary matching the provided schema

        Raises:
            LLMError: If the LLM call fails
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the LLM client is available (API key configured, model loaded).

        Returns:
            True if the client can be used, False otherwise
        """
        pass

    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """
        Estimate the cost of an LLM call in INR.

        Args:
            prompt_tokens: Number of tokens in the prompt
            completion_tokens: Number of tokens in the response

        Returns:
            Estimated cost in INR
        """
        # Default implementation - subclasses should override
        return 0.0

    def ping(self) -> bool:
        """
        Lightweight connectivity check for the LLM provider.

        Returns True if the LLM API is reachable and responsive.
        Subclasses should override with a real light API call
        (e.g. token counting or a minimal completion).

        Returns:
            True if the LLM is reachable
        """
        return self.is_available()

    def count_tokens(self, text: str) -> int:
        """
        Estimate the number of tokens in a text string.

        Args:
            text: The text to count tokens for

        Returns:
            Estimated token count
        """
        # Rough estimate: ~4 characters per token
        return len(text) // 4


class LLMError(Exception):
    """Base exception for LLM-related errors."""

    pass


class LLMUnavailableError(LLMError):
    """Raised when the LLM client is not available (no API key, model not loaded)."""

    pass


class LLMResponseError(LLMError):
    """Raised when the LLM response cannot be parsed or is invalid."""

    pass
