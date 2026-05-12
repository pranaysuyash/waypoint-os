"""Build runtime D6 gate snapshots for public-surface authority decisions."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from .fixtures import AuditFixture, load_fixtures
from .gates import evaluate_report_against_manifest
from .manifest import load_manifest
from .rules.activity import run_activity_fixture
from .runner import run_eval_suite

DEFAULT_FIXTURE_ROOT = Path("data/fixtures/audit")
DEFAULT_SNAPSHOT_PATH = Path("data/evals/d6_audit_gate_snapshot.json")


def _rule_dispatch(fixture: AuditFixture):
    if fixture.category == "activity":
        return run_activity_fixture(fixture)
    return []


def build_gate_snapshot(*, fixture_root: Path = DEFAULT_FIXTURE_ROOT) -> dict[str, Any]:
    fixtures = load_fixtures(fixture_root)
    manifest = load_manifest()
    report = run_eval_suite(fixtures, rule_runner=_rule_dispatch)
    gate = evaluate_report_against_manifest(report, manifest)

    categories: dict[str, Any] = {}
    for name, decision in gate.categories.items():
        categories[name] = {
            "status": decision.status,
            "meets_thresholds": decision.meets_thresholds,
            "blocks_ci": decision.blocks_ci,
            "authoritative_for_public_surface": decision.authoritative_for_public_surface,
            "reasons": list(decision.reasons),
            "metrics": asdict(decision.metrics) if decision.metrics is not None else None,
        }

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "manifest_version": manifest.version,
        "fixture_root": str(fixture_root),
        "total_fixtures": report.total_fixtures,
        "categories": categories,
    }


def write_gate_snapshot(
    *,
    output_path: Path = DEFAULT_SNAPSHOT_PATH,
    fixture_root: Path = DEFAULT_FIXTURE_ROOT,
) -> Path:
    snapshot = build_gate_snapshot(fixture_root=fixture_root)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(snapshot, indent=2, sort_keys=True))
    return output_path


def stable_snapshot_view(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Return deterministic comparable view (ignores volatile timestamp)."""
    return {
        "manifest_version": snapshot.get("manifest_version"),
        "fixture_root": snapshot.get("fixture_root"),
        "total_fixtures": snapshot.get("total_fixtures"),
        "categories": snapshot.get("categories"),
    }


def verify_gate_snapshot_file(
    *,
    snapshot_path: Path = DEFAULT_SNAPSHOT_PATH,
    fixture_root: Path = DEFAULT_FIXTURE_ROOT,
) -> tuple[bool, dict[str, Any], dict[str, Any] | None]:
    expected = build_gate_snapshot(fixture_root=fixture_root)
    if not snapshot_path.exists():
        return False, expected, None
    try:
        actual = json.loads(snapshot_path.read_text())
    except Exception:
        return False, expected, None
    return stable_snapshot_view(actual) == stable_snapshot_view(expected), expected, actual
