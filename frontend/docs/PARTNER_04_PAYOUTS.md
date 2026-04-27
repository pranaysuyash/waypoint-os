# Partner & Affiliate Management 04: Payouts

> Partner commission calculation, payment processing, and reconciliation

---

## Document Overview

**Focus:** Partner payout management
**Status:** Research Exploration
**Last Updated:** 2026-04-27

---

## Key Questions

### Commission Calculation
- How are partner commissions calculated?
- What about reversals and adjustments?
- How do we handle tiered rates?
- What about bonuses and incentives?

### Payout Processing
- When are partners paid?
- What are payment methods?
- How do we handle international payments?
- What about payment failures?

### Reconciliation
- How do we reconcile with partners?
- What about disputes?
- How do we handle discrepancies?
- What audit trail is needed?

### Reporting
- What reports do partners need?
- How real-time is data?
- What about tax documents?
- How do partners access history?

---

## Research Areas

### A. Commission Calculation

**Base Commission:**

| Formula | Example | Research Needed |
|---------|---------|-----------------|
| **% of booking value** | ₹10,000 × 5% = ₹500 | ? |
| **Fixed per booking** | ₹200 per booking | ? |
| **Tiered** | ₹5K+ = 5%, ₹10K+ = 7% | ? |

**Calculation Triggers:**

| Event | Action | Research Needed |
|--------|--------|-----------------|
| **Booking confirmed** | Calculate pending | ? |
| **Payment received** | Mark as earned | ? |
| **Service consumed** | Finalize commission | ? |
| **Cancellation** | Reverse commission | ? |

**Adjustments:**

| Type | When | Research Needed |
|------|------|-----------------|
| **Reversal** | Cancellation/refund | ? |
| **Correction** | Calculation error | ? |
| **Bonus** | Performance incentive | ? |
| **Penalty** | Policy violation | ? |

**Bonus Calculation:**

| Bonus Type | Trigger | Research Needed |
|------------|---------|-----------------|
| **Volume bonus** | Threshold reached | ? |
| **Growth bonus** | % increase | ? |
| **Category bonus** | Product focus | ? |
| **New customer** | First-time booking | ? |

### B. Payout Scheduling

**Payout Cycles:**

| Cycle | Best For | Research Needed |
|-------|----------|-----------------|
| **Weekly** | High-volume partners | ? |
| **Bi-weekly** | Medium volume | ? |
| **Monthly** | Most partners | ? |
| **Quarterly** | Low volume | ? |

**Payout Triggers:**

| Trigger | Action | Research Needed |
|---------|--------|-----------------|
| **Scheduled date** | Process all payable | ? |
| **Minimum reached** | Process early | ? |
| **Manual request** | Ad-hoc payout | ? |
| **Partner termination** | Final payout | ? |

**Minimum Thresholds:**

| Partner Tier | Minimum | Research Needed |
|--------------|---------|-----------------|
| **Standard** | ₹1,000 | ? |
| **Premium** | ₹500 | ? |
| **VIP** | No minimum | ? |

**Holding Periods:**

| Reason | Duration | Research Needed |
|--------|----------|-----------------|
| **Cancellation risk** | 30-60 days | ? |
| **Payment verification** | 7-14 days | ? |
| **Dispute resolution** | Until resolved | ? |

### C. Payment Methods

**Domestic Payments:**

| Method | Availability | Cost | Research Needed |
|--------|--------------|------|-----------------|
| **Bank transfer (NEFT)** | All | Low | ? |
| **Bank transfer (IMPS)** | All | Medium | ? |
| **UPI** | Limited | Low | ? |
| **Wallet** | Specific | Varies | ? |

**International Payments:**

| Method | Availability | Cost | Research Needed |
|--------|--------------|------|-----------------|
| **SWIFT** | All | High | ? |
| **PayPal** | Many | Medium | ? |
| **Wise** | Many | Medium | ? |
| **Local transfer** | Country-specific | Low | ? |

**Payment Fees:**

| Who Pays | Approach | Research Needed |
|----------|----------|-----------------|
| **Platform pays** | Absorb cost | ? |
| **Partner pays** | Deducted | ? |
| **Split** | Negotiated | ? |

### D. Tax & Compliance

**Tax Deduction:**

| Tax | When | Rate | Research Needed |
|-----|------|------|-----------------|
| **TDS** | Payment to partner | ? | ? |
| **GST** | If applicable | ? | ? |
| **Withholding tax** | International | ? | ? |

**Documentation:**

| Document | When | Research Needed |
|----------|------|-----------------|
| **Tax invoice** | Each payout | ? |
| **TDS certificate** | Annual | ? |
| **Tax summary** | Annual | ? |
| **Form 16/16A** | For partners | ? |

**International Considerations:**

