# Safety & Risk Systems — Technical Deep Dive

> Part 1 of 5 in the Safety & Risk Systems Deep Dive Series

**Series Index:**
1. [Technical Deep Dive](SAFETY_01_TECHNICAL_DEEP_DIVE.md) — Architecture & Risk Engine (this document)
2. [UX/UI Deep Dive](SAFETY_02_UX_UI_DEEP_DIVE.md) — Risk Display & Warning UI
3. [Business Value Deep Dive](SAFETY_03_BUSINESS_VALUE_DEEP_DIVE.md) — Protection & ROI
4. [Compliance Deep Dive](SAFETY_04_COMPLIANCE_DEEP_DIVE.md) — GST, TCS & Regulations
5. [Escalation Deep Dive](SAFETY_05_ESCALATION_DEEP_DIVE.md) — Owner Workflows & Alerts

---

## Document Overview

**Purpose:** Comprehensive technical exploration of the Safety & Risk Systems architecture — how risks are detected, scored, presented, and managed throughout the trip lifecycle.

**Scope:**
- Risk detection architecture
- Risk scoring framework
- Budget validation engine
- Compliance checking system
- Safety nets and guardrails
- Alert and notification system
- Risk resolution workflows
- Integration with trip lifecycle

**Target Audience:** Engineers, architects, and technical stakeholders implementing or configuring the safety system.

