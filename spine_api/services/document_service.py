"""
Document service — upload, list, review, and soft-delete for booking documents.

File validation: magic-byte primary, MIME header secondary, streaming size enforcement.
NoopScanner returns scan_status=skipped; documents go directly to pending_review.
"""

import hashlib
import logging
import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Protocol, runtime_checkable

from fastapi import HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from spine_api.models.tenant import BookingDocument
from spine_api.services.document_storage import DocumentStorageBackend, get_document_storage

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VALID_DOCUMENT_TYPES = frozenset({
    "passport", "visa", "insurance",
    "flight_ticket", "hotel_confirmation", "other",
})

ALLOWED_MIME_TYPES = frozenset({"application/pdf", "image/jpeg", "image/png"})

ALLOWED_EXTENSIONS = frozenset({".pdf", ".jpg", ".jpeg", ".png"})

MAX_FILE_SIZE_BYTES = int(os.getenv("DOCUMENT_MAX_FILE_SIZE_MB", "10")) * 1024 * 1024

# Magic byte signatures — primary file validation
MAGIC_BYTES = {
    b"%PDF": "application/pdf",
    b"\xff\xd8\xff": "image/jpeg",
    b"\x89PNG": "image/png",
}

# ---------------------------------------------------------------------------
# Scanner abstraction
# ---------------------------------------------------------------------------


@dataclass
class ScanResult:
    status: str  # skipped | clean | suspicious | failed
    details: Optional[str] = None


@runtime_checkable
class DocumentScanner(Protocol):
    async def scan(self, file_path: str) -> ScanResult: ...


class NoopScanner:
    """Dev/test scanner — skips scan, returns status=skipped."""

    async def scan(self, file_path: str) -> ScanResult:
        return ScanResult(status="skipped")


def get_scanner() -> DocumentScanner:
    return NoopScanner()


# ---------------------------------------------------------------------------
# File validation helpers
# ---------------------------------------------------------------------------


def _detect_mime_by_magic(data: bytes) -> str:
    """Detect MIME type from file magic bytes."""
    for magic, mime in MAGIC_BYTES.items():
        if data[:len(magic)] == magic:
            return mime
    return "application/octet-stream"


def sanitize_extension(filename: Optional[str]) -> str:
    """Extract and validate file extension. Returns lowercase with dot."""
    if not filename:
        raise HTTPException(status_code=400, detail="Filename required")
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=415, detail=f"File type {ext} not allowed")
    return ext


async def validate_file_upload(file: UploadFile) -> tuple[bytes, str]:
    """Stream-read file with per-chunk size enforcement and magic-byte validation.

    Returns (data, detected_mime).
    """
    ext = sanitize_extension(file.filename)

    # Stream read with per-chunk size check
    chunks = []
    total = 0
    while True:
        chunk = await file.read(65536)  # 64KB chunks
        if not chunk:
            break
        total += len(chunk)
        if total > MAX_FILE_SIZE_BYTES:
            raise HTTPException(status_code=413, detail="File exceeds maximum size")
        chunks.append(chunk)
    data = b"".join(chunks)

    if len(data) == 0:
        raise HTTPException(status_code=400, detail="Empty file")

    # Magic-byte validation (primary)
    detected_mime = _detect_mime_by_magic(data)
    if detected_mime not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=415, detail="File content type not allowed")

    # MIME header validation (secondary)
    if file.content_type and file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=415, detail="Declared content type not allowed")

    return data, detected_mime


def generate_storage_key(agency_id: str, trip_id: str, ext: str) -> str:
    """Generate storage key: {agency_id}/{trip_id}/{uuid}.{ext}."""
    return f"{agency_id}/{trip_id}/{uuid.uuid4().hex}{ext}"


# ---------------------------------------------------------------------------
# CRUD operations
# ---------------------------------------------------------------------------


