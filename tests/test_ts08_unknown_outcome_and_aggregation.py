"""
tests/test_ts08_unknown_outcome_and_aggregation.py — TS-08 (2026-09-10
training-session register): BOOKING_RESULT_UNKNOWN as a first-class
idempotency outcome, plus trip-level component-state aggregation.

Contract under test (Docs/architecture/TRIP_LIFECYCLE_STATE_CONTRACTS_2026-09-02.md
addendum 2026-09-10 / register TS-08):

UNKNOWN outcome:
- mark_unknown: fenced PENDING -> UNKNOWN transition.
- UNKNOWN blocks re-acquire (never re-execute without verification).
- UNKNOWN is exempt from TTL reclaim (an expired unresolved outcome must not
  be silently reset to PENDING — the duplicate-side-effect hazard).
- resolve_unknown: fenced UNKNOWN -> COMPLETED (verified success, replayable)
  or UNKNOWN -> FAILED (verified non-occurrence, retryable). Exactly one of
  payload/error required.

Aggregation:
- JourneyDependencyGraph.aggregate_commitment(): None / PENDING_BOOKING /
  BOOKED / BOOKING_EXCEPTION over per-node commitment statuses, void excluded.
- Journey-graph router GET surfaces commitment_verdict derived from stored
  nodes only.

SQL-backend coverage follows the repo's documented pattern: in-memory SQLite
(aiosqlite, StaticPool) — the live Postgres test database is never written.
"""

import os

import pytest

os.environ.setdefault("RUNNING_TESTS", "1")

from src.agents.idempotency import (  # noqa: E402
    IdempotencyRegistry,
    IdempotencyStatus,
    SqlIdempotencyBackend,
)
from src.schemas.journey_graph import (  # noqa: E402
    JourneyDependencyGraph,
    JourneyNode,
    NodeType,
)


@pytest.fixture()
def registry():
    """Fresh in-memory registry per test (no process singleton pollution)."""
    return IdempotencyRegistry()


def _acquire(registry, key="idem:ts08:act:01", ttl_seconds=86400):
    return registry.try_acquire(
        key, trip_id="t1", action_name="act", payload={"x": 1}, ttl_seconds=ttl_seconds
    )


# --- UNKNOWN outcome: in-memory registry ---------------------------------------


def test_mark_unknown_transitions_pending_to_unknown(registry):
    acquired, record = _acquire(registry)
    assert acquired
    assert registry.mark_unknown("idem:ts08:act:01", "provider timeout", fencing_token=record.fencing_token)
    assert record.status is IdempotencyStatus.UNKNOWN


def test_mark_unknown_requires_matching_fence(registry):
    _, record = _acquire(registry)
    assert not registry.mark_unknown("idem:ts08:act:01", "x", fencing_token="wrong-token")
    assert record.status is IdempotencyStatus.PENDING


def test_unknown_blocks_reacquire(registry):
    _, record = _acquire(registry)
    registry.mark_unknown("idem:ts08:act:01", "provider timeout", fencing_token=record.fencing_token)
    acquired2, existing = _acquire(registry)
    assert acquired2 is False
    assert existing is not None
    assert existing.status is IdempotencyStatus.UNKNOWN


def test_unknown_exempt_from_ttl_reclaim(registry):
    # ttl_seconds=0 makes the record expired immediately; an expired UNKNOWN
    # must NOT be dropped and re-acquired.
    _, record = _acquire(registry, key="idem:ts08:ttl:01", ttl_seconds=0)
    registry.mark_unknown("idem:ts08:ttl:01", "provider timeout", fencing_token=record.fencing_token)
    acquired2, existing = _acquire(registry, key="idem:ts08:ttl:01")
    assert acquired2 is False
    assert existing is not None
    assert existing.status is IdempotencyStatus.UNKNOWN


def test_expired_pending_is_still_reclaimed(registry):
    """Control for the exemption above: an expired PENDING record IS
    reclaimed (existing TTL semantics unchanged)."""
    _, _record = _acquire(registry, key="idem:ts08:ctl:01", ttl_seconds=0)
    acquired2, new_record = _acquire(registry, key="idem:ts08:ctl:01")
    assert acquired2 is True
    assert new_record.status is IdempotencyStatus.PENDING


def test_resolve_unknown_to_completed_enables_replay(registry):
    _, record = _acquire(registry)
    registry.mark_unknown("idem:ts08:act:01", "provider timeout", fencing_token=record.fencing_token)
    assert registry.resolve_unknown(
        "idem:ts08:act:01",
        response_payload={"status": "success", "pnr": "ABC123"},
        fencing_token=record.fencing_token,
    )
    acquired2, existing = _acquire(registry)
    assert acquired2 is False
    assert existing.status is IdempotencyStatus.COMPLETED
    assert existing.response_payload["pnr"] == "ABC123"


