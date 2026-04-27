# Corporate Travel 05: Analytics & Reporting

> Corporate travel analytics and management dashboards

---

## Document Overview

**Focus:** Analytics and reporting for corporate travel
**Status:** Research Exploration
**Last Updated:** 2026-04-27

---

## Key Questions to Answer

### 1. Management Dashboards
- What metrics do travel managers need?
- How do we present travel data?
- What about real-time vs. historical data?
- How do we handle drill-down capabilities?

### 2. Traveler Analytics
- What traveler metrics matter?
- How do we track traveler patterns?
- What about traveler satisfaction?
- How do we identify policy violations?

### 3. Supplier Analytics
- How do we track supplier performance?
- What about negotiated rate utilization?
- How do we assess supplier value?
- What about consolidation opportunities?

### 4. Budget & Forecasting
- How do we support budgeting?
- What forecasting capabilities are needed?
- How do we track budget utilization?
- What about variance reporting?

---

## Research Areas

### A. Management Dashboards

**Key Metrics:**

| Metric | Description | Update Frequency | Research Needed |
|--------|-------------|------------------|-----------------|
| **Total spend** | All travel expenses | Daily/Monthly | ? |
| **Trip count** | Number of trips | Daily/Monthly | ? |
| **Average trip cost** | Mean cost per trip | Monthly | ? |
| **Policy compliance** | % within policy | Monthly | ? |
| **Bookings by channel** | Direct vs. TMC | Monthly | ? |
| **Advance booking** | % booked X days ahead | Monthly | ? |
| **Active travelers** | Currently traveling | Real-time | Duty of care |

**Dashboard Views:**

| View | Audience | Key Elements | Research Needed |
|------|----------|--------------|-----------------|
| **Executive summary** | Senior management | High-level KPIs, trends | ? |
| **Travel manager** | Travel admin | Detailed metrics, drill-downs | ? |
| **Finance** | Finance team | Spend, budgets, accruals | ? |
| **HR** | HR team | Traveler welfare, safety | ? |
| **Real-time** | Duty of care | Current traveler locations | ? |

### B. Traveler Analytics

**Traveler Metrics:**

| Metric | Description | Use | Research Needed |
|--------|-------------|-----|-----------------|
| **Trips per traveler** | Travel frequency | Policy review | ? |
| **Spend per traveler** | Total spend | Budget tracking | ? |
| **Preferred suppliers** | Most used suppliers | Negotiation | ? |
| **Policy violations** | Count, type | Coaching | ? |
| **Advance booking rate** | How early they book | Policy adherence | ? |
| **Cancellation rate** | Cancelled trips | Process improvement | ? |

**Risk & Safety:**

| Metric | Description | Use | Research Needed |
|--------|-------------|-----|-----------------|
| **High-risk destinations** | Travelers in risky areas | Duty of care | ? |
| **Overdue check-ins** | Travelers who haven't checked in | Safety | ? |
| **Near-misses** | Incidents, disruptions | Review | ? |

### C. Supplier Analytics

**Performance Metrics:**

| Metric | Description | Research Needed |
|--------|-------------|-----------------|
| **Volume by supplier** | Bookings, spend | ? |
| **Preferred supplier utilization** | % using preferred | ? |
| **Negotiated rate usage** | % using corporate rates | ? |
| **Average discount achieved** | Savings vs. public rates | ? |
| **On-time performance** | For airlines, trains | ? |
| **Cancellation rate** | Supplier cancellations | ? |

**Opportunity Analysis:**

| Analysis | Description | Research Needed |
|----------|-------------|-----------------|
| **Consolidation potential** | Where we could consolidate spend | ? |
| **Leakage** | Bookings outside program | ? |
| **Rate negotiation targets** | Where better rates possible | ? |

### D. Budget & Forecasting

**Budget Tracking:**

| Type | Description | Research Needed |
|------|-------------|-----------------|
| **Cost center budget** | Department travel budgets | ? |
| **Project budget** | Project-specific budgets | ? |
| **Annual budget** | Company-wide budget | ? |
| **Variance analysis** | Actual vs. budget | ? |

**Forecasting:**

| Input | Method | Research Needed |
|--------|--------|-----------------|
| **Historical spend** | Trend analysis | ? |
| **Seasonality** | Seasonal patterns | ? |
| **Upcoming trips** | Booked travel | ? |
| **Business plans** | Hiring, growth | ? |

---

## Dashboard Design

**Executive Dashboard:**