async def upload_document(
    db: AsyncSession,
    *,
    trip_id: str,
    agency_id: str,
    file_data: bytes,
    mime_type: str,
    filename_hash: str,
    filename_ext: str,
    document_type: str,
    uploaded_by_type: str,
    uploaded_by_id: Optional[str] = None,
    traveler_id: Optional[str] = None,
    collection_token_id: Optional[str] = None,
) -> BookingDocument:
    """Create a document record and store file."""
    if document_type not in VALID_DOCUMENT_TYPES:
        raise HTTPException(status_code=422, detail=f"Invalid document type: {document_type}")

    sha256 = hashlib.sha256(file_data).hexdigest()
    storage_key = generate_storage_key(agency_id, trip_id, filename_ext)

    # Store file
    storage = get_document_storage()
    await storage.put(storage_key, file_data)

    # Run scanner
    scanner = get_scanner()
    scan_result = await scanner.scan(storage_key)

    doc = BookingDocument(
        id=str(uuid.uuid4()),
        trip_id=trip_id,
        agency_id=agency_id,
        traveler_id=traveler_id,
        uploaded_by_type=uploaded_by_type,
        uploaded_by_id=uploaded_by_id,
        collection_token_id=collection_token_id,
        filename_hash=filename_hash,
        filename_ext=filename_ext,
        storage_key=storage_key,
        mime_type=mime_type,
        size_bytes=len(file_data),
        sha256=sha256,
        document_type=document_type,
        status="pending_review",
        scan_status=scan_result.status,
    )

    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    logger.info(
        "Document uploaded: id=%s trip=%s type=%s uploaded_by=%s scan=%s",
        doc.id, trip_id, document_type, uploaded_by_type, scan_result.status,
    )
    return doc


async def get_documents_for_trip(
    db: AsyncSession,
    trip_id: str,
    agency_id: str,
) -> list[BookingDocument]:
    """List all non-deleted documents for a trip."""
    result = await db.execute(
        select(BookingDocument).where(
            BookingDocument.trip_id == trip_id,
            BookingDocument.agency_id == agency_id,
            BookingDocument.status != "deleted",
        ).order_by(BookingDocument.created_at.desc())
    )
    return list(result.scalars().all())


async def get_document_by_id(
    db: AsyncSession,
    document_id: str,
    agency_id: str,
) -> Optional[BookingDocument]:
    """Get a single document by ID, scoped to agency."""
    result = await db.execute(
        select(BookingDocument).where(
            BookingDocument.id == document_id,
            BookingDocument.agency_id == agency_id,
        )
    )
    return result.scalar_one_or_none()


async def accept_document(
    db: AsyncSession,
    document_id: str,
    agency_id: str,
    reviewed_by: str,
    notes_present: bool = False,
) -> BookingDocument:
    """Accept a document — only from pending_review status."""
    doc = await get_document_by_id(db, document_id, agency_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.status != "pending_review":
        raise HTTPException(status_code=409, detail=f"Cannot accept document in status: {doc.status}")

    doc.status = "accepted"
    doc.reviewed_by = reviewed_by
    doc.reviewed_at = datetime.now(timezone.utc)
    doc.review_notes_present = notes_present
    await db.commit()
    await db.refresh(doc)

    logger.info("Document accepted: id=%s reviewed_by=%s", document_id, reviewed_by)
    return doc


async def reject_document(
    db: AsyncSession,
    document_id: str,
    agency_id: str,
    reviewed_by: str,
    notes_present: bool = False,
) -> BookingDocument:
    """Reject a document — only from pending_review status."""
    doc = await get_document_by_id(db, document_id, agency_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.status != "pending_review":
        raise HTTPException(status_code=409, detail=f"Cannot reject document in status: {doc.status}")

    doc.status = "rejected"
    doc.reviewed_by = reviewed_by
    doc.reviewed_at = datetime.now(timezone.utc)
    doc.review_notes_present = notes_present
    await db.commit()
    await db.refresh(doc)

    logger.info("Document rejected: id=%s reviewed_by=%s", document_id, reviewed_by)
    return doc


async def soft_delete_document(
    db: AsyncSession,
    document_id: str,
    agency_id: str,
    deleted_by: str,
) -> BookingDocument:
    """Soft-delete a document — only from accepted or rejected status.

    Sets status=deleted but does NOT remove file from storage.
    """
    doc = await get_document_by_id(db, document_id, agency_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.status not in ("accepted", "rejected"):
        raise HTTPException(status_code=409, detail=f"Cannot delete document in status: {doc.status}")

    doc.status = "deleted"
    doc.deleted_at = datetime.now(timezone.utc)
    doc.deleted_by = deleted_by
    doc.storage_delete_status = "retained"
    await db.commit()
    await db.refresh(doc)

    logger.info("Document soft-deleted: id=%s deleted_by=%s", document_id, deleted_by)
    return doc
