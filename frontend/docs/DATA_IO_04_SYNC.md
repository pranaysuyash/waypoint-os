# Data Import, Export & Migration — Data Sync & Integration

> Research document for ongoing data synchronization, real-time sync, and cross-system data consistency.

---

## Key Questions

1. **How do we keep data synchronized between the platform and external systems?**
2. **What's the sync model — real-time, near-real-time, or batch?**
3. **How do we handle sync conflicts when both systems modify the same data?**
4. **What's the webhook/event model for notifying external systems?**
5. **How do we monitor sync health and detect drift?**

---

## Research Areas

### Sync Architecture

```typescript
interface DataSync {
  syncId: string;
  name: string;
  source: SyncEndpoint;
  target: SyncEndpoint;
  direction: SyncDirection;
  entities: SyncEntity[];
  schedule: SyncSchedule;
  conflictResolution: ConflictStrategy;
  status: SyncStatus;
  lastSyncAt?: Date;
  nextSyncAt?: Date;
}

type SyncDirection =
  | 'one_way_export'                  // Platform → External
  | 'one_way_import'                  // External → Platform
  | 'bidirectional';                  // Both ways with conflict resolution

interface SyncEndpoint {
  type: 'platform' | 'tally' | 'zoho' | 'quickbooks' | 'salesforce' | 'google_sheets' | 'custom_api';
  config: Record<string, unknown>;
  auth: SyncAuth;
}

type SyncAuth =
  | { type: 'api_key'; key: string }
  | { type: 'oauth2'; clientId: string }
  | { type: 'basic_auth'; username: string }
  | { type: 'custom'; description: string };

// Common sync scenarios:
// Platform → Tally: Sync invoices and payments for accounting
// Platform → Zoho CRM: Sync customer profiles for sales
// Google Sheets → Platform: Supplier price list updates
// Platform → WhatsApp Business: Customer communication
// Platform → Bank: Payment reconciliation
// Salesforce → Platform: Lead/customer data from corporate CRM
```

### Sync Entities & Scheduling

```typescript
type SyncEntity =
  | 'customers'                      // Customer master sync
  | 'bookings'                       // Booking status sync
  | 'payments'                       // Payment/Invoice sync
  | 'invoices'                       // Invoice sync for accounting
  | 'suppliers'                      // Supplier directory sync
  | 'price_lists'                    // Rate updates from suppliers
  | 'agent_performance'              // Performance metrics to HR
  | 'commission_data'                // Commission data to payroll
  | 'gst_data'                       // GST data to filing system
  | 'inventory';                     // Availability/stock sync

interface SyncSchedule {
  mode: SyncMode;
  interval?: number;                 // Minutes between syncs (for scheduled)
  eventTriggers?: string[];          // Events that trigger sync (for event-driven)
}

type SyncMode =
  | { type: 'realtime'; transport: 'webhook' | 'websocket' | 'sse' }
  | { type: 'scheduled'; intervalMinutes: number }
  | { type: 'event_driven'; events: string[] }
  | { type: 'manual' };              // Triggered by user action

// Sync frequency by entity:
// Payments → Real-time (every payment must sync to accounting immediately)
// Bookings → Near-real-time (within 5 minutes of status change)
// Customers → Scheduled hourly (customer profile updates)
// Price lists → Scheduled daily at 6 AM (supplier rate updates)
// GST data → Scheduled monthly (before filing deadline)
// Inventory → Real-time (availability changes affect bookings)
// Commission → Scheduled daily (end of day processing)

// Sync batch optimization:
// Instead of syncing each change individually:
// 1. Collect changes in a buffer (1-5 minutes window)
// 2. Batch into a single sync request
// 3. Reduces API calls and improves efficiency
// 4. Real-time overrides batch for critical entities (payments)
```

### Conflict Resolution

