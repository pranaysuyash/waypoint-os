# Core Domain Model Foundation — Workflow Models

> Bridging research: workflow state machines, transition rules, trigger events, and guard conditions for the core travel domain.

---

## Key Questions

1. **What are the core workflows every subsystem orchestrates?**
2. **How does an inquiry flow from raw input to a confirmed booking?**
3. **What triggers workflow transitions and what guards prevent invalid ones?**
4. **How do workflows interact (e.g., payment workflow depends on booking workflow)?**

---

## Research Areas

### Master Workflow Map

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│  INGESTION          TRIAGE           PLANNING         BOOKING           │
│  ─────────          ─────           ─────────         ────────           │
│  Raw Note ──→ Parse ──→ Categorize ──→ Quote ──→ Confirm ──→ Ticket  │
│               │          │              │           │           │        │
│               ▼          ▼              ▼           ▼           ▼        │
│            Extract    Assign        Itinerary    Payment    Documents  │
│            Validate   Score         Pricing      Hold       Vouchers   │
│            Enrich     Route         Review       Capture               │
│                                                                          │
│  ──────────────────────────────────────────────────────────────────     │
│                                                                          │
│  COMMUNICATION       FULFILLMENT        POST-TRIP                      │
│  ─────────────       ───────────        ──────────                      │
│  Channel Route ──→ Pre-trip ──→ In-trip ──→ Complete ──→ Feedback     │
│       │               │            │           │            │           │
│       ▼               ▼            ▼           ▼            ▼           │
│    Template       Reminders     Support    Settle      Retention      │
│    Schedule       Documents    Disruption  Vendors     Referral       │
│    Follow-up      Briefing     Alerts      Reconcile   Win-back       │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Ingestion Workflow

```typescript
type IngestionState =
  | "RECEIVED"       // raw message/note arrived
  | "PARSING"        // AI extracting structured data
  | "EXTRACTED"      // structured data available
  | "VALIDATING"     // checking completeness and quality
  | "VALID"          // passed validation gates
  | "ESCALATED"      // requires human review
  | "TRIAGE_READY";  // ready for routing

interface IngestionWorkflow {
  enquiry_id: string;
  state: IngestionState;
  raw_input: string;
  source: EnquirySource;

  // Extraction results
  packet: CanonicalPacket | null;       // extracted fields
  extraction_confidence: number;        // 0-1
  extraction_method: "AI" | "MANUAL" | "HYBRID";

  // Validation
  validation_gates: ValidationGate[];
  validation_result: "PASS" | "FAIL" | "PARTIAL" | "ESCALATED";
  validation_reasons: string[];

  // Provenance
  provenance: ProvenanceChain;
}

interface ValidationGate {
  gate_id: string;                      // "NB01", "NB02"
  name: string;                         // "Traveler Count Check"
  status: "PASS" | "FAIL" | "SKIP" | "PENDING";
  reasons: string[];
  severity: "BLOCKER" | "WARNING" | "INFO";
  auto_fix_applied: boolean;
}

interface ProvenanceChain {
  entries: ProvenanceEntry[];
}

interface ProvenanceEntry {
  step: string;
  actor: "AI" | "AGENT" | "SYSTEM" | "CUSTOMER";
  timestamp: string;
  input_snapshot: Record<string, unknown>;
  output_snapshot: Record<string, unknown>;
  confidence: number;
}

// ── Ingestion State Machine ──
//
//  RECEIVED ──→ PARSING ──→ EXTRACTED ──→ VALIDATING ──→ VALID
//                  │                          │              │
//                  │                          ▼              │
//                  │                     ESCALATED ──→ VALID  │
//                  │                          │              │
//                  │                          ▼              ▼
//                  └──────────────────→ TRIAGE_READY ◄──────┘
//
//  Guards:
//    PARSING → EXTRACTED: confidence > 0.5
//    EXTRACTED → VALIDATING: packet not null
//    VALIDATING → VALID: all BLOCKER gates pass
//    VALIDATING → ESCALATED: any BLOCKER gate fails
//    ESCALATED → VALID: human resolves blockers
```

