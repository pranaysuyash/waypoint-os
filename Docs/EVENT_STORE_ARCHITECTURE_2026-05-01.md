# EventStore Architecture — Durable Event System Before Packet Editing

**Date**: 2026-05-01
**Status**: Revised design spec (pre-implementation)
**Problem**: 6 independent logging systems, capped AuditStore, no durable unified event history. Packet fact editing blocked until a reliable event foundation exists.

---

## Core Rule

```
Current state lives in the domain object.
History lives in one durable EventStore.
UI timelines are projections from EventStore.
Execution reads current state only.
```

For this product:

| What | Where | Who reads it |
|------|-------|-------------|
| Current fact values | `trips.extracted.facts[field]` | All consumers: planners, validators, exporters, BFF mappers, decision engine |
| Durable event history | `EventStore` | Timeline UI, PacketTab "show original", learning loop, audit export |
| UI timeline projection | `EventStore` query → `GET /api/trips/{id}/timeline` | Frontend TimelinePanel |
| Packet-local snapshot (optional) | `trips.extracted.events[]` | **DEPRECATED** — keep for read compat during migration, no new writers |

**No consumer reads events as current fact values.**

---

## Current State: 6 Systems to Replace/Consolidate

| System | Storage | Cap | Future |
|--------|---------|-----|--------|
| `AuditStore` | `data/audit/events.json` (JSON array) | 10K global, silent drop | → Deprecated. Wrapped as read-compat layer during migration, then removed. |
| `RunLedger` | `data/runs/{run_id}/steps/*.json` | None per-step | → Keep (bulky step checkpoints, not general events) |
| `RunEvents` | `data/runs/{run_id}/events.jsonl` | None | → Migrate to EventStore (lifecycle events live there) |
| `extracted.events[]` | Inside trip JSON | None (per-trip) | → Deprecated for writes. Existing data displayed for old trips. No new pipeline consumers. |
| `OverrideStore` | `data/overrides/per_trip/*.jsonl` | None | → Keep (decision overrides have different semantics from general events) |
| `frontend audit types` | Unconnected design artifact | N/A | → Wire to EventStore if used, or remove |

---

## EventStore Architecture

### Storage (mirrors TripStore pattern)

**FileEventStore** (`dev default`):
- Append-only JSONL per aggregate
- `data/events/{aggregate_type}/{aggregate_id}.jsonl`
- No global cap. No silent drops.
- Each file is an append-only log for one entity (trip, run, draft, etc.)
- Read: scan file, filter by event_type if needed
- O(n) per read, but scoped to one aggregate/trip — not global

**SQLEventStore** (`production default`):
- PostgreSQL `events` table
- Indexed by `(tenant_id, aggregate_type, aggregate_id, aggregate_sequence)`
- Same schema as FileEventStore

### Event Schema

```python
@dataclass
class Event:
    event_id: str                    # evt_{hex12}
    tenant_id: str                   # agency_id — required for multi-tenant scoping and indexing
    aggregate_type: str              # "trip", "run", "draft", "followup"
    aggregate_id: str                # trip_id, run_id, draft_id
    aggregate_sequence: int          # 1-based per aggregate (line count for file, sequence for SQL)
    event_type: str                  # "packet_fact_corrected", "trip_created", ...
    actor_id: Optional[str]          # user_id or "system"
    actor_type: str                  # "user", "system", "agent"
    created_at: str                  # ISO-8601
    payload: Dict[str, Any]          # event-specific data
    visibility: str                  # "user_visible", "internal", "system_only"
    source: str                      # "manual_packet_edit", "pipeline", "intake_panel", "api"
    correlation_id: Optional[str]    # links related events (e.g., all events from one request)
    idempotency_key: Optional[str]   # required for API-originated writes; prevents duplicate on retry
    schema_version: int              # 1
```

### Key Design Decisions

