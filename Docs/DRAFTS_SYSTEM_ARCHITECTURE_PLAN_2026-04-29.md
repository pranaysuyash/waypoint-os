# Drafts System Architecture — First Principles Analysis & Plan

**Date:** 2026-04-29  
**Context:** Workbench auto-tab-switch fix + comprehensive history/log capture + Drafts as first-class persistent workspace  
**Stakeholders:** Engineering (agent), Product (Pranay)  
**Status:** Architecture confirmed, ready for implementation

---

## Table of Contents

1. [Problem Statement](#1-problem-statement)
2. [What Was Implemented Today](#2-what-was-implemented-today)
3. [Storage Medium Decision](#3-storage-medium-decision)
4. [User Answers & Decisions](#4-user-answers--decisions)
5. [The "Draft Linking/Merging" Requirement](#5-the-draft-linkingmerging-requirement)
6. [Proposed Architecture](#6-proposed-architecture)
7. [Data Model](#7-data-model)
8. [API Surface](#8-api-surface)
9. [Audit Integration Strategy](#9-audit-integration-strategy)
10. [Frontend Changes](#10-frontend-changes)
11. [Implementation Phases](#11-implementation-phases)
12. [Open Risks & Mitigations](#12-open-risks--mitigations)

---

## 1. Problem Statement

### Original Pain Point
When running a scenario in the Workbench, if the pipeline ends in `blocked` or `failed`, the UI shows errors but the user stays on the current tab. The errors are actually rendered in the `Trip Details` (packet) tab, but nothing tells the user to look there. As a developer, the user knew to check other tabs — but this is poor UX for any operator.

### Expanded Vision: The Drafts System
The user recognized that solving the tab-switch problem opens a larger product opportunity: **the Workbench should not be ephemeral**. Agents should be able to save incomplete work as drafts, return to it later, and have a complete audit trail from the very first customer message through final trip creation.

---

## 2. What Was Implemented Today

### 2.1 Auto-Tab-Switch Fix
**File:** `frontend/src/app/workbench/page.tsx`  
**Change:** Added a `useEffect` that watches `spineRunState` transitions. When the run transitions into `blocked`, it auto-switches to the `packet` tab. When it transitions into `failed`, it switches to the tab matching `stage_at_failure`.

**Code added (lines ~240-275 in page.tsx):**
```tsx
// Auto-switch to the tab containing errors when a run ends in blocked/failed state.
const prevRunStateRef = useRef<string | null>(null);
useEffect(() => {
  const currentState = spineRunState?.state ?? null;
  const prevState = prevRunStateRef.current;

  if (currentState !== prevState && (currentState === 'blocked' || currentState === 'failed')) {
    if (currentState === 'blocked') {
      handleTabChange('packet');
    } else if (currentState === 'failed') {
      const stage = spineRunState?.stage_at_failure;
      const stageToTab = { packet: 'packet', validation: 'packet', decision: 'decision', strategy: 'strategy', safety: 'safety' };
      if (stageToTab[stage]) handleTabChange(stageToTab[stage]);
    }
  }
  prevRunStateRef.current = currentState;
}, [spineRunState, handleTabChange]);
```

**Verification:** TypeScript compilation passes (no new errors introduced by this change).

---

## 3. Storage Medium Decision

> **⚠️ ADR Note — Contradiction Resolution (2026-04-29):**
>
> This document previously recommended **file-based JSON only** for Drafts. That recommendation has been corrected after external review. The full product requires Drafts to support listing, filtering, ownership, assignment, status queries, search, duplicate detection, linking, merging, audit history, retention, and promotion to Trip. That makes Drafts an **operational workflow entity**, not a static artifact like RunLedger entries.
>
> **Correct long-term architecture:** **Hybrid SQL + JSONB** — SQL for metadata and queryable operational fields, JSONB for flexible workbench payload.
>
> **Phase 0 decision:** Implement **FileDraftStore** for speed and local debuggability, but **only as the first backend behind a clean `DraftStore` abstraction**. It is explicitly **not** the permanent product architecture. The abstraction must allow a future `SQLDraftStore` or hybrid backend without changing API callers or frontend contracts.
>
> **Earlier hybrid recommendation (from research docs) remains valid** for future production/multi-agent scale.

### First Principles Analysis

We have two persistence backends in the system today:

| Backend | Used By | Pattern | Strengths | Weaknesses |
|---------|---------|---------|-----------|------------|
| **File-based JSON** (`data/trips/`, `data/runs/`, `data/audit/`) | `FileTripStore`, `RunLedger`, `AuditStore` | One JSON file per entity, file-lock for concurrency | Simple, debuggable, no schema migrations, fast for small data | No queries, no indexing, concurrency via file locks, doesn't scale |
| **PostgreSQL + SQLAlchemy** (`Trip` model) | `SQLTripStore` (optional via `TRIPSTORE_BACKEND=sql`) | Relational tables, async sessions, field-level PII encryption, JSONB columns | Queryable, indexed, concurrent, relational, JSONB for flexible payload | Schema migrations, more complex, requires PostgreSQL running |

### Why Hybrid SQL+JSONB is Correct for Full Product

Drafts are **active work**, not append-only history. They need:

| Capability | SQL Metadata | JSONB Payload |
|------------|-------------|---------------|
| List all open drafts for agency | `SELECT ... WHERE agency_id=$1 AND status='open'` | — |
| Show my blocked drafts | `SELECT ... WHERE assigned_to=$1 AND status='blocked'` | — |
| Search drafts by customer name | `WHERE customer_name_snapshot ILIKE '%Sharma%'` | — |
| Find drafts linked to TRIP-442 | `JOIN draft_links ON ...` | — |
| Duplicate detection by phone/email | `WHERE customer_phone_hash=$1` | — |
| Transfer ownership | `UPDATE assigned_to=$1` | — |
| Stale draft cleanup job | `WHERE updated_at < NOW() - INTERVAL '30 days'` | — |
| Large pasted WhatsApp message | — | `customer_message` text/JSONB |
| Generated packet snapshot | — | `last_packet` JSONB |
| Validation result snapshot | — | `last_validation` JSONB |

The moment you add `index.json`, `by_agency`, `by_user`, `by_status`, rebuild logic, corruption recovery, and filtering, you are **recreating weak SQL badly**.

### Phase 0: FileDraftStore (Dev-First Backend)

For Phase 0 only, we implement `FileDraftStore` because:
- We are dogfooding; need persistence, restore-on-refresh, run linking, and audit logging **now**
- SQL metadata is architectically cleaner for future multi-agent usage, but it slows this PR and creates migration/schema overhead before we even know the draft workflow feels right
- PostgreSQL is available in the project (`DATABASE_URL`, `AsyncSession`, `Base` model), but we are not blocked on schema design

**Constraints:**
1. `DraftStore` is an **interface/abstraction** — callers never know whether the backend is file or SQL
2. File layout is an implementation detail, not an API contract
3. `index.json` is a performance optimization, not the source of truth
4. All index corruption must be recoverable by scanning `data/drafts/*.json`

**Directory Layout (implementation detail):**
```
data/drafts/
  draft_abc123.json      # draft document
  draft_def456.json
  index.json             # agency-scoped index (rebuildable)
```

**Index Structure (rebuildable):**
```json
{
  "version": 1,
  "by_agency": {
    "agency_001": ["draft_abc123", "draft_def456"]
  },
  "by_user": {
    "user_001": ["draft_abc123"]
  },
  "by_status": {
    "open": ["draft_abc123"],
    "blocked": ["draft_def456"]
  },
  "last_updated": "2026-04-29T10:32:00Z"
}
```
data/drafts/
  draft_abc123.json      # draft document
  draft_def456.json
  index.json             # agency-scoped index for fast listing
```

**Index Structure (for fast listing without globbing all files):**
```json
{
  "by_agency": {
    "agency_001": ["draft_abc123", "draft_def456"]
  },
  "by_user": {
    "user_001": ["draft_abc123"]
  },
  "last_updated": "2026-04-29T10:32:00Z"
}
```

---

## 4. User Answers & Decisions

### 4.1 Auto-Save vs. Explicit Save

**User Decision:** Both.

- **Auto-save:** Debounced (minimum 5 seconds after last keystroke). Fields must have *some* content (not blank/empty) before auto-save triggers. This prevents the Google Docs problem of saving blank documents.
- **Explicit "Save Draft" button:** Always available. Agents in travel need to feel in control, especially with customer PII. Explicit save is a comfort action.

**Implementation Note:** Auto-save should update a subtle indicator (e.g., "Draft saved 10:32 AM" in the header), not a disruptive toast.

### 4.2 Draft Naming

**User Decision:** Auto-generate from content, allow editing.

- **Primary source:** First line of `customer_message` (raw note)
- **Fallback:** First line of `agent_notes` (owner note)
- **Fallback fallback:** `"Draft — Apr 29, 10:32 AM"`
- **User can edit:** Click-to-edit name field in the header or drafts list

**Implementation Note:** Auto-name updates whenever the source field changes *and* the user hasn't manually edited the name yet. Once manually edited, auto-naming stops for that draft.

### 4.3 UI Placement

**User Decision:** Option B — "Drafts" item in the left sidebar.

Next to Inbox, Workbench, etc. This gives drafts equal footing with other primary navigation items. It signals that drafts are not second-class.

### 4.4 Draft → Trip Linking / Merging

**New Requirement Raised by User:**

> "Suppose today I save something in draft, later another agent started work on the same customer but created a new draft/trip — user should be able to attach existing draft / trip to another one?"

**Interpretation:** This is a **merge/attach** capability. Two scenarios:

1. **Draft-to-Draft Merge:** Agent A has draft D1 for customer "John Smith". Agent B starts a new draft D2 for the same customer. The system should detect this (or let B explicitly search) and allow B to attach/merge D1's content into D2.
2. **Draft-to-Trip Attach:** A draft was created but never processed. Later, a trip T1 was created for the same customer via a different channel. The draft should be linkable to T1 so its history is preserved.

**This is a P1 feature, not P0.** The initial Drafts system should design for it (store `linked_drafts`, `linked_trips` arrays) but not implement the merge UI yet.

---

## 5. The "Draft Linking/Merging" Requirement

### Design for Future Merge (Schema-Ready)

The `Draft` model should include:

```python
# Linking fields (prepared for future merge feature)
linked_draft_ids: List[str] = Field(default_factory=list)
linked_trip_ids: List[str] = Field(default_factory=list)
merge_history: List[dict] = Field(default_factory=list)
# Example merge_history entry:
# {
#   "merged_at": "2026-04-29T14:00:00Z",
#   "source_draft_id": "draft_abc123",
#   "merged_by": "user_002",
#   "reason": "Same customer, continuing work"
# }
```

### Why Not Implement Merge UI Now?

1. **Scope Control:** The core drafts system (create, save, load, process, promote) is already substantial.
2. **Usage Validation:** We need to see if agents actually create duplicate drafts before building merge UI.
3. **Detection Complexity:** Auto-detecting "same customer" across drafts requires PII matching, which is risky and error-prone.

**Decision:** Schema includes linking fields. UI for merge is deferred to Phase 2.

---

## 6. Proposed Architecture

### Two-Tier Log (Corrected)

| Tier | Scope | Persistence | Lifecycle |
|------|-------|-------------|-----------|
| **Tier 1: Draft Session Events** | Per-draft, pre-trip | `AuditStore` keyed by `draft_id` | **Preserved permanently** — never destroyed |
| **Tier 2: Trip Timeline** | Per-trip, post-promotion | `AuditStore` keyed by `trip_id` | Permanent |

> **Correction:** Original doc stated draft-era events were "destroyed when promoted." This is wrong. Audit logs must be append-only. On promotion, we add a linking event (`draft_promoted`) that connects `draft_id` → `trip_id`. Trip timeline reads both trip events and linked draft events by relationship lookup.

### Draft Lifecycle

```
[Agent opens Workbench]
    ↓
[Backend auto-creates Draft OR loads existing ?draft=xxx]
    ↓
[Agent edits inputs → auto-saves or explicit saves]
    ↓
[Agent clicks "Process"]
    ↓
[Run executes, linked to draft_id]
    ↓
[Run completes]
    ├──→ Success: Draft.promote_to_trip(trip_id) → status="promoted"
    │             Agent routed to workspace
    │             Draft events merged into trip timeline
    │
    └──→ Blocked/Failed: Draft.status="blocked" or "failed"
                       Agent edits, saves, re-processes
    ↓
[Agent can return to draft anytime via sidebar]
```

---

## 7. Data Model

### 7.1 Long-Term: Hybrid SQL + JSONB

**SQL Table: `drafts`** — operational metadata

```sql
CREATE TABLE drafts (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid(),
    agency_id VARCHAR(36) NOT NULL REFERENCES agencies(id) ON DELETE CASCADE,
    created_by VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE SET NULL,
    assigned_to VARCHAR(36) REFERENCES users(id) ON DELETE SET NULL,
    
    status VARCHAR(20) NOT NULL DEFAULT 'open',
    name VARCHAR(255) NOT NULL,
    name_source VARCHAR(20) DEFAULT 'auto',           -- 'auto' | 'user' | 'timestamp'
    
    stage VARCHAR(30) DEFAULT 'discovery',
    operating_mode VARCHAR(30) DEFAULT 'normal_intake',
    scenario_id VARCHAR(36),
    strict_leakage BOOLEAN DEFAULT FALSE,
    source_channel VARCHAR(50),                        -- 'web', 'whatsapp', 'phone', 'email'
    
    customer_id VARCHAR(36),                           -- future CRM link
    customer_name_snapshot VARCHAR(255),
    customer_phone_hash VARCHAR(64),                   -- for duplicate detection
    customer_email_hash VARCHAR(64),                   -- for duplicate detection
    
    last_run_id VARCHAR(36),
    last_run_state VARCHAR(20),
    last_run_completed_at TIMESTAMPTZ,
    
    promoted_trip_id VARCHAR(36) REFERENCES trips(id) ON DELETE SET NULL,
    promoted_at TIMESTAMPTZ,
    merged_into_draft_id VARCHAR(36),
    
    discarded_at TIMESTAMPTZ,
    discarded_by VARCHAR(36),
    
    version INTEGER NOT NULL DEFAULT 1,                -- optimistic concurrency
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    INDEX idx_drafts_agency_status (agency_id, status),
    INDEX idx_drafts_assigned (assigned_to, status),
    INDEX idx_drafts_customer_hash (customer_phone_hash, customer_email_hash),
    INDEX idx_drafts_promoted (promoted_trip_id),
    INDEX idx_drafts_merged (merged_into_draft_id)
);
```

**SQL Table: `draft_payloads`** — flexible workbench content

```sql
CREATE TABLE draft_payloads (
    draft_id VARCHAR(36) PRIMARY KEY REFERENCES drafts(id) ON DELETE CASCADE,
    customer_message TEXT,
    agent_notes TEXT,
    structured_json JSONB,
    itinerary_text TEXT,
    last_validation JSONB,
    last_packet JSONB,
    run_snapshots JSONB DEFAULT '[]',                  -- array of {run_id, state, snapshot, timestamp}
    merge_history JSONB DEFAULT '[]',
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

**SQL Table: `draft_links`** — relational linking/merging

```sql
CREATE TABLE draft_links (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid(),
    source_draft_id VARCHAR(36) NOT NULL REFERENCES drafts(id) ON DELETE CASCADE,
    target_type VARCHAR(10) NOT NULL,                  -- 'DRAFT' | 'TRIP'
    target_id VARCHAR(36) NOT NULL,
    link_type VARCHAR(20) NOT NULL,                    -- 'SAME_CUSTOMER' | 'FOLLOW_UP' | 'REVISION' | 'DUPLICATE' | 'MERGED_FROM' | 'MERGED_INTO' | 'RELATED'
    created_by VARCHAR(36),
    note TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### 7.2 Phase 0: FileDraftStore Representation

For Phase 0, the `FileDraftStore` serializes the **union** of SQL metadata + payload into a single JSON file. This is temporary — it allows us to defer SQL schema design while still capturing all fields.

Stored at `data/drafts/{draft_id}.json`:

```python
class Draft(BaseModel):
    # === Identity (SQL metadata) ===
    id: str
    agency_id: str
    created_by: str
    assigned_to: Optional[str] = None
    
    # === Metadata (SQL metadata) ===
    name: str
    name_source: str = "auto"
    status: Literal["open", "processing", "blocked", "failed", "promoted", "merged", "discarded"]
    stage: str = "discovery"
    operating_mode: str = "normal_intake"
    scenario_id: Optional[str] = None
    strict_leakage: bool = False
    source_channel: Optional[str] = None
    
    # === Customer identity (SQL metadata, future duplicate detection) ===
    customer_id: Optional[str] = None
    customer_name_snapshot: Optional[str] = None
    customer_phone_hash: Optional[str] = None
    customer_email_hash: Optional[str] = None
    
    # === Run tracking (SQL metadata) ===
    last_run_id: Optional[str] = None
    last_run_state: Optional[str] = None
    last_run_completed_at: Optional[str] = None
    
    # === Promotion (SQL metadata) ===
    promoted_trip_id: Optional[str] = None
    promoted_at: Optional[str] = None
    merged_into_draft_id: Optional[str] = None
    
    # === Lifecycle (SQL metadata) ===
    discarded_at: Optional[str] = None
    discarded_by: Optional[str] = None
    version: int = 1
    created_at: str
    updated_at: str
    
    # === Payload (JSONB in full app) ===
    customer_message: Optional[str] = None
    agent_notes: Optional[str] = None
    structured_json: Optional[dict] = None
    itinerary_text: Optional[str] = None
    last_validation: Optional[dict] = None
    last_packet: Optional[dict] = None
    run_snapshots: List[dict] = Field(default_factory=list)
    merge_history: List[dict] = Field(default_factory=list)
    
    # === Linking cache (denormalized from draft_links table in full app) ===
    linked_draft_ids: List[str] = Field(default_factory=list)
    linked_trip_ids: List[str] = Field(default_factory=list)
```

**Note:** When we migrate to SQL, `linked_draft_ids` and `linked_trip_ids` become **read-only denormalized caches** populated from `draft_links` table. The source of truth for links is the relational table.

#### 7.3 Backend: Draft Index (Phase 0 Only)

Stored at `data/drafts/index.json`. Updated atomically with file lock. Rebuildable by scanning all draft JSON files.

```json
{
  "version": 1,
  "by_agency": {
    "agency_001": ["draft_abc123", "draft_def456"]
  },
  "by_user": {
    "user_001": ["draft_abc123"]
  },
  "by_status": {
    "open": ["draft_abc123"],
    "blocked": ["draft_def456"]
  }
}
```

**Migration note:** In SQL backend, this index is replaced by proper `INDEX` definitions on the `drafts` table.

#### 7.4 Frontend: Workbench Store Extension

Zustand store gets a `draft_id` field and syncs to backend. **Zustand is the local editing buffer, not the source of truth.**

```typescript
interface WorkbenchStore {
  // ... existing fields ...
  
  // Draft identity (server is source of truth)
  draft_id: string | null;
  draft_name: string;
  draft_status: DraftStatus;
  draft_last_saved_at: string | null;
  draft_version: number;           -- for optimistic concurrency
  
  // UI state only
  save_state: 'clean' | 'dirty' | 'saving' | 'saved' | 'conflict' | 'error';
  
  setDraftId: (id: string | null) => void;
  setDraftName: (name: string) => void;
  setDraftStatus: (status: DraftStatus) => void;
  setSaveState: (state: SaveState) => void;
}
```

---

## 8. API Surface

### Draft Management

```
POST   /api/drafts                    → Create draft (returns {draft_id, name, created_at})
GET    /api/drafts                    → List my agency's drafts (paginated)
GET    /api/drafts/{id}               → Load full draft state
PUT    /api/drafts/{id}               → Save draft (inputs, config, name)
DELETE /api/drafts/{id}               → Discard (soft delete: status="discarded")
POST   /api/drafts/{id}/process       → Run spine pipeline (sets draft_id on run)
GET    /api/drafts/{id}/events        → Audit timeline for this draft
GET    /api/drafts/{id}/runs          → All runs linked to this draft
POST   /api/drafts/{id}/promote       → Manual promote to trip (if run completed)
```

### Run Endpoint Changes

```
POST   /api/spine/run                 → Accepts optional draft_id in payload
                                       If draft_id provided, run is linked to draft
```

### Timeline Endpoint Changes

```
GET    /api/trips/{trip_id}/timeline  → Transparently includes draft-era events
                                       (looks up promoted_from_draft_id on trip)
```

---

## 9. Audit Integration Strategy

### The Key Problem

`AuditStore.get_events_for_trip(trip_id)` filters events by `details.trip_id`. Draft-era events have `details.draft_id` instead. How do we make the timeline seamless?

### Solution: Append-Only Events + Promotion-Time Link

**Rule: Audit events are append-only. Never destroy, delete, or overwrite draft-era events.**

When a draft is promoted to a trip:
1. Create a new audit event: `draft_promoted` with `details.draft_id` and `details.trip_id`
2. This event acts as a bridge between the draft timeline and the trip timeline
3. Trip timeline queries read:
   - Events where `details.trip_id == trip_id`
   - PLUS events where a `draft_promoted` event links that draft to this trip

**Why not copy events?**
Because duplicating events creates data integrity risks (what if the original is updated?). A linking event preserves the single-source-of-truth principle.

**Event Types for Drafts:**

| Event Type | When | Payload |
|------------|------|---------|
| `draft_created` | On POST /api/drafts | `{draft_id, created_by, agency_id}` |
| `draft_autosaved` | Auto-save fires | `{draft_id, fields_changed, auto_save: true}` |
| `draft_saved` | Explicit save | `{draft_id, fields_changed, auto_save: false}` |
| `draft_renamed` | Name changed | `{draft_id, old_name, new_name, source}` |
| `draft_process_started` | On POST /api/drafts/{id}/process | `{draft_id, run_id, stage, mode, scenario_id}` |
| `draft_process_completed` | Run completes | `{draft_id, run_id, trip_id, duration_ms}` |
| `draft_process_blocked` | Run blocked | `{draft_id, run_id, gate, reasons}` |
| `draft_process_failed` | Run failed | `{draft_id, run_id, stage_at_failure, error}` |
| `draft_promoted` | On promotion | `{draft_id, trip_id, promoted_by}` |
| `draft_discarded` | On DELETE | `{draft_id, discarded_by}` |
| `draft_restored` | Restore from discarded | `{draft_id, restored_by}` |
| `draft_linked` | Link created | `{draft_id, target_type, target_id, link_type, created_by}` |

**Security note:** Do not include raw PII (customer messages, phone numbers, emails) in audit payloads. Use hashes or redacted snippets.

---

## 10. Frontend Changes

### 10.1 New "Drafts" Sidebar Item

**File:** `frontend/src/components/layouts/Shell.tsx` (or wherever sidebar nav is defined)

Add "Drafts" with a badge showing count of `open` + `blocked` drafts for the current agent.

### 10.2 Drafts List Page

**New file:** `frontend/src/app/drafts/page.tsx`

Table view:
- Name (clickable)
- Status badge (Open, Blocked, Failed, Promoted → links to trip)
- Last modified
- Created by
- Actions: Open, Delete

### 10.3 Workbench URL Changes

Current: `/workbench?trip=xxx&stage=discovery`  
New: `/workbench?draft=abc123&stage=discovery`

If `?draft=` is present, load draft state on mount.  
If `?trip=` is present, continue existing behavior (trip-linked workbench).  
If neither, auto-create a new draft on first user interaction (or on "Save Draft").

### 10.4 Workbench Header Changes

Add to header:
- Draft name (click-to-edit)
- Draft status badge
- "Last saved: 2 min ago" indicator
- "Save Draft" button (always visible)

### 10.5 Auto-Save Implementation

**Hook:** `useAutoSave({ draftId, debounceMs: 5000, minContentLength: 10 })`

```typescript
useEffect(() => {
  if (!draftId) return;
  if (contentLength < minContentLength) return;
  
  const timer = setTimeout(() => {
    saveDraft(draftId, draftData);
    setLastSavedAt(new Date());
  }, debounceMs);
  
  return () => clearTimeout(timer);
}, [draftId, customerMessage, agentNotes, config]);
```

---

## 11. Implementation Phases

### Phase 0: Foundation (Backend Plumbing)
**Goal:** Draft persistence exists, but no UI yet. Workbench continues to work as before.

1. Create `spine_api/draft_store.py`
   - `DraftStore.create()`, `.get()`, `.save()`, `.list()`, `.delete()`, `.promote()`
   - File-based JSON with index
   - Reuse `file_lock()` from `persistence.py`
2. Add `draft_id` to `SpineRunRequest` contract
3. Modify `POST /api/spine/run` to accept `draft_id`, link run to draft
4. Modify run completion logic to call `DraftStore.update_status()`
5. Add AuditStore event logging for draft lifecycle
6. Add `Draft` SQLAlchemy migration (optional, prepare schema)

**Verification:**
```bash
# Create draft
curl -X POST http://localhost:8000/api/drafts -d '{"name":"Test"}'

# Save draft
curl -X PUT http://localhost:8000/api/drafts/draft_xxx -d '{"customer_message":"Hello"}'

# Process with draft_id
curl -X POST http://localhost:8000/api/spine/run -d '{"draft_id":"draft_xxx","raw_note":"Hello"}'

# List drafts
curl http://localhost:8000/api/drafts
```

### Phase 1: Workbench Integration
**Goal:** Workbench uses drafts transparently. Users can save/load drafts.

1. Extend Zustand workbench store with draft fields
2. Add `?draft=` URL handling in Workbench
3. Auto-create draft on first meaningful interaction
4. Implement auto-save (debounced) + explicit "Save Draft" button
5. Load draft state on mount when `?draft=` present
6. Show draft name, status, last-saved indicator in header
7. On successful run completion, show "Promoted to Trip #xxx" with link

**Verification:**
- Open Workbench → new draft auto-created
- Type in intake → auto-saves after 5s
- Refresh page → draft state restored
- Process → blocked → save draft → close tab → reopen via URL → state intact

### Phase 2: Drafts UI (Sidebar + List)
**Goal:** Drafts are discoverable and manageable.

1. Add "Drafts" to sidebar navigation
2. Create `/drafts` list page
3. Drafts list shows: name, status, last modified, actions
4. Clicking a draft opens `/workbench?draft=xxx`
5. Delete action with confirmation

**Verification:**
- Navigate to Drafts → see saved drafts
- Click draft → opens workbench with state restored
- Delete draft → disappears from list

### Phase 3: Timeline Integration
**Goal:** Draft-era events appear in trip timeline after promotion.

1. Implement promotion-time link event (`draft_promoted`) in `DraftStore.promote()`
2. Modify `/api/trips/{id}/timeline` to include draft events via `draft_promoted` link lookup
3. Add `promoted_from_draft_id` to trip document
4. Verify timeline shows draft events with appropriate badges

**Verification:**
- Create draft → process → complete → view trip timeline
- Timeline shows: "Draft created", "Process started", "Process completed", "Draft promoted"
- Verify original draft audit events are preserved (not destroyed or overwritten)

### Phase 4: Advanced Features (Deferred)
- Draft-to-draft merge UI
- Draft-to-trip attach UI
- Draft sharing between agents
- Draft templates (save as template, create from template)

---

## 12. Open Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **File lock contention** if many agents auto-save simultaneously | Low | Medium | Use `file_lock()` with short timeout (5s). Auto-save is async, non-blocking. |
| **Draft index corruption** if process crashes during index write | Low | High | Index write is atomic (write to temp file, rename). Corrupt index can be rebuilt by scanning `data/drafts/*.json`. |
| **Drafts accumulate forever** | Medium | Low | Add `prune_discarded_drafts()` background job. Keep for 30 days then archive. |
| **PII in draft files** | Medium | High | Apply same privacy guard as `FileTripStore`. Block real PII in dogfood mode. Encrypt when moving to production. |
| **Draft ID collision** | Very Low | Medium | Use `uuid4` with 12-char hex suffix (same as trip IDs). Collision probability: ~1 in 10^15. |
| **Frontend assumes draft always exists** | Medium | Medium | Defensive coding: every draft-dependent UI path handles `draft_id === null` gracefully. |

---

## Appendix A: Discussion Trail

**Original Issue (2026-04-29):**
> "I ran a scenario... I got errors on the UI/UX I'm not so happy. It says errors but since I am developing I knew maybe I should look at other tabs but for me also it was not clear, maybe it should have auto switched to the tab where it had the errors."

**Agent Analysis:**
- Tabs are URL-driven via `?tab=` query param
- Workbench never auto-switches tabs after processing
- Errors are rendered in `RunProgressPanel` and in tab-specific panels (`PacketTab` for validation errors)
- Fix: `useEffect` watching `spineRunState` transitions into `blocked`/`failed`, then calling `handleTabChange()`

**User Expanded Vision:**
> "This is the right time to talk about the log/history capture — for all processes everything should be captured — the process button was clicked with what details... next log entry could be errors... third could be the edits I make..."

**Agent Counter-Proposal:**
> "AuditStore can't capture pre-trip events because there's no trip_id. Solution: draft_id as persistent pre-trip identity."

**User Architectural Push:**
> "Why not a draft id, once it's processed, draft maps to actual?"

**Agent Response:**
> "Exactly — you're seeing the bigger product. The draft_id shouldn't be invisible plumbing. It should be a first-class persistent workspace that agents explicitly own, save, and return to."

**User Decisions:**
1. Storage: Asked agent to think architecturally and from first principles
2. Auto-save: Minimum time debounced, explicit save also available, no blank saves
3. Naming: From first line of customer message or agent notes, editable
4. UI: Drafts in left sidebar
5. New requirement: Draft/trip linking and merging for duplicate customer scenarios

**Agent Initial Assessment (Superseded):**
File-based JSON is the correct choice for drafts given the system's existing patterns, debuggability needs, and draft access patterns. SQL would be premature optimization.

**External Review Findings (Critical Correction):**
An external architecture review identified a **contradiction** in the docs:
- This doc recommended JSON-only for Drafts
- Earlier research docs recommended **hybrid SQL + JSON payload** because drafts need listing, filtering, status queries, multi-agent access, cleanup, and linking
- The review concluded: **JSON-only is the wrong long-term architecture**

**Corrected Decision:**
- **Long-term:** Hybrid SQL + JSONB — SQL for metadata/queryable fields, JSONB for flexible workbench payload
- **Phase 0:** FileDraftStore as **dev-first backend only**, behind a clean `DraftStore` abstraction
- The abstraction must allow future `SQLDraftStore` without changing API or frontend contracts

**Key corrections applied:**
1. Audit events are **append-only** — never destroyed on promotion
2. Draft model includes all SQL-metadata fields (assigned_to, customer hashes, version, etc.)
3. `linked_draft_ids` / `linked_trip_ids` are denormalized caches; source of truth is `draft_links` table
4. Zustand is **local editing buffer**, not source of truth
5. Auto-save must be **conflict-safe** using version/updated_at checks

---

*End of document.*
