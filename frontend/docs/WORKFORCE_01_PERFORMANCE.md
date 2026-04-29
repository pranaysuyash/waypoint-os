# Agent Performance & Workforce Management — Performance Metrics

> Research document for agent performance measurement, KPI frameworks, performance dashboards, goal tracking, review workflows, and India-specific salary structures and incentive models.

---

## Key Questions

1. **What are the right performance metrics for travel agents in an Indian agency context?**
2. **How do we build a KPI framework that balances revenue, customer satisfaction, and operational efficiency?**
3. **What does a real-time performance dashboard look like for agents, team leads, and agency owners?**
4. **How do we design goal-setting (individual + team) with fair, transparent tracking?**
5. **What is the performance review workflow for quarterly and annual cycles?**
6. **How do India-specific salary structures, incentive models, and statutory compliance shape performance management?**

---

## Research Areas

### Core Performance Metrics

```typescript
interface AgentPerformanceMetrics {
  agentId: string;
  period: MetricPeriod;
  conversion: ConversionMetrics;
  responsiveness: ResponsivenessMetrics;
  revenue: RevenueMetrics;
  quality: QualityMetrics;
  operational: OperationalMetrics;
}

type MetricPeriod =
  | 'daily'
  | 'weekly'
  | 'monthly'
  | 'quarterly'
  | 'annual';

interface ConversionMetrics {
  // Lead → Quote → Booking pipeline
  leadsReceived: number;
  quotesSent: number;
  bookingsConfirmed: number;
  leadToQuoteRate: number;            // % leads that receive a quote
  quoteToBookingRate: number;         // % quotes that convert to confirmed booking
  overallConversionRate: number;      // % leads that become confirmed bookings
  averageTimeToQuote: number;         // Hours from lead to first quote
  averageTimeToConfirm: number;       // Days from lead to confirmed booking
}

// Indian agency benchmarks (research-derived):
// Lead-to-Quote: 70-85% (agents who respond fast)
// Quote-to-Booking: 25-40% (varies by destination complexity)
// Overall Conversion: 18-30%
// Time to Quote: <4 hours is excellent, >24 hours is poor
// Time to Confirm: 3-7 days average, >14 days is slow
//
// Seasonal adjustments:
// Peak season (Oct-Mar for international, Apr-Jun for domestic):
//   Higher lead volume, faster conversion, more competitive
// Off-season (Jul-Sep monsoon):
//   Lower volume, slower conversion, discount-driven

interface ResponsivenessMetrics {
  averageFirstResponseTime: number;   // Minutes
  averageReplyTime: number;           // Minutes per message
  responseTimeByChannel: Record<Channel, number>;
  slaComplianceRate: number;          // % responses within SLA
  afterHoursResponseRate: number;     // % responses outside shift
  customerWaitTime: number;           // Average customer wait (minutes)
}

type Channel =
  | 'whatsapp'
  | 'email'
  | 'phone'
  | 'instagram'
  | 'website_chat';

// Response time SLA targets:
// WhatsApp: <15 minutes (during shift)
// Phone: Immediate or callback within 10 minutes
// Email: <2 hours (during shift)
// Instagram DM: <30 minutes (during shift)
// Website chat: <5 minutes (live chat hours)
//
// India reality check:
// - WhatsApp is primary (>60% of customer communication)
// - Agents juggle 3-5 conversations simultaneously
// - Peak inquiry times: 10-11 AM, 2-3 PM, 8-9 PM
// - Sunday queries often go unanswered until Monday

interface RevenueMetrics {
  totalRevenue: number;               // INR
  revenuePerTrip: number;             // Average booking value
  revenuePerLead: number;             // Revenue / leads received
  marginPercentage: number;           // Gross margin on bookings
  upsellRevenue: number;              // Revenue from add-ons (insurance, forex, activities)
  ancillaryRevenue: number;           // Visa, insurance, forex, airport transfers
  averageTripValue: number;           // INR per confirmed trip
  revenueGrowth: number;              // % growth vs previous period
}

// Revenue benchmarks (Indian mid-size agency):
// Average trip value: ₹35,000 (domestic) to ₹1,50,000 (international)
// Margin: 8-15% (flights low, packages high)
// Ancillary revenue: 5-10% of total
// Top agents: ₹8-15 lakh revenue/month
// Average agents: ₹3-6 lakh revenue/month

interface QualityMetrics {
  customerNPS: number;                // Net Promoter Score (-100 to +100)
  customerCSAT: number;               // Customer Satisfaction (1-5)
  complaintRate: number;              // % trips with complaints
  repeatCustomerRate: number;         // % customers who book again
  referralRate: number;               // % customers who refer others
  documentAccuracyRate: number;       // % error-free documents first time
  tripModificationRate: number;       // % trips requiring post-booking changes
  cancellationRate: number;           // % confirmed trips cancelled
}

// NPS benchmarks for Indian travel:
// World-class: 60+
// Good: 40-60
// Average: 20-40
// Needs improvement: <20
//
// Indian customer expectations:
// - High-touch communication (frequent updates)
// - Price transparency (hidden fees = immediate trust loss)
// - Visa/document handling reliability
// - Emergency support during trip

interface OperationalMetrics {
  tripsHandled: number;               // Total trips in period
  tripsInProgress: number;            // Currently active
  tripsCompleted: number;             // Successfully completed
  averageHandlingTime: number;        // Hours per trip (start to confirmed)
  reworkRate: number;                 // % trips requiring major revision
  systemUtilization: number;          // % of shift time on platform
  taskCompletionRate: number;         // % tasks completed on time
  knowledgeBaseContributions: number; // KB articles/updates authored
  mentorshipHours: number;            // Hours spent mentoring juniors
}
```

