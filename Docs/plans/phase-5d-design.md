# Phase 5D: Execution Timeline UX Hardening + Event Integrity Controls

## Context

Phase 5C completed the event emission pipeline — all task, confirmation, document, and extraction lifecycle events flow into `execution_events`. Phase 5D hardens the timeline for daily operator use: adds grouping, filtering, an event detail drawer, and backend event integrity validation.

## Scope

- Timeline grouping by day and run
- Actor-type filter (agent actions vs system events)
- Event detail drawer with allowlisted metadata only
- Backend validation: subject_type, source, category, event_type/category pairing
- Redaction tests for rendered timeline
- Empty/loading/error states (already exist, validate and extend)

## Non-goals

- No new business workflow
- No supplier API, payments, messaging, or customer portal
- No historical data migration
- No changes to event emission logic

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
    valid_types = {
        "task": TASK_EVENT_TYPES,
        "confirmation": CONFIRMATION_EVENT_TYPES,
        "document": DOCUMENT_EVENT_TYPES,
        "extraction": EXTRACTION_EVENT_TYPES,
    }
    allowed = valid_types.get(category, ())
    if event_type not in allowed:
        raise ValueError(f"event_type '{event_type}' not valid for category '{category}'")
```

### Add `actor_type` validation

```python
ALLOWED_ACTOR_TYPES = ("agent", "system")

def _validate_actor_type(actor_type: str) -> None:
    if actor_type not in ALLOWED_ACTOR_TYPES:
        raise ValueError(f"Invalid actor_type: {actor_type}")
```

### Add to `tenant.py`

```python
ALLOWED_ACTOR_TYPES = ("agent", "system")
```

### Impact on `emit_event_best_effort`

Validation errors are programmer errors, not runtime failures. They should NOT be caught by `emit_event_best_effort`. The savepoint isolation catches only DB-level errors (table missing, constraint violation). Validation `ValueError`s will bubble up through the savepoint and be caught by the outer `try/except`, which is correct — a validation error means the calling code has a bug.

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

### Add `actor_type` query param to router

`GET /api/trips/{trip_id}/execution-timeline?category=task&actor_type=agent`

Both params optional. `actor_type` values: `agent`, `system`.

### Response stays the same shape

No new fields. The `ExecutionTimelineEvent` type already contains all needed data.

---

## 3. Frontend: Timeline Grouping

### Group events by date

Events already have `timestamp`. Group by date header:

```tsx
// In ExecutionTimelinePanel
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

## 5. Frontend: Event Detail Drawer

### Click event row to expand metadata

```tsx
function TimelineRow({ event }: { event: ExecutionTimelineEvent }) {
    const [expanded, setExpanded] = useState(false);
    // ...existing rendering...

    {expanded && event.event_metadata && (
        <div className="ml-6 mt-1 space-y-0.5">
            {Object.entries(event.event_metadata).map(([key, value]) => (
                <div key={key} className="flex gap-2 text-[10px]">
                    <span className="text-zinc-500">{METADATA_LABELS[key] ?? key}</span>
                    <span className="text-zinc-300">{formatMetadataValue(key, value)}</span>
                </div>
            ))}
        </div>
    )}
}
```

### Metadata labels

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

No PII values can appear here — the backend `_validate_metadata()` allowlist already guarantees only safe keys reach the database.

---

## 6. Files to Modify

### Backend
- `spine_api/models/tenant.py` — add `ALLOWED_ACTOR_TYPES`
- `spine_api/services/execution_event_service.py` — add validation functions, add `actor_type` filter to `get_timeline()`
- `spine_api/routers/confirmations.py` — add `actor_type` query param to timeline endpoint

### Frontend
- `frontend/src/components/workspace/panels/ExecutionTimelinePanel.tsx` — grouping, actor filter, detail drawer

---

## 7. Files to Create

### Tests
- `tests/test_event_integrity.py` — ~12 tests for validation functions
- `frontend/src/components/workspace/panels/__tests__/ExecutionTimelinePanel.phase5d.test.tsx` — ~10 tests

---

## 8. Test Plan (~22 tests)

### `test_event_integrity.py` (~12 tests)

**Subject type validation (2)**:
- Valid subject types accepted
- Invalid subject_type raises ValueError

**Source validation (2)**:
- Valid sources accepted
- Invalid source raises ValueError

**Category validation (2)**:
- Valid categories accepted
- Invalid category raises ValueError

**Event type/category pairing (4)**:
- task event_type with task category accepted
- confirmation event_type with confirmation category accepted
- document event_type with document category accepted
- extraction event_type with task category rejected

**Actor type validation (2)**:
- Valid actor types accepted
- Invalid actor_type raises ValueError

**Integration (1)**:
- emit_event with invalid subject_type raises even through best-effort wrapper

### `ExecutionTimelinePanel.phase5d.test.tsx` (~10 tests)

**Grouping (2)**:
- Events grouped by date with date headers
- Single-day events show one header

**Actor filter (2)**:
- Actor filter chips rendered
- Clicking agent filter calls API with actor_type=agent

**Detail drawer (3)**:
- Clicking event row expands metadata
- Metadata keys rendered with human labels
- No PII in rendered metadata (sentinel test)

**Empty/error states (2)**:
- Empty state message
- Error state with retry

**Redaction (1)**:
- Rendered timeline contains zero PII patterns (supplier_name, confirmation_number, filename, storage_key, extracted_fields, passport_number, error_summary)

---

## 9. Implementation Order

1. `tenant.py` — add `ALLOWED_ACTOR_TYPES`
2. `execution_event_service.py` — add 5 validation functions + `actor_type` filter
3. `confirmations.py` router — add `actor_type` query param
4. `test_event_integrity.py` — ~12 tests
5. `ExecutionTimelinePanel.tsx` — grouping, actor filter, detail drawer
6. `ExecutionTimelinePanel.phase5d.test.tsx` — ~10 tests
7. Run full regression suite

---

## 10. Verification

1. `pytest tests/test_event_integrity.py -v` — all pass
2. `pytest tests/test_document_events.py tests/test_extraction_events.py tests/test_confirmation_service.py tests/test_execution_event_service.py -v` — no regressions
3. `vitest run` — all frontend tests pass
4. `tsc --noEmit` — zero errors
5. Manual: create document, run extraction, verify timeline shows grouped events with correct metadata in drawer
