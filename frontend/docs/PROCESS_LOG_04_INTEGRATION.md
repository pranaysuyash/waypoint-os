# Process Log & History Capture — Integration & Audit

> Research document for integrating process logs with existing Timeline, Audit, and Change Tracking systems, plus compliance, reporting, and support escalation use cases.

---

## Key Questions

1. **How does the process log relate to the existing Timeline and Audit systems?**
2. **What compliance and audit requirements does the process log support?**
3. **How do support and escalation workflows use process logs?**
4. **What reporting and analytics does the process log enable?**

---

## Research Areas

### Integration with Existing Systems

```typescript
// ── System relationship map ──
// ┌─────────────────────────────────────────────────────┐
// │  Three Related Systems — Different Audiences          │
// │                                                       │
// │  Process Log (this series)                            │
// │  Audience: Agent (operator), Developer, Support      │
// │  Focus: "What happened in this workspace session"    │
// │  Granularity: Every click, edit, error, response     │
// │  Storage: Client buffer + server batch               │
// │  Retention: 30 days - 1 year                        │
// │                                                       │
// │  Timeline (TIMELINE_* series)                        │
// │  Audience: Agent, Owner, Customer                    │
// │  Focus: "The story of this trip"                     │
// │  Granularity: Business milestones and decisions      │
// │  Storage: Trip database (permanent)                  │
// │  Retention: Permanent (trip lifetime)                │
// │                                                       │
// │  Audit Trail (AUDIT_* series)                        │
// │  Audience: Compliance, Legal, Security               │
// │  Focus: "Who did what, when, for regulatory purposes"│
// │  Granularity: Entity-level CRUD operations           │
// │  Storage: Immutable audit log                        │
// │  Retention: Per regulation (2-8 years)               │
// │                                                       │
// │  ─────────────────────────────────────────────────── │
// │                                                       │
// │  Data flow:                                           │
// │  Process Log ──filter──→ Timeline (milestones only)  │
// │  Process Log ──filter──→ Audit Trail (CRUD only)     │
// │  Process Log ──full───→ Process History UI           │
// │                                                       │
// │  Shared concepts:                                     │
// │  • Event IDs (process_log references timeline IDs)   │
// │  • Actor identification (same user/agent context)    │
// │  • Trip/Run linking (all reference same entities)    │
// │  • Timestamps (same clock source)                    │
// └─────────────────────────────────────────────────────┘
```

### Event Promotion Rules

```typescript
interface EventPromotionRule {
  // Which process log events get promoted to Timeline?
  to_timeline: {
    categories: ["MILESTONE", "USER_ACTION"];
    filter: {
      action: string[];                 // specific actions to promote
    };
    transform: (event: ProcessLogEvent) => TimelineEvent;
  };

  // Which process log events get promoted to Audit?
  to_audit: {
    categories: ["DATA_EDIT", "USER_ACTION", "ERROR"];
    filter: {
      linked_entity_type: ["TRIP", "ENQUIRY", "BOOKING"];
    };
    transform: (event: ProcessLogEvent) => AuditEntry;
  };
}

// ── Promotion examples ──
// ┌─────────────────────────────────────────────────────┐
// │  Event Promotion: Process Log → Timeline              │
// │                                                       │
// │  Process Log: MILESTONE "Packet generated"           │
// │  → Timeline: "Trip details extracted and organized"  │
// │    (customer-friendly version)                        │
// │                                                       │
// │  Process Log: MILESTONE "Safety cleared"             │
// │  → Timeline: "Final review completed — ready to go" │
// │                                                       │
// │  Process Log: USER_ACTION "Process Trip clicked"     │
// │  → Timeline: (not promoted — too granular)           │
// │                                                       │
// │  ─────────────────────────────────────────────────── │
// │                                                       │
// │  Event Promotion: Process Log → Audit                 │
// │                                                       │
// │  Process Log: DATA_EDIT "budget changed ₹3L → ₹4L"  │
// │  → Audit: UPDATE Trip.WP-442.budget 3L → 4L         │
// │    (compliance record)                                │
// │                                                       │
// │  Process Log: ERROR "Validation blocked"             │
// │  → Audit: (not promoted — operational, not entity)   │
// └─────────────────────────────────────────────────────┘
```

### Support & Escalation Workflows

