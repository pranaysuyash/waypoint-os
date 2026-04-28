# Integration Hub & Connectors — Webhooks & Events

> Research document for webhook management, event-driven architecture, and integration event processing.

---

## Key Questions

1. **How do external systems send events to the platform?**
2. **What's the event processing pipeline for incoming webhooks?**
3. **How do we handle webhook retries and delivery guarantees?**
4. **What's the event schema for cross-system communication?**
5. **How do we monitor webhook processing health?**

---

## Research Areas

### Incoming Webhook Processing

```typescript
interface IncomingWebhook {
  webhookId: string;
  source: string;
  eventType: string;
  payload: unknown;
  receivedAt: Date;
  processingStatus: WebhookStatus;
  processingAttempts: number;
  lastAttemptAt?: Date;
  error?: string;
}

type WebhookStatus =
  | 'received'
  | 'processing'
  | 'completed'
  | 'failed'
  | 'retrying'
  | 'dead_letter';

// Webhook processing pipeline:
// 1. Receive webhook → Verify signature
// 2. Parse payload → Normalize to internal event format
// 3. Route to appropriate handler
// 4. Process event (update booking, payment, etc.)
// 5. Acknowledge to sender (200 OK)
// 6. If processing fails → Queue for retry
// 7. If retries exhausted → Dead letter queue
// 8. Alert team if dead letter queue grows

// Signature verification per provider:
// Razorpay: HMAC-SHA256 with webhook secret
// WhatsApp: HMAC-SHA256 with app secret
// Amadeus: JWT token verification
// Stripe: HMAC-SHA256 with signing secret
// Custom: Configurable (HMAC, JWT, API key)

// Incoming webhook sources:
// Payment gateway: payment.captured, payment.failed, refund.processed
// WhatsApp: message.received, message.read, message.delivery_report
// Amadeus: booking.confirmed, booking.cancelled, schedule.change
// Supplier APIs: booking.confirmed, booking.rejected, price.update
// Government: gst.filing_status, visa.status_update
```

### Outgoing Webhooks

```typescript
interface OutgoingWebhook {
  webhookId: string;
  agencyId: string;
  url: string;
  events: string[];
  headers: Record<string, string>;
  secret: string;
  retryPolicy: OutgoingRetryPolicy;
  active: boolean;
  createdAt: Date;
  createdBy: string;
  deliveryLog: WebhookDelivery[];
}

interface OutgoingRetryPolicy {
  maxRetries: number;
  backoffStrategy: 'exponential' | 'fixed';
  initialDelayMs: number;
  maxDelayMs: number;
  retryOnStatusCodes: number[];      // [408, 429, 500, 502, 503, 504]
}

interface WebhookDelivery {
  deliveryId: string;
  webhookId: string;
  event: string;
  payload: string;
  statusCode?: number;
  responseTimeMs?: number;
  deliveredAt?: Date;
  nextRetryAt?: Date;
  status: 'pending' | 'delivered' | 'failed' | 'retrying';
}

// Outgoing webhook events for travel platform:
// Booking lifecycle:
//   booking.created, booking.confirmed, booking.cancelled,
//   booking.modified, booking.ticket_issued
//
// Payment:
//   payment.received, payment.refunded, payment.failed,
//   invoice.generated, receipt.generated
//
// Customer:
//   customer.created, customer.updated, customer.feedback_received
//
// Trip:
//   trip.quoted, trip.confirmed, trip.in_progress,
//   trip.completed, trip.cancelled
//
// Agent:
//   agent.created, agent.task_assigned, agent.commission_earned

// Webhook management UI:
// - Register webhook URL
// - Select events to subscribe
// - Test webhook (send test payload)
// - View delivery log (last 100 deliveries)
// - Retry failed deliveries
// - View payload and response for each delivery
// - Disable/enable webhook
```

### Event Processing Pipeline

```typescript
interface EventPipeline {
  stages: EventPipelineStage[];
  deadLetterQueue: DeadLetterConfig;
  monitoring: PipelineMonitoring;
}

interface EventPipelineStage {
  stageName: string;
  handler: string;
  timeout: number;
  retries: number;
  onError: 'retry' | 'skip' | 'dead_letter';
}

// Pipeline stages:
// Stage 1: Ingestion
//   - Receive raw webhook payload
//   - Verify signature/authenticity
//   - Parse and normalize
//   - Assign event ID
//
// Stage 2: Routing
//   - Match event type to handler
//   - Determine priority (payment events = high)
//   - Queue for processing
//
// Stage 3: Processing
//   - Execute business logic
//   - Update database
//   - Trigger downstream events
//   - Idempotency check (prevent duplicate processing)
//
// Stage 4: Notification
//   - Send notifications for relevant events
//   - Update real-time clients (WebSocket)
//   - Trigger workflow automations
//
// Stage 5: Audit
//   - Log event processing
//   - Record outcome
//   - Store raw payload for debugging

// Idempotency:
interface IdempotencyRecord {
  eventId: string;
  source: string;
  processedAt: Date;
  result: 'success' | 'duplicate' | 'error';
}

// Every event is checked against idempotency records
// Same event processed twice = no side effects
// Key: source + event_type + external_id
```

---

## Open Problems

1. **Webhook security** — Anyone can send a POST to a webhook URL. Need robust signature verification and IP allowlisting.

2. **Event ordering** — Payment captured event arrives before payment created event due to network timing. Need event ordering or idempotent handling.

3. **Payload size** — Some webhooks carry large payloads (full booking details). Need payload size limits and selective field delivery.

4. **Webhook URL management** — If the platform URL changes (migration, load balancer update), all registered webhooks break. Need stable URLs.

5. **Testing webhooks** — Developers need to test webhook handling locally. Need webhook tunneling (like ngrok) or replay capability.

---

## Next Steps

- [ ] Design webhook processing pipeline with signature verification
- [ ] Build outgoing webhook management with delivery tracking
- [ ] Create event schema registry for cross-system events
- [ ] Design dead letter queue and retry mechanism
- [ ] Study event-driven patterns (AWS EventBridge, Stripe webhooks, Shopify webhooks)
