# Core Domain Model Foundation — Domain Events

> Bridging research: event sourcing patterns, event taxonomy, projection models, and CQRS for the travel domain.

---

## Key Questions

1. **What events does the travel domain produce?**
2. **How do we design an event schema that supports both real-time processing and historical replay?**
3. **What read models (projections) do subsystems need from the event stream?**
4. **How does CQRS separate write operations from read queries?**

---

## Research Areas

### Event Taxonomy

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Domain Event Taxonomy                            │
│                                                                          │
│  ENQUIRY EVENTS           BOOKING EVENTS          PAYMENT EVENTS        │
│  ──────────────           ──────────────          ─────────────         │
│  EnquiryReceived          BookingCreated          PaymentInitiated       │
│  EnquiryParsed            BookingConfirmed        PaymentCaptured        │
│  EnquiryValidated         BookingCancelled        PaymentFailed          │
│  EnquiryEscalated         BookingModified         PaymentRefunded        │
│  EnquiryAssigned          ComponentConfirmed      PaymentDisputed        │
│  EnquiryLost              ComponentCancelled      SettlementCreated      │
│  EnquiryWon               TicketIssued            SettlementSettled      │
│                           DocumentsGenerated                             │
│                                                                          │
│  COMMUNICATION EVENTS     TRAVELER EVENTS          VENDOR EVENTS         │
│  ────────────────────     ────────────────         ─────────────         │
│  MessageSent              TravelerCheckedIn        VendorOnboarded       │
│  MessageDelivered         TravelerNoShow           VendorSuspended       │
│  MessageRead              TripStarted              RateUpdated           │
│  MessageReplied           TripCompleted            InventoryUpdated      │
│  FollowUpTriggered        TripDisrupted            InvoiceReceived       │
│  FeedbackCollected        ReviewSubmitted          ContractSigned        │
│                                                                          │
│  SYSTEM EVENTS            AGENT EVENTS             LIFECYCLE EVENTS      │
│  ─────────────            ────────────             ─────────────────     │
│  SLABreachDetected        AgentAssigned            CustomerCreated       │
│  SLAWarningTriggered      AgentUnassigned          CustomerSegmented     │
│  WorkflowStateChanged     AgentStatusChanged       TierUpgraded          │
│  IntegrationSynced        ShiftStarted             TierDowngraded        │
│  DataImportCompleted      ShiftEnded               ReferralCreated       │
│  AlertTriggered           PerformanceReviewed       ReferralConverted    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Event Schema Design

