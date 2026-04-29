# Draft System — Multi-Agent Collaboration & Merging

> Research document for multi-agent draft scenarios, draft merging, linking drafts to trips, duplicate detection, and draft transfer protocols.

---

## Key Questions

1. **How do multiple agents work on the same customer's request?**
2. **How do we detect and handle duplicate drafts?**
3. **How does draft merging work?**
4. **How do drafts link to existing trips?**

---

## Research Areas

### Multi-Agent Draft Scenarios

```typescript
// ── Scenario catalog ──
// ┌─────────────────────────────────────────────────────┐
// │  Scenario 1: Sequential Handoff                       │
// │                                                       │
// │  Agent A starts draft for customer Sharma             │
// │  Agent A saves draft, goes on leave                   │
// │  Customer calls again, Agent B answers                │
// │  Agent B sees existing draft for Sharma               │
// │  Agent B opens draft, continues from where A left off │
// │                                                       │
// │  Resolution: Draft transfer or shared access          │
// │                                                       │
// │  ─────────────────────────────────────────────────── │
// │                                                       │
// │  Scenario 2: Parallel Drafts (Duplicate)              │
// │                                                       │
// │  Agent A creates draft from WhatsApp inquiry          │
// │  Agent B creates draft from phone call (same customer)│
// │  Both drafts are for the same customer                │
// │                                                       │
// │  Resolution: Duplicate detection + merge              │
// │                                                       │
// │  ─────────────────────────────────────────────────── │
// │                                                       │
// │  Scenario 3: Draft → Existing Trip                    │
// │                                                       │
// │  Customer had trip WP-442 (completed)                 │
// │  Customer calls with follow-up request                │
// │  Agent creates draft for the follow-up                │
// │  Draft should link to existing WP-442                 │
// │                                                       │
// │  Resolution: Draft-to-trip linking                    │
// │                                                       │
// │  ─────────────────────────────────────────────────── │
// │                                                       │
// │  Scenario 4: Multiple Trips, One Customer             │
// │                                                       │
// │  Sharma has 3 trips (Goa, Kerala, Singapore)          │
// │  Sharma calls with a new request                      │
// │  Agent creates draft, system shows existing trips     │
// │                                                       │
// │  Resolution: Customer context panel in draft          │
// └─────────────────────────────────────────────────────┘
```

### Duplicate Detection

```typescript
interface DraftDuplicateDetector {
  // Check for potential duplicates when creating/saving a draft
  detectDuplicates(draft: Draft): DuplicateMatch[];

  // Merge two drafts
  mergeDrafts(source_id: string, target_id: string): MergeResult;
}

interface DuplicateMatch {
  match_type: "SAME_CUSTOMER" | "SIMILAR_REQUEST" | "SAME_DESTINATION";
  confidence: number;                   // 0-1
  matched_entity: {
    type: "DRAFT" | "TRIP";
    id: string;
    name: string;
    status: string;
    created_by: string;                 // agent name
    created_at: string;
  };
  evidence: string[];                   // ["Same phone number", "Same destination"]
}

// ── Duplicate detection rules ──
// ┌─────────────────────────────────────────────────────┐
// │  Duplicate Detection Signals                           │
// │                                                       │
// │  Signal                    | Weight | Matching Method │
// │  ─────────────────────────────────────────────────── │
// │  Phone number match        | HIGH   | Exact match    │
// │  Email match               | HIGH   | Exact match    │
// │  Customer name + phone     | HIGH   | Fuzzy name +   │
// │                            |        | exact phone    │
// │  Same destination + dates  | MED    | Overlap check  │
// │  Similar customer message  | MED    | Cosine sim     │
// │  Same WhatsApp number      | HIGH   | Exact match    │
// │                                                       │
// │  When to check:                                       │
// │  • On draft creation (auto-detect before agent starts│
// │    working on a duplicate)                            │
// │  • On first save (after customer details extracted)  │
// │  • On demand (agent clicks "Check for duplicates")   │
// │                                                       │
// │  UI when duplicate found:                             │
// │  ┌───────────────────────────────────────────────┐   │
// │  │ ⚠️ Potential duplicate detected                 │   │
// │  │                                                 │   │
// │  │ Agent Priya already has a draft for this        │   │
// │  │ customer:                                      │   │
// │  │ "Singapore trip for family" (OPEN, 2h ago)     │   │
// │  │                                                 │   │
// │  │ [Open existing draft] [Create new anyway]       │   │
// │  │ [Merge into existing]                           │   │
// │  └───────────────────────────────────────────────┘   │
// └─────────────────────────────────────────────────────┘
```

### Draft Merging

