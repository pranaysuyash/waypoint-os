# Process Log & History Capture — UI Design

> Research document for the process log UI — expandable log entries, detail panels, history linking, filter/search, and the "DevTools for agents" experience.

---

## Key Questions

1. **How should the process log be displayed in the workspace?**
2. **What does expandable detail look like for each event type?**
3. **How do log entries link to related entities (trips, runs, old tickets)?**
4. **What filtering and search capabilities are needed?**

---

## Research Areas

### Process Log Panel Design

```typescript
// ── Process log panel — positioned as a collapsible bottom/side panel ──
// ┌─────────────────────────────────────────────────────┐
// │  Process History                              [▼ Hide]│
// │  ┌───────────────────────────────────────────────┐   │
// │  │  Filter: [All ▼] [This Session ▼] [🔍 Search] │   │
// │  │                                               │   │
// │  │  14:32:05  ✅ MILESTONE  Packet generated      │   │
// │  │           4 travelers, ₹3.5L budget          │   │
// │  │                                               │   │
// │  │  14:31:58  🔄 SYSTEM   Spine run completed    │   │
// │  │           run_abc123 · 3.2s · discovery       │   │
// │  │                                               │   │
// │  │  14:31:52  🔄 SYSTEM   Pipeline: intake → ... │   │
// │  │           Stage transition triggered          │   │
// │  │                                               │   │
// │  │  14:31:48  ❌ ERROR    Validation failed       │   │
// │  │           Gate NB01: Missing destination ▾    │   │
// │  │           ┌─ Expanded Detail ──────────────┐  │   │
// │  │           │ Gate: NB01 (Basic Validation)  │  │   │
// │  │           │ Status: BLOCKED                │  │   │
// │  │           │ Reasons:                       │  │   │
// │  │           │  1. Destination is required    │  │   │
// │  │           │  2. Travel dates are missing   │  │   │
// │  │           │ Fields: destination, dates     │  │   │
// │  │           │                                │  │   │
// │  │           │ [Fix in Packet Tab →]           │  │   │
// │  │           │ Related: run_abc123             │  │   │
// │  │           └────────────────────────────────┘  │   │
// │  │                                               │   │
// │  │  14:31:45  📝 EDIT      destination: "" → ... │   │
// │  │           Field updated in packet form        │   │
// │  │                                               │   │
// │  │  14:31:30  ▶️ ACTION   Process Trip clicked   │   │
// │  │           discovery · normal_intake ▾         │   │
// │  │           ┌─ Expanded Detail ──────────────┐  │   │
// │  │           │ Input:                         │  │   │
// │  │           │  raw_note: "Singapore trip..."  │  │   │
// │  │           │  stage: discovery               │  │   │
// │  │           │  mode: normal_intake            │  │   │
// │  │           │  scenario: (none)               │  │   │
// │  │           │                                │  │   │
// │  │           │ Actor: Priya (Agent)           │  │   │
// │  │           │ Component: WorkbenchPage        │  │   │
// │  │           │                                │  │   │
// │  │           │ [View Run →] run_abc123         │  │   │
// │  │           └────────────────────────────────┘  │   │
// │  │                                               │   │
// │  │  14:30:12  🔄 SYSTEM   Trip data loaded       │   │
// │  │           WP-442 · Singapore Family Trip      │   │
// │  │                                               │   │
// │  │  14:30:10  🔄 SYSTEM   Store hydrated          │   │
// │  │           Populated from trip WP-442          │   │
// │  └───────────────────────────────────────────────┘   │
// │  Showing 8 events · Total: 47 · [Load More]          │
// └─────────────────────────────────────────────────────┘
```

### Expandable Detail Views

