# Draft System — Architecture & Data Model

> Research document for the Draft as a first-class persistent workspace — data model, storage architecture, API surface, and integration with existing systems.

---

## Key Questions

1. **What is a Draft — its data model and lifecycle?**
2. **How should Drafts be stored — JSON files, SQL, or hybrid?**
3. **What API surface does the Draft system expose?**
4. **How does it integrate with existing RunLedger, AuditStore, and TripStore?**

---

## Background: Current Architecture

```
Existing Storage Patterns:
├── TripStore:     Dual backend (JSON files + PostgreSQL via SQLAlchemy)
│                  data/trips/trip_{id}.json OR SQL trips table
├── RunLedger:     JSON files per run
│                  data/runs/{run_id}/meta.json + steps/*.json + events.jsonl
├── AuditStore:    Append-only JSONL file
│                  data/audit/events.json (rotation at 10K events)
└── Workbench:     In-memory Zustand store (LOST on refresh)
```

**Gap:** No persistence between "open workbench" and "trip created." Agents lose work on refresh. This is the problem the Draft system solves.

---

## Research Areas

### Data Model

```typescript
interface Draft {
  id: string;                           // nanoid, e.g., "dft_abc123"
  agency_id: string;
  created_by: string;                   // agent user_id
  created_at: string;                   // ISO 8601
  updated_at: string;
  status: DraftStatus;

  // Identity
  name: string;                         // auto-generated, editable
  name_source: "CUSTOMER_MSG" | "AGENT_NOTE" | "AUTO";

  // Workbench input state (the "what the agent typed" fields)
  customer_message: string | null;
  agent_notes: string | null;
  structured_json: Record<string, unknown> | null;
  itinerary_text: string | null;

  // Configuration (from Settings panel)
  stage: string;                        // "discovery" | "shortlist" | etc.
  operating_mode: string;               // "normal_intake" | "audit" | etc.
  scenario_id: string | null;
  strict_leakage: boolean;

  // Last run snapshot (so UI can show status without re-querying run)
  last_run_id: string | null;
  last_run_state: string | null;        // "completed" | "blocked" | "failed"
  last_validation: Record<string, unknown> | null;
  last_run_at: string | null;

  // Promotion
  promoted_trip_id: string | null;
  promoted_at: string | null;

  // Relationships
  linked_draft_ids: string[];           // other drafts for same customer
  linked_trip_ids: string[];            // existing trips for same customer
  transferred_from_agent: string | null; // if draft was reassigned
}

type DraftStatus =
  | "open"            // agent is working, no run yet
  | "processing"      // run in progress
  | "blocked"         // last run blocked (validation failed)
  | "failed"          // last run failed (system error)
  | "promoted"        // successfully created a trip
  | "discarded";      // agent deleted the draft
```

### Storage Architecture — First Principles Analysis

```
Access Pattern Analysis for Drafts:

Operation           | Frequency  | Pattern          | Best Storage
──────────────────────────────────────────────────────────────────
Create draft        | High       | Single insert    | SQL + JSON
Save draft          | Very High  | Update by ID     | SQL + JSON
List drafts         | Moderate   | Filter by agency | SQL (indexed)
Filter by status    | Moderate   | WHERE status=    | SQL (indexed)
Filter by agent     | Moderate   | WHERE created_by= | SQL (indexed)
Load single draft   | High       | Single read      | JSON file
Search by name      | Low        | Full-text search | SQL (LIKE/FTS)
Bulk cleanup        | Low        | DELETE old       | SQL
Link/merge          | Low        | Update relations | SQL

Conclusion: HYBRID (same as TripStore)
- SQL for metadata (listing, filtering, status, relations)
- JSON for full payload (customer_message, structured_json, validation snapshot)
- Why: Drafts need relational queries ("show all blocked drafts for agency X")
  that JSON files can't do efficiently. But customer_message can be large
  (full WhatsApp conversations pasted), so keeping it in SQL bloats the table.
```

```
Storage Layout:

data/drafts/
├── meta.db                    # SQLite for metadata (or PostgreSQL)
│   └── drafts table           # id, status, name, agent, timestamps, refs
│
├── draft_{id}.json            # Full payload (like trip JSON files)
│   ├── customer_message
│   ├── agent_notes
│   ├── structured_json
│   ├── itinerary_text
│   ├── last_validation
│   └── config
│
└── draft_{id}_autosave.json   # Auto-save staging (atomic swap on save)

SQL Schema (metadata):
CREATE TABLE drafts (
    id VARCHAR(36) PRIMARY KEY,
    agency_id VARCHAR(36) NOT NULL REFERENCES agencies(id),
    created_by VARCHAR(36) NOT NULL REFERENCES users(id),
    name VARCHAR(200) NOT NULL,
    status VARCHAR(20) DEFAULT 'open',
    stage VARCHAR(30) DEFAULT 'discovery',
    operating_mode VARCHAR(30) DEFAULT 'normal_intake',

    last_run_id VARCHAR(36),
    last_run_state VARCHAR(20),

    promoted_trip_id VARCHAR(36),

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    INDEX idx_drafts_agency_status (agency_id, status),
    INDEX idx_drafts_created_by (created_by),
    INDEX idx_drafts_promoted (promoted_trip_id)
);
```

