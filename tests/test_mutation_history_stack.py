"""Tests for Invertible Time-Travel & Undo/Redo State Mutation Stack."""

from src.state.mutation_history_stack import TripMutationHistoryStack


def setup_function():
    TripMutationHistoryStack.clear()


def test_checkpoint_push_and_timeline():
    state1 = {"budget": 10000, "hotel": "Aman Tokyo", "days": 5}
    chk = TripMutationHistoryStack.push_checkpoint("TRIP-HIST-001", state1, author="agent_marcus", description="Initial intake")
    assert chk.checkpoint_id.startswith("chk_")

    timeline = TripMutationHistoryStack.get_timeline("TRIP-HIST-001")
    assert timeline["undo_available"] is True
    assert timeline["undo_count"] == 1
    assert timeline["redo_available"] is False


def test_undo_and_redo_cycle():
    trip_id = "TRIP-HIST-002"
    v1 = {"step": 1, "tier": "Silver"}
    v2 = {"step": 2, "tier": "Gold"}
    v3 = {"step": 3, "tier": "Platinum"}

    # Push checkpoints before changes
    TripMutationHistoryStack.push_checkpoint(trip_id, v1, description="Set Silver")
    TripMutationHistoryStack.push_checkpoint(trip_id, v2, description="Upgrade to Gold")

    # Current live state is v3
    # Step A: Undo back to v2
    restored_v2 = TripMutationHistoryStack.undo(trip_id, current_live_state=v3)
    assert restored_v2 == v2

    # Step B: Undo back to v1
    restored_v1 = TripMutationHistoryStack.undo(trip_id, current_live_state=restored_v2)
    assert restored_v1 == v1

    # Step C: Redo back forward to v2
    redone_v2 = TripMutationHistoryStack.redo(trip_id, current_live_state=restored_v1)
    assert redone_v2 == v2
