"""
llm.openai_client — OpenAI API client implementation.

Fallback LLM provider for the hybrid decision engine.
Uses GPT-4o-mini for cost-effective decisions (₹0.30-₹1.50 per call).

Models supported:
- gpt-4o-mini: Fast, cost-effective (recommended for decisions)
- gpt-4o: Better reasoning, more expensive
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional

from spine_api.core.llm_egress import DecisionType, prepare_egress_payload

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from .base import BaseLLMClient, LLMUnavailableError, LLMResponseError


# OpenAI pricing in INR (approximate, per 1M tokens; 1 USD ≈ 83 INR)
# Standard tier, short context. Sources: developers.openai.com/api/docs/pricing
# (fetched 2026-09-11). Models not listed fall back to gpt-4o-mini pricing.
PRICING = {
    "gpt-3.5-turbo": {"input_per_million": 0.50 * 83, "output_per_million": 1.50 * 83},
    "gpt-4-turbo": {"input_per_million": 10.00 * 83, "output_per_million": 30.00 * 83},
    "gpt-4o": {
        "input_per_million": 2.50 * 83,   # ~₹207.5 per million
        "output_per_million": 10.00 * 83, # ~₹830 per million
    },
    "gpt-4o-mini": {
        "input_per_million": 0.15 * 83,   # ~₹12.5 per million tokens
        "output_per_million": 0.60 * 83,  # ~₹49.8 per million tokens
    },
    "gpt-4.1": {"input_per_million": 2.00 * 83, "output_per_million": 8.00 * 83},
    "gpt-4.1-mini": {"input_per_million": 0.40 * 83, "output_per_million": 1.60 * 83},
    "gpt-4.1-nano": {"input_per_million": 0.10 * 83, "output_per_million": 0.40 * 83},
    "gpt-5": {"input_per_million": 1.25 * 83, "output_per_million": 10.00 * 83},
    "gpt-5-mini": {"input_per_million": 0.25 * 83, "output_per_million": 2.00 * 83},
    "gpt-5-nano": {"input_per_million": 0.05 * 83, "output_per_million": 0.40 * 83},
    "gpt-5.1": {"input_per_million": 1.25 * 83, "output_per_million": 10.00 * 83},
    "gpt-5.2": {"input_per_million": 1.75 * 83, "output_per_million": 14.00 * 83},
    "gpt-5.4": {"input_per_million": 2.50 * 83, "output_per_million": 15.00 * 83},
    "gpt-5.4-mini": {"input_per_million": 0.75 * 83, "output_per_million": 4.50 * 83},
    "gpt-5.4-nano": {"input_per_million": 0.20 * 83, "output_per_million": 1.25 * 83},
    "gpt-5.5": {"input_per_million": 5.00 * 83, "output_per_million": 30.00 * 83},
    "gpt-5.6-luna": {"input_per_million": 0.20 * 83, "output_per_million": 1.20 * 83},
    "gpt-5.6-terra": {"input_per_million": 2.00 * 83, "output_per_million": 12.00 * 83},
    "gpt-5.6-sol": {"input_per_million": 4.00 * 83, "output_per_million": 20.00 * 83},
    "o3": {"input_per_million": 2.00 * 83, "output_per_million": 8.00 * 83},
    "o3-mini": {"input_per_million": 1.10 * 83, "output_per_million": 4.40 * 83},
    "o4-mini": {"input_per_million": 1.10 * 83, "output_per_million": 4.40 * 83},
    "gpt-6-astra": {"input_per_million": 10.00 * 83, "output_per_million": 50.00 * 83},
}


# Model families whose Chat Completions contract differs from the classic one.
# Reasoning models (gpt-5+, o-series) reject `max_tokens` (want
# `max_completion_tokens`) and any `temperature` other than 1. Legacy gpt-4
# (pre-turbo) rejects `response_format: json_object`.
_REASONING_MODEL_PREFIXES = ("gpt-5", "gpt-6", "o1", "o3", "o4")


def _is_reasoning_model(model: str) -> bool:
    return model.startswith(_REASONING_MODEL_PREFIXES)


def _supports_json_mode(model: str) -> bool:
    # Legacy gpt-4 (gpt-4, gpt-4-0613) rejects response_format json_object;
    # gpt-4-turbo, gpt-4o*, gpt-4.1*, gpt-3.5-turbo* and all newer support it.
    if model.startswith(("gpt-4-turbo", "gpt-4o", "gpt-4.1")):
        return True
    if model.startswith("gpt-4"):
        return False
    return True


class OpenAIClient(BaseLLMClient):
    """
    OpenAI API client implementation.

    Configure via environment variable:
        OPENAI_API_KEY=your_api_key_here

    Example:
        client = OpenAIClient(model="gpt-4o-mini")
        result = client.decide(
            prompt="Is this trip suitable for elderly travelers?",
            schema={"type": "object", "properties": {...}}
        )
    """

    # Default model
    DEFAULT_MODEL = "gpt-4o-mini"

    def __init__(
        self,
        model: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 1024,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        """
        Initialize the OpenAI client.

        Args:
            model: Model name (default: gpt-4o-mini)
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens in response
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            base_url: Custom base URL (for Azure or OpenAI-compatible APIs)
        """
        if not OPENAI_AVAILABLE:
            raise LLMUnavailableError(
                "openai package not installed. "
                "Install with: uv add --group llm openai"
            )

        model = model or self.DEFAULT_MODEL
        super().__init__(model, temperature, max_tokens)

        # Get API key from parameter or environment
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise LLMUnavailableError(
                "OPENAI_API_KEY not set. Set environment variable or pass api_key parameter."
            )

        # Initialize client
        try:
            self._client = OpenAI(
                api_key=self.api_key,
                base_url=base_url,
            )
        except (ValueError, TypeError) as e:
            raise LLMUnavailableError(f"Failed to initialize OpenAI client: {e}")

    def is_available(self) -> bool:
        """Check if the OpenAI client is available."""
        if not OPENAI_AVAILABLE:
            return False
        if not self.api_key:
            return False
        try:
            # Quick availability check
            return hasattr(self, "_client") and self._client is not None
        except AttributeError:
            return False

    def ping(self) -> bool:
        """Lightweight connectivity check — list models via the API."""
        if not self.is_available():
            return False
        try:
            self._client.models.list(limit=1)
            return True
        except (OSError, ValueError):
            return False

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
            LLMUnavailableError: If API call fails
            LLMResponseError: If response cannot be parsed
        """
        if not self.is_available():
            raise LLMUnavailableError("OpenAI client not available")

        # Build the prompt with JSON schema instruction
        full_prompt = self._build_prompt(prompt, schema)
        full_prompt = prepare_egress_payload(
            decision_type=DecisionType.EXTRACTION,
            content=full_prompt,
            provider="openai",
        )

        try:
            # Model-aware request params: reasoning models (gpt-5+/o-series)
            # require max_completion_tokens and reject temperature != 1;
            # legacy gpt-4 rejects response_format json_object.
            params: Dict[str, Any] = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a decision-making assistant. Always respond with valid JSON matching the provided schema.",
                    },
                    {
                        "role": "user",
                        "content": full_prompt,
                    },
                ],
            }
            if _is_reasoning_model(self.model):
                params["max_completion_tokens"] = self.max_tokens
            else:
                params["temperature"] = (
                    temperature if temperature is not None else self.temperature
                )
                params["max_tokens"] = self.max_tokens
                if _supports_json_mode(self.model):
                    params["response_format"] = {"type": "json_object"}
            response = self._client.chat.completions.create(**params)

            # Parse response
            response_text = response.choices[0].message.content
            if not response_text:
                raise LLMResponseError("Empty response from OpenAI")

            # Parse JSON
            try:
                decision = json.loads(response_text)
            except json.JSONDecodeError as e:
                raise LLMResponseError(f"Failed to parse JSON response: {e}\nResponse: {response_text}")

            return decision

        except (LLMUnavailableError, LLMResponseError):
            raise
        except (OSError, ValueError, TypeError, KeyError) as e:
            raise LLMUnavailableError(f"OpenAI API call failed: {e}")

    def _build_prompt(self, prompt: str, schema: Dict[str, Any]) -> str:
        """Build the full prompt with JSON schema instruction."""
        schema_str = json.dumps(schema, indent=2)

        return f"""{prompt}

You must respond with valid JSON matching this schema:
{schema_str}

Respond ONLY with the JSON object, no additional text."""

    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """
        Estimate the cost of an LLM call in INR.

        Args:
            prompt_tokens: Number of tokens in the prompt
            completion_tokens: Number of tokens in the response

        Returns:
            Estimated cost in INR
        """
        pricing = PRICING.get(self.model, PRICING["gpt-4o-mini"])

        input_cost = (prompt_tokens / 1_000_000) * pricing["input_per_million"]
        output_cost = (completion_tokens / 1_000_000) * pricing["output_per_million"]

        return input_cost + output_cost

    def count_tokens(self, text: str) -> int:
        """
        Count tokens using OpenAI's tokenizer.

        For now, use the default character-based estimate.
        OpenAI's tiktoken could be used for more accurate counting.
        """
        # Default estimate: ~4 characters per token
        return super().count_tokens(text)


def create_openai_client(
    model: Optional[str] = None,
    temperature: float = 0.3,
    max_tokens: int = 1024,
) -> OpenAIClient:
    """
    Factory function to create an OpenAI client.

    Reads configuration from environment variables by default.

    Environment variables:
        OPENAI_API_KEY: API key (required)
        OPENAI_MODEL: Model name (optional, defaults to gpt-4o-mini)

    Args:
        model: Override model from environment
        temperature: Sampling temperature
        max_tokens: Maximum tokens in response

    Returns:
        Configured OpenAIClient instance

    Raises:
        LLMUnavailableError: If client cannot be created
    """
    model = model or os.environ.get("OPENAI_MODEL", OpenAIClient.DEFAULT_MODEL)

    try:
        return OpenAIClient(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    except (ValueError, TypeError) as e:
        raise LLMUnavailableError(f"Failed to create OpenAI client: {e}")
