# Payments & Gateways — First Principles Analysis

**Date:** 2026-04-29  
**Context:** Travel Agency Agent — solo dev, NO payment collection  
**Approach:** Track payment status/amounts only, NO gateways, NO money movement  

---

## 1. The Core Principle: We Track, We Don't Collect**

### Your Clarification

> "payment collection is something i want to avoid … maybe just things like is payment done, agreed, amount etc being captured but no actual transaction"

### What This Means (Solo Dev Reality)

| What We DO | What We DON'T DO |
|--------------|-------------------|
| ✅ Track if payment is done | ❌ Process credit card / UPI |
| ✅ Record agreed amount | ❌ Integrate Stripe/Razorpay |
| ✅ Store payment method (for records) | ❌ Tokenize cards (PCI compliance) |
| ✅ Track EMI status (customer promised) | ❌ Disburse EMI loans |
| ✅ Log refund decisions | ❌ Actually refund via gateway |
| ✅ Store invoice PDFs (customer sent) | ❌ Generate GST invoices |
| ✅ Record commission agreed | ❌ Payout commissions to agents |

**My insight:**  
As a solo dev, you're building a **tracking/coordination system**, not a fintech platform.  
Money moves **outside the system** (bank transfer, cash, UPI direct to agency).  
System just records: "Customer agreed ₹50,000, paid on 2026-04-15 via UPI."

---

## 2. My Lean Payment Model (Status-Only)**

### Payment Record (What We Track)**

```json
{
  "payment_id": "string (UUID)",
  "booking_id": "string",
  "recorded_by_agent_id": "string",  // Who marked it as paid
  
  // What was agreed?
  "agreed_amount": "number (float)",
  "agreed_currency": "string",  // "INR", "USD"
  "agreed_at": "string (ISO8601)",  // When customer accepted quote
  
  // What actually happened?
  "paid_amount": "number (float)",  // May differ (advance, part-payment)
  "paid_currency": "string",
  "payment_status": "NOT_STARTED | PARTIAL | COMPLETED | OVERDUE",
  "paid_at": "string | null",  // When customer actually paid
  
  // How did they pay? (for records, no processing)
  "payment_method_type": "UPI | BANK_TRANSFER | CASH | CHEQUE | CREDIT_CARD | EMI",
  "payment_reference": "string | null",  // UPI txn ID, cheque number
  "payer_name": "string | null",  // Who paid (if not customer)
  "payer_bank": "string | null",  // Bank name (for follow-up)
  
  // Commission agreed (between agency & agent/vendor)
  "agent_commission_agreed_percent": "number (0.0-100.0)",
  "agent_commission_agreed_amount": "number (float)",
  "vendor_commission_agreed_percent": "number (0.0-100.0)",
  
  // Notes (critical for disputes)
  "notes": "string | null",  // "Customer paid ₹30k advance, ₹20k pending"
  "receipt_url": "string | null"  // Customer sent screenshot/PDF
}
```

**My insight:**  
`payment_reference` is critical — when customer says "I paid," you need to cross-check UPI ID / cheque number.  
`payer_name` — sometimes company pays for employee, or parent pays for child.

---

### EMI Tracking (Status Only, No Loans)**

```json
{
  "emi_tracking_id": "string (UUID)",
  "booking_id": "string",
  "is_emi": "boolean",  // Was EMI agreed?
  
  // What customer promised
  "total_emi_amount": "number (float)",
  "emi_tenure_months": "integer",
  "emi_monthly_amount": "number (float)",
  "emi_start_date": "string (ISO8601)",
  
  // Customer's bank/loan info (for follow-up, no processing)
  "loan_provider": "string | null",  // "HDFC Bank", "Bajaj Finserv"
  "loan_account_number": "string | null",  // For follow-up calls
  "loan_status": "APPROVED | PENDING | REJECTED | CLOSED",
  
  // Tracking (did they pay?)
  "installments_paid": "integer",  // Out of total_emi_tenure_months
  "next_due_date": "string (ISO8601) | null",
  "overdue_count": "integer",  // How many missed?
  
  // Agency action
  "reminder_sent_count": "integer",  // How many reminders sent
  "escalated_to_agent_id": "string | null",  // Senior agent took over
  "notes": "string | null"  // "Customer struggling, extended deadline"
}
```

