"""
FND-0340 (Sim #4): every product-facing backend route must be reachable
through the BFF route-map — a door without a route-map key is backend-only by
definition, so "SHIPPED" claims are claims about the API, not the product.

This gate asserts the known parity gap set (captured in
tests/fixtures/bff_parity_known_gaps.json, originally 46 routes on 2026-10-23) never
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
# "agency-api" (R2-A, 2026-11-04): the external agency-facing API authenticates
# with X-API-Key (not the operator JWT) and is consumed by external agent/MCP
# integrations directly against the backend — it is not an operator BFF door.
EXEMPT_SUBSTRINGS = ("webhook", "/internal/", "/stream-events", "/docs", "ws/", "agency-api")


def _path_shape(path: str) -> str:
    return re.sub(r"(?<=/)[{][a-zA-Z_][a-zA-Z0-9_]*[}](?=/|$)", "{}", "/" + path.strip("/"))


def _mapped_backend_paths() -> set[str]:
    # Frontend URLs can alias backend paths. Compare the declared backend destination.
    targets = re.findall(r'\[\s*"[^"]+"\s*,\s*\{\s*backendPath:\s*"([^"]+)"', ROUTE_MAP.read_text())
    return {_path_shape(target) for target in targets}


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


def _current_gaps(backend_routes: set[str], mapped_paths: set[str]) -> set[str]:
    gaps: set[str] = set()
    for route in backend_routes:
        method, path = route.split(" ", 1)
        if method != "GET" or not path.startswith(PRODUCT_PREFIXES):
            continue
        if any(sub in path for sub in EXEMPT_SUBSTRINGS):
            continue
        if _path_shape(path) not in mapped_paths:
            gaps.add(route)
    return gaps


def test_parity_gap_set_never_grows():
    snapshot = set(json.loads(SNAPSHOT.read_text())["routes"])
    current = _current_gaps(_backend_routes(), _mapped_backend_paths())
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


def test_parity_compares_whole_backend_paths_and_ignores_parameter_names():
    target = "/api/v1/messaging/whatsapp/{conversation_id}"
    unmapped = {
        "GET /api/v1/messaging/whatsapp",
        "GET /api/v1/messaging/whatsapp/{conversation_id}/extra",
        "GET /api/v1/messaging/other/{conversation_id}",
    }
    routes = unmapped | {f"GET {target}", "POST /api/v1/messaging/unmapped-command"}
    assert _current_gaps(routes, {_path_shape("api/v1/messaging/whatsapp/{id}")}) == unmapped
