# Payment Processing — Reconciliation Deep Dive

> Accounting, settlements, refund handling, and financial reconciliation

---

## Document Overview

**Series:** Payment Processing Deep Dive
**Document:** 4 of 4
**Last Updated:** 2026-04-25
**Status:** ✅ Complete

**Related Documents:**
- [Technical Deep Dive](./PAYMENT_PROCESSING_01_TECHNICAL_DEEP_DIVE.md) — Architecture, gateways
- [UX/UI Deep Dive](./PAYMENT_PROCESSING_02_UX_UI_DEEP_DIVE.md) — Payment flow design
- [Compliance Deep Dive](./PAYMENT_PROCESSING_03_COMPLIANCE_DEEP_DIVE.md) — PCI, data security

---

## Table of Contents

1. [Settlement Process](#settlement-process)
2. [Accounting Integration](#accounting-integration)
3. [Refund Management](#refund-management)
4. [Reconciliation Workflows](#reconciliation-workflows)
5. [Dispute Resolution](#dispute-resolution)
6. [Financial Reporting](#financial-reporting)
7. [Implementation Reference](#implementation-reference)

---

## Settlement Process

### Settlement Lifecycle

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      PAYMENT SETTLEMENT LIFECYCLE                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  DAY 0: PAYMENT                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Customer pays → Gateway → Us → Confirmation sent                   │   │
│  │  Status: COMPLETED                                                  │   │
│  │  Settlement: PENDING                                                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                              │
│                              ▼                                              │
│  DAY 1-2: CAPTURE & BATCHING                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Gateway batches transactions                                      │   │
│  │  Files sent to acquiring bank                                     │   │
│  │  Settlement ID generated                                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                              │
│                              ▼                                              │
│  DAY 2-3: BANK PROCESSING                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Acquiring bank processes batch                                   │   │
│  │  Interbank settlement via NPCI (India)                            │   │
│  │  Funds move from customer bank to gateway                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                              │
│                              ▼                                              │
│  DAY 3-4: GATEWAY SETTLEMENT                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Gateway receives funds                                           │   │
│  │  Settlement webhook sent                                          │   │
│  │  Status: SETTLED                                                  │   │
│  │  Amount: Gross - MDR                                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                              │
│                              ▼                                              │
│  DAY 4-5: PAYOUT TO MERCHANT                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Gateway transfers to our bank account                            │   │
│  │  NEFT/IMPS/RTGS based on amount                                   │   │
│  │  UTR generated                                                     │   │
│  │  Status: PAID_OUT                                                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Settlement Timeline by Gateway

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SETTLEMENT TIMELINE BY GATEWAY                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  RAZORPAY (India)                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  T+0 to T+2: Payment captured                                       │   │
│  │  T+2 to T+3: Settlement to bank account                             │   │
│  │  Daily settlements for high-volume merchants                         │   │
│  │  Same-day settlement available (additional fee)                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  STRIPE (India)                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  T+2 to T+3: Payment captured                                       │   │
│  │  T+3 to T+5: Settlement to bank account                             │   │
│  │  Rolling reserves: 5-10% held for 90 days                          │   │
│  │  Minimum payout: ₹2000                                              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  UPI (Immediate)                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Near-instant settlement                                          │   │
│  │  Funds settle in 30 minutes to 24 hours                           │   │
│  │  No MDR for transactions up to ₹2000 (regulated)                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### MDR (Merchant Discount Rate)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    TYPICAL MDR STRUCTURE (INDIA)                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  CARDS                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Domestic Cards:      1.9% - 2.5%                                  │   │
│  │  International Cards:  3.5% - 4.0%                                  │   │
│  │  Amex:               3.5% (higher)                                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  UPI                                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ≤ ₹2000:            0% (regulated by RBI)                         │   │
│  │  > ₹2000:            ~0.5% - 1.0%                                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  NETBANKING                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Typically:         ₹15 - ₹25 per transaction                       │   │
│  │  Or percentage:      1.0% - 1.5%                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  WALLETS                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Paytm, PhonePe:    1.0% - 2.0%                                   │   │
│  │  Amazon Pay:        1.5% - 2.5%                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ADDITIONAL CHARGES                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  GST on MDR:         18% on transaction fee                         │   │
│  │  Payment gateway fee: ~0.5% additional                             │   │
│  │  Chargeback fee:    ₹15 - ₹25 per instance                         │   │
│  │  Refund fee:        Same as original transaction                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Accounting Integration

### Ledger Structure

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      PAYMENT ACCOUNTING LEDGER                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  CHART OF ACCOUNTS                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ASSETS                                                             │   │
│  │  ├─ Bank Accounts                                                   │   │
│  │  │  ├─ HDFC Business Account (Primary)                             │   │
│  │  │  └─ ICIL Settlement Account                                      │   │
│  │  │                                                                  │   │
│  │  ├─ Payment Gateway Receivables                                     │   │
│  │  │  ├─ Razorpay Receivable                                         │   │
│  │  │  └─ Stripe Receivable                                           │   │
│  │  │                                                                  │   │
│  │  └─ Customer Advances (Unsettled payments)                         │   │
│  │                                                                     │   │
│  │  LIABILITIES                                                        │   │
│  │  ├─ Customer Liability (Unearned revenue)                           │   │
│  │  └─ Refund Payable                                                 │   │
│  │                                                                     │   │
│  │  REVENUE                                                            │   │
│  │  ├─ Gross Booking Revenue                                          │   │
│  │  └─ Commission Revenue                                             │   │
│  │                                                                     │   │
│  │  EXPENSES                                                           │   │
│  │  ├─ Payment Gateway Charges (MDR)                                  │   │
│  │  ├─ Refund Processing Charges                                      │   │
│  │  └─ Chargeback Losses                                              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Journal Entry Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PAYMENT JOURNAL ENTRY FLOW                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. PAYMENT RECEIVED (Day 0)                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Dr. Payment Gateway Receivable    ₹45,000                          │   │
│  │      Cr. Customer Liability          ₹45,000                         │   │
│  │                                                                     │   │
│  │  (Payment received but not settled)                                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  2. SERVICE DELIVERED / BOOKING CONFIRMED                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Dr. Customer Liability          ₹45,000                            │   │
│  │      Cr. Gross Booking Revenue        ₹45,000                       │   │
│  │                                                                     │   │
│  │  (Revenue recognized as service is delivered)                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  3. SETTLEMENT RECEIVED (Day 3)                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Dr. Bank Account (HDFC)          ₹43,650                          │   │
│  │  Dr. Payment Gateway Charges      ₹1,350                           │   │
│  │      Cr. Payment Gateway Receivable    ₹45,000                     │   │
│  │                                                                     │   │
│  │  (Settlement received after deducting MDR of 3%)                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  4. GST REVERSAL ON MDR                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Dr. Input GST Credit          ₹203                               │   │
│  │      Cr. Payment Gateway Charges      ₹203                         │   │
│  │                                                                     │   │
│  │  (18% GST on MDR is available as input credit)                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Accounting Service

```typescript
/**
 * Payment accounting service
 */
class PaymentAccountingService {
  constructor(
    private ledger: GeneralLedger,
    private gatewayService: GatewayService,
    private taxService: TaxService
  ) {}

  /**
   * Record payment received
   */
  async recordPaymentReceived(transaction: Transaction): Promise<JournalEntry> {
    const entry: JournalEntry = {
      id: this.generateEntryId(),
      date: transaction.paidAt!,
      reference: `PAYMENT_${transaction.id}`,
      description: `Payment received for ${transaction.tripId || transaction.invoiceId}`,
      lines: [
        {
          account: `PAYMENT_GATEWAY_RECEIVABLE_${transaction.gateway}`,
          debit: transaction.amount,
          credit: 0
        },
        {
          account: 'CUSTOMER_LIABILITY',
          debit: 0,
          credit: transaction.amount
        }
      ],
      metadata: {
        transactionId: transaction.id,
        gateway: transaction.gateway,
        gatewayPaymentId: transaction.gatewayPaymentId
      }
    };

    await this.ledger.postEntry(entry);
    return entry;
  }

  /**
   * Recognize revenue when booking is confirmed
   */
  async recognizeRevenue(booking: Booking): Promise<JournalEntry> {
    const entry: JournalEntry = {
      id: this.generateEntryIdId(),
      date: booking.confirmedAt,
      reference: `BOOKING_${booking.id}`,
      description: `Revenue recognized for booking ${booking.id}`,
      lines: [
        {
          account: 'CUSTOMER_LIABILITY',
          debit: booking.totalAmount,
          credit: 0
        },
        {
          account: 'GROSS_BOOKING_REVENUE',
          debit: 0,
          credit: booking.totalAmount
        }
      ],
      metadata: {
        bookingId: booking.id,
        tripId: booking.tripId,
        customerId: booking.customerId
      }
    };

    await this.ledger.postEntry(entry);
    return entry;
  }

  /**
   * Record settlement from gateway
   */
  async recordSettlement(settlement: GatewaySettlement): Promise<JournalEntry> {
    // Calculate MDR
    const mdrAmount = settlement.grossAmount - settlement.netAmount;
    const gstOnMDR = await this.taxService.calculateGST(mdrAmount);

    const entry: JournalEntry = {
      id: this.generateEntryId(),
      date: settlement.settlementDate,
      reference: `SETTLEMENT_${settlement.settlementId}`,
      description: `Settlement from ${settlement.gateway} - UTR: ${settlement.utr}`,
      lines: [
        {
          account: 'BANK_HDFC_PRIMARY',
          debit: settlement.netAmount,
          credit: 0
        },
        {
          account: 'PAYMENT_GATEWAY_CHARGES',
          debit: mdrAmount,
          credit: 0
        },
        {
          account: 'INPUT_GST_CREDIT',
          debit: gstOnMDR,
          credit: 0
        },
        {
          account: `PAYMENT_GATEWAY_RECEIVABLE_${settlement.gateway}`,
          debit: 0,
          credit: settlement.grossAmount
        }
      ],
      metadata: {
        settlementId: settlement.settlementId,
        gateway: settlement.gateway,
        utr: settlement.utr,
        transactions: settlement.transactionIds
      }
    };

    await this.ledger.postEntry(entry);

    // Update transaction settlement status
    for (const txnId of settlement.transactionIds) {
      await this.updateTransactionSettlement(txnId, settlement);
    }

    return entry;
  }

  /**
   * Record refund
   */
  async recordRefund(refund: Refund): Promise<JournalEntry> {
    const mdrAmount = refund.amount * 0.03; // Assume 3% MDR
    const gstOnMDR = await this.taxService.calculateGST(mdrAmount);

    const entry: JournalEntry = {
      id: this.generateEntryId(),
      date: refund.processedAt,
      reference: `REFUND_${refund.id}`,
      description: `Refund for transaction ${refund.transactionId}`,
      lines: [
        {
          account: 'REFUND_PAYABLE',
          debit: 0,
          credit: refund.amount
        },
        {
          account: 'GROSS_BOOKING_REVENUE',
          debit: refund.amount,
          credit: 0
        },
        {
          account: 'REFUND_PROCESSING_CHARGES',
          debit: mdrAmount,
          credit: 0
        },
        {
          account: 'INPUT_GST_CREDIT',
          debit: gstOnMDR,
          credit: 0
        }
      ],
      metadata: {
        refundId: refund.id,
        transactionId: refund.transactionId,
        gateway: refund.gateway
      }
    };

    await this.ledger.postEntry(entry);
    return entry;
  }

  /**
   * Generate reconciliation report
   */
  async generateReconciliationReport(
    startDate: Date,
    endDate: Date
  ): Promise<ReconciliationReport> {
    // Get all journal entries in period
    const entries = await this.ledger.getEntriesByDateRange(startDate, endDate);

    // Calculate totals
    const paymentsReceived = entries
      .filter(e => e.reference?.startsWith('PAYMENT_'))
      .reduce((sum, e) => sum + e.lines[0].debit, 0);

    const settlementsReceived = entries
      .filter(e => e.reference?.startsWith('SETTLEMENT_'))
      .reduce((sum, e) => sum + e.lines[0].debit, 0);

    const gatewayCharges = entries
      .filter(e => e.lines.some(l => l.account === 'PAYMENT_GATEWAY_CHARGES'))
      .reduce((sum, e) => sum + e.lines.find(l => l.account === 'PAYMENT_GATEWAY_CHARGES')!.debit, 0);

    const refundsProcessed = entries
      .filter(e => e.reference?.startsWith('REFUND_'))
      .reduce((sum, e) => sum + Math.abs(e.lines[0].credit), 0);

    // Get outstanding receivables
    const outstandingReceivables = await this.getOutstandingReceivables();

    return {
      period: { start: startDate, end: endDate },
      summary: {
        paymentsReceived,
        settlementsReceived,
        pendingSettlements: paymentsReceived - settlementsReceived,
        gatewayCharges,
        refundsProcessed,
        netSettlement: settlementsReceived - refundsProcessed
      },
      outstandingReceivables,
      entries
    };
  }

  private async updateTransactionSettlement(
    transactionId: string,
    settlement: GatewaySettlement
  ): Promise<void> {
    // Update transaction record
  }

  private async getOutstandingReceivables(): Promise<OutstandingReceivable[]> {
    // Get pending settlements
    return [];
  }

  private generateEntryId(): string {
    return `JE_${Date.now()}_${crypto.randomBytes(4).toString('hex')}`;
  }
}

interface JournalEntry {
  id: string;
  date: Date;
  reference: string;
  description: string;
  lines: JournalLine[];
  metadata: Record<string, unknown>;
}

interface JournalLine {
  account: string;
  debit: number;
  credit: number;
}

interface GatewaySettlement {
  settlementId: string;
  gateway: string;
  settlementDate: Date;
  grossAmount: number;
  netAmount: number;
  utr: string;
  transactionIds: string[];
}

interface ReconciliationReport {
  period: { start: Date; end: Date };
  summary: {
    paymentsReceived: number;
    settlementsReceived: number;
    pendingSettlements: number;
    gatewayCharges: number;
    refundsProcessed: number;
    netSettlement: number;
  };
  outstandingReceivables: OutstandingReceivable[];
  entries: JournalEntry[];
}

interface OutstandingReceivable {
  transactionId: string;
  amount: number;
  gateway: string;
  expectedSettlementDate: Date;
  daysOutstanding: number;
}
```

---

## Refund Management

### Refund Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         REFUND PROCESS FLOW                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  REFUND REQUEST                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Agent initiates refund for:                                        │   │
│  │  • Cancellation by customer                                         │   │
│  │  • Service not delivered                                           │   │
│  │  • Overpayment                                                      │   │
│  │  • Chargeback reversal                                              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                              │
│                              ▼                                              │
│  VALIDATION                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  • Original payment exists and is COMPLETED                        │   │
│  │  • Refund amount ≤ original amount                                 │   │
│  │  • Refund window not exceeded (varies by gateway)                  │   │
│  │  • Sufficient balance in refund account                            │   │
│  │  • Approval based on amount (agent vs finance)                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                              │
│                              ▼                                              │
│  REFUND INITIATION                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  • Create refund record with PENDING status                        │   │
│  │  • Call gateway refund API                                          │   │
│  │  • Get refund ID from gateway                                      │   │
│  │  • Update customer and trip status                                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                              │
│                              ▼                                              │
│  GATEWAY PROCESSING                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  • Gateway initiates refund to customer's bank/UPI                 │   │
│  │  • Processing time:                                               │   │
│  │    - UPI: 1-2 business days                                       │   │
│  │    - Card: 5-7 business days                                      │   │
│  │    - Netbanking: 7-10 business days                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                              │
│                              ▼                                              │
│  REFUND COMPLETION                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  • Gateway sends webhook notification                              │   │
│  │  • Update refund status to COMPLETED                               │   │
│  │  • Notify customer via email/SMS                                   │   │
│  │  • Record accounting entries                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Refund Policies

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         REFUND POLICY RULES                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  TIME-BASED REFUND RULES                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Within 24 hours of payment:                                        │   │
│  │  • Full refund                                                      │   │
│  │  • No cancellation charges                                          │   │
│  │  • Automatic approval (agent level)                                 │   │
│  │                                                                     │   │
│  │  Within 7 days of payment:                                         │   │
│  │  • Full refund                                                      │   │
│  │  • May have cancellation fee depending on supplier                  │   │
│  │  • Agent approval (up to ₹50,000)                                  │   │
│  │                                                                     │   │
│  │  7-30 days from payment:                                           │   │
│  │  • Full or partial refund based on supplier terms                  │   │
│  │  • Cancellation fees may apply                                      │   │
│  │  • Finance approval required                                       │   │
│  │                                                                     │   │
│  │  > 30 days from payment:                                            │   │
│  │  • Case-by-case basis                                              │   │
│  │  • Supplier policies apply                                         │   │
│  │  • Management approval required                                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  PARTIAL REFUND RULES                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  • Partial cancellations: Refund only for cancelled portion         │   │
│  │  • Price difference: If rebooking at lower price                    │   │
│  │  • Service downgrade: Refund difference                             │   │
│  │  • Multiple partial refunds allowed up to original amount           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  REFUND METHOD PRIORITY                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  1. Original payment method (same source)                          │   │
│  │  2. Customer bank account (NEFT) if original method unavailable    │   │
│  │  3. Wallet credit (if agreed with customer)                         │   │
│  │  4. Voucher for future use (if agreed)                              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Refund Service

```typescript
/**
 * Refund management service
 */
class RefundService {
  constructor(
    private gatewayFactory: GatewayFactory,
    private transactionStore: TransactionStore,
    private refundStore: RefundStore,
    private accountingService: PaymentAccountingService,
    private notificationService: NotificationService,
    private approvalService: ApprovalService
  ) {}

  /**
   * Initiate refund
   */
  async initiateRefund(
    request: RefundRequest,
    context: RequestContext
  ): Promise<Refund> {
    // Validate original transaction
    const transaction = await this.transactionStore.get(request.transactionId);

    if (!transaction) {
      throw new NotFoundError('Original transaction not found');
    }

    if (transaction.status !== 'COMPLETED') {
      throw new InvalidStateError('Can only refund completed transactions');
    }

    if (transaction.status === 'REFUNDED') {
      throw new InvalidStateError('Transaction already refunded');
    }

    // Validate refund amount
    const totalRefunded = await this.refundStore.getTotalRefunded(request.transactionId);
    const availableForRefund = transaction.amount - totalRefunded;

    if (request.amount > availableForRefund) {
      throw new ValidationError('Refund amount exceeds available balance');
    }

    // Check if approval needed
    const requiresApproval = await this.requiresApproval(
      request,
      transaction,
      context
    );

    if (requiresApproval) {
      // Submit for approval
      const approvalRequest = await this.approvalService.submit({
        type: 'REFUND',
        amount: request.amount,
        transactionId: request.transactionId,
        requestedBy: context.userId,
        reason: request.reason
      });

      // Create pending refund record
      const refund: Refund = {
        id: this.generateRefundId(),
        transactionId: request.transactionId,
        amount: request.amount,
        reason: request.reason,
        status: 'PENDING_APPROVAL',
        approvalRequestId: approvalRequest.id,
        requestedBy: context.userId,
        requestedAt: new Date(),
        gateway: transaction.gateway
      };

      await this.refundStore.create(refund);
      return refund;
    }

    // Auto-approve and process
    return await this.processRefund(request, transaction, context);
  }

  /**
   * Process approved refund
   */
  async processRefund(
    request: RefundRequest,
    transaction: Transaction,
    context: RequestContext
  ): Promise<Refund> {
    // Create refund record
    const refund: Refund = {
      id: this.generateRefundId(),
      transactionId: transaction.id,
      amount: request.amount,
      reason: request.reason,
      status: 'PROCESSING',
      processedBy: context.userId,
      processedAt: new Date(),
      gateway: transaction.gateway
    };

    await this.refundStore.create(refund);

    try {
      // Call gateway refund API
      const gateway = this.gatewayFactory.get(transaction.gateway);
      const gatewayRefund = await gateway.processRefund({
        paymentId: transaction.gatewayPaymentId!,
        amount: request.amount,
        notes: {
          refundId: refund.id,
          reason: request.reason
        }
      });

      // Update refund record
      refund.gatewayRefundId = gatewayRefund.refundId;
      refund.status = this.mapRefundStatus(gatewayRefund.status);
      refund.expectedSettlementDate = this.calculateExpectedSettlement(
        transaction.paymentMethod!,
        new Date()
      );

      await this.refundStore.update(refund);

      // Notify customer
      await this.notificationService.sendRefundInitiated({
        refundId: refund.id,
        amount: refund.amount,
        transactionId: transaction.id,
        expectedDate: refund.expectedSettlementDate
      });

      return refund;

    } catch (error) {
      // Update refund status
      refund.status = 'FAILED';
      refund.error = error instanceof Error ? error.message : 'Unknown error';
      await this.refundStore.update(refund);
      throw error;
    }
  }

  /**
   * Handle refund webhook from gateway
   */
  async handleRefundWebhook(event: RefundWebhookEvent): Promise<void> {
    const refund = await this.refundStore.getByGatewayRefundId(event.refundId);

    if (!refund) {
      logger.error('Refund not found for webhook', { refundId: event.refundId });
      return;
    }

    // Update status
    const oldStatus = refund.status;
    refund.status = this.mapWebhookStatus(event.status);
    refund.completedAt = event.timestamp;

    await this.refundStore.update(refund);

    // If completed, record accounting entries
    if (refund.status === 'COMPLETED' && oldStatus !== 'COMPLETED') {
      await this.accountingService.recordRefund(refund);

      // Notify customer
      await this.notificationService.sendRefundCompleted({
        refundId: refund.id,
        amount: refund.amount,
        transactionId: refund.transactionId
      });
    }

    // If failed, notify support
    if (refund.status === 'FAILED') {
      await this.notificationService.sendRefundFailed({
        refundId: refund.id,
        amount: refund.amount,
        error: event.error
      });
    }
  }

  /**
   * Check if refund requires approval
   */
  private async requiresApproval(
    request: RefundRequest,
    transaction: Transaction,
    context: RequestContext
  ): Promise<boolean> {
    const daysSincePayment = (Date.now() - transaction.paidAt!.getTime()) / (1000 * 60 * 60 * 24);

    // Rules for requiring approval
    const rules = [
      // More than 7 days from payment
      daysSincePayment > 7,

      // Amount exceeds agent limit
      request.amount > this.getAgentRefundLimit(context.userId),

      // Partial refund (not full amount)
      request.amount < transaction.amount,

      // High-value refund
      request.amount > 50000 // ₹50,000
    ];

    return rules.some(rule => rule);
  }

  private getAgentRefundLimit(userId: string): number {
    // Get from user settings
    return 25000; // Default ₹25,000
  }

  private generateRefundId(): string {
    return `REF_${Date.now()}_${crypto.randomBytes(4).toString('hex')}`;
  }

  private mapRefundStatus(status: string): RefundStatus {
    const statusMap: Record<string, RefundStatus> = {
      'pending': 'PROCESSING',
      'processing': 'PROCESSING',
      'processed': 'COMPLETED',
      'failed': 'FAILED',
      'cancelled': 'CANCELLED'
    };
    return statusMap[status] || 'PROCESSING';
  }

  private mapWebhookStatus(status: string): RefundStatus {
    return this.mapRefundStatus(status);
  }

  private calculateExpectedSettlement(method: PaymentMethod, fromDate: Date): Date {
    const days = {
      'upi': 2,
      'card': 7,
      'netbanking': 10,
      'wallet': 3
    };
    return new Date(fromDate.getTime() + (days[method] || 7) * 24 * 60 * 60 * 1000);
  }
}

interface RefundRequest {
  transactionId: string;
  amount: number;
  reason: string;
  notes?: string;
}

interface Refund {
  id: string;
  transactionId: string;
  amount: number;
  reason: string;
  status: RefundStatus;
  gateway: string;
  gatewayRefundId?: string;
  requestedBy?: string;
  requestedAt?: Date;
  processedBy?: string;
  processedAt?: Date;
  completedAt?: Date;
  expectedSettlementDate?: Date;
  approvalRequestId?: string;
  error?: string;
}

type RefundStatus = 'PENDING_APPROVAL' | 'PROCESSING' | 'COMPLETED' | 'FAILED' | 'CANCELLED';

interface RefundWebhookEvent {
  refundId: string;
  status: string;
  timestamp: Date;
  error?: string;
}
```

---

## Reconciliation Workflows

### Daily Reconciliation

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      DAILY RECONCILIATION PROCESS                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  STEP 1: PULL TRANSACTION DATA                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  • Fetch all transactions from our database                        │   │
│  │  • Fetch settlement reports from gateways                          │   │
│  │  • Fetch bank statement for the day                                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                              │
│                              ▼                                              │
│  STEP 2: MATCH TRANSACTIONS TO SETTLEMENTS                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  For each settlement:                                              │   │
│  │  • Match settlement line items to transactions                     │   │
│  │  • Verify amounts (gross - MDR = net)                             │   │
│  │  • Flag any unmatched items                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                              │
│                              ▼                                              │
│  STEP 3: MATCH SETTLEMENTS TO BANK CREDITS                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  For each settlement:                                              │   │
│  │  • Find corresponding bank credit by amount + date                │   │
│  │  • Match UTR if available                                         │   │
│  │  • Flag any unmatched credits                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                              │
│                              ▼                                              │
│  STEP 4: IDENTIFY DISCREPANCIES                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Common discrepancies:                                             │   │
│  │  • Missing settlements                                             │   │
│  │  • Amount mismatches                                               │   │
│  │  • Delayed settlements                                             │   │
│  │  • Unexpected MDR                                                  │   │
│  │  • Chargebacks                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                              │
│                              ▼                                              │
│  STEP 5: GENERATE REPORT                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  • Daily reconciliation report                                     │   │
│  │  • Summary of matched and unmatched items                          │   │
│  │  • Action items for discrepancies                                  │   │
│  │  • Send to finance team                                            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Reconciliation Engine

```typescript
/**
 * Payment reconciliation engine
 */
class PaymentReconciliationEngine {
  constructor(
    private transactionStore: TransactionStore,
    private gatewayService: GatewayService,
    private bankService: BankService,
    private alertService: AlertService
  ) {}

  /**
   * Run daily reconciliation
   */
  async runDailyReconciliation(date: Date = new Date()): Promise<ReconciliationResult> {
    const startOfDay = new Date(date.setHours(0, 0, 0, 0));
    const endOfDay = new Date(date.setHours(23, 59, 59, 999));

    // Step 1: Get data
    const transactions = await this.transactionStore.findByDateRange(startOfDay, endOfDay);
    const settlements = await this.gatewayService.getSettlements(startOfDay, endOfDay);
    const bankCredits = await this.bankService.getCredits(startOfDay, endOfDay);

    // Step 2: Match transactions to settlements
    const settlementMatch = await this.matchSettlementsToTransactions(settlements, transactions);

    // Step 3: Match settlements to bank
    const bankMatch = await this.matchSettlementsToBank(settlements, bankCredits);

    // Step 4: Identify discrepancies
    const discrepancies = this.identifyDiscrepancies(
      transactions,
      settlements,
      bankCredits,
      settlementMatch,
      bankMatch
    );

    // Step 5: Generate report
    const report: ReconciliationResult = {
      date,
      summary: {
        totalTransactions: transactions.length,
        totalSettlements: settlements.length,
        totalBankCredits: bankCredits.length,
        matchedTransactions: settlementMatch.matched,
        unmatchedTransactions: settlementMatch.unmatched.length,
        matchedSettlements: bankMatch.matched,
        unmatchedSettlements: bankMatch.unmatched.length,
        totalDiscrepancies: discrepancies.length
      },
      discrepancies,
      details: {
        unmatchedTransactions: settlementMatch.unmatched,
        unmatchedSettlements: bankMatch.unmatched,
        unmatchedBankCredits: bankMatch.unmatchedBankCredits
      }
    };

    // Alert if discrepancies found
    if (discrepancies.length > 0) {
      await this.alertService.send({
        type: 'RECONCILIATION_DISCREPANCY',
        date,
        discrepancyCount: discrepancies.length,
        discrepancies: discrepancies.slice(0, 10) // First 10
      });
    }

    return report;
  }

  /**
   * Match settlements to transactions
   */
  private async matchSettlementsToTransactions(
    settlements: GatewaySettlement[],
    transactions: Transaction[]
  ): Promise<SettlementMatchResult> {
    let matched = 0;
    const unmatched: Transaction[] = [];
    const matchedMap = new Map<string, SettlementMatch>();

    // Build transaction map
    const txnMap = new Map<string, Transaction>();
    for (const txn of transactions) {
      if (txn.gatewayPaymentId) {
        txnMap.set(txn.gatewayPaymentId, txn);
      }
    }

    // Match settlement line items to transactions
    for (const settlement of settlements) {
      for (const lineItem of settlement.lineItems) {
        const transaction = txnMap.get(lineItem.paymentId);

        if (transaction) {
          // Verify amount
          const expectedAmount = transaction.amount;
          const actualAmount = lineItem.grossAmount;

          if (Math.abs(expectedAmount - actualAmount) < 1) { // Allow 1 rupee difference
            matchedMap.set(transaction.id, {
              transaction,
              settlement,
              lineItem
            });
            matched++;
          } else {
            unmatched.push(transaction);
          }
        }
      }
    }

    // Find unmatched transactions
    for (const txn of transactions) {
      if (!matchedMap.has(txn.id)) {
        unmatched.push(txn);
      }
    }

    return { matched, unmatched, matchedMap };
  }

  /**
   * Match settlements to bank credits
   */
  private async matchSettlementsToBank(
    settlements: GatewaySettlement[],
    bankCredits: BankCredit[]
  ): Promise<BankMatchResult> {
    let matched = 0;
    const unmatched: GatewaySettlement[] = [];
    const unmatchedBankCredits: BankCredit[] = [];
    const usedBankCredits = new Set<string>();

    for (const settlement of settlements) {
      // Try to match by UTR
      let matchedCredit = bankCredits.find(
        c => c.utr === settlement.utr && !usedBankCredits.has(c.id)
      );

      // If no UTR match, try by amount + date
      if (!matchedCredit) {
        matchedCredit = bankCredits.find(
          c =>
            Math.abs(c.amount - settlement.netAmount) < 1 &&
            c.creditDate >= settlement.settlementDate &&
            c.creditDate <= new Date(settlement.settlementDate.getTime() + 2 * 24 * 60 * 60 * 1000) &&
            !usedBankCredits.has(c.id)
        );
      }

      if (matchedCredit) {
        matched++;
        usedBankCredits.add(matchedCredit.id);
      } else {
        unmatched.push(settlement);
      }
    }

    // Find unmatched bank credits
    for (const credit of bankCredits) {
      if (!usedBankCredits.has(credit.id)) {
        unmatchedBankCredits.push(credit);
      }
    }

    return { matched, unmatched, unmatchedBankCredits };
  }

  /**
   * Identify discrepancies
   */
  private identifyDiscrepancies(
    transactions: Transaction[],
    settlements: GatewaySettlement[],
    bankCredits: BankCredit[],
    settlementMatch: SettlementMatchResult,
    bankMatch: BankMatchResult
  ): Discrepancy[] {
    const discrepancies: Discrepancy[] = [];

    // Unmatched transactions (paid but not settled)
    for (const txn of settlementMatch.unmatched) {
      const daysSincePayment = (Date.now() - txn.paidAt!.getTime()) / (1000 * 60 * 60 * 24);

      if (daysSincePayment > 5) {
        discrepancies.push({
          type: 'MISSING_SETTLEMENT',
          severity: daysSincePayment > 10 ? 'HIGH' : 'MEDIUM',
          description: `Transaction ${txn.id} not settled after ${Math.floor(daysSincePayment)} days`,
          transactionId: txn.id,
          amount: txn.amount
        });
      }
    }

    // Unmatched settlements (settled but not in bank)
    for (const settlement of bankMatch.unmatched) {
      const daysSinceSettlement = (Date.now() - settlement.settlementDate.getTime()) / (1000 * 60 * 60 * 24);

      if (daysSinceSettlement > 3) {
        discrepancies.push({
          type: 'MISSING_BANK_CREDIT',
          severity: daysSinceSettlement > 7 ? 'HIGH' : 'MEDIUM',
          description: `Settlement ${settlement.settlementId} not received in bank after ${Math.floor(daysSinceSettlement)} days`,
          settlementId: settlement.settlementId,
          amount: settlement.netAmount
        });
      }
    }

    // Unmatched bank credits (money received without settlement record)
    for (const credit of bankMatch.unmatchedBankCredits) {
      discrepancies.push({
        type: 'UNRECONCILED_BANK_CREDIT',
        severity: 'MEDIUM',
        description: `Bank credit ${credit.id} has no matching settlement`,
        bankCreditId: credit.id,
        amount: credit.amount
      });
    }

    return discrepancies;
  }
}

interface ReconciliationResult {
  date: Date;
  summary: {
    totalTransactions: number;
    totalSettlements: number;
    totalBankCredits: number;
    matchedTransactions: number;
    unmatchedTransactions: number;
    matchedSettlements: number;
    unmatchedSettlements: number;
    totalDiscrepancies: number;
  };
  discrepancies: Discrepancy[];
  details: {
    unmatchedTransactions: Transaction[];
    unmatchedSettlements: GatewaySettlement[];
    unmatchedBankCredits: BankCredit[];
  };
}

interface SettlementMatchResult {
  matched: number;
  unmatched: Transaction[];
  matchedMap: Map<string, SettlementMatch>;
}

interface BankMatchResult {
  matched: number;
  unmatched: GatewaySettlement[];
  unmatchedBankCredits: BankCredit[];
}

interface SettlementMatch {
  transaction: Transaction;
  settlement: GatewaySettlement;
  lineItem: SettlementLineItem;
}

interface Discrepancy {
  type: 'MISSING_SETTLEMENT' | 'MISSING_BANK_CREDIT' | 'UNRECONCILED_BANK_CREDIT' | 'AMOUNT_MISMATCH';
  severity: 'LOW' | 'MEDIUM' | 'HIGH';
  description: string;
  transactionId?: string;
  settlementId?: string;
  bankCreditId?: string;
  amount: number;
}
```

---

## Dispute Resolution

### Chargeback Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      CHARGEBACK PROCESS FLOW                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  DAY 0: CHARGEBACK INITIATED                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Customer's bank initiates chargeback                              │   │
│  │  We receive notification from gateway                             │   │
│  │  Amount debited from our account                                  │   │
│  │  Status: CHARGEBACK_INITIATED                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                              │
│                              ▼                                              │
│  DAY 1-7: PREPARATION PERIOD                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  • Gather evidence (receipts, communications, delivery proof)      │   │
│  │  • Review transaction details                                       │   │
│  │  • Prepare response document                                       │   │
│  │  • Contact customer if appropriate                                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                              │
│                              ▼                                              │
│  DAY 7-10: SUBMIT RESPONSE                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  • Submit evidence to gateway                                      │   │
│  │  • Gateway forwards to acquiring bank                              │   │
│  │  • Status: CHARGEBACK_UNDER_REVIEW                                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                              │
│                              ▼                                              │
│  DAY 30-45: BANK DECISION                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  WIN:                                                             │   │
│  │  • Chargeback reversed                                            │   │
│  │  • Amount credited back to our account                            │   │
│  │  • Status: CHARGEBACK_WON                                         │   │
│  │                                                                    │   │
│  │  LOSS:                                                            │   │
│  │  • Chargeback upheld                                             │   │
│  │  • Amount remains with customer                                   │   │
│  │  • Status: CHARGEBACK_LOST                                        │   │
│  │  • Can appeal (pre-arbitration)                                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Chargeback Management

```typescript
/**
 * Chargeback management service
 */
class ChargebackService {
  constructor(
    private gatewayFactory: GatewayFactory,
    private chargebackStore: ChargebackStore,
    private evidenceService: EvidenceService,
    private notificationService: NotificationService
  ) {}

  /**
   * Handle chargeback notification from gateway
   */
  async handleChargebackNotification(
    event: ChargebackWebhookEvent
  ): Promise<void> {
    // Get original transaction
    const transaction = await this.getTransactionByGatewayId(event.paymentId);

    if (!transaction) {
      logger.error('Transaction not found for chargeback', { paymentId: event.paymentId });
      return;
    }

    // Create chargeback record
    const chargeback: Chargeback = {
      id: this.generateChargebackId(),
      transactionId: transaction.id,
      gateway: event.gateway,
      gatewayChargebackId: event.chargebackId,
      amount: event.amount,
      currency: event.currency,
      reason: event.reason,
      reasonCode: event.reasonCode,
      status: 'INITIATED',
      initiatedAt: event.timestamp,
      deadline: this.calculateDeadline(event.timestamp, event.gateway),
      evidence: []
    };

    await this.chargebackStore.create(chargeback);

    // Notify finance team
    await this.notificationService.sendChargebackAlert({
      chargebackId: chargeback.id,
      transactionId: transaction.id,
      amount: chargeback.amount,
      reason: chargeback.reason,
      deadline: chargeback.deadline
    });
  }

  /**
   * Gather evidence for chargeback defense
   */
  async gatherEvidence(chargebackId: string): Promise<EvidencePackage> {
    const chargeback = await this.chargebackStore.get(chargebackId);

    if (!chargeback) {
      throw new NotFoundError('Chargeback not found');
    }

    // Get transaction details
    const transaction = await this.getTransaction(chargeback.transactionId);

    // Gather evidence based on reason
    const evidence = await this.evidenceService.gather({
      chargebackId,
      transaction,
      reason: chargeback.reason,
      reasonCode: chargeback.reasonCode
    });

    // Update chargeback
    chargeback.evidence = evidence.documents;
    chargeback.status = 'EVIDENCE_GATHERED';

    await this.chargebackStore.update(chargeback);

    return {
      chargebackId,
      evidence,
      deadline: chargeback.deadline,
      canSubmit: true
    };
  }

  /**
   * Submit chargeback response
   */
  async submitResponse(
    chargebackId: string,
    evidence: EvidenceDocument[],
    notes: string
  ): Promise<void> {
    const chargeback = await this.chargebackStore.get(chargebackId);

    if (!chargeback) {
      throw new NotFoundError('Chargeback not found');
    }

    if (chargeback.status !== 'EVIDENCE_GATHERED' && chargeback.status !== 'INITIATED') {
      throw new InvalidStateError('Cannot submit response for this chargeback');
    }

    // Check deadline
    if (new Date() > chargeback.deadline) {
      throw new ValidationError('Chargeback deadline has passed');
    }

    // Submit to gateway
    const gateway = this.gatewayFactory.get(chargeback.gateway);
    await gateway.submitChargebackResponse({
      chargebackId: chargeback.gatewayChargebackId,
      evidence,
      notes
    });

    // Update chargeback
    chargeback.status = 'UNDER_REVIEW';
    chargeback.submittedAt = new Date();
    chargeback.evidence = evidence;

    await this.chargebackStore.update(chargeback);
  }

  /**
   * Handle chargeback resolution
   */
  async handleResolution(event: ChargebackResolutionEvent): Promise<void> {
    const chargeback = await this.chargebackStore.getByGatewayId(event.chargebackId);

    if (!chargeback) {
      logger.error('Chargeback not found for resolution', { chargebackId: event.chargebackId });
      return;
    }

    chargeback.status = event.won ? 'WON' : 'LOST';
    chargeback.resolvedAt = event.timestamp;

    await this.chargebackStore.update(chargeback);

    if (event.won) {
      // Notify team of win
      await this.notificationService.sendChargebackWon({
        chargebackId: chargeback.id,
        amount: chargeback.amount
      });
    } else {
      // Notify team of loss
      await this.notificationService.sendChargebackLost({
        chargebackId: chargeback.id,
        amount: chargeback.amount,
        canAppeal: event.canAppeal
      });
    }
  }

  private calculateDeadline(initiatedAt: Date, gateway: string): Date {
    // Typically 7-10 days from initiation
    const days = gateway === 'STRIPE' ? 7 : 10;
    return new Date(initiatedAt.getTime() + days * 24 * 60 * 60 * 1000);
  }

  private generateChargebackId(): string {
    return `CB_${Date.now()}_${crypto.randomBytes(4).toString('hex')}`;
  }

  private async getTransactionByGatewayId(gatewayPaymentId: string): Promise<Transaction | null> {
    // Implementation
    throw new Error('Not implemented');
  }

  private async getTransaction(transactionId: string): Promise<Transaction> {
    // Implementation
    throw new Error('Not implemented');
  }
}

interface Chargeback {
  id: string;
  transactionId: string;
  gateway: string;
  gatewayChargebackId: string;
  amount: number;
  currency: string;
  reason: string;
  reasonCode: string;
  status: ChargebackStatus;
  initiatedAt: Date;
  deadline: Date;
  submittedAt?: Date;
  resolvedAt?: Date;
  evidence: EvidenceDocument[];
}

type ChargebackStatus =
  | 'INITIATED'
  | 'EVIDENCE_GATHERED'
  | 'UNDER_REVIEW'
  | 'WON'
  | 'LOST'
  | 'UNDER_APPEAL';

interface EvidencePackage {
  chargebackId: string;
  evidence: EvidenceDocument[];
  deadline: Date;
  canSubmit: boolean;
}

interface EvidenceDocument {
  type: 'RECEIPT' | 'COMMUNICATION' | 'DELIVERY_PROOF' | 'TERMS' | 'OTHER';
  url: string;
  description: string;
}
```

---

## Financial Reporting

### Payment Analytics

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      PAYMENT ANALYTICS DASHBOARD                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────┐  ┌─────────────────────────┐                  │
│  │  PAYMENT OVERVIEW       │  │  GATEWAY BREAKDOWN      │                  │
│  │  ─────────────────────  │  │  ─────────────────────  │                  │
│  │  Total Volume:  ₹2.5Cr  │  │  Razorpay:  65%        │                  │
│  │  Transactions:  1,234   │  │  Stripe:     25%        │                  │
│  │  Success Rate:  98.5%  │  │  UPI:        10%        │                  │
│  │  Avg Ticket:    ₹20,250│  │                         │                  │
│  └─────────────────────────┘  └─────────────────────────┘                  │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  PAYMENT METHOD DISTRIBUTION                                       │    │
│  │  ─────────────────────────────────────────────────────────────────  │    │
│  │  UPI          ████████████████ 45%                                 │    │
│  │  Card         ██████████ 30%                                       │    │
│  │  Netbanking   ███ 12%                                              │    │
│  │  Wallet       ██ 8%                                                │    │
│  │  Other        █ 5%                                                 │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  ┌─────────────────────────┐  ┌─────────────────────────┐                  │
│  │  SETTLEMENT STATUS       │  │  REFUND SUMMARY         │                  │
│  │  ─────────────────────  │  │  ─────────────────────  │                  │
│  │  Pending:     ₹5.2L     │  │  This Month:  ₹45,000   │                  │
│  │  In Transit:  ₹2.1L     │  │  Refund Rate:  1.8%     │                  │
│  │  Settled:     ₹2.43Cr   │  │  Avg Processing: 4 days │                  │
│  └─────────────────────────┘  └─────────────────────────┘                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Reporting Service

```typescript
/**
 * Payment reporting service
 */
class PaymentReportingService {
  constructor(
    private transactionStore: TransactionStore,
    private settlementStore: SettlementStore,
    private refundStore: RefundStore
  ) {}

  /**
   * Generate payment summary report
   */
  async generatePaymentSummary(
    startDate: Date,
    endDate: Date,
    agencyId?: string
  ): Promise<PaymentSummaryReport> {
    const transactions = await this.transactionStore.findByDateRange(
      startDate,
      endDate,
      agencyId
    );

    const summary = {
      period: { start: startDate, end: endDate },
      overview: this.calculateOverview(transactions),
      byGateway: this.groupByGateway(transactions),
      byPaymentMethod: this.groupByPaymentMethod(transactions),
      byStatus: this.groupByStatus(transactions),
      dailyBreakdown: this.calculateDailyBreakdown(transactions, startDate, endDate)
    };

    return summary;
  }

  /**
   * Generate settlement report
   */
  async generateSettlementReport(
    startDate: Date,
    endDate: Date,
    agencyId?: string
  ): Promise<SettlementReport> {
    const settlements = await this.settlementStore.findByDateRange(
      startDate,
      endDate,
      agencyId
    );

    const transactions = await this.transactionStore.findByDateRange(
      startDate,
      endDate,
      agencyId
    );

    return {
      period: { start: startDate, end: endDate },
      totalSettled: settlements.reduce((sum, s) => sum + s.netAmount, 0),
      totalMDR: settlements.reduce((sum, s) => sum + (s.grossAmount - s.netAmount), 0),
      pendingSettlement: transactions
        .filter(t => t.status === 'COMPLETED')
        .reduce((sum, t) => sum + t.amount, 0) -
        settlements.reduce((sum, s) => sum + s.grossAmount, 0),
      settlements: settlements.map(s => ({
        settlementId: s.settlementId,
        gateway: s.gateway,
        settlementDate: s.settlementDate,
        grossAmount: s.grossAmount,
        netAmount: s.netAmount,
        mdr: s.grossAmount - s.netAmount,
        transactionCount: s.transactionIds.length
      }))
    };
  }

  /**
   * Generate refund report
   */
  async generateRefundReport(
    startDate: Date,
    endDate: Date,
    agencyId?: string
  ): Promise<RefundReport> {
    const refunds = await this.refundStore.findByDateRange(
      startDate,
      endDate,
      agencyId
    );

    return {
      period: { start: startDate, end: endDate },
      totalRefunds: refunds.reduce((sum, r) => sum + r.amount, 0),
      refundCount: refunds.length,
      refundRate: refunds.length / await this.getTotalTransactions(startDate, endDate, agencyId),
      byReason: this.groupRefundsByReason(refunds),
      byGateway: this.groupRefundsByGateway(refunds),
      byStatus: this.groupRefundsByStatus(refunds),
      averageProcessingTime: this.calculateAvgProcessingTime(refunds)
    };
  }

  /**
   * Export report to Excel/CSV
   */
  async exportReport(
    reportType: 'PAYMENT' | 'SETTLEMENT' | 'REFUND',
    params: ReportParams,
    format: 'EXCEL' | 'CSV'
  ): Promise<Buffer> {
    let data: unknown[];

    switch (reportType) {
      case 'PAYMENT':
        data = await this.generatePaymentSummary(params.startDate, params.endDate, params.agencyId);
        break;
      case 'SETTLEMENT':
        data = await this.generateSettlementReport(params.startDate, params.endDate, params.agencyId);
        break;
      case 'REFUND':
        data = await this.generateRefundReport(params.startDate, params.endDate, params.agencyId);
        break;
    }

    if (format === 'EXCEL') {
      return await this.exportToExcel(data, reportType);
    } else {
      return await this.exportToCSV(data, reportType);
    }
  }

  private calculateOverview(transactions: Transaction[]): PaymentOverview {
    const completed = transactions.filter(t => t.status === 'COMPLETED');
    const failed = transactions.filter(t => t.status === 'FAILED');

    return {
      totalVolume: completed.reduce((sum, t) => sum + t.amount, 0),
      transactionCount: completed.length,
      successRate: completed.length / transactions.length,
      averageTicket: completed.length > 0
        ? completed.reduce((sum, t) => sum + t.amount, 0) / completed.length
        : 0,
      failureCount: failed.length,
      failureRate: failed.length / transactions.length
    };
  }

  private groupByGateway(transactions: Transaction[]): Record<string, PaymentStats> {
    const grouped = new Map<string, Transaction[]>();

    for (const txn of transactions) {
      const existing = grouped.get(txn.gateway) || [];
      existing.push(txn);
      grouped.set(txn.gateway, existing);
    }

    const result: Record<string, PaymentStats> = {};

    for (const [gateway, txns] of grouped) {
      const completed = txns.filter(t => t.status === 'COMPLETED');
      result[gateway] = {
        count: completed.length,
        amount: completed.reduce((sum, t) => sum + t.amount, 0),
        percentage: 0 // Will calculate
      };
    }

    // Calculate percentages
    const total = Object.values(result).reduce((sum, s) => sum + s.amount, 0);
    for (const stats of Object.values(result)) {
      stats.percentage = (stats.amount / total) * 100;
    }

    return result;
  }

  private groupByPaymentMethod(transactions: Transaction[]): Record<string, PaymentStats> {
    const grouped = new Map<string, Transaction[]>();

    for (const txn of transactions) {
      const method = txn.paymentMethod || 'unknown';
      const existing = grouped.get(method) || [];
      existing.push(txn);
      grouped.set(method, existing);
    }

    const result: Record<string, PaymentStats> = {};

    for (const [method, txns] of grouped) {
      const completed = txns.filter(t => t.status === 'COMPLETED');
      result[method] = {
        count: completed.length,
        amount: completed.reduce((sum, t) => sum + t.amount, 0),
        percentage: 0
      };
    }

    const total = Object.values(result).reduce((sum, s) => sum + s.amount, 0);
    for (const stats of Object.values(result)) {
      stats.percentage = (stats.amount / total) * 100;
    }

    return result;
  }

  private async exportToExcel(data: unknown, reportType: string): Promise<Buffer> {
    // Use ExcelJS or similar
    throw new Error('Not implemented');
  }

  private async exportToCSV(data: unknown, reportType: string): Promise<Buffer> {
    // Convert to CSV
    throw new Error('Not implemented');
  }

  private async getTotalTransactions(startDate: Date, endDate: Date, agencyId?: string): Promise<number> {
    return (await this.transactionStore.findByDateRange(startDate, endDate, agencyId)).length;
  }

  private groupByStatus(transactions: Transaction[]): Record<string, number> {
    return transactions.reduce((acc, txn) => {
      acc[txn.status] = (acc[txn.status] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
  }

  private calculateDailyBreakdown(
    transactions: Transaction[],
    startDate: Date,
    endDate: Date
  ): DailyBreakdown[] {
    // Implementation
    return [];
  }

  private groupRefundsByReason(refunds: Refund[]): Record<string, number> {
    return refunds.reduce((acc, refund) => {
      acc[refund.reason] = (acc[refund.reason] || 0) + refund.amount;
      return acc;
    }, {} as Record<string, number>);
  }

  private groupRefundsByGateway(refunds: Refund[]): Record<string, number> {
    return refunds.reduce((acc, refund) => {
      acc[refund.gateway] = (acc[refund.gateway] || 0) + refund.amount;
      return acc;
    }, {} as Record<string, number>);
  }

  private groupRefundsByStatus(refunds: Refund[]): Record<string, number> {
    return refunds.reduce((acc, refund) => {
      acc[refund.status] = (acc[refund.status] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
  }

  private calculateAvgProcessingTime(refunds: Refund[]): number {
    const completed = refunds.filter(r => r.completedAt && r.processedAt);

    if (completed.length === 0) return 0;

    const totalDays = completed.reduce((sum, r) => {
      return sum + (r.completedAt!.getTime() - r.processedAt!.getTime()) / (1000 * 60 * 60 * 24);
    }, 0);

    return totalDays / completed.length;
  }
}

interface PaymentSummaryReport {
  period: { start: Date; end: Date };
  overview: PaymentOverview;
  byGateway: Record<string, PaymentStats>;
  byPaymentMethod: Record<string, PaymentStats>;
  byStatus: Record<string, number>;
  dailyBreakdown: DailyBreakdown[];
}

interface SettlementReport {
  period: { start: Date; end: Date };
  totalSettled: number;
  totalMDR: number;
  pendingSettlement: number;
  settlements: SettlementSummary[];
}

interface RefundReport {
  period: { start: Date; end: Date };
  totalRefunds: number;
  refundCount: number;
  refundRate: number;
  byReason: Record<string, number>;
  byGateway: Record<string, number>;
  byStatus: Record<string, number>;
  averageProcessingTime: number;
}

interface PaymentOverview {
  totalVolume: number;
  transactionCount: number;
  successRate: number;
  averageTicket: number;
  failureCount: number;
  failureRate: number;
}

interface PaymentStats {
  count: number;
  amount: number;
  percentage: number;
}

interface DailyBreakdown {
  date: Date;
  amount: number;
  count: number;
}

interface SettlementSummary {
  settlementId: string;
  gateway: string;
  settlementDate: Date;
  grossAmount: number;
  netAmount: number;
  mdr: number;
  transactionCount: number;
}

interface ReportParams {
  startDate: Date;
  endDate: Date;
  agencyId?: string;
}
```

---

## Summary

This document covers financial reconciliation for payment processing:

1. **Settlement Process** — Settlement lifecycle, timeline by gateway, MDR structure
2. **Accounting Integration** — Ledger structure, journal entries, accounting service
3. **Refund Management** — Refund flow, policies, approval workflow
4. **Reconciliation Workflows** — Daily reconciliation, matching engine, discrepancy handling
5. **Dispute Resolution** — Chargeback flow, evidence gathering, resolution
6. **Financial Reporting** — Analytics dashboard, reporting service, exports

**Key Takeaways:**

- Settlements typically take T+2 to T+5 days depending on gateway
- MDR varies by payment method (0% for UPI ≤₹2000, 2-4% for cards)
- Reconciliation should run daily to catch discrepancies early
- Refunds have time-based policies and approval workflows
- Chargebacks require timely response (7-10 days)
- Comprehensive reporting enables financial visibility

**Related Documents:**
- [Technical Deep Dive](./PAYMENT_PROCESSING_01_TECHNICAL_DEEP_DIVE.md) — Backend architecture
- [Compliance Deep Dive](./PAYMENT_PROCESSING_03_COMPLIANCE_DEEP_DIVE.md) — PCI compliance

---

**End of Payment Processing Deep Dive Series**
