"""Embedding provider abstraction for Waypoint OS RAG Engine.

Defines the EmbeddingProvider protocol, an offline deterministic HashEmbeddingProvider
(for unit tests and zero-dependency operation), and a pluggable SemanticEmbeddingProvider
adapter interface with explicit reality tier disclosure.
"""

from typing import List, Protocol, runtime_checkable
import os
import hashlib
import logging

logger = logging.getLogger(__name__)

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "he",
    "in", "is", "it", "its", "of", "on", "or", "that", "the", "to", "was", "were",
    "will", "with", "we", "you", "your", "this", "have"
}


@runtime_checkable
class EmbeddingProvider(Protocol):
    """Protocol for vector representation generators in Waypoint OS."""

    @property
    def provider_name(self) -> str:
        """Name of the embedding provider."""
        ...

    @property
    def model_name(self) -> str:
        """Underlying model identifier."""
        ...

    @property
    def dimension(self) -> int:
        """Output vector dimension."""
        ...

    @property
    def is_semantic(self) -> bool:
        """Whether this provider produces true semantic vectors (True) or deterministic hash buckets (False)."""
        ...

    def embed_text(self, text: str) -> List[float]:
        """Generate an embedding vector for a single text chunk."""
        ...

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embedding vectors for a batch of texts."""
        ...


class HashEmbeddingProvider:
    """Deterministic hash-bucket pseudo-vector generator for zero-dependency offline/test execution.

    Produces unit-normalized 64-dim (or user configured dim) vectors based on MD5 hashing
    of normalized words. This is explicitly NOT a semantic model, but satisfies the
    EmbeddingProvider contract deterministically.
    """

    def __init__(self, dimension: int = 64):
        self._dimension = dimension

    @property
    def provider_name(self) -> str:
        return "local_hash"

    @property
    def model_name(self) -> str:
        return "md5_word_bucket"

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def is_semantic(self) -> bool:
        return False

    def embed_text(self, text: str) -> List[float]:
        words = [w.strip(".,!?:;\"'()[]{}") for w in text.lower().split()]
        filtered_words = [w for w in words if w and w not in STOPWORDS and len(w) > 1]

        vector = [0.0] * self._dimension
        for idx, word in enumerate(filtered_words):
            h = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
            vector[h % self._dimension] += 1.0 / (1.0 + idx * 0.1)

        norm = sum(v * v for v in vector) ** 0.5
        if norm > 0.0:
            vector = [v / norm for v in vector]
        return vector

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return [self.embed_text(t) for t in texts]


class SemanticEmbeddingProvider:
    """Configurable semantic embedding provider adapter.

    Wraps an external provider or local transformer if installed and configured
    (e.g., OPENAI_API_KEY with text-embedding-3-small). Gracefully falls back
    to HashEmbeddingProvider if credentials or optional libraries are absent.
    """

    def __init__(
        self,
        provider_name: str = "openai",
        model_name: str = "text-embedding-3-small",
        dimension: int = 1536,
        fallback_dimension: int = 64,
    ):
        self._provider_name = provider_name
        self._model_name = model_name
        self._dimension = dimension
        self._fallback = HashEmbeddingProvider(dimension=fallback_dimension)
        self._is_active = False

        api_key = os.getenv("OPENAI_API_KEY")
        if api_key and provider_name.lower() == "openai":
            self._is_active = True
        else:
            logger.debug(
                "SemanticEmbeddingProvider configured for %s:%s but credentials absent; fallback active.",
                provider_name,
                model_name,
            )

    @property
    def provider_name(self) -> str:
        return self._provider_name if self._is_active else f"{self._provider_name}_fallback_local_hash"

    @property
    def model_name(self) -> str:
        return self._model_name if self._is_active else self._fallback.model_name

    @property
    def dimension(self) -> int:
        return self._dimension if self._is_active else self._fallback.dimension

    @property
    def is_semantic(self) -> bool:
        return self._is_active

    def embed_text(self, text: str) -> List[float]:
        if not self._is_active:
            return self._fallback.embed_text(text)

        try:
            import urllib.request
            import json

            api_key = os.environ["OPENAI_API_KEY"]
            req = urllib.request.Request(
                "https://api.openai.com/v1/embeddings",
                data=json.dumps({
                    "input": text,
                    "model": self._model_name,
                }).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                },
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["data"][0]["embedding"]
        except Exception as exc:
            logger.warning("Remote semantic embedding failed (%s); falling back to local hash vector", exc)
            return self._fallback.embed_text(text)

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        if not self._is_active:
            return self._fallback.embed_batch(texts)
        try:
            import urllib.request
            import json

            api_key = os.environ["OPENAI_API_KEY"]
            req = urllib.request.Request(
                "https://api.openai.com/v1/embeddings",
                data=json.dumps({
                    "input": texts,
                    "model": self._model_name,
                }).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                },
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return [item["embedding"] for item in data["data"]]
        except Exception as exc:
            logger.warning("Remote batch semantic embedding failed (%s); falling back to local hash vector", exc)
            return self._fallback.embed_batch(texts)


def get_default_embedding_provider() -> EmbeddingProvider:
    """Return the configured or safe default embedding provider."""
    provider_type = os.getenv("RAG_EMBEDDING_PROVIDER", "local_hash").lower()
    if provider_type == "openai" and os.getenv("OPENAI_API_KEY"):
        return SemanticEmbeddingProvider(provider_name="openai")
    return HashEmbeddingProvider()
