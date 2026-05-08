# Phase 4E: Multi-Model Fallback, PDF Extraction, and Append-Only Attempts

## Context

Phase 4D (closed 2026-05-07) delivered a single-provider vision extraction pipeline with OpenAI. Phase 4E extends it with three capabilities:

1. **Model fallback chain** — Primary model fails → try next → try next. Best quality/cost first. Every provider call preserved as its own attempt row.
2. **PDF extraction** — Provider-native PDF support (no image conversion). Page-count limit policy.
3. **Append-only attempts** — Retry failed extractions. Full history preserved per provider call.

Phase 4C/4D boundaries preserved: encrypted PII, static error codes, schema validation, audit trail, MIME prevalidation.

---

## Model Pricing (best-effort static pricing snapshot, May 2026)

**Not accounting truth.** Prices are sourced from provider pricing pages at time of writing and may change. `PRICING_TABLE_VERSION` and `PRICING_TABLE_SOURCE` track provenance.

**OpenAI:** GPT-4.1 family deprecated Feb 2026 (ChatGPT) with API retirement timeline. Current production models are GPT-5.4 family.

**Google:** Gemini 2.0 Flash deprecating June 1, 2026. Gemini 2.5 and 3.x are current.

| Model | Input/1M | Output/1M | OCR Quality | Provider | Status |
|:------|:---------|:----------|:------------|:---------|:-------|
| gemini-2.5-flash | $0.30 | $2.50 | Best | Google | Stable |
| gemini-2.5-flash-lite | $0.10 | $0.40 | Good | Google | Stable |
| gemini-3-flash-preview | $0.50 | $3.00 | Best | Google | Preview — not in default chain |
| gpt-5.4-nano | $0.20 | $1.25 | Adequate | OpenAI | Stable |
| gpt-5.4-mini | $0.75 | $4.50 | Good | OpenAI | Stable |

**Fallback chain (default):** `gemini-2.5-flash` → `gpt-5.4-nano` → `gemini-2.5-flash-lite`

---

## Architecture

```
EXTRACTION_MODEL_CHAIN env var (comma-separated model IDs)
        │
        ▼
   get_extractor()
   ┌─────────────────────────────────────────┐
   │ Returns one of:                         │
   │   ModelChain (multi-model container)    │
   │   Single OpenAIVisionExtractor          │
   │   Single GeminiVisionExtractor          │
   │   NoopExtractor (dev/test)              │
   │                                         │
   │ ModelChain holds ordered pairs:         │
   │   [(gemini-2.5-flash, GeminiExtractor), │
   │    (gpt-5.4-nano, OpenAIExtractor),     │
   │    (gemini-2.5-flash-lite, GeminiExt)]  │
   │ No extract() method — service iterates. │
   └─────────────────────────────────────────┘
        │
        ▼
   run_extraction() — OWNS fallback loop
   ┌──────────────────────────────────┐
   │ 1. Create extraction (running)   │
   │ 2. _get_model_chain() → list     │
   │ 3. For each model in chain:      │
   │    a. Create attempt row         │
   │    b. Emit provider-call audit   │
   │    c. Call model extractor       │
   │    d. Update attempt row         │
   │    e. If retriable → continue    │
   │    f. If success → break         │
   │    g. If non-retriable → break   │
   │ 4. Update extraction aggregate   │
   │ 5. Return extraction             │
   └──────────────────────────────────┘
```

Separate from `BaseLLMClient` — extraction is document→structured-data, not text→decision.

---

## Part 1: Provider Abstraction

### 1a. VisionClient Protocol Update

**File:** `src/extraction/vision_client.py`

The existing `VisionClient` protocol method `extract_from_image` stays unchanged — each client handles its own MIME type dispatch (image vs PDF internally).

### 1b. OpenAIVisionClient Update

**File:** `src/extraction/vision_client.py`

Changes:
- Model from constructor arg (not env var) — factory passes the model name.
- Support `application/pdf` via `input_file` content type in the Responses API.
- Timeout from constructor arg.
- Pricing from `MODEL_PRICING` dict in `src/extraction/pricing.py`.

```python
class OpenAIVisionClient:
    def __init__(self, model: str = "gpt-5.4-nano", timeout: int = 30) -> None:
        self._model = model
        self._timeout = timeout
        ...
```