```typescript
interface ProcessLogSupportIntegration {
  // Create support ticket from process log
  createSupportTicket(options: {
    event_ids: string[];                // events to include
    trip_id: string;
    description: string;
    include_screenshots: boolean;
  }): Promise<SupportTicket>;

  // Share process log with support
  shareProcessLog(options: {
    trip_id: string;
    time_range: { from: string; to: string };
    filter?: Partial<ProcessLogFilter>;
    format: "JSON" | "LINKED_VIEW" | "PDF_REPORT";
  }): Promise<string>;                  // returns shareable link

  // Attach to existing support ticket
  attachToTicket(ticket_id: string, event_ids: string[]): Promise<void>;
}

// ── Support escalation flow ──
// ┌─────────────────────────────────────────────────────┐
// │  Support Escalation Using Process Log                 │
// │                                                       │
// │  Agent reports: "Trip processing failed"             │
// │                                                       │
// │  1. Support agent opens process log for trip WP-442  │
// │     → Filters to ERROR events                        │
// │     → Sees: "Validation failed: NB01" at 14:31      │
// │                                                       │
// │  2. Expands error detail                              │
// │     → Sees raw validation response                   │
// │     → Sees the input that was sent                   │
// │     → Sees the chain: Click → API → Error            │
// │                                                       │
// │  3. Checks edit history                               │
// │     → Sees agent edited destination after error      │
// │     → Sees retry succeeded                           │
// │     → Closes ticket: "Agent resolved by fixing data" │
// │                                                       │
// │  4. If unresolved, creates escalation                 │
// │     → Exports full process log as JSON               │
// │     → Attaches to JIRA/Linera ticket                 │
// │     → Developer can replay the failing action        │
// └─────────────────────────────────────────────────────┘
```

### Reporting & Analytics

```typescript
// ── Process log analytics dashboard ──
// ┌─────────────────────────────────────────────────────┐
// │  Process Log Analytics — This Week                    │
// │                                                       │
// │  Process Volume:                                      │
// │  Total events: 12,450                                 │
// │  Per agent avg: 622 events                           │
// │  Peak hour: 11:00 AM (2,100 events)                  │
// │                                                       │
// │  Error Rates:                                         │
// │  Total errors: 342 (2.7% of events)                  │
// │  By type:                                             │
// │  • Validation errors: 210 (61%)                      │
// │  • API errors: 85 (25%)                              │
// │  • Network errors: 32 (9%)                           │
// │  • Other: 15 (4%)                                    │
// │                                                       │
// │  Processing Funnel:                                   │
// │  Process Trip clicks: 185                            │
// │  → Run created: 185 (100%)                           │
// │  → Validation passed: 142 (77%)                      │
// │  → Packet generated: 138 (75%)                       │
// │  → Decision made: 130 (70%)                          │
// │  → Strategy built: 118 (64%)                         │
// │  → Safety cleared: 112 (61%)                         │
// │  → Output delivered: 98 (53%)                        │
// │                                                       │
// │  Top Failure Reasons:                                 │
// │  1. Missing destination (42 occurrences)             │
// │  2. Invalid budget format (28)                       │
// │  3. Traveler count mismatch (18)                     │
// │                                                       │
// │  Retry Patterns:                                      │
// │  Avg retries per trip: 1.4                           │
// │  Trips with 0 retries: 65%                           │
// │  Trips with 1 retry: 25%                             │
// │  Trips with 2+ retries: 10%                          │
// │                                                       │
// │  Agent Efficiency:                                     │
// │  Fastest to process: Priya (avg 3.2 min)             │
// │  Most retries: Neha (avg 2.8 retries)                │
// │  Common edit patterns: destination, dates, budget    │
// └─────────────────────────────────────────────────────┘
```

### Compliance & Data Governance

```typescript
// ── Compliance considerations ──
// ┌─────────────────────────────────────────────────────┐
// │  Process Log Compliance Requirements                  │
// │                                                       │
// │  1. PII Redaction:                                    │
// │     • Customer names, phones, emails in payloads     │
// │     • Must redact before server storage              │
// │     • Support exports need approval for full data    │
// │                                                       │
// │  2. DPDP Act (India):                                │
// │     • Process logs are "processing records"          │
// │     • User can request deletion of their activity    │
// │     • Agent activity logs are employer records       │
// │                                                       │
// │  3. Data Minimization:                                │
// │     • Don't log full API responses — log summaries   │
// │     • Truncate large payloads (>10KB)                │
// │     • Navigation events don't need server storage    │
// │                                                       │
// │  4. Access Control:                                   │
// │     • Agents see own session logs only               │
// │     • Managers see team logs                         │
// │     • Support staff see logs for assigned tickets    │
// │     • Full log export requires admin approval        │
// │                                                       │
// │  5. Immutability (for promoted audit events):        │
// │     • Events promoted to Audit Trail are immutable   │
// │     • Process log events can be deleted per retention│
// │     • But deletion is logged (meta-audit)            │
// └─────────────────────────────────────────────────────┘
```

---

## Open Problems

1. **Event deduplication** — The same state change may be logged by both the process log (client) and the audit trail (server). Need deduplication when displaying unified views.

2. **Cross-trip correlation** — An agent working on multiple trips in parallel generates interleaved events. Grouping by trip_id is straightforward but cross-trip patterns (copy-paste between trips) are harder to detect.

3. **Cost-benefit of granularity** — Every button click is cheap to capture but expensive to store and process. Need to validate that fine-grained logging provides enough value vs. just milestone-level logging.

4. **Real-time monitoring** — Should managers see live process logs from their team? Real-time streaming (WebSocket) is technically feasible but raises privacy concerns.

---

## Next Steps

- [ ] Define event promotion rules (process log → timeline, process log → audit)
- [ ] Build support ticket integration with log export
- [ ] Create process log analytics dashboard
- [ ] Implement PII redaction pipeline
- [ ] Design access control for process log viewing
- [ ] Build unified event view (process + timeline + audit)
