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
        # Only the table under test: the wider tenant metadata carries
        # Postgres-only JSONB columns that SQLite cannot compile.
        await conn.run_sync(
            lambda sync_conn: BookingConfirmation.__table__.create(
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
