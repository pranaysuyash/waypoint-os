"""
tests.test_llm_clients — Unit tests for LLM client implementations.

Tests for Gemini, OpenAI, and Local LLM clients.
"""

import json
import os
import pytest

from src.llm.base import (
    BaseLLMClient,
    LLMError,
    LLMUnavailableError,
    LLMResponseError,
)
from src.llm.gemini_client import GeminiClient, create_gemini_client
from src.llm.openai_client import OpenAIClient, create_openai_client
from src.llm.local_llm import LocalLLMClient, create_local_llm_client


class MockLLMClient(BaseLLMClient):
    """Mock LLM client for testing."""

    def __init__(self, model="mock-model", temperature=0.3, max_tokens=1024):
        super().__init__(model, temperature, max_tokens)
        self._available = True
        self._decisions = {}

    def set_available(self, available: bool):
        """Set availability status."""
        self._available = available

    def set_decision(self, prompt: str, decision: dict):
        """Set a mock decision for a prompt."""
        self._decisions[prompt] = decision

    def decide(self, prompt: str, schema: dict, temperature: float = None) -> dict:
        """Return mock decision."""
        if not self.is_available():
            raise LLMUnavailableError("Mock client not available")

        if prompt in self._decisions:
            return self._decisions[prompt]

        # Return a default mock decision
        return {"result": "mock_decision"}

    def is_available(self) -> bool:
        """Check availability."""
        return self._available


class TestBaseLLMClient:
    """Tests for BaseLLMClient abstract class."""

    def test_initialization(self):
        """Test client initialization."""
        client = MockLLMClient(model="test-model", temperature=0.5, max_tokens=2048)

        assert client.model == "test-model"
        assert client.temperature == 0.5
        assert client.max_tokens == 2048

    def test_estimate_cost_default(self):
        """Test default cost estimation."""
        client = MockLLMClient()
        cost = client.estimate_cost(1000, 500)
        assert cost == 0.0

    def test_count_tokens_default(self):
        """Test default token counting."""
        client = MockLLMClient()
        count = client.count_tokens("This is a test text with some words")
        # Rough estimate: ~4 chars per token
        assert count > 0


class TestGeminiClient:
    """Tests for GeminiClient."""

    def test_create_without_api_key(self, monkeypatch):
        """Test that creating client without API key raises error."""
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)

        with pytest.raises(LLMUnavailableError, match="GEMINI_API_KEY not set"):
            GeminiClient()

    def test_create_with_api_key(self, monkeypatch):
        """Test creating client with API key."""
        monkeypatch.setenv("GEMINI_API_KEY", "test_key")

        # Will fail if google-generativeai not installed
        try:
            client = GeminiClient()
            assert client.model == "gemini-1.5-flash"
        except LLMUnavailableError as e:
            # Expected if package not installed
            assert "google-generativeai" in str(e)

    def test_estimate_cost(self):
        """Test cost estimation for Gemini."""
        try:
            client = GeminiClient(api_key="test")
        except LLMUnavailableError:
            pytest.skip("google-generativeai not installed")

        cost = client.estimate_cost(1000, 500)

        # gemini-1.5-flash: ~₹6.2 per million input, ~₹24.9 per million output
        # Expected: (1000/1M * 6.2) + (500/1M * 24.9) ≈ ₹0.0187
        assert cost > 0
        assert cost < 1  # Should be very small for 1500 tokens

    def test_estimate_cost_pro_model(self):
        """Test cost estimation for Gemini Pro."""
        try:
            client = GeminiClient(model="gemini-1.5-pro", api_key="test")
        except LLMUnavailableError:
            pytest.skip("google-generativeai not installed")

        cost = client.estimate_cost(1000, 500)

        # gemini-1.5-pro is more expensive than flash
        flash_client = GeminiClient(model="gemini-1.5-flash", api_key="test")
        flash_cost = flash_client.estimate_cost(1000, 500)

        assert cost > flash_cost


