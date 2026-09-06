"""Trip-store SQL coverage and the R-03 pagination regression (R-03).

WHY THIS FILE EXISTS
    The trip-store unit tests call ``FileTripStore`` directly, so the production
    SQL path had *no* coverage from the suite at all. Every tenant-scoping,
    token-lookup and round-trip guarantee that actually runs in production was
    therefore unverified on the backend that serves it.

WHAT IT PINS
    * ``TripStore._iter_all_trips`` must page past the first page. The old code
      fetched a single fixed page of 1000 trips, so a token belonging to any
      trip past the first 1000 silently failed to resolve. That test is pure
      and needs no database.
    * The SQL backend must round-trip, enforce tenant isolation, honour
      ``offset`` when paging, and preserve proposal tokens through the
      ``analytics._extra`` mechanism.

SKIP BEHAVIOUR
    Only the Postgres-dependent tests are skipped (individually) when no
    DATABASE_URL is configured, so this never breaks a local run or an
    un-provisioned CI job. The pagination regression test always runs.
"""
from __future__ import annotations

import os
import uuid

import pytest

try:  # Prefer the app's own resolved DB URL when DATABASE_URL is unset.
    from spine_api.core.database import DATABASE_URL as _APP_DATABASE_URL
except Exception:  # pragma: no cover - import guard only
    _APP_DATABASE_URL = None

DATABASE_URL = os.getenv("DATABASE_URL") or _APP_DATABASE_URL

requires_db = pytest.mark.skipif(
    not DATABASE_URL,
    reason="No DATABASE_URL configured; SQL trip-store coverage needs a Postgres",
)


# ---------------------------------------------------------------------------
# R-03 regression: token lookups must reach past the first page.
# ---------------------------------------------------------------------------


def test_iter_all_trips_reaches_past_the_first_page(monkeypatch):
    """A trip beyond the first page must still be scanned.

    Fails before the fix: the old implementation read exactly one page of 1000
    and stopped, so trip #1001 was silently unreachable by token lookup.
    """
    import spine_api.persistence as persistence

    corpus = {f"t{i}": {"id": f"t{i}"} for i in range(1001)}
    ordered = [corpus[f"t{i}"] for i in range(1001)]
    page_size = 1000
    offsets = []

    def fake_list_trips(limit: int = 100, offset: int = 0, **_kwargs):
        offsets.append(offset)
        return ordered[offset : offset + limit]

    monkeypatch.setattr(
        persistence.TripStore, "list_trips", staticmethod(fake_list_trips)
    )

    scanned = [trip["id"] for trip in persistence.TripStore._iter_all_trips(page_size)]

    # The trip that the capped scan used to miss.
    assert "t1000" in scanned
    assert len(scanned) == 1001
    assert offsets == [0, 1000]


# ---------------------------------------------------------------------------
# Postgres-backed coverage of the SQL trip path.
# ---------------------------------------------------------------------------


@pytest.fixture()
def sql_agency_id():
    """Create a throwaway agency (trips FK to agencies.id) and clean up after."""
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy.pool import NullPool

    from spine_api.persistence import _run_async_blocking

    engine = create_async_engine(DATABASE_URL, poolclass=NullPool)
    agency_id = str(uuid.uuid4())

    async def _setup() -> None:
        async with engine.begin() as conn:
            await conn.execute(
                text(
                    "INSERT INTO agencies (id, slug, name, plan, settings, is_test, "
                    "jurisdiction, created_at) "
                    "VALUES (:id, :slug, :name, 'internal', CAST(:settings AS JSONB), "
                    "true, 'other', NOW()) "
                    "ON CONFLICT (id) DO NOTHING"
                ),
                {
                    "id": agency_id,
                    "slug": f"sql-cov-{agency_id[:8]}",
                    "name": "SQL coverage",
                    "settings": '{"source":"test_trip_store_sql_coverage"}',
                },
            )

    async def _teardown() -> None:
        async with engine.begin() as conn:
            await conn.execute(
                text("DELETE FROM trips WHERE agency_id = :aid"), {"aid": agency_id}
            )
            await conn.execute(
                text("DELETE FROM agencies WHERE id = :aid"), {"aid": agency_id}
            )
        await engine.dispose()

    _run_async_blocking(_setup())
    try:
        yield agency_id
    finally:
        _run_async_blocking(_teardown())


@pytest.fixture()
def sql_backend(monkeypatch):
    """Pin the facade onto SQL regardless of TRIPSTORE_BACKEND / ENVIRONMENT.

    Also lifts dogfood-mode redaction: this module covers the *persistence*
    path, and the privacy guard (which has its own tests) otherwise refuses
    freeform payloads.
    """
    import spine_api.persistence as persistence

    monkeypatch.setenv("DATA_PRIVACY_MODE", "beta")
    monkeypatch.setattr(
        persistence.TripStore,
        "_backend",
        staticmethod(lambda: persistence.SQLTripStore),
    )
    return persistence.TripStore