#### 1. `tenant_id` Required
Every event carries `tenant_id` (agency_id). All SQL queries and indexes include it. FileEventStore includes it in the event line for cross-aggregate scanning only when explicitly needed. No event exists without a tenant scope.

#### 2. `idempotency_key` Required for API Origins
- API-originated writes (packet edits, status changes, etc.) **must** provide an `idempotency_key`.
- System pipeline events may generate deterministic keys from `run_id + stage + step`.
- SQL: unique constraint on `(tenant_id, idempotency_key)`.
- FileEventStore: before append, scan the aggregate file for the key. If found, return the existing event_id (idempotent no-op). This is O(n) per aggregate file — acceptable for dev because each aggregate file is small (one trip/run). The scan stops at first match.
- If `idempotency_key` is None for an API-originated write, the write is rejected.

#### 3. `aggregate_sequence` for Ordering
- 1-based, auto-incremented per `(tenant_id, aggregate_type, aggregate_id)`.
- FileEventStore: `aggregate_sequence = line_count + 1` at append time.
- SQL: derived via `SELECT COALESCE(MAX(aggregate_sequence), 0) + 1 FROM events WHERE tenant_id = ? AND aggregate_type = ? AND aggregate_id = ?` within transaction, or use a separate aggregate counter table.
- Timeline reads order by `aggregate_sequence ASC`.

#### 4. FileEventStore APIs — V1 Scope

**Supported in v1:**

```python
class EventStore:
    @staticmethod
    def append(event: Event) -> str:
        """Append one event. Returns event_id. Raises on write failure.
        Checks idempotency_key if present — returns existing event_id on duplicate."""

    @staticmethod
    def list_for_aggregate(tenant_id: str, aggregate_type: str, aggregate_id: str,
                           event_type: Optional[str] = None,
                           visibility: Optional[str] = None,
                           limit: int = 100) -> List[Event]:
        """List events for an aggregate, ordered by aggregate_sequence ASC.
        Scans one aggregate file — O(n) per file, acceptable for dev."""

    @staticmethod
    def get_by_id(event_id: str) -> Optional[Event]:
        """Get single event by ID.
        FileEventStore: scans all aggregate files — O(total_events). For dev only.
        SQLEventStore: indexed lookup — O(1)."""
```

**Excluded from v1 (deferred until SQL or export job):**

```text
- list_by_type(event_type) — global scan. Needed for learning loop later, not for Phase 0.
- list_by_tenant(tenant_id) — global per-tenant scan. Audit page can paginate by aggregate for now.
```

These are deferred. No code promises them for FileEventStore. SQLEventStore can add them later with proper indexes.

---

### Packet Fact Corrected Event Payload

```json
{
  "event_id": "evt_a1b2c3d4e5f6",
  "tenant_id": "agency_17",
  "aggregate_type": "trip",
  "aggregate_id": "trip_abc123",
  "aggregate_sequence": 3,
  "event_type": "packet_fact_corrected",
  "actor_id": "agent_42",
  "actor_type": "user",
  "created_at": "2026-05-01T14:00:00Z",
  "payload": {
    "field_name": "origin_city",
    "previous_slot": {
      "value": "Bangalore",
      "confidence": 0.9,
      "authority_level": "explicit_user"
    },
    "new_slot": {
      "value": "Mumbai",
      "confidence": 1.0,
      "authority_level": "manual_override",
      "extraction_mode": "manual_entry"
    },
    "requires_revalidation": true,
    "display_label": "Origin changed from Bangalore to Mumbai"
  },
  "visibility": "user_visible",
  "source": "manual_packet_edit",
  "correlation_id": "req_xyz789",
  "idempotency_key": "edit_origin_trip_abc123_20260501_140000",
  "schema_version": 1
}
```

### SQL Schema

