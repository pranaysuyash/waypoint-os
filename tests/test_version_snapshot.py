"""Tests for VersionSnapshot — immutable version snapshots for extraction attempts."""

from __future__ import annotations

import os
from datetime import datetime, timezone

import pytest

from src.intake.version_snapshot import (
    VersionDimension,
    VersionSnapshot,
    RolloutMode,
    capture_version_snapshot,
    detect_rollout_change,
)


# ---------------------------------------------------------------------------
# VersionDimension tests
# ---------------------------------------------------------------------------

class TestVersionDimension:
    def test_from_env_reads_version(self, monkeypatch):
        monkeypatch.setenv("TEST_PROMPT_VERSION", "v3")
        dim = VersionDimension.from_env("TEST_PROMPT_VERSION")
        assert dim.version == "v3"
        assert dim.content_hash is None

    def test_from_env_with_content_hash(self, monkeypatch):
        monkeypatch.setenv("TEST_PROMPT_VERSION", "v2")
        monkeypatch.setenv("TEST_PROMPT_TEXT", "You are a travel agent.")
        dim = VersionDimension.from_env("TEST_PROMPT_VERSION", "TEST_PROMPT_TEXT")
        assert dim.version == "v2"
        assert dim.content_hash is not None
        assert len(dim.content_hash) == 12  # SHA-256 prefix

    def test_from_env_defaults(self, monkeypatch):
        monkeypatch.delenv("NONEXISTENT_KEY", raising=False)
        dim = VersionDimension.from_env("NONEXISTENT_KEY")
        assert dim.version == "v1"
        assert dim.content_hash is None

    def test_to_dict(self):
        dim = VersionDimension(version="v5", content_hash="abc123")
        d = dim.to_dict()
        assert d == {"version": "v5", "content_hash": "abc123"}

    def test_frozen(self):
        dim = VersionDimension(version="v1")
        with pytest.raises(AttributeError):
            dim.version = "v2"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# VersionSnapshot capture tests
# ---------------------------------------------------------------------------

class TestVersionSnapshotCapture:
    def test_capture_reads_env(self, monkeypatch):
        monkeypatch.setenv("EXTRACTION_PROMPT_VERSION", "v4")
        monkeypatch.setenv("EXTRACTION_SCHEMA_VERSION", "v2")
        monkeypatch.setenv("EXTRACTION_ROUTING_VERSION", "v3")

        snap = VersionSnapshot.capture(document_type="passport")

        assert snap.prompt_version == "v4"
        assert snap.schema_version == "v2"
        assert snap.routing_version == "v3"
        assert snap.document_type == "passport"
        assert snap.captured_at  # auto-populated
        assert snap.rollout_mode == RolloutMode.FULL

    def test_capture_explicit_overrides(self, monkeypatch):
        monkeypatch.setenv("EXTRACTION_PROMPT_VERSION", "v1")

        snap = VersionSnapshot.capture(
            prompt_version="v99",
            document_type="visa",
            rollout_mode=RolloutMode.SHADOW,
        )

        assert snap.prompt_version == "v99"
        assert snap.document_type == "visa"
        assert snap.rollout_mode == RolloutMode.SHADOW

    def test_capture_default_versions(self):
        snap = VersionSnapshot.capture()
        assert snap.prompt_version == "v1"
        assert snap.schema_version == "v1"
        assert snap.routing_version == "v1"
        assert snap.dictionary_version == "v1"
        assert snap.normalization_version == "v1"

    def test_capture_with_rollout_metadata(self):
        meta = {"traffic_percentage": 10, "feature_flag": "new_prompt_v2"}
        snap = VersionSnapshot.capture(
            rollout_mode=RolloutMode.CANARY,
            rollout_metadata=meta,
        )
        assert snap.rollout_mode == RolloutMode.CANARY
        assert snap.rollout_metadata == meta

    def test_prompt_hash_from_content(self, monkeypatch):
        monkeypatch.setenv("EXTRACTION_PROMPT_TEXT", "You are a travel extraction agent.")
        snap = VersionSnapshot.capture()
        assert snap.prompt_hash is not None
        assert len(snap.prompt_hash) == 12

    def test_frozen(self):
        snap = VersionSnapshot.capture()
        with pytest.raises(AttributeError):
            snap.prompt_version = "v2"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Diff tests
# ---------------------------------------------------------------------------

