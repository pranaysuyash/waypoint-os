# Payment Processing — Technical Deep Dive

> Payment architecture, gateway integrations, and transaction management

---

## Document Overview

**Series:** Payment Processing Deep Dive
**Document:** 1 of 4
**Last Updated:** 2026-04-25
**Status:** ✅ Complete

**Related Documents:**
- [UX/UI Deep Dive](./PAYMENT_PROCESSING_02_UX_UI_DEEP_DIVE.md) — Payment flow design
- [Compliance Deep Dive](./PAYMENT_PROCESSING_03_COMPLIANCE_DEEP_DIVE.md) — PCI, RBI regulations
- [Reconciliation Deep Dive](./PAYMENT_PROCESSING_04_RECONCILIATION_DEEP_DIVE.md) — Accounting, settlements

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Payment Gateway Integration](#payment-gateway-integration)
3. [Payment Link System](#payment-link-system)
4. [Transaction State Management](#transaction-state-management)
5. [Webhook Handling](#webhook-handling)
6. [Idempotency & Safety](#idempotency--safety)
7. [API Reference](#api-reference)

---

## Architecture Overview

### System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PAYMENT PROCESSING ARCHITECTURE                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌───────────────┐                                                           │
│  │   Frontend    │                                                           │
│  │   (Workspace) │                                                           │
│  └───────┬───────┘                                                           │
│          │                                                                   │
│          ▼                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         API GATEWAY                                 │    │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐      │    │
│  │  │ Payment Links   │  │ Payment Status  │  │ Refunds         │      │    │
│  │  │   API           │  │   API           │  │   API           │      │    │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│          │                                                                   │
│          ▼                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                      PAYMENT SERVICE                                │    │
│  │  ┌──────────────────────────────────────────────────────────────┐  │    │
│  │  │                   Transaction Manager                         │  │    │
│  │  │  • State machine                                              │  │    │
│  │  │  • Idempotency tracking                                       │  │    │
│  │  │  • Lock management                                            │  │    │
│  │  └──────────────────────────────────────────────────────────────┘  │    │
│  │                                                                       │    │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐      │    │
│  │  │  Razorpay       │  │   Stripe        │  │   UPI           │      │    │
│  │  │  Adapter        │  │   Adapter       │  │   Adapter       │      │    │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│          │                                                                   │
│          ▼                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    EXTERNAL GATEWAYS                                 │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                  │    │
│  │  │  Razorpay   │  │   Stripe    │  │    UPI      │                  │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    SUPPORTING SERVICES                              │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                  │    │
│  │  │   Redis     │  │ PostgreSQL  │  │   S3        │                  │    │
│  │  │  (Locks)    │  │ (Txn Store) │  │ (Exports)   │                  │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Data Flow: Payment Link Creation

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     PAYMENT LINK CREATION FLOW                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Agent Workspace ──► POST /api/payments/link                                │
│                             │                                               │
│                             ▼                                               │
│                    ┌──────────────────┐                                     │
│                    │ Validate Request │                                     │
│                    │ • Amount          │                                     │
│                    │ • Trip exists     │                                     │
│                    │ • Permissions     │                                     │
│                    └────────┬─────────┘                                     │
│                             │                                               │
│                             ▼                                               │
│                    ┌──────────────────┐                                     │
│                    │ Generate Link    │                                     │
│                    │ • Unique ID      │                                     │
│                    │ • Idempotency Key│                                     │
│                    │ • Expiry Time    │                                     │
│                    └────────┬─────────┘                                     │
│                             │                                               │
│                             ▼                                               │
│                    ┌──────────────────┐                                     │
│                    │ Create Txn Record│                                     │
│                    │ • Status: PENDING│                                     │
│                    │ • Metadata       │                                     │
│                    └────────┬─────────┘                                     │
│                             │                                               │
│                             ▼                                               │
│                    ┌──────────────────┐                                     │
│                    │ Call Gateway     │                                     │
│                    │ Create Link API  │                                     │
│                    └────────┬─────────┘                                     │
│                             │                                               │
│                             ▼                                               │
│                    ┌──────────────────┐                                     │
│                    │ Return Link URL  │                                     │
│                    │ + QR Code        │                                     │
│                    └──────────────────┘                                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Data Flow: Payment Completion

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     PAYMENT COMPLETION FLOW (Webhook)                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Gateway ──► POST /api/webhooks/payment                                     │
│                   │                                                         │
│                   ▼                                                         │
│          ┌─────────────────────┐                                            │
│          │ Verify Signature    │                                            │
│          │ (HMAC validation)   │                                            │
│          └──────────┬──────────┘                                            │
│                   │                                                         │
│                   ▼                                                         │
│          ┌─────────────────────┐                                            │
│          │ Parse Event Type    │                                            │
│          │ • payment.captured  │                                            │
│          │ • payment.failed    │                                            │
│          │ • refund.processed  │                                            │
│          └──────────┬──────────┘                                            │
│                   │                                                         │
│                   ▼                                                         │
│          ┌─────────────────────┐                                            │
│          │ Acquire Lock        │                                            │
│          │ (idempotency key)   │                                            │
│          └──────────┬──────────┘                                            │
│                   │                                                         │
│                   ▼                                                         │
│          ┌─────────────────────┐                                            │
│          │ Process Event       │                                            │
│          │ • Update status     │                                            │
│          │ • Trigger booking   │                                            │
│          │ • Send notifications │                                            │
│          └──────────┬──────────┘                                            │
│                   │                                                         │
│                   ▼                                                         │
│          ┌─────────────────────┐                                            │
│          │ Release Lock        │                                            │
│          │ Return 200 OK       │                                            │
│          └─────────────────────┘                                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Payment Gateway Integration

### Supported Gateways

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SUPPORTED PAYMENT GATEWAYS                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │   RAZORPAY      │  │    STRIPE       │  │      UPI        │             │
│  │                 │  │                 │  │                 │             │
│  │ • Cards         │  │ • Cards         │  │ • UPI ID        │             │
│  │ • UPI           │  │ • UPI (via PI)  │  │ • QR Code       │             │
│  │ • Netbanking    │  │ • Netbanking    │  │                 │             │
│  │ • Wallets       │  │ • Wallets       │  │                 │             │
│  │ • EMI           │  │                │  │                 │             │
│  │                 │  │                │  │                 │             │
│  │ India-focused   │  │ Global          │  │ India-native    │             │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘             │
│                                                                             │
│  Gateway Selection Strategy:                                                │
│  • Default: Razorpay (India), Stripe (International)                        │
│  • Fallback: Automatic failover if primary down                            │
│  • Customer preference: Saved from previous transactions                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Gateway Adapter Interface

```typescript
/**
 * Base interface for payment gateway adapters
 */
interface PaymentGatewayAdapter {
  /**
   * Gateway identifier
   */
  readonly gatewayId: string;

  /**
   * Create a payment link
   */
  createPaymentLink(request: PaymentLinkRequest): Promise<PaymentLinkResponse>;

  /**
   * Get payment status
   */
  getPaymentStatus(paymentId: string): Promise<PaymentStatus>;

  /**
   * Process a refund
   */
  processRefund(request: RefundRequest): Promise<RefundResponse>;

  /**
   * Verify webhook signature
   */
  verifyWebhookSignature(
    payload: string,
    signature: string,
    secret: string
  ): boolean;

  /**
   * Parse webhook event
   */
  parseWebhookEvent(payload: unknown): PaymentWebhookEvent;
}

/**
 * Payment link creation request
 */
interface PaymentLinkRequest {
  amount: number;              // in paise/cents
  currency: string;            // INR, USD, etc.
  description: string;
  customerId?: string;
  customerEmail?: string;
  customerPhone?: string;
  metadata?: Record<string, unknown>;
  expireBy?: Date;             // link expiration
  notes?: Record<string, string>;

  // Our internal tracking
  transactionId: string;       // our transaction ID
  tripId?: string;
  invoiceId?: string;
}

/**
 * Payment link response
 */
interface PaymentLinkResponse {
  paymentId: string;           // gateway's payment ID
  linkUrl: string;
  shortUrl?: string;
  qrCode?: string;             // base64 encoded QR
  expiryAt?: Date;
  amount: number;
  currency: string;
}

/**
 * Payment status response
 */
interface PaymentStatusResponse {
  paymentId: string;
  status: PaymentStatus;
  amount: number;
  currency: string;
  paidAt?: Date;
  method?: PaymentMethod;
  card?: CardInfo;
  utr?: string;                // UTR for UPI
  bank?: string;               // bank for netbanking
}
```

### Razorpay Adapter Implementation

```typescript
/**
 * Razorpay gateway adapter
 */
import Razorpay from 'razorpay';

class RazorpayAdapter implements PaymentGatewayAdapter {
  readonly gatewayId = 'RAZORPAY';

  private client: Razorpay;

  constructor(config: RazorpayConfig) {
    this.client = new Razorpay({
      key_id: config.keyId,
      key_secret: config.keySecret
    });
  }

  async createPaymentLink(
    request: PaymentLinkRequest
  ): Promise<PaymentLinkResponse> {
    try {
      const razorpayRequest = {
        amount: request.amount,
        currency: request.currency,
        accept_partial: false,
        description: request.description,
        customer: request.customerId ? {
          name: request.customerId
        } : undefined,
        notify: {
          sms: true,
          email: request.customerEmail ? true : false
        },
        reminder_enable: true,
        notes: {
          ...request.notes,
          transactionId: request.transactionId,
          tripId: request.tripId || '',
          invoiceId: request.invoiceId || ''
        },
        expire_by: request.expireBy
          ? Math.floor(request.expireBy.getTime() / 1000)
          : undefined
      };

      const result = await this.client.paymentLink.create(razorpayRequest);

      return {
        paymentId: result.id,
        linkUrl: result.short_url || result.url,
        shortUrl: result.short_url,
        expiryAt: result.expire_by
          ? new Date(result.expire_by * 1000)
          : undefined,
        amount: result.amount,
        currency: result.currency
      };

    } catch (error) {
      throw new GatewayError(
        'Failed to create Razorpay payment link',
        this.gatewayId,
        error
      );
    }
  }

  async getPaymentStatus(
    paymentId: string
  ): Promise<PaymentStatusResponse> {
    try {
      const payment = await this.client.payments.fetch(paymentId);

      return {
        paymentId: payment.id,
        status: this.mapStatus(payment.status),
        amount: payment.amount,
        currency: payment.currency,
        paidAt: payment.created_at
          ? new Date(payment.created_at * 1000)
          : undefined,
        method: payment.method,
        card: payment.card ? {
          brand: payment.card.network,
          last4: payment.card.last4
        } : undefined,
        utr: payment.acquirer_data?.bank_transaction_id,
        bank: payment.bank
      };

    } catch (error) {
      throw new GatewayError(
        'Failed to fetch Razorpay payment status',
        this.gatewayId,
        error
      );
    }
  }

  async processRefund(
    request: RefundRequest
  ): Promise<RefundResponse> {
    try {
      const refund = await this.client.payments.refund(request.paymentId, {
        amount: request.amount,
        notes: request.notes
      });

      return {
        refundId: refund.id,
        status: this.mapRefundStatus(refund.status),
        amount: refund.amount,
        createdAt: new Date(refund.created_at * 1000)
      };

    } catch (error) {
      throw new GatewayError(
        'Failed to process Razorpay refund',
        this.gatewayId,
        error
      );
    }
  }

  verifyWebhookSignature(
    payload: string,
    signature: string,
    secret: string
  ): boolean {
    const crypto = require('crypto');
    const expectedSignature = crypto
      .createHmac('sha256', secret)
      .update(payload)
      .digest('hex');

    return crypto.timingSafeEqual(
      Buffer.from(signature),
      Buffer.from(expectedSignature)
    );
  }

  parseWebhookEvent(payload: unknown): PaymentWebhookEvent {
    const event = payload as RazorpayWebhookPayload;

    return {
      eventId: event.id,
      eventType: this.mapEventType(event.event),
      paymentId: event.payload.payment?.entity?.id,
      payload: event,
      timestamp: new Date(event.created_at * 1000)
    };
  }

  private mapStatus(status: string): PaymentStatus {
    const statusMap: Record<string, PaymentStatus> = {
      'created': 'PENDING',
      'authorized': 'AUTHORIZED',
      'captured': 'COMPLETED',
      'failed': 'FAILED',
      'refunded': 'REFUNDED'
    };
    return statusMap[status] || 'UNKNOWN';
  }

  private mapRefundStatus(status: string): RefundStatus {
    const statusMap: Record<string, RefundStatus> = {
      'created': 'PENDING',
      'processed': 'COMPLETED',
      'failed': 'FAILED'
    };
    return statusMap[status] || 'UNKNOWN';
  }

  private mapEventType(event: string): WebhookEventType {
    const eventMap: Record<string, WebhookEventType> = {
      'payment.captured': 'PAYMENT_SUCCESS',
      'payment.failed': 'PAYMENT_FAILED',
      'payment.authorized': 'PAYMENT_AUTHORIZED',
      'refund.processed': 'REFUND_PROCESSED',
      'refund.failed': 'REFUND_FAILED'
    };
    return eventMap[event] || 'UNKNOWN';
  }
}

/**
 * Razorpay configuration
 */
interface RazorpayConfig {
  keyId: string;
  keySecret: string;
  webhookSecret?: string;
}

type PaymentStatus = 'PENDING' | 'AUTHORIZED' | 'COMPLETED' | 'FAILED' | 'REFUNDED' | 'UNKNOWN';
type RefundStatus = 'PENDING' | 'COMPLETED' | 'FAILED';
type PaymentMethod = 'card' | 'upi' | 'netbanking' | 'wallet' | 'emi';
type WebhookEventType = 'PAYMENT_SUCCESS' | 'PAYMENT_FAILED' | 'PAYMENT_AUTHORIZED' | 'REFUND_PROCESSED' | 'REFUND_FAILED' | 'UNKNOWN';

interface CardInfo {
  brand: string;
  last4: string;
}
```

### Gateway Factory

```typescript
/**
 * Gateway factory for creating adapter instances
 */
class GatewayFactory {
  private adapters = new Map<string, PaymentGatewayAdapter>();
  private defaultGateway: string;

  constructor(config: GatewayConfig) {
    // Initialize configured gateways
    if (config.razorpay) {
      this.adapters.set(
        'RAZORPAY',
        new RazorpayAdapter(config.razorpay)
      );
    }

    if (config.stripe) {
      this.adapters.set(
        'STRIPE',
        new StripeAdapter(config.stripe)
      );
    }

    this.defaultGateway = config.default || 'RAZORPAY';
  }

  get(gatewayId?: string): PaymentGatewayAdapter {
    const id = gatewayId || this.defaultGateway;
    const adapter = this.adapters.get(id);

    if (!adapter) {
      throw new Error(`Unknown gateway: ${id}`);
    }

    return adapter;
  }

  getAvailableGateways(): string[] {
    return Array.from(this.adapters.keys());
  }

  getDefaultGateway(): string {
    return this.defaultGateway;
  }
}

interface GatewayConfig {
  default?: string;
  razorpay?: RazorpayConfig;
  stripe?: StripeConfig;
}
```

---

## Payment Link System

### Link Types

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PAYMENT LINK TYPES                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │   FULL PAYMENT  │  │   PARTIAL       │  │   SPLIT         │             │
│  │                 │  │   PAYMENT       │  │   PAYMENT       │             │
│  │ • Single amount │  │                 │  │                 │             │
│  │ • Full balance  │  │ • Min amount    │  │ • Multiple links│             │
│  │ • Standard flow │  │ • Flexibility   │  │ • Allocated     │             │
│  │                 │  │ • Deposit use   │  │ • Group travel  │             │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘             │
│                                                                             │
│  Link Features:                                                             │
│  • Expiration time (configurable, default 24 hours)                         │
│  • QR code for easy UPI payment                                             │
│  • SMS/Email notification on creation                                       │
│  • Reminders before expiration                                              │
│  • Multi-channel sharing (WhatsApp, Email, SMS)                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Payment Link Manager

```typescript
/**
 * Payment link manager
 */
class PaymentLinkManager {
  constructor(
    private gatewayFactory: GatewayFactory,
    private transactionStore: TransactionStore,
    private notificationService: NotificationService
  ) {}

  /**
   * Create a payment link
   */
  async createLink(
    request: CreateLinkRequest,
    context: RequestContext
  ): Promise<PaymentLink> {
    // Validate request
    await this.validateRequest(request, context);

    // Generate transaction ID and idempotency key
    const transactionId = this.generateTransactionId();
    const idempotencyKey = this.generateIdempotencyKey(transactionId);

    // Calculate expiry (default 24 hours)
    const expireBy = request.expireIn
      ? new Date(Date.now() + request.expireIn * 1000)
      : new Date(Date.now() + 24 * 60 * 60 * 1000);

    // Create transaction record
    const transaction: Transaction = {
      id: transactionId,
      idempotencyKey,
      type: request.type || 'FULL',
      amount: request.amount,
      currency: request.currency || 'INR',
      status: 'PENDING',
      gateway: request.gateway || this.gatewayFactory.getDefaultGateway(),
      tripId: request.tripId,
      invoiceId: request.invoiceId,
      agencyId: context.agencyId,
      createdBy: context.userId,
      expiresAt: expireBy,
      metadata: request.metadata || {}
    };

    await this.transactionStore.create(transaction);

    // Create gateway link
    const gateway = this.gatewayFactory.get(transaction.gateway);
    const gatewayResponse = await gateway.createPaymentLink({
      amount: transaction.amount,
      currency: transaction.currency,
      description: request.description || this.generateDescription(request),
      transactionId,
      tripId: request.tripId,
      invoiceId: request.invoiceId,
      expireBy,
      metadata: {
        transactionId,
        agencyId: context.agencyId,
        tripId: request.tripId
      }
    });

    // Update transaction with gateway details
    await this.transactionStore.update(transactionId, {
      gatewayPaymentId: gatewayResponse.paymentId,
      gatewayLinkUrl: gatewayResponse.linkUrl,
      gatewayShortUrl: gatewayResponse.shortUrl,
      qrCode: gatewayResponse.qrCode
    });

    // Generate QR code if not provided
    let qrCode = gatewayResponse.qrCode;
    if (!qrCode) {
      qrCode = await this.generateQRCode(gatewayResponse.linkUrl);
    }

    const paymentLink: PaymentLink = {
      id: transactionId,
      url: gatewayResponse.linkUrl,
      shortUrl: gatewayResponse.shortUrl,
      qrCode,
      amount: transaction.amount,
      currency: transaction.currency,
      expiresAt: expireBy,
      status: 'PENDING',
      gateway: transaction.gateway
    };

    // Send notifications if requested
    if (request.notify) {
      await this.sendLinkNotifications(paymentLink, request, context);
    }

    return paymentLink;
  }

  /**
   * Get payment link status
   */
  async getLinkStatus(
    transactionId: string,
    context: RequestContext
  ): Promise<PaymentLinkStatus> {
    const transaction = await this.transactionStore.get(transactionId);

    if (!transaction) {
      throw new NotFoundError('Payment link not found');
    }

    // Check agency access
    if (transaction.agencyId !== context.agencyId) {
      throw new ForbiddenError('Access denied');
    }

    // Check if expired
    const isExpired = transaction.expiresAt && new Date() > transaction.expiresAt;

    // If pending and not expired, check gateway status
    let gatewayStatus: PaymentStatusResponse | undefined;
    if (transaction.status === 'PENDING' && !isExpired) {
      const gateway = this.gatewayFactory.get(transaction.gateway);
      gatewayStatus = await gateway.getPaymentStatus(transaction.gatewayPaymentId!);

      // Update if status changed
      if (gatewayStatus.status !== 'PENDING') {
        await this.updateTransactionStatus(transaction, gatewayStatus);
      }
    }

    return {
      id: transaction.id,
      status: isExpired ? 'EXPIRED' : transaction.status,
      amount: transaction.amount,
      currency: transaction.currency,
      expiresAt: transaction.expiresAt,
      paidAt: transaction.paidAt,
      paymentMethod: transaction.paymentMethod,
      gateway: transaction.gateway,
      gatewayPaymentId: transaction.gatewayPaymentId
    };
  }

  /**
   * Create split payment links
   */
  async createSplitLinks(
    request: CreateSplitLinksRequest,
    context: RequestContext
  ): Promise<PaymentLink[]> {
    const links: PaymentLink[] = [];

    for (const split of request.splits) {
      const link = await this.createLink({
        ...request,
        amount: split.amount,
        description: split.description || request.description,
        metadata: {
          ...request.metadata,
          splitIndex: split.index,
          splitLabel: split.label
        }
      }, context);

      links.push(link);
    }

    // Store split relationship
    await this.transactionStore.createSplitGroup({
      groupId: request.groupId || this.generateGroupId(),
      transactionIds: links.map(l => l.id),
      tripId: request.tripId,
      totalAmount: request.splits.reduce((sum, s) => sum + s.amount, 0)
    });

    return links;
  }

  /**
   * Validate link creation request
   */
  private async validateRequest(
    request: CreateLinkRequest,
    context: RequestContext
  ): Promise<void> {
    // Check amount
    if (request.amount <= 0) {
      throw new ValidationError('Amount must be positive');
    }

    // Check max amount
    if (request.amount > 10_000_000) { // 1 lakh INR in paise
      throw new ValidationError('Amount exceeds maximum limit');
    }

    // Verify trip exists if provided
    if (request.tripId) {
      const trip = await this.tripStore.get(request.tripId);
      if (!trip || trip.agencyId !== context.agencyId) {
        throw new ValidationError('Invalid trip ID');
      }
    }

    // Verify invoice exists if provided
    if (request.invoiceId) {
      const invoice = await this.invoiceStore.get(request.invoiceId);
      if (!invoice || invoice.agencyId !== context.agencyId) {
        throw new ValidationError('Invalid invoice ID');
      }
    }
  }

  /**
   * Update transaction status from gateway
   */
  private async updateTransactionStatus(
    transaction: Transaction,
    gatewayStatus: PaymentStatusResponse
  ): Promise<void> {
    const update: Partial<Transaction> = {
      status: gatewayStatus.status,
      paidAt: gatewayStatus.paidAt,
      paymentMethod: gatewayStatus.method
    };

    if (gatewayStatus.card) {
      update.cardInfo = gatewayStatus.card;
    }

    if (gatewayStatus.utr) {
      update.utr = gatewayStatus.utr;
    }

    await this.transactionStore.update(transaction.id, update);

    // Trigger post-payment actions
    if (gatewayStatus.status === 'COMPLETED') {
      await this.onPaymentComplete(transaction, gatewayStatus);
    }
  }

  /**
   * Handle payment completion
   */
  private async onPaymentComplete(
    transaction: Transaction,
    gatewayStatus: PaymentStatusResponse
  ): Promise<void> {
    // Update trip status if linked
    if (transaction.tripId) {
      await this.tripService.recordPayment(transaction.tripId, {
        transactionId: transaction.id,
        amount: transaction.amount,
        paidAt: gatewayStatus.paidAt!,
        method: gatewayStatus.method!
      });
    }

    // Send confirmation notifications
    await this.notificationService.sendPaymentConfirmation({
      transactionId: transaction.id,
      tripId: transaction.tripId,
      amount: transaction.amount,
      paidAt: gatewayStatus.paidAt!
    });
  }

  /**
   * Send link notifications
   */
  private async sendLinkNotifications(
    link: PaymentLink,
    request: CreateLinkRequest,
    context: RequestContext
  ): Promise<void> {
    const channels: NotificationChannel[] = [];

    if (request.customerEmail) {
      channels.push({
        type: 'EMAIL',
        destination: request.customerEmail,
        template: 'payment-link-email',
        data: { link }
      });
    }

    if (request.customerPhone) {
      channels.push({
        type: 'SMS',
        destination: request.customerPhone,
        template: 'payment-link-sms',
        data: { link: link.shortUrl || link.url }
      });
    }

    await this.notificationService.send(channels);
  }

  /**
   * Generate QR code
   */
  private async generateQRCode(url: string): Promise<string> {
    // Use QR code library
    const QRCode = require('qrcode');
    return await QRCode.toDataURL(url);
  }

  private generateTransactionId(): string {
    return `TXN_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private generateIdempotencyKey(transactionId: string): string {
    return transactionId;
  }

  private generateGroupId(): string {
    return `GRP_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private generateDescription(request: CreateLinkRequest): string {
    if (request.tripId) {
      return `Payment for trip ${request.tripId}`;
    }
    if (request.invoiceId) {
      return `Payment for invoice ${request.invoiceId}`;
    }
    return 'Payment';
  }
}

/**
 * Create link request
 */
interface CreateLinkRequest {
  amount: number;
  currency?: string;
  description?: string;
  type?: 'FULL' | 'PARTIAL';
  tripId?: string;
  invoiceId?: string;
  gateway?: string;
  expireIn?: number;           // seconds
  notify?: boolean;
  customerEmail?: string;
  customerPhone?: string;
  metadata?: Record<string, unknown>;
}

/**
 * Create split links request
 */
interface CreateSplitLinksRequest extends CreateLinkRequest {
  splits: Array<{
    index: number;
    amount: number;
    label?: string;
    description?: string;
  }>;
  groupId?: string;
}

/**
 * Payment link response
 */
interface PaymentLink {
  id: string;
  url: string;
  shortUrl?: string;
  qrCode?: string;             // base64 data URL
  amount: number;
  currency: string;
  expiresAt: Date;
  status: TransactionStatus;
  gateway: string;
}

/**
 * Payment link status
 */
interface PaymentLinkStatus {
  id: string;
  status: TransactionStatus | 'EXPIRED';
  amount: number;
  currency: string;
  expiresAt?: Date;
  paidAt?: Date;
  paymentMethod?: PaymentMethod;
  gateway: string;
  gatewayPaymentId?: string;
}
```

---

## Transaction State Management

### Transaction State Machine

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      TRANSACTION STATE MACHINE                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│    ┌─────────┐                                                              │
│    │ PENDING │                                                              │
│    │         │◄─────────────────┐                                           │
│    └────┬────┘                   │                                           │
│         │                         │                                           │
│         │ Payment link created    │                                           │
│         │                         │                                           │
│         ▼                         │                                           │
│    ┌─────────┐   Authorize        │                                           │
│    │AUTHORIZE │───────────────────┤                                           │
│    └────┬────┘                   │                                           │
│         │                         │                                           │
│         │ Capture                 │                                           │
│         ▼                         │                                           │
│    ┌─────────┐   Failure          │    ┌─────────┐                            │
│    │COMPLETED │◄──────────────────┤    │  FAILED │                            │
│    └────┬────┘                   │    └────┬────┘                            │
│         │                         │         │                                 │
│         │ Refund                  │         │                                 │
│         ▼                         │         │                                 │
│    ┌─────────┐                    │    ┌───┴─────┐                            │
│    │ REFUNDED │                    │    │EXPIRED  │                            │
│    └─────────┘                    │    └─────────┘                            │
│                                    │                                           │
│  State Transitions:                │                                           │
│  ─────────────────                 │                                           │
│  PENDING → AUTHORIZED  (auth only) │                                           │
│  PENDING → COMPLETED    (auto-capture)                                          │
│  PENDING → FAILED       (payment failed)                                      │
│  PENDING → EXPIRED      (link expired)                                        │
│  AUTHORIZED → COMPLETED (capture)                                             │
│  AUTHORIZED → FAILED     (capture failed)                                     │
│  COMPLETED → REFUNDED   (refund processed)                                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Transaction Store

```typescript
/**
 * Transaction database model
 */
interface Transaction {
  id: string;
  idempotencyKey: string;

  // Amount details
  amount: number;
  currency: string;
  type: 'FULL' | 'PARTIAL';

  // Status
  status: TransactionStatus;
  statusHistory: TransactionStatusTransition[];

  // Gateway details
  gateway: string;
  gatewayPaymentId?: string;
  gatewayLinkUrl?: string;
  gatewayShortUrl?: string;

  // Payment details (when completed)
  paidAt?: Date;
  paymentMethod?: PaymentMethod;
  cardInfo?: CardInfo;
  utr?: string;

  // Relationship
  tripId?: string;
  invoiceId?: string;
  splitGroupId?: string;

  // Ownership
  agencyId: string;
  createdBy: string;

  // Timestamps
  expiresAt?: Date;
  createdAt: Date;
  updatedAt: Date;

  // Additional data
  qrCode?: string;
  metadata: Record<string, unknown>;
}

type TransactionStatus = 'PENDING' | 'AUTHORIZED' | 'COMPLETED' | 'FAILED' | 'REFUNDED';

interface TransactionStatusTransition {
  status: TransactionStatus;
  timestamp: Date;
  reason?: string;
  gatewayData?: unknown;
}

/**
 * Transaction store
 */
class TransactionStore {
  constructor(private db: Database) {}

  async create(transaction: Transaction): Promise<void> {
    await this.db.transactions.insert({
      ...transaction,
      statusHistory: [{
        status: transaction.status,
        timestamp: new Date()
      }]
    });
  }

  async get(id: string): Promise<Transaction | null> {
    return await this.db.transactions.findOne({ id });
  }

  async update(
    id: string,
    updates: Partial<Omit<Transaction, 'id' | 'idempotencyKey' | 'createdAt'>>
  ): Promise<void> {
    // Get current transaction
    const current = await this.get(id);
    if (!current) throw new NotFoundError('Transaction not found');

    // Build status history
    const statusHistory = [...current.statusHistory];
    if (updates.status && updates.status !== current.status) {
      statusHistory.push({
        status: updates.status,
        timestamp: new Date(),
        reason: updates.metadata?.reason as string
      });
    }

    await this.db.transactions.update(
      { id },
      {
        ...updates,
        statusHistory,
        updatedAt: new Date()
      }
    );
  }

  async findByTrip(tripId: string): Promise<Transaction[]> {
    return await this.db.transactions.find({ tripId }).sort({ createdAt: -1 });
  }

  async findByInvoice(invoiceId: string): Promise<Transaction[]> {
    return await this.db.transactions.find({ invoiceId }).sort({ createdAt: -1 });
  }

  async findBySplitGroup(groupId: string): Promise<Transaction[]> {
    return await this.db.transactions.find({ splitGroupId: groupId });
  }

  async findByAgency(
    agencyId: string,
    filters: TransactionFilters
  ): Promise<Transaction[]> {
    const query: Record<string, unknown> = { agencyId };

    if (filters.status) query.status = filters.status;
    if (filters.gateway) query.gateway = filters.gateway;
    if (filters.fromDate || filters.toDate) {
      query.createdAt = {};
      if (filters.fromDate) query.createdAt.$gte = filters.fromDate;
      if (filters.toDate) query.createdAt.$lte = filters.toDate;
    }

    return await this.db.transactions
      .find(query)
      .sort({ createdAt: -1 })
      .limit(filters.limit || 50);
  }
}

interface TransactionFilters {
  status?: TransactionStatus;
  gateway?: string;
  fromDate?: Date;
  toDate?: Date;
  limit?: number;
}
```

### Distributed Lock Manager

```typescript
/**
 * Distributed lock manager for idempotency
 */
class LockManager {
  constructor(private redis: Redis) {}

  /**
   * Acquire lock with timeout
   */
  async acquire(
    key: string,
    timeout: number = 30000
  ): Promise<Lock | null> {
    const lockKey = `lock:${key}`;
    const lockValue = Math.random().toString(36).substr(2);

    const acquired = await this.redis.set(
      lockKey,
      lockValue,
      'PX',
      timeout,
      'NX'
    );

    if (!acquired) {
      return null;
    }

    return {
      key: lockKey,
      value: lockValue,
      release: async () => {
        await this.release(lockKey, lockValue);
      }
    };
  }

  /**
   * Release lock
   */
  private async release(key: string, value: string): Promise<void> {
    const script = `
      if redis.call("get", KEYS[1]) == ARGV[1] then
        return redis.call("del", KEYS[1])
      else
        return 0
      end
    `;

    await this.redis.eval(script, 1, key, value);
  }

  /**
   * Execute with lock
   */
  async withLock<T>(
    key: string,
    fn: () => Promise<T>,
    timeout: number = 30000
  ): Promise<T> {
    const lock = await this.acquire(key, timeout);

    if (!lock) {
      throw new LockAcquisitionError(`Failed to acquire lock: ${key}`);
    }

    try {
      return await fn();
    } finally {
      await lock.release();
    }
  }
}

interface Lock {
  key: string;
  value: string;
  release: () => Promise<void>;
}

class LockAcquisitionError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'LockAcquisitionError';
  }
}
```

---

## Webhook Handling

### Webhook Endpoint

```typescript
/**
 * Webhook handler for payment events
 */
class PaymentWebhookHandler {
  constructor(
    private gatewayFactory: GatewayFactory,
    private transactionStore: TransactionStore,
    private lockManager: LockManager,
    private eventStore: EventStore
  ) {}

  /**
   * Handle incoming webhook
   */
  async handleWebhook(
    gatewayId: string,
    payload: string,
    signature: string,
    headers: Headers
  ): Promise<{ received: boolean }> {
    // Get gateway
    const gateway = this.gatewayFactory.get(gatewayId);

    // Verify signature
    const secret = this.getWebhookSecret(gatewayId);
    const isValid = gateway.verifyWebhookSignature(payload, signature, secret);

    if (!isValid) {
      throw new InvalidSignatureError('Invalid webhook signature');
    }

    // Parse event
    const event = gateway.parseWebhookEvent(JSON.parse(payload));

    // Store event first (idempotent)
    await this.eventStore.record(event);

    // Process with idempotency lock
    const lockKey = `webhook:${gatewayId}:${event.paymentId || event.eventId}`;

    await this.lockManager.withLock(lockKey, async () => {
      // Check if already processed
      const alreadyProcessed = await this.eventStore.isProcessed(event.eventId);
      if (alreadyProcessed) {
        return { received: true };
      }

      // Process event
      await this.processEvent(event, gatewayId);

      // Mark as processed
      await this.eventStore.markProcessed(event.eventId);
    });

    return { received: true };
  }

  /**
   * Process webhook event
   */
  private async processEvent(
    event: PaymentWebhookEvent,
    gatewayId: string
  ): Promise<void> {
    switch (event.eventType) {
      case 'PAYMENT_SUCCESS':
        await this.handlePaymentSuccess(event);
        break;

      case 'PAYMENT_FAILED':
        await this.handlePaymentFailed(event);
        break;

      case 'PAYMENT_AUTHORIZED':
        await this.handlePaymentAuthorized(event);
        break;

      case 'REFUND_PROCESSED':
        await this.handleRefundProcessed(event);
        break;

      case 'REFUND_FAILED':
        await this.handleRefundFailed(event);
        break;

      default:
        logger.warn('Unknown webhook event type', { eventType: event.eventType });
    }
  }

  /**
   * Handle payment success
   */
  private async handlePaymentSuccess(
    event: PaymentWebhookEvent
  ): Promise<void> {
    const payload = event.payload as any;
    const gatewayPaymentId = payload.payload?.payment?.entity?.id;

    if (!gatewayPaymentId) {
      logger.error('Payment success event missing payment ID');
      return;
    }

    // Find transaction
    const transaction = await this.transactionStore.db.transactions.findOne({
      gatewayPaymentId
    });

    if (!transaction) {
      logger.error('Transaction not found for payment', { gatewayPaymentId });
      return;
    }

    // Update status
    await this.transactionStore.update(transaction.id, {
      status: 'COMPLETED',
      paidAt: event.timestamp,
      paymentMethod: payload.payload?.payment?.entity?.method,
      cardInfo: payload.payload?.payment?.entity?.card,
      utr: payload.payload?.payment?.entity?.acquirer_data?.bank_transaction_id,
      metadata: {
        gatewayEventData: payload
      }
    });

    // Trigger post-payment actions
    await this.triggerPaymentActions(transaction);
  }

  /**
   * Handle payment failure
   */
  private async handlePaymentFailed(
    event: PaymentWebhookEvent
  ): Promise<void> {
    const payload = event.payload as any;
    const gatewayPaymentId = payload.payload?.payment?.entity?.id;

    if (!gatewayPaymentId) return;

    const transaction = await this.transactionStore.db.transactions.findOne({
      gatewayPaymentId
    });

    if (!transaction) return;

    await this.transactionStore.update(transaction.id, {
      status: 'FAILED',
      metadata: {
        failureReason: payload.payload?.payment?.entity?.error?.description,
        gatewayEventData: payload
      }
    });

    await this.notifyPaymentFailed(transaction);
  }

  /**
   * Handle payment authorization
   */
  private async handlePaymentAuthorized(
    event: PaymentWebhookEvent
  ): Promise<void> {
    const payload = event.payload as any;
    const gatewayPaymentId = payload.payload?.payment?.entity?.id;

    if (!gatewayPaymentId) return;

    const transaction = await this.transactionStore.db.transactions.findOne({
      gatewayPaymentId
    });

    if (!transaction) return;

    await this.transactionStore.update(transaction.id, {
      status: 'AUTHORIZED',
      paidAt: event.timestamp,
      paymentMethod: payload.payload?.payment?.entity?.method,
      metadata: {
        gatewayEventData: payload
      }
    });
  }

  /**
   * Handle refund processed
   */
  private async handleRefundProcessed(
    event: PaymentWebhookEvent
  ): Promise<void> {
    const payload = event.payload as any;
    const paymentId = payload.payload?.refund?.entity?.payment_id;

    if (!paymentId) return;

    const transaction = await this.transactionStore.db.transactions.findOne({
      gatewayPaymentId: paymentId
    });

    if (!transaction) return;

    await this.transactionStore.update(transaction.id, {
      status: 'REFUNDED',
      metadata: {
        refundId: payload.payload?.refund?.entity?.id,
        refundAmount: payload.payload?.refund?.entity?.amount,
        gatewayEventData: payload
      }
    });

    await this.notifyRefundProcessed(transaction);
  }

  /**
   * Trigger post-payment actions
   */
  private async triggerPaymentActions(
    transaction: Transaction
  ): Promise<void> {
    // Update trip if linked
    if (transaction.tripId) {
      await this.tripService.onPaymentComplete(transaction.tripId, {
        transactionId: transaction.id,
        amount: transaction.amount,
        paidAt: transaction.paidAt!
      });
    }

    // Update invoice if linked
    if (transaction.invoiceId) {
      await this.invoiceService.onPaymentComplete(transaction.invoiceId, {
        transactionId: transaction.id,
        amount: transaction.amount
      });
    }

    // Send notifications
    await this.notificationService.sendPaymentSuccess({
      transactionId: transaction.id,
      tripId: transaction.tripId,
      amount: transaction.amount,
      paidAt: transaction.paidAt!
    });
  }

  private getWebhookSecret(gatewayId: string): string {
    // Get from secure config
    return process.env[`${gatewayId}_WEBHOOK_SECRET`] || '';
  }
}

/**
 * Payment webhook event
 */
interface PaymentWebhookEvent {
  eventId: string;
  eventType: WebhookEventType;
  paymentId?: string;
  payload: unknown;
  timestamp: Date;
}

/**
 * Event store for idempotency
 */
class EventStore {
  constructor(private db: Database) {}

  async record(event: PaymentWebhookEvent): Promise<void> {
    await this.db.webhookEvents.insert({
      eventId: event.eventId,
      eventType: event.eventType,
      paymentId: event.paymentId,
      payload: event.payload,
      timestamp: event.timestamp,
      processed: false
    });
  }

  async isProcessed(eventId: string): Promise<boolean> {
    const event = await this.db.webhookEvents.findOne({ eventId });
    return event?.processed || false;
  }

  async markProcessed(eventId: string): Promise<void> {
    await this.db.webhookEvents.update(
      { eventId },
      { processed: true, processedAt: new Date() }
    );
  }
}

class InvalidSignatureError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'InvalidSignatureError';
  }
}
```

---

## Idempotency & Safety

### Idempotency Key Strategy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         IDEMPOTENCY STRATEGY                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Purpose: Ensure duplicate requests don't create duplicate payments         │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  1. Client generates idempotency key (UUID)                          │    │
│  │  2. Send with first request                                         │    │
│  │  3. Server checks if key seen before                                │    │
│  │  4. If new: process normally, store result                           │    │
│  │  5. If seen: return stored result without processing                │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  Key Lifecycle:                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  Created ──► Used ──► Result Stored ──► Expires (24h)               │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  Storage: Redis with 24-hour TTL                                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Idempotency Middleware

```typescript
/**
 * Idempotency middleware for payment operations
 */
class IdempotencyMiddleware {
  constructor(private redis: Redis) {}

  /**
   * Middleware handler
   */
  async handle(
    request: IdempotentRequest,
    next: () => Promise<unknown>
  ): Promise<unknown> {
    const { idempotencyKey, operation } = request;

    if (!idempotencyKey) {
      throw new IdempotencyKeyRequiredError('Idempotency key required');
    }

    const storageKey = this.getStorageKey(operation, idempotencyKey);

    // Check for existing response
    const existing = await this.getStoredResponse(storageKey);

    if (existing) {
      logger.info('Returning cached idempotent response', {
        operation,
        idempotencyKey
      });
      return existing.response;
    }

    // Lock to prevent race conditions
    const lock = await this.acquireLock(storageKey);

    try {
      // Double-check after acquiring lock
      const recheck = await this.getStoredResponse(storageKey);
      if (recheck) {
        return recheck.response;
      }

      // Process request
      const response = await next();

      // Store response
      await this.storeResponse(storageKey, {
        response,
        timestamp: new Date()
      });

      return response;

    } finally {
      await lock?.release();
    }
  }

  private getStorageKey(operation: string, key: string): string {
    return `idempotent:${operation}:${key}`;
  }

  private async getStoredResponse(
    key: string
  ): Promise<StoredResponse | null> {
    const data = await this.redis.get(key);

    if (!data) return null;

    return JSON.parse(data);
  }

  private async storeResponse(
    key: string,
    data: StoredResponse
  ): Promise<void> {
    await this.redis.setex(
      key,
      86400, // 24 hours
      JSON.stringify(data)
    );
  }

  private async acquireLock(key: string): Promise<Lock> {
    const lockKey = `lock:${key}`;
    const lockValue = Math.random().toString(36).substr(2);

    const acquired = await this.redis.set(
      lockKey,
      lockValue,
      'PX',
      5000, // 5 second lock
      'NX'
    );

    if (!acquired) {
      throw new ConcurrentRequestError('Concurrent request with same idempotency key');
    }

    return {
      key: lockKey,
      value: lockValue,
      release: async () => {
        const script = `
          if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
          end
        `;
        await this.redis.eval(script, 1, lockKey, lockValue);
      }
    };
  }
}

interface IdempotentRequest {
  idempotencyKey: string;
  operation: string;
}

interface StoredResponse {
  response: unknown;
  timestamp: Date;
}

class IdempotencyKeyRequiredError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'IdempotencyKeyRequiredError';
  }
}

class ConcurrentRequestError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'ConcurrentRequestError';
  }
}
```

---

## API Reference

### Payment Link API

```typescript
/**
 * POST /api/payments/link
 * Create a payment link
 */
interface CreatePaymentLinkRequest {
  amount: number;
  currency?: string;              // default: INR
  description?: string;
  type?: 'FULL' | 'PARTIAL';
  tripId?: string;
  invoiceId?: string;
  gateway?: string;               // default: from config
  expireIn?: number;              // seconds, default: 86400 (24h)
  notify?: boolean;               // default: false
  customerEmail?: string;
  customerPhone?: string;
  metadata?: Record<string, unknown>;
}

interface CreatePaymentLinkResponse {
  id: string;
  url: string;
  shortUrl?: string;
  qrCode?: string;
  amount: number;
  currency: string;
  expiresAt: Date;
  status: 'PENDING';
}

/**
 * GET /api/payments/link/:id
 * Get payment link status
 */
interface GetPaymentLinkResponse {
  id: string;
  status: 'PENDING' | 'AUTHORIZED' | 'COMPLETED' | 'FAILED' | 'EXPIRED';
  amount: number;
  currency: string;
  expiresAt?: Date;
  paidAt?: Date;
  paymentMethod?: string;
  gateway: string;
}
```

### Payment Status API

```typescript
/**
 * GET /api/payments/transaction/:id
 * Get transaction details
 */
interface GetTransactionResponse {
  id: string;
  amount: number;
  currency: string;
  status: TransactionStatus;
  gateway: string;
  tripId?: string;
  invoiceId?: string;
  paidAt?: Date;
  paymentMethod?: PaymentMethod;
  cardInfo?: CardInfo;
  createdAt: Date;
  updatedAt: Date;
}
```

### Webhook Endpoint

```typescript
/**
 * POST /api/webhooks/payment/:gateway
 * Webhook endpoint for payment gateway events
 */
interface WebhookRequest {
  // Raw body as string for signature verification
  headers: {
    'x-webhook-signature': string;
    'x-gateway-id': string;
  };
  body: string;
}

interface WebhookResponse {
  received: boolean;
}
```

---

## Summary

This document covers the technical architecture of payment processing:

1. **Architecture Overview** — System design, data flows for link creation and payment completion
2. **Payment Gateway Integration** — Gateway adapter interface, Razorpay implementation, factory pattern
3. **Payment Link System** — Link types (full, partial, split), link manager, QR code generation
4. **Transaction State Management** — State machine, transaction store, distributed locks
5. **Webhook Handling** — Signature verification, event processing, idempotency
6. **Idempotency & Safety** — Idempotency keys, duplicate prevention, concurrent request handling
7. **API Reference** — Payment link and status APIs

**Key Takeaways:**

- Gateway adapter pattern abstracts provider differences
- Idempotency keys prevent duplicate payments
- Distributed locks ensure webhook safety
- Transaction state machine tracks payment lifecycle
- Webhooks drive real-time status updates
- QR codes enable easy UPI payments

**Related Documents:**
- [UX/UI Deep Dive](./PAYMENT_PROCESSING_02_UX_UI_DEEP_DIVE.md) — Payment flow design
- [Compliance Deep Dive](./PAYMENT_PROCESSING_03_COMPLIANCE_DEEP_DIVE.md) — PCI compliance
