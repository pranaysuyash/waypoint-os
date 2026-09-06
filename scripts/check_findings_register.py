#!/usr/bin/env python3
"""check_findings_register.py — enforce the findings lifecycle state machine.

Background (EX-06, FINDINGS_LIFECYCLE_2026-08-30.md): ~25 audits produced
findings with no lifecycle — no status, owner, or re-verification date — so
findings could only be re-discovered, never closed. This checker makes the
lifecycle mechanical for markdown register tables (our canonical register
format).

Per table row whose first column is a finding ID (e.g. R-03, A-14, F-01):
  - the Status / Live status column alone owns lifecycle; its leading state
    determines open/closed/deferred. Missing/unknown canonical states fail.
  - formatted IDs are normalized; historical companions are checked for
    duplicate IDs but excluded from current lifecycle counts and freshness.
  - verification dates come from Last verified, then status, then document
    date. Dates in findings/evidence prose never renew verification.

Checks (exit 1 on any violation):
  1. duplicate ID rows within a file
  2. every body row in an ID table needs one valid ID and state column
  3. open findings whose last-verified date is older than --max-age days

Usage:
  python3 scripts/check_findings_register.py Docs/review/FINDINGS_REGISTER_2026-08-31.md
  python3 scripts/check_findings_register.py --max-age 30 <file1.md> <file2.md>
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
from pathlib import Path

ID_PATTERN = re.compile(r"^[A-Z]{1,4}-\d{1,4}\b")
DATE_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}")
DATE_LINE_PATTERN = re.compile(r"^\*\*Date:\*\*\s*(.*)$", re.IGNORECASE)
ROLE_PATTERN = re.compile(r"^\*\*Role:\*\*\s*(.*)$", re.IGNORECASE)

STATUS_HEADERS = re.compile(r"^(?:live\s+)?status(?:\s+\(\d{4}-\d{2}-\d{2}\))?$", re.IGNORECASE)
STATE_RULES = (
    ("deferred", r"no-go-for-now|deferred|conditional|trap"),
    ("open", r"open|partial(?:ly)?|partly|in[- ]flight|watch|unknown|contested"),
    ("closed", r"resolved|fixed|closed|implemented|wontfix|won't fix|superseded|no-go|rejected"),
)
STATE_DATE = re.compile(
    r"^(?:" + "|".join(pattern for _, pattern in STATE_RULES)
    + r")(?:\s+locally)?\s+(\d{4}-\d{2}-\d{2})\b", re.IGNORECASE
)


def _plain(value: str) -> str:
    """Normalize presentation markup, not the meaning of a cell."""
    return re.sub(r"[*_`~]", "", value).strip()


def _document_lines(text: str):
    """One structural boundary for metadata and tables; examples have no authority."""
    fence: str | None = None
    comment = False
    for line_number, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        match = re.match(r"^(`{3,}|~{3,})", stripped) if not comment else None
        if match:
            marker = match.group()
            if fence is None:
                fence = marker
            elif marker[0] == fence[0] and len(marker) >= len(fence):
                fence = None
            yield line_number, ""
            continue
        if fence is not None or line.startswith(("    ", "\t")):
            yield line_number, ""
            continue
        visible: list[str] = []
        remainder = stripped
        while remainder:
            if comment:
                end = remainder.find("-->")
                if end < 0:
                    break
                remainder = remainder[end + 3:]
                comment = False
            else:
                start = remainder.find("<!--")
                if start < 0:
                    visible.append(remainder)
                    break
                visible.append(remainder[:start])
                remainder = remainder[start + 4:]
                comment = True
        yield line_number, "".join(visible).strip()


def _row_date(status_cell: str, date_cell: str | None, doc_date: dt.date | None):
    """An explicit verification field cannot fall back to incidental prose dates."""
    if date_cell is not None:
        value = _plain(date_cell)
        if not DATE_PATTERN.fullmatch(value):
            return None, False
        return dt.date.fromisoformat(value), True
    status = _plain(status_cell)
    if re.search(r"last[- ]verified\b", status, re.IGNORECASE):
        segments = re.findall(r"last[- ]verified\s*:?\s*([^;—]+)", status, re.IGNORECASE)
        if len(segments) != 1 or not DATE_PATTERN.fullmatch(segments[0].strip()):
            return None, False
        return dt.date.fromisoformat(segments[0].strip()), True
    # Compatibility: CLOSED 2026-09-04 — explanation. The state segment,
    # not the entire explanation, may supply a date when no explicit field exists.
    leading = re.sub(r"^[^a-zA-Z]+", "", re.split(r"[;—]", status, maxsplit=1)[0])
    dates = DATE_PATTERN.findall(leading)
    match = STATE_DATE.match(leading)
    if match and len(dates) > 1:
        return None, False
    return (dt.date.fromisoformat(match.group(1)) if match else doc_date), True


def _row_status(status_cell: str) -> str | None:
    # Ignore a leading visual badge, but never search the explanatory prose.
    state = re.sub(r"^[^a-z]+", "", _plain(status_cell).lower())
    for lifecycle, pattern in STATE_RULES:
        if re.match(r"(?:" + pattern + r")\b", state):
            return lifecycle
    return None


def _parse_document(path: Path) -> tuple[list[dict], dt.date | None, str]:
    text = path.read_text(encoding="utf-8")
    lines = list(_document_lines(text))
    metadata: dict[str, str] = {}
    for line_number, line in lines:
        if line.startswith(("|", "## ")):
            break
        for key, pattern in (("role", ROLE_PATTERN), ("date", DATE_LINE_PATTERN)):
            match = pattern.fullmatch(line)
            if match:
                if key in metadata:
                    raise ValueError(f"line {line_number}: duplicate document {key} metadata")
                metadata[key] = match.group(1).strip()
    role = metadata.get("role", "canonical").lower()
    doc_date = None
    if "date" in metadata:
        match = DATE_PATTERN.match(metadata["date"])
        if match is None:
            raise ValueError("invalid document date metadata")
        doc_date = dt.date.fromisoformat(match.group())
    findings: list[dict] = []
    headers: list[str] = []
    in_table = False
    expect_separator = False
    for line_number, stripped in lines:
        if not stripped.startswith("|"):
            headers = []
            in_table = False
            expect_separator = False
            continue
        cells = [c.strip() for c in re.split(r"(?<!\\)\|", stripped.strip("|"))]
        identity = _plain(cells[0])
        if not in_table:
            in_table = True
            if identity == "ID":
                headers = [_plain(cell) for cell in cells]
                expect_separator = True
            continue
        if expect_separator:
            expect_separator = False
            if len(cells) != len(headers) or not all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
                raise ValueError(f"line {line_number}: ID table requires a complete separator row")
            continue
        if not headers:
            continue
        match = ID_PATTERN.match(identity)
        status_indices = [i for i, h in enumerate(headers) if STATUS_HEADERS.fullmatch(h)]
        status_index = status_indices[0] if len(status_indices) == 1 else None
        status_cell = cells[status_index] if status_index is not None and status_index < len(cells) else ""
        status = _row_status(status_cell)
        date_indices = [i for i, h in enumerate(headers) if h.lower() == "last verified"]
        date_cell = (cells[date_indices[0]] if date_indices[0] < len(cells) else "") if date_indices else None
        last_verified, date_valid = _row_date(status_cell, date_cell, doc_date)
        findings.append({
            "id": identity or "<missing>",
            "id_valid": match is not None and match.group() == identity,
            "status": status or "open",
            "status_valid": status is not None,
            "date_valid": date_valid and len(date_indices) <= 1,
            "last_verified": last_verified,
            "line": line_number,
        })
    return findings, doc_date, role


def parse_register(path: Path) -> tuple[list[dict], dt.date | None]:
    findings, doc_date, _ = _parse_document(path)
    return findings, doc_date


def check(paths: list[Path], max_age_days: int) -> tuple[list[str], list[str], dict[str, int]]:
    errors: list[str] = []
    warnings: list[str] = []
    counts = {"open": 0, "closed": 0, "deferred": 0}
    today = dt.date.today()

    documents = {}
    for path in paths:
        try:
            documents[path] = _parse_document(path)
        except (ValueError, OSError, UnicodeError) as exc:
            errors.append(f"{path.name}: invalid register/verification date: {exc}")
    canonical_paths = [path for path, (_, _, role) in documents.items() if re.match(r"canonical\b", role)]
    for path, (_, _, role) in documents.items():
        if not re.match(r"(?:canonical|historical)\b", role):
            errors.append(f"{path.name}: unrecognized register role; use canonical or historical")
    if len(canonical_paths) > 1:
        errors.append(
            "multiple canonical findings registers supplied: "
            + ", ".join(str(path) for path in canonical_paths)
        )

    ids_by_path: dict[str, list[tuple[Path, int]]] = {}
    for path, (findings, _, _) in documents.items():
        canonical = path in canonical_paths
        if canonical and not findings:
            errors.append(f"{path.name}: canonical register has no finding rows")
        seen: dict[str, int] = {}
        for f in findings:
            if canonical:
                counts[f["status"]] += 1
                if not f["status_valid"]:
                    errors.append(f"{path.name}:{f['line']} {f['id']} missing or unrecognized Status column value")
                if not f["id_valid"]:
                    errors.append(f"{path.name}:{f['line']} expected a single finding ID; move aliases to a separate column")
                if not f["date_valid"]:
                    errors.append(f"{path.name}:{f['line']} {f['id']} invalid or missing explicit verification date")
                if f["last_verified"] is not None and f["last_verified"] > today:
                    errors.append(f"{path.name}:{f['line']} {f['id']} verification date is in the future")
            if f["id"] in seen:
                errors.append(f"{path.name}:{f['line']} duplicate finding ID {f['id']} (first at line {seen[f['id']]})")
            else:
                seen[f["id"]] = f["line"]
            ids_by_path.setdefault(f["id"], []).append((path, f["line"]))
            if canonical and f["status"] == "open":
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

    # A historical/planning companion may repeat IDs for context, but two
    # canonical sources would create contradictory lifecycle truth.  The
    # explicit role metadata makes that distinction mechanical and reviewable.
    for finding_id, locations in ids_by_path.items():
        canonical_locations = [
            (path, line) for path, line in locations if path in canonical_paths
        ]
        if len(canonical_locations) > 1:
            details = ", ".join(f"{path.name}:{line}" for path, line in canonical_locations)
            errors.append(f"finding ID {finding_id} appears in multiple canonical registers: {details}")

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
    print(f"Canonical findings: {total} rows — open {counts['open']} · closed {counts['closed']} · deferred {counts['deferred']}")
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
