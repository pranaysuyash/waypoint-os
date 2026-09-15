"""FND-0118 parity: verify/void join the transactional confirmation internals.

The F-31/FND-0118 migration moved create/record (and the insurance attach)
into caller-owned transactions so a row and its required execution event
commit atomically. ``verify_confirmation`` and ``void_confirmation`` carried
the legacy split-commit pattern (status commit, then a second event commit) —
a durable status transition could exist without its required event. These
tests pin the same transaction-participation contract for the two remaining
transitions:

- the ``*_in_transaction`` internals never commit on their own;
- each transition stages its required execution event with it;
- a mid-transaction failure leaves no partial status on the durable row.

Durable-state assertions always read through a FRESH session so they reflect
the database, not the identity map.

Coverage honesty (mirrors test_booking_confirmation_uniqueness.py): exercised
against an in-memory SQLite (aiosqlite) engine created from the two tenant
tables under test — the live Postgres test database is never written.
"""

import os
import uuid

import pytest
import pytest_asyncio

os.environ["RUNNING_TESTS"] = "1"

from spine_api.models.tenant import BookingConfirmation


@pytest_asyncio.fixture()
async def session_maker():
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from sqlalchemy.pool import StaticPool

    engine = create_async_engine(
        "sqlite+aiosqlite://",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
        future=True,
    )
    async with engine.begin() as conn:
        # Only the tables under test: the wider tenant metadata carries
        # Postgres-only JSONB columns that SQLite cannot compile.
        from spine_api.models.tenant import ExecutionEvent

        await conn.run_sync(
            lambda sync_conn: BookingConfirmation.__table__.create(
                sync_conn, checkfirst=True
            )
        )
        await conn.run_sync(
            lambda sync_conn: ExecutionEvent.__table__.create(
                sync_conn, checkfirst=True
            )
        )
    try:
        yield async_sessionmaker(engine, expire_on_commit=False)
    finally:
        await engine.dispose()


async def _make_recorded_confirmation(db) -> BookingConfirmation:
    from spine_api.services import confirmation_service

    trip_id = uuid.uuid4().hex[:10]
    c = await confirmation_service.create_confirmation_in_transaction(
        db,
        trip_id=trip_id,
        agency_id="agency_test",
        created_by="tester",
        data={"confirmation_type": "flight", "confirmation_number": "PN-ATOMIC-V"},
    )
    await confirmation_service.record_confirmation_in_transaction(
        db, c, recorded_by="tester"
    )
    await db.commit()
    return c


@pytest.mark.asyncio
async def test_verify_and_void_internals_never_commit_alone(
    session_maker, monkeypatch
):
    from spine_api.services import confirmation_service

    emitted: list[str] = []

    async def _record_event(db, **kwargs):
        emitted.append(kwargs["event_type"])
        return None

    monkeypatch.setattr(
        confirmation_service.execution_event_service, "emit_event", _record_event
    )

    async with session_maker() as db:
        commits: list[int] = []
        original_commit = db.commit

        async def _spy_commit():
            commits.append(1)
            return await original_commit()

        monkeypatch.setattr(db, "commit", _spy_commit)

        c = await _make_recorded_confirmation(db)
        commits.clear()
        emitted.clear()

        await confirmation_service.verify_confirmation_in_transaction(
            db, c, verified_by="tester"
        )
        await confirmation_service.void_confirmation_in_transaction(
            db, c, voided_by="tester"
        )

        # The internals must NOT have committed; the caller owns each durable
        # commit point, and each transition stages its required event with it.
        assert commits == []
        assert emitted == ["confirmation_verified", "confirmation_voided"]

        await db.commit()
        assert commits == [1]

    # Durable truth through a fresh session: exactly the transitions the
    # caller committed, nothing staged on its own.
    async with session_maker() as verify_db:
        row = await verify_db.get(BookingConfirmation, c.id)
        assert row is not None
        assert row.confirmation_status == "voided"
        assert row.verified_by == "tester"
        assert row.voided_by == "tester"


@pytest.mark.asyncio
async def test_void_internal_failure_leaves_status_untouched(
    session_maker, monkeypatch
):
    from spine_api.services import confirmation_service

    async with session_maker() as db:
        c = await _make_recorded_confirmation(db)
        # Capture before the rollback: rollback expires every attribute, and
        # touching an expired attribute afterwards would lazy-load synchronously.
        confirmation_id = c.id

        async def _event_emission_fails(*args, **kwargs):
            raise RuntimeError("event emission failed mid-transaction")

        monkeypatch.setattr(
            confirmation_service.execution_event_service,
            "emit_event",
            _event_emission_fails,
        )

        with pytest.raises(RuntimeError):
            await confirmation_service.void_confirmation_in_transaction(
                db, c, voided_by="tester"
            )

        await db.rollback()

    # Durable truth through a fresh session: the failed void left NO partial
    # status transition behind.
    async with session_maker() as verify_db:
        row = await verify_db.get(BookingConfirmation, confirmation_id)
        assert row is not None
        assert row.confirmation_status == "recorded", (
            "a mid-transaction failure must not leave a partial status transition"
        )
