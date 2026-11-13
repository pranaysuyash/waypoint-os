"""Regression tests for the three PLANNING navigation surfaces & canonical GET /trips extensions.

Covers:
1. SSOT total + statusCounts + offset pagination + server-side search (`q`) in `GET /trips`.
2. `scope="quotes"` prioritizing priced quotes / strategy recommendations over empty leads.
3. `scope="bookings"` prioritizing populated dossiers > pending submissions > active collection tokens
   while keeping encrypted PII blobs (`booking_data`, `pending_booking_data`) stripped from list responses.
4. PostgreSQL SQLTripStore parity & candidate ordering verification (`requires_db`).
"""

from __future__ import annotations

import os
import uuid
from types import SimpleNamespace

import pytest
from starlette.testclient import TestClient

import spine_api.persistence as persistence
from spine_api.server import app

try:
    from spine_api.core.database import DATABASE_URL as _APP_DATABASE_URL
except Exception:  # pragma: no cover
    _APP_DATABASE_URL = None

DATABASE_URL = os.getenv("DATABASE_URL") or _APP_DATABASE_URL
requires_db = pytest.mark.skipif(
    not DATABASE_URL,
    reason="No DATABASE_URL configured; SQL planning-surface test needs Postgres",
)

AGENCY_ID = "agency_planning_reg"
client = TestClient(app)


@pytest.fixture()
def _file_trips_env(monkeypatch, tmp_path):
    """Isolate FileTripStore to a temp dir + bypass auth for fast HTTP contract tests."""
    from spine_api.core.auth import (
        get_current_agency,
        get_current_membership,
        get_current_user,
    )

    monkeypatch.setenv("SPINE_API_DISABLE_AUTH", "1")
    monkeypatch.setattr(persistence, "TRIPS_DIR", tmp_path)
    monkeypatch.setattr(
        persistence.TripStore, "_backend", staticmethod(lambda: persistence.FileTripStore)
    )

    original = dict(app.dependency_overrides)
    app.dependency_overrides[get_current_agency] = lambda: SimpleNamespace(
        id=AGENCY_ID, is_test=False
    )
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        id="op-reg-1", email="operator@example.test"
    )
    app.dependency_overrides[get_current_membership] = lambda: SimpleNamespace(
        agency_id=AGENCY_ID, role="owner"
    )
    try:
        yield tmp_path
    finally:
        app.dependency_overrides = original


def _seed_file_trip(trip_id: str, **fields):
    payload = {
        "id": trip_id,
        "agency_id": AGENCY_ID,
        "destination": "Paris",
        "status": "assigned",
        "state": "blue",
        "party_size": 2,
        "updated_at": "2026-11-10T10:00:00+00:00",
        "created_at": "2026-11-10T09:00:00+00:00",
        **fields,
    }
    persistence.FileTripStore.save_trip(payload, agency_id=AGENCY_ID)
    return payload


def test_get_trips_ssot_total_status_counts_search_and_offset(_file_trips_env):
    """GET /trips returns full statusCounts, filters with q/status, and honors offset/limit."""
    _seed_file_trip("trip_a1", destination="Paris", status="assigned", updated_at="2026-11-10T12:00:00+00:00")
    _seed_file_trip("trip_a2", destination="Kyoto", status="in_progress", updated_at="2026-11-10T11:00:00+00:00")
    _seed_file_trip("trip_a3", destination="Singapore", status="blocked", updated_at="2026-11-10T10:00:00+00:00")
    _seed_file_trip("trip_a4", destination="Rome", status="assigned", updated_at="2026-11-10T09:00:00+00:00")

    resp = client.get("/trips?status=assigned,in_progress,blocked&limit=2&offset=0")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 4
    assert body["limit"] == 2
    assert body["offset"] == 0
    assert len(body["items"]) == 2
    assert body["statusCounts"] == {"assigned": 2, "in_progress": 1, "blocked": 1}

    page2 = client.get("/trips?status=assigned,in_progress,blocked&limit=2&offset=2")
    assert page2.status_code == 200
    assert [t["id"] for t in page2.json()["items"]] == ["trip_a2", "trip_a1"]

    search_resp = client.get("/trips?status=assigned,in_progress,blocked&q=kyoto")
    assert search_resp.status_code == 200
    assert search_resp.json()["total"] == 1
    assert [t["id"] for t in search_resp.json()["items"]] == ["trip_a2"]

    ref_search = client.get("/trips?q=trip_a3")
    assert ref_search.status_code == 200
    assert [t["id"] for t in ref_search.json()["items"]] == ["trip_a3"]