class TestOpenAIClient:
    """Tests for OpenAIClient."""

    def test_create_without_api_key(self, monkeypatch):
        """Test that creating client without API key raises error."""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        with pytest.raises(LLMUnavailableError, match="OPENAI_API_KEY not set"):
            OpenAIClient()

    def test_create_with_api_key(self, monkeypatch):
        """Test creating client with API key."""
        monkeypatch.setenv("OPENAI_API_KEY", "test_key")

        try:
            client = OpenAIClient()
            assert client.model == "gpt-4o-mini"
        except LLMUnavailableError as e:
            # Expected if package not installed
            assert "openai" in str(e)

    def test_estimate_cost(self):
        """Test cost estimation for OpenAI."""
        try:
            client = OpenAIClient(api_key="test")
        except LLMUnavailableError:
            pytest.skip("openai not installed")

        cost = client.estimate_cost(1000, 500)

        # gpt-4o-mini: ~₹12.5 per million input, ~₹49.8 per million output
        # Expected: (1000/1M * 12.5) + (500/1M * 49.8) ≈ ₹0.0374
        assert cost > 0
        assert cost < 1  # Should be very small for 1500 tokens

    def test_estimate_cost_gpt4o(self):
        """Test cost estimation for GPT-4o."""
        try:
            client = OpenAIClient(model="gpt-4o", api_key="test")
        except LLMUnavailableError:
            pytest.skip("openai not installed")

        cost = client.estimate_cost(1000, 500)

        # gpt-4o is more expensive than gpt-4o-mini
        mini_client = OpenAIClient(model="gpt-4o-mini", api_key="test")
        mini_cost = mini_client.estimate_cost(1000, 500)

        assert cost > mini_cost


class TestLocalLLMClient:
    """Tests for LocalLLMClient."""

    def test_create(self):
        """Test creating local LLM client."""
        try:
            client = LocalLLMClient()
            assert client.model == "microsoft/phi-3-mini-4k-instruct"
        except LLMUnavailableError as e:
            # Expected if transformers not installed
            assert "transformers" in str(e)

    def test_estimate_cost(self):
        """Test cost estimation for local LLM (should be near zero)."""
        try:
            client = LocalLLMClient()
        except LLMUnavailableError:
            pytest.skip("transformers not installed")

        cost = client.estimate_cost(1000, 500)

        # Local LLM has nominal cost (~₹0.01 per 1000 tokens)
        assert cost >= 0
        assert cost < 1  # Should be very small

    def test_model_can_be_unloaded(self):
        """Test that model can be unloaded."""
        try:
            client = LocalLLMClient()
        except LLMUnavailableError:
            pytest.skip("transformers not installed")

        # Unload should not raise an error
        client.unload()
        assert not client._loaded


class TestFactoryFunctions:
    """Tests for factory functions."""

    def test_create_gemini_client_from_env(self, monkeypatch):
        """Test creating Gemini client from environment."""
        monkeypatch.setenv("GEMINI_API_KEY", "test_key")
        monkeypatch.setenv("GEMINI_MODEL", "gemini-1.5-pro")

        try:
            client = create_gemini_client()
            assert client.model == "gemini-1.5-pro"
        except LLMUnavailableError:
            pytest.skip("google-generativeai not installed")

    def test_create_openai_client_from_env(self, monkeypatch):
        """Test creating OpenAI client from environment."""
        monkeypatch.setenv("OPENAI_API_KEY", "test_key")
        monkeypatch.setenv("OPENAI_MODEL", "gpt-4o")

        try:
            client = create_openai_client()
            assert client.model == "gpt-4o"
        except LLMUnavailableError:
            pytest.skip("openai not installed")

    def test_create_local_llm_client_from_env(self, monkeypatch):
        """Test creating local LLM client from environment."""
        monkeypatch.setenv("LOCAL_LLM_MODEL", "custom-model")
        monkeypatch.setenv("LOCAL_LLM_MAX_TOKENS", "512")

        try:
            client = create_local_llm_client()
            assert client.model == "custom-model"
            assert client.max_tokens == 512
        except LLMUnavailableError:
            pytest.skip("transformers not installed")


class TestLLMDecide:
    """Integration tests for LLM decide method (require API keys)."""

    @pytest.mark.skipif(
        not os.environ.get("GEMINI_API_KEY"),
        reason="GEMINI_API_KEY not set"
    )
    def test_gemini_decide(self):
        """Test actual Gemini API call."""
        client = GeminiClient()

        result = client.decide(
            prompt="Is Paris suitable for elderly travelers?",
            schema={
                "type": "object",
                "properties": {
                    "suitable": {"type": "boolean"},
                    "reason": {"type": "string"},
                },
                "required": ["suitable", "reason"],
            },
        )

        assert "suitable" in result
        assert "reason" in result
        assert isinstance(result["suitable"], bool)

    @pytest.mark.skipif(
        not os.environ.get("OPENAI_API_KEY"),
        reason="OPENAI_API_KEY not set"
    )
    def test_openai_decide(self):
        """Test actual OpenAI API call."""
        client = OpenAIClient()

        result = client.decide(
            prompt="Is Paris suitable for elderly travelers?",
            schema={
                "type": "object",
                "properties": {
                    "suitable": {"type": "boolean"},
                    "reason": {"type": "string"},
                },
                "required": ["suitable", "reason"],
            },
        )

        assert "suitable" in result
        assert "reason" in result
        assert isinstance(result["suitable"], bool)
