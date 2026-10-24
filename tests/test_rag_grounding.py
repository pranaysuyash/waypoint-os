from src.rag.models import (
    RAGChunk,
    RAGChunkMetadata,
    DocumentSourceType,
    RAGSearchResult,
)
from src.rag.grounding import GroundednessEvaluator

import pytest


def _citation(content: str, *, source_text: str | None = None) -> RAGSearchResult:
    return RAGSearchResult(
        chunk=RAGChunk(
            id="numeric_guard_chunk",
            content=content,
            metadata=RAGChunkMetadata(
                document_id="numeric_guard_doc",
                agency_id="agency_a",
                source_type=DocumentSourceType.AGENCY_POLICY,
                title="Synthetic policy",
                source_text=source_text,
            ),
        ),
        score=0.99,
    )


@pytest.mark.parametrize(("source", "answer"), [
    ("The cancellation fee is USD 100 per traveler.", "The cancellation fee is USD 900 per traveler."),
    ("Passport validity must be 6 months.", "Passport validity must be 9 months."),
    ("A deposit of 10 percent is required.", "A deposit of 90 percent is required."),
    ("The cancellation fee is USD 100.", "The cancellation fee is INR 100."),
])
def test_numeric_contradiction_cannot_pass_as_grounded(source, answer):
    grounded = GroundednessEvaluator().evaluate_answer("What is required?", answer, [_citation(source)])
    assert grounded.is_grounded is False
    assert grounded.groundedness_score < 0.75
    assert grounded.must_confirm
    assert grounded.claim_support_status == "unsupported_numeric"


def test_numeric_guard_uses_verbatim_source_not_retrieval_rendering():
    citation = _citation(
        "The cancellation fee is USD 900 per traveler.",
        source_text="The cancellation fee is USD 100 per traveler.",
    )
    grounded = GroundednessEvaluator().evaluate_answer(
        "What is the fee?", "The cancellation fee is USD 900 per traveler.", [citation]
    )
    assert grounded.is_grounded is False
    assert grounded.claim_support_status == "unsupported_numeric"


def test_same_numbers_and_word_overlap_do_not_establish_claim_entailment():
    grounded = GroundednessEvaluator().evaluate_answer(
        "Does a cancellation fee apply?",
        "The cancellation fee is not USD 100 per traveler.",
        [_citation("The cancellation fee is USD 100 per traveler.")],
    )
    assert grounded.claim_support_status == "not_verified"
    assert any("claim" in warning.lower() for warning in grounded.must_confirm)


def test_empty_answer_is_not_grounded_even_with_citations():
    grounded = GroundednessEvaluator().evaluate_answer("What is the fee?", "   ", [_citation("Fee: USD 100.")])
    assert grounded.is_grounded is False
    assert grounded.groundedness_score == 0.0
    assert grounded.claim_support_status == "empty_answer"


def test_exact_excerpt_is_explicitly_labeled_without_claim_verification():
    source = "The cancellation fee is USD 100 per traveler."
    grounded = GroundednessEvaluator().evaluate_answer("What is the fee?", source, [_citation(source)])
    assert grounded.is_grounded is True
    assert grounded.claim_support_status == "source_excerpt"
    assert grounded.grounding_method == "lexical_overlap_numeric_guard_v1"


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
    assert grounded.claim_support_status == "not_verified"
    assert any("Claim support" in warning for warning in grounded.must_confirm)
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