### Triage Workflow

```typescript
type TriageState =
  | "QUEUED"           // in triage queue
  | "SCORING"          // calculating priority and fit
  | "ROUTING"          // finding best agent
  | "ASSIGNED"         // agent claimed
  | "ACCEPTED"         // agent acknowledged
  | "DEFERRED"         // agent deferred (busy)
  | "REASSIGNED";      // sent to different agent

interface TriageWorkflow {
  enquiry_id: string;
  state: TriageState;

  // Scoring
  priority_score: number;               // 0-100
  priority_factors: PriorityFactor[];
  estimated_value: number;              // potential INR revenue
  urgency: "IMMEDIATE" | "SAME_DAY" | "THIS_WEEK" | "FLEXIBLE";

  // Routing
  routing_strategy: RoutingStrategy;
  required_skills: string[];
  preferred_agent_id: string | null;
  assigned_agent_id: string | null;
  assignment_history: AssignmentRecord[];

  // SLA
  sla_response_by: string;              // ISO datetime
  sla_quote_by: string | null;
  current_sla_status: "ON_TRACK" | "AT_RISK" | "BREACHED";
}

interface PriorityFactor {
  factor: string;                       // "customer_tier", "trip_value", "channel"
  weight: number;                       // 0-1
  score: number;                        // 0-100
  reasoning: string;
}

type RoutingStrategy =
  | "SKILL_BASED"       // match agent expertise
  | "ROUND_ROBIN"       // even distribution
  | "LEAST_LOADED"      // agent with fewest trips
  | "PREFERRED"         // repeat customer → same agent
  | "MANUAL";           // supervisor assigns

interface AssignmentRecord {
  agent_id: string;
  assigned_at: string;
  accepted_at: string | null;
  deferred_at: string | null;
  defer_reason: string | null;
  reassigned_at: string | null;
}

// ── Triage Flow ──
// ┌─────────────────────────────────────────┐
// │                                          │
// │  QUEUED                                  │
// │    │                                     │
// │    ▼                                     │
// │  SCORING ──→ calculate priority          │
// │    │         estimate value              │
// │    │         determine urgency           │
// │    ▼                                     │
// │  ROUTING ──→ match skills                │
// │    │         check availability          │
// │    │         apply strategy              │
// │    ▼                                     │
// │  ASSIGNED ──→ notify agent               │
// │    │                                     │
// │    ├──→ ACCEPTED (agent says yes)        │
// │    ├──→ DEFERRED (agent too busy)        │
// │    │         │                           │
// │    │         ▼                           │
// │    └──→ REASSIGNED ──→ ASSIGNED          │
// │                                          │
// └──────────────────────────────────────────┘
```

### Communication Workflow

