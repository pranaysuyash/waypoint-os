# Commission Management 03: Payouts

> Commission payment processing and reconciliation

---

## Document Overview

**Focus:** Commission payout processing
**Status:** Research Exploration
**Last Updated:** 2026-04-27

---

## Key Questions

### Payout Processing
- When are payouts processed?
- What are payout cycles?
- How are payments made?
- What about minimum thresholds?

### Payment Methods
- How do agents receive commissions?
- What payment methods are supported?
- How do we handle bank details?
- What about payment fees?

### Reconciliation
- How do we reconcile payments?
- What if payment fails?
- How do we handle returns?
- What about tax reporting?

### Compliance
- What tax information is needed?
- How do we handle TDS?
- What about GST on commissions?
- What are reporting requirements?

---

## Research Areas

### A. Payout Scheduling

**Payout Cycles:**

| Cycle | Use Case | Research Needed |
|-------|----------|-----------------|
| **Weekly** | High-volume agents | ? |
| **Bi-weekly** | Standard | ? |
| **Monthly** | Most common | ? |
| **Quarterly** | Low volume | ? |
| **On demand** | Special arrangements | ? |

**Payout Triggers:**

| Trigger | Action | Research Needed |
|---------|--------|-----------------|
| **Scheduled date** | Process batch | ? |
| **Threshold reached** | Process early | ? |
| **Manual request** | Ad-hoc payout | ? |
| **Agent termination** | Final payout | ? |

**Minimum Thresholds:**

| Agent Tier | Minimum Payout | Research Needed |
|------------|----------------|-----------------|
| **Standard** | ₹1,000 | ? |
| **Premium** | ₹500 | ? |
| **VIP** | No minimum | ? |

**Rollover:**

| Scenario | Handling | Research Needed |
|----------|----------|-----------------|
| **Below threshold** | Roll to next period | ? |
| **Agent inactive** | Hold until claim | ? |
| **Account closed** | Escheat process | ? |

### B. Payment Methods

**Supported Methods:**

| Method | Availability | Fees | Research Needed |
|--------|--------------|------|-----------------|
| **Bank transfer (IMPS)** | Instant | Medium | ? |
| **Bank transfer (NEFT)** | Standard | Low | ? |
| **UPI** | Limited amounts | Low | ? |
| **Check** | Manual | Low | ? |
| **Wallet** | Specific | Varies | ? |

**Bank Account Management:**

| Action | Workflow | Research Needed |
|--------|----------|-----------------|
| **Add account** | Verify details | ? |
| **Change account** | Re-verify | ? |
| **Delete account** | Confirmation | ? |
| **Set default** | Preference | ? |

**Verification:**

| Method | Description | Research Needed |
|--------|-------------|-----------------|
| **Penny drop** | Small deposit verification | ? |
| **Instant verification** | Bank API | ? |
| **Manual** | Document upload | ? |

### C. Payout Processing

**Batch Processing:**

```
1. Generate payout batch
   → Select payable commissions
   → Group by agent
   → Calculate totals

2. Validate
   → Check bank details
   → Verify minimum
   → Check holds

3. Create payments
   → Generate payment instructions
   → Calculate fees
   → Apply tax if needed

4. Execute
   → Process transfers
   → Update statuses
   → Handle failures

5. Reconcile
   → Confirm payments
   → Update ledgers
   → Generate statements
```

**Payment Failure Handling:**

| Failure Type | Retry | Research Needed |
|--------------|-------|-----------------|
| **Invalid account** | Manual fix | ? |
| **Insufficient funds** | Retry next cycle | ? |
| **Technical error** | Auto retry | ? |
| **Bank timeout** | Retry | ? |

**Reconciliation:**

| Step | Description | Research Needed |
|------|-------------|-----------------|
| **UTR matching** | Match bank reference | ? |
| **Status update** | Mark as paid | ? |
| **Exception handling** | Investigate mismatches | ? |

### D. Tax & Compliance

**Tax Deduction:**

| Tax | When | Rate | Research Needed |
|-----|------|------|-----------------|
| **TDS** | Payment > threshold | ? | ? |
| **GST** | If applicable | ? | ? |

**TDS Rules:**

| Scenario | Treatment | Research Needed |
|----------|-----------|-----------------|
| **PAN provided** | Standard rate | ? |
| **No PAN** | Higher rate | ? |
| **Below threshold** | No deduction | ? |