### KPI Framework

```typescript
interface KPIFramework {
  agentRole: AgentRole;
  level: AgentLevel;
  kpis: KPIDefinition[];
  weights: KPIWeightSet;
  targets: KPITargetSet;
}

type AgentRole =
  | 'junior_agent'                    // Entry-level, domestic focus
  | 'senior_agent'                    // Experienced, international capable
  | 'specialist'                      // Cruise / MICE / Corporate / Honeymoon
  | 'team_lead'                       // Manages 4-8 agents
  | 'branch_manager';                 // Manages branch + P&L

type AgentLevel =
  | 'L1'  // Trainee (0-6 months)
  | 'L2'  // Junior (6-18 months)
  | 'L3'  // Mid (18-36 months)
  | 'L4'  // Senior (3-5 years)
  | 'L5'  // Lead / Expert (5+ years);

interface KPIDefinition {
  id: string;
  name: string;
  category: KPICategory;
  description: string;
  unit: string;                       // "%", "INR", "minutes", "score"
  direction: 'higher_is_better' | 'lower_is_better';
  frequency: MetricPeriod;
  dataSource: string;                 // Where the metric comes from
  calculationMethod: string;          // How it's computed
}

type KPICategory =
  | 'revenue'                         // Revenue generation
  | 'conversion'                      // Lead conversion efficiency
  | 'responsiveness'                  // Speed of customer response
  | 'quality'                         // Customer satisfaction
  | 'operations'                      // Operational efficiency
  | 'growth';                         // Professional development

interface KPIWeightSet {
  // Weights must sum to 100%
  revenue: number;                    // Default: 30%
  conversion: number;                 // Default: 20%
  responsiveness: number;             // Default: 15%
  quality: number;                    // Default: 20%
  operations: number;                 // Default: 10%
  growth: number;                     // Default: 5%
}

// Weight adjustments by role:
// Junior Agent:   Revenue 20%, Conversion 25%, Responsiveness 20%, Quality 15%, Operations 15%, Growth 5%
// Senior Agent:   Revenue 35%, Conversion 20%, Responsiveness 10%, Quality 20%, Operations 10%, Growth 5%
// Specialist:     Revenue 25%, Conversion 15%, Responsiveness 10%, Quality 30%, Operations 10%, Growth 10%
// Team Lead:      Revenue 20%, Conversion 10%, Responsiveness 5%,  Quality 25%, Operations 25%, Growth 15%
// Branch Manager: Revenue 30%, Conversion 10%, Responsiveness 5%,  Quality 20%, Operations 20%, Growth 15%

interface KPITargetSet {
  agentId: string;
  period: MetricPeriod;
  targets: KPITarget[];
  setBy: string;                      // Manager ID
  approvedBy?: string;                // Director ID (for senior+)
  setAt: Date;
}

interface KPITarget {
  kpiId: string;
  baseline: number;                   // Current/previous performance
  target: number;                     // Goal for this period
  stretch: number;                    // Stretch goal (110-120% of target)
  minimum: number;                    // Minimum acceptable (below = PIP)
}
```

