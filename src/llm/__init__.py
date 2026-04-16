"""
llm — LLM client implementations for the hybrid decision engine.

This module provides multiple LLM backends:
- Gemini (primary): Fast, cost-effective API
- Local: Privacy-first offline inference
- OpenAI: Fallback API option

Usage:
    from llm import create_llm_client, get_default_client

    # Create client based on environment config
    client = get_default_client()

    # Or create specific client
    from llm import GeminiClient
    client = GeminiClient()
"""

from __future__ import annotations

from typing import Optional

from .base import (
    BaseLLMClient,
    LLMError,
    LLMUnavailableError,
    LLMResponseError,
)

from .gemini_client import (
    GeminiClient,
    create_gemini_client,
)

from .local_llm import (
    LocalLLMClient,
    create_local_llm_client,
)

from .openai_client import (
    OpenAIClient,
    create_openai_client,
)

import os


__all__ = [
    # Base classes
    "BaseLLMClient",
    "LLMError",
    "LLMUnavailableError",
    "LLMResponseError",
    # Clients
    "GeminiClient",
    "LocalLLMClient",
    "OpenAIClient",
    # Factory functions
    "create_gemini_client",
    "create_local_llm_client",
    "create_openai_client",
    "create_llm_client",
    "get_default_client",
]


def create_llm_client(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.3,
    max_tokens: int = 1024,
) -> BaseLLMClient:
    """
    Create an LLM client for the specified provider.

    Args:
        provider: LLM provider (gemini, openai, local).
                  Defaults to LLM_PROVIDER env var or "gemini".
        model: Model name (uses provider default if not specified)
        temperature: Sampling temperature (0-1)
        max_tokens: Maximum tokens in response

    Returns:
        Configured LLM client instance

    Raises:
        LLMUnavailableError: If client cannot be created

    Example:
        client = create_llm_client(provider="gemini")
        result = client.decide(prompt, schema)
    """
    provider = provider or os.environ.get("LLM_PROVIDER", "gemini").lower()

    if provider == "gemini":
        return create_gemini_client(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    elif provider == "openai":
        return create_openai_client(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    elif provider == "local":
        return create_local_llm_client(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    else:
        raise LLMUnavailableError(
            f"Unknown LLM provider: {provider}. "
            f"Choose from: gemini, openai, local"
        )


def get_default_client() -> BaseLLMClient:
    """
    Get the default LLM client based on environment configuration.

    Reads from LLM_PROVIDER environment variable.
    Falls back through providers in order: gemini → openai → local

    Returns:
        Configured LLM client instance

    Raises:
        LLMUnavailableError: If no configured provider is available

    Example:
        client = get_default_client()
        decision = client.decide(prompt, schema)
    """
    provider = os.environ.get("LLM_PROVIDER", "gemini").lower()

    try:
        return create_llm_client(provider=provider)
    except LLMUnavailableError as e:
        # Try fallback providers
        fallbacks = {
            "gemini": ["openai", "local"],
            "openai": ["gemini", "local"],
            "local": ["gemini", "openai"],
        }

        for fallback_provider in fallbacks.get(provider, []):
            try:
                return create_llm_client(provider=fallback_provider)
            except LLMUnavailableError:
                continue

        raise LLMUnavailableError(
            f"No LLM provider available. Tried: {provider}, {fallbacks.get(provider, [])}. "
            f"Please configure API keys or install dependencies."
        )


def is_any_llm_available() -> bool:
    """
    Check if any LLM provider is available.

    Returns:
        True if at least one provider can be initialized
    """
    for provider in ["gemini", "openai", "local"]:
        try:
            client = create_llm_client(provider=provider)
            if client.is_available():
                return True
        except LLMUnavailableError:
            continue

    return False
