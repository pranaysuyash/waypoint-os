# Agency Operations Command Center — Reporting

> Research document for operational reporting: daily/weekly/monthly reports, KPI tracking, trend analysis, automated report generation and distribution, role-based customization, and India-specific regulatory reporting (GST, TCS, TDS, IATA BSP, PF/ESI, state tourism board filings).

---

## Key Questions

1. **What operational reports does each role need, and at what frequency?**
2. **How do we automate report generation, scheduling, and multi-channel distribution?**
3. **What KPIs should be tracked in trend reports, and how do we present comparative analysis (this month vs. last month)?**
4. **What India-specific regulatory reports must be generated (GST returns, TCS certificates, TDS returns, IATA BSP, PF/ESI, state tourism board filings)?**
5. **How do we support report customization by role without creating unmaintainable report sprawl?**
6. **What export formats and delivery channels are needed (email, WhatsApp, PDF, Excel, API)?**

---

## Research Areas

### Report Data Model

```typescript
interface OpsReport {
  reportId: string;
  templateId: string;
  name: string;
  description: string;
  category: ReportCategory;
  frequency: ReportFrequency;
  format: ReportFormat;

  // Scheduling
  schedule: ReportSchedule;
  distribution: ReportDistribution;

  // Content
  sections: ReportSection[];
  parameters: ReportParameter[];

  // Access
  visibility: 'private' | 'team' | 'agency';
  requiredRole: DashboardRole[];

  // Metadata
  lastGeneratedAt?: Date;
  nextGenerationAt?: Date;
  generationDurationMs?: number;
  dataSizeBytes?: number;
  createdBy: string;
  createdAt: Date;
}

type ReportCategory =
  | 'operational'         // Day-to-day operations
  | 'financial'           // Revenue, margins, costs
  | 'compliance'          // Regulatory filings
  | 'performance'         // Agent/team performance
  | 'customer'            // CSAT, NPS, feedback
  | 'supplier'            // Supplier performance and SLA
  | 'strategic';          // Trends, forecasts, benchmarks

type ReportFrequency =
  | 'real_time'           // Live dashboard
  | 'daily'               // Every business day
  | 'weekly'              // Every Monday
  | 'bi_weekly'           // Every other Monday
  | 'monthly'             // First business day of month
  | 'quarterly'           // Start of quarter
  | 'half_yearly'
  | 'annual'
  | 'on_demand';          // User-triggered

type ReportFormat = 'pdf' | 'excel' | 'csv' | 'html' | 'json' | 'whatsapp_card';

interface ReportSchedule {
  cron: string;                          // Standard cron expression
  timezone: string;                      // 'Asia/Kolkata' default
  businessDaysOnly: boolean;
  skipHolidays: boolean;                 // Indian public holidays
  retryOnFailure: boolean;
  maxRetryAttempts: number;
}

interface ReportDistribution {
  channels: DistributionChannel[];
  recipients: DistributionRecipient[];
  condition?: DistributionCondition;     // Only send if condition met
}

type DistributionChannel =
  | 'email'
  | 'whatsapp'
  | 'slack'
  | 'sftp'                // For regulatory submissions
  | 'api_webhook'
  | 'in_app';             // Available in reports library

interface DistributionRecipient {
  type: 'user' | 'role' | 'team' | 'email_list';
  identifier: string;
  format: ReportFormat;                  // Per-recipient format override
}

interface DistributionCondition {
  type: 'threshold' | 'anomaly' | 'always' | 'non_empty';
  config: Record<string, unknown>;
}

// Example: Only send daily revenue report if revenue < 80% of target
// { type: 'threshold', config: { metric: 'revenuePercentOfTarget', operator: 'less_than', value: 80 } }
```

### Report Sections & Parameters

```typescript
interface ReportSection {
  sectionId: string;
  title: string;
  type: SectionType;
  dataSource: string;                    // API endpoint or query
  visualization?: VisualizationType;
  order: number;
  collapsible: boolean;
  defaultExpanded: boolean;
}

type SectionType =
  | 'kpi_summary'         // Key metrics with sparklines
  | 'table'               // Tabular data
  | 'chart'               // Visualization
  | 'comparison'          // Period-over-period comparison
  | 'trend'               // Time series trend
  | 'list'                // Bulleted list (alerts, actions)
  | 'text'                // Rich text commentary
  | 'regulatory_form';    // Pre-formatted regulatory form

interface ReportParameter {
  name: string;
  label: string;
  type: 'date_range' | 'select' | 'multi_select' | 'agent' | 'team' | 'destination' | 'service_type';
  required: boolean;
  defaultValue?: unknown;
  options?: { label: string; value: string }[];
  affectsSections: string[];             // Section IDs that use this parameter
}
```

