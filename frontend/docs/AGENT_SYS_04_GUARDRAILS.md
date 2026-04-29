# Agentic Systems & AI Orchestration — Guardrails, Safety & Evaluation

> Research document for agent guardrails, safety mechanisms, human-in-the-loop patterns, evaluation frameworks, and responsible AI deployment in travel.

---

## Key Questions

1. **How do we prevent agents from taking harmful actions?**
2. **When should agents escalate to humans?**
3. **How do we evaluate agent performance and reliability?**
4. **What responsible AI practices apply to travel agentic systems?**

---

## Research Areas

### Agent Guardrail Architecture

```typescript
// ── Multi-layer guardrail system ──
// ┌─────────────────────────────────────────────────────┐
// │                                                        │
// │  ┌───────────────────────────────────────────────┐   │
// │  │ Layer 1: INPUT VALIDATION                     │   │
// │  │ - Schema validation                           │   │
// │  │ - Prompt injection detection                  │   │
// │  │ - PII redaction                               │   │
// │  └───────────────────────────────────────────────┘   │
// │                      │                                 │
// │  ┌───────────────────────────────────────────────┐   │
// │  │ Layer 2: ACTION AUTHORIZATION                 │   │
// │  │ - Tool whitelist per agent role               │   │
// │  │ - Financial limits (₹X max per action)        │   │
// │  │ - Data access scope (tenant isolation)        │   │
// │  └───────────────────────────────────────────────┘   │
// │                      │                                 │
// │  ┌───────────────────────────────────────────────┐   │
// │  │ Layer 3: OUTPUT VALIDATION                    │   │
// │  │ - Fact-checking against knowledge base        │   │
// │  │ - PII detection in responses                  │   │
// │  │ - Brand voice compliance                      │   │
// │  └───────────────────────────────────────────────┘   │
// │                      │                                 │
// │  ┌───────────────────────────────────────────────┐   │
// │  │ Layer 4: BEHAVIORAL MONITORING                │   │
// │  │ - Hallucination detection                     │   │
// │  │ - Repetition / loop detection                 │   │
// │  │ - Cost anomaly detection                      │   │
// │  │ - Latency anomaly detection                   │   │
// │  └───────────────────────────────────────────────┘   │
// │                                                        │
// └────────────────────────────────────────────────────────┘

interface Guardrail {
  id: string;
  name: string;
  layer: GuardrailLayer;
  condition: GuardrailCondition;
  action: GuardrailAction;
}

type GuardrailLayer = "INPUT" | "AUTHORIZATION" | "OUTPUT" | "BEHAVIORAL";

type GuardrailCondition =
  | { type: "MAX_TOOL_CALLS"; max: number }
  | { type: "MAX_COST"; limit: Money }
  | { type: "FINANCIAL_ACTION"; max_amount: Money }
  | { type: "SENSITIVE_DATA"; patterns: string[] }
  | { type: "LOOP_DETECTION"; max_repeated_calls: number }
  | { type: "HALLUCINATION_CHECK"; confidence_threshold: number }
  | { type: "TIMEOUT"; max_seconds: number }
  | { type: "TOOL_WHITELIST"; allowed_tools: string[] }
  | { type: "DATA_SCOPE"; tenant_only: boolean };

type GuardrailAction =
  | { type: "BLOCK"; message: string }
  | { type: "ESCALATE"; to: string; reason: string }
  | { type: "MODIFY"; transform: string }
  | { type: "LOG"; level: "INFO" | "WARN" | "ERROR" }
  | { type: "RATE_LIMIT"; cooldown_seconds: number };
```

### Human-in-the-Loop Patterns