```
+--------------------------------------------------+
| Corporate Travel Overview - Q1 2026             |
+--------------------------------------------------+
| Total Spend: ₹12.5M  (+8% vs. last quarter)    |
| Trips: 347                                      |
| Policy Compliance: 94%                          |
| Active Travelers: 23                            |
+--------------------------------------------------+
| [Spend Trend Chart]                             |
| [Top Destinations]                              |
| [Budget vs. Actual]                              |
+--------------------------------------------------+
```

**Travel Manager Dashboard:**

```
+--------------------------------------------------+
| Travel Management Dashboard                      |
+--------------------------------------------------+
| Pending Approvals: 12                            |
| Outside Policy This Month: 18                   |
| Leakages: 6 bookings outside program            |
+--------------------------------------------------+
| [Spend by Cost Center]                           |
| [Policy Violations by Type]                      |
| [Upcoming Trips]                                 |
| [Recent Bookings]                                |
+--------------------------------------------------+
```

**Duty of Care Dashboard:**

```
+--------------------------------------------------+
| Traveler Safety Dashboard                        |
+--------------------------------------------------+
| Active Travelers: 23                             |
| High-Risk Areas: 2                              |
| Alerts: 1 (Weather in Bangkok)                  |
+--------------------------------------------------+
| [World Map with Traveler Locations]              |
| [Upcoming Travel to Risk Areas]                  |
| [Emergency Contact List]                         |
+--------------------------------------------------+
```

---

## Data Model Sketch

```typescript
interface CorporateAnalytics {
  companyId: string;
  period: AnalyticsPeriod;

  // Spend metrics
  totalSpend: Money;
  spendByCategory: CategorySpend[];
  spendByCostCenter: CostCenterSpend[];
  spendBySupplier: SupplierSpend[];

  // Trip metrics
  totalTrips: number;
  tripsByDestination: DestinationTrips[];
  averageTripCost: Money;
  averageTripDuration: number;

  // Policy metrics
  policyComplianceRate: number;
  policyViolations: PolicyViolationSummary[];

  // Budget metrics
  budgetUtilization: BudgetUtilization[];

  // Traveler metrics
  topTravelers: TravelerStats[];
  activeTravelers: number;
  travelersAtRisk: number;

  // Supplier metrics
  preferredSupplierUtilization: number;
  negotiatedRateUsage: number;
  topSuppliers: SupplierStats[];
}

interface CategorySpend {
  category: ExpenseCategory;
  amount: Money;
  percentage: number;
  change: number; // % change vs. prior period
}

interface PolicyViolationSummary {
  type: string;
  count: number;
  amount: Money;
  topViolators: string[];
}

interface BudgetUtilization {
  costCenter: string;
  budget: Money;
  actual: Money;
  utilized: number; // %
  remaining: Money;
  variance: Money;
}
```

---

## Export & Reporting

**Export Formats:**

| Format | Use | Research Needed |
|--------|-----|-----------------|
| **PDF** | Management reports | ? |
| **Excel** | Data analysis | ? |
| **CSV** | System integration | ? |
| **Email** | Scheduled reports | ? |

**Scheduled Reports:**

| Report | Frequency | Recipients | Research Needed |
|--------|-----------|------------|-----------------|
| **Monthly spend summary** | Monthly | Travel manager, finance | ? |
| **Policy compliance report** | Monthly | Travel manager, HR | ? |
| **Budget vs. actual** | Monthly | Finance, cost center heads | ? |
| **Quarterly review** | Quarterly | Executive team | ? |
| **Annual summary** | Annually | All stakeholders | ? |

---

## Open Problems

### 1. Data Quality
**Challenge**: Data from multiple sources, inconsistent

**Options**:
- Data validation rules
- Standardization
- Manual correction
- Clear source attribution

### 2. Real-Time vs. Batch
**Challenge**: Some data needs to be real-time, some doesn't

**Options**:
- Real-time for safety, bookings
- Batch for financial reporting
- Hybrid approach

### 3. Privacy Concerns
**Challenge**: Detailed tracking of employee travel

**Options**:
- Aggregate for most views
- Individual access controls
- Clear disclosure
- Minimum necessary data

### 4. Actionable Insights
**Challenge**: Data doesn't automatically lead to action

**Options**:
- Highlight anomalies
- Suggest actions
- Explain trends
- Drill-down capabilities

---

## Competitor Research Needed

| Competitor | Analytics Features | Notable Patterns |
|------------|-------------------|------------------|
| **Concur** | ? | ? |
| **TravelPerk** | ? | ? |
| **Navan** | ? | ? |

---

## Next Steps

1. Design dashboard mockups
2. Build analytics engine
3. Implement reporting system
4. Create export capabilities
5. Test with travel managers

---

**Status**: Research Phase — Analytics patterns unknown

**Last Updated**: 2026-04-27