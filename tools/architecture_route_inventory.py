#!/usr/bin/env python3
"""Inventory FastAPI routes and Next.js BFF route-map coverage.

This is a static architecture aid, not a runtime parity test. It complements
``scripts/snapshot_server_routes.py`` by showing route ownership and BFF mapping
coverage without importing the FastAPI app.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SERVER_FILE = PROJECT_ROOT / "spine_api" / "server.py"
ROUTERS_DIR = PROJECT_ROOT / "spine_api" / "routers"
BFF_ROUTE_MAP = PROJECT_ROOT / "frontend" / "src" / "lib" / "route-map.ts"

HTTP_METHODS = frozenset({"get", "post", "put", "patch", "delete"})
BFF_ENTRY_RE = re.compile(
    r'\[\s*"(?P<frontend>[^"]+)"\s*,\s*\{\s*backendPath:\s*"(?P<backend>[^"]+)"'
    r"(?P<body>.*?)\}\s*\]",
    re.DOTALL,
)
TIMEOUT_RE = re.compile(r"timeoutMs:\s*(?P<timeout>[A-Z0-9_]+)")
PARAM_RE = re.compile(r"\{[^}/]+\}")


@dataclass(frozen=True)
class BackendRoute:
    method: str
    path: str
    function: str
    source: str
    line: int
    owner: str


@dataclass(frozen=True)
class BffRoute:
    frontend_path: str
    backend_path: str
    timeout_policy: str | None


def _string_arg(node: ast.AST | None) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _router_prefix(tree: ast.AST) -> str:
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == "router" for target in node.targets):
            continue
        call = node.value
        if not isinstance(call, ast.Call):
            continue
        if not isinstance(call.func, ast.Name) or call.func.id != "APIRouter":
            continue
        for keyword in call.keywords:
            if keyword.arg == "prefix":
                return _string_arg(keyword.value) or ""
    return ""


def _join_paths(prefix: str, path: str) -> str:
    if not prefix:
        return path or "/"
    if not path:
        return prefix
    return f"{prefix.rstrip('/')}/{path.lstrip('/')}"


def _decorated_routes(path: Path, decorator_owner: str, route_prefix: str = "") -> list[BackendRoute]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    routes: list[BackendRoute] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call):
                continue
            func = decorator.func
            if not isinstance(func, ast.Attribute):
                continue
            if func.attr not in HTTP_METHODS:
                continue
            owner = func.value
            if not isinstance(owner, ast.Name) or owner.id != decorator_owner:
                continue
            route_path = _string_arg(decorator.args[0] if decorator.args else None)
            if route_path is None:
                continue
            routes.append(
                BackendRoute(
                    method=func.attr.upper(),
                    path=_join_paths(route_prefix, route_path),
                    function=node.name,
                    source=str(path.relative_to(PROJECT_ROOT)),
                    line=node.lineno,
                    owner=path.stem if decorator_owner == "router" else "server.py",
                )
            )
    return routes


def collect_backend_routes() -> list[BackendRoute]:
    routes = _decorated_routes(SERVER_FILE, decorator_owner="app")
    for router_file in sorted(ROUTERS_DIR.glob("*.py")):
        if router_file.name == "__init__.py":
            continue
        tree = ast.parse(router_file.read_text(encoding="utf-8"), filename=str(router_file))
        routes.extend(
            _decorated_routes(
                router_file,
                decorator_owner="router",
                route_prefix=_router_prefix(tree),
            )
        )
    return sorted(routes, key=lambda route: (route.path, route.method, route.source, route.line))


def collect_bff_routes() -> list[BffRoute]:
    text = BFF_ROUTE_MAP.read_text(encoding="utf-8")
    routes: list[BffRoute] = []
    for match in BFF_ENTRY_RE.finditer(text):
        timeout = TIMEOUT_RE.search(match.group("body"))
        routes.append(
            BffRoute(
                frontend_path=match.group("frontend"),
                backend_path=match.group("backend"),
                timeout_policy=timeout.group("timeout") if timeout else None,
            )
        )
    return sorted(routes, key=lambda route: (route.frontend_path, route.backend_path))


def _backend_key(route: BackendRoute) -> tuple[str, str]:
    return (route.method, route.path)


def _normalized_path(path: str) -> str:
    value = path if path.startswith("/") else f"/{path}"
    return PARAM_RE.sub("{param}", value.rstrip("/") or "/")


def _potential_duplicate_backend_routes(routes: Iterable[BackendRoute]) -> dict[str, list[BackendRoute]]:
    grouped: dict[tuple[str, str], list[BackendRoute]] = defaultdict(list)
    for route in routes:
        grouped[_backend_key(route)].append(route)
    duplicates = {
        f"{method} {path}": members
        for (method, path), members in grouped.items()
        if len(members) > 1
    }
    return dict(sorted(duplicates.items()))


def _owner_summary(routes: Iterable[BackendRoute]) -> list[dict[str, object]]:
    grouped: dict[str, list[BackendRoute]] = defaultdict(list)
    for route in routes:
        grouped[route.owner].append(route)
    summary = []
    for owner, members in sorted(grouped.items()):
        methods = Counter(route.method for route in members)
        summary.append(
            {
                "owner": owner,
                "route_count": len(members),
                "methods": dict(sorted(methods.items())),
            }
        )
    return summary


def build_inventory() -> dict[str, object]:
    backend_routes = collect_backend_routes()
    bff_routes = collect_bff_routes()
    server_routes = [route for route in backend_routes if route.owner == "server.py"]
    router_routes = [route for route in backend_routes if route.owner != "server.py"]
    mapped_backend_paths = {route.backend_path for route in bff_routes}
    normalized_backend_paths = {_normalized_path(route.path) for route in backend_routes}
    bff_unmatched_routes = [
        route for route in bff_routes
        if _normalized_path(route.backend_path) not in normalized_backend_paths
    ]

    return {
        "summary": {
            "backend_route_count": len(backend_routes),
            "server_py_route_count": len(server_routes),
            "router_module_route_count": len(router_routes),
            "router_module_count": len({route.owner for route in router_routes}),
            "bff_route_map_count": len(bff_routes),
            "bff_backend_path_count": len(mapped_backend_paths),
            "bff_unmatched_backend_path_count": len(bff_unmatched_routes),
            "potential_duplicate_backend_route_count": len(_potential_duplicate_backend_routes(backend_routes)),
        },
        "backend_owner_summary": _owner_summary(backend_routes),
        "potential_duplicate_backend_routes": {
            key: [asdict(route) for route in routes]
            for key, routes in _potential_duplicate_backend_routes(backend_routes).items()
        },
        "server_py_routes": [asdict(route) for route in server_routes],
        "router_module_routes": [asdict(route) for route in router_routes],
        "bff_routes": [asdict(route) for route in bff_routes],
        "bff_unmatched_backend_routes": [asdict(route) for route in bff_unmatched_routes],
    }


def render_markdown(inventory: dict[str, object]) -> str:
    summary = inventory["summary"]
    assert isinstance(summary, dict)
    owner_summary = inventory["backend_owner_summary"]
    duplicates = inventory["potential_duplicate_backend_routes"]
    server_routes = inventory["server_py_routes"]
    bff_routes = inventory["bff_routes"]
    bff_unmatched_routes = inventory["bff_unmatched_backend_routes"]
    assert isinstance(owner_summary, list)
    assert isinstance(duplicates, dict)
    assert isinstance(server_routes, list)
    assert isinstance(bff_routes, list)
    assert isinstance(bff_unmatched_routes, list)

    lines = [
        "# Architecture Route Inventory",
        "",
        "Generated by `tools/architecture_route_inventory.py`.",
        "",
        "## Summary",
        "",
    ]
    for key, value in summary.items():
        lines.append(f"- `{key}`: {value}")

    lines.extend(["", "## Backend Route Ownership", "", "| Owner | Routes | Methods |", "| --- | ---: | --- |"])
    for row in owner_summary:
        assert isinstance(row, dict)
        methods = ", ".join(f"{method}:{count}" for method, count in row["methods"].items())
        lines.append(f"| `{row['owner']}` | {row['route_count']} | {methods} |")

    lines.extend(["", "## Potential Duplicate Backend Routes", ""])
    if duplicates:
        for key, routes in duplicates.items():
            lines.append(f"- `{key}`")
            for route in routes:
                lines.append(f"  - `{route['source']}:{route['line']}` `{route['function']}`")
    else:
        lines.append("No exact method/path duplicates found by static scan.")

    lines.extend(["", "## Routes Still Owned By `spine_api/server.py`", ""])
    for route in server_routes:
        lines.append(
            f"- `{route['method']} {route['path']}` -> `{route['function']}` "
            f"(`{route['source']}:{route['line']}`)"
        )

    lines.extend(["", "## BFF Entries Without A Matching Backend Path", ""])
    if bff_unmatched_routes:
        for route in bff_unmatched_routes:
            lines.append(
                f"- `/{route['frontend_path']}` -> `{route['backend_path']}`"
            )
    else:
        lines.append("All BFF route-map backend paths match a current backend path after path-parameter normalization.")

    lines.extend(["", "## BFF Route Map Entries", "", "| Frontend Path | Backend Path | Timeout Policy |", "| --- | --- | --- |"])
    for route in bff_routes:
        lines.append(
            f"| `/{route['frontend_path']}` | `{route['backend_path']}` | "
            f"`{route['timeout_policy'] or ''}` |"
        )

    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Inventory backend route ownership and BFF route-map entries")
    parser.add_argument("--format", choices=("json", "md"), default="json")
    parser.add_argument("--output", type=Path, help="Write inventory to this path instead of stdout")
    args = parser.parse_args()

    inventory = build_inventory()
    rendered = (
        json.dumps(inventory, indent=2, sort_keys=True) + "\n"
        if args.format == "json"
        else render_markdown(inventory)
    )

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
