"""RDA-2026-09-08 FT-06 — product-B event store segment rotation.

The append-only JSONL store previously grew without bound while every write
paid an O(N) dedupe scan. Writes now rotate an oversized segment to
`<name>.1` (one retained generation) under the store lock. Documented
trade-off: dedupe/KPI reads cover the current segment only after rotation.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from spine_api.product_b_events import ProductBEventStore


@pytest.fixture()
def isolated_store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    data_dir = tmp_path / "product_b_events"
    raw_file = data_dir / "events_raw.jsonl"
    normalized_file = data_dir / "events_normalized.jsonl"
    monkeypatch.setattr(ProductBEventStore, "DATA_DIR", data_dir)
    monkeypatch.setattr(ProductBEventStore, "RAW_FILE", raw_file)
    monkeypatch.setattr(ProductBEventStore, "NORMALIZED_FILE", normalized_file)
    return ProductBEventStore


def _event(store: type[ProductBEventStore], seq: int) -> dict:
    return store.build_event(
        event_name="intake_started",
        session_id=f"sess_{seq}",
        inquiry_id=f"inq_{seq}",
        actor_type="traveler",
        channel="web",
        workspace_id="waypoint-hq",
        properties={
            "input_mode": "freeform_text",
            "has_destination": False,
            "has_dates": False,
            "has_budget_band": False,
            "has_traveler_profile": False,
        },
    )


class TestStoreRotation:
    def test_no_rotation_under_cap(self, isolated_store, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr(ProductBEventStore, "_max_store_bytes", classmethod(lambda cls: 10 * 1024 * 1024))
        for seq in range(3):
            result = isolated_store.log_event(_event(isolated_store, seq))
            assert result["status"] == "accepted"
        assert not isolated_store.NORMALIZED_FILE.with_name(isolated_store.NORMALIZED_FILE.name + ".1").exists()

    def test_rotation_when_oversized(self, isolated_store, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr(ProductBEventStore, "_max_store_bytes", classmethod(lambda cls: 2048))
        for seq in range(12):
            isolated_store.log_event(_event(isolated_store, seq))

        rotated = isolated_store.NORMALIZED_FILE.with_name(isolated_store.NORMALIZED_FILE.name + ".1")
        assert rotated.exists(), "oversized normalized segment should rotate to .1"
        assert isolated_store.NORMALIZED_FILE.exists(), "current segment must continue receiving writes"
        assert isolated_store.RAW_FILE.with_name(isolated_store.RAW_FILE.name + ".1").exists()
        assert isolated_store.NORMALIZED_FILE.stat().st_size <= 2048 + 4096

    def test_reads_and_dedupe_work_after_rotation(self, isolated_store, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr(ProductBEventStore, "_max_store_bytes", classmethod(lambda cls: 2048))
        for seq in range(12):
            isolated_store.log_event(_event(isolated_store, seq))

        current_events = isolated_store.list_events(window_days=30)
        assert len(current_events) >= 1

        # Dedupe still applies within the current segment: re-submitting the
        # exact same envelope (same event_id) must be recognized as duplicate.
        replay = _event(isolated_store, 11)
        assert isolated_store.log_event(replay)["status"] == "accepted"
        assert isolated_store.log_event(replay)["status"] == "duplicate"

    def test_env_cap_floor_enforced(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("PUBLIC_B_EVENTS_MAX_BYTES", "10")
        assert ProductBEventStore._max_store_bytes() == 64 * 1024

    def test_env_cap_invalid_falls_back_to_default(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("PUBLIC_B_EVENTS_MAX_BYTES", "not-a-number")
        assert ProductBEventStore._max_store_bytes() == 10 * 1024 * 1024

    def test_env_cap_respected_when_set(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("PUBLIC_B_EVENTS_MAX_BYTES", "1048576")
        assert ProductBEventStore._max_store_bytes() == 1048576
