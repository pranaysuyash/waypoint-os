# Phase 4C Closure Report

**Date:** 2026-05-06
**Phase:** 4C — Document OCR and Structured Extraction
**Status:** CLOSED — audit passed 2026-05-06

## Context

Phase 4B (closed 2026-05-05) gave agents secure document upload, review gates, and privacy boundaries. But documents are opaque binary — agents still manually transcribe passport numbers, dates of birth, and visa details into booking_data. Phase 4C adds structured OCR extraction from uploaded documents. The core invariant: **OCR output is untrusted and never auto-writes to booking_data.** Agents must explicitly select which fields to apply, to which traveler, with conflict awareness.

## Blocker Resolution

Phase 4C design was revised through one round of review addressing 9 blockers:

| # | Blocker | Resolution |
|:--|:--------|:-----------|
| 1 | Extracted PII in plaintext columns | Single `extracted_fields_encrypted` Fernet blob. No plaintext PII columns. Same encryption pattern as `booking_data`. |
| 2 | raw_ocr_text stored but never returned | Not stored in Phase 4C. NoopExtractor has no raw text. Deferred to future phase with encrypted storage and dedicated accessor. |
| 3 | One extraction + re-extraction deletes records | One extraction per document. No re-extraction in Phase 4C. Applied/rejected are terminal. No row deletion. |
| 4 | Apply overwrites trusted data | Apply requires explicit `fields_to_apply`, `traveler_id`. Refuses overwrite unless `allow_overwrite=true`. Returns masked conflicts. No auto-append traveler. |
| 5 | _field_sources not in BookingDataModel | Deferred. Audit applied field names only. No schema extension to booking_data. |
| 6 | Extraction requires document accepted | Extraction allowed on `pending_review` OR `accepted`. Apply blocked unless document `accepted`. Two-step trust model. |
| 7 | NoopExtractor fake PII-like sentinels | Uses explicit audit sentinels: `DO_NOT_LOG_NAME`, `DO_NOT_LOG_PASSPORT`, `DO_NOT_LOG_DOB`, etc. Tests assert these never appear in logs. |
| 8 | API returns arbitrary extra_fields | No `extra_fields` column or response field. Fixed field set only (`VALID_EXTRACTION_FIELDS`). |
| 9 | Audit includes field values | Audit: field names/counts/confidence summary only. No values. |

## Audit Results

### Backend (29 tests in `tests/test_document_extractions.py`)

**NoopExtractor (2):**
- Returns sentinel values with confidence scores
- Different fields per document type (passport/visa/insurance)

**Extract Endpoint (6):**
- Accepted document → extraction created with status=pending_review
- Pending_review document → extraction allowed
- Rejected document → 409
- Deleted document → 404/409
- Duplicate extraction → 409 (one per document)
- Discovery stage → 403 (stage gate)

**Get Extraction (2):**
- Returns decrypted fields, no encrypted blob in response
- No extraction found → 404

**Apply (8):**
- Selected fields written to booking_data.travelers
- Blocked unless document accepted
- Blocked on already-applied extraction
- Conflicts returned without overwrite (masked values)
- With allow_overwrite=true → succeeds
- Does not auto-append traveler without explicit flag
- Recomputes readiness after booking_data update
- Blocked at discovery stage (stage gate)

**Apply Guardrails (4):**
- Rejects unknown fields → 422
- Rejects empty fields_to_apply → 422
- Rejects fields not present in extraction → 422
- New traveler creation requires full_name + date_of_birth → 422

**Encryption Proof (1):**
- Raw DB column contains no sentinel values; encrypted blob shape verified; round-trip decryption confirmed

**Reject (3):**
- Does not modify booking_data
- Blocked on already-applied extraction
- Works at any stage (no stage gate on reject)

**Privacy (3):**
- Response excludes `extracted_fields_encrypted`, `raw_ocr_text`, `extra_fields`
- Audit has no `DO_NOT_LOG_*` sentinels
- Extraction data not in document list endpoint

### Regression Tests

- **Phase 4B:** 44/44 passed
- **Phase 4A:** 72/72 passed
- **Frontend:** 679/679 passed, 72 suites (6 new extraction apply flow tests)
- **TypeScript:** 0 errors

