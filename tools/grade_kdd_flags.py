#!/usr/bin/env python3
"""Grade KDD experiment risk-flag arms against the curated ground-truth labels.

Completes KDD §7.5 item 2: converts added-flag counts into precision / recall /
F1. Labels: `data/fixtures/risk_flags/ground_truth_labels.json` (note-level
business reality — see the file's `_meta.rubric` for the fixed-before-grading
rubric and caveats).

Usage:
    python3 tools/grade_kdd_flags.py                       # grade all runs
    python3 tools/grade_kdd_flags.py records_ladder.jsonl  # grade one run

Matching is at flag-name level (does the arm emit the justified flag at all);
severity agreement is reported separately as `severity_exact` — the share of
matched flags whose severity equals the label. An emitted flag that is NOT in
the record's expected set counts as a false positive; a justified flag that is
missing counts as a false negative.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO = Path(__file__).resolve().parents[1]
LABELS_PATH = REPO / "data/fixtures/risk_flags/ground_truth_labels.json"
RUNS_DIR = REPO / "data/experiments/hybrid_kdd_v1"


def load_labels() -> Tuple[Dict[str, Dict[str, str]], set]:
    blob = json.loads(LABELS_PATH.read_text())
    labels = {rid: lab["expected"] for rid, lab in blob["labels"].items()}
    excluded = set(blob["_meta"].get("excluded_flags", {}))
    return labels, excluded


def grade_arm(
    rows: List[Dict[str, Any]],
    labels: Dict[str, Dict[str, str]],
    excluded: set = frozenset(),
) -> Optional[Dict[str, Any]]:
    tp = fp = fn = 0
    sev_matches = sev_total = 0
    fp_detail: List[Tuple[str, str]] = []
    fn_detail: List[Tuple[str, str]] = []
    graded = 0

    for r in rows:
        rid = r["record_id"]
        expected = labels.get(rid)
        if expected is None:
            continue
        graded += 1
        emitted: Dict[str, str] = {}
        for flag in r["risks"]:
            name = flag.get("flag")
            if name and name not in excluded:
                emitted[name] = flag.get("severity")
        for name, sev in expected.items():
            if name in emitted:
                tp += 1
                sev_total += 1
                if emitted[name] == sev:
                    sev_matches += 1
            else:
                fn += 1
                fn_detail.append((rid, name))
        for name, sev in emitted.items():
            if name not in expected:
                fp += 1
                fp_detail.append((rid, f"{name}({sev})"))

    if graded == 0:
        return None
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return {
        "graded_records": graded,
        "tp": tp, "fp": fp, "fn": fn,
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": round(f1, 3),
        "severity_exact": round(sev_matches / sev_total, 3) if sev_total else None,
        "fp_examples": fp_detail[:5],
        "fn_examples": fn_detail[:5],
    }


def main() -> int:
    args = sys.argv[1:]
    files = (
        [RUNS_DIR / a for a in args]
        if args
        else sorted(RUNS_DIR.glob("records*.jsonl"))
    )
    labels, excluded = load_labels()

    results: List[Tuple[str, Dict[str, Any]]] = []
    for path in files:
        if not path.exists():
            print(f"[skip] missing: {path}", file=sys.stderr)
            continue
        rows = [
            json.loads(line)
            for line in path.read_text().splitlines()
            if line.strip()
        ]
        arms = sorted(set(r["arm"] for r in rows))
        for arm in arms:
            g = grade_arm([r for r in rows if r["arm"] == arm], labels)
            if g:
                results.append((f"{path.name}::{arm}", g))

    print(f"{'run::arm':<62} {'P':>6} {'R':>6} {'F1':>6} {'sev✓':>6} {'tp/fp/fn':>10}")
    for name, g in results:
        sev = f"{g['severity_exact']:.2f}" if g["severity_exact"] is not None else "-"
        counts = f"{g['tp']}/{g['fp']}/{g['fn']}"
        print(f"{name:<62} {g['precision']:>6.3f} {g['recall']:>6.3f} {g['f1']:>6.3f} {sev:>6} {counts:>10}")

    # Persist a machine-readable receipt alongside the runs.
    out = RUNS_DIR / "grading_receipt.json"
    out.write_text(json.dumps({name: g for name, g in results}, indent=2))
    print(f"\n[grade] receipt: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