### Why Not JSON-Only (Like RunLedger)?

```
RunLedger uses JSON files because:
  ✅ Single-key lookup (always by run_id)
  ✅ Write-once per step (append-only)
  ✅ Never needs listing/filtering
  ✅ Query pattern: "give me run_abc123"

Drafts are DIFFERENT:
  ❌ Need listing: "Show me all my drafts"
  ❌ Need filtering: "Show blocked drafts only"
  ❌ Need relational: "Which draft promoted to TRIP-442?"
  ❌ Need multi-agent: "Who else has drafts for this customer?"
  ❌ Need cleanup: "Delete drafts older than 30 days"

JSON files can't do these efficiently without loading ALL files.
SQL gives us indexed queries for free.
```

### API Surface

```
Draft CRUD:
POST   /api/drafts                         → Create new draft
GET    /api/drafts                         → List drafts (filterable)
GET    /api/drafts/{id}                    → Load full draft state
PUT    /api/drafts/{id}                    → Save draft (inputs + config)
PATCH  /api/drafts/{id}                    → Partial update (auto-save)
DELETE /api/drafts/{id}                    → Discard draft

Draft Actions:
POST   /api/drafts/{id}/process            → Run spine against this draft
GET    /api/drafts/{id}/events             → Audit timeline (draft-era)
GET    /api/drafts/{id}/runs               → All runs linked to this draft
POST   /api/drafts/{id}/promote            → Mark as promoted (link to trip)
POST   /api/drafts/{id}/transfer           → Reassign to another agent
POST   /api/drafts/{id}/link               → Link to another draft/trip
POST   /api/drafts/{id}/merge              → Merge with another draft
PATCH  /api/drafts/{id}/name               → Rename draft

Integration Endpoints:
GET    /api/trips/{id}/draft-history       → Draft-era events for promoted trip
GET    /api/runs/{id}/draft                → Which draft spawned this run
```

### Integration with Existing Systems

```typescript
// ── Integration touchpoints ──
// ┌─────────────────────────────────────────────────────┐
// │  System         | Change Needed                      │
// │  ─────────────────────────────────────────────────── │
// │  AuditStore     | Events keyed by draft_id (new).   │
// │                 | get_events(trip_id) transparently │
// │                 | looks up draft_id, includes both.  │
// │                                                       │
// │  RunLedger      | Run metadata adds draft_id field. │
// │                 | Runs queryable by draft_id.        │
// │                                                       │
// │  TripStore      | On successful run, trip creation  │
// │                 | records source_draft_id.           │
// │                 | Trip model gets optional draft_id. │
// │                                                       │
// │  Timeline API   | /trips/{id}/timeline includes     │
// │                 | draft-era events (draft_created,   │
// │                 | draft_saved, run_blocked, etc.)    │
// │                                                       │
// │  Process Log    | Process log events get draft_id   │
// │                 | context. Draft-era events visible  │
// │                 | in process log panel.              │
// │                                                       │
// │  Workbench UI   | Zustand store loads from draft API│
// │                 | instead of starting empty.         │
// │                 | URL becomes ?draft=abc123.         │
// └─────────────────────────────────────────────────────┘
```

---

## Open Problems

1. **Dual-backend complexity** — TripStore already maintains JSON+SQL sync. Adding the same for Drafts doubles the maintenance. Consider: SQL-only for drafts (simpler) since drafts don't need the file-backend fallback.

2. **Auto-save atomicity** — Auto-save writes must be atomic (don't corrupt if browser closes mid-write). Use write-to-temp-then-rename pattern.

3. **Large payloads** — Customer messages can be 10KB+ (full WhatsApp exports). Need to decide if SQL JSON column handles this or if file storage is mandatory for payload.

4. **Draft → Trip transition** — When a draft is promoted, should the draft be archived (read-only) or deleted? Recommendation: archive, keep for audit trail.

---

## Next Steps

- [ ] Finalize storage decision (SQL-only vs hybrid)
- [ ] Implement DraftStore backend (SQL metadata + JSON payload)
- [ ] Create Draft API endpoints
- [ ] Integrate draft_id into RunLedger and AuditStore
