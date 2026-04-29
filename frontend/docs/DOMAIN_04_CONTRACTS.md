# Core Domain Model Foundation — API Contracts

> Bridging research: REST API contract design, request/response types, validation rules, BFF proxy patterns, and real-time event contracts.

---

## Key Questions

1. **What API endpoints does each entity expose?**
2. **How do frontend and backend types stay in sync?**
3. **What validation runs on each endpoint?**
4. **How do BFF (Backend-for-Frontend) proxy patterns shape the API?**

---

## Research Areas

### API Endpoint Map

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        API Endpoint Map                                 │
│                                                                          │
│  Enquiries          Bookings            Payments          Agents         │
│  ─────────          ─────────           ─────────          ──────         │
│  GET    /enquiries  GET    /bookings    GET    /payments  GET    /agents │
│  POST   /enquiries  POST   /bookings    POST   /payments  GET    /agents │
│  GET    /enquiries/:id                                                                    /:id    │
│  PATCH  /enquiries/:id  PATCH /bookings/:id                               │
│  POST   /enquiries/:id                                                                  /assign │
│    /parse           POST   /bookings/:id                                 │
│  POST   /enquiries/:id                    /confirm                        │
│    /validate       POST   /bookings/:id                                 │
│  POST   /enquiries/:id                    /cancel                         │
│    /triage         GET    /bookings/:id                                 │
│                     /components     /health                              │
│  Vendors            Customers          Notifications    Search           │
│  ────────           ──────────         ──────────────  ──────           │
│  GET    /vendors    GET    /customers   POST   /notify   GET    /search │
│  POST   /vendors    POST   /customers   GET    /notifications           │
│  GET    /vendors/:id GET   /customers/:id  /:id/preferences              │
│  PATCH  /vendors/:id PATCH /customers/:id                               │
│  GET    /vendors    GET    /customers                                   │
│    /:id/rates        /:id/bookings                                      │
│  GET    /vendors    GET    /customers                                   │
│    /:id/performance  /:id/trips                                         │
│                                                                          │
│  Pipeline & Analytics                                                    │
│  ─────────────────────                                                   │
│  GET    /pipeline    GET    /analytics/revenue                          │
│  GET    /stats       GET    /analytics/conversion                       │
│  GET    /dashboard   GET    /analytics/agents                           │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Enquiry API Contracts

```typescript
// ── POST /enquiries ──
interface CreateEnquiryRequest {
  raw_input: string;
  source: EnquirySource;
  buyer_id?: string;                   // link to existing customer
  buyer_info?: {                       // or create new
    name: string;
    phone: string;
    email?: string;
  };
  assigned_agent_id?: string;
  tags?: string[];
}

interface CreateEnquiryResponse {
  id: string;
  status: "RAW";
  created_at: string;
  // Immediately starts ingestion pipeline
  pipeline_status: "QUEUED";
}

// ── GET /enquiries?state=...&assigned_to=...&priority=... ──
interface ListEnquiriesRequest {
  state?: EnquiryStatus;
  assigned_to?: string;
  priority?: EnquiryPriority;
  source?: EnquirySource;
  destination?: string;
  created_after?: string;
  created_before?: string;
  sort_by?: "created_at" | "priority" | "updated_at";
  sort_order?: "asc" | "desc";
  limit?: number;
  offset?: number;
}

interface ListEnquiriesResponse {
  items: EnquirySummary[];
  total: number;
  limit: number;
  offset: number;
}

interface EnquirySummary {
  id: string;
  status: EnquiryStatus;
  priority: EnquiryPriority;
  buyer_name: string;
  destinations: string[];
  budget_range: string | null;         // "₹50K-₹1L"
  assigned_agent: string | null;
  created_at: string;
  updated_at: string;
  sla_status: "ON_TRACK" | "AT_RISK" | "BREACHED";
}

// ── GET /enquiries/:id ──
interface GetEnquiryResponse {
  enquiry: Enquiry;                    // full entity
  timeline: TimelineEvent[];           // audit trail
  related_trips: string[];             // trip IDs
  communication_history: MessageSummary[];
  suggested_actions: SuggestedAction[];
}

// ── POST /enquiries/:id/parse ──
interface ParseEnquiryResponse {
  packet: CanonicalPacket;
  confidence: number;
  fields_extracted: string[];
  fields_missing: string[];
  fields_ambiguous: AmbiguityRef[];
}

// ── POST /enquiries/:id/validate ──
interface ValidateEnquiryResponse {
  result: "VALID" | "PARTIAL" | "ESCALATED";
  gates: ValidationGateResult[];
  auto_fixes_applied: AutoFix[];
}

interface ValidationGateResult {
  gate_id: string;
  gate_name: string;
  status: "PASS" | "FAIL" | "SKIP";
  reasons: string[];
  severity: "BLOCKER" | "WARNING" | "INFO";
}

// ── POST /enquiries/:id/triage ──
interface TriageEnquiryResponse {
  priority_score: number;
  suggested_agent_id: string;
  routing_reason: string;
  sla_response_by: string;
}

// ── PATCH /enquiries/:id ──
interface UpdateEnquiryRequest {
  status?: EnquiryStatus;
  assigned_agent_id?: string;
  priority?: EnquiryPriority;
  tags?: string[];
  notes?: string;
  follow_up_due_date?: string;
}

// ── Error Response (standard) ──
interface ApiError {
  error: {
    code: string;                      // "VALIDATION_ERROR"
    message: string;                   // human-readable
    details: {
      field: string;
      issue: string;
      suggestion?: string;
    }[];
  };
  request_id: string;
  timestamp: string;
}
```

