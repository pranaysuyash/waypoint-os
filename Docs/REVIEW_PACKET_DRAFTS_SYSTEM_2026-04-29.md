# Review Packet: Drafts System Architecture + Auto-Tab-Switch Fix

**For:** External reviewer (ChatGPT/Claude/Codex)  
**Date:** 2026-04-29  
**Scope:** Architecture review of the Drafts system + code review of the auto-tab-switch fix  
**Author:** OpenCode (implementation agent)  
**Project:** Waypoint OS — travel_agency_agent

---

## How to Use This Packet

1. Read the **Context** section to understand the existing system
2. Read the **Architecture Doc** (full text included)
3. Read the **Code Change** (auto-tab-switch)
4. Answer the **Review Questions** at the end
5. Flag any **blocking concerns** or **better alternatives**

---

## Part 1: Context — Existing System Patterns

### Persistence Architecture

The backend uses a **dual-persistence strategy**:

**File-based JSON** (default, used for all pre-trip artifacts):
- `FileTripStore` — trips stored as `data/trips/{trip_id}.json`
- `RunLedger` — runs stored as `data/runs/{run_id}/meta.json` + `steps/*.json`
- `AuditStore` — events stored as `data/audit/events.json` (append-only, single file)
- All use `file_lock()` for cross-process concurrency

**PostgreSQL** (optional, via `TRIPSTORE_BACKEND=sql`):
- `SQLTripStore` — async SQLAlchemy with field-level PII encryption
- Used only for trips (not runs, not audit events)

### Workbench Architecture

- **Tabs are URL-driven** via `?tab=` query parameter (`intake`, `packet`, `decision`, `strategy`, `safety`, `output`, `frontier`, `feedback`)
- **State management:** Zustand store (`workbench.ts`) — all inputs, config, and results in browser memory
- **Processing:** `POST /api/spine/run` queues a background thread. Frontend polls `GET /runs/{run_id}` via `useSpineRun` hook
- **Run states:** `queued` → `running` → `completed` | `failed` | `blocked`

### The Problem That Started This

When a user clicks "Process Trip" and the pipeline ends in `blocked` (validation errors) or `failed`, the Workbench stays on the current tab. The errors are rendered in the `Trip Details` (packet) tab, but the user has no signal to look there. The user (a developer) knew to check other tabs, but operators won't.

---

## Part 2: Architecture Document

**File:** `Docs/DRAFTS_SYSTEM_ARCHITECTURE_PLAN_2026-04-29.md`  
**Status:** Proposed, awaiting review

---

### 1. Problem Statement

### Original Pain Point
When running a scenario in the Workbench, if the pipeline ends in `blocked` or `failed`, the UI shows errors but the user stays on the current tab. The errors are actually rendered in the `Trip Details` (packet) tab, but nothing tells the user to look there. As a developer, the user knew to check other tabs — but this is poor UX for any operator.

### Expanded Vision: The Drafts System
The user recognized that solving the tab-switch problem opens a larger product opportunity: **the Workbench should not be ephemeral**. Agents should be able to save incomplete work as drafts, return to it later, and have a complete audit trail from the very first customer message through final trip creation.

---

### 2. What Was Implemented Today

#### 2.1 Auto-Tab-Switch Fix
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

### 3. Storage Medium Decision

#### First Principles Analysis

We have two persistence backends in the system today:

| Backend | Used By | Pattern | Strengths | Weaknesses |
|---------|---------|---------|-----------|------------|
| **File-based JSON** (`data/trips/`, `data/runs/`, `data/audit/`) | `FileTripStore`, `RunLedger`, `AuditStore` | One JSON file per entity, file-lock for concurrency | Simple, debuggable, no schema migrations, fast for small data | No queries, no indexing, concurrency via file locks, doesn't scale |
| **PostgreSQL + SQLAlchemy** (`Trip` model) | `SQLTripStore` (optional via `TRIPSTORE_BACKEND=sql`) | Relational tables, async sessions, field-level PII encryption | Queryable, indexed, concurrent, relational | Schema migrations, more complex, requires PostgreSQL running |

#### Decision: File-Based JSON for Drafts

**Rationale:**

1. **Architectural Consistency (Principle: Least Surprise)**  
   Every other pre-trip artifact in the system uses file-based JSON: `RunLedger` (runs), `AuditStore` (events), `FileTripStore` (trips in file mode). Adding a SQL table for drafts would introduce an exception that every developer must remember. The system already has a `data/` directory convention.

