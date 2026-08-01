import pytest
from src.rag.models import (
    RAGChunk,
    RAGChunkMetadata,
    DocumentSourceType,
    KnowledgeNode,
    KnowledgeEdge,
)
from src.rag.store import SQLiteRAGStore


@pytest.fixture
def rag_store(tmp_path):
    db_path = str(tmp_path / "test_rag.db")
    return SQLiteRAGStore(db_path=db_path)


def test_insert_and_retrieve_chunk(rag_store):
    metadata = RAGChunkMetadata(
        document_id="doc_123",
        agency_id="agency_a",
        source_type=DocumentSourceType.GOVERNMENT_ADVISORY,
        title="Singapore Visa Policy 2026",
        page_number=1,
    )
    chunk = RAGChunk(
        id="chunk_1",
        content="Singapore requires a valid passport with at least 6 months validity.",
        embedding=[0.1, 0.2, 0.3, 0.4],
        metadata=metadata,
        token_count=12,
    )

    rag_store.insert_chunk(chunk)
    retrieved = rag_store.get_chunk("chunk_1", "agency_a")
    
    assert retrieved is not None
    assert retrieved.id == "chunk_1"
    assert retrieved.metadata.title == "Singapore Visa Policy 2026"
    assert retrieved.metadata.source_type == DocumentSourceType.GOVERNMENT_ADVISORY
    assert retrieved.embedding == [0.1, 0.2, 0.3, 0.4]


def test_tenant_isolation(rag_store):
    chunk_a = RAGChunk(
        id="chunk_a",
        content="Agency A proprietary rates",
        embedding=[1.0, 0.0],
        metadata=RAGChunkMetadata(
            document_id="doc_a",
            agency_id="agency_a",
            source_type=DocumentSourceType.SUPPLIER_CONTRACT,
            title="Agency A Rates",
        ),
    )
    chunk_b = RAGChunk(
        id="chunk_b",
        content="Agency B proprietary rates",
        embedding=[1.0, 0.0],
        metadata=RAGChunkMetadata(
            document_id="doc_b",
            agency_id="agency_b",
            source_type=DocumentSourceType.SUPPLIER_CONTRACT,
            title="Agency B Rates",
        ),
    )

    rag_store.insert_chunk(chunk_a)
    rag_store.insert_chunk(chunk_b)

    # Agency A should not see Agency B chunk
    assert rag_store.get_chunk("chunk_b", "agency_a") is None
    
    # Vector search for Agency A should return only chunk_a
    results_a = rag_store.search_dense([1.0, 0.0], agency_id="agency_a")
    assert len(results_a) == 1
    assert results_a[0][0].id == "chunk_a"


def test_bm25_keyword_search(rag_store):
    chunk_1 = RAGChunk(
        id="c1",
        content="Luxury resort in Bali with private pool and scuba diving center.",
        metadata=RAGChunkMetadata(
            document_id="d1",
            agency_id="agency_a",
            source_type=DocumentSourceType.ITINERARY_TEMPLATE,
            title="Bali Luxury Escape",
        ),
        token_count=12,
    )
    chunk_2 = RAGChunk(
        id="c2",
        content="Mountain hiking tour in Swiss Alps with certified guide.",
        metadata=RAGChunkMetadata(
            document_id="d2",
            agency_id="agency_a",
            source_type=DocumentSourceType.ITINERARY_TEMPLATE,
            title="Alps Trekking",
        ),
        token_count=10,
    )

    rag_store.insert_chunk(chunk_1)
    rag_store.insert_chunk(chunk_2)

    results = rag_store.search_sparse_bm25("Bali scuba diving", agency_id="agency_a")
    assert len(results) >= 1
    assert results[0][0].id == "c1"


def test_knowledge_graph_store(rag_store):
    node1 = KnowledgeNode(
        id="destination:singapore",
        agency_id="agency_a",
        node_type="destination",
        label="Singapore",
    )
    node2 = KnowledgeNode(
        id="activity:night_safari",
        agency_id="agency_a",
        node_type="activity",
        label="Night Safari",
    )
    edge = KnowledgeEdge(
        id="edge_1",
        agency_id="agency_a",
        source_node_id="destination:singapore",
        target_node_id="activity:night_safari",
        relation="OFFERS_ACTIVITY",
    )

    rag_store.insert_node(node1)
    rag_store.insert_node(node2)
    rag_store.insert_edge(edge)

    nodes = rag_store.get_nodes("agency_a", node_type="destination")
    assert len(nodes) == 1
    assert nodes[0].id == "destination:singapore"

    edges = rag_store.get_edges_for_node("destination:singapore", "agency_a")
    assert len(edges) == 1
    assert edges[0].relation == "OFFERS_ACTIVITY"
