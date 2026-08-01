import pytest
from src.rag.models import (
    DocumentSourceType,
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
    # Seed knowledge into RAG
    seeded_count = SpecialtyKnowledgeService.seed_rag_knowledge(agency_id, rag_service)
    assert seeded_count == len(KNOWLEDGE_BASE)

    # Query specialty knowledge via RAG
    text = "We are arranging diving equipment, nitrox compressors, and saturation gear for a sea expedition."
    hits = SpecialtyKnowledgeService.identify_niche(text, agency_id=agency_id, rag_service=rag_service)

    assert len(hits) >= 1
    assert any(h.niche == "Sub-Aquatic & Diving Operations" for h in hits)


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
