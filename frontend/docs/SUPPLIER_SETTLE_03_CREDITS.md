# Supplier Invoice & Settlement — Credit Notes & Adjustments

> Research document for credit notes, debit notes, airline ADMs/ACMs, and adjustment handling.

---

## Key Questions

1. **How do we process credit notes from suppliers?**
2. **What are ADMs (Airline Debit Memos) and how do we handle them?**
3. **How do we reconcile adjustments against original bookings?**
4. **What's the accounting treatment for credit notes and adjustments?**
5. **How do we prevent duplicate credits and missed adjustments?**

---

## Research Areas

### Credit Note Management

```typescript
interface CreditNoteSystem {
  types: CreditNoteType[];
  processing: CreditNoteProcessing;
  matching: CreditNoteMatching;
  accounting: CreditNoteAccounting;
}

type CreditNoteType =
  | 'cancellation_refund'              // Supplier refunds for cancelled service
  | 'service_downgrade'               // Customer downgraded, partial refund
  | 'overcharge_correction'           // Supplier overcharged, correcting
  | 'volume_rebate'                   // Quarterly/yearly volume-based rebate
  | 'early_payment_discount'          // Discount for paying early
  | 'loyalty_credit'                  // Supplier loyalty program credit
  | 'goodwill_credit';                // Compensation for service issue

interface CreditNoteProcessing {
  creditNoteId: string;
  supplierId: string;
  originalInvoiceId: string;
  reason: string;
  amount: Money;
  taxImpact: TaxImpact;
  status: CreditNoteStatus;
  settlement: CreditNoteSettlement;
}

type CreditNoteStatus =
  | 'received'                        // Credit note received from supplier
  | 'verified'                        // Verified against original invoice
  | 'approved'                        // Approved for settlement
  | 'settled'                         // Refund received or offset against payable
  | 'disputed';                       // Agency disputes the credit amount

// Credit note processing flow:
// 1. Receive credit note from supplier (email, portal, WhatsApp)
// 2. Extract: Credit note number, original invoice, reason, amount
// 3. Match to original invoice in system
// 4. Verify: Amount matches expected refund/cancellation policy
// 5. Calculate tax impact:
//    - If original invoice had GST, credit note must have corresponding GST reversal
//    - GST credit reversal: Reduce ITC claim by GST amount on credit note
// 6. Approval: Route based on amount (same as invoice approval matrix)
// 7. Settlement: Offset against future payment OR receive refund
// 8. Accounting: Reverse original entries
//
// Settlement options:
// Option A: Offset against future payable
//   - Most common for recurring suppliers
//   - Next payment to supplier reduced by credit note amount
//   - Example: Hotel credit note ₹5,000 → Next hotel payment reduced by ₹5,000
//
// Option B: Receive refund
//   - For one-time suppliers or large credits
//   - Supplier transfers refund to agency bank account
//   - Timeline: 7-30 days depending on supplier
//
// Option C: Exchange for alternative service
//   - Instead of cash refund, supplier offers equivalent service
//   - Example: Hotel gives free night instead of cash refund
//   - Accounting: No cash movement, adjust booking cost

// GST impact of credit notes:
// Original invoice: ₹18,000 (₹17,143 + CGST ₹429 + SGST ₹429)
// Credit note: ₹5,000 (₹4,762 + CGST ₹119 + SGST ₹119)
//
// GST return impact:
// GSTR-1: Report credit note (reduces outward supply)
// ITC reversal: Reduce input credit claim by ₹238
// Net effect: Agency's GST liability reduced by credit note GST amount
//
// Time limit for GST credit notes:
// Must be issued before September of following financial year
// OR before filing annual return, whichever is earlier
// Credit notes after this period: GST reversal not allowed
```

### Airline ADM/ACM Management

