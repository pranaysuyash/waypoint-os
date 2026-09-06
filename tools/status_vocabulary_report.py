#!/usr/bin/env python3
"""Read-only inventory of the Trip.status vocabulary.

The report is deliberately an observation tool, not a second status
implementation.  It imports the backend alias map, preserves raw tokens, and
separates missing/null/empty/invalid values. It emits JSON only to stdout and
never changes trip data. SQL requires an explicit agency, enforced RLS, and a
bounded read-only transaction which is always rolled back. Raw status strings
can contain sensitive data: retain reports only in an appropriately restricted
location. Writer provenance requires a separate source audit.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import errno
import math
import os
import stat
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy import func, select, text

from spine_api.core.trip_status import _STATUS_ALIASES


class ReportError(ValueError):
    """A fixed, payload-free diagnostic code safe to include in report JSON."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def _token_entry(raw: str, count: int) -> dict[str, Any]:
    normalized = raw.strip().lower()
    canonical = _STATUS_ALIASES.get(normalized)
    if canonical is None:
        canonical = raw.strip()
    return {
        "raw": raw,
        "count": count,
        "normalized": normalized,
        "canonical": canonical,
        "alias_covered": normalized in _STATUS_ALIASES,
        "writer_provenance": "not_evaluated",
    }


def _entries(counter: Counter[str]) -> list[dict[str, Any]]:
    return [_token_entry(token, count) for token, count in sorted(counter.items())]


def scan_file_store(root: Path) -> dict[str, Any]:
    """Scan JSON trip files without changing them or any surrounding state."""

    counts: Counter[str] = Counter()
    diagnostics: Counter[str] = Counter()
    # Pin the directory and reject symlinks atomically, including JSON symlink
    # swaps. O_NONBLOCK prevents a hostile *.json FIFO from hanging the scan.
    try:
        root_fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    except OSError as exc:
        raise ReportError("file_root_unavailable") from exc
    try:
        names = sorted(name for name in os.listdir(root_fd) if name.endswith(".json"))
        for name in names:
            diagnostics["files_scanned"] += 1
            try:
                fd = os.open(
                    name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=root_fd
                )
                try:
                    if not stat.S_ISREG(os.fstat(fd).st_mode):
                        diagnostics["unsafe_files_skipped"] += 1
                        continue
                    with os.fdopen(fd, encoding="utf-8", closefd=False) as stream:
                        payload = json.load(stream)
                finally:
                    # Also owns failures before a stream is constructed.
                    os.close(fd)
            except OSError as exc:
                key = (
                    "unsafe_files_skipped"
                    if exc.errno == errno.ELOOP
                    else "unreadable_files"
                )
                diagnostics[key] += 1
                continue
            except (UnicodeDecodeError, json.JSONDecodeError, RecursionError):
                diagnostics["malformed_files"] += 1
                continue
            if not isinstance(payload, dict):
                diagnostics["invalid_record_shape"] += 1
                continue
            diagnostics["rows_counted"] += 1
            if "status" not in payload:
                diagnostics["missing_status_key"] += 1
            elif payload["status"] is None:
                diagnostics["explicit_null_status"] += 1
            elif not isinstance(payload["status"], str):
                diagnostics["invalid_status_type"] += 1
            else:
                value = payload["status"]
                counts[value] += 1
                if not value.strip():
                    diagnostics["blank_status"] += 1
    except OSError as exc:
        raise ReportError("file_root_unavailable") from exc
    finally:
        os.close(root_fd)
    problem_keys = (
        "malformed_files",
        "unreadable_files",
        "unsafe_files_skipped",
        "invalid_record_shape",
        "invalid_status_type",
    )
    return {
        "source": "file_store",
        "root": str(root),
        "scope": "directory_unfiltered",
        "observation_status": "partial"
        if any(diagnostics[key] for key in problem_keys)
        else "complete",
        **{
            key: diagnostics[key]
            for key in (
                "files_scanned",
                "rows_counted",
                "missing_status_key",
                "explicit_null_status",
                "blank_status",
                *problem_keys,
            )
        },
        "groups_returned": len(counts),
        "status_values_counted": sum(counts.values()),
        "tokens": _entries(counts),
    }


