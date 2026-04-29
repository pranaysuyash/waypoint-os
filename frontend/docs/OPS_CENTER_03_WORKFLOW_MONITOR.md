# Agency Operations Command Center — Workflow Monitor

> Research document for workflow monitoring, bottleneck detection, trip pipeline velocity, SLA monitoring, process mining, and India-specific regulatory deadline tracking.

---

## Key Questions

1. **How do we measure trip pipeline velocity and detect bottlenecks in real-time?**
2. **What time-in-stage metrics define healthy operations, and what thresholds indicate problems?**
3. **How do we detect "stuck" trips — trips that have been idle beyond acceptable limits?**
4. **What SLA targets apply to each workflow stage, and how do we monitor them?**
5. **Can we apply process mining to trip event data to discover actual (vs. designed) workflows?**
6. **What automated interventions prevent bottlenecks before they impact customers?**

---

## Research Areas

### Pipeline Velocity Data Model

```typescript
interface TripPipeline {
  pipelineId: string;
  period: DateRange;

  // Funnel metrics
  stages: PipelineStage[];
  totalTripsInPipeline: number;

  // Velocity
  avgTimeToIntake: string;               // From inquiry to intake complete
  avgTimeToQuote: string;                // From intake to first quote
  avgTimeToBooking: string;              // From quote to booking confirmed
  avgTimeToTravel: string;               // From booking to travel date
  avgTotalCycleTime: string;             // End-to-end

  // Throughput
  tripsEntered: number;                  // New trips this period
  tripsCompleted: number;                // Trips that exited pipeline
  tripsCancelled: number;
  netChange: number;                     // Entered - Completed - Cancelled
}

interface PipelineStage {
  stageName: string;
  displayName: string;

  // Counts
  tripsInStage: number;
  tripsEnteredThisPeriod: number;
  tripsExitedThisPeriod: number;

  // Time metrics
  avgTimeInStage: string;                // e.g., "2h 15m"
  medianTimeInStage: string;
  p95TimeInStage: string;
  longestTimeInStage: string;            // Current worst case

  // Health
  slaTarget: string;
  slaCompliancePercent: number;
  atRiskCount: number;                   // Approaching SLA
  breachedCount: number;                 // Past SLA
  stuckCount: number;                    // No activity for >threshold

  // Capacity
  assignedAgents: number;
  avgLoadPerAgent: number;
  maxLoadPerAgent: number;
}

// Pipeline stages for a typical Indian travel agency:
//
// ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
// │  INTAKE  │───→│ QUOTING  │───→│ REVIEW   │───→│ BOOKING  │
// │  30 min  │    │  2-4 hrs │    │  1-2 hrs │    │  4-24 hr │
// └──────────┘    └──────────┘    └──────────┘    └──────────┘
//       │              │               │               │
//       ▼              ▼               ▼               ▼
//   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
//   │ Lost/    │   │ Revised  │   │ Approved │   │ Confirmed│
//   │ Spam     │   │ Quote    │   │ Rejected │   │ Waitlist │
//   └──────────┘   └──────────┘   └──────────┘   └──────────┘
//                                                    │
//                                          ┌─────────▼──────────┐
//                                          │    PRE-TRAVEL      │
//                                          │ Docs, Visa, Insure │
//                                          │    7-30 days       │
//                                          └─────────┬──────────┘
//                                                    │
//                                          ┌─────────▼──────────┐
//                                          │    TRAVELING       │
//                                          │  On-trip support   │
//                                          │    1-14 days       │
//                                          └─────────┬──────────┘
//                                                    │
//                                          ┌─────────▼──────────┐
//                                          │   POST-TRAVEL      │
//                                          │ Feedback, Settle   │
//                                          │    3-7 days        │
//                                          └────────────────────┘
```

### Time-in-Stage Metrics

