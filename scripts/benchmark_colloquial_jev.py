#!/usr/bin/env python3
"""
Benchmark script: evaluate IntakeAmbiguityClassifier across the 16 colloquial fixtures.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from src.intake.ambiguity_classifier import IntakeAmbiguityClassifier
from src.llm.typesafe_client import TypesafeJevClient


def run_benchmark():
    fixtures_path = REPO / "data/fixtures/extraction/colloquial_golden.json"
    fixtures = json.loads(fixtures_path.read_text())

    client = TypesafeJevClient(model="jev-1.13.0")
    classifier = IntakeAmbiguityClassifier(client=client)

    print(f"Running colloquial benchmark across {len(fixtures)} fixtures using {client.model}...")
    print("=" * 80)

    results = []
    total_time = 0.0

    for fx in fixtures:
        fid = fx["fixture_id"]
        raw_text = fx["raw_input"]

        t0 = time.perf_counter()
        report = classifier.evaluate(raw_text)
        elapsed = time.perf_counter() - t0
        total_time += elapsed

        dims = {k: "✓" if v.is_clear else "✗" for k, v in report.dimensions.items()}
        print(
            f"[{fid:26s}] ({elapsed*1000:5.0f}ms) -> Action: {report.action:12s} "
            f"Dest:{dims['destination']} Dates:{dims['dates']} Party:{dims['party']} Budget:{dims['budget']} "
            f"| Text: \"{raw_text}\""
        )
        results.append({
            "fixture_id": fid,
            "raw_input": raw_text,
            "action": report.action,
            "source": report.source,
            "missing": report.missing_dimensions,
            "elapsed_ms": round(elapsed * 1000, 1),
        })

    avg_latency = total_time / len(fixtures) * 1000
    print("=" * 80)
    print(f"Benchmark completed: {len(fixtures)} cases in {total_time:.2f}s (avg {avg_latency:.1f}ms/call)")

    out_path = REPO / "data/experiments/hybrid_kdd_v1/colloquial_benchmark_results.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps({
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "model": client.model,
        "total_fixtures": len(fixtures),
        "avg_latency_ms": avg_latency,
        "results": results,
    }, indent=2))
    print(f"Saved benchmark receipt to: {out_path}")


if __name__ == "__main__":
    run_benchmark()