```typescript
// ── Detail views per event type ──

// ACTION event expanded
// ┌─────────────────────────────────────────────────────┐
// │  ▶️ Process Trip clicked                    14:31:30 │
// │  ─────────────────────────────────────────────────── │
// │  Input:                                              │
// │  ┌──────────────────────────────────────────────┐   │
// │  │ {                                             │   │
// │  │   "raw_note": "Planning a Singapore trip...", │   │
// │  │   "stage": "discovery",                       │   │
// │  │   "operating_mode": "normal_intake",           │   │
// │  │   "strict_leakage": false                     │   │
// │  │ }                                             │   │
// │  └──────────────────────────────────────────────┘   │
// │                                                       │
// │  Context:                                             │
// │  • Actor: Priya Sharma (agent_042)                   │
// │  • Component: WorkbenchPage > ProcessButton          │
// │  • Pipeline: intake stage                            │
// │  • Session: sess_abc123                              │
// │                                                       │
// │  Timeline:                                            │
// │  → 14:31:30 Action triggered                         │
// │  → 14:31:31 API call started (spine_run)             │
// │  → 14:31:34 API response received (200 OK)           │
// │  → 14:31:34 Run created: run_abc123                  │
// │  → 14:31:52 Pipeline stage changed: intake → packet  │
// │  → 14:31:58 Run completed (success)                  │
// │  → 14:32:05 Packet generated (milestone)             │
// │                                                       │
// │  Links:                                               │
// │  [View Run: run_abc123 →]                            │
// │  [View Trip: WP-442 →]                               │
// │  [Replay This Action]                                │
// └─────────────────────────────────────────────────────┘

// ERROR event expanded
// ┌─────────────────────────────────────────────────────┐
// │  ❌ Validation failed                       14:31:48 │
// │  ─────────────────────────────────────────────────── │
// │  Gate: NB01 (Basic Validation)                       │
// │  Status: BLOCKED                                     │
// │  Severity: ERROR                                     │
// │                                                       │
// │  Reasons:                                             │
// │  1. "Destination is required"                        │
// │     → Field: destination                             │
// │     → Fix: Add destination in Packet tab             │
// │  2. "Travel dates are required"                      │
// │     → Field: travel_dates                            │
// │     → Fix: Add dates in Packet tab                   │
// │                                                       │
// │  Validation payload:                                  │
// │  ┌──────────────────────────────────────────────┐   │
// │  │ {                                             │   │
// │  │   "status": "BLOCKED",                        │   │
// │  │   "gate": "NB01",                             │   │
// │  │   "is_valid": false,                          │   │
// │  │   "reasons": ["...","..."]                    │   │
// │  │ }                                             │   │
// │  └──────────────────────────────────────────────┘   │
// │                                                       │
// │  Actions:                                             │
// │  [Go to Packet Tab →]                                │
// │  [Retry After Fix]                                   │
// │  [Dismiss Error]                                     │
// │                                                       │
// │  Related:                                             │
// │  Parent: Process Trip (14:31:30)                     │
// │  Run: run_abc123                                     │
// └─────────────────────────────────────────────────────┘

// DATA_EDIT event expanded (compact)
// ┌─────────────────────────────────────────────────────┐
// │  📝 destination edited                      14:31:45 │
// │  ─────────────────────────────────────────────────── │
// │  Before: (empty)                                     │
// │  After:  "Singapore"                                 │
// │  Source: PacketTab > DestinationField                │
// │  [View Full Diff]                                    │
// └─────────────────────────────────────────────────────┘
```

### History Linking & Cross-References

```typescript
// ── Cross-reference navigation ──
// ┌─────────────────────────────────────────────────────┐
// │  History Linking Patterns                             │
// │                                                       │
// │  1. Run → Trip link                                  │
// │     Log entry for "Spine run created" shows:         │
// │     → run_abc123 [View Run]                          │
// │     → WP-442 [View Trip] (if trip was created)       │
// │                                                       │
// │  2. Error → Fix → Retry chain                        │
// │     Log entry for error shows:                       │
// │     → [View Edit] that fixed it                      │
// │     → [View Retry] that succeeded                    │
// │     Full chain: Error → Edit → Retry → Success      │
// │                                                       │
// │  3. Current trip → Previous runs                     │
// │     Process log shows all runs for this trip:         │
// │     Run 1: 14:31 (failed, validation)                │
// │     Run 2: 14:45 (success) ← current                │
// │     [View full run history →]                        │
// │                                                       │
// │  4. Old ticket reference                              │
// │     When re-processing a trip, show link:             │
// │     "Previously processed on Apr 25 as run_xyz789"   │
// │     [View Previous Run →]                            │
// │     [Compare Current vs Previous]                    │
// │                                                       │
// │  5. Related entity drill-down                         │
// │     Clicking [View Trip] on a run event:             │
// │     → Navigates to /workspace/{tripId}/intake        │
// │     Clicking [View Run] on a trip event:             │
// │     → Opens run detail modal with full run status    │
// └─────────────────────────────────────────────────────┘
```

