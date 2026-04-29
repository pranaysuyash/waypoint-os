# Agentic Systems & AI Orchestration — Agent Architecture

> Research document for AI agent architecture patterns, agent roles, communication protocols, and orchestration strategies for the travel domain.

---

## Key Questions

1. **What agent architecture patterns work for multi-step travel workflows?**
2. **How do we define distinct agent roles with clear responsibilities?**
3. **How do agents communicate and coordinate in a multi-agent system?**
4. **What orchestration patterns ensure reliable workflow execution?**

---

## Research Areas

### Agent Taxonomy for Travel

```typescript
// ── Agent Role Definitions ──
// ┌───────────────────────────────────────────────────────────────┐
// │                                                                │
// │  ORCHESTRATOR AGENT (Top-level coordinator)                    │
// │  ├── INTAKE AGENT (Raw note → structured packet)               │
// │  │   ├── Extraction Agent (field extraction)                  │
// │  │   ├── Validation Agent (quality gates)                     │
// │  │   └── Enrichment Agent (destination/season context)        │
// │  │                                                              │
// │  ├── TRIAGE AGENT (Categorize + route)                         │
// │  │   ├── Scoring Agent (priority + value estimation)          │
// │  │   └── Routing Agent (agent matching)                       │
// │  │                                                              │
// │  ├── PLANNING AGENT (Build itinerary)                          │
// │  │   ├── Route Optimizer Agent                                 │
// │  │   ├── Cost Estimator Agent                                  │
// │  │   ├── Preference Matcher Agent                              │
// │  │   └── Vendor Lookup Agent                                   │
// │  │                                                              │
// │  ├── BOOKING AGENT (Execute bookings)                          │
// │  │   ├── Availability Checker Agent                           │
// │  │   ├── Price Negotiator Agent                                │
// │  │   ├── Payment Agent                                         │
// │  │   └── Confirmation Agent                                    │
// │  │                                                              │
// │  ├── COMMUNICATION AGENT (Customer interaction)                │
// │  │   ├── Message Composer Agent                                │
// │  │   ├── Follow-up Scheduler Agent                             │
// │  │   └── Sentiment Analyzer Agent                              │
// │  │                                                              │
// │  └── MONITORING AGENT (Trip oversight)                         │
// │      ├── Disruption Detector Agent                             │
// │      ├── Re-routing Agent                                      │
// │      └── Alert Agent                                           │
// │                                                                │
// └───────────────────────────────────────────────────────────────┘

interface AgentDefinition {
  id: string;
  name: string;
  role: AgentRole;
  description: string;

  // Capabilities
  tools: ToolDefinition[];
  input_schema: AgentInputSchema;
  output_schema: AgentOutputSchema;

  // Configuration
  model: AgentModelConfig;
  max_iterations: number;
  timeout_seconds: number;

  // Guardrails
  allowed_actions: AgentAction[];
  blocked_actions: AgentAction[];
  escalation_conditions: EscalationCondition[];
  cost_limit_per_invocation: Money | null;
}

type AgentRole =
  // Core workflow agents
  | "ORCHESTRATOR" | "INTAKE" | "TRIAGE" | "PLANNING"
  | "BOOKING" | "COMMUNICATION" | "MONITORING"
  // Sub-agents
  | "EXTRACTOR" | "VALIDATOR" | "ENRICHER" | "SCORER"
  | "ROUTER" | "ROUTE_OPTIMIZER" | "COST_ESTIMATOR"
  | "PREFERENCE_MATCHER" | "VENDOR_LOOKUP" | "AVAILABILITY_CHECKER"
  | "PRICE_NEGOTIATOR" | "PAYMENT" | "CONFIRMATION"
  | "MESSAGE_COMPOSER" | "FOLLOWUP_SCHEDULER" | "SENTIMENT_ANALYZER"
  | "DISRUPTION_DETECTOR" | "REROUTER" | "ALERTER"
  // Utility agents
  | "MEMORY" | "KNOWLEDGE_RETRIEVER" | "TRANSLATOR";
```

### Agent Communication Protocol

```typescript
interface AgentMessage {
  id: string;
  from_agent: string;
  to_agent: string;
  message_type: AgentMessageType;
  payload: Record<string, unknown>;
  metadata: MessageMetadata;
  correlation_id: string;              // links to original request
  parent_message_id: string | null;    // conversation threading
}

type AgentMessageType =
  | "REQUEST"           // asking another agent to do something
  | "RESPONSE"          // result of a request
  | "DELEGATE"          // orchestrator delegating to sub-agent
  | "ESCALATE"          // agent requesting human intervention
  | "NOTIFY"            // informational broadcast
  | "ERROR"             // error report
  | "TOOL_CALL"         // agent invoking a tool
  | "TOOL_RESULT";      // tool returning results

interface MessageMetadata {
  timestamp: string;
  priority: "LOW" | "MEDIUM" | "HIGH" | "URGENT";
  ttl_seconds: number | null;
  retry_count: number;
  max_retries: number;
}

// ── Agent communication flow ──
// ┌─────────────────────────────────────────────────────┐
// │  Customer inquiry: "Kerala trip, 5 days, ₹50K, 4 pax"│
// │                                                       │
// │  ORCHESTRATOR receives request                        │
// │    │                                                  │
// │    ├── DELEGATE → INTAKE AGENT                        │
// │    │     ├── TOOL_CALL → parse_note(raw_input)       │
// │    │     ├── TOOL_CALL → extract_fields(parsed)      │
// │    │     ├── TOOL_CALL → validate_packet(packet)     │
// │    │     └── RESPONSE → {packet, confidence: 0.87}   │
// │    │                                                  │
// │    ├── DELEGATE → TRIAGE AGENT                        │
// │    │     ├── TOOL_CALL → score_priority(packet)      │
// │    │     ├── TOOL_CALL → match_agent(skills)         │
// │    │     └── RESPONSE → {priority: HIGH, agent: Ravi}│
// │    │                                                  │
// │    ├── DELEGATE → PLANNING AGENT                      │
// │    │     ├── TOOL_CALL → optimize_route(destinations)│
// │    │     ├── TOOL_CALL → estimate_costs(route)       │
// │    │     ├── TOOL_CALL → match_preferences(profile)  │
// │    │     └── RESPONSE → {itinerary, cost: ₹47K}      │
// │    │                                                  │
// │    └── RESPONSE → Human Agent                         │
// │          "Kerala itinerary ready. ₹47K, within budget."│
// └─────────────────────────────────────────────────────┘
```

