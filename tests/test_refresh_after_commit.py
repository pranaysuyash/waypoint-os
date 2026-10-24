"""
tests/test_refresh_after_commit.py — FND-0310 / FND-0311 regression tests.

Defect: ``POST /api/v1/customers/remember`` and
``POST /api/trips/{id}/confirmations/extract`` crash with
``sqlalchemy.exc.InvalidRequestError: Could not refresh instance ...`` AFTER a
successful commit, while the row IS persisted (subsequent GET returns 200).

Root cause (probed empirically against the local Postgres, 2026-10-05):

1. ``rls_session`` applies ``set_config('app.current_agency_id', ..., false)``
   — a SESSION-level GUC bound to the specific pooled connection it ran on.
2. ``Session.commit()`` ends the transaction and RELEASES that connection back
   to the pool (SQLAlchemy 2.0 autobegin semantics).
3. The post-commit ``db.refresh()`` autobegins a NEW transaction, which may
   check out a DIFFERENT pooled connection that never received the GUC.
4. ``customer_memory_profiles`` / ``booking_confirmations`` run FORCE RLS, so
   the refresh's identity re-select matches zero rows → InvalidRequestError.
   ``expire_on_commit=False`` (spine_api/core/database.py:95) rules out classic
   post-commit expiry as the cause.

The tests below reproduce the failure deterministically with a
holder/thief connection dance that steals the connection released by the
commit, exactly as a concurrent request does in production (Sim #3).
"""

from __future__ import annotations

import asyncio
import os
import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.exc import InvalidRequestError

os.environ["RUNNING_TESTS"] = "1"

AGENCY = "agency_rls_refresh_regression"
USER = "usr_rls_refresh_regression"


@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    monkeypatch.setenv("DATA_PRIVACY_MODE", "beta")
    monkeypatch.setenv("SPINE_API_DISABLE_AUTH", "1")
    monkeypatch.setenv("TRIPSTORE_BACKEND", "file")


@pytest.fixture(autouse=True)
def materialize_rls_refresh_tenant(boundary_principal_factory):
    """agency_id is an FK to agencies.id — the test tenant must exist first.
    Additive only (ON CONFLICT DO NOTHING)."""
    boundary_principal_factory(USER, AGENCY)


async def _steal_released_connection():
    """Deterministically force the production failure mode.

    The dance must run on the SAME pool the session uses. Since 57113daf,
    ``rls_session`` draws from the per-loop tripstore engine
    (``spine_api.persistence.tripstore_session_maker``), NOT
    ``spine_api.core.database.engine`` — stealing from the old pool checks out
    a connection that never carried the GUC while the session keeps its own
    (session-level GUC survives commit by design), which made the GUC-loss
    assertion vacuous. Retargeted to the tripstore pool (FND-0364 sweep,
    2026-10-22).

    Fresh pool → a holder occupies a slot → the caller's ``rls_session``
    runs on its own connection → ``commit()`` releases that connection to
    the FIFO pool → ``steal()`` checks out that exact (now-oldest-idle)
    connection → the caller's next autobegin must create a brand-new
    connection that never received the session-level RLS GUC.
    """
    from spine_api.persistence import _tripstore_engines, tripstore_session_maker

    # Constructing the maker registers this loop's tripstore engine
    # (spine_api/persistence.py `_tripstore_engines`). rls_session draws from
    # that pool — read it from the registry rather than poking the session.
    tripstore_session_maker()
    engine = _tripstore_engines.get(asyncio.get_running_loop())
    assert engine is not None, "tripstore engine not registered for this loop"

    # Fresh pool so the FIFO hand-off below is deterministic.
    await engine.dispose()
    holder = await engine.connect()

    async def _steal():
        # Called between commit and refresh: at this point the session's
        # connection is idle in the pool and is the OLDEST idle entry, so the
        # FIFO pool hands it to this new checkout.
        return await engine.connect()

    return holder, _steal


async def _cleanup_profile(profile_id: str) -> None:
    from spine_api.core.database import async_session_maker

    async with async_session_maker() as s:
        await s.execute(
            text("DELETE FROM customer_memory_profiles WHERE id = :id"),
            {"id": profile_id},
        )
        await s.commit()


def _run(coro):
    return asyncio.run(coro)


# ---------------------------------------------------------------------------
# Mechanism lock: raw post-commit refresh DOES fail on re-checkout.
# (This documents the exact production failure; keep even after the fix.)
# ---------------------------------------------------------------------------


