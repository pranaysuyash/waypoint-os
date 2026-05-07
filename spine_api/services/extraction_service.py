"""Extraction service: OCR/document extraction with encrypted PII storage."""

import json
import logging
import os
from dataclasses import dataclass, field
from typing import Optional, Protocol

from src.security.encryption import encrypt, decrypt


class ExtractionValidationError(ValueError):
    """Invalid input — should map to 422 in the endpoint."""

logger = logging.getLogger(__name__)

VALID_EXTRACTION_FIELDS = frozenset({
    "full_name", "date_of_birth", "passport_number", "passport_expiry",
    "nationality", "visa_type", "visa_number", "visa_expiry",
    "insurance_provider", "insurance_policy_number",
})


# ---------------------------------------------------------------------------
# Encryption helpers (same blob pattern as SQLTripStore)
# ---------------------------------------------------------------------------

def encrypt_blob(data: dict) -> dict:
    """Encrypt a JSON dict as a single Fernet token."""
    if data is None:
        return None
    serialized = json.dumps(data, default=str)
    token = encrypt(serialized)
    return {"__encrypted_blob": True, "v": 1, "ciphertext": token}


def decrypt_blob(data: dict) -> dict:
    """Decrypt a blob-encrypted JSON dict back to original form."""
    if data is None:
        return None
    if isinstance(data, dict) and data.get("__encrypted_blob"):
        token = data.get("ciphertext", "")
        serialized = decrypt(token)
        return json.loads(serialized)
    return data


# ---------------------------------------------------------------------------
# Extractor protocol and NoopExtractor
# ---------------------------------------------------------------------------

class DocumentExtractor(Protocol):
    async def extract(self, file_data: bytes, mime_type: str, document_type: str) -> "ExtractionResult": ...


@dataclass
class ExtractionResult:
    fields: dict[str, Optional[str]]
    confidence_scores: dict[str, float]
    overall_confidence: float
    confidence_method: str = "model"  # "model" for noop, "heuristic_presence" for vision
    provider_metadata: Optional[dict] = field(default=None)


class NoopExtractor:
    """Dev/test extractor returning mock data with explicit audit sentinels."""

    MOCK_DATA = {
        "passport": {
            "full_name": "DO_NOT_LOG_NAME",
            "passport_number": "DO_NOT_LOG_PASSPORT",
            "passport_expiry": "DO_NOT_LOG_EXPIRY",
            "nationality": "US",
            "date_of_birth": "DO_NOT_LOG_DOB",
        },
        "visa": {
            "visa_type": "Tourist",
            "visa_number": "DO_NOT_LOG_VISA_NUM",
            "visa_expiry": "DO_NOT_LOG_EXPIRY",
            "full_name": "DO_NOT_LOG_NAME",
            "nationality": "US",
        },
        "insurance": {
            "insurance_provider": "DO_NOT_LOG_PROVIDER",
            "insurance_policy_number": "DO_NOT_LOG_POLICY",
            "full_name": "DO_NOT_LOG_NAME",
        },
    }
    DEFAULT_DATA = {"full_name": "DO_NOT_LOG_NAME"}

    async def extract(self, file_data: bytes, mime_type: str, document_type: str) -> ExtractionResult:
        fields = dict(self.MOCK_DATA.get(document_type, self.DEFAULT_DATA))
        confidence_scores = {k: 0.85 for k in fields}
        return ExtractionResult(
            fields=fields,
            confidence_scores=confidence_scores,
            overall_confidence=0.85,
            confidence_method="model",
            provider_metadata=None,
        )


def get_extractor() -> DocumentExtractor:
    """Get the configured extraction provider.

    Unknown provider falls back to noop only when APP_ENV is local/test/development.
    Missing OPENAI_API_KEY fails fast when EXTRACTION_PROVIDER=openai_vision.
    """
    provider = os.environ.get("EXTRACTION_PROVIDER", "noop").lower()
    if provider == "noop":
        return NoopExtractor()
    elif provider == "openai_vision":
        from src.extraction.openai_vision_extractor import OpenAIVisionExtractor
        return OpenAIVisionExtractor()  # raises if OPENAI_API_KEY missing
    else:
        app_env = os.environ.get("APP_ENV", "production").lower()
        if app_env in ("local", "test", "development"):
            logger.warning("Unknown EXTRACTION_PROVIDER '%s' in %s, falling back to noop", provider, app_env)
            return NoopExtractor()
        raise RuntimeError(f"Unknown EXTRACTION_PROVIDER '{provider}'")


# ---------------------------------------------------------------------------
# CRUD functions
# ---------------------------------------------------------------------------

