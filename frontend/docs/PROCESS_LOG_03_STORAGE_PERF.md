# Process Log & History Capture — Storage & Performance

> Research document for process log storage architecture, retention policies, real-time event streaming, performance optimization, and replay capabilities.

---

## Key Questions

1. **Where and how are process log events stored?**
2. **What retention policies apply to different event types?**
3. **How do we stream events in real-time without blocking the UI?**
4. **What replay and debugging capabilities does the log enable?**

---

## Research Areas

### Storage Architecture

```typescript
interface ProcessLogStorage {
  // Two-tier storage
  client_buffer: {
    // In-memory ring buffer for current session
    max_events: number;                 // 500 events in memory
    strategy: "ring_buffer";            // oldest events dropped when full
    persistence: "SESSION_STORAGE";     // survives tab refresh
  };

  server_store: {
    // Server-side persistence for cross-session history
    batch_interval_ms: number;          // send every 2 seconds
    max_batch_size: number;             // max 50 events per batch
    endpoint: "POST /api/process-log/events";
    storage: "TimescaleDB";             // time-series optimized
    partition_by: "trip_id + month";
  };
}

// ── Storage tiers ──
// ┌─────────────────────────────────────────────────────┐
// │  Process Log Storage Architecture                     │
// │                                                       │
// │  ┌─ Client (Browser) ─────────────────────────────┐ │
// │  │                                                │ │
// │  │  Ring Buffer (500 events)                      │ │
// │  │  ├── Latest events for current session         │ │
// │  │  ├── Survives tab refresh (sessionStorage)     │ │
// │  │  └── Instant access, no network                │ │
// │  │                                                │ │
// │  │  Event Queue (outgoing)                        │ │
// │  │  ├── Batch every 2s or 50 events              │ │
// │  │  ├── Retry on failure (3 attempts)            │ │
// │  │  └── Compressed before sending (gzip)         │ │
// │  └────────────────────────────────────────────────┘ │
// │                    │                                   │
// │                    ▼ batch send                        │
// │  ┌─ Server ───────────────────────────────────────┐ │
// │  │                                                │ │
// │  │  API: POST /api/process-log/events             │ │
// │  │  ├── Auth required (session token)             │ │
// │  │  ├── Rate limited (10 batches/sec per client)  │ │
// │  │  └── Async write (respond 202 immediately)     │ │
// │  │                                                │ │
// │  │  TimescaleDB (hypertable)                      │ │
// │  │  ├── Partitioned by (trip_id, month)           │ │
// │  │  ├── Indexed on (trip_id, run_id, timestamp)   │ │
// │  │  ├── Indexed on (category, severity)           │ │
// │  │  └── Compression policy after 30 days          │ │
// │  └────────────────────────────────────────────────┘ │
// └─────────────────────────────────────────────────────┘
```

### Retention Policies

```typescript
interface ProcessLogRetentionPolicy {
  event_category: ProcessLogEventCategory;
  retention: string;
  reason: string;
}

// ── Retention by event category ──
// ┌─────────────────────────────────────────────────────┐
// │  Retention Policies                                    │
// │                                                       │
// │  Category         | Retention  | Reason               │
// │  ─────────────────────────────────────────────────── │
// │  USER_ACTION      | 90 days    | Debugging, UX analytics│
// │  SYSTEM_RESPONSE  | 90 days    | Debugging, support    │
// │  ERROR            | 1 year     | Support escalations   │
// │  STATE_CHANGE     | 90 days    | Debugging             │
// │  DATA_EDIT        | 1 year     | Audit, change history │
// │  NAVIGATION       | 30 days    | UX analytics only     │
// │  EXTERNAL_EVENT   | 1 year     | Compliance, audit     │
// │  RECOVERY         | 1 year     | Support, debugging    │
// │  INSIGHT          | 90 days    | Product analytics     │
// │  MILESTONE        | 2 years    | Business audit trail   │
// │                                                       │
// │  Archival:                                           │
// │  • After retention: compress to cold storage (S3)     │
// │  • MILESTONE events: keep in hot storage for 2 years │
// │  • DATA_EDIT events: aggregate to daily summaries    │
// │    after 1 year, keep individual for 90 days         │
// │                                                       │
// │  Client-side cleanup:                                │
// │  • Session buffer: clear on tab close (sessionStorage)│
// │  • Server batch queue: flush on page unload          │
// │  • Navigation events: never persist to server        │
// └─────────────────────────────────────────────────────┘
```

### Real-Time Event Streaming

