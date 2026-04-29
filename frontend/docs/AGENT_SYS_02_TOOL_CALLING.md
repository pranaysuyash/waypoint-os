# Agentic Systems & AI Orchestration — Tool Calling & Function Integration

> Research document for tool calling patterns, function schemas, tool execution engines, and API integration for AI agents in the travel domain.

---

## Key Questions

1. **How do we design tool schemas that agents can reliably invoke?**
2. **What tool execution patterns ensure safety and reliability?**
3. **How do we handle tool failures, retries, and fallbacks?**
4. **What travel-specific tools does the agent ecosystem need?**

---

## Research Areas

### Tool Schema Design

```typescript
interface ToolDefinition {
  name: string;                        // "search_flights"
  description: string;                 // when and why to use this tool
  category: ToolCategory;
  parameters: ToolParameterSchema;
  returns: ToolReturnSchema;
  side_effects: "NONE" | "READ_ONLY" | "WRITES_DATA" | "EXTERNAL_API" | "FINANCIAL";
  requires_approval: boolean;          // human-in-the-loop for dangerous tools
  rate_limit: RateLimit | null;
  cost_per_call: Money | null;
}

type ToolCategory =
  | "DATA_RETRIEVAL"    // search, lookup, query
  | "DATA_MUTATION"     // create, update, delete
  | "EXTERNAL_API"      // third-party integration
  | "AI_INFERENCE"      // model inference
  | "COMMUNICATION"     // send messages
  | "FINANCIAL"         // payments, refunds
  | "DOCUMENT"          // PDF, voucher generation
  | "SCHEDULING";       // calendar, reminders

// ── Example: Flight search tool ──
const flightSearchTool: ToolDefinition = {
  name: "search_flights",
  description: "Search for available flights between two cities on specific dates. Use when building itinerary options or checking availability.",
  category: "EXTERNAL_API",
  parameters: {
    type: "object",
    properties: {
      origin: { type: "string", description: "IATA code or city name", examples: ["DEL", "Mumbai"] },
      destination: { type: "string", description: "IATA code or city name", examples: ["SIN", "Singapore"] },
      date: { type: "string", format: "date", description: "Departure date (YYYY-MM-DD)" },
      return_date: { type: "string", format: "date", description: "Return date, if round trip" },
      passengers: { type: "number", minimum: 1, maximum: 9 },
      class: { type: "string", enum: ["ECONOMY", "PREMIUM_ECONOMY", "BUSINESS", "FIRST"], default: "ECONOMY" },
      max_stops: { type: "number", enum: [0, 1, 2] },
      max_results: { type: "number", default: 10, maximum: 50 },
    },
    required: ["origin", "destination", "date", "passengers"],
  },
  returns: {
    type: "object",
    properties: {
      flights: {
        type: "array",
        items: {
          type: "object",
          properties: {
            airline: { type: "string" },
            flight_number: { type: "string" },
            departure: { type: "string", format: "datetime" },
            arrival: { type: "string", format: "datetime" },
            duration_minutes: { type: "number" },
            stops: { type: "number" },
            price: { type: "object", properties: { amount: { type: "number" }, currency: { type: "string" } } },
            seats_available: { type: "number" },
            booking_class: { type: "string" },
          },
        },
      },
      total_results: { type: "number" },
      search_id: { type: "string" },
    },
  },
  side_effects: "EXTERNAL_API",
  requires_approval: false,
  rate_limit: { calls_per_minute: 30, calls_per_hour: 200 },
  cost_per_call: { amount: 50, currency: "INR" },  // API cost
};
```

### Travel Domain Tool Catalog

```typescript
// ── Complete tool catalog for travel agents ──
// ┌─────────────────────────────────────────────────────────┐
// │  Category        | Tools                                  │
// │  ─────────────────────────────────────────────────────── │
// │  INTAKE          | parse_note, extract_fields,            │
// │                  | validate_packet, enrich_context,       │
// │                  | detect_language, classify_intent       │
// │                                                           │
// │  SEARCH          | search_flights, search_hotels,         │
// │                  | search_activities, search_transport,   │
// │                  | search_packages, search_vendors        │
// │                                                           │
// │  PRICING         | get_flight_price, get_hotel_rate,     │
// │                  | get_activity_price, estimate_trip_cost,│
// │                  | compare_prices, get_dynamic_rate       │
// │                                                           │
// │  AVAILABILITY    | check_flight_seats, check_hotel_rooms, │
// │                  | check_activity_slots, check_vendor_cal │
// │                                                           │
// │  BOOKING         | create_booking, modify_booking,        │
// │                  | cancel_booking, confirm_booking,       │
// │                  | issue_ticket, generate_voucher         │
// │                                                           │
// │  CUSTOMER        | get_customer_profile, get_booking_hist,│
// │                  | get_preferences, get_loyalty_tier,     │
// │                  | get_communication_history              │
// │                                                           │
// │  ITINERARY       | optimize_route, calculate_pace,        │
// │                  | score_itinerary, suggest_alternatives, │
// │                  | get_opening_hours, get_travel_time     │
// │                                                           │
// │  COMMUNICATION   | send_whatsapp, send_email, send_sms,   │
// │                  | schedule_followup, get_template,       │
// │                  | analyze_sentiment                       │
// │                                                           │
// │  VENDOR          | get_vendor_profile, get_vendor_rates,  │
// │                  | check_vendor_performance, contact_vendor│
// │                                                           │
// │  DOCUMENT        | generate_itinerary_pdf, generate_quote,│
// │                  | generate_voucher, generate_invoice     │
// │                                                           │
// │  PAYMENT         | initiate_payment, capture_payment,     │
// │                  | refund_payment, get_payment_status      │
// │                                                           │
// │  KNOWLEDGE       | search_destination_guide,               │
// │                  | get_visa_requirements, get_weather,     │
// │                  | get_travel_advisory, get_event_calendar │
// │                                                           │
// │  ANALYTICS       | get_pipeline_stats, get_conversion_rate,│
// │                  | get_agent_performance, get_revenue     │
// └─────────────────────────────────────────────────────────┘
```