### Guardrail Verifications

1. Raw DB/storage column does not contain `DO_NOT_LOG_*` sentinels
2. Audit logs do not contain `DO_NOT_LOG_*` sentinels
3. Apply rejects empty `fields_to_apply` → 422
4. Apply rejects unknown fields → 422
5. Apply rejects fields not present in extraction → 422
6. New traveler creation requires `full_name` + `date_of_birth` → 422
7. `ValueError` from service maps to 409; `ExtractionValidationError` maps to 422

---

## Data Model

### Table: `document_extractions`

| Column | Type | Nullable | Default | Notes |
|:-------|:-----|:---------|:--------|:------|
| `id` | String(36) | No | UUID | PK |
| `document_id` | String(36) | No | — | FK → booking_documents.id CASCADE, UNIQUE |
| `trip_id` | String(36) | No | — | FK → trips.id CASCADE |
| `agency_id` | String(36) | No | — | FK → agencies.id CASCADE |
| `extracted_fields_encrypted` | JSON | Yes | — | Fernet blob: `{"__encrypted_blob": true, "v": 1, "ciphertext": "..."}` |
| `fields_present` | JSON | Yes | — | `{field_name: bool}` — no PII values |
| `field_count` | Integer | No | 0 | Count of present fields |
| `confidence_scores` | JSON | Yes | — | `{field_name: float}` — numbers only |
| `overall_confidence` | Float | Yes | — | Weighted average |
| `status` | String(20) | No | `pending_review` | `pending_review` → `applied`/`rejected` |
| `extracted_by` | String(20) | No | `noop_extractor` | |
| `reviewed_by` | String(36) | Yes | — | |
| `reviewed_at` | DateTime(tz) | Yes | — | |
| `created_at` | DateTime(tz) | No | now() | |
| `updated_at` | DateTime(tz) | No | now() | |

**Indexes:** `ix_de_document_id` (unique), `ix_de_trip_id`, `ix_de_status`

**Encrypted blob shape** (decrypted):
```json
{
  "full_name": "John Doe",
  "passport_number": "AB1234567",
  "passport_expiry": "2030-01-01",
  "nationality": "US",
  "date_of_birth": "1990-06-15"
}
```

**`fields_present` shape** (plaintext, for queryability):
```json
{
  "full_name": true,
  "passport_number": true,
  "date_of_birth": true,
  "visa_type": false,
  "insurance_provider": false
}
```

**Valid extraction fields** (10, fixed set):
`full_name`, `date_of_birth`, `passport_number`, `passport_expiry`, `nationality`, `visa_type`, `visa_number`, `visa_expiry`, `insurance_provider`, `insurance_policy_number`

**Status state machine** (terminal):
```
pending_review → applied   (agent applies selected fields)
pending_review → rejected  (agent rejects extraction)
```

No re-extraction in Phase 4C. One extraction per document (enforced by unique constraint on `document_id`).

**Relationships:**
- `document` → BookingDocument
- `trip` → Trip
- `agency` → Agency

### Migration

- **File:** `alembic/versions/add_document_extractions.py`
- **Revision:** `add_document_extractions`
- **Down revision:** `add_booking_documents`
- **Idempotent:** Guarded table + index creation

---

## Encryption

Extracted PII is encrypted at rest using the same Fernet blob pattern as `booking_data`:

```python
# spine_api/services/extraction_service.py
def encrypt_blob(data: dict) -> dict:
    serialized = json.dumps(data, default=str)
    token = encrypt(serialized)  # Fernet encrypt
    return {"__encrypted_blob": True, "v": 1, "ciphertext": token}

def decrypt_blob(data: dict) -> dict:
    if isinstance(data, dict) and data.get("__encrypted_blob"):
        token = data.get("ciphertext", "")
        serialized = decrypt(token)
        return json.loads(serialized)
    return data
```

Reuses the same `src.security.encryption` module and Fernet key as the rest of the application. No second encryption scheme.

---

## Extraction Service

**File:** `spine_api/services/extraction_service.py`

### Extractor Protocol

