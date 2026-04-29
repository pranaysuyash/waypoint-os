# Process Log & History Capture — Event Taxonomy

> Research document for workspace-level event capture taxonomy — every button click, API call, state transition, error, and user interaction logged as a queryable, expandable process history.

---

## Key Questions

1. **What events must be captured at the workspace level?**
2. **How do we categorize events for filtering and search?**
3. **What metadata must each event carry?**
4. **How does this relate to the existing Timeline and Audit systems?**

---

## Research Areas

### Event Categories

```typescript
type ProcessLogEventCategory =
  | "USER_ACTION"       // Button click, form submit, tab switch
  | "SYSTEM_RESPONSE"   // API response, run completion, validation result
  | "ERROR"             // Failed API call, validation error, timeout
  | "STATE_CHANGE"      // Store update, pipeline stage transition
  | "DATA_EDIT"         // Field change, form edit, structured JSON update
  | "NAVIGATION"        // Tab switch, page navigation, deep link
  | "EXTERNAL_EVENT"    // Webhook, push notification, real-time update
  | "RECOVERY"          // Retry, fallback, error dismissal
  | "INSIGHT"           // AI-generated observation, suggestion, warning
  | "MILESTONE"         // Pipeline stage completed, trip created, output generated;

interface ProcessLogEvent {
  id: string;
  trip_id: string | null;
  run_id: string | null;               // spine run ID if applicable
  session_id: string;                  // browser session

  // Classification
  category: ProcessLogEventCategory;
  action: string;                      // "process_trip_clicked", "validation_failed"
  label: string;                       // Human-readable: "Process Trip button clicked"
  severity: "DEBUG" | "INFO" | "WARN" | "ERROR" | "CRITICAL";

  // Timing
  timestamp: string;
  duration_ms: number | null;          // for actions that take time (API calls)

  // Actor
  actor_type: "USER" | "SYSTEM" | "AI_AGENT";
  actor_id: string | null;             // user ID or agent ID
  actor_label: string;                 // "Priya (Agent)" or "Spine Pipeline"

  // Context
  source_component: string;            // "WorkbenchPage", "IntakeTab", "PacketTab"
  source_location: string;             // "process_button", "raw_note_field"
  pipeline_stage: string | null;       // "intake", "packet", "decision", etc.

  // Payload (expandable detail)
  summary: string;                     // one-line summary shown in log
  detail: {
    input?: unknown;                   // what was sent/submitted
    output?: unknown;                  // what came back
    error?: {
      message: string;
      code: string | null;
      stack?: string;                  // only in dev mode
      recoverable: boolean;
    };
    metadata?: Record<string, unknown>;
  };

  // Linking
  related_events: string[];            // IDs of related events
  parent_event_id: string | null;      // for sub-events (e.g., stages within a run)
  linked_entity: {
    type: "TRIP" | "RUN" | "ENQUIRY" | "BOOKING" | null;
    id: string | null;
  };
}

// ── Event examples from the workbench ──
// ┌─────────────────────────────────────────────────────┐
// │  Sample Process Log Events                            │
// │                                                       │
// │  #1  USER_ACTION  "Process Trip button clicked"      │
// │      input: { raw_note: "Singapore trip...",          │
// │               stage: "discovery", mode: "normal" }   │
// │      actor: Priya (Agent)                            │
// │      stage: intake → (triggering pipeline)           │
// │                                                       │
// │  #2  SYSTEM_RESPONSE  "Spine run created"            │
// │      output: { run_id: "run_abc123", status: "queued"}│
// │      parent: #1                                      │
// │      duration: 340ms (API call)                      │
// │                                                       │
// │  #3  STATE_CHANGE  "Pipeline stage: intake → packet" │
// │      linked: run_abc123                              │
// │      parent: #2                                      │
// │                                                       │
// │  #4  ERROR  "Validation failed: missing destination" │
// │      detail: { gate: "NB01", reasons: [...],         │
// │                fields: ["destination"] }              │
// │      linked: run_abc123                              │
// │      severity: ERROR                                 │
// │      parent: #2                                      │
// │                                                       │
// │  #5  DATA_EDIT  "Field edited: destination"          │
// │      detail: { field: "destination",                 │
// │                from: null, to: "Singapore" }          │
// │      actor: Priya (Agent)                            │
// │                                                       │
// │  #6  USER_ACTION  "Process Trip re-clicked"          │
// │      parent: #1 (retry after fixing)                 │
// │      related: [#4, #5]                               │
// │                                                       │
// │  #7  MILESTONE  "Packet generated successfully"      │
// │      detail: { travelers: 4, budget: "₹3.5L" }      │
// │      linked: run_def456                              │
// │                                                       │
// │  #8  USER_ACTION  "Saved trip"                       │
// │      detail: { trip_id: "WP-442" }                   │
// │      linked: { type: "TRIP", id: "WP-442" }         │
// └─────────────────────────────────────────────────────┘
```

### Specific Workbench Event Catalog

