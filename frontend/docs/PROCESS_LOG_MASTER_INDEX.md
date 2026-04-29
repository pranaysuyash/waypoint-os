# Process Log & History Capture — Master Index

> Research on workspace-level process logging — every action, error, and state change captured as an expandable, linkable, queryable operational history.

---

## Series Overview

This series covers the operational process history layer for Waypoint OS — capturing every button click, API call, error, state transition, and data edit in the workspace as a structured, expandable log that agents, developers, and support staff can use for debugging, audit, and analytics.

**Target Audience:** Frontend engineers, product managers, support engineers, compliance officers

**Key Insight:** The existing Timeline (trip story for stakeholders), Audit Trail (compliance records), and Change Tracking (field diffs) cover business-level events. This series fills the gap: **workspace-level operational logging** — the "what happened in this session" view that agents need when debugging their own work.

---

## Documents

| # | Document | Focus |
|---|----------|-------|
| 1 | [PROCESS_LOG_01_EVENT_CAPTURE.md](PROCESS_LOG_01_EVENT_CAPTURE.md) | Event taxonomy, categories, metadata schema, instrumentation API |
| 2 | [PROCESS_LOG_02_UI_DESIGN.md](PROCESS_LOG_02_UI_DESIGN.md) | Expandable log entries, detail panels, history linking, filtering, panel placement |
| 3 | [PROCESS_LOG_03_STORAGE_PERF.md](PROCESS_LOG_03_STORAGE_PERF.md) | Ring buffer, batch sending, TimescaleDB, retention, replay, performance budget |
| 4 | [PROCESS_LOG_04_INTEGRATION.md](PROCESS_LOG_04_INTEGRATION.md) | Timeline/Audit integration, event promotion, support escalation, compliance |

---

## Key Themes

### 1. DevTools for Agents
Every workspace action captured, timestamped, and queryable — like browser DevTools but for the travel agent's workflow. Expand any log entry to see full context, input payloads, error details, and linked entities.

### 2. Three Related Systems, Three Audiences
- **Process Log** → Agent/Developer: "What happened in this session?"
- **Timeline** → Agent/Owner/Customer: "What's the story of this trip?"
- **Audit Trail** → Compliance/Legal: "Who changed what, when?"

Process log events are promoted (not duplicated) into Timeline and Audit when they match business significance thresholds.

### 3. Error-First Debugging
Errors are first-class log entries with full context — what the user was doing, what input was sent, what came back, and what happened next. No more "it just didn't work."

### 4. Session Continuity
When an agent returns to a trip, they see the previous session's process log. Cross-referencing runs, edits, and errors from different sessions helps resolve issues faster.

---

## Cross-References

| Related Series | Connection |
|---------------|------------|
| Timeline (TIMELINE_*) | Business-level trip story; process log promotes milestones here |
| Audit Trail (AUDIT_*) | Compliance records; process log promotes CRUD operations here |
| Change Tracking (FIELD_04_*) | Field-level diffs; process log captures the intent behind changes |
| Domain Events (DOMAIN_03_*) | Event sourcing; process log events are a different granularity |
| Error Handling (ERROR_HANDLING_*) | Error patterns; process log captures specific error instances |
| Agent Training (AGENT_TRAINING_*) | Process log analytics reveal common mistakes and training gaps |

---

## Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Client Buffer | Ring buffer + sessionStorage | Instant access, survives refresh |
| Event Capture | Custom React hooks + instrumentation API | Non-blocking event emission |
| Batch Transport | Fetch API with gzip compression | Efficient server persistence |
| Server Storage | TimescaleDB (hypertable) | Time-series optimized, compressed |
| UI Rendering | Virtualized list (react-window) | Handle 500+ events without lag |
| Search | Client-side (session) + server-side (history) | Full-text event search |

---

**Created:** 2026-04-29
