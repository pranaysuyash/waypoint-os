# Phase 4B Closure Report

**Date:** 2026-05-05
**Phase:** 4B — Secure Document Upload and Storage
**Status:** CLOSED — audit passed 2026-05-05

## Design Packet

Approved per revised Phase 4B design with two additions:
1. `INTERNAL_URL_SECRET` must fail fast in production/staging (no random fallback)
2. `deleted_at`/`deleted_by`/`storage_delete_status` soft-delete metadata fields

All 12 original blockers resolved (see Blocker Resolution table below).

## Blocker Resolution

| # | Blocker | Resolution |
|:--|:--------|:-----------|
| 1 | Signed URLs expose storage_key | Endpoint keyed by document_id; HMAC claim = `{document_id}:{operation}:{expires_ts}` |
| 2 | NoopScanner returns `clean` | NoopScanner returns `scan_status=skipped`; documents go directly to `pending_review` |
| 3 | Accept from quarantined allowed | Accept/reject only from `pending_review`; no quarantine in NoopScanner flow |
| 4 | Plaintext filename stored | `filename_hash` (SHA-256) + `filename_ext` only; `filename_present: bool` in response |
| 5 | MIME-only file validation | Magic-byte detection primary (`%PDF`, `\xff\xd8\xff`, `\x89PNG`); MIME header secondary |
| 6 | Full-buffer size check | Streaming read in 64KB chunks; aborts immediately on overflow |
| 7 | Hard delete | Soft-delete: `status=deleted`, file retained on disk, `storage_delete_status="retained"` |
| 8 | Token lifecycle conflict | Customer uploads BEFORE final submit; token stays active; `mark_token_used` unchanged |
| 9 | No FK on collection_token_id | `ForeignKey("booking_collection_tokens.id", ondelete="SET NULL")` |
| 10 | No audit sentinel tests | 6-sentinel PII test + filename leak test; hard-fail, no OR |
| 11 | Customer response too rich | `CustomerDocumentResponse` = `{id, status}` only |
| 12 | No document type validation | Enum-validated; unknown types rejected with 422 |

## Audit Results

### Backend (38 tests in `tests/test_booking_documents.py`)

**Storage (6):**
- `LocalDocumentStorage` put/get round-trip
- Soft-delete retains file on disk
- Signed URL keyed by document_id (not storage_key)
- HMAC validation: wrong document_id rejected
- Signed URL expiration check
- File metadata retrieval

**File Validation (7):**
- Magic-byte detection: PDF, JPEG, EXE rejection
- Extension sanitization: valid extensions, rejects `.exe`, rejects empty
- NoopScanner returns `status=skipped`

**Service CRUD (2):**
- Upload creates document with `status=pending_review`, `scan_status=skipped`
- Invalid document_type rejected with 422

**Upload Endpoints (5):**
- Agent upload creates document record
- Blocked at discovery stage (403)
- Magic-byte rejection of executables (415)
- Bad extension rejection (415)
- Invalid document_type rejection (422)

**List (1):**
- Returns non-deleted documents; excludes internal fields

**Token Session (4):**
- Customer upload through active token succeeds
- Upload blocked after token consumed by booking-data submit (410)
- Token still valid for submit after document upload
- Upload blocked after stage change to discovery (410)

**Review Gate (5):**
- Accept from `pending_review` → `accepted`
- Reject from `pending_review` → `rejected`
- Accept blocked on already-accepted (409)
- Accept blocked on rejected (409)
- Reject blocked on deleted (409)

**Soft Delete (3):**
- Sets `status=deleted`
- Delete blocked on `pending_review` (409)
- Deleted documents excluded from list

**Download URL (2):**
- URL contains document_id, not storage_key
- Cross-trip access blocked (404)

**Privacy (6):**
- Documents not in generic `GET /trips/{id}`
- `DocumentResponse` has no `storage_key` or `filename_hash`
- Customer response is `{id, status}` only
- No public document list endpoint (404/405)
- **6-sentinel audit test** — hard fail on: raw filename, traveler name, storage_key, traveler ID with PII hint, filename_hash. No OR escape hatch.
- Audit uses `filename_present: bool`, not raw filename

**Access Control (3):**
- Wrong agency blocked (404)
- Nonexistent document (404)
- Internal download rejects bad HMAC (403)

### Frontend (667 tests, 667 pass)
- 0 TypeScript errors across entire project
- No new test failures introduced

---

## Data Model

### Table: `booking_documents`