```typescript
interface StageTimeMetrics {
  stageName: string;
  period: DateRange;

  // Distribution
  mean: number;                          // milliseconds
  median: number;
  p75: number;
  p90: number;
  p95: number;
  p99: number;
  max: number;

  // Segments
  byTripType: Record<TripType, StageTimeStats>;
  byDestination: Record<string, StageTimeStats>;  // Domestic vs International
  byAgent: Record<string, StageTimeStats>;
  byServiceType: Record<string, StageTimeStats>;

  // Trends
  trendVsLastPeriod: number;             // % change
  trendVsLastMonth: number;
  isImproving: boolean;
}

interface StageTimeStats {
  count: number;
  mean: number;
  median: number;
  p95: number;
}

type TripType =
  | 'domestic_package'
  | 'international_package'
  | 'flight_only'
  | 'hotel_only'
  | 'custom_itinerary'
  | 'group_tour'
  | 'corporate'
  | 'mice';

// Benchmark time-in-stage (Indian travel agency, typical):
//
// ┌────────────────┬──────────┬──────────┬──────────┬─────────────────────────┐
// │ Stage          │ Target   │ Warning  │ Breach   │ Notes                   │
// ├────────────────┼──────────┼──────────┼──────────┼─────────────────────────┤
// │ Intake         │ 30 min   │ 20 min   │ 45 min   │ Call/chat → data entry  │
// │ Quoting        │ 2 hrs    │ 1.5 hrs  │ 4 hrs    │ First quote to customer │
// │ Quote Review   │ 1 hr     │ 45 min   │ 2 hrs    │ Manager/senior reviews  │
// │ Booking Init   │ 4 hrs    │ 3 hrs    │ 8 hrs    │ Supplier reservations   │
// │ Payment Confirm│ 24 hrs   │ 18 hrs   │ 48 hrs   │ Waiting for customer $  │
// │ Doc Prep       │ 3 days   │ 2 days   │ 5 days   │ Visa, insurance, etc.   │
// │ Pre-Travel     │ 1 day    │ 6 hrs    │ 2 days   │ Final confirmations     │
// │ On-Trip        │ 15 min*  │ 10 min   │ 30 min   │ *response to issue      │
// │ Post-Travel    │ 3 days   │ 2 days   │ 7 days   │ Settlement & feedback   │
// └────────────────┴──────────┴──────────┴──────────┴─────────────────────────┘
```

### Stuck Trip Detection

```typescript
interface StuckTripRule {
  ruleId: string;
  stageName: string;
  tripType?: TripType;                   // Optional override by trip type
  noActivityThreshold: string;           // e.g., "2h" for quoting stage
  slaThreshold: string;                  // When SLA is breached
  detectionCriteria: StuckCriteria[];
  autoActions: AutoAction[];
}

interface StuckCriteria {
  type: 'no_activity' | 'sla_approaching' | 'sla_breached' | 'waiting_on_customer' | 'waiting_on_supplier' | 'waiting_on_approval';
  threshold: string;
  excludeConditions?: string[];          // e.g., "customer.responsive == false"
}

interface AutoAction {
  type: 'remind_agent' | 'remind_customer' | 'escalate' | 'reassign' | 'flag_for_review';
  delay: string;                         // Wait before taking action
  channel?: NotificationChannel;
  messageTemplate?: string;
}

// Stuck trip detection rules:
//
// Stage: INTAKE
//   - No activity > 30 min → remind agent (in-app)
//   - No activity > 45 min → escalate to team lead (push + SMS)
//   - Waiting on customer > 2h → auto-send WhatsApp reminder
//
// Stage: QUOTING
//   - No activity > 2h → remind agent (in-app)
//   - No activity > 4h → escalate to team lead (push)
//   - Waiting on supplier pricing > 3h → flag supplier, remind agent
//   - Customer hasn't responded to quote > 24h → auto-follow-up (WhatsApp/email)
//
// Stage: BOOKING
//   - No activity > 4h → remind agent (in-app)
//   - Payment not received > 24h → remind customer (SMS + email)
//   - Payment not received > 48h → escalate, flag at-risk
//   - Supplier not confirming > 6h → re-attempt, flag alternative suppliers

interface StuckTripAlert {
  tripId: string;
  tripName: string;
  stageName: string;
  stuckDuration: string;
  stuckReason: string;
  lastActivity: Date;
  lastActivityType: string;
  assignedAgent: string;
  suggestedActions: string[];
  autoActionsTaken: string[];
  customerImpact: 'low' | 'medium' | 'high';
}
```

