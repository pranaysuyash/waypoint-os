from src.rag.models import (
    RAGChunk,
    RAGChunkMetadata,
    DocumentSourceType,
    RAGSearchResult,
)
from src.rag.grounding import GroundednessEvaluator


def test_groundedness_evaluation_high_confidence():
    evaluator = GroundednessEvaluator(min_confidence_threshold=0.75)

    chunk = RAGChunk(
        id="c1",
        content="Singapore requires a valid passport with at least 6 months validity from date of entry.",
        metadata=RAGChunkMetadata(
            document_id="doc_singapore_visa",
            agency_id="agency_a",
            source_type=DocumentSourceType.GOVERNMENT_ADVISORY,
            title="Singapore Entry Rules 2026",
            page_number=2,
        ),
    )
    result = RAGSearchResult(chunk=chunk, score=0.85, dense_score=0.8, sparse_score=0.9)

    query = "What is the passport validity requirement for Singapore?"
    answer = "Singapore requires a valid passport with at least 6 months validity from entry."

    grounded = evaluator.evaluate_answer(query, answer, [result])

    assert grounded.is_grounded is True
    assert grounded.groundedness_score >= 0.75
    assert len(grounded.must_confirm) == 0
    assert len(grounded.citations) == 1

    citation_text = evaluator.format_citation_text(grounded.citations)
    assert "Singapore Entry Rules 2026" in citation_text
    assert "Page 2" in citation_text


def test_groundedness_evaluation_low_confidence_trigger_must_confirm():
    evaluator = GroundednessEvaluator(min_confidence_threshold=0.75)

    query = "What is the visa policy for Mars?"
    answer = "Mars requires a 30-day visa on arrival."

    # Empty citations
    grounded = evaluator.evaluate_answer(query, answer, [])

    assert grounded.is_grounded is False
    assert grounded.groundedness_score == 0.0
    assert len(grounded.must_confirm) >= 1
    assert "No supporting documentation" in grounded.must_confirm[0]