### Orchestration Patterns

```typescript
type OrchestrationPattern =
  | "SEQUENTIAL"        // A → B → C (each waits for previous)
  | "PARALLEL"          // A + B + C (all run simultaneously)
  | "PIPELINE"          // A → B → C (streaming, B starts as A produces)
  | "FAN_OUT_FAN_IN"    // one → many → aggregate
  | "MAP_REDUCE"        // distribute work → collect results
  | "HIERARCHICAL"      // orchestrator → sub-orchestrators → agents
  | "EVENT_DRIVEN"      // agents react to events
  | "CONSENSUS";        // multiple agents vote on decision

// ── Pattern selection by task ──
// ┌─────────────────────────────────────────────────────┐
// │  Task                    | Pattern   | Why            │
// │  ─────────────────────────────────────────────────── │
// │  Parse + validate        | PIPELINE  | Stream results │
// │  Score + route + assign  | PARALLEL  | Independent    │
// │  Build itinerary         | HIERARCHICAL | Complex,    │
// │                          |           | multi-step     │
// │  Check availability      | FAN_OUT   | Multiple       │
// │  (multiple vendors)      | _FAN_IN   | vendors        │
// │  Handle disruption       | EVENT_    | Reactive       │
// │                          | DRIVEN    │                │
// │  Price comparison        | MAP_      | Compare many   │
// │                          | REDUCE    │ options        │
// └─────────────────────────────────────────────────────┘

interface OrchestrationPlan {
  workflow_id: string;
  pattern: OrchestrationPattern;
  steps: OrchestrationStep[];
  timeout_total_seconds: number;
  retry_policy: RetryPolicy;
  fallback_plan: OrchestrationPlan | null;
}

interface OrchestrationStep {
  id: string;
  agent: string;
  input: StepInput;
  output_key: string;                  // key to store result
  condition: string | null;            // when to run this step
  parallel_group: number | null;       // steps with same group run in parallel
  depends_on: string[];                // step IDs this depends on
  timeout_seconds: number;
  on_failure: "RETRY" | "SKIP" | "ESCALATE" | "ABORT";
}
```

### Agent Memory & State

```typescript
interface AgentMemory {
  // Short-term: within current conversation/workflow
  working_memory: WorkingMemory;

  // Medium-term: across conversations for same entity
  entity_memory: EntityMemory;

  // Long-term: learned patterns and preferences
  knowledge_memory: KnowledgeMemory;
}

interface WorkingMemory {
  workflow_id: string;
  messages: AgentMessage[];
  tool_results: Map<string, ToolResult>;
  intermediate_outputs: Map<string, unknown>;
  created_at: string;
}

interface EntityMemory {
  entity_type: "CUSTOMER" | "TRIP" | "VENDOR" | "AGENT";
  entity_id: string;
  recent_interactions: AgentMessage[];
  learned_preferences: Record<string, unknown>;
  last_updated: string;
}

interface KnowledgeMemory {
  domain_facts: Map<string, string>;           // "Kerala_monsoon: June-September"
  successful_patterns: Map<string, Pattern>;    // itineraries that got 5-star reviews
  failure_patterns: Map<string, Pattern>;       // approaches that led to complaints
  vendor_intelligence: Map<string, VendorIntel>;
}
```

---

## Open Problems

1. **Agent hallucination in tool calls** — Agents may generate invalid tool parameters or call non-existent tools. Need strict schema validation before tool execution.

2. **Orchestration complexity** — Hierarchical orchestration with multiple levels creates debugging and tracing challenges. Need observability at every level.

3. **Agent context window limits** — Long workflows with many tool calls may exceed context windows. Need summarization strategies for intermediate results.

4. **Cost control** — Each agent invocation costs API tokens. A single complex workflow may invoke 10+ agents with 5+ tool calls each. Need per-workflow cost tracking and budgets.

5. **Agent reliability** — LLM-based agents are non-deterministic. Same input may produce different results. Need confidence scoring and validation layers.

---

## Next Steps

- [ ] Design agent registry with role definitions and capability declarations
- [ ] Implement message bus for inter-agent communication
- [ ] Build orchestrator engine supporting all 8 orchestration patterns
- [ ] Create agent memory system with working/entity/knowledge layers
- [ ] Design agent observability dashboard with trace visualization