**My insight:**  
`loan_account_number` — you need this for **follow-up calls** ("Your loan #12345 is overdue").  
`overdue_count` should **auto-alert** manager if >2.

---

### Refund Tracking (Decision Only, No Processing)**

```json
{
  "refund_id": "string (UUID)",
  "booking_id": "string",
  "reason": "CUSTOMER_REQUEST | VENDOR_CANCELLATION | AGENCY_ERROR | FORCE_MAJEURE",
  "requested_at": "string (ISO8601)",
  "requested_by": "CUSTOMER | AGENT | VENDOR",
  
  // Decision
  "status": "PENDING_APPROVAL | APPROVED | REJECTED | PROCESSING | COMPLETED",
  "approved_by_agent_id": "string | null",
  "approved_at": "string | null",
  "rejection_reason": "string | null",
  
  // Amount (what was decided)
  "refund_amount_agreed": "number (float)",
  "refund_method": "ORIGINAL_PAYMENT | BANK_TRANSFER | WALLET",  // Where to send
  "refund_reference": "string | null",  // Cheque number, UPI reference
  
  // Proof (customer sent proof to agency)
  "customer_proof_url": "string | null",  // Screenshot of cancellation
  "agency_proof_url": "string | null",  // Agency sent cheque photo
  
  // Actual money movement (happens OUTSIDE system)
  "actually_paid_by_agency": "boolean",
  "actually_paid_at": "string | null",
  "notes": "string | null"  // "Sent via HDFC cheque #123456"
}
```

**My insight:**  
`actually_paid_by_agency` — system NEVER pays, but tracks "did we actually send the cheque?"  
`customer_proof_url` — customer sends cancellation screenshot, agency stores it for records.

---

## 3. Invoice Tracking (PDF Storage Only)**

```json
{
  "invoice_id": "string (UUID)",
  "invoice_number": "string",  // "INV-2026-0042" (your own format)
  "booking_id": "string",
  "invoice_type": "PROFORMA | COMMERCIAL | CREDIT_NOTE",
  
  // Generated by YOU (not system) — you upload PDF
  "pdf_url": "string | null",  // Where you stored the PDF
  "generated_by_agent_id": "string",
  "generated_at": "string (ISO8601)",
  
  // Basic fields (for display, no GST calculation)
  "subtotal": "number (float)",
  "tax_amount": "number (float) | null",  // If you collect tax
  "total_amount": "number (float)",
  "currency": "string",
  
  // Customer acknowledgment
  "sent_to_customer_at": "string | null",
  "customer_acknowledged": "boolean",
  "customer_acknowledged_at": "string | null"
}
```

**My insight:**  
As solo dev, YOU generate invoices in **external tool** (Zoho, Excel, physical).  
System just **stores PDF URL** so agents can quickly find "what did we quote?"

---

## 4. What We DON'T Build (Solo Dev Boundaries)**

| Feature | Why Skip It | Alternative |
|---------|--------------|-------------|
| **Payment gateway** | PCI compliance, complex, not needed | Customer pays via UPI/cheque directly |
| **EMI disbursement** | You're not a lender | Customer arranges own loan, you track status |
| **Automatic refund** | Money movement = risk | Agency pays manually, marks as "done" |
| **GST invoice generation** | Tax software exists | Generate in Zoho/Excel, upload PDF |
| **Commission payout** | You pay manually | Record what you owe, pay via bank transfer |
| **Reconciliation** | Needs bank API integration | Quarterly manual check |

