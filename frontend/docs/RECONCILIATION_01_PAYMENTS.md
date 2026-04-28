# Financial Reconciliation — Payment Processing & Matching

> Research document for payment processing, matching, and reconciliation workflows in travel.

---

## Key Questions

1. **What payment methods must we support (cards, UPI, bank transfer, wallets, credit lines)?**
2. **How do we match incoming payments to specific bookings when customers combine multiple bookings?**
3. **What's the reconciliation frequency — real-time, daily, weekly?**
4. **How do we handle partial payments, advances, and deposits?**
5. **What fraud detection patterns apply to travel payments?**
6. **How do payment flows differ between B2C and B2B transactions?**

---

## Research Areas

### Payment Method Landscape (India)

```typescript
type PaymentMethod =
  | 'credit_card'       // Visa, Mastercard, Amex, RuPay
  | 'debit_card'        // All card networks
  | 'upi'               // Unified Payments Interface
  | 'net_banking'       // Direct bank transfer
  | 'wallet'            // Paytm, PhonePe, Amazon Pay
  | 'emi'               // Equated monthly installments
  | 'bank_transfer'     // NEFT, RTGS, IMPS
  | 'cheque'            // Still used by some corporates
  | 'cash'              // Physical cash at branches
  | 'credit_line'       // Agency credit to corporate clients
  | 'international_wire'; // SWIFT for international payments

interface PaymentTransaction {
  transactionId: string;
  bookingId: string;
  amount: number;
  currency: string;
  method: PaymentMethod;
  status: PaymentStatus;
  gatewayReference: string;
  timestamp: Date;
  reconciliationStatus: ReconciliationStatus;
}

type PaymentStatus =
  | 'initiated'
  | 'authorized'
  | 'captured'
  | 'failed'
  | 'refunded'
  | 'partially_refunded'
  | 'chargeback'
  | 'disputed';

type ReconciliationStatus =
  | 'unmatched'
  | 'matched'
  | 'partially_matched'
  | 'discrepancy'
  | 'reconciled';
```

### Payment Matching Logic

**Challenges:**
- Customer pays for 3 bookings in one transfer
- Customer overpays or underpays due to currency conversion
- Customer pays from a different account than registered
- Corporate payments with invoice-level breakdown vs. lump-sum

```typescript
interface MatchingRule {
  ruleId: string;
  priority: number;
  conditions: MatchingCondition[];
  action: MatchingAction;
}

interface MatchingCondition {
  field: string;
  operator: 'equals' | 'contains' | 'range' | 'regex';
  value: string | number;
}

type MatchingAction =
  | { type: 'auto_match'; confidence: number }
  | { type: 'manual_review'; reason: string }
  | { type: 'split'; allocation: SplitAllocation[] };

interface SplitAllocation {
  bookingId: string;
  amount: number;
  reason: string;
}
```

### B2B vs. B2C Payment Patterns

| Aspect | B2C | B2B |
|--------|-----|-----|
| Payment timing | Before/at booking | Net 15/30/60 terms |
| Payment method | Cards, UPI | Bank transfer, credit line |
| Invoice format | Simplified receipt | Tax invoice with GST details |
| Credit | Rare | Common (credit limits, terms) |
| Reconciliation | 1:1 (payment to booking) | 1:many (payment to multiple bookings) |
| Dispute | Chargeback via bank | Negotiation and credit notes |
| Volume | High frequency, low value | Low frequency, high value |

---

## Open Problems

1. **Partial payment matching** — Customer books a ₹5L trip, pays ₹2L advance, then ₹3L balance. The two payments need to be linked to the same booking across different time periods.

2. **Currency conversion discrepancies** — A USD payment arrives as INR with slight conversion differences. What tolerance threshold triggers manual review?

3. **Payment gateway reconciliation** — Gateway reports (settlement files) may not match our transaction records due to fees, chargebacks, or timing differences.

4. **Corporate credit management** — Extending credit to corporate clients requires a separate sub-ledger, aging analysis, and collection workflow.

5. **Refund complexity** — A cancelled booking may involve refunds to customer, recovery from supplier, and commission adjustment — all flowing in different directions.

---

## Next Steps

- [ ] Research payment gateway options for India (Razorpay, PayU, BillDesk)
- [ ] Design payment matching algorithm with confidence scoring
- [ ] Study corporate credit management patterns
- [ ] Map refund workflow for different cancellation scenarios
- [ ] Investigate GST compliance requirements for payment reconciliation