### SLA Monitoring

```typescript
interface SLAMonitor {
  monitorId: string;
  period: DateRange;

  // Overall SLA health
  overallCompliance: number;             // Percentage
  totalSLABreaches: number;
  breachesByStage: Record<string, number>;
  breachesByAgent: Record<string, number>;

  // Active SLA tracking
  activeTripsWithSLA: ActiveSLATrip[];

  // SLA trends
  complianceTrend: TrendDataPoint[];     // Daily for last 30 days
  breachCauseBreakdown: Record<string, number>;
}

interface ActiveSLATrip {
  tripId: string;
  tripName: string;
  currentStage: string;
  stageEnteredAt: Date;
  slaTarget: string;                     // Time allowed
  timeRemaining: string;                 // Positive = within SLA, negative = breached
  status: 'within_sla' | 'approaching' | 'at_risk' | 'breached';
  assignedAgent: string;
  customerName: string;
  tripValue: Money;
}

// SLA compliance dashboard:
//
// ┌─────────────────────────────────────────────────────────────────────┐
// │  SLA COMPLIANCE — This Week                         94.2% ████████ │
// ├────────────┬────────┬────────┬────────┬────────┬────────────────────┤
// │ Stage      │ Within │ At Risk│Breached│ Total  │ Trend              │
// ├────────────┼────────┼────────┼────────┼────────┼────────────────────┤
// │ Intake     │   38   │    2   │    0   │   40   │ 100% ████████████ │
// │ Quoting    │   28   │    4   │    3   │   35   │  91% ███████████  │
// │ Review     │   15   │    1   │    0   │   16   │  94% ███████████  │
// │ Booking    │   22   │    5   │    2   │   29   │  86% ██████████   │
// │ Doc Prep   │   18   │    2   │    1   │   21   │  90% ███████████  │
// │ Pre-Travel │    8   │    0   │    0   │    8   │ 100% ████████████ │
// └────────────┴────────┴────────┴────────┴────────┴────────────────────┘
//
// Breached Trips (requires immediate attention):
// ────────────────────────────────────────────
// 🔴 TRP-4213  Goa Package    Booking   6h overdue   Amit
// 🔴 TRP-4187  Thailand Tour  Quoting   2h overdue   Priya
// 🟡 TRP-4191  Kerala Trip    Doc Prep  30min left   Ravi
```

### Process Mining from Trip Events

