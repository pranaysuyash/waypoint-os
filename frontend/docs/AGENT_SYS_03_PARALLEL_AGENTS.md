# Agentic Systems & AI Orchestration — Parallel Agent Patterns

> Research document for parallel agent execution, task distribution, result aggregation, consensus mechanisms, and conflict resolution in multi-agent systems.

---

## Key Questions

1. **When and how do we run multiple agents in parallel?**
2. **How do we aggregate results from parallel agents?**
3. **How do agents reach consensus when results conflict?**
4. **What patterns prevent parallel agents from creating race conditions?**

---

## Research Areas

### Parallel Execution Patterns

```typescript
// ── When to parallelize ──
// ┌─────────────────────────────────────────────────────┐
// │  Pattern                  | Example                  │
// │  ─────────────────────────────────────────────────── │
// │  Independent lookups      | Check 5 vendors          │
// │                           | simultaneously            │
// │  Alternative generation   | 3 agents build different  │
// │                           | itineraries               │
// │  Multi-criteria scoring   | Score cost, preference,   │
// │                           | pace in parallel           │
// │  Validation ensemble      | 3 validators check the    │
// │                           | same packet                │
// │  Multi-destination plan   | Plan each destination     │
// │                           | independently              │
// └─────────────────────────────────────────────────────┘

interface ParallelAgentGroup {
  id: string;
  pattern: ParallelPattern;
  agents: ParallelAgentTask[];
  aggregation: AggregationStrategy;
  timeout_seconds: number;
  min_results: number;                 // how many must succeed
}

type ParallelPattern =
  | "FAN_OUT"              // same task, different targets
  | "ENSEMBLE"             // same task, different approaches
  | "PARTITION"            // divide work, each agent handles a part
  | "COMPETITION"          // agents compete, best result wins
  | "REDUNDANCY";          // duplicate for reliability

interface ParallelAgentTask {
  agent_id: string;
  agent_role: AgentRole;
  input: Record<string, unknown>;
  weight: number;                      // for weighted aggregation
}

type AggregationStrategy =
  | "FIRST_SUCCESS"       // use first successful result
  | "MAJORITY_VOTE"       // most common result wins
  | "WEIGHTED_AVERAGE"    // combine with weights
  | "BEST_SCORE"          // highest scored result
  | "MERGE_ALL"           // combine all results
  | "CONSENSUS"           // agents must agree
  | "RANKED";             // rank and pick top N
```

### Fan-Out Pattern: Multi-Vendor Availability

```typescript
// ── Fan-out: Check availability across all vendors ──
// ┌─────────────────────────────────────────────────────┐
// │  ORCHESTRATOR                                         │
// │    │                                                  │
// │    ├──→ Agent A: Check Hotel Taj (availability)      │
// │    ├──→ Agent B: Check Hotel Marriott (availability) │
// │    ├──→ Agent C: Check Hotel ITC (availability)      │
// │    ├──→ Agent D: Check Hotel Oberoi (availability)   │
// │    └──→ Agent E: Check Hotel Leela (availability)    │
// │       │                                              │
// │       ▼ (all return within 10 seconds)               │
// │    AGGREGATOR                                         │
// │    ├── Taj: Available, ₹8,500/night                  │
// │    ├── Marriott: Available, ₹9,200/night             │
// │    ├── ITC: Sold out                                 │
// │    ├── Oberoi: Available, ₹12,000/night              │
// │    └── Leela: Available, ₹7,800/night                │
// │       │                                              │
// │       ▼                                              │
// │    Result: 4 available options, ranked by value      │
// └─────────────────────────────────────────────────────┘

interface FanOutResult<T> {
  group_id: string;
  results: {
    agent_id: string;
    status: "SUCCESS" | "ERROR" | "TIMEOUT";
    result: T | null;
    execution_time_ms: number;
  }[];
  aggregated: T[];
  successful_count: number;
  failed_count: number;
}
```

### Ensemble Pattern: Itinerary Generation

```typescript
// ── Ensemble: 3 agents build itineraries, best wins ──
// ┌─────────────────────────────────────────────────────┐
// │  PLANNING ORCHESTRATOR                                │
// │    │                                                  │
// │    ├──→ Agent A: "Budget Optimizer" focus            │
// │    │     Build cheapest Kerala itinerary              │
// │    │     Result: ₹38K, 4★ hotels, packed schedule   │
// │    │                                                  │
// │    ├──→ Agent B: "Experience Optimizer" focus        │
// │    │     Build best experience Kerala itinerary      │
// │    │     Result: ₹52K, 5★ hotels, relaxed schedule  │
// │    │                                                  │
// │    └──→ Agent C: "Balanced Optimizer" focus          │
// │          Build balanced Kerala itinerary              │
// │          Result: ₹44K, 4★ hotels, moderate pace      │
// │       │                                              │
// │       ▼                                              │
// │    SCORER AGENT                                       │
// │    Score each against customer preferences:           │
// │    A: 72/100 (budget great, pace too packed)         │
// │    B: 68/100 (experience great, over budget)         │
// │    C: 89/100 (balanced, within budget) ★             │
// │       │                                              │
// │       ▼                                              │
// │    Selected: Agent C's itinerary                     │
// │    Runner-up: Agent A (if customer prefers budget)   │
// └─────────────────────────────────────────────────────┘

interface EnsembleResult {
  candidates: {
    agent_id: string;
    strategy: string;
    itinerary: ProposedItinerary;
    score: number;
    cost: Money;
    strengths: string[];
    weaknesses: string[];
  }[];
  winner: string;
  reasoning: string;
  alternatives_offered: number;
}
```

