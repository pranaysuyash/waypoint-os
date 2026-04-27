# Commission Management 04: Reporting

> Commission analytics, statements, and performance tracking

---

## Document Overview

**Focus:** Commission reporting and analytics
**Status:** Research Exploration
**Last Updated:** 2026-04-27

---

## Key Questions

### Agent Reports
- What reports do agents need?
- How is earnings data presented?
- What about historical trends?
- How do agents export data?

### Management Reports
- What analytics are needed?
- How do we track performance?
- What about cost analysis?
- How do we identify trends?

### Statements
- What format are statements in?
- When are statements generated?
- What information is included?
- How are they delivered?

### Performance Tracking
- How do we track agent performance?
- What metrics matter?
- How do we compare agents?
- What about leaderboards?

---

## Research Areas

### A. Agent Reports

**Earnings Summary:**

| Period | Content | Research Needed |
|--------|---------|-----------------|
| **Today** | Real-time earnings | ? |
| **This week** | Week to date | ? |
| **This month** | Month to date | ? |
| **This quarter** | Quarter to date | ? |
| **This year** | Year to date | ? |
| **Custom** | Date range | ? |

**Earnings Breakdown:**

| Dimension | Detail | Research Needed |
|-----------|--------|-----------------|
| **By product** | Flight, hotel, etc. | ? |
| **By supplier** | Airline, hotel chain | ? |
| **By customer** | Top customers | ? |
| **By booking** | Individual bookings | ? |

**Commission Detail View:**

| Field | Display | Research Needed |
|-------|---------|-----------------|
| **Booking ID** | Linkable | ? |
| **Date** | Booking date | ? |
| **Customer** | Name | ? |
| **Product** | Type | ? |
| **Amount** | Booking value | ? |
| **Rate** | Applied % | ? |
| **Commission** | Amount | ? |
| **Status** | Current status | ? |
| **Payout date** | Expected/actual | ? |

**Export Options:**

| Format | Use Case | Research Needed |
|--------|----------|-----------------|
| **PDF** | Statements | ? |
| **Excel** | Analysis | ? |
| **CSV** | Data export | ? |

### B. Management Analytics

**Agency-Level Metrics:**

| Metric | Description | Research Needed |
|--------|-------------|-----------------|
| **Total commission paid** | Per period | ? |
| **Average per agent** | Benchmark | ? |
| **Top performers** | Leaderboard | ? |
| **Product mix** | What sells | ? |
| **Commission cost** | % of revenue | ? |

**Agent Performance:**

| Metric | Description | Research Needed |
|--------|-------------|-----------------|
| **Total bookings** | Volume | ? |
| **Total revenue** | Sales value | ? |
| **Total commission** | Earned | ? |
| **Average commission** | Per booking | ? |
| **Conversion rate** | Lead to booking | ? |
| **Growth rate** | Period over period | ? |

**Trend Analysis:**

| Analysis | Value | Research Needed |
|----------|-------|-----------------|
| **Month-over-month** | Growth tracking | ? |
| **Year-over-year** | Seasonal comparison | ? |
| **Moving average** | Smoothing | ? |
| **Forecast** | Prediction | ? |

### C. Statements

**Statement Types:**

| Type | Frequency | Research Needed |
|------|-----------|-----------------|
| **Payout statement** | Per payout | ? |
| **Monthly statement** | Monthly | ? |
| **Annual statement** | Annual | ? |
| **On-demand** | Anytime | ? |

**Statement Content:**

| Section | Content | Research Needed |
|---------|---------|-----------------|
| **Summary** | Totals, period | ? |
| **Earnings** | Commission details | ? |
| **Deductions** | Tax, fees | ? |
| **Payments** | Payout details | ? |
| **Balance** | Carried forward | ? |

**Delivery Methods:**

| Method | Use Case | Research Needed |
|--------|----------|-----------------|
| **In-app** | Default | ? |
| **Email** | Automatic | ? |
| **SMS** | Notification | ? |
| **Download** | Manual | ? |

### D. Performance Tracking

**Leaderboards:**

| Type | Period | Research Needed |
|------|--------|-----------------|
| **Total revenue** | Month | ? |
| **Total commission** | Quarter | ? |
| **Booking count** | Year | ? |
| **Growth rate** | Month | ? |

**Comparisons:**

