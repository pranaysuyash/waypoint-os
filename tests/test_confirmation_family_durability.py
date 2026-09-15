"""FND-0174 / AT-04: confirmation-family durability map.

The legacy finding was "dual confirmation systems, one unused": a SQL
BookingConfirmation state machine existed while runtime truth lived in the
trip JSON blob. Post F-31/FND-0118 the SQL machine is the durable authority
for the insurance family and the flight-fulfillment family. This suite pins
the post-migration contract per family so no confirmation family can regress
into silently blob-only consequential state:

Family map (FND-0174 resolution):

==================  =========================  =====================================
Family              Durable authority          Blob projection / honest marker
==================  =========================  =====================================
A. Insurance        BookingConfirmation        ``trip["insurance_policy"]
   policy attach    (type=insurance,           ["confirmation_id"]`` (projection
                    F-31, tested in            linkage; replay skips projections).
                    test_insurance_quote_
                    evidence.py)
B. Flight           BookingConfirmation        ``trip["booking_confirmation"]
   fulfillment      (type=flight, AT-04)       ["confirmation_id"]`` (uniform
                    + replay repair            linkage; explicit None when the
                                               durable write degraded) +
                                               ``sql_confirmation`` outcome.
C. Proposal         The trip record ITSELF     ``proposal_acceptance_reality_tier``
   acceptance       (TripStore, PA-02 —        ("real") + ``proposal_acceptance_
   (e-sign/intent)  client authorization,      storage`` ("trip_record_durable").
                    deliberately NOT a
                    BookingConfirmation)
D. Manual supplier  BookingConfirmation        none by design (SQL-native CRUD
   confirmations    (full draft→recorded→      through /confirmations router).
                    verified→voided SM)
==================  =========================  =====================================

Coverage honesty: the SQL-backed tests exercise the live Postgres test
database through the shared additive ``boundary_principal_factory`` tenant
seam and read rows back through the canonical
``confirmation_service.list_confirmations`` read seam (RLS-bound via the
production ``rls_session``); the degraded-path test runs on the file trip
store exactly like the fulfillment lifecycle suite.
"""

import os
import uuid
from contextlib import asynccontextmanager

import pytest

os.environ["RUNNING_TESTS"] = "1"
if not os.environ.get("JWT_SECRET"):
    os.environ["JWT_SECRET"] = "test-jwt-secret-for-pytest-only-32byt"

from spine_api.persistence import TripStore

AGENCY = "agency_fnd0174_family"


@pytest.fixture(autouse=True)
def family_test_env(monkeypatch):
    monkeypatch.setenv("DATA_PRIVACY_MODE", "beta")
    monkeypatch.setenv("TRIPSTORE_BACKEND", "file")
    # Router-level scenario (family D) drives the real app over ASGITransport
    # with an X-Agency-ID header; the explicit "0"-vs-"1" semantics of
    # auth_bypass_enabled are honored (mirrors the wave F30-F40 suite).
    monkeypatch.setenv("SPINE_API_DISABLE_AUTH", "1")


@pytest.fixture()
def sql_tenant(boundary_principal_factory):
    """A real (additive) Postgres tenant so the durable write path succeeds."""
    agency_id = f"{AGENCY}_{uuid.uuid4().hex[:8]}"
    boundary_principal_factory("usr_fnd0174", agency_id)
    return agency_id


def _seed_trip(prefix: str, agency_id: str, cost: float = 4500.0) -> str:
    trip_id = f"trip_fnd0174_{prefix}_{uuid.uuid4().hex[:10]}"
    TripStore.save_trip(
        {
            "id": trip_id,
            "agency_id": agency_id,
            "status": "assigned",
            "destination": "Paris",
            "packet": {
                "destination": "Paris",
                "start_date": "2026-11-15",
                "end_date": "2026-11-22",
                "party_size": 2,
            },
            "strategy": {
                "recommended_option": {
                    "name": "Paris Luxury Escape",
                    "cost": cost,
                    "currency": "USD",
                }
            },
        },
        agency_id=agency_id,
    )
    return trip_id


