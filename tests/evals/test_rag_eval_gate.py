"""RAG retrieval eval — deterministic CI gate (RAGAS-inspired metrics).

Runs the specialty-QA corpus (tests/evals/data/rag_specialty_qa_v1.json)
through the SERVING seam (``SpecialtyKnowledgeService.identify_niche``) on
the deterministic hash lane:

- retrieval hit-rate: positives must surface the expected niche as top hit
- negative rejection: negatives must return no niche

Gate: hit_rate == 1.0 AND negative_rejection == 1.0. The corpus is
deterministic against the hash lane; the semantic lane runs the same corpus
via ``tools/rag_eval.py --semantic`` (live, never gating CI).
"""

import json
import os
from pathlib import Path

import pytest

os.environ.setdefault("RUNNING_TESTS", "1")

from src.rag.service import RAGService
from src.intake.specialty_knowledge import SpecialtyKnowledgeService

CORPUS_PATH = Path(__file__).parent / "data" / "rag_specialty_qa_v1.json"

GATE_HIT_RATE = 1.0
GATE_NEGATIVE_REJECTION = 1.0


def _load_corpus():
    with open(CORPUS_PATH) as f:
        return json.load(f)["questions"]


def _evaluate(corpus, service, agency_id="agency_rag_eval"):
    SpecialtyKnowledgeService.ensure_seeded(agency_id, service)
    hits_expected = 0
    hits_correct = 0
    negatives = 0
    negatives_rejected = 0
    misses = []
    for q in corpus:
        hits = SpecialtyKnowledgeService.identify_niche(
            q["question"], agency_id=agency_id, rag_service=service
        )
        if q["negative"]:
            negatives += 1
            if not hits:
                negatives_rejected += 1
            else:
                misses.append({"q": q["question"], "got": [h.niche for h in hits]})
        else:
            hits_expected += 1
            if hits and hits[0].niche == q["expected_niche"]:
                hits_correct += 1
            else:
                misses.append(
                    {"q": q["question"], "want": q["expected_niche"], "got": [h.niche for h in hits]}
                )
    return {
        "hit_rate": hits_correct / hits_expected if hits_expected else 1.0,
        "negative_rejection": negatives_rejected / negatives if negatives else 1.0,
        "misses": misses,
    }


@pytest.fixture
def seeded_service(tmp_path):
    return RAGService(db_path=str(tmp_path / "rag_eval_gate.db"))


def test_rag_specialty_retrieval_gate(seeded_service):
    """S2-sensitive gate: the serving seam must retrieve the right niche and
    reject out-of-domain queries on the deterministic lane."""
    corpus = _load_corpus()
    result = _evaluate(corpus, seeded_service)
    assert result["hit_rate"] >= GATE_HIT_RATE, f"misses: {result['misses']}"
    assert result["negative_rejection"] >= GATE_NEGATIVE_REJECTION, (
        f"false positives: {result['misses']}"
    )