```typescript
interface HumanLoopConfig {
  trigger: HumanLoopTrigger;
  approver: string;                    // role or specific person
  timeout_seconds: number;
  timeout_action: "ABORT" | "AUTO_APPROVE" | "ESCALATE";
  notification_channel: "IN_APP" | "WHATSAPP" | "SLACK" | "EMAIL";
}

type HumanLoopTrigger =
  // Financial
  | { type: "FINANCIAL_THRESHOLD"; amount: Money; action: "PAYMENT" | "REFUND" | "DISCOUNT" }
  // Quality
  | { type: "LOW_CONFIDENCE"; threshold: number; action: "EXTRACTION" | "CLASSIFICATION" }
  // Safety
  | { type: "RISK_DETECTED"; risk_type: "FRAUD" | "COMPLIANCE" | "SAFETY" }
  // Customer-facing
  | { type: "CUSTOMER_COMMUNICATION"; channels: ("WHATSAPP" | "EMAIL")[]; first_time: boolean }
  // Booking
  | { type: "BOOKING_ACTION"; action: "CREATE" | "CANCEL" | "MODIFY"; value_above: Money }
  // Escalation
  | { type: "AGENT_ESCALATION"; reason: "UNABLE_TO_HELP" | "POLICY_QUESTION" | "COMPLAINT" };

// ── Human approval flow ──
// ┌─────────────────────────────────────────────────────┐
// │  AGENT: "Proposing ₹15,000 refund for TP-101"        │
// │       │                                               │
// │       ├── Guardrail: amount > ₹10K → NEEDS APPROVAL │
// │       │                                               │
// │       ▼                                               │
// │  ┌─────────────────────────────────────────┐        │
// │  │ Approval Request                          │        │
// │  │                                            │        │
// │  │ Agent: AI Booking Agent                   │        │
// │  │ Action: Refund ₹15,000                    │        │
// │  │ Reason: Flight cancelled by airline       │        │
// │  │ Customer: Priya Sharma                    │        │
// │  │ Policy: Full refund applicable             │        │
// │  │                                            │        │
// │  │ [Approve] [Reject] [Modify Amount]        │        │
// │  └─────────────────────────────────────────┘        │
// │       │                                               │
// │       ├── Approved → execute refund                  │
// │       └── Rejected → agent notified with reason      │
// └─────────────────────────────────────────────────────┘
```

### Agent Evaluation Framework

```typescript
interface AgentEvaluation {
  agent_id: string;
  evaluation_type: "UNIT" | "INTEGRATION" | "E2E" | "ADVERSARIAL" | "REGRESSION";

  test_cases: AgentTestCase[];
  results: AgentTestResult[];
  metrics: AgentMetrics;
}

interface AgentTestCase {
  id: string;
  name: string;
  category: string;
  input: Record<string, unknown>;
  expected_output: Record<string, unknown> | null;  // null for generative
  evaluation_criteria: EvaluationCriteria[];
  difficulty: "EASY" | "MEDIUM" | "HARD" | "ADVERSARIAL";
}

interface EvaluationCriteria {
  dimension: "ACCURACY" | "COMPLETENESS" | "RELEVANCE" | "SAFETY" | "EFFICIENCY";
  weight: number;
  scoring: "BINARY" | "SCALE_1_5" | "LLM_JUDGE" | "HUMAN_JUDGE";
}

// ── Evaluation metrics ──
// ┌─────────────────────────────────────────────────────┐
// │  Agent: Intake Agent          Date: 2026-04-29        │
// │                                                       │
// │  Test Suite: 200 cases                                │
// │                                                       │
// │  Accuracy:        94.5% (189/200 correct)            │
// │  Completeness:    91.0% (avg fields extracted/total) │
// │  Safety:          100% (0 PII leaks, 0 harmful out)  │
// │  Efficiency:      2.1s avg, 1.8 tool calls avg       │
// │  Cost:            ₹0.42 per invocation avg           │
// │                                                       │
// │  Failure analysis:                                    │
// │  - Messy handwriting OCR: 4 failures                 │
// │  - Ambiguous destinations: 3 failures                │
// │  - Multi-language input: 2 failures                  │
// │  - Extremely long notes: 2 failures                  │
// │                                                       │
// │  Regression check: ✅ No regressions vs v2.1          │
// │  Adversarial check: ✅ 50/50 passed                   │
// └─────────────────────────────────────────────────────┘

// ── Automated evaluation pipeline ──
// ┌─────────────────────────────────────────────────────┐
// │  Evaluation Pipeline                                   │
// │       │                                                │
// │       ├── Unit tests (fast, deterministic)           │
// │       │    ├── Field extraction accuracy             │
// │       │    ├── Validation gate logic                 │
// │       │    └── Tool schema compliance                │
// │       │                                                │
// │       ├── Integration tests (medium speed)           │
// │       │    ├── End-to-end intake flow                │
// │       │    ├── Orchestrator → agent delegation       │
// │       │    └── Tool execution + error handling       │
// │       │                                                │
// │       ├── E2E tests (slow, full workflow)            │
// │       │    ├── Customer inquiry → quote generated    │
// │       │    ├── Disruption detection → re-routing     │
// │       │    └── Booking → confirmation → documents    │
// │       │                                                │
// │       ├── Adversarial tests                           │
// │       │    ├── Prompt injection attempts             │
// │       │    ├── PII extraction attempts               │
// │       │    ├── Financial manipulation attempts       │
// │       │    └── Policy circumvention attempts         │
// │       │                                                │
// │       └── Regression tests                            │
// │            ├── Golden dataset comparison              │
// │            ├── Cost regression detection              │
// │            └── Latency regression detection           │
// └─────────────────────────────────────────────────────┘
```