```typescript
interface ProcessLogStream {
  // Client-side event emitter
  onEvent(callback: (event: ProcessLogEvent) => void): () => void;

  // Batched for performance
  onBatch(callback: (events: ProcessLogEvent[]) => void): () => void;

  // Filtered stream (only errors, only milestones, etc.)
  onFiltered(
    filter: Partial<ProcessLogFilter>,
    callback: (event: ProcessLogEvent) => void,
  ): () => void;
}

// ── Event flow pipeline ──
// ┌─────────────────────────────────────────────────────┐
// │  Event Flow: Capture → Buffer → Emit → Persist       │
// │                                                       │
// │  User clicks "Process Trip"                          │
// │     │                                                 │
// │     ├── 1. trackAction() → creates USER_ACTION event │
// │     │   ├── Adds to ring buffer (instant)            │
// │     │   ├── Emits to subscribers (UI update)         │
// │     │   └── Enqueues for batch send                  │
// │     │                                                 │
// │     ├── 2. executeSpineRun() → trackApiCall()        │
// │     │   ├── SYSTEM_RESPONSE on resolve              │
// │     │   └── ERROR on reject                          │
// │     │                                                 │
// │     ├── 3. Store updates → trackStateChange()        │
// │     │   └── STATE_CHANGE for each field update       │
// │     │                                                 │
// │     └── 4. All events visible in log panel           │
// │         immediately (from ring buffer)                │
// │                                                       │
// │  Performance guardrails:                              │
// │  • Events emitted synchronously (no await)           │
// │  • UI updates batched with requestAnimationFrame     │
// │  • Server sends batched every 2s (non-blocking)     │
// │  • Ring buffer never exceeds 500 events              │
// │  • Detail payloads lazy-loaded (summary first)       │
// └─────────────────────────────────────────────────────┘
```

### Replay & Debugging

```typescript
interface ProcessLogReplay {
  // Replay a specific action
  replayAction(eventId: string): Promise<ReplayResult>;

  // Replay a full run sequence
  replayRun(runId: string): Promise<ReplayResult>;

  // Compare two runs
  compareRuns(runIdA: string, runIdB: string): RunComparison;

  // Export events for support
  exportEvents(filter: ProcessLogFilter): Promise<string>; // JSON export
}

interface ReplayResult {
  original_event: ProcessLogEvent;
  replay_event: ProcessLogEvent;
  match: boolean;
  differences: {
    field: string;
    original: unknown;
    replay: unknown;
  }[];
}

// ── Debugging use cases ──
// ┌─────────────────────────────────────────────────────┐
// │  Process Log Debugging Scenarios                      │
// │                                                       │
// │  Scenario 1: "Why did validation fail?"              │
// │  → Filter by ERROR + linked run                      │
// │  → Expand error to see gate, reasons, fields         │
// │  → See the EDIT events that fixed it                 │
// │  → See the retry that succeeded                      │
// │                                                       │
// │  Scenario 2: "What changed between run 1 and run 2?" │
// │  → Compare runs: show input diff, output diff        │
// │  → Highlight which edits happened between runs       │
// │  → Show pipeline stage differences                   │
// │                                                       │
// │  Scenario 3: "Support ticket — trip WP-442 broken"   │
// │  → Export all events for trip WP-442                 │
// │  → Share with developer (JSON or formatted report)   │
// │  → Replay the failing action to reproduce            │
// │                                                       │
// │  Scenario 4: "Agent says they processed but no trip" │
// │  → Filter by actor + time range                      │
// │  → Show all actions, find the failed run             │
// │  → Identify if it was user error or system error     │
// └─────────────────────────────────────────────────────┘
```

### Performance Budget

```typescript
// ── Performance constraints ──
// ┌─────────────────────────────────────────────────────┐
// │  Performance Budget                                    │
// │                                                       │
// │  Event capture overhead:                              │
// │  • trackAction(): < 0.1ms per call (sync, no await) │
// │  • trackApiCall(): < 0.5ms (wraps promise)          │
// │  • trackStateChange(): < 0.1ms                       │
// │  • trackEdit(): < 0.1ms (debounced 500ms)           │
// │                                                       │
// │  Memory:                                              │
// │  • Ring buffer: max 2MB (500 events × avg 4KB)      │
// │  • Detail payloads: lazy-loaded, not in buffer       │
// │  • Session storage: compressed, max 5MB total        │
// │                                                       │
// │  Network:                                             │
// │  • Batch sends: max 1 request per 2 seconds         │
// │  • Payload compression: gzip, ~70% reduction        │
// │  • Fail silently: never block UI for log send        │
// │                                                       │
// │  UI rendering:                                        │
// │  • Log panel: virtualized list (render only visible) │
// │  • Expand/collapse: no re-render of other entries    │
// │  • Search: debounced 300ms, client-side for session  │
// └─────────────────────────────────────────────────────┘
```

---

## Open Problems

1. **Offline accumulation** — If the user is offline, events accumulate in the client buffer. On reconnect, a large batch needs to be sent. Need backpressure handling.

2. **Storage cost at scale** — 500 events per session × 100 agents × 30 days = 1.5M events/month. TimescaleDB handles this well, but compression policies are essential.

3. **PII in event payloads** — Raw notes, customer names, and phone numbers appear in event payloads. Need field-level redaction before server persistence.

4. **Replay accuracy** — Replaying a "Process Trip" action with the same input may produce different results (LLM non-determinism). Replay is for debugging input/output, not exact reproduction.

---

## Next Steps

- [ ] Implement client-side ring buffer with session persistence
- [ ] Build batch event sender with retry and compression
- [ ] Create TimescaleDB schema for server-side storage
- [ ] Design retention and archival policies
- [ ] Build run comparison and event export tools
