# Intake System — Analytics Deep Dive

> Part 6 of 6 in the Intake / Packet Processing Deep Dive Series

**Series Index:**
1. [Technical Deep Dive](INTAKE_01_TECHNICAL_DEEP_DIVE.md) — Architecture & Extraction Pipeline
2. [UX/UI Deep Dive](INTAKE_02_UX_UI_DEEP_DIVE.md) — Packet Panel & Extraction Experience
3. [Channel Integration Deep Dive](INTAKE_03_CHANNEL_INTEGRATION_DEEP_DIVE.md) — Multi-Channel Processing
4. [Extraction Quality Deep Dive](INTAKE_04_EXTRACTION_QUALITY_DEEP_DIVE.md) — Quality Framework & Monitoring
5. [Triage Strategies Deep Dive](INTAKE_05_TRIAGE_STRATEGIES_DEEP_DIVE.md) — Routing, Prioritization & Assignment
6. **Analytics Deep Dive** (this document) — Metrics, Insights & Dashboards

---

## Document Overview

**Purpose:** Comprehensive exploration of analytics for the intake system — what to measure, how to visualize, and how to derive actionable insights.

**Scope:**
- Metric definitions and KPIs
- Channel performance analytics
- Extraction quality analytics
- Triage and routing analytics
- Agent performance analytics
- Customer journey analytics
- Dashboard specifications
- Alerting and anomaly detection
- Executive reporting

**Target Audience:** Product managers, data analysts, engineers, and stakeholders interested in intake system performance and optimization.