2. **Lifecycle Fit (Principle: Match Storage to Access Pattern)**  
   Drafts are looked up by `draft_id` (single-key fetch) or listed by `agency_id` (simple filter). There are no joins, no complex queries, no relationships. File-based storage is actually *faster* for this access pattern than SQL (no connection pool, no query planner).

3. **Operational Simplicity (Principle: Optimize for Debuggability)**  
   When an agent says "my draft disappeared," we can `cat data/drafts/draft_abc123.json` and see exactly what was saved. With SQL, we'd need `psql` or a migration to inspect. In early-stage product development, debuggability trumps theoretical scale.

4. **Migration Path (Principle: Make Reversible Decisions)**  
   File-based storage is not a trap. If drafts grow to 10,000+ per agency, we can build a migration that reads all `data/drafts/*.json` and inserts them into a new `drafts` SQL table. The abstraction layer (`DraftStore`) makes this transparent to callers.

5. **The SQL Argument Countered**  
   One might argue: "But SQL gives us concurrent edits and ACID!"  
   Response: Drafts are owned by a single agent at a time. Concurrent editing of the same draft is not a product requirement today. File locks (already built and battle-tested via `file_lock()`) provide sufficient isolation.

**Directory Layout:**
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

### 4. User Answers & Decisions

#### 4.1 Auto-Save vs. Explicit Save

**User Decision:** Both.

- **Auto-save:** Debounced (minimum 5 seconds after last keystroke). Fields must have *some* content (not blank/empty) before auto-save triggers. This prevents the Google Docs problem of saving blank documents.
- **Explicit "Save Draft" button:** Always available. Agents in travel need to feel in control, especially with customer PII. Explicit save is a comfort action.

**Implementation Note:** Auto-save should update a subtle indicator (e.g., "Draft saved 10:32 AM" in the header), not a disruptive toast.

#### 4.2 Draft Naming

**User Decision:** Auto-generate from content, allow editing.

- **Primary source:** First line of `customer_message` (raw note)
- **Fallback:** First line of `agent_notes` (owner note)
- **Fallback fallback:** `"Draft — Apr 29, 10:32 AM"`
- **User can edit:** Click-to-edit name field in the header or drafts list

**Implementation Note:** Auto-name updates whenever the source field changes *and* the user hasn't manually edited the name yet. Once manually edited, auto-naming stops for that draft.

#### 4.3 UI Placement

**User Decision:** Option B — "Drafts" item in the left sidebar.

Next to Inbox, Workbench, etc. This gives drafts equal footing with other primary navigation items. It signals that drafts are not second-class.

#### 4.4 Draft → Trip Linking / Merging

**New Requirement Raised by User:**

> "Suppose today I save something in draft, later another agent started work on the same customer but created a new draft/trip — user should be able to attach existing draft / trip to another one?"

**Interpretation:** This is a **merge/attach** capability. Two scenarios:

1. **Draft-to-Draft Merge:** Agent A has draft D1 for customer "John Smith". Agent B starts a new draft D2 for the same customer. The system should detect this (or let B explicitly search) and allow B to attach/merge D1's content into D2.
2. **Draft-to-Trip Attach:** A draft was created but never processed. Later, a trip T1 was created for the same customer via a different channel. The draft should be linkable to T1 so its history is preserved.

**This is a P1 feature, not P0.** The initial Drafts system should design for it (store `linked_drafts`, `linked_trips` arrays) but not implement the merge UI yet.

---

### 5. The "Draft Linking/Merging" Requirement

#### Design for Future Merge (Schema-Ready)

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

#### Why Not Implement Merge UI Now?

1. **Scope Control:** The core drafts system (create, save, load, process, promote) is already substantial.
2. **Usage Validation:** We need to see if agents actually create duplicate drafts before building merge UI.
3. **Detection Complexity:** Auto-detecting "same customer" across drafts requires PII matching, which is risky and error-prone.

**Decision:** Schema includes linking fields. UI for merge is deferred to Phase 2.

---

### 6. Proposed Architecture

#### Two-Tier Log (Confirmed)

| Tier | Scope | Persistence | Lifecycle |
|------|-------|-------------|-----------|
| **Tier 1: Draft Session Events** | Per-draft, pre-trip | `AuditStore` keyed by `draft_id` | Destroyed when draft promoted (events copied to trip timeline) |
| **Tier 2: Trip Timeline** | Per-trip, post-promotion | `AuditStore` keyed by `trip_id` | Permanent |

#### Draft Lifecycle

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

### 7. Data Model

#### 7.1 Backend: Draft Document (JSON)

Stored at `data/drafts/{draft_id}.json`.