For PDF, the `input` message changes:
```python
# Image (existing)
{"type": "input_image", "image_url": data_url}

# PDF (new)
{"type": "input_file", "file_data": base64_data, "filename": "document.pdf"}
```

### 1c. GeminiVisionClient (new)

**New file:** `src/extraction/gemini_vision_client.py`

```python
class GeminiVisionClient:
    """Vision client using Google Gemini API with structured outputs."""

    def __init__(self, model: str = "gemini-2.5-flash", timeout: int = 30) -> None:
        # Requires GEMINI_API_KEY env var
        # Uses google-genai SDK
        ...

    async def extract_from_image(
        self, image_data: bytes, mime_type: str, json_schema: dict, prompt: str,
    ) -> VisionExtractionResult:
        # For images: inline base64 in Part
        # For PDF: upload via client.files.upload(), then reference
        # asyncio.to_thread wraps sync SDK call
        ...
```

**Gemini structured output format** — must be verified against installed `google-genai` SDK at implementation time. The plan does not assume Pydantic. Two possible formats:

```python
# Option A: If SDK supports response_json_schema (JSON Schema dict)
config = GenerateContentConfig(
    response_mime_type="application/json",
    response_json_schema=json_schema,  # dict, same shape as OpenAI
)

# Option B: If SDK requires Pydantic model
from pydantic import create_model
DynamicModel = create_model("Extraction", **{f: (Optional[str], None) for f in fields})
config = GenerateContentConfig(
    response_mime_type="application/json",
    response_schema=DynamicModel,
)
```

**Implementation rule:** At implementation time, check the installed `google-genai` SDK docs and use whichever format the SDK supports. Add SDK-level tests proving:
- Schema passed in the format the installed SDK accepts
- Unknown fields are rejected/dropped
- Wrong types fail
- Response parses into the same fixed field set as OpenAI

**Gemini PDF handling:**
```python
# Upload PDF, then reference in content — with temp file cleanup
import tempfile
tmp_path = None
try:
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        f.write(file_data)
        tmp_path = f.name
    uploaded = await asyncio.to_thread(client.files.upload, file=tmp_path)

    response = await asyncio.to_thread(
        client.models.generate_content,
        model=self._model,
        contents=[uploaded, prompt],
        config=...
    )
finally:
    if tmp_path:
        os.unlink(tmp_path)
```

**Gemini Files API retention:** Uploaded files are stored by Google for 48 hours. Document this in provider metadata and audit:

```python
# In provider_metadata
"provider_file_retention": "gemini_48h",  # metadata-only, no filenames
```

The `extraction_provider_call_started` audit event already covers that a file was sent to the provider. No filename or storage key in audit.

**Error classification** — reuse `_classify_openai_error` pattern adapted for Gemini SDK exceptions:
```python
def _classify_gemini_error(exc: Exception) -> str:
    # Map google.genai errors to the same ERROR_CODES namespace
    ...
```

### 1d. Pricing Table

**New file:** `src/extraction/pricing.py`

```python
PRICING_TABLE_VERSION = "2026-05-07"
PRICING_TABLE_SOURCE = "manual_static_provider_pricing_2026_05_07"

MODEL_PRICING: dict[str, dict[str, float]] = {
    "gemini-2.5-flash":       {"input_per_1m": 0.30, "output_per_1m": 2.50},
    "gemini-2.5-flash-lite":  {"input_per_1m": 0.10, "output_per_1m": 0.40},
    "gemini-3-flash-preview":  {"input_per_1m": 0.50, "output_per_1m": 3.00},
    "gpt-5.4-nano":           {"input_per_1m": 0.20, "output_per_1m": 1.25},
    "gpt-5.4-mini":           {"input_per_1m": 0.75, "output_per_1m": 4.50},
}

def get_model_pricing(model: str) -> Optional[dict[str, float]]:
    """Get pricing for a model. Returns None if unknown (cost_estimate_usd will be null)."""
    return MODEL_PRICING.get(model)
```

**Unknown model behavior:** `get_model_pricing()` returns `None` for unknown models → `cost_estimate_usd = None`. Never store `$0.00` — null is honest about missing data.

**Version tracking:** `PRICING_TABLE_VERSION` stored in provider_metadata as `pricing_source` for every extraction attempt. Not accounting truth — best-effort estimate.