class TestVersionSnapshotDiff:
    def test_no_diff_identical(self):
        a = VersionSnapshot.capture(prompt_version="v1", schema_version="v1")
        b = VersionSnapshot.capture(prompt_version="v1", schema_version="v1")
        assert a.diff(b) == []

    def test_prompt_diff(self):
        a = VersionSnapshot.capture(prompt_version="v1")
        b = VersionSnapshot.capture(prompt_version="v2")
        assert a.diff(b) == ["prompt"]

    def test_multiple_diffs(self):
        a = VersionSnapshot.capture(prompt_version="v1", schema_version="v1")
        b = VersionSnapshot.capture(prompt_version="v2", schema_version="v3")
        changed = a.diff(b)
        assert "prompt" in changed
        assert "schema" in changed
        assert len(changed) == 2

    def test_all_diffs(self):
        a = VersionSnapshot.capture(
            prompt_version="v1", schema_version="v1", routing_version="v1",
            dictionary_version="v1", normalization_version="v1",
        )
        b = VersionSnapshot.capture(
            prompt_version="v2", schema_version="v2", routing_version="v2",
            dictionary_version="v2", normalization_version="v2",
        )
        assert len(a.diff(b)) == 5

    def test_changed_dimensions_with_baseline(self):
        a = VersionSnapshot.capture(prompt_version="v1", schema_version="v1", routing_version="v1")
        b = VersionSnapshot.capture(prompt_version="v2", schema_version="v1", routing_version="v1")
        changed = b.changed_dimensions(a)
        assert "prompt" in changed
        assert "schema" not in changed
        assert "routing" not in changed
        assert changed["prompt"]["before"]["version"] == "v1"
        assert changed["prompt"]["after"]["version"] == "v2"

    def test_changed_dimensions_no_baseline(self):
        snap = VersionSnapshot.capture(prompt_version="v1")
        all_dims = snap.changed_dimensions(None)
        assert len(all_dims) == 5


# ---------------------------------------------------------------------------
# Serialisation tests
# ---------------------------------------------------------------------------

class TestVersionSnapshotSerialisation:
    def test_to_dict_roundtrip(self):
        snap = VersionSnapshot.capture(
            document_type="passport",
            rollout_mode=RolloutMode.CANARY,
            rollout_metadata={"traffic": 25},
        )
        d = snap.to_dict()
        restored = VersionSnapshot.from_dict(d)

        assert restored.prompt_version == snap.prompt_version
        assert restored.schema_version == snap.schema_version
        assert restored.document_type == "passport"
        assert restored.rollout_mode == RolloutMode.CANARY
        assert restored.rollout_metadata == {"traffic": 25}
        assert restored.captured_at == snap.captured_at

    def test_from_dict_ignores_unknown_keys(self):
        data = {
            "prompt_version": "v5",
            "unknown_future_field": "should_be_ignored",
            "schema_version": "v3",
        }
        snap = VersionSnapshot.from_dict(data)
        assert snap.prompt_version == "v5"
        assert snap.schema_version == "v3"


# ---------------------------------------------------------------------------
# RolloutMode tests
# ---------------------------------------------------------------------------

class TestRolloutMode:
    def test_all_modes_present(self):
        assert RolloutMode.SHADOW in RolloutMode.ALL
        assert RolloutMode.CANARY in RolloutMode.ALL
        assert RolloutMode.FULL in RolloutMode.ALL
        assert RolloutMode.ROLLED_BACK in RolloutMode.ALL
        assert RolloutMode.PENDING in RolloutMode.ALL


# ---------------------------------------------------------------------------
# detect_rollout_change tests
# ---------------------------------------------------------------------------

class TestDetectRolloutChange:
    def test_no_change_returns_none(self):
        a = VersionSnapshot.capture(prompt_version="v1", schema_version="v1")
        b = VersionSnapshot.capture(prompt_version="v1", schema_version="v1")
        assert detect_rollout_change(a, b) is None

    def test_detects_change(self):
        a = VersionSnapshot.capture(prompt_version="v1")
        b = VersionSnapshot.capture(prompt_version="v2")
        change = detect_rollout_change(a, b)
        assert change is not None
        assert "prompt" in change["changed_dimensions"]
        assert change["suggested_rollout_mode"] in (RolloutMode.CANARY, RolloutMode.SHADOW)

    def test_previous_none_returns_none(self):
        snap = VersionSnapshot.capture()
        assert detect_rollout_change(None, snap) is None

    def test_suggests_shadow_for_many_changes(self):
        a = VersionSnapshot.capture(
            prompt_version="v1", schema_version="v1", routing_version="v1",
        )
        b = VersionSnapshot.capture(
            prompt_version="v2", schema_version="v2", routing_version="v2",
        )
        change = detect_rollout_change(a, b)
        assert change is not None
        assert change["suggested_rollout_mode"] == RolloutMode.SHADOW


# ---------------------------------------------------------------------------
# Convenience function tests
# ---------------------------------------------------------------------------

class TestConvenienceFunctions:
    def test_capture_version_snapshot(self):
        snap = capture_version_snapshot(document_type="insurance")
        assert isinstance(snap, VersionSnapshot)
        assert snap.document_type == "insurance"
        assert snap.rollout_mode == RolloutMode.FULL
