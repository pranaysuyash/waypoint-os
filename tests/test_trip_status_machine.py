"""
Tests for the canonical trip-status transition invariant (register N-2 / F-29 class).

Contract under test:
- Intake-blocked statuses (incomplete / needs_followup / needs_clarification /
  awaiting_customer_details / escalated) can NEVER become quote-capable
  (ready_to_quote / quote_ready / ready_to_book) in one hop — enforced inside
  BOTH TripStore backends so every writer inherits it.
- All other transitions are legal; every status change is audited into the
  record's `status_history` (capped).
- `normalize_trip_status` maps legacy/case variants; unknowns pass through.
"""

import os
import uuid
from datetime import datetime, timezone

os.environ["RUNNING_TESTS"] = "1"
if not os.environ.get("JWT_SECRET"):
    os.environ["JWT_SECRET"] = "test-jwt-secret-for-pytest-only-32byt"

import pytest

from spine_api import persistence
from spine_api.core.trip_status import (
    IllegalTripStatusTransition,
    enforce_status_transition,
    is_intake_blocked,
    is_quote_capable,
    normalize_trip_status,
    record_status_transition,
)

TripStore = persistence.TripStore
FileTripStore = persistence.FileTripStore

AGENCY = "test_agency_status"


@pytest.fixture(autouse=True)
def status_test_env(monkeypatch):
    monkeypatch.setenv("DATA_PRIVACY_MODE", "beta")
    monkeypatch.setenv("SPINE_API_DISABLE_AUTH", "1")
    monkeypatch.setenv("TRIPSTORE_BACKEND", "file")


# ---------------------------------------------------------------- unit: invariant


@pytest.mark.parametrize("blocked", sorted(["incomplete", "needs_followup", "needs_clarification", "awaiting_customer_details", "escalated"]))
@pytest.mark.parametrize("quote_ready", sorted(["ready_to_quote", "quote_ready", "ready_to_book"]))
def test_intake_blocked_never_directly_quote_capable(blocked, quote_ready):
    with pytest.raises(IllegalTripStatusTransition):
        enforce_status_transition(blocked, quote_ready)


@pytest.mark.parametrize(
    "old,new",
    [
        ("new", "active"),
        ("active", "in_progress"),
        ("incomplete", "active"),  # the legal reprocess path: enrich first, then promote
        ("incomplete", "new"),
        ("needs_followup", "active"),
        ("active", "ready_to_quote"),
        ("in_progress", "completed"),
        (None, "active"),
        ("active", None),
        ("active", "active"),  # same-status write is a no-op, not a transition
    ],
)
def test_legal_transitions_pass(old, new):
    enforce_status_transition(old, new)  # must not raise


def test_case_insensitive_matching():
    with pytest.raises(IllegalTripStatusTransition):
        enforce_status_transition("INCOMPLETE", "Ready_To_Quote")


def test_classification_helpers():
    assert is_intake_blocked("incomplete")
    assert is_quote_capable("ready_to_book")
    assert not is_intake_blocked("active")
    assert not is_quote_capable("new")
    assert not is_intake_blocked(None)
    assert not is_quote_capable("")


# ---------------------------------------------------------------- unit: history + normalize


def test_history_records_and_caps():
    trip: dict = {}
    for i in range(60):
        if i % 2 == 0:
            record_status_transition(trip, "new", "active")
        else:
            record_status_transition(trip, "active", "in_progress")
    history = trip["status_history"]
    assert len(history) == 50  # capped
    assert history[0]["from"] == "new"
    assert history[0]["to"] == "active"
    assert "at" in history[0]


def test_history_ignores_noop():
    trip: dict = {}
    record_status_transition(trip, "active", "active")
    record_status_transition(trip, None, "active")
    assert trip == {}


def test_normalize_aliases():
    assert normalize_trip_status("") == "new"
    assert normalize_trip_status(None) == "new"
    assert normalize_trip_status("IN_PROGRESS") == "in_progress"
    assert normalize_trip_status(" Active ") == "active"
    # unknowns pass through untouched (additive-first: never brick a writer)
    assert normalize_trip_status("blocked") == "blocked"
    assert normalize_trip_status("some_future_status") == "some_future_status"