```typescript
interface ProcessMiningResult {
  // Discovered workflow: what actually happens
  discoveredProcess: ProcessNode[];
  discoveredEdges: ProcessEdge[];

  // Deviations from designed process
  deviations: ProcessDeviation[];

  // Variants: common paths through the workflow
  variants: ProcessVariant[];

  // Bottlenecks: stages with high wait times
  bottlenecks: DetectedBottleneck[];

  // Rework: stages that are repeated (quality issues)
  reworkPoints: ReworkPoint[];
}

interface ProcessNode {
  stageName: string;
  avgDuration: number;
  visitCount: number;                    // How many trips pass through
  exitRate: number;                      // % of trips that exit pipeline here
}

interface ProcessEdge {
  from: string;
  to: string;
  frequency: number;                     // How many trips took this path
  avgTransitionTime: number;
  isExpectedPath: boolean;               // True if this matches designed workflow
}

interface ProcessDeviation {
  type: 'skip_stage' | 'repeat_stage' | 'unusual_path' | 'missing_step';
  description: string;
  affectedTrips: number;
  percentOfTotal: number;
  exampleTripIds: string[];
  impact: 'low' | 'medium' | 'high';
}

interface ProcessVariant {
  name: string;                          // e.g., "Standard Domestic", "Fast-Track Corporate"
  path: string[];                        // Stage sequence
  frequency: number;                     // How many trips follow this path
  avgDuration: number;
  avgOutcome: 'successful' | 'cancelled' | 'delayed';
}

interface DetectedBottleneck {
  stageName: string;
  avgWaitTime: number;
  maxWaitTime: number;
  affectedTrips: number;
  rootCauses: string[];                  // Inferred from data
  suggestedActions: string[];
}

interface ReworkPoint {
  stageName: string;
  reworkRate: number;                    // % of trips that revisit this stage
  avgReworkCount: number;
  commonReasons: string[];
  costEstimate: Money;                   // Estimated cost of rework
}

// Example process mining findings:
//
// Designed process: INTAKE → QUOTING → REVIEW → BOOKING → DOCS → TRAVEL
//
// Variant 1 (68% of trips): Standard path — matches design
// Variant 2 (15% of trips): INTAKE → QUOTING → QUOTING (rework) → REVIEW → ...
//   Root cause: Incomplete pricing on first quote attempt
//   Suggested: Improve supplier price fetching, add pre-quote checklist
//
// Variant 3 (8% of trips): INTAKE → QUOTING → REVIEW → QUOTING (back to quoting)
//   Root cause: Manager rejects quote, sends back for revision
//   Suggested: Add manager guidelines, pre-review checklist
//
// Variant 4 (5% of trips): INTAKE → BOOKING (skip quoting)
//   Root cause: Repeat customer, same itinerary as before
//   Suggested: Allow "express path" for repeat bookings
//
// Bottleneck detected: QUOTING stage
//   Average wait: 3.5 hours (target: 2 hours)
//   42% of trips spend >4 hours in quoting
//   Root causes: Supplier API delays (35%), Agent unavailable (25%),
//                Complex itinerary (20%), Waiting for group confirmation (20%)
```

### Bottleneck Visualization

```typescript
interface BottleneckVisualization {
  // Funnel chart: trips at each stage
  funnel: FunnelData;

  // Stage duration heatmap
  heatmap: HeatmapData;

  // Timeline chart: stage duration over time
  timeline: TimelineData;

  // Sankey diagram: actual trip paths
  sankey: SankeyData;
}

interface FunnelData {
  stages: FunnelStage[];
  dropoffPoints: DropoffPoint[];
}

interface FunnelStage {
  name: string;
  count: number;
  percentOfTotal: number;
  avgTime: string;
  dropoffToNext: number;                 // Trips lost between this and next stage
  dropoffPercent: number;
}

// Funnel visualization (typical month):
//
// Inquiries Received    500  ████████████████████████████████████████  100%
// Intake Completed      420  ██████████████████████████████████        84%  (80 lost/spam)
// Quotes Sent           350  ███████████████████████████████           70%  (70 lost/unresponsive)
// Quotes Accepted       180  █████████████████                         36%  (170 went elsewhere)
// Booking Initiated     165  ███████████████                           33%  (15 cancelled during booking)
// Booking Confirmed     150  ██████████████                            30%  (15 payment issues)
// Docs Complete          140  █████████████                            28%  (10 visa/insurance delays)
// Traveling              135  █████████████                            27%  (5 postponed)
// Completed              130  ████████████                             26%  (5 cancelled on-trip)
//
// Key metrics:
//   Inquiry → Booking: 30% conversion
//   Inquiry → Completed: 26% conversion
//   Biggest dropoff: Quote → Accepted (51% drop)
//   Recommended: Improve quote quality, add urgency triggers

interface HeatmapData {
  // Rows: stages, Columns: hours of day or days of week
  // Value: average time-in-stage or volume
  // Shows patterns like "quoting takes longer on Monday mornings"
  rows: string[];
  columns: string[];
  values: number[][];
}

// Heatmap example (stage × day of week, avg hours):
//
//            Mon   Tue   Wed   Thu   Fri   Sat   Sun
// Intake     0.3   0.4   0.3   0.5   0.8   1.2   0.9    ← Weekend slower
// Quoting    2.1   2.0   2.3   2.5   3.1   4.2   3.5    ← Weekend much slower
// Review     0.8   0.7   0.9   1.0   1.5   2.0   1.8
// Booking    3.5   3.2   3.0   3.8   4.5   5.2   4.8    ← Fri-Sun bottleneck
// Doc Prep   2.0   1.8   2.0   2.2   2.5   3.0   2.8
```

