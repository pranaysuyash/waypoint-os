"""Canonical RAG Service facade for Waypoint OS.

Provides unified document indexing, hybrid vector/sparse/graph search,
and grounded generation interfaces with multi-tenant isolation.

Mount hardening (2026-10-22): one process-wide default service (canonical
factory — the spine router delegates to it), retrieval lineage recorded
per search (hashed queries only), a loud warning when the corpus holds
vectors from a different embedding model than the live provider, and a
truthful status surface.
"""

from typing import Callable, List, Optional
import logging
import os
import time

from src.llm.base import content_sha256
from src.rag.models import (
    RAGChunk,
    DocumentSourceType,
    HybridSearchQuery,
    RAGSearchResult,
    GroundedAnswer,
    KnowledgeNode,
    KnowledgeEdge,
)
from src.rag.store import SQLiteRAGStore
from src.rag.indexer import DocumentIndexer
from src.rag.retriever import HybridGraphVectorRetriever
from src.rag.grounding import GroundednessEvaluator
from src.rag.reranker import CrossEncoderReranker
from src.rag.embeddings import (
    EmbeddingProvider,
    estimate_embedding_cost_inr,
    get_default_embedding_provider,
)

logger = logging.getLogger(__name__)

_DEFAULT_STORE_PATH = "data/rag_store.db"
_default_service: Optional["RAGService"] = None


def get_default_rag_service() -> "RAGService":
    """Process-wide default RAG service (canonical factory).

    The spine router's Depends wrapper delegates here so the API and any
    in-pipeline consumer (e.g. specialty knowledge identification) share
    one store and one provider configuration — never parallel instances.
    Path overridable via ``RAG_STORE_PATH`` (tests use isolated tmp paths).
    """
    global _default_service
    if _default_service is None:
        _default_service = RAGService(db_path=os.getenv("RAG_STORE_PATH", _DEFAULT_STORE_PATH))
    return _default_service


