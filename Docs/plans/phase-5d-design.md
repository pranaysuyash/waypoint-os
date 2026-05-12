# Phase 5D: Execution Timeline UX Hardening + Event Integrity Controls

## Context

Phase 5C completed the event emission pipeline — all task, confirmation, document, and extraction lifecycle events flow into `execution_events`. Phase 5D hardens the timeline for daily operator use: adds grouping, filtering, an event detail drawer, and backend event integrity validation.

## Scope

- Timeline grouping by date (run grouping deferred)
- Actor-type filter (agent actions vs system events)
- Event detail drawer with allowlisted metadata only (frontend defense-in-depth)
- Backend validation: subject_type, source, category, event_type/category pairing, actor_type
- `emit_event_best_effort` semantics: validate BEFORE savepoint, catch DB errors only
- Router validation for actor_type query param
- Redaction tests for rendered timeline
- Empty/loading/error states (already exist, validate and extend)

## Non-goals

- No new business workflow
- No supplier API, payments, messaging, or customer portal
- No historical data migration
- No changes to event emission logic in document/extraction/confirmation services
- No run grouping within date groups (deferred to later phase if operators need it)

---

## 1. Backend: Event Integrity Validation

### Add validation to `emit_event()`

Currently `_validate_metadata()` checks keys. Phase 5D adds validation for the other fields:

```python
async def emit_event(db, *, ...):
    _validate_subject_type(subject_type)
    _validate_source(source)
    _validate_category(event_category)
    _validate_event_type_category(event_type, event_category)
    _validate_actor_type(actor_type)
    _validate_metadata(event_metadata)
    ...
```

### New validation functions

```python
def _validate_subject_type(subject_type: str) -> None:
    if subject_type not in ALLOWED_SUBJECT_TYPES:
        raise ValueError(f"Invalid subject_type: {subject_type}")

def _validate_source(source: str) -> None:
    if source not in ALLOWED_EVENT_SOURCES:
        raise ValueError(f"Invalid source: {source}")

def _validate_category(category: str) -> None:
    if category not in EVENT_CATEGORIES:
        raise ValueError(f"Invalid event_category: {category}")

def _validate_event_type_category(event_type: str, category: str) -> None:
    """Validate event_type is known AND matches the declared category."""
    valid_types = {
        "task": TASK_EVENT_TYPES,
        "confirmation": CONFIRMATION_EVENT_TYPES,
        "document": DOCUMENT_EVENT_TYPES,
        "extraction": EXTRACTION_EVENT_TYPES,
    }
    allowed = valid_types.get(category)
    if allowed is None:
        raise ValueError(f"Unknown event_category: {category}")
    if event_type not in allowed:
        raise ValueError(f"event_type '{event_type}' not valid for category '{category}'")

def _validate_actor_type(actor_type: str) -> None:
    if actor_type not in ALLOWED_ACTOR_TYPES:
        raise ValueError(f"Invalid actor_type: {actor_type}")
```

### Add `ALLOWED_ACTOR_TYPES` to `tenant.py`

```python
ALLOWED_ACTOR_TYPES = ("agent", "system")
```

### Semantic rule: validation errors raise, DB errors are best-effort

Validation errors are programmer bugs. They MUST raise `ValueError` immediately, even through `emit_event_best_effort`. DB insert failures (table missing, constraint violation) are operational and should be swallowed.

### Corrected `emit_event_best_effort`

Validation runs BEFORE the savepoint. The savepoint/try catches only database errors:

```python
from sqlalchemy.exc import SQLAlchemyError

async def emit_event_best_effort(db, *, ...):
    # Validate inputs before touching the DB.
    # These raise ValueError on programmer bugs.
    _validate_subject_type(subject_type)
    _validate_source(source)
    _validate_category(event_category)
    _validate_event_type_category(event_type, event_category)
    _validate_actor_type(actor_type)
    _validate_metadata(event_metadata)

    try:
        async with db.begin_nested():
            await _insert_event_row(db, ...)
    except SQLAlchemyError:
        logger.exception(
            "Failed to emit execution event: type=%s subject=%s/%s",
            event_type, subject_type, subject_id,
        )
```

Key changes from current implementation:

1. **Validation runs before `try/savepoint`** — `ValueError` from validators is never caught
2. **Catches `SQLAlchemyError` only** — not generic `Exception`
3. **Inserts via `_insert_event_row()`** — internal function that creates the row without re-validating (validation already done above)

### Internal `_insert_event_row()`

Extracts the row-creation logic from `emit_event()` so `emit_event_best_effort()` can skip double validation:

```python
async def _insert_event_row(
    db: AsyncSession,
    *,
    agency_id: str,
    trip_id: str,
    subject_type: str,
    subject_id: str,
    event_type: str,
    event_category: str,
    status_from: Optional[str],
    status_to: str,
    actor_type: str,
    actor_id: Optional[str],
    source: str,
    event_metadata: Optional[dict],
) -> ExecutionEvent:
    """Create and flush an ExecutionEvent row. No validation — caller must validate."""
    event = ExecutionEvent(
        agency_id=agency_id,
        trip_id=trip_id,
        subject_type=subject_type,
        subject_id=subject_id,
        event_type=event_type,
        event_category=event_category,
        status_from=status_from,
        status_to=status_to,
        actor_type=actor_type,
        actor_id=actor_id,
        source=source,
        event_metadata=event_metadata,
    )
    db.add(event)
    await db.flush()
    return event
```

`emit_event()` becomes: validate all fields → call `_insert_event_row()`.

### Impact on existing callers

All callers of `emit_event_best_effort()` in document_service, extraction_service, and confirmation_service are unaffected — they already pass valid values. The validators confirm correctness; they do not change behavior.

---

## 2. Backend: Timeline API Enhancements

### Add `actor_type` filter to `get_timeline()`

```python
async def get_timeline(
    db: AsyncSession,
    trip_id: str,
    agency_id: str,
    category: Optional[str] = None,
    actor_type: Optional[str] = None,
) -> TimelineResult:
```

Query adds:
```python
if actor_type:
    q = q.where(ExecutionEvent.actor_type == actor_type)
```

### Add `actor_type` query param to router — WITH validation

```python
@router.get("/{trip_id}/execution-timeline")
async def get_execution_timeline(
    trip_id: str,
    category: Optional[str] = None,
    actor_type: Optional[str] = None,
    agency_id: str = Depends(get_current_agency_id),
    membership=require_permission("trips:read"),
    db: AsyncSession = Depends(get_rls_db),
):
    if actor_type is not None and actor_type not in ("agent", "system"):
        raise HTTPException(status_code=422, detail=f"Invalid actor_type: {actor_type}")
    result = await execution_event_service.get_timeline(
        db, trip_id, agency_id, category=category, actor_type=actor_type,
    )
    ...
```

Router rejects invalid `actor_type` with 422. Does NOT pass arbitrary values to the query layer.

### Response stays the same shape

No new fields. The `ExecutionTimelineEvent` type already contains all needed data.

---

## 3. Frontend: Timeline Grouping

### Group events by date (day grouping only, no run grouping)

Events already have `timestamp`. Group by date header:

```tsx
const groupedEvents = useMemo(() => {
    const groups: Record<string, ExecutionTimelineEvent[]> = {};
    for (const event of events) {
        const date = event.timestamp.split('T')[0]; // YYYY-MM-DD
        if (!groups[date]) groups[date] = [];
        groups[date].push(event);
    }
    return groups;
}, [events]);
```

Render with date headers between groups:
```tsx
{Object.entries(groupedEvents).map(([date, dateEvents]) => (
    <div key={date}>
        <div className="text-[10px] text-zinc-500 px-2 py-1">{formatDate(date)}</div>
        {dateEvents.map(event => <TimelineRow key={...} event={event} />)}
    </div>
))}
```

### Run grouping: explicitly deferred

If operators later report noisy extraction events within a date, grouping by `subject_id` within extraction events can be added. Not in Phase 5D.

---

## 4. Frontend: Actor Type Filter

### Add actor filter chips alongside category chips

```tsx
const ACTOR_FILTERS = [
    { key: 'all', label: 'All actors' },
    { key: 'agent', label: 'Agent actions' },
    { key: 'system', label: 'System events' },
];
```

When active, passes `actor_type` query param to API.

---

## 5. Frontend: Event Detail Drawer (Defense-in-Depth)

### Frontend allowlist — only render keys in METADATA_LABELS

The backend allowlist guarantees safety at write time. The frontend adds a second layer: only keys present in `METADATA_LABELS` are rendered. This catches old rows, test fixtures, or future bugs.

```tsx
const METADATA_LABELS: Record<string, string> = {
    task_type: "Task type",
    confirmation_type: "Confirmation type",
    document_type: "Document type",
    provider: "Provider",
    model: "Model",
    blocker_code: "Blocker",
    evidence_ref_count: "Evidence refs",
    size_bytes: "File size",
    mime_type: "MIME type",
    uploaded_by_type: "Uploaded by",
    scan_status: "Scan status",
    review_notes_present: "Has notes",
    storage_delete_status: "Storage status",
    run_count: "Run count",
    attempt_count: "Attempt count",
    overall_confidence: "Confidence",
    field_count: "Fields found",
    latency_ms: "Latency",
    cost_estimate_usd: "Cost",
    error_code: "Error code",
    attempt_number: "Attempt #",
    fallback_rank: "Fallback rank",
    fields_applied_count: "Fields applied",
    allow_overwrite: "Overwrite allowed",
};

const SAFE_METADATA_KEYS = new Set(Object.keys(METADATA_LABELS));
```

### Filter before rendering

