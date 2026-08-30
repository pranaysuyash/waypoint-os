"""
spine_api/routers/trip_documents.py — Modular router for trip document management, scanning, and extraction.

Extracted from monolith server.py for clean modular architecture (Direction 3).
"""

from __future__ import annotations

import inspect
import logging
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from spine_api.core.auth import get_current_agency
from spine_api.core.rls import get_rls_db
from spine_api.models.tenant import Agency, DocumentExtractionAttempt
from spine_api.persistence import TripStore, AuditStore
from src.intake.config.agency_settings import AgencySettingsStore

logger = logging.getLogger("spine_api.routers.trip_documents")

router = APIRouter(tags=["Trip Documents"])


async def _ts(fn, *args, **kwargs):
    res = fn(*args, **kwargs)
    if inspect.isawaitable(res):
        return await res
    return res


# ---------------------------------------------------------------------------
# Schema Models
# ---------------------------------------------------------------------------

class ReviewDocumentRequest(BaseModel):
    notes_present: bool = False


class DocumentResponse(BaseModel):
    id: str
    trip_id: str
    agency_id: str
    document_type: str
    status: str
    filename_ext: str
    mime_type: str
    byte_size: int
    sha256_checksum: str
    scan_status: str
    filename_present: bool = True
    uploaded_by_type: str = "agent"
    uploaded_by_id: Optional[str] = None
    review_notes_present: bool = False
    uploaded_at: str
    reviewed_at: Optional[str] = None
    reviewed_by: Optional[str] = None
    deleted_at: Optional[str] = None
    deleted_by: Optional[str] = None


class DocumentListResponse(BaseModel):
    trip_id: str
    documents: List[DocumentResponse]


class DownloadUrlResponse(BaseModel):
    url: str
    expires_in: int = 900


class ExtractionFieldView(BaseModel):
    field_name: str
    value: Optional[str] = None
    confidence: float
    present: bool


class ExtractionResponse(BaseModel):
    id: str
    document_id: str
    status: str
    extracted_by: str
    overall_confidence: Optional[float] = None
    field_count: int
    fields: List[ExtractionFieldView]
    created_at: str
    updated_at: str
    reviewed_at: Optional[str] = None
    reviewed_by: Optional[str] = None
    provider_name: Optional[str] = None
    model_name: Optional[str] = None
    latency_ms: Optional[int] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    cost_estimate_usd: Optional[float] = None
    error_code: Optional[str] = None
    error_summary: Optional[str] = None
    confidence_method: Optional[str] = None
    attempt_count: int = 0
    run_count: int = 0
    current_attempt_id: Optional[str] = None
    page_count: Optional[int] = None


class AttemptSummaryResponse(BaseModel):
    attempt_id: str
    run_number: int
    attempt_number: int
    fallback_rank: Optional[int] = None
    provider_name: str
    model_name: Optional[str] = None
    latency_ms: Optional[int] = None
    status: str
    error_code: Optional[str] = None
    created_at: Optional[str] = None


class ApplyExtractionRequest(BaseModel):
    traveler_id: str
    fields_to_apply: List[str]
    allow_overwrite: bool = False
    create_traveler_if_missing: bool = False


class ApplyConflict(BaseModel):
    field_name: str
    existing_value: str
    extracted_value: str


class ApplyExtractionResponse(BaseModel):
    applied: bool
    conflicts: List[ApplyConflict] = Field(default_factory=list)
    extraction: Optional[ExtractionResponse] = None


