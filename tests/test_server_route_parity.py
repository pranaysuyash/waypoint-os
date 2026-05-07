from __future__ import annotations

import json
from pathlib import Path

from scripts.snapshot_server_routes import ROUTES_FIXTURE, _route_snapshot


def _load_expected(path: Path) -> dict:
    assert path.exists(), f"Missing snapshot fixture: {path}"
    return json.loads(path.read_text(encoding="utf-8"))


def test_server_route_parity_snapshot_matches_fixture():
    expected = _load_expected(ROUTES_FIXTURE)
    actual_routes = _route_snapshot()

    assert expected["route_count"] == len(actual_routes), (
        f"Route count changed: expected={expected['route_count']} actual={len(actual_routes)}. "
        "If intentional, regenerate with scripts/snapshot_server_routes.py --write"
    )
    assert expected["routes"] == actual_routes, (
        "Route snapshot drift detected. "
        "If intentional, regenerate with scripts/snapshot_server_routes.py --write"
    )
