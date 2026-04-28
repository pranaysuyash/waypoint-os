# Mobile Experience — Offline Support & Data Sync

> Research document for offline-first architecture, data synchronization, and conflict resolution.

---

## Key Questions

1. **What operations must work offline (view itinerary, contact emergency, show vouchers)?**
2. **What's the sync model — real-time, eventual, or manual?**
3. **How do we handle conflicts when offline changes conflict with server state?**
4. **What's the storage budget per device, and how to manage it?**
5. **How do we communicate sync status to the user?**

---

## Research Areas

### Offline Capabilities Matrix

```typescript
interface OfflineCapability {
  feature: string;
  offlineMode: OfflineMode;
  dataRequired: string[];
  storageEstimate: string;
}

type OfflineMode =
  | 'full'               // Works completely offline
  | 'degraded'           // Works with reduced functionality
  | 'view_only'          // Can view but not modify
  | 'queue_and_sync'     // Actions queued for when online
  | 'unavailable';       // Requires connectivity

// Feature mapping:
// View itinerary → full (cached locally)
// View vouchers → full (PDF cached)
// View booking details → full
// Edit customer notes → queue_and_sync
// Upload photos → queue_and_sync (queued for upload)
// Search new trips → unavailable
// Make new booking → unavailable
// Contact support → degraded (show cached phone numbers)
// View maps → degraded (static map tiles cached)
// Emergency contacts → full (always cached)
// Payment → unavailable
```

### Sync Architecture

```typescript
interface SyncEngine {
  // Queue a mutation while offline
  enqueue(mutation: PendingMutation): void;
  // Process queue when online
  processQueue(): Promise<SyncResult[]>;
  // Get current sync status
  getStatus(): SyncStatus;
  // Subscribe to sync events
  onSyncEvent(handler: SyncEventHandler): void;
}

interface PendingMutation {
  mutationId: string;
  entityType: string;
  entityId: string;
  operation: 'create' | 'update' | 'delete';
  payload: Record<string, unknown>;
  timestamp: Date;
  deviceId: string;
  retryCount: number;
  maxRetries: number;
}

interface SyncStatus {
  state: 'online' | 'offline' | 'syncing';
  pendingCount: number;
  lastSyncAt?: Date;
  lastSyncError?: string;
  queueSize: number;             // Bytes
}

interface SyncResult {
  mutationId: string;
  success: boolean;
  conflict?: ConflictDetail;
  serverVersion?: Record<string, unknown>;
  error?: string;
}
```

### Conflict Resolution

```typescript
interface ConflictDetail {
  entityType: string;
  entityId: string;
  clientVersion: Record<string, unknown>;
  serverVersion: Record<string, unknown>;
  conflictingFields: string[];
  resolution: ConflictResolution;
}

type ConflictResolution =
  | { strategy: 'server_wins'; reason: string }
  | { strategy: 'client_wins'; reason: string }
  | { strategy: 'merge'; mergedData: Record<string, unknown> }
  | { strategy: 'manual'; options: ConflictOption[] };

interface ConflictOption {
  label: string;
  data: Record<string, unknown>;
  description: string;
}

// Resolution strategies by data type:
// Customer notes → client_wins (user intent)
// Booking details → server_wins (source of truth)
// Customer preferences → merge (combine both)
// Pricing data → server_wins (always authoritative)
// Trip status → server_wins (source of truth)
// Agent comments → merge (combine both)
```

### Storage Management

```typescript
interface StorageBudget {
  totalBudgetMB: number;           // Target: 30-50MB
  allocations: StorageAllocation[];
  evictionPolicy: EvictionPolicy;
}

interface StorageAllocation {
  category: string;
  budgetMB: number;
  priority: number;                // Higher = last to evict
  items: number;
}

// Budget allocation:
// Itinerary data: 5MB (priority 10 — never evict)
// Voucher PDFs: 15MB (priority 9 — evict after trip ends)
// Emergency contacts: 0.5MB (priority 10 — never evict)
// Customer profile: 2MB (priority 8)
// Image cache: 10MB (priority 3 — evict first)
// Pending mutations: 2MB (priority 7)
// App shell: 5MB (priority 10 — never evict)

interface EvictionPolicy {
  // Evict in priority order (lowest first)
  strategy: 'priority_order';
  // Don't evict data for active trips
  protectActiveTrips: boolean;
  // Clean up data for trips completed >30 days ago
  autoCleanup: boolean;
  cleanupAfterDays: number;
}
```

---

## Open Problems

1. **Large PDF caching** — Vouchers and tickets as PDFs consume significant storage. Need intelligent caching (only upcoming trips) and lazy loading.

2. **Map offline support** — Showing destination maps offline requires pre-caching map tiles. Google Maps offline support is limited in PWA context.

3. **Binary data sync** — Photos uploaded offline need to sync when online. Large file uploads over unreliable connections need resumable upload support.

4. **Multi-device sync** — Customer uses both phone and tablet. Changes on one need to sync to the other through the server. Two offline devices modifying the same data creates complex conflicts.

5. **Sync indicator UX** — How to show "you're seeing cached data, last synced 2 hours ago" without alarming users.

---

## Next Steps

- [ ] Design offline-first data layer using IndexedDB
- [ ] Build sync engine prototype with queue and retry logic
- [ ] Design conflict resolution strategies per entity type
- [ ] Study offline-first patterns (PouchDB/CouchDB, Firebase offline)
- [ ] Design storage budget and eviction policy
- [ ] Create sync status UI component
