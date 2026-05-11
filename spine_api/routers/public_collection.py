from __future__ import annotations

import hashlib
from typing import List, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, field_validator
from starlette.requests import Request
from starlette.responses import Response
from spine_api.core.rate_limiter import limiter
from spine_api.services.collection_service import validate_token, mark_token_used
from spine_api.services.document_service import (
    sanitize_extension,
    upload_document,
    validate_file_upload,
)
from spine_api.core.database import async_session_maker

try:
    from spine_api import persistence
except (ImportError, ValueError):
    import persistence

router = APIRouter()


class BookingTravelerModel(BaseModel):
    traveler_id: str
    full_name: str
    date_of_birth: str
    passport_number: Optional[str] = None
    passport_expiry: Optional[str] = None
    nationality: Optional[str] = None
    emergency_contact: Optional[str] = None

    @field_validator("full_name", "traveler_id", "date_of_birth")
    @classmethod
    def not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be blank")
        return v


class BookingPayerModel(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None

    @field_validator("name")
    @classmethod
    def not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be blank")
        return v


class BookingDataModel(BaseModel):
    travelers: List[BookingTravelerModel]
    payer: Optional[BookingPayerModel] = None
    special_requirements: Optional[str] = None
    booking_notes: Optional[str] = None

    @field_validator("travelers")
    @classmethod
    def non_empty(cls, v: List[BookingTravelerModel]) -> List[BookingTravelerModel]:
        if not v:
            raise ValueError("must contain at least one traveler")
        return v


class PublicCollectionContext(BaseModel):
    valid: bool
    reason: Optional[str] = None
    trip_summary: Optional[dict] = None
    already_submitted: bool = False
    expires_at: Optional[str] = None


class PublicSubmissionResponse(BaseModel):
    ok: bool
    message: str


class PublicBookingDataSubmitRequest(BaseModel):
    booking_data: BookingDataModel


class CustomerDocumentResponse(BaseModel):
    id: str
    status: str


def _safe_fact_value(slot: object) -> object:
    """Extract only the primitive value from a fact slot that may carry metadata."""
    if isinstance(slot, dict):
        return slot.get("value")
    return getattr(slot, "value", slot)


async def _ts(fn, *args, **kwargs):
    import asyncio
    return await asyncio.to_thread(fn, *args, **kwargs)


@router.get("/api/public/booking-collection/{token}", response_model=PublicCollectionContext)
@limiter.limit("20/minute")
async def get_public_collection_form(request: Request, response: Response, token: str):
    """Customer loads form context. No auth required. Shows safe trip summary only."""
    async with async_session_maker() as db:
        record = await validate_token(db, token)

    if not record:
        return PublicCollectionContext(valid=False, reason="invalid")

    trip = await _ts(persistence.TripStore.get_trip, record.trip_id)
    if not trip:
        return PublicCollectionContext(valid=False, reason="invalid")

    if trip.get("stage", "discovery") not in ("proposal", "booking"):
        return PublicCollectionContext(valid=False, reason="invalid")

    extracted = trip.get("extracted") or {}
    facts = extracted.get("facts", {}) if isinstance(extracted, dict) else {}

    dest_val = _safe_fact_value(facts.get("destination_candidates"))
    date_val = _safe_fact_value(facts.get("date_window"))
    pending = await _ts(persistence.TripStore.get_pending_booking_data, record.trip_id)

    _ = (request, response)

    return PublicCollectionContext(
        valid=True,
        trip_summary={
            "destination": dest_val,
            "date_window": date_val,
            "traveler_count": trip.get("party_composition"),
            "agency_name": "Waypoint Travel",
        },
        already_submitted=pending is not None,
        expires_at=record.expires_at.isoformat(),
    )


@router.post("/api/public/booking-collection/{token}/submit", response_model=PublicSubmissionResponse)
@limiter.limit("5/minute")
async def submit_public_booking_data(request: Request, response: Response, token: str, payload: PublicBookingDataSubmitRequest):
    """Customer submits booking data. No auth. Writes to pending_booking_data."""
    async with async_session_maker() as db:
        record = await validate_token(db, token)
    if not record:
        raise HTTPException(status_code=410, detail="invalid")

    trip = await _ts(persistence.TripStore.get_trip, record.trip_id)
    if not trip or trip.get("stage", "discovery") not in ("proposal", "booking"):
        raise HTTPException(status_code=410, detail="invalid")

    pending = await _ts(persistence.TripStore.get_pending_booking_data, record.trip_id)
    if pending:
        raise HTTPException(status_code=409, detail="already_submitted")

    booking_data = payload.booking_data
    bd_dict = booking_data.model_dump()

    await _ts(persistence.TripStore.update_trip, record.trip_id, {"pending_booking_data": bd_dict})

    async with async_session_maker() as db:
        await mark_token_used(db, record.id)

    persistence.AuditStore.log_event("customer_booking_data_submitted", record.agency_id, {
        "trip_id": record.trip_id,
        "token_id": record.id,
        "traveler_count": len(booking_data.travelers),
        "has_payer": booking_data.payer is not None,
        "has_passport_data": any(t.passport_number for t in booking_data.travelers),
    })

    _ = (request, response)

    return PublicSubmissionResponse(
        ok=True,
        message="Your booking details have been submitted. The travel agent will review them shortly.",
    )


@router.post("/api/public/booking-collection/{token}/documents", response_model=CustomerDocumentResponse)
@limiter.limit("10/minute")
async def upload_public_document(
    request: Request,
    response: Response,
    token: str,
    document_type: str = Form(...),
    file: UploadFile = File(...),
):
    """Customer uploads a document through a collection link token.

    Token is NOT consumed — stays active for booking-data submit.
    """
    async with async_session_maker() as db:
        record = await validate_token(db, token)
    if not record:
        raise HTTPException(status_code=410, detail="invalid")

    trip = await _ts(persistence.TripStore.get_trip, record.trip_id)
    if not trip or trip.get("stage", "discovery") not in ("proposal", "booking"):
        raise HTTPException(status_code=410, detail="invalid")

    file_data, mime_type = await validate_file_upload(file)
    ext = sanitize_extension(file.filename)
    filename_hash = hashlib.sha256((file.filename or "").encode()).hexdigest()

    async with async_session_maker() as db:
        doc = await upload_document(
            db,
            trip_id=record.trip_id,
            agency_id=record.agency_id,
            file_data=file_data,
            mime_type=mime_type,
            filename_hash=filename_hash,
            filename_ext=ext,
            document_type=document_type,
            uploaded_by_type="customer",
            collection_token_id=record.id,
        )

    persistence.AuditStore.log_event("document_uploaded", record.agency_id, {
        "trip_id": record.trip_id,
        "document_id": doc.id,
        "document_type": document_type,
        "uploaded_by_type": "customer",
        "size_bytes": doc.size_bytes,
        "mime_type": mime_type,
        "sha256_present": True,
        "filename_present": True,
        "status": doc.status,
        "scan_status": doc.scan_status,
    })

    _ = (request, response)

    return CustomerDocumentResponse(id=doc.id, status=doc.status)
