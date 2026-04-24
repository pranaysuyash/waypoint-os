# Intake System — Triage Strategies Deep Dive

> Part 5 of 6 in the Intake / Packet Processing Deep Dive Series

**Series Index:**
1. [Technical Deep Dive](INTAKE_01_TECHNICAL_DEEP_DIVE.md) — Architecture & Extraction Pipeline
2. [UX/UI Deep Dive](INTAKE_02_UX_UI_DEEP_DIVE.md) — Packet Panel & Extraction Experience
3. [Channel Integration Deep Dive](INTAKE_03_CHANNEL_INTEGRATION_DEEP_DIVE.md) — Multi-Channel Processing
4. [Extraction Quality Deep Dive](INTAKE_04_EXTRACTION_QUALITY_DEEP_DIVE.md) — Quality Framework & Monitoring
5. **Triage Strategies Deep Dive** (this document) — Routing, Prioritization & Assignment
6. [Analytics Deep Dive](INTAKE_06_ANALYTICS_DEEP_DIVE.md) — Metrics & Insights

---

## Document Overview

**Purpose:** Comprehensive exploration of how inquiries are triaged — routed to the right queue, prioritized for attention, and assigned to the most suitable agent.

**Scope:**
- Triage architecture and decision framework
- Routing strategies (manual, rule-based, ML-driven)
- Prioritization models (urgency, complexity, value)
- Agent assignment algorithms
- Auto-assignment vs. manual assignment
- Specialized routing scenarios
- Triage performance metrics

**Target Audience:** Product managers, engineers, designers, and stakeholders involved in building or configuring the triage system.