### Report Catalog by Role

```typescript
// ┌─────────────────────────────────────────────────────────────────────────┐
// │  REPORT CATALOG BY ROLE                                                │
// ├─────────────────┬──────────────────────────────────┬──────────┬─────────┤
// │ Role            │ Report                           │ Frequency │ Format  │
// ├─────────────────┼──────────────────────────────────┼──────────┼─────────┤
// │ AGENT           │ My Daily Brief                   │ Daily     │ In-App  │
// │                 │ My Weekly Performance            │ Weekly    │ Email   │
// │                 │ Customer Feedback Summary        │ Weekly    │ In-App  │
// │                 │ My Revenue & Targets             │ Monthly   │ Email   │
// ├─────────────────┼──────────────────────────────────┼──────────┼─────────┤
// │ TEAM LEAD       │ Team Daily Pipeline              │ Daily     │ In-App  │
// │                 │ Team SLA Report                  │ Daily     │ In-App  │
// │                 │ Team Performance Comparison      │ Weekly    │ Email   │
// │                 │ Team Revenue & Targets           │ Monthly   │ Email   │
// │                 │ Agent Ranking                    │ Monthly   │ Email   │
// ├─────────────────┼──────────────────────────────────┼──────────┼─────────┤
// │ MANAGER         │ Operations Daily Digest          │ Daily     │ Email   │
// │                 │ Pipeline Health Report           │ Daily     │ In-App  │
// │                 │ Weekly Revenue Report            │ Weekly    │ Email   │
// │                 │ Agent Performance Report         │ Weekly    │ Email   │
// │                 │ Customer Satisfaction Report     │ Monthly   │ PDF     │
// │                 │ Department P&L                   │ Monthly   │ Excel   │
// │                 │ Supplier Performance Scorecard   │ Monthly   │ PDF     │
// ├─────────────────┼──────────────────────────────────┼──────────┼─────────┤
// │ OWNER / EXEC    │ Daily Flash Report               │ Daily     │ WhatsApp│
// │                 │ Weekly Business Review            │ Weekly    │ PDF     │
// │                 │ Monthly P&L Statement             │ Monthly   │ Excel   │
// │                 │ Quarterly Business Review         │ Quarterly │ PDF     │
// │                 │ Annual Performance Report         │ Annual    │ PDF     │
// │                 │ Compliance Dashboard             │ Weekly    │ In-App  │
// │                 │ Branch Comparison Report         │ Monthly   │ Excel   │
// └─────────────────┴──────────────────────────────────┴──────────┴─────────┘
```

### Operational Reports Detail