```typescript
// ── Base Event ──
interface DomainEvent<T extends string, P> {
  // Identity
  event_id: string;                    // UUID
  event_type: T;
  event_version: number;               // schema version for evolution

  // Source
  aggregate_id: string;                // entity this event belongs to
  aggregate_type: "ENQUIRY" | "BOOKING" | "PAYMENT" | "TRIP" | "CUSTOMER" | "VENDOR" | "AGENT";
  tenant_id: string;                   // agency

  // Payload
  payload: P;
  metadata: EventMetadata;

  // Timing
  occurred_at: string;                 // when it happened
  recorded_at: string;                 // when system recorded it
}

interface EventMetadata {
  correlation_id: string;              // links events in same workflow
  causation_id: string | null;         // what triggered this event
  actor: {
    type: "AGENT" | "CUSTOMER" | "SYSTEM" | "AI" | "VENDOR";
    id: string;
  };
  source: "API" | "WEBHOOK" | "CRON" | "MANUAL" | "AI_PIPELINE";
  trace_id: string;                    // distributed tracing
}

// ── Enquiry Events ──
type EnquiryEvent =
  | DomainEvent<"ENQUIRY_RECEIVED", EnquiryReceivedPayload>
  | DomainEvent<"ENQUIRY_PARSED", EnquiryParsedPayload>
  | DomainEvent<"ENQUIRY_VALIDATED", EnquiryValidatedPayload>
  | DomainEvent<"ENQUIRY_ESCALATED", EnquiryEscalatedPayload>
  | DomainEvent<"ENQUIRY_ASSIGNED", EnquiryAssignedPayload>
  | DomainEvent<"ENQUIRY_WON", EnquiryWonPayload>
  | DomainEvent<"ENQUIRY_LOST", EnquiryLostPayload>;

interface EnquiryReceivedPayload {
  source: EnquirySource;
  raw_input: string;
  buyer_id: string | null;
  channel_message_id: string | null;
}

interface EnquiryParsedPayload {
  packet: CanonicalPacket;
  confidence: number;
  extraction_method: "AI" | "MANUAL" | "HYBRID";
  fields_extracted: string[];
  fields_missing: string[];
  fields_ambiguous: string[];
}

interface EnquiryValidatedPayload {
  validation_result: "PASS" | "FAIL" | "PARTIAL";
  gates_passed: string[];
  gates_failed: string[];
  escalation_reasons: string[];
}

interface EnquiryAssignedPayload {
  agent_id: string;
  routing_strategy: RoutingStrategy;
  priority_score: number;
  sla_response_by: string;
}

interface EnquiryWonPayload {
  trip_id: string;
  estimated_value: Money;
  time_to_convert_hours: number;
}

// ── Booking Events ──
type BookingEvent =
  | DomainEvent<"BOOKING_CREATED", BookingCreatedPayload>
  | DomainEvent<"BOOKING_CONFIRMED", BookingConfirmedPayload>
  | DomainEvent<"BOOKING_CANCELLED", BookingCancelledPayload>
  | DomainEvent<"BOOKING_MODIFIED", BookingModifiedPayload>
  | DomainEvent<"COMPONENT_CONFIRMED", ComponentConfirmedPayload>
  | DomainEvent<"TICKET_ISSUED", TicketIssuedPayload>;

interface BookingCreatedPayload {
  enquiry_id: string;
  trip_id: string;
  buyer_id: string;
  components: {
    type: BookingType;
    vendor_id: string;
    description: string;
  }[];
  estimated_total: Money;
}

interface BookingConfirmedPayload {
  confirmed_components: string[];
  total_confirmed_value: Money;
  pending_components: string[];
  all_confirmed: boolean;
}

interface BookingCancelledPayload {
  reason: "CUSTOMER" | "VENDOR" | "AGENT" | "FORCE_MAJEURE" | "SYSTEM";
  cancellation_policy_applied: string;
  refund_amount: Money | null;
  penalty_amount: Money | null;
}

// ── Payment Events ──
type PaymentEvent =
  | DomainEvent<"PAYMENT_INITIATED", PaymentInitiatedPayload>
  | DomainEvent<"PAYMENT_CAPTURED", PaymentCapturedPayload>
  | DomainEvent<"PAYMENT_FAILED", PaymentFailedPayload>
  | DomainEvent<"PAYMENT_REFUNDED", PaymentRefundedPayload>;

interface PaymentInitiatedPayload {
  amount: Money;
  method: PaymentMethod;
  booking_id: string;
  milestone: string;
  gateway: string;
}

interface PaymentCapturedPayload {
  amount: Money;
  gateway_reference: string;
  captured_at: string;
  gateway_fee: Money;
  net_amount: Money;
}

// ── Traveler Events ──
type TravelerEvent =
  | DomainEvent<"TRIP_STARTED", TripStartedPayload>
  | DomainEvent<"TRIP_COMPLETED", TripCompletedPayload>
  | DomainEvent<"TRIP_DISRUPTED", TripDisruptedPayload>
  | DomainEvent<"REVIEW_SUBMITTED", ReviewSubmittedPayload>;

interface TripStartedPayload {
  booking_id: string;
  first_component: string;
  traveler_count: number;
  on_time: boolean;
}

interface TripCompletedPayload {
  booking_id: string;
  total_duration_days: number;
  all_components_fulfilled: boolean;
  issues_count: number;
}
```

### Event Store Architecture

```typescript
interface EventStore {
  // Append events (write side)
  append(stream_id: string, events: DomainEvent<string, unknown>[], expected_version: number): Promise<void>;

  // Read events (for replay/projections)
  read(stream_id: string, from_version?: number): Promise<DomainEvent<string, unknown>[]>;

  // Subscribe (for real-time projections)
  subscribe(stream_id: string, handler: EventHandler): Promise<void>;

  // Query by aggregate type
  query(filter: EventQuery): Promise<DomainEvent<string, unknown>[]>;
}

interface EventQuery {
  aggregate_type?: string;
  event_types?: string[];
  tenant_id?: string;
  from?: string;                       // ISO datetime
  to?: string;                         // ISO datetime
  correlation_id?: string;
  actor_id?: string;
  limit?: number;
  cursor?: string;
}

// ── Event flow architecture ──
// ┌─────────────────────────────────────────────────────────────┐
// │                                                              │
// │  [Command]          Write Side          Read Side            │
// │  "CreateEnquiry"                            │                │
// │       │                                     │                │
// │       ▼                                     │                │
// │  ┌──────────┐                              │                │
// │  │ Command  │                              │                │
// │  │ Handler  │                              │                │
// │  └──────────┘                              │                │
// │       │                                     │                │
// │       ▼                                     │                │
// │  ┌──────────┐    ┌──────────┐              │                │
// │  │ Validate │──→ │  Event   │──────────────┤                │
// │  │ Business │    │  Store   │              │                │
// │  │ Rules    │    │          │              │                │
// │  └──────────┘    └──────────┘              │                │
// │       │              │                      │                │
// │       │              ├──→ Projection A      │                │
// │       │              │   (Enquiry Dashboard) │                │
// │       │              │                       │                │
// │       │              ├──→ Projection B      │                │
// │       │              │   (Agent Workload)    │                │
// │       │              │                       │                │
// │       │              ├──→ Projection C      │                │
// │       │              │   (Revenue Metrics)   │                │
// │       │              │                       │                │
// │       │              └──→ Notification       │                │
// │       │                   Engine             │                │
// │       │                                      │                │
// │       ▼                                      ▼                │
// │  [Read Model]     ◄─────── Projections ──── [Query API]     │
// │                                                              │
// └─────────────────────────────────────────────────────────────┘
```

