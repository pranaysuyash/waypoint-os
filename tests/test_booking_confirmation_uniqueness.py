"""
Part-J #3 (2026-09-07): at most ONE active BookingConfirmation per
(trip_id, confirmation_type). Voids are excluded, so a legitimate re-issue
after a void stays legal.

Coverage honesty (mirrors test_idempotency_sql_backend.py): exercised against
an **in-memory SQLite (aiosqlite) engine** created from the tenant model
metadata — the live Postgres test database is never written. The Postgres
partial-index seam is additionally carried by the alembic revision
``bc_active_type_uniqueness``.
"""

import os
import uuid
from datetime import datetime, timezone

import pytest
import pytest_asyncio

os.environ["RUNNING_TESTS"] = "1"

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from spine_api.models.tenant import BookingConfirmation


@pytest_asyncio.fixture()
async def db_session():
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
        await conn.run_sync(
            lambda sync_conn: BookingConfirmation.__table__.create(
                sync_conn, checkfirst=True
            )
        )
        from spine_api.models.tenant import ExecutionEvent

        await conn.run_sync(
            lambda sync_conn: ExecutionEvent.__table__.create(
                sync_conn, checkfirst=True
            )
        )
    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    async with session_maker() as session:
        yield session
    await engine.dispose()


def _confirmation(trip_id: str, status: str = "recorded") -> BookingConfirmation:
    return BookingConfirmation(
        agency_id="agency_test",
        trip_id=trip_id,
        confirmation_type="flight",
        confirmation_status=status,
        created_by="test",
    )


@pytest.mark.asyncio
async def test_second_active_flight_confirmation_for_same_trip_is_rejected(db_session):
    trip_id = f"trip_{uuid.uuid4().hex[:10]}"
    db_session.add(_confirmation(trip_id))
    await db_session.commit()

    db_session.add(_confirmation(trip_id))
    with pytest.raises(IntegrityError):
        await db_session.commit()


@pytest.mark.asyncio
async def test_voided_confirmation_frees_the_slot(db_session):
    trip_id = f"trip_{uuid.uuid4().hex[:10]}"
    first = _confirmation(trip_id)
    db_session.add(first)
    await db_session.commit()

    first.confirmation_status = "voided"
    first.voided_by = "test"
    first.voided_at = datetime.now(timezone.utc)
    await db_session.commit()

    db_session.add(_confirmation(trip_id))
    await db_session.commit()


@pytest.mark.asyncio
async def test_same_type_across_different_trips_is_allowed(db_session):
    db_session.add(_confirmation(f"trip_{uuid.uuid4().hex[:10]}"))
    db_session.add(_confirmation(f"trip_{uuid.uuid4().hex[:10]}"))
    await db_session.commit()


# ---------------------------------------------------------------------------
# F-31 / FND-0118: transaction-participating internals
#
# The canonical service internals must stage rows + required events inside a
# caller-owned transaction: a failure anywhere before the caller's commit
# leaves NO partial state, and the internals themselves never commit.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_in_transaction_failure_leaves_no_partial_state(db_session, monkeypatch):
    from spine_api.services import confirmation_service

    async def _event_emission_fails(*args, **kwargs):
        raise RuntimeError("event emission failed mid-transaction")

    monkeypatch.setattr(
        confirmation_service.execution_event_service, "emit_event", _event_emission_fails
    )
    trip_id = f"trip_{uuid.uuid4().hex[:10]}"

    with pytest.raises(RuntimeError):
        await confirmation_service.create_confirmation_in_transaction(
            db_session,
            trip_id=trip_id,
            agency_id="agency_test",
            created_by="tester",
            data={"confirmation_type": "insurance", "confirmation_number": "PN-ATOMIC-1"},
        )

    await db_session.rollback()
    rows = (
        (await db_session.execute(select(BookingConfirmation))).scalars().all()
    )
    assert rows == [], "a mid-transaction failure must not leave a partial confirmation row"


