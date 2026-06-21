#!/usr/bin/env python3
"""Verify canonical D6 gate snapshot is fresh and contract-compatible.

Usage:
  uv run python scripts/verify_d6_gate_snapshot.py
  uv run python scripts/verify_d6_gate_snapshot.py --write
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.evals.audit.snapshot import (  # noqa: E402
    DEFAULT_FIXTURE_ROOT,
    DEFAULT_SNAPSHOT_PATH,
    stable_snapshot_view,
    verify_gate_snapshot_file,
    write_gate_snapshot,
)


def _check_blocks_ci(snapshot: dict) -> list[dict]:
    """Check routing_health and extraction_health blocks_ci flags."""
    blockers: list[dict] = []

    routing_health = snapshot.get("routing_health")
    if isinstance(routing_health, dict) and routing_health.get("blocks_ci"):
        blockers.append({
            "gate": "routing_health",
            "status": routing_health.get("status", "unknown"),
            "reason": "routing_health.blocks_ci is true",
        })

    extraction_health = snapshot.get("extraction_health")
    if isinstance(extraction_health, dict) and extraction_health.get("blocks_ci"):
        blockers.append({
            "gate": "extraction_health",
            "status": extraction_health.get("status", "unknown"),
            "reason": f"extraction_health.blocks_ci is true (f1={extraction_health.get('overall_f1', 0)})",
        })

    pipeline_health = snapshot.get("pipeline_health")
    if isinstance(pipeline_health, dict) and pipeline_health.get("blocks_ci"):
        blockers.append({
            "gate": "pipeline_health",
            "status": pipeline_health.get("status", "unknown"),
            "reason": f"pipeline_health.blocks_ci is true (accuracy={pipeline_health.get('overall_accuracy', 0)})",
        })

    categories = snapshot.get("categories")
    if isinstance(categories, dict):
        for cat_name, cat_data in categories.items():
            if isinstance(cat_data, dict) and cat_data.get("blocks_ci"):
                blockers.append({
                    "gate": f"category:{cat_name}",
                    "status": cat_data.get("status", "unknown"),
                    "reason": f"category {cat_name} blocks_ci is true",
                })

    return blockers


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify D6 gate snapshot drift.")
    parser.add_argument("--write", action="store_true", help="Regenerate snapshot before verification.")
    parser.add_argument("--output", type=Path, default=DEFAULT_SNAPSHOT_PATH, help="Snapshot path.")
    parser.add_argument("--fixtures", type=Path, default=DEFAULT_FIXTURE_ROOT, help="Fixture root.")
    args = parser.parse_args()

    if args.write:
        write_gate_snapshot(output_path=args.output, fixture_root=args.fixtures)

    ok, expected, actual = verify_gate_snapshot_file(snapshot_path=args.output, fixture_root=args.fixtures)

    # Check for CI-blocking health gates
    snapshot_to_check = actual if isinstance(actual, dict) else expected
    ci_blockers = _check_blocks_ci(snapshot_to_check)

    if ok and not ci_blockers:
        print(json.dumps({"ok": True, "snapshot_path": str(args.output)}, indent=2))
        return 0

    payload = {
        "ok": False,
        "snapshot_path": str(args.output),
        "reason": "missing_or_drifted_snapshot" if not ok else "health_gate_failure",
        "expected_stable": stable_snapshot_view(expected),
        "actual_stable": stable_snapshot_view(actual) if isinstance(actual, dict) else None,
    }
    if ci_blockers:
        payload["ci_blockers"] = ci_blockers
    print(json.dumps(payload, indent=2))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