**Last Updated:** 2026-04-24

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [System Architecture](#system-architecture)
3. [Risk Detection Framework](#risk-detection-framework)
4. [Risk Scoring Engine](#risk-scoring-engine)
5. [Budget Validation System](#budget-validation-system)
6. [Compliance Checking](#compliance-checking)
7. [Safety Nets & Guardrails](#safety-nets--guardrails)
8. [Alert & Notification System](#alert--notification-system)
9. [Risk Resolution Workflows](#risk-resolution-workflows)
10. [Data Model](#data-model)
11. [API Specification](#api-specification)

---

## 1. Executive Summary

### The Safety Problem

Travel bookings carry multiple types of risk:

- **Financial Risk** — Budget overruns, payment failures, refund disputes
- **Compliance Risk** — GST/TCS violations, missing documentation, regulatory issues
- **Operational Risk** — Invalid bookings, supplier failures, timeline violations
- **Customer Risk** — Unrealistic expectations, dissatisfaction, disputes
- **Agency Risk** — Reputation damage, liability exposure, cash flow issues

Without systematic risk management, agencies face:
- Revenue loss from unpaid or disputed bookings
- Regulatory penalties from compliance violations
- Customer churn from unmet expectations
- Operational chaos from last-minute issues

### The Safety Solution

A comprehensive risk management system that:

1. **Detects risks early** — Identify issues before they become problems
2. **Scores risks appropriately** — Prioritize by severity and likelihood
3. **Presents risks clearly** — Make risks visible and actionable
4. **Provides guardrails** — Prevent risky actions with safety nets
5. **Enables resolution** — Guide agents through risk remediation

### Key Design Principles

| Principle | Description |
|-----------|-------------|
| **Fail safe** | System prevents risky actions by default |
| **Progressive disclosure** | Show risks at appropriate severity levels |
| **Contextual relevance** | Risk checks depend on trip stage and context |
| **Agency control** | Owners configure risk tolerance and rules |
| **Audit everything** | Complete trail of risk detection and resolution |
| **Learning system** | Improve detection from outcomes |

---

## 2. System Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SAFETY & RISK SYSTEM ARCHITECTURE                    │
└─────────────────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────┐
  │                      TRIP DATA SOURCES                          │
  │                                                                  │
  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
  │  │ Packet   │  │ Quote    │  │ Booking  │  │ Payment  │      │
  │  │ Data     │  │ Data     │  │ Data     │  │ Data     │      │
  │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘      │
  └───────┼────────────┼────────────┼────────────┼──────────────┘
          │            │            │            │
          └────────────┴────────────┴────────────┴────┬──────────────┐
                                                       │              │
                                                       ▼              │
  ┌─────────────────────────────────────────────────────────────┐    │
  │                    RISK DETECTION LAYER                      │    │
  │                                                              │    │
  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐  │    │
  │  │ Budget Rules    │  │ Compliance      │  │ Operational │  │    │
  │  │ Engine          │  │ Checker         │  │ Validators  │  │    │
  │  └────────┬────────┘  └────────┬────────┘  └──────┬──────┘  │    │
  │           │                    │                   │         │    │
  │           └────────────────────┴───────────────────┘         │    │
  │                              │                               │    │
  └──────────────────────────────┼───────────────────────────────┘    │
                                 │                                    │
                                 ▼                                    │
  ┌─────────────────────────────────────────────────────────────┐    │
  │                    RISK SCORING ENGINE                       │    │
  │                                                              │    │
  │  • Severity assessment (0-100)                               │    │
  │  • Likelihood calculation (0-100)                            │    │
  │  • Risk score = Severity × Likelihood                        │    │
  │  • Category assignment                                       │    │
  └──────────────────────────────┬───────────────────────────────┘    │
                                 │                                    │
                                 ▼                                    │
  ┌─────────────────────────────────────────────────────────────┐    │
  │                    RISK ACTION LAYER                         │    │
  │                                                              │    │
  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │    │
  │  │ Block/      │  │ Warn/       │  │ Notify/             │  │    │
  │  │ Prevent     │  │ Flag        │  │ Escalate           │  │    │
  │  └─────────────┘  └─────────────┘  └─────────────────────┘  │    │
  └──────────────────────────────┬───────────────────────────────┘    │
                                 │                                    │
          ┌──────────────────────┼──────────────────────┐            │
          │                      │                      │            ▼
          ▼                      ▼                      ▼    ┌───────────────────┐
  ┌───────────────┐    ┌───────────────┐    ┌───────────────┐   │   RISK          │
  │  Agent UI     │    │  Owner Alert  │    │  System Log   │   │   RESOLUTION    │
  │  (Warnings)   │    │  (Escalation) │    │  (Audit Trail)│   │   WORKFLOWS     │
  └───────────────┘    └───────────────┘    └───────────────┘   └───────────────────┘
```

### 2.2 Component Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      CORE COMPONENTS INTERACTION                            │
└─────────────────────────────────────────────────────────────────────────────┘

  ┌───────────────────────────────────────────────────────────────────────┐
  │                          RiskOrchestrator                             │
  │                                                                       │
  │  • Coordinates all risk checks                                       │
  │  • Manages check execution order                                      │
  │  • Aggregates risk results                                           │
  │  • Triggers appropriate actions                                       │
  └───────┬───────────────────────────────────────────────────┬─────────┘
          │                                                   │
          │                                                   │
  ┌───────▼─────────┐  ┌─────────────────┐  ┌─────────────────▼─────────┐
  │ RiskRuleEngine  │  │ BudgetValidator │  │ ComplianceChecker          │
  │                 │  │                 │  │                            │
  │ • Rule storage  │  │ • Budget rules  │  │ • GST/TCS rules            │
  │ • Evaluation    │  │ • Overrun calc  │  │ • Document checks          │
  │ • Matching      │  │ • Payment check │  │ • Regulatory validation    │
  └─────────────────┘  └─────────────────┘  └────────────────────────────┘
           │                     │                        │
           └─────────────────────┴────────────────────────┘
                                  │
                                  ▼
                       ┌─────────────────────┐
                       │   RiskScorer        │
                       │                     │
                       │ • Severity calc     │
                       │ • Likelihood calc   │
                       │ • Score aggregation │
                       └──────────┬──────────┘
                                  │
                                  ▼
                       ┌─────────────────────┐
                       │  RiskActionManager  │
                       │                     │
                       │ • Block actions     │
                       │ • Show warnings     │
                       │ • Send alerts       │
                       │ • Create tasks      │
                       └─────────────────────┘
```

### 2.3 Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           RISK CHECK DATA FLOW                              │
└─────────────────────────────────────────────────────────────────────────────┘

  User Action (e.g., "Create Quote")
           │
           ▼
  ┌─────────────────────────────────────────────────────────────┐
  │  PRE-CHECK HOOK                                             │
  │  • Intercept action                                         │
  │  • Gather context (trip data, user, stage)                   │
  └──────────────────────────┬──────────────────────────────────┘
                             │
                             ▼
  ┌─────────────────────────────────────────────────────────────┐
  │  RISK DETECTION                                             │
  │  • Run applicable risk checks                               │
  │  • Parallel execution where possible                        │
  │  • Cache results where appropriate                          │
  └──────────────────────────┬──────────────────────────────────┘
                             │
                    ┌────────┴────────┐
                    │                 │
                    ▼                 ▼
            ┌───────────┐     ┌───────────────┐
            │ Risks     │     │ No Risks      │
            │ Detected  │     │ Detected      │
            └─────┬─────┘     └───────┬───────┘
                  │                    │
                  ▼                    │
  ┌─────────────────────────────────────┴───────────────────────────┐
  │  RISK SCORING                                                  │
  │  • Calculate severity (0-100)                                  │
  │  • Calculate likelihood (0-100)                               │
  │  • Determine risk level (LOW/MED/HIGH/CRITICAL)                │
  └──────────────────────────┬──────────────────────────────────────┘
                             │
                             ▼
  ┌─────────────────────────────────────────────────────────────┐
  │  ACTION DETERMINATION                                        │
  │  • CRITICAL → Block action                                   │
  │  • HIGH → Require confirmation                               │
  │  • MEDIUM → Show warning                                     │
  │  • LOW → Log only                                            │
  └──────────────────────────┬──────────────────────────────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
      ┌───────────┐  ┌───────────┐  ┌───────────┐
      │  BLOCK    │  │   WARN    │  │   LOG     │
      │  Action   │  │   User    │  │   Only    │
      └───────────┘  └───────────┘  └───────────┘
```

---

## 3. Risk Detection Framework

### 3.1 Risk Categories

```typescript
/**
 * Risk Categories and Types
 */

type RiskCategory =
  | "financial"        // Budget, payment, refund risks
  | "compliance"       // GST, TCS, documentation
  | "operational"      // Booking validity, supplier issues
  | "customer"         // Expectations, satisfaction
  | "agency";          // Reputation, liability

interface RiskType {
  id: string;
  category: RiskCategory;
  name: string;
  description: string;
  severity: "low" | "medium" | "high" | "critical";
  checkFunction: string;      // Reference to check implementation
  mitigation: string[];
}

// Risk type registry
const RISK_TYPES: RiskType[] = [
  // Financial risks
  {
    id: "budget_overrun",
    category: "financial",
    name: "Budget Overrun",
    description: "Quote exceeds customer's budget",
    severity: "high",
    checkFunction: "checkBudgetOverrun",
    mitigation: ["adjust_itinerary", "increase_budget", "inform_customer"]
  },
  {
    id: "payment_failure_risk",
    category: "financial",
    name: "Payment Failure Risk",
    description: "High risk of payment failure based on history",
    severity: "medium",
    checkFunction: "checkPaymentRisk",
    mitigation: ["pre_payment_verification", "partial_payment", "upfront_full"]
  },
  {
    id: "refund_risk",
    category: "financial",
    name: "Refund Risk",
    description: "Booking has restrictive refund terms",
    severity: "medium",
    checkFunction: "checkRefundRisk",
    mitigation: ["inform_customer", "offer_insurance", "choose_flexible_supplier"]
  },

  // Compliance risks
  {
    id: "gst_compliance",
    category: "compliance",
    name: "GST Compliance",
    description: "GST calculation or documentation issue",
    severity: "high",
    checkFunction: "checkGSTCompliance",
    mitigation: ["correct_gst_calculation", "obtain_gst_details", "update_invoice"]
  },
  {
    id: "tcs_compliance",
    category: "compliance",
    name: "TCS Compliance",
    description: "TCS collection or remittance issue",
    severity: "high",
    checkFunction: "checkTCSCompliance",
    mitigation: ["collect_tcs", "update_pan_details", "adjust_tax_calculation"]
  },
  {
    id: "missing_documentation",
    category: "compliance",
    name: "Missing Documentation",
    description: "Required travel documents missing",
    severity: "critical",
    checkFunction: "checkDocumentation",
    mitigation: ["request_documents", "verify_validity", "assist_application"]
  },

  // Operational risks
  {
    id: "invalid_booking",
    category: "operational",
    name: "Invalid Booking",
    description: "Booking cannot be fulfilled as specified",
    severity: "critical",
    checkFunction: "checkBookingValidity",
    mitigation: ["find_alternatives", "modify_dates", "change_destination"]
  },
  {
    id: "supplier_risk",
    category: "operational",
    name: "Supplier Risk",
    description: "Supplier has reliability issues",
    severity: "medium",
    checkFunction: "checkSupplierReliability",
    mitigation: ["use_alternative_supplier", "add_contingency", "increase_deposit"]
  },
  {
    id: "timeline_risk",
    category: "operational",
    name: "Timeline Risk",
    description: "Insufficient time for booking/processing",
    severity: "high",
    checkFunction: "checkTimelineFeasibility",
    mitigation: ["expedite_process", "extend_deadline", "manage_expectations"]
  },

  // Customer risks
  {
    id: "unrealistic_expectations",
    category: "customer",
    name: "Unrealistic Expectations",
    description: "Customer expectations may not be met",
    severity: "medium",
    checkFunction: "checkExpectations",
    mitigation: ["set_expectations", "provide_alternatives", "document_communication"]
  },
  {
    id: "satisfaction_risk",
    category: "customer",
    name: "Satisfaction Risk",
    description: "Low predicted satisfaction based on profile",
    severity: "low",
    checkFunction: "checkSatisfactionRisk",
    mitigation: ["enhance_service", "add_perks", "proactive_communication"]
  },

  // Agency risks
  {
    id: "reputation_risk",
    category: "agency",
    name: "Reputation Risk",
    description: "High-risk booking that could damage reputation",
    severity: "high",
    checkFunction: "checkReputationRisk",
    mitigation: ["owner_approval", "enhanced_service", "risk_pricing"]
  },
  {
    id: "liability_exposure",
    category: "agency",
    name: "Liability Exposure",
    description: "Potential liability from booking conditions",
    severity: "high",
    checkFunction: "checkLiabilityExposure",
    mitigation: ["liability_waiver", "insurance", "terms_clarification"]
  }
];
```

### 3.2 Risk Check Interface

```typescript
/**
 * Risk Check Interface
 */

interface RiskCheck {
  id: string;
  name: string;
  category: RiskCategory;

  // When to run
  triggers: CheckTrigger[];

  // Check configuration
  config: {
    enabled: boolean;
    priority: number;              // Higher = earlier check
    async: boolean;                // Can run in parallel
    cacheable: boolean;            // Cache results
    cacheTTL?: number;             // milliseconds
  };

  // Check function
  execute: (context: CheckContext) => Promise<RiskCheckResult>;
}

interface CheckTrigger {
  eventType: string;              // e.g., "quote_created", "booking_confirmed"
  stage?: string;                 // Optional stage filter
  conditions?: TriggerCondition[];
}

interface CheckContext {
  // Trip data
  packet: TripPacket;
  quote?: Quote;
  booking?: Booking;

  // Context
  agency: Agency;
  agent: Agent;
  customer: Customer;

  // Metadata
  timestamp: Date;
  stage: TripStage;
}

interface RiskCheckResult {
  checkId: string;
  passed: boolean;
  risks: DetectedRisk[];
  confidence: number;             // 0-1
  metadata: {
    executionTime: number;         // milliseconds
    cached: boolean;
    [key: string]: any;
  };
}

interface DetectedRisk {
  typeId: string;
  severity: RiskSeverity;
  likelihood: number;             // 0-100
  impact: number;                 // 0-100
  score: number;                  // severity × likelihood

  // Risk details
  details: {
    description: string;
    affectedField?: string;
    currentValue?: any;
    threshold?: any;
    recommendation?: string;
  };

  // Mitigation
  suggestedActions: string[];
  canOverride: boolean;
  requiresApproval: boolean;
}

type RiskSeverity = "low" | "medium" | "high" | "critical";
type TripStage = "inquiry" | "quoting" | "negotiating" | "booking" | "post_booking";
```

### 3.3 Risk Check Registry

```typescript
/**
 * Risk Check Registry
 */

class RiskCheckRegistry {
  private checks: Map<string, RiskCheck> = new Map();

  /**
   * Register a risk check
   */
  register(check: RiskCheck): void {
    this.checks.set(check.id, check);
  }

  /**
   * Get applicable checks for an event
   */
  getApplicableChecks(eventType: string, stage: TripStage): RiskCheck[] {
    return Array.from(this.checks.values())
      .filter(check => this.isApplicable(check, eventType, stage))
      .sort((a, b) => b.config.priority - a.config.priority);
  }

  /**
   * Check if a risk check is applicable
   */
  private isApplicable(
    check: RiskCheck,
    eventType: string,
    stage: TripStage
  ): boolean {
    if (!check.config.enabled) return false;

    const matchingTrigger = check.triggers.find(t =>
      t.eventType === eventType &&
      (!t.stage || t.stage === stage)
    );

    if (!matchingTrigger) return false;

    if (matchingTrigger.conditions) {
      // Evaluate conditions (implementation depends on context)
      return this.evaluateConditions(matchingTrigger.conditions);
    }

    return true;
  }

  /**
   * Execute applicable checks
   */
  async executeChecks(
    eventType: string,
    context: CheckContext
  ): Promise<RiskCheckResult[]> {
    const applicableChecks = this.getApplicableChecks(
      eventType,
      context.stage
    );

    // Separate async and sync checks
    const asyncChecks = applicableChecks.filter(c => c.config.async);
    const syncChecks = applicableChecks.filter(c => !c.config.async);

    // Execute sync checks first (in order)
    const syncResults = await this.executeSyncChecks(syncChecks, context);

    // Execute async checks in parallel
    const asyncResults = await this.executeAsyncChecks(asyncChecks, context);

    return [...syncResults, ...asyncResults];
  }

  private async executeSyncChecks(
    checks: RiskCheck[],
    context: CheckContext
  ): Promise<RiskCheckResult[]> {
    const results: RiskCheckResult[] = [];

    for (const check of checks) {
      // Stop if previous critical risk found
      if (this.hasCriticalRisk(results)) break;

      results.push(await this.executeCheck(check, context));
    }

    return results;
  }

  private async executeAsyncChecks(
    checks: RiskCheck[],
    context: CheckContext
  ): Promise<RiskCheckResult[]> {
    return Promise.all(
      checks.map(check => this.executeCheck(check, context))
    );
  }

  private async executeCheck(
    check: RiskCheck,
    context: CheckContext
  ): Promise<RiskCheckResult> {
    const start = Date.now();

    // Check cache if enabled
    if (check.config.cacheable) {
      const cached = await this.getCachedResult(check.id, context);
      if (cached) {
        cached.metadata.cached = true;
        return cached;
      }
    }

    // Execute check
    const result = await check.execute(context);
    result.metadata.executionTime = Date.now() - start;
    result.metadata.cached = false;

    // Cache result if enabled
    if (check.config.cacheable) {
      await this.cacheResult(check.id, context, result);
    }

    return result;
  }

  private hasCriticalRisk(results: RiskCheckResult[]): boolean {
    return results.some(r =>
      r.risks.some(risk => risk.severity === "critical")
    );
  }

  private async getCachedResult(
    checkId: string,
    context: CheckContext
  ): Promise<RiskCheckResult | null> {
    // Implementation depends on cache backend
    return null;
  }

  private async cacheResult(
    checkId: string,
    context: CheckContext,
    result: RiskCheckResult
  ): Promise<void> {
    // Implementation depends on cache backend
  }

  private evaluateConditions(conditions: TriggerCondition[]): boolean {
    // Implementation for condition evaluation
    return true;
  }
}

interface TriggerCondition {
  field: string;
  operator: string;
  value: any;
}
```

---

## 4. Risk Scoring Engine

### 4.1 Scoring Algorithm

```typescript
/**
 * Risk Scoring Engine
 */

class RiskScoringEngine {
  /**
   * Calculate risk score from detected risk
   */
  calculateRiskScore(risk: DetectedRisk): RiskScore {
    const severity = this.calculateSeverity(risk);
    const likelihood = risk.likelihood;

    // Risk score = severity × likelihood
    const score = Math.round((severity * likelihood) / 100);

    return {
      score,
      severity: this.getSeverityLevel(score),
      confidence: risk.impact,     // Use impact as proxy for confidence
      factors: {
        severity,
        likelihood,
        impact: risk.impact
      }
    };
  }

  /**
   * Calculate severity from risk details
   */
  private calculateSeverity(risk: DetectedRisk): number {
    let severity = risk.severity === "critical" ? 100 :
                   risk.severity === "high" ? 75 :
                   risk.severity === "medium" ? 50 : 25;

    // Adjust based on impact
    if (risk.impact > 75) severity = Math.min(severity + 15, 100);
    else if (risk.impact < 25) severity = Math.max(severity - 10, 0);

    return severity;
  }

  /**
   * Get severity level from score
   */
  private getSeverityLevel(score: number): "low" | "medium" | "high" | "critical" {
    if (score >= 75) return "critical";
    if (score >= 50) return "high";
    if (score >= 25) return "medium";
    return "low";
  }

  /**
   * Aggregate multiple risks into overall assessment
   */
  aggregateRisks(risks: DetectedRisk[]): RiskAssessment {
    if (risks.length === 0) {
      return {
        overallRisk: "none",
        totalScore: 0,
        riskCount: 0,
        byCategory: {},
        bySeverity: { low: 0, medium: 0, high: 0, critical: 0 },
        recommendedAction: "proceed"
      };
    }

    // Score individual risks
    const scoredRisks = risks.map(r => ({
      risk: r,
      score: this.calculateRiskScore(r)
    }));

    // Calculate total score (weighted sum, critical risks dominate)
    const totalScore = this.calculateAggregateScore(scoredRisks);

    // Count by category and severity
    const byCategory = this.groupByCategory(scoredRisks);
    const bySeverity = this.groupBySeverity(scoredRisks);

    // Determine overall risk level
    const overallRisk = this.determineOverallRisk(totalScore, bySeverity);

    // Recommend action
    const recommendedAction = this.recommendAction(overallRisk, bySeverity);

    return {
      overallRisk,
      totalScore,
      riskCount: risks.length,
      byCategory,
      bySeverity,
      recommendedAction,
      topRisks: this.getTopRisks(scoredRisks, 5)
    };
  }

  private calculateAggregateScore(scoredRisks: ScoredRisk[]): number {
    // Critical risks dominate
    const hasCritical = scoredRisks.some(s => s.score.severity === "critical");
    if (hasCritical) return 100;

    // Weighted sum with diminishing returns
    let score = 0;
    const weights = scoredRisks.map(s => s.score.score).sort((a, b) => b - a);

    for (let i = 0; i < weights.length; i++) {
      // First risk: 100%, second: 80%, third: 60%, etc.
      const weight = Math.max(1 - (i * 0.2), 0.1);
      score += weights[i] * weight;
    }

    return Math.min(Math.round(score), 100);
  }

  private groupByCategory(scoredRisks: ScoredRisk[]): { [category: string]: number } {
    return scoredRisks.reduce((acc, s) => {
      const category = s.risk.typeId.split("_")[0]; // Simple categorization
      acc[category] = (acc[category] || 0) + s.score.score;
      return acc;
    }, {} as { [category: string]: number });
  }

  private groupBySeverity(scoredRisks: ScoredRisk[]): SeverityCount {
    return scoredRisks.reduce((acc, s) => {
      acc[s.score.severity]++;
      return acc;
    }, { low: 0, medium: 0, high: 0, critical: 0 });
  }

  private determineOverallRisk(
    score: number,
    bySeverity: SeverityCount
  ): "none" | "low" | "medium" | "high" | "critical" {
    if (bySeverity.critical > 0) return "critical";
    if (score >= 75) return "high";
    if (score >= 40) return "medium";
    if (score >= 10) return "low";
    return "none";
  }

  private recommendAction(
    overallRisk: string,
    bySeverity: SeverityCount
  ): "proceed" | "caution" | "review" | "block" {
    if (bySeverity.critical > 0) return "block";
    if (overallRisk === "high") return "review";
    if (overallRisk === "medium") return "caution";
    return "proceed";
  }

  private getTopRisks(scoredRisks: ScoredRisk[], limit: number): DetectedRisk[] {
    return scoredRisks
      .sort((a, b) => b.score.score - a.score.score)
      .slice(0, limit)
      .map(s => s.risk);
  }
}

interface RiskScore {
  score: number;                  // 0-100
  severity: "low" | "medium" | "high" | "critical";
  confidence: number;             // 0-1
  factors: {
    severity: number;
    likelihood: number;
    impact: number;
  };
}

interface RiskAssessment {
  overallRisk: "none" | "low" | "medium" | "high" | "critical";
  totalScore: number;             // 0-100
  riskCount: number;
  byCategory: { [category: string]: number };
  bySeverity: SeverityCount;
  recommendedAction: "proceed" | "caution" | "review" | "block";
  topRisks: DetectedRisk[];
}

interface SeverityCount {
  low: number;
  medium: number;
  high: number;
  critical: number;
}

interface ScoredRisk {
  risk: DetectedRisk;
  score: RiskScore;
}
```

### 4.2 Context-Aware Scoring

```typescript
/**
 * Context-Aware Risk Scoring
 */

class ContextAwareScorer {
  /**
   * Adjust risk score based on context
   */
  adjustForContext(
    risk: DetectedRisk,
    context: CheckContext
  ): DetectedRisk {
    let adjusted = { ...risk };

    // Adjust based on customer tier
    adjusted = this.adjustForCustomerTier(adjusted, context.customer);

    // Adjust based on agent experience
    adjusted = this.adjustForAgentExperience(adjusted, context.agent);

    // Adjust based on trip stage
    adjusted = this.adjustForTripStage(adjusted, context.stage);

    // Adjust based on agency risk tolerance
    adjusted = this.adjustForAgencyTolerance(adjusted, context.agency);

    return adjusted;
  }

  private adjustForCustomerTier(
    risk: DetectedRisk,
    customer: Customer
  ): DetectedRisk {
    // VIP customers get higher severity (protect reputation)
    if (customer.tier === "VIP") {
      risk.likelihood = Math.min(risk.likelihood + 10, 100);
    }
    // New customers get slightly lower severity (more forgiveness)
    else if (customer.isNew) {
      risk.likelihood = Math.max(risk.likelihood - 5, 0);
    }

    return risk;
  }

  private adjustForAgentExperience(
    risk: DetectedRisk,
    agent: Agent
  ): DetectedRisk {
    // Experienced agents can handle more risk
    const experience = agent.experienceYears || 0;

    if (experience >= 5) {
      // Reduce severity for non-critical risks
      if (risk.severity !== "critical") {
        risk.likelihood = Math.max(risk.likelihood - 10, 0);
      }
    } else if (experience < 1) {
      // Increase severity for new agents
      risk.likelihood = Math.min(risk.likelihood + 15, 100);
    }

    return risk;
  }

  private adjustForTripStage(
    risk: DetectedRisk,
    stage: TripStage
  ): DetectedRisk {
    // Earlier stages = more flexibility to fix issues
    if (stage === "inquiry" || stage === "quoting") {
      risk.likelihood = Math.max(risk.likelihood - 10, 0);
    }
    // Later stages = less flexibility
    else if (stage === "booking") {
      risk.likelihood = Math.min(risk.likelihood + 10, 100);
    }

    return risk;
  }

  private adjustForAgencyTolerance(
    risk: DetectedRisk,
    agency: Agency
  ): DetectedRisk {
    const tolerance = agency.riskTolerance || "medium";

    const toleranceAdjustment = {
      low: 20,      // Lower severity for risk-tolerant agencies
      medium: 0,
      high: -20     // Higher severity for risk-averse agencies
    };

    risk.likelihood = Math.max(
      Math.min(risk.likelihood + toleranceAdjustment[tolerance], 100),
      0
    );

    return risk;
  }
}
```

---

## 5. Budget Validation System

### 5.1 Budget Rule Engine

```typescript
/**
 * Budget Validation Engine
 */

class BudgetValidator {
  private rules: BudgetRule[];

  constructor(rules: BudgetRule[]) {
    this.rules = rules.sort((a, b) => b.priority - a.priority);
  }

  /**
   * Validate budget constraints
   */
  async validate(
    quote: Quote,
    packet: TripPacket
  ): Promise<BudgetValidationResult> {
    const results: BudgetCheck[] = [];

    for (const rule of this.rules) {
      if (!rule.enabled) continue;

      const result = await this.checkRule(rule, quote, packet);
      results.push(result);
    }

    return this.aggregateResults(results);
  }

  private async checkRule(
    rule: BudgetRule,
    quote: Quote,
    packet: TripPacket
  ): Promise<BudgetCheck> {
    const totalCost = quote.totalPrice;
    const budget = packet.budget?.total;

    // Get budget threshold
    const threshold = this.getThreshold(rule, packet);

    // Check condition
    const passed = this.evaluateCondition(rule.condition, {
      totalCost,
      budget,
      threshold
    });

    return {
      ruleId: rule.id,
      ruleName: rule.name,
      passed,
      severity: rule.severity,
      details: {
        totalCost,
        budget,
        threshold,
        overBudget: budget ? totalCost - budget : null,
        overPercentage: budget ? ((totalCost - budget) / budget) * 100 : null
      },
      message: this.generateMessage(rule, passed, totalCost, budget, threshold)
    };
  }

  private getThreshold(rule: BudgetRule, packet: TripPacket): number {
    // Dynamic threshold based on rule configuration
    if (rule.thresholdType === "fixed") {
      return rule.thresholdValue;
    } else if (rule.thresholdType === "percentage") {
      return (packet.budget?.total || 0) * (rule.thresholdValue / 100);
    } else if (rule.thresholdType === "flexible") {
      // Flexible budget allows some overrun
      return (packet.budget?.total || 0) * 1.1; // 10% flexibility
    }
    return rule.thresholdValue;
  }

  private evaluateCondition(
    condition: string,
    values: any
  ): boolean {
    // Simple condition evaluation
    // In production, use a proper expression parser
    if (condition === "total_cost <= budget") {
      return values.totalCost <= values.budget;
    } else if (condition === "total_cost <= threshold") {
      return values.totalCost <= values.threshold;
    } else if (condition === "over_percentage <= 10") {
      return (values.overPercentage || 0) <= 10;
    }
    return true;
  }

  private generateMessage(
    rule: BudgetRule,
    passed: boolean,
    totalCost: number,
    budget: number | undefined,
    threshold: number
  ): string {
    if (passed) {
      return `Within ${rule.name} limit (₹${totalCost.toLocaleString()} ≤ ₹${threshold.toLocaleString()})`;
    }

    const over = budget ? totalCost - budget : 0;
    const overPct = budget ? ((over / budget) * 100).toFixed(1) : "0";

    return `Over ${rule.name} by ₹${over.toLocaleString()} (${overPct}%)`;
  }

  private aggregateResults(results: BudgetCheck[]): BudgetValidationResult {
    const failed = results.filter(r => !r.passed);
    const criticalFailed = failed.filter(r => r.severity === "critical");

    return {
      valid: criticalFailed.length === 0,
      checks: results,
      summary: {
        total: results.length,
        passed: results.filter(r => r.passed).length,
        failed: failed.length,
        critical: criticalFailed.length
      },
      canOverride: criticalFailed.length === 0 && failed.length > 0,
      requiredApproval: criticalFailed.length > 0
    };
  }
}

interface BudgetRule {
  id: string;
  name: string;
  enabled: boolean;
  priority: number;
  severity: "low" | "medium" | "high" | "critical";
  condition: string;
  thresholdType: "fixed" | "percentage" | "flexible";
  thresholdValue: number;
}

interface BudgetCheck {
  ruleId: string;
  ruleName: string;
  passed: boolean;
  severity: "low" | "medium" | "high" | "critical";
  details: {
    totalCost: number;
    budget?: number;
    threshold: number;
    overBudget: number | null;
    overPercentage: number | null;
  };
  message: string;
}

interface BudgetValidationResult {
  valid: boolean;
  checks: BudgetCheck[];
  summary: {
    total: number;
    passed: number;
    failed: number;
    critical: number;
  };
  canOverride: boolean;
  requiredApproval: boolean;
}
```

### 5.2 Budget Risk Detection

```typescript
/**
 * Budget Risk Detection
 */

class BudgetRiskDetector {
  /**
   * Detect budget-related risks
   */
  async detect(quote: Quote, packet: TripPacket): Promise<DetectedRisk[]> {
    const risks: DetectedRisk[] = [];

    // Risk 1: Quote exceeds budget
    if (packet.budget?.total && quote.totalPrice > packet.budget.total) {
      risks.push({
        typeId: "budget_overrun",
        severity: this.getOverrunSeverity(quote, packet),
        likelihood: 100,  // Certain if over budget
        impact: this.calculateOverrunImpact(quote, packet),
        score: 0,  // Calculated by scorer
        details: {
          description: "Quote exceeds customer budget",
          affectedField: "budget.total",
          currentValue: quote.totalPrice,
          threshold: packet.budget.total,
          recommendation: "Discuss budget increase or itinerary adjustments"
        },
        suggestedActions: [
          "Adjust itinerary to fit budget",
          "Propose budget increase",
          "Offer alternative dates/destinations"
        ],
        canOverride: true,
        requiresApproval: false
      });
    }

    // Risk 2: Budget too tight for destination
    const tightnessRisk = await this.checkBudgetTightness(quote, packet);
    if (tightnessRisk) risks.push(tightnessRisk);

    // Risk 3: Hidden costs not accounted for
    const hiddenCostsRisk = await this.checkHiddenCosts(quote, packet);
    if (hiddenCostsRisk) risks.push(hiddenCostsRisk);

    // Risk 4: Payment timing risk
    const paymentRisk = await this.checkPaymentTiming(quote, packet);
    if (paymentRisk) risks.push(paymentRisk);

    return risks;
  }

  private getOverrunSeverity(quote: Quote, packet: TripPacket): "low" | "medium" | "high" | "critical" {
    if (!packet.budget?.total) return "medium";

    const overrunPct = ((quote.totalPrice - packet.budget.total) / packet.budget.total) * 100;

    if (overrunPct > 25) return "critical";
    if (overrunPct > 15) return "high";
    if (overrunPct > 5) return "medium";
    return "low";
  }

  private calculateOverrunImpact(quote: Quote, packet: TripPacket): number {
    // Impact based on customer tier and trip importance
    let impact = 50;

    if (packet.customer?.tier === "VIP") impact += 20;
    if (packet.tripType === "honeymoon") impact += 15;
    if (packet.destination?.international) impact += 10;

    return Math.min(impact, 100);
  }

  private async checkBudgetTightness(
    quote: Quote,
    packet: TripPacket
  ): Promise<DetectedRisk | null> {
    // Check if budget is unrealistically low for destination/trip type
    const expectedCost = await this.getExpectedCost(packet);
    const budget = packet.budget?.total || quote.totalPrice;

    if (budget < expectedCost * 0.7) {
      return {
        typeId: "budget_tightness",
        severity: "high",
        likelihood: 80,
        impact: 70,
        score: 0,
        details: {
          description: "Budget appears tight for requested destination and activities",
          affectedField: "budget.total",
          currentValue: budget,
          threshold: expectedCost,
          recommendation: "Set expectations or suggest alternatives"
        },
        suggestedActions: [
          "Discuss realistic budget requirements",
          "Suggest alternative destinations",
          "Adjust trip scope/activities"
        ],
        canOverride: true,
        requiresApproval: false
      };
    }

    return null;
  }

  private async checkHiddenCosts(
    quote: Quote,
    packet: TripPacket
  ): Promise<DetectedRisk | null> {
    // Check for common hidden costs
    const hiddenCosts = [
      { name: "Visa fees", estimated: 5000 },
      { name: "Travel insurance", estimated: 3000 },
      { name: "Local transport", estimated: 10000 },
      { name: "Meals not included", estimated: 15000 }
    ];

    const totalHidden = hiddenCosts.reduce((sum, c) => sum + c.estimated, 0);
    const buffer = packet.budget?.total ? packet.budget.total * 0.1 : 0;

    if (totalHidden > buffer) {
      return {
        typeId: "hidden_costs",
        severity: "medium",
        likelihood: 70,
        impact: 50,
        score: 0,
        details: {
          description: "Potential hidden costs not included in quote",
          currentValue: totalHidden,
          recommendation: "Inform customer about additional expenses"
        },
        suggestedActions: [
          "Add hidden costs to quote",
          "Create separate estimate for exclusions",
          "Document what's included clearly"
        ],
        canOverride: true,
        requiresApproval: false
      };
    }

    return null;
  }

  private async checkPaymentTiming(
    quote: Quote,
    packet: TripPacket
  ): Promise<DetectedRisk | null> {
    // Check if payment deadlines are reasonable
    const now = new Date();
    const departure = packet.dates?.departure;

    if (!departure) return null;

    const daysToDeparture = Math.floor((departure.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));

    // If departure is soon and full payment required
    if (daysToDeparture < 30 && quote.paymentTerms?.fullPaymentBefore) {
      const paymentDeadline = new Date(quote.paymentTerms.fullPaymentBefore);
      const daysToPayment = Math.floor((paymentDeadline.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));

      if (daysToPayment < 7) {
        return {
          typeId: "payment_timing",
          severity: "high",
          likelihood: 60,
          impact: 80,
          score: 0,
          details: {
            description: "Payment deadline very close to departure",
            currentValue: daysToPayment,
            recommendation: "Expedite payment process or negotiate terms"
          },
          suggestedActions: [
            "Collect payment immediately",
            "Negotiate extended payment terms",
            "Consider payment plan"
          ],
          canOverride: false,
          requiresApproval: true
        };
      }
    }

    return null;
  }

  private async getExpectedCost(packet: TripPacket): Promise<number> {
    // Get expected cost based on destination, duration, trip type
    // This would typically come from a pricing database
    return 100000;  // Placeholder
  }
}
```

---

## 6. Compliance Checking

### 6.1 GST Compliance Checker

```typescript
/**
 * GST Compliance Checker
 */

class GSTComplianceChecker {
  /**
   * Check GST compliance
   */
  async check(quote: Quote, packet: TripPacket): Promise<DetectedRisk[]> {
    const risks: DetectedRisk[] = [];

    // Check 1: GSTIN validity
    const gstinRisk = await this.checkGSTIN(packet);
    if (gstinRisk) risks.push(gstinRisk);

    // Check 2: GST calculation accuracy
    const calculationRisk = await this.checkGSTCalculation(quote);
    if (calculationRisk) risks.push(calculationRisk);

    // Check 3: GST invoice requirements
    const invoiceRisk = await this.checkInvoiceRequirements(quote, packet);
    if (invoiceRisk) risks.push(invoiceRisk);

    // Check 4: GST registration threshold
    const thresholdRisk = await this.checkRegistrationThreshold(packet);
    if (thresholdRisk) risks.push(thresholdRisk);

    return risks;
  }

  private async checkGSTIN(packet: TripPacket): Promise<DetectedRisk | null> {
    const gstin = packet.customer?.gstin;

    if (!gstin) {
      // No GSTIN provided - check if needed
      const totalValue = packet.budget?.total || 0;

      if (totalValue > 40000) {  // Threshold for requiring GSTIN
        return {
          typeId: "gst_compliance",
          severity: "medium",
          likelihood: 80,
          impact: 60,
          score: 0,
          details: {
            description: "Customer GSTIN not provided for high-value booking",
            affectedField: "customer.gstin",
            currentValue: null,
            recommendation: "Collect GSTIN for invoice and tax purposes"
          },
          suggestedActions: [
            "Request customer GSTIN",
            "Verify GSTIN format",
            "Explain GST benefits to customer"
          ],
          canOverride: true,
          requiresApproval: false
        };
      }
    } else {
      // Validate GSTIN format
      const isValid = this.validateGSTINFormat(gstin);
      if (!isValid) {
        return {
          typeId: "gst_compliance",
          severity: "high",
          likelihood: 100,
          impact: 70,
          score: 0,
          details: {
            description: "Invalid GSTIN format",
            affectedField: "customer.gstin",
            currentValue: gstin,
            recommendation: "Verify and correct GSTIN"
          },
          suggestedActions: [
            "Verify GSTIN with customer",
            "Check against GST portal",
            "Correct GSTIN before invoicing"
          ],
          canOverride: false,
          requiresApproval: true
        };
      }
    }

    return null;
  }

  private async checkGSTCalculation(quote: Quote): Promise<DetectedRisk | null> {
    // Verify GST calculation
    const taxableValue = quote.taxableValue || quote.totalPrice;
    const expectedGST = taxableValue * 0.18;  // 18% GST (typical)
    const actualGST = quote.taxes?.gst || 0;

    const variance = Math.abs(expectedGST - actualGST);
    const variancePct = (variance / expectedGST) * 100;

    if (variancePct > 5) {
      return {
        typeId: "gst_compliance",
        severity: "high",
        likelihood: 90,
        impact: 80,
        score: 0,
        details: {
          description: `GST calculation variance: ${variancePct.toFixed(1)}%`,
          affectedField: "taxes.gst",
          currentValue: actualGST,
          threshold: expectedGST,
          recommendation: "Review and correct GST calculation"
        },
        suggestedActions: [
          "Verify GST rate applied",
          "Check taxable value calculation",
          "Recalculate GST before invoicing"
        ],
        canOverride: false,
        requiresApproval: true
      };
    }

    return null;
  }

  private async checkInvoiceRequirements(
    quote: Quote,
    packet: TripPacket
  ): Promise<DetectedRisk | null> {
    const requirements: string[] = [];

    // Check for required invoice fields
    if (!packet.customer?.name) requirements.push("Customer name");
    if (!packet.customer?.address) requirements.push("Customer address");
    if (!packet.customer?.phone) requirements.push("Customer phone");

    if (requirements.length > 0) {
      return {
        typeId: "gst_compliance",
        severity: "medium",
        likelihood: 100,
        impact: 50,
        score: 0,
        details: {
          description: "Missing required GST invoice information",
          recommendation: `Collect: ${requirements.join(", ")}`
        },
        suggestedActions: [
          "Request missing customer details",
          "Verify address format",
          "Ensure all fields are complete"
        ],
        canOverride: true,
        requiresApproval: false
      };
    }

    return null;
  }

  private async checkRegistrationThreshold(packet: TripPacket): Promise<DetectedRisk | null> {
    // Check if agency registration threshold is at risk
    const agencyTurnover = packet.agency?.annualTurnover || 0;
    const currentBooking = packet.budget?.total || 0;

    if (agencyTurnover + currentBooking > 4000000) {  // ₹40L threshold
      return {
        typeId: "gst_compliance",
        severity: "low",
        likelihood: 60,
        impact: 70,
        score: 0,
        details: {
          description: "Approaching GST registration threshold",
          currentValue: agencyTurnover + currentBooking,
          threshold: 4000000,
          recommendation: "Plan for GST registration if not already registered"
        },
        suggestedActions: [
          "Review GST registration status",
          "Plan for registration if needed",
          "Track turnover accurately"
        ],
        canOverride: true,
        requiresApproval: false
      };
    }

    return null;
  }

  private validateGSTINFormat(gstin: string): boolean {
    // GSTIN format: 22AAAAA0000A1Z5
    // 22 characters, alphanumeric, specific pattern
    const pattern = /^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$/;
    return pattern.test(gstin);
  }
}
```

### 6.2 TCS Compliance Checker

```typescript
/**
 * TCS Compliance Checker
 */

class TCSComplianceChecker {
  /**
   * Check TCS compliance
   */
  async check(quote: Quote, packet: TripPacket): Promise<DetectedRisk[]> {
    const risks: DetectedRisk[] = [];

    // Check 1: TCS applicability
    const applicabilityRisk = await this.checkTCSApplicability(quote, packet);
    if (applicabilityRisk) risks.push(applicabilityRisk);

    // Check 2: PAN requirement
    const panRisk = await this.checkPANRequirement(packet);
    if (panRisk) risks.push(panRisk);

    // Check 3: TCS calculation
    const calculationRisk = await this.checkTCSCalculation(quote);
    if (calculationRisk) risks.push(calculationRisk);

    // Check 4: TCS credit eligibility
    const creditRisk = await this.checkTCSCreditEligibility(packet);
    if (creditRisk) risks.push(creditRisk);

    return risks;
  }

  private async checkTCSApplicability(
    quote: Quote,
    packet: TripPacket
  ): Promise<DetectedRisk | null> {
    // TCS applies to international travel packages > ₹7L
    const isInternational = packet.destination?.international;
    const packageCost = quote.totalPrice;
    const threshold = 700000;

    if (isInternational && packageCost > threshold) {
      const tcsRate = 0.20;  // 20% TCS
      const expectedTCS = (packageCost - threshold) * tcsRate;
      const actualTCS = quote.taxes?.tcs || 0;

      if (actualTCS < expectedTCS * 0.9) {
        return {
          typeId: "tcs_compliance",
          severity: "high",
          likelihood: 100,
          impact: 80,
          score: 0,
          details: {
            description: "TCS not correctly calculated for international package",
            affectedField: "taxes.tcs",
            currentValue: actualTCS,
            threshold: expectedTCS,
            recommendation: `Apply TCS of ₹${expectedTCS.toLocaleString()}`
          },
          suggestedActions: [
            "Calculate TCS on amount exceeding ₹7L",
            "Collect PAN card for TCS credit",
            "Inform customer about TCS credit process"
          ],
          canOverride: false,
          requiresApproval: true
        };
      }
    }

    return null;
  }

  private async checkPANRequirement(packet: TripPacket): Promise<DetectedRisk | null> {
    // PAN required for TCS credit
    const isInternational = packet.destination?.international;
    const packageCost = packet.budget?.total || 0;

    if (isInternational && packageCost > 700000) {
      if (!packet.customer?.pan) {
        return {
          typeId: "tcs_compliance",
          severity: "high",
          likelihood: 100,
          impact: 70,
          score: 0,
          details: {
            description: "PAN card required for TCS credit",
            affectedField: "customer.pan",
            recommendation: "Collect customer PAN for TCS credit eligibility"
          },
          suggestedActions: [
            "Request customer PAN card",
            "Verify PAN format",
            "Explain TCS credit benefit"
          ],
          canOverride: false,
          requiresApproval: true
        };
      }
    }

    return null;
  }

  private async checkTCSCalculation(quote: Quote): Promise<DetectedRisk | null> {
    // Verify TCS calculation if applicable
    const tcs = quote.taxes?.tcs || 0;

    if (tcs > 0) {
      const packageCost = quote.totalPrice;
      const threshold = 700000;
      const taxableAmount = Math.max(packageCost - threshold, 0);
      const expectedTCS = taxableAmount * 0.20;

      const variance = Math.abs(expectedTCS - tcs);
      const variancePct = (variance / expectedTCS) * 100;

      if (variancePct > 1) {  // TCS calculation should be precise
        return {
          typeId: "tcs_compliance",
          severity: "high",
          likelihood: 95,
          impact: 75,
          score: 0,
          details: {
            description: "TCS calculation appears incorrect",
            affectedField: "taxes.tcs",
            currentValue: tcs,
            threshold: expectedTCS,
            recommendation: "Verify TCS calculation formula"
          },
          suggestedActions: [
            "Review TCS calculation",
            "Verify taxable amount",
            "Correct before invoicing"
          ],
          canOverride: false,
          requiresApproval: true
        };
      }
    }

    return null;
  }

  private async checkTCSCreditEligibility(packet: TripPacket): Promise<DetectedRisk | null> {
    // Check if customer can claim TCS credit
    if (packet.customer?.pan && packet.destination?.international) {
      const packageCost = packet.budget?.total || 0;

      if (packageCost > 700000) {
        // Customer should be informed about TCS credit
        return {
          typeId: "tcs_compliance",
          severity: "low",
          likelihood: 100,
          impact: 40,
          score: 0,
          details: {
            description: "Customer eligible for TCS credit",
            recommendation: "Inform customer about TCS credit while filing tax returns"
          },
          suggestedActions: [
            "Explain TCS credit process",
            "Provide TCS certificate",
            "Include in booking documents"
          ],
          canOverride: true,
          requiresApproval: false
        };
      }
    }

    return null;
  }
}
```

---

## 7. Safety Nets & Guardrails

### 7.1 Action Blocking

```typescript
/**
 * Safety Net - Action Blocking
 */

class SafetyNet {
  /**
   * Check if action should be blocked
   */
  async shouldBlock(
    action: ProtectedAction,
    context: CheckContext
  ): Promise<BlockResult> {
    // Get risk assessment
    const assessment = await this.assessRisks(action, context);

    // Block if critical risks and not overridden
    if (assessment.hasCriticalRisks && !this.canOverride(context)) {
      return {
        blocked: true,
        reason: "Critical risks detected",
        risks: assessment.criticalRisks,
        resolution: "Resolve critical risks or get owner approval"
      };
    }

    // Block if compliance violations
    if (assessment.hasComplianceViolations) {
      return {
        blocked: true,
        reason: "Compliance violations detected",
        risks: assessment.complianceRisks,
        resolution: "Resolve compliance issues before proceeding"
      };
    }

    return {
      blocked: false,
      warnings: assessment.nonCriticalRisks
    };
  }

  private async assessRisks(
    action: ProtectedAction,
    context: CheckContext
  ): Promise<RiskAssessmentResult> {
    // Run risk checks based on action type
    const checks = this.getChecksForAction(action);

    const results = await Promise.all(
      checks.map(check => check.execute(context))
    );

    const allRisks = results.flatMap(r => r.risks);

    return {
      hasCriticalRisks: allRisks.some(r => r.severity === "critical"),
      hasComplianceViolations: allRisks.some(r =>
        r.typeId.startsWith("gst_") || r.typeId.startsWith("tcs_")
      ),
      criticalRisks: allRisks.filter(r => r.severity === "critical"),
      complianceRisks: allRisks.filter(r =>
        r.typeId.startsWith("gst_") || r.typeId.startsWith("tcs_")
      ),
      nonCriticalRisks: allRisks.filter(r =>
        r.severity !== "critical" &&
        !r.typeId.startsWith("gst_") &&
        !r.typeId.startsWith("tcs_")
      )
    };
  }

  private canOverride(context: CheckContext): boolean {
    // Owner can override
    if (context.agent.role === "owner") return true;

    // Senior agents can override non-compliance risks
    if (context.agent.experienceYears >= 5) return true;

    return false;
  }

  private getChecksForAction(action: ProtectedAction): RiskCheck[] {
    // Return relevant checks for the action
    return [];
  }
}

type ProtectedAction =
  | "create_quote"
  | "confirm_booking"
  | "collect_payment"
  | "issue_refund"
  | "cancel_booking"
  | "modify_booking";

interface BlockResult {
  blocked: boolean;
  reason?: string;
  risks?: DetectedRisk[];
  resolution?: string;
  warnings?: DetectedRisk[];
}

interface RiskAssessmentResult {
  hasCriticalRisks: boolean;
  hasComplianceViolations: boolean;
  criticalRisks: DetectedRisk[];
  complianceRisks: DetectedRisk[];
  nonCriticalRisks: DetectedRisk[];
}
```

### 7.2 Confirmation Flows

```typescript
/**
 * Confirmation Flow for Risky Actions
 */

class ConfirmationFlow {
  /**
   * Get confirmation requirements for action
   */
  getConfirmation(
    action: ProtectedAction,
    risks: DetectedRisk[]
  ): ConfirmationRequirement {
    // Determine if confirmation is needed
    const needsConfirmation = risks.length > 0 ||
      this.isHighValueAction(action) ||
      this.isIrreversibleAction(action);

    if (!needsConfirmation) {
      return { required: false };
    }

    // Group risks by severity
    const criticalRisks = risks.filter(r => r.severity === "critical");
    const highRisks = risks.filter(r => r.severity === "high");
    const otherRisks = risks.filter(r => r.severity !== "critical" && r.severity !== "high");

    return {
      required: true,
      level: criticalRisks.length > 0 ? "owner_approval" :
             highRisks.length > 0 ? "explicit_confirmation" :
             "acknowledgement",
      message: this.generateConfirmationMessage(action, risks),
      risks: {
        critical: criticalRisks,
        high: highRisks,
        other: otherRisks
      },
      checkboxes: this.generateCheckboxes(risks),
      warnings: this.generateWarnings(risks)
    };
  }

  private generateConfirmationMessage(
    action: ProtectedAction,
    risks: DetectedRisk[]
  ): string {
    const criticalCount = risks.filter(r => r.severity === "critical").length;
    const highCount = risks.filter(r => r.severity === "high").length;

    if (criticalCount > 0) {
      return `This ${action} has ${criticalCount} critical risk${criticalCount > 1 ? 's' : ''} that require owner approval.`;
    }

    if (highCount > 0) {
      return `This ${action} has ${highCount} high-severity risk${highCount > 1 ? 's' : ''}. Please review before proceeding.`;
    }

    return `This ${action} has ${risks.length} risk${risks.length > 1 ? 's' : ''}. Please acknowledge to continue.`;
  }

  private generateCheckboxes(risks: DetectedRisk[]): ConfirmationCheckbox[] {
    return risks.map(risk => ({
      id: `ack_${risk.typeId}`,
      label: `I understand: ${risk.details.description}`,
      required: risk.severity === "critical" || risk.severity === "high"
    }));
  }

  private generateWarnings(risks: DetectedRisk[]): string[] {
    return risks
      .filter(r => r.severity === "high" || r.severity === "critical")
      .map(r => r.details.recommendation || "");
  }

  private isHighValueAction(action: ProtectedAction): boolean {
    return action === "confirm_booking" || action === "collect_payment";
  }

  private isIrreversibleAction(action: ProtectedAction): boolean {
    return action === "confirm_booking" || action === "cancel_booking";
  }
}

interface ConfirmationRequirement {
  required: boolean;
  level?: "acknowledgement" | "explicit_confirmation" | "owner_approval";
  message?: string;
  risks?: {
    critical: DetectedRisk[];
    high: DetectedRisk[];
    other: DetectedRisk[];
  };
  checkboxes?: ConfirmationCheckbox[];
  warnings?: string[];
}

interface ConfirmationCheckbox {
  id: string;
  label: string;
  required: boolean;
}
```

---

## 8. Alert & Notification System

### 8.1 Alert Configuration

```typescript
/**
 * Alert Configuration
 */

interface AlertRule {
  id: string;
  name: string;
  enabled: boolean;

  trigger: AlertTrigger;
  conditions: AlertCondition[];

  actions: AlertAction[];
  escalation?: AlertEscalation;
}

interface AlertTrigger {
  eventType: string;
  riskType?: string;
  severity?: RiskSeverity;
}

interface AlertCondition {
  field: string;
  operator: "gt" | "lt" | "eq" | "gte" | "lte";
  value: any;
}

interface AlertAction {
  type: "email" | "slack" | "in_app" | "sms";
  recipients: string[];
  template: string;
  priority: "low" | "medium" | "high" | "urgent";
}

interface AlertEscalation {
  steps: {
    delay: number;              // minutes
    actions: AlertAction[];
  }[];
}

// Example alert rules
const SAFETY_ALERT_RULES: AlertRule[] = [
  // Critical risk detected
  {
    id: "critical_risk_alert",
    name: "Critical Risk Detected",
    enabled: true,
    trigger: {
      eventType: "risk_detected",
      severity: "critical"
    },
    conditions: [],
    actions: [
      {
        type: "in_app",
        recipients: ["agent", "owner"],
        template: "critical_risk_detected",
        priority: "urgent"
      },
      {
        type: "slack",
        recipients: ["#operations"],
        template: "critical_risk_slack",
        priority: "urgent"
      }
    ],
    escalation: {
      steps: [
        {
          delay: 15,
          actions: [
            {
              type: "sms",
              recipients: ["owner"],
              template: "critical_risk_escalation",
              priority: "urgent"
            }
          ]
        }
      ]
    }
  },

  // Budget overrun warning
  {
    id: "budget_overrun_alert",
    name: "Budget Overrun Warning",
    enabled: true,
    trigger: {
      eventType: "risk_detected",
      riskType: "budget_overrun"
    },
    conditions: [
      { field: "severity", operator: "gte", value: "high" }
    ],
    actions: [
      {
        type: "in_app",
        recipients: ["agent"],
        template: "budget_overrun_warning",
        priority: "high"
      }
    ]
  },

  // Compliance violation
  {
    id: "compliance_violation_alert",
    name: "Compliance Violation",
    enabled: true,
    trigger: {
      eventType: "risk_detected",
      riskType: ["gst_compliance", "tcs_compliance"]
    },
    conditions: [],
    actions: [
      {
        type: "in_app",
        recipients: ["agent", "owner"],
        template: "compliance_violation",
        priority: "urgent"
      },
      {
        type: "email",
        recipients: ["owner", "compliance@agency.com"],
        template: "compliance_violation_email",
        priority: "high"
      }
    ]
  }
];
```

### 8.2 Alert Delivery

```typescript
/**
 * Alert Delivery Service
 */

class AlertDeliveryService {
  private channels: Map<string, AlertChannel> = new Map();

  constructor() {
    this.channels.set("email", new EmailChannel());
    this.channels.set("slack", new SlackChannel());
    this.channels.set("in_app", new InAppChannel());
    this.channels.set("sms", new SMSChannel());
  }

  /**
   * Send alert based on rule
   */
  async sendAlert(
    rule: AlertRule,
    context: AlertContext
  ): Promise<void> {
    for (const action of rule.actions) {
      const channel = this.channels.get(action.type);
      if (!channel) continue;

      const message = this.renderMessage(action.template, context);

      await channel.send({
        recipients: action.recipients,
        message,
        priority: action.priority
      });
    }
  }

  /**
   * Escalate alert if not resolved
   */
  async escalate(
    rule: AlertRule,
    step: number,
    context: AlertContext
  ): Promise<void> {
    const escalation = rule.escalation;
    if (!escalation || step >= escalation.steps.length) return;

    const escalationStep = escalation.steps[step];

    for (const action of escalationStep.actions) {
      const channel = this.channels.get(action.type);
      if (!channel) continue;

      const message = this.renderMessage(action.template, {
        ...context,
        escalation: true,
        escalationStep: step + 1
      });

      await channel.send({
        recipients: action.recipients,
        message,
        priority: "urgent"
      });
    }
  }

  private renderMessage(template: string, context: AlertContext): string {
    // Template rendering implementation
    return template;
  }
}

interface AlertChannel {
  send(params: { recipients: string[]; message: string; priority: string }): Promise<void>;
}

interface AlertContext {
  packetId: string;
  risk: DetectedRisk;
  agent: Agent;
  escalation?: boolean;
  escalationStep?: number;
  [key: string]: any;
}
```

---

## 9. Risk Resolution Workflows

### 9.1 Resolution Tracking

```typescript
/**
 * Risk Resolution Tracking
 */

class RiskResolutionTracker {
  /**
   * Track risk resolution
   */
  async trackResolution(
    risk: DetectedRisk,
    packetId: string
  ): Promise<ResolutionTracker> {
    const tracker: ResolutionTracker = {
      riskId: this.generateRiskId(risk, packetId),
      packetId,
      risk,
      status: "open",
      createdAt: new Date(),
      history: [],
      actions: this.generateSuggestedActions(risk)
    };

    await this.save(tracker);

    return tracker;
  }

  /**
   * Update resolution status
   */
  async updateStatus(
    riskId: string,
    status: ResolutionStatus,
    note?: string,
    agentId?: string
  ): Promise<void> {
    const tracker = await this.get(riskId);
    if (!tracker) return;

    tracker.status = status;
    tracker.statusHistory.push({
      status,
      timestamp: new Date(),
      agentId,
      note
    });

    if (status === "resolved") {
      tracker.resolvedAt = new Date();
      tracker.resolvedBy = agentId;
    }

    await this.save(tracker);
  }

  /**
   * Get open risks for agent
   */
  async getOpenRisks(agentId: string): Promise<ResolutionTracker[]> {
    const all = await this.getAll();
    return all.filter(t =>
      t.status === "open" &&
      t.assignedTo === agentId
    );
  }

  /**
   * Get overdue risks
   */
  async getOverdueRisks(): Promise<ResolutionTracker[]> {
    const all = await this.getAll();
    const now = new Date();

    return all.filter(t =>
      t.status === "open" &&
      t.dueAt &&
      t.dueAt < now
    );
  }

  private generateSuggestedActions(risk: DetectedRisk): ResolutionAction[] {
    return risk.suggestedActions.map((action, i) => ({
      id: `action_${i}`,
      description: action,
      completed: false,
      completedAt: null,
      completedBy: null
    }));
  }

  private generateRiskId(risk: DetectedRisk, packetId: string): string {
    return `${packetId}_${risk.typeId}_${Date.now()}`;
  }

  private async save(tracker: ResolutionTracker): Promise<void> {
    // Save to database
  }

  private async get(riskId: string): Promise<ResolutionTracker | null> {
    // Get from database
    return null;
  }

  private async getAll(): Promise<ResolutionTracker[]> {
    // Get all from database
    return [];
  }
}

interface ResolutionTracker {
  riskId: string;
  packetId: string;
  risk: DetectedRisk;
  status: ResolutionStatus;
  createdAt: Date;
  resolvedAt?: Date;
  resolvedBy?: string;
  dueAt?: Date;
  assignedTo?: string;
  statusHistory: StatusChange[];
  actions: ResolutionAction[];
}

type ResolutionStatus =
  | "open"
  | "in_progress"
  | "awaiting_approval"
  | "resolved"
  | "escalated"
  | "dismissed";

interface StatusChange {
  status: ResolutionStatus;
  timestamp: Date;
  agentId?: string;
  note?: string;
}

interface ResolutionAction {
  id: string;
  description: string;
  completed: boolean;
  completedAt?: Date;
  completedBy?: string;
}
```

### 9.2 Owner Approval Workflow

```typescript
/**
 * Owner Approval Workflow
 */

class OwnerApprovalWorkflow {
  /**
   * Request owner approval for risk
   */
  async requestApproval(
    risk: DetectedRisk,
    packetId: string,
    requestedBy: string
  ): Promise<ApprovalRequest> {
    const request: ApprovalRequest = {
      id: this.generateRequestId(),
      riskId: `${packetId}_${risk.typeId}`,
      packetId,
      risk,
      requestedBy,
      requestedAt: new Date(),
      status: "pending",
      expiresAt: new Date(Date.now() + 24 * 60 * 60 * 1000) // 24 hours
    };

    await this.save(request);

    // Notify owner
    await this.notifyOwner(request);

    return request;
  }

  /**
   * Process approval decision
   */
  async processDecision(
    requestId: string,
    decision: "approved" | "denied",
    decidedBy: string,
    notes?: string
  ): Promise<void> {
    const request = await this.get(requestId);
    if (!request) throw new Error("Request not found");

    if (request.status !== "pending") {
      throw new Error("Request already processed");
    }

    request.status = decision === "approved" ? "approved" : "denied";
    request.decidedBy = decidedBy;
    request.decidedAt = new Date();
    request.notes = notes;

    await this.save(request);

    // Notify requester
    await this.notifyRequester(request);

    // Update risk tracker
    if (decision === "approved") {
      await this.riskTracker.updateStatus(
        request.riskId,
        "resolved",
        `Approved by owner: ${notes}`,
        decidedBy
      );
    } else {
      await this.riskTracker.updateStatus(
        request.riskId,
        "open",
        `Denied by owner: ${notes}`,
        decidedBy
      );
    }
  }

  /**
   * Get pending approvals for owner
   */
  async getPendingApprovals(ownerId: string): Promise<ApprovalRequest[]> {
    const all = await this.getAll();
    return all.filter(r =>
      r.status === "pending" &&
      !this.isExpired(r)
    );
  }

  /**
   * Check for expired approvals
   */
  async checkExpired(): Promise<ApprovalRequest[]> {
    const all = await this.getAll();
    const expired = all.filter(r =>
      r.status === "pending" &&
      this.isExpired(r)
    );

    for (const request of expired) {
      request.status = "expired";
      await this.save(request);
      await this.notifyExpired(request);
    }

    return expired;
  }

  private isExpired(request: ApprovalRequest): boolean {
    return new Date() > request.expiresAt;
  }

  private async notifyOwner(request: ApprovalRequest): Promise<void> {
    // Send notification to owner
  }

  private async notifyRequester(request: ApprovalRequest): Promise<void> {
    // Send notification to requester
  }

  private async notifyExpired(request: ApprovalRequest): Promise<void> {
    // Send notification about expired request
  }

  private generateRequestId(): string {
    return `approval_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private async save(request: ApprovalRequest): Promise<void> {
    // Save to database
  }

  private async get(requestId: string): Promise<ApprovalRequest | null> {
    // Get from database
    return null;
  }

  private async getAll(): Promise<ApprovalRequest[]> {
    // Get all from database
    return [];
  }

  constructor(private riskTracker: RiskResolutionTracker) {}
}

interface ApprovalRequest {
  id: string;
  riskId: string;
  packetId: string;
  risk: DetectedRisk;
  requestedBy: string;
  requestedAt: Date;
  decidedBy?: string;
  decidedAt?: Date;
  status: "pending" | "approved" | "denied" | "expired";
  expiresAt: Date;
  notes?: string;
}
```

---

## 10. Data Model

### 10.1 Risk Storage Schema

```typescript
/**
 * Risk Data Model
 */

interface StoredRisk {
  id: string;
  packetId: string;
  quoteId?: string;
  bookingId?: string;

  // Risk details
  typeId: string;
  category: RiskCategory;
  severity: RiskSeverity;
  score: number;

  // Detection info
  detectedAt: Date;
  detectedBy: string;              // System check ID
  confidence: number;

  // Risk details
  details: {
    description: string;
    affectedField?: string;
    currentValue?: any;
    threshold?: any;
    recommendation?: string;
  };

  // Status
  status: RiskStatus;
  resolvedAt?: Date;
  resolvedBy?: string;
  resolution?: string;

  // Approval
  requiresApproval: boolean;
  approvedBy?: string;
  approvedAt?: Date;

  // Metadata
  agencyId: string;
  metadata: {
    [key: string]: any;
  };
}

type RiskStatus =
  | "open"
  | "acknowledged"
  | "in_progress"
  | "resolved"
  | "escalated"
  | "dismissed";
```

### 10.2 Risk Summary

```typescript
/**
 * Risk Summary for Packet/Quote/Booking
 */

interface RiskSummary {
  // Overall assessment
  overallRisk: "none" | "low" | "medium" | "high" | "critical";
  totalScore: number;
  riskCount: number;

  // Breakdown
  byCategory: {
    [category: string]: {
      count: number;
      maxScore: number;
    };
  };
  bySeverity: {
    low: number;
    medium: number;
    high: number;
    critical: number;
  };

  // Top risks
  topRisks: {
    typeId: string;
    description: string;
    severity: RiskSeverity;
    score: number;
  }[];

  // Action required
  requiresAction: boolean;
  requiresApproval: boolean;
  canProceed: boolean;
  recommendedAction: string;

  // Timestamps
  assessedAt: Date;
  validUntil: Date;
}
```

---

## 11. API Specification

### 11.1 Risk Check Endpoints

```
POST /api/v1/safety/check
```

Check for risks on a packet/quote/booking.

**Request:**
```json
{
  "packetId": "packet_123",
  "quoteId": "quote_456",
  "eventType": "quote_created",
  "context": {
    "stage": "quoting",
    "agentId": "agent_789"
  }
}
```

**Response:**
```json
{
  "assessment": {
    "overallRisk": "medium",
    "totalScore": 45,
    "riskCount": 3,
    "byCategory": {
      "financial": { "count": 2, "maxScore": 65 },
      "compliance": { "count": 1, "maxScore": 50 }
    },
    "bySeverity": {
      "low": 1,
      "medium": 1,
      "high": 1,
      "critical": 0
    },
    "topRisks": [
      {
        "typeId": "budget_overrun",
        "description": "Quote exceeds budget by 12%",
        "severity": "high",
        "score": 65
      }
    ],
    "requiresAction": true,
    "requiresApproval": false,
    "canProceed": true,
    "recommendedAction": "caution"
  },
  "risks": [
    {
      "typeId": "budget_overrun",
      "category": "financial",
      "severity": "high",
      "likelihood": 100,
      "impact": 65,
      "score": 65,
      "details": {
        "description": "Quote exceeds customer budget by 12%",
        "affectedField": "budget.total",
        "currentValue": 112000,
        "threshold": 100000,
        "recommendation": "Discuss budget adjustment or itinerary changes"
      },
      "suggestedActions": [
        "Adjust itinerary to fit budget",
        "Propose budget increase",
        "Offer alternative dates"
      ],
      "canOverride": true,
      "requiresApproval": false
    }
  ],
  "checks": [
    {
      "checkId": "budget_validation",
      "name": "Budget Validation",
      "passed": false,
      "risks": ["risk_123"],
      "confidence": 0.95,
      "executionTime": 45
    }
  ],
  "assessedAt": "2026-04-24T10:30:00Z",
  "validUntil": "2026-04-24T11:30:00Z"
}
```

### 11.2 Risk Resolution Endpoints

```
POST /api/v1/safety/risks/{riskId}/resolve
```

Mark a risk as resolved.

**Request:**
```json
{
  "resolution": "Customer approved budget increase",
  "actions": ["discussed_with_customer", "updated_quote"],
  "resolvedBy": "agent_789"
}
```

**Response:**
```json
{
  "riskId": "risk_123",
  "status": "resolved",
  "resolvedAt": "2026-04-24T10:35:00Z",
  "resolvedBy": "agent_789",
  "resolution": "Customer approved budget increase"
}
```

```
POST /api/v1/safety/risks/{riskId}/approve
```

Request owner approval for a risk.

**Request:**
```json
{
  "requestedBy": "agent_789",
  "notes": "Customer is VIP, willing to proceed despite risk"
}
```

**Response:**
```json
{
  "approvalId": "approval_456",
  "riskId": "risk_123",
  "status": "pending",
  "requestedBy": "agent_789",
  "requestedAt": "2026-04-24T10:35:00Z",
  "expiresAt": "2026-04-25T10:35:00Z"
}
```

---

## Summary

The Safety & Risk System provides comprehensive protection across the trip lifecycle through:

1. **Risk Detection Framework** — Categorized risk checks for financial, compliance, operational, customer, and agency risks
2. **Risk Scoring Engine** — Severity × likelihood scoring with context-aware adjustments
3. **Budget Validation** — Multi-rule budget checking with configurable thresholds
4. **Compliance Checking** — GST and TCS compliance validation with detailed requirements
5. **Safety Nets** — Action blocking and confirmation flows for risky operations
6. **Alert System** — Multi-channel alerts with escalation rules
7. **Resolution Workflows** — Owner approval processes and resolution tracking

The system balances protection with flexibility — blocking critical/compliance risks while allowing overrides for lower-severity issues with proper acknowledgment.

---

**Next Document:** SAFETY_02_UX_UI_DEEP_DIVE.md — Risk Display, Warning UI, and Agent Experience
