from __future__ import annotations

import json
from pathlib import Path

from scripts.snapshot_server_routes import OPENAPI_FIXTURE, _openapi_paths_snapshot


def _load_expected(path: Path) -> dict:
    assert path.exists(), f"Missing snapshot fixture: {path}"
    return json.loads(path.read_text(encoding="utf-8"))


def test_server_openapi_paths_parity_snapshot_matches_fixture():
    expected = _load_expected(OPENAPI_FIXTURE)
    actual_paths = _openapi_paths_snapshot()

    assert expected["openapi_path_count"] == len(actual_paths), (
        f"OpenAPI path count changed: expected={expected['openapi_path_count']} actual={len(actual_paths)}. "
        "If intentional, regenerate with scripts/snapshot_server_routes.py --write"
    )
    assert expected["paths"] == actual_paths, (
        "OpenAPI path snapshot drift detected. "
        "If intentional, regenerate with scripts/snapshot_server_routes.py --write"
    )
