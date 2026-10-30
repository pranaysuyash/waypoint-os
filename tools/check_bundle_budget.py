#!/usr/bin/env python3
"""
tools/check_bundle_budget.py — shared-JS bundle budget guard (FND-0390).

Runs `next build` in frontend/, parses the "First Load JS shared by all" total
from the build output, and fails when it exceeds the budget. Rationale: the
departure-board landing (FND-0386) introduced a large interactive component on
the public route; nothing guarded against the shared bundle creeping. This tool
is the guard — run it before any landing/marketing change merges.

Budget: 200 kB default (≈2.3× the 2026-10-26 measured 88.1 kB), overridable via
--budget-kb or WAYPOINT_BUNDLE_BUDGET_KB. Raising the budget is a decision —
the tool prints the current measurement so the raise is informed, not accidental.

Usage:
  python3 tools/check_bundle_budget.py
  python3 tools/check_bundle_budget.py --budget-kb 250 --skip-build
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
FRONTEND = REPO / "frontend"
DEFAULT_BUDGET_KB = 200.0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--budget-kb", type=float,
                    default=float(os.environ.get("WAYPOINT_BUNDLE_BUDGET_KB", DEFAULT_BUDGET_KB)))
    ap.add_argument("--skip-build", action="store_true",
                    help="parse the last saved receipt instead of rebuilding")
    args = ap.parse_args()

    receipt = FRONTEND / ".next" / "bundle_budget_receipt.json"
    if args.skip_build and receipt.exists():
        measured = float(receipt.read_bytes().split(b'"shared_first_load_kb":')[1].split(b",")[0])
    else:
        build = subprocess.run(
            ["npx", "next", "build"],
            cwd=FRONTEND, capture_output=True, text=True,
        )
        if build.returncode != 0:
            print("bundle-budget: FAIL — next build failed", file=sys.stderr)
            print(build.stderr[-800:], file=sys.stderr)
            return 1
        m = re.search(r"First Load JS shared by all\s+([\d.]+)\s*kB", build.stdout)
        if not m:
            print("bundle-budget: FAIL — could not parse shared-JS total from build output",
                  file=sys.stderr)
            return 1
        measured = float(m.group(1))
        receipt.write_text(
            f'{{"shared_first_load_kb": {measured}, "budget_kb": {args.budget_kb}}}\n'
        )

    verdict = "OK" if measured <= args.budget_kb else "OVER BUDGET"
    print(f"shared First Load JS: {measured} kB / budget {args.budget_kb:g} kB — {verdict}")
    if measured > args.budget_kb:
        print(
            "bundle-budget: the shared bundle grew past the budget. Before raising the",
            "budget, identify the regression (npx @next/bundle-analyzer) and prefer",
            "dynamic imports / route-level code splitting over a silent raise.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