@requires_db
def test_sql_backend_roundtrip_and_tenant_isolation(sql_backend, sql_agency_id):
    trip_id = sql_backend.save_trip(
        {
            "id": str(uuid.uuid4()),
            "agency_id": sql_agency_id,
            "status": "new",
            "raw_input": {"note": "sql coverage"},
        },
        agency_id=sql_agency_id,
    )
    assert trip_id

    stored = sql_backend.get_trip_for_agency(trip_id, sql_agency_id)
    assert stored is not None
    assert stored["agency_id"] == sql_agency_id
    assert stored["raw_input"] == {"note": "sql coverage"}

    # Tenant isolation must hold on the SQL path, not only on the file path.
    assert sql_backend.get_trip_for_agency(trip_id, str(uuid.uuid4())) is None

    updated = sql_backend.update_trip_for_agency(trip_id, sql_agency_id, {"status": "done"})
    assert updated is not None
    assert updated["status"] == "done"

    assert sql_backend.delete_trip_for_agency(trip_id, sql_agency_id) is True
    assert sql_backend.get_trip_for_agency(trip_id, sql_agency_id) is None


@requires_db
def test_sql_list_trips_honours_offset(sql_backend, sql_agency_id):
    """Offset must actually paginate on SQL - the file store ignored it (R-03)."""
    ids = [
        sql_backend.save_trip(
            {"id": str(uuid.uuid4()), "agency_id": sql_agency_id, "status": "new"},
            agency_id=sql_agency_id,
        )
        for _ in range(3)
    ]
    page_one = sql_backend.list_trips(limit=2, offset=0, agency_id=sql_agency_id)
    page_two = sql_backend.list_trips(limit=2, offset=2, agency_id=sql_agency_id)

    assert len(page_one) == 2
    assert len(page_two) == 1
    assert {t["id"] for t in page_one} | {t["id"] for t in page_two} == set(ids)


@requires_db
def test_sql_proposal_token_survives_roundtrip_and_is_scannable(sql_backend, sql_agency_id):
    """Proposal tokens must survive the SQL round-trip and be visible to a scan.

    Tokens are not Trip columns - they ride in ``analytics._extra`` - so this
    guards that mechanism on the backend that serves production. The RLS agency
    is set inside the coroutine because the ContextVar is task-local and
    ``_run_async_blocking`` executes on its own loop.
    """
    import spine_api.persistence as persistence
    from spine_api.core.rls import set_rls_agency

    token = f"tok-{uuid.uuid4().hex}"
    trip_id = sql_backend.save_trip(
        {
            "id": str(uuid.uuid4()),
            "agency_id": sql_agency_id,
            "status": "new",
            "proposal_link_token": token,
        },
        agency_id=sql_agency_id,
    )
    assert trip_id

    async def _scan():
        set_rls_agency(sql_agency_id)
        offset = 0
        page_size = 1000
        while True:
            page = await persistence.SQLTripStore.list_trips(
                limit=page_size, offset=offset
            )
            for trip in page:
                if trip.get("proposal_link_token") == token:
                    return trip
            if len(page) < page_size:
                return None
            offset += page_size

    found = persistence._run_async_blocking(_scan())
    assert found is not None, "proposal token must survive the SQL round-trip"
    assert found["id"] == trip_id


# ---------------------------------------------------------------------------
# Review cycle 2, finding A: the SQL CAS must fold unmapped keys into
# analytics._extra and return the read shape — the production backend must
# not silently drop packet/decision_state/missing_fields on optimistic-sync.
# ---------------------------------------------------------------------------


@requires_db
def test_sql_cas_update_folds_unmapped_keys_and_returns_read_shape(sql_backend, sql_agency_id):
    trip_id = sql_backend.save_trip(
        {"id": str(uuid.uuid4()), "agency_id": sql_agency_id, "status": "new"},
        agency_id=sql_agency_id,
    )
    try:
        stored = sql_backend.get_trip_for_agency(trip_id, sql_agency_id)
        updated = sql_backend.update_trip_if_version_for_agency(
            trip_id,
            sql_agency_id,
            {
                "packet": {"destination": "Tokyo", "budget_max": 8000},
                "decision_state": "READY_FOR_STRATEGY",
                "missing_fields": [],
                "packet_version": 1,
                "status": "active",
            },
            expected_updated_at=stored.get("updated_at"),
        )

        assert updated is not None, "CAS must match on the fresh read"
        # Unmapped keys ride in analytics._extra but surface at top level.
        assert updated["packet"] == {"destination": "Tokyo", "budget_max": 8000}
        assert updated["decision_state"] == "READY_FOR_STRATEGY"
        assert updated["missing_fields"] == []
        assert updated["packet_version"] == 1

        # The vanished-on-refetch defect: reads must agree with the CAS return.
        refetched = sql_backend.get_trip_for_agency(trip_id, sql_agency_id)
        assert refetched is not None
        assert refetched["packet"] == {"destination": "Tokyo", "budget_max": 8000}
        assert refetched["decision_state"] == "READY_FOR_STRATEGY"
        assert refetched["packet_version"] == 1
    finally:
        sql_backend.delete_trip_for_agency(trip_id, sql_agency_id)