### Performance Dashboard

```typescript
interface PerformanceDashboard {
  // Role-specific dashboard views
  agentView: AgentDashboard;
  teamLeadView: TeamLeadDashboard;
  ownerView: AgencyOwnerDashboard;
}

// AGENT VIEW: Personal performance snapshot
// ┌──────────────────────────────────────────────────────────────────┐
// │  My Performance — April 2026                  [Monthly] [Quarter]│
// ├──────────────────────────────────────────────────────────────────┤
// │                                                                  │
// │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
// │  │ Revenue  │ │ Convers. │ │ Response │ │   NPS    │           │
// │  │ ₹4.2L    │ │  24.8%   │ │  12 min  │ │   52     │           │
// │  │ ↑8%      │ │ ↑3.2%    │ │ ↓2 min   │ │  ↑5 pts  │           │
// │  │ 84% tgt  │ │ 92% tgt  │ │ 96% tgt  │ │ 87% tgt  │           │
// │  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
// │                                                                  │
// │  Revenue Trend (30 days)                                         │
// │  ▁▂▃▅▇█▇▅▆▇██▇▅▃  ← Daily revenue chart                       │
// │                                                                  │
// │  Conversion Funnel        My Trips                               │
// │  Leads:    45 ████████   Active: 12 ████                         │
// │  Quotes:   32 ██████     Pending: 5  ██                          │
// │  Bookings: 11 ███        Confirmed: 7 ███                        │
// │                                                                  │
// │  Recent Reviews                                                  │
// │  ★★★★★ Rajesh — "Excellent Kerala trip planning"                │
// │  ★★★★☆ Priya — "Good but visa processing was slow"              │
// │  ★★★★★ Amit  — "Perfect Goa weekend arrangement"                │
// │                                                                  │
// │  Upcoming Goals                                                  │
// │  □ Hit ₹5L monthly revenue (84% → need ₹80K more)               │
// │  □ Achieve 30% conversion rate (24.8% → need 5.2% more)         │
// │  □ NPS score 55+ (52 → need 3 more points)                      │
// └──────────────────────────────────────────────────────────────────┘

// TEAM LEAD VIEW: Team performance grid
// ┌──────────────────────────────────────────────────────────────────┐
// │  Team Performance — April 2026          [This Month] [Quarterly] │
// ├──────────────────────────────────────────────────────────────────┤
// │                                                                  │
// │  Team Summary                                                    │
// │  Revenue: ₹28.4L (↑12%) | Trips: 148 (↑8%) | NPS: 48 (↑3)     │
// │                                                                  │
// │  Agent Leaderboard                                               │
// │  ┌──────────┬────────┬────────┬─────────┬──────┬───────┐        │
// │  │ Agent    │ Revenue│ Conv%  │ Response│ NPS  │ Trend │        │
// │  ├──────────┼────────┼────────┼─────────┼──────┼───────┤        │
// │  │ Vikram S │ ₹6.1L  │ 32%    │ 8 min   │ 62   │ ↑↑    │        │
// │  │ Neha P   │ ₹5.4L  │ 28%    │ 10 min  │ 58   │ ↑     │        │
// │  │ Arjun M  │ ₹4.2L  │ 25%    │ 12 min  │ 52   │ →     │        │
// │  │ Sneha R  │ ₹3.8L  │ 22%    │ 14 min  │ 48   │ ↑     │        │
// │  │ Rohit K  │ ₹3.1L  │ 20%    │ 18 min  │ 42   │ ↓     │        │
// │  │ Pooja D  │ ₹2.8L  │ 18%    │ 22 min  │ 38   │ ↓↓    │        │
// │  └──────────┴────────┴────────┴─────────┴──────┴───────┘        │
// │                                                                  │
// │  🔴 Needs Attention: Rohit K (response time), Pooja D (NPS)     │
// │  🟢 Stars: Vikram S (all metrics above target)                  │
// └──────────────────────────────────────────────────────────────────┘

// AGENCY OWNER VIEW: Business-wide analytics
// ┌──────────────────────────────────────────────────────────────────┐
// │  Agency Performance Dashboard — FY 2026-27 Q1                    │
// ├──────────────────────────────────────────────────────────────────┤
// │                                                                  │
// │  Revenue: ₹1.24Cr (↑18% YoY)  |  Margin: 11.2% (↑0.8%)        │
// │  Trips: 1,248 (↑15%)          |  NPS: 46 (↑4 pts)              │
// │  Active Agents: 32            |  Utilization: 78%               │
// │                                                                  │
// │  Branch Comparison                                               │
// │  Delhi:   ₹42L ██████████ (↑22%) | 14 agents | NPS 48          │
// │  Mumbai:  ₹38L █████████  (↑15%) | 12 agents | NPS 44          │
// │  Bangalore:₹28L ███████    (↑20%) | 6 agents  | NPS 52          │
// │                                                                  │
// │  Cost per Agent: ₹45K/month avg (salary + overhead)             │
// │  Revenue per Agent: ₹3.88L/month                                │
// │  Agent ROI: 8.6x (target: 8x+)                                  │
// └──────────────────────────────────────────────────────────────────┘

interface AgentDashboard {
  agentId: string;
  period: MetricPeriod;
  summaryCards: MetricCard[];
  charts: DashboardChart[];
  funnel: ConversionFunnel;
  reviews: CustomerReview[];
  goals: GoalProgress[];
}

interface MetricCard {
  label: string;
  value: number | string;
  unit: string;
  trend: 'up' | 'down' | 'flat';
  trendValue: string;                 // "+8%", "-2 min", "+5 pts"
  targetPercent: number;              // % of target achieved
  sparkline?: number[];               // Last 30 data points
  color: 'green' | 'yellow' | 'red'; // Based on target %
}
```