```python
# In provider_metadata
"pricing_source": PRICING_TABLE_SOURCE,
```

---

## Part 2: Model Chain Container

**New file:** `src/extraction/model_chain.py`

The service layer (`run_extraction`) owns fallback logic and attempt persistence. There is no `FallbackExtractor.extract()` — that would hide provider calls from the service layer.

`ModelChain` is a thin container holding ordered `(model_name, extractor)` pairs. No fallback logic, no `extract()` method.

```python
RETRIABLE_ERRORS = frozenset({
    "api_timeout", "api_rate_limit", "api_server_error", "empty_response",
})

class ModelChain:
    """Ordered list of (model_name, extractor) pairs. No fallback logic — service layer owns that."""

    def __init__(self, extractors: list[tuple[str, DocumentExtractor]]):
        self._chain = extractors

    @property
    def models(self) -> list[tuple[str, DocumentExtractor]]:
        return list(self._chain)

    def __len__(self) -> int:
        return len(self._chain)
```

The factory returns either a `ModelChain` (multi-model), a single extractor, or `NoopExtractor`. `run_extraction()` normalizes all three via `_get_model_chain()` and iterates itself.

**Fallback behavior (in service layer):**
- `api_timeout` → try next model
- `api_rate_limit` → try next model
- `api_server_error` → try next model
- `empty_response` → try next model
- `api_auth_error` → stop immediately (likely all models from same provider will fail)
- `schema_validation_failed` → stop immediately (schema is same across models)
- `unsupported_mime_type` → stop immediately (provider capability issue)

---

## Part 3: Factory Update

**File:** `spine_api/services/extraction_service.py`

Replace the single `get_extractor()` with a chain-aware factory:

```python
from typing import Union

ExtractorRuntime = Union[DocumentExtractor, "ModelChain"]

def get_extractor() -> ExtractorRuntime:
    """Build the extraction chain from EXTRACTION_MODEL_CHAIN env var.

    Returns one of: NoopExtractor, OpenAIVisionExtractor, GeminiVisionExtractor, or ModelChain.
    ModelChain has no extract() method — service layer iterates it via _get_model_chain().
    """
    chain_str = os.environ.get("EXTRACTION_MODEL_CHAIN", "").strip()

    if not chain_str:
        provider = os.environ.get("EXTRACTION_PROVIDER", "noop").lower()
        if provider == "noop":
            return NoopExtractor()
        app_env = os.environ.get("APP_ENV", "production").lower()
        if app_env in ("local", "test", "development"):
            return NoopExtractor()
        raise RuntimeError("EXTRACTION_MODEL_CHAIN must be set in production")

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
    if model.startswith("gemini"):
        return "gemini"
    if model.startswith("gpt-"):
        return "openai"
    raise ValueError(f"Cannot determine provider for model '{model}'")


def _resolve_provider_name(model_name: str) -> str:
    """Get provider_name for attempt row. Handles noop safely."""
    if model_name == "noop":
        return "noop_extractor"
    return _model_to_provider(model_name)
```

**OpenAIVisionExtractor update** — accept `model` parameter:
```python
class OpenAIVisionExtractor:
    def __init__(self, model: str = "gpt-5.4-nano") -> None:
        self._client = OpenAIVisionClient(model=model)
```

**GeminiVisionExtractor (new):**
```python
class GeminiVisionExtractor:
    def __init__(self, model: str = "gemini-2.5-flash") -> None:
        self._client = GeminiVisionClient(model=model)

    async def extract(self, file_data, mime_type, document_type):
        schema = get_schema(document_type)
        fields = schema["fields"]
        prompt = schema["prompt"]
        json_schema = build_json_schema(fields)
        vision_result = await self._client.extract_from_image(...)
        return ExtractionResult(...)
```

---

## Part 4: PDF Extraction Support

### 4a. MIME Prevalidation Update

**File:** `spine_api/server.py`

Expand allowed MIME types:
```python
ALLOWED_EXTRACTION_MIME_TYPES = {"image/jpeg", "image/png", "application/pdf"}
```

