"""Embedding provider abstraction for Waypoint OS RAG Engine.

Defines the EmbeddingProvider protocol, an offline deterministic HashEmbeddingProvider
(for unit tests and zero-dependency operation), and a pluggable SemanticEmbeddingProvider
adapter interface with explicit reality tier disclosure.

Egress discipline (mount hardening 2026-10-22): the semantic provider strips
PII through the canonical ``spine_api.core.llm_egress`` guard before any text
leaves the process, and every successful remote call emits a forensics record
via ``record_llm_call`` (hashes only — content is never logged), matching the
contract enforced on the generative lanes. PII stripping trades a little
retrieval signal for tenant privacy; that trade is deliberate and documented.
"""

from typing import List, Protocol, runtime_checkable
import os
import hashlib
import logging
import time

from src.llm.base import record_llm_call

logger = logging.getLogger(__name__)

# OpenAI published pricing (2026-10): text-embedding-3-small is $0.02 per
# 1M input tokens. Converted at the repo convention (≈₹83/USD, matching
# openai_client.py PRICING). Tokens are ESTIMATED at ≈4 chars/token — the
# same heuristic the other clients use — so this is an accounting estimate,
# never a billed figure.
_EMBEDDING_USD_PER_MTOK = 0.02
_USD_TO_INR = 83.0
_CHARS_PER_TOKEN = 4


def estimate_embedding_cost_inr(text_chars: int) -> float:
    """Char-derived INR cost estimate for one embedding input.

    tokens ≈ chars/4; ₹ = tokens × $0.02/1M × ₹83/USD."""
    tokens = max(1, text_chars) / _CHARS_PER_TOKEN
    return tokens / 1_000_000 * _EMBEDDING_USD_PER_MTOK * _USD_TO_INR


def _strip_pii_for_egress(text: str) -> str:
    """Best-effort PII strip via the canonical egress guard (never raises).

    ``strip_pii`` returns ``(cleaned_text, redaction_count)`` — unpack it;
    the provider embeds only the cleaned text."""
    try:
        from spine_api.core.llm_egress import strip_pii

        cleaned, _count = strip_pii(text)
        return cleaned
    except Exception:
        return text


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

    MD5 note (Mimosa advisory, 2026-10-22): this is a word-bucketing hash for a
    deterministic pseudo-vector, not a security primitive — collision resistance
    is irrelevant to its function, and switching algorithms would invalidate
    every stored vector for zero security gain. Deliberately kept.
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

    Failure semantics (contract-verification fix, 2026-10-22): when active,
    a remote failure RAISES rather than silently degrading — a hash-vector
    fallback would write/query vectors from a different space under this
    provider's name, which is exactly the mislabeled-vector class the
    embedding contract (FND-0362) forbids. The indexer propagates the error
    (document not indexed, nothing mislabeled written); the query side
    catches it in the retriever and degrades to sparse-only with a logged
    reason. The hash fallback applies ONLY when the provider is not active
    (no credentials configured).
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
        self.last_call_record = None

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

    def _get_sdk_client(self):
        """Lazy OpenAI SDK client — battle-tested transport, retries, pooling."""
        from openai import OpenAI

        return OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    def embed_text(self, text: str) -> List[float]:
        if not self._is_active:
            return self._fallback.embed_text(text)

        # Egress guard BEFORE anything leaves the process; the forensics
        # record hashes the STRIPPED text — what the provider actually saw.
        outbound = _strip_pii_for_egress(text)
        try:
            started = time.perf_counter()
            resp = self._get_sdk_client().embeddings.create(
                model=self._model_name,
                input=outbound,
            )
            vector = list(resp.data[0].embedding)
            record = record_llm_call(
                provider="openai",
                model=self._model_name,
                prompt=outbound,
                response_text=str(vector),
                temperature_requested=None,
                temperature_effective=None,
                latency_ms=(time.perf_counter() - started) * 1000.0,
                cost_estimate_inr=estimate_embedding_cost_inr(len(outbound)),
            )
            self.last_call_record = record
            return vector
        except Exception as exc:
            # Active provider + failure = RAISE. A silent hash fallback here
            # would stamp this provider's model_name on hash vectors.
            raise RuntimeError(
                f"semantic embedding provider '{self._model_name}' failed: {exc}"
            ) from exc

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        if not self._is_active:
            return self._fallback.embed_batch(texts)
        # Egress guard BEFORE anything leaves the process.
        outbound = [_strip_pii_for_egress(t) for t in texts]
        try:
            started = time.perf_counter()
            resp = self._get_sdk_client().embeddings.create(
                model=self._model_name,
                input=outbound,
            )
            ordered = sorted(resp.data, key=lambda item: item.index)
            vectors = [list(item.embedding) for item in ordered]
            record = record_llm_call(
                provider="openai",
                model=self._model_name,
                prompt="\n---\n".join(outbound),
                response_text=str(vectors),
                temperature_requested=None,
                temperature_effective=None,
                latency_ms=(time.perf_counter() - started) * 1000.0,
                cost_estimate_inr=estimate_embedding_cost_inr(sum(len(t) for t in outbound)),
            )
            self.last_call_record = record
            return vectors
        except Exception as exc:
            raise RuntimeError(
                f"semantic embedding provider '{self._model_name}' failed: {exc}"
            ) from exc


def get_default_embedding_provider() -> EmbeddingProvider:
    """Return the configured or safe default embedding provider.

    Posture (owner ruling 2026-10-22): the SEMANTIC leg is the default for
    the RAG lane — agency text egress is PII-stripped and forensics-recorded
    (``record_llm_call``), and the owner explicitly authorized it. Without an
    ``OPENAI_API_KEY`` the provider degrades gracefully to the deterministic
    hash lane, so the default is safe in every environment. The test suite
    pins ``RAG_EMBEDDING_PROVIDER=local_hash`` (conftest) and stays offline;
    the semantic lane is exercised by explicitly-configured tests only.
    """
    provider_type = os.getenv("RAG_EMBEDDING_PROVIDER", "openai").lower()
    if provider_type == "openai" and os.getenv("OPENAI_API_KEY"):
        return SemanticEmbeddingProvider(provider_name="openai")
    return HashEmbeddingProvider()
