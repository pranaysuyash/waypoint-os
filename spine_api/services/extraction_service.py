"""Extraction service: OCR/document extraction with encrypted PII storage."""

import json
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Optional, Protocol, Union

from src.extraction.exceptions import ExtractionValidationError
from src.security.encryption import encrypt, decrypt

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


def get_extractor() -> Union[DocumentExtractor, "ModelChain"]:
    """Build the extraction chain from EXTRACTION_MODEL_CHAIN env var.

    Returns one of: NoopExtractor, OpenAIVisionExtractor, GeminiVisionExtractor, or ModelChain.
    ModelChain has no extract() method — service layer iterates it via _get_model_chain().
    """
    chain_str = os.environ.get("EXTRACTION_MODEL_CHAIN", "").strip()

    if not chain_str:
        # Legacy: fall back to EXTRACTION_PROVIDER or noop
        provider = os.environ.get("EXTRACTION_PROVIDER", "noop").lower()
        if provider == "noop":
            return NoopExtractor()
        elif provider == "openai_vision":
            from src.extraction.openai_vision_extractor import OpenAIVisionExtractor
            return OpenAIVisionExtractor()
        else:
            app_env = os.environ.get("APP_ENV", "production").lower()
            if app_env in ("local", "test", "development"):
                logger.warning("Unknown EXTRACTION_PROVIDER '%s' in %s, falling back to noop", provider, app_env)
                return NoopExtractor()
            raise RuntimeError(f"Unknown EXTRACTION_PROVIDER '{provider}'")

    models = [m.strip() for m in chain_str.split(",") if m.strip()]
    if not models:
        return NoopExtractor()

    extractors: list[tuple[str, DocumentExtractor]] = []
    for model in models:
        provider = _model_to_provider(model)
        if provider == "openai":
            from src.extraction.openai_vision_extractor import OpenAIVisionExtractor
            extractors.append((model, OpenAIVisionExtractor(model=model)))
        elif provider == "gemini":
            from src.extraction.gemini_vision_extractor import GeminiVisionExtractor
            extractors.append((model, GeminiVisionExtractor(model=model)))
        else:
            raise RuntimeError(f"Unknown provider for model '{model}'")

    if len(extractors) == 1:
        return extractors[0][1]

    from src.extraction.model_chain import ModelChain
    return ModelChain(extractors)


def _model_to_provider(model: str) -> str:
    """Determine provider from model name prefix."""
    if model.startswith("gemini"):
        return "gemini"
    if model.startswith("gpt-"):
        return "openai"
    raise ValueError(f"Cannot determine provider for model '{model}'")


def _resolve_provider_name(model_name: str) -> str:
    """Get provider_name for attempt row. Handles noop and unknown safely."""
    if model_name == "noop":
        return "noop_extractor"
    try:
        return _model_to_provider(model_name)
    except ValueError:
        return model_name


def _get_model_chain(extractor) -> list[tuple[str, object]]:
    """Normalize any extractor into a list of (model_name, extractor) pairs."""
    from src.extraction.model_chain import ModelChain
    if isinstance(extractor, ModelChain):
        return extractor.models
    if isinstance(extractor, NoopExtractor):
        return [("noop", extractor)]
    # Single vision extractor — get model from client
    model = getattr(extractor, "_model", None)
    if not isinstance(model, str):
        model = "unknown"
    return [(model, extractor)]


# ---------------------------------------------------------------------------
# CRUD functions
# ---------------------------------------------------------------------------

