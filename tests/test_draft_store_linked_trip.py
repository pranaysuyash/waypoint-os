"""DraftStore.update_run_state linked_trip_id recording (ADR_ESCALATE_LEAD_PERSISTENCE)."""

from __future__ import annotations

from spine_api.draft_store import DraftStore


def test_update_run_state_records_linked_trip_id(tmp_path, monkeypatch) -> None:
    import spine_api.draft_store as ds

    monkeypatch.setattr(ds, "DRAFTS_DIR", tmp_path)
    monkeypatch.setattr(ds, "INDEX_FILE", tmp_path / "index.json")

    draft = DraftStore.create(
        agency_id="agency-1",
        created_by="user-1",
        name="Test draft",
        customer_message="hello",
    )

    updated = DraftStore.update_run_state(
        draft_id=draft.id,
        run_id="run-1",
        run_state="blocked",
        linked_trip_id="trip-9",
    )
    assert updated is not None
    assert updated.linked_trip_ids == ["trip-9"]

    # Re-recording the same trip must not duplicate the linkage.
    updated2 = DraftStore.update_run_state(
        draft_id=draft.id,
        run_id="run-2",
        run_state="completed",
        linked_trip_id="trip-9",
    )
    assert updated2 is not None
    assert updated2.linked_trip_ids == ["trip-9"]

    # Omitted linked_trip_id preserves existing linkage.
    updated3 = DraftStore.update_run_state(
        draft_id=draft.id,
        run_id="run-3",
        run_state="completed",
    )
    assert updated3 is not None
    assert updated3.linked_trip_ids == ["trip-9"]