**My insight:**  
Every payment feature you skip = **10-20 hours saved** as solo dev.  
Focus on **coordination** (who owes what, who paid what) — not money movement.

---

## 5. Current Schema vs Lean Payment Model**

| Concept | Current Schema | My Lean Model |
|---------|---------------|-------------------|
| Payment status | None | `payment_status` (NOT_STARTED → COMPLETED) |
| Agreed amount | None | `agreed_amount` + `agreed_currency` |
| Payment method | `facts.payment_method` (FieldSlot) | `payment_method_type` (UPI, CASH, etc.) |
| EMI tracking | None | `emi_tracking_id` with tenure + overdue count |
| Refund decision | None | `refund_id` with status (no processing) |
| Invoice PDF | None | `invoice.pdf_url` (storage only) |
| Commission agreed | None | `agent_commission_agreed_percent` (track only) |
| Payment proof | None | `receipt_url` (customer sent screenshot) |

---

## 6. Decisions Needed (Simple Answers)**

| Decision | Options | My Recommendation |
|-----------|---------|-------------------|
| Track UPI references? | Yes / No | **YES** — ₹50 sent via UPI needs reference for disputes |
| EMI tracking? | Full / Simple status | **Simple** — loan_provider + overdue_count only |
| Invoice generation? | System / Manual upload | **Manual upload** — generate outside, store PDF |
| Refund processing? | System / Mark as done | **Mark as done** — agency pays manually |
| Commission calculation? | Auto / Manual entry | **Manual entry** — agent agrees % verbally |
| Payment alerts? | Yes / No | **YES** — "EMI overdue" → alert agent |

---

## 7. Next Discussion: Notifications & Alerts**

Now that we know:
- **Enquiry types** (new tour, in-progress issue, post-trip)
- **Channels** (WhatsApp, Telegram, WeChat, email, etc.)
- **Customer model** (individual vs corporate, VIP, health score)
- **Human Agent model** (skills, workload, performance)
- **Vendor model** (types, contracts, performance)
- **Communication model** (comms tracking, drafts, templates)
- **Booking model** (contracts, payments, modifications)
- **Payments** (status-only tracking, NO collection)

We need to discuss: **WHEN and HOW do we alert people?**

Key questions for next discussion:
1. **SLA alerts** — agent hasn't replied in 4h → alert manager?
2. **Follow-up reminders** — vendor hasn't quoted in 24h → auto-remind?
3. **Payment alerts** — EMI overdue, invoice pending?
4. **WhatsApp alerts** — push notifications to agents' phones?
5. **Escalation chains** — who gets alerted when SLA breached?
6. **Digest notifications** — daily summary for managers?
7. **Customer notifications** — booking confirmations, payment reminders?
8. **Solo dev reality** — what can we skip? (email only? WhatsApp only?)

---

**Next file:** `Docs/discussions/notifications_and_alerts_2026-04-29.md`

---

## 2. My Payment Gateway Model**

### Supported Gateways (By Region)**

```json
{
  "gateway_id": "string (UUID)",
  "gateway_name": "STRIPE | RAZORPAY | PAYPAL | PAYTM | BANK_TRANSFER | CASH | EMI_PARTNER",
  
  // Regional support
  "supported_countries": ["IN", "US", "AE", "TH", "ID"],
  "default_currency": "INR",
  "supports_multi_currency": "boolean",
    
  // Capabilities
  "supports_emi": "boolean",
  "supports_upi": "boolean",
  "supports_net_banking": "boolean",
  "supports_wallets": ["paytm", "phonepe", "gpay"],
  "supports_international_cards": "boolean",
    
  // Configuration
  "is_active": "boolean",
  "is_default_for_countries": ["IN"],
  "webhook_url": "string | null",
  "api_keys": {
    "test_publishable": "string | null",
    "test_secret": "string | null",
    "live_publishable": "string | null",
    "live_secret": "string | null"
  },
  "fees_percent": "number (0.0-100.0)",  // 2.5% for Stripe
  "fees_fixed": "number (float)",  // Fixed fee per transaction
  "settlement_days": "integer"  // T+2, T+3, etc.
}
```