@pytest.mark.asyncio
async def test_create_and_record_internals_never_commit_alone(db_session, monkeypatch):
    from spine_api.services import confirmation_service

    emitted: list[str] = []

    async def _record_event(db, **kwargs):
        emitted.append(kwargs["event_type"])
        return None

    monkeypatch.setattr(
        confirmation_service.execution_event_service, "emit_event", _record_event
    )

    commits: list[int] = []
    original_commit = db_session.commit

    async def _spy_commit():
        commits.append(1)
        return await original_commit()

    monkeypatch.setattr(db_session, "commit", _spy_commit)

    trip_id = f"trip_{uuid.uuid4().hex[:10]}"
    c = await confirmation_service.create_confirmation_in_transaction(
        db_session,
        trip_id=trip_id,
        agency_id="agency_test",
        created_by="tester",
        data={"confirmation_type": "insurance", "confirmation_number": "PN-TXN-1"},
    )
    await confirmation_service.record_confirmation_in_transaction(
        db_session, c, recorded_by="tester"
    )

    # The transaction-participating internals must NOT have committed; the
    # caller owns the single durable commit point.
    assert commits == []
    assert emitted == ["confirmation_created", "confirmation_recorded"]

    await db_session.commit()
    assert commits == [1]

    row = (
        await db_session.execute(
            select(BookingConfirmation).where(BookingConfirmation.id == c.id)
        )
    ).scalar_one()
    assert row.confirmation_status == "recorded"
    assert row.recorded_by == "tester"


@pytest.mark.asyncio
async def test_insurance_attach_conflict_type_carries_existing_id():
    from spine_api.services.confirmation_service import ConfirmationAttachConflict

    exc = ConfirmationAttachConflict(
        "active exists", existing_confirmation_id="conf-123"
    )
    assert isinstance(exc, ValueError)
    assert exc.existing_confirmation_id == "conf-123"


# ---------------------------------------------------------------------------
# FND-0174 / AT-04: flight fulfillment → canonical SQL confirmation
#
# The engine's AT-04 path (try_record_fulfillment_confirmation) is the
# ADOPTED writer for the flight family: the SQL row is the durable truth and
# the trip blob carries only a ``sql_confirmation``/``confirmation_id``
# projection. Repair must converge on the durable row (relink), never
# double-record it. The canonical rls_session seam is bound to this file's
# in-memory engine so the background/RLS path runs without Postgres.
# ---------------------------------------------------------------------------


def _bind_rls_session_to(db_session, monkeypatch):
    import contextlib

    import spine_api.core.rls as rls_module

    @contextlib.asynccontextmanager
    async def _fake_rls_session(agency_id: str):
        yield db_session

    monkeypatch.setattr(rls_module, "rls_session", _fake_rls_session)


@pytest.mark.asyncio
async def test_at04_fulfillment_records_durable_flight_confirmation(
    db_session, monkeypatch
):
    from spine_api.services import confirmation_service

    _bind_rls_session_to(db_session, monkeypatch)
    trip_id = "trip_" + uuid.uuid4().hex[:10]

    first = await confirmation_service.try_record_fulfillment_confirmation(
        agency_id="agency_test",
        trip_id=trip_id,
        created_by="tester",
        pnr_locator="ABC123",
        e_ticket_number="ET-001",
        vcc_card_id="vcc-1",
        total_usd=1200.0,
        reality_tier="deterministic_preview",
        provider_connected=False,
    )
    assert first["recorded"] is True
    assert first.get("relinked") in (None, False)
    assert first["confirmation_id"]

    row = await db_session.get(BookingConfirmation, first["confirmation_id"])
    assert row is not None
    assert row.confirmation_type == "flight"
    assert row.confirmation_status == "recorded"
    assert row.agency_id == "agency_test"
    assert row.trip_id == trip_id


@pytest.mark.asyncio
async def test_at04_replay_relinks_existing_confirmation_never_double_records(
    db_session, monkeypatch
):
    from spine_api.services import confirmation_service

    _bind_rls_session_to(db_session, monkeypatch)
    trip_id = "trip_" + uuid.uuid4().hex[:10]
    kwargs = dict(
        agency_id="agency_test",
        trip_id=trip_id,
        created_by="tester",
        pnr_locator="ABC123",
        e_ticket_number="ET-001",
        vcc_card_id="vcc-1",
        total_usd=1200.0,
        reality_tier="deterministic_preview",
        provider_connected=False,
    )

    first = await confirmation_service.try_record_fulfillment_confirmation(**kwargs)
    assert first["recorded"] is True

    # A repair/retry that lost the blob-side marker must converge on the
    # EXISTING durable row instead of colliding with uq_bc_trip_type_active.
    replay = await confirmation_service.try_record_fulfillment_confirmation(**kwargs)
    assert replay["recorded"] is True
    assert replay.get("relinked") is True
    assert replay["confirmation_id"] == first["confirmation_id"]

    rows = (
        (
            await db_session.execute(
                select(BookingConfirmation).where(
                    BookingConfirmation.trip_id == trip_id,
                    BookingConfirmation.confirmation_type == "flight",
                )
            )
        )
        .scalars()
        .all()
    )
    assert len(rows) == 1, "convergent replay must never double-record"
