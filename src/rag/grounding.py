"""Groundedness evaluation and citation provenance engine for Waypoint OS.

Prevents AI hallucinations by evaluating answer support against retrieved chunks
and generating explicit document citations and operator confirmation flags.
"""

import uuid
from typing import List
from src.rag.models import RAGSearchResult, GroundedAnswer


class GroundednessEvaluator:
    def __init__(self, min_confidence_threshold: float = 0.75):
        self.min_confidence_threshold = min_confidence_threshold

    def evaluate_answer(
        self,
        query: str,
        answer: str,
        citations: List[RAGSearchResult],
    ) -> GroundedAnswer:
        """Evaluate if the generated answer is grounded in the retrieved citations."""
        telemetry_id = f"rag_eval_{uuid.uuid4().hex[:8]}"

        if not citations:
            return GroundedAnswer(
                query=query,
                answer=answer,
                groundedness_score=0.0,
                is_grounded=False,
                citations=[],
                must_confirm=["No supporting documentation found in agency knowledge base."],
                execution_telemetry_id=telemetry_id,
            )

        # Compute groundedness score based on citation top score and token overlap
        top_citation = citations[0] if citations else None
        retrieval_confidence = (
            min(1.0, max(top_citation.dense_score, min(1.0, top_citation.sparse_score / 2.0)))
            if top_citation
            else 0.0
        )
        
        # Word overlap check between answer and retrieved chunk contents
        answer_words = set(w.lower() for w in answer.split() if len(w) > 3)
        chunk_words = set()
        for c in citations:
            chunk_words.update(w.lower() for w in c.chunk.content.split() if len(w) > 3)

        overlap_ratio = len(answer_words.intersection(chunk_words)) / max(1, len(answer_words))
        
        # Groundedness score combines retrieval confidence + overlap ratio
        groundedness_score = min(1.0, round((retrieval_confidence * 0.4) + (overlap_ratio * 0.6), 2))
        is_grounded = groundedness_score >= self.min_confidence_threshold

        must_confirm = []
        if not is_grounded:
            must_confirm.append(
                f"Low grounding confidence ({groundedness_score:.2f} < {self.min_confidence_threshold}). "
                "Operator must verify document details before client proposal."
            )

        return GroundedAnswer(
            query=query,
            answer=answer,
            groundedness_score=groundedness_score,
            is_grounded=is_grounded,
            citations=citations,
            must_confirm=must_confirm,
            execution_telemetry_id=telemetry_id,
        )

    def format_citation_text(self, citations: List[RAGSearchResult]) -> str:
        """Format citations into Markdown provenance footers."""
        if not citations:
            return ""

        lines = ["\n**Sources & Provenance:**"]
        for idx, res in enumerate(citations, start=1):
            meta = res.chunk.metadata
            page_info = f", Page {meta.page_number}" if meta.page_number else ""
            heading_info = f" ({meta.section_heading})" if meta.section_heading else ""
            lines.append(
                f"[{idx}] **{meta.title}**{heading_info} — *{meta.source_type.value if hasattr(meta.source_type, 'value') else meta.source_type}*{page_info} (Doc ID: {meta.document_id})"
            )
        return "\n".join(lines)
