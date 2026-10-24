"""
tools/finding_to_fixture.py — Invariant 5 (failure flywheel): turn a finding's
reproducing input into an adversarial-corpus scenario in one action.

Roadmap: Docs/architecture/LONG_TERM_STRUCTURAL_ROADMAP_2026-10-23.md
Invariant 5. The seed corpus (data/fixtures/adversarial/adversarial_seed_v1.json)
owns the schema; this tool appends a scenario with finding-id provenance and
bumps the per-class summary atomically (single write, dry-run by default).

Usage:
    .venv/bin/python tools/finding_to_fixture.py \\
        --finding FND-0329 --input-file note.txt \\
        --expected "destination_candidates == ['Japan']" \\
        [--corpus data/fixtures/adversarial/adversarial_seed_v1.json] [--apply]
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DEFAULT_CORPUS = REPO / "data" / "fixtures" / "adversarial" / "adversarial_seed_v1.json"


def build_scenario(finding_id: str, input_text: str, expected: str, source: str) -> dict:
    """Pure builder — the scenario shape mirrors the seed corpus's records."""
    return {
        "id": f"fixture_{finding_id.lower().replace('-', '_')}_{input_text[:12].strip().replace(' ', '_')}",
        "finding_id": finding_id,
        "input": input_text,
        "expected_properties": [expected],
        "status": "passes_today" if source == "verified_fix" else "unverified",
        "provenance": {
            "origin": "finding_flywheel",
            "finding_id": finding_id,
            "added_at": datetime.now(timezone.utc).isoformat(),
        },
    }


def apply_scenario(corpus: dict, scenario: dict) -> dict:
    """Pure: return the updated corpus document with the scenario appended."""
    out = json.loads(json.dumps(corpus))  # deep copy
    scenarios = out.setdefault("scenarios", [])
    scenarios = [s for s in scenarios if s.get("id") != scenario["id"]]
    scenarios.append(scenario)
    out["scenarios"] = scenarios
    summary = out.setdefault("summary", {"total": 0})
    summary["total"] = len(scenarios)
    out["flywheel_appended"] = scenario["finding_id"]
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--finding", required=True, help="Finding id, e.g. FND-0329")
    ap.add_argument("--input-file", required=True, help="File with the verbatim reproducing input")
    ap.add_argument("--expected", required=True, help="Expected property, e.g. \"destination_candidates == ['Japan']\"")
    ap.add_argument("--corpus", default=str(DEFAULT_CORPUS))
    ap.add_argument("--source", default="registered", choices=["registered", "verified_fix"])
    ap.add_argument("--apply", action="store_true", help="write (default: print the scenario only)")
    args = ap.parse_args()

    input_text = Path(args.input_file).read_text()
    scenario = build_scenario(args.finding, input_text, args.expected, args.source)
    print(json.dumps(scenario, indent=2, ensure_ascii=False))
    if args.apply:
        corpus = json.loads(Path(args.corpus).read_text())
        corpus = apply_scenario(corpus, scenario)
        Path(args.corpus).write_text(json.dumps(corpus, indent=2, ensure_ascii=False))
        print(f"applied to {args.corpus}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