def test_resolve_unknown_to_failed_enables_retry(registry):
    _, record = _acquire(registry)
    registry.mark_unknown("idem:ts08:act:01", "provider timeout", fencing_token=record.fencing_token)
    assert registry.resolve_unknown(
        "idem:ts08:act:01",
        error_message="verified: booking never created",
        fencing_token=record.fencing_token,
    )
    acquired2, new_record = _acquire(registry)
    assert acquired2 is True  # verified-failure keys are retryable again
    assert new_record.status is IdempotencyStatus.PENDING


def test_resolve_unknown_requires_exactly_one_argument(registry):
    _, record = _acquire(registry)
    registry.mark_unknown("idem:ts08:act:01", "provider timeout", fencing_token=record.fencing_token)
    with pytest.raises(ValueError):
        registry.resolve_unknown("idem:ts08:act:01", fencing_token=record.fencing_token)
    with pytest.raises(ValueError):
        registry.resolve_unknown(
            "idem:ts08:act:01",
            response_payload={"a": 1},
            error_message="also set",
            fencing_token=record.fencing_token,
        )


def test_resolve_unknown_rejects_stale_fence(registry):
    _, record = _acquire(registry)
    registry.mark_unknown("idem:ts08:act:01", "provider timeout", fencing_token=record.fencing_token)
    assert not registry.resolve_unknown(
        "idem:ts08:act:01",
        error_message="verified",
        fencing_token="wrong-token",
    )
    assert record.status is IdempotencyStatus.UNKNOWN  # unchanged


def test_mark_unknown_only_from_pending(registry):
    _, record = _acquire(registry)
    registry.mark_completed("idem:ts08:act:01", {"ok": True}, fencing_token=record.fencing_token)
    assert not registry.mark_unknown("idem:ts08:act:01", "late timeout", fencing_token=record.fencing_token)
    assert record.status is IdempotencyStatus.COMPLETED


# --- UNKNOWN outcome: SQL backend (in-memory SQLite, StaticPool) ----------------


@pytest.fixture()
def sqlite_sql_backend():
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from sqlalchemy.pool import StaticPool

    engine = create_async_engine(
        "sqlite+aiosqlite://",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
        future=True,
    )
    backend = SqlIdempotencyBackend(
        engine=engine, session_maker=async_sessionmaker(engine, expire_on_commit=False)
    )
    yield backend
    backend._run(_dispose(engine))


async def _dispose(engine):
    await engine.dispose()


def test_sql_unknown_blocks_reacquire_and_resolves(sqlite_sql_backend):
    backend = sqlite_sql_backend
    key = "idem:ts08sql:act:01"

    acquired, record = backend.try_acquire(key, trip_id="t1", action_name="act", payload={"x": 1})
    assert acquired
    assert backend.mark_unknown(key, "provider timeout", fencing_token=record.fencing_token)

    # Re-acquire is refused while UNKNOWN.
    acquired2, existing = backend.try_acquire(key, trip_id="t1", action_name="act", payload={"x": 1})
    assert acquired2 is False
    assert existing.status is IdempotencyStatus.UNKNOWN

    # Verified success resolves to COMPLETED and replays.
    assert backend.resolve_unknown(
        key, response_payload={"status": "success"}, fencing_token=record.fencing_token
    )
    acquired3, replay = backend.try_acquire(key, trip_id="t1", action_name="act", payload={"x": 1})
    assert acquired3 is False
    assert replay.status is IdempotencyStatus.COMPLETED
    assert replay.response_payload == {"status": "success"}


def test_sql_unknown_exempt_from_ttl_reclaim(sqlite_sql_backend):
    backend = sqlite_sql_backend
    key = "idem:ts08sql:ttl:01"

    # ttl_seconds=0: the row is expired the moment it exists. An UNKNOWN row
    # must not be reclaimed to PENDING by a later acquire.
    acquired, record = backend.try_acquire(
        key, trip_id="t1", action_name="act", payload={"x": 1}, ttl_seconds=0
    )
    assert acquired
    backend.mark_unknown(key, "provider timeout", fencing_token=record.fencing_token)

    acquired2, existing = backend.try_acquire(key, trip_id="t1", action_name="act", payload={"x": 1})
    assert acquired2 is False
    assert existing.status is IdempotencyStatus.UNKNOWN


# --- Component-state aggregation ------------------------------------------------