class RAGService:
    def __init__(
        self,
        db_path: str = "data/rag_store.db",
        embedding_provider: Optional[EmbeddingProvider] = None,
    ):
        self.store = SQLiteRAGStore(db_path=db_path)
        self.embedding_provider = embedding_provider or get_default_embedding_provider()
        self.indexer = DocumentIndexer(
            embedding_dim=self.embedding_provider.dimension,
            embedding_provider=self.embedding_provider,
        )
        self.retriever = HybridGraphVectorRetriever(
            self.store,
            embedding_provider=self.embedding_provider,
        )
        # Optional capability: dark unless RAG_RERANKER=1 AND
        # sentence-transformers is installed (see src/rag/reranker.py).
        self.reranker = CrossEncoderReranker()
        self.evaluator = GroundednessEvaluator()

    def index_document(
        self,
        document_id: str,
        agency_id: str,
        source_type: DocumentSourceType,
        title: str,
        text: str,
        canonical_url: Optional[str] = None,
        file_path: Optional[str] = None,
        tags: Optional[List[str]] = None,
        entity_references: Optional[List[str]] = None,
        license_class: str = "agency_owned",
    ) -> List[RAGChunk]:
        """Chunk, embed, and store a full text document.

        When the semantic lane serves, embedding usage is checked against the
        agency's quota ledger (usage_guard) and finalized with the actual
        estimated cost — a blocked reservation aborts indexing BEFORE any
        vectors are written (fail-closed, matching the embedding contract).
        """
        usage_decision = None
        if self.embedding_provider.is_semantic:
            try:
                from src.llm.usage_guard import get_guard_for_agency

                guard = get_guard_for_agency(agency_id)
                estimated = estimate_embedding_cost_inr(len(text or ""))
                usage_decision = guard.check_before_call(
                    model=self.embedding_provider.model_name,
                    estimated_cost=estimated,
                    feature="rag_embedding",
                )
                if not usage_decision.allowed:
                    raise ValueError(
                        f"Embedding usage blocked by agency quota ledger: "
                        f"{usage_decision.reason}. Document not indexed."
                    )
            except ValueError:
                raise
            except Exception as guard_exc:
                # Guard registry/setting failures must not crash indexing
                # outside the guard's own fail-closed contract — record and
                # proceed (the per-call forensics still carry the cost).
                logger.warning("RAG usage guard check skipped: %s", guard_exc)

        try:
            chunks = self._index_document_inner(
                document_id=document_id,
                agency_id=agency_id,
                source_type=source_type,
                title=title,
                text=text,
                canonical_url=canonical_url,
                file_path=file_path,
                tags=tags,
                entity_references=entity_references,
                license_class=license_class,
            )
            if usage_decision is not None and usage_decision.allowed:
                actual = 0.0
                rec = getattr(self.embedding_provider, "last_call_record", None) or {}
                actual = float(rec.get("cost_estimate_inr") or 0.0)
                try:
                    from src.llm.usage_guard import get_guard_for_agency

                    get_guard_for_agency(agency_id).record_call(
                        usage_decision, actual_cost=actual, success=True
                    )
                except Exception as fin_exc:
                    logger.warning("RAG usage finalize skipped: %s", fin_exc)
            return chunks
        except Exception:
            if usage_decision is not None and usage_decision.allowed:
                try:
                    from src.llm.usage_guard import get_guard_for_agency

                    rec = getattr(self.embedding_provider, "last_call_record", None) or {}
                    get_guard_for_agency(agency_id).record_call(
                        usage_decision,
                        actual_cost=float(rec.get("cost_estimate_inr") or 0.0),
                        success=False,
                    )
                except Exception:
                    pass
            raise

    def _index_document_inner(
        self,
        document_id: str,
        agency_id: str,
        source_type: DocumentSourceType,
        title: str,
        text: str,
        canonical_url: Optional[str] = None,
        file_path: Optional[str] = None,
        tags: Optional[List[str]] = None,
        entity_references: Optional[List[str]] = None,
        license_class: str = "agency_owned",
    ) -> List[RAGChunk]:
        chunks = self.indexer.chunk_text(
            text=text,
            document_id=document_id,
            agency_id=agency_id,
            source_type=source_type,
            title=title,
            canonical_url=canonical_url,
            file_path=file_path,
            tags=tags,
            entity_references=entity_references,
            license_class=license_class,
        )
        for chunk in chunks:
            self.store.insert_chunk(chunk)
        return chunks

    def search(self, search_query: HybridSearchQuery) -> List[RAGSearchResult]:
        """Perform hybrid retrieval with a lineage record (hashes only).

        When the semantic lane serves, the query embedding is checked against
        the agency quota ledger; a block serves sparse-only (logged) instead
        of making the call."""
        started = time.perf_counter()
        skip_dense = False
        usage_decision = None
        if self.embedding_provider.is_semantic:
            try:
                from src.llm.usage_guard import get_guard_for_agency

                guard = get_guard_for_agency(search_query.agency_id)
                usage_decision = guard.check_before_call(
                    model=self.embedding_provider.model_name,
                    estimated_cost=estimate_embedding_cost_inr(
                        len(search_query.query or "")
                    ),
                    feature="rag_query_embedding",
                )
                if not usage_decision.allowed:
                    skip_dense = True
                    logger.warning(
                        "RAG query embedding blocked by quota ledger for agency "
                        "%s: %s — serving sparse-only",
                        search_query.agency_id,
                        usage_decision.reason,
                    )
            except Exception as guard_exc:
                usage_decision = None
                logger.warning("RAG usage guard check skipped: %s", guard_exc)

        results = self.retriever.retrieve(search_query, skip_dense=skip_dense)
        if self.reranker.is_available:
            results = self.reranker.rerank(
                search_query.query, results, top_k=search_query.top_k
            )

        # Lineage + honesty surfaces — best-effort, never breaks retrieval.
        try:
            other_models = [
                m for m in self.store.get_embedding_models(search_query.agency_id)
                if m["embedding_model"] != self.embedding_provider.model_name
            ]
            if other_models and not results:
                logger.warning(
                    "RAG search for agency %s: corpus holds vectors from %s but the "
                    "live provider is %s — dense leg empty by contract (re-index "
                    "to compare). Serving sparse-only.",
                    search_query.agency_id,
                    other_models,
                    self.embedding_provider.model_name,
                )
            self.store.record_retrieval_run(
                agency_id=search_query.agency_id,
                query_sha256=content_sha256(search_query.query),
                query_length=len(search_query.query or ""),
                top_k=search_query.top_k,
                embedding_model=self.embedding_provider.model_name,
                latency_ms=(time.perf_counter() - started) * 1000.0,
                result_count=len(results),
                top_chunk_ids=[r.chunk.id for r in results],
            )
        except Exception as audit_exc:
            logger.debug("RAG lineage record skipped: %s", audit_exc)
        return results

    def status(self, agency_id: Optional[str] = None) -> dict:
        """Truthful service status: what provider is live, what the corpus
        holds, and whether the lexical leg is FTS-backed or heuristic."""
        info = {
            "embedding_provider": self.embedding_provider.provider_name,
            "embedding_model": self.embedding_provider.model_name,
            "embedding_dimension": self.embedding_provider.dimension,
            "is_semantic": self.embedding_provider.is_semantic,
            "fts_lexical_leg": self.store.fts_available,
            "store_path": self.store.db_path,
        }
        if agency_id:
            info["agency_chunk_count"] = self.store.count_chunks(agency_id)
            info["corpus_embedding_models"] = self.store.get_embedding_models(agency_id)
        return info

    def _expand_parent_context(
        self,
        agency_id: str,
        citations: List[RAGSearchResult],
        max_expansions: int = 5,
    ) -> List[RAGSearchResult]:
        """Append parent chunks for child citations (CoverWise adjacent-context
        pattern, adapted to our parent/child chunking): a child hit earns its
        whole section. Parents are added once, marked ``parent_context``,
        score 0.0, capped so one answer cannot balloon."""
        expanded = list(citations)
        seen_ids = {c.chunk.id for c in expanded}
        for res in citations:
            if len(expanded) >= len(citations) + max_expansions:
                break
            parent_id = res.chunk.parent_id
            if not parent_id or parent_id in seen_ids:
                continue
            parent = self.store.get_chunk(parent_id, agency_id)
            if parent is None:
                continue
            seen_ids.add(parent_id)
            expanded.append(
                RAGSearchResult(
                    chunk=parent,
                    score=0.0,
                    dense_score=0.0,
                    sparse_score=0.0,
                    retrieval_method="parent_context",
                )
            )
        return expanded

    def query_and_ground(
        self,
        query: str,
        agency_id: str,
        generator_fn: Optional[Callable[[str, List[RAGSearchResult]], str]] = None,
        source_types: Optional[List[DocumentSourceType]] = None,
        top_k: int = 5,
        expand_parents: bool = True,
    ) -> GroundedAnswer:
        """Retrieve relevant knowledge, generate answer, and evaluate groundedness."""
        search_query = HybridSearchQuery(
            query=query,
            agency_id=agency_id,
            top_k=top_k,
            source_types=source_types,
        )
        citations = self.search(search_query)
        if expand_parents:
            citations = self._expand_parent_context(agency_id, citations)

        if generator_fn:
            answer_text = generator_fn(query, citations)
        else:
            # Fallback simple synthesis from top citations
            if citations:
                top_contents = "\n\n".join(
                    c.chunk.metadata.source_text
                    if c.chunk.metadata.source_text is not None else c.chunk.content
                    for c in citations[:2]
                )
                answer_text = f"Based on retrieved documents:\n\n{top_contents}"
            else:
                answer_text = "No relevant knowledge found in the agency document repository."

        grounded = self.evaluator.evaluate_answer(
            query=query,
            answer=answer_text,
            citations=citations,
        )
        return grounded

    def add_node(self, node: KnowledgeNode) -> None:
        self.store.insert_node(node)

    def add_edge(self, edge: KnowledgeEdge) -> None:
        self.store.insert_edge(edge)

    def get_nodes(self, agency_id: str, node_type: Optional[str] = None) -> List[KnowledgeNode]:
        return self.store.get_nodes(agency_id, node_type)