# ---------------------------------------------------- integration: file store guard


def _save(trip: dict) -> str:
    return FileTripStore.save_trip(trip, agency_id=trip.get("agency_id", AGENCY))


def test_file_store_blocks_illegal_promotion():
    trip_id = f"trip_{uuid.uuid4().hex[:12]}"
    _save(
        {
            "id": trip_id,
            "agency_id": AGENCY,
            "status": "incomplete",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
    )

    with pytest.raises(IllegalTripStatusTransition):
        _save({"id": trip_id, "agency_id": AGENCY, "status": "ready_to_quote"})

    # The store rejects before writing: persisted record unchanged.
    persisted = TripStore.get_trip(trip_id)
    assert persisted["status"] == "incomplete"
    assert "status_history" not in persisted


def test_file_store_allows_legal_transition_and_audits_it():
    trip_id = f"trip_{uuid.uuid4().hex[:12]}"
    _save({"id": trip_id, "agency_id": AGENCY, "status": "incomplete"})
    _save({"id": trip_id, "agency_id": AGENCY, "status": "active"})

    persisted = TripStore.get_trip(trip_id)
    assert persisted["status"] == "active"
    history = persisted["status_history"]
    assert history == [{"from": "incomplete", "to": "active", "at": history[0]["at"]}]


def test_file_store_history_accumulates_across_saves():
    trip_id = f"trip_{uuid.uuid4().hex[:12]}"
    _save({"id": trip_id, "agency_id": AGENCY, "status": "new"})
    _save({"id": trip_id, "agency_id": AGENCY, "status": "active"})
    _save({"id": trip_id, "agency_id": AGENCY, "status": "in_progress"})

    persisted = TripStore.get_trip(trip_id)
    transitions = [(h["from"], h["to"]) for h in persisted["status_history"]]
    assert transitions == [("new", "active"), ("active", "in_progress")]


def test_file_store_first_save_no_transition():
    trip_id = f"trip_{uuid.uuid4().hex[:12]}"
    _save({"id": trip_id, "agency_id": AGENCY, "status": "new"})
    persisted = TripStore.get_trip(trip_id)
    assert "status_history" not in persisted


def test_incomplete_trip_cannot_reach_quote_ready_via_reprocess_regression():
    """The ESCALATE-era hand-patched invariant, now structural: a reprocess that
    erroneously marks an incomplete lead as quote-ready is rejected at the store."""
    trip_id = f"trip_{uuid.uuid4().hex[:12]}"
    _save({"id": trip_id, "agency_id": AGENCY, "status": "incomplete"})
    with pytest.raises(IllegalTripStatusTransition):
        _save({"id": trip_id, "agency_id": AGENCY, "status": "ready_to_book"})


# --------------------------------------------- integration: update-path guards (review cycle 1 P1)


def test_file_store_update_trip_blocks_illegal_promotion():
    """The primary operator surface (manual trip update endpoint → update_trip)
    is guarded: no one-hop incomplete → quote-capable via updates."""
    trip_id = f"trip_{uuid.uuid4().hex[:12]}"
    _save({"id": trip_id, "agency_id": AGENCY, "status": "incomplete"})

    with pytest.raises(IllegalTripStatusTransition):
        FileTripStore.update_trip(trip_id, {"status": "ready_to_quote"})

    persisted = TripStore.get_trip(trip_id)
    assert persisted["status"] == "incomplete"


def test_file_store_update_trip_audits_legal_transition():
    trip_id = f"trip_{uuid.uuid4().hex[:12]}"
    _save({"id": trip_id, "agency_id": AGENCY, "status": "incomplete"})

    updated = FileTripStore.update_trip(trip_id, {"status": "active", "budget_max": 8000})

    assert updated["status"] == "active"
    assert updated["status_history"] == [
        {"from": "incomplete", "to": "active", "at": updated["status_history"][0]["at"]}
    ]
    assert updated["budget_max"] == 8000
    persisted = TripStore.get_trip(trip_id)
    assert persisted["status_history"] == updated["status_history"]


def test_file_store_update_trip_if_version_guarded():
    trip_id = f"trip_{uuid.uuid4().hex[:12]}"
    _save({"id": trip_id, "agency_id": AGENCY, "status": "needs_followup"})
    FileTripStore.update_trip(trip_id, {"budget_max": 1})  # establishes updated_at
    trip = TripStore.get_trip(trip_id)
    version_token = trip["updated_at"]

    with pytest.raises(IllegalTripStatusTransition):
        FileTripStore.update_trip_if_version(
            trip_id, {"status": "quote_ready"}, expected_updated_at=version_token
        )
    # Legal transition through the same CAS path still works.
    ok = FileTripStore.update_trip_if_version(
        trip_id, {"status": "active"}, expected_updated_at=version_token
    )
    assert ok is not None and ok["status"] == "active"


def test_orm_guard_helper_rejects_and_seeds_history():
    """Unit coverage for the SQL-row guard (no live DB needed): the invariant
    fires and legal transitions seed status_history into analytics._extra,
    preserving caller-supplied analytics keys."""
    from spine_api.persistence import _apply_status_guard_orm

    class FakeRow:
        status = "incomplete"
        analytics = {"_extra": {"status_history": [{"from": "new", "to": "incomplete", "at": "t0"}]}}

    row = FakeRow()
    with pytest.raises(IllegalTripStatusTransition):
        _apply_status_guard_orm(row, {"status": "ready_to_quote"})

    updates = {"status": "active", "analytics": {"custom": "keep-me"}}
    _apply_status_guard_orm(row, updates)
    extra = updates["analytics"]["_extra"]
    assert updates["analytics"]["custom"] == "keep-me"
    assert extra["status_history"] == [
        {"from": "new", "to": "incomplete", "at": "t0"},
        {"from": "incomplete", "to": "active", "at": extra["status_history"][1]["at"]},
    ]


def test_orm_guard_helper_noop_without_status_update():
    from spine_api.persistence import _apply_status_guard_orm

    class FakeRow:
        status = "active"
        analytics = None

    updates = {"budget_max": 5000}
    _apply_status_guard_orm(FakeRow(), updates)  # must not raise or mutate
    assert "analytics" not in updates


def test_sql_guard_predicate_rejects_blocked_to_capable():
    from spine_api.persistence import _status_guard_sql_predicate

    sql, params = _status_guard_sql_predicate("ready_to_quote", "g")
    assert sql.startswith("NOT (status IN (")
    assert params["g_new"] == "ready_to_quote"
    assert any(v == "ready_to_quote" for k, v in params.items() if k.endswith("_capable_0") or k.endswith("_capable_1") or k.endswith("_capable_2"))


# --------------------------------------------- review cycle 2, finding A: SQL folding


def test_fold_unmapped_updates_carries_non_columns_into_analytics():
    from spine_api.persistence import _fold_unmapped_updates

    folded = _fold_unmapped_updates({"status": "active", "packet": {"a": 1}, "packet_version": 3})
    assert folded["status"] == "active"
    assert folded["analytics"]["_extra"]["packet"] == {"a": 1}
    assert folded["analytics"]["_extra"]["packet_version"] == 3
    assert "packet" not in folded
    assert "packet_version" not in folded


def test_fold_unmapped_updates_preserves_existing_analytics_extra():
    from spine_api.persistence import _fold_unmapped_updates

    folded = _fold_unmapped_updates({"analytics": {"_extra": {"keep": "me"}}, "decision_state": "READY_FOR_STRATEGY"})
    assert folded["analytics"]["_extra"]["keep"] == "me"
    assert folded["analytics"]["_extra"]["decision_state"] == "READY_FOR_STRATEGY"


def test_fold_unmapped_updates_noop_for_column_only_updates():
    from spine_api.persistence import _fold_unmapped_updates

    folded = _fold_unmapped_updates({"status": "active", "stage": "proposal", "source": "whatsapp"})
    assert folded == {"status": "active", "stage": "proposal", "source": "whatsapp"}
    assert "analytics" not in folded


def test_fold_unmapped_updates_drops_saved_at():
    from spine_api.persistence import _fold_unmapped_updates

    folded = _fold_unmapped_updates({"status": "active", "saved_at": "2026-01-01T00:00:00Z"})
    assert "saved_at" not in folded
    assert "analytics" not in folded
