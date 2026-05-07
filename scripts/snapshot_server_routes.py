"""
Generate route and OpenAPI path snapshots for spine_api.server.

Usage:
  TMPDIR=/private/tmp PYTHONDONTWRITEBYTECODE=1 uv run python scripts/snapshot_server_routes.py --write
  TMPDIR=/private/tmp PYTHONDONTWRITEBYTECODE=1 uv run python scripts/snapshot_server_routes.py
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from fastapi.routing import APIRoute

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Keep import-time requirements deterministic for CLI runs.
os.environ.setdefault("JWT_SECRET", "snapshot-routes-jwt-secret")
os.environ.setdefault("RUNNING_TESTS", "1")

from spine_api.server import app  # noqa: E402

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "tests" / "fixtures"
ROUTES_FIXTURE = FIXTURES_DIR / "server_route_snapshot.json"
OPENAPI_FIXTURE = FIXTURES_DIR / "server_openapi_paths_snapshot.json"


def _route_snapshot() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        methods = sorted(m for m in (route.methods or set()) if m not in {"HEAD", "OPTIONS"})
        rows.append(
            {
                "path": route.path,
                "name": route.name,
                "methods": methods,
                "operation_id": route.operation_id,
            }
        )
    rows.sort(key=lambda r: (str(r["path"]), ",".join(r["methods"]), str(r["name"])))
    return rows


def _openapi_paths_snapshot() -> list[str]:
    schema = app.openapi()
    paths = sorted((schema.get("paths") or {}).keys())
    return paths


def main() -> int:
    parser = argparse.ArgumentParser(description="Snapshot server routes and OpenAPI paths")
    parser.add_argument("--write", action="store_true", help="Write snapshots to tests/fixtures")
    args = parser.parse_args()

    route_rows = _route_snapshot()
    openapi_paths = _openapi_paths_snapshot()

    payload = {
        "route_count": len(route_rows),
        "openapi_path_count": len(openapi_paths),
        "routes": route_rows,
        "openapi_paths": openapi_paths,
    }

    if args.write:
        FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
        ROUTES_FIXTURE.write_text(
            json.dumps({"route_count": len(route_rows), "routes": route_rows}, indent=2) + "\n",
            encoding="utf-8",
        )
        OPENAPI_FIXTURE.write_text(
            json.dumps({"openapi_path_count": len(openapi_paths), "paths": openapi_paths}, indent=2) + "\n",
            encoding="utf-8",
        )

    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
