"""
llm.gemini_client — Google Gemini API client implementation.

Primary LLM provider for the hybrid decision engine.
Uses Gemini Flash for fast, cost-effective decisions.

Models supported:
- gemini-2.0-flash: Fast, cost-effective (recommended for decisions)
- gemini-2.5-pro: Better reasoning, more expensive

Uses the google-genai SDK (successor to deprecated google-generativeai).
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional

try:
    from google import genai
    from google.genai import types as genai_types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

from .base import BaseLLMClient, LLMError, LLMUnavailableError, LLMResponseError


# Gemini pricing in INR (approximate)
# 1 USD ≈ 83 INR
PRICING = {
    "gemini-2.0-flash": {
        "input_per_million": 0.10 * 83,
        "output_per_million": 0.40 * 83,
    },
    "gemini-2.0-flash-lite": {
        "input_per_million": 0.075 * 83,
        "output_per_million": 0.30 * 83,
    },
    "gemini-2.5-pro": {
        "input_per_million": 1.25 * 83,
        "output_per_million": 10.00 * 83,
    },
    # Legacy model aliases (kept for backward compat)
    "gemini-1.5-flash": {
        "input_per_million": 0.075 * 83,
        "output_per_million": 0.30 * 83,
    },
    "gemini-1.5-pro": {
        "input_per_million": 1.25 * 83,
        "output_per_million": 5.00 * 83,
    },
}


class GeminiClient(BaseLLMClient):
    """
    Google Gemini API client implementation.

    Configure via environment variable:
        GEMINI_API_KEY=your_api_key_here

    Example:
        client = GeminiClient(model="gemini-2.0-flash")
        result = client.decide(
            prompt="Is this trip suitable for elderly travelers?",
            schema={"type": "object", "properties": {...}}
        )
    """

    DEFAULT_MODEL = "gemini-2.0-flash"

    def __init__(
        self,
        model: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 1024,
        api_key: Optional[str] = None,
    ):
        if not GENAI_AVAILABLE:
            raise LLMUnavailableError(
                "google-genai package not installed. "
                "Install with: uv add --group llm google-genai"
            )

        model = model or self.DEFAULT_MODEL
        super().__init__(model, temperature, max_tokens)

        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise LLMUnavailableError(
                "GEMINI_API_KEY not set. Set environment variable or pass api_key parameter."
            )

        try:
            self._client = genai.Client(api_key=self.api_key)
        except Exception as e:
            raise LLMUnavailableError(f"Failed to initialize Gemini client: {e}")

    def is_available(self) -> bool:
        if not GENAI_AVAILABLE:
            return False
        if not self.api_key:
            return False
        try:
            return hasattr(self, "_client") and self._client is not None
        except Exception:
            return False

    def ping(self) -> bool:
        """Lightweight connectivity check — counts tokens via the API."""
        if not self.is_available():
            return False
        try:
            self._client.models.count_tokens(
                model=self.model,
                contents="ping",
            )
            return True
        except Exception:
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
            raise LLMUnavailableError("Gemini client not available")

        full_prompt = self._build_prompt(prompt, schema)

        config = genai_types.GenerateContentConfig(
            temperature=temperature if temperature is not None else self.temperature,
            max_output_tokens=self.max_tokens,
            response_mime_type="application/json",
        )

        try:
            response = self._client.models.generate_content(
                model=self.model,
                contents=full_prompt,
                config=config,
            )

            response_text = response.text if hasattr(response, 'text') else None
            if not response_text:
                # Try extracting from candidates
                if response.candidates:
                    for part in response.candidates[0].content.parts:
                        if part.text:
                            response_text = part.text
                            break

            if not response_text:
                raise LLMResponseError("Empty response from Gemini")

            try:
                decision = json.loads(response_text)
            except json.JSONDecodeError as e:
                raise LLMResponseError(f"Failed to parse JSON response: {e}\nResponse: {response_text}")

            return decision

        except (LLMUnavailableError, LLMResponseError):
            raise
        except Exception as e:
            raise LLMUnavailableError(f"Gemini API call failed: {e}")

    def _build_prompt(self, prompt: str, schema: Dict[str, Any]) -> str:
        schema_str = json.dumps(schema, indent=2)
        return f"""{prompt}

You must respond with valid JSON matching this schema:
{schema_str}

Respond ONLY with the JSON object, no additional text."""

    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        pricing = PRICING.get(self.model, PRICING["gemini-2.0-flash"])
        input_cost = (prompt_tokens / 1_000_000) * pricing["input_per_million"]
        output_cost = (completion_tokens / 1_000_000) * pricing["output_per_million"]
        return input_cost + output_cost

    def count_tokens(self, text: str) -> int:
        try:
            response = self._client.models.count_tokens(
                model=self.model,
                contents=text,
            )
            return response.total_tokens
        except Exception:
            return super().count_tokens(text)


def create_gemini_client(
    model: Optional[str] = None,
    temperature: float = 0.3,
    max_tokens: int = 1024,
) -> GeminiClient:
    """
    Factory function to create a Gemini client.

    Environment variables:
        GEMINI_API_KEY: API key (required)
        GEMINI_MODEL: Model name (optional, defaults to gemini-2.0-flash)
    """
    model = model or os.environ.get("GEMINI_MODEL", GeminiClient.DEFAULT_MODEL)

    try:
        return GeminiClient(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    except Exception as e:
        raise LLMUnavailableError(f"Failed to create Gemini client: {e}")
