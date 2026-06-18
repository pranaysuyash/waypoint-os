"""Extraction service: OCR/document extraction with encrypted PII storage."""

import logging
import hashlib
import os
import time
from dataclasses import dataclass, field
from typing import Optional, Protocol, Union

from src.extraction.exceptions import ExtractionValidationError
from src.extraction.model_chain import RETRIABLE_ERRORS
from spine_api.services import execution_event_service
from spine_api.services.private_fields import encrypt_blob, decrypt_blob

logger = logging.getLogger(__name__)

VALID_EXTRACTION_FIELDS = frozenset({
    "full_name", "date_of_birth", "passport_number", "passport_expiry",
    "nationality", "visa_type", "visa_number", "visa_expiry",
    "insurance_provider", "insurance_policy_number",
})

_EVAL_DEFAULTS = {
    "prompt_version": "v1",
    "schema_version": "v1",
    "routing_version": "v1",
    "dictionary_version": "v1",
    "normalization_version": "v1",
}

_FAILURE_LAYER_BY_ERROR = {
    "schema_validation_failed": "schema",
    "empty_response": "model",
    "unsupported_mime_type": "input_validation",
    "api_auth_error": "provider",
    "api_timeout": "provider",
    "api_rate_limit": "provider",
    "api_server_error": "provider",
}

_NEXT_FIX_BY_FAILURE_LAYER = {
    "provider": "provider_stack",
    "schema": "schema_contract",
    "model": "prompt_contract",
    "input_validation": "input_preprocessing",
}


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


def _get_eval_metadata(document_type: str) -> dict[str, Optional[str]]:
    prompt_version = os.environ.get("EXTRACTION_PROMPT_VERSION", _EVAL_DEFAULTS["prompt_version"])
    schema_version = os.environ.get("EXTRACTION_SCHEMA_VERSION", _EVAL_DEFAULTS["schema_version"])
    routing_version = os.environ.get("EXTRACTION_ROUTING_VERSION", _EVAL_DEFAULTS["routing_version"])
    dictionary_version = os.environ.get("EXTRACTION_DICTIONARY_VERSION", _EVAL_DEFAULTS["dictionary_version"])
    normalization_version = os.environ.get("EXTRACTION_NORMALIZATION_VERSION", _EVAL_DEFAULTS["normalization_version"])

    prompt_text = os.environ.get("EXTRACTION_PROMPT_TEXT")
    prompt_hash: Optional[str]
    if prompt_text:
        prompt_hash = hashlib.sha256(prompt_text.encode("utf-8")).hexdigest()[:12]
    else:
        prompt_hash = os.environ.get("EXTRACTION_PROMPT_HASH")

    return {
        "prompt_version": prompt_version,
        "prompt_hash": prompt_hash,
        "schema_version": schema_version,
        "routing_version": routing_version,
        "dictionary_version": dictionary_version,
        "normalization_version": normalization_version,
        "document_type": document_type,
    }


def _failure_layer(error_code: str | None) -> str:
    if not error_code:
        return "model"
    return _FAILURE_LAYER_BY_ERROR.get(error_code, "model")


def _next_fix_layer(error_code: str | None) -> str:
    return _NEXT_FIX_BY_FAILURE_LAYER.get(_failure_layer(error_code), "prompt_contract")


def _fallback_trigger_reason(
    error_code: str | None,
    has_more_candidates: bool,
) -> str:
    if error_code in RETRIABLE_ERRORS:
        return "fallback_available" if has_more_candidates else "retriable_exhausted"
    if error_code == "unsupported_mime_type":
        return "input_validation_blocked"
    if error_code == "schema_validation_failed":
        return "schema_validation_retry_not_available"
    if error_code == "api_auth_error":
        return "provider_auth_blocked"
    if error_code in {"api_timeout", "api_rate_limit", "api_server_error"}:
        return "provider_fallback_after_retry"
    return "hard_failure"