def test_get_trips_scope_quotes_excludes_empty_leads(_file_trips_env):
    """scope=quotes keeps only trips with strategy/quote/budget models and prioritizes recommended_option."""
    _seed_file_trip("trip_empty_lead", destination="Goa", status="assigned")
    _seed_file_trip(
        "trip_budget_only",
        destination="London",
        decision={"budget_breakdown": {"verdict": "realistic", "buckets": []}},
        updated_at="2026-11-10T12:00:00+00:00",
    )
    _seed_file_trip(
        "trip_full_quote",
        destination="Tokyo",
        strategy={"recommended_option": {"name": "Tokyo Autumn Discovery", "cost": 4800, "currency": "USD"}},
        updated_at="2026-11-10T09:00:00+00:00",
    )

    resp = client.get("/trips?scope=quotes")
    assert resp.status_code == 200
    body = resp.json()
    ids = [item["id"] for item in body["items"]]
    assert body["total"] == 2
    assert "trip_empty_lead" not in ids
    assert ids[0] == "trip_full_quote"
    assert ids[1] == "trip_budget_only"


def test_get_trips_scope_bookings_ranks_dossiers_and_strips_pii_blobs(_file_trips_env):
    """scope=bookings prioritizes real populated dossiers while stripping sensitive PII blobs from list payload."""
    _seed_file_trip("trip_plain", destination="Bangkok", status="assigned")
    _seed_file_trip(
        "trip_empty_dossier",
        destination="Dubai",
        booking_data={"travelers": []},
        updated_at="2026-11-10T12:00:00+00:00",
    )
    _seed_file_trip(
        "trip_pending_sub",
        destination="Bali",
        pending_booking_data={"travelers": [{"full_name": "Rohan Verma"}]},
        updated_at="2026-11-10T10:00:00+00:00",
    )
    _seed_file_trip(
        "trip_full_dossier",
        destination="Zurich",
        booking_data={
            "travelers": [{"full_name": "John Doe", "passport_number": "Z12345"}],
            "payment_tracking": {"agreed_amount": 120000, "amount_paid": 50000},
        },
        updated_at="2026-11-10T08:00:00+00:00",
    )

    resp = client.get("/trips?scope=bookings")
    assert resp.status_code == 200
    body = resp.json()
    items = body["items"]
    ids = [item["id"] for item in items]
    assert "trip_plain" not in ids
    assert ids[0] == "trip_full_dossier"
    assert ids[1] == "trip_pending_sub"

    # Generic list payload must never expose decrypted/raw booking_data blobs.
    for item in items:
        assert "booking_data" not in item
        assert "pending_booking_data" not in item


@pytest.fixture()
def sql_planning_agency():
    """Throwaway Postgres agency for end-to-end SQLTripStore ranking & count verification."""
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy.pool import NullPool

    engine = create_async_engine(DATABASE_URL, poolclass=NullPool)
    agency_id = str(uuid.uuid4())

    async def _setup() -> None:
        async with engine.begin() as conn:
            await conn.execute(
                text(
                    "INSERT INTO agencies (id, slug, name, plan, settings, is_test, "
                    "jurisdiction, created_at) "
                    "VALUES (:id, :slug, :name, 'internal', CAST(:settings AS JSONB), "
                    "true, 'other', NOW()) ON CONFLICT (id) DO NOTHING"
                ),
                {
                    "id": agency_id,
                    "slug": f"plan-reg-{agency_id[:8]}",
                    "name": "Planning Regression Agency",
                    "settings": '{"source":"test_planning_surfaces_regressions"}',
                },
            )

    async def _teardown() -> None:
        async with engine.begin() as conn:
            await conn.execute(
                text("DELETE FROM booking_collection_tokens WHERE agency_id = :aid"),
                {"aid": agency_id},
            )
            await conn.execute(text("DELETE FROM trips WHERE agency_id = :aid"), {"aid": agency_id})
            await conn.execute(text("DELETE FROM agencies WHERE id = :aid"), {"aid": agency_id})
        await engine.dispose()

    persistence._run_async_blocking(_setup())
    try:
        yield agency_id
    finally:
        persistence._run_async_blocking(_teardown())


