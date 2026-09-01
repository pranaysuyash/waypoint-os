#!/usr/bin/env python3
"""check_findings_register.py — enforce the findings lifecycle state machine.

Background (EX-06, FINDINGS_LIFECYCLE_2026-08-30.md): ~25 audits produced
findings with no lifecycle — no status, owner, or re-verification date — so
findings could only be re-discovered, never closed. This checker makes the
lifecycle mechanical for markdown register tables (our canonical register
format).

Per table row whose first column is a finding ID (e.g. R-03, A-14, F-01):
  - status is derived from markers in the row text:
      fixed/closed/resolved/wontfix/superseded/no-go/rejected -> terminal
      deferred/conditional/trap                               -> deferred
      otherwise                                               -> open
  - last-verified date is the latest YYYY-MM-DD in the row, falling back to
    the document's own date (H1/H2 "Date:" line or the first date in the doc).

Checks (exit 1 on any violation):
  1. duplicate ID rows within a file
  2. a row with no recognizable finding ID format is ignored; an ID row that
     cannot be parsed at all is an error
  3. open findings whose last-verified date is older than --max-age days

Usage:
  python3 scripts/check_findings_register.py Docs/review/FINDINGS_TASKS_CONSOLIDATED_2026-08-30.md
  python3 scripts/check_findings_register.py --max-age 30 <file1.md> <file2.md>
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
from pathlib import Path

ID_PATTERN = re.compile(r"^[A-Z]{1,4}-\d{1,4}\b")
DATE_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}")
DATE_LINE_PATTERN = re.compile(r"\*\*Date:\*\*\s*(\d{4}-\d{2}-\d{2})")

TERMINAL_MARKERS = ("resolved", "fixed", "closed", "wontfix", "won't fix", "superseded", "no-go", "rejected")
DEFERRED_MARKERS = ("deferred", "conditional", "trap", "no-go-for-now")


def _doc_date(text: str) -> dt.date | None:
    match = DATE_LINE_PATTERN.search(text)
    if match:
        return dt.date.fromisoformat(match.group(1))
    dates = DATE_PATTERN.findall(text[:2000])
    if dates:
        return dt.date.fromisoformat(dates[0])
    return None


def _row_status(row_text: str) -> str:
    lowered = row_text.lower()
    for marker in TERMINAL_MARKERS:
        if marker in lowered:
            # "no-go-for-now" and "conditional trap" entries are recorded but
            # not actionable; treat as deferred so they are not re-proposed.
            if marker == "no-go" and "for-now" in lowered:
                return "deferred"
            return "closed"
    for marker in DEFERRED_MARKERS:
        if marker in lowered:
            return "deferred"
    return "open"


def parse_register(path: Path) -> tuple[list[dict], dt.date | None]:
    text = path.read_text(encoding="utf-8")
    doc_date = _doc_date(text)
    findings: list[dict] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if not cells or cells[0] in ("", "ID") or set(cells[0]) <= {"-", ":", " "}:
            continue
        match = ID_PATTERN.match(cells[0])
        if not match:
            continue
        # The register's own date is when its rows were verified; in-row dates
        # only raise it (e.g. "RESOLVED 2026-08-30"), never lower it — rows
        # often cite other docs' older dates as references.
        row_dates = [dt.date.fromisoformat(d) for d in DATE_PATTERN.findall(stripped)]
        last_verified = max(row_dates) if row_dates else doc_date
        if doc_date is not None and last_verified is not None:
            last_verified = max(last_verified, doc_date)
        findings.append({
            "id": cells[0].split()[0].rstrip(":"),
            "status": _row_status(stripped),
            "last_verified": last_verified,
            "line": text[: text.index(line)].count("\n") + 1,
        })
    return findings, doc_date


def check(paths: list[Path], max_age_days: int) -> tuple[list[str], list[str], dict[str, int]]:
    errors: list[str] = []
    warnings: list[str] = []
    counts = {"open": 0, "closed": 0, "deferred": 0}
    today = dt.date.today()

    for path in paths:
        findings, doc_date = parse_register(path)
        seen: dict[str, int] = {}
        for f in findings:
            counts[f["status"]] += 1
            if f["id"] in seen:
                errors.append(f"{path.name}:{f['line']} duplicate finding ID {f['id']} (first at line {seen[f['id']]})")
            else:
                seen[f["id"]] = f["line"]
            if f["status"] == "open":
                if f["last_verified"] is None:
                    warnings.append(
                        f"{path.name}:{f['line']} {f['id']} is open with no verifiable date "
                        f"(add a YYYY-MM-DD to the row or a **Date:** header to the doc)"
                    )
                elif (today - f["last_verified"]).days > max_age_days:
                    errors.append(
                        f"{path.name}:{f['line']} open finding {f['id']} last verified "
                        f"{f['last_verified']} ({(today - f['last_verified']).days}d ago, "
                        f"max {max_age_days}d) — re-verify or close it"
                    )

    return errors, warnings, counts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("files", nargs="+", type=Path, help="Register markdown files to check")
    parser.add_argument("--max-age", type=int, default=45, help="Max days an open finding may go unverified (default 45)")
    args = parser.parse_args()

    missing = [str(p) for p in args.files if not p.exists()]
    if missing:
        print(f"ERROR: file(s) not found: {', '.join(missing)}")
        return 1

    errors, warnings, counts = check(args.files, args.max_age)
    total = sum(counts.values())
    print(f"Findings: {total} rows — open {counts['open']} · closed {counts['closed']} · deferred {counts['deferred']}")
    for w in warnings:
        print(f"WARN  {w}")
    for e in errors:
        print(f"ERROR {e}")
    if errors:
        print(f"FAILED: {len(errors)} violation(s), {len(warnings)} warning(s)")
        return 1
    print(f"OK: lifecycle valid ({len(warnings)} warning(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