### Goal Setting & Tracking

```typescript
interface GoalSettingWorkflow {
  agentId: string;
  period: 'monthly' | 'quarterly' | 'annual';
  goals: AgentGoal[];
  state: GoalState;
}

interface AgentGoal {
  id: string;
  category: KPICategory;
  description: string;                // "Achieve ₹5L monthly revenue"
  target: number;
  current: number;
  unit: string;
  deadline: Date;
  priority: 'must' | 'should' | 'stretch';
  progress: number;                   // 0-100%
  milestones: GoalMilestone[];
}

interface GoalMilestone {
  label: string;                      // "50% of target"
  value: number;
  achievedAt?: Date;
  reward?: string;                    // "₹2,000 bonus", "Team dinner"
}

// Goal-setting process:
// 1. Agent + Manager review previous period performance
// 2. Manager proposes targets based on:
//    - Historical agent performance (trailing 3 months)
//    - Seasonal adjustments (peak vs off-season)
//    - Agency growth targets
//    - Peer comparison (anonymized percentile)
// 3. Agent can counter-propose (with justification)
// 4. Negotiated goals locked in for period
// 5. Weekly check-ins, monthly formal review
// 6. Quarterly performance review against goals
```

### Performance Review Workflow

```typescript
interface PerformanceReview {
  reviewId: string;
  agentId: string;
  reviewerId: string;                 // Manager / Team Lead
  period: ReviewPeriod;
  selfAssessment: SelfAssessment;
  managerAssessment: ManagerAssessment;
  goalReview: GoalReviewResult[];
  overallRating: PerformanceRating;
  feedback: ReviewFeedback;
  actionItems: ReviewActionItem[];
  status: ReviewStatus;
  submittedAt?: Date;
  acknowledgedAt?: Date;
}

interface ReviewPeriod {
  type: 'quarterly' | 'annual' | 'probation_end';
  startDate: Date;
  endDate: Date;
}

type PerformanceRating =
  | 'exceptional'    // Top 5%, exceeds all targets
  | 'exceeds'        // Top 20%, exceeds most targets
  | 'meets'          // Meets expectations across the board
  | 'partially'      // Meets some, misses others
  | 'below';         // Below expectations, PIP candidate

// Review workflow states:
// DRAFT → SELF_ASSESSMENT → MANAGER_REVIEW → CALIBRATION → FINAL → ACKNOWLEDGED
//
// 1. DRAFT: System generates review with metrics
// 2. SELF_ASSESSMENT: Agent fills self-evaluation
// 3. MANAGER_REVIEW: Manager reviews + adds assessment
// 4. CALIBRATION: Leadership team calibrates ratings
//    - Ensures fair distribution across teams
//    - Prevents grade inflation/deflation by manager
//    - Cross-team comparison on same data
// 5. FINAL: Locked rating + feedback + action items
// 6. ACKNOWLEDGED: Agent reads and acknowledges
//    - Agent can add comments but cannot change rating
//    - If agent disputes → escalation to HR

interface SelfAssessment {
  highlights: string[];               // Agent's key achievements
  challenges: string[];               // Obstacles faced
  areasOfImprovement: string[];       // Self-identified growth areas
  supportNeeded: string[];            // What help agent needs
  goalProposals: string[];            // Goals for next period
}

interface ManagerAssessment {
  strengths: string[];
  developmentAreas: string[];
  kpiRatings: Record<string, PerformanceRating>;
  overallComments: string;
  promotionRecommendation?: PromotionRecommendation;
  pipRequired: boolean;               // Performance Improvement Plan needed?
}

// Performance-linked outcomes:
// EXCEPTIONAL: 20% bonus + promotion consideration + ESOP grant
// EXCEEDS: 15% bonus + skill upgrade opportunity
// MEETS: 8-10% bonus + standard increment
// PARTIALLY: No bonus + improvement plan
// BELOW: PIP (60-day) + possible role change

interface PromotionRecommendation {
  targetRole: AgentRole;
  targetLevel: AgentLevel;
  readinessAssessment: 'ready_now' | 'ready_6_months' | 'potential_future';
  developmentPlan: string[];
}
```

