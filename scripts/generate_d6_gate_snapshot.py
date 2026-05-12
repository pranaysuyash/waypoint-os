#!/usr/bin/env python3
"""Generate canonical D6 gate snapshot JSON for runtime authority decisions.

Usage:
  uv run python scripts/generate_d6_gate_snapshot.py
  uv run python scripts/generate_d6_gate_snapshot.py --output data/evals/d6_audit_gate_snapshot.json
  uv run python scripts/generate_d6_gate_snapshot.py --fixtures data/fixtures/audit
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.evals.audit.snapshot import (
    DEFAULT_FIXTURE_ROOT,
    DEFAULT_SNAPSHOT_PATH,
    write_gate_snapshot,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate D6 gate snapshot JSON.")
    parser.add_argument("--output", type=Path, default=DEFAULT_SNAPSHOT_PATH, help="Output snapshot path.")
    parser.add_argument("--fixtures", type=Path, default=DEFAULT_FIXTURE_ROOT, help="Fixture root path.")
    args = parser.parse_args()

    output_path = write_gate_snapshot(output_path=args.output, fixture_root=args.fixtures)
    print(f"D6 gate snapshot written: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