```typescript
// ── Complete event catalog for the Workbench page ──
// ┌─────────────────────────────────────────────────────┐
// │  Event Catalog: Workbench                             │
// │                                                       │
// │  USER_ACTION events:                                  │
// │  • process_trip_clicked     — Process button clicked │
// │  • save_clicked             — Save button clicked    │
// │  • reset_clicked            — Reset button clicked   │
// │  • settings_opened          — Settings panel opened  │
// │  • resolve_clicked          — Recovery resolve btn   │
// │  • tab_changed              — Workspace tab switch   │
// │  • view_trip_clicked        — "View Trip" button     │
// │  • retry_clicked            — Retry after error      │
// │  • scenario_selected        — Scenario lab pick      │
// │                                                       │
// │  SYSTEM_RESPONSE events:                              │
// │  • spine_run_created        — Run submitted to API   │
// │  • spine_run_polling        — Status poll response   │
// │  • spine_run_completed      — Run finished           │
// │  • spine_run_blocked        — Run blocked (validation│
// │  • spine_run_failed         — Run failed             │
// │  • trip_saved               — Save API response      │
// │  • trip_loaded              — Initial trip data load │
// │  • store_hydrated           — Store populated        │
// │  • validation_updated       — Validation result recv │
// │  • packet_updated           — Packet data received   │
// │                                                       │
// │  ERROR events:                                        │
// │  • api_error                — API call failed        │
// │  • validation_error         — Validation blocked     │
// │  • save_error               — Save failed            │
// │  • load_error               — Trip load failed       │
// │  • parse_error              — JSON parse failed      │
// │  • timeout_error            — Request timed out      │
// │  • network_error            — Network unavailable    │
// │  • rate_limit_error         — 429 Too Many Requests  │
// │                                                       │
// │  STATE_CHANGE events:                                 │
// │  • pipeline_stage_changed   — Stage transition       │
// │  • store_field_updated      — Any store field change │
// │  • run_state_changed        — Run status changed     │
// │  • recovery_mode_entered    — Entered recovery       │
// │  • recovery_mode_exited     — Exited recovery        │
// │  • transient_cleared        — Transient data reset   │
// │                                                       │
// │  DATA_EDIT events:                                    │
// │  • raw_note_edited          — Intake text changed    │
// │  • owner_note_edited        — Agent notes changed    │
// │  • structured_json_edited   — JSON editor changed    │
// │  • itinerary_text_edited    — Itinerary text changed │
// │  • field_value_changed      — Any packet field edit  │
// │                                                       │
// │  MILESTONE events:                                    │
// │  • trip_created             — New trip record created│
// │  • extraction_complete      — Data extraction done   │
// │  • packet_generated         — Packet assembled       │
// │  • decision_made            — Decision output ready  │
// │  • strategy_generated       — Strategy built         │
// │  • safety_cleared           — Safety check passed    │
// │  • output_delivered         — Output sent to customer│
// └─────────────────────────────────────────────────────┘
```

### Event Capture Instrumentation

```typescript
interface ProcessLogCapture {
  // Instrument a button click
  trackAction(action: string, detail?: {
    input?: unknown;
    component?: string;
    metadata?: Record<string, unknown>;
  }): string;                           // returns event ID

  // Instrument an API call
  trackApiCall(apiName: string, promise: Promise<unknown>, context?: {
    requestId?: string;
    parentEventId?: string;
  }): Promise<unknown>;                 // resolves/rejects, auto-logs

  // Track a state change
  trackStateChange(field: string, from: unknown, to: unknown, context?: {
    source?: string;
  }): void;

  // Track an error
  trackError(error: Error | string, context?: {
    code?: string;
    recoverable?: boolean;
    parentEventId?: string;
  }): void;

  // Track a field edit
  trackEdit(field: string, from: unknown, to: unknown): void;

  // Track navigation
  trackNavigation(from: string, to: string): void;

  // Create a span (grouped events)
  startSpan(label: string): string;     // returns span ID
  endSpan(spanId: string): void;
}

// ── Instrumentation in the workbench ──
// ┌─────────────────────────────────────────────────────┐
// │  Example: handleProcessTrip with instrumentation      │
// │                                                       │
// │  const spanId = logger.startSpan("Process Trip");    │
// │                                                       │
// │  logger.trackAction("process_trip_clicked", {        │
// │    input: {                                           │
// │      raw_note: store.input_raw_note,                  │
// │      stage: spineStage,                               │
// │      mode: currentMode,                               │
// │      scenario: currentScenario,                       │
// │    },                                                 │
// │    component: "WorkbenchPage",                        │
// │    metadata: { hasTripId: !!tripId }                  │
// │  });                                                  │
// │                                                       │
// │  try {                                                │
// │    const result = await logger.trackApiCall(          │
// │      "spine_run",                                     │
// │      executeSpineRun(request),                        │
// │      { parentEventId: spanId }                        │
// │    );                                                 │
// │    // auto-logged: SYSTEM_RESPONSE spine_run_created  │
// │    // auto-logged: STATE_CHANGE pipeline_stage → ...  │
// │  } catch (err) {                                      │
// │    // auto-logged: ERROR api_error                    │
// │    logger.trackError(err, {                           │
// │      parentEventId: spanId,                           │
// │      recoverable: true                                │
// │    });                                                │
// │  }                                                    │
// │                                                       │
// │  logger.endSpan(spanId);                              │
// └─────────────────────────────────────────────────────┘
```

---

## Open Problems

1. **Capture volume vs signal** — Every keypress generates an edit event. Need debouncing and aggregation (collect edits within a 5-second window into one "editing session" event).

2. **Sensitive data in payloads** — Raw notes may contain PII (phone numbers, addresses). Payload logging must have redaction rules or truncate sensitive fields.

3. **Client-only vs server-side** — Button clicks and tab switches are client-only events. API calls produce both client and server events. Need correlation IDs to stitch them together.

4. **Performance impact** — High-frequency event logging must be non-blocking. Buffer events and batch-send, never block the UI thread.

---

## Next Steps

- [ ] Design the ProcessLogEvent schema with all categories
- [ ] Create the capture/instrumentation API (trackAction, trackApiCall, etc.)
- [ ] Build event aggregation for high-frequency edits
- [ ] Design payload redaction for PII
- [ ] Implement correlation IDs for client-server event stitching
