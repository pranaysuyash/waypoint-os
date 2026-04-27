# Corporate Travel 04: Expense Management

> Corporate expense tracking and reporting

---

## Document Overview

**Focus:** Corporate travel expense management
**Status:** Research Exploration
**Last Updated:** 2026-04-27

---

## Key Questions to Answer

### 1. Expense Capture
- How do we capture travel expenses?
- What data needs to be tracked?
- How do we handle out-of-pocket expenses?
- What about cash advances?

### 2. Expense Reporting
- How do we generate expense reports?
- What integrations are needed?
- How do we handle different currencies?
- What about GST/input tax credits?

### 3. Reimbursement
- How do reimbursements work?
- What are the timelines?
- How do we handle corporate cards?
- What about rejected expenses?

### 4. Analytics
- What expense analytics do companies need?
- How do we track spend by cost center?
- What about policy compliance tracking?
- How do we support budgeting?

---

## Research Areas

### A. Expense Capture

**Expense Sources:**

| Source | Data Captured | Automation | Research Needed |
|--------|---------------|------------|-----------------|
| **Bookings through platform** | Full booking data | Automatic | ? |
| **Corporate card feeds** | Card transactions | Automatic | ? |
| **E-receipts** | Digital receipts | Semi-automatic | ? |
| **Manual entry** | Cash expenses, tips | Manual | ? |
| **Upload receipts** | Scanned paper receipts | OCR? | ? |

**Data Requirements:**

| Data Point | Required For | Research Needed |
|------------|--------------|-----------------|
| **Date** | Accounting, per diem calculation | ? |
| **Amount** | Reimbursement | ? |
| **Currency** | Multi-currency accounting | ? |
| **Vendor** | Spend analysis | ? |
| **Category** | Expense classification | ? |
| **Business purpose** | Policy compliance, tax | ? |
| **Cost center** | Cost allocation | ? |
| **Project code** | Project billing | ? |
| **Receipt** | Audit, tax | ? |
| **GST details** | Input tax credit (India) | ? |

### B. Expense Reporting

**Report Types:**

| Type | Purpose | Frequency | Research Needed |
|------|---------|-----------|-----------------|
| **Individual expense report** | Reimbursement | Per trip/monthly | ? |
| **Cost center report** | Budget tracking | Monthly | ? |
| **Project report** | Project billing | Per project/monthly | ? |
| **Policy compliance report** | Management review | Monthly/quarterly | ? |
| **Spend analysis** | Strategic review | Quarterly/annually | ? |

**GST/Input Tax Credit (India):**

| Aspect | Requirement | Research Needed |
|--------|-------------|-----------------|
| **GSTIN** | Company GST number | Required? |
| **Invoice GST** | GST amount on invoice | Must be valid GST invoice |
| **Input tax credit** | Claimable GST | How to calculate? |
| **GST composition** | CGST, SGST, IGST | Different rules? |
| **Exempt expenses** | Some expenses no GST | Which ones? |

**Multi-Currency:**

| Aspect | Handling | Research Needed |
|--------|----------|-----------------|
| **Exchange rates** | Rate at time of expense | Which rate to use? |
| **Reporting currency** | Convert to base currency | Real-time or period-end? |
| **Gains/Losses** | FX differences | How to account? |

### C. Reimbursement

**Reimbursement Methods:**

| Method | Timing | Research Needed |
|--------|--------|-----------------|
| **Payroll** | Next payroll cycle | Most common? |
| **Direct deposit** | X days after approval | SLA? |
| **Corporate card settlement** | Auto-settled | How? |

**Approval Workflow:**

| Expense Type | Approval Required | Research Needed |
|--------------|-------------------|-----------------|
| **Within policy, booking through platform** | Often auto-approved | ? |
| **Within policy, manual entry** | Manager approval | ? |
| **Outside policy** | Manager + finance | ? |
| **High value** | Additional approval | Threshold? |

**Timelines:**

| Stage | Typical Duration | Research Needed |
|--------|------------------|-----------------|
| **Submission to approval** | 2-5 days | ? |
| **Approval to payment** | 3-10 days | ? |
| **Total cycle** | 1-3 weeks | Industry standard? |

### D. Analytics

**Key Metrics:**

| Metric | Description | Use | Research Needed |
|--------|-------------|-----|-----------------|
| **Total spend** | All travel expenses | Budgeting | ? |
| **Spend by category** | Flights, hotels, etc. | Cost optimization | ? |
| **Spend by cost center** | Department/team spend | Budget tracking | ? |
| **Spend by vendor** | Supplier spend | Negotiation leverage | ? |
| **Policy compliance rate** | % within policy | Policy effectiveness | ? |
| **Average trip cost** | Mean cost per trip | Benchmarking | ? |
| **Advance booking rate** | % booked X days ahead | Policy adherence | ? |