async def run_extraction(db, document, storage, agency_id: str) -> "DocumentExtraction":
    """Run extraction on a document (pending_review or accepted). Creates encrypted record."""
    from spine_api.models.tenant import DocumentExtraction
    from src.extraction.vision_client import ExtractionProviderError, ERROR_CODES

    # Check no existing extraction
    from sqlalchemy import select
    existing = (await db.execute(
        select(DocumentExtraction).where(DocumentExtraction.document_id == document.id)
    )).scalar_one_or_none()
    if existing:
        raise ValueError("Extraction already exists for this document")

    # Read file from storage
    file_data = await storage.get(document.storage_key)

    # Run extractor
    extractor = get_extractor()
    provider_name = "noop_extractor"
    if isinstance(extractor, NoopExtractor):
        provider_name = "noop_extractor"
    else:
        cls_name = extractor.__class__.__name__
        if "OpenAI" in cls_name or "Vision" in cls_name:
            provider_name = "openai_vision"
        else:
            provider_name = cls_name.lower()[:29]

    try:
        result = await extractor.extract(file_data, document.mime_type, document.document_type)
    except ExtractionProviderError as e:
        # Provider failed — create failed row with no PII
        error_code = e.error_code
        error_summary = ERROR_CODES.get(error_code, "Unknown error")
        extraction = DocumentExtraction(
            document_id=document.id,
            trip_id=document.trip_id,
            agency_id=agency_id,
            extracted_fields_encrypted=None,
            fields_present={},
            field_count=0,
            confidence_scores=None,
            overall_confidence=None,
            status="failed",
            extracted_by=provider_name,
            error_code=error_code,
            error_summary=error_summary,
        )
        db.add(extraction)
        await db.commit()
        await db.refresh(extraction)
        return extraction

    # Filter to valid fields only
    filtered_fields = {k: v for k, v in result.fields.items() if k in VALID_EXTRACTION_FIELDS}
    filtered_confidence = {k: v for k, v in result.confidence_scores.items() if k in VALID_EXTRACTION_FIELDS}

    # Encrypt PII
    encrypted = encrypt_blob(filtered_fields)

    # Build plaintext indicators
    fields_present = {k: k in filtered_fields and filtered_fields[k] is not None for k in VALID_EXTRACTION_FIELDS}
    field_count = sum(1 for v in fields_present.values() if v)

    # Provider metadata
    meta = result.provider_metadata or {}

    extraction = DocumentExtraction(
        document_id=document.id,
        trip_id=document.trip_id,
        agency_id=agency_id,
        extracted_fields_encrypted=encrypted,
        fields_present=fields_present,
        field_count=field_count,
        confidence_scores=filtered_confidence,
        overall_confidence=result.overall_confidence,
        status="pending_review",
        extracted_by=provider_name,
        provider_name=provider_name,
        model_name=meta.get("model_name"),
        latency_ms=meta.get("latency_ms"),
        prompt_tokens=meta.get("prompt_tokens"),
        completion_tokens=meta.get("completion_tokens"),
        total_tokens=meta.get("total_tokens"),
        cost_estimate_usd=meta.get("cost_estimate_usd"),
        confidence_method=result.confidence_method,
    )
    db.add(extraction)
    await db.commit()
    await db.refresh(extraction)
    return extraction


async def get_extraction_for_document(db, document_id: str, agency_id: str) -> Optional["DocumentExtraction"]:
    """Get extraction for a document, scoped to agency."""
    from spine_api.models.tenant import DocumentExtraction
    from sqlalchemy import select

    result = (await db.execute(
        select(DocumentExtraction).where(
            DocumentExtraction.document_id == document_id,
            DocumentExtraction.agency_id == agency_id,
        )
    )).scalar_one_or_none()
    return result


