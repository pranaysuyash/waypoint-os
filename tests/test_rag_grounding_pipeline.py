"""
tests/test_rag_grounding_pipeline.py — Verification suite for RAG grounding & provenance citations.
"""

from src.rag.models import (
    RAGChunk,
    RAGChunkMetadata,
    RAGSearchResult,
    DocumentSourceType,
)
from src.rag.grounding import GroundednessEvaluator


def test_groundedness_evaluator_high_confidence():
    evaluator = GroundednessEvaluator(min_confidence_threshold=0.70)
    
    meta = RAGChunkMetadata(
        document_id="doc_goa_001",
        agency_id="default_agency",
        title="Goa Luxury Resort Partner Directory",
        source_type=DocumentSourceType.SUPPLIER_CONTRACT,
        section_heading="Taj Exotica Villa Amenities",
        page_number=4,
    )
    
    chunk = RAGChunk(
        id="chunk_001",
        content="Taj Exotica Resort offers private sea view villas with personal butler service, complimentary spa credits, and airport transfers.",
        metadata=meta,
    )
    
    citations = [
        RAGSearchResult(
            chunk=chunk,
            score=0.92,
            dense_score=0.95,
            sparse_score=0.88,
        )
    ]
    
    query = "What amenities are included in Taj Exotica Goa?"
    answer = "Taj Exotica Resort includes sea view villas with personal butler service, spa credits, and private transfers."
    
    result = evaluator.evaluate_answer(query, answer, citations)
    
    assert result.is_grounded is True
    assert result.groundedness_score >= 0.70
    assert len(result.citations) == 1
    assert result.must_confirm == []
    
    formatted = evaluator.format_citation_text(citations)
    assert "Goa Luxury Resort Partner Directory" in formatted
    assert "Page 4" in formatted
    assert "Doc ID: doc_goa_001" in formatted



def test_groundedness_evaluator_low_confidence_flag():
    evaluator = GroundednessEvaluator(min_confidence_threshold=0.85)
    
    meta = RAGChunkMetadata(
        document_id="doc_generic",
        agency_id="default_agency",
        title="Generic Travel Brochure",
        source_type=DocumentSourceType.AGENCY_POLICY,
    )
    
    chunk = RAGChunk(
        id="chunk_002",
        content="Goa has warm weather and sandy beaches.",
        metadata=meta,
    )
    
    citations = [
        RAGSearchResult(
            chunk=chunk,
            score=0.30,
            dense_score=0.35,
            sparse_score=0.25,
        )
    ]
    
    query = "Does the resort offer private heliport access?"
    answer = "The resort has private heliport access for VIP arrivals."
    
    result = evaluator.evaluate_answer(query, answer, citations)
    
    assert result.is_grounded is False
    assert len(result.must_confirm) == 1
    assert "Low grounding confidence" in result.must_confirm[0]

