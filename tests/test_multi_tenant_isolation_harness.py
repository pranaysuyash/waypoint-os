"""
Multi-Tenant Database Isolation & Security Harness.

Exhaustively verifies that distinct agency tenants (agency_alpha vs agency_beta)
cannot access, modify, or leak data across isolated tenant boundaries (A-19/A-20).
"""

import uuid
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from spine_api.core.database import DATABASE_URL
from spine_api.persistence import TripStore


@pytest.fixture(scope="module")
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def seeded_agencies():
    """Seeds two distinct test agencies into the database for isolation testing."""
    agency_a_id = f"agency_a_{uuid.uuid4().hex[:8]}"
    agency_b_id = f"agency_b_{uuid.uuid4().hex[:8]}"
    engine = create_async_engine(DATABASE_URL)

    async with engine.begin() as conn:
        await conn.execute(
            text(
                """
                INSERT INTO agencies (id, slug, name, plan, settings, is_test, jurisdiction, created_at)
                VALUES
                (:id_a, :slug_a, 'Agency Alpha', 'internal', '{}', true, 'other', NOW()),
                (:id_b, :slug_b, 'Agency Beta', 'internal', '{}', true, 'other', NOW())
                ON CONFLICT (id) DO NOTHING
                """
            ),
            {
                "id_a": agency_a_id,
                "slug_a": f"slug-a-{agency_a_id}",
                "id_b": agency_b_id,
                "slug_b": f"slug-b-{agency_b_id}",
            },
        )

    yield agency_a_id, agency_b_id
    await engine.dispose()


@pytest.mark.anyio
async def test_cross_tenant_trip_isolation(seeded_agencies):
    agency_a, agency_b = seeded_agencies
    trip_id_alpha = f"trip_alpha_{uuid.uuid4().hex[:8]}"
    trip_id_beta = f"trip_beta_{uuid.uuid4().hex[:8]}"

    # Tenant Alpha writes Trip Alpha
    trip_alpha = {
        "id": trip_id_alpha,
        "agency_id": agency_a,
        "destination": "St. Moritz",
    }
    TripStore.save_trip(trip_alpha, agency_id=agency_a)

    # Tenant Beta writes Trip Beta
    trip_beta = {
        "id": trip_id_beta,
        "agency_id": agency_b,
        "destination": "Kyoto",
    }
    TripStore.save_trip(trip_beta, agency_id=agency_b)

    # Verification A: Tenant Alpha cannot read Tenant Beta's trip
    retrieved_by_alpha = TripStore.get_trip_for_agency(trip_id_beta, agency_id=agency_a)
    assert retrieved_by_alpha is None

    # Verification B: Tenant Beta cannot read Tenant Alpha's trip
    retrieved_by_beta = TripStore.get_trip_for_agency(trip_id_alpha, agency_id=agency_b)
    assert retrieved_by_beta is None

    # Verification C: Each tenant can read their own trip
    own_alpha = TripStore.get_trip_for_agency(trip_id_alpha, agency_id=agency_a)
    assert own_alpha is not None
    assert own_alpha.get("destination") == "St. Moritz"

    own_beta = TripStore.get_trip_for_agency(trip_id_beta, agency_id=agency_b)
    assert own_beta is not None
    assert own_beta.get("destination") == "Kyoto"


@pytest.mark.anyio
async def test_cross_tenant_list_leak_prevention(seeded_agencies):
    agency_a, agency_b = seeded_agencies

    t1_id = f"t1_{uuid.uuid4().hex[:6]}"
    t2_id = f"t2_{uuid.uuid4().hex[:6]}"
    t3_id = f"t3_{uuid.uuid4().hex[:6]}"

    TripStore.save_trip({"id": t1_id, "agency_id": agency_a, "destination": "Paris"}, agency_id=agency_a)
    TripStore.save_trip({"id": t2_id, "agency_id": agency_a, "destination": "Rome"}, agency_id=agency_a)
    TripStore.save_trip({"id": t3_id, "agency_id": agency_b, "destination": "Tokyo"}, agency_id=agency_b)

    # Agency A list only returns its 2 trips
    trips_a = TripStore.list_trips(agency_id=agency_a)
    assert len(trips_a) == 2
    assert all(t["agency_id"] == agency_a for t in trips_a)

    # Agency B list only returns its 1 trip
    trips_b = TripStore.list_trips(agency_id=agency_b)
    assert len(trips_b) == 1
    assert trips_b[0]["destination"] == "Tokyo"
