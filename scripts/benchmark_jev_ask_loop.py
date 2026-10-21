#!/usr/bin/env python3
"""
E2 Jev ask-loop probe (Docs/exploration/E2_JEV_ASK_LOOP_PROBE_2026-09-29.md).

Runs LIVE against TypeSafe System One (Jev) using the ask_loop_golden fixtures:

  Probe 1 — question-rendering GRADING. Jev cannot generate text (jaggedness
  #9), so the probe tests the corrected role: Jev grades candidate renderings
  of an engine question against an explicit rubric (field-intent preserved,
  no new facts, traveler naturalness). Good renderings must pass both nouls;
  field-drift renderings must fail intent; fact-fabricating renderings must
  fail no-new-facts.

  Probe 2 — answer-ROUTING. Given an engine question + one free-text reply,
  Jev chooses which canonical packet field the reply answers (Choice over the
  FIELD_REQUIRED_FOR vocabulary + explicit 'unparsed'). Proposed values are
  never written directly — the deterministic extractor stack re-validates
  (hard boundary from the E2 doc).

Gates (E2 doc): Probe 1 defect-detection accuracy >= 0.95; Probe 2 field
routing >= 0.95 with wrong-field = automatic FAIL and non-answers routed to
the explicit 'unparsed' marker (zero silent drops).

Skips honestly when no Jev credentials are present.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from src.intake.ask_reply_router import FIELD_DESCRIPTIONS, UNPARSED_DESCRIPTION  # noqa: E402
from src.llm.typesafe_client import TypesafeJevClient  # noqa: E402

FIXTURES = REPO / "data/fixtures/extraction/ask_loop_golden.json"
RECEIPT = REPO / "data/experiments/hybrid_kdd_v1/ask_loop_probe_receipt.json"

FIELD_PROMPT_NAME = {
    "destination_candidates": "destination(s) of the trip",
    "date_window": "travel dates or date range",
    "origin_city": "departure city",
    "party_size": "number of travellers",
    "budget_raw_text": "trip budget",
    "trip_purpose": "purpose of the trip",
    "passport_status": "passport validity",
    "visa_status": "visa status",
    "dietary_requirements": "dietary requirements",
}

PROBE1_GATE = 0.95
PROBE2_GATE = 0.95


def run() -> int:
    client = TypesafeJevClient(model="jev-1.13.0")
    if not client.is_available():
        print("SKIP: no Jev credentials present (TYPESAFE_API_KEY/JEV_API_KEY).")
        return 2

    fixtures = json.loads(FIXTURES.read_text())
    questions = fixtures["questions"]

    p1_rows: list[dict] = []
    p2_rows: list[dict] = []
    t_start = time.perf_counter()

    print(f"E2 ask-loop probe: {len(questions)} questions x (3 renderings + 3 replies), live on {client.model}")
    print("=" * 88)

    # ---------------- Probe 1: rendering grading ----------------
    for q in questions:
        asked = FIELD_PROMPT_NAME[q["field_name"]]
        for kind in ("good", "drift", "fabricated"):
            rendering = q["renderings"][kind]
            state = (
                f"The travel agency's system needs to ask the traveler about: {asked}.\n"
                f"Original system question: \"{q['engine_question']}\"\n"
                f"Trip context: {q['packet_context']}\n"
                f"Proposed rephrasing to evaluate: \"{rendering}\""
            )
            resp = client.raw_query(state, {
                "preserves_field_intent": {
                    "type": "noul",
                    "instructions": (
                        f"Does this proposed rephrasing ask the traveler about exactly "
                        f"{asked} — and not about some other trip detail?"
                    ),
                },
                "introduces_no_new_facts": {
                    "type": "noul",
                    "instructions": (
                        "Does the proposed rephrasing avoid introducing any specific "
                        "place, date, number, or assumption that is not present in the "
                        "original system question? Answer yes only if it adds zero new specifics."
                    ),
                },
                "traveler_naturalness": {
                    "type": "score",
                    "instructions": (
                        "How naturally does this rephrasing read to a traveler, "
                        "including Hinglish-speaking travelers? 1 = robotic or confusing, "
                        "5 = something a human travel agent would say."
                    ),
                    "criteria": [
                        {"label": "1", "description": "Robotic, system-like, or confusing to a traveler"},
                        {"label": "2", "description": "Understandable but stiff or jargon-heavy"},
                        {"label": "3", "description": "Acceptable plain question"},
                        {"label": "4", "description": "Natural, friendly agent phrasing"},
                        {"label": "5", "description": "Exactly how a warm human agent would ask"},
                    ],
                },
            })
            answers = resp.get("answers", {})
            n_intent = float(answers.get("preserves_field_intent", {}).get("noul", 0.0))
            n_facts = float(answers.get("introduces_no_new_facts", {}).get("noul", 0.0))
            n_nat = answers.get("traveler_naturalness", {})
            score = n_nat.get("score")
            score_conf = n_nat.get("confidence")

            if kind == "good":
                caught = not (n_intent >= 0.5 and n_facts >= 0.5)
                verdict = "false_rejection" if caught else "pass"
            elif kind == "drift":
                caught = n_intent < 0.5
                verdict = "defect_caught" if caught else "missed"
            else:  # fabricated
                caught = n_facts < 0.5
                verdict = "defect_caught" if caught else "missed"
            p1_rows.append({
                "question_id": q["id"], "field": q["field_name"], "kind": kind,
                "rendering": rendering, "noul_intent": round(n_intent, 3),
                "noul_no_new_facts": round(n_facts, 3),
                "naturalness_score": score, "naturalness_confidence": score_conf,
                "verdict": verdict,
            })
            print(f"[P1 {q['id']:12s} {kind:10s}] intent={n_intent:.2f} facts={n_facts:.2f} "
                  f"nat={score} -> {verdict}")

    # ---------------- Probe 2: reply routing ----------------
    choice_criteria = {**FIELD_DESCRIPTIONS, "unparsed": UNPARSED_DESCRIPTION}
    for q in questions:
        for kind in ("direct", "colloquial", "nonanswer", "implicit_answer"):
            reply = q["replies"][kind]
            state = (
                f"The travel agency asked the traveler: \"{q['engine_question']}\"\n"
                f"The traveler replied: \"{reply}\""
            )
            resp = client.raw_query(state, {
                "answered_field": {
                    "type": "choice",
                    "instructions": (
                        "Which piece of trip information does this reply actually answer? "
                        "If it answers none of them, choose 'unparsed'."
                    ),
                    "criteria": choice_criteria,
                },
                "reply_contains_answer": {
                    "type": "noul",
                    "instructions": (
                        "Does the reply contain a usable answer to the question that was asked?"
                    ),
                },
            })
            answers = resp.get("answers", {})
            routed = answers.get("answered_field", {}).get("choice")
            routed_conf = answers.get("answered_field", {}).get("confidence")
            noul_ans = float(answers.get("reply_contains_answer", {}).get("noul", 0.0))

            if kind == "nonanswer":
                ok = routed == "unparsed"
                verdict = "unparsed_ok" if ok else f"wrong:{routed}"
            elif kind == "implicit_answer":
                # First run (2026-10-13) showed two fixtures labelled nonanswer were
                # implicit answers ('applying...', 'standard is fine') — labels
                # corrected; the model must not mark an implicit answer unparsed.
                if routed == "unparsed":
                    verdict = "silent_drop"
                else:
                    verdict = f"implicit_routed:{routed}"
            else:
                ok = routed == q["field_name"]
                verdict = "routed_ok" if ok else f"wrong:{routed}"
            p2_rows.append({
                "question_id": q["id"], "expected_field": q["field_name"], "kind": kind,
                "reply": reply, "routed_to": routed, "routing_confidence": routed_conf,
                "noul_contains_answer": round(noul_ans, 3), "verdict": verdict,
            })
            print(f"[P2 {q['id']:12s} {kind:10s}] routed={routed} (conf={routed_conf}) "
                  f"noul_ans={noul_ans:.2f} -> {verdict}")

    # ---------------- Aggregates + gates ----------------
    total_ms = (time.perf_counter() - t_start) * 1000

    good = [r for r in p1_rows if r["kind"] == "good"]
    drift = [r for r in p1_rows if r["kind"] == "drift"]
    fab = [r for r in p1_rows if r["kind"] == "fabricated"]
    p1 = {
        "defect_detection_accuracy": (
            sum(1 for r in drift + fab if r["verdict"] == "defect_caught") / (len(drift) + len(fab))
        ),
        "drift_caught": sum(1 for r in drift if r["verdict"] == "defect_caught"),
        "drift_total": len(drift),
        "fabrication_caught": sum(1 for r in fab if r["verdict"] == "defect_caught"),
        "fabrication_total": len(fab),
        "good_acceptance_rate": sum(1 for r in good if r["verdict"] == "pass") / len(good),
        "mean_naturalness_good": _mean([r["naturalness_score"] for r in good if r["naturalness_score"] is not None]),
        "mean_naturalness_all": _mean([r["naturalness_score"] for r in p1_rows if r["naturalness_score"] is not None]),
        "gate": PROBE1_GATE,
    }
    p1["pass"] = p1["defect_detection_accuracy"] >= p1["gate"]

    routed = [r for r in p2_rows if r["kind"] in ("direct", "colloquial")]
    nonans = [r for r in p2_rows if r["kind"] == "nonanswer"]
    implicit = [r for r in p2_rows if r["kind"] == "implicit_answer"]
    wrong_field = [r for r in routed if r["routed_to"] not in (r["expected_field"], "unparsed")]
    p2 = {
        "routing_accuracy": sum(1 for r in routed if r["verdict"] == "routed_ok") / len(routed),
        "unparsed_routing_accuracy": sum(1 for r in nonans if r["verdict"] == "unparsed_ok") / len(nonans),
        "implicit_answer_not_dropped": sum(1 for r in implicit if r["verdict"] != "silent_drop") / len(implicit),
        "wrong_field_count": len(wrong_field),
        "wrong_field_rate": len(wrong_field) / len(routed),
        "silent_drop_count": sum(1 for r in nonans if r["routed_to"] != "unparsed")
        + sum(1 for r in implicit if r["verdict"] == "silent_drop"),
        "mean_routing_confidence": _mean([r["routing_confidence"] for r in p2_rows if r["routing_confidence"] is not None]),
        "gate": PROBE2_GATE,
    }
    p2["pass"] = (
        p2["routing_accuracy"] >= p2["gate"]
        and p2["wrong_field_count"] == 0
        and p2["silent_drop_count"] == 0
    )

    print("=" * 88)
    print(f"Probe 1 defect-detection: {p1['defect_detection_accuracy']:.3f} "
          f"(drift {p1['drift_caught']}/{p1['drift_total']}, fabrication {p1['fabrication_caught']}/{p1['fabrication_total']}, "
          f"good acceptance {p1['good_acceptance_rate']:.3f}) -> GATE {'PASS' if p1['pass'] else 'FAIL'} (>= {p1['gate']})")
    print(f"Probe 2 routing: accuracy {p2['routing_accuracy']:.3f}, unparsed {p2['unparsed_routing_accuracy']:.3f}, "
          f"implicit-kept {p2['implicit_answer_not_dropped']:.3f}, "
          f"wrong-field {p2['wrong_field_count']}, silent-drops {p2['silent_drop_count']} -> "
          f"GATE {'PASS' if p2['pass'] else 'FAIL'} (>= {p2['gate']})")
    print(f"Wall time {total_ms/1000:.1f}s")

    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT.write_text(json.dumps({
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "model": client.model,
        "doc": "Docs/exploration/E2_JEV_ASK_LOOP_PROBE_2026-09-29.md",
        "probe1_grading": {"gate": PROBE1_GATE, **p1, "rows": p1_rows},
        "probe2_routing": {"gate": PROBE2_GATE, **p2, "rows": p2_rows},
        "wall_time_ms": round(total_ms, 1),
    }, indent=2))
    print(f"Receipt saved: {RECEIPT}")
    return 0 if (p1["pass"] and p2["pass"]) else 1


def _mean(values: list) -> float | None:
    return round(sum(values) / len(values), 3) if values else None


if __name__ == "__main__":
    sys.exit(run())
