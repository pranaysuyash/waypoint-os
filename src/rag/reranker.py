"""Optional cross-encoder reranker for the RAG retrieval boundary.

Deliberately dependency-free until enabled: the reranker activates ONLY when
(a) ``sentence-transformers`` is importable AND (b) ``RAG_RERANKER=1``. With
either absent it reports unavailable and the retriever's RRF ordering stands
unchanged — the capability is dark by default, never a surprise dependency
(determinism-audit posture: capability routing records the model, and the
lexical/RFF baseline remains the floor).

Model: ``cross-encoder/ms-marco-MiniLM-L-6-v2`` — the CoverWise
(medpiper insurance_app) production choice for the same job.
"""

from __future__ import annotations

import logging
import os
from typing import List, Optional

from src.rag.models import RAGSearchResult

logger = logging.getLogger(__name__)

_RERANK_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"


class CrossEncoderReranker:
    """Rerank fused retrieval results with a cross-encoder when available."""

    def __init__(self, model_name: str = _RERANK_MODEL):
        self.model_name = model_name
        self._encoder = None
        self._checked = False

    @property
    def is_available(self) -> bool:
        """True only when the flag is set AND the library is importable."""
        if os.getenv("RAG_RERANKER", "").strip().lower() not in ("1", "true", "yes"):
            return False
        try:
            from sentence_transformers import CrossEncoder  # noqa: F401

            return True
        except ImportError:
            return False

    def _get_encoder(self):
        if not self._checked:
            self._checked = True
            try:
                from sentence_transformers import CrossEncoder

                self._encoder = CrossEncoder(self.model_name)
                logger.info("Cross-encoder reranker loaded (%s)", self.model_name)
            except Exception as exc:
                self._encoder = None
                logger.info("Cross-encoder reranker unavailable (optional): %s", exc)
        return self._encoder

    def rerank(
        self,
        query: str,
        results: List[RAGSearchResult],
        top_k: Optional[int] = None,
    ) -> List[RAGSearchResult]:
        """Resort results by cross-encoder relevance; identity when unavailable
        or on any encoder failure (the RRF ordering is the floor, never lost)."""
        if len(results) <= 1:
            return results
        encoder = self._get_encoder()
        if encoder is None:
            return results
        try:
            pairs = [(query, r.chunk.content) for r in results]
            scores = encoder.predict(pairs)
            rescored = sorted(
                zip(results, [float(s) for s in scores]),
                key=lambda pair: pair[1],
                reverse=True,
            )
            ordered = [
                RAGSearchResult(
                    chunk=r.chunk,
                    score=round(s, 6),
                    dense_score=r.dense_score,
                    sparse_score=r.sparse_score,
                    retrieval_method=r.retrieval_method + "+reranked",
                )
                for r, s in rescored
            ]
            return ordered[:top_k] if top_k else ordered
        except Exception as exc:
            logger.warning("Cross-encoder rerank failed (%s); RRF order stands", exc)
            return results