### Booking API Contracts

```typescript
// ── POST /bookings ──
interface CreateBookingRequest {
  trip_id: string;
  type: BookingType;
  components: {
    type: BookingType;
    vendor_id: string;
    description: string;
    dates: DateRange;
    quantity: number;
    unit_price: Money;
    cancellation_policy_id?: string;
  }[];
  pricing_override?: Partial<BookingPricing>;
}

interface CreateBookingResponse {
  id: string;
  status: "DRAFT";
  components: BookingComponent[];
  pricing: BookingPricing;
  created_at: string;
}

// ── POST /bookings/:id/confirm ──
interface ConfirmBookingRequest {
  component_ids?: string[];            // confirm specific components (partial)
  payment_method: PaymentMethod;
  payment_amount: Money;
}

interface ConfirmBookingResponse {
  status: "CONFIRMED" | "PARTIAL";
  confirmed_components: string[];
  pending_components: string[];
  payment: {
    id: string;
    status: PaymentStatus;
    amount: Money;
  };
  confirmation_documents: DocumentRef[];
}

// ── POST /bookings/:id/cancel ──
interface CancelBookingRequest {
  reason: string;
  component_ids?: string[];            // cancel specific components
  waive_penalty?: boolean;
  refund_to: "ORIGINAL" | "WALLET" | "CREDIT_NOTE";
}

interface CancelBookingResponse {
  status: "CANCELLED";
  refund_amount: Money;
  penalty_amount: Money;
  refund_id: string | null;
  estimated_refund_date: string | null;
}

// ── GET /bookings/:id/health ──
interface BookingHealthResponse {
  booking_id: string;
  health_score: number;                // 0-100
  components: {
    id: string;
    type: BookingType;
    status: string;
    health: "GOOD" | "WARNING" | "CRITICAL";
    issues: string[];
  }[];
  payment_status: {
    total: Money;
    paid: Money;
    outstanding: Money;
    next_due: string | null;
    next_due_amount: Money | null;
  };
  document_status: {
    generated: number;
    pending: number;
    required: number;
  };
  risk_flags: string[];
}
```

### BFF Proxy Patterns

```typescript
// ── BFF: Frontend-specific endpoints ──
// These wrap backend APIs for frontend consumption

// BFF endpoint: GET /api/workspace/trips
// Combines: trips + bookings + payments + documents into workspace view
interface WorkspaceTripListResponse {
  trips: {
    id: string;
    enquiry_status: EnquiryStatus;
    booking_status: BookingStatus | null;
    buyer_name: string;
    destinations: string[];
    assigned_agent: string;
    priority: EnquiryPriority;
    total_value: Money | null;
    payment_status: "FULLY_PAID" | "PARTIAL" | "UNPAID" | null;
    health_score: number | null;
    next_action: {
      type: string;                    // "SEND_QUOTE", "FOLLOW_UP", "CONFIRM"
      due_by: string;
      description: string;
    } | null;
    created_at: string;
    updated_at: string;
  }[];
  total: number;
  pipeline_summary: {
    new: number;
    in_progress: number;
    awaiting_response: number;
    confirmed: number;
    completed: number;
  };
}

// BFF endpoint: GET /api/workspace/trips/:id/detail
// Full trip detail combining all subsystems
interface WorkspaceTripDetailResponse {
  trip: Trip;
  enquiry: Enquiry;
  booking: Booking | null;
  timeline: TimelineEvent[];
  communications: MessageSummary[];
  documents: DocumentRef[];
  payments: PaymentSummary[];
  assigned_agent: HumanAgent;
  buyer: Buyer;
  vendors: Vendor[];
  health: BookingHealthResponse | null;
  suggested_actions: SuggestedAction[];
  ai_insights: AIInsight[];
}

interface SuggestedAction {
  type: string;
  priority: "HIGH" | "MEDIUM" | "LOW";
  title: string;
  description: string;
  action_endpoint: string;
  action_payload: Record<string, unknown>;
  auto_executable: boolean;
}

interface AIInsight {
  type: "OPPORTUNITY" | "RISK" | "EFFICIENCY" | "CUSTOMER";
  title: string;
  description: string;
  confidence: number;
  actionable: boolean;
}
```

