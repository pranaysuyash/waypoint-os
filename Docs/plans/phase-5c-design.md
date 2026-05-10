# Phase 5C: Document & Extraction Event Emission Backfill

## Context

Phase 5B established the execution event ledger with task and confirmation events. Phase 5C backfills document and extraction events into the same timeline. The schema already supports these categories (`EVENT_CATEGORIES` includes `"document"` and `"extraction"`), but no code emits them yet.

## Scope

- Add event emission to `document_service.py` (upload, accept, reject, soft_delete)
- Add event emission to `extraction_service.py` (run, apply, reject, plus per-attempt events)
- Expand metadata allowlist for new safe keys
- Add new event type constants
- Add `document_extraction_attempt` to allowed subject types
- Add `customer_submission` to allowed source values
- Best-effort emission policy (failure logged, never rolls back document/extraction operations)
- Update frontend timeline labels for document/extraction events
- Tests for all new event emissions

---

## 1. New Constants

### `ALLOWED_SUBJECT_TYPES` (add to `tenant.py`)

```python
ALLOWED_SUBJECT_TYPES = (
    "booking_task",
    "booking_confirmation",
    "booking_document",
    "document_extraction",
    "document_extraction_attempt",
)
```

### `ALLOWED_EVENT_SOURCES` (add to `tenant.py`)

```python
ALLOWED_EVENT_SOURCES = (
    "agent_action",
    "system_generation",
    "reconciliation",
    "customer_submission",
)
```

### `DOCUMENT_EVENT_TYPES` (add to `tenant.py`)

```python
DOCUMENT_EVENT_TYPES = (
    "document_uploaded",
    "document_accepted",
    "document_rejected",
    "document_deleted",
)
```

### `EXTRACTION_EVENT_TYPES` (add to `tenant.py`)

```python
EXTRACTION_EVENT_TYPES = (
    "extraction_run_started",
    "extraction_run_completed",
    "extraction_run_failed",
    "extraction_applied",
    "extraction_rejected",
    "extraction_attempt_started",
    "extraction_attempt_completed",
    "extraction_attempt_failed",
)
```

### Expanded `ALLOWED_EVENT_METADATA_KEYS`

Add these safe (non-PII) keys. No `tokens` — token counts are noise for execution timeline and already stored in extraction attempts. No `confidence_scores` dict — only `overall_confidence` scalar. No `fields_applied` — use `fields_applied_count`.

```python
ALLOWED_EVENT_METADATA_KEYS = frozenset({
    # Phase 5B
    "task_type", "confirmation_type", "document_type",
    "provider", "model", "blocker_code", "evidence_ref_count",
    # Phase 5C — document metadata
    "size_bytes", "mime_type", "uploaded_by_type", "scan_status",
    "review_notes_present", "storage_delete_status",
    # Phase 5C — extraction metadata
    "run_count", "attempt_count", "page_count",
    "overall_confidence", "field_count",
    "latency_ms", "cost_estimate_usd",
    "error_code",
    # Phase 5C — attempt metadata
    "run_number", "attempt_number", "fallback_rank",
    "fields_applied_count", "allow_overwrite",
})
```

### Expanded `FORBIDDEN_METADATA_PATTERNS`

No changes needed — already covers `filename`, `storage_key`, `signed_url`, `extracted_fields`, etc. Add explicit test that `error_summary` is rejected.

---

## 2. Event Emission Policy — Best-Effort

**Rule**: Event emission failure is logged and does NOT roll back the document/extraction operation.

**Implementation**: Wrap each `emit_event` call in a helper:

```python
async def emit_event_best_effort(
    db: AsyncSession,
    *,
    agency_id: str,
    trip_id: str,
    subject_type: str,
    subject_id: str,
    event_type: str,
    category: str,
    status_from: Optional[str],
    status_to: str,
    actor_type: str,
    actor_id: Optional[str],
    source: str,
    event_metadata: Optional[dict],
) -> None:
    try:
        await execution_event_service.emit_event(
            db,
            agency_id=agency_id,
            trip_id=trip_id,
            subject_type=subject_type,
            subject_id=subject_id,
            event_type=event_type,
            category=category,
            status_from=status_from,
            status_to=status_to,
            actor_type=actor_type,
            actor_id=actor_id,
            source=source,
            event_metadata=event_metadata,
        )
    except Exception:
        logger.exception(
            "Failed to emit execution event: type=%s subject=%s/%s",
            event_type, subject_type, subject_id,
        )
```

