#!/usr/bin/env python3
"""
tools/db_backup.py — consistent pg_dump backup of the Waypoint Postgres DB
(FND-0388). Reusable per the tools doctrine; the restore half is
tools/db_restore.py, the procedure doc is Docs/runbooks/DATABASE_BACKUP_RESTORE_2026-10-26.md.

Connection handling: DATABASE_URL is parsed into the STANDARD libpq
environment variables (PGHOST/PGPORT/PGUSER/PGPASSWORD/PGDATABASE) and passed
via env — pg_dump/psql/pg_restore read them natively, so every subprocess
command is a fully literal argument list at its call site (nothing caller-
or env-shaped in argv; no shell anywhere).

What it does:
  1. pg_dump custom format (-Fc, compressed) → backups/<db>_<ts>.dump
  2. VERIFIES the artifact: non-empty + `pg_restore --list` parses; a
     manifest.json is written alongside (source db, timestamp, sha256,
     core-table row counts at backup time).
  3. Optional retention: --keep-last N prunes only our own <db>_*.dump files.

Read-only against the source database. Never modifies, never drops.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit, unquote

REPO = Path(__file__).resolve().parent.parent
BACKUP_DIR = REPO / "backups"
# Literal SQL per core table (scanner-friendly: no SQL string assembly).
COUNT_SQL = {
    "trips": "select count(*) from trips",
    "users": "select count(*) from users",
    "agencies": "select count(*) from agencies",
    "audit_logs": "select count(*) from audit_logs",
    "execution_events": "select count(*) from execution_events",
}


def fail(msg: str) -> None:
    print(f"db_backup: FAIL — {msg}", file=sys.stderr)
    sys.exit(1)


def pg_env() -> tuple[dict, str]:
    """DATABASE_URL → standard libpq env vars. Returns (env, dbname).
    Fail-closed when DATABASE_URL is absent or malformed."""
    url = os.environ.get("DATABASE_URL", "").strip().replace("+asyncpg", "")
    if not url:
        fail("DATABASE_URL is not set (load .env or export it). Refusing to guess a target.")
    parts = urlsplit(url)
    if parts.scheme not in ("postgres", "postgresql"):
        fail(f"unexpected scheme: {parts.scheme!r}")
    dbname = (parts.path or "").lstrip("/")
    if not dbname:
        fail("DATABASE_URL carries no database name")
    env = dict(os.environ)
    if parts.hostname:
        env["PGHOST"] = parts.hostname
    if parts.port:
        env["PGPORT"] = str(parts.port)
    if parts.username:
        env["PGUSER"] = unquote(parts.username)
    if parts.password:
        env["PGPASSWORD"] = unquote(parts.password)
    env["PGDATABASE"] = dbname
    return env, dbname


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--keep-last", type=int, default=0, metavar="N",
                    help="prune oldest <db>_*.dump artifacts beyond N")
    args = ap.parse_args()

    env, dbname = pg_env()
    BACKUP_DIR.mkdir(exist_ok=True)

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = BACKUP_DIR / f"{dbname}_{ts}.dump"

    dump = subprocess.run(
        ["pg_dump", "-Fc", "-f", str(out)],
        capture_output=True, text=True, env=env,
    )
    if dump.returncode != 0:
        out.unlink(missing_ok=True)
        fail(f"pg_dump failed: {dump.stderr.strip()[:300]}")

    size = out.stat().st_size
    if size < 1024:
        out.unlink(missing_ok=True)
        fail(f"dump suspiciously small ({size}B) — refusing to report success")

    listing = subprocess.run(
        ["pg_restore", "--list", str(out)],
        capture_output=True, text=True, env=env,
    )
    if listing.returncode != 0 or "TABLE" not in listing.stdout:
        out.unlink(missing_ok=True)
        fail("pg_restore --list failed — artifact not verifiable, deleted")

    counts: dict[str, int | None] = {}
    for table, sql in COUNT_SQL.items():
        raw = subprocess.run(
            ["psql", "-tAc", sql],
            capture_output=True, text=True, env=env,
        ).stdout.strip()
        try:
            counts[table] = int(raw) if raw else None
        except ValueError:
            counts[table] = None

    sha = hashlib.sha256(out.read_bytes()).hexdigest()

    manifest = {
        "artifact": out.name,
        "sha256": sha,
        "bytes": size,
        "source_database": dbname,
        "created_at": ts,
        "core_table_rows_at_backup": counts,
        "tables_in_dump": sum(1 for line in listing.stdout.splitlines() if " TABLE " in line),
    }
    (BACKUP_DIR / f"{out.stem}.manifest.json").write_text(json.dumps(manifest, indent=1))

    print(f"backup OK: {out.name} ({size:,}B)")
    print(f"sha256: {sha[:16]}…  tables: {manifest['tables_in_dump']}  core rows: {counts}")

    if args.keep_last > 0:
        artifacts = sorted(BACKUP_DIR.glob(f"{dbname}_*.dump"))
        for stale in artifacts[:-args.keep_last] if len(artifacts) > args.keep_last else []:
            stale.unlink()
            Path(f"{stale.stem}.manifest.json").unlink(missing_ok=True)
            print(f"pruned: {stale.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