```python
class DocumentExtractor(Protocol):
    async def extract(self, file_data: bytes, mime_type: str, document_type: str) -> ExtractionResult: ...

@dataclass
class ExtractionResult:
    fields: dict[str, Optional[str]]       # {full_name: "...", passport_number: "..."}
    confidence_scores: dict[str, float]     # {full_name: 0.95}
    overall_confidence: float
```

### NoopExtractor (dev/test)

Returns mock data with explicit audit sentinels for PII privacy testing:
- `passport` → full_name, passport_number, passport_expiry, nationality, date_of_birth
- `visa` → visa_type, visa_number, visa_expiry, full_name, nationality
- `insurance` → insurance_provider, insurance_policy_number, full_name
- Default → full_name only

All sentinel values use `DO_NOT_LOG_*` prefix. Audit tests hard-fail if any sentinel appears in logs.

### CRUD Functions

- `run_extraction(db, document, storage, agency_id)` — Runs extractor, encrypts PII, creates record
- `get_extraction_for_document(db, document_id, agency_id)` — Scoped to agency
- `apply_extraction(db, document, extraction, fields_to_apply, traveler_id, ...)` — Conflict-aware apply with readiness recompute
- `reject_extraction(db, extraction, reviewed_by)` — Does not modify booking_data
- `decrypt_extraction_fields(extraction)` — Decrypts blob for API response
- `_mask_value(val)` — Masks values for conflict display: `"John Doe"` → `"Jo***e"`

---

## API Endpoints

### Agent Endpoints (authenticated via `get_current_agency`)

| Method | Path | Purpose | Stage Guard | Document Guard | Extraction Guard |
|:-------|:-----|:---------|:------------|:---------------|:-----------------|
| POST | `/trips/{trip_id}/documents/{document_id}/extract` | Run extraction | proposal/booking | pending_review or accepted | — |
| GET | `/trips/{trip_id}/documents/{document_id}/extraction` | Get results | — | — | — |
| POST | `/trips/{trip_id}/documents/{document_id}/extraction/apply` | Apply fields | proposal/booking | accepted | pending_review |
| POST | `/trips/{trip_id}/documents/{document_id}/extraction/reject` | Reject | **none** | — | pending_review |

### Apply Request

```json
{
  "traveler_id": "t1",
  "fields_to_apply": ["passport_number", "passport_expiry"],
  "allow_overwrite": false,
  "create_traveler_if_missing": false
}
```

### Apply Response

```json
{
  "applied": false,
  "conflicts": [
    {
      "field_name": "full_name",
      "existing_value": "Ma***y",
      "extracted_value": "DO***ME"
    }
  ],
  "extraction": { ... }
}
```

### Conflict Detection

When `allow_overwrite=false` (default):
1. For each field in `fields_to_apply`, compare extracted value against existing booking_data value
2. If existing value is non-empty and differs from extraction: conflict
3. Conflict values are masked (`_mask_value`) — first 2 and last 2 chars visible
4. Return `{applied: false, conflicts: [...]}` — no booking_data mutation

When `allow_overwrite=true`:
1. Same conflict detection runs
2. Conflicts are overwritten
3. Return `{applied: true, conflicts: []}`

### Traveler Matching

- Searches `booking_data.travelers` for matching `traveler_id`
- If not found and `create_traveler_if_missing=false`: 409 error
- If not found and `create_traveler_if_missing=true`: appends new traveler entry
- No fuzzy matching, no "first traveler if only one" heuristic

### Readiness Recompute

After successful apply:
1. Saves updated `booking_data` to trip store
2. Reloads trip data
3. Calls `compute_readiness()` with updated booking_data (same pattern as Phase 4A accept)
4. Persists `validation.readiness`
5. Ensures UI shows current readiness state

---

## Privacy Boundaries

### Storage
- `extracted_fields_encrypted` — Fernet blob, same scheme as `booking_data`
- `fields_present` — boolean indicators only, no PII values
- `confidence_scores` — numbers only, no PII values
- No `raw_ocr_text` column
- No `extra_fields` column
- No plaintext PII columns