### Consensus Mechanism

```typescript
interface ConsensusEngine {
  reachConsensus(results: AgentResult[]): ConsensusOutcome;
}

interface AgentResult {
  agent_id: string;
  agent_role: string;
  result: unknown;
  confidence: number;
  reasoning: string;
}

interface ConsensusOutcome {
  consensus_reached: boolean;
  agreed_result: unknown;
  agreement_percentage: number;
  dissenting_agents: {
    agent_id: string;
    alternative: unknown;
    reason: string;
  }[];
  resolution_strategy: "MAJORITY" | "WEIGHTED_CONFIDENCE" | "EXPERT_OVERRIDE";
}

// ── Consensus example: Validating extracted data ──
// ┌─────────────────────────────────────────────────────┐
// │  3 Extraction Agents validate same inquiry           │
// │                                                       │
// │  Agent A: destination = "Singapore" (confidence: 0.9)│
// │  Agent B: destination = "Singapore" (confidence: 0.85)│
// │  Agent C: destination = "Malaysia" (confidence: 0.6) │
// │                                                       │
// │  Consensus:                                           │
// │  - Singapore: 2/3 agents (weighted: 0.9+0.85=1.75)  │
// │  - Malaysia: 1/3 agents (weighted: 0.6)              │
// │  - Agreement: 75% → CONSENSUS REACHED               │
// │  - Result: Singapore                                  │
// │  - Note: Agent C's Malaysia flag → human review?     │
// └─────────────────────────────────────────────────────┘
```

### Conflict Resolution & Race Conditions

```typescript
interface ConflictResolver {
  resolveWriteConflict(conflicts: WriteConflict[]): ConflictResolution;
  acquireLock(resource: string, agent: string): LockResult;
}

interface WriteConflict {
  resource_id: string;                 // e.g., booking_id
  conflicting_agents: string[];
  operation: "UPDATE" | "DELETE" | "BOOK";
  resolution_strategy: "LAST_WRITER_WINS" | "FIRST_WRITER_WINS"
    | "MERGE" | "ESCALATE_TO_HUMAN";
}

// ── Preventing race conditions ──
// ┌─────────────────────────────────────────────────────┐
// │  Problem: Two agents try to book same hotel room     │
// │                                                       │
// │  Solution: Distributed locking                       │
// │                                                       │
// │  Agent A: acquire_lock("hotel_X_room_101")           │
// │    → Lock acquired ✅                                 │
// │    → Book room                                        │
// │    → Release lock                                     │
// │                                                       │
// │  Agent B: acquire_lock("hotel_X_room_101")           │
// │    → Lock held by A ❌                                │
// │    → Wait or try different room                       │
// │                                                       │
// │  Lock types:                                         │
// │  - Optimistic: check version before write            │
// │  - Pessimistic: acquire before any work              │
// │  - Advisory: soft lock, warn but don't block         │
// └─────────────────────────────────────────────────────┘
```

### Parallel Execution Metrics

```typescript
interface ParallelMetrics {
  group_id: string;
  total_agents: number;
  successful_agents: number;
  failed_agents: number;
  timed_out_agents: number;

  wall_clock_time_ms: number;          // total time
  total_agent_time_ms: number;         // sum of individual times
  parallelism_speedup: number;         // total_agent_time / wall_clock

  cost: {
    total_tokens: number;
    total_api_calls: number;
    total_cost: Money;
  };
}

// ── Performance comparison ──
// ┌─────────────────────────────────────────────────────┐
// │  5-vendor availability check                         │
// │                                                       │
// │  Sequential: 5 × 2s = 10 seconds                     │
// │  Parallel:   max(2s) = 2 seconds                     │
// │  Speedup:    5x                                       │
// │                                                       │
// │  Cost: 5× API calls (same either way)                │
// │  Benefit: 8 seconds faster for customer              │
// └─────────────────────────────────────────────────────┘
```

---

## Open Problems

1. **Cost amplification** — Running 5 agents instead of 1 multiplies API costs. Need cost-benefit analysis: is 5x cost worth 5x speed?

2. **Result quality variance** — Parallel agents may produce wildly different quality. Aggregation must handle outliers and low-quality results gracefully.

3. **Shared state corruption** — Agents reading shared state during parallel execution may see inconsistent data. Need snapshot isolation or versioned reads.

4. **Cascade failures** — If the orchestrator fails during parallel execution, orphaned agents may continue consuming resources. Need heartbeat and cancellation mechanisms.

---

## Next Steps

- [ ] Implement fan-out executor with configurable timeout and min-results
- [ ] Build ensemble pattern with multi-strategy scoring
- [ ] Create consensus engine with confidence-weighted voting
- [ ] Design distributed locking for write conflict prevention
- [ ] Build parallel execution metrics and cost tracking