### Projection Models (Read Models)

```typescript
// ── Enquiry Dashboard Projection ──
interface EnquiryDashboardProjection {
  enquiry_id: string;
  status: EnquiryStatus;
  buyer_name: string;
  destination: string;
  assigned_agent: string | null;
  priority_score: number;
  sla_status: "ON_TRACK" | "AT_RISK" | "BREACHED";
  time_in_stage_minutes: number;
  estimated_value: number;
  created_at: string;
}

// ── Agent Workload Projection ──
interface AgentWorkloadProjection {
  agent_id: string;
  agent_name: string;
  status: AgentStatus;
  active_trips: number;
  max_capacity: number;
  utilization_percentage: number;
  pending_actions: number;
  sla_at_risk_count: number;
  current_shift_ends: string | null;
}

// ── Revenue Pipeline Projection ──
interface RevenuePipelineProjection {
  agency_id: string;
  period: "DAILY" | "WEEKLY" | "MONTHLY";
  enquiries_received: number;
  enquiries_converted: number;
  conversion_rate: number;
  pipeline_value: Money;                // potential revenue
  confirmed_value: Money;               // confirmed bookings
  collected_value: Money;               // payments received
  avg_deal_size: Money;
  avg_time_to_convert_hours: number;
  by_source: Record<EnquirySource, {
    count: number;
    conversion_rate: number;
    avg_value: Money;
  }>;
  by_destination: Record<string, {
    count: number;
    revenue: Money;
  }>;
}

// ── Booking Health Projection ──
interface BookingHealthProjection {
  booking_id: string;
  status: BookingStatus;
  travel_start: string;
  components_total: number;
  components_confirmed: number;
  components_pending: number;
  payment_status: "FULLY_PAID" | "PARTIALLY_PAID" | "UNPAID" | "OVERPAID";
  outstanding_amount: Money;
  documents_generated: number;
  documents_pending: number;
  health_score: number;                 // 0-100
  risk_flags: string[];
}

// ── Customer 360 Projection ──
interface Customer360Projection {
  buyer_id: string;
  name: string;
  tier: string;
  lifecycle_stage: CustomerLifecycleStage;
  total_bookings: number;
  lifetime_value: Money;
  avg_booking_value: Money;
  last_booking_date: string | null;
  last_interaction_date: string;
  upcoming_trips: number;
  open_enquiries: number;
  preferred_destinations: string[];
  preferred_channel: string;
  nps_score: number | null;
  churn_risk: "LOW" | "MEDIUM" | "HIGH";
}
```

### Event Versioning & Evolution

```typescript
// Events evolve over time. Version field enables backward compatibility.
//
// V1: EnquiryReceived { source, raw_input }
// V2: EnquiryReceived { source, raw_input, buyer_id, channel_message_id }
// V3: EnquiryReceived { source, raw_input, buyer_id, channel_message_id, ai_classification }
//
// Projection handlers must handle all versions:
//
// function handleEnquiryReceived(event: DomainEvent<"ENQUIRY_RECEIVED", any>) {
//   const payload = event.payload;
//   const buyerId = payload.buyer_id ?? null;        // V1 compat
//   const classification = payload.ai_classification  // V3 only
//     ?? classifyFromSource(payload.source);
// }

// Upcaster pattern:
interface EventUpcaster {
  from_version: number;
  to_version: number;
  upcast(payload: Record<string, unknown>): Record<string, unknown>;
}

// Example upcaster V1 → V2:
const enquiryReceivedV1toV2: EventUpcaster = {
  from_version: 1,
  to_version: 2,
  upcast: (payload) => ({
    ...payload,
    buyer_id: null,
    channel_message_id: null,
  }),
};
```

---

## Open Problems

1. **Event granularity** — Should "booking confirmed" be one event or separate events per component? Coarse events are simpler but lose detail; fine-grained events create noise and storage overhead.

2. **Projection consistency** — Eventually consistent projections may show stale data to agents making real-time decisions. Need to define acceptable staleness per projection (e.g., revenue dashboard: 5 min OK; agent workload: 30 sec max).

3. **Event replay cost** — Rebuilding projections from scratch requires replaying thousands of events. Snapshot strategies are needed for high-volume aggregates.

4. **Cross-tenant events** — In multi-tenant SaaS, events from one agency must never leak to another. Tenant isolation at the event store level is critical.

5. **GDPR/DPDP event deletion** — Right-to-erasure conflicts with immutable event stores. Need cryptographic erasure or anonymization strategies for PII in event payloads.

---

## Next Steps

- [ ] Define event schema registry with versioning support
- [ ] Build projection engine with snapshot optimization
- [ ] Design correlation ID propagation through all workflows
- [ ] Create event replay tooling for projection rebuilding
- [ ] Implement tenant-scoped event store with isolation guarantees