def _accept(token: str):
    from spine_api.routers.public_proposals import (
        AcceptProposalRequest,
        accept_proposal,
    )

    return accept_proposal(
        token=token,
        req=AcceptProposalRequest(
            signer_name="Sarah Connor",
            signer_email="sarah@fnd0174.test",
            e_signature_consent=True,
        ),
    )


async def _read_flight_rows(agency_id: str, trip_id: str) -> list[dict]:
    """Read the flight confirmation rows for a trip through the canonical
    service read seam (``list_confirmations``) inside the production
    ``rls_session`` tenant binding — the same isolation the durable write
    path uses."""
    from spine_api.services import confirmation_service

    async with _isolated_db() as _maker:
        from spine_api.core.rls import rls_session

        async with rls_session(agency_id) as session:
            summaries = await confirmation_service.list_confirmations(
                session, trip_id, agency_id
            )
    return [
        {
            "id": s.id,
            "type": s.confirmation_type,
            "status": s.confirmation_status,
            "created_by": s.created_by,
        }
        for s in summaries
        if s.confirmation_type == "flight"
    ]


@asynccontextmanager
async def _isolated_db():
    """Bind ``rls_session`` / ``get_db`` to a PRIVATE engine for the duration
    of one test's event loop.

    The process-global asyncpg pool is shared across event loops in the test
    process (session-scoped TestClient portal loop vs pytest-asyncio loops vs
    asyncio.run loops). The pool's checkout-time loop-affinity guard does not
    cover every post-commit refresh path, so tests that REQUIRE the durable
    write to succeed must not depend on global-pool loop hygiene. A private
    engine is created and disposed on the caller's own loop, making this file
    order-independent regardless of which suites ran before it.
    """
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    from spine_api.core import database
    from spine_api.core.database import DATABASE_URL

    engine = create_async_engine(DATABASE_URL)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    original_maker = database.async_session_maker
    database.async_session_maker = maker
    try:
        yield maker
    finally:
        database.async_session_maker = original_maker
        await engine.dispose()


def _run_coro(coro):
    import asyncio

    return asyncio.run(coro)


# ---------------------------------------------------------------------------
# Family B — flight fulfillment
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_flight_family_blob_projection_honestly_reports_degraded_or_linked():
    """No silent blob-only confirmation: after fulfillment the blob must carry
    BOTH the ``sql_confirmation`` outcome AND the explicit ``confirmation_id``
    linkage key — non-null when the durable row landed, an explicit None when
    the durable write degraded."""
    from src.orchestration.booking_fulfillment import BookingFulfillmentEngine
    from spine_api.routers.public_proposals import generate_signed_proposal_token

    trip_id = _seed_trip("degraded", "system")
    token = generate_signed_proposal_token(trip_id=trip_id, agency_id="system")
    _accept(token)

    async with _isolated_db():
        result = await BookingFulfillmentEngine.fulfill_accepted_proposal(
            trip_id=trip_id,
            proposal_token=token,
            holder_id="user:advisor@test",
        )
    assert result.status == "FULFILLED_CONFIRMED"

    confirmation = (TripStore.get_trip(trip_id) or {}).get("booking_confirmation") or {}
    # The linkage key is ALWAYS present — absence would be the old silent
    # blob-only failure mode this finding exists to prevent.
    assert "confirmation_id" in confirmation
    assert isinstance(confirmation.get("sql_confirmation"), dict)
    outcome = confirmation["sql_confirmation"]
    assert outcome.get("recorded") in (True, False)
    if outcome.get("recorded"):
        assert confirmation["confirmation_id"] == outcome.get("confirmation_id")
    else:
        assert confirmation["confirmation_id"] is None
        assert outcome.get("reason"), "degraded durable write must carry an explicit reason"


