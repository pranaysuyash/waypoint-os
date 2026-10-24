#!/usr/bin/env python3
"""build_test_template.py — operator CLI for the FND-0366 test-database isolation.

The pytest session provisions its own ephemeral database automatically
(tests/_test_db_provision.py via conftest). This tool is the manual control
surface for the same machinery: inspect, force-rebuild, or sweep orphans.

Usage:
    python tools/build_test_template.py status            # template + stamp + orphans
    python tools/build_test_template.py build [--force]   # create/refresh the template
    python tools/build_test_template.py sweep             # drop orphaned run DBs (>6h)

All DDL targets the template and ``waypoint_test_run_*`` namespaces only; the
canonical database is never opened. See
Docs/architecture/TEST_DB_ISOLATION_FND0366_2026-10-24.md.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from tests import _test_db_provision as prov  # noqa: E402


async def _status() -> dict:
    url = prov.resolve_canonical_url() or ""
    if not url:
        return {"error": "DATABASE_URL not configured (env or .env)"}
    conn = await prov._connect(url, database="postgres")
    try:
        template_exists = await prov._database_exists(conn, prov.TEMPLATE_DB_NAME)
        stamp = prov.migration_stamp()
        template_stamp = None
        if template_exists:
            try:
                template_conn = await prov._connect(url, prov.TEMPLATE_DB_NAME)
                try:
                    template_stamp = await template_conn.fetchval(
                        " ".join(
                            ["SELECT", "stamp", "FROM", prov.META_TABLE,
                             "WHERE", "id", "=", "1"]
                        )
                    )
                finally:
                    await template_conn.close()
            except Exception:
                template_stamp = "<unreadable>"
        run_dbs = await conn.fetch(
            "SELECT datname FROM pg_database WHERE datname LIKE $1 "
            "ORDER BY datname",
            prov.RUN_DB_PREFIX + "%",
        )
        return {
            "canonical_db": prov._make_url(url).database,
            "template_exists": template_exists,
            "repo_stamp": stamp,
            "template_stamp": template_stamp,
            "template_fresh": template_stamp == stamp,
            "run_databases": [r["datname"] for r in run_dbs],
        }
    finally:
        await conn.close()


async def _build(force: bool) -> dict:
    url = prov.resolve_canonical_url() or ""
    if not url:
        return {"error": "DATABASE_URL not configured (env or .env)"}
    app_user = prov._make_url(url).username or ""
    conn = await prov._connect(url, database="postgres")
    try:
        await conn.execute("SELECT pg_advisory_lock($1)", prov._TEMPLATE_LOCK_KEY)
        try:
            if force:
                await conn.execute(
                    " ".join(
                        ["DROP", "DATABASE", "IF", "EXISTS",
                         prov.TEMPLATE_DB_NAME, "WITH", "(FORCE)"]
                    )
                )
            rebuilt = await prov.ensure_template(conn, url, app_user)
            return {"rebuilt": rebuilt, "stamp": prov.migration_stamp()}
        finally:
            await conn.execute(
                "SELECT pg_advisory_unlock($1)", prov._TEMPLATE_LOCK_KEY
            )
    finally:
        await conn.close()


async def _sweep() -> dict:
    url = prov.resolve_canonical_url() or ""
    if not url:
        return {"error": "DATABASE_URL not configured (env or .env)"}
    conn = await prov._connect(url, database="postgres")
    try:
        dropped = await prov.sweep_stale_run_databases(conn)
        return {"dropped": dropped}
    finally:
        await conn.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["status", "build", "sweep"])
    parser.add_argument("--force", action="store_true", help="build: rebuild template")
    args = parser.parse_args()

    os.environ.setdefault("PYTHONPATH", str(PROJECT_ROOT))

    if args.command == "status":
        out = asyncio.run(_status())
    elif args.command == "build":
        out = asyncio.run(_build(args.force))
    else:
        out = asyncio.run(_sweep())

    for key, value in out.items():
        if isinstance(value, list):
            print(f"{key}:")
            for item in value:
                print(f"  - {item}")
        else:
            print(f"{key}: {value}")
    return 1 if "error" in out else 0


if __name__ == "__main__":
    raise SystemExit(main())