### Automated Intervention Triggers

```typescript
interface InterventionTrigger {
  triggerId: string;
  name: string;
  description: string;
  enabled: boolean;

  // When to fire
  conditions: InterventionCondition[];

  // What to do
  actions: InterventionAction[];

  // Limits
  maxTriggersPerHour: number;
  cooldownPeriod: string;                // Min time between triggers for same entity
}

interface InterventionCondition {
  metric: string;
  operator: ComparisonOperator;
  value: number | string;
  timeWindow?: string;                   // e.g., "last_1_hour"
}

interface InterventionAction {
  type: 'reassign' | 'notify' | 'auto_respond' | 'create_task' | 'adjust_sla' | 'page_on_call';
  config: Record<string, unknown>;
}

// Intervention rules:
//
// 1. Auto-assign when overloaded:
//    IF agent has >15 active trips AND new trip enters intake
//    THEN assign to least-loaded agent in same team
//    AND notify team lead
//
// 2. SLA boundary reminder:
//    IF trip is within 80% of SLA target for current stage
//    THEN send in-app + push notification to assigned agent
//    AND include suggested next action
//
// 3. Supplier non-response:
//    IF supplier hasn't responded in 3 hours during business hours
//    THEN auto-retry request
//    AND flag alternative suppliers
//    AND notify agent with options
//
// 4. Customer waiting too long:
//    IF customer hasn't received update in 4 hours (during business hours)
//    THEN auto-send status update (WhatsApp/email)
//    WITH estimated time for next update
//
// 5. Agent idle with pending tasks:
//    IF agent has no activity for 30 min AND has trips in active stages
//    THEN send reminder with task list
//    AND notify team lead if no response in 15 min

// India-specific intervention triggers:

interface IndiaRegulatoryTrigger {
  triggerId: string;
  type: 'gst_deadline' | 'tcs_deposit' | 'tds_filing' | 'iata_bsp' | 'pf_esi';
  description: string;

  // When to fire
  advanceWarningDays: number[];          // e.g., [7, 3, 1, 0]
  deadline: string;                      // e.g., "11th of every month" for GSTR-3B

  // Who to notify
  recipients: RoutingRecipient[];

  // What to check
  preConditions: string[];
  postActions: string[];
}

// India regulatory deadline calendar:
//
// GST Deadlines:
//   GSTR-1 (outward supplies): 11th of following month
//   GSTR-3B (summary return): 20th of following month
//   GSTR-9 (annual return): December 31 of following year
//   Advance warning: 7 days, 3 days, 1 day, day-of
//
// TCS (Tax Collected at Source):
//   Deposit to government: 7th of following month
//   Quarterly certificate issuance: Within 15 days of quarter end
//   Advance warning: 5 days, 2 days, 1 day, day-of
//
// TDS (Tax Deducted at Source):
//   Deposit to government: 7th of following month
//   Quarterly return filing: Form 26Q/27Q by 31st of following quarter
//   Advance warning: 7 days, 3 days, 1 day
//
// IATA BSP (Billing and Settlement Plan):
//   BSP billing period: 1st-15th and 16th-end of month
//   Settlement date: Typically 15 days after billing period
//   Advance warning: 5 days before settlement
//
// PF/ESI:
//   PF contribution deposit: 15th of following month
//   ESI contribution deposit: 15th of following month
//   Advance warning: 5 days, 2 days, 1 day
```