### Tool Execution Engine

```typescript
interface ToolExecutor {
  execute(call: ToolCall): Promise<ToolResult>;
  validateParams(call: ToolCall): ValidationResult;
  checkRateLimit(tool_name: string): boolean;
  requiresApproval(call: ToolCall): boolean;
}

interface ToolCall {
  id: string;
  tool_name: string;
  parameters: Record<string, unknown>;
  calling_agent: string;
  workflow_id: string;
  timestamp: string;
}

interface ToolResult {
  call_id: string;
  status: "SUCCESS" | "ERROR" | "TIMEOUT" | "RATE_LIMITED" | "PENDING_APPROVAL";
  data: Record<string, unknown> | null;
  error: ToolError | null;
  execution_time_ms: number;
  cost: Money | null;
  cached: boolean;
}

interface ToolError {
  code: string;
  message: string;
  retryable: boolean;
  retry_after_seconds: number | null;
  suggested_fix: string | null;
}

// ── Execution flow with safety ──
// ┌─────────────────────────────────────────────────────┐
// │  Tool Call Received                                   │
// │       │                                               │
// │       ├── Validate parameters against schema          │
// │       │    └── Invalid? → return error immediately    │
// │       │                                               │
// │       ├── Check rate limits                           │
// │       │    └── Limited? → return rate limit error     │
// │       │                                               │
// │       ├── Check approval requirements                 │
// │       │    └── Needs approval? → queue for human      │
// │       │                                               │
// │       ├── Check cache (for read-only tools)           │
// │       │    └── Cached? → return cached result         │
// │       │                                               │
// │       ├── Execute tool                                │
// │       │    ├── Timeout guard                          │
// │       │    └── Error handling                         │
// │       │                                               │
// │       ├── Log execution (audit trail)                 │
// │       │                                               │
// │       └── Return result                               │
// └─────────────────────────────────────────────────────┘
```

### Tool Chaining Patterns

```typescript
// ── Common tool chains in travel domain ──

// Chain 1: Full itinerary pricing
// search_flights → search_hotels → search_activities
//   → estimate_trip_cost → compare_prices

// Chain 2: Booking with confirmation
// check_availability → create_booking → initiate_payment
//   → capture_payment → confirm_booking → generate_voucher
//   → send_whatsapp(confirmation)

// Chain 3: Disruption handling
// detect_disruption → analyze_impact → search_alternatives
//   → modify_booking → notify_customer → update_itinerary

interface ToolChain {
  name: string;
  description: string;
  steps: ToolChainStep[];
  rollback_chain: ToolChainStep[];     // undo on failure
}

interface ToolChainStep {
  tool: string;
  input_mapping: Record<string, string>;  // map outputs from previous steps
  condition: string | null;            // when to execute this step
  on_failure: "ROLLBACK" | "SKIP" | "RETRY" | "ESCALATE";
  max_retries: number;
}
```

---

## Open Problems

1. **Tool hallucination** — Agents may invent tool names or parameters. Strict schema validation and a closed tool registry prevent this, but add friction.

2. **Chained tool latency** — Sequential tool calls (search → price → book) create compounding latency. Need parallel execution where possible and streaming results.

3. **Cost attribution** — Multiple agents using the same tools makes it hard to attribute costs to specific workflows or customers. Need per-workflow cost tracking.

4. **Tool versioning** — Third-party APIs change. When a vendor updates their API, all agents using that tool need to adapt. Need versioned tool definitions with migration paths.

---

## Next Steps

- [ ] Build tool registry with schema validation and approval workflows
- [ ] Implement tool execution engine with rate limiting and caching
- [ ] Create tool chaining framework with rollback support
- [ ] Design per-workflow cost tracking for tool usage
- [ ] Build tool observability dashboard with execution metrics