def _doc_to_response(doc: Any) -> DocumentResponse:
    byte_size = getattr(doc, "size_bytes", None) or getattr(doc, "byte_size", 0)
    sha256 = getattr(doc, "sha256", None) or getattr(doc, "sha256_checksum", "")
    created_at = getattr(doc, "created_at", None) or getattr(doc, "uploaded_at", None)
    reviewed_at = getattr(doc, "reviewed_at", None)
    reviewed_by = getattr(doc, "reviewed_by", None)
    deleted_at = getattr(doc, "deleted_at", None)
    deleted_by = getattr(doc, "deleted_by", None)
    uploaded_by_type = getattr(doc, "uploaded_by_type", None) or "agent"
    uploaded_by_id = getattr(doc, "uploaded_by_id", None)
    return DocumentResponse(
        id=doc.id,
        trip_id=doc.trip_id,
        agency_id=doc.agency_id,
        document_type=doc.document_type,
        status=doc.status,
        filename_ext=doc.filename_ext,
        mime_type=doc.mime_type,
        byte_size=byte_size,
        sha256_checksum=sha256,
        scan_status=doc.scan_status,
        filename_present=True,
        uploaded_by_type=uploaded_by_type,
        uploaded_by_id=uploaded_by_id,
        review_notes_present=getattr(doc, "review_notes_present", False),
        uploaded_at=created_at.isoformat() if created_at else "",
        reviewed_at=reviewed_at.isoformat() if reviewed_at else None,
        reviewed_by=reviewed_by,
        deleted_at=deleted_at.isoformat() if deleted_at else None,
        deleted_by=deleted_by,
    )


def _extraction_to_response(ext: Any) -> ExtractionResponse:
    from spine_api.services.extraction_service import decrypt_extraction_fields, VALID_EXTRACTION_FIELDS

    decrypted = decrypt_extraction_fields(ext) or {}
    confidence = ext.confidence_scores or {}
    fields = []
    for fname in VALID_EXTRACTION_FIELDS:
        if fname in decrypted or fname in confidence:
            fields.append(
                ExtractionFieldView(
                    field_name=fname,
                    value=decrypted.get(fname),
                    confidence=confidence.get(fname, 0.0),
                    present=fname in decrypted and decrypted[fname] is not None,
                )
            )

    return ExtractionResponse(
        id=ext.id,
        document_id=ext.document_id,
        status=ext.status,
        extracted_by=ext.extracted_by,
        overall_confidence=ext.overall_confidence,
        field_count=ext.field_count,
        fields=fields,
        created_at=ext.created_at.isoformat() if ext.created_at else "",
        updated_at=ext.updated_at.isoformat() if ext.updated_at else "",
        reviewed_at=ext.reviewed_at.isoformat() if ext.reviewed_at else None,
        reviewed_by=ext.reviewed_by,
        provider_name=getattr(ext, "provider_name", None),
        model_name=getattr(ext, "model_name", None),
        latency_ms=getattr(ext, "latency_ms", None),
        prompt_tokens=getattr(ext, "prompt_tokens", None),
        completion_tokens=getattr(ext, "completion_tokens", None),
        total_tokens=getattr(ext, "total_tokens", None),
        cost_estimate_usd=getattr(ext, "cost_estimate_usd", None),
        error_code=getattr(ext, "error_code", None),
        error_summary=getattr(ext, "error_summary", None),
        confidence_method=getattr(ext, "confidence_method", None),
        attempt_count=getattr(ext, "attempt_count", 0) or 0,
        run_count=getattr(ext, "run_count", 0) or 0,
        current_attempt_id=getattr(ext, "current_attempt_id", None),
        page_count=getattr(ext, "page_count", None),
    )


# ---------------------------------------------------------------------------
# Document Endpoints
# ---------------------------------------------------------------------------