@pytest.mark.asyncio
async def test_flight_family_records_durable_row_and_blob_links_to_it(sql_tenant):
    """Adopt-side proof: with a real tenant the fulfillment records the SQL
    BookingConfirmation and the blob projection links to that exact row."""
    from src.orchestration.booking_fulfillment import BookingFulfillmentEngine
    from spine_api.routers.public_proposals import generate_signed_proposal_token

    trip_id = _seed_trip("sql", sql_tenant)
    token = generate_signed_proposal_token(trip_id=trip_id, agency_id=sql_tenant)
    _accept(token)

    async with _isolated_db():
        result = await BookingFulfillmentEngine.fulfill_accepted_proposal(
            trip_id=trip_id,
            proposal_token=token,
            holder_id="user:advisor@test",
        )
    assert result.status == "FULFILLED_CONFIRMED"
    assert result.durable_confirmation.get("recorded") is True
    confirmation_id = result.durable_confirmation.get("confirmation_id")
    assert confirmation_id

    confirmation = (TripStore.get_trip(trip_id) or {}).get("booking_confirmation") or {}
    assert confirmation.get("confirmation_id") == confirmation_id

    rows = await _read_flight_rows(sql_tenant, trip_id)
    assert len(rows) == 1
    assert rows[0]["id"] == confirmation_id
    assert rows[0]["type"] == "flight"
    assert rows[0]["status"] == "recorded"
    assert rows[0]["created_by"] == "user:advisor@test"


@pytest.mark.asyncio
async def test_flight_family_replay_repair_converges_on_existing_durable_row(sql_tenant):
    """Part-J #3 repair must converge on the durable truth: when the blob-side
    marker was lost but the SQL row exists, the repair RE-LINKS the existing
    row (never double-records, never leaves the blob unlinked)."""
    from src.orchestration.booking_fulfillment import BookingFulfillmentEngine
    from spine_api.routers.public_proposals import generate_signed_proposal_token

    trip_id = _seed_trip("repair", sql_tenant)
    token = generate_signed_proposal_token(trip_id=trip_id, agency_id=sql_tenant)
    _accept(token)

    async with _isolated_db():
        first = await BookingFulfillmentEngine.fulfill_accepted_proposal(
            trip_id=trip_id,
            proposal_token=token,
            holder_id="user:advisor@test",
        )
    first_confirmation_id = first.durable_confirmation.get("confirmation_id")
    assert first_confirmation_id

    # Simulate the crash: the blob lost its linkage and outcome marker while
    # the durable row survived.
    blob = (TripStore.get_trip(trip_id) or {}).get("booking_confirmation") or {}
    stripped = {k: v for k, v in blob.items() if k != "confirmation_id"}
    stripped["sql_confirmation"] = {
        "recorded": False,
        "reason": "simulated crash lost the marker",
    }
    TripStore.update_trip(trip_id, {"booking_confirmation": stripped})

    async with _isolated_db():
        second = await BookingFulfillmentEngine.fulfill_accepted_proposal(
            trip_id=trip_id,
            proposal_token=token,
            holder_id="user:advisor@test",
        )
    assert second.idempotent_replay is True
    assert second.durable_confirmation.get("recorded") is True
    assert second.durable_confirmation.get("relinked") is True
    assert second.durable_confirmation.get("confirmation_id") == first_confirmation_id

    confirmation = (TripStore.get_trip(trip_id) or {}).get("booking_confirmation") or {}
    assert confirmation.get("confirmation_id") == first_confirmation_id

    # Exactly one durable row: repair converged, it did not double-record.
    rows = await _read_flight_rows(sql_tenant, trip_id)
    assert len(rows) == 1


# ---------------------------------------------------------------------------
# Family C — proposal acceptance (e-sign)
# ---------------------------------------------------------------------------


def test_proposal_acceptance_family_carries_explicit_durability_markers():
    """The acceptance is consequential state (it authorizes the money path), so
    it must never look silently blob-only: it persists on the durable trip
    record WITH explicit reality-tier and storage-authority markers."""
    from spine_api.routers.public_proposals import generate_signed_proposal_token

    trip_id = _seed_trip("accept", "system")
    token = generate_signed_proposal_token(trip_id=trip_id, agency_id="system")
    accepted = _accept(token)
    assert accepted.status == "accepted"

    stored = TripStore.get_trip(trip_id)
    assert stored.get("proposal_accepted_at")
    assert stored.get("proposal_esign_consent") is True
    # FND-0174 explicit honest markers.
    assert stored.get("proposal_acceptance_reality_tier") == "real"
    assert stored.get("proposal_acceptance_storage") == "trip_record_durable"


