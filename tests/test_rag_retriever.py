import pytest
from src.rag.models import (
    RAGChunk,
    RAGChunkMetadata,
    DocumentSourceType,
    HybridSearchQuery,
    KnowledgeNode,
)
from src.rag.store import SQLiteRAGStore
from src.rag.retriever import HybridGraphVectorRetriever


@pytest.fixture
def rag_store(tmp_path):
    return SQLiteRAGStore(db_path=str(tmp_path / "test_retriever.db"))


def test_hybrid_rrf_retrieval(rag_store):
    retriever = HybridGraphVectorRetriever(rag_store)
    
    # Document 1: Matches semantic intent (luxury beach)
    c1 = RAGChunk(
        id="c1",
        content="Resort on private beach with spa and infinity pool.",
        embedding=[0.9, 0.1, 0.0],
        metadata=RAGChunkMetadata(
            document_id="d1",
            agency_id="agency_a",
            source_type=DocumentSourceType.ITINERARY_TEMPLATE,
            title="Luxury Beach Escape",
        ),
        token_count=10,
    )
    # Document 2: Matches exact keyword (Amanpuri)
    c2 = RAGChunk(
        id="c2",
        content="Amanpuri resort rates and booking rules for 2026.",
        embedding=[0.0, 0.9, 0.1],
        metadata=RAGChunkMetadata(
            document_id="d2",
            agency_id="agency_a",
            source_type=DocumentSourceType.SUPPLIER_CONTRACT,
            title="Amanpuri Contract",
        ),
        token_count=8,
    )

    rag_store.insert_chunk(c1)
    rag_store.insert_chunk(c2)

    query = HybridSearchQuery(
        query="Amanpuri luxury resort on private beach",
        agency_id="agency_a",
        top_k=2,
        alpha=0.5,
    )
    results = retriever.retrieve(query)

    assert len(results) == 2
    # RRF combines dense and sparse ranks
    assert all(r.score > 0.0 for r in results)
    assert any(r.chunk.id == "c2" for r in results)


def test_graph_boosted_retrieval(rag_store):
    retriever = HybridGraphVectorRetriever(rag_store)

    node = KnowledgeNode(
        id="destination:bali",
        agency_id="agency_a",
        node_type="destination",
        label="Bali",
    )
    rag_store.insert_node(node)

    c1 = RAGChunk(
        id="c1",
        content="Hotel located in Bali near beach",
        metadata=RAGChunkMetadata(
            document_id="d1",
            agency_id="agency_a",
            source_type=DocumentSourceType.ITINERARY_TEMPLATE,
            title="Bali Hotel",
            entity_references=["destination:bali"],
        ),
    )
    rag_store.insert_chunk(c1)

    query = HybridSearchQuery(
        query="Tell me about Bali hotels",
        agency_id="agency_a",
        include_graph=True,
    )
    results = retriever.retrieve(query)
    assert len(results) == 1
    assert results[0].chunk.id == "c1"