### India-Specific Salary Structures

```typescript
interface IndiaSalaryStructure {
  agentId: string;
  role: AgentRole;
  level: AgentLevel;
  ctc: CTCBreakdown;                  // Cost to Company
  statutory: StatutoryComponents;
  variable: VariablePay;
  benefits: BenefitsPackage;
}

interface CTCBreakdown {
  // Annual figures in INR
  basicSalary: number;                // 40-50% of CTC
  houseRentAllowance: number;         // 40-50% of basic (metro), 20-30% (non-metro)
  specialAllowance: number;           // Balancing component
  conveyanceAllowance: number;        // ₹19,200/year (tax-exempt limit)
  medicalAllowance: number;           // ₹15,000/year (tax-exempt with bills)
  leaveTravelAllowance: number;       // 2 trips in 4-year block (tax-exempt)
  variablePay: number;                // Performance-linked (10-30% of CTC)
  annualCTC: number;                  // Total CTC
}

// Salary bands by level (Indian travel agency, 2026):
// L1 Trainee:     ₹2.4-3.6 LPA CTC (₹20K-30K/month)
// L2 Junior:      ₹3.6-5.4 LPA CTC (₹30K-45K/month)
// L3 Mid:         ₹5.4-8.4 LPA CTC (₹45K-70K/month)
// L4 Senior:      ₹8.4-14.4 LPA CTC (₹70K-1.2L/month)
// L5 Lead/Expert: ₹14.4-24 LPA CTC (₹1.2L-2L/month)
// Branch Manager: ₹18-36 LPA CTC (₹1.5L-3L/month)
//
// Metro vs Non-metro differential:
// Metro (Delhi, Mumbai, Bangalore): +15-20% on base
// Tier 2 (Pune, Hyderabad, Chennai): +5-10% on base
// Tier 3 (Jaipur, Kochi, Indore): Base rate
//
// Travel industry specifics:
// - Commission is SIGNIFICANT (can be 30-60% of take-home for high performers)
// - Seasonal bonuses common (Dussehra/Diwali in Oct-Nov)
// - International specialist premium: 10-20% above domestic-only agents
// - Language premium: Agents fluent in regional languages + English: 5-10%

interface StatutoryComponents {
  // Employer contributions (added to CTC but not in-hand)
  providentFund: {
    employerContribution: number;     // 12% of basic (₹7,500/month cap)
    employeeContribution: number;     // 12% of basic (deducted from salary)
    uan: string;                      // Universal Account Number
  };
  esi: {
    applicable: boolean;              // Gross salary ≤ ₹21,000/month
    employerContribution: number;     // 3.25% of gross
    employeeContribution: number;     // 0.75% of gross
  };
  professionalTax: number;           // ₹200/month (most states)
  labourWelfareFund: number;         // ₹6-50/year (state-specific)
  gratuity: {
    applicable: boolean;              // After 5 years continuous service
    monthlyProvision: number;         // 4.81% of basic (provisioned monthly)
  };
}

// Statutory compliance calendar:
// Monthly: PF return (15th), ESI return (15th), TDS deposit (7th)
// Quarterly: TDS return (Form 24Q), Advance tax
// Annually: PF annual return, ESI annual return, Form 16, ITR filing support
// Inspections: Shops & Establishment Act renewal, PF/ESI inspections

interface VariablePay {
  // Commission structure (see WORKFORCE_04_COMPENSATION for full details)
  commissionOnRevenue: number;        // % of revenue generated
  targetBonus: number;                // For hitting KPI targets
  quarterlyIncentive: number;         // Performance-based quarterly payout
  annualBonus: number;                // Year-end performance bonus
  spotAwards: number;                 // Immediate recognition awards
  retentionBonus: number;             // Annual retention (if applicable)
}

interface BenefitsPackage {
  healthInsurance: {
    sumInsured: number;               // ₹3-5 lakh for self + family
    premiumPaidBy: 'employer';        // Standard in Indian agencies
  };
  leavePolicy: {
    casualLeave: number;              // 12 days/year
    sickLeave: number;                // 12 days/year
    earnedLeave: number;              // 15-20 days/year (encashable)
    maternityLeave: number;           // 26 weeks (as per Maternity Benefit Act)
    paternityLeave: number;           // 15 days (company policy, not statutory)
  };
  travelBenefits: {
    famTripsPerYear: number;          // 1-2 subsidized familiarization trips
    supplierDiscount: number;         // Agent rates for personal travel
    annualCompanyTrip: boolean;       // Team outing
  };
  professional: {
    trainingBudget: number;           // Annual training/education budget
    certificationSupport: boolean;    // IATA/UFTAA exam fees covered
    conferenceAttendance: number;     // Annual conference visits
  };
}
```