### Real-Time Event Contracts

```typescript
// ── WebSocket / SSE Payloads ──

// Connection: ws://localhost:8000/ws?token=...&agency_id=...
// Subscribe to events for a specific agency

interface WSEventEnvelope {
  type: "EVENT" | "NOTIFICATION" | "PING";
  event?: SSEEventPayload;
  notification?: WSNotification;
}

interface SSEEventPayload {
  event_type: string;
  aggregate_id: string;
  aggregate_type: string;
  payload: Record<string, unknown>;
  occurred_at: string;
  correlation_id: string;
}

interface WSNotification {
  id: string;
  type: "SLA_WARNING" | "SLA_BREACH" | "NEW_ENQUIRY" | "PAYMENT_RECEIVED"
    | "BOOKING_CONFIRMED" | "DISRUPTION_ALERT" | "AGENT_ASSIGNMENT"
    | "SYSTEM_ALERT";
  title: string;
  message: string;
  priority: "URGENT" | "HIGH" | "NORMAL" | "LOW";
  action_url: string | null;
  action_label: string | null;
  dismissible: boolean;
  created_at: string;
}

// ── Real-time subscriptions ──
// Client subscribes to specific event streams:
//
// { "subscribe": "enquiries", "filters": { "assigned_to": "me" } }
// { "subscribe": "bookings", "filters": { "status": ["CONFIRMED", "TICKETED"] } }
// { "subscribe": "notifications", "filters": { "priority": ["URGENT", "HIGH"] } }
//
// Server pushes matching events:
// { "type": "EVENT", "event": { "event_type": "ENQUIRY_ASSIGNED", ... } }
// { "type": "NOTIFICATION", "notification": { "type": "SLA_WARNING", ... } }
```

### Validation Schema

```typescript
// ── Shared validation (used by both frontend and backend) ──

interface ValidationRule {
  field: string;
  rules: {
    type: "REQUIRED" | "MIN_LENGTH" | "MAX_LENGTH" | "PATTERN"
      | "MIN_VALUE" | "MAX_VALUE" | "ENUM" | "DATE_RANGE"
      | "PHONE" | "EMAIL" | "GST" | "PAN";
    params: Record<string, unknown>;
    message: string;
  }[];
}

// Example: Enquiry validation rules
const enquiryValidationRules: ValidationRule[] = [
  {
    field: "raw_input",
    rules: [
      { type: "REQUIRED", params: {}, message: "Raw input is required" },
      { type: "MIN_LENGTH", params: { min: 10 }, message: "Input too short" },
    ],
  },
  {
    field: "source",
    rules: [
      { type: "REQUIRED", params: {}, message: "Source is required" },
      { type: "ENUM", params: { values: ["WHATSAPP", "PHONE", "EMAIL", "WEBSITE", "WALK_IN", "REFERRAL", "PORTAL"] }, message: "Invalid source" },
    ],
  },
  {
    field: "buyer_info.phone",
    rules: [
      { type: "REQUIRED", params: {}, message: "Phone is required for new buyer" },
      { type: "PHONE", params: { country: "IN" }, message: "Invalid Indian phone number" },
    ],
  },
];
```

---

## Open Problems

1. **Type sync drift** — Frontend TypeScript types and backend Pydantic models can drift. Need code generation (OpenAPI → TypeScript) or shared schema definitions to prevent mismatches.

2. **BFF over-fetching** — The workspace detail endpoint combines 8+ backend calls into one response. If any sub-call is slow, the whole response is delayed. Need parallel fetching with partial response support.

3. **WebSocket reconnection** — Agent workspace loses real-time updates if WebSocket drops. Need automatic reconnection with event replay for missed events.

4. **Pagination consistency** — List endpoints returning inconsistent total counts when data changes during pagination. Cursor-based pagination needed for high-churn queries.

5. **File upload contracts** — Document uploads (passports, visas, tickets) need multipart form handling with size limits, virus scanning, and OCR extraction triggers.

---

## Next Steps

- [ ] Generate OpenAPI 3.1 spec from Pydantic models
- [ ] Auto-generate TypeScript API client from OpenAPI spec
- [ ] Build BFF proxy layer with parallel sub-request aggregation
- [ ] Implement WebSocket event streaming with subscription filters
- [ ] Create shared validation schema (JSON Schema) for frontend + backend