**My insight:**  
`gateway_name = BANK_TRANSFER` and `CASH` are valid "gateways" — track them even if no API.  
`settlement_days` affects **cash flow** — agency pays vendor only after receiving from gateway.

---

### Payment Method Types (What Customer Sees)**

```json
{
  "payment_method_id": "string (UUID)",
  "method_type": "CREDIT_CARD | DEBIT_CARD | UPI | NET_BANKING | WALLET | CASH | CHEQUE | EMI | BANK_TRANSFER",
    
  // Card-specific
  "card_network": "VISA | MASTERCARD | RUPAY | AMEX | DINERS",
  "card_last4": "string",  // "4242"
  "card_expiry": "string",  // "12/28"
  "card_token": "string | null",  // Tokenized by gateway
    
  // UPI-specific
  "upi_id": "string | null",  // "user@paytm"
    
  // Wallet-specific
  "wallet_provider": "PAYTM | PHONEPE | GPAY | AMAZON_PAY",
  "wallet_identifier": "string | null",
    
  // EMI-specific
  "emi_partner": "BAJAJ_FINSERV | HDFC_BANK | ICICI_BANK",
  "emi_tenure_months": "integer",
  "emi_interest_rate": "number (0.0-100.0)",
  "emi_monthly_payment": "number (float)",
    
  // Verification
  "is_verified": "boolean",
  "verified_at": "string (ISO8601)",
  "is_default": "boolean"  // Customer's default payment method
}
```

**My insight:**  
Store `card_token`, NOT raw card numbers (PCI-DSS compliance).  
`emi_partner` creates a **new financial relationship** — agency acts as loan facilitator.

---

## 3. Transaction Model (Money Movement)**

### Payment Transaction (Customer → Agency)**

```json
{
  "transaction_id": "string (UUID)",
  "booking_id": "string",
  "payment_method_id": "string",
  "gateway_id": "string",
    
  // Amounts
  "currency": "string",  // "INR", "USD"
  "amount_subtotal": "number (float)",  // Base amount
  "tax_amount": "number (float)",  // GST/VAT
  "gateway_fee": "number (float)",  // Stripe/Razorpay fee
  "total_amount": "number (float)",  // What customer pays
  "exchange_rate": "number (float) | null",  // If multi-currency
  "base_currency_amount": "number (float)",  // Converted to agency base currency
    
  // Status (critical for reconciliation)
  "status": "INITIATED | AUTHORIZED | CAPTURED | FAILED | REFUNDED | DISPUTED",
  "gateway_transaction_id": "string | null",  // Stripe/Razorpay ID
  "gateway_response": "object | null",  // Raw gateway response
    
  // Timing
  "initiated_at": "string (ISO8601)",
  "captured_at": "string | null",
  "settled_at": "string | null",  // When money reaches agency account
    
  // Refund (if any)
  "refund_transactions": ["string (transaction_id)"],  // Links to refund txns
  "refund_reason": "string | null",
    
  // Internal
  "created_by_agent_id": "string",
  "notes": "string | null"
}
```

**My insight:**  
`status = AUTHORIZED` ≠ `CAPTURED` — auth holds money, capture actually takes it.  
`settled_at` is critical for **cash flow forecasting** — money isn't yours until settled.

---

### Vendor Payout (Agency → Vendor)**