async def scan_sql_store(
    agency_id: str, *, timeout_seconds: float = 30
) -> dict[str, Any]:
    """Observe one agency under RLS; never issue unscoped or write transactions."""

    try:
        agency_id = str(UUID(agency_id))
    except (ValueError, TypeError, AttributeError) as exc:
        raise ReportError("agency_id_required_or_invalid") from exc
    if not math.isfinite(timeout_seconds) or not 0 < timeout_seconds <= 120:
        raise ReportError("sql_timeout_invalid")

    try:
        return await asyncio.wait_for(
            _scan_scoped_sql(agency_id, timeout_seconds), timeout=timeout_seconds
        )
    except asyncio.TimeoutError as exc:
        raise ReportError("sql_timeout") from exc


async def _scan_scoped_sql(agency_id: str, timeout_seconds: float) -> dict[str, Any]:

    # Lazy import keeps ``--backend file`` independent of DATABASE_URL and
    # makes the read-only file report usable during migrations/outages.
    from spine_api.core.database import async_session_maker
    from spine_api.core.rls import apply_rls, inspect_rls_runtime_posture
    from spine_api.models.trips import Trip

    query = (
        select(Trip.status, func.count())
        .where(Trip.agency_id == agency_id)
        .group_by(Trip.status)
        .order_by(Trip.status)
    )
    async with async_session_maker() as session:
        await session.begin()
        try:
            await session.execute(text("SET TRANSACTION READ ONLY"))
            await session.execute(
                text("SELECT set_config('statement_timeout', :timeout, true)"),
                {"timeout": f"{max(1, int(timeout_seconds * 1000))}ms"},
            )
            await apply_rls(session, agency_id)
            posture = await inspect_rls_runtime_posture(
                session, expected_tables=("trips",)
            )
            if not posture.is_enforced_for_runtime_role:
                raise ReportError("sql_rls_not_enforced")
            rows = (await session.execute(query)).all()
        finally:
            await session.rollback()
    counts = Counter(
        {status: int(count) for status, count in rows if isinstance(status, str)}
    )
    return {
        "source": "sql_store",
        "scope": "agency_rls_and_predicate",
        "observation_status": "complete",
        "agency_id": agency_id,
        "read_only_transaction": True,
        "rls_enforced_for_runtime_role": True,
        "timeout_seconds": timeout_seconds,
        "groups_returned": len(rows),
        "rows_counted": sum(int(count) for _, count in rows),
        "status_values_counted": sum(counts.values()),
        "missing_status_key": 0,
        "explicit_null_status": sum(
            int(count) for status, count in rows if status is None
        ),
        "blank_status": sum(
            count for status, count in counts.items() if not status.strip()
        ),
        "tokens": _entries(counts),
    }


def _parse_agency_id(value: str | None) -> str | None:
    if value is None:
        return None
    try:
        return str(UUID(value))
    except ValueError as exc:
        raise argparse.ArgumentTypeError("--agency-id must be a UUID") from exc


async def _build_report(args: argparse.Namespace) -> dict[str, Any]:
    report: dict[str, Any] = {
        "schema_version": 2,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generator": "tools.status_vocabulary_report",
        "backend": args.backend,
        "agency_id": args.agency_id,
        "sources": [],
        "errors": [],
    }
    if args.backend in {"file", "both"}:
        try:
            report["sources"].append(scan_file_store(args.file_root))
        except ReportError as exc:
            report["errors"].append({"source": "file_store", "code": exc.code})
    if args.backend in {"sql", "both"}:
        try:
            report["sources"].append(
                await scan_sql_store(
                    args.agency_id, timeout_seconds=args.sql_timeout_seconds
                )
            )
        except Exception as exc:  # noqa: BLE001 - partial report with payload-free failure code
            code = exc.code if isinstance(exc, ReportError) else "sql_unavailable"
            report["errors"].append({"source": "sql_store", "code": code})
    if not report["sources"]:
        report["observation_status"] = "unavailable"
    elif report["errors"] or any(
        source["observation_status"] != "complete" for source in report["sources"]
    ):
        report["observation_status"] = "partial"
    else:
        report["observation_status"] = "complete"
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend", choices=("file", "sql", "both"), default="both")
    parser.add_argument(
        "--file-root",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "data" / "trips",
        help="directory containing JSON file-store trips",
    )
    parser.add_argument("--agency-id", type=_parse_agency_id, default=None)
    parser.add_argument(
        "--sql-timeout-seconds",
        type=float,
        default=30,
        help="SQL deadline, greater than 0 and at most 120 seconds",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.backend in {"sql", "both"} and args.agency_id is None:
        parser.error("--agency-id is required for sql or both backends")
    report = asyncio.run(_build_report(args))
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["observation_status"] == "complete" else 2


if __name__ == "__main__":
    raise SystemExit(main())
