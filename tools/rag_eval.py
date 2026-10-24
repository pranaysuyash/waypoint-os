"""RAG retrieval eval runner — reusable metrics over a QA corpus.

Runs tests/evals/data/rag_specialty_qa_v1.json (or --corpus) through the
serving seam (SpecialtyKnowledgeService.identify_niche) and prints
hit-rate / negative-rejection with misses. Mirrors the CI gate
(tests/evals/test_rag_eval_gate.py) as a standalone tool.

Lanes:
  default           — deterministic hash lane (offline, what CI gates)
  --semantic        — live OpenAI embeddings via RAG_EMBEDDING_PROVIDER=openai
                      (requires OPENAI_API_KEY; never gating; egress is
                      PII-stripped per the 2026-10-22 owner ruling)

Usage:
  uv run python tools/rag_eval.py
  uv run python tools/rag_eval.py --semantic
  uv run python tools/rag_eval.py --corpus path.json --agency my_agency
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.rag.service import RAGService  # noqa: E402
from src.intake.specialty_knowledge import SpecialtyKnowledgeService  # noqa: E402

DEFAULT_CORPUS = Path(__file__).resolve().parents[1] / "tests" / "evals" / "data" / "rag_specialty_qa_v1.json"


def evaluate(corpus_questions, service, agency_id):
    SpecialtyKnowledgeService.ensure_seeded(agency_id, service)
    hits_expected = hits_correct = negatives = negatives_rejected = 0
    misses = []
    for q in corpus_questions:
        hits = SpecialtyKnowledgeService.identify_niche(
            q["question"], agency_id=agency_id, rag_service=service
        )
        got = [h.niche for h in hits]
        if q["negative"]:
            negatives += 1
            if not got:
                negatives_rejected += 1
            else:
                misses.append({"q": q["question"], "want": None, "got": got})
        else:
            hits_expected += 1
            if got and got[0] == q["expected_niche"]:
                hits_correct += 1
            else:
                misses.append({"q": q["question"], "want": q["expected_niche"], "got": got})
    return {
        "hit_rate": hits_correct / hits_expected if hits_expected else 1.0,
        "negative_rejection": negatives_rejected / negatives if negatives else 1.0,
        "positives": hits_expected,
        "negatives": negatives,
        "misses": misses,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", default=str(DEFAULT_CORPUS))
    parser.add_argument("--agency", default="agency_rag_eval_tool")
    parser.add_argument(
        "--semantic",
        action="store_true",
        help="Live OpenAI embeddings lane (requires OPENAI_API_KEY; not a gate).",
    )
    parser.add_argument(
        "--fail-under", type=float, default=None,
        help="Optional gate: exit 1 when hit-rate or negative-rejection falls below this.",
    )
    args = parser.parse_args()

    if args.semantic:
        os.environ["RAG_EMBEDDING_PROVIDER"] = "openai"
        if not os.getenv("OPENAI_API_KEY"):
            print("--semantic requires OPENAI_API_KEY; refusing to fake a live lane.", file=sys.stderr)
            return 2

    with open(args.corpus) as f:
        questions = json.load(f)["questions"]

    service = RAGService(
        db_path=os.path.join(os.environ.get("RAG_STORE_PATH", "data"), f"rag_eval_{args.agency}.db")
    )
    result = evaluate(questions, service, args.agency)

    provider = service.embedding_provider
    print(f"corpus:            {args.corpus}")
    print(f"lane:              {provider.provider_name}:{provider.model_name} (semantic={provider.is_semantic})")
    print(f"hit_rate:          {result['hit_rate']:.3f}  ({result['positives']} positives)")
    print(f"negative_reject:   {result['negative_rejection']:.3f}  ({result['negatives']} negatives)")
    if result["misses"]:
        print("misses:")
        for m in result["misses"]:
            print(f"  - {m['q']!r} want={m['want']!r} got={m['got']}")
    if args.fail_under is not None:
        ok = (
            result["hit_rate"] >= args.fail_under
            and result["negative_rejection"] >= args.fail_under
        )
        print(f"gate (>={args.fail_under}): {'PASS' if ok else 'FAIL'}")
        return 0 if ok else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