This helper lives in `execution_event_service.py` and is imported by document_service and extraction_service.

---

## 3. Actor/Source Mapping

### Document uploads

`uploaded_by_type` can be `"agent"` or `"customer"`. The `actor_type` field only supports `"agent"` or `"system"` — there is no customer actor model yet.

```python
if doc.uploaded_by_type == "agent":
    actor_type = "agent"
    actor_id = doc.uploaded_by_id
    source = "agent_action"
else:  # customer or traveler via collection token
    actor_type = "system"
    actor_id = None
    source = "customer_submission"
```

### Document accept/reject/delete

```python
actor_type = "agent"
actor_id = reviewed_by  # or deleted_by
source = "agent_action"
```

### Extraction run/attempt events

```python
actor_type = "system"
actor_id = None
source = "system_generation"
```

### Extraction apply/reject

```python
actor_type = "agent"
actor_id = reviewed_by
source = "agent_action"
```

---

## 4. Event Emission Points

### `document_service.py`

**`upload_document`** — after doc creation and commit:
```python
actor_type = "agent" if doc.uploaded_by_type == "agent" else "system"
actor_id = doc.uploaded_by_id if doc.uploaded_by_type == "agent" else None
source = "agent_action" if doc.uploaded_by_type == "agent" else "customer_submission"

await emit_event_best_effort(
    db, agency_id=doc.agency_id, trip_id=doc.trip_id,
    subject_type="booking_document", subject_id=doc.id,
    event_type="document_uploaded", category="document",
    status_from=None, status_to="pending_review",
    actor_type=actor_type, actor_id=actor_id, source=source,
    event_metadata={
        "document_type": doc.document_type,
        "size_bytes": doc.size_bytes,
        "mime_type": doc.mime_type,
        "uploaded_by_type": doc.uploaded_by_type,
        "scan_status": doc.scan_status,
    },
)
```

**`accept_document`** — after status change and commit:
```python
await emit_event_best_effort(
    db, agency_id=doc.agency_id, trip_id=doc.trip_id,
    subject_type="booking_document", subject_id=doc.id,
    event_type="document_accepted", category="document",
    status_from="pending_review", status_to="accepted",
    actor_type="agent", actor_id=reviewed_by, source="agent_action",
    event_metadata={
        "document_type": doc.document_type,
        "review_notes_present": notes_present,
    },
)
```

**`reject_document`** — after status change and commit:
```python
await emit_event_best_effort(
    db, agency_id=doc.agency_id, trip_id=doc.trip_id,
    subject_type="booking_document", subject_id=doc.id,
    event_type="document_rejected", category="document",
    status_from="pending_review", status_to="rejected",
    actor_type="agent", actor_id=reviewed_by, source="agent_action",
    event_metadata={
        "document_type": doc.document_type,
        "review_notes_present": notes_present,
    },
)
```

**`soft_delete_document`** — after soft delete and commit:
```python
await emit_event_best_effort(
    db, agency_id=doc.agency_id, trip_id=doc.trip_id,
    subject_type="booking_document", subject_id=doc.id,
    event_type="document_deleted", category="document",
    status_from=old_status, status_to="deleted",
    actor_type="agent", actor_id=deleted_by, source="agent_action",
    event_metadata={
        "document_type": doc.document_type,
        "storage_delete_status": "retained",
    },
)
```

### `extraction_service.py`

**`run_extraction`** — three emission points:

1. On run start:
```python
await emit_event_best_effort(
    db, agency_id=agency_id, trip_id=document.trip_id,
    subject_type="document_extraction", subject_id=extraction.id,
    event_type="extraction_run_started", category="extraction",
    status_from=None, status_to="running",
    actor_type="system", actor_id=None, source="system_generation",
    event_metadata={
        "document_type": document.document_type,
        "provider": provider_name,
        "model": model_name,
        "run_count": extraction.run_count,
    },
)
```

2. On run completion (success → pending_review):
```python
await emit_event_best_effort(
    db, agency_id=agency_id, trip_id=document.trip_id,
    subject_type="document_extraction", subject_id=extraction.id,
    event_type="extraction_run_completed", category="extraction",
    status_from="running", status_to="pending_review",
    actor_type="system", actor_id=None, source="system_generation",
    event_metadata={
        "document_type": document.document_type,
        "provider": extraction.provider_name,
        "model": extraction.model_name,
        "attempt_count": extraction.attempt_count,
        "field_count": extraction.field_count,
        "overall_confidence": extraction.overall_confidence,
        "latency_ms": extraction.latency_ms,
    },
)
```