async def run_extraction(db, document, storage, agency_id: str) -> "DocumentExtraction":
    """Run extraction with full fallback history.

    Invariant: validation failures (PDF page limit) must not leave
    any extraction row or attempt row in the database.
    """
    from spine_api.models.tenant import DocumentExtraction, DocumentExtractionAttempt
    from src.extraction.vision_client import ExtractionProviderError, ERROR_CODES
    from src.extraction.model_chain import RETRIABLE_ERRORS
    from src.extraction.pdf_utils import validate_pdf_pages
    from sqlalchemy import select

    # --- Step 0: Check existing state (read-only) ---
    existing = (await db.execute(
        select(DocumentExtraction).where(DocumentExtraction.document_id == document.id)
    )).scalar_one_or_none()

    if existing and existing.status in ("applied", "rejected", "pending_review"):
        raise ValueError("Cannot retry: extraction already resolved")
    if existing is not None and existing.status == "running":
        raise ValueError("Extraction already in progress")

    is_retry = existing is not None and existing.status == "failed"

    # --- Step 1: Read file and validate BEFORE any DB mutation ---
    file_data = await storage.get(document.storage_key)
    page_count = validate_pdf_pages(file_data, document.mime_type)  # raises ExtractionValidationError → no row created

    # --- Step 2: Find or create extraction aggregate ---
    if is_retry:
        extraction = existing
        extraction.status = "running"
        extraction.run_count = (extraction.run_count or 0) + 1
        await db.commit()
    else:
        extraction = DocumentExtraction(
            document_id=document.id,
            trip_id=document.trip_id,
            agency_id=agency_id,
            status="running",
            attempt_count=0,
            run_count=1,
            extracted_fields_encrypted=None,
            fields_present={},
            field_count=0,
            extracted_by="pending",
            provider_name="pending",
        )
        db.add(extraction)
        await db.commit()
        await db.refresh(extraction)

    run_number = extraction.run_count
    attempt_base = extraction.attempt_count

    # --- Step 3: Run extractor chain with per-call attempt tracking ---
    extractor = get_extractor()
    last_error = None
    success_attempt = None
    models_to_try = _get_model_chain(extractor)

    try:
        for rank, (model_name, model_extractor) in enumerate(models_to_try):
            attempt_number = attempt_base + rank + 1

            attempt = DocumentExtractionAttempt(
                extraction_id=extraction.id,
                run_number=run_number,
                attempt_number=attempt_number,
                fallback_rank=rank,
                provider_name=_resolve_provider_name(model_name),
                model_name=model_name,
                status="failed",  # pessimistic default
            )
            db.add(attempt)
            await db.commit()
            await db.refresh(attempt)

            start = time.monotonic()
            try:
                result = await model_extractor.extract(file_data, document.mime_type, document.document_type)
            except ExtractionProviderError as e:
                attempt.error_code = e.error_code
                attempt.error_summary = ERROR_CODES.get(e.error_code, "Unknown error")
                attempt.latency_ms = int((time.monotonic() - start) * 1000)
                attempt.extracted_fields_encrypted = None  # explicit: no PII on failure
                await db.commit()
                extraction.attempt_count = attempt_number

                if e.error_code not in RETRIABLE_ERRORS:
                    last_error = e
                    break
                last_error = e
                logger.warning("Model %s failed with %s, trying next", model_name, e.error_code)
                continue

            # --- Success path ---
            filtered_fields = {k: v for k, v in result.fields.items() if k in VALID_EXTRACTION_FIELDS}
            encrypted = encrypt_blob(filtered_fields)
            fields_present = {k: k in filtered_fields and filtered_fields[k] is not None for k in VALID_EXTRACTION_FIELDS}
            field_count = sum(1 for v in fields_present.values() if v)
            meta = result.provider_metadata or {}

            attempt.status = "success"
            attempt.extracted_fields_encrypted = encrypted
            attempt.fields_present = fields_present
            attempt.field_count = field_count
            attempt.confidence_scores = _filter_confidence(result.confidence_scores)
            attempt.overall_confidence = result.overall_confidence
            attempt.confidence_method = result.confidence_method
            attempt.latency_ms = meta.get("latency_ms")
            attempt.prompt_tokens = meta.get("prompt_tokens")
            attempt.completion_tokens = meta.get("completion_tokens")
            attempt.total_tokens = meta.get("total_tokens")
            attempt.cost_estimate_usd = meta.get("cost_estimate_usd")
            await db.commit()

            success_attempt = attempt
            extraction.attempt_count = attempt_number
            break

    except Exception:
        # Unexpected exception (not ExtractionProviderError) — try to mark as failed
        try:
            extraction.status = "failed"
            extraction.error_code = "internal_error"
            extraction.error_summary = ERROR_CODES.get("internal_error", "Internal error during extraction")
            await db.commit()
        except Exception:
            pass  # DB may be broken; don't mask original error
        raise

    # --- Step 4: Update extraction aggregate ---
    if success_attempt:
        extraction.status = "pending_review"
        extraction.current_attempt_id = success_attempt.id
        extraction.extracted_fields_encrypted = success_attempt.extracted_fields_encrypted
        extraction.fields_present = success_attempt.fields_present
        extraction.field_count = success_attempt.field_count
        extraction.confidence_scores = success_attempt.confidence_scores
        extraction.overall_confidence = success_attempt.overall_confidence
        extraction.confidence_method = success_attempt.confidence_method
        extraction.error_code = None
        extraction.error_summary = None
        extraction.provider_name = success_attempt.provider_name
        extraction.extracted_by = success_attempt.provider_name
        extraction.model_name = success_attempt.model_name
        extraction.latency_ms = success_attempt.latency_ms
        extraction.page_count = page_count
    else:
        extraction.status = "failed"
        if last_error:
            extraction.error_code = last_error.error_code
            extraction.error_summary = ERROR_CODES.get(last_error.error_code, "Unknown error")

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


def _filter_confidence(confidence_scores: dict) -> dict:
    """Filter confidence scores to valid extraction fields only."""
    return {k: v for k, v in confidence_scores.items() if k in VALID_EXTRACTION_FIELDS}


def _mask_value(val: str, visible_chars: int = 2) -> str:
    """Mask a value for conflict display: 'John Doe' → 'Jo***e'."""
    if len(val) <= visible_chars * 2:
        return "***"
    return val[:visible_chars] + "***" + val[-visible_chars:]