```python
class Draft(BaseModel):
    # Identity
    id: str                          # nanoid, e.g. "draft_abc123"
    agency_id: str
    created_by: str                  # user_id
    created_at: str                  # ISO 8601
    updated_at: str                  # ISO 8601
    
    # Metadata
    name: str                        # Auto-generated or user-edited
    status: Literal["open", "processing", "blocked", "failed", "promoted", "discarded"]
    
    # Workbench Input State
    customer_message: Optional[str] = None      # raw_note
    agent_notes: Optional[str] = None           # owner_note
    structured_json: Optional[dict] = None
    itinerary_text: Optional[str] = None
    
    # Config
    stage: str = "discovery"
    operating_mode: str = "normal_intake"
    scenario_id: Optional[str] = None
    strict_leakage: bool = False
    
    # Run Tracking
    last_run_id: Optional[str] = None
    last_run_state: Optional[str] = None        # queued|running|completed|failed|blocked
    last_run_completed_at: Optional[str] = None
    
    # Result Snapshots (for fast UI hydration without re-querying runs)
    last_validation: Optional[dict] = None
    last_packet: Optional[dict] = None
    
    # Promotion
    promoted_trip_id: Optional[str] = None
    promoted_at: Optional[str] = None
    
    # Future: Linking/Merge
    linked_draft_ids: List[str] = Field(default_factory=list)
    linked_trip_ids: List[str] = Field(default_factory=list)
    merge_history: List[dict] = Field(default_factory=list)
```

#### 7.2 Backend: Draft Index

Stored at `data/drafts/index.json`. Updated atomically with file lock.

```python
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

#### 7.3 Frontend: Workbench Store Extension

Zustand store gets a `draft_id` field and persists to backend instead of just local state.

```typescript
interface WorkbenchStore {
  // ... existing fields ...
  
  draft_id: string | null;
  draft_name: string;
  draft_status: DraftStatus;
  draft_last_saved_at: string | null;
  
  setDraftId: (id: string | null) => void;
  setDraftName: (name: string) => void;
  setDraftStatus: (status: DraftStatus) => void;
}
```

---

### 8. API Surface

#### Draft Management

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

#### Run Endpoint Changes

```
POST   /api/spine/run                 → Accepts optional draft_id in payload
                                       If draft_id provided, run is linked to draft
```

#### Timeline Endpoint Changes

```
GET    /api/trips/{trip_id}/timeline  → Transparently includes draft-era events
                                       (looks up promoted_from_draft_id on trip)