def test_proposal_intent_writer_carries_the_same_markers():
    """The 1-click intent writer mutates the same acceptance family; its writes
    must carry the identical explicit markers."""
    from spine_api.routers.trust_scorecard import accept_proposal_by_token

    trip_id = _seed_trip("intent", "system")
    token = f"link_tok_{uuid.uuid4().hex[:12]}"
    trip = TripStore.get_trip(trip_id)
    trip["proposal_link_token"] = token
    TripStore.save_trip(trip, agency_id="system")

    async def _scenario():
        async with _isolated_db():
            return await accept_proposal_by_token(token)

    response = _run_coro(_scenario())
    assert response["ok"] is True

    stored = TripStore.get_trip(trip_id)
    assert stored.get("proposal_accepted_at")
    assert stored.get("proposal_acceptance_reality_tier") == "real"
    assert stored.get("proposal_acceptance_storage") == "trip_record_durable"


# ---------------------------------------------------------------------------
# Family D — manual supplier confirmations (SQL-native CRUD)
# ---------------------------------------------------------------------------


def test_manual_confirmation_family_full_state_machine_through_router(
    sql_tenant, boundary_token_factory
):
    """The CRUD router drives the full SQL state machine (create → record →
    verify → void); no blob mirror is written for this family by design.

    Runs the app through ASGITransport on this test's own event loop with a
    private DB engine (see ``_isolated_db``), so the suite never depends on
    the session-scoped TestClient's portal loop or the global asyncpg pool —
    order-independent in any combined run. A real signed JWT for the additive
    tenant principal keeps the RLS ContextVar and the route's agency scope
    consistent (the bare auth bypass would bind RLS to ``default_agency``)."""
    from httpx import ASGITransport, AsyncClient

    from spine_api.server import app

    trip_id = f"trip_fnd0174_manual_{uuid.uuid4().hex[:10]}"
    token = boundary_token_factory("usr_fnd0174", sql_tenant)
    headers = {"Authorization": f"Bearer {token}"}

    async def _scenario():
        async with _isolated_db():
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                created = await client.post(
                    f"/api/trips/{trip_id}/confirmations",
                    json={
                        "confirmation_type": "hotel",
                        "supplier_name": "Hotel Artemide",
                        "confirmation_number": "HTL-FND0174",
                    },
                    headers=headers,
                )
                assert created.status_code == 201  # create is 201 Created
                body = created.json()
                assert body["ok"] is True
                confirmation_id = body["confirmation"]["id"]
                assert body["confirmation"]["confirmation_status"] == "draft"

                recorded = await client.post(
                    f"/api/trips/{trip_id}/confirmations/{confirmation_id}/record",
                    headers=headers,
                )
                assert recorded.status_code == 200
                assert (
                    recorded.json()["confirmation"]["confirmation_status"] == "recorded"
                )

                verified = await client.post(
                    f"/api/trips/{trip_id}/confirmations/{confirmation_id}/verify",
                    headers=headers,
                )
                assert verified.status_code == 200
                assert (
                    verified.json()["confirmation"]["confirmation_status"] == "verified"
                )

                voided = await client.post(
                    f"/api/trips/{trip_id}/confirmations/{confirmation_id}/void",
                    headers=headers,
                )
                assert voided.status_code == 200
                assert voided.json()["confirmation"]["confirmation_status"] == "voided"

    _run_coro(_scenario())

    # Family D writes no blob mirror: the trip record stays untouched.
    assert (TripStore.get_trip(trip_id) or {}).get("booking_confirmation") is None


# ---------------------------------------------------------------------------
# Cross-family guard
# ---------------------------------------------------------------------------


def test_confirmation_type_vocabulary_covers_every_supplier_family():
    """The SQL SM's type vocabulary must stay a superset of the supplier
    confirmation families the runtime can produce (flight via fulfillment,
    insurance via attach, hotel/other via manual CRUD). Adding a new
    blob-only confirmation family without extending this vocabulary is the
    regression FND-0174 exists to prevent."""
    from spine_api.models.tenant import CONFIRMATION_TYPES

    assert set(CONFIRMATION_TYPES) >= {"flight", "hotel", "insurance", "payment", "other"}