**Last Updated:** 2026-04-24

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Triage Architecture](#triage-architecture)
3. [Routing Strategies](#routing-strategies)
4. [Prioritization Models](#prioritization-models)
5. [Agent Assignment](#agent-assignment)
6. [Specialized Routing Scenarios](#specialized-routing-scenarios)
7. [Auto-Assignment Configuration](#auto-assignment-configuration)
8. [Triage Performance Metrics](#triage-performance-metrics)
9. [Implementation Roadmap](#implementation-roadmap)
10. [Future Evolution](#future-evolution)

---

## 1. Executive Summary

### The Triage Problem

Every inquiry entering the system faces three fundamental questions:

1. **Where does it go?** — Which queue, team, or agent should handle it?
2. **When should it be handled?** — What's its priority relative to other work?
3. **Who should handle it?** — Which specific agent is best suited?

The triage system answers these questions through a combination of:
- **Explicit routing rules** configured by agency owners
- **ML-based predictions** of urgency, complexity, and value
- **Agent specialization matching** based on skills and workload
- **Real-time operational constraints** (availability, capacity, SLAs)

### Key Design Principles

| Principle | Description |
|-----------|-------------|
| **Predictable routing** | Agents and customers should understand why packets go where they go |
| **Balanced workload** | Distribute work fairly while respecting specialization |
| **Fast path for simple cases** | Low-complexity inquiries should route automatically |
| **Expert escalation** | Complex or high-value cases reach qualified agents |
| **Agency control** | Owners configure routing rules to match their operations |
| **Learning optimization** | System learns from outcomes to improve routing decisions |

### Business Impact

| Metric | Impact |
|--------|--------|
| **Response time** | Proper prioritization reduces average first response by 40-60% |
| **Conversion rate** | Expert assignment increases conversion on complex trips by 25-35% |
| **Agent efficiency** | Specialized routing increases agent productivity by 30-50% |
| **Customer satisfaction** | Appropriate urgency handling improves CSAT by 20-30% |

---

## 2. Triage Architecture

### 2.1 System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           TRIAGE SYSTEM ARCHITECTURE                        │
└─────────────────────────────────────────────────────────────────────────────┘

                              ┌─────────────────┐
                              │  New Inquiry    │
                              │  (Any Channel)  │
                              └────────┬────────┘
                                       │
                                       ▼
                    ┌──────────────────────────────────────┐
                    │       EXTRACTION & ENRICHMENT        │
                    │  • Extract structured data           │
                    │  • Calculate confidence scores       │
                    │  • Detect special signals            │
                    │  • Gather context (history, etc.)    │
                    └──────────────────┬───────────────────┘
                                       │
                                       ▼
                    ┌──────────────────────────────────────┐
                    │          TRIAGE DECISION ENGINE       │
                    │                                      │
                    │  ┌────────────────────────────────┐  │
                    │  │   SIGNAL COMPUTATION           │  │
                    │  │   • Urgency score              │  │
                    │  │   • Complexity score           │  │
                    │  │   • Value score                │  │
                    │  │   • Special flags              │  │
                    │  └────────────┬───────────────────┘  │
                    │               │                       │
                    │  ┌────────────▼───────────────────┐  │
                    │  │   ROUTING RULE EVALUATION      │  │
                    │  │   • Agency-defined rules       │  │
                    │  │   • Conditional routing        │  │
                    │  │   • Queue assignments          │  │
                    │  └────────────┬───────────────────┘  │
                    │               │                       │
                    │  ┌────────────▼───────────────────┐  │
                    │  │   ASSIGNMENT ALGORITHM         │  │
                    │  │   • Skill matching             │  │
                    │  │   • Workload balancing         │  │
                    │  │   • Availability checking      │  │
                    │  └────────────┬───────────────────┘  │
                    └───────────────┼───────────────────────┘
                                    │
            ┌───────────────────────┼───────────────────────┐
            │                       │                       │
            ▼                       ▼                       ▼
    ┌───────────────┐     ┌───────────────┐     ┌───────────────┐
    │  AUTO-ROUTE   │     │  MANUAL QUEUE │     │ SPECIAL FLOW  │
    │  (Assigned)   │     │  (Unassigned) │     │  (Escalation) │
    └───────┬───────┘     └───────┬───────┘     └───────┬───────┘
            │                     │                     │
            ▼                     ▼                     ▼
    ┌───────────────┐     ┌───────────────┐     ┌───────────────┐
    │  AGENT WORK   │     │  INBOX SORT   │     │  EXPERT/OWNER │
    │  QUEUE        │     │  (Manual)     │     │  NOTIFICATION │
    └───────────────┘     └───────────────┘     └───────────────┘
```

### 2.2 Triage Decision Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         TRIAGE DECISION FLOW                                │
└─────────────────────────────────────────────────────────────────────────────┘

  ┌────────────────┐
  │ Packet Created │
  └───────┬────────┘
          │
          ▼
  ┌─────────────────────────────────────────────────────────────┐
  │ STEP 1: CHECK EXPLICIT ROUTING RULES                         │
  │                                                               │
  │ • Destination-specific rules (e.g., "Europe → Expert Team")  │
  │ • Value-based rules (e.g., "Budget > ₹5L → Senior Agent")    │
  │ • Channel-based rules (e.g., "Phone → Owner Queue")          │
  │ • Customer-based rules (e.g., "VIP → Priority Queue")        │
  └───────┬─────────────────────────────────────────────────────┘
          │
          ├─── Match Found? ──Yes──► Direct Route
          │
          ▼ No
  ┌─────────────────────────────────────────────────────────────┐
  │ STEP 2: CALCULATE TRIAGE SCORES                              │
  │                                                               │
  │ • Urgency: Time sensitivity (departure date, response delay) │
  │ • Complexity: Trip structure, special requests, custom work  │
  │ • Value: Revenue potential, budget size, customer lifetime   │
  └───────┬─────────────────────────────────────────────────────┘
          │
          ▼
  ┌─────────────────────────────────────────────────────────────┐
  │ STEP 3: DETERMINE ROUTING STRATEGY                           │
  │                                                               │
  │ ┌─────────────────┬─────────────────┬─────────────────┐     │
  │ │   LOW Urgency   │  MEDIUM Urgency │   HIGH Urgency  │     │
  │ │   LOW Complexity│  Any Complexity │  Any Complexity │     │
  │ │   LOW Value     │   Any Value     │   Any Value     │     │
  │ ├─────────────────┼─────────────────┼─────────────────┤     │
  │ │  Auto-Route to  │  Route to       │  Route to       │     │
  │ │  General Pool   │  Specialized    │  Priority Queue │     │
  │ └─────────────────┴─────────────────┴─────────────────┘     │
  └───────┬─────────────────────────────────────────────────────┘
          │
          ▼
  ┌─────────────────────────────────────────────────────────────┐
  │ STEP 4: AGENT ASSIGNMENT (if auto-routing enabled)          │
  │                                                               │
  │ • Filter: Agents in target queue/team                        │
  │ • Filter: Agents with required skills                        │
  │ • Filter: Agents under capacity threshold                    │
  │ • Score: Workload balance + skill match + past performance   │
  │ • Assign: Top-scoring available agent                        │
  └───────┬─────────────────────────────────────────────────────┘
          │
          ▼
  ┌─────────────────────────────────────────────────────────────┐
  │ STEP 5: POST-ASSIGNMENT ACTIONS                              │
  │                                                               │
  │ • Send notification to assigned agent                        │
  │ • Add to agent's work queue                                  │
  │ • Update packet metadata (assigned_at, assigned_to)          │
  │ • Log routing decision for analytics                         │
  │ • Trigger escalation timer if high-priority                  │
  └───────┬─────────────────────────────────────────────────────┘
          │
          ▼
  ┌────────────────┐
  │  Packet Active │
  └────────────────┘
```

### 2.3 Core Components

```typescript
/**
 * Triage System Core Types
 */

// Tri-dimensional scoring
interface TriageScores {
  urgency: TriageScore;        // 0-100: Time sensitivity
  complexity: TriageScore;     // 0-100: Difficulty level
  value: TriageScore;          // 0-100: Revenue potential

  // Computed priority
  priority: PriorityLevel;     // LOW | MEDIUM | HIGH | CRITICAL
}

interface TriageScore {
  value: number;               // 0-100
  confidence: number;          // 0-1
  factors: ScoreFactor[];      // Contributing factors
}

interface ScoreFactor {
  name: string;
  weight: number;
  value: number;
  reason: string;
}

// Routing decision
interface RoutingDecision {
  strategy: RoutingStrategy;
  targetQueue?: string;
  targetAgent?: string;
  priority: PriorityLevel;
  estimatedWait?: number;      // minutes
  reason: RoutingReason;
}

type RoutingStrategy =
  | "auto_assign"              // Automatically assign to best agent
  | "queue_pool"               // Route to queue pool, no assignment
  | "manual_review"            // Requires manual triage
  | "expert_escalation"        // Route to expert/senior
  | "owner_direct"             // Route directly to owner
  | "specialized_team"         // Route to specialized team

type PriorityLevel = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

// Routing rule
interface RoutingRule {
  id: string;
  name: string;
  enabled: boolean;
  priority: number;            // Higher = evaluated first

  conditions: RoutingCondition[];
  action: RoutingAction;
  metadata: {
    createdAt: Date;
    createdBy: string;
    lastModified: Date;
    effectiveness?: number;    // Tracked over time
  };
}

interface RoutingCondition {
  field: string;               // e.g., "destination.country"
  operator: ConditionOperator;
  value: any;
}

type ConditionOperator =
  | "equals" | "not_equals"
  | "contains" | "not_contains"
  | "greater_than" | "less_than"
  | "in" | "not_in"
  | "matches_regex";

interface RoutingAction {
  type: RoutingStrategy;
  queue?: string;
  agent?: string;
  priority?: PriorityLevel;
  notify?: boolean;
}

// Agent profile for assignment
interface AgentProfile {
  id: string;
  name: string;

  // Capacity
  capacity: {
    maxConcurrent: number;
    currentLoad: number;
    utilization: number;       // 0-1
  };

  // Skills
  skills: AgentSkill[];
  specializations: string[];   // Destinations, trip types

  // Performance
  performance: {
    avgResponseTime: number;   // minutes
    conversionRate: number;    // 0-1
    customerRating: number;    // 0-5
    packetsHandled: number;
  };

  // Availability
  availability: {
    status: "online" | "away" | "offline" | "busy";
    workingHours?: TimeWindow;
    nextAvailable?: Date;
  };
}

interface AgentSkill {
  category: string;            // "destination", "trip_type", etc.
  value: string;               // "europe", "honeymoon", etc.
  level: number;               // 0-100
  verified: boolean;           // Certified/tested?
}
```

---

## 3. Routing Strategies

### 3.1 Strategy Spectrum

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ROUTING STRATEGY SPECTRUM                           │
└─────────────────────────────────────────────────────────────────────────────┘

  FULLY AUTOMATIC                                   FULLY MANUAL
  ┌──────────────────────┐                         ┌──────────────────────┐
  │                      │                         │                      │
  │  • ML-based scoring  │                         │  • Owner reviews all │
  │  • Auto-assignment   │                         │  • Manual routing    │
  │  • No human touch    │                         │  • Full control      │
  │                      │                         │                      │
  │  Best for:           │                         │  Best for:           │
  │  • High volume       │                         │  • Low volume        │
  │  • Simple cases      │                         │  • Complex cases     │
  │  • Standard trips    │                         │  • Premium service   │
  │                      │                         │                      │
  └──────────────────────┘                         └──────────────────────┘
          │                                                    │
          │                                                    │
          └────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────────┐
                    │                      │
                    │  HYBRID APPROACH     │
                    │  (Recommended)       │
                    │                      │
                    │  • Auto-route simple │
                    │  • Manual complex    │
                    │  • Configurable      │
                    │  • Learned rules     │
                    │                      │
                    └──────────────────────┘
```

### 3.2 Rule-Based Routing

Agency owners define explicit rules for routing decisions. Rules are evaluated in priority order.

```typescript
/**
 * Rule-Based Routing Engine
 */

class RoutingRuleEngine {
  private rules: RoutingRule[];

  constructor(rules: RoutingRule[]) {
    // Sort by priority (highest first)
    this.rules = rules.sort((a, b) => b.priority - a.priority);
  }

  /**
   * Evaluate routing rules against a packet
   * Returns first matching rule's action, or null if no match
   */
  evaluate(packet: TripPacket): RoutingDecision | null {
    for (const rule of this.rules) {
      if (!rule.enabled) continue;

      if (this.matchesRule(packet, rule)) {
        return this.buildDecision(rule, packet);
      }
    }

    return null; // No explicit rule matched
  }

  /**
   * Check if a packet matches a routing rule
   */
  private matchesRule(packet: TripPacket, rule: RoutingRule): boolean {
    // ALL conditions must match (AND logic)
    return rule.conditions.every(condition =>
      this.matchesCondition(packet, condition)
    );
  }

  /**
   * Check if a single condition matches
   */
  private matchesCondition(
    packet: TripPacket,
    condition: RoutingCondition
  ): boolean {
    const fieldValue = this.getFieldValue(packet, condition.field);

    switch (condition.operator) {
      case "equals":
        return fieldValue === condition.value;

      case "not_equals":
        return fieldValue !== condition.value;

      case "contains":
        return typeof fieldValue === "string" &&
          fieldValue.includes(condition.value);

      case "greater_than":
        return typeof fieldValue === "number" &&
          fieldValue > condition.value;

      case "less_than":
        return typeof fieldValue === "number" &&
          fieldValue < condition.value;

      case "in":
        return Array.isArray(condition.value) &&
          condition.value.includes(fieldValue);

      case "not_in":
        return Array.isArray(condition.value) &&
          !condition.value.includes(fieldValue);

      case "matches_regex":
        return typeof fieldValue === "string" &&
          new RegExp(condition.value).test(fieldValue);

      default:
        return false;
    }
  }

  /**
   * Extract nested field value from packet
   */
  private getFieldValue(packet: TripPacket, field: string): any {
    const parts = field.split(".");
    let value: any = packet;

    for (const part of parts) {
      if (value == null) return null;
      value = value[part];
    }

    return value;
  }

  /**
   * Build routing decision from matching rule
   */
  private buildDecision(rule: RoutingRule, packet: TripPacket): RoutingDecision {
    return {
      strategy: rule.action.type,
      targetQueue: rule.action.queue,
      targetAgent: rule.action.agent,
      priority: rule.action.priority || this.calculatePriority(packet),
      reason: {
        type: "rule_match",
        ruleId: rule.id,
        ruleName: rule.name
      }
    };
  }

  /**
   * Calculate priority from triage scores
   */
  private calculatePriority(packet: TripPacket): PriorityLevel {
    const scores = packet.triageScores;
    if (!scores) return "MEDIUM";

    // Priority matrix: urgency is primary, complexity/value secondary
    if (scores.urgency.value > 75) return "CRITICAL";
    if (scores.urgency.value > 50) return "HIGH";
    if (scores.value.value > 75) return "HIGH";
    return "MEDIUM";
  }
}
```

### 3.3 Example Routing Rules

```typescript
/**
 * Common Routing Rule Examples
 */

const EXAMPLE_ROUTING_RULES: RoutingRule[] = [
  // VIP Customers → Owner Direct
  {
    id: "rule_vip_owner",
    name: "VIP Customers to Owner",
    enabled: true,
    priority: 1000,
    conditions: [
      { field: "customer.tier", operator: "equals", value: "VIP" }
    ],
    action: {
      type: "owner_direct",
      priority: "HIGH",
      notify: true
    },
    metadata: {
      createdAt: new Date("2026-01-01"),
      createdBy: "system"
    }
  },

  // High Value → Senior Agent Pool
  {
    id: "rule_high_value_senior",
    name: "High Value to Senior Agents",
    enabled: true,
    priority: 900,
    conditions: [
      { field: "budget.total", operator: "greater_than", value: 500000 }
    ],
    action: {
      type: "specialized_team",
      queue: "senior_agents",
      priority: "HIGH"
    },
    metadata: {
      createdAt: new Date("2026-01-01"),
      createdBy: "system"
    }
  },

  // Europe → Europe Specialist Team
  {
    id: "rule_europe_specialists",
    name: "Europe Trips to Specialists",
    enabled: true,
    priority: 800,
    conditions: [
      { field: "destination.continent", operator: "equals", value: "Europe" }
    ],
    action: {
      type: "specialized_team",
      queue: "europe_specialists"
    },
    metadata: {
      createdAt: new Date("2026-01-01"),
      createdBy: "system"
    }
  },

  // Urgent → Priority Queue
  {
    id: "rule_urgent_priority",
    name: "Urgent to Priority Queue",
    enabled: true,
    priority: 700,
    conditions: [
      { field: "dates.departure", operator: "less_than", value: "<7_days" }
    ],
    action: {
      type: "queue_pool",
      queue: "priority",
      priority: "HIGH"
    },
    metadata: {
      createdAt: new Date("2026-01-01"),
      createdBy: "system"
    }
  },

  // Honeymoon → Romance Specialists
  {
    id: "rule_honeymoon_romance",
    name: "Honeymoons to Romance Team",
    enabled: true,
    priority: 600,
    conditions: [
      { field: "tripType", operator: "equals", value: "honeymoon" }
    ],
    action: {
      type: "specialized_team",
      queue: "romance_specialists"
    },
    metadata: {
      createdAt: new Date("2026-01-01"),
      createdBy: "system"
    }
  },

  // Low Complexity → Auto-Assign
  {
    id: "rule_simple_auto",
    name: "Simple Trips Auto-Assign",
    enabled: true,
    priority: 500,
    conditions: [
      { field: "triageScores.complexity.value", operator: "less_than", value: 30 },
      { field: "budget.total", operator: "less_than", value: 100000 }
    ],
    action: {
      type: "auto_assign",
      queue: "general_pool"
    },
    metadata: {
      createdAt: new Date("2026-01-01"),
      createdBy: "system"
    }
  },

  // Default → Manual Review
  {
    id: "rule_default_manual",
    name: "Default Manual Review",
    enabled: true,
    priority: 0,
    conditions: [], // Always matches
    action: {
      type: "manual_review",
      queue: "unassigned"
    },
    metadata: {
      createdAt: new Date("2026-01-01"),
      createdBy: "system"
    }
  }
];
```

### 3.4 ML-Based Routing Recommendation

For agencies without explicit rules, or as a suggestion system:

```typescript
/**
 * ML-Based Routing Recommendation Engine
 */

class RoutingRecommendationEngine {
  private model: RoutingModel;

  /**
   * Get routing recommendation for a packet
   */
  async recommend(packet: TripPacket): Promise<RoutingRecommendation> {
    const features = this.extractFeatures(packet);
    const prediction = await this.model.predict(features);

    return {
      suggestedStrategy: prediction.strategy,
      suggestedQueue: prediction.queue,
      suggestedAgent: prediction.agent,
      confidence: prediction.confidence,
      reasoning: prediction.reasoning,
      alternatives: prediction.alternatives
    };
  }

  /**
   * Extract features for routing prediction
   */
  private extractFeatures(packet: TripPacket): RoutingFeatures {
    return {
      // Trip characteristics
      destinationContinent: packet.destination?.continent,
      destinationCountry: packet.destination?.country,
      tripType: packet.tripType,
      duration: packet.duration,

      // Value indicators
      budgetLevel: this.categorizeBudget(packet.budget?.total),
      estimatedValue: packet.estimatedValue,

      // Complexity
      complexity: packet.triageScores?.complexity.value || 50,
      passengerCount: packet.passengers?.length || 0,
      specialRequests: packet.specialRequests?.length || 0,

      // Urgency
      urgency: packet.triageScores?.urgency.value || 50,
      daysToDeparture: this.daysTo(packet.dates?.departure),

      // Customer
      customerTier: packet.customer?.tier,
      isReturning: packet.customer?.isReturning,
      pastTrips: packet.customer?.pastTrips || 0,

      // Channel
      channel: packet.sourceChannel,
      responseTime: packet.responseTimeMs
    };
  }

  private categorizeBudget(budget?: number): "low" | "medium" | "high" | "luxury" {
    if (!budget) return "medium";
    if (budget < 50000) return "low";
    if (budget < 200000) return "medium";
    if (budget < 500000) return "high";
    return "luxury";
  }

  private daysTo(date?: Date): number {
    if (!date) return 999;
    return Math.floor((date.getTime() - Date.now()) / (1000 * 60 * 60 * 24));
  }
}

interface RoutingFeatures {
  destinationContinent?: string;
  destinationCountry?: string;
  tripType?: string;
  duration?: number;
  budgetLevel: string;
  estimatedValue?: number;
  complexity: number;
  passengerCount: number;
  specialRequests: number;
  urgency: number;
  daysToDeparture: number;
  customerTier?: string;
  isReturning?: boolean;
  pastTrips: number;
  channel?: string;
  responseTime?: number;
}

interface RoutingRecommendation {
  suggestedStrategy: RoutingStrategy;
  suggestedQueue?: string;
  suggestedAgent?: string;
  confidence: number;              // 0-1
  reasoning: string[];
  alternatives: AlternativeRoute[];
}

interface AlternativeRoute {
  strategy: RoutingStrategy;
  queue?: string;
  reason: string;
}
```

---

## 4. Prioritization Models

### 4.1 Tri-Dimensional Priority Framework

Priority is calculated across three dimensions, then combined into a single priority level.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         TRI-DIMENSIONAL PRIORITY                             │
└─────────────────────────────────────────────────────────────────────────────┘

                    ┌─────────────────────────────┐
                    │      PRIORITY CALCULATION    │
                    └──────────────┬──────────────┘
                                   │
        ┌──────────────────────────┼──────────────────────────┐
        │                          │                          │
        ▼                          ▼                          ▼
┌───────────────┐          ┌───────────────┐          ┌───────────────┐
│    URGENCY    │          │  COMPLEXITY   │          │     VALUE     │
│               │          │               │          │               │
│ Time-sensitive│          │ Skill-demand  │          │ Revenue       │
│ Departure     │          │ Custom work   │          │ Budget        │
│ Response delay│          │ Multi-dest    │          │ Customer LTV  │
│ Seasonality   │          │ Special req   │          │ Growth        │
└───────┬───────┘          └───────┬───────┘          └───────┬───────┘
        │                          │                          │
        │ 0-100 score              │ 0-100 score              │ 0-100 score
        │                          │                          │
        └──────────────────────────┼──────────────────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────┐
                    │    PRIORITY MATRIX          │
                    │                             │
                    │  Urgency + Value + Complex  │
                    │          ↓                  │
                    │  CRITICAL | HIGH | MED | LOW│
                    └──────────────┬──────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────┐
                    │   QUEUE ORDERING            │
                    │                             │
                    │  1. CRITICAL (Immediate)    │
                    │  2. HIGH (Same day)         │
                    │  3. MEDIUM (48 hours)       │
                    │  4. LOW (When available)    │
                    └─────────────────────────────┘
```

### 4.2 Urgency Scoring

```typescript
/**
 * Urgency Score Calculation
 */

class UrgencyScorer {
  /**
   * Calculate urgency score (0-100)
   */
  calculate(packet: TripPacket): TriageScore {
    const factors: ScoreFactor[] = [];

    // Factor 1: Days to departure (weight: 40%)
    const departureScore = this.scoreDeparture(packet.dates?.departure);
    factors.push({
      name: "departure_proximity",
      weight: 0.4,
      value: departureScore,
      reason: this.describeDepartureScore(departureScore)
    });

    // Factor 2: Customer wait time (weight: 25%)
    const waitScore = this.scoreWaitTime(packet.createdAt);
    factors.push({
      name: "customer_wait_time",
      weight: 0.25,
      value: waitScore,
      reason: this.describeWaitScore(waitScore)
    });

    // Factor 3: Seasonality (weight: 20%)
    const seasonScore = this.scoreSeasonality(packet.dates?.departure);
    factors.push({
      name: "seasonality",
      weight: 0.2,
      value: seasonScore,
      reason: this.describeSeasonScore(seasonScore)
    });

    // Factor 4: Travel reason urgency (weight: 15%)
    const reasonScore = this.scoreTravelReason(packet.tripType, packet.travelReason);
    factors.push({
      name: "travel_reason",
      weight: 0.15,
      value: reasonScore,
      reason: this.describeReasonScore(reasonScore)
    });

    // Calculate weighted sum
    const value = factors.reduce((sum, f) => sum + (f.value * f.weight), 0);

    return {
      value: Math.round(value),
      confidence: this.calculateConfidence(factors),
      factors
    };
  }

  /**
   * Score based on departure proximity
   */
  private scoreDeparture(departure?: Date): number {
    if (!departure) return 30; // Default medium urgency

    const daysTo = this.daysTo(departure);

    if (daysTo < 0) return 100;        // Past departure (CRITICAL)
    if (daysTo <= 3) return 100;       // Within 3 days (CRITICAL)
    if (daysTo <= 7) return 85;        // Within a week (HIGH)
    if (daysTo <= 14) return 70;       // Within two weeks (MED-HIGH)
    if (daysTo <= 30) return 50;       // Within a month (MEDIUM)
    if (daysTo <= 60) return 35;       // Within two months (LOW-MED)
    if (daysTo <= 90) return 20;       // Within three months (LOW)
    return 10;                         // 3+ months out (VERY LOW)
  }

  /**
   * Score based on customer wait time
   */
  private scoreWaitTime(createdAt: Date): number {
    const hoursWaited = (Date.now() - createdAt.getTime()) / (1000 * 60 * 60);

    if (hoursWaited < 1) return 20;    // Under 1 hour
    if (hoursWaited < 4) return 35;    // 1-4 hours
    if (hoursWaited < 12) return 50;   // 4-12 hours
    if (hoursWaited < 24) return 70;   // 12-24 hours
    if (hoursWaited < 48) return 85;   // 1-2 days
    return 100;                        // 2+ days (very urgent)
  }

  /**
   * Score based on seasonality
   */
  private scoreSeasonality(departure?: Date): number {
    if (!departure) return 30;

    const month = departure.getMonth(); // 0-11

    // Peak season months (India travel context)
    const peakMonths = [3, 4, 10, 11, 12]; // Apr-May, Oct-Dec
    const highMonths = [0, 1, 5, 6];      // Jan-Feb, Jun-Jul
    const lowMonths = [7, 8, 9];          // Aug-Sep

    if (peakMonths.includes(month)) return 80;
    if (highMonths.includes(month)) return 60;
    if (lowMonths.includes(month)) return 30;
    return 50; // Shoulder season
  }

  /**
   * Score based on travel reason
   */
  private scoreTravelReason(tripType?: string, reason?: string): number {
    // Some trip types are inherently more urgent
    if (reason === "medical") return 100;
    if (reason === "business") return 80;
    if (reason === "emergency") return 100;
    if (tripType === "honeymoon") return 60; // Time-sensitive milestone
    if (tripType === "last_minute") return 90;
    return 50; // Normal leisure travel
  }

  private daysTo(date: Date): number {
    return Math.floor((date.getTime() - Date.now()) / (1000 * 60 * 60 * 24));
  }

  private calculateConfidence(factors: ScoreFactor[]): number {
    // Higher confidence if we have more data points
    let confidence = 0.5;
    if (factors.some(f => f.name === "departure_proximity")) confidence += 0.3;
    if (factors.some(f => f.name === "customer_wait_time")) confidence += 0.2;
    return Math.min(confidence, 1.0);
  }

  private describeDepartureScore(score: number): string {
    if (score >= 85) return "Departure within 7 days";
    if (score >= 50) return "Departure within 30 days";
    return "Departure more than 30 days out";
  }

  private describeWaitScore(score: number): string {
    if (score >= 70) return `Customer waited ${this.getWaitDescription()}`;
    return "Recent inquiry";
  }

  private describeSeasonScore(score: number): string {
    if (score >= 70) return "Peak travel season";
    if (score >= 50) return "High travel season";
    return "Low/shoulder season";
  }

  private describeReasonScore(score: number): string {
    if (score >= 80) return "Urgent travel reason";
    return "Normal leisure travel";
  }

  private getWaitDescription(): string {
    // Simplified for example
    return "more than 12 hours";
  }
}
```

### 4.3 Complexity Scoring

```typescript
/**
 * Complexity Score Calculation
 */

class ComplexityScorer {
  /**
   * Calculate complexity score (0-100)
   */
  calculate(packet: TripPacket): TriageScore {
    const factors: ScoreFactor[] = [];

    // Factor 1: Destination complexity (weight: 25%)
    const destScore = this.scoreDestination(packet.destination);
    factors.push({
      name: "destination_complexity",
      weight: 0.25,
      value: destScore,
      reason: this.describeDestScore(destScore)
    });

    // Factor 2: Trip structure (weight: 30%)
    const structureScore = this.scoreStructure(packet);
    factors.push({
      name: "trip_structure",
      weight: 0.3,
      value: structureScore,
      reason: this.describeStructureScore(structureScore)
    });

    // Factor 3: Passenger count (weight: 15%)
    const paxScore = this.scorePax(packet.passengers?.length || 0);
    factors.push({
      name: "passenger_count",
      weight: 0.15,
      value: paxScore,
      reason: this.describePaxScore(paxScore)
    });

    // Factor 4: Special requests (weight: 20%)
    const specialScore = this.scoreSpecialRequests(packet.specialRequests);
    factors.push({
      name: "special_requests",
      weight: 0.2,
      value: specialScore,
      reason: this.describeSpecialScore(specialScore)
    });

    // Factor 5: Custom requirements (weight: 10%)
    const customScore = this.scoreCustomReqs(packet);
    factors.push({
      name: "custom_requirements",
      weight: 0.1,
      value: customScore,
      reason: this.describeCustomScore(customScore)
    });

    const value = factors.reduce((sum, f) => sum + (f.value * f.weight), 0);

    return {
      value: Math.round(value),
      confidence: this.calculateConfidence(factors),
      factors
    };
  }

  /**
   * Score destination complexity
   */
  private scoreDestination(destination?: Destination): number {
    if (!destination) return 30;

    let score = 20; // Base score

    // Visa complexity
    if (destination.visaRequired) score += 15;
    if (destination.visaComplexity === "high") score += 20;

    // Multi-destination
    if (destination.multipleCountries) score += 25;

    // Remote/exotic destinations
    const exoticRegions = ["Antarctica", "Arctic", "Sahara"];
    if (exoticRegions.some(r => destination.region?.includes(r))) {
      score += 30;
    }

    // Language barrier
    if (destination.languageBarrier) score += 10;

    return Math.min(score, 100);
  }

  /**
   * Score trip structure
   */
  private scoreStructure(packet: TripPacket): number {
    let score = 10;

    // Multi-city
    if (packet.destinations && packet.destinations.length > 1) {
      score += 20 * (packet.destinations.length - 1);
    }

    // Multi-modal transport
    const modes = new Set(
      packet.segments?.map(s => s.transportMode).filter(Boolean)
    );
    if (modes.size > 1) score += 15;

    // Complex connections
    if (packet.hasComplexConnections) score += 20;

    // Trip type complexity
    const complexTypes = ["group_tour", "corporate_retreat", "multi_family"];
    if (complexTypes.includes(packet.tripType || "")) {
      score += 25;
    }

    return Math.min(score, 100);
  }

  /**
   * Score passenger count
   */
  private scorePax(count: number): number {
    if (count <= 2) return 10;
    if (count <= 4) return 25;
    if (count <= 6) return 50;
    if (count <= 10) return 75;
    return 100; // 10+ is complex
  }

  /**
   * Score special requests
   */
  private scoreSpecialRequests(requests?: SpecialRequest[]): number {
    if (!requests || requests.length === 0) return 0;

    let score = 10 * requests.length; // Base per request

    // Certain requests add more complexity
    const complexKeywords = ["wheelchair", "medical", "dietary", "visa", "passport"];
    for (const req of requests) {
      if (complexKeywords.some(kw =>
        req.description?.toLowerCase().includes(kw)
      )) {
        score += 15;
      }
    }

    return Math.min(score, 100);
  }

  /**
   * Score custom requirements
   */
  private scoreCustomReqs(packet: TripPacket): number {
    let score = 0;

    if (packet.customItineraryRequired) score += 30;
    if (packet.negotiationRequired) score += 25;
    if (packet.budgetHandling === "tight") score += 20;
    if (packet.accommodationSpecific) score += 15;

    return Math.min(score, 100);
  }

  private calculateConfidence(factors: ScoreFactor[]): number {
    // We usually have good data for complexity
    return 0.8;
  }

  private describeDestScore(score: number): string {
    if (score >= 70) return "Complex destination (visa, multi-country)";
    if (score >= 40) return "Moderate destination";
    return "Standard destination";
  }

  private describeStructureScore(score: number): string {
    if (score >= 60) return "Complex trip structure";
    if (score >= 30) return "Multi-city or multi-modal";
    return "Simple point-to-point";
  }

  private describePaxScore(score: number): string {
    if (score >= 75) return "Large group (10+ travelers)";
    if (score >= 50) return "Medium group (4-10 travelers)";
    return "Small group (1-4 travelers)";
  }

  private describeSpecialScore(score: number): string {
    if (score >= 50) return "Multiple or complex special requests";
    if (score >= 20) return "Some special requests";
    return "No special requests";
  }

  private describeCustomScore(score: number): string {
    if (score >= 40) return "Custom itinerary or tight constraints";
    return "Standard requirements";
  }
}
```

### 4.4 Value Scoring

```typescript
/**
 * Value Score Calculation
 */

class ValueScorer {
  /**
   * Calculate value score (0-100)
   */
  calculate(packet: TripPacket): TriageScore {
    const factors: ScoreFactor[] = [];

    // Factor 1: Budget size (weight: 35%)
    const budgetScore = this.scoreBudget(packet.budget?.total);
    factors.push({
      name: "budget_size",
      weight: 0.35,
      value: budgetScore,
      reason: this.describeBudgetScore(budgetScore)
    });

    // Factor 2: Customer LTV (weight: 30%)
    const ltvScore = this.scoreCustomerLTV(packet.customer);
    factors.push({
      name: "customer_lifetime_value",
      weight: 0.3,
      value: ltvScore,
      reason: this.describeLTVScore(ltvScore)
    });

    // Factor 3: Repeat potential (weight: 20%)
    const repeatScore = this.scoreRepeatPotential(packet);
    factors.push({
      name: "repeat_potential",
      weight: 0.2,
      value: repeatScore,
      reason: this.describeRepeatScore(repeatScore)
    });

    // Factor 4: Referral potential (weight: 15%)
    const referralScore = this.scoreReferralPotential(packet);
    factors.push({
      name: "referral_potential",
      weight: 0.15,
      value: referralScore,
      reason: this.describeReferralScore(referralScore)
    });

    const value = factors.reduce((sum, f) => sum + (f.value * f.weight), 0);

    return {
      value: Math.round(value),
      confidence: this.calculateConfidence(factors),
      factors
    };
  }

  /**
   * Score budget size
   */
  private scoreBudget(budget?: number): number {
    if (!budget) return 30; // Unknown budget = medium value

    // INR-based thresholds
    if (budget >= 1000000) return 100;   // ₹10L+ (luxury)
    if (budget >= 500000) return 85;      // ₹5-10L (high)
    if (budget >= 200000) return 70;      // ₹2-5L (good)
    if (budget >= 100000) return 50;      // ₹1-2L (medium)
    if (budget >= 50000) return 35;       // ₹50K-1L (budget)
    return 20;                            // < ₹50K (low)
  }

  /**
   * Score customer lifetime value
   */
  private scoreCustomerLTV(customer?: Customer): number {
    if (!customer) return 40; // Unknown customer = default

    let score = 0;

    // Past trips
    score += Math.min(customer.pastTrips * 15, 40);

    // Total spend
    if (customer.totalSpend >= 500000) score += 30;
    else if (customer.totalSpend >= 200000) score += 20;
    else if (customer.totalSpend >= 50000) score += 10;

    // Tier
    if (customer.tier === "PLATINUM") score += 30;
    else if (customer.tier === "GOLD") score += 20;
    else if (customer.tier === "SILVER") score += 10;

    return Math.min(score, 100);
  }

  /**
   * Score repeat potential
   */
  private scoreRepeatPotential(packet: TripPacket): number {
    let score = 30; // Base score

    // Younger travelers travel more
    const avgAge = this.averageAge(packet.passengers);
    if (avgAge && avgAge < 40) score += 20;

    // Certain trip types indicate repeat travelers
    const repeatTypes = ["honeymoon", "anniversary", "family_vacation"];
    if (repeatTypes.includes(packet.tripType || "")) {
      score += 25;
    }

    // International travelers tend to repeat
    if (packet.destination?.international) {
      score += 15;
    }

    return Math.min(score, 100);
  }

  /**
   * Score referral potential
   */
  private scoreReferralPotential(packet: TripPacket): number {
    let score = 20; // Base score

    // Group trips have high referral potential
    const paxCount = packet.passengers?.length || 0;
    if (paxCount > 4) score += 30;

    // Honeymoon/wedding trips
    if (["honeymoon", "wedding"].includes(packet.tripType || "")) {
      score += 35;
    }

    // High-value trips generate referrals
    if (packet.budget?.total && packet.budget.total > 300000) {
      score += 20;
    }

    return Math.min(score, 100);
  }

  private averageAge(passengers?: Passenger[]): number | undefined {
    if (!passengers || passengers.length === 0) return undefined;
    const sum = passengers.reduce((s, p) => s + (p.age || 30), 0);
    return sum / passengers.length;
  }

  private calculateConfidence(factors: ScoreFactor[]): number {
    let confidence = 0.3; // Low base confidence

    // Higher confidence if we have customer data
    if (factors.some(f => f.name === "customer_lifetime_value" && f.value > 0)) {
      confidence += 0.4;
    }
    if (factors.some(f => f.name === "budget_size" && f.value > 0)) {
      confidence += 0.3;
    }

    return Math.min(confidence, 1.0);
  }

  private describeBudgetScore(score: number): string {
    if (score >= 85) return "High-value trip (₹5L+ budget)";
    if (score >= 50) return "Good-value trip (₹1L+ budget)";
    return "Standard budget trip";
  }

  private describeLTVScore(score: number): string {
    if (score >= 70) return "High-value customer (repeat, tiered)";
    if (score >= 40) return "Returning customer";
    return "New customer";
  }

  private describeRepeatScore(score: number): string {
    if (score >= 60) return "High repeat potential";
    return "Standard repeat potential";
  }

  private describeReferralScore(score: number): string {
    if (score >= 60) return "High referral potential";
    return "Standard referral potential";
  }
}
```

### 4.5 Priority Matrix

Combining all three scores into a final priority level:

```typescript
/**
 * Priority Calculation
 */

class PriorityCalculator {
  private urgencyScorer: UrgencyScorer;
  private complexityScorer: ComplexityScorer;
  private valueScorer: ValueScorer;

  constructor() {
    this.urgencyScorer = new UrgencyScorer();
    this.complexityScorer = new ComplexityScorer();
    this.valueScorer = new ValueScorer();
  }

  /**
   * Calculate triage scores and priority
   */
  calculate(packet: TripPacket): TriageScores {
    const urgency = this.urgencyScorer.calculate(packet);
    const complexity = this.complexityScorer.calculate(packet);
    const value = this.valueScorer.calculate(packet);

    const priority = this.determinePriority(urgency, complexity, value);

    return { urgency, complexity, value, priority };
  }

  /**
   * Determine priority level from scores
   */
  private determinePriority(
    urgency: TriageScore,
    complexity: TriageScore,
    value: TriageScore
  ): PriorityLevel {
    // CRITICAL: Very high urgency OR high urgency + high value
    if (urgency.value >= 85) return "CRITICAL";
    if (urgency.value >= 70 && value.value >= 70) return "CRITICAL";

    // HIGH: High urgency OR high value + moderate urgency
    if (urgency.value >= 60) return "HIGH";
    if (value.value >= 80 && urgency.value >= 40) return "HIGH";

    // MEDIUM: Moderate anything, or low urgency but high complexity
    if (urgency.value >= 40) return "MEDIUM";
    if (complexity.value >= 70) return "MEDIUM";
    if (value.value >= 60) return "MEDIUM";

    // LOW: Everything else
    return "LOW";
  }
}
```

---

## 5. Agent Assignment

### 5.1 Assignment Algorithm

When auto-assignment is enabled, the system selects the best agent using a multi-factor scoring algorithm.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         AGENT ASSIGNMENT ALGORITHM                          │
└─────────────────────────────────────────────────────────────────────────────┘

  ┌────────────────┐
  │ Packet Ready   │
  │ for Assignment │
  └────────┬───────┘
           │
           ▼
  ┌─────────────────────────────────────────────────────────────┐
  │ STEP 1: FILTER ELIGIBLE AGENTS                              │
  │                                                               │
  │ • In target queue/team                                      │
  │ • Has required skills                                        │
  │ • Currently online/available                                │
  │ • Under capacity threshold                                  │
  └──────────────────┬──────────────────────────────────────────┘
                     │
                     ▼
  ┌─────────────────────────────────────────────────────────────┐
  │ STEP 2: SCORE EACH ELIGIBLE AGENT                           │
  │                                                               │
  │  Score =                                                    │
  │    (Skill Match × 0.35) +                                   │
  │    (Workload Balance × 0.30) +                              │
  │    (Past Performance × 0.20) +                              │
  │    (Customer Relationship × 0.15)                           │
  └──────────────────┬──────────────────────────────────────────┘
                     │
                     ▼
  ┌─────────────────────────────────────────────────────────────┐
  │ STEP 3: SELECT TOP SCORING AGENT                            │
  │                                                               │
  │ • Agent with highest composite score                        │
  │ • If tie-breaker needed: lower workload wins               │
  └──────────────────┬──────────────────────────────────────────┘
                     │
                     ▼
  ┌─────────────────────────────────────────────────────────────┐
  │ STEP 4: ASSIGN AND NOTIFY                                   │
  │                                                               │
  │ • Update packet assignment                                  │
  │ • Send notification to agent                                │
  │ • Add to agent's work queue                                 │
  │ • Log assignment for analytics                              │
  └──────────────────┬──────────────────────────────────────────┘
                     │
                     ▼
  ┌────────────────┐
  │ Assignment     │
  │ Complete       │
  └────────────────┘
```

### 5.2 Assignment Implementation

```typescript
/**
 * Agent Assignment Engine
 */

class AgentAssignmentEngine {
  private agentRegistry: AgentRegistry;
  private skillMatcher: SkillMatcher;

  /**
   * Assign packet to best available agent
   */
  async assign(
    packet: TripPacket,
    targetQueue: string
  ): Promise<AssignmentResult> {
    // Step 1: Get eligible agents
    const eligible = await this.getEligibleAgents(packet, targetQueue);

    if (eligible.length === 0) {
      return {
        success: false,
        reason: "No eligible agents available",
        fallbackAction: "route_to_unassigned_queue"
      };
    }

    // Step 2: Score each agent
    const scored = await Promise.all(
      eligible.map(agent => this.scoreAgent(agent, packet))
    );

    // Step 3: Select best agent
    scored.sort((a, b) => b.totalScore - a.totalScore);
    const best = scored[0];

    // Step 4: Assign
    await this.executeAssignment(best.agent, packet);

    return {
      success: true,
      agentId: best.agent.id,
      agentName: best.agent.name,
      score: best.totalScore,
      reasoning: best.reasoning
    };
  }

  /**
   * Get eligible agents for a packet
   */
  private async getEligibleAgents(
    packet: TripPacket,
    queue: string
  ): Promise<AgentProfile[]> {
    const allAgents = await this.agentRegistry.getAgentsInQueue(queue);

    return allAgents.filter(agent =>
      this.isEligible(agent, packet)
    );
  }

  /**
   * Check if agent is eligible for assignment
   */
  private isEligible(agent: AgentProfile, packet: TripPacket): boolean {
    // Must be online
    if (agent.availability.status !== "online") return false;

    // Must be under capacity
    if (agent.capacity.utilization >= 0.9) return false;

    // Must have basic skills (if specialization required)
    if (packet.destination?.country) {
      const hasSkill = agent.skills.some(s =>
        s.category === "destination" &&
        s.value === packet.destination.country &&
        s.level >= 50
      );
      if (!hasSkill && this.requiresSpecialization(packet)) {
        return false;
      }
    }

    return true;
  }

  private requiresSpecialization(packet: TripPacket): boolean {
    // Require specialization for complex or high-value trips
    return (
      packet.triageScores?.complexity.value > 60 ||
      packet.budget?.total > 300000
    );
  }

  /**
   * Score an agent for a packet
   */
  private async scoreAgent(
    agent: AgentProfile,
    packet: TripPacket
  ): Promise<AgentScore> {
    const skillScore = await this.scoreSkillMatch(agent, packet);
    const workloadScore = this.scoreWorkload(agent);
    const performanceScore = this.scorePerformance(agent);
    const relationshipScore = await this.scoreRelationship(agent, packet);

    const totalScore =
      (skillScore.score * 0.35) +
      (workloadScore.score * 0.30) +
      (performanceScore.score * 0.20) +
      (relationshipScore.score * 0.15);

    return {
      agent,
      totalScore,
      reasoning: {
        skill: skillScore.reason,
        workload: workloadScore.reason,
        performance: performanceScore.reason,
        relationship: relationshipScore.reason
      }
    };
  }

  /**
   * Score skill match (0-100)
   */
  private async scoreSkillMatch(
    agent: AgentProfile,
    packet: TripPacket
  ): Promise<ScoreDetail> {
    let score = 30; // Base score for being eligible

    // Destination expertise
    if (packet.destination?.country) {
      const destSkill = agent.skills.find(s =>
        s.category === "destination" &&
        s.value === packet.destination.country
      );
      if (destSkill) {
        score += destSkill.level * 0.5; // Up to 50 points
      }
    }

    // Trip type expertise
    if (packet.tripType) {
      const typeSkill = agent.skills.find(s =>
        s.category === "trip_type" &&
        s.value === packet.tripType
      );
      if (typeSkill) {
        score += typeSkill.level * 0.2; // Up to 20 points
      }
    }

    return {
      score: Math.min(score, 100),
      reason: this.describeSkillScore(score)
    };
  }

  /**
   * Score workload balance (0-100)
   * Higher is better - prefer agents with lower current load
   */
  private scoreWorkload(agent: AgentProfile): ScoreDetail {
    const utilization = agent.capacity.utilization;

    // Invert: lower utilization = higher score
    const score = Math.round((1 - utilization) * 100);

    return {
      score,
      reason: this.describeWorkloadScore(utilization)
    };
  }

  /**
   * Score past performance (0-100)
   */
  private scorePerformance(agent: AgentProfile): ScoreDetail {
    let score = 50; // Base score

    // Conversion rate (biggest factor)
    score += (agent.performance.conversionRate - 0.5) * 80;

    // Customer rating
    score += (agent.performance.customerRating - 3) * 15;

    // Response time (faster is better)
    if (agent.performance.avgResponseTime < 60) score += 10;
    else if (agent.performance.avgResponseTime < 120) score += 5;

    return {
      score: Math.max(0, Math.min(score, 100)),
      reason: this.describePerformanceScore(agent.performance)
    };
  }

  /**
   * Score customer relationship (0-100)
   */
  private async scoreRelationship(
    agent: AgentProfile,
    packet: TripPacket
  ): Promise<ScoreDetail> {
    if (!packet.customer?.id) {
      return { score: 50, reason: "New customer" };
    }

    // Check if agent has worked with this customer before
    const pastInteractions = await this.agentRegistry
      .getPastInteractions(agent.id, packet.customer.id);

    if (pastInteractions === 0) {
      return { score: 40, reason: "No prior relationship" };
    }

    // Prior relationship = higher score
    const score = Math.min(40 + pastInteractions * 20, 100);

    return {
      score,
      reason: `${pastInteractions} prior interaction${pastInteractions > 1 ? 's' : ''}`
    };
  }

  /**
   * Execute the assignment
   */
  private async executeAssignment(
    agent: AgentProfile,
    packet: TripPacket
  ): Promise<void> {
    // Update packet
    packet.assignedTo = agent.id;
    packet.assignedAt = new Date();

    // Update agent capacity
    agent.capacity.currentLoad++;

    // Send notification
    await this.notifyAgent(agent, packet);

    // Log for analytics
    await this.logAssignment(agent, packet);
  }

  private async notifyAgent(agent: AgentProfile, packet: TripPacket): Promise<void> {
    // Implementation depends on notification system
    // Could be in-app, email, push notification, etc.
  }

  private async logAssignment(agent: AgentProfile, packet: TripPacket): Promise<void> {
    // Log assignment decision for learning
  }

  private describeSkillScore(score: number): string {
    if (score >= 80) return "Strong skill match";
    if (score >= 60) return "Good skill match";
    if (score >= 40) return "Partial skill match";
    return "Basic eligibility";
  }

  private describeWorkloadScore(utilization: number): string {
    if (utilization < 0.3) return "Light workload";
    if (utilization < 0.6) return "Moderate workload";
    if (utilization < 0.8) return "Heavy workload";
    return "Near capacity";
  }

  private describePerformanceScore(perf: AgentProfile["performance"]): string {
    if (perf.conversionRate > 0.6) return "Excellent conversion";
    if (perf.conversionRate > 0.5) return "Good conversion";
    return "Standard performance";
  }
}

interface AgentScore {
  agent: AgentProfile;
  totalScore: number;
  reasoning: {
    skill: string;
    workload: string;
    performance: string;
    relationship: string;
  };
}

interface ScoreDetail {
  score: number;
  reason: string;
}

interface AssignmentResult {
  success: boolean;
  agentId?: string;
  agentName?: string;
  score?: number;
  reasoning?: AgentScore["reasoning"];
  reason?: string;
  fallbackAction?: string;
}
```

---

## 6. Specialized Routing Scenarios

### 6.1 Escalation Paths

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            ESCALATION PATHS                                 │
└─────────────────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────┐
  │                      INITIAL ASSIGNMENT                         │
  │                  (Auto-assigned or manual)                      │
  └────────────────────────────┬────────────────────────────────────┘
                               │
                               │ Agent unable to resolve
                               │ or requires expertise
                               │
                               ▼
  ┌─────────────────────────────────────────────────────────────────┐
  │                   ESCALATION TRIGGERS                           │
  │                                                                  │
  │  ┌─────────────────┬─────────────────┬─────────────────┐       │
  │  │   Time-based    │   Complexity    │   Value-based   │       │
  │  │                 │                 │                 │       │
  │  │ • No response   │ • Agent flags   │ • Budget > ₹5L  │       │
  │  │   in 24 hours   │   complexity    │ • VIP customer  │       │
  │  │ • Near SLA      │ • Stuck state   │ • High-risk     │       │
  │  │   breach        │ • 3+ attempts   │                 │       │
  │  └─────────────────┴─────────────────┴─────────────────┘       │
  └────────────────────────────┬────────────────────────────────────┘
                               │
                               ▼
  ┌─────────────────────────────────────────────────────────────────┐
  │                      ESCALATION TARGETS                         │
  │                                                                  │
  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐    │
  │  │   SENIOR POOL  │  │   SPECIALIST   │  │     OWNER      │    │
  │  │                │  │                │  │                │    │
  │  │ • Experienced  │  │ • Destination  │  │ • All VIP      │    │
  │  │   agents       │  │   experts      │  │ • All escalat- │    │
  │  │ • Higher       │  │ • Trip type    │  │   ions > 48h   │    │
  │  │   capacity     │  │   specialists  │  │ • Final        │    │
  │  │                │  │                │  │   authority    │    │
  │  └────────────────┘  └────────────────┘  └────────────────┘    │
  └─────────────────────────────────────────────────────────────────┘
```

### 6.2 Reassignment and Handoff

```typescript
/**
 * Reassignment and Handoff System
 */

class ReassignmentHandler {
  /**
   * Reassign packet to different agent
   */
  async reassign(
    packetId: string,
    fromAgentId: string,
    toAgentId: string,
    reason: ReassignmentReason,
    notes?: string
  ): Promise<ReassignmentResult> {
    const packet = await this.getPacket(packetId);
    const toAgent = await this.getAgent(toAgentId);

    // Create handoff context
    const handoff = await this.createHandoffContext(packet, fromAgentId);

    // Transfer assignment
    packet.assignedTo = toAgentId;
    packet.reassignmentHistory = packet.reassignmentHistory || [];
    packet.reassignmentHistory.push({
      from: fromAgentId,
      to: toAgentId,
      at: new Date(),
      reason,
      notes
    });

    // Notify both agents
    await this.notifyHandoff(fromAgentId, toAgentId, packet, handoff);

    // Update agent capacities
    await this.updateCapacities(fromAgentId, toAgentId);

    return {
      success: true,
      packetId,
      newAgent: toAgent.name,
      handoffProvided: handoff.summary
    };
  }

  /**
   * Create handoff context for smooth transfer
   */
  private async createHandoffContext(
    packet: TripPacket,
    fromAgentId: string
  ): Promise<HandoffContext> {
    const timeline = await this.getAgentTimeline(packet.id, fromAgentId);
    const currentStatus = await this.getCurrentStatus(packet.id);
    const pendingActions = await this.getPendingActions(packet.id);

    return {
      summary: this.generateHandoffSummary(timeline, currentStatus),
      currentState: currentStatus,
      pendingActions,
      keyDecisions: await this.getKeyDecisions(packet.id),
      customerNotes: await this.getCustomerNotes(packet.id),
      documents: await this.getRelevantDocuments(packet.id)
    };
  }

  private generateHandoffSummary(
    timeline: TimelineEvent[],
    status: PacketStatus
  ): string {
    return `
Handoff Summary for ${status.tripName || "Trip"}:

Current State: ${status.state}
Progress: ${status.completeness}%

Key Actions Taken:
${timeline.slice(-5).map(e => `- ${e.description}`).join("\n")}

Next Steps:
${status.nextSteps}
    `.trim();
  }
}

type ReassignmentReason =
  | "workload_balance"
  | "expertise_required"
  | "agent_unavailable"
  | "customer_request"
  | "performance_issue"
  | "escalation";

interface HandoffContext {
  summary: string;
  currentState: PacketStatus;
  pendingActions: Action[];
  keyDecisions: Decision[];
  customerNotes: CustomerNote[];
  documents: Document[];
}

interface ReassignmentResult {
  success: boolean;
  packetId: string;
  newAgent?: string;
  handoffProvided?: string;
}
```

---

## 7. Auto-Assignment Configuration

### 7.1 Agency-Level Settings

Agencies control their triage and assignment behavior through configuration:

```typescript
/**
 * Triage and Assignment Configuration
 */

interface TriageConfiguration {
  // Auto-assignment settings
  autoAssignment: {
    enabled: boolean;
    queues: string[];              // Queues where auto-assign is active
    exemptAgents?: string[];       // Agents who opt out
    maxCapacityThreshold: number;  // 0-1, don't assign if above this
  };

  // Routing rules
  routingRules: RoutingRule[];

  // Priority settings
  priority: {
    enabled: boolean;
    respectManualPriority: boolean; // Allow agents to override
    slaTargets: {
      [key in PriorityLevel]: number; // Target response time (minutes)
    };
  };

  // Skill requirements
  skillRequirements: {
    requireDestinationMatch: boolean;
    requireTripTypeMatch: boolean;
    minimumSkillLevel: number;      // 0-100
    allowPartialMatch: boolean;
  };

  // Workload balancing
  workloadBalancing: {
    strategy: "round_robin" | "least_loaded" | "skill_based";
    maxConcurrentPerAgent: number;
    softCapacityLimit: number;      // Warning threshold
    hardCapacityLimit: number;      // Stop assignment threshold
  };

  // Escalation settings
  escalation: {
    enabled: boolean;
    autoEscalateRules: EscalationRule[];
    escalationPaths: EscalationPath[];
  };
}

interface EscalationRule {
  trigger: EscalationTrigger;
  targetQueue: string;
  notifyOwner: boolean;
  timeThreshold?: number;          // minutes
}

interface EscalationPath {
  fromQueue: string;
  toQueue: string;
  triggerCondition: string;
}

type EscalationTrigger =
  | "no_response"
  | "stuck_state"
  | "near_sla_breach"
  | "agent_flagged"
  | "value_threshold";
```

### 7.2 Example Configurations

```typescript
/**
 * Example Triage Configurations for Different Agency Types
 */

// Small agency - mostly manual
const SMALL_AGENCY_CONFIG: TriageConfiguration = {
  autoAssignment: {
    enabled: false,
    queues: [],
    maxCapacityThreshold: 0.8
  },
  routingRules: [
    {
      id: "default",
      name: "All to Owner",
      enabled: true,
      priority: 0,
      conditions: [],
      action: {
        type: "manual_review",
        queue: "owner"
      },
      metadata: {
        createdAt: new Date(),
        createdBy: "system"
      }
    }
  ],
  priority: {
    enabled: true,
    respectManualPriority: true,
    slaTargets: {
      LOW: 1440,      // 24 hours
      MEDIUM: 720,    // 12 hours
      HIGH: 240,      // 4 hours
      CRITICAL: 60    // 1 hour
    }
  },
  skillRequirements: {
    requireDestinationMatch: false,
    requireTripTypeMatch: false,
    minimumSkillLevel: 0,
    allowPartialMatch: true
  },
  workloadBalancing: {
    strategy: "least_loaded",
    maxConcurrentPerAgent: 10,
    softCapacityLimit: 0.7,
    hardCapacityLimit: 0.9
  },
  escalation: {
    enabled: false,
    autoEscalateRules: [],
    escalationPaths: []
  }
};

// Medium agency - smart routing, no auto-assign
const MEDIUM_AGENCY_CONFIG: TriageConfiguration = {
  autoAssignment: {
    enabled: false,
    queues: [],
    maxCapacityThreshold: 0.8
  },
  routingRules: [
    {
      id: "vip",
      name: "VIP to Senior",
      enabled: true,
      priority: 100,
      conditions: [
        { field: "customer.tier", operator: "equals", value: "VIP" }
      ],
      action: {
        type: "queue_pool",
        queue: "senior_agents",
        priority: "HIGH"
      },
      metadata: { createdAt: new Date(), createdBy: "system" }
    },
    {
      id: "international",
      name: "International to Specialists",
      enabled: true,
      priority: 90,
      conditions: [
        { field: "destination.international", operator: "equals", value: true }
      ],
      action: {
        type: "queue_pool",
        queue: "international_team"
      },
      metadata: { createdAt: new Date(), createdBy: "system" }
    },
    {
      id: "default",
      name: "Default to General",
      enabled: true,
      priority: 0,
      conditions: [],
      action: {
        type: "queue_pool",
        queue: "general_pool"
      },
      metadata: { createdAt: new Date(), createdBy: "system" }
    }
  ],
  priority: {
    enabled: true,
    respectManualPriority: true,
    slaTargets: {
      LOW: 480,       // 8 hours
      MEDIUM: 240,    // 4 hours
      HIGH: 120,      // 2 hours
      CRITICAL: 30    // 30 minutes
    }
  },
  skillRequirements: {
    requireDestinationMatch: true,
    requireTripTypeMatch: false,
    minimumSkillLevel: 50,
    allowPartialMatch: true
  },
  workloadBalancing: {
    strategy: "skill_based",
    maxConcurrentPerAgent: 15,
    softCapacityLimit: 0.7,
    hardCapacityLimit: 0.9
  },
  escalation: {
    enabled: true,
    autoEscalateRules: [
      {
        trigger: "no_response",
        targetQueue: "senior_agents",
        notifyOwner: false,
        timeThreshold: 480 // 8 hours
      }
    ],
    escalationPaths: [
      {
        fromQueue: "general_pool",
        toQueue: "senior_agents",
        triggerCondition: "complexity > 70 AND no_response > 4h"
      }
    ]
  }
};

// Large agency - full automation
const LARGE_AGENCY_CONFIG: TriageConfiguration = {
  autoAssignment: {
    enabled: true,
    queues: ["general_pool", "international_team", "domestic_team"],
    maxCapacityThreshold: 0.85
  },
  routingRules: [
    {
      id: "vip_owner",
      name: "VIP to Owner",
      enabled: true,
      priority: 1000,
      conditions: [
        { field: "customer.tier", operator: "equals", value: "VIP" }
      ],
      action: {
        type: "owner_direct",
        priority: "HIGH",
        notify: true
      },
      metadata: { createdAt: new Date(), createdBy: "system" }
    },
    {
      id: "high_value_senior",
      name: "High Value to Senior",
      enabled: true,
      priority: 900,
      conditions: [
        { field: "budget.total", operator: "greater_than", value: 500000 }
      ],
      action: {
        type: "auto_assign",
        queue: "senior_agents"
      },
      metadata: { createdAt: new Date(), createdBy: "system" }
    },
    {
      id: "simple_auto",
      name: "Simple Auto-Assign",
      enabled: true,
      priority: 800,
      conditions: [
        { field: "triageScores.complexity.value", operator: "less_than", value: 40 }
      ],
      action: {
        type: "auto_assign",
        queue: "general_pool"
      },
      metadata: { createdAt: new Date(), createdBy: "system" }
    },
    {
      id: "default_manual",
      name: "Default Manual",
      enabled: true,
      priority: 0,
      conditions: [],
      action: {
        type: "manual_review",
        queue: "unassigned"
      },
      metadata: { createdAt: new Date(), createdBy: "system" }
    }
  ],
  priority: {
    enabled: true,
    respectManualPriority: false,
    slaTargets: {
      LOW: 60,        // 1 hour
      MEDIUM: 30,     // 30 minutes
      HIGH: 15,       // 15 minutes
      CRITICAL: 5     // 5 minutes
    }
  },
  skillRequirements: {
    requireDestinationMatch: true,
    requireTripTypeMatch: true,
    minimumSkillLevel: 60,
    allowPartialMatch: false
  },
  workloadBalancing: {
    strategy: "skill_based",
    maxConcurrentPerAgent: 20,
    softCapacityLimit: 0.75,
    hardCapacityLimit: 0.9
  },
  escalation: {
    enabled: true,
    autoEscalateRules: [
      {
        trigger: "no_response",
        targetQueue: "senior_agents",
        notifyOwner: false,
        timeThreshold: 120 // 2 hours
      },
      {
        trigger: "near_sla_breach",
        targetQueue: "priority_queue",
        notifyOwner: true,
        timeThreshold: 45
      }
    ],
    escalationPaths: [
      {
        fromQueue: "general_pool",
        toQueue: "senior_agents",
        triggerCondition: "no_response > 2h OR agent_flagged"
      },
      {
        fromQueue: "senior_agents",
        toQueue: "owner",
        triggerCondition: "no_response > 4h OR value > 10L"
      }
    ]
  }
};
```

---

## 8. Triage Performance Metrics

### 8.1 Key Metrics Dashboard

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         TRIAGE PERFORMANCE DASHBOARD                        │
└─────────────────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────┐
  │                        RESPONSE METRICS                         │
  │                                                                  │
  │  First Response Time              │      47 min avg            │
  │  ├─ CRITICAL: 8 min               │      ▼ 12% vs last week    │
  │  ├─ HIGH: 28 min                  │                             │
  │  ├─ MEDIUM: 52 min                │  SLA Compliance: 94.2%     │
  │  └─ LOW: 124 min                  │      ▲ 3% vs last week     │
  │                                                                  │
  │  Assignment Rate                   │      Auto: 67%             │
  │  ├─ Auto-assigned: 67%             │      Manual: 33%           │
  │  └─ Manual assignment: 33%        │                             │
  └─────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────┐
  │                        ROUTING METRICS                          │
  │                                                                  │
  │  Routing Accuracy                   │      89.3%                 │
  │  ├─ Correct queue: 89.3%            │      ▲ 2% vs last month   │
  │  ├─ Reassignment rate: 8.2%         │                             │
  │  └─ Owner escalation: 2.5%          │                             │
  │                                                                  │
  │  Agent-Selection Accuracy            │      76.8%                 │
  │  ├─ No reassignment: 76.8%          │      ▲ 5% vs last month   │
  │  ├─ One reassignment: 15.0%         │                             │
  │  └─ Multiple: 8.2%                  │                             │
  └─────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────┐
  │                        WORKLOAD METRICS                         │
  │                                                                  │
  │  Agent Utilization                  │      72% avg              │
  │  ├─ Overutilized (>90%): 3 agents   │      ▲ Stable             │
  │  ├─ Optimal (60-80%): 12 agents     │                             │
  │  └─ Underutilized (<40%): 2 agents  │                             │
  │                                                                  │
  │  Queue Balance                      │      Good                  │
  │  ├─ General Pool: 45 packets        │      3.75 avg/agent       │
  │  ├─ Senior Agents: 18 packets       │      3.00 avg/agent       │
  │  └─ Specialists: 22 packets         │      3.67 avg/agent       │
  └─────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────┐
  │                        OUTCOME METRICS                          │
  │                                                                  │
  │  Conversion by Assignment Type          │                        │
  │  ├─ Auto-assigned: 18.2%                │      Manual: 24.1%    │
  │  └─ Manual assigned: 24.1%              │      ▲ 5.9% gap       │
  │                                                                  │
  │  Customer Satisfaction by Priority       │                        │
  │  ├─ CRITICAL: 4.8/5.0                   │      Avg: 4.6/5.0     │
  │  ├─ HIGH: 4.7/5.0                       │                       │
  │  ├─ MEDIUM: 4.6/5.0                     │                       │
  │  └─ LOW: 4.3/5.0                        │                       │
  └─────────────────────────────────────────────────────────────────┘
```

### 8.2 Metric Definitions

```typescript
/**
 * Triage Performance Metrics
 */

interface TriageMetrics {
  // Response time metrics
  responseTime: {
    firstResponse: {
      average: number;              // minutes
      median: number;
      p95: number;
      p99: number;
      byPriority: {
        [key in PriorityLevel]: ResponseTimeStats;
      };
    };
    slaCompliance: {
      overall: number;              // 0-1, percentage meeting SLA
      byPriority: {
        [key in PriorityLevel]: number;
      };
      trend: "improving" | "stable" | "declining";
    };
  };

  // Routing metrics
  routing: {
    accuracy: number;               // 0-1, correct queue on first try
    reassignmentRate: number;       // 0-1, percentage reassigned
    reassignmentReasons: {
      [reason: string]: number;     // count by reason
    };
    ownerEscalationRate: number;    // 0-1
  };

  // Assignment metrics
  assignment: {
    autoAssignRate: number;         // 0-1
    agentSelectionAccuracy: number; // 0-1, no reassignment needed
    avgAssignmentTime: number;      // milliseconds
  };

  // Workload metrics
  workload: {
    avgUtilization: number;         // 0-1
    utilizationDistribution: {
      overutilized: number;         // count, >90%
      optimal: number;              // count, 60-80%
      underutilized: number;        // count, <40%
    };
    queueBalance: {
      [queue: string]: {
        packetCount: number;
        agentCount: number;
        avgPacketsPerAgent: number;
      };
    };
  };

  // Outcome metrics
  outcomes: {
    conversionByAssignmentType: {
      auto: number;                 // 0-1
      manual: number;               // 0-1
    };
    customerSatisfaction: {
      overall: number;              // 0-5
      byPriority: {
        [key in PriorityLevel]: number;
      };
    };
  };
}

interface ResponseTimeStats {
  average: number;
  median: number;
  p95: number;
  count: number;
}
```

---

## 9. Implementation Roadmap

### Phase 1: Foundation (Weeks 1-4)

**Week 1-2: Core Scoring**
- Implement urgency, complexity, and value scorers
- Create triage score calculation pipeline
- Add score storage to packet model
- Unit tests for scoring algorithms

**Week 3-4: Basic Routing**
- Implement routing rule engine
- Create rule configuration UI
- Add manual queue assignment
- Basic priority-based inbox sorting

### Phase 2: Assignment (Weeks 5-8)

**Week 5-6: Agent Profiles**
- Agent skill and capacity tracking
- Agent registry service
- Profile management UI

**Week 7-8: Auto-Assignment**
- Assignment algorithm implementation
- Eligibility filtering
- Skill matching
- Notification system integration

### Phase 3: Advanced Features (Weeks 9-12)

**Week 9-10: Escalation**
- Escalation rule engine
- Auto-escalation triggers
- Reassignment workflow
- Handoff context building

**Week 11-12: ML Recommendations**
- Feature extraction pipeline
- Model training pipeline
- Recommendation API
- A/B testing framework

### Phase 4: Analytics & Optimization (Weeks 13-16)

**Week 13-14: Metrics**
- Performance tracking
- Dashboard implementation
- Alerting on SLA breaches

**Week 15-16: Optimization**
- Rule effectiveness tracking
- Automatic rule suggestions
- Workload balancing optimization

---

## 10. Future Evolution

### 10.1 Learned Routing

The system will learn from outcomes to improve routing:

```typescript
/**
 * Learned Routing Rule Suggestion
 */

class LearnedRouter {
  /**
   * Suggest new routing rules based on outcomes
   */
  async suggestRules(): Promise<RoutingRuleSuggestion[]> {
    const patterns = await this.analyzeOutcomes();

    return patterns.map(p => ({
      suggestedRule: this.buildRule(p),
      confidence: p.confidence,
      expectedImprovement: p.improvement,
      supportingCases: p.cases
    }));
  }

  /**
   * Analyze historical outcomes for patterns
   */
  private async analyzeOutcomes(): Promise<RoutingPattern[]> {
    // Look for patterns like:
    // - "Packets to queue A have 20% better conversion when budget > ₹3L"
    // - "Agent X performs 30% better on Europe trips"
    // - "VIP customers assigned to seniors convert 15% more"

    return [];
  }
}
```

### 10.2 Predictive Capacity Planning

Predict future workload to proactively manage agent capacity:

```typescript
/**
 * Predictive Capacity Planning
 */

class CapacityPlanner {
  /**
   * Predict workload for next N days
   */
  async predictWorkload(days: number): Promise<WorkloadPrediction[]> {
    const predictions: WorkloadPrediction[] = [];

    for (let i = 1; i <= days; i++) {
      const date = this.addDays(Date.now(), i);
      const prediction = await this.predictDay(date);
      predictions.push(prediction);
    }

    return predictions;
  }

  /**
   * Predict single day workload
   */
  private async predictDay(date: Date): Promise<WorkloadPrediction> {
    // Factors:
    // - Seasonality (day of week, month)
    // - Historical trends
    // - Upcoming holidays
    // - Marketing campaigns
    // - Weather events

    return {
      date,
      expectedPackets: 0,
      expectedByComplexity: {},
      expectedByPriority: {},
      recommendedStaffing: {
        totalAgents: 0,
        bySpecialization: {}
      }
    };
  }
}
```

### 10.3 Dynamic Routing Optimization

Continuously optimize routing based on real-time performance:

```typescript
/**
 * Dynamic Routing Optimizer
 */

class RoutingOptimizer {
  /**
   * Get real-time routing adjustments
   */
  async optimize(): Promise<RoutingAdjustment[]> {
    const adjustments: RoutingAdjustment[] = [];

    // Check current system state
    const state = await this.getCurrentState();

    // Identify issues
    if (state.queueImbalance > 0.3) {
      adjustments.push(await this.balanceQueues(state));
    }

    if (state.slaBreachRisk > 0.1) {
      adjustments.push(await this.prioritizeCritical(state));
    }

    if (state.underutilizedExperts.length > 0) {
      adjustments.push(await this.recommendSpecialistRouting(state));
    }

    return adjustments;
  }
}
```

---

## Summary

The Triage Strategies system is the intelligence layer that ensures every inquiry reaches the right person at the right time. By combining:

- **Explicit routing rules** for agency control
- **Multi-dimensional scoring** for nuanced decisions
- **Smart assignment algorithms** for optimal matching
- **Configurable automation** for different agency sizes

The system balances efficiency with personalization, ensuring high-value and complex trips get expert attention while standard trips flow through automatically.

---

**Next Document:** INTAKE_06_ANALYTICS_DEEP_DIVE.md — Metrics, insights, and analytics for the intake system.