3. On run failure (all attempts exhausted → failed):
```python
await emit_event_best_effort(
    db, agency_id=agency_id, trip_id=document.trip_id,
    subject_type="document_extraction", subject_id=extraction.id,
    event_type="extraction_run_failed", category="extraction",
    status_from="running", status_to="failed",
    actor_type="system", actor_id=None, source="system_generation",
    event_metadata={
        "document_type": document.document_type,
        "error_code": extraction.error_code,
        "attempt_count": extraction.attempt_count,
        "latency_ms": extraction.latency_ms,
    },
)
```

**Per-attempt events** — inside the extraction chain loop:

On attempt success:
```python
await emit_event_best_effort(
    db, agency_id=agency_id, trip_id=document.trip_id,
    subject_type="document_extraction_attempt", subject_id=attempt.id,
    event_type="extraction_attempt_completed", category="extraction",
    status_from=None, status_to="success",
    actor_type="system", actor_id=None, source="system_generation",
    event_metadata={
        "provider": attempt.provider_name,
        "model": attempt.model_name,
        "attempt_number": attempt.attempt_number,
        "fallback_rank": attempt.fallback_rank,
        "field_count": attempt.field_count,
        "latency_ms": attempt.latency_ms,
    },
)
```

On attempt failure:
```python
await emit_event_best_effort(
    db, agency_id=agency_id, trip_id=document.trip_id,
    subject_type="document_extraction_attempt", subject_id=attempt.id,
    event_type="extraction_attempt_failed", category="extraction",
    status_from=None, status_to="failed",
    actor_type="system", actor_id=None, source="system_generation",
    event_metadata={
        "provider": attempt.provider_name,
        "model": attempt.model_name,
        "attempt_number": attempt.attempt_number,
        "fallback_rank": attempt.fallback_rank,
        "error_code": attempt.error_code,
        "latency_ms": attempt.latency_ms,
    },
)
```

**`apply_extraction`** — after status change and booking_data update:
```python
await emit_event_best_effort(
    db, agency_id=extraction.agency_id, trip_id=extraction.trip_id,
    subject_type="document_extraction", subject_id=extraction.id,
    event_type="extraction_applied", category="extraction",
    status_from="pending_review", status_to="applied",
    actor_type="agent", actor_id=reviewed_by, source="agent_action",
    event_metadata={
        "document_type": document.document_type,
        "fields_applied_count": len(fields_to_apply),
        "allow_overwrite": allow_overwrite,
    },
)
```

**`reject_extraction`** — after status change:
```python
await emit_event_best_effort(
    db, agency_id=extraction.agency_id, trip_id=extraction.trip_id,
    subject_type="document_extraction", subject_id=extraction.id,
    event_type="extraction_rejected", category="extraction",
    status_from="pending_review", status_to="rejected",
    actor_type="agent", actor_id=reviewed_by, source="agent_action",
    event_metadata={
        "document_type": document.document_type,
    },
)
```

---

## 5. Frontend Changes

### `ExecutionTimelinePanel.tsx`

Update event type labels:
```tsx
const EVENT_LABELS: Record<string, string> = {
  // Task
  task_created: 'Task created',
  task_completed: 'Task completed',
  // ... existing ...
  // Document
  document_uploaded: 'Document uploaded',
  document_accepted: 'Document accepted',
  document_rejected: 'Document rejected',
  document_deleted: 'Document deleted',
  // Extraction
  extraction_run_started: 'Extraction started',
  extraction_run_completed: 'Extraction completed',
  extraction_run_failed: 'Extraction failed',
  extraction_applied: 'Extraction applied',
  extraction_rejected: 'Extraction rejected',
  extraction_attempt_completed: 'Attempt completed',
  extraction_attempt_failed: 'Attempt failed',
};
```

Subject type icons:
```tsx
const SUBJECT_ICONS: Record<string, ReactNode> = {
  booking_task: <CheckSquare size={14} />,
  booking_confirmation: <FileCheck size={14} />,
  booking_document: <FileText size={14} />,
  document_extraction: <ScanLine size={14} />,
  document_extraction_attempt: <Layers size={14} />,
};
```