```typescript
type CommunicationState =
  | "DRAFT"            // composing
  | "PENDING_REVIEW"   // awaiting approval
  | "APPROVED"         // ready to send
  | "SENDING"          // in transit
  | "SENT"             // delivered to channel
  | "DELIVERED"        // confirmed delivery
  | "READ"             // customer opened
  | "REPLIED"          // customer responded
  | "FAILED"           // delivery failed
  | "SCHEDULED";       // future send

interface CommunicationWorkflow {
  id: string;
  enquiry_id: string;
  trip_id: string | null;
  booking_id: string | null;

  // Channel
  channel: "WHATSAPP" | "EMAIL" | "SMS" | "PUSH" | "IN_APP";
  direction: "OUTBOUND" | "INBOUND";

  // Content
  template_id: string | null;
  subject: string | null;
  body: string;
  attachments: AttachmentRef[];
  variables: Record<string, string>;

  // Scheduling
  scheduled_at: string | null;
  sent_at: string | null;
  delivered_at: string | null;
  read_at: string | null;
  replied_at: string | null;

  // Follow-up
  follow_up_sequence: FollowUpStep[] | null;
  current_step: number;

  // Metadata
  sender_agent_id: string;
  recipient_buyer_id: string;
  thread_id: string;
}

interface FollowUpStep {
  step: number;
  delay_hours: number;
  channel: "WHATSAPP" | "EMAIL" | "SMS";
  template_id: string;
  condition: "NO_RESPONSE" | "NOT_OPENED" | "ALWAYS";
  is_terminal: boolean;
}

// ── Follow-up sequence example ──
// ┌─────────────────────────────────────────┐
// │  "Abandoned Quote" sequence              │
// │                                          │
// │  Step 1 (48h): WhatsApp nudge            │
// │    "Did you review the Kerala quote?"    │
// │       │                                  │
// │       ├── No response ──→ Step 2         │
// │       └── Replied ──→ END                │
// │                                          │
// │  Step 2 (96h): WhatsApp adjustment       │
// │    "I can adjust the budget if needed"   │
// │       │                                  │
// │       ├── No response ──→ Step 3         │
// │       └── Replied ──→ END                │
// │                                          │
// │  Step 3 (168h): WhatsApp alternative     │
// │    "Here's a similar Goa option"         │
// │       │                                  │
// │       └── No response ──→ Mark LOST      │
// └──────────────────────────────────────────┘
```

### Booking Fulfillment Workflow

```typescript
type FulfillmentState =
  | "PLANNING"          // building itinerary components
  | "QUOTING"           // getting vendor prices
  | "QUOTE_REVIEW"      // agent reviewing quotes
  | "QUOTE_SENT"        // sent to customer
  | "NEGOTIATING"       // revising based on feedback
  | "ACCEPTED"          // customer approved
  | "CONFIRMING"        // confirming with vendors
  | "PAYMENT_PENDING"   // awaiting payment
  | "PAYMENT_RECEIVED"  // payment captured
  | "TICKETING"         // issuing tickets/vouchers
  | "DOCUMENTED"        // all documents generated
  | "PRE_TRAVEL"        // countdown to travel
  | "IN_TRAVEL"         // trip in progress
  | "POST_TRAVEL"       // trip completed
  | "CLOSED";           // fully settled

interface FulfillmentWorkflow {
  booking_id: string;
  state: FulfillmentState;

  // Component tracking
  components: ComponentFulfillment[];
  all_confirmed: boolean;
  all_ticketed: boolean;

  // Payment tracking
  payment_schedule: PaymentSchedule[];
  total_paid: Money;
  total_outstanding: Money;

  // Document tracking
  documents_required: DocumentRequirement[];
  documents_generated: DocumentRef[];

  // Timeline
  target_confirmation_by: string | null;
  target_ticketing_by: string | null;
  travel_start: string | null;
  travel_end: string | null;
}

interface ComponentFulfillment {
  component_id: string;
  type: BookingType;
  vendor_id: string;
  state: "PENDING" | "QUOTE_REQUESTED" | "QUOTE_RECEIVED" | "CONFIRMING" | "CONFIRMED" | "TICKETED" | "CANCELLED";
  vendor_reference: string | null;
  quoted_price: Money | null;
  confirmed_price: Money | null;
  confirmation_deadline: string | null;
}

interface PaymentSchedule {
  milestone: string;                    // "Advance", "50%", "Balance", "Final"
  amount: Money;
  due_date: string;
  status: "PENDING" | "PAID" | "OVERDUE" | "WAIVED";
  paid_at: string | null;
  payment_id: string | null;
}

// ── Fulfillment State Machine ──
//
//  PLANNING ──→ QUOTING ──→ QUOTE_REVIEW ──→ QUOTE_SENT
//                 │                             │
//                 │                             ▼
//                 │         ┌── NEGOTIATING ◄──┤
//                 │         │                   │
//                 │         ▼                   ▼
//                 │       QUOTING           ACCEPTED
//                 │                             │
//                 │                             ▼
//                 │                     CONFIRMING
//                 │                       │ │ │
//                 │  ┌────────────────────┘ │ └──────────────┐
//                 │  ▼                      ▼                 ▼
//                 │  (vendor confirms)  (vendor fails)  (partial)
//                 │  │                      │                 │
//                 │  ▼                      ▼                 ▼
//                 │  CONFIRMED ──→ PAYMENT_PENDING ──→ PAYMENT_RECEIVED
//                 │                                │
//                 │                                ▼
//                 │                          TICKETING ──→ DOCUMENTED
//                 │                                          │
//                 │                              ┌───────────┘
//                 │                              ▼
//                 │                         PRE_TRAVEL ──→ IN_TRAVEL ──→ POST_TRAVEL ──→ CLOSED
//                 │                                                              │
//                 └──────────────────────────────────────────────────────────→ CANCELLED
```