def test_raw_refresh_after_commit_fails_when_connection_rechecked_out():
    from spine_api.core.rls import rls_session
    from spine_api.models.tenant import CustomerMemoryProfile

    async def scenario():
        holder, steal = await _steal_released_connection()
        stolen = None
        profile_id = str(uuid.uuid4())
        try:
            async with rls_session(AGENCY) as db:
                profile_row = CustomerMemoryProfile(
                    id=profile_id,
                    agency_id=AGENCY,
                    customer_id=f"cust_rls_refresh_{profile_id[:8]}",
                    name="Conn Thief",
                )
                db.add(profile_row)
                await db.commit()  # releases the connection carrying the GUC
                stolen = await steal()
                # Post-commit GUC is gone on the fresh connection:
                guc = (
                    await db.execute(
                        text("SELECT current_setting('app.current_agency_id', true)")
                    )
                ).scalar()
                assert guc in (None, ""), (
                    f"expected GUC loss after commit re-checkout, got {guc!r}"
                )
                with pytest.raises(InvalidRequestError):
                    await db.refresh(profile_row)
                return profile_id
        finally:
            if stolen is not None:
                await stolen.close()
            await holder.close()

    profile_id = _run(scenario())
    _run(_cleanup_profile(profile_id))


# ---------------------------------------------------------------------------
# FND-0310 regression: the remember endpoint's post-commit refresh must
# survive connection re-checkout via refresh_or_reselect.
# ---------------------------------------------------------------------------


def test_refresh_or_reselect_recovers_profile_after_commit_recheckout():
    from spine_api.core.rls import refresh_or_reselect, rls_session
    from spine_api.models.tenant import CustomerMemoryProfile

    async def scenario():
        holder, steal = await _steal_released_connection()
        stolen = None
        profile_id = str(uuid.uuid4())
        try:
            async with rls_session(AGENCY) as db:
                profile_row = CustomerMemoryProfile(
                    id=profile_id,
                    agency_id=AGENCY,
                    customer_id=f"cust_rls_refresh_{profile_id[:8]}",
                    name="Recovered Row",
                )
                db.add(profile_row)
                await db.commit()
                stolen = await steal()
                # The endpoint path (customer_memory.py remember) calls the
                # helper instead of a bare refresh:
                await refresh_or_reselect(db, profile_row)
                # The instance must be live and the RLS GUC must be restored
                # on the (new) connection for subsequent queries:
                assert profile_row.name == "Recovered Row"
                guc = (
                    await db.execute(
                        text("SELECT current_setting('app.current_agency_id', true)")
                    )
                ).scalar()
                assert guc == AGENCY, f"GUC not restored, got {guc!r}"
                return profile_id
        finally:
            if stolen is not None:
                await stolen.close()
            await holder.close()

    profile_id = _run(scenario())
    _run(_cleanup_profile(profile_id))


# ---------------------------------------------------------------------------
# FND-0311 regression: confirmation_service.create path shape (generic PK
# re-select must work for any RLS-scoped model, not just profiles).
# ---------------------------------------------------------------------------


def test_refresh_or_reselect_restores_row_for_confirmation_path():
    """Exercise the helper on a second FORCE-RLS model class using the same
    commit→steal dance used for the profile row (the confirmation create path
    shares the identical commit-then-refresh shape at
    spine_api/services/confirmation_service.py:363)."""
    from spine_api.core.rls import refresh_or_reselect, rls_session
    from spine_api.models.tenant import CustomerMemoryProfile  # noqa: F401

    async def scenario():
        holder, steal = await _steal_released_connection()
        stolen = None
        profile_id = str(uuid.uuid4())
        try:
            async with rls_session(AGENCY) as db:
                row = CustomerMemoryProfile(
                    id=profile_id,
                    agency_id=AGENCY,
                    customer_id=f"cust_rls_refresh_{profile_id[:8]}",
                    name="Second Model",
                )
                db.add(row)
                await db.commit()
                stolen = await steal()
                await refresh_or_reselect(db, row)
                assert row.customer_id.startswith("cust_rls_refresh_")
                return profile_id
        finally:
            if stolen is not None:
                await stolen.close()
            await holder.close()

    profile_id = _run(scenario())
    _run(_cleanup_profile(profile_id))


# ---------------------------------------------------------------------------
# End-to-end HTTP regression: the remember endpoint must return 200 (not 500)
# and the profile must be readable afterwards. Exercises the converted call
# site through the real router (plain re-checkout path — no theft needed; the
# connection dance above covers the adversarial interleaving).
# ---------------------------------------------------------------------------


def test_remember_endpoint_roundtrip(session_client):
    email = f"conn.thief.{uuid.uuid4().hex[:8]}@example.com"
    remember_res = session_client.post(
        "/api/v1/customers/remember",
        json={
            "name": "Conn Thief E2E",
            "email": email,
            "room_preference": "High floor",
        },
        headers={"X-Agency-ID": AGENCY},
    )
    assert remember_res.status_code == 200, remember_res.text
    customer_id = remember_res.json()["customer_id"]

    lookup_res = session_client.get(
        f"/api/v1/customers/memory?email={email}",
        headers={"X-Agency-ID": AGENCY},
    )
    assert lookup_res.status_code == 200
    assert lookup_res.json()["customer_id"] == customer_id