### Filtering & Search

```typescript
interface ProcessLogFilter {
  // Category filter
  categories: ProcessLogEventCategory[];

  // Severity filter
  min_severity: "DEBUG" | "INFO" | "WARN" | "ERROR" | "CRITICAL";

  // Time range
  time_range: "THIS_SESSION" | "LAST_HOUR" | "TODAY" | "THIS_TRIP" | "CUSTOM";

  // Source filter
  sources: string[];                    // component names

  // Actor filter
  actor: string | null;

  // Search
  search_query: string;                 // full-text search in summaries, details

  // Entity filter
  linked_entity_type: "TRIP" | "RUN" | "ALL";
  linked_entity_id: string | null;
}

// ── Filter bar design ──
// ┌─────────────────────────────────────────────────────┐
// │  Process History                                [⚙️]  │
// │                                                       │
// │  [All Categories ▼] [≥ INFO ▼] [This Session ▼]     │
// │  [🔍 Search events...]                               │
// │                                                       │
// │  Quick filters:                                       │
// │  [Errors Only] [Actions Only] [My Actions] [Edits]   │
// │                                                       │
// │  Active filters: Errors + This Session               │
// │  Showing 3 of 8 events                               │
// │  ...                                                  │
// └─────────────────────────────────────────────────────┘
```

### Panel Placement Options

```typescript
// ── Three placement options ──
// ┌─────────────────────────────────────────────────────┐
// │  Option A: Bottom Panel (IDE-style, like DevTools)   │
// │  ┌───────────────────────────────────────────────┐   │
// │  │  Workspace Content (tabs, forms, panels)       │   │
// │  │                                                │   │
// │  │                                                │   │
// │  ├───────────────────────────────────────────────┤   │
// │  │  Process History ▲  (draggable resize)         │   │
// │  │  14:32 ✅ Milestone  14:31 ❌ Error  ...       │   │
// │  │                                                │   │
// │  └───────────────────────────────────────────────┘   │
// │  Best for: debugging, developer experience           │
// │                                                       │
// │  Option B: Right Sidebar (collapsible)               │
// │  ┌────────────────────────────┬──────────────────┐   │
// │  │  Workspace Content          │ Process History  │   │
// │  │                             │ 14:32 ✅ Mile... │   │
// │  │                             │ 14:31 ❌ Error   │   │
// │  │                             │                  │   │
// │  └────────────────────────────┴──────────────────┘   │
// │  Best for: always-visible status, monitoring          │
// │                                                       │
// │  Option C: Dedicated Tab                              │
// │  [Intake] [Packet] [Decision] [Strategy] [History]   │
// │  ┌───────────────────────────────────────────────┐   │
// │  │  Full-page process history view                │   │
// │  │  With advanced filtering, timeline, replay     │   │
// │  └───────────────────────────────────────────────┘   │
// │  Best for: detailed investigation, audit review       │
// └─────────────────────────────────────────────────────┘
```

---

## Open Problems

1. **Log overflow** — A single "Process Trip" click generates 8-15 events. Over a full session, this can be hundreds. Need smart grouping (collapse related events under a parent).

2. **Detail vs summary** — The expanded view for an API call could include the entire request/response JSON. Need truncation with "load full" option.

3. **Panel real estate** — The workspace already has many panels competing for space. The process log needs to be non-intrusive but accessible.

4. **Cross-session history** — When a user returns to a trip, should they see the previous session's process log? Requires server-side persistence of client events.

---

## Next Steps

- [ ] Design the process log panel component with expandable entries
- [ ] Create detail views for each event category
- [ ] Implement cross-reference linking (run → trip → old ticket)
- [ ] Build filtering and full-text search
- [ ] Choose and implement panel placement strategy