### API Response Exclusions
- `ExtractionResponse` includes decrypted field values (agent-only, authenticated)
- Excluded from response: `extracted_fields_encrypted`, `raw_ocr_text`, `extra_fields`
- Conflict display uses masked values only

### No Extraction in Generic Responses
- `GET /trips/{id}` — no extraction data
- `GET /trips/{id}/documents` — no extraction data in document list
- Extraction accessed only through dedicated endpoints
- `spine_api/persistence.py` has 0 references to `document_extractions`

### Audit Policy

**Logged (metadata only):**
```python
# extraction_created
{"trip_id", "document_id", "document_type", "field_count",
 "overall_confidence", "fields_present"}  # fields_present = {name: bool}

# extraction_applied
{"trip_id", "document_id", "fields_applied": ["passport_number", ...],
 "field_count", "min_confidence", "overall_confidence"}

# extraction_rejected
{"trip_id", "document_id", "extraction_id", "field_count"}
```

**Never logged:** extracted field values, encrypted blob, traveler PII, confidence with values, masked conflict values

---

## Stage Gates

| Action | Stage Requirement | Rationale |
|:-------|:------------------|:----------|
| Extract | proposal or booking | Extraction is a booking-stage operation |
| Get extraction | any | Read-only, no mutation |
| Apply | proposal or booking | Mutates booking_data — only valid in booking flow |
| Reject | **any stage** | Rejection never mutates booking_data; should work even if trip regressed |

---

## Frontend

### API Client (`frontend/src/lib/api-client.ts`)

Types: `ExtractionFieldView`, `ExtractionResponse`, `ApplyConflict`, `ApplyExtractionResponse`

Functions: `extractDocument`, `getExtraction`, `applyExtraction`, `rejectExtraction`

### Route Map (`frontend/src/lib/route-map.ts`)

4 proxy entries: extract, extraction, extraction/apply, extraction/reject

### OpsPanel (`frontend/src/app/(agency)/workbench/OpsPanel.tsx`)

- "Extract" button on pending_review/accepted documents
- Extraction results: field-by-field with confidence bars (green ≥90%, yellow ≥70%, red <70%)
- **Traveler selector** dropdown sourced from `booking_data.travelers` — agent must pick target
- **Field checkboxes** per extracted field — agent selects which to apply
- **Apply disabled** until traveler selected AND at least one field checked
- First apply sends `allow_overwrite=false` — does not auto-overwrite trusted data
- If conflicts returned: conflict display with masked values + "Apply with overwrite" button
- Overwrite confirmation requires explicit second click sending `allow_overwrite=true`
- "Reject" button
- Status badges: pending_review (yellow), applied (green), rejected (red)
- data-testids: `ops-doc-extract-btn-{id}`, `ops-extraction-fields-{id}`, `ops-extraction-apply-btn-{id}`, `ops-extraction-reject-btn-{id}`, `ops-extraction-traveler-select-{id}`, `ops-extraction-field-cb-{id}-{field}`, `ops-extraction-conflicts-{id}`, `ops-extraction-overwrite-btn-{id}`

### OpsPanel Tests (`frontend/src/app/(agency)/workbench/__tests__/OpsPanel.test.tsx`)

6 new tests for extraction apply flow:
- Apply disabled when no traveler selected
- Apply disabled when no fields selected
- Apply sends selected traveler_id and selected fields only
- First apply sends `allow_overwrite=false`
- Conflict response shows overwrite confirmation
- Overwrite confirmation sends `allow_overwrite=true`

---

## Architectural Decisions