### Disruption Recovery Workflow

```typescript
type DisruptionState =
  | "DETECTED"         // disruption identified
  | "ASSESSING"        // evaluating impact
  | "NOTIFYING"        // alerting stakeholders
  | "REPLANNING"       // finding alternatives
  | "ALTERNATIVE_OFFERED"
  | "ALTERNATIVE_ACCEPTED"
  | "ALTERNATIVE_REJECTED"
  | "RECOVERING"       // implementing new plan
  | "RECOVERED"
  | "UNRECOVERABLE";

interface DisruptionWorkflow {
  id: string;
  booking_id: string;
  component_id: string;

  disruption_type: "FLIGHT_DELAY" | "FLIGHT_CANCEL" | "HOTEL_OVERBOOKED"
    | "WEATHER" | "STRIKE" | "VENDOR_FAILURE" | "DOCUMENT_ISSUE"
    | "HEALTH" | "POLITICAL" | "NATURAL_DISASTER";

  state: DisruptionState;
  severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

  impact: DisruptionImpact;
  recovery_options: RecoveryOption[];
  selected_option: string | null;

  affected_travelers: string[];
  notifications_sent: NotificationRecord[];
}

interface DisruptionImpact {
  affected_components: string[];
  financial_impact: Money;
  traveler_impact: "MINOR_INCONVENIENCE" | "PARTIAL_DISRUPTION" | "FULL_DISRUPTION" | "SAFETY_RISK";
  time_impact_hours: number;
}

interface RecoveryOption {
  id: string;
  description: string;
  cost_delta: Money;                    // additional cost (+/-)
  time_delta_hours: number;
  quality_impact: "IMPROVED" | "SAME" | "DOWNGRADED";
  availability: "IMMEDIATE" | "PENDING_CONFIRMATION" | "UNAVAILABLE";
  vendor_id: string;
}
```

---

## Open Problems

1. **Workflow nesting** — A booking fulfillment workflow contains component-level workflows (each vendor confirmation is its own micro-workflow). State management at nested levels creates combinatorial complexity.

2. **Cross-workflow dependencies** — The payment workflow depends on booking confirmation, which depends on vendor confirmation, which depends on quoting. Circular dependencies can emerge when vendors require payment proof before confirming.

3. **SLA cascading** — When an upstream workflow breaches its SLA, downstream SLAs need automatic recalculation. A 2-hour triage delay should push the quote-by deadline by 2 hours.

4. **Concurrent workflow instances** — A customer may have an active enquiry workflow AND a post-trip feedback workflow AND a referral workflow simultaneously. These must not conflict.

5. **Manual override traceability** — When agents manually override workflow state (force-advancing, skipping steps), the audit trail must capture the reason and prior state for compliance.

---

## Next Steps

- [ ] Design workflow engine abstraction (generic state machine with typed transitions)
- [ ] Define guard condition DSL for transition rules
- [ ] Map existing frontier_orchestrator flow to canonical ingestion workflow
- [ ] Build SLA calculation engine with cascade rules
- [ ] Create workflow visualization for agent workspace
