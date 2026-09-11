#!/usr/bin/env python3
"""Reproducible test-inventory receipt (FND-0264 / ISS-007).

Why this exists: handoff receipts quoted three different suite totals in seven
days (3,718 / 4,250 / 4,350 "of 0"), none reproducible from the tree, and the
green total is conditional — integration tests auto-skip without a dev server,
Postgres-backed files skip without a database, and LLM-client tests skip
without provider keys. A receipt that cannot be reproduced cannot gate
anything.

What it reports (all mechanical, all reproducible):
  - collected_tests: pytest --collect-only count at the current tree
    (run in-process; no shell, no subprocess)
  - static_test_functions: count of ``def test_`` definitions on disk
  - skip_markers: files and hit counts of pytest.mark.skip / pytest.skip /
    xfail / skipif (the conditional-green surface)
  - ci_excluded_files: files CI deliberately ignores (optional deps)

Usage:
    .venv/bin/python tools/test_inventory.py                 # human summary
    .venv/bin/python tools/test_inventory.py --json          # machine receipt
    .venv/bin/python tools/test_inventory.py --json --out path/to/receipt.json

Read-only: never mutates the tree or environment.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import re
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
TESTS_DIR = REPO_ROOT / "tests"

# Files CI deliberately excludes (see .github/workflows/ci.yml) — they need
# provider API keys that the CI runner does not have.
CI_EXCLUDED_FILES = [
    "tests/test_vision_extraction.py",
    "tests/test_extraction_fallback.py",
]

_SKIP_RE = re.compile(r"pytest\.mark\.skip|pytest\.skip\(|pytest\.mark\.xfail|pytest\.mark\.skipif|pytest\.xfail")
_DEF_RE = re.compile(r"^\s*(?:async\s+)?def\s+test_")


def _collected_count() -> int:
    """Count tests pytest would collect right now (skips still collect).

    Runs pytest in-process with stdout captured — no shell, no subprocess.
    Returns -1 when collection itself fails; the receipt shows that rather
    than guessing.
    """
    import pytest

    captured = io.StringIO()
    with contextlib.redirect_stdout(captured):
        pytest.main(["tests/", "--collect-only", "-q", "--no-header", "-p", "no:cacheprovider"])
    for line in captured.getvalue().splitlines():
        line = line.strip()
        if line and line[0].isdigit() and "collected" in line:
            return int(line.split()[0])
    return -1


def _static_counts() -> tuple[int, dict]:
    """Count test-function definitions and skip-marker hits per file."""
    total_defs = 0
    skips: dict[str, int] = {}
    for path in sorted(TESTS_DIR.rglob("test_*.py")):
        text = path.read_text(encoding="utf-8", errors="replace")
        total_defs += sum(1 for line in text.splitlines() if _DEF_RE.match(line))
        hits = len(_SKIP_RE.findall(text))
        if hits:
            skips[str(path.relative_to(REPO_ROOT))] = hits
    return total_defs, skips


def build_inventory() -> dict:
    static_defs, skip_files = _static_counts()
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "tree": "uncommitted working tree at receipt time",
        "collected_tests": _collected_count(),
        "static_test_functions": static_defs,
        "skip_marked_files": skip_files,
        "skip_marker_total": sum(skip_files.values()),
        "ci_excluded_files": CI_EXCLUDED_FILES,
        "counting_basis": (
            "collected_tests = pytest --collect-only at this tree; "
            "a green run is conditional: integration tests auto-skip without a "
            "dev server (tests/conftest.py), Postgres-marked files skip without "
            "a database, LLM tests skip without provider keys. Quote this "
            "receipt (path + generated_at) instead of a bare total."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--json", action="store_true", help="emit the machine-readable receipt")
    parser.add_argument("--out", type=Path, default=None, help="also write the receipt to this path")
    args = parser.parse_args()

    inventory = build_inventory()

    if args.out:
        args.out.write_text(json.dumps(inventory, indent=2) + "\n", encoding="utf-8")

    if args.json:
        print(json.dumps(inventory, indent=2))
    else:
        print(f"collected tests       : {inventory['collected_tests']}")
        print(f"static test functions : {inventory['static_test_functions']}")
        print(f"skip-marked files     : {len(inventory['skip_marked_files'])} "
              f"({inventory['skip_marker_total']} markers)")
        print(f"CI-excluded files     : {len(inventory['ci_excluded_files'])}")
        print("Note: quote this receipt instead of a bare suite total (FND-0264).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