| Column | Type | Nullable | Default | Notes |
|:-------|:-----|:---------|:--------|:------|
| `id` | String(36) | No | UUID | PK |
| `trip_id` | String(36) | No | — | FK → trips.id CASCADE |
| `agency_id` | String(36) | No | — | FK → agencies.id CASCADE |
| `traveler_id` | String(36) | Yes | — | Optional |
| `uploaded_by_type` | String(20) | No | — | `agent` or `customer` |
| `uploaded_by_id` | String(36) | Yes | — | |
| `collection_token_id` | String(36) | Yes | — | FK → booking_collection_tokens.id SET NULL |
| `filename_hash` | String(64) | No | — | SHA-256 of original filename |
| `filename_ext` | String(10) | No | — | `.pdf`, `.jpg`, `.jpeg`, `.png` |
| `storage_key` | String(512) | No | — | `{agency_id}/{trip_id}/{uuid}.{ext}` |
| `mime_type` | String(100) | No | — | From magic bytes |
| `size_bytes` | Integer | No | — | |
| `sha256` | String(64) | No | — | SHA-256 of file content |
| `document_type` | String(30) | No | — | Enum-validated |
| `status` | String(20) | No | `pending_review` | `pending_review` → `accepted`/`rejected` → `deleted` |
| `scan_status` | String(20) | No | `skipped` | `skipped`/`clean`/`suspicious`/`failed` |
| `review_notes_present` | Boolean | No | false | |
| `created_at` | DateTime(tz) | No | now() | |
| `updated_at` | DateTime(tz) | No | now() | |
| `reviewed_at` | DateTime(tz) | Yes | — | |
| `reviewed_by` | String(36) | Yes | — | |
| `deleted_at` | DateTime(tz) | Yes | — | Soft-delete timestamp |
| `deleted_by` | String(36) | Yes | — | Agent who deleted |
| `storage_delete_status` | String(20) | Yes | — | `retained` for soft-delete |

**Indexes:** `ix_bd_trip_id`, `ix_bd_agency_id`, `ix_bd_status`

**Status state machine:**
```
pending_review → accepted  (agent review)
pending_review → rejected  (agent review)
accepted → deleted  (soft-delete, file retained)
rejected → deleted  (soft-delete, file retained)
```

### Migration

- **File:** `alembic/versions/add_booking_documents.py`
- **Revision:** `add_booking_documents`
- **Down revision:** `f1a2b3c4d5e6`
- **Idempotent:** Guarded table + index creation

---

## API Endpoints

### Agent Endpoints (authenticated via `get_current_agency`)

| Method | Path | Purpose | Stage Guard | Status Guard |
|:-------|:-----|:---------|:------------|:-------------|
| POST | `/trips/{trip_id}/documents` | Upload document | proposal/booking | — |
| GET | `/trips/{trip_id}/documents` | List documents | — | excludes `deleted` |
| GET | `/trips/{trip_id}/documents/{document_id}/download-url` | Signed URL | — | — |
| POST | `/trips/{trip_id}/documents/{document_id}/accept` | Accept | proposal/booking | `pending_review` only |
| POST | `/trips/{trip_id}/documents/{document_id}/reject` | Reject | — | `pending_review` only |
| DELETE | `/trips/{trip_id}/documents/{document_id}` | Soft-delete | — | `accepted`/`rejected` only |

### Public Customer Endpoint (no auth)

| Method | Path | Purpose | Notes |
|:-------|:-----|:---------|:------|
| POST | `/api/public/booking-collection/{token}/documents` | Upload | Token NOT consumed; returns `{id, status}` |

### Internal Endpoint

| Method | Path | Purpose |
|:-------|:-----|:---------|
| GET | `/api/internal/documents/{document_id}/download` | Serves file via HMAC-signed URL |

---

## File Validation

### Allowed types
- **Extensions:** `.pdf`, `.jpg`, `.jpeg`, `.png`
- **MIME (magic bytes):** `%PDF` → PDF, `\xff\xd8\xff` → JPEG, `\x89PNG` → PNG
- **Max size:** 10 MB (configurable via `DOCUMENT_MAX_FILE_SIZE_MB`)

### Validation flow
1. Extension check (`sanitize_extension`)
2. Streaming read in 64KB chunks with per-chunk size enforcement
3. Magic-byte detection (primary) — `_detect_mime_by_magic`
4. MIME header validation (secondary)
5. Document type enum validation

---

## Privacy Boundaries

### Excluded from trip hydration
- `booking_documents` not in `TripStore._to_dict()`
- `GET /trips/{id}` returns no document array
- Documents accessed only through dedicated endpoint