```

---

### 9. Audit Integration Strategy

#### The Key Problem

`AuditStore.get_events_for_trip(trip_id)` filters events by `details.trip_id`. Draft-era events have `details.draft_id` instead. How do we make the timeline seamless?

#### Solution: Dual-Key Events + Promotion-Time Copy

**Option A (Chosen): Promotion-Time Copy**

When a draft is promoted to a trip:
1. Fetch all audit events where `details.draft_id == draft_id`
2. Create copies of those events with `details.trip_id == trip_id` added
3. Insert the copied events into `AuditStore`
4. Mark original draft events as `archived: true` (optional, for dedup)

**Why not just query by both IDs?**  
Because `AuditStore` is a flat JSON file. Queries are O(n) scans. Doing two scans (one for trip_id, one for draft_id) doubles the cost. Copying at promotion time is a one-time cost that makes all future timeline queries simple and fast.

**Event Types for Drafts:**

| Event Type | When | Payload |
|------------|------|---------|
| `draft_created` | On POST /api/drafts | `{draft_id, created_by, agency_id}` |
| `draft_saved` | On PUT /api/drafts | `{draft_id, fields_changed, auto_save: bool}` |
| `draft_process_started` | On POST /api/drafts/{id}/process | `{draft_id, run_id, stage, mode, scenario_id}` |
| `draft_process_completed` | Run completes | `{draft_id, run_id, trip_id, duration_ms}` |
| `draft_process_blocked` | Run blocked | `{draft_id, run_id, gate, reasons}` |
| `draft_process_failed` | Run failed | `{draft_id, run_id, stage_at_failure, error}` |
| `draft_promoted` | On promotion | `{draft_id, trip_id, promoted_by}` |
| `draft_discarded` | On DELETE | `{draft_id, discarded_by}` |

---

### 10. Frontend Changes

#### 10.1 New "Drafts" Sidebar Item

**File:** `frontend/src/components/layouts/Shell.tsx` (or wherever sidebar nav is defined)

Add "Drafts" with a badge showing count of `open` + `blocked` drafts for the current agent.

#### 10.2 Drafts List Page

**New file:** `frontend/src/app/drafts/page.tsx`

Table view:
- Name (clickable)
- Status badge (Open, Blocked, Failed, Promoted → links to trip)
- Last modified
- Created by
- Actions: Open, Delete

#### 10.3 Workbench URL Changes

Current: `/workbench?trip=xxx&stage=discovery`  
New: `/workbench?draft=abc123&stage=discovery`

If `?draft=` is present, load draft state on mount.  
If `?trip=` is present, continue existing behavior (trip-linked workbench).  
If neither, auto-create a new draft on first user interaction (or on "Save Draft").

#### 10.4 Workbench Header Changes

Add to header:
- Draft name (click-to-edit)
- Draft status badge
- "Last saved: 2 min ago" indicator
- "Save Draft" button (always visible)

#### 10.5 Auto-Save Implementation

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

### 11. Implementation Phases

#### Phase 0: Foundation (Backend Plumbing)
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

#### Phase 1: Workbench Integration
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

#### Phase 2: Drafts UI (Sidebar + List)
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

#### Phase 3: Timeline Integration
**Goal:** Draft-era events appear in trip timeline after promotion.

1. Implement promotion-time event copy in `DraftStore.promote()`
2. Modify `/api/trips/{id}/timeline` to include draft events
3. Add `promoted_from_draft_id` to trip document
4. Verify timeline shows draft events with appropriate badges

**Verification:**
- Create draft → process → complete → view trip timeline
- Timeline shows: "Draft created", "Process started", "Process completed", "Draft promoted"

#### Phase 4: Advanced Features (Deferred)
- Draft-to-draft merge UI
- Draft-to-trip attach UI
- Draft sharing between agents
- Draft templates (save as template, create from template)

---

### 12. Open Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **File lock contention** if many agents auto-save simultaneously | Low | Medium | Use `file_lock()` with short timeout (5s). Auto-save is async, non-blocking. |
| **Draft index corruption** if process crashes during index write | Low | High | Index write is atomic (write to temp file, rename). Corrupt index can be rebuilt by scanning `data/drafts/*.json`. |
| **Drafts accumulate forever** | Medium | Low | Add `prune_discarded_drafts()` background job. Keep for 30 days then archive. |
| **PII in draft files** | Medium | High | Apply same privacy guard as `FileTripStore`. Block real PII in dogfood mode. Encrypt when moving to production. |
| **Draft ID collision** | Very Low | Medium | Use `uuid4` with 12-char hex suffix (same as trip IDs). Collision probability: ~1 in 10^15. |
| **Frontend assumes draft always exists** | Medium | Medium | Defensive coding: every draft-dependent UI path handles `draft_id === null` gracefully. |

---

## Part 3: Code Change for Review

### File: `frontend/src/app/workbench/page.tsx`

**What changed:** Added auto-tab-switch logic when `spineRunState` transitions into `blocked` or `failed`.

**Full context of the change:**

```tsx
// Located in the WorkbenchContent component, after the useEffect that populates
// store.validation/store.packet from spineRunState, and before the useUpdateTrip hook.

// Auto-switch to the tab containing errors when a run ends in blocked/failed state.
// This prevents the user from missing field-level validation errors that are rendered
// in the Trip Details (packet) tab or other stage-specific tabs.
const prevRunStateRef = useRef<string | null>(null);
useEffect(() => {
  const currentState = spineRunState?.state ?? null;
  const prevState = prevRunStateRef.current;

  // Only act when transitioning into a terminal error state
  if (
    currentState !== prevState &&
    (currentState === 'blocked' || currentState === 'failed')
  ) {
    if (currentState === 'blocked') {
      // Blocked runs with validation errors show details in the packet tab
      handleTabChange('packet');
    } else if (currentState === 'failed') {
      const stage = spineRunState?.stage_at_failure;
      const stageToTab: Record<string, WorkspaceTabId> = {
        packet: 'packet',
        validation: 'packet',
        decision: 'decision',
        strategy: 'strategy',
        safety: 'safety',
      };
      const targetTab = stage ? stageToTab[stage] : undefined;
      if (targetTab) {
        handleTabChange(targetTab);
      }
    }
  }

  prevRunStateRef.current = currentState;
}, [spineRunState, handleTabChange]);
```

**Dependencies:**
- `useRef` was already imported from `react`
- `handleTabChange` was already defined earlier in the component
- `WorkspaceTabId` type was already defined

---

## Part 4: Key Files for Context

The reviewer should read these files to understand the existing patterns:

### Backend

| File | Why It Matters |
|------|---------------|
| `spine_api/persistence.py` | Shows `FileTripStore`, `AuditStore`, `file_lock()` patterns |
| `spine_api/run_ledger.py` | Shows how runs are persisted as JSON files |
| `spine_api/contract.py` | Shows `SpineRunRequest`, `RunStatusResponse` schemas |
| `spine_api/server.py` | Shows `/api/spine/run`, `/runs/{id}`, `/api/trips/{id}/timeline` endpoints |
| `spine_api/core/database.py` | Shows SQLAlchemy setup (for comparison with file-based approach) |

### Frontend

| File | Why It Matters |
|------|---------------|
| `frontend/src/app/workbench/page.tsx` | Main workbench component — tabs, processing, state |
| `frontend/src/stores/workbench.ts` | Zustand store — all workbench state |
| `frontend/src/hooks/useSpineRun.ts` | Hook that polls run status |
| `frontend/src/app/workbench/RunProgressPanel.tsx` | Shows run progress, errors, blocked state |
| `frontend/src/hooks/useFieldAuditLog.ts` | Existing localStorage audit log (for comparison) |

---

## Part 5: Review Questions

Please answer these questions. Flag any **blocking concerns** or **significantly better alternatives**.

### Architecture

1. **Storage medium:** Is file-based JSON the right choice for drafts, given the existing system uses files for runs and audit events, but SQL for trips? Or is there a strong argument for SQL that I'm missing?

2. **Index strategy:** Is the `index.json` approach (agency-scoped lookup tables) sound, or would you recommend a different listing strategy? Consider that we need to list drafts by agency, by user, and filter by status.

3. **Promotion-time event copy:** When a draft is promoted to a trip, I plan to copy all draft-era audit events and rewrite them with `trip_id`. Is this the right approach? Alternative: query by both `draft_id` and `trip_id` at read time. Trade-off: one-time write vs. double scan on every timeline read.

4. **Draft schema completeness:** Are there fields missing from the `Draft` model that would cause us pain later? Think about: versioning, soft-delete, tags/categories, agent assignment.

### Code

5. **Auto-tab-switch safety:** The `useEffect` uses a `prevRunStateRef` to detect transitions. Could this cause unwanted navigation in any edge case? For example:
   - User manually switches tabs while run is running, then it blocks — does the effect override their manual choice?
   - User refreshes the page with a blocked run already in state — does it switch tabs on mount?
   - What if `spineRunState` is null briefly between polls?

6. **Zustand store pollution:** Adding draft fields to the workbench store couples draft identity to workbench state. Should drafts have their own store, or is colocation correct?

### Security / Compliance

7. **PII in draft files:** Drafts will contain raw customer messages and agent notes. The existing `FileTripStore` has a privacy guard for dogfood mode. Should drafts use the same guard? Is there additional risk because drafts are more ephemeral and might be forgotten?

8. **Agency isolation:** The index includes `by_agency`. Is file-path scoping (`data/drafts/agency_001/draft_xxx.json`) better than a flat directory with agency_id in the JSON?

### UX / Product

9. **Auto-save debounce:** 5 seconds feels right for travel agents typing customer notes. Too aggressive? Too lazy?

10. **Draft auto-creation:** I proposed auto-creating a draft on first user interaction. Alternative: only create when user clicks "Save Draft" or "Process". Which is less surprising?

11. **The merge/linking requirement:** The user wants to attach/link drafts and trips. My schema includes `linked_draft_ids` and `linked_trip_ids` but defers UI. Is the schema design future-proof enough?

### Implementation Order

12. **Phase ordering:** I proposed: Backend plumbing → Workbench integration → Drafts UI → Timeline integration. Would you reorder or combine any phases?

---

## Part 6: Known Uncertainties

These are areas where I explicitly want the reviewer's opinion because I don't have high confidence:

1. **Should `DraftStore` be in `persistence.py` or its own file?** I'm leaning toward `spine_api/draft_store.py` for modularity, but `persistence.py` already has the file-lock utilities.

2. **Should the frontend cache draft state locally (localStorage) as a fallback?** If the backend save fails, should the frontend keep the draft in localStorage and retry? Or is that over-engineering?

3. **How should we handle draft cleanup?** Discarded drafts should probably be kept for 30 days (for audit), then archived or deleted. Should this be a cron job, a background thread, or manual admin action?

4. **Should draft names be searchable?** If yes, the index should include a `name` field. If no, we can skip it for now.

---

*End of review packet.*
