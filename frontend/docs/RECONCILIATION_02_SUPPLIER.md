# Supplier Reconciliation — Supplier Account Reconciliation

> Research document for reconciling supplier accounts, managing payables, and settlement workflows.

---

## Key Questions

1. **How do we reconcile supplier invoices against our booking records?**
2. **What's the standard payment cycle to suppliers (advance, on-confirmation, post-service)?**
3. **How do we handle supplier overcharges, undercharges, and billing errors?**
4. **What's the reconciliation workflow for commission deductions from supplier payments?**
5. **How do we manage supplier credit notes and adjustments?**

---

## Research Areas

### Supplier Invoice Matching

```typescript
interface SupplierInvoice {
  invoiceId: string;
  supplierId: string;
  invoiceNumber: string;
  invoiceDate: Date;
  dueDate: Date;
  lineItems: InvoiceLineItem[];
  totalAmount: number;
  currency: string;
  status: InvoiceStatus;
}

interface InvoiceLineItem {
  lineId: string;
  bookingId: string;
  description: string;
  quantity: number;
  unitPrice: number;
  total: number;
  ourRecords: OurBookingRecord;
  matchStatus: MatchStatus;
  discrepancy?: Discrepancy;
}

interface OurBookingRecord {
  bookingId: string;
  expectedAmount: number;
  commissionRate: number;
  commissionAmount: number;
  netPayable: number;
  paymentStatus: string;
}

type MatchStatus =
  | 'exact_match'
  | 'amount_mismatch'
  | 'booking_not_found'
  | 'duplicate_charge'
  | 'missing_charge'
  | 'rate_mismatch';
```

### Payment Timing Models

| Supplier Type | Typical Payment Terms | Advance Required |
|--------------|----------------------|-----------------|
| Hotels | Post-checkout, Net 15-30 | Rarely |
| Airlines | At ticketing (via BSP) | Always |
| Transfer operators | Post-service, Net 7-15 | Sometimes |
| Activity providers | Post-service, Net 15-30 | Sometimes |
| Insurance | At issuance | Always |
| Cruise lines | At booking / deposit schedule | Always |
| Rail | At booking | Always |
| Visa services | At submission | Always |

### Commission Deduction Workflow

**Two models:**

**Model A: Agency deducts commission, pays net to supplier**
- Agency collects full payment from customer
- Agency deducts commission
- Agency pays net amount to supplier
- More common for smaller suppliers

**Model B: Customer pays supplier, supplier remits commission**
- Customer pays supplier directly (or agency pays full)
- Supplier remits commission to agency
- More common for large chains (Marriott, etc.)

**Open questions:**
- Which model applies to which supplier categories?
- How to handle mixed models (some bookings Model A, some Model B)?
- What's the reconciliation workflow for each model?

---

## Open Problems

1. **Three-way matching** — Matching supplier invoice ↔ booking record ↔ customer payment is a three-way reconciliation that doesn't always align cleanly.

2. **Commission rate variations** — Different booking types, seasons, or volume tiers may have different commission rates. Applying the correct rate per booking requires accurate rate card management.

3. **Batch vs. individual reconciliation** — Suppliers may send monthly consolidated invoices covering hundreds of bookings. Reconciling at the individual booking level against batch invoices is time-consuming.

4. **Currency risk in supplier payments** — International suppliers may invoice in USD/EUR while the customer paid in INR. Who bears the conversion difference?

5. **Late supplier invoicing** — Some suppliers delay sending invoices, creating reconciliation backlogs. How to enforce timely invoicing through contracts?

---

## Next Steps

- [ ] Map payment timing models per supplier category
- [ ] Design three-way matching algorithm
- [ ] Study commission deduction patterns in Indian travel industry
- [ ] Research supplier payment automation tools
- [ ] Design dispute workflow for invoice discrepancies