async def apply_extraction(db, document, extraction, fields_to_apply: list[str],
                           traveler_id: str, reviewed_by: str,
                           allow_overwrite: bool = False,
                           create_traveler_if_missing: bool = False) -> dict:
    """Apply selected extraction fields to booking_data. Returns {applied, conflicts, extraction}."""
    from spine_api.models.tenant import DocumentExtraction

    if extraction.status != "pending_review":
        raise ValueError(f"Cannot apply extraction with status {extraction.status}")

    if document.status != "accepted":
        raise ValueError("Cannot apply extraction: document must be accepted")

    # Validate fields_to_apply
    if not fields_to_apply:
        raise ExtractionValidationError("fields_to_apply must not be empty")

    invalid_fields = [f for f in fields_to_apply if f not in VALID_EXTRACTION_FIELDS]
    if invalid_fields:
        raise ExtractionValidationError(f"Invalid fields: {invalid_fields}")

    # Decrypt and check fields are present in extraction
    extracted_fields = decrypt_blob(extraction.extracted_fields_encrypted) or {}
    not_present = [f for f in fields_to_apply if f not in extracted_fields or extracted_fields[f] is None]
    if not_present:
        raise ExtractionValidationError(f"Fields not present in extraction: {not_present}")

    # Get booking_data from trip store (decrypted)
    from spine_api.persistence import TripStore
    import asyncio
    booking_data = await asyncio.to_thread(TripStore.get_booking_data, extraction.trip_id)
    if not booking_data:
        booking_data = {"travelers": []}

    travelers = booking_data.get("travelers", [])

    # Find target traveler
    target_idx = None
    for i, t in enumerate(travelers):
        if t.get("traveler_id") == traveler_id:
            target_idx = i
            break

    if target_idx is None:
        if not create_traveler_if_missing:
            raise ValueError(f"Traveler {traveler_id} not found")
        # Require full_name + date_of_birth for new traveler
        has_name = "full_name" in fields_to_apply and extracted_fields.get("full_name")
        has_dob = "date_of_birth" in fields_to_apply and extracted_fields.get("date_of_birth")
        if not (has_name and has_dob):
            raise ExtractionValidationError(
                "New traveler requires full_name and date_of_birth in fields_to_apply"
            )
        travelers.append({"traveler_id": traveler_id})
        target_idx = len(travelers) - 1

    # Check for conflicts
    conflicts = []
    target = travelers[target_idx]
    for field in fields_to_apply:
        extracted_val = extracted_fields.get(field)
        existing_val = target.get(field)
        if existing_val and str(existing_val).strip() and str(existing_val) != str(extracted_val):
            conflicts.append({
                "field_name": field,
                "existing_value": _mask_value(str(existing_val)),
                "extracted_value": _mask_value(str(extracted_val)),
            })

    if conflicts and not allow_overwrite:
        return {"applied": False, "conflicts": conflicts, "extraction": extraction}

    # Apply fields
    for field in fields_to_apply:
        val = extracted_fields.get(field)
        if val is not None:
            target[field] = val
    travelers[target_idx] = target
    booking_data["travelers"] = travelers

    # Save booking_data
    await asyncio.to_thread(TripStore.update_trip, extraction.trip_id, {"booking_data": booking_data})

    # Recompute readiness using same pattern as Phase 4A accept
    updated_trip = await asyncio.to_thread(TripStore.get_trip, extraction.trip_id)
    if updated_trip:
        from intake.readiness import compute_readiness
        from intake.packet_models import CanonicalPacket
        packet = CanonicalPacket(packet_id=extraction.trip_id)
        packet.facts.update((updated_trip.get("extracted") or {}).get("facts", {}))
        readiness = compute_readiness(
            packet,
            validation=updated_trip.get("validation"),
            decision=updated_trip.get("decision"),
            traveler_bundle=updated_trip.get("traveler_bundle"),
            internal_bundle=updated_trip.get("internal_bundle"),
            safety=updated_trip.get("safety"),
            fees=updated_trip.get("fees"),
            booking_data=booking_data,
        )
        validation = dict(updated_trip.get("validation") or {})
        validation["readiness"] = readiness.to_dict()
        await asyncio.to_thread(TripStore.update_trip, extraction.trip_id, {"validation": validation})

    # Update extraction status
    extraction.status = "applied"
    extraction.reviewed_by = reviewed_by
    from datetime import datetime, timezone
    extraction.reviewed_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(extraction)

    return {"applied": True, "conflicts": [], "extraction": extraction}


async def reject_extraction(db, extraction, reviewed_by: str) -> "DocumentExtraction":
    """Reject extraction. Does not modify booking_data."""
    if extraction.status != "pending_review":
        raise ValueError(f"Cannot reject extraction with status {extraction.status}")

    extraction.status = "rejected"
    extraction.reviewed_by = reviewed_by
    from datetime import datetime, timezone
    extraction.reviewed_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(extraction)
    return extraction


def decrypt_extraction_fields(extraction) -> dict:
    """Decrypt and return extracted fields for API response."""
    return decrypt_blob(extraction.extracted_fields_encrypted) if extraction else {}


def _mask_value(val: str, visible_chars: int = 2) -> str:
    """Mask a value for conflict display: 'John Doe' → 'Jo***e'."""
    if len(val) <= visible_chars * 2:
        return "***"
    return val[:visible_chars] + "***" + val[-visible_chars:]