### Workflow Monitor Dashboard Wireframe

```typescript
// ┌─────────────────────────────────────────────────────────────────────┐
// │  WORKFLOW MONITOR                              Pipeline: 142 trips │
// ├─────────────────────────────────────────────────────────────────────┤
// │  [Overview] [SLA] [Bottlenecks] [Process Mining] [Regulatory]     │
// ├─────────────────────────────────────────────────────────────────────┤
// │                                                                     │
// │  TRIP PIPELINE FUNNEL                                              │
// │  ████████████████████████████████████████████████████  45 Intake    │
// │  ██████████████████████████████████████████████████    35 Quoting   │
// │  ████████████████████████████████████████              16 Review    │
// │  ████████████████████████████████████                  29 Booking   │
// │  ████████████████████████████                          21 Doc Prep  │
// │  ██████████████████████████                            8  Pre-Travel│
// │  ██████████████████████████████                        12 Traveling │
// │  ████████████████████████████                          10 Post      │
// │                                                                     │
// │  VELOCITY                │  SLA COMPLIANCE       │  STUCK TRIPS     │
// │  Avg cycle: 6.2 days     │  Overall: 94.2%       │  5 need attention│
// │  This week: 6.0 days     │  Today: 96.1%         │  Oldest: 8h      │
// │  Trend: ↑ improving      │  Breaches: 3          │  2 in Quoting    │
// │  Best agent: Priya 4.1d  │  At risk: 7           │  2 in Booking    │
// │                          │  Breached: TRP-4213   │  1 in Doc Prep   │
// │  BOTTLENECK DETECTED     │                       │                  │
// │  ⚠ Quoting stage        │  REGULATORY DEADLINES │  [View All]      │
// │  Avg 3.5h vs target 2h  │  GSTR-1: 3 days       │                  │
// │  42% exceed 4h target   │  TCS deposit: 5 days  │                  │
// │  Root: Supplier API     │  PF deposit: 7 days   │                  │
// │  [View Details]         │  [View Calendar]       │                  │
// │                                                                     │
// └─────────────────────────────────────────────────────────────────────┘
```

---

## Open Problems

1. **Process mining accuracy** — Trip events may not capture every real-world step. An agent might call a supplier but not log it. Incomplete event data leads to false bottleneck detection.

2. **SLA target calibration** — Setting SLA targets too tight causes constant breaches and alert fatigue. Setting them too loose means slow service. Need data-driven calibration with historical baseline.

3. **Cross-team dependencies** — A trip stuck in "Booking" might be because the finance team hasn't approved a credit limit. The monitor needs to trace bottlenecks across team boundaries, not just within one team.

4. **Seasonal variation** — Peak travel seasons (summer holidays, Diwali, Christmas) naturally increase pipeline volume and times. SLA targets should adjust for seasonality.

5. **India regulatory complexity** — GST filing dates, TCS deposit deadlines, and state-specific tourism board requirements create a complex calendar. Missing one is a compliance violation. The system needs a comprehensive regulatory calendar with state-level granularity.

6. **Attribution of delays** — When a trip is slow, is it the agent, the supplier, the customer, or the system? The monitor needs to distinguish between "agent didn't act" vs. "supplier didn't respond" vs. "customer is unresponsive."

---

## Next Steps

- [ ] Instrument the trip lifecycle with granular event tracking for every stage transition
- [ ] Collect 30 days of baseline pipeline data to calibrate SLA targets
- [ ] Research process mining libraries (pm4py, Fluxicon Disco, Apromore)
- [ ] Build India regulatory deadline calendar with automated triggers
- [ ] Design bottleneck root-cause analysis algorithm
- [ ] Prototype the pipeline funnel visualization with real event data
- [ ] Evaluate seasonal SLA adjustment models
- [ ] Study Sankey diagram libraries for process path visualization (d3-sankey, plotly)