```sql
CREATE TABLE events (
    event_id          VARCHAR(36) PRIMARY KEY,
    tenant_id         VARCHAR(36) NOT NULL,
    aggregate_type    VARCHAR(50) NOT NULL,
    aggregate_id      VARCHAR(100) NOT NULL,
    aggregate_sequence INTEGER NOT NULL,
    event_type        VARCHAR(100) NOT NULL,
    actor_id          VARCHAR(100),
    actor_type        VARCHAR(50) NOT NULL DEFAULT 'system',
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    payload           JSONB NOT NULL DEFAULT '{}',
    visibility        VARCHAR(50) NOT NULL DEFAULT 'internal',
    source            VARCHAR(100) NOT NULL DEFAULT 'unknown',
    correlation_id    VARCHAR(100),
    idempotency_key   VARCHAR(255),
    schema_version    INTEGER NOT NULL DEFAULT 1,
    UNIQUE (tenant_id, aggregate_type, aggregate_id, aggregate_sequence),
    UNIQUE (tenant_id, idempotency_key)
);

CREATE INDEX idx_events_lookup
    ON events (tenant_id, aggregate_type, aggregate_id, aggregate_sequence);
CREATE INDEX idx_events_type
    ON events (tenant_id, event_type, created_at DESC);
CREATE INDEX idx_events_tenant
    ON events (tenant_id, created_at DESC);
```

### FileEventStore Implementation

```python
class FileEventStore:
    EVENTS_DIR = DATA_DIR / "events"

    @staticmethod
    def _path(tenant_id: str, aggregate_type: str, aggregate_id: str) -> Path:
        return FileEventStore.EVENTS_DIR / tenant_id / aggregate_type / f"{aggregate_id}.jsonl"

    @staticmethod
    def append(event: Event) -> str:
        path = FileEventStore._path(event.tenant_id, event.aggregate_type, event.aggregate_id)
        path.parent.mkdir(parents=True, exist_ok=True)

        # Idempotency check
        if event.idempotency_key:
            existing = FileEventStore._find_by_idempotency_key(path, event.idempotency_key)
            if existing:
                return existing.event_id

        # Compute aggregate_sequence
        current_count = FileEventStore._count_lines(path)
        event.aggregate_sequence = current_count + 1

        with open(path, "a") as f:
            f.write(json.dumps(asdict(event)) + "\n")
        return event.event_id

    @staticmethod
    def list_for_aggregate(tenant_id: str, aggregate_type: str, aggregate_id: str,
                           event_type: Optional[str] = None,
                           visibility: Optional[str] = None,
                           limit: int = 100) -> List[Event]:
        path = FileEventStore._path(tenant_id, aggregate_type, aggregate_id)
        if not path.exists():
            return []
        events = []
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                data = json.loads(line)
                if event_type and data.get("event_type") != event_type:
                    continue
                if visibility and data.get("visibility") != visibility:
                    continue
                events.append(Event(**data))
        return events[-limit:]

    @staticmethod
    def _find_by_idempotency_key(path: Path, key: str) -> Optional[Event]:
        if not path.exists():
            return None
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                data = json.loads(line)
                if data.get("idempotency_key") == key:
                    return Event(**data)
        return None

    @staticmethod
    def _count_lines(path: Path) -> int:
        if not path.exists():
            return 0
        with open(path) as f:
            return sum(1 for line in f if line.strip())
```

---

## Single Event Recording Helper (`record_event`)

Routes must not manually dual-write to EventStore and old systems. One helper owns the write:

```python
def record_event(
    tenant_id: str,
    aggregate_type: str,
    aggregate_id: str,
    event_type: str,
    payload: dict,
    *,
    actor_id: Optional[str] = None,
    actor_type: str = "system",
    visibility: str = "internal",
    source: str = "unknown",
    correlation_id: Optional[str] = None,
    idempotency_key: Optional[str] = None,
) -> Event:
    """
    Record one event. Writes to EventStore.
    During migration phase, also writes to AuditStore if the event type was previously logged there.
    After migration completes, AuditStore write is removed.
    """
    event = Event(
        event_id=f"evt_{uuid4().hex[:12]}",
        tenant_id=tenant_id,
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
        aggregate_sequence=0,  # assigned by EventStore.append
        event_type=event_type,
        actor_id=actor_id,
        actor_type=actor_type,
        created_at=datetime.now(timezone.utc).isoformat(),
        payload=payload,
        visibility=visibility,
        source=source,
        correlation_id=correlation_id,
        idempotency_key=idempotency_key,
        schema_version=1,
    )
    EventStore.append(event)

    # Migration dual-write: remove this after timeline reads from EventStore
    if event_type in _AUDITSTORE_EVENT_TYPES:
        AuditStore.log_event(event_type, actor_id or "system", {
            "trip_id": aggregate_id if aggregate_type == "trip" else None,
            "draft_id": aggregate_id if aggregate_type == "draft" else None,
            "event_store_id": event.event_id,
            **payload,
        })

    return event
```

**Dual-write exit criteria** (all must be met before `_AUDITSTORE_EVENT_TYPES` list is removed):
1. `GET /api/trips/{id}/timeline` reads from EventStore, not AuditStore
2. `/audit` endpoint reads from EventStore, not AuditStore
3. All existing AuditStore event writers have been migrated to `record_event()`
4. No frontend component depends on AuditStore-specific event shapes
5. Tests prove all historical events are queryable from EventStore

---

## Transaction Model

### SQL (Production)

Packet fact edit runs as a single DB transaction:

```sql
BEGIN;
  UPDATE trips SET extracted = jsonb_set(...) WHERE id = 'trip_abc';
  INSERT INTO events (...) VALUES (...);
COMMIT;
```

Both the state update and the event insert succeed or fail together. This is the production path and is the only path that can be production-approved for packet editing.

### FileEventStore (Dev Only)

Non-atomic: trip state update and event append are separate file writes. If event append fails after state update succeeds:
- Trip is updated (state change applied).
- Event loss is logged.
- Response reports partial failure.
- State update is NOT rolled back (no cross-file transaction primitive for FileEventStore).

**Packet editing cannot be production-approved until SQLEventStore + SQLTripStore share a transaction path.** FileEventStore is for local development only.

---

## RunLedger vs EventStore

| System | Stores | Consumers | Future |
|--------|--------|-----------|--------|
| `RunLedger` | Pipeline step checkpoints: full packet.json, validation.json, decision.json, strategy.json | `GET /runs/{id}` (full result), `GET /runs/{id}/steps/{name}` (individual step) | **Keep**. These are bulky artifacts, not events. Do not store full state snapshots in EventStore payload. |
| `EventStore` | Lifecycle events: `run_started`, `pipeline_stage_entered`, `pipeline_stage_completed`, `run_completed`, `run_blocked` | Timeline UI, audit page, future learning loop | **Receive pipeline lifecycle events** via `record_event()`. |

RunLedger checkpoints remain where they are. Only the lightweight lifecycle events (currently in `RunEvents`) migrate to EventStore.

---

## `extracted.events[]` Deprecation

| What | When |
|------|------|
| Current state | `CanonicalPacket.set_fact()` emits `fact_set` into `extracted.events[]`. These are internal pipeline debug events. No product consumer reads them. |
| Phase 0 (EventStore build) | No change. Existing `fact_set` events still written and serialized. |
| Phase 1 (dual-write) | No new code reads `extracted.events[]`. All new event producers use `record_event()` → EventStore. |
| Phase 4 (deprecate) | `CanonicalPacket` stops serializing `events[]` into `to_dict()` output. Existing trips retain their historical `extracted.events[]` for display. No new events appended. |
| After migration | PacketTab "show original" reads from EventStore, not `extracted.events[]`. |

**Key rule**: `fact_set` events are debug/internal only. They are NOT part of the product audit history. `packet_fact_corrected` (in EventStore) IS part of the product audit history. These are separate event types for different consumers.