@router.post("/trips/{trip_id}/documents", response_model=DocumentResponse)
async def upload_trip_document(
    trip_id: str,
    file: UploadFile = File(...),
    document_type: str = Form(...),
    traveler_id: Optional[str] = Form(None),
    agency: Agency = Depends(get_current_agency),
    db: AsyncSession = Depends(get_rls_db),
):
    """Upload a new document for a trip."""
    import hashlib
    from spine_api.services.document_service import (
        upload_document,
        validate_file_upload,
        sanitize_extension,
    )

    trip = await _ts(TripStore.get_trip_for_agency, trip_id, agency.id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    if trip.get("stage", "discovery") not in ("proposal", "booking"):
        raise HTTPException(status_code=403, detail="Upload only allowed at proposal/booking stage")

    filename_ext = sanitize_extension(file.filename)
    file_data, detected_mime = await validate_file_upload(file)
    filename_hash = hashlib.sha256((file.filename or "").encode()).hexdigest()

    doc = await upload_document(
        db,
        trip_id=trip_id,
        agency_id=agency.id,
        file_data=file_data,
        mime_type=detected_mime,
        filename_hash=filename_hash,
        filename_ext=filename_ext,
        document_type=document_type,
        uploaded_by_type="agent",
        uploaded_by_id=agency.id,
        traveler_id=traveler_id,
    )

    AuditStore.log_event("document_uploaded", agency.id, {
        "trip_id": trip_id,
        "document_id": doc.id,
        "document_type": doc.document_type,
        "byte_size": doc.size_bytes,
        "mime_type": doc.mime_type,
    })

    return _doc_to_response(doc)


@router.get("/trips/{trip_id}/documents", response_model=DocumentListResponse)
async def list_trip_documents(
    trip_id: str,
    agency: Agency = Depends(get_current_agency),
    db: AsyncSession = Depends(get_rls_db),
):
    """List all non-deleted documents for a trip."""
    from spine_api.services.document_service import get_documents_for_trip

    trip = await _ts(TripStore.get_trip_for_agency, trip_id, agency.id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    docs = await get_documents_for_trip(db, trip_id, agency.id)
    return DocumentListResponse(
        trip_id=trip_id,
        documents=[_doc_to_response(d) for d in docs],
    )


@router.get("/trips/{trip_id}/documents/{document_id}/download-url", response_model=DownloadUrlResponse)
async def get_document_download_url(
    trip_id: str,
    document_id: str,
    agency: Agency = Depends(get_current_agency),
    db: AsyncSession = Depends(get_rls_db),
):
    """Get a short-lived signed URL for downloading a document."""
    from spine_api.services.document_service import get_document_by_id
    from spine_api.services.document_storage import get_document_storage

    trip = await _ts(TripStore.get_trip_for_agency, trip_id, agency.id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    doc = await get_document_by_id(db, document_id, agency.id)
    if not doc or doc.trip_id != trip_id:
        raise HTTPException(status_code=404, detail="Document not found")

    storage = get_document_storage()
    url = await storage.get_signed_url(document_id, "download")
    return DownloadUrlResponse(url=url, expires_in=900)


@router.post("/trips/{trip_id}/documents/{document_id}/accept", response_model=DocumentResponse)
async def accept_trip_document(
    trip_id: str,
    document_id: str,
    request: Optional[ReviewDocumentRequest] = None,
    agency: Agency = Depends(get_current_agency),
    db: AsyncSession = Depends(get_rls_db),
):
    """Accept a pending document. Only allowed from pending_review status."""
    from spine_api.services.document_service import accept_document

    trip = await _ts(TripStore.get_trip_for_agency, trip_id, agency.id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    if trip.get("stage", "discovery") not in ("proposal", "booking"):
        raise HTTPException(status_code=403, detail="Accept only allowed at proposal/booking stage")

    doc = await accept_document(
        db, document_id, agency.id, reviewed_by=agency.id,
        notes_present=request.notes_present if request else False,
    )

    AuditStore.log_event("document_accepted", agency.id, {
        "trip_id": trip_id,
        "document_id": document_id,
        "document_type": doc.document_type,
        "review_notes_present": doc.review_notes_present,
    })

    return _doc_to_response(doc)


@router.post("/trips/{trip_id}/documents/{document_id}/reject", response_model=DocumentResponse)
async def reject_trip_document(
    trip_id: str,
    document_id: str,
    request: Optional[ReviewDocumentRequest] = None,
    agency: Agency = Depends(get_current_agency),
    db: AsyncSession = Depends(get_rls_db),
):
    """Reject a pending document. Only allowed from pending_review status."""
    from spine_api.services.document_service import reject_document

    trip = await _ts(TripStore.get_trip_for_agency, trip_id, agency.id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    if trip.get("stage", "discovery") not in ("proposal", "booking"):
        raise HTTPException(status_code=403, detail="Reject only allowed at proposal/booking stage")

    doc = await reject_document(
        db, document_id, agency.id, reviewed_by=agency.id,
        notes_present=request.notes_present if request else False,
    )

    AuditStore.log_event("document_rejected", agency.id, {
        "trip_id": trip_id,
        "document_id": document_id,
        "document_type": doc.document_type,
        "review_notes_present": doc.review_notes_present,
    })

    return _doc_to_response(doc)


@router.delete("/trips/{trip_id}/documents/{document_id}")
async def delete_trip_document(
    trip_id: str,
    document_id: str,
    agency: Agency = Depends(get_current_agency),
    db: AsyncSession = Depends(get_rls_db),
):
    """Soft-delete a document. Only allowed from accepted/rejected status."""
    from spine_api.services.document_service import soft_delete_document

    trip = await _ts(TripStore.get_trip_for_agency, trip_id, agency.id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    if trip.get("stage", "discovery") not in ("proposal", "booking"):
        raise HTTPException(status_code=403, detail="Delete only allowed at proposal/booking stage")

    doc = await soft_delete_document(db, document_id, agency.id, deleted_by=agency.id)

    AuditStore.log_event("document_deleted", agency.id, {
        "trip_id": trip_id,
        "document_id": document_id,
        "document_type": doc.document_type,
        "storage_delete_status": doc.storage_delete_status,
    })

    return {"ok": True, "status": "deleted"}


@router.get("/api/internal/documents/{document_id}/download")
async def internal_document_download(
    document_id: str,
    token: str = Query(...),
    expires: str = Query(...),
):
    """Internal signed URL endpoint for document download."""
    from spine_api.services.document_storage import verify_signed_url, get_document_storage
    from spine_api.core.database import async_session_maker
    from spine_api.models.tenant import BookingDocument
    from fastapi.responses import Response as FastAPIResponse
    from spine_api.core.rls import apply_rls

    if not verify_signed_url(document_id, "download", token, expires):
        raise HTTPException(status_code=403, detail="Invalid or expired download URL")

    async with async_session_maker() as db:
        result = await db.execute(
            select(BookingDocument).where(BookingDocument.id == document_id)
        )
        doc = result.scalar_one_or_none()
        if doc:
            await apply_rls(db, doc.agency_id)

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    storage = get_document_storage()
    try:
        data = await storage.get(doc.storage_key)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found on disk")

    return FastAPIResponse(
        content=data,
        media_type=doc.mime_type,
        headers={
            "Content-Disposition": f'attachment; filename="document{doc.filename_ext}"',
        },
    )


# ---------------------------------------------------------------------------
# Extraction Endpoints
# ---------------------------------------------------------------------------

@router.get("/trips/{trip_id}/documents/{document_id}/extraction", response_model=ExtractionResponse)
async def get_document_extraction(
    trip_id: str,
    document_id: str,
    agency: Agency = Depends(get_current_agency),
    db: AsyncSession = Depends(get_rls_db),
):
    """Get the current extraction result for a document."""
    from spine_api.services.extraction_service import get_extraction_for_document

    trip = await _ts(TripStore.get_trip_for_agency, trip_id, agency.id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    extraction = await get_extraction_for_document(db, document_id, agency.id)
    if not extraction:
        raise HTTPException(status_code=404, detail="No extraction found for document")

    return _extraction_to_response(extraction)


@router.post("/trips/{trip_id}/documents/{document_id}/extract", response_model=ExtractionResponse)
async def extract_document(
    trip_id: str,
    document_id: str,
    agency: Agency = Depends(get_current_agency),
    db: AsyncSession = Depends(get_rls_db),
):
    """Run OCR extraction on a document. Allowed for pending_review or accepted documents."""
    from spine_api.services.extraction_service import run_extraction, ExtractionValidationError
    from spine_api.services.document_service import get_document_by_id
    from spine_api.services.document_storage import get_document_storage

    # Gated by enable_document_extraction (AiAgentSettings feature gate)
    _ext_ai = AgencySettingsStore.load(agency.id).ai_agent
    if not getattr(_ext_ai, "enable_document_extraction", True):
        raise HTTPException(status_code=403, detail="Document extraction is disabled by agency settings")

    trip = await _ts(TripStore.get_trip_for_agency, trip_id, agency.id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    if trip.get("stage", "discovery") not in ("proposal", "booking"):
        raise HTTPException(status_code=403, detail="Extraction requires proposal or booking stage")

    doc = await get_document_by_id(db, document_id, agency.id)
    if not doc or doc.trip_id != trip_id:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.status not in ("pending_review", "accepted"):
        raise HTTPException(status_code=409, detail=f"Cannot extract from document with status {doc.status}")

    # MIME prevalidation: reject unsupported MIME before creating any extraction row
    ALLOWED_EXTRACTION_MIME_TYPES = {"image/jpeg", "image/png", "application/pdf"}
    if doc.mime_type not in ALLOWED_EXTRACTION_MIME_TYPES:
        raise HTTPException(
            status_code=422,
            detail={
                "error_code": "unsupported_mime_type",
                "message": f"MIME type '{doc.mime_type}' not supported for extraction",
            },
        )

    storage = get_document_storage()
    try:
        extraction = await run_extraction(db, doc, storage, agency.id)
    except ExtractionValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    # Handle failed extraction
    if extraction.status == "failed":
        AuditStore.log_event("extraction_failed", agency.id, {
            "trip_id": trip_id,
            "document_id": document_id,
            "provider": extraction.provider_name,
            "model": getattr(extraction, "model_name", None),
            "error_code": extraction.error_code,
            "latency_ms": getattr(extraction, "latency_ms", None),
        })
        raise HTTPException(status_code=422, detail={
            "message": "Extraction failed",
            "error_code": extraction.error_code,
            "error_summary": extraction.error_summary,
            "provider": extraction.provider_name,
        })

    AuditStore.log_event("extraction_created", agency.id, {
        "trip_id": trip_id,
        "document_id": document_id,
        "document_type": doc.document_type,
        "field_count": extraction.field_count,
        "overall_confidence": extraction.overall_confidence,
        "fields_present": extraction.fields_present,
        "provider": extraction.provider_name,
        "model": getattr(extraction, "model_name", None),
        "latency_ms": getattr(extraction, "latency_ms", None),
        "confidence_method": getattr(extraction, "confidence_method", None),
    })

    return _extraction_to_response(extraction)


@router.post("/trips/{trip_id}/documents/{document_id}/extraction/retry", response_model=ExtractionResponse)
async def retry_extraction(
    trip_id: str,
    document_id: str,
    agency: Agency = Depends(get_current_agency),
    db: AsyncSession = Depends(get_rls_db),
):
    """Retry a failed extraction. Creates new run with attempt rows."""
    from spine_api.services.extraction_service import run_extraction, ExtractionValidationError
    from spine_api.services.document_service import get_document_by_id
    from spine_api.services.document_storage import get_document_storage

    trip = await _ts(TripStore.get_trip_for_agency, trip_id, agency.id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    if trip.get("stage", "discovery") not in ("proposal", "booking"):
        raise HTTPException(status_code=403, detail="Retry requires proposal or booking stage")

    doc = await get_document_by_id(db, document_id, agency.id)
    if not doc or doc.trip_id != trip_id:
        raise HTTPException(status_code=404, detail="Document not found")

    storage = get_document_storage()
    try:
        extraction = await run_extraction(db, doc, storage, agency.id)
    except ExtractionValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    if extraction.status == "failed":
        raise HTTPException(status_code=422, detail={
            "message": "Extraction retry failed",
            "error_code": extraction.error_code,
            "error_summary": extraction.error_summary,
            "provider": extraction.provider_name,
        })

    return _extraction_to_response(extraction)


@router.get("/trips/{trip_id}/documents/{document_id}/extraction/attempts", response_model=List[AttemptSummaryResponse])
async def list_extraction_attempts(
    trip_id: str,
    document_id: str,
    agency: Agency = Depends(get_current_agency),
    db: AsyncSession = Depends(get_rls_db),
):
    """List all extraction attempts for a document (audit trail). No PII."""
    from spine_api.services.extraction_service import get_extraction_for_document

    trip = await _ts(TripStore.get_trip_for_agency, trip_id, agency.id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    extraction = await get_extraction_for_document(db, document_id, agency.id)
    if not extraction:
        raise HTTPException(status_code=404, detail="No extraction found")

    attempts = (await db.execute(
        select(DocumentExtractionAttempt)
        .where(DocumentExtractionAttempt.extraction_id == extraction.id)
        .order_by(DocumentExtractionAttempt.attempt_number)
    )).scalars().all()

    return [
        AttemptSummaryResponse(
            attempt_id=a.id,
            run_number=a.run_number,
            attempt_number=a.attempt_number,
            fallback_rank=a.fallback_rank,
            provider_name=a.provider_name,
            model_name=a.model_name,
            latency_ms=a.latency_ms,
            status=a.status,
            error_code=a.error_code,
            created_at=a.created_at.isoformat() if a.created_at else None,
        )
        for a in attempts
    ]


@router.post("/trips/{trip_id}/documents/{document_id}/extraction/apply", response_model=ApplyExtractionResponse)
async def apply_extraction(
    trip_id: str,
    document_id: str,
    payload: ApplyExtractionRequest,
    agency: Agency = Depends(get_current_agency),
    db: AsyncSession = Depends(get_rls_db),
):
    """Apply selected extraction fields to booking_data. Requires document accepted."""
    from spine_api.services.extraction_service import (
        get_extraction_for_document, apply_extraction as do_apply,
        ExtractionValidationError,
    )
    from spine_api.services.document_service import get_document_by_id

    trip = await _ts(TripStore.get_trip_for_agency, trip_id, agency.id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    if trip.get("stage", "discovery") not in ("proposal", "booking"):
        raise HTTPException(status_code=403, detail="Apply requires proposal or booking stage")

    doc = await get_document_by_id(db, document_id, agency.id)
    if not doc or doc.trip_id != trip_id:
        raise HTTPException(status_code=404, detail="Document not found")

    if doc.status != "accepted":
        raise HTTPException(status_code=409, detail="Document must be accepted before applying extraction")

    extraction = await get_extraction_for_document(db, document_id, agency.id)
    if not extraction:
        raise HTTPException(status_code=404, detail="No extraction found")

    try:
        result = await do_apply(
            db=db, document=doc, extraction=extraction,
            fields_to_apply=payload.fields_to_apply,
            traveler_id=payload.traveler_id,
            reviewed_by=agency.id,
            allow_overwrite=payload.allow_overwrite,
            create_traveler_if_missing=payload.create_traveler_if_missing,
        )
    except ExtractionValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    applied = result["applied"]
    conflicts = result["conflicts"]
    extraction = result["extraction"]

    if applied:
        AuditStore.log_event("extraction_applied", agency.id, {
            "trip_id": trip_id,
            "document_id": document_id,
            "fields_applied": payload.fields_to_apply,
            "field_count": len(payload.fields_to_apply),
            "min_confidence": min(
                (extraction.confidence_scores or {}).get(f, 0.0) for f in payload.fields_to_apply
            ) if payload.fields_to_apply else 0.0,
            "overall_confidence": extraction.overall_confidence,
        })

    return ApplyExtractionResponse(
        applied=applied,
        conflicts=[ApplyConflict(**c) for c in conflicts],
        extraction=_extraction_to_response(extraction) if extraction else None,
    )


@router.post("/trips/{trip_id}/documents/{document_id}/extraction/reject", response_model=ExtractionResponse)
async def reject_extraction(
    trip_id: str,
    document_id: str,
    agency: Agency = Depends(get_current_agency),
    db: AsyncSession = Depends(get_rls_db),
):
    """Reject extraction results. Does not modify booking_data. Allowed at any stage."""
    from spine_api.services.extraction_service import get_extraction_for_document, reject_extraction as do_reject

    trip = await _ts(TripStore.get_trip_for_agency, trip_id, agency.id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    extraction = await get_extraction_for_document(db, document_id, agency.id)
    if not extraction:
        raise HTTPException(status_code=404, detail="No extraction found")

    try:
        extraction = await do_reject(db, extraction, reviewed_by=agency.id)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    AuditStore.log_event("extraction_rejected", agency.id, {
        "trip_id": trip_id,
        "document_id": document_id,
        "extraction_id": extraction.id,
        "field_count": extraction.field_count,
    })

    return _extraction_to_response(extraction)
