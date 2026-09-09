#!/usr/bin/env python3
"""Failure-Mode Atlas v0 generator (WOBS P3).

Aggregates public-checker trips from the JSON file store into a source-keyed
failure table: plan-origin × destination × finding category. This is the
generator for the Atlas concept — publication waits for real corpus volume
(WOBS Part 3.2: "built when data exists").

Usage:
    python3 tools/failure_mode_atlas.py [--trips-dir data/trips] [--format markdown|json] [--min-count 1]

Read-only: never mutates trip data. SQL-backed trips are out of scope for v0
(file store only); the durable-store endgame (E-G) will unify this.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.public_checker.live_checks import extract_destination  # noqa: E402

_CATEGORY_KEYWORDS = {
    "visa": "visa",
    "passport": "documents",
    "insurance": "insurance",
    "monsoon": "weather-window",
    "weather": "weather",
    "season": "weather-window",
    "transfer": "logistics",
    "connection": "logistics",
    "timing": "logistics",
    "budget": "cost",
    "cost": "cost",
    "pace": "pacing",
    "toddler": "composition",
    "elderly": "composition",
    "senior": "composition",
    "wheelchair": "accessibility",
}


def categorize(finding_text: str) -> str:
    text = finding_text.lower()
    for keyword, category in _CATEGORY_KEYWORDS.items():
        if keyword in text:
            return category
    return "other"


def iter_public_checker_trips(trips_dir: Path):
    for path in sorted(trips_dir.glob("*.json")):
        try:
            trip = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if not isinstance(trip, dict):
            continue
        if trip.get("source") != "public_checker":
            continue
        yield trip


def build_atlas(trips_dir: Path, min_count: int = 1) -> Dict[str, Any]:
    rows: Counter = Counter()
    total_checks = 0
    destinations_seen: Counter = Counter()
    sources_seen: Counter = Counter()

    for trip in iter_public_checker_trips(trips_dir):
        meta = trip.get("meta") if isinstance(trip.get("meta"), dict) else {}
        plan_source = str(meta.get("declared_plan_source") or "unknown")
        decision = trip.get("decision") if isinstance(trip.get("decision"), dict) else {}
        packet = trip.get("packet") if isinstance(trip.get("packet"), dict) else {}
        findings = [
            str(item)
            for item in (decision.get("hard_blockers") or []) + (decision.get("soft_blockers") or [])
            if str(item).strip()
        ]
        total_checks += 1
        sources_seen[plan_source] += 1
        destination = extract_destination(packet, "") or "unknown"
        destinations_seen[destination] += 1
        for finding in findings:
            rows[(plan_source, destination, categorize(finding))] += 1

    table = [
        {"plan_source": source, "destination": destination, "category": category, "count": count}
        for (source, destination, category), count in sorted(
            rows.items(), key=lambda kv: -kv[1]
        )
        if count >= min_count
    ]
    return {
        "total_checks": total_checks,
        "checks_by_plan_source": dict(sources_seen),
        "checks_by_destination": dict(destinations_seen.most_common()),
        "failure_modes": table,
        "note": "Advisory findings only; counts are raw and uncalibrated (WOBS EX-06).",
    }


def render_markdown(atlas: Dict[str, Any]) -> str:
    lines = [
        "# Failure-Mode Atlas v0 (generated)",
        "",
        f"Total checks: **{atlas['total_checks']}**",
        "",
        "By plan source: " + ", ".join(f"{k}={v}" for k, v in atlas["checks_by_plan_source"].items()) or "none",
        "",
        "| plan source | destination | category | count |",
        "|---|---|---|---|",
    ]
    for row in atlas["failure_modes"]:
        lines.append(
            f"| {row['plan_source']} | {row['destination']} | {row['category']} | {row['count']} |"
        )
    if not atlas["failure_modes"]:
        lines.append("| — | — | no findings recorded yet | 0 |")
    lines += ["", atlas["note"], ""]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trips-dir", default="data/trips", type=Path)
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    parser.add_argument("--min-count", default=1, type=int)
    args = parser.parse_args()

    atlas = build_atlas(Path(args.trips_dir), min_count=args.min_count)
    if args.format == "json":
        print(json.dumps(atlas, indent=2, ensure_ascii=False))
    else:
        print(render_markdown(atlas))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