```python
if document.mime_type not in ALLOWED_EXTRACTION_MIME_TYPES:
    raise HTTPException(422, detail={
        "error_code": "unsupported_mime_type",
        "message": f"MIME type '{document.mime_type}' not supported for extraction",
    })
```

### 4b. PDF Page-Count Limit Policy

**Problem:** A 300-page PDF sent to a provider is a cost bomb. Gemini supports up to 1000 pages/50MB; OpenAI up to 50MB. Do not rely on provider limits as policy.

**Configuration:**
```python
# .env
EXTRACTION_MAX_PDF_PAGES=10  # default 10
```

**Pre-call page count check:**

```python
def _get_pdf_page_count(file_data: bytes) -> Optional[int]:
    """Lightweight PDF page-count using pypdf. Returns None if cannot determine."""
    try:
        from pypdf import PdfReader
        import io
        reader = PdfReader(io.BytesIO(file_data))
        return len(reader.pages)
    except Exception:
        return None

def _validate_pdf_pages(file_data: bytes, mime_type: str) -> None:
    """Raise ExtractionValidationError if PDF exceeds page limit."""
    if mime_type != "application/pdf":
        return
    max_pages = int(os.environ.get("EXTRACTION_MAX_PDF_PAGES", "10"))
    page_count = _get_pdf_page_count(file_data)
    if page_count is not None and page_count > max_pages:
        raise ExtractionValidationError(
            f"PDF has {page_count} pages, max allowed is {max_pages}"
        )
```

**Policy rules:**
- If page count can be read locally → block over max before any provider call. Return 422, no extraction row.
- If page count cannot be read locally → allow if file size ≤ Phase 4B document size cap. Record `page_count` from provider metadata after response if available.

### 4c. Client-Level MIME Handling

| Client | `image/jpeg` | `image/png` | `application/pdf` |
|:-------|:-------------|:------------|:------------------|
| `OpenAIVisionClient` | `input_image` | `input_image` | `input_file` |
| `GeminiVisionClient` | inline base64 | inline base64 | `files.upload()` |

### 4d. Page Count Metadata

```python
# In provider_metadata
"page_count": page_count,  # int or None — from provider response or local check
```

---

## Part 5: Append-Only Extraction Attempts (Revised)

### 5a. Schema Design: One Attempt Row Per Provider Call

**Key principle:** Every provider call within a fallback chain creates its own attempt row. This preserves the full fallback history.

```
Run 1 (first extraction):
  Attempt 1: gemini-2.5-flash  → failed (api_timeout)
  Attempt 2: gpt-5.4-nano      → success

Run 2 (retry after failed run):
  Attempt 3: gemini-2.5-flash  → success
```

### 5b. New Table: `document_extraction_attempts`

**File:** `spine_api/models/tenant.py`