```typescript
interface SyncConflict {
  conflictId: string;
  entity: string;
  entityId: string;
  sourceValue: unknown;
  targetValue: unknown;
  sourceUpdatedAt: Date;
  targetUpdatedAt: Date;
  resolution: ConflictResolution;
}

type ConflictStrategy =
  | { type: 'source_wins' }          // Always prefer source system
  | { type: 'target_wins' }          // Always prefer target system
  | { type: 'latest_wins' }          // Most recently updated wins
  | { type: 'manual' }               // Require human resolution
  | { type: 'field_level' }          // Per-field strategy
  | { type: 'merge' };               // Attempt automatic merge

// Conflict resolution rules by entity:
// Customers: latest_wins (most recent update takes precedence)
// Payments: source_wins (platform is source of truth for payments)
// Invoices: manual (financial discrepancies need human review)
// Price lists: source_wins (supplier's system is source of truth)
// Bookings: latest_wins with manual override (booking changes are critical)

// Conflict detection:
// 1. Track last_synced_at per entity per record
// 2. Before writing, check if source was modified since last sync
// 3. If both sides modified → Conflict detected
// 4. Apply conflict strategy or queue for manual resolution
// 5. Log conflict for audit trail
```

### Webhook & Event System

```typescript
interface WebhookConfig {
  webhookId: string;
  url: string;
  events: WebhookEvent[];
  headers: Record<string, string>;
  retryPolicy: RetryPolicy;
  active: boolean;
  secret: string;                    // For signature verification
}

type WebhookEvent =
  | 'booking.created'
  | 'booking.confirmed'
  | 'booking.cancelled'
  | 'booking.modified'
  | 'payment.received'
  | 'payment.refunded'
  | 'invoice.generated'
  | 'customer.created'
  | 'customer.updated'
  | 'trip.quoted'
  | 'trip.confirmed'
  | 'trip.completed'
  | 'supplier.updated'
  | 'price.updated';

// Webhook delivery:
// 1. Event occurs in platform
// 2. Webhook payload constructed with event data
// 3. HMAC signature computed for verification
// 4. HTTP POST to registered URL
// 5. Expect 200 response within 10 seconds
// 6. On failure, retry with exponential backoff (1min, 5min, 15min, 1hr)
// 7. After 5 failures, mark webhook as failing, notify owner
// 8. Delivery log maintained for 30 days

// Webhook payload format:
// {
//   "event_id": "evt_123abc",
//   "event_type": "booking.confirmed",
//   "timestamp": "2026-04-28T10:30:00+05:30",
//   "data": {
//     "booking_id": "BK-2026-001234",
//     "trip_id": "TRP-2026-00567",
//     "customer_name": "Rajesh Sharma",
//     "total_amount": 125000.00,
//     "currency": "INR",
//     "booking_date": "2026-04-28"
//   },
//   "signature": "sha256=abc123..."
// }
```

### Sync Health Monitoring

```typescript
interface SyncHealth {
  syncId: string;
  status: 'healthy' | 'degraded' | 'failing' | 'paused';
  lastSuccessfulSync: Date;
  consecutiveFailures: number;
  recordsSynced: number;
  recordsFailed: number;
  latencyMs: number;
  driftDetected: boolean;
  driftDetails?: DriftReport;
}

interface DriftReport {
  checkedAt: Date;
  sourceCount: number;
  targetCount: number;
  mismatchCount: number;
  missingInTarget: number;
  missingInSource: number;
  sampleMismatches: DriftSample[];
}

// Sync health dashboard:
// - Green: All syncs running within SLA
// - Yellow: Some syncs delayed or degraded
// - Red: Sync failing, data may be stale
// - Per-entity status cards
// - Last sync timestamp and next scheduled sync
// - Failure log with error details
// - "Sync Now" button for manual trigger
// - Drift detection: Compare source and target counts weekly
```

---

## Open Problems

1. **Accounting system diversity** — Every agency uses a different accounting system (Tally, Busy, Zoho Books, ClearTax). Each needs a custom sync adapter.

2. **Rate limiting** — External APIs have rate limits (Tally API: 100 req/min). Sync must respect limits while staying current.

3. **Data format mismatches** — Platform uses decimal for amounts, Tally uses strings. Date formats differ. Each sync needs format translation.

4. **Idempotency** — Syncing the same record twice shouldn't create duplicates. Need idempotency keys and deduplication.

5. **Schema evolution** — Platform schema changes over time. Sync adapters need to handle version differences gracefully.

---

## Next Steps

- [ ] Design sync framework with pluggable adapters for common systems
- [ ] Build webhook delivery system with retry and signature verification
- [ ] Create sync health monitoring dashboard
- [ ] Design drift detection and reconciliation tools
- [ ] Study integration platforms (Zapier, Workato, MuleSoft, custom)