```typescript
// --- DAILY FLASH REPORT (Owner/Exec) ---
interface DailyFlashReport {
  date: Date;

  // Top-line numbers
  revenue: {
    today: Money;
    yesterday: Money;
    sameDayLastWeek: Money;
    mtdTotal: Money;
    mtdTarget: Money;
    mtdPercentOfTarget: number;
  };

  pipeline: {
    newTripsToday: number;
    tripsBookedToday: number;
    tripsCompletedToday: number;
    cancellationsToday: number;
    netNew: number;
    pipelineTotal: number;
  };

  alerts: {
    critical: number;
    unacknowledged: number;
    escalated: number;
    resolved: number;
  };

  highlights: string[];                  // Top 3 good things
  concerns: string[];                    // Top 3 concerns
  actionsNeeded: string[];               // Items requiring owner decision
}

// Example Daily Flash (WhatsApp format):
//
// ┌─────────────────────────────────────┐
// │  DAILY FLASH — Mon, Apr 28 2026     │
// ├─────────────────────────────────────┤
// │  REVENUE                            │
// │  Today: ₹5.2L  ↑ 12% vs yesterday  │
// │  MTD: ₹82L   (Target ₹1.2Cr = 68%) │
// │                                     │
// │  PIPELINE                           │
// │  New: 8 │ Booked: 5 │ Done: 3      │
// │  Cancelled: 1 │ Net: +7            │
// │  Pipeline: 142 trips                │
// │                                     │
// │  ALERTS                             │
// │  Critical: 1 │ Open: 3 │ Esc: 0    │
// │                                     │
// │  ✅ HIGHLIGHTS                      │
// │  • Corporate deal closed (₹18L)     │
// │  • CSAT score 4.7 (best this month) │
// │                                     │
// │  ⚠ CONCERNS                         │
// │  • SpiceJet disruption: 3 trips     │
// │  • TCS deposit due in 2 days        │
// │                                     │
// │  🔴 OWNER ACTION NEEDED             │
// │  • Approve new Goa supplier contract│
// └─────────────────────────────────────┘

// --- WEEKLY OPERATIONS REPORT ---
interface WeeklyOpsReport {
  weekStart: Date;
  weekEnd: Date;

  // Pipeline summary
  pipeline: {
    entered: number;
    booked: number;
    completed: number;
    cancelled: number;
    conversionRate: number;
    conversionVsLastWeek: number;        // % change
  };

  // Revenue
  revenue: {
    total: Money;
    byServiceType: Record<string, Money>;
    byDestination: Record<string, Money>;
    vsLastWeek: number;                  // % change
    vsSameWeekLastYear: number;
  };

  // SLA compliance
  sla: {
    overallCompliance: number;
    stageBreakdown: Record<string, number>;
    worstPerformingAgent: string;
    bestPerformingAgent: string;
    breachReasons: Record<string, number>;
  };

  // Team performance
  team: {
    agentRankings: AgentRanking[];
    avgResponseTime: string;
    avgResolutionTime: string;
    topPerformer: string;
    needsAttention: string[];
  };

  // Customer metrics
  customer: {
    newCustomers: number;
    repeatCustomers: number;
    repeatRate: number;
    complaintsReceived: number;
    complaintsResolved: number;
    avgCSAT: number;
  };

  // Action items
  actionItems: ActionItem[];
}

interface AgentRanking {
  agentId: string;
  agentName: string;
  tripsHandled: number;
  revenue: Money;
  conversionRate: number;
  avgResponseTime: string;
  csatScore: number;
  slaCompliance: number;
  rank: number;
  trendVsLastWeek: 'up' | 'down' | 'same';
}

interface ActionItem {
  id: string;
  priority: 'high' | 'medium' | 'low';
  description: string;
  assignee: string;
  dueDate: Date;
  status: 'open' | 'in_progress' | 'done';
}
```

### KPI Tracking & Trend Analysis

```typescript
interface KPITrackingReport {
  period: DateRange;
  comparisonPeriod: DateRange;

  kpis: KPITrend[];

  // Summary
  kpisImproving: number;
  kpisStable: number;
  kpisDeclining: number;
}

interface KPITrend {
  kpiId: string;
  name: string;
  category: string;
  unit: string;

  // Current period
  currentValue: number;
  targetValue: number;
  percentOfTarget: number;

  // Comparison period
  previousValue: number;
  changePercent: number;
  trend: 'up' | 'down' | 'flat';

  // Trend (last 12 periods)
  history: TrendDataPoint[];

  // Status
  status: 'on_track' | 'at_risk' | 'off_track';
  statusReason?: string;
}

// KPI comparison table (monthly report):
//
// ┌────────────────────────────┬──────────┬──────────┬─────────┬─────────┬──────────┐
// │ KPI                        │ This Mo  │ Last Mo  │ Change  │ Target  │ Status   │
// ├────────────────────────────┼──────────┼──────────┼─────────┼─────────┼──────────┤
// │ Revenue                    │ ₹1.2Cr   │ ₹1.05Cr  │ +14.3%  │ ₹1.3Cr  │ 🟡 At Risk│
// │ Trips Booked               │ 145      │ 128      │ +13.3%  │ 150     │ 🟡 At Risk│
// │ Avg Trip Value             │ ₹82.8K   │ ₹82.0K   │ +1.0%   │ ₹85K    │ 🟢 On Track│
// │ Conversion Rate            │ 32%      │ 29%      │ +3 pts  │ 35%     │ 🟡 At Risk│
// │ Avg Time to Quote          │ 2.1 hrs  │ 2.8 hrs  │ -25%    │ 2 hrs   │ 🟢 On Track│
// │ SLA Compliance             │ 94.2%    │ 91.8%    │ +2.4 pts│ 95%     │ 🟡 At Risk│
// │ CSAT Score                 │ 4.5      │ 4.3      │ +0.2    │ 4.5     │ 🟢 On Track│
// │ Repeat Customer Rate       │ 38%      │ 35%      │ +3 pts  │ 40%     │ 🟡 At Risk│
// │ Agent Utilization          │ 78%      │ 72%      │ +6 pts  │ 80%     │ 🟢 On Track│
// │ Payment Collection Rate    │ 92%      │ 88%      │ +4 pts  │ 95%     │ 🟡 At Risk│
// │ Complaint Rate             │ 2.1%     │ 2.8%     │ -0.7 pts│ <3%     │ 🟢 On Track│
// │ NPS                        │ 72       │ 68       │ +4      │ 70      │ 🟢 On Track│
// └────────────────────────────┴──────────┴──────────┴─────────┴─────────┴──────────┘
```

