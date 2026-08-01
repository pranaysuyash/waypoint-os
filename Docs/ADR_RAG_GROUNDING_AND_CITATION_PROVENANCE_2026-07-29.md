# ADR: RAG Grounding & Citation Provenance Engine

**Status**: Accepted  
**Date**: 2026-07-29  
**Context**: Waypoint OS RAG Knowledge Engine & Hallucination Prevention (`src/rag/`)

---

## Context

Generative proposal strategy models risk introducing factual hallucinations regarding supplier policies, resort amenities, transfer rules, and visa requirements. Unverified claims in traveler proposals create agency liability and client trust failure.

---

## Decision

Implemented the Groundedness Evaluation & Citation Provenance Engine in `src/rag/`:

1. **Groundedness Evaluator (`src/rag/grounding.py`)**:
   - Evaluates answer support against retrieved chunks using a hybrid score combining dense retrieval confidence and token overlap ratio.
   - Enforces a minimum confidence threshold (`min_confidence_threshold=0.75`). Answers below threshold trigger mandatory operator verification flags (`must_confirm`).
2. **Hybrid Graph-Vector Retrieval (`src/rag/retriever.py`)**:
   - Combines dense vector embeddings (`search_dense`), sparse BM25 lexical search (`search_sparse_bm25`), and Knowledge Graph node boosting via Reciprocal Rank Fusion (RRF).
3. **Citation Provenance Footers (`format_citation_text`)**:
   - Formats Markdown provenance footers attaching document titles, page numbers, section headings, and document IDs to every proposal claim.
4. **Test Suite (`tests/test_rag_grounding_pipeline.py`)**:
   - Verified high-confidence grounded answers, citation formatting, and low-confidence operator warning triggers.

---

## Consequences

- Prevents ungrounded AI hallucinations from reaching client proposals without explicit operator review.
- Provides complete document provenance and source traceability.