def _failure_signature(
    document_type: str,
    error_code: str | None,
    model: str | None,
    attempt_number: int,
    fallback_rank: int | None,
) -> str:
    normalized_model = model or "unknown"
    normalized_fallback_rank = fallback_rank if fallback_rank is not None else 0
    normalized_error = error_code or "unknown"
    return f"{document_type}|{normalized_model}|attempt-{attempt_number}|fb-{normalized_fallback_rank}|{normalized_error}"


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

    primary_model = models_to_try[0][0] if models_to_try else "unknown"
    primary_provider = _resolve_provider_name(primary_model)
    eval_metadata = _get_eval_metadata(document.document_type)
    attempt_failure_reasons: list[dict[str, str]] = []

    await execution_event_service.emit_event_best_effort(
        db, agency_id=agency_id, trip_id=document.trip_id,
        subject_type="document_extraction", subject_id=extraction.id,
        event_type="extraction_run_started", event_category="extraction",
        status_from="failed" if is_retry else None, status_to="running",
        actor_type="system", actor_id=None, source="system_generation",
        event_metadata={**eval_metadata, "provider": primary_provider, "model": primary_model, "run_count": extraction.run_count},
    )

    try:
        for rank, (model_name, model_extractor) in enumerate(models_to_try):
            attempt_number = attempt_base + rank + 1
            is_last_candidate = rank >= len(models_to_try) - 1

            attempt = DocumentExtractionAttempt(
                extraction_id=extraction.id,
                agency_id=agency_id,
                trip_id=document.trip_id,
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
                fallback_reason = _fallback_trigger_reason(attempt.error_code, not is_last_candidate)
                layer = _failure_layer(attempt.error_code)
                next_fix = _next_fix_layer(attempt.error_code)
                signature = _failure_signature(document.document_type, attempt.error_code, attempt.model_name, attempt_number, attempt.fallback_rank)
                attempt_failure_reasons.append({
                    "error_code": attempt.error_code,
                    "fallback_reason": fallback_reason,
                    "failure_layer": layer,
                    "next_fix_layer": next_fix,
                    "failure_signature": signature,
                })

                await execution_event_service.emit_event_best_effort(
                    db, agency_id=agency_id, trip_id=document.trip_id,
                    subject_type="document_extraction_attempt", subject_id=attempt.id,
                    event_type="extraction_attempt_failed", event_category="extraction",
                    status_from=None, status_to="failed",
                    actor_type="system", actor_id=None, source="system_generation",
                    event_metadata={
                        **eval_metadata,
                        "provider": attempt.provider_name,
                        "model": attempt.model_name,
                        "attempt_number": attempt.attempt_number,
                        "fallback_rank": attempt.fallback_rank,
                        "error_code": attempt.error_code,
                        "latency_ms": attempt.latency_ms,
                        "fallback_trigger_reason": fallback_reason,
                        "failure_layer": layer,
                        "next_fix_layer": next_fix,
                        "failure_signature": signature,
                    },
                )

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

            await execution_event_service.emit_event_best_effort(
                db, agency_id=agency_id, trip_id=document.trip_id,
                subject_type="document_extraction_attempt", subject_id=attempt.id,
                event_type="extraction_attempt_completed", event_category="extraction",
                status_from=None, status_to="success",
                actor_type="system", actor_id=None, source="system_generation",
                event_metadata={
                    **eval_metadata,
                    "provider": attempt.provider_name,
                    "model": attempt.model_name,
                    "attempt_number": attempt.attempt_number,
                    "fallback_rank": attempt.fallback_rank,
                    "field_count": attempt.field_count,
                    "latency_ms": attempt.latency_ms,
                    "failure_layer": None,
                    "failure_signature": None,
                    "next_fix_layer": None,
                    "fallback_result": "succeeded_after_fallback" if attempt.fallback_rank > 0 else "no_fallback_needed",
                },
            )

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
        final_reason = attempt_failure_reasons[-1] if attempt_failure_reasons else {}
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

    if success_attempt:
        fallback_result = "no_fallback" if success_attempt.fallback_rank == 0 else "succeeded_after_fallback"
        await execution_event_service.emit_event_best_effort(
            db, agency_id=agency_id, trip_id=document.trip_id,
            subject_type="document_extraction", subject_id=extraction.id,
            event_type="extraction_run_completed", event_category="extraction",
            status_from="running", status_to="pending_review",
            actor_type="system", actor_id=None, source="system_generation",
            event_metadata={
                **eval_metadata,
                "document_type": document.document_type,
                "provider": extraction.provider_name,
                "model": extraction.model_name,
                "attempt_count": extraction.attempt_count,
                "field_count": extraction.field_count,
                "overall_confidence": extraction.overall_confidence,
                "latency_ms": extraction.latency_ms,
                "review_trigger_reason": "manual_review_required",
                "fallback_result": fallback_result,
                "fallback_trigger_reason": final_reason.get("fallback_reason"),
                "next_fix_layer": final_reason.get("next_fix_layer"),
                "failure_signature": final_reason.get("failure_signature"),
                "failure_layer": final_reason.get("failure_layer"),
            },
        )
    else:
        final_reason = attempt_failure_reasons[-1] if attempt_failure_reasons else {}
        await execution_event_service.emit_event_best_effort(
            db, agency_id=agency_id, trip_id=document.trip_id,
            subject_type="document_extraction", subject_id=extraction.id,
            event_type="extraction_run_failed", event_category="extraction",
            status_from="running", status_to="failed",
            actor_type="system", actor_id=None, source="system_generation",
            event_metadata={
                **eval_metadata,
                "document_type": document.document_type,
                "error_code": extraction.error_code,
                "attempt_count": extraction.attempt_count,
                "latency_ms": extraction.latency_ms,
                "fallback_result": "exhausted",
                "fallback_trigger_reason": final_reason.get("fallback_reason"),
                "next_fix_layer": final_reason.get("next_fix_layer"),
                "failure_signature": final_reason.get("failure_signature"),
                "failure_layer": final_reason.get("failure_layer"),
                "review_trigger_reason": "manual_review_required",
            },
        )

    return extraction


async def get_extraction_for_document(db, document_id: str, agency_id: str) -> Optional["DocumentExtraction"]:
    """Get extraction for a document, scoped to agency.

    Eagerly loads the ``document`` relationship (via selectinload) so callers
    can access ``extraction.document.document_type`` after a commit without
    triggering a lazy-load that fails with MissingGreenlet on async sessions.
    """
    from spine_api.models.tenant import DocumentExtraction
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    result = (await db.execute(
        select(DocumentExtraction)
        .options(selectinload(DocumentExtraction.document))
        .where(
            DocumentExtraction.document_id == document_id,
            DocumentExtraction.agency_id == agency_id,
        )
    )).scalar_one_or_none()
    return result


async def apply_extraction(db, document, extraction, fields_to_apply: list[str],
                           traveler_id: str, reviewed_by: str,
                           allow_overwrite: bool = False,
                           create_traveler_if_missing: bool = False,
                           review_trigger_reason: str = "manual_apply",
                           review_outcome: str = "applied") -> dict:
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

    await execution_event_service.emit_event_best_effort(
        db, agency_id=extraction.agency_id, trip_id=extraction.trip_id,
        subject_type="document_extraction", subject_id=extraction.id,
        event_type="extraction_applied", event_category="extraction",
        status_from="pending_review", status_to="applied",
        actor_type="agent", actor_id=reviewed_by, source="agent_action",
        event_metadata={
            "review_trigger_reason": review_trigger_reason,
            "review_outcome": review_outcome,
            "next_fix_layer": None,
            "document_type": document.document_type,
            "fields_applied_count": len(fields_to_apply),
            "allow_overwrite": allow_overwrite,
        },
    )

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

    await execution_event_service.emit_event_best_effort(
        db, agency_id=extraction.agency_id, trip_id=extraction.trip_id,
        subject_type="document_extraction", subject_id=extraction.id,
        event_type="extraction_rejected", event_category="extraction",
        status_from="pending_review", status_to="rejected",
        actor_type="agent", actor_id=reviewed_by, source="agent_action",
        event_metadata={
            "review_trigger_reason": "manual_reject",
            "review_outcome": "rejected",
            "next_fix_layer": "prompt_contract",
            "error_code": extraction.error_code,
            "document_type": getattr(
                getattr(extraction, "document", None), "document_type", None
            ),
        },
    )

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