def _node(node_id: str, commitment: str, node_type: NodeType = NodeType.FLIGHT) -> JourneyNode:
    return JourneyNode(
        node_id=node_id,
        node_type=node_type,
        title=node_id,
        commitment_status=commitment,  # type: ignore[arg-type]
    )


def test_aggregation_abstains_without_active_nodes():
    graph = JourneyDependencyGraph("t1")
    assert graph.aggregate_commitment() is None
    graph.add_node(_node("v1", "void"))
    assert graph.aggregate_commitment() is None  # void-only is not a booking


def test_aggregation_pending_booking():
    graph = JourneyDependencyGraph("t1")
    graph.add_node(_node("f1", "quoted"))
    graph.add_node(_node("h1", "held"))
    assert graph.aggregate_commitment() == "PENDING_BOOKING"


def test_aggregation_booked():
    graph = JourneyDependencyGraph("t1")
    graph.add_node(_node("f1", "ticketed"))
    graph.add_node(_node("h1", "booked"))
    assert graph.aggregate_commitment() == "BOOKED"


def test_aggregation_booking_exception_partial():
    """The tutor's shape: flight + hotel confirmed, Disney failed (stays
    uncommitted while siblings are ticketed) -> BOOKING_EXCEPTION."""
    graph = JourneyDependencyGraph("t1")
    graph.add_node(_node("f1", "ticketed"))
    graph.add_node(_node("h1", "booked"))
    graph.add_node(_node("d1", "quoted", NodeType.ACTIVITY))
    assert graph.aggregate_commitment() == "BOOKING_EXCEPTION"


def test_aggregation_void_excluded_from_verdict():
    graph = JourneyDependencyGraph("t1")
    graph.add_node(_node("f1", "ticketed"))
    graph.add_node(_node("d1", "void", NodeType.ACTIVITY))  # reversed commitment
    assert graph.aggregate_commitment() == "BOOKED"


def test_aggregation_from_stored_round_trip():
    graph = JourneyDependencyGraph.from_stored(
        "t1",
        nodes=[
            {"node_id": "f1", "node_type": "FLIGHT", "title": "F", "commitment_status": "ticketed"},
            {"node_id": "h1", "node_type": "HOTEL_STAY", "title": "H", "commitment_status": "quoted"},
        ],
    )
    assert graph.aggregate_commitment() == "BOOKING_EXCEPTION"


# --- Router surfaces the verdict -------------------------------------------------


def _save_graph_trip(nodes: list) -> tuple:
    import uuid

    from spine_api.persistence import TripStore

    agency_id = "d1e3b2b6-5509-4c27-b123-4b1e02b0bf5b"
    trip_id = f"trip_ts08_{uuid.uuid4().hex[:10]}"
    TripStore.save_trip(
        {
            "id": trip_id,
            "source": "test_ts08",
            "agency_id": agency_id,
            "status": "assigned",
            "stage": "booking",
            "extracted": {},
            "validation": {},
            "decision": {},
            "raw_input": {},
            "journey_graph_nodes": nodes,
        },
        agency_id=agency_id,
    )
    return trip_id, agency_id


def test_journey_graph_get_includes_commitment_verdict(session_client):
    """Stored nodes only: mixed commitment -> BOOKING_EXCEPTION in the GET."""
    from spine_api.persistence import TripStore

    trip_id, agency_id = _save_graph_trip(
        [
            {"node_id": "f1", "node_type": "FLIGHT", "title": "Flight", "commitment_status": "ticketed"},
            {"node_id": "h1", "node_type": "HOTEL_STAY", "title": "Hotel", "commitment_status": "quoted"},
        ]
    )
    try:
        resp = session_client.get(
            f"/api/v1/journey-graph/{trip_id}", headers={"X-Agency-ID": agency_id}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["commitment_verdict"] == "BOOKING_EXCEPTION"
    finally:
        try:
            TripStore.delete_trip_for_agency(trip_id, agency_id)
        except Exception:
            pass


def test_journey_graph_verdict_all_ticketed_is_booked(session_client):
    from spine_api.persistence import TripStore

    trip_id, agency_id = _save_graph_trip(
        [
            {"node_id": "f1", "node_type": "FLIGHT", "title": "Flight", "commitment_status": "ticketed"},
            {"node_id": "h1", "node_type": "HOTEL_STAY", "title": "Hotel", "commitment_status": "ticketed"},
        ]
    )
    try:
        resp = session_client.get(
            f"/api/v1/journey-graph/{trip_id}", headers={"X-Agency-ID": agency_id}
        )
        assert resp.status_code == 200
        assert resp.json()["commitment_verdict"] == "BOOKED"
    finally:
        try:
            TripStore.delete_trip_for_agency(trip_id, agency_id)
        except Exception:
            pass