```python
class DocumentExtractionAttempt(Base):
    __tablename__ = "document_extraction_attempts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    extraction_id = Column(String, ForeignKey("document_extractions.id"), nullable=False, index=True)
    run_number = Column(Integer, nullable=False)      # groups attempts from same extraction trigger (1, 2, ...)
    attempt_number = Column(Integer, nullable=False)   # global monotonic across all runs (1, 2, 3, 4, ...)
    fallback_rank = Column(Integer, nullable=True)     # 0=primary, 1=first fallback within this run

    # Provider details for THIS specific call
    provider_name = Column(String(30), nullable=False)
    model_name = Column(String(50), nullable=True)

    # Timing and usage
    latency_ms = Column(Integer, nullable=True)
    prompt_tokens = Column(Integer, nullable=True)
    completion_tokens = Column(Integer, nullable=True)
    total_tokens = Column(Integer, nullable=True)
    cost_estimate_usd = Column(Float, nullable=True)

    # Result — PII fields only on success attempts
    status = Column(String(20), nullable=False)  # "success" or "failed"
    error_code = Column(String(50), nullable=True)
    error_summary = Column(String(200), nullable=True)

    # Encrypted fields — NULL for failed attempts, populated only for success
    extracted_fields_encrypted = Column(JSON, nullable=True)
    fields_present = Column(JSON, nullable=True)
    field_count = Column(Integer, default=0)
    confidence_scores = Column(JSON, nullable=True)
    overall_confidence = Column(Float, nullable=True)
    confidence_method = Column(String(30), default="model")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

**Failed attempt rows contain:** provider_name, model_name, error_code, error_summary (from static dict), latency_ms, token usage. **No PII, no encrypted blob, no raw provider response.**

**Success attempt rows contain:** all of the above plus encrypted_fields_encrypted, fields_present, confidence_scores, etc.

### 5c. DocumentExtraction Updates

Add columns to existing `DocumentExtraction`:

| Column | Type | Notes |
|:-------|:-----|:------|
| `current_attempt_id` | String(36), nullable, indexed | Points to the latest successful attempt. **No FK constraint in Phase 4E** — enforced in service tests instead. |
| `attempt_count` | Integer, default=0 | Total attempt rows across all runs |
| `run_count` | Integer, default=0 | Number of extraction runs (initial + retries) |
| `page_count` | Integer, nullable | For PDF documents |

**Status flow:**
```
running → pending_review   (success)
running → failed           (all models exhausted or non-retriable)
failed → running           (via retry)
pending_review → applied   (terminal)
pending_review → rejected  (terminal)
```

`running` is a new status. Not exposed in the extraction GET response — client sees `pending_review`, `failed`, `applied`, or `rejected`.

### 5d. Creation Order (Fixed)

The extraction row is created **first** as a shell, then attempt rows are created with a valid `extraction_id`.

```python
async def run_extraction(db, document, storage, agency_id: str) -> DocumentExtraction:
    """Run extraction with full fallback history.

    Invariant: validation failures (PDF page limit) must not leave
    any extraction row or attempt row in the database.
    """

    # --- Step 0: Check existing state (read-only) ---

    existing = _find_extraction(db, document.id, agency_id)
    if existing and existing.status in ("applied", "rejected"):
        raise ValueError("Cannot retry: extraction already resolved")
    if existing is not None and existing.status == "running":
        raise ValueError("Extraction already in progress")

    is_retry = existing is not None and existing.status == "failed"

    # --- Step 1: Read file and validate BEFORE any DB mutation ---

    file_data = await storage.get(document.storage_key)
    _validate_pdf_pages(file_data, document.mime_type)  # raises ExtractionValidationError → no row created

    # --- Step 2: Find or create extraction aggregate (only after validation passes) ---

    if is_retry:
        extraction = existing
        extraction.status = "running"
        extraction.run_count += 1
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

            _emit_provider_call_audit(extraction, attempt, model_name)

            start = time.monotonic()
            try:
                result = await model_extractor.extract(file_data, document.mime_type, document.document_type)
            except ExtractionProviderError as e:
                attempt.error_code = e.error_code
                attempt.error_summary = ERROR_CODES.get(e.error_code, "Unknown error")
                attempt.latency_ms = int((time.monotonic() - start) * 1000)
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
        extraction.error_code = None
        extraction.error_summary = None
        extraction.provider_name = success_attempt.provider_name
        extraction.model_name = success_attempt.model_name
        extraction.latency_ms = success_attempt.latency_ms
        extraction.page_count = _get_page_count(file_data, document.mime_type)
    else:
        extraction.status = "failed"
        extraction.error_code = last_error.error_code
        extraction.error_summary = ERROR_CODES.get(last_error.error_code, "Unknown error")

    await db.commit()
    await db.refresh(extraction)
    return extraction
```

**Error handling invariants:**
- `ExtractionValidationError` before shell creation → no extraction row, no attempt rows, no audit
- `ExtractionProviderError` → extraction status=failed, attempt rows persisted with error_code
- Unexpected exception → try to mark extraction as failed, never leave `running` status
- PDF over page limit → 422, no DB changes at all

**Helper for single extractors (non-ModelChain):**

```python
def _get_model_chain(extractor) -> list[tuple[str, DocumentExtractor]]:
    """Normalize any extractor into a list of (model_name, extractor) pairs."""
    from src.extraction.model_chain import ModelChain
    if isinstance(extractor, ModelChain):
        return extractor.models
    if isinstance(extractor, NoopExtractor):
        return [("noop", extractor)]  # handled by _resolve_provider_name("noop")
    # Single vision extractor
    model = getattr(extractor, '_model', 'unknown')
    return [(model, extractor)]
