"""Runtime D6 public-surface authority resolution.

Prefers a concrete eval-gate snapshot when present, and falls back to manifest
status when no snapshot is available.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .manifest import load_manifest

_DEFAULT_SNAPSHOT_PATH = Path("data/evals/d6_audit_gate_snapshot.json")


@dataclass(slots=True)
class CategoryPublicAuthority:
    category: str
    authority: str
    category_status: str
    source: str
    reasons: list[str]


def _normalize_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes"}
    if isinstance(value, (int, float)):
        return bool(value)
    return False


def _load_snapshot() -> dict[str, Any] | None:
    snapshot_path = Path(os.environ.get("D6_AUDIT_GATE_SNAPSHOT_PATH") or _DEFAULT_SNAPSHOT_PATH)
    if not snapshot_path.exists():
        return None
    try:
        payload = json.loads(snapshot_path.read_text())
    except Exception:
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def resolve_public_authority(category: str) -> CategoryPublicAuthority:
    normalized = (category or "").strip().lower() or "unknown"
    manifest = load_manifest()
    manifest_category = manifest.categories.get(normalized)
    manifest_status = manifest_category.status if manifest_category else "untracked"
    manifest_authority = "authoritative" if manifest_status == "gating" else "advisory"

    snapshot = _load_snapshot()
    if snapshot:
        categories = snapshot.get("categories")
        if isinstance(categories, dict):
            category_snapshot = categories.get(normalized)
            if isinstance(category_snapshot, dict):
                authoritative = _normalize_bool(category_snapshot.get("authoritative_for_public_surface"))
                status = str(category_snapshot.get("status") or manifest_status)
                reasons = category_snapshot.get("reasons")
                return CategoryPublicAuthority(
                    category=normalized,
                    authority="authoritative" if authoritative else "advisory",
                    category_status=status,
                    source="eval_snapshot",
                    reasons=[str(item) for item in reasons] if isinstance(reasons, list) else [],
                )

    return CategoryPublicAuthority(
        category=normalized,
        authority=manifest_authority,
        category_status=manifest_status,
        source="manifest_fallback",
        reasons=["snapshot_missing_or_category_unavailable"],
    )

