"""Heuristic groundedness evaluation and citation provenance engine.

Evaluates answer overlap and retrieval scores against retrieved chunks, then
generates document citations and operator confirmation flags.  The evaluator
can flag likely unsupported answers; it cannot prove truth or prevent
hallucinations, especially when a caller supplies an external generator.
"""

import re
import uuid
from decimal import Decimal
from typing import List
from src.rag.models import RAGSearchResult, GroundedAnswer


_CURRENCY = r"USD|INR|EUR|GBP|AED|SAR|JPY|CNY|NPR|LKR|PHP|MYR|THB|IDR|MXN|BRL|AUD|CAD|SGD|NGN|ZAR|KES|GHS|[$₹€£]"
_QUANTITY = re.compile(
    rf"(?<!\w)(?:(?P<currency>{_CURRENCY})\s*)?"
    r"(?P<number>\d[\d,]*(?:\.\d+)?)"
    rf"(?:\s*(?P<unit>%|percent\b|days?\b|months?\b|years?\b|hours?\b|nights?\b|kg\b|{_CURRENCY}\b))?",
    re.IGNORECASE,
)


def _source_text(result: RAGSearchResult) -> str:
    source = result.chunk.metadata.source_text
    return source if source is not None else result.chunk.content


def _quantities(text: str) -> set[tuple[Decimal, str, str]]:
    """Bounded numeric-support check, never a claim entailment classifier.

    Decimal preserves exact decimal values; units/currencies remain separate
    so 100 INR cannot be supported by 100 USD. Ambiguous symbols such as $
    are intentionally not silently promoted to an ISO currency.
    """
    quantities = set()
    for match in _QUANTITY.finditer(text):
        number = Decimal(match.group("number").replace(",", ""))
        currency = (match.group("currency") or "").upper()
        unit = (match.group("unit") or "").lower()
        if unit.upper() in _CURRENCY.split("|"):
            currency = f"{currency}/{unit.upper()}" if currency else unit.upper()
            unit = ""
        if unit == "percent":
            unit = "%"
        elif unit.endswith("s"):
            unit = unit[:-1]
        quantities.add((number, currency, unit))
    return quantities


def _is_literal_excerpt(answer: str, source_texts: list[str]) -> bool:
    # The service's default assembly adds this fixed heading. Every remaining
    # paragraph must still be a verbatim source span after whitespace folding.
    candidate = answer.removeprefix("Based on retrieved documents:\n\n")
    paragraphs = [" ".join(part.split()) for part in candidate.split("\n\n") if part.strip()]
    sources = [" ".join(source.split()) for source in source_texts]
    return bool(paragraphs) and all(any(part in source for source in sources) for part in paragraphs)


class GroundednessEvaluator:
    def __init__(self, min_confidence_threshold: float = 0.75):
        self.min_confidence_threshold = min_confidence_threshold

    def evaluate_answer(
        self,
        query: str,
        answer: str,
        citations: List[RAGSearchResult],
    ) -> GroundedAnswer:
        """Estimate support from retrieved citations using local heuristics.

        The score is not calibrated confidence or a claim-level entailment
        proof.  A passing result still requires domain-appropriate source and
        operator review for high-stakes facts.
        """
        telemetry_id = f"rag_eval_{uuid.uuid4().hex[:8]}"

        source_texts = [_source_text(citation) for citation in citations]
        if not citations or not any(source.strip() for source in source_texts):
            return GroundedAnswer(
                query=query,
                answer=answer,
                groundedness_score=0.0,
                is_grounded=False,
                citations=citations,
                must_confirm=["No supporting documentation found in agency knowledge base."],
                execution_telemetry_id=telemetry_id,
                claim_support_status="no_sources",
            )

        if not answer.strip():
            return GroundedAnswer(
                query=query, answer=answer, groundedness_score=0.0,
                is_grounded=False, citations=citations,
                must_confirm=["No answer was produced. Review the retrieved source documentation."],
                execution_telemetry_id=telemetry_id,
                claim_support_status="empty_answer",
            )

        # Compute groundedness score from token overlap, with retrieval
        # presence as the relevance signal. Retrieval confidence is 1.0 when
        # the retriever surfaced any citation (rank fusion already decided
        # relevance) and 0.0 otherwise — deliberately SCALE-FREE across
        # lexical backends (FTS bm25 vs substring counts return
        # incomparable raw numbers; binding this input to a backend's raw
        # score made groundedness move when the lexical leg was swapped,
        # not when relevance changed). Neither presence nor overlap proves
        # that a source entails the answer's claims.
        retrieval_confidence = 1.0 if citations else 0.0

        # Word overlap check between answer and retrieved chunk contents
        answer_words = set(w.lower() for w in answer.split() if len(w) > 3)
        chunk_words = set()
        for source in source_texts:
            chunk_words.update(w.lower() for w in source.split() if len(w) > 3)

        overlap_ratio = len(answer_words.intersection(chunk_words)) / max(1, len(answer_words))
        
        # Groundedness score combines retrieval confidence + overlap ratio
        groundedness_score = min(1.0, round((retrieval_confidence * 0.4) + (overlap_ratio * 0.6), 2))
        is_grounded = groundedness_score >= self.min_confidence_threshold

        source_quantities = set().union(*(_quantities(source) for source in source_texts))
        unsupported = _quantities(answer) - source_quantities
        literal_excerpt = _is_literal_excerpt(answer, source_texts)
        support_status = "source_excerpt" if literal_excerpt else "not_verified"

        must_confirm = []
        if not is_grounded:
            must_confirm.append(
                f"Low grounding confidence ({groundedness_score:.2f} < {self.min_confidence_threshold}). "
                "Operator must verify document details before client proposal."
            )
        if unsupported:
            is_grounded = False
            groundedness_score = 0.0
            support_status = "unsupported_numeric"
            must_confirm.append(
                "One or more numbers, currencies, or units in the answer are not supported "
                "by the cited source text. Verify the original document before using these claims."
            )
        elif not literal_excerpt:
            must_confirm.append(
                "Claim support has not been verified. Word overlap and matching numbers "
                "do not establish that the cited sources support the answer's meaning."
            )

        return GroundedAnswer(
            query=query,
            answer=answer,
            groundedness_score=groundedness_score,
            is_grounded=is_grounded,
            citations=citations,
            must_confirm=must_confirm,
            execution_telemetry_id=telemetry_id,
            lexical_overlap_score=round(overlap_ratio, 4),
            claim_support_status=support_status,
        )

    def format_citation_text(self, citations: List[RAGSearchResult]) -> str:
        """Format citations into Markdown provenance footers with verbatim
        excerpts (``source_text`` is the citable truth — content may be a
        retrieval-optimized rendering)."""
        if not citations:
            return ""

        lines = ["\n**Sources & Provenance:**"]
        for idx, res in enumerate(citations, start=1):
            meta = res.chunk.metadata
            page_info = f", Page {meta.page_number}" if meta.page_number else ""
            heading_info = f" ({meta.section_heading})" if meta.section_heading else ""
            lines.append(
                f"[{idx}] **{meta.title}**{heading_info} — *{meta.source_type.value if hasattr(meta.source_type, 'value') else meta.source_type}*{page_info} (Doc ID: {meta.document_id}, license: {meta.license_class})"
            )
            if res.retrieval_method == "parent_context":
                lines.append("    ↳ parent section context for a child hit")
                continue
            excerpt = (meta.source_text or res.chunk.content or "").strip()
            if excerpt:
                if len(excerpt) > 160:
                    excerpt = excerpt[:157] + "..."
                lines.append(f"    > {excerpt}")
        return "\n".join(lines)
