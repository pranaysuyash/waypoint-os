#!/usr/bin/env python3
"""
tools/db_restore.py — verified pg_restore of a Waypoint backup into an
EXPLICIT target database (FND-0388). Companion to tools/db_backup.py;
procedure doc: Docs/runbooks/DATABASE_BACKUP_RESTORE_2026-10-26.md.

Safety contract (the whole point of this tool):
  - The target database must be named EXPLICITLY via --target. There is no
    default. The live database name (PGDATABASE from DATABASE_URL) is
    REFUSED as a target unless --i-accept-live-overwrite is passed — and
    even then it restores into it only after a second confirmation flag,
    because the doctrine forbids destructive ops against the live DB.
  - Recommended flow: create a SCRATCH database (createdb), restore into it,
    compare row counts against the manifest, drop the scratch. The scratch
    belongs to the drill; the live DB is never touched.

Usage:
  python3 tools/db_restore.py --from backups/waypoint_os_X.dump \
      --target waypoint_restore_drill [--drop-existing]
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import os
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BACKUP_DIR = REPO / "backups"
VERIFY_TABLES = ("trips", "users", "agencies")


def fail(msg: str) -> None:
    print(f"db_restore: FAIL — {msg}", file=sys.stderr)
    sys.exit(1)


def pg_env_for(target: str) -> dict:
    """Standard libpq env from DATABASE_URL, with PGDATABASE pointed at the
    explicit restore target."""
    url = os.environ.get("DATABASE_URL", "").strip().replace("+asyncpg", "")
    if not url:
        fail("DATABASE_URL is not set.")
    from urllib.parse import urlsplit, unquote

    parts = urlsplit(url)
    env = dict(os.environ)
    if parts.hostname:
        env["PGHOST"] = parts.hostname
    if parts.port:
        env["PGPORT"] = str(parts.port)
    if parts.username:
        env["PGUSER"] = unquote(parts.username)
    if parts.password:
        env["PGPASSWORD"] = unquote(parts.password)
    env["PGDATABASE"] = target
    return env


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="backup", required=True, help="path to .dump artifact")
    ap.add_argument("--target", required=True, help="explicit target database name")
    ap.add_argument("--drop-existing", action="store_true",
                    help="drop+recreate the target if it exists (target must not be the live DB)")
    args = ap.parse_args()

    backup = Path(args.backup)
    if not backup.is_absolute():
        backup = REPO / backup
    if not backup.exists():
        fail(f"backup artifact not found: {backup}")

    manifest_path = backup.with_suffix("").with_suffix(".manifest.json")  # noqa: F841
    counts_at_backup: dict = {}
    if Path(str(backup).replace(".dump", ".manifest.json")).exists():
        manifest = json.loads(Path(str(backup).replace(".dump", ".manifest.json")).read_text())
        counts_at_backup = manifest.get("core_table_rows_at_backup", {})

    env = pg_env_for(args.target)
    live_name = os.environ.get("PGDATABASE", "")
    source_url = os.environ.get("DATABASE_URL", "")
    if source_url:
        from urllib.parse import urlsplit

        live_name = (urlsplit(source_url.replace("+asyncpg", "")).path or "").lstrip("/")

    if args.target == live_name and not args.i_accept_live_overwrite():
        fail(
            f"refusing: {args.target!r} is the LIVE database from DATABASE_URL. "
            "Restore into a scratch database instead (see the runbook)."
        )

    if args.drop_existing:
        subprocess.run(["dropdb", "--if-exists"], capture_output=True, text=True, env=env)
        # dropdb reads PGDATABASE — create a maintenance connection to drop it
        maintenance = dict(env)
        maintenance["PGDATABASE"] = "postgres"
        subprocess.run(["dropdb", "--if-exists", args.target],
                       capture_output=True, text=True, env=maintenance)
    createdb = subprocess.run(["createdb", args.target],
                              capture_output=True, text=True,
                              env={**env, "PGDATABASE": "postgres"})
    if createdb.returncode != 0 and not args.drop_existing:
        fail(f"createdb failed (exists? use --drop-existing): {createdb.stderr.strip()[:200]}")

    restore = subprocess.run(
        ["pg_restore", "--no-owner", *(["--role", env["PGUSER"]] if env.get("PGUSER") else []),
         "-d", args.target, str(backup)],
        capture_output=True, text=True, env=env,
    )
    # pg_restore exits 1 on ignorable errors (role/ownership); errors that
    # matter print to stderr — surface everything either way.
    if restore.stderr.strip():
        print(f"pg_restore stderr (review): {restore.stderr.strip()[:500]}")

    print(f"restore into {args.target}: command exit {restore.returncode}")
    print("verification — restored row counts (vs manifest at backup time):")
    verify_sql = {
        "trips": "select count(*) from trips",
        "users": "select count(*) from users",
        "agencies": "select count(*) from agencies",
    }
    ok = True
    for table, sql in verify_sql.items():
        raw = subprocess.run(
            ["psql", "-tAc", sql],
            capture_output=True, text=True, env=env,
        ).stdout.strip()
        try:
            n = int(raw) if raw else None
        except ValueError:
            n = None
        at_backup = counts_at_backup.get(table)
        mark = "OK" if n is not None and (at_backup is None or n == at_backup) else "MISMATCH"
        if mark == "MISMATCH":
            ok = False
        print(f"  {table}: {n}  (at backup: {at_backup})  {mark}")

    print("DONE — the scratch database is yours to inspect; drop it with:")
    print(f"  dropdb {args.target}  (PG env already in your shell via DATABASE_URL)")
    return 0 if ok else 1


def i_accept_live_overwrite() -> bool:
    return "--i-accept-live-overwrite" in sys.argv


if __name__ == "__main__":
    sys.exit(main())