### India-Specific Regulatory Reporting

```typescript
interface IndiaRegulatoryReports {
  // GST Returns
  gst: {
    // GSTR-1: Outward supplies (monthly/quarterly)
    gstr1: GSTReturn;
    // GSTR-3B: Summary return (monthly)
    gstr3b: GSTReturn;
    // GSTR-9: Annual return
    gstr9: GSTReturn;
    // GSTR-9C: Reconciliation statement (annual, if turnover > ₹5Cr)
    gstr9c: GSTReturn;
    // GST reconciliation: Books vs. returns
    reconciliation: GSTReconciliation;
  };

  // TCS (Tax Collected at Source)
  tcs: {
    // Monthly TCS collection summary
    monthlyCollection: TCSCollectionReport;
    // Quarterly TCS certificate (Form 27D)
    certificate: TCSCertificate;
    // TCS deposit tracking
    depositTracking: TCSDepositReport;
  };

  // TDS (Tax Deducted at Source)
  tds: {
    // Monthly TDS deduction summary
    monthlyDeduction: TDSDeductionReport;
    // Quarterly TDS return (Form 24Q - salary, 26Q - non-salary)
    quarterlyReturn: TDSReturn;
    // TDS certificate (Form 16/16A)
    certificates: TDSCertificate[];
  };

  // IATA BSP (Billing and Settlement Plan)
  iataBSP: {
    // BSP billing analysis
    billingAnalysis: BSPBillingReport;
    // ADM/ACM tracking (Agency Debit Memo / Agency Credit Memo)
    admAcm: ADMACMReport;
    // Stock utilization (ticket stock)
    stockUtilization: StockUtilizationReport;
  };

  // PF/ESI Compliance
  pfEsi: {
    // Monthly PF contribution report
    pfMonthly: PFMonthlyReport;
    // Monthly ESI contribution report
    esiMonthly: ESIMonthlyReport;
    // Annual PF return
    pfAnnual: PFAAnnualReport;
  };

  // State tourism board filings
  stateTourism: {
    // State-specific tourism tax reports
    stateFilings: StateFiling[];
  };
}

// --- GST Return Data Model ---
interface GSTReturn {
  returnType: 'GSTR-1' | 'GSTR-3B' | 'GSTR-9' | 'GSTR-9C';
  period: string;                        // "2026-04" or "2025-26"
  gstin: string;                         // Agency GST Identification Number

  // Outward supplies (GSTR-1)
  outwardSupplies?: {
    b2b: B2BInvoice[];                   // Business-to-business
    b2cLarge: B2CInvoice[];              // B2C > ₹2.5L
    b2cSmall: B2CSummary[];              // B2C < ₹2.5L (summarized)
    creditDebitNotes: CreditDebitNote[];
    exportInvoices: ExportInvoice[];
  };

  // Summary (GSTR-3B)
  summary?: {
    outwardTaxableSupplies: Money;
    inwardReverseCharge: Money;
    inputTaxCredit: Money;
    taxPayable: {
      cgst: Money;
      sgst: Money;
      igst: Money;
      cess: Money;
    };
    taxPaid: {
      cash: Money;
      itc: Money;
    };
  };

  status: 'draft' | 'ready_to_file' | 'filed' | 'acknowledged';
  filedDate?: Date;
  dueDate: Date;
  acknowledgementNo?: string;
}

// --- TCS Collection Report ---
interface TCSCollectionReport {
  month: string;                         // "2026-04"
  collections: {
    section: string;                     // e.g., "206C(1G)" for foreign tour packages
    rate: number;                        // 5% for overseas tour packages
    totalAmountCollected: Money;
    numberOfTransactions: number;
    deposited: Money;
    pendingDeposit: Money;
    depositDueDate: Date;
    depositStatus: 'pending' | 'deposited' | 'overdue';
  }[];
  certificatesIssued: number;
  certificatesPending: number;
  nextCertificateDueDate: Date;
}

// --- TDS Reporting ---
interface TDSDeductionReport {
  month: string;
  deductions: {
    section: string;                     // e.g., "194C" for contractor payments
    rate: number;
    totalAmountDeducted: Money;
    numberOfDeductions: number;
    deposited: Money;
    pendingDeposit: Money;
  }[];
}

interface TDSReturn {
  formType: '24Q' | '26Q' | '27Q' | '27EQ';
  quarter: string;                       // "Q1 2026"
  deductions: {
    deducteeName: string;
    deducteePAN: string;
    section: string;
    amountPaid: Money;
    taxDeducted: Money;
    taxDeposited: Money;
  }[];
  status: 'draft' | 'prepared' | 'filed' | 'processed';
  filedDate?: Date;
  dueDate: Date;
}

// --- IATA BSP Report ---
interface BSPBillingReport {
  billingPeriod: string;                 // "BSP-2026-08" (bi-monthly)
  airlineBreakdown: {
    airlineCode: string;                 // "6E" for IndiGo, "AI" for Air India
    airlineName: string;
    ticketsIssued: number;
    ticketsRefunded: number;
    ticketsVoided: number;
    grossSales: Money;
    commissions: Money;
    taxes: Money;
    netPayable: Money;
  }[];
  totals: {
    grossSales: Money;
    commissions: Money;
    taxes: Money;
    penalties: Money;
    netSettlement: Money;
    settlementDate: Date;
  };
}

// --- PF/ESI Report ---
interface PFMonthlyReport {
  month: string;
  employees: {
    employeeId: string;
    employeeName: string;
    uan: string;                         // Universal Account Number
    grossSalary: Money;
    epfEmployeeShare: Money;             // 12% of basic
    epfEmployerShare: Money;             // 3.67% of basic
    epsEmployerShare: Money;             // 8.33% of basic
    edliCharges: Money;                  // 0.5% of basic
    adminCharges: Money;                 // 0.5% of basic
    total: Money;
  }[];
  totals: {
    totalWages: Money;
    totalEmployeeContribution: Money;
    totalEmployerContribution: Money;
    grandTotal: Money;
    dueDate: Date;                       // 15th of following month
    status: 'pending' | 'paid' | 'overdue';
  };
}

interface ESIMonthlyReport {
  month: string;
  employees: {
    employeeId: string;
    employeeName: string;
    esicNumber: string;
    grossSalary: Money;
    employeeContribution: Money;         // 0.75% of gross
    employerContribution: Money;         // 3.25% of gross
    total: Money;
  }[];
  totals: {
    totalWages: Money;
    totalContribution: Money;
    dueDate: Date;                       // 15th of following month
    status: 'pending' | 'paid' | 'overdue';
  };
}

// --- State Tourism Board Filings ---
interface StateFiling {
  state: string;                        // "Kerala", "Goa", "Rajasthan"
  filingType: string;                   // "tourism_tax" | "luxury_tax" | "gst_supplementary"
  period: string;
  amount: Money;
  dueDate: Date;
  status: 'pending' | 'filed' | 'overdue';
  portalUrl?: string;
  notes?: string;
}
```