```tsx
function TimelineRow({ event }: { event: ExecutionTimelineEvent }) {
    const [expanded, setExpanded] = useState(false);
    // ...existing rendering...

    {expanded && event.event_metadata && (
        <div className="ml-6 mt-1 space-y-0.5">
            {Object.entries(event.event_metadata)
                .filter(([key]) => SAFE_METADATA_KEYS.has(key))
                .map(([key, value]) => (
                    <div key={key} className="flex gap-2 text-[10px]">
                        <span className="text-zinc-500">{METADATA_LABELS[key]}</span>
                        <span className="text-zinc-300">{formatMetadataValue(key, value)}</span>
                    </div>
                ))}
        </div>
    )}
}
```

### `formatMetadataValue` — safe formatting

```tsx
function formatMetadataValue(key: string, value: unknown): string {
    if (value === null || value === undefined) return "—";
    if (key === "size_bytes") return `${(Number(value) / 1024).toFixed(1)} KB`;
    if (key === "latency_ms") return `${value}ms`;
    if (key === "cost_estimate_usd" && value != null) return `$${Number(value).toFixed(4)}`;
    if (key === "overall_confidence" && value != null) return `${Math.round(Number(value) * 100)}%`;
    if (typeof value === "boolean") return value ? "Yes" : "No";
    return String(value);
}
```

---

## 6. Files to Modify

### Backend
- `spine_api/models/tenant.py` — add `ALLOWED_ACTOR_TYPES`
- `spine_api/services/execution_event_service.py` — add 5 validation functions, refactor `emit_event()` to validate then insert, refactor `emit_event_best_effort()` to validate before savepoint and catch `SQLAlchemyError` only, add `_insert_event_row()`, add `actor_type` filter to `get_timeline()`
- `spine_api/routers/confirmations.py` — add `actor_type` query param with validation to timeline endpoint

### Frontend
- `frontend/src/components/workspace/panels/ExecutionTimelinePanel.tsx` — grouping, actor filter, detail drawer with frontend allowlist

---

## 7. Files to Create

### Tests
- `tests/test_event_integrity.py` — ~15 tests for validation functions + best-effort semantics
- `frontend/src/components/workspace/panels/__tests__/ExecutionTimelinePanel.phase5d.test.tsx` — ~12 tests

---

## 8. Test Plan (~27 tests)

### `test_event_integrity.py` (~15 tests)

**Subject type validation (2)**:
- Valid subject types accepted
- Invalid subject_type raises ValueError

**Source validation (2)**:
- Valid sources accepted
- Invalid source raises ValueError

**Category validation (2)**:
- Valid categories accepted
- Invalid category raises ValueError

**Event type/category pairing (3)**:
- task event_type with task category accepted
- confirmation event_type with confirmation category accepted
- extraction event_type with task category rejected

**Unknown event type (1)**:
- `event_type="made_up_event"`, category="task" raises ValueError

**Actor type validation (2)**:
- Valid actor types accepted
- Invalid actor_type raises ValueError

**Best-effort semantics (3)**:
- `emit_event_best_effort` with invalid subject_type raises ValueError (NOT swallowed)
- `emit_event_best_effort` with invalid metadata key raises ValueError (NOT swallowed)
- `emit_event_best_effort` with DB insert failure is swallowed and logged

### `ExecutionTimelinePanel.phase5d.test.tsx` (~12 tests)

**Grouping (2)**:
- Events grouped by date with date headers
- Single-day events show one header

**Actor filter (2)**:
- Actor filter chips rendered
- Clicking agent filter calls API with actor_type=agent

**Detail drawer (4)**:
- Clicking event row expands metadata
- Metadata keys rendered with human labels
- Only SAFE_METADATA_KEYS are rendered (arbitrary keys filtered)
- Frontend redaction: metadata includes supplier_name/passport_number/storage_key → drawer does NOT render those keys or values

**Empty/error states (2)**:
- Empty state message
- Error state with retry

**Redaction sentinel (1)**:
- Rendered timeline contains zero PII patterns (supplier_name, confirmation_number, filename, storage_key, extracted_fields, passport_number, error_summary)

**Router validation (1)**:
- Invalid actor_type query param returns 422

---

## 9. Implementation Order

1. `tenant.py` — add `ALLOWED_ACTOR_TYPES`
2. `execution_event_service.py` — add 5 validation functions, extract `_insert_event_row()`, refactor `emit_event()` and `emit_event_best_effort()`, add `actor_type` filter to `get_timeline()`
3. `confirmations.py` router — add `actor_type` query param with validation
4. `test_event_integrity.py` — ~15 tests
5. `ExecutionTimelinePanel.tsx` — grouping, actor filter, detail drawer with frontend allowlist
6. `ExecutionTimelinePanel.phase5d.test.tsx` — ~12 tests
7. Run full regression suite

---

## 10. Verification

1. `pytest tests/test_event_integrity.py -v` — all pass
2. `pytest tests/test_document_events.py tests/test_extraction_events.py tests/test_confirmation_service.py tests/test_execution_event_service.py -v` — no regressions
3. `vitest run` — all frontend tests pass
4. `tsc --noEmit` — zero errors
5. Manual: create document, run extraction, verify timeline shows grouped events with correct metadata in drawer