```typescript
interface AirlineADM {
  admId: string;
  airline: string;
  ticketNumber: string;
  pnr: string;
  reason: ADMReason;
  amount: Money;
  issuedDate: Date;
  dueDate: Date;
  status: ADMStatus;
  dispute: ADMDispute?;
}

type ADMReason =
  | 'fare_difference'                  // Incorrect fare applied
  | 'tax_difference'                  // Tax calculation error
  | 'commission_overpayment'          // Agency claimed excess commission
  | 'fare_rule_violation'             // Booking violated fare rules
  | 'ticketing_deadline_missed'       // Ticket not issued in time
  | 'duplicate_booking'               // Same passenger booked twice
  | 'name_change_fee'                 // Name correction charge
  | 'reissue_difference'              // Fare difference on reissued ticket
  | 'no_show'                         // Passenger no-show, agency liable
  | 'card_fraud';                     // Fraudulent card payment

type ADMStatus =
  | 'received'                        // ADM received from airline
  | 'under_review'                    // Agency reviewing validity
  | 'accepted'                        // Agency accepts, will pay
  | 'disputed'                        // Agency disputes the ADM
  | 'settled'                         // ADM paid via BSP
  | 'expired';                        // Dispute period expired

// ADM processing:
// 1. Receive ADM notification (BSP system or airline direct)
// 2. Match to ticket/PNR in system
// 3. Verify reason: Is the ADM valid?
//    - Fare difference: Check GDS fare quote vs. ticketed fare
//    - Commission overpayment: Check agreed commission rate
//    - Fare rule violation: Check fare rules at time of booking
//    - Ticketing deadline: Check if ticket was issued on time
// 4. If valid: Accept ADM, settle via BSP
// 5. If invalid: Dispute with evidence
//
// ADM dispute process:
// - Gather evidence: GDS booking screenshots, fare quotes, emails
// - Submit dispute through BSP system or airline portal
// - Timeline: 30 days from ADM receipt to dispute
// - Airline response: 30 days to accept or reject dispute
// - Escalation: IATA if airline rejects valid dispute
// - Resolution: ADM cancelled, reduced, or upheld
//
// ACM (Airline Credit Memo):
// - Opposite of ADM: Airline credits the agency
// - Reasons: Overcharge correction, commission adjustment, refund
// - ACM reduces next BSP settlement (agency pays less)
//
// BSP settlement with ADMs/ACMs:
// Week 17 settlement:
//   Sales: ₹21,500
//   Refunds: -₹4,200
//   ADM (IndiGo fare diff): +₹500
//   ACM (Air India overcharge): -₹300
//   Net: ₹21,500 - ₹4,200 + ₹500 - ₹300 = ₹17,500
//   Bank debited: ₹17,500
```

### Adjustment Accounting

```typescript
interface AdjustmentAccounting {
  creditNoteEntries: CreditNoteEntry[];
  admEntries: ADMEntry[];
  nettingEntries: NettingEntry[];
  taxAdjustments: TaxAdjustment[];
}

// Credit note accounting:
// Original hotel invoice for ₹18,000 (net ₹17,143 + GST ₹857):
//   Debit: 5111 — Hotel Cost        ₹17,143
//   Debit: 1142 — GST ITC             ₹857
//   Credit: 2111 — Supplier Payable ₹18,000
//
// Credit note for ₹5,000 (partial cancellation):
//   (Reverse original entry proportionally)
//   Debit: 2111 — Supplier Payable   ₹5,000
//   Credit: 5111 — Hotel Cost         ₹4,762
//   Credit: 1142 — GST ITC             ₹238
//   (Reduce cost, reverse ITC)
//
// If credit note settled by offset against next payment:
// Next hotel payment: ₹12,000 - ₹5,000 (offset) = ₹7,000
//   Debit: 2111 — Supplier Payable   ₹7,000
//   Debit: 2111 — Supplier Payable   ₹5,000  (credit note offset)
//   Credit: 1111 — Bank Account      ₹7,000
//   (Only ₹7,000 bank debit, ₹5,000 offset internally)
//
// ADM accounting:
// IndiGo ADM ₹500 (fare difference):
//   Debit: 5112 — Flight Cost          ₹500
//   Credit: 2112 — Airline Payable     ₹500
//   (Additional cost recognized, included in next BSP settlement)
//
// ACM accounting:
// Air India ACM ₹300 (overcharge refund):
//   Debit: 2112 — Airline Payable      ₹300
//   Credit: 5112 — Flight Cost          ₹300
//   (Reduce flight cost, deducted from next BSP settlement)
```

---

## Open Problems

1. **ADM validity verification** — Airlines often issue ADMs with vague reasons. Agents lack data (original fare quotes, GDS screenshots) to dispute effectively. Need automatic ADM evidence collection.

2. **Credit note GST matching** — Credit note GST must exactly match original invoice GST for ITC reversal. Rounding differences create reconciliation gaps.

3. **Cross-period adjustments** — Credit note for March invoice processed in May. GST return for March already filed. Requires amendment or adjustment in current period.

4. **Supplier credit tracking** — Multiple credit notes from same supplier across different periods. Tracking net credit position per supplier is complex without automation.

5. **Exchange rate on foreign credits** — Credit note for a USD-denominated hotel booking. Exchange rate at booking differs from credit note date. Creates forex gain/loss entries.

---

## Next Steps

- [ ] Build credit note processing with GST reversal automation
- [ ] Create ADM/ACM management with dispute evidence collection
- [ ] Design adjustment accounting with automatic journal entries
- [ ] Build supplier net credit position tracking
- [ ] Study airline ADM systems (BSPlink, IATA ADM Manager)