### Responsible AI for Travel

```typescript
interface ResponsibleAIConfig {
  // Bias prevention
  bias_checks: {
    pricing_fairness: boolean;          // no price discrimination
    recommendation_diversity: boolean;  // don't always suggest same destinations
    language_fairness: boolean;         // equal quality across languages
  };

  // Transparency
  transparency: {
    ai_generated_label: boolean;        // mark AI-generated content
    decision_explainability: boolean;   // explain why agent made a choice
    confidence_display: boolean;        // show confidence scores
    human_escalation_option: boolean;   // always offer human agent
  };

  // Data handling
  data_handling: {
    pii_minimization: boolean;          // only collect needed PII
    retention_limits: boolean;          // auto-delete old data
    cross_tenant_isolation: boolean;    // strict data separation
    audit_trail: boolean;               // log all AI actions
  };

  // Customer protection
  customer_protection: {
    max_ai_actions_without_human: number;
    financial_action_approval: boolean;
    complaint_auto_escalation: boolean;
    refund_policy_compliance: boolean;
  };
}

// ── AI transparency in customer communication ──
// ┌─────────────────────────────────────────────────────┐
// │  WhatsApp Message:                                     │
// │                                                       │
// │  📋 Here's your Singapore itinerary (AI-assisted):    │
// │                                                       │
// │  Day 1: Arrival + Marina Bay                          │
// │  Day 2: Sentosa + Universal Studios                   │
// │  Day 3: Gardens + Orchard Road                        │
// │  Day 4: Little India + Departure                      │
// │                                                       │
// │  💰 Estimated cost: ₹1,40,000 (2 pax)                │
// │                                                       │
// │  [This itinerary was generated with AI assistance.    │
// │   Your travel agent Ravi will review before           │
// │   final confirmation.]                                │
// │                                                       │
// │  Reply "human" to speak with Ravi directly.           │
// └─────────────────────────────────────────────────────┘
```

---

## Open Problems

1. **Hallucination detection** — LLMs can generate plausible but incorrect travel information (wrong opening hours, non-existent restaurants). Need fact-checking against verified databases.

2. **Guardrail false positives** — Overly aggressive guardrails block legitimate agent actions, causing frustration. Need calibrated thresholds with per-agent tuning.

3. **Evaluation dataset maintenance** — Travel data changes frequently (new hotels, changed prices, updated schedules). Test datasets need regular updates to remain relevant.

4. **Multi-agent accountability** — When 3 agents work in parallel and produce a wrong result, which agent is responsible? Need end-to-end traceability with causal chains.

5. **Cultural sensitivity** — AI agents may not understand cultural nuances (religious preferences, dietary restrictions, family dynamics). Need culture-aware training and evaluation.

---

## Next Steps

- [ ] Build multi-layer guardrail system with configurable rules
- [ ] Implement human-in-the-loop approval workflows
- [ ] Create agent evaluation framework with automated test pipeline
- [ ] Design responsible AI compliance dashboard
- [ ] Build adversarial test suite for prompt injection and PII extraction
- [ ] Study responsible AI frameworks (Anthropic's Responsible Scaling, Google's AI Principles)
