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


def test_update_run_state(draft_id: str):
    print("=== test_update_run_state ===")
    # Create a fresh draft for this test
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


def test_rebuild_index():
    print("=== test_rebuild_index ===")
    index = FileDraftStore.rebuild_index()
    assert "by_agency" in index
    assert "by_user" in index
    assert "by_status" in index
    print(f"  Index rebuilt: agencies={len(index['by_agency'])}, statuses={list(index['by_status'].keys())}")


def test_auto_name_generation():
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


def cleanup():
    print("=== cleanup ===")
    import shutil
    from spine_api.draft_store import DRAFTS_DIR, INDEX_FILE
    if DRAFTS_DIR.exists():
        for f in DRAFTS_DIR.glob("draft_*.json"):
            f.unlink()
        if INDEX_FILE.exists():
            INDEX_FILE.unlink()
    print("  Cleaned up draft files")


if __name__ == "__main__":
    cleanup()
    
    draft_id = test_create_and_get()
    test_patch(draft_id)
    test_list_by_agency(draft_id)
    test_discard_and_restore(draft_id)
    test_promote(draft_id)
    test_update_run_state(draft_id)
    test_rebuild_index()
    test_auto_name_generation()
    
    print("\n✅ All tests passed!")
