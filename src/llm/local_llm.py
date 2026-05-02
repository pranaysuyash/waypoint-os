"""
llm.local_llm — Local HuggingFace LLM client implementation.

Provides offline, privacy-first LLM inference using HuggingFace transformers.
Primary model: microsoft/phi-3-mini-4k-instruct (CPU-friendly, ~4GB RAM)

Benefits:
- No API cost after model download
- Privacy: data never leaves the machine
- Offline operation
- Predictable costs (one-time download)

Trade-offs:
- Slower than API-based models (2-10 seconds per decision)
- Requires 4-8GB RAM for model loading
- Model quality lower than GPT-4 level
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import warnings
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="builtin type.*has no __module__", category=DeprecationWarning)
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

from .base import BaseLLMClient, LLMError, LLMUnavailableError, LLMResponseError


# Default model configuration
DEFAULT_MODEL = "microsoft/phi-3-mini-4k-instruct"
DEFAULT_CACHE_DIR = Path.home() / ".cache" / "waypoint" / "models"

# Model path mapping (can be overridden by environment)
MODEL_PATHS = {
    "microsoft/phi-3-mini-4k-instruct": DEFAULT_CACHE_DIR / "phi-3-mini-4k-instruct",
}


class LocalLLMClient(BaseLLMClient):
    """
    Local HuggingFace LLM client.

    Downloads and runs models locally using transformers.
    Ideal for privacy-sensitive or offline scenarios.

    Configure via environment variables:
        LOCAL_LLM_MODEL=microsoft/phi-3-mini-4k-instruct
        LOCAL_LLM_DEVICE=auto  # auto, cpu, cuda
        LOCAL_LLM_MAX_TOKENS=512

    Example:
        client = LocalLLMClient()
        result = client.decide(
            prompt="Is this trip suitable for elderly travelers?",
            schema={"type": "object", "properties": {...}}
        )
    """

    def __init__(
        self,
        model: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 1024,
        device: Optional[str] = None,
        cache_dir: Optional[Path] = None,
    ):
        """
        Initialize the local LLM client.

        Args:
            model: Model name/path (default: microsoft/phi-3-mini-4k-instruct)
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens in response
            device: Device to use (auto, cpu, cuda)
            cache_dir: Directory to cache downloaded models
        """
        if not TRANSFORMERS_AVAILABLE:
            raise LLMUnavailableError(
                "transformers package not installed. "
                "Install with: uv add --group llm transformers torch sentencepiece"
            )

        model = model or os.environ.get("LOCAL_LLM_MODEL", DEFAULT_MODEL)
        super().__init__(model, temperature, max_tokens)

        self.device = device or os.environ.get("LOCAL_LLM_DEVICE", "auto")
        self.cache_dir = cache_dir or DEFAULT_CACHE_DIR

        # Load model on first use (lazy loading)
        self._model: Optional[Any] = None
        self._tokenizer: Optional[Any] = None
        self._loaded = False

    def _load_model(self) -> None:
        """Load the model and tokenizer (lazy loading)."""
        if self._loaded:
            return

        try:
            print(f"Loading local LLM: {self.model}...")
            print(f"Cache directory: {self.cache_dir}")

            # Ensure cache directory exists
            self.cache_dir.mkdir(parents=True, exist_ok=True)

            # Load tokenizer
            self._tokenizer = AutoTokenizer.from_pretrained(
                self.model,
                cache_dir=self.cache_dir,
                trust_remote_code=True,
            )

            # Load model
            self._model = AutoModelForCausalLM.from_pretrained(
                self.model,
                cache_dir=self.cache_dir,
                torch_dtype=torch.float32 if self.device == "cpu" else torch.float16,
                trust_remote_code=True,
            )

            # Move to device
            if self.device == "cuda" and torch.cuda.is_available():
                self._model = self._model.to("cuda")
            elif self.device == "auto":
                if torch.cuda.is_available():
                    self._model = self._model.to("cuda")
                    print("Using CUDA device")
                else:
                    print("Using CPU device")
            else:
                print("Using CPU device")

            # Set to eval mode
            self._model.eval()

            self._loaded = True
            print(f"Model loaded successfully")

        except Exception as e:
            raise LLMUnavailableError(f"Failed to load local model: {e}")

    def is_available(self) -> bool:
        """Check if the local LLM client is available."""
        if not TRANSFORMERS_AVAILABLE:
            return False
        try:
            # Try to load the model
            self._load_model()
            return self._loaded
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
            LLMUnavailableError: If model cannot be loaded
            LLMResponseError: If response cannot be parsed
        """
        if not self.is_available():
            raise LLMUnavailableError("Local LLM not available")

        # Build the prompt
        full_prompt = self._build_prompt(prompt, schema)

        # Tokenize
        inputs = self._tokenizer(
            full_prompt,
            return_tensors="pt",
            truncation=True,
            max_length=4096,  # phi-3-mini context window
        ).to(self._model.device)

        try:
            # Generate
            with torch.no_grad():
                outputs = self._model.generate(
                    **inputs,
                    max_new_tokens=min(self.max_tokens, 512),  # Conservative for local models
                    temperature=temperature if temperature is not None else self.temperature,
                    do_sample=True,
                    pad_token_id=self._tokenizer.eos_token_id,
                )

            # Decode response
            response_text = self._tokenizer.decode(outputs[0], skip_special_tokens=True)

            # Extract only the generated part (remove prompt)
            if full_prompt in response_text:
                response_text = response_text[len(full_prompt):].strip()

            if not response_text:
                raise LLMResponseError("Empty response from local LLM")

            # Parse JSON
            try:
                # Try to extract JSON from response
                decision = self._extract_json(response_text)
            except (json.JSONDecodeError, ValueError) as e:
                raise LLMResponseError(f"Failed to parse JSON response: {e}\nResponse: {response_text}")

            return decision

        except Exception as e:
            if isinstance(e, (LLMUnavailableError, LLMResponseError)):
                raise
            raise LLMUnavailableError(f"Local LLM inference failed: {e}")

    def _build_prompt(self, prompt: str, schema: Dict[str, Any]) -> str:
        """Build the full prompt with JSON schema instruction."""
        schema_str = json.dumps(schema, indent=2)

        # Phi-3 uses a chat-like format
        return f"""<|user|>
{prompt}

You must respond with valid JSON matching this schema:
{schema_str}

Respond ONLY with the JSON object, no additional text.
<|end|>
<|assistant|>"""

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """
        Extract JSON from text, handling common formatting issues.

        Local models sometimes include explanatory text before/after the JSON.
        """
        # Try direct parse first
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try to find JSON object in the text
        start = text.find("{")
        end = text.rfind("}") + 1

        if start >= 0 and end > start:
            try:
                return json.loads(text[start:end])
            except json.JSONDecodeError:
                pass

        # Try to find JSON array
        start = text.find("[")
        end = text.rfind("]") + 1

        if start >= 0 and end > start:
            try:
                return json.loads(text[start:end])
            except json.JSONDecodeError:
                pass

        raise ValueError(f"Could not extract JSON from response: {text[:200]}")

    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """
        Estimate the cost of an LLM call in INR.

        For local models, cost is effectively zero after download.
        We return a small "compute cost" for accounting purposes.
        """
        # Nominal compute cost (electricity, hardware amortization)
        # Approximately ₹0.01 per 1000 tokens for local inference
        return ((prompt_tokens + completion_tokens) / 1000) * 0.01

    def count_tokens(self, text: str) -> int:
        """
        Count tokens using the model's tokenizer.

        More accurate than the default character-based estimate.
        """
        if not self._loaded:
            self._load_model()

        try:
            tokens = self._tokenizer.encode(text, add_special_tokens=False)
            return len(tokens)
        except Exception:
            return super().count_tokens(text)

    def unload(self) -> None:
        """
        Unload the model from memory.

        Useful for freeing RAM when the model won't be used for a while.
        """
        if self._model is not None:
            del self._model
            self._model = None
        if self._tokenizer is not None:
            del self._tokenizer
            self._tokenizer = None
        self._loaded = False

        # Clear CUDA cache if applicable
        if torch.cuda.is_available():
            torch.cuda.empty_cache()


def create_local_llm_client(
    model: Optional[str] = None,
    temperature: float = 0.3,
    max_tokens: Optional[int] = None,
    device: Optional[str] = None,
) -> LocalLLMClient:
    """
    Factory function to create a local LLM client.

    Reads configuration from environment variables by default.

    Environment variables:
        LOCAL_LLM_MODEL: Model name (default: microsoft/phi-3-mini-4k-instruct)
        LOCAL_LLM_DEVICE: Device (auto, cpu, cuda)
        LOCAL_LLM_MAX_TOKENS: Maximum tokens (default: 1024)

    Args:
        model: Override model from environment
        temperature: Sampling temperature
        max_tokens: Maximum tokens in response (None = read from env or 1024)
        device: Override device from environment

    Returns:
        Configured LocalLLMClient instance

    Raises:
        LLMUnavailableError: If client cannot be created
    """
    model = model or os.environ.get("LOCAL_LLM_MODEL", DEFAULT_MODEL)
    if max_tokens is None:
        max_tokens = int(os.environ.get("LOCAL_LLM_MAX_TOKENS", "1024"))

    try:
        return LocalLLMClient(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            device=device,
        )
    except Exception as e:
        raise LLMUnavailableError(f"Failed to create local LLM client: {e}")
