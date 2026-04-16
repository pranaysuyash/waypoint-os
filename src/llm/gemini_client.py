"""
llm.gemini_client — Google Gemini API client implementation.

Primary LLM provider for the hybrid decision engine.
Uses Gemini Flash for fast, cost-effective decisions (₹0.10-₹0.50 per call).

Models supported:
- gemini-1.5-flash: Fast, cost-effective (recommended for decisions)
- gemini-1.5-pro: Better reasoning, more expensive
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional

try:
    import google.generativeai as genai
    from google.generativeai.types import GenerationConfig
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

from .base import BaseLLMClient, LLMError, LLMUnavailableError, LLMResponseError


# Gemini pricing in INR (approximate, as of 2024)
# 1 USD ≈ 83 INR
PRICING = {
    "gemini-1.5-flash": {
        "input_per_million": 0.075 * 83,  # ~₹6.2 per million tokens
        "output_per_million": 0.30 * 83,  # ~₹24.9 per million tokens
    },
    "gemini-1.5-pro": {
        "input_per_million": 1.25 * 83,   # ~₹103.8 per million
        "output_per_million": 5.00 * 83,  # ~₹415 per million
    },
}


class GeminiClient(BaseLLMClient):
    """
    Google Gemini API client implementation.

    Configure via environment variable:
        GEMINI_API_KEY=your_api_key_here

    Example:
        client = GeminiClient(model="gemini-1.5-flash")
        result = client.decide(
            prompt="Is this trip suitable for elderly travelers?",
            schema={"type": "object", "properties": {...}}
        )
    """

    # Default model
    DEFAULT_MODEL = "gemini-1.5-flash"

    def __init__(
        self,
        model: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 1024,
        api_key: Optional[str] = None,
    ):
        """
        Initialize the Gemini client.

        Args:
            model: Model name (default: gemini-1.5-flash)
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens in response
            api_key: Gemini API key (defaults to GEMINI_API_KEY env var)
        """
        if not GENAI_AVAILABLE:
            raise LLMUnavailableError(
                "google-generativeai package not installed. "
                "Install with: uv add --group llm google-generativeai"
            )

        model = model or self.DEFAULT_MODEL
        super().__init__(model, temperature, max_tokens)

        # Get API key from parameter or environment
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise LLMUnavailableError(
                "GEMINI_API_KEY not set. Set environment variable or pass api_key parameter."
            )

        # Configure the API
        try:
            genai.configure(api_key=self.api_key)
            self._client = genai.GenerativeModel(model)
        except Exception as e:
            raise LLMUnavailableError(f"Failed to initialize Gemini client: {e}")

    def is_available(self) -> bool:
        """Check if the Gemini client is available."""
        if not GENAI_AVAILABLE:
            return False
        if not self.api_key:
            return False
        try:
            # Quick availability check
            return hasattr(self, "_client") and self._client is not None
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

        # Build the prompt with JSON schema instruction
        full_prompt = self._build_prompt(prompt, schema)

        # Configure generation
        config = GenerationConfig(
            temperature=temperature if temperature is not None else self.temperature,
            max_output_tokens=self.max_tokens,
            response_mime_type="application/json",  # Request JSON response
        )

        try:
            # Call the API
            response = self._client.generate_content(
                full_prompt,
                generation_config=config,
            )

            # Parse response
            response_text = response.text
            if not response_text:
                raise LLMResponseError("Empty response from Gemini")

            # Parse JSON
            try:
                decision = json.loads(response_text)
            except json.JSONDecodeError as e:
                raise LLMResponseError(f"Failed to parse JSON response: {e}\nResponse: {response_text}")

            return decision

        except genai.types.BlockedPromptException as e:
            raise LLMResponseError(f"Prompt blocked by Gemini safety filters: {e}")
        except genai.types.StopCandidateException as e:
            raise LLMResponseError(f"Generation stopped: {e}")
        except Exception as e:
            if isinstance(e, (LLMUnavailableError, LLMResponseError)):
                raise
            raise LLMUnavailableError(f"Gemini API call failed: {e}")

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
        pricing = PRICING.get(self.model, PRICING["gemini-1.5-flash"])

        input_cost = (prompt_tokens / 1_000_000) * pricing["input_per_million"]
        output_cost = (completion_tokens / 1_000_000) * pricing["output_per_million"]

        return input_cost + output_cost

    def count_tokens(self, text: str) -> int:
        """
        Count tokens using Gemini's tokenizer.

        More accurate than the default character-based estimate.
        """
        try:
            # Use genai's token counting if available
            return genai.count_tokens(self._client, text).total_tokens
        except Exception:
            # Fallback to character-based estimate
            return super().count_tokens(text)


def create_gemini_client(
    model: Optional[str] = None,
    temperature: float = 0.3,
    max_tokens: int = 1024,
) -> GeminiClient:
    """
    Factory function to create a Gemini client.

    Reads configuration from environment variables by default.

    Environment variables:
        GEMINI_API_KEY: API key (required)
        GEMINI_MODEL: Model name (optional, defaults to gemini-1.5-flash)

    Args:
        model: Override model from environment
        temperature: Sampling temperature
        max_tokens: Maximum tokens in response

    Returns:
        Configured GeminiClient instance

    Raises:
        LLMUnavailableError: If client cannot be created
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