| Comparison | Purpose | Research Needed |
|------------|---------|-----------------|
| **Peer comparison** | Benchmarking | ? |
| **Self comparison** | Progress | ? |
| **Goal comparison** | Targets | ? |
| **Historical** | Trends | ? |

**Goal Setting:**

| Goal Type | Trigger | Research Needed |
|-----------|---------|-----------------|
| **Revenue target** | Monthly | ? |
| **Commission target** | Quarterly | ? |
| **Booking count** | Monthly | ? |
| **Product mix** | Ongoing | ? |

---

## Data Model Sketch

```typescript
interface CommissionReport {
  reportId: string;
  type: ReportType;
  period: DateRange;

  // Subject
  agentId?: string; // Null for agency-wide
  agencyId: string;

  // Data
  summary: CommissionSummary;
  details: CommissionDetail[];
  breakdowns: ReportBreakdown[];

  // Metadata
  generatedAt: Date;
  generatedBy: string;
}

type ReportType =
  | 'earnings_summary'
  | 'payout_statement'
  | 'performance'
  | 'agency_analytics';

interface CommissionSummary {
  // Totals
  totalBookings: number;
  totalRevenue: number;
  totalCommission: number;
  totalPaid: number;
  totalPending: number;

  // Averages
  avgCommissionPerBooking: number;
  avgRevenuePerBooking: number;

  // Rates
  commissionRate: number; // % of revenue
}

interface CommissionDetail {
  bookingId: string;
  date: Date;
  customer: string;
  product: ProductType;
  supplier: string;
  revenue: number;
  commissionRate: number;
  commissionAmount: number;
  status: CommissionStatus;
  payoutDate?: Date;
}

interface ReportBreakdown {
  dimension: BreakdownDimension;
  items: BreakdownItem[];
}

type BreakdownDimension =
  | 'product'
  | 'supplier'
  | 'customer'
  | 'agent';

interface BreakdownItem {
  key: string;
  revenue: number;
  commission: number;
  count: number;
  rate: number;
}

interface AgentPerformance {
  agentId: string;
  agentName: string;
  period: DateRange;

  // Metrics
  metrics: PerformanceMetrics;

  // Rank
  rank?: {
    revenue: number;
    commission: number;
    bookings: number;
  };

  // Comparison
  vsPreviousPeriod?: PeriodComparison;
  vsTarget?: TargetComparison;
}

interface PerformanceMetrics {
  totalBookings: number;
  totalRevenue: number;
  totalCommission: number;
  avgCommissionPerBooking: number;
  conversionRate?: number;
  growthRate?: number;
}

interface PeriodComparison {
  revenueChange: number; // % and absolute
  commissionChange: number;
  bookingsChange: number;
}

interface TargetComparison {
  target: number;
  actual: number;
  achievement: number; // %
}

interface CommissionStatement {
  statementId: string;
  agentId: string;
  period: DateRange;

  // Summary
  openingBalance: number;
  earned: number;
  paid: number;
  deducted: number;
  closingBalance: number;

  // Details
  earnings: CommissionEarning[];
  payments: StatementPayment[];
  deductions: StatementDeduction[];

  // Delivery
  deliveredAt?: Date;
  deliveryMethod?: DeliveryMethod;
  downloadedAt?: Date;
}

interface CommissionEarning {
  date: Date;
  bookingId: string;
  amount: number;
  description: string;
}

interface StatementPayment {
  date: Date;
  amount: number;
  method: PaymentMethod;
  reference: string;
}

interface StatementDeduction {
  date: Date;
  type: string;
  amount: number;
  description: string;
}

type DeliveryMethod =
  | 'in_app'
  | 'email'
  | 'sms';
```

---

## Open Problems

### 1. Data Freshness
**Challenge:** Reports need to be current

**Options:** Real-time, periodic refresh, on-demand generation

### 2. Performance at Scale
**Challenge:** Large datasets are slow

**Options:** Pre-aggregation, caching, incremental loading

### 3. Customization
**Challenge:** Everyone wants different views

**Options:** Saved filters, custom reports, export flexibility

### 4. Goal Fairness
**Challenge:** Setting fair targets

**Options:** Historical baselines, peer benchmarks, negotiation

### 5. Privacy
**Challenge:** Leaderboards expose data

**Options:** Anonymization, opt-in, restricted access

---

## Next Steps

1. Define report requirements
2. Build reporting engine
3. Create agent dashboard
4. Implement statement generation

---

**Status:** Research Phase — Reporting patterns unknown

**Last Updated:** 2026-04-27
