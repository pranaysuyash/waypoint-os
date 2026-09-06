"""Contract tests for the currently local, provider-neutral RAG retriever."""

from src.rag.models import (
    DocumentSourceType,
    HybridSearchQuery,
    RAGChunk,
    RAGChunkMetadata,
)
from src.rag.retriever import HybridGraphVectorRetriever


def _chunk(chunk_id: str) -> RAGChunk:
    return RAGChunk(
        id=chunk_id,
        content=chunk_id,
        metadata=RAGChunkMetadata(
            document_id=f"doc-{chunk_id}",
            agency_id="agency-test",
            source_type=DocumentSourceType.AGENCY_POLICY,
            title=chunk_id,
        ),
    )


class _RankedStore:
    """Minimal store double exposing independently ranked retrieval lanes."""

    def __init__(self) -> None:
        self.dense = [(_chunk("dense-first"), 0.9), (_chunk("sparse-first"), 0.1)]
        self.sparse = [(_chunk("sparse-first"), 3.0), (_chunk("dense-first"), 1.0)]

    def search_dense(self, **_kwargs):
        return self.dense

    def search_sparse_bm25(self, **_kwargs):
        return self.sparse

    def get_nodes(self, _agency_id):
        return []


def test_alpha_contract_weights_dense_and_sparse_lanes_in_documented_direction():
    store = _RankedStore()
    retriever = HybridGraphVectorRetriever(store)

    dense_only = retriever.retrieve(
        HybridSearchQuery(
            query="query",
            agency_id="agency-test",
            top_k=2,
            alpha=1.0,
            include_graph=False,
        )
    )
    sparse_only = retriever.retrieve(
        HybridSearchQuery(
            query="query",
            agency_id="agency-test",
            top_k=2,
            alpha=0.0,
            include_graph=False,
        )
    )

    assert dense_only[0].chunk.id == "dense-first"
    assert sparse_only[0].chunk.id == "sparse-first"