```json
{
  "payout_id": "string (UUID)",
  "booking_item_id": "string",  // Which flight/hotel
  "vendor_id": "string",
    
  // Amounts
  "currency": "string",
  "gross_amount": "number (float)",  // What customer paid for this item
  "agency_commission": "number (float)",  // Agency keeps this
  "vendor_payout_amount": "number (float)",  // What vendor gets
  "commission_rate_applied": "number (0.0-100.0)",
    
  // Timing (critical for vendor relationships)
  "payout_policy": "IMMEDIATE | T+7 | T+15 | T+30 | POST_TRAVEL",
  "scheduled_payout_date": "string (ISO8601)",
  "actual_payout_date": "string | null",
    
  // Status
  "status": "PENDING | PROCESSING | COMPLETED | FAILED | DISPUTED",
  "payout_method": "BANK_TRANSFER | CHEQUE | WALLET",
  "transaction_reference": "string | null",  // Bank reference
    
  // Deductions
  "tds_deducted": "number (float) | null",  // Tax deducted at source (India)
  "gateway_fee_deducted": "number (float) | null",
    
  // Internal
  "approved_by_agent_id": "string",  // Who approved the payout
  "invoice_url": "string | null"  // Invoice sent to vendor
}
```

**My insight:**  
`payout_policy = POST_TRAVEL` is common — agency holds money until customer returns (risk mitigation).  
`tds_deducted` is India-specific — 10% TDS on vendor payments (section 194J/194C).

---

## 4. Invoice & Tax Model**

### Invoice Generation (Legal Requirement)**

```json
{
  "invoice_id": "string (UUID)",
  "invoice_number": "string",  // "INV-2026-0042" (GST-compliant)
  "booking_id": "string",
  "customer_id": "string",
    
  // Invoice details
  "invoice_type": "PROFORMA | COMMERCIAL | CREDIT_NOTE | DEBIT_NOTE",
  "invoice_date": "string (ISO8601)",
    
  // Seller (Agency)
  "seller_name": "string",
  "seller_gstin": "string | null",  // India GST
  "seller_address": "string",
  "seller_pan": "string | null",  // India PAN
    
  // Buyer (Customer)
  "buyer_name": "string",
  "buyer_gstin": "string | null",  // B2B customers
  "buyer_address": "string",
  "buyer_pan": "string | null",
    
  // Line items
  "line_items": [
    {
      "description": "Bali Family Package - 5N/6D",
      "hsn_sac_code": "string",  // GST code (998559 for tours)
      "quantity": "integer",
      "unit_price": "number (float)",
      "tax_rate": "number (0.0-100.0)",  // 5%, 12%, 18%
      "tax_amount": "number (float)",
      "line_total": "number (float)"
    }
  ],
    
  // Totals
  "subtotal": "number (float)",
  "total_tax": "number (float)",
  "total_amount": "number (float)",
  "currency": "string",
    
  // Status
  "status": "DRAFT | ISSUED | PAID | CANCELLED | DISPUTED",
  "pdf_url": "string | null",
    
  // GST (India-specific)
  "gst_breakup": {
    "cgst": "number (float)",  // Central GST
    "sgst": "number (float)",  // State GST
    "igst": "number (float)",  // Integrated GST (inter-state)
    "cess": "number (float) | null"  // Compensation cess
  }
}
```

**My insight:**  
`invoice_type = CREDIT_NOTE` handles **refunds** (negative invoice).  
`hsn_sac_code` is mandatory for GST — wrong code = penalty.

---

## 5. EMI & Credit Model**

### EMI Partner (For Installment Payments)**

```json
{
  "emi_partner_id": "string (UUID)",
  "partner_name": "BAJAJ_FINSERV | HDFC_BANK | ICICI_BANK | EXTERNAL_FINANCIER",
    
  // Agreement
  "agency_commission_share": "number (0.0-100.0)",  // How much agency gets
  "interest_rate_range": {
    "min": "number (0.0-100.0)",
    "max": "number (0.0-100.0)"
  },
  "tenure_options_months": [3, 6, 9, 12, 18, 24],
    
  // Customer eligibility
  "min_credit_score": "integer | null",  // CIBIL score
  "min_monthly_income": "number (float) | null",
  "required_documents": ["PAN_CARD", "AADHAAR", "BANK_STATEMENT"],
    
  // Process
  "application_process": "INSTANT | DOCUMENT_VERIFICATION | MANUAL_REVIEW",
  "approval_timeline_hours": "integer",
    
  // Status
  "is_active": "boolean",
  "api_integration": "boolean",  // Can we auto-approve?
  "api_endpoint": "string | null"
}
```