| Issue | Handling | Research Needed |
|-------|----------|-----------------|
| **Tax treaties** | Reduced withholding | ? |
| **Local laws** | Country-specific rules | ? |
| **Currency** | FX conversion | ? |
| **Reporting** | CRS, FATCA | ? |

### E. Reconciliation & Disputes

**Reconciliation Process:**

```
1. Generate payout
   → Calculate commissions
   → Apply deductions
   → Create payment batch

2. Send payment
   → Process transfers
   → Get references
   → Update status

3. Partner confirmation
   → Partner receives
   → Acknowledges receipt
   → Reports issues

4. Reconcile
   → Match bank statements
   → Resolve discrepancies
   → Update records
```

**Dispute Reasons:**

| Reason | Frequency | Research Needed |
|--------|-----------|-----------------|
| **Missing commission** | Common | ? |
| **Wrong amount** | Common | ? |
| **Attribution issue** | Less common | ? |
| **Payment not received** | Rare | ? |

**Resolution:**

| Action | When | Research Needed |
|--------|------|-----------------|
| **Adjust** | Partner right | ? |
| **Explain** | Misunderstanding | ? |
| **Investigate** | Unclear | ? |
| **Deny** | Platform right | ? |

---

## Data Model Sketch

```typescript
interface PartnerCommission {
  commissionId: string;
  partnerId: string;

  // Source
  bookingId: string;
  trackingId: string;

  // Calculation
  bookingValue: number;
  commissionRate: number;
  commissionAmount: number;

  // Bonuses
  bonuses: PartnerBonus[];
  totalCommission: number;

  // Status
  status: CommissionStatus;
  earnedAt?: Date;
  reversedAt?: Date;
  reversalReason?: string;

  // Payout
  payoutId?: string;
  paidAt?: Date;
}

interface PartnerBonus {
  bonusId: string;
  type: BonusType;
  amount: number;
  reason: string;
  calculatedAt: Date;
}

type BonusType =
  | 'volume'
  | 'growth'
  | 'category'
  | 'new_customer'
  | 'special';

interface PartnerPayout {
  payoutId: string;
  partnerId: string;
  period: DateRange;

  // Commissions
  commissions: PartnerCommission[];

  // Summary
  grossCommission: number;
  bonuses: number;
  reversals: number;
  netCommission: number;

  // Deductions
  tds: number;
  fees: number;
  otherDeductions: number;

  // Payment
  netPayable: number;
  currency: string;
  paymentMethod: PaymentMethod;
  paymentDetails: PaymentDetails;

  // Status
  status: PayoutStatus;
  initiatedAt?: Date;
  completedAt?: Date;
  reference?: string;

  // Reconciliation
  partnerConfirmedAt?: Date;
  partnerIssues?: PayoutIssue[];
}

type PayoutStatus =
  | 'pending'
  | 'processing'
  | 'in_transit'
  | 'completed'
  | 'failed'
  | 'disputed';

interface PayoutIssue {
  issueId: string;
  type: IssueType;
  description: string;
  amount?: number;
  raisedBy: string;
  raisedAt: Date;
  status: IssueStatus;
  resolution?: string;
  resolvedAt?: Date;
}

type IssueType =
  | 'missing_commission'
  | 'wrong_amount'
  | 'attribution'
  | 'payment_not_received'
  | 'other';

interface PartnerTaxInfo {
  partnerId: string;

  // Indian tax
  pan?: string;
  tan?: string;
  gstin?: string;
  tdsApplicable: boolean;
  tdsRate: number;

  // International
  country?: string;
  taxId?: string;
  taxTreaty?: string;
  withholdingRate?: number;

  // Documentation
  documents: TaxDocument[];

  // History
  tdsDeducted: number; // YTD
  tdsCertificates: TaxCertificate[];
}

interface TaxDocument {
  type: 'pan' | 'gst' | 'tax_id' | 'other';
  documentUrl: string;
  verified: boolean;
  verifiedAt?: Date;
}

interface TaxCertificate {
  certificateId: string;
  year: number;
  quarter?: number;
  amount: number;
  documentUrl: string;
  issuedAt: Date;
}
```

---

## Open Problems

### 1. Currency Conversion
**Challenge:** FX rates fluctuate

**Options:** Lock at payout, use spot rate, partner chooses

### 2. Payment Failures
**Challenge:** International payments fail

**Options:** Multiple methods, retry logic, manual intervention

### 3. Cost Management
**Challenge:** Payment fees add up

**Options:** Minimum thresholds, absorb vs. pass through, negotiate

### 4. Dispute Volume
**Challenge:** Many small disputes

**Options:** Clear reporting, automation, minimum dispute amount

### 5. Regulatory Complexity
**Challenge:** Different rules by country

**Options:** Local expertise, compliance tools, partner responsibility

---

## Next Steps

1. Define payout rules
2. Build calculation engine
3. Implement payment processing
4. Create reconciliation tools

---

**Status:** Research Phase — Payout patterns unknown

**Last Updated:** 2026-04-27
