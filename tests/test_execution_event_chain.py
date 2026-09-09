"""
PA-19 tests (2026-09-08): per-agency tamper-evidence chain on execution_events.

Covers, against an in-memory SQLite engine (live-PG semantics mirrored; the
PG-specific RLS posture stays an integration seam per test_idempotency_sql_backend
precedent):
- emission chains events (prev_hash links to prior event_hash)
- verify_execution_chain passes on an intact chain
- payload tampering after append is detected by recompute
- continuity break (insertion with wrong prev_hash) is detected
- legacy pre-chain rows (NULL hashes) are an unanchored prefix, not a failure
- concurrent-append fork (two siblings sharing a prev_hash) is detected
"""

import os

os.environ["RUNNING_TESTS"] = "1"
os.environ.setdefault("TRIPSTORE_BACKEND", "file")

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from spine_api.models.tenant import ExecutionEvent
from spine_api.services.execution_event_service import (
    compute_event_hash,
    emit_event,
    verify_execution_chain,
)


@pytest_asyncio.fixture()
async def db():
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
        future=True,
    )
    async with engine.begin() as conn:
        await conn.run_sync(
            lambda sync_conn: ExecutionEvent.__table__.create(sync_conn, checkfirst=True)
        )
    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    async with session_maker() as session:
        yield session
    await engine.dispose()


AGENCY = "agency_chain_test"

pytestmark = pytest.mark.asyncio


async def _emit(db, event_type: str, subject_id: str = "bc_chain_1", **overrides):
    kwargs = {
        "agency_id": AGENCY,
        "trip_id": "trip_chain_1",
        "subject_type": "booking_confirmation",
        "subject_id": subject_id,
        "event_type": event_type,
        "event_category": "confirmation",
        "status_from": None,
        "status_to": event_type,
        "actor_type": "agent",
        "actor_id": "tester",
        "source": "agent_action",
        **overrides,
    }
    return await emit_event(db, **kwargs)


async def test_emission_chains_events(db):
    e1 = await _emit(db, "confirmation_created", subject_id="bc_one")
    e2 = await _emit(db, "confirmation_recorded", subject_id="bc_two")

    assert e1.prev_hash is None  # genesis
    assert e1.event_hash is not None
    assert e2.prev_hash == e1.event_hash  # links to prior

    verdict = await verify_execution_chain(db, agency_id=AGENCY)
    assert verdict["verdict"] == "pass"
    assert verdict["anchored"] == 2
    assert verdict["first_break"] is None
    assert verdict["forks"] == []


async def test_verifier_detects_payload_tamper(db):
    await _emit(db, "confirmation_created", subject_id="bc_tamper")
    e1 = (await db.execute(select(ExecutionEvent))).scalars().first()
    e1.event_metadata = {"tampered": True}

    verdict = await verify_execution_chain(db, agency_id=AGENCY)
    assert verdict["verdict"] == "fail"
    assert verdict["first_break"]["reason"].startswith("event_hash does not match")


async def test_verifier_detects_continuity_break(db):
    """Insertion whose prev_hash does not chain from the prior anchored
    event_hash — continuity break, detected on the forged row itself. The
    forged row's own event_hash covers its payload, so the recompute check
    passes and ONLY the continuity check can flag it."""
    await _emit(db, "confirmation_created", subject_id="bc_one")
    forged_payload = {
        "agency_id": AGENCY, "trip_id": "trip_chain_1",
        "subject_type": "booking_confirmation", "subject_id": "bc_forged",
        "event_type": "confirmation_recorded", "event_category": "confirmation",
        "status_from": None, "status_to": "recorded",
        "actor_type": "agent", "actor_id": "forger", "source": "agent_action",
        "event_metadata": None,
    }
    forged_hash = compute_event_hash("b" * 64, forged_payload)
    forged = ExecutionEvent(
        agency_id=AGENCY, trip_id="trip_chain_1",
        subject_type="booking_confirmation", subject_id="bc_forged",
        event_type="confirmation_recorded", event_category="confirmation",
        status_from=None, status_to="recorded",
        actor_type="agent", actor_id="forger", source="agent_action",
        prev_hash="b" * 64,  # does not chain from the genesis event
        event_hash=forged_hash,
    )
    db.add(forged)
    await db.commit()

    verdict = await verify_execution_chain(db, agency_id=AGENCY)
    assert verdict["verdict"] == "fail"
    assert "continuity break" in verdict["first_break"]["reason"]


async def test_legacy_null_hash_rows_are_unanchored_prefix(db):
    db.add(ExecutionEvent(
        agency_id=AGENCY, trip_id="trip_chain_legacy",
        subject_type="booking_confirmation", subject_id="bc_legacy",
        event_type="legacy_event", event_category="confirmation",
        status_from=None, status_to="legacy",
        actor_type="system", source="agent_action",
        prev_hash=None, event_hash=None,
    ))
    await db.commit()
    await _emit(db, "confirmation_created", subject_id="bc_one")

    verdict = await verify_execution_chain(db, agency_id=AGENCY)
    assert verdict["legacy_unanchored"] == 1
    assert verdict["verdict"] == "pass"


async def test_fork_duplicate_prev_hash_is_detected(db):
    """Two siblings chain from the same parent hash: the walk flags the
    second sibling as a fork even though both are internally consistent."""
    await _emit(db, "confirmation_created", subject_id="bc_parent")
    e1 = (await db.execute(select(ExecutionEvent))).scalars().first()

    def _sibling(tag: str) -> ExecutionEvent:
        event_payload = {
            "agency_id": AGENCY, "trip_id": "trip_chain_1",
            "subject_type": "booking_confirmation", "subject_id": f"bc_{tag}",
            "event_type": "confirmation_recorded", "event_category": "confirmation",
            "status_from": None, "status_to": "recorded",
            "actor_type": "agent", "actor_id": tag, "source": "agent_action",
            "event_metadata": None,
        }
        return ExecutionEvent(
            agency_id=AGENCY, trip_id="trip_chain_1",
            subject_type="booking_confirmation", subject_id=f"bc_{tag}",
            event_type="confirmation_recorded", event_category="confirmation",
            status_from=None, status_to="recorded",
            actor_type="agent", actor_id=tag, source="agent_action",
            prev_hash=e1.event_hash,
            event_hash=compute_event_hash(e1.event_hash, event_payload),
        )

    sib_a = _sibling("worker_a")
    sib_b = _sibling("worker_b")
    db.add_all([sib_a, sib_b])
    await db.commit()

    assert sib_a.prev_hash == sib_b.prev_hash == e1.event_hash  # same parent

    verdict = await verify_execution_chain(db, agency_id=AGENCY)
    assert verdict["verdict"] == "fail"
    assert len(verdict["forks"]) == 1
