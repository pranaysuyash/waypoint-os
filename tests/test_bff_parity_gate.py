"""
FND-0340 (Sim #4): every product-facing backend route must be reachable
through the BFF route-map — a door without a route-map key is backend-only by
definition, so "SHIPPED" claims are claims about the API, not the product.

This gate asserts the known parity gap set (captured in
tests/fixtures/bff_parity_known_gaps.json on 2026-10-23, 46 routes) never
GROWS: new product-facing GET routes must ship with a route-map key. The set
SHRINKS as DP-03c per-door decisions map doors — re-capture the fixture when
they do.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ROUTE_MAP = REPO / "frontend" / "src" / "lib" / "route-map.ts"
SNAPSHOT = REPO / "tests" / "fixtures" / "bff_parity_known_gaps.json"

PRODUCT_PREFIXES = ("/api/v1/", "/api/triage", "/api/public/")
EXEMPT_SUBSTRINGS = ("webhook", "/internal/", "/stream-events", "/docs", "ws/")


def _route_map_keys() -> set[str]:
    keys: set[str] = set()
    for match in re.finditer(
        r'\[\s*"([^"]+)"\s*,\s*\{\s*backendPath', ROUTE_MAP.read_text()
    ):
        keys.add(match.group(1))
    return keys


def _backend_routes() -> set[str]:
    routes: set[str] = set()
    routers_dir = REPO / "spine_api" / "routers"
    for py in routers_dir.glob("*.py"):
        text = py.read_text()
        pm = re.search(r'prefix="([^"]*)"', text)
        prefix = pm.group(1) if pm else ""
        for m in re.finditer(r'@router\.(get|post|patch|delete|put)\("([^"]+)"', text):
            routes.add(f"{m.group(1).upper()} {prefix}{m.group(2)}")
    return routes


def _current_gaps() -> set[str]:
    keys = _route_map_keys()
    gaps: set[str] = set()
    for route in sorted(_backend_routes()):
        method, path = route.split(" ", 1)
        if method != "GET" or not path.startswith(PRODUCT_PREFIXES):
            continue
        if any(sub in path for sub in EXEMPT_SUBSTRINGS):
            continue
        if not any(
            k in path or path.startswith(k.rstrip("/")) or k.rstrip("/") in path
            for k in keys
        ):
            gaps.add(route)
    return gaps


def test_parity_gap_set_never_grows():
    snapshot = set(json.loads(SNAPSHOT.read_text())["routes"])
    current = _current_gaps()
    grown = current - snapshot
    assert not grown, (
        "New product-facing GET routes lack BFF mappings (FND-0340 gate). "
        f"Add route-map keys or extend DP-03c: {sorted(grown)}"
    )


def test_parity_snapshot_is_fresh_enough():
    # Guard against the snapshot drifting from reality (e.g. routes removed):
    # every pinned route must still exist in the backend, else re-capture.
    snapshot = set(json.loads(SNAPSHOT.read_text())["routes"])
    stale = snapshot - _backend_routes()
    assert not stale, (
        f"Pinned gap routes no longer exist — re-capture the fixture: {sorted(stale)}"
    )