### Automated Report Generation & Distribution

```typescript
interface ReportGenerator {
  generatorId: string;
  templateId: string;

  // Generation pipeline
  steps: GenerationStep[];

  // Output
  outputs: ReportOutput[];

  // Quality checks
  validations: ReportValidation[];
}

interface GenerationStep {
  step: number;
  type: 'fetch_data' | 'transform' | 'aggregate' | 'format' | 'render' | 'upload';
  config: Record<string, unknown>;
  timeout: number;                       // ms
  retryOnFailure: boolean;
}

interface ReportOutput {
  format: ReportFormat;
  template: string;                      // Template file path (HTML, Excel, LaTeX, etc.)
  fileName: string;                      // e.g., "daily_flash_2026-04-28.pdf"
  storagePath: string;                   // S3/local path
  sizeLimitBytes: number;
}

interface ReportValidation {
  type: 'data_freshness' | 'completeness' | 'cross_check' | 'threshold';
  config: Record<string, unknown>;
  onFailure: 'warn' | 'block' | 'send_with_caveat';
}

// Generation pipeline example (Monthly P&L):
//
// Step 1: Fetch data from analytics warehouse
//   - Revenue by category (SQL query)
//   - Expense by category (SQL query)
//   - Receivables aging (SQL query)
//   - Payables aging (SQL query)
//
// Step 2: Transform & calculate
//   - Compute gross margin, net margin, EBITDA
//   - Calculate period-over-period changes
//   - Flag anomalies (>2 std dev from mean)
//
// Step 3: Validate
//   - Check: total revenue matches sum of service types
//   - Check: no negative balances
//   - Check: data is from current period
//
// Step 4: Render
//   - PDF: Professional layout with charts
//   - Excel: Data tables for analysis
//   - WhatsApp: Summary card with key numbers
//
// Step 5: Distribute
//   - Email PDF + Excel to owner, manager
//   - WhatsApp card to owner's business number
//   - Upload to reports library

// Report generation cost estimate:
//
// ┌──────────────────┬────────────┬──────────┬────────────────────────────┐
// │ Report           │ Gen Time   │ Cost/Run │ Monthly Cost (at frequency)│
// ├──────────────────┼────────────┼──────────┼────────────────────────────┤
// │ Daily Flash      │ 5-10 sec   │ ₹0.5     │ ₹15 (daily)               │
// │ Weekly Ops       │ 30-60 sec  │ ₹2       │ ₹8 (weekly)               │
// │ Monthly P&L      │ 2-5 min    │ ₹10      │ ₹10 (monthly)             │
// │ GST Return       │ 1-3 min    │ ₹5       │ ₹15 (3 returns/month)     │
// │ Quarterly Review │ 5-10 min   │ ₹25      │ ₹25 (quarterly)           │
// │ Annual Report    │ 15-30 min  │ ₹100     │ ₹100 (annual)             │
// └──────────────────┴────────────┴──────────┴────────────────────────────┘
```

