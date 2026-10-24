import pytest
from src.rag.models import (
    DocumentSourceType,
    HybridSearchQuery,
    KnowledgeNode,
    KnowledgeEdge,
)
from src.rag.service import RAGService
from src.intake.specialty_knowledge import SpecialtyKnowledgeService, KNOWLEDGE_BASE


@pytest.fixture
def rag_service(tmp_path):
    return RAGService(db_path=str(tmp_path / "test_integration_rag.db"))


def test_rag_service_full_document_lifecycle(rag_service):
    doc_id = "advisory_japan_2026"
    agency_id = "agency_tokyo"
    text = (
        "Japan Visa Advisory 2026.\n\n"
        "Travelers holding US or EU passports can enter Japan visa-free for up to 90 days.\n\n"
        "Passport must be valid for the duration of stay."
    )

    chunks = rag_service.index_document(
        document_id=doc_id,
        agency_id=agency_id,
        source_type=DocumentSourceType.GOVERNMENT_ADVISORY,
        title="Japan Visa Regulations",
        text=text,
        tags=["japan", "visa", "passport"],
    )

    assert len(chunks) >= 1

    # Query and ground
    grounded = rag_service.query_and_ground(
        query="Can US passport holders enter Japan visa free?",
        agency_id=agency_id,
    )

    assert grounded.is_grounded is True
    assert "Japan" in grounded.answer
    assert len(grounded.citations) >= 1


def test_specialty_knowledge_rag_integration(rag_service):
    agency_id = "agency_specialist"
    # Seed knowledge into RAG — ensure_seeded is idempotent and registers
    # graph nodes (supersedes seed_rag_knowledge, 2026-10-22).
    assert SpecialtyKnowledgeService.ensure_seeded(agency_id, rag_service) is True
    assert SpecialtyKnowledgeService.ensure_seeded(agency_id, rag_service) is False

    # Query specialty knowledge via RAG
    text = "We are arranging diving equipment, nitrox compressors, and saturation gear for a sea expedition."
    hits = SpecialtyKnowledgeService.identify_niche(text, agency_id=agency_id, rag_service=rag_service)

    assert len(hits) >= 1
    assert any(h.niche == "Sub-Aquatic & Diving Operations" for h in hits)

    # Seeding registered the graph nodes with keyword properties so the
    # retriever's graph boost can fire on keyword mentions.
    nodes = rag_service.get_nodes(agency_id, node_type="niche")
    assert len(nodes) == len(KNOWLEDGE_BASE)
    assert all("keywords" in n.properties for n in nodes)

    # Auto-seed path: identify_niche on a fresh agency seeds before searching.
    fresh_agency = "agency_fresh_seed"
    fresh_hits = SpecialtyKnowledgeService.identify_niche(
        "repatriation of remains documentation", agency_id=fresh_agency, rag_service=rag_service
    )
    assert any("Repatriation" in h.niche for h in fresh_hits)
    assert rag_service.store.count_chunks(fresh_agency) > 0


def test_service_audit_trail_records_lineage(rag_service):
    """Mount hardening: every search leaves a hashes-only lineage row."""
    import hashlib

    agency_id = "agency_audit"
    rag_service.index_document(
        document_id="d1",
        agency_id=agency_id,
        source_type=DocumentSourceType.GOVERNMENT_ADVISORY,
        title="Advisory",
        text="Visa-free entry for 90 days with a valid passport.",
    )
    query = "visa free entry duration"
    rag_service.search(
        HybridSearchQuery(query=query, agency_id=agency_id, top_k=3)
    )
    with rag_service.store._get_connection() as conn:
        row = conn.execute("SELECT * FROM rag_runs WHERE agency_id = ?", (agency_id,)).fetchone()
    assert row is not None
    assert row["query_sha256"] == hashlib.sha256(query.encode()).hexdigest()
    assert "visa" not in (row["query_sha256"] or "")
    assert row["result_count"] >= 0
    assert row["embedding_model"]


def test_rag_knowledge_graph_integration(rag_service):
    agency_id = "agency_graph"

    node_supplier = KnowledgeNode(
        id="supplier:amanpuri",
        agency_id=agency_id,
        node_type="supplier",
        label="Amanpuri Resort",
        properties={"rating": 5.0, "location": "Phuket"},
    )
    node_dest = KnowledgeNode(
        id="destination:phuket",
        agency_id=agency_id,
        node_type="destination",
        label="Phuket",
    )
    edge = KnowledgeEdge(
        id="edge_1",
        agency_id=agency_id,
        source_node_id="supplier:amanpuri",
        target_node_id="destination:phuket",
        relation="LOCATED_IN",
    )

    rag_service.add_node(node_supplier)
    rag_service.add_node(node_dest)
    rag_service.add_edge(edge)

    nodes = rag_service.get_nodes(agency_id)
    assert len(nodes) == 2
