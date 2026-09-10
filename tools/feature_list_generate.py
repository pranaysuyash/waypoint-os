#!/usr/bin/env python3
"""Generate JSON + CSV derivatives from a FEATURE_LIST markdown inventory.

The markdown file is the single source of truth. Domain sections use `## X) Title`
headings followed by a table with the exact header:

    | ID | Feature | Status | Priority | What it does | Evidence |

Usage:
    python3 tools/feature_list_generate.py \
        --md Docs/status/FEATURE_LIST_V3_2026-09-03.md \
        --json Docs/status/FEATURE_LIST_V3_2026-09-03.json \
        --csv  Docs/status/FEATURE_LIST_V3_2026-09-03.csv

Validates IDs, statuses, and priorities; exits non-zero on any parse problem so it
can double as a CI-style consistency check. Never hand-edit the derived files.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

VALID_STATUSES = {"LIVE", "PARTIAL", "GATED", "SIMULATED", "STUB", "SPEC", "EXPLORE"}
VALID_PRIORITIES = {"P0", "P1", "P2"}
HEADER = ["ID", "Feature", "Status", "Priority", "What it does", "Evidence"]
SECTION_RE = re.compile(r"^## ([A-Z])\) (.+)$")
ROW_RE = re.compile(r"^\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|$")


def parse(md_path: Path) -> list[dict]:
    records: list[dict] = []
    domain = ""
    seen_ids: set[str] = set()
    errors: list[str] = []

    for lineno, raw in enumerate(md_path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        section = SECTION_RE.match(line)
        if section:
            domain = f"{section.group(1)}) {section.group(2).strip()}"
            continue
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split(" | ")] if " | " in line else None
        match = ROW_RE.match(line)
        if not match:
            if [c.strip() for c in line.strip("|").split("|")] == HEADER:
                continue
            continue
        cells = [c.strip() for c in match.groups()]
        fid, name, status, priority, what, evidence = cells
        if fid == "ID":
            continue
        if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
            continue  # markdown delimiter row (|---|---|...)
        if fid in seen_ids:
            errors.append(f"line {lineno}: duplicate ID {fid}")
        seen_ids.add(fid)
        if status not in VALID_STATUSES:
            errors.append(f"line {lineno}: {fid} invalid status {status!r}")
        if priority not in VALID_PRIORITIES:
            errors.append(f"line {lineno}: {fid} invalid priority {priority!r}")
        records.append(
            {
                "id": fid,
                "domain": domain,
                "feature": name,
                "status": status,
                "priority": priority,
                "what_it_does": what,
                "evidence": [e.strip() for e in evidence.split(",") if e.strip()],
            }
        )

    if errors:
        for err in errors:
            print(f"ERROR: {err}", file=sys.stderr)
        sys.exit(1)
    if not records:
        print("ERROR: no records parsed", file=sys.stderr)
        sys.exit(1)
    return records


def write_json(records: list[dict], json_path: Path, md_path: Path) -> None:
    counts: dict[str, int] = {}
    for rec in records:
        counts[rec["status"]] = counts.get(rec["status"], 0) + 1
    payload = {
        "metadata": {
            "name": md_path.stem,
            "date": md_path.stem.rsplit("_", 1)[-1] if "_" in md_path.stem else "",
            "source_doc": md_path.as_posix(),
            "generator": "tools/feature_list_generate.py",
            "notes": "Derived from the markdown source of truth; regenerate, never hand-edit.",
        },
        "counts": {"total_features": len(records), **dict(sorted(counts.items()))},
        "records": records,
    }
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_csv(records: list[dict], csv_path: Path) -> None:
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["id", "domain", "feature", "status", "priority", "what_it_does", "evidence"])
        for rec in records:
            writer.writerow(
                [
                    rec["id"],
                    rec["domain"],
                    rec["feature"],
                    rec["status"],
                    rec["priority"],
                    rec["what_it_does"],
                    "; ".join(rec["evidence"]),
                ]
            )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--md", required=True, type=Path, help="Feature-list markdown source of truth")
    parser.add_argument("--json", required=True, type=Path, help="JSON output path")
    parser.add_argument("--csv", required=True, type=Path, help="CSV output path")
    args = parser.parse_args()

    records = parse(args.md)
    write_json(records, args.json, args.md)
    write_csv(records, args.csv)
    counts: dict[str, int] = {}
    for rec in records:
        counts[rec["status"]] = counts.get(rec["status"], 0) + 1
    summary = ", ".join(f"{k}={v}" for k, v in sorted(counts.items()))
    print(f"OK: {len(records)} features -> {args.json} + {args.csv} ({summary})")


if __name__ == "__main__":
    main()