---

## 6. Files to Modify

### Backend
- `spine_api/models/tenant.py` — add ALLOWED_SUBJECT_TYPES, ALLOWED_EVENT_SOURCES, DOCUMENT_EVENT_TYPES, EXTRACTION_EVENT_TYPES, expand ALLOWED_EVENT_METADATA_KEYS
- `spine_api/services/execution_event_service.py` — add `emit_event_best_effort` helper
- `spine_api/services/document_service.py` — add 4 emit_event_best_effort calls
- `spine_api/services/extraction_service.py` — add emit_event_best_effort calls (run start/complete/fail, apply, reject, per-attempt)

### Frontend
- `frontend/src/components/workspace/panels/ExecutionTimelinePanel.tsx` — update labels and icons for document/extraction events

---

## 7. Files to Create

### Tests
- `tests/test_document_events.py` — ~15 tests
- `tests/test_extraction_events.py` — ~17 tests

---

## 8. Test Plan (~32 tests)

### `test_document_events.py` (~15 tests)

**Emission correctness (5)**:
- Document uploaded emits `document_uploaded` with correct metadata
- Document accepted emits `document_accepted` with correct status_from/to
- Document rejected emits `document_rejected` with correct status_from/to
- Document deleted emits `document_deleted` with status_from=previous status
- All document events have category="document" and subject_type="booking_document"

**Actor/source mapping (3)**:
- Agent upload → actor_type=agent, source=agent_action
- Customer upload → actor_type=system, source=customer_submission
- Accept/reject/delete → actor_type=agent, source=agent_action

**PII boundaries (4)**:
- Upload metadata contains no filename, filename_hash, storage_key, or sha256
- Accept/reject metadata contains no review_notes content (only notes_present boolean)
- Delete metadata contains no storage_key
- error_summary absent from all document event metadata

**Best-effort policy (2)**:
- Document accept succeeds even if event emission raises
- Event emission failure is logged, does not corrupt document state

**Subject type validation (1)**:
- `booking_document` is in ALLOWED_SUBJECT_TYPES

### `test_extraction_events.py` (~17 tests)

**Emission correctness (6)**:
- Run start emits `extraction_run_started` with provider/model/run_count
- Run completion emits `extraction_run_completed` with field_count/overall_confidence
- Run failure emits `extraction_run_failed` with error_code
- Apply emits `extraction_applied` with fields_applied_count (integer)
- Reject emits `extraction_rejected`
- All extraction events have category="extraction"

**Attempt events (3)**:
- Attempt success emits `extraction_attempt_completed` with subject_type="document_extraction_attempt"
- Attempt failure emits `extraction_attempt_failed` with error_code only
- Attempt events contain provider/model/fallback_rank

**Actor/source mapping (3)**:
- Run/attempt events → actor_type=system, source=system_generation
- Apply event → actor_type=agent, source=agent_action
- Reject event → actor_type=agent, source=agent_action

**PII boundaries (3)**:
- Metadata contains no extracted_fields, no storage_key, no filename
- Metadata contains no confidence_scores dict (only overall_confidence scalar)
- fields_applied_count is an integer, never field names
- error_summary absent from all extraction event metadata

**Best-effort policy (1)**:
- Extraction run completes even if event emission raises

**Subject type validation (1)**:
- `document_extraction` and `document_extraction_attempt` are in ALLOWED_SUBJECT_TYPES

---

## 9. Non-goals

- No changes to document/extraction service logic — only adding event emission
- No new API endpoints
- No new database tables or migrations
- No changes to the timeline query (already reads from execution_events)
- No document/extraction backfill of historical data — events start from Phase 5C forward
- No token counts in event metadata (already stored in extraction attempts)

---

## 10. Implementation Order

1. `tenant.py` — add new constants (ALLOWED_SUBJECT_TYPES, ALLOWED_EVENT_SOURCES, event types, expanded metadata keys)
2. `execution_event_service.py` — add `emit_event_best_effort` helper
3. `document_service.py` — add 4 emit_event_best_effort calls with correct actor/source mapping
4. `extraction_service.py` — add emit_event_best_effort calls (run start/complete/fail, apply, reject, per-attempt)
5. `test_document_events.py` — ~15 tests
6. `test_extraction_events.py` — ~17 tests
7. `ExecutionTimelinePanel.tsx` — update labels and icons
8. Run full test suite to verify no regressions
