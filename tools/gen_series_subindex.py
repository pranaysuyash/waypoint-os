#!/usr/bin/env python3
"""Regenerate Docs/personas_scenarios/SERIES_INDEX.md.

Indexes the `ADDITIONAL_SCENARIOS_<N>_<SLUG>.md` series (303 docs as of
2026-09-10; FND-0256 B1) so the live-consumed corpus is discoverable from
Docs/INDEX.md without hand-maintaining 303 lines there.

Usage:
    python3 tools/gen_series_subindex.py          # regenerate
    python3 tools/gen_series_subindex.py --check   # exit 1 if out of date

The generated file is derived state — never hand-edit it; rerun this tool.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SERIES_DIR = REPO / "Docs" / "personas_scenarios"
OUT_FILE = SERIES_DIR / "SERIES_INDEX.md"
NAME_RE = re.compile(r"ADDITIONAL_SCENARIOS_(\d+)_(.+)\.md")
# Legacy compendium: <start>_<end> range in the filename, e.g. 21_25 covers
# "Scenarios 21-30" as sections inside one file.
RANGE_RE = re.compile(r"ADDITIONAL_SCENARIOS_(\d+)_(\d+)\.md")

HEADER = """# ADDITIONAL_SCENARIOS Series Sub-Index

Auto-generated index for the `ADDITIONAL_SCENARIOS_<N>_*.md` series under
`Docs/personas_scenarios/`. Regenerate after adding or removing series files
with: `python3 tools/gen_series_subindex.py`.
"""


def build_index() -> tuple[str, list[str], int]:
    singles: list[tuple[int, str, str]] = []
    compendia: list[tuple[str, str]] = []  # (sort key, name) for legacy range files
    for p in SERIES_DIR.glob("ADDITIONAL_SCENARIOS_*.md"):
        if RANGE_RE.match(p.name):
            # Legacy multi-scenario compendium (e.g. 21_25 = "Scenarios 21-30"
            # in one file). Index by filename; do not fabricate a per-scenario
            # number/slug from the range pair.
            compendia.append((p.name, p.name))
            continue
        m = NAME_RE.match(p.name)
        if not m:
            continue
        singles.append((int(m.group(1)), m.group(2), p.name))
    singles.sort(key=lambda e: e[0])  # numeric series order, not lexicographic
    compendia.sort()

    rows = ["| # | Title |", "|---|-------|"]
    for num, slug, name in singles:
        title = f"Additional Scenario {num}: {slug.replace('_', ' ').title()}"
        rows.append(f"| {num} | [{title}]({name}) |")
    if compendia:
        rows.append("")
        rows.append("### Legacy compendium files (multi-scenario, old format)")
        rows.append("")
        rows.append("| File |")
        rows.append("|------|")
        for _, name in compendia:
            rows.append(f"| [{name}]({name}) |")
    body = "\n".join([HEADER, *rows, "", f"Total: {len(singles)} single-scenario docs.", ""])
    return body, rows, len(singles)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true", help="exit 1 if index is stale")
    args = ap.parse_args()

    body, _rows, count = build_index()
    if args.check:
        current = OUT_FILE.read_text(encoding="utf-8") if OUT_FILE.exists() else ""
        if current != body:
            print(f"SERIES_INDEX.md is stale ({count} series docs on disk). Rerun without --check.")
            return 1
        print(f"SERIES_INDEX.md up to date ({count} docs).")
        return 0

    OUT_FILE.write_text(body, encoding="utf-8")
    print(f"wrote {OUT_FILE.relative_to(REPO)} with {count} entries")
    return 0


if __name__ == "__main__":
    sys.exit(main())