---

## Open Problems

1. **Attribution in team-sold trips** — When a senior agent and junior collaborate on a ₹8 lakh international booking, who gets credit? Split attribution models (70/30, 50/50, by activity) are subjective and can cause friction.

2. **Seasonal normalization** — Peak season inflates metrics (Oct-Mar), off-season deflates them (Jul-Sep). Comparing an agent's April performance to December is unfair. Need a seasonality index for fair evaluation.

3. **NPS sampling bias** — Only 10-15% of customers respond to surveys. Happy customers are more likely to respond. Aggressive customers respond when something went wrong. Low response rates make NPS unreliable for individual agent assessment.

4. **Commission gaming** — Agents may cherry-pick easy, high-value leads while avoiding complex but valuable ones. Revenue-only metrics reward transaction volume over customer relationship building and long-term value.

5. **Privacy in monitoring** — Response time tracking, system utilization monitoring, and keystroke-level analytics raise employee privacy concerns. India's DPDP Act (2023) and IT Act have implications for workplace surveillance. Agents must consent and understand what is tracked.

6. **Multi-branch fairness** — A Delhi agent has access to more corporate clients and higher-value bookings than a Jaipur agent. Comparing raw revenue across branches is inherently unfair without normalization.

---

## Next Steps

- [ ] Design KPI framework with role-specific weights and seasonal adjustments
- [ ] Build performance dashboard wireframes for agent, team lead, and owner views
- [ ] Model salary structures for all levels with statutory compliance
- [ ] Study performance management tools (Darwinbox, Zoho People, Keka, BambooHR India)
- [ ] Create goal-setting workflow with negotiation and approval states
- [ ] Design quarterly performance review process with calibration step
- [ ] Research commission calculation engine patterns (see WORKFORCE_04_COMPENSATION)
