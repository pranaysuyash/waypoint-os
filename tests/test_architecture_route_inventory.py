from __future__ import annotations

from tools.architecture_route_inventory import build_inventory


def test_route_inventory_finds_backend_and_bff_routes():
    inventory = build_inventory()
    summary = inventory["summary"]

    assert summary["backend_route_count"] > 100
    assert summary["bff_route_map_count"] > 50


def test_route_inventory_tracks_server_py_and_router_module_ownership():
    inventory = build_inventory()
    owners = {
        row["owner"]: row["route_count"]
        for row in inventory["backend_owner_summary"]
    }

    assert owners["server.py"] > 0
    assert owners["drafts"] == 10
    assert owners["run_status"] == 4
    assert owners["settings"] == 8
    assert owners["team"] == 6


def test_route_inventory_detects_no_exact_backend_route_duplicates():
    inventory = build_inventory()

    assert inventory["potential_duplicate_backend_routes"] == {}


def test_route_inventory_captures_spine_run_timeout_policy():
    inventory = build_inventory()
    bff_routes = {
        row["frontend_path"]: row
        for row in inventory["bff_routes"]
    }

    assert bff_routes["spine/run"]["backend_path"] == "run"
    assert bff_routes["spine/run"]["timeout_policy"] == "LONG_RUNNING_COMMAND_TIMEOUT_MS"


def test_route_inventory_has_no_bff_backend_paths_without_runtime_route():
    inventory = build_inventory()

    assert inventory["summary"]["bff_unmatched_backend_path_count"] == 0
    assert inventory["bff_unmatched_backend_routes"] == []