### Report Customization by Role

```typescript
interface ReportCustomization {
  reportId: string;
  role: DashboardRole;

  // Which sections to include/exclude
  sectionOverrides: SectionOverride[];

  // Parameter defaults for this role
  parameterDefaults: Record<string, unknown>;

  // Distribution preferences
  distribution: {
    preferredChannel: DistributionChannel;
    preferredFormat: ReportFormat;
    preferredTime: string;               // "08:00" IST
    includeAttachments: boolean;
  };

  // Branding
  branding: {
    agencyLogo: boolean;
    agencyColors: boolean;
    customHeader?: string;
    customFooter?: string;
  };
}

interface SectionOverride {
  sectionId: string;
  included: boolean;
  order?: number;
  customTitle?: string;
  collapsed?: boolean;
}

// Customization examples:
//
// AGENT sees "My Daily Brief":
//   - My trips pipeline (required, expanded)
//   - My tasks for today (required, expanded)
//   - My revenue vs target (included, expanded)
//   - My SLA compliance (included, collapsed)
//   - Agency-wide pipeline (excluded)
//   - Financial summary (excluded)
//
// MANAGER sees "Operations Daily Digest":
//   - Pipeline overview (required, expanded)
//   - Team performance (required, expanded)
//   - SLA compliance (required, expanded)
//   - Revenue summary (included, expanded)
//   - Alerts & escalations (included, expanded)
//   - Agent rankings (included, collapsed)
//   - Compliance status (included, collapsed)
//   - My tasks (excluded — manager has team view)
//
// OWNER sees "Daily Flash Report":
//   - Revenue flash (required, expanded)
//   - Pipeline summary (required, expanded)
//   - Key highlights & concerns (required, expanded)
//   - Action items (required, expanded)
//   - Agent-level detail (excluded — too granular)
//   - SLA by stage (collapsed — available if needed)
```

