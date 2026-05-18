"""
Manual tests for draft_store.py.
Run with: cd /Users/pranay/Projects/travel_agency_agent && uv run python spine_api/draft_store_test.py
"""

import sys
sys.path.insert(0, "/Users/pranay/Projects/travel_agency_agent")

from spine_api.draft_store import DraftStore, FileDraftStore, Draft


def test_create_and_get():
    print("=== test_create_and_get ===")
    draft = DraftStore.create(
        agency_id="agency_001",
        created_by="user_001",
        name="Test Draft",
        customer_message="Flight cancelled, need rebook",
        stage="discovery",
        operating_mode="emergency",
    )
    assert draft.id.startswith("draft_")
    assert draft.status == "open"
    assert draft.name == "Test Draft"
    print(f"  Created draft: {draft.id}")

    fetched = DraftStore.get(draft.id)
    assert fetched is not None
    assert fetched.id == draft.id
    assert fetched.customer_message == "Flight cancelled, need rebook"
    print(f"  Fetched draft OK")
    return draft.id


def test_patch(draft_id: str):
    print("=== test_patch ===")
    updated = DraftStore.patch(draft_id, {"agent_notes": "Customer prefers morning flights"})
    assert updated is not None
    assert updated.agent_notes == "Customer prefers morning flights"
    assert updated.version == 2  # version incremented
    print(f"  Patched draft, version={updated.version}")

    # Test optimistic concurrency
    try:
        DraftStore.patch(draft_id, {"agent_notes": "Override"}, expected_version=1)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "version conflict" in str(e)
        print(f"  Optimistic concurrency works: {e}")


def test_list_by_agency(draft_id: str):
    print("=== test_list_by_agency ===")
    drafts = DraftStore.list_by_agency("agency_001")
    assert any(d.id == draft_id for d in drafts)
    print(f"  Found draft in agency listing ({len(drafts)} total)")


def test_discard_and_restore(draft_id: str):
    print("=== test_discard_and_restore ===")
    discarded = DraftStore.discard(draft_id, "user_001")
    assert discarded is not None
    assert discarded.status == "discarded"
    print(f"  Discarded draft")

    restored = DraftStore.restore(draft_id)
    assert restored is not None
    assert restored.status == "open"
    print(f"  Restored draft")


def test_promote(draft_id: str):
    print("=== test_promote ===")
    promoted = DraftStore.promote(draft_id, "trip_abc123")
    assert promoted is not None
    assert promoted.status == "promoted"
    assert promoted.promoted_trip_id == "trip_abc123"
    print(f"  Promoted draft to trip_abc123")


def test_update_run_state(draft_id: str) -> str:
    print("=== test_update_run_state ===")
    # Create a fresh draft for this test (returns ID for cleanup)
    draft = DraftStore.create(
        agency_id="agency_001",
        created_by="user_001",
        name="Run State Test",
    )
    updated = DraftStore.update_run_state(
        draft.id,
        run_id="run_xyz789",
        run_state="blocked",
        run_snapshot={"block_reason": "Missing dates", "gate": "NB01"},
    )
    assert updated is not None
    assert updated.status == "blocked"
    assert updated.last_run_id == "run_xyz789"
    assert len(updated.run_snapshots) == 1
    print(f"  Run state updated to blocked, snapshots={len(updated.run_snapshots)}")
    return draft.id


def test_rebuild_index():
    print("=== test_rebuild_index ===")
    index = FileDraftStore.rebuild_index()
    assert "by_agency" in index
    assert "by_user" in index
    assert "by_status" in index
    print(f"  Index rebuilt: agencies={len(index['by_agency'])}, statuses={list(index['by_status'].keys())}")


def test_auto_name_generation() -> list[str]:
    print("=== test_auto_name_generation ===")
    # Auto-name generation happens at API layer, but we can test store with explicit names
    draft1 = DraftStore.create(
        agency_id="agency_001",
        created_by="user_001",
        name="Sharma family · Singapore · Jun 2026",
        customer_message="Sharma family wants to go to Singapore in June 2026",
    )
    assert "Sharma family" in draft1.name
    print(f"  Draft name: '{draft1.name}'")

    draft2 = DraftStore.create(
        agency_id="agency_001",
        created_by="user_001",
        name="Rahul — urgent rebooking",
        agent_notes="Rahul needs urgent rebooking due to flight cancellation",
    )
    assert "Rahul" in draft2.name
    print(f"  Draft name: '{draft2.name}'")
    return [draft1.id, draft2.id]


def cleanup_created(created_ids: list[str]) -> None:
    """Delete only the drafts created by this test run.

    Uses a targeted ID list rather than a glob so committed seed fixtures in
    data/drafts/ are never touched.  The old broad cleanup() would nuke the
    entire directory — including intentional fixtures — and was never called
    after tests, leaving orphan files behind.

    Index entries are removed surgically (not via rebuild_index) to avoid
    reordering the committed fixture list on every test run.
    """
    import json
    from spine_api.draft_store import DRAFTS_DIR, INDEX_FILE

    id_set = set(created_ids)

    # Remove draft files.
    removed = 0
    for draft_id in created_ids:
        path = DRAFTS_DIR / f"{draft_id}.json"
        if path.exists():
            path.unlink()
            removed += 1

    # Surgically remove test IDs from every list in the index so we don't
    # reorder the committed fixture entries.
    if removed and INDEX_FILE.exists():
        with open(INDEX_FILE) as f:
            index = json.load(f)
        for section in index.values():
            if isinstance(section, dict):
                for key in list(section.keys()):
                    if isinstance(section[key], list):
                        section[key] = [v for v in section[key] if v not in id_set]
                        if not section[key]:
                            del section[key]
        with open(INDEX_FILE, "w") as f:
            json.dump(index, f, indent=2)
            f.write("\n")

    print(f"=== cleanup: removed {removed} test draft(s), index updated surgically ===")


if __name__ == "__main__":
    _created: list[str] = []

    draft_id = test_create_and_get()
    _created.append(draft_id)
    test_patch(draft_id)
    test_list_by_agency(draft_id)
    test_discard_and_restore(draft_id)
    test_promote(draft_id)

    run_state_draft = test_update_run_state(draft_id)
    if run_state_draft:
        _created.append(run_state_draft)

    test_rebuild_index()

    auto_name_ids = test_auto_name_generation()
    if auto_name_ids:
        _created.extend(auto_name_ids)

    print("\n✅ All tests passed!")
    cleanup_created(_created)