**Budget Tracking:**

| Type | Description | Research Needed |
|------|-------------|-----------------|
| **Cost center budget** | Department travel budget | ? |
| **Project budget** | Project-specific travel budget | ? |
| **Annual budget** | Company-wide travel budget | ? |
| **Real-time tracking** | Current spend vs. budget | Alerts? |

---

## Data Model Sketch

```typescript
interface ExpenseReport {
  id: string;
  companyId: string;
  userId: string;

  // Report details
  reportName: string;
  period: { start: Date; end: Date };
  status: ReportStatus;

  // Allocation
  costCenter: string;
  projectCode?: string;

  // Expenses
  expenses: Expense[];

  // Totals
  totalAmount: Money;
  totalReimbursable: Money;
  totalNonReimbursable: Money;

  // Workflow
  submittedAt: Date;
  approvedAt?: Date;
  approvedBy?: string;
  paidAt?: Date;
  paymentMethod?: string;
}

type ReportStatus =
  | 'draft'
  | 'submitted'
  | 'pending_approval'
  | 'approved'
  | 'rejected'
  | 'paid';

interface Expense {
  id: string;
  reportId?: string;

  // Details
  type: ExpenseType;
  date: Date;
  amount: Money;
  currency: string;

  // Vendor
  vendor: string;
  category: ExpenseCategory;

  // Business
  businessPurpose: string;
  costCenter: string;
  projectCode?: string;
  billable: boolean;

  // Policy
  withinPolicy: boolean;
  policyException?: string;

  // Receipt
  receiptUrl?: string;
  receiptVerified: boolean;

  // GST (India)
  gstDetails?: {
    gstin?: string;
    gstAmount: Money;
    gstType: 'cgst' | 'sgst' | 'igst';
    inputTaxCredit: boolean;
  };

  // Payment
  paymentMethod: ExpensePaymentMethod;
  reimbursable: boolean;
}

type ExpenseType =
  | 'flight'
  | 'hotel'
  | 'car_rental'
  | 'train'
  | 'meal'
  | 'transport'
  | 'incidentals'
  | 'other';

type ExpensePaymentMethod =
  | 'corporate_card'
  | 'personal_card'
  | 'cash'
  | 'per_diem';

interface SpendAnalytics {
  companyId: string;
  period: { start: Date; end: Date };

  // Totals
  totalSpend: Money;
  spendByCategory: Map<ExpenseCategory, Money>;
  spendByCostCenter: Map<string, Money>;
  spendByVendor: Map<string, Money>;

  // Metrics
  averageTripCost: Money;
  policyComplianceRate: number;
  advanceBookingRate: number;

  // Budget
  budgetUtilization: Map<string, number>; // cost center -> %
}
```

---

## Open Problems

### 1. Receipt Management
**Challenge**: Collecting and matching receipts

**Options**:
- E-receipt integration
- Mobile photo capture
- OCR for scanned receipts
- Receipt matching

### 2. Policy Compliance
**Challenge**: Enforcing policy on manual expenses

**Options**:
- Auto-flag violations
- Require justification
- Manager approval
- Analytics for patterns

### 3. GST Complexity
**Challenge**: Input tax credit rules are complex

**Options**:
- Validate GSTINs
- Calculate eligible credit
- Flag ineligible expenses
- Integration with accounting

### 4. Timeliness
**Challenge**: Employees delay expense submission

**Options**:
- Automated reminders
- Mobile capture
- Pre-populated data
- Deadline enforcement

---

## Integrations Needed

| System | Integration Type | Research Needed |
|---------|-----------------|-----------------|
| **SAP** | ERP | ? |
| **Oracle** | ERP | ? |
| **Microsoft Dynamics** | ERP | ? |
| **Tally** | Accounting (India) | ? |
| **Zoho Books** | Accounting (India) | ? |
| **Concur** | Expense | Competitor, may integrate |
| **Expensify** | Expense | Competitor, may integrate |

---

## Competitor Research Needed

| Competitor | Expense Features | Notable Patterns |
|------------|------------------|------------------|
| **Concur** | ? | ? |
| **Expensify** | ? | ? |
| **Fyle** | ? | India-focused? |

---

## Next Steps

1. Design expense capture system
2. Build approval workflows
3. Implement GST handling
4. Create analytics dashboards
5. Integrate with accounting systems

---

**Status**: Research Phase — Expense patterns unknown

**Last Updated**: 2026-04-27