### Audit policy
**Logged (metadata only):**
```python
{
    "trip_id": str,
    "document_id": str,
    "document_type": str,
    "uploaded_by_type": str,
    "size_bytes": int,
    "mime_type": str,
    "sha256_present": True,
    "filename_present": True,
    "status": str,
    "scan_status": str,
    "review_notes_present": bool,
}
```

**Never logged:** raw filename, storage_key, filename_hash, traveler PII, file content, signed URLs

### Customer isolation
- Customer can only upload (never list/download)
- Response minimal: `{id, status}`
- `collection_token_id` links to specific token session

---

## Token Lifecycle Resolution

**The problem:** Phase 4A marks tokens `used` after booking-data submit. Phase 4B needs document upload through the same token.

**The resolution:** Customer uploads documents BEFORE final submit. Token stays active.

```
1. Customer opens collection link → GET validates token
2. Customer optionally uploads documents → POST /documents (token still active)
3. Customer fills booking data
4. Customer clicks Submit → POST /submit (consumes token)
```

No changes to Phase 4A's `mark_token_used`. The token is only consumed when the customer submits their booking data.

---

## Architectural Decisions

| Decision | Choice | Rationale |
|:---------|:-------|:----------|
| Pending data compartment | Separate `booking_documents` table | Not in trip hydration; dedicated accessors only |
| Filename storage | `filename_hash` + `filename_ext` | No plaintext; audit uses `filename_present: bool` |
| File validation | Magic bytes primary, MIME secondary | Prevents MIME spoofing attacks |
| Size enforcement | Streaming per-chunk | No OOM on oversized uploads |
| Signed URLs | document_id + operation + HMAC | No storage_key in URLs; per-document, per-operation |
| HMAC secret | Fail-fast in prod/staging | Prevents silent ephemeral secret rotation |
| Soft-delete | File retained, status=deleted | Recoverable; `storage_delete_status="retained"` |
| Scanner | NoopScanner returns `skipped` | Deterministic; no `clean`/`quarantined` confusion |
| Accept/reject | Only from `pending_review` | Clear state machine; no ambiguous transitions |
| Token lifecycle | Upload before submit | Token consumed only by booking-data submit |
| Customer response | `{id, status}` only | Minimal attack surface; no download URL |

---

## Files Changed

| File | Change |
|:-----|:-------|
| `alembic/versions/add_booking_documents.py` | New — idempotent table migration |
| `spine_api/models/tenant.py` | Add `BookingDocument` model (23 columns, 3 indexes, 3 relationships) |
| `spine_api/services/document_storage.py` | New — storage protocol + local impl + HMAC signing + fail-fast secret |
| `spine_api/services/document_service.py` | New — scanner, file validation, CRUD functions |
| `spine_api/server.py` | 6 agent + 1 public + 1 internal endpoints, 7 Pydantic models |
| `frontend/src/lib/api-client.ts` | 4 types + 7 API functions |
| `frontend/src/lib/route-map.ts` | 5 proxy route entries |
| `frontend/src/app/(agency)/workbench/OpsPanel.tsx` | Document section: upload, list, review, download, delete |
| `frontend/src/app/(public)/booking-collection/[token]/page.tsx` | Document upload section within active form |
| `tests/test_booking_documents.py` | New — 38 backend tests |

---

## Known Future Work (Not Phase 4B Debt)

- S3 storage implementation (interface ready, `NotImplementedError` stub)
- Real malware scanner (ClamAV or provider hook)
- Document thumbnails/previews
- Batch upload (multiple files at once)
- Document versioning/revision history
- Email notifications on upload/review
- Document expiry/retention policy
- OCR/text extraction from documents
- Customer email notifications

---

## Verification Commands

```bash
# Migration
cd /Users/pranay/Projects/travel_agency_agent
uv run alembic upgrade head

# Backend tests
uv run pytest tests/test_booking_documents.py -v

# Existing Phase 4A tests must still pass
uv run pytest tests/test_booking_collection.py -v

# Frontend (use local binary, NOT npx)
cd frontend && npm test -- --run

# TypeScript
cd frontend && npx tsc --noEmit

# Privacy: documents not in trip hydration
cd /Users/pranay/Projects/travel_agency_agent
grep "booking_documents" spine_api/persistence.py | grep "_to_dict"  # should find nothing

# Privacy: no original_filename column
grep "original_filename" spine_api/models/tenant.py  # should only find comment

# File storage
ls data/documents/  # verify upload creates files
```