**Last Updated:** 2026-04-24

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Analytics Architecture](#analytics-architecture)
3. [Channel Performance Analytics](#channel-performance-analytics)
4. [Extraction Quality Analytics](#extraction-quality-analytics)
5. [Triage & Routing Analytics](#triage--routing-analytics)
6. [Agent Performance Analytics](#agent-performance-analytics)
7. [Customer Journey Analytics](#customer-journey-analytics)
8. [Dashboard Specifications](#dashboard-specifications)
9. [Alerting & Anomaly Detection](#alerting--anomaly-detection)
10. [Executive Reporting](#executive-reporting)

---

## 1. Executive Summary

### The Analytics Challenge

The intake system generates rich data at every step:
- Channel reception patterns
- Extraction accuracy by field type
- Triage decision outcomes
- Agent assignment effectiveness
- Customer response behavior

Without proper analytics, this data is noise. With analytics, it becomes:
- **Operational intelligence** — Are we meeting SLAs? Where's the bottleneck?
- **Quality assurance** — How accurate is our extraction? Where do we fail?
- **Business insights** — Which channels drive value? What's our conversion funnel?
- **Optimization guidance** — What should we improve first?

### Key Analytics Principles

| Principle | Description |
|-----------|-------------|
| **Action-oriented** | Every metric should inform a decision or action |
| **Contextual** | Numbers alone are meaningless — provide comparison and trends |
| **Hierarchical** | Executive KPIs → Operational metrics → Diagnostic details |
| **Real-time + Historical** | Live monitoring for operations, historical for trends |
| **Predictive** | Not just what happened, but what will happen |

### Core KPI Tree

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              INTAKE SYSTEM KPI TREE                          │
└─────────────────────────────────────────────────────────────────────────────┘

                              INTAKE SYSTEM HEALTH
                                      │
        ┌─────────────────────────────┼─────────────────────────────┐
        │                             │                             │
        ▼                             ▼                             ▼
  RESPONSE VELOCITY          EXTRACTION QUALITY            CONVERSION EFFICIENCY
        │                             │                             │
        ├─── First Response Time      ├─── Extraction Accuracy     ├─── Inquiry → Quote
        ├─── SLA Compliance           ├─── Field-Level Rates        ├─── Quote → Booking
        └─── Agent Assignment Speed   └─── Correction Rate         └─── Time to Convert
```

---

## 2. Analytics Architecture

### 2.1 Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ANALYTICS DATA FLOW                                 │
└─────────────────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────┐
  │                      INTAKE SYSTEM EVENTS                       │
  │                                                                  │
  │  • Inquiry received                                             │
  │  • Extraction completed                                         │
  │  • Field extracted (per field)                                  │
  │  • Extraction corrected                                         │
  │  • Triage decision made                                         │
  │  • Agent assigned                                               │
  │  • Agent responded                                              │
  │  • Quote generated                                              │
  │  • Booking completed                                            │
  └────────────────────────────┬────────────────────────────────────┘
                               │
                               ▼
  ┌─────────────────────────────────────────────────────────────────┐
  │                      EVENT STREAMING                            │
  │                                                                  │
  │  • Real-time events → Kafka / EventBridge                       │
  │  • Batch events → Data warehouse                                │
  │  • Metrics aggregation → Redis / TSDB                           │
  └────────────────────────────┬────────────────────────────────────┘
                               │
          ┌────────────────────┼────────────────────┐
          │                    │                    │
          ▼                    ▼                    ▼
  ┌───────────────┐   ┌───────────────┐   ┌───────────────┐
  │ REAL-TIME     │   │ BATCH         │   │ PREDICTIVE    │
  │ METRICS       │   │ ANALYTICS     │   │ ANALYTICS     │
  │               │   │               │   │               │
  │ • Live dash   │   │ • Daily       │   │ • Forecasting │
  │ • Alerting    │   │   reports     │   │ • Trends      │
  │ • Monitoring  │   │ • Trends      │   │ • Anomaly     │
  └───────────────┘   └───────────────┘   └───────────────┘
          │                    │                    │
          └────────────────────┼────────────────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   CONSUMPTION LAYER   │
                    │                       │
                    │ • Dashboards          │
                    │ • Reports             │
                    │ • Alerts              │
                    │ • API                 │
                    └──────────────────────┘
```

### 2.2 Metric Storage Schema

```typescript
/**
 * Analytics Event Schema
 */

// Core event types
type IntakeEventType =
  | "inquiry_received"
  | "extraction_completed"
  | "field_extracted"
  | "field_corrected"
  | "triage_decision"
  | "agent_assigned"
  | "agent_responded"
  | "quote_generated"
  | "booking_completed"
  | "escalation";

// Base event structure
interface IntakeEvent {
  id: string;
  type: IntakeEventType;
  timestamp: Date;
  packetId: string;
  agencyId: string;

  // Event-specific data
  data: EventData;

  // Metadata
  metadata: {
    source: string;
    version: string;
    [key: string]: any;
  };
}

type EventData =
  | InquiryReceivedData
  | ExtractionCompletedData
  | FieldExtractedData
  | FieldCorrectedData
  | TriageDecisionData
  | AgentAssignedData
  | AgentRespondedData
  | QuoteGeneratedData
  | BookingCompletedData
  | EscalationData;

// Event-specific schemas
interface InquiryReceivedData {
  channel: Channel;
  customerType?: "new" | "returning" | "vip";
  sourceCampaign?: string;
}

interface ExtractionCompletedData {
  duration: number;              // milliseconds
  fieldsExtracted: number;
  fieldsTotal: number;
  overallConfidence: number;     // 0-1
}

interface FieldExtractedData {
  fieldName: string;
  confidence: number;            // 0-1
  method: "llm" | "rule" | "hybrid";
  wasCorrect: boolean;           // Determined later
}

interface FieldCorrectedData {
  fieldName: string;
  originalValue: any;
  correctedValue: any;
  correctedBy: string;           // agent ID or "system"
  correctionReason: string;
}

interface TriageDecisionData {
  priority: PriorityLevel;
  urgencyScore: number;
  complexityScore: number;
  valueScore: number;
  routedTo: string;              // queue or agent
  routingStrategy: RoutingStrategy;
}

interface AgentAssignedData {
  agentId: string;
  assignmentMethod: "auto" | "manual";
  skillMatch: number;            // 0-1
  currentWorkload: number;       // packets
}

interface AgentRespondedData {
  agentId: string;
  responseTime: number;          // minutes from inquiry
  firstResponse: boolean;
}

interface QuoteGeneratedData {
  agentId: string;
  quoteValue: number;
  timeToQuote: number;           // minutes from inquiry
}

interface BookingCompletedData {
  agentId: string;
  bookingValue: number;
  timeToBook: number;            // minutes from inquiry
  margin?: number;
}

interface EscalationData {
  fromAgentId?: string;
  toAgentId: string;
  reason: string;
  escalationType: "reassignment" | "expert" | "owner";
}
```

### 2.3 Aggregation Strategy

```typescript
/**
 * Metric Aggregation Configuration
 */

interface AggregationConfig {
  // Real-time metrics (1-min granularity)
  realtime: {
    window: "1m";
    retention: "24h";
    metrics: RealtimeMetric[];
  };

  // Operational metrics (15-min granularity)
  operational: {
    window: "15m";
    retention: "90d";
    metrics: OperationalMetric[];
  };

  // Business metrics (daily granularity)
  business: {
    window: "1d";
    retention: "2y";
    metrics: BusinessMetric[];
  };
}

// Real-time metrics for live monitoring
type RealtimeMetric =
  | "active_packets"
  | "pending_assignments"
  | "agent_utilization"
  | "queue_depth"
  | "extraction_rate"
  | "current_response_time";

// Operational metrics for daily operations
type OperationalMetric =
  | "first_response_time"
  | "sla_compliance_rate"
  | "extraction_accuracy"
  | "routing_accuracy"
  | "agent_productivity"
  | "correction_rate";

// Business metrics for strategic decisions
type BusinessMetric =
  | "inquiry_volume"
  | "conversion_rate"
  | "revenue_per_inquiry"
  | "channel_effectiveness"
  | "customer_acquisition_cost"
  | "lifetime_value_by_source";
```

---

## 3. Channel Performance Analytics

### 3.1 Channel Overview Dashboard

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        CHANNEL PERFORMANCE DASHBOARD                        │
└─────────────────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────┐
  │                    INQUIRY VOLUME BY CHANNEL                    │
  │                                                                  │
  │   ┌─────┐    ┌─────┐    ┌─────┐    ┌─────┐    ┌─────┐          │
  │   │ 342 │    │ 287 │    │ 198 │    │ 156 │    │  89 │          │
  │   │     │    │     │    │     │    │     │    │     │          │
  │   │ WA  │    │ WEB │    │ EML │    │ PHN │    │ OTH │          │
  │   └─────┘    └─────┘    └─────┘    └─────┘    └─────┘          │
  │                                                                  │
  │   Volume trend:  ▲ 12% vs last week                            │
  └─────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────┐
  │                    RESPONSE TIME BY CHANNEL                     │
  │                                                                  │
  │   Channel          │  Avg   │  Median │  P95   │  SLA Target    │
  │   ─────────────────┼────────┼─────────┼────────┼──────────────  │
  │   WhatsApp         │  18m   │   12m   │  45m   │     30m        │
  │   Web Form         │  32m   │   24m   │  72m   │     60m        │
  │   Email            │ 124m   │   98m   │ 240m   │    240m        │
  │   Phone            │   5m   │    3m   │  12m   │     15m        │
  │                                                                  │
  │   ⚠️  Web form exceeding SLA target                            │
  └─────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────┐
  │                    CONVERSION BY CHANNEL                        │
  │                                                                  │
  │   ┌─────────────────────────────────────────────────────────┐   │
  │   │ Phone:     ████████████████████ 24.5%                    │   │
  │   │ WhatsApp:  ████████████████ 18.2%                        │   │
  │   │ Web:       ██████████ 12.8%                              │   │
  │   │ Email:     ████████ 9.4%                                │   │
  │   │ Other:     █████ 5.1%                                   │   │
  │   └─────────────────────────────────────────────────────────┘   │
  │                                                                  │
  │   Weighted avg: 14.8%                                           │
  └─────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────┐
  │                    EXTRACTION QUALITY BY CHANNEL                │
  │                                                                  │
  │   Channel          │  Accuracy  │  Corrections  │  Avg Fields    │
  │   ─────────────────┼───────────┼───────────────┼──────────────   │
  │   Web Form         │   96.2%   │     3.8%      │     8.2        │
  │   Email            │   82.4%   │    17.6%      │     5.1        │
  │   WhatsApp         │   88.7%   │    11.3%      │     6.8        │
  │   Phone            │   94.1%   │     5.9%      │     7.5        │
  │                                                                  │
  │   💡 Email has highest correction rate — consider templates     │
  └─────────────────────────────────────────────────────────────────┘
```

### 3.2 Channel Metrics Definition

```typescript
/**
 * Channel Performance Metrics
 */

interface ChannelMetrics {
  channel: Channel;
  period: DateRange;

  // Volume metrics
  volume: {
    totalInquiries: number;
    trend: "increasing" | "stable" | "decreasing";
    trendPercent: number;
    peakHours: HourOfDay[];
    lowHours: HourOfDay[];
  };

  // Response metrics
  response: {
    firstResponseTime: ResponseTimeMetrics;
    slaCompliance: number;           // 0-1
    abandonmentRate: number;          // 0-1, inquiries that got no response
  };

  // Quality metrics
  quality: {
    extractionAccuracy: number;       // 0-1
    avgFieldsExtracted: number;
    correctionRate: number;           // 0-1
    structuredDataRate: number;       // 0-1, how many have structured input
  };

  // Business metrics
  business: {
    conversionRate: number;           // 0-1
    avgValuePerInquiry: number;
    timeToConversion: number;         // days
    customerAcquisitionCost?: number;
  };

  // Operational metrics
  operational: {
    triageAccuracy: number;           // 0-1, correct priority assignment
    autoAssignmentRate: number;       // 0-1
    agentSatisfaction?: number;       // 0-5, agents prefer this channel
  };
}

interface ResponseTimeMetrics {
  average: number;                   // minutes
  median: number;
  p90: number;
  p95: number;
  p99: number;
}

interface HourOfDay {
  hour: number;                       // 0-23
  percentage: number;                 // 0-1
}
```

### 3.3 Channel Comparison Queries

```typescript
/**
 * Channel Analytics Queries
 */

class ChannelAnalyticsQuery {
  /**
   * Compare channels across all metrics
   */
  async compareChannels(
    channels: Channel[],
    period: DateRange
  ): Promise<ChannelComparisonReport> {
    const metrics = await Promise.all(
      channels.map(ch => this.getChannelMetrics(ch, period))
    );

    return {
      bestForVolume: this.getBest(metrics, "volume"),
      bestForResponse: this.getBest(metrics, "response"),
      bestForQuality: this.getBest(metrics, "quality"),
      bestForConversion: this.getBest(metrics, "conversion"),
      mostImproved: this.getMostImproved(metrics),
      recommendations: this.generateRecommendations(metrics)
    };
  }

  /**
   * Get best performing channel for a metric
   */
  private getBest(
    metrics: ChannelMetrics[],
    category: string
  ): { channel: Channel; score: number } {
    // Implementation varies by category
    return { channel: "whatsapp", score: 0 };
  }

  /**
   * Generate channel optimization recommendations
   */
  private generateRecommendations(
    metrics: ChannelMetrics[]
  ): Recommendation[] {
    const recommendations: Recommendation[] = [];

    // Example: If email has poor extraction quality
    const email = metrics.find(m => m.channel === "email");
    if (email && email.quality.extractionAccuracy < 0.85) {
      recommendations.push({
        type: "quality_improvement",
        priority: "high",
        channel: "email",
        suggestion: "Implement email templates with structured fields",
        expectedImprovement: "+12% extraction accuracy"
      });
    }

    // Example: If web form has slow response
    const web = metrics.find(m => m.channel === "web");
    if (web && web.response.firstResponseTime.average > 30) {
      recommendations.push({
        type: "response_improvement",
        priority: "medium",
        channel: "web",
        suggestion: "Add real-time agent availability indicator",
        expectedImprovement: "-15% first response time"
      });
    }

    return recommendations;
  }
}

interface Recommendation {
  type: string;
  priority: "low" | "medium" | "high";
  channel: Channel;
  suggestion: string;
  expectedImprovement: string;
}
```

---

## 4. Extraction Quality Analytics

### 4.1 Quality Dashboard

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      EXTRACTION QUALITY DASHBOARD                           │
└─────────────────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────┐
  │                    OVERALL ACCURACY TREND                       │
  │                                                                  │
  │   100% ┌                                                          │
  │    95% │  ●───●───●───●───●───●───●───●                           │
  │    90% │        ●                                            │  │
  │    85% │                                                       │  │
  │    80% └────────────────────────────────────────────────────  │  │
  │        Jan  Feb  Mar  Apr  May  Jun  Jul  Aug                    │
  │                                                                  │
  │   Current: 94.2%  │  Target: 95%  │  Gap: -0.8%                  │
  │   Trend: Improving (+2.3% vs last month)                        │
  └─────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────┐
  │                    FIELD-LEVEL ACCURACY                         │
  │                                                                  │
  │   Field              │  Accuracy  │  Trend  │  Corrections       │
  │   ───────────────────┼───────────┼─────────┼───────────────     │
  │   Destination        │   98.4%   │   ▲     │     1.6%           │
  │   Departure Date     │   97.8%   │   ▲     │     2.2%           │
  │   Return Date        │   96.2%   │   →     │     3.8%           │
  │   Passenger Count    │   95.1%   │   ▲     │     4.9%           │
  │   Budget             │   82.3%   │   ▼     │    17.7%           │
  │   Trip Type          │   91.7%   │   →     │     8.3%           │
  │   Special Requests   │   68.4%   │   ▼     │    31.6%           │
  │                                                                  │
  │   ⚠️  Budget accuracy declining — 3 consecutive weeks           │
  │   ⚠️  Special requests below threshold — needs review           │
  └─────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────┐
  │                    ERROR BREAKDOWN                               │
  │                                                                  │
  │   ┌─────────────────────────────────────────────────────────┐   │
  │   │                                                           │   │
  │   │   Missed        ████████████████████████████  42.3%      │   │
  │   │   Incorrect     ████████████████████  28.7%              │   │
  │   │   Format        ████████████  16.4%                      │   │
  │   │   False Positive ██████  12.6%                          │   │
  │   │                                                           │   │
  │   └─────────────────────────────────────────────────────────┘   │
  │                                                                  │
  │   Top error patterns:                                           │
  │   • Budget range: Missed upper bound (34% of budget errors)    │
  │   • Dates: Confused DD/MM vs MM/DD (28% of date errors)        │
  │   • Special requests: Not detected in unstructured text (67%)  │
  └─────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────┐
  │                    CONFIDENCE CALIBRATION                       │
  │                                                                  │
  │   Confidence Band  │  Count   │  Actual Accuracy  │  Gap       │
  │   ─────────────────┼──────────┼───────────────────┼───────────  │
  │   90-100%           │   1,247  │      94.2%        │   -4.2%    │
  │   80-90%            │   2,381  │      85.7%        │   -2.3%    │
  │   70-80%            │   1,892  │      73.1%        │   -1.9%    │
  │   60-70%            │   1,456  │      62.4%        │   -1.6%    │
  │   < 60%             │     982  │      51.8%        │   +4.2%    │
  │                                                                  │
  │   ✅ Well-calibrated — gaps within acceptable range              │
  └─────────────────────────────────────────────────────────────────┘
```

### 4.2 Quality Metrics Schema

```typescript
/**
 * Extraction Quality Metrics
 */

interface ExtractionQualityMetrics {
  period: DateRange;

  // Overall accuracy
  overall: {
    accuracy: number;               // 0-1, percentage of correct extractions
    trend: Trend;
    target: number;
    gap: number;
  };

  // Field-level accuracy
  byField: FieldAccuracyMetric[];

  // Error analysis
  errors: {
    total: number;
    byType: ErrorTypeBreakdown;
    topPatterns: ErrorPattern[];
    byChannel: { [channel: string]: number };
  };

  // Confidence calibration
  calibration: {
    byBand: ConfidenceBandMetric[];
    isCalibrated: boolean;
    avgGap: number;
  };

  // Correction analysis
  corrections: {
    totalCorrections: number;
    correctionRate: number;         // 0-1
    avgCorrectionsPerPacket: number;
    byField: { [field: string]: number };
    timeToCorrect: number;          // avg minutes
  };

  // Extraction performance
  performance: {
    avgExtractionTime: number;      // milliseconds
    p95ExtractionTime: number;
    extractionRate: number;         // packets per minute
  };
}

interface FieldAccuracyMetric {
  fieldName: string;
  accuracy: number;                 // 0-1
  trend: Trend;
  corrections: number;              // count
  confidence: number;               // avg confidence score
  sampleSize: number;
}

type Trend = "improving" | "stable" | "declining";

interface ErrorTypeBreakdown {
  missed: number;                   // Field not extracted
  incorrect: number;                // Wrong value extracted
  falsePositive: number;            // Extracted when not present
  format: number;                   // Wrong format
}

interface ErrorPattern {
  pattern: string;
  count: number;
  percentage: number;               // 0-1
  example: string;
  suggestedFix: string;
}

interface ConfidenceBandMetric {
  band: string;                     // e.g., "90-100"
  count: number;
  avgConfidence: number;
  actualAccuracy: number;
  gap: number;                      // actual - predicted
}
```

### 4.3 Learning Pipeline Analytics

```typescript
/**
 * Learning Pipeline Analytics
 */

interface LearningAnalytics {
  // Data collection
  dataCollection: {
    totalCorrections: number;
    correctionRate: number;         // 0-1
    labeledData: number;            // Human-verified samples
    dataQuality: number;            // 0-1
  };

  // Model training
  modelTraining: {
    lastTrainingDate: Date;
    trainingFrequency: string;      // e.g., "weekly"
    samplesUsed: number;
    trainingDuration: number;       // minutes
    modelVersion: string;
  };

  // Model performance
  modelPerformance: {
    validationAccuracy: number;
    testAccuracy: number;
    f1Score: number;
    precision: number;
    recall: number;
    auc: number;
  };

  // Impact tracking
  impact: {
    accuracyImprovement: number;    // percentage points
    errorReduction: number;         // percentage points
    roi: number;                    // return on investment
  };

  // A/B test results
  abTests: ABTestResult[];
}

interface ABTestResult {
  testName: string;
  startDate: Date;
  endDate?: Date;
  variants: {
    name: string;
    samples: number;
    metrics: {
      accuracy: number;
      confidence: number;
      extractionTime: number;
    };
  }[];
  winner?: string;
  significance: number;            // 0-1
  recommendation: string;
}
```

---

## 5. Triage & Routing Analytics

### 5.1 Triage Performance Dashboard

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       TRIAGE PERFORMANCE DASHBOARD                          │
└─────────────────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────┐
  │                    PRIORITY DISTRIBUTION                        │
  │                                                                  │
  │   ┌─────────────────────────────────────────────────────────┐   │
  │   │                                                           │   │
  │   │   CRITICAL    ████  4.2%                                 │   │
  │   │   HIGH       ████████████ 18.7%                          │   │
  │   │   MEDIUM    ███████████████████████████████ 57.3%       │   │
  │   │   LOW       █████████████ 19.8%                          │   │
  │   │                                                           │   │
  │   └─────────────────────────────────────────────────────────┘   │
  │                                                                  │
  │   Volume by priority aligns with SLA targets                    │
  └─────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────┐
  │                    TRIAGE SCORE DISTRIBUTIONS                    │
  │                                                                  │
  │   ┌─────────────────────────────────────────────────────────┐   │
  │   │ URGENCY SCORE                                            │   │
  │   │ 80+ │  ████  CRITICAL ZONE                              │   │
  │   │ 60-80│  ████████  HIGH                                   │   │
  │   │ 40-60│  ████████████  MEDIUM                             │   │
  │   │ 20-40│  ██████  LOW                                      │   │
  │   │ 0-20 │  ██  VERY LOW                                    │   │
  │   └─────────────────────────────────────────────────────────┘   │
  │                                                                  │
  │   ┌─────────────────────────────────────────────────────────┐   │
  │   │ COMPLEXITY SCORE                                         │   │
  │   │ 70+ │  ██  EXPERT REQUIRED                              │   │
  │   │ 50-70│  ███████  SENIOR LEVEL                           │   │
  │   │ 30-50│  ████████████  STANDARD                           │   │
  │   │ <30 │  ████████████████████  SIMPLE                      │   │
  │   └─────────────────────────────────────────────────────────┘   │
  │                                                                  │
  │   ┌─────────────────────────────────────────────────────────┐   │
  │   │ VALUE SCORE                                              │   │
  │   │ 70+ │  ████  HIGH VALUE                                 │   │
  │   │ 50-70│  ████████  GOOD VALUE                            │   │
  │   │ 30-50│  ████████████  STANDARD VALUE                     │   │
  │   │ <30 │  ████████████████████  LOW VALUE                   │   │
  │   └─────────────────────────────────────────────────────────┘   │
  └─────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────┐
  │                    ROUTING ACCURACY                             │
  │                                                                  │
  │   Metric              │  Score   │  Target  │  Status           │
  │   ────────────────────┼──────────┼─────────┼───────────────     │
  │   Correct Queue       │   91.2%  │   90%   │      ✅           │
  │   Correct Priority    │   87.4%  │   85%   │      ✅           │
  │   First-Agent Match   │   76.8%  │   75%   │      ✅           │
  │   No Reassignment     │   84.3%  │   80%   │      ✅           │
  │                                                                  │
  │   Overall Routing Score: 85.0% (Target: 82%)                    │
  └─────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────┐
  │                    ASSIGNMENT METHOD BREAKDOWN                   │
  │                                                                  │
  │   ┌─────────────────────────────────────────────────────────┐   │
  │   │                                                           │   │
  │   │   Auto-assign    ████████████████████████████████  67.3%  │   │
  │   │   Manual assign  ████████████  32.7%                     │   │
  │   │                                                           │   │
  │   └─────────────────────────────────────────────────────────┘   │
  │                                                                  │
  │   Auto-assign trending up: +5.2% vs last month                   │
  │   Manual assign avg time: 8.3 minutes                            │
  └─────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────┐
  │                    ESCALATION ANALYSIS                           │
  │                                                                  │
  │   Escalation Type    │  Count   │  Rate   │  Avg Time           │
  │   ───────────────────┼──────────┼─────────┼───────────────     │
  │   Reassignment       │    156   │   8.2%  │    4.2 hours        │
  │   Expert escalation   │     48   │   2.5%  │    6.8 hours        │
  │   Owner escalation    │     12   │   0.6%  │   12.4 hours        │
  │                                                                  │
  │   Top escalation reasons:                                       │
  │   • Complexity exceeded agent skill (42%)                       │
  │   • Customer requested specific agent (28%)                     │
  │   • Agent unavailable (18%)                                     │
  │   • Workload balancing (12%)                                   │
  └─────────────────────────────────────────────────────────────────┘
```

### 5.2 Triage Metrics Schema

```typescript
/**
 * Triage & Routing Metrics
 */

interface TriageMetrics {
  period: DateRange;

  // Priority distribution
  priority: {
    distribution: {
      [key in PriorityLevel]: number;
    };
    trend: PriorityTrend;
    accuracy: number;               // 0-1, correct priority assignment
  };

  // Score distributions
  scores: {
    urgency: ScoreDistribution;
    complexity: ScoreDistribution;
    value: ScoreDistribution;
  };

  // Routing performance
  routing: {
    correctQueueRate: number;        // 0-1
    correctPriorityRate: number;     // 0-1
    firstAgentMatchRate: number;     // 0-1
    reassignmentRate: number;        // 0-1
    avgTimeToAssign: number;         // minutes
  };

  // Assignment breakdown
  assignment: {
    autoAssignRate: number;          // 0-1
    manualAssignRate: number;        // 0-1
    byQueue: QueueAssignmentStats[];
    byAgent: AgentAssignmentStats[];
  };

  // Escalation analysis
  escalation: {
    totalEscalations: number;
    escalationRate: number;          // 0-1
    byType: EscalationTypeStats[];
    byReason: { [reason: string]: number };
    avgTimeToEscalate: number;       // hours
  };

  // Rule effectiveness
  rules: {
    totalRules: number;
    activeRules: number;
    triggeredRules: RuleTriggerStats[];
    effectiveness: RuleEffectivenessStats;
  };
}

interface ScoreDistribution {
  min: number;
  max: number;
  mean: number;
  median: number;
  p25: number;
  p75: number;
  histogram: {
    range: string;
    count: number;
    percentage: number;
  }[];
}

interface PriorityTrend {
  critical: Trend;
  high: Trend;
  medium: Trend;
  low: Trend;
}

interface QueueAssignmentStats {
  queue: string;
  assigned: number;
  autoAssigned: number;
  manuallyAssigned: number;
  avgWaitTime: number;
}

interface AgentAssignmentStats {
  agentId: string;
  assigned: number;
  reassignments: number;
  avgResponseTime: number;
  utilization: number;
}

interface EscalationTypeStats {
  type: string;
  count: number;
  percentage: number;
  avgTime: number;
}

interface RuleTriggerStats {
  ruleId: string;
  ruleName: string;
  triggered: number;
  percentage: number;
  accuracy: number;                 // 0-1, correct routing
}

interface RuleEffectivenessStats {
  avgAccuracy: number;
  topRules: string[];
  underperformingRules: string[];
  unusedRules: string[];
}
```

---

## 6. Agent Performance Analytics

### 6.1 Agent Performance Dashboard

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        AGENT PERFORMANCE DASHBOARD                          │
└─────────────────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────┐
  │                    TEAM OVERVIEW                                 │
  │                                                                  │
  │   Total Agents: 18  │  Online: 14  │  Away: 3  │  Offline: 1    │
  │                                                                  │
  │   Team Utilization: 72% avg (Target: 70-80%) ✅                  │
  │   Active Packets: 127  │  Unassigned: 8  │  Overdue: 2          │
  └─────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────┐
  │                    TOP PERFORMERS (THIS WEEK)                    │
  │                                                                  │
  │   Agent     │  Packets │  Response │  Conversion │  Rating  │   │
  │   ──────────┼──────────┼───────────┼─────────────┼─────────     │
  │   Priya S.  │    48    │    12m    │    24.8%    │   4.8   │   │
  │   Amit K.   │    52    │    18m    │    22.1%    │   4.7   │   │
  │   Neha R.   │    41    │    15m    │    21.4%    │   4.9   │   │
  │   Rahul M.  │    44    │    22m    │    19.8%    │   4.6   │   │
  │                                                                  │
  │   🏆 Priya S. — Best conversion rate, fastest response           │
  └─────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────┐
  │                    RESPONSE TIME ANALYSIS                       │
  │                                                                  │
  │   ┌─────────────────────────────────────────────────────────┐   │
  │   │                                                           │   │
  │   │   < 15min     ████████████████████████████  42.3%        │   │
  │   │   15-30min    ████████████████  28.7%                    │   │
  │   │   30-60min    ████████  16.4%                           │   │
  │   │   > 60min     ████  12.6%                               │   │
  │   │                                                           │   │
  │   └─────────────────────────────────────────────────────────┘   │
  │                                                                  │
  │   Team avg: 24 min  │  Best: 12 min  │  Target: <30 min         │
  └─────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────┐
  │                    WORKLOAD DISTRIBUTION                        │
  │                                                                  │
  │   Agent           │  Load  │  Capacity  │  Utilization  │ Status│
  │   ────────────────┼────────┼───────────┼───────────────┼──────  │
  │   Priya S.        │   18   │     20    │     90%       │ ⚠️    │
  │   Amit K.         │   15   │     20    │     75%       │ ✅     │
  │   Neha R.         │   12   │     20    │     60%       │ ✅     │
  │   Rahul M.        │   14   │     18    │     78%       │ ✅     │
  │   Sneha P.        │    8   │     15    │     53%       │ ✅     │
  │   Vikram S.       │    6   │     15    │     40%       │ 💤     │
  │                                                                  │
  │   ⚠️  Priya at capacity — consider routing away                 │
  │   💤  Vikram underutilized — can take more work                 │
  └─────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────┐
  │                    SPECIALIZATION EFFECTIVENESS                  │
  │                                                                  │
  │   Specialization     │  Agents │  Avg Conv │  Team Avg │  Lift │
  │   ───────────────────┼─────────┼───────────┼───────────┼──────  │
  │   Europe             │    3    │   26.4%   │   18.2%   │ +45%  │
  │   Southeast Asia     │    4    │   23.1%   │   18.2%   │ +27%  │
  │   Domestic           │    5    │   16.8%   │   18.2%   │  -8%  │
  │   Honeymoon          │    2    │   28.9%   │   18.2%   │ +59%  │
  │   Family             │    3    │   19.2%   │   18.2%   │  +5%  │
  │                                                                  │
  │   💡 Europe specialists show 45% conversion lift                 │
  └─────────────────────────────────────────────────────────────────┘
```

### 6.2 Agent Performance Schema

```typescript
/**
 * Agent Performance Metrics
 */

interface AgentPerformanceMetrics {
  agentId: string;
  period: DateRange;

  // Productivity
  productivity: {
    packetsHandled: number;
    avgPacketsPerDay: number;
    activeTime: number;             // hours
    utilization: number;             // 0-1
  };

  // Response metrics
  response: {
    firstResponseTime: ResponseTimeMetrics;
    slaCompliance: number;           // 0-1
    responseRate: number;            // 0-1, responded within SLA
  };

  // Quality metrics
  quality: {
    extractionAccuracy: number;      // 0-1, corrections they made
    correctionRate: number;          // 0-1
    quoteAccuracy: number;           // 0-1
  };

  // Business outcomes
  outcomes: {
    conversionRate: number;          // 0-1
    revenueGenerated: number;
    avgValuePerPacket: number;
    bookings: number;
  };

  // Customer satisfaction
  satisfaction: {
    customerRating: number;          // 0-5
    positiveFeedback: number;        // count
    negativeFeedback: number;        // count
    responseRate: number;            // 0-1
  };

  // Specialization effectiveness
  specializations: {
    area: string;                    // e.g., "europe"
    packetsHandled: number;
    conversionRate: number;
    teamAvg: number;
    lift: number;                    // percentage points above team
  }[];

  // Comparison
  comparison: {
    vsTeamAvg: {
      responseTime: number;          // percentage diff
      conversion: number;
      utilization: number;
    };
    rank: {
      responseTime: number;          // position in team
      conversion: number;
      overall: number;
    };
  };
}

interface TeamPerformanceMetrics {
  period: DateRange;

  // Team overview
  overview: {
    totalAgents: number;
    onlineAgents: number;
    totalPackets: number;
    avgUtilization: number;
  };

  // Team metrics
  metrics: {
    firstResponseTime: ResponseTimeMetrics;
    conversionRate: number;
    slaCompliance: number;
    customerRating: number;
  };

  // Individual agents
  agents: AgentPerformanceMetrics[];

  // Work distribution
  workload: {
    distribution: WorkloadDistribution;
    balance: "balanced" | "imbalanced";
    recommendations: string[];
  };

  // Specialization analysis
  specializations: {
    area: string;
    agents: number;
    avgConversion: number;
    teamAvg: number;
    lift: number;
    topAgent: string;
  }[];
}

interface WorkloadDistribution {
  underutilized: number;             // count, <50%
  optimal: number;                  // count, 50-80%
  overutilized: number;             // count, >80%
}
```

---

## 7. Customer Journey Analytics

### 7.1 Journey Funnel Dashboard

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       CUSTOMER JOURNEY DASHBOARD                            │
└─────────────────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────┐
  │                    CONVERSION FUNNEL                            │
  │                                                                  │
  │   1,000 ┌                                                        │
  │    900  │  ████  Inquiry Received                               │
  │    800  │  ████                                                 │
  │    700  │  ████                                                 │
  │    600  │  ████  Quote Sent (42%)                               │
  │    500  │  ████                                                 │
  │    400  │  ████                                                 │
  │    300  │  ████  Booking Confirmed (14.8%)                      │
  │    200  │                                                       │
  │    100  │                                                       │
  │      0  └────────────────────────────────────────────────────  │
  │                                                                  │
  │   Drop-off analysis:                                            │
  │   • Inquiry → Quote: 58% drop (normal for consideration)        │
  │   • Quote → Booking: 65% drop (opportunity for improvement)     │
  └─────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────┐
  │                    TIME-TO-CONVERT ANALYSIS                      │
  │                                                                  │
  │   Stage              │  Median  │  P75   │  P90   │  P95        │
  │   ───────────────────┼─────────┼────────┼────────┼────────────  │
  │   First Response     │   18m   │  32m   │  58m   │   2.4h       │
  │   Quote Delivered    │   4.2h  │  8.4h  │  18h   │  28h         │
  │   Booking Completed  │  2.8d   │  5.4d  │  12d   │  18d         │
  │                                                                  │
  │   Total Journey: 2.8 days median (Target: <3 days) ✅           │
  └─────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────┐
  │                    JOURNEY STAGE BREAKDOWN                       │
  │                                                                  │
  │   ┌─────────────────────────────────────────────────────────┐   │
  │   │                                                           │   │
  │   │   Intake          ████████████████████████████  28%      │   │
  │   │   Quote Building  ████████████████████████████████████  │   │
  │   │   Negotiation    ████████████████  18%                    │   │
  │   │   Payment         ██████████████  14%                     │   │
  │   │   Post-Booking   ████  6%                                │   │
  │   │                                                           │   │
  │   └─────────────────────────────────────────────────────────┘   │
  │                                                                  │
  │   Longest stage: Quote Building (avg 8.4 hours)                  │
  │   💤 Bottleneck: Negotiation takes 18% of journey time           │
  └─────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────┐
  │                    CHANNEL JOURNEY COMPARISON                    │
  │                                                                  │
  │   Channel    │  Funnel   │  Response  │  Quote   │  Convert │   │
  │             │  Start    │  Time     │  Rate    │  Rate    │   │
  │   ──────────┼───────────┼───────────┼─────────┼─────────     │
  │   Phone     │   156     │    5m     │   68%   │  24.5%   │   │
  │   WhatsApp  │   342     │   18m     │   52%   │  18.2%   │   │
  │   Web       │   287     │   32m     │   38%   │  12.8%   │   │
  │   Email     │   198     │  124m     │   34%   │   9.4%   │   │
  │                                                                  │
  │   💡 Phone has best conversion but highest cost per inquiry     │
  └─────────────────────────────────────────────────────────────────┘
```

### 7.2 Journey Metrics Schema

```typescript
/**
 * Customer Journey Metrics
 */

interface JourneyMetrics {
  period: DateRange;

  // Funnel metrics
  funnel: {
    stage: JourneyStage;
    count: number;
    conversionRate: number;         // 0-1, from previous stage
    dropOffRate: number;            // 0-1
    avgTime: number;                // minutes to reach this stage
  }[];

  // Time metrics
  timing: {
    firstResponse: TimeMetrics;
    quoteDelivery: TimeMetrics;
    conversion: TimeMetrics;
    totalJourney: TimeMetrics;
  };

  // By channel
  byChannel: {
    channel: Channel;
    funnel: FunnelStageMetrics[];
    conversionRate: number;
    avgValue: number;
    avgTimeToConvert: number;
  }[];

  // By trip type
  byTripType: {
    tripType: string;
    volume: number;
    conversionRate: number;
    avgValue: number;
    avgTimeToConvert: number;
  }[];

  // By customer segment
  bySegment: {
    segment: CustomerSegment;
    volume: number;
    conversionRate: number;
    avgValue: number;
    retention: number;              // 0-1
  }[];

  // Drop-off analysis
  dropOff: {
    stage: JourneyStage;
    dropped: number;
    dropOffRate: number;
    topReasons: DropOffReason[];
  }[];
}

type JourneyStage =
  | "inquiry_received"
  | "responded"
  | "quoted"
  | "negotiating"
  | "payment_pending"
  | "booked";

interface FunnelStageMetrics {
  stage: JourneyStage;
  count: number;
  percentage: number;               // 0-1, of original
}

interface TimeMetrics {
  median: number;                   // minutes
  p75: number;
  p90: number;
  p95: number;
}

interface DropOffReason {
  reason: string;
  count: number;
  percentage: number;
}

type CustomerSegment =
  | "new"
  | "returning"
  | "vip"
  | "high_value"
  | "price_sensitive";
```

---

## 8. Dashboard Specifications

### 8.1 Dashboard Hierarchy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DASHBOARD HIERARCHY                                │
└─────────────────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────┐
  │                    EXECUTIVE DASHBOARD                          │
  │                                                                  │
  │  Audience: Agency owners, executives                             │
  │  Refresh: Daily                                                 │
  │  Focus: Business outcomes, trends, comparisons                   │
  │                                                                  │
  │  • Total inquiries, conversion rate, revenue                    │
  │  • Channel performance comparison                               │
  │  • Team utilization and productivity                            │
  │  • Month-over-month trends                                      │
  └─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
  ┌─────────────────────────────────────────────────────────────────┐
  │                    OPERATIONS DASHBOARD                        │
  │                                                                  │
  │  Audience: Operations managers, team leads                      │
  │  Refresh: Real-time (1-min)                                     │
  │  Focus: Current state, SLAs, bottlenecks                        │
  │                                                                  │
  │  • Active packets, unassigned count                             │
  │  • Agent status, utilization, workload                          │
  │  • SLA compliance, overdue items                                │
  │  • Queue depths, wait times                                     │
  └─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
  ┌─────────────────────────────────────────────────────────────────┐
  │                    QUALITY DASHBOARD                           │
  │                                                                  │
  │  Audience: Quality analysts, trainers                           │
  │  Refresh: Hourly / Daily                                        │
  │  Focus: Accuracy, errors, improvements                          │
  │                                                                  │
  │  • Extraction accuracy by field                                │
  │  • Error patterns and frequencies                              │
  │  • Correction rates by agent                                   │
  │  • Learning pipeline status                                    │
  └─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
  ┌─────────────────────────────────────────────────────────────────┐
  │                    AGENT PERFORMANCE DASHBOARD                 │
  │                                                                  │
  │  Audience: Individual agents                                   │
  │  Refresh: Real-time (5-min)                                    │
  │  Focus: Personal metrics, goals, comparisons                    │
  │                                                                  │
  │  • My packets, response time, conversion                        │
  │  • My utilization, upcoming tasks                              │
  │  • My ranking vs team                                          │
  │  • My performance trend                                        │
  └─────────────────────────────────────────────────────────────────┘
```

### 8.2 Dashboard Component Library

```typescript
/**
 * Dashboard Component Specifications
 */

interface DashboardComponent {
  id: string;
  type: ComponentType;
  title: string;
  dataSource: string;
  refreshInterval: string;
  config: ComponentConfig;
}

type ComponentType =
  | "metric_card"           // Single KPI with trend
  | "sparkline"             // Small trend chart
  | "line_chart"            // Time series
  | "bar_chart"             // Categorical comparison
  | "pie_chart"             // Distribution
  | "table"                 // Data table
  | "funnel"                // Conversion funnel
  | "heatmap"               // 2D visualization
  | "gauge"                 // Progress to target
  | "leaderboard"           // Ranked list;

// Example: Metric Card
interface MetricCardConfig {
  metric: string;
  value: number;
  format: "number" | "currency" | "percentage" | "duration";
  trend: {
    direction: "up" | "down" | "flat";
    value: number;
    period: string;
  };
  target?: number;
  comparison?: string;
  status?: "good" | "warning" | "critical";
}

// Example: Leaderboard
interface LeaderboardConfig {
  rows: {
    rank: number;
    label: string;
    value: number;
    trend?: "up" | "down" | "flat";
    highlight?: boolean;
  }[];
  sortBy: "value" | "label";
  limit: number;
}

// Example: Funnel Chart
interface FunnelConfig {
  stages: {
    label: string;
    count: number;
    conversionRate?: number;
  }[];
  showPercentages: boolean;
  showDropOff: boolean;
}
```

### 8.3 Dashboard Layout Specification

```typescript
/**
 * Dashboard Layout Configuration
 */

interface DashboardLayout {
  dashboardId: string;
  name: string;
  description: string;
  audience: string[];
  refreshInterval: string;

  layout: {
    grid: {
      columns: number;
      rows: number;
    };
    components: DashboardComponent[];
  };

  filters: DashboardFilter[];
  actions: DashboardAction[];
}

interface DashboardFilter {
  field: string;
  type: "date_range" | "select" | "multi_select";
  defaultValue?: any;
  options?: { label: string; value: any }[];
}

interface DashboardAction {
  label: string;
  type: "export" | "drill_down" | "refresh";
  config: any;
}

// Example: Operations Dashboard
const OPERATIONS_DASHBOARD: DashboardLayout = {
  dashboardId: "intake_operations",
  name: "Intake Operations Dashboard",
  description: "Real-time monitoring of intake system performance",
  audience: ["ops_manager", "team_lead"],
  refreshInterval: "1m",

  layout: {
    grid: { columns: 4, rows: 6 },
    components: [
      // Row 1: Key metrics
      {
        id: "active_packets",
        type: "metric_card",
        title: "Active Packets",
        dataSource: "packets.active",
        refreshInterval: "1m",
        config: {
          metric: "active_packets",
          value: 127,
          format: "number",
          trend: { direction: "up", value: 12, period: "vs last hour" },
          status: "good"
        }
      },
      {
        id: "unassigned",
        type: "metric_card",
        title: "Unassigned",
        dataSource: "packets.unassigned",
        refreshInterval: "1m",
        config: {
          metric: "unassigned",
          value: 8,
          format: "number",
          trend: { direction: "down", value: 3, period: "vs last hour" },
          target: 10,
          status: "good"
        }
      },
      {
        id: "avg_response",
        type: "metric_card",
        title: "Avg Response Time",
        dataSource: "metrics.response_time",
        refreshInterval: "5m",
        config: {
          metric: "first_response_time",
          value: 18,
          format: "duration",
          trend: { direction: "down", value: 5, period: "vs yesterday" },
          target: 30,
          status: "good"
        }
      },
      {
        id: "sla_compliance",
        type: "gauge",
        title: "SLA Compliance",
        dataSource: "metrics.sla_compliance",
        refreshInterval: "5m",
        config: {
          value: 94.2,
          min: 0,
          max: 100,
          target: 90,
          zones: [
            { min: 0, max: 80, color: "red" },
            { min: 80, max: 90, color: "yellow" },
            { min: 90, max: 100, color: "green" }
          ]
        }
      },

      // Row 2-3: Agent status table
      {
        id: "agent_status",
        type: "table",
        title: "Agent Status",
        dataSource: "agents.status",
        refreshInterval: "1m",
        config: {
          columns: [
            { key: "name", label: "Agent" },
            { key: "status", label: "Status" },
            { key: "active_packets", label: "Active" },
            { key: "utilization", label: "Utilization", format: "percentage" },
            { key: "avg_response", label: "Avg Response", format: "duration" }
          ],
          sortBy: "utilization",
          sortOrder: "desc"
        }
      },

      // Row 4: Queue depths
      {
        id: "queue_depths",
        type: "bar_chart",
        title: "Queue Depths",
        dataSource: "queues.depth",
        refreshInterval: "5m",
        config: {
          horizontal: true,
          data: [
            { label: "General Pool", value: 45, target: 50 },
            { label: "Senior Agents", value: 18, target: 20 },
            { label: "Priority Queue", value: 8, target: 10 },
            { label: "Unassigned", value: 8, target: 5 }
          ]
        }
      },

      // Row 5-6: Recent activity
      {
        id: "recent_activity",
        type: "table",
        title: "Recent Activity",
        dataSource: "activity.recent",
        refreshInterval: "1m",
        config: {
          columns: [
            { key: "timestamp", label: "Time", format: "time_ago" },
            { key: "event", label: "Event" },
            { key: "packet_id", label: "Packet" },
            { key: "agent", label: "Agent" }
          ],
          limit: 20
        }
      }
    ]
  },

  filters: [
    {
      field: "date_range",
      type: "date_range",
      defaultValue: "today"
    },
    {
      field: "agency",
      type: "select",
      defaultValue: "all",
      options: [
        { label: "All Agencies", value: "all" },
        { label: "Agency A", value: "agency_a" },
        { label: "Agency B", value: "agency_b" }
      ]
    }
  ],

  actions: [
    {
      label: "Export Report",
      type: "export",
      config: { format: "csv" }
    },
    {
      label: "Refresh",
      type: "refresh",
      config: {}
    }
  ]
};
```

---

## 9. Alerting & Anomaly Detection

### 9.1 Alert Rules

```typescript
/**
 * Alert Configuration
 */

interface AlertRule {
  id: string;
  name: string;
  description: string;
  enabled: boolean;

  condition: AlertCondition;
  severity: "info" | "warning" | "critical";

  notification: AlertNotification;
  cooldown: number;                 // minutes between alerts
  escalation?: AlertEscalation;
}

interface AlertCondition {
  metric: string;
  operator: "gt" | "lt" | "eq" | "gte" | "lte";
  threshold: number;
  duration?: number;                // sustained for this many minutes
  aggregation?: "avg" | "sum" | "max" | "min";
  window?: number;                  // time window in minutes
}

interface AlertNotification {
  channels: NotificationChannel[];
  template: string;
}

type NotificationChannel =
  | "email"
  | "slack"
  | "push"
  | "sms"
  | "in_app";

interface AlertEscalation {
  steps: {
    delay: number;                  // minutes
    severity: "info" | "warning" | "critical";
    additionalChannels?: NotificationChannel[];
  }[];
}

// Example alert rules
const INTAKE_ALERT_RULES: AlertRule[] = [
  // SLA Breach Warning
  {
    id: "sla_breach_warning",
    name: "SLA Breach Warning",
    description: "Warn when response time approaches SLA limit",
    enabled: true,
    condition: {
      metric: "first_response_time_p95",
      operator: "gt",
      threshold: 0.8,               // 80% of SLA
      window: 15,
      aggregation: "avg"
    },
    severity: "warning",
    notification: {
      channels: ["slack", "in_app"],
      template: "⚠️ Response time at {{value}}min, approaching SLA of {{sla}}min"
    },
    cooldown: 30
  },

  // Unassigned Backlog
  {
    id: "unassigned_backlog",
    name: "Unassigned Backlog",
    description: "Alert when too many packets remain unassigned",
    enabled: true,
    condition: {
      metric: "unassigned_count",
      operator: "gt",
      threshold: 20,
      duration: 10                  // sustained for 10 minutes
    },
    severity: "warning",
    notification: {
      channels: ["slack", "email"],
      template: "📋 {{count}} packets unassigned for >10min"
    },
    cooldown: 15,
    escalation: {
      steps: [
        {
          delay: 30,
          severity: "critical",
          additionalChannels: ["sms"]
        }
      ]
    }
  },

  // Extraction Quality Drop
  {
    id: "extraction_quality_drop",
    name: "Extraction Quality Drop",
    description: "Alert when extraction accuracy drops significantly",
    enabled: true,
    condition: {
      metric: "extraction_accuracy",
      operator: "lt",
      threshold: 0.85,              // 85%
      window: 60,
      aggregation: "avg"
    },
    severity: "warning",
    notification: {
      channels: ["slack", "email"],
      template: "📉 Extraction accuracy dropped to {{accuracy}}%"
    },
    cooldown: 60
  },

  // Agent Overload
  {
    id: "agent_overload",
    name: "Agent Overload",
    description: "Alert when agents are consistently over capacity",
    enabled: true,
    condition: {
      metric: "overloaded_agents_count",
      operator: "gt",
      threshold: 3,
      duration: 15
    },
    severity: "warning",
    notification: {
      channels: ["slack", "in_app"],
      template: "⚖️ {{count}} agents operating above 90% capacity"
    },
    cooldown: 20
  },

  // Critical Queue Overflow
  {
    id: "critical_queue_overflow",
    name: "Critical Queue Overflow",
    description: "Alert when critical priority packets are backing up",
    enabled: true,
    condition: {
      metric: "critical_queue_depth",
      operator: "gt",
      threshold: 10
    },
    severity: "critical",
    notification: {
      channels: ["slack", "sms", "in_app"],
      template: "🚨 {{count}} CRITICAL packets in queue!"
    },
    cooldown: 5
  }
];
```

### 9.2 Anomaly Detection

```typescript
/**
 * Anomaly Detection Engine
 */

class AnomalyDetector {
  /**
   * Detect anomalies in metrics
   */
  async detectAnomalies(
    metric: string,
    historicalData: number[],
    currentValue: number,
    threshold: number = 2.5
  ): Promise<AnomalyResult | null> {
    // Calculate statistics
    const stats = this.calculateStatistics(historicalData);

    // Z-score based detection
    const zScore = Math.abs(
      (currentValue - stats.mean) / stats.stdDev
    );

    if (zScore > threshold) {
      return {
        metric,
        currentValue,
        expectedValue: stats.mean,
        deviation: currentValue - stats.mean,
        zScore,
        severity: zScore > 4 ? "critical" : "warning",
        direction: currentValue > stats.mean ? "high" : "low",
        confidence: this.calculateConfidence(zScore)
      };
    }

    return null;
  }

  /**
   * Detect trend anomalies
   */
  async detectTrendAnomaly(
    historicalData: number[]
  ): Promise<TrendAnomalyResult | null> {
    // Compare recent to historical trend
    const recent = historicalData.slice(-10);
    const historical = historicalData.slice(0, -10);

    const recentTrend = this.calculateTrend(recent);
    const historicalTrend = this.calculateTrend(historical);

    const trendChange = recentTrend - historicalTrend;

    // Sudden change in trend
    if (Math.abs(trendChange) > 0.3) {
      return {
        type: "trend_change",
        previousTrend: historicalTrend,
        currentTrend: recentTrend,
        change: trendChange,
        direction: trendChange > 0 ? "accelerating" : "decelerating",
        severity: Math.abs(trendChange) > 0.5 ? "critical" : "warning"
      };
    }

    return null;
  }

  private calculateStatistics(data: number[]): Statistics {
    const mean = data.reduce((a, b) => a + b, 0) / data.length;
    const variance = data.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / data.length;
    const stdDev = Math.sqrt(variance);

    return { mean, stdDev, variance };
  }

  private calculateTrend(data: number[]): number {
    // Simple linear regression slope
    const n = data.length;
    const xSum = (n * (n - 1)) / 2;
    const ySum = data.reduce((a, b) => a + b, 0);
    const xySum = data.reduce((a, b, i) => a + i * b, 0);
    const x2Sum = (n * (n - 1) * (2 * n - 1)) / 6;

    const slope = (n * xySum - xSum * ySum) / (n * x2Sum - xSum * xSum);
    return slope;
  }

  private calculateConfidence(zScore: number): number {
    // Convert z-score to confidence (rough approximation)
    if (zScore > 4) return 0.99;
    if (zScore > 3) return 0.95;
    return 0.90;
  }
}

interface Statistics {
  mean: number;
  stdDev: number;
  variance: number;
}

interface AnomalyResult {
  metric: string;
  currentValue: number;
  expectedValue: number;
  deviation: number;
  zScore: number;
  severity: "warning" | "critical";
  direction: "high" | "low";
  confidence: number;
}

interface TrendAnomalyResult {
  type: "trend_change";
  previousTrend: number;
  currentTrend: number;
  change: number;
  direction: "accelerating" | "decelerating";
  severity: "warning" | "critical";
}
```

---

## 10. Executive Reporting

### 10.1 Weekly Report Template

```typescript
/**
 * Weekly Executive Report
 */

interface WeeklyReport {
  period: {
    start: Date;
    end: Date;
    type: "weekly" | "monthly";
  };

  summary: {
    totalInquiries: number;
    conversionRate: number;
    revenue: number;
    vsLastPeriod: {
      inquiries: number;           // percentage change
      conversion: number;
      revenue: number;
    };
  };

  highlights: string[];
  concerns: string[];
  actions: {
    owner: string;
    action: string;
    dueDate: Date;
  }[];

  sections: ReportSection[];
}

interface ReportSection {
  title: string;
  content: SectionContent;
}

type SectionContent =
  | MetricSection
  | ChannelSection
  | TeamSection
  | QualitySection;

// Example: Generate weekly report
async function generateWeeklyReport(
  agencyId: string,
  period: DateRange
): Promise<WeeklyReport> {
  const metrics = await getAggregatedMetrics(agencyId, period);
  const lastPeriod = getPreviousPeriod(period);
  const lastMetrics = await getAggregatedMetrics(agencyId, lastPeriod);

  return {
    period: { start: period.start, end: period.end, type: "weekly" },
    summary: {
      totalInquiries: metrics.totalInquiries,
      conversionRate: metrics.conversionRate,
      revenue: metrics.revenue,
      vsLastPeriod: {
        inquiries: percentChange(metrics.totalInquiries, lastMetrics.totalInquiries),
        conversion: percentChange(metrics.conversionRate, lastMetrics.conversionRate),
        revenue: percentChange(metrics.revenue, lastMetrics.revenue)
      }
    },
    highlights: generateHighlights(metrics, lastMetrics),
    concerns: generateConcerns(metrics),
    actions: generateActionItems(metrics),
    sections: [
      {
        title: "Channel Performance",
        content: await generateChannelSection(metrics)
      },
      {
        title: "Team Productivity",
        content: await generateTeamSection(metrics)
      },
      {
        title: "Quality Metrics",
        content: await generateQualitySection(metrics)
      }
    ]
  };
}

function generateHighlights(
  current: AggregatedMetrics,
  previous: AggregatedMetrics
): string[] {
  const highlights: string[] = [];

  if (current.conversionRate > previous.conversionRate) {
    highlights.push(
      `Conversion rate improved to ${(current.conversionRate * 100).toFixed(1)}% ` +
      `(${percentChange(current.conversionRate, previous.conversionRate).toFixed(1)}% improvement)`
    );
  }

  if (current.avgResponseTime < previous.avgResponseTime) {
    highlights.push(
      `Response time reduced to ${current.avgResponseTime.toFixed(0)}min ` +
      `(${percentChange(current.avgResponseTime, previous.avgResponseTime).toFixed(1)}% faster)`
    );
  }

  return highlights;
}

function generateConcerns(metrics: AggregatedMetrics): string[] {
  const concerns: string[] = [];

  if (metrics.slaCompliance < 0.9) {
    concerns.push(
      `SLA compliance at ${(metrics.slaCompliance * 100).toFixed(1)}%, ` +
      `below target of 90%`
    );
  }

  if (metrics.unassignedRate > 0.15) {
    concerns.push(
      `${(metrics.unassignedRate * 100).toFixed(1)}% of packets remaining unassigned ` +
      `for >30 minutes`
    );
  }

  return concerns;
}

function generateActionItems(metrics: AggregatedMetrics): Action[] {
  const actions: Action[] = [];

  if (metrics.extractionAccuracy < 0.9) {
    actions.push({
      owner: "Quality Team",
      action: "Review extraction errors for top 3 underperforming fields",
      dueDate: addDays(new Date(), 3)
    });
  }

  return actions;
}
```

### 10.2 Report Delivery

```typescript
/**
 * Report Delivery System
 */

interface ReportDelivery {
  format: "email" | "pdf" | "dashboard" | "slack";
  schedule: DeliverySchedule;
  recipients: string[];
  template: string;
}

interface DeliverySchedule {
  frequency: "daily" | "weekly" | "monthly";
  dayOfWeek?: number;              // 0-6 for weekly
  time: string;                    // HH:MM format
  timezone: string;
}

// Example report configurations
const REPORT_CONFIGS: ReportDelivery[] = [
  {
    format: "email",
    schedule: {
      frequency: "weekly",
      dayOfWeek: 1,                // Monday
      time: "09:00",
      timezone: "Asia/Kolkata"
    },
    recipients: ["owner@agency.com", "ops@agency.com"],
    template: "weekly_executive_summary"
  },
  {
    format: "slack",
    schedule: {
      frequency: "daily",
      time: "18:00",
      timezone: "Asia/Kolkata"
    },
    recipients: ["#operations"],
    template: "daily_ops_summary"
  },
  {
    format: "dashboard",
    schedule: {
      frequency: "weekly",
      dayOfWeek: 1,
      time: "09:00",
      timezone: "Asia/Kolkata"
    },
    recipients: [],
    template: "weekly_performance_report"
  }
];
```

---

## Summary

The Intake Analytics system transforms raw intake data into actionable intelligence across four dimensions:

1. **Channel Performance** — Which channels drive value? Where are the bottlenecks?
2. **Extraction Quality** — How accurate is our extraction? What needs improvement?
3. **Triage & Routing** — Are we routing correctly? How effective is assignment?
4. **Customer Journey** — What's the conversion funnel? Where do we lose customers?

With real-time dashboards for operations, historical reports for insights, and predictive analytics for planning, agencies can continuously optimize their intake operations for maximum efficiency and conversion.

---

**Series Complete:** This concludes the Intake / Packet Processing Deep Dive Series (6 documents).

**Related Documents:**
- [Technical Deep Dive](INTAKE_01_TECHNICAL_DEEP_DIVE.md) — Architecture & Extraction Pipeline
- [UX/UI Deep Dive](INTAKE_02_UX_UI_DEEP_DIVE.md) — Packet Panel & Extraction Experience
- [Channel Integration Deep Dive](INTAKE_03_CHANNEL_INTEGRATION_DEEP_DIVE.md) — Multi-Channel Processing
- [Extraction Quality Deep Dive](INTAKE_04_EXTRACTION_QUALITY_DEEP_DIVE.md) — Quality Framework & Monitoring
- [Triage Strategies Deep Dive](INTAKE_05_TRIAGE_STRATEGIES_DEEP_DIVE.md) — Routing, Prioritization & Assignment
