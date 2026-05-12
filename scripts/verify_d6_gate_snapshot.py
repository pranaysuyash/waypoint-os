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


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify D6 gate snapshot drift.")
    parser.add_argument("--write", action="store_true", help="Regenerate snapshot before verification.")
    parser.add_argument("--output", type=Path, default=DEFAULT_SNAPSHOT_PATH, help="Snapshot path.")
    parser.add_argument("--fixtures", type=Path, default=DEFAULT_FIXTURE_ROOT, help="Fixture root.")
    args = parser.parse_args()

    if args.write:
        write_gate_snapshot(output_path=args.output, fixture_root=args.fixtures)

    ok, expected, actual = verify_gate_snapshot_file(snapshot_path=args.output, fixture_root=args.fixtures)
    if ok:
        print(json.dumps({"ok": True, "snapshot_path": str(args.output)}, indent=2))
        return 0

    payload = {
        "ok": False,
        "snapshot_path": str(args.output),
        "reason": "missing_or_drifted_snapshot",
        "expected_stable": stable_snapshot_view(expected),
        "actual_stable": stable_snapshot_view(actual) if isinstance(actual, dict) else None,
    }
    print(json.dumps(payload, indent=2))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