@requires_db
@pytest.mark.asyncio
async def test_sql_trip_store_scopes_status_counts_and_booking_tier_order(
    monkeypatch, sql_planning_agency
):
    """Postgres SQLTripStore ranks full booking dossiers before pending/token trips and excludes PII."""
    monkeypatch.setenv("DATA_PRIVACY_MODE", "beta")
    aid = sql_planning_agency

    await persistence.SQLTripStore.save_trip(
        {
            "id": "sql_plain",
            "agency_id": aid,
            "destination": "Madrid",
            "status": "assigned",
        },
        agency_id=aid,
    )
    await persistence.SQLTripStore.save_trip(
        {
            "id": "sql_quote",
            "agency_id": aid,
            "destination": "Tokyo",
            "status": "in_progress",
            "strategy": {"recommended_option": {"name": "Tokyo Luxury", "cost": 6500}},
        },
        agency_id=aid,
    )
    await persistence.SQLTripStore.save_trip(
        {
            "id": "sql_empty_dossier",
            "agency_id": aid,
            "destination": "Lisbon",
            "status": "assigned",
            "booking_data": {"travelers": []},
        },
        agency_id=aid,
    )
    await persistence.SQLTripStore.save_trip(
        {
            "id": "sql_pending_dossier",
            "agency_id": aid,
            "destination": "Vienna",
            "status": "in_progress",
            "pending_booking_data": {"travelers": [{"full_name": "Pending Guest"}]},
        },
        agency_id=aid,
    )
    await persistence.SQLTripStore.save_trip(
        {
            "id": "sql_stage_booking",
            "agency_id": aid,
            "destination": "Nice",
            "status": "assigned",
            "stage": "booking",
        },
        agency_id=aid,
    )
    await persistence.SQLTripStore.save_trip(
        {
            "id": "sql_full_dossier",
            "agency_id": aid,
            "destination": "Zurich",
            "status": "ready_to_book",
            "extracted": {"facts": {"destination": {"value": "Zurich"}}},
            "booking_data": {
                "travelers": [
                    {
                        "full_name": "John Doe",
                        "passport_number": "Z1234567",
                        "email": "john@example.com",
                        "phone": "+919999999999",
                        "nationality": "IN",
                    },
                    {
                        "full_name": "Jane Doe",
                        "passport_number": "Z7654321",
                        "email": "jane@example.com",
                        "phone": "+919999999998",
                        "nationality": "IN",
                    },
                ],
                "payer": {"full_name": "John Doe", "email": "john@example.com"},
                "special_requirements": "Vegetarian meals and adjacent suites requested.",
                "booking_notes": "Deposit invoice verified with Zurich supplier desk.",
                "payment_tracking": {"agreed_amount": 120000, "amount_paid": 50000},
            },
        },
        agency_id=aid,
    )

    counts = await persistence.SQLTripStore.count_trips_by_status(
        agency_id=aid, status="assigned,in_progress,ready_to_book"
    )
    assert counts == {"assigned": 3, "in_progress": 2, "ready_to_book": 1}

    quote_trips = await persistence.SQLTripStore.list_trips(
        agency_id=aid, scope="quotes", limit=10
    )
    assert [t["id"] for t in quote_trips] == ["sql_quote", "sql_full_dossier"]

    search_trips = await persistence.SQLTripStore.list_trips(
        agency_id=aid, q="zurich", limit=10
    )
    assert [t["id"] for t in search_trips] == ["sql_full_dossier"]

    booking_trips = await persistence.SQLTripStore.list_trips(
        agency_id=aid, scope="bookings", limit=10
    )
    booking_ids = [t["id"] for t in booking_trips]
    assert booking_ids[0] == "sql_full_dossier"
    assert "sql_pending_dossier" in booking_ids
    assert booking_ids.index("sql_pending_dossier") < booking_ids.index("sql_stage_booking")
    assert "sql_empty_dossier" not in booking_ids
    assert "sql_plain" not in booking_ids
    for row in booking_trips:
        assert "booking_data" not in row
        assert "pending_booking_data" not in row


def test_get_trips_scope_documents_and_suppliers(_file_trips_env):
    """scope=documents prioritizes upload-ready stages; scope=suppliers prioritizes actionable strategy/booking stages."""
    _seed_file_trip(
        "trip_intake_only",
        destination="Goa",
        status="assigned",
        stage="intake",
        updated_at="2026-11-10T12:00:00+00:00",
    )
    _seed_file_trip(
        "trip_proposal_ready",
        destination="Kyoto",
        status="assigned",
        stage="proposal",
        strategy={"recommended_option": {"name": "Kyoto Autumn Sanctuary"}},
        updated_at="2026-11-10T10:00:00+00:00",
    )
    _seed_file_trip(
        "trip_booking_ready",
        destination="Zurich",
        status="in_progress",
        stage="booking",
        strategy={"recommended_option": {"name": "Swiss Alpine Express"}},
        updated_at="2026-11-10T11:00:00+00:00",
    )

    docs_resp = client.get("/trips?scope=documents&limit=10")
    assert docs_resp.status_code == 200
    docs_ids = [t["id"] for t in docs_resp.json()["items"]]
    assert docs_ids == ["trip_booking_ready", "trip_proposal_ready"]

    sup_resp = client.get("/trips?scope=suppliers&limit=10")
    assert sup_resp.status_code == 200
    sup_ids = [t["id"] for t in sup_resp.json()["items"]]
    assert sup_ids == ["trip_booking_ready", "trip_proposal_ready"]