### Report Distribution Channels

```typescript
interface ReportDelivery {
  deliveryId: string;
  reportId: string;
  generatedAt: Date;
  deliveries: ChannelDelivery[];
}

interface ChannelDelivery {
  channel: DistributionChannel;
  recipient: string;
  status: 'pending' | 'sent' | 'delivered' | 'failed';
  sentAt?: Date;
  deliveredAt?: Date;
  failureReason?: string;
  format: ReportFormat;
  sizeBytes: number;
  trackingId?: string;
}

// Distribution channel capabilities:
//
// ┌────────────┬───────────────────────────────────────────────────────────┐
// │ Channel    │ Capabilities & Limitations                               │
// ├────────────┼───────────────────────────────────────────────────────────┤
// │ Email      │ PDF + Excel attachments, up to 25MB per email            │
// │            │ Branded HTML body with report summary                     │
// │            │ Deep link to full report in app                           │
// │            │ Cost: ~₹0.05-0.10 per email (SendGrid/SES)               │
// ├────────────┼───────────────────────────────────────────────────────────┤
// │ WhatsApp   │ Summary card (image + text), max 1024 chars text          │
// │            │ PDF attachment via WhatsApp (max 100MB)                   │
// │            │ Interactive buttons for quick actions                     │
// │            │ Cost: ~₹0.30-0.70 per message (template pricing)         │
// ├────────────┼───────────────────────────────────────────────────────────┤
// │ Slack      │ Rich message with charts as images                       │
// │            │ Interactive buttons for drill-down                       │
// │            │ File attachment for detailed reports                     │
// │            │ Cost: Free (within Slack plan)                           │
// ├────────────┼───────────────────────────────────────────────────────────┤
// │ SFTP       │ Automated upload for regulatory submissions               │
// │            │ CSV/XML format for government portals                    │
// │            │ Audit trail of uploads                                   │
// │            │ Cost: ₹0 (infrastructure cost only)                      │
// ├────────────┼───────────────────────────────────────────────────────────┤
// │ In-App     │ Available in reports library with search & filter        │
// │            │ Interactive drill-down (not possible in PDF)             │
// │            │ Export to any format on demand                           │
// │            │ Cost: ₹0                                                 │
// └────────────┴───────────────────────────────────────────────────────────┘
```

---

## Open Problems

1. **Report template sprawl** — Different agents want different sections. Without guardrails, we end up with 50 variants of the same report. Need a template system with controlled customization points.

2. **Regulatory report accuracy** — GST returns and TCS deposits must be penny-perfect. Any discrepancy with the government portal triggers notices. Need robust reconciliation between our data and GSTN data.

3. **Real-time vs. batch reporting** — Operational reports benefit from real-time data, but financial reports need reconciled (batch-processed) data. A single report that mixes both can be confusing ("why does revenue differ between the dashboard and the report?").

4. **Multi-branch consolidation** — Agencies with multiple branches need consolidated reports plus branch-level breakdowns. Currency conversion, inter-branch transactions, and different GST registrations complicate this.

5. **Report delivery reliability** — WhatsApp messages can fail (template rejection), emails can land in spam, SFTP connections can drop. Need delivery tracking and retry logic with confirmation.

6. **Historical report consistency** — If the report formula changes (e.g., how "conversion rate" is calculated), historical reports become incomparable. Need versioned report definitions.

---

## Next Steps

- [ ] Design the report template engine with section-based customization
- [ ] Build the regulatory report calendar (GST, TCS, TDS, IATA, PF/ESI) with automated triggers
- [ ] Research PDF generation libraries (Puppeteer, WeasyPrint, jsPDF) for high-quality report output
- [ ] Evaluate Excel generation libraries (ExcelJS, SheetJS) for financial reports
- [ ] Design the report scheduling and distribution pipeline
- [ ] Research GSTN API for automated return preparation and filing
- [ ] Prototype the Daily Flash Report WhatsApp card template
- [ ] Build report versioning system to track formula changes over time
- [ ] Design report access control matrix (who can see/create/distribute what)
