from __future__ import annotations

import ast
from pathlib import Path


ROUTER_PATH = Path(__file__).parents[1] / "spine_api" / "routers" / "corporate_policy.py"


def _router_tree() -> ast.Module:
    return ast.parse(ROUTER_PATH.read_text(encoding="utf-8"))


def _function(tree: ast.Module, name: str) -> ast.FunctionDef:
    return next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name)


def test_corporate_policy_trip_routes_bind_agency_to_jwt_dependency():
    tree = _router_tree()
    source = ROUTER_PATH.read_text(encoding="utf-8")
    assert "Depends(get_current_agency_id)" in source
    assert "Header(" not in source
    assert "TEST_AGENCY_ID" not in source

    for name in ("audit_trip_corporate_policy", "approve_corporate_policy_override"):
        route = _function(tree, name)
        dependency_defaults = [
            ast.unparse(default)
            for default in route.args.defaults
            if isinstance(default, ast.Call)
        ]
        assert "Depends(get_current_agency_id)" in dependency_defaults


def test_corporate_policy_handlers_pass_dependency_value_to_store():
    tree = _router_tree()
    for name in ("audit_trip_corporate_policy", "approve_corporate_policy_override"):
        route = _function(tree, name)
        calls = [
            node
            for node in ast.walk(route)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "get_trip_for_agency"
        ]
        assert calls, name
        assert any(
            len(call.args) >= 2
            and isinstance(call.args[1], ast.Name)
            and call.args[1].id == "agency_id"
            for call in calls
        )