| Decision | Choice | Rationale |
|:---------|:-------|:----------|
| PII storage | Fernet-encrypted JSON blob | Same pattern as booking_data; no plaintext PII at rest |
| Plaintext indicators | `fields_present` + `field_count` | Queryability without decryption |
| No raw OCR text | Column not created | Raw text contains all PII; store only when there's a compliance reason |
| No re-extraction | Unique constraint on document_id | Simpler lifecycle; applied/rejected are terminal |
| Two-step trust | Extract from pending_review/accepted; apply only when accepted | Document trust and data trust are separate |
| Explicit apply | Agent selects traveler_id + fields_to_apply | No automatic field assignment or traveler matching |
| Conflict awareness | Return conflicts without overwrite; require explicit allow_overwrite | Prevents accidental overwrite of trusted data |
| No traveler auto-creation | create_traveler_if_missing defaults to false | Agent must explicitly opt in |
| Readiness recompute | After successful apply | Booking data changed; readiness must reflect new state |
| Stage gates | Extract/apply at proposal/booking; reject at any stage | Booking operations only during booking flow; reject always safe |
| NoopExtractor sentinels | DO_NOT_LOG_* values | Privacy test sentinels that would fail audit if leaked |
| No extra_fields | Fixed 10-field set only | Prevents arbitrary PII storage; add fields via migration |
| ExtractionValidationError → 422 | Separate validation vs business-logic errors | Validation errors (bad input) return 422; business conflicts return 409 |
| Traveler creation guard | full_name + date_of_birth required | Prevents invalid booking_data with only passport_number |
| Raw encryption proof | test_extracted_fields_encrypted_at_rest | Proves Fernet encryption at rest via direct DB query; sentinels absent from raw column |

---

## Files Changed

| File | Change |
|:-----|:-------|
| `alembic/versions/add_document_extractions.py` | New — idempotent table migration |
| `spine_api/models/tenant.py` | Add `DocumentExtraction` model (15 columns, 3 indexes, 3 relationships) |
| `spine_api/services/extraction_service.py` | New — extractor protocol, NoopExtractor, Fernet blob encryption, CRUD, conflict-aware apply, `ExtractionValidationError`, field/traveler validation guards |
| `spine_api/server.py` | Add 4 endpoints + 5 Pydantic models, stage gates, readiness recompute, `ExtractionValidationError` → 422 |
| `frontend/src/lib/api-client.ts` | Add 4 types + 4 API functions |
| `frontend/src/lib/route-map.ts` | Add 4 proxy entries |
| `frontend/src/app/(agency)/workbench/OpsPanel.tsx` | Add extraction UI (extract btn, results display, apply/reject) |
| `tests/test_document_extractions.py` | New — 29 backend tests (24 base + 4 guardrails + 1 encryption proof) |

---

## Known Future Work (Not Phase 4C Debt)

- Real OCR/vision API extractor (Claude Vision, GPT-4o, Tesseract)
- Encrypted raw OCR text storage with dedicated accessor
- Re-extraction (append-only attempts with superseded_by)
- Field-level source tagging in booking_data schema
- Selective field apply (per-field apply/reject)
- Extraction from customer-uploaded documents with traveler matching
- Batch extraction (multiple documents at once)
- Document thumbnails/previews with OCR overlay
- Traveler auto-matching by full_name fuzzy search
- Per-field confidence thresholds (auto-reject low-confidence fields)

---

## Verification Commands

```bash
# Migration
cd /Users/pranay/Projects/travel_agency_agent
uv run alembic upgrade head

# Phase 4C tests
uv run pytest tests/test_document_extractions.py -v

# Phase 4B regression
uv run pytest tests/test_booking_documents.py -v

# Phase 4A regression
uv run pytest tests/test_booking_collection.py tests/test_readiness_engine.py -v

# Frontend (use local binary, NOT npx)
cd frontend && npm test -- --run

# TypeScript
cd frontend && npx tsc --noEmit

# Privacy: no plaintext PII columns in extraction model
grep -n "full_name\|passport_number\|date_of_birth" spine_api/models/tenant.py | grep -v "fields_present\|# "
# Should find nothing (only in fields_present JSON or comments)

# Privacy: encrypted blob column exists
grep "extracted_fields_encrypted" spine_api/models/tenant.py

# Privacy: no raw_ocr_text column
grep "raw_ocr_text" spine_api/models/tenant.py  # should find nothing

# Privacy: no extraction in trip hydration
grep "document_extractions" spine_api/persistence.py  # should find nothing

# Privacy: no field values in audit
grep -A5 "extraction_created\|extraction_applied" spine_api/server.py

# Privacy: response excludes encrypted blob
grep "extracted_fields_encrypted" spine_api/server.py  # should find nothing in response models
```