---

## Migration Plan (Revised)

### Phase 0: Build EventStore (no existing consumers change)

1. Create `Event` model + `FileEventStore` + `SQLEventStore`
2. Add SQLAlchemy `EventModel` for events table (mirrors Trip pattern)
3. Create `record_event()` helper
4. Wire `EventStore` into app startup (`EVENTSTORE_BACKEND` env var)
5. Write EventStore tests
6. Existing systems (AuditStore, RunEvents, RunLedger, extracted.events) untouched

### Phase 1: Record new events to EventStore

1. Replace `AuditStore.log_event(...)` calls with `record_event(...)` for all event types.
2. `record_event()` dual-writes to EventStore + AuditStore during migration.
3. Pipeline lifecycle events (RunEvents) move to EventStore via `record_event()`.
4. Verify both stores receive the same data.
5. No consumers switch yet.

### Phase 2: Timeline reads from EventStore

1. Update `GET /api/trips/{id}/timeline` to read from `EventStore.list_for_aggregate(tenant_id, "trip", trip_id, visibility="user_visible")`.
2. Adapt `TimelineEventMapper` to produce `TimelineEvent` objects from EventStore data.
3. Add `TimelineEvent.field_changes` support for `packet_fact_corrected` events.
4. Keep AuditStore as fallback during migration.
5. Frontend TimelinePanel unchanged.

### Phase 3: Deprecate AuditStore for timeline

1. Verify all timeline consumers read from EventStore.
2. Remove AuditStore dual-write from `record_event()`.
3. AuditStore file retained for manual inspection.

### Phase 4: Deprecate extracted.events[]

1. `CanonicalPacket` stops serializing `events[]` into `to_dict()`.
2. PacketTab "show original" reads from EventStore.
3. Existing `extracted.events[]` data still displayed for old trips.
4. No new code reads or writes `extracted.events[]`.

---

## Packet Facts Editing: How It Uses EventStore

Once EventStore exists, `PATCH /api/trips/{id}/packet-facts`:

1. Build payload with `field_name`, `previous_slot`, `new_slot`.
2. Update `extracted.facts[field]` with `manual_override` authority.
3. Remove matching unknowns.
4. Set `validation_stale: true`.
5. Persist trip (SQL: within same transaction as event insert).
6. Call `record_event(tenant_id, "trip", trip_id, "packet_fact_corrected", payload, ...)`.
7. Return updated trip.

Read paths:
- **Timeline UI**: `EventStore.list_for_aggregate(tenant_id, "trip", trip_id, event_type="packet_fact_corrected")` → displayed in timeline.
- **PacketTab "show original"**: Same query, extract `previous_slot` from latest matching event.
- **Learning loop (future)**: `EventStore.list_for_aggregate(tenant_id, "trip", trip_id, event_type="packet_fact_corrected")` across all trips → export as correction dataset.

No consumer reads events as current truth. Events are never used by planners, validators, exporters, or BFF mappers.

---

## Failure Behavior

| Scenario | Action |
|----------|--------|
| SQL: state update + event insert (same transaction) | Atomic: both succeed or both fail. No partial state. |
| FileEventStore: state update succeeds, event append fails | Trip updated. Event loss logged. Response reports partial failure. Do NOT roll back state (no cross-file atomicity). Dev only — not production-approved for packet editing. |
| State update fails, event not attempted | Return error. Consistent state. |
| Event append succeeds, duplicate idempotency_key | EventStore returns existing event_id. No duplicate. State update proceeds. |
| Event append succeeds, state update never called | Bug in caller. Orphan event in EventStore. Detectable by checking current facts don't match the event's `new_slot`. Acceptable gap — no silent data corruption. |

---

## Editable Field Whitelist (for when Packet Editing ships)