```typescript
interface DraftMerge {
  // Merge source into target (target survives)
  source_draft_id: string;              // will be marked "merged_into"
  target_draft_id: string;              // absorbs source data

  merge_strategy: {
    customer_message: "COMBINE" | "REPLACE";  // combine both messages
    agent_notes: "COMBINE";              // always combine notes
    structured_json: "TARGET_WINS";      // target's structured data wins
    config: "TARGET_WINS";               // target's stage/mode wins
  };

  result: {
    merged_draft_id: string;            // target draft, now enriched
    source_status: "merged_into";       // source is marked
    merge_event_logged: boolean;        // audit trail preserved
  };
}

// ── Merge flow ──
// ┌─────────────────────────────────────────────────────┐
// │  Draft Merge Flow                                      │
// │                                                       │
// │  Source Draft (Agent B's):                             │
// │  customer_message: "Need Singapore trip, 4 pax"       │
// │  agent_notes: "Customer called at 2PM, budget ₹3L"   │
// │  status: open                                         │
// │                                                       │
// │  Target Draft (Agent A's):                             │
// │  customer_message: "Planning family trip to Singapore" │
// │  agent_notes: "WhatsApp inquiry, family of 4"        │
// │  status: blocked (has run history)                    │
// │                                                       │
// │  Merge Result (Target survives):                       │
// │  customer_message: COMBINE                            │
// │    "[From draft by Agent B]: Need Singapore trip..."  │
// │    "[Original]: Planning family trip..."              │
// │  agent_notes: COMBINE                                 │
// │    "[Agent B]: Customer called at 2PM, budget ₹3L"   │
// │    "[Agent A]: WhatsApp inquiry, family of 4"         │
// │  config: TARGET_WINS (keeps Agent A's stage/mode)    │
// │  run_history: TARGET_WINS (keeps Agent A's runs)     │
// │                                                       │
// │  Source draft: status → "merged_into {target_id}"    │
// │  Audit: merge event logged on both drafts            │
// └─────────────────────────────────────────────────────┘
```

### Draft-to-Trip Linking

```typescript
interface DraftTripLink {
  draft_id: string;
  trip_id: string;
  link_type: "FOLLOW_UP" | "RELATED" | "SAME_CUSTOMER" | "REVISION";
  linked_by: string;                    // agent who created the link
  linked_at: string;
  note: string | null;                  // "Customer called about add-on activities"
}

// ── Draft-to-trip linking UI ──
// ┌─────────────────────────────────────────────────────┐
// │  Link Draft to Existing Trip                           │
// │                                                       │
// │  Draft: "Singapore trip for family"                    │
// │                                                       │
// │  Detected related trips:                              │
// │  ┌───────────────────────────────────────────────┐   │
// │  │ WP-442 Singapore Family Trip (Completed)       │   │
// │  │ Jun 1-6, 2026 · Sharma family · ₹3.85L       │   │
// │  │ [Link as follow-up] [View trip]                │   │
// │  └───────────────────────────────────────────────┘   │
// │  ┌───────────────────────────────────────────────┐   │
// │  │ WP-398 Goa Weekend (Completed)                 │   │
// │  │ Mar 15-17, 2026 · Sharma family · ₹1.2L      │   │
// │  │ [Link as related] [View trip]                  │   │
// │  └───────────────────────────────────────────────┘   │
// │                                                       │
// │  Or search: [Search by trip ID or customer name]      │
// │                                                       │
// │  Link type:                                           │
// │  ○ Follow-up (same customer, new request)             │
// │  ○ Revision (modify existing trip)                    │
// │  ○ Same customer (different trip)                     │
// │  ○ Related (shared travelers, group booking)          │
// │                                                       │
// │  Note: [Optional note about the relationship    ]     │
// │                                                       │
// │  [Link] [Cancel]                                      │
// └─────────────────────────────────────────────────────┘
```

### Draft Transfer Protocol

```typescript
interface DraftTransfer {
  draft_id: string;
  from_agent: string;
  to_agent: string;
  reason: "AGENT_UNAVAILABLE" | "REASSIGNMENT" | "EXPERTISE" | "WORKLOAD";
  note: string | null;

  // What the receiving agent sees
  transfer_notification: {
    title: string;                      // "Draft transferred from Priya"
    summary: string;                    // "Singapore family trip, blocked on validation"
    last_action: string;                // "Last saved 2 hours ago"
    action_items: string;               // "Fix destination field and re-run"
  };
}

// ── Transfer scenarios ──
// ┌─────────────────────────────────────────────────────┐
// │  Draft Transfer Scenarios                              │
// │                                                       │
// │  1. Agent goes on leave / sick                         │
// │     → Manager transfers all open drafts to coverage   │
// │     → Notification: "3 drafts transferred to you"    │
// │                                                       │
// │  2. Expertise mismatch                                 │
// │     → Agent A realizes this is a corporate trip       │
// │     → Transfers to Agent B (corporate specialist)     │
// │     → Note: "Corporate inquiry, over to you"          │
// │                                                       │
// │  3. Workload balancing                                 │
// │     → Manager sees Agent A has 8 drafts, Agent C has 2│
// │     → Transfers 3 drafts from A to C                  │
// │                                                       │
// │  4. Shift handoff                                      │
// │     → End of day shift, transfer open drafts to       │
// │       night shift agent                               │
// │     → Night agent picks up where day agent left off   │
// └─────────────────────────────────────────────────────┘
```

---

## Open Problems

1. **Merge conflicts** — If both drafts have runs, which run history survives? Recommendation: target wins for runs, combine for notes/messages.

2. **Duplicate detection accuracy** — Fuzzy matching customer names can produce false positives. Need human confirmation before auto-merging.

3. **Cross-agency drafts** — If the platform supports multiple agencies, draft data must not leak between agencies. Strict agency_id scoping.

4. **Link chain depth** — A draft linked to a trip, which was itself created from a draft, which was linked to another trip... Need to limit or flatten link chains for UI clarity.

---

## Next Steps

- [ ] Build duplicate detection engine with matching signals
- [ ] Create draft merge workflow with conflict resolution
- [ ] Implement draft-to-trip linking API
- [ ] Design draft transfer protocol with notifications
