"""
intake.version_snapshot — Immutable version snapshots for extraction attempts.

Captures a point-in-time snapshot of all version dimensions (prompt, schema,
routing, dictionary, normalization) plus a content hash for each mutable
dimension. This enables:

  1. **Immutable audit trail**: each extraction attempt records exactly which
     prompt/schema/routing was active, reproducible years later.
  2. **Diff detection**: compare snapshots to identify which version dimension
     changed between attempts (prompt vs schema vs routing).
  3. **Rollout mode tracking**: attach rollout metadata to understand whether
     a version change was a shadow deploy, canary, or full rollout.

Usage:
    snapshot = VersionSnapshot.capture(document_type="passport")
    # snapshot.prompt_version, snapshot.prompt_hash, snapshot.schema_version, ...

    # Compare two snapshots
    diff = snapshot_a.diff(snapshot_b)
    # Returns list of changed dimensions: ["prompt", "schema"]
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Rollout mode constants
# ---------------------------------------------------------------------------

class RolloutMode:
    """Immutable constants for version rollout tracking."""

    SHADOW = "shadow"           # Version active in shadow mode only
    CANARY = "canary"           # Version active for a subset of traffic
    FULL = "full"               # Version fully rolled out
    ROLLED_BACK = "rolled_back" # Version was rolled back
    PENDING = "pending"         # Version change staged but not active

    ALL = frozenset({SHADOW, CANARY, FULL, ROLLED_BACK, PENDING})


# ---------------------------------------------------------------------------
# Version dimension model
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class VersionDimension:
    """A single version dimension with value and content hash."""

    version: str
    content_hash: Optional[str] = None  # SHA-256 prefix of the actual content

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_env(cls, version_key: str, content_key: str | None = None, hash_len: int = 12) -> "VersionDimension":
        """Build a dimension from environment variables."""
        version = os.environ.get(version_key, "v1")
        content_hash = None
        if content_key:
            content = os.environ.get(content_key)
            if content:
                content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()[:hash_len]
        return cls(version=version, content_hash=content_hash)


# ---------------------------------------------------------------------------
# Immutable version snapshot
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class VersionSnapshot:
    """Immutable point-in-time capture of all version dimensions.

    Each extraction attempt creates one snapshot. The snapshot is frozen
    (immutable) — it cannot be modified after creation, guaranteeing
    reproducibility.

    Dimensions:
        prompt_version / prompt_hash: Which prompt template was active.
        schema_version / schema_hash: Which output schema was enforced.
        routing_version / routing_hash: Which model routing policy was active.
        dictionary_version / dictionary_hash: Which normalization dictionary was used.
        normalization_version / normalization_hash: Which normalization rules were active.

    Metadata:
        document_type: e.g. "passport", "visa", "insurance".
        captured_at: ISO-8601 timestamp of snapshot creation.
        rollout_mode: How the version was deployed (shadow/canary/full/etc.).
        rollout_metadata: Additional rollout context (e.g. traffic percentage, feature flag).
    """

    # Prompt
    prompt_version: str = "v1"
    prompt_hash: Optional[str] = None

    # Schema
    schema_version: str = "v1"
    schema_hash: Optional[str] = None

    # Routing
    routing_version: str = "v1"
    routing_hash: Optional[str] = None

    # Dictionary
    dictionary_version: str = "v1"
    dictionary_hash: Optional[str] = None

    # Normalization
    normalization_version: str = "v1"
    normalization_hash: Optional[str] = None

    # Metadata
    document_type: str = ""
    captured_at: str = ""
    rollout_mode: str = RolloutMode.FULL
    rollout_metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Frozen dataclass — __post_init__ runs once at creation.
        # We use object.__setattr__ to set the default captured_at if empty.
        if not self.captured_at:
            object.__setattr__(self, "captured_at", datetime.now(timezone.utc).isoformat())

    # -- Factory ---------------------------------------------------------------

    @classmethod
    def capture(
        cls,
        document_type: str = "",
        rollout_mode: str = RolloutMode.FULL,
        rollout_metadata: Optional[dict[str, Any]] = None,
        *,
        prompt_version: str | None = None,
        schema_version: str | None = None,
        routing_version: str | None = None,
        dictionary_version: str | None = None,
        normalization_version: str | None = None,
    ) -> "VersionSnapshot":
        """Capture a snapshot from environment variables (or explicit overrides).

        Args:
            document_type: The document type being extracted.
            rollout_mode: How the version was deployed.
            rollout_metadata: Additional rollout context.
            prompt_version: Override prompt version (reads from env if None).
            schema_version: Override schema version (reads from env if None).
            routing_version: Override routing version (reads from env if None).
            dictionary_version: Override dictionary version (reads from env if None).
            normalization_version: Override normalization version (reads from env if None).
        """
        prompt_dim = VersionDimension.from_env("EXTRACTION_PROMPT_VERSION", "EXTRACTION_PROMPT_TEXT")
        schema_dim = VersionDimension.from_env("EXTRACTION_SCHEMA_VERSION")
        routing_dim = VersionDimension.from_env("EXTRACTION_ROUTING_VERSION")
        dictionary_dim = VersionDimension.from_env("EXTRACTION_DICTIONARY_VERSION")
        normalization_dim = VersionDimension.from_env("EXTRACTION_NORMALIZATION_VERSION")

        return cls(
            prompt_version=prompt_version or prompt_dim.version,
            prompt_hash=prompt_dim.content_hash,
            schema_version=schema_version or schema_dim.version,
            schema_hash=schema_dim.content_hash,
            routing_version=routing_version or routing_dim.version,
            routing_hash=routing_dim.content_hash,
            dictionary_version=dictionary_version or dictionary_dim.version,
            dictionary_hash=dictionary_dim.content_hash,
            normalization_version=normalization_version or normalization_dim.version,
            normalization_hash=normalization_dim.content_hash,
            document_type=document_type,
            rollout_mode=rollout_mode,
            rollout_metadata=rollout_metadata or {},
        )

    # -- Diff ------------------------------------------------------------------

    def diff(self, other: "VersionSnapshot") -> list[str]:
        """Return list of dimensions that differ between two snapshots.

        Returns a list like ["prompt", "schema"] when prompt_version or
        prompt_hash differs.
        """
        changed: list[str] = []

        for dim in ("prompt", "schema", "routing", "dictionary", "normalization"):
            v1 = getattr(self, f"{dim}_version")
            v2 = getattr(other, f"{dim}_version")
            h1 = getattr(self, f"{dim}_hash")
            h2 = getattr(other, f"{dim}_hash")

            if v1 != v2 or h1 != h2:
                changed.append(dim)

        return changed

    def changed_dimensions(self, baseline: Optional["VersionSnapshot"] = None) -> dict[str, dict[str, Any]]:
        """Return a dict of changed dimensions with before/after values.

        If baseline is None, returns all dimensions.
        """
        if baseline is None:
            return self._all_dimensions()

        result: dict[str, dict[str, Any]] = {}
        for dim in ("prompt", "schema", "routing", "dictionary", "normalization"):
            v1 = getattr(baseline, f"{dim}_version")
            v2 = getattr(self, f"{dim}_version")
            h1 = getattr(baseline, f"{dim}_hash")
            h2 = getattr(self, f"{dim}_hash")

            if v1 != v2 or h1 != h2:
                result[dim] = {
                    "before": {"version": v1, "hash": h1},
                    "after": {"version": v2, "hash": h2},
                }

        return result

    def _all_dimensions(self) -> dict[str, dict[str, Any]]:
        """Return all dimensions with current values."""
        return {
            dim: {"version": getattr(self, f"{dim}_version"), "hash": getattr(self, f"{dim}_hash")}
            for dim in ("prompt", "schema", "routing", "dictionary", "normalization")
        }

    # -- Serialisation ---------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-safe dict (immutable, no PII)."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "VersionSnapshot":
        """Deserialize from a dict. Ignores unknown keys for forward compat."""
        known = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in known}
        return cls(**filtered)


# ---------------------------------------------------------------------------
# Convenience functions
# ---------------------------------------------------------------------------

def capture_version_snapshot(
    document_type: str = "",
    rollout_mode: str = RolloutMode.FULL,
    rollout_metadata: Optional[dict[str, Any]] = None,
) -> VersionSnapshot:
    """Shorthand for VersionSnapshot.capture()."""
    return VersionSnapshot.capture(
        document_type=document_type,
        rollout_mode=rollout_mode,
        rollout_metadata=rollout_metadata,
    )


def detect_rollout_change(
    previous: Optional[VersionSnapshot],
    current: VersionSnapshot,
) -> Optional[dict[str, Any]]:
    """Detect if a rollout-relevant change occurred between two snapshots.

    Returns None if no change, or a dict describing the change with
    dimensions, previous/current values, and suggested rollout mode.
    """
    if previous is None:
        return None

    changed = current.diff(previous)
    if not changed:
        return None

    return {
        "changed_dimensions": changed,
        "previous": previous.to_dict(),
        "current": current.to_dict(),
        "suggested_rollout_mode": RolloutMode.CANARY if len(changed) <= 2 else RolloutMode.SHADOW,
    }