**Reporting:**

| Report | Frequency | Research Needed |
|--------|-----------|-----------------|
| **Commission statement** | Per payout | ? |
| **TDS certificate** | Annual | ? |
| **Tax summary** | Annual | ? |
| **Form 26AS** | Integration | ? |

**Compliance Documents:**

| Document | Required | Research Needed |
|----------|----------|-----------------|
| **PAN card** | Yes | ? |
| **Aadhaar** | Sometimes | ? |
| **Bank proof** | Yes | ? |
| **GST registration** | If applicable | ? |

---

## Data Model Sketch

```typescript
interface PayoutBatch {
  batchId: string;
  period: DateRange;
  createdAt: Date;
  processedAt?: Date;

  // Summary
  totalAmount: number;
  totalCommissions: number;
  totalAgents: number;

  // Status
  status: PayoutStatus;

  // Payments
  payments: PayoutPayment[];

  // Financial
  totalDeductions: number;
  totalFees: number;
  netAmount: number;

  // Reconciliation
  reconciledAt?: Date;
  reconciliationId?: string;
}

type PayoutStatus =
  | 'pending'
  | 'processing'
  | 'completed'
  | 'failed'
  | 'partial';

interface PayoutPayment {
  paymentId: string;
  batchId: string;
  agentId: string;

  // Amount
  grossAmount: number;
  deductions: TaxDeduction[];
  fees: PaymentFee[];
  netAmount: number;

  // Method
  method: PaymentMethod;
  bankAccount: BankAccount;

  // Status
  status: PaymentStatus;
  reference?: string; // UTR, etc.

  // Timing
  initiatedAt: Date;
  completedAt?: Date;
  failedAt?: Date;
  failureReason?: string;

  // Commissions
  commissionIds: string[];
}

interface TaxDeduction {
  type: 'TDS' | 'GST' | 'other';
  amount: number;
  reference?: string;
}

interface PaymentFee {
  type: 'processing' | 'transfer' | 'other';
  amount: number;
}

type PaymentMethod =
  | 'imps'
  | 'neft'
  | 'upi'
  | 'check'
  | 'wallet';

type PaymentStatus =
  | 'pending'
  | 'initiated'
  | 'completed'
  | 'failed'
  | 'reversed';

interface BankAccount {
  accountId: string;
  agentId: string;

  // Details
  accountHolder: string;
  accountNumber: string; // Encrypted
  ifsc: string;
  bankName: string;

  // Status
  verified: boolean;
  verifiedAt?: Date;
  isDefault: boolean;

  // Metadata
  createdAt: Date;
}

interface PayoutConfiguration {
  agentId: string;

  // Schedule
  payoutCycle: PayoutCycle;
  payoutDay?: number; // Day of month

  // Thresholds
  minimumPayout: number;

  // Payment
  defaultPaymentMethod: PaymentMethod;
  defaultBankAccount?: string;

  // Tax
  panNumber?: string;
  gstin?: string;
  tdsApplicable: boolean;

  // Holds
  payoutHolds?: PayoutHold[];
}

type PayoutCycle =
  | 'weekly'
  | 'bi_weekly'
  | 'monthly'
  | 'quarterly';

interface PayoutHold {
  holdId: string;
  reason: string;
  amount?: number;
  until?: Date;
  createdAt: Date;
}
```

---

## Open Problems

### 1. Payment Failures
**Challenge:** Some payments always fail

**Options:** Better verification, retry logic, manual intervention

### 2. Cash Flow
**Challenge:** Paying before receiving from supplier

**Options:** Hold period, credit line, reserve

### 3. Tax Complexity
**Challenge:** Varying tax rules

**Options:** Configurable rules, expert review, integration

### 4. Bank Verification
**Challenge:** Failed transfers cost money

**Options:** Penny drop, instant verification, manual checks

### 5. Reconciliation Effort
**Challenge:** Manual reconciliation is time-consuming

**Options:** Automation, bank APIs, matching algorithms

---

## Next Steps

1. Define payout cycles
2. Build payment processing
3. Implement bank verification
4. Create tax calculation

---

**Status:** Research Phase — Payout patterns unknown

**Last Updated:** 2026-04-27