| Field | Type | Validation |
|-------|------|-----------|
| `origin_city` | `string` | Known city check (geography.py) |
| `destination_candidates` | `string[]` | Each must be known destination |
| `destination_status` | `string` | Enum: definite, semi_open, open |
| `date_window` | `string` | Non-empty |
| `date_start` | `string` (ISO) | Regex: `\d{4}-\d{2}-\d{2}` |
| `date_end` | `string` (ISO) | Regex: `\d{4}-\d{2}-\d{2}` |
| `party_size` | `integer` | > 0 |
| `party_composition` | `object` | Keys subset of: adults, children, elderly, teens |
| `child_ages` | `number[]` | Each > 0 |
| `budget_raw_text` | `string` | If set, also parse budget_min/max |
| `budget_min` | `integer\|null` | >= 0 |
| `budget_max` | `integer\|null` | >= 0 |
| `budget_currency` | `string` | Enum: INR, USD, SGD, EUR, GBP |

Reject unknown fields. Reject type mismatches. Accept partial updates (only specified fields change).

---

## Tests (Phase 0: EventStore alone)

| Test | What it covers |
|------|---------------|
| `FileEventStore.append_and_list` | Event is written, readable by list_for_aggregate |
| `FileEventStore.list_empty_aggregate` | Returns empty list for non-existent aggregate |
| `FileEventStore.filter_by_event_type` | Only matching events returned |
| `FileEventStore.filter_by_visibility` | Only matching visibility returned |
| `FileEventStore.limit` | Returns only last N events |
| `FileEventStore.aggregate_sequence_auto` | Sequence increments: 1, 2, 3 per aggregate |
| `FileEventStore.idempotency_dedup` | Same key written twice → first event_id returned, no duplicate |
| `FileEventStore.idempotency_cross_aggregate` | Same key on different aggregates: both written |
| `FileEventStore.tenant_isolation` | Different tenants' events don't mix |
| `FileEventStore.append_twice` | Two events for same aggregate, both returned in sequence order |
| `SQLEventStore.append_and_list` | Same tests for SQL backend |
| `SQLEventStore.unique_idempotency_key` | Duplicate key raises integrity error |
| `SQLEventStore.indexed_lookup` | get_by_id returns in O(1) |
| `record_event.dual_write` | Event written to both EventStore and AuditStore during migration |
| `record_event.no_audit_write` | After migration flag off, AuditStore not written |
| `EventStore.event_id_unique` | No two events share an event_id |

---

## Summary: What This Unlocks

```
Without EventStore:
  AuditStore capped → events silently lost
  extracted.events[] fragmented → no cross-trip queries
  PacketTab editing blocked → no correction path
  Learning loop blocked → no correction dataset
  6 systems → confusion about which is canonical

With EventStore:
  One append API for all product changes
  No silent data loss
  Timeline reads from EventStore
  PacketTab editing writes to EventStore → history preserved
  Learning loop queries corrections from EventStore
```

---

## Appendix: Current Event Types Migration Map

| Current Event Type | Current System | aggregate_type | event_type | Notes |
|-------------------|---------------|----------------|------------|-------|
| `trip_created` | AuditStore | `trip` | `trip_created` | |
| `trip_assigned` | AuditStore | `trip` | `trip_assigned` | |
| `trip_status_changed` | AuditStore | `trip` | `trip_status_changed` | |
| `spine_stage_transition` | AuditStore | `run` | `pipeline_stage_transition` | |
| `run_started` | RunEvents | `run` | `run_started` | |
| `pipeline_stage_entered` | RunEvents | `run` | `pipeline_stage_entered` | |
| `run_completed` | RunEvents | `run` | `run_completed` | |
| `override_created` | AuditStore | `trip` | `override_created` | Decision-level overrides stay in OverrideStore |
| `fact_set` | extracted.events | `trip` | `fact_set` | Debug/internal only. Deprecated. No new consumers. |
| `packet_fact_corrected` | NEW | `trip` | `packet_fact_corrected` | First consumer of EventStore |