```

### 5e. Retry Endpoint

**File:** `spine_api/server.py`

```python
@app.post("/trips/{trip_id}/documents/{document_id}/extraction/retry")
async def retry_extraction(trip_id: str, document_id: str, ...):
    """Retry a failed extraction. Creates new run with attempt rows."""

    # Guards: trip exists, document exists, agency authorized
    # Check extraction exists and status == "failed"
    # If status in ("running", "pending_review", "applied", "rejected") → 409

    extraction = await run_extraction(db, document, storage, agency.id)
    # Returns same ExtractionResponse format
```

### 5f. Attempts List Endpoint

```python
@app.get("/trips/{trip_id}/documents/{document_id}/extraction/attempts")
async def list_extraction_attempts(trip_id: str, document_id: str, ...):
    """List all extraction attempts for a document (audit trail)."""
    # Returns list of AttemptSummaryResponse
    # NO decrypted PII in list view
    # NO encrypted blob in list view
    # NO raw provider response
    # PII only available via the main GET extraction endpoint
```

---

## Part 6: Migration

**New file:** `alembic/versions/add_extraction_attempts_and_pdf.py`

Migration steps (all idempotent):

1. Create `document_extraction_attempts` table (no FK cycle issues — this table references `document_extractions.id`)
2. Add nullable columns to `document_extractions`:
   - `current_attempt_id` — String(36), nullable, indexed, **no FK constraint**
   - `attempt_count` — Integer, default 0
   - `run_count` — Integer, default 0
   - `page_count` — Integer, nullable
3. Backfill:
   - For each existing extraction with `status in ("pending_review", "applied", "rejected")`:
     - Create an attempt record with `run_number=1, attempt_number=1, fallback_rank=0, status="success"`
     - Copy encrypted_fields, confidence, provider metadata
     - Set `current_attempt_id` to the new attempt's id
   - For failed extractions:
     - Create a failed `DocumentExtractionAttempt` row:
       - `run_number=1, attempt_number=1, fallback_rank=0, status="failed"`
       - `extracted_fields_encrypted=NULL, fields_present={}, field_count=0`
       - Copy `error_code`/`error_summary` from aggregate if present
     - Set `attempt_count=1, run_count=1, current_attempt_id=NULL`
     - This preserves the invariant: `attempt_count` = number of attempt rows
   - For all: set `attempt_count` and `run_count` appropriately
4. All column additions checked with `has_column` before adding

**No circular FK:** `current_attempt_id` is a nullable indexed string, not a FK constraint. Correctness enforced by service layer and tests.

---

## Part 7: Configuration

### Env Vars

**File:** `.env.example`

```bash
# Extraction Configuration
# Phase 4E uses EXTRACTION_MODEL_CHAIN as the primary config.
# To run a single model locally: EXTRACTION_MODEL_CHAIN=gpt-5.4-nano
# The old EXTRACTION_PROVIDER=openai_vision is no longer the primary config.
# If EXTRACTION_MODEL_CHAIN is empty, factory falls back to noop in local/test/development.
EXTRACTION_MODEL_CHAIN=gemini-2.5-flash,gpt-5.4-nano,gemini-2.5-flash-lite
EXTRACTION_PROVIDER=noop  # legacy fallback when EXTRACTION_MODEL_CHAIN is empty
EXTRACTION_MAX_PDF_PAGES=10  # reject PDFs with more pages before provider call

# Provider: OpenAI
OPENAI_API_KEY=sk-...
OPENAI_VISION_TIMEOUT_SECONDS=30

# Provider: Google Gemini
GEMINI_API_KEY=...
GEMINI_VISION_TIMEOUT_SECONDS=30
```

### Pricing

Pricing is hardcoded in `src/extraction/pricing.py` with version tracking. Not accounting truth — best-effort estimate versioned with the code.

---

## Part 8: Endpoint Changes Summary

**File:** `spine_api/server.py`

| Endpoint | Change |
|:---------|:-------|
| `POST .../extract` | Expand MIME to include PDF. PDF page-count prevalidation. Attempt-aware `run_extraction()`. |
| `GET .../extraction` | Add `attempt_count`, `run_count`, `page_count` to response. `current_attempt_id`. |
| `POST .../extraction/retry` | **New.** Retry failed extraction. 409 if not failed. |
| `GET .../extraction/attempts` | **New.** List all attempts for audit. No PII. |

**ExtractionResponse** — add:
```python
attempt_count: int = 0
run_count: int = 0
current_attempt_id: Optional[str] = None
page_count: Optional[int] = None
```

**AttemptSummaryResponse** (new) — **no PII fields, no encrypted blob:**
```python
class AttemptSummaryResponse(BaseModel):
    attempt_id: str
    run_number: int
    attempt_number: int
    fallback_rank: Optional[int]
    provider_name: str
    model_name: Optional[str]
    latency_ms: Optional[int]
    status: str  # "success" or "failed"
    error_code: Optional[str]
    created_at: Optional[datetime]
    # Explicitly excluded: extracted_fields, fields_present, confidence_scores,
    # encrypted blob, raw provider response, error_summary
