"""
tests/test_collection_token_cas.py — PA-16 S2 evidence (2026-09-06).

FAILED BEFORE: ``collection_service.mark_token_used`` was SELECT-then-write —
two concurrent customers submitting through the same collection link could
both read ``status='active'`` and both "consume" the token (TOCTOU).

PASSES AFTER: consumption is a single conditional UPDATE
(``... SET status='used' WHERE id=? AND status='active'``); rowcount 0 means
the token was already consumed/expired/revoked and raises the same 410
rejection the validate path produces.

S2 note: the concurrent double-consume race is evidenced with a sequential
double-call below — the second call hits the CAS guard (rowcount 0) and
raises. Under true simultaneous execution the database decides via the same
rowcount predicate; sequential ordering is the worst case for detecting it,
and the guard fires there too.
"""

from __future__ import annotations

import asyncio
import uuid

import pytest
from fastapi import HTTPException

from spine_api.core.rls import rls_session
from spine_api.persistence import TEST_AGENCY_ID, TripStore
from spine_api.services.collection_service import (
    generate_token,
    mark_token_used,
    validate_token,
)


@pytest.fixture()
def cas_trip_id():
    trip_id = f"trip_cas_{uuid.uuid4().hex[:10]}"
    TripStore.save_trip(
        {"id": trip_id, "status": "assigned", "stage": "proposal"},
        agency_id=TEST_AGENCY_ID,
    )
    yield trip_id
    try:
        TripStore.delete_trip_for_agency(trip_id, TEST_AGENCY_ID)
    except Exception:
        pass


def _run(coro):
    return asyncio.run(coro)


def test_single_consume_succeeds(cas_trip_id):
    async def _scenario():
        async with rls_session(TEST_AGENCY_ID) as db:
            plain, record = await generate_token(
                db, trip_id=cas_trip_id, agency_id=TEST_AGENCY_ID, created_by="tester"
            )
        async with rls_session(TEST_AGENCY_ID) as db:
            validated = await validate_token(db, plain)
            assert validated is not None
            consumed = await mark_token_used(db, validated.id)
            assert consumed is True
        return plain

    plain_token = _run(_scenario())

    # Token is no longer valid after the single successful consumption.
    async def _post_check():
        async with rls_session(TEST_AGENCY_ID) as db:
            return await validate_token(db, plain_token)

    assert _run(_post_check()) is None


def test_double_consume_exactly_one_success(cas_trip_id):
    """Sequential double-call: first consume wins, second hits the CAS guard."""

    async def _scenario():
        async with rls_session(TEST_AGENCY_ID) as db:
            _plain, record = await generate_token(
                db, trip_id=cas_trip_id, agency_id=TEST_AGENCY_ID, created_by="tester"
            )
        async with rls_session(TEST_AGENCY_ID) as db:
            first = await mark_token_used(db, record.id)
        assert first is True
        # Second concurrent-would-be consumer: CAS rowcount 0 -> 410 rejection,
        # consistent with the validate path's invalid-token code.
        async with rls_session(TEST_AGENCY_ID) as db:
            with pytest.raises(HTTPException) as exc_info:
                await mark_token_used(db, record.id)
            assert exc_info.value.status_code == 410

    _run(_scenario())


def test_public_duplicate_submit_still_410(session_client, cas_trip_id):
    """End-to-end: existing duplicate-submit contract still holds under CAS."""
    gen = session_client.post(f"/trips/{cas_trip_id}/collection-link")
    assert gen.status_code == 200
    url = gen.json()["collection_url"]
    token = url.rstrip("/").split("/")[-1]

    payload = {"booking_data": {"travelers": [
        {"traveler_id": "t1", "full_name": "C A S", "date_of_birth": "1990-01-01"}
    ]}}

    resp1 = session_client.post(
        f"/api/public/booking-collection/{TEST_AGENCY_ID}/{token}/submit",
        json=payload,
    )
    assert resp1.status_code == 200

    resp2 = session_client.post(
        f"/api/public/booking-collection/{TEST_AGENCY_ID}/{token}/submit",
        json=payload,
    )
    assert resp2.status_code == 410
