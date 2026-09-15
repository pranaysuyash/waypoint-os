"""FND-0174 / confirmation-extract endpoint contract tests.

The extract endpoint is an honest PREVIEW by default; with ``auto_record``
it is an ADOPTED caller of the canonical SQL confirmation machine — the
durable row (draft → recorded) is created through ``confirmation_service``,
inference types outside ``CONFIRMATION_TYPES`` ("transfer"/"activity")
clamp to ``"other"`` on the durable row while the fine-grained type stays
in the extracted payload, and the response states the reality tier of the
result explicitly (``persistence`` marker). A preview never persists a
blob-only confirmation silently.

Supersedes the previous conditional (``if resp.status_code == 200``) test:
it could pass vacuously without exercising anything (false confidence —
repo test-schema-validation doctrine). The flight/hotel extraction-shape
assertions are preserved, now unconditional.
"""

import os
import uuid

import pytest

os.environ.setdefault("RUNNING_TESTS", "1")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-for-pytest-only-32byt")

from spine_api.persistence import TripStore


# The canonical shared test agency/principal (tests/conftest.py) — the
# session_client token AND the request-scoped RLS context are bound to it,
# so the get_rls_db session can insert into booking_confirmations.
AGENCY = "d1e3b2b6-5509-4c27-b123-4b1e02b0bf5b"


@pytest.fixture(autouse=True)
def extraction_test_env(monkeypatch):
    monkeypatch.setenv("DATA_PRIVACY_MODE", "beta")
    monkeypatch.setenv("SPINE_API_DISABLE_AUTH", "1")
    monkeypatch.setenv("TRIPSTORE_BACKEND", "file")


def _headers() -> dict:
    return {"X-Agency-ID": AGENCY}


def _make_trip() -> str:
    trip_id = f"trip_extract_{uuid.uuid4().hex[:12]}"
    TripStore.save_trip(
        {
            "id": trip_id,
            "agency_id": AGENCY,
            "status": "new",
            "destination": "Cape Town",
        },
        agency_id=AGENCY,
    )
    return trip_id


def _run_coro(coro):
    import asyncio

    return asyncio.run(coro)


def _count_confirmations(trip_id: str) -> int:
    """Count the durable SQL confirmation rows for a trip via a private engine
    (the same per-call engine pattern the conftest principal factory uses).

    booking_confirmations is RLS-protected, so the tenant context is bound
    explicitly (mirrors spine_api.core.rls.rls_session)."""
    from sqlalchemy import func, select, text
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    from spine_api.core.database import DATABASE_URL
    from spine_api.models.tenant import BookingConfirmation

    async def _run() -> int:
        engine = create_async_engine(DATABASE_URL)
        try:
            maker = async_sessionmaker(engine, expire_on_commit=False)
            async with maker() as session:
                await session.execute(
                    text("SELECT set_config('app.current_agency_id', :agency, false)"),
                    {"agency": AGENCY},
                )
                total = (
                    await session.execute(
                        select(func.count())
                        .select_from(BookingConfirmation)
                        .where(BookingConfirmation.trip_id == trip_id)
                    )
                ).scalar()
                return int(total or 0)
        finally:
            await engine.dispose()

    return _run_coro(_run())


_FLIGHT_TEXT = (
    "PNR: 6X9ZPL. Flight Emirates EK-501 Mumbai to Dubai on 15 Nov 2026. "
    "Total USD 1,850."
)


def test_extract_flight_shape_preserved(session_client):
    trip_id = _make_trip()
    resp = session_client.post(
        f"/api/trips/{trip_id}/confirmations/extract",
        json={"raw_text": _FLIGHT_TEXT, "document_name": "emirates_eticket.pdf"},
        headers=_headers(),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["extracted"]["confirmation_type"] == "flight"
    assert data["extracted"]["confirmation_number"] == "6X9ZPL"
    assert data["extracted"]["supplier_name"] == "Emirates"
    assert data["extracted"]["confidence_score"] >= 0.8


def test_extract_hotel_shape_preserved(session_client):
    trip_id = _make_trip()
    resp = session_client.post(
        f"/api/trips/{trip_id}/confirmations/extract",
        json={
            "raw_text": (
                "Confirmation Number: SILO-2026-9942. The Silo Hotel Deluxe "
                "Suite check-in 16 Nov 2026. Total USD 3,400."
            ),
            "document_name": "silo_voucher.pdf",
        },
        headers=_headers(),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["extracted"]["confirmation_type"] == "hotel"
    assert data["extracted"]["confirmation_number"] == "SILO-2026-9942"
    assert data["extracted"]["supplier_name"] == "The Silo Hotel"


def test_extract_preview_only_persists_nothing(session_client):
    """FND-0174: without auto_record the endpoint is an explicit honest
    preview — no durable confirmation row is written anywhere."""
    trip_id = _make_trip()
    resp = session_client.post(
        f"/api/trips/{trip_id}/confirmations/extract",
        json={"raw_text": _FLIGHT_TEXT, "document_name": "emirates_eticket.pdf"},
        headers=_headers(),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["persistence"] == "preview_only"
    assert data["recorded_confirmation"] is None
    assert _count_confirmations(trip_id) == 0


def test_extract_auto_record_creates_recorded_sql_confirmation(session_client):
    """FND-0174 (AT-04 family repair): auto_record is an adopted caller of the
    canonical SQL confirmation machine — the pre-F-31 keyword-signature call
    raised TypeError at runtime (a dead adoption path). The repaired path
    creates the row AND records it (draft → recorded), so the required
    execution event lands with the durable evidence."""
    trip_id = _make_trip()
    resp = session_client.post(
        f"/api/trips/{trip_id}/confirmations/extract",
        json={
            "raw_text": _FLIGHT_TEXT,
            "document_name": "emirates_eticket.pdf",
            "auto_record": True,
        },
        headers=_headers(),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["persistence"] == "sql_confirmation_recorded"

    recorded = data["recorded_confirmation"]
    assert recorded is not None
    assert recorded["confirmation_type"] == "flight"
    assert recorded["confirmation_status"] == "recorded"

    assert _count_confirmations(trip_id) == 1


def test_extract_auto_record_unmapped_type_clamps_to_other(session_client):
    """Inference types outside CONFIRMATION_TYPES ("transfer"/"activity")
    clamp to "other" on the durable row; the fine-grained inference stays in
    the extracted payload — never silently dropped, never a 422 dead end."""
    trip_id = _make_trip()
    resp = session_client.post(
        f"/api/trips/{trip_id}/confirmations/extract",
        json={
            "raw_text": (
                "Booking Ref: TRF442. Transfer chauffeur pickup 15 Nov 2026 "
                "by Cape Executive VIP. Amount USD 220."
            ),
            "document_name": "transfer_voucher.pdf",
            "auto_record": True,
        },
        headers=_headers(),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["extracted"]["confirmation_type"] == "transfer"

    recorded = data["recorded_confirmation"]
    assert recorded is not None
    assert recorded["confirmation_type"] == "other"
    assert recorded["confirmation_status"] == "recorded"
    assert _count_confirmations(trip_id) == 1