**My insight:**  
`agency_commission_share` — EMI partners often **share** their interest income with the agency.  
`min_credit_score` — agency risks **default** if customer doesn't pay EMI.

---

## 6. Payment Reconciliation**

### Why This Matters

Gateways send money in batches — you need to match:
- **Gateway settlement report** (what they say they paid)
- **Bank statement** (what actually arrived)
- **Booking transactions** (what you recorded)

```json
{
  "reconciliation_id": "string (UUID)",
  "settlement_date": "string (ISO8601)",
  "gateway_id": "string",
    
  // Gateway claims
  "gateway_settlement_id": "string",
  "gateway_claimed_amount": "number (float)",
  "gateway_fees": "number (float)",
  "gateway_net_amount": "number (float)",
    
  // Bank statement
  "bank_reference": "string",
  "bank_received_amount": "number (float)",
  "bank_fees": "number (float)",
    
  // Our records
  "booking_transaction_ids": ["string"],
  "our_recorded_amount": "number (float)",
    
  // Reconciliation
  "status": "MATCHED | DISCREPANCY | PENDING_INVESTIGATION",
  "discrepancy_amount": "number (float) | null",
  "discrepancy_reason": "string | null",  // "Gateway fee higher", "Bank fee unexpected"
  "resolved_by_agent_id": "string | null",
  "resolved_at": "string | null"
}
```

**My insight:**  
Reconciliation is **accounting drudgery** — system should auto-match 95% of cases.  
`status = DISCREPANCY` needs **manager alert** (potential fraud/theft).

---

## 7. Current Schema vs Payment Model**

| Concept | Current Schema | My Proposed Model |
|---------|---------------|-------------------|
| Payment gateway | None | `PaymentGateway` entity (Stripe, Razorpay) |
| Payment method | `facts.payment_method` (FieldSlot) | `PaymentMethod` entity with tokenization |
| Transaction | None | `PaymentTransaction` with status flow |
| Vendor payout | None | `VendorPayout` (agency → vendor) |
| Invoice | None | `Invoice` with GST/ VAT compliance |
| EMI | None | `EMIPartner` + `EMIApplication` |
| Reconciliation | None | `Reconciliation` auto-matching |

---

## 8. Decisions Needed**

| Decision | Options | My Recommendation |
|-----------|---------|-------------------|
| Gateway abstraction? | Per-gateway code / Adapter pattern | **Adapter pattern** — `StripeAdapter`, `RazorpayAdapter` |
| PCI compliance scope? | Store cards / Tokenize only | **Tokenize only** — never store raw card data |
| EMI risk? | Agency bears / Partner bears | **Partner bears** — they're in lending business |
| Invoice generation? | System / External CA | **System** — generate PDF with GST fields |
| Multi-currency? | Store base only / Track both | **Track both** — reporting needs both |
| Settlement tracking? | Yes / No | **YES** — cash flow forecasting critical |

---

## 9. Next Discussion: Notifications & Alerts**

Now that we know HOW money moves, we need to discuss: **WHEN and HOW do we alert people?**

Key questions for next discussion:
1. **SLA alerts** — agent hasn't replied in 4h → alert manager?
2. **Follow-up reminders** — vendor hasn't quoted in 24h → auto-remind?
3. **Payment alerts** — EMI due, invoice overdue, settlement received?
4. **WhatsApp alerts** — push notifications to agents' phones?
5. **Escalation chains** — who gets alerted when SLA breached?
6. **Digest notifications** — daily summary for managers?
7. **Customer notifications** — booking confirmations, payment reminders?

---

**Next file:** `Docs/discussions/notifications_and_alerts_2026-04-29.md`
