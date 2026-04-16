"""
llm.base — Base LLM client interface.

Defines the contract that all LLM clients must implement.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


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
