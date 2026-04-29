# Draft System — Lifecycle & State Machine

> Research document for the Draft lifecycle — state transitions, auto-save behavior, promotion workflow, and the seamless draft→trip timeline.

---

## Key Questions

1. **What states does a Draft go through?**
2. **How does auto-save work with the state machine?**
3. **What happens when a draft promotes to a trip?**
4. **How does the draft-era timeline merge with the trip timeline?**

---

## Research Areas

### Draft State Machine

```
                    ┌──────────┐
                    │          │
      Create ──────►│   OPEN   │◄─────── Re-open (undo discard)
                    │          │
                    └────┬─────┘
                         │ Process clicked
                         ▼
                    ┌──────────┐
                    │          │
                    │PROCESSING│
                    │          │
                    └──┬───┬───┘
                       │   │
            Success    │   │ Blocked / Failed
                       │   │
                       │   ▼
                       │  ┌──────────┐     ┌──────────┐
                       │  │          │     │          │
                       │  │ BLOCKED  │────►│   OPEN   │ (agent fixes)
                       │  │          │     │          │
                       │  └──────────┘     └──────────┘
                       │
                       │  ┌──────────┐     ┌──────────┐
                       │  │          │     │          │
                       │  │ FAILED   │────►│   OPEN   │ (agent retries)
                       │  │          │     │          │
                       │  └──────────┘     └──────────┘
                       │
                       ▼
                  ┌──────────┐
                  │          │
                  │ PROMOTED │ ──── immutable, linked to trip_id
                  │          │
                  └──────────┘

                  ┌──────────┐
       Discard ──►│          │
                  │DISCARDED │ ──── soft delete, recoverable 7 days
                  │          │
                  └──────────┘
```

### Auto-Save Design

```typescript
interface AutoSaveConfig {
  // Timing
  debounce_ms: number;                  // 5000ms (5 seconds)
  min_content_length: number;           // 10 chars (don't save "hi")

  // Guards — skip auto-save if all conditions true
  skip_conditions: {
    all_fields_empty: boolean;          // skip if nothing meaningful
    unchanged_since_last_save: boolean; // skip if no edits
    draft_is_processing: boolean;       // skip during active run
    draft_is_promoted: boolean;         // skip after promotion
  };

  // Visual feedback
  status_display: {
    idle: null;                         // no indicator
    typing: null;                       // still typing, no indicator
    pending: "Saving...";               // debounce timer active
    saving: "Saving...";                // API call in flight
    saved: "Saved at 10:32 AM";         // success, show timestamp
    error: "Save failed — click to retry"; // error state
  };
}

// ── Auto-save flow ──
// ┌─────────────────────────────────────────────────────┐
// │  Auto-Save Trigger Logic                              │
// │                                                       │
// │  Agent types in customer_message field               │
// │     │                                                 │
// │     ├── Is draft processing? → SKIP                  │
// │     ├── Is draft promoted? → SKIP                    │
// │     ├── Is content empty/whitespace? → SKIP          │
// │     ├── Is content unchanged since last save? → SKIP │
// │     │                                                 │
// │     └── All guards pass → Start 5s debounce timer    │
// │         │                                             │
// │         ├── Agent keeps typing → Reset timer         │
// │         ├── Agent clicks Save Draft → Cancel timer,  │
// │         │                              save immediately│
// │         └── 5s passes with no changes → Auto-save    │
// │             │                                         │
// │             ├── PATCH /api/drafts/{id} (partial)     │
// │             │   body: { customer_message: "..." }    │
// │             ├── Success → "Saved at 10:32 AM"       │
// │             └── Error → "Save failed" (retry on next │
// │                        change or manual click)        │
// │                                                       │
// │  Explicit "Save Draft" button:                        │
// │  • Always available (even during auto-save pending)  │
// │  • Cancels any pending auto-save debounce            │
// │  • Sends PUT /api/drafts/{id} (full save)            │
// │  • Shows confirmation: "Draft saved"                 │
// └─────────────────────────────────────────────────────┘
```