```

---

## Part 9: Audit Events

| Event | Fields | Notes |
|:------|:-------|:------|
| `extraction_run_started` | trip_id, document_id, extraction_id, run_number | Before any provider call |
| `extraction_provider_call_started` | trip_id, document_id, extraction_id, attempt_id, provider, model, fallback_rank | Before each provider call — metadata only |
| `extraction_attempt_failed` | trip_id, document_id, extraction_id, attempt_id, provider, model, error_code, latency_ms | After failed provider call |
| `extraction_run_completed` | trip_id, document_id, extraction_id, run_number, status, provider, model, latency_ms | After run completes (success or all-failed) |
| `extraction_retry_requested` | trip_id, document_id, extraction_id, previous_run_count | When retry endpoint called |

**Never audited:** field values, raw response, error_summary, filename, storage key, signed URL, file content.

The `extraction_provider_call_started` event provides an audit trail for data transfers — which providers received customer document data and when.

---

## Part 10: Tests

**New file:** `tests/test_extraction_fallback.py` (~14 tests)

**TestModelChain (3):**
- ModelChain holds ordered pairs, `.models` returns list
- `_get_model_chain()` normalizes single extractor, ModelChain, and NoopExtractor
- RETRIABLE_ERRORS set is correct

**TestServiceFallback (4):**
- Primary model succeeds → one attempt row (success), extraction pending_review
- Primary timeout + secondary success → two attempt rows (failed + success), current_attempt_id points to second
- All models fail → all attempt rows failed, extraction failed
- Non-retriable error (auth) → one attempt row, no further fallback

**TestGeminiVisionClient (3):**
- Mocked Gemini API → parsed fields + metadata (image input)
- Mocked Gemini API → parsed fields + metadata (PDF input)
- Gemini API error → ExtractionProviderError with classified error_code

**TestModelPricing (3):**
- Known model → correct pricing with cost_estimate_usd
- Unknown model → pricing is None → cost_estimate_usd is None
- Pricing source includes version string in metadata

**TestFactory (3):**
- `EXTRACTION_MODEL_CHAIN=gemini-2.5-flash,gpt-5.4-nano` → ModelChain with 2 extractors
- `EXTRACTION_MODEL_CHAIN=gpt-5.4-nano` → OpenAIVisionExtractor (no fallback wrapper)
- `EXTRACTION_MODEL_CHAIN=gemini-2.5-flash` → GeminiVisionExtractor (no fallback wrapper)

**New file:** `tests/test_extraction_attempts.py` (~14 tests)

**TestAttemptCreation (3):**
- First extraction → extraction shell (running) → attempt rows → extraction updated to pending_review
- Retry after failure → new run_number, new attempt rows, extraction back to pending_review
- Retry on non-failed extraction → 409

**TestFallbackHistory (3):**
- **Primary timeout + secondary success → two attempt rows exist:**
  - First has error_code=api_timeout, status=failed, no encrypted blob
  - Second has status=success, encrypted blob present
  - current_attempt_id points to second
  - Audit contains no provider raw error
- **All models fail → all attempt rows have status=failed, extraction status=failed**
- **Non-retriable error → only one attempt row (no further fallback)**

**TestAttemptListNoPII (2):**
- **Attempt list response contains no encrypted blob, no field values, no raw provider errors**
- **Failed attempt rows in DB have extracted_fields_encrypted=NULL**

**TestPDFExtraction (4):**
- PDF + OpenAI → client sends input_file (mocked)
- PDF + Gemini → client uses files.upload (mocked), temp file cleaned up after
- PDF page_count recorded in metadata
- **PDF with pages > EXTRACTION_MAX_PDF_PAGES → 422 before provider call, no extraction row, no provider-call audit**
- **PDF page-count parse failure but small file → allowed, proceeds normally**

**TestMigrationBackfill (2):**
- Existing successful extraction → one success attempt row created, current_attempt_id set
- **Existing failed extraction → one failed attempt row created with error_code copied, current_attempt_id=NULL**

**TestRetryEndpoint (2):**
- POST retry on failed extraction → new run, status back to pending_review
- POST retry on applied extraction → 409

**TestNoopAttempt (1):**
- **NoopExtractor extraction creates one success attempt with provider_name=noop_extractor**

**TestPDFPageLimitInvariants (4):**
- **Over-page-limit first extraction → 422, no document_extractions row, no attempt rows, no provider-call audit**
- **Over-page-limit retry → existing failed extraction remains failed, run_count unchanged**
- **Over-page-limit retry → no new attempt rows created**
- **Over-page-limit → no provider-call audit event emitted**

**Updated:** `tests/test_vision_extraction.py`
- Update factory tests for new `EXTRACTION_MODEL_CHAIN` env var
- Update MIME tests to include `application/pdf`
- Verify PDF MIME type passes prevalidation

---

## Part 11: Files Changed

| File | Change |
|:-----|:-------|
| `src/extraction/pricing.py` | New — model pricing table with versioning, null-for-unknown |
| `src/extraction/gemini_vision_client.py` | New — Gemini API client |
| `src/extraction/gemini_vision_extractor.py` | New — Gemini extractor |
| `src/extraction/model_chain.py` | New — thin ModelChain container (no fallback logic) |
| `src/extraction/vision_client.py` | Update — constructor takes model/timeout params, add PDF support |
| `src/extraction/openai_vision_extractor.py` | Update — accept model param |
| `src/extraction/pdf_utils.py` | New — lightweight PDF page-count check |
| `spine_api/services/extraction_service.py` | Update — chain factory, attempt-per-call run_extraction |
| `spine_api/models/tenant.py` | Add DocumentExtractionAttempt table, update DocumentExtraction columns |
| `alembic/versions/add_extraction_attempts_and_pdf.py` | New — migration with backfill |
| `spine_api/server.py` | Update — MIME expansion, PDF page limit, retry endpoint, attempts endpoint |
| `.env.example` | Add EXTRACTION_MODEL_CHAIN, GEMINI_API_KEY, EXTRACTION_MAX_PDF_PAGES |
| `tests/test_extraction_fallback.py` | New — ModelChain, service fallback, Gemini, pricing tests |
| `tests/test_extraction_attempts.py` | New — attempts, fallback history, retry, PDF, migration backfill tests |
| `tests/test_vision_extraction.py` | Update — MIME and factory test updates |

---

## Implementation Order

1. **Pricing table** — `src/extraction/pricing.py` (no dependencies)
2. **PDF utils** — `src/extraction/pdf_utils.py` (page count check, no dependencies)
3. **OpenAIVisionClient refactor** — constructor params, PDF support, pricing integration
4. **GeminiVisionClient** — new client + extractor (verify SDK structured output format)
5. **ModelChain** — thin chain container (service layer owns fallback)
6. **Factory update** — chain-aware `get_extractor()`
7. **Model + migration** — DocumentExtractionAttempt, new columns, backfill
8. **Service refactor** — attempt-per-call `run_extraction()` with creation-order fix
9. **Endpoints** — MIME expansion, PDF page limit, retry, attempts list
10. **Tests** — fallback, attempts, PDF, regression
11. **Env config** — .env.example

---

## Verification

```bash
# Migration
uv run alembic upgrade head

# Phase 4E tests
uv run pytest tests/test_extraction_fallback.py tests/test_extraction_attempts.py -v

# Phase 4D regression
uv run pytest tests/test_vision_extraction.py -v

# Phase 4C regression
uv run pytest tests/test_document_extractions.py -v

# Phase 4B + 4A regression
uv run pytest tests/test_booking_documents.py tests/test_booking_collection.py tests/test_readiness_engine.py -v

# Frontend
cd frontend && npm test -- --run

# TypeScript
cd frontend && npx tsc --noEmit
```
