#!/usr/bin/env python3
"""Recount the Research Opportunity Master List (Docs/research/RESEARCH_OPPORTUNITY_MASTER_LIST_2026-04-25.md).

The file's own summary tables drifted from its content (three mutually
inconsistent totals: prose 1,897 / table 1,903 / actual count). This tool
recounts ground truth so the tables can be regenerated from reality:

  - Categories = `## XX. TITLE` headers.
  - Total items = every `- ` bullet (any indent) under the category.
  - Status columns = bullets whose first non-space char is ✅ 🟡 ❌ 🔵.
    Content-Prism topic bullets (🟢/🔷/🟠 and other non-status bullets)
    count toward Total only — honest, no forced bucket.

Usage:
  python3 tools/master_list_recount.py                 # print recount
  python3 tools/master_list_recount.py --json out.json # also dump machine-readable
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

MASTER = Path("Docs/research/RESEARCH_OPPORTUNITY_MASTER_LIST_2026-04-25.md")
HEADER_RE = re.compile(r"^## ([A-Z]{1,2})[A-B]?\. (.+)$")
# Category IDs in this file are 1-2 letters (A..Z, AA..BE); BE has no dot-letter
# collision but "## BE." matches [A-Z]{1,2}\. fine.
STATUS = ("✅", "🟡", "❌", "🔵")


def recount(text: str) -> list[dict]:
    categories: list[dict] = []
    current: dict | None = None
    for line in text.splitlines():
        header = HEADER_RE.match(line)
        if header:
            current = {"id": header.group(1), "title": header.group(2).strip(),
                       "total": 0, "done": 0, "partial": 0, "open": 0, "new": 0,
                       "unmarked": 0}
            categories.append(current)
            continue
        if current is None:
            continue
        stripped = line.lstrip()
        if not stripped.startswith("- "):
            continue
        current["total"] += 1
        marker = stripped[2]
        if marker == "✅":
            current["done"] += 1
        elif marker == "🟡":
            current["partial"] += 1
        elif marker == "❌":
            current["open"] += 1
        elif marker == "🔵":
            current["new"] += 1
        else:
            current["unmarked"] += 1
    return categories


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--json", help="optional output path for machine-readable recount")
    args = parser.parse_args()

    categories = recount(MASTER.read_text())
    rows = [(f"{c['id']}. {c['title']}", c) for c in categories]

    width = max(len(name) for name, _ in rows) + 2
    print(f"{'Category'.ljust(width)} Total  ✅  🟡  ❌  🔵  other")
    grand = {"total": 0, "done": 0, "partial": 0, "open": 0, "new": 0, "unmarked": 0}
    for name, c in rows:
        print(f"{name.ljust(width)} {c['total']:5d} {c['done']:3d} {c['partial']:3d} "
              f"{c['open']:3d} {c['new']:3d} {c['unmarked']:5d}")
        for k in grand:
            grand[k] += c[k]
    print(f"{'TOTAL'.ljust(width)} {grand['total']:5d} {grand['done']:3d} {grand['partial']:3d} "
          f"{grand['open']:3d} {grand['new']:3d} {grand['unmarked']:5d}")
    print(f"\ncategories found: {len(categories)}")
    print(f"grand: total={grand['total']} done={grand['done']} partial={grand['partial']} "
          f"open={grand['open']} new={grand['new']} unmarked={grand['unmarked']}")

    if args.json:
        Path(args.json).write_text(json.dumps({"categories": categories, "grand": grand}, indent=2))
        print(f"json written: {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