### Draft Naming Logic

```typescript
interface DraftNamingEngine {
  generateName(draft: Draft): string;
  updateNameOnEdit(draft: Draft, field: string, value: string): string | null;
}

// ── Naming logic ──
// ┌─────────────────────────────────────────────────────┐
// │  Draft Name Generation                                │
// │                                                       │
// │  Priority 1: First line of customer_message           │
// │  "Hi, I want to plan a Singapore trip for my family" │
// │  → "Singapore trip for my family"                    │
// │  (strip greeting, truncate at 60 chars)              │
// │                                                       │
// │  Priority 2: First line of agent_notes                │
// │  (if no customer_message)                             │
// │  "Ravi Sharma callback, Kerala backwaters enquiry"   │
// │  → "Ravi Sharma callback, Kerala..."                  │
// │                                                       │
// │  Priority 3: Timestamp fallback                       │
// │  → "Draft - Apr 29, 10:32 AM"                        │
// │                                                       │
// │  Name updates:                                        │
// │  • Auto-updates while name_source = AUTO              │
// │  • Once agent manually edits name → name_source =    │
// │    MANUAL, stops auto-updating                        │
// │  • Agent can always rename (editable field)           │
// │                                                       │
// │  Display:                                             │
// │  • In sidebar list: full name (max 60 chars)         │
// │  • In workbench header: full name + status badge     │
// │  • In URL: ?draft=abc123 (never the name)             │
// └─────────────────────────────────────────────────────┘
```

### Promotion Workflow

```typescript
interface DraftPromotion {
  draft_id: string;
  trip_id: string;
  promoted_at: string;

  // What happens on promotion
  steps: {
    // 1. Run completes successfully
    run_completed: {
      run_id: string;
      trip_id: string;                  // newly created trip
    };

    // 2. Draft status → PROMOTED
    draft_update: {
      status: "promoted";
      promoted_trip_id: trip_id;
      promoted_at: ISO_timestamp;
    };

    // 3. Draft becomes immutable
    freeze: {
      no_more_edits: true;
      no_more_runs: true;
      auto_save_disabled: true;
    };

    // 4. Audit trail stitching
    audit_stitch: {
      // All draft-era events now linked to trip_id too
      // get_events(trip_id) → includes draft_created, draft_saved, run_blocked, etc.
      // get_events(draft_id) → same events, keyed by draft_id
    };

    // 5. Timeline merge
    timeline_merge: {
      // Trip timeline starts with draft-era events
      // Seamless: "Draft created → Customer message → Run 1 (blocked) →
      //   Field edited → Run 2 (success) → Trip created → ..."
    };

    // 6. UI transition
    ui_transition: {
      // Workbench URL changes: ?draft=abc123 → /workspace/{tripId}/intake
      // Draft sidebar item shows "Promoted → TRIP-442"
      // Agent auto-navigated to full workspace
    };
  };
}

// ── Promotion flow ──
// ┌─────────────────────────────────────────────────────┐
// │  Draft → Trip Promotion                               │
// │                                                       │
// │  Draft: dft_abc123 (status: processing)              │
// │     │                                                 │
// │     ├── Run completes successfully                   │
// │     │   run_id: run_xyz789                           │
// │     │   trip_id: WP-442 (newly created)              │
// │     │                                                 │
// │     ├── Draft.promote("WP-442")                      │
// │     │   status → "promoted"                          │
// │     │   promoted_trip_id → "WP-442"                  │
// │     │   freeze → immutable                           │
// │     │                                                 │
// │     ├── AuditStore.stitch(draft_id, trip_id)         │
// │     │   All draft-era events now also keyed by trip  │
// │     │                                                 │
// │     ├── Timeline API merge                           │
// │     │   /api/trips/WP-442/timeline includes:         │
// │     │   ├── Draft created (10:30 AM)                │
// │     │   ├── Customer message saved (10:31 AM)       │
// │     │   ├── Run 1: blocked - NB01 (10:32 AM)        │
// │     │   ├── Field edited: destination (10:35 AM)    │
// │     │   ├── Run 2: completed (10:38 AM)             │
// │     │   └── Trip created (10:38 AM) ← standard timeline│
// │     │                                                 │
// │     └── UI transition                                │
// │         URL: ?draft=abc123 → /workspace/WP-442/intake│
// │         Sidebar: "Draft → Promoted → WP-442"        │
// └─────────────────────────────────────────────────────┘
```

### Draft-Era Event Taxonomy

```typescript
type DraftEventType =
  | "draft_created"            // auto-created when workbench opens
  | "draft_saved"              // explicit or auto-save
  | "draft_renamed"            // agent changed the name
  | "draft_input_changed"      // customer_message, agent_notes, etc.
  | "draft_config_changed"     // stage, mode, scenario changed
  | "draft_run_started"        // process button clicked
  | "draft_run_blocked"        // run returned blocked
  | "draft_run_failed"         // run returned error
  | "draft_run_completed"      // run succeeded
  | "draft_promoted"           // trip created from draft
  | "draft_transferred"        // reassigned to another agent
  | "draft_linked"             // linked to another draft/trip
  | "draft_merged"             // merged with another draft
  | "draft_discarded"          // agent deleted the draft
  | "draft_recovered";         // discarded draft recovered

// ── Draft-era timeline view ──
// ┌─────────────────────────────────────────────────────┐
// │  Draft Timeline (before trip existed)                  │
// │                                                       │
// │  10:30:00  📝 Draft created                           │
// │            Auto-named: "Singapore trip for family"    │
// │                                                       │
// │  10:30:45  💬 Customer message saved                  │
// │            "Planning a Singapore trip, 4 travelers..." │
// │                                                       │
// │  10:31:02  📋 Agent notes added                       │
// │            "Budget ~₹3.5L, family with 2 kids"       │
// │                                                       │
// │  10:31:30  ▶️ Run started (discovery/normal_intake)   │
// │            → run_abc123                               │
// │                                                       │
// │  10:32:15  ❌ Run blocked — Gate NB01                 │
// │            Missing: destination, travel_dates         │
// │            → Agent goes to lunch                      │
// │                                                       │
// │  ──── 2 hours later ────                              │
// │                                                       │
// │  12:45:00  🔄 Draft opened (agent returns)            │
// │            State restored from save                   │
// │                                                       │
// │  12:45:30  ✏️ Field edited: destination → Singapore   │
// │  12:45:45  ✏️ Field edited: dates → Jun 1-6, 2026    │
// │  12:46:00  💾 Draft saved                             │
// │                                                       │
// │  12:46:10  ▶️ Run started (retry)                     │
// │            → run_def456                               │
// │                                                       │
// │  12:48:30  ✅ Run completed — Packet generated        │
// │            4 travelers, Singapore, ₹3.85L            │
// │                                                       │
// │  12:48:31  🎉 Draft promoted → Trip WP-442            │
// │            Auto-navigated to workspace                │
// └─────────────────────────────────────────────────────┘
```

---

## Open Problems

1. **Auto-save vs run conflict** — If auto-save fires while a run is processing, it could overwrite in-flight state. Solution: skip auto-save during `status: processing`.

2. **Draft retention for promoted drafts** — Should promoted drafts be kept forever (for audit) or archived after 90 days? Recommendation: keep permanently as immutable audit records.

3. **Draft versioning depth** — Every auto-save creates state. Should we keep full version history (like Google Docs) or just the last state? Recommendation: just last state + event log (draft_saved events capture timestamps).

4. **Multiple tabs** — Agent opens same draft in two tabs. Last-write-wins? Or detect conflict? Recommendation: optimistic locking with `updated_at` timestamp.

---

## Next Steps

- [ ] Implement draft state machine with transition guards
- [ ] Build auto-save engine with debouncing and content guards
- [ ] Create draft naming engine with auto-generation
- [ ] Implement promotion workflow with audit stitching
- [ ] Build draft-era event taxonomy in AuditStore
