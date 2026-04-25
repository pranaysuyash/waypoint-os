# Mobile App — Sync Deep Dive

> Data synchronization, conflict resolution, and offline-first architecture

---

## Document Overview

**Series:** Mobile App | **Document:** 3 of 4 | **Focus:** Data Synchronization

**Related Documents:**
- [01: Technical Deep Dive](./MOBILE_APP_01_TECHNICAL_DEEP_DIVE.md) — Architecture overview
- [02: UX/UI Deep Dive](./MOBILE_APP_02_UX_UI_DEEP_DIVE.md) — Mobile design patterns
- [04: Notifications Deep Dive](./MOBILE_APP_04_NOTIFICATIONS_DEEP_DIVE.md) — Push notifications

---

## Table of Contents

1. [Offline-First Architecture](#1-offline-first-architecture)
2. [Data Synchronization Strategies](#2-data-synchronization-strategies)
3. [Conflict Resolution](#3-conflict-resolution)
4. [Background Sync](#4-background-sync)
5. [Cache Management](#5-cache-management)
6. [Network State Handling](#6-network-state-handling)
7. [Implementation Patterns](#7-implementation-patterns)
8. [Testing & Monitoring](#8-testing--monitoring)

---

## 1. Offline-First Architecture

### 1.1 Philosophy

**Offline-first means the app works without network connectivity**. All data is cached locally, and synchronization happens transparently when connectivity is restored.

```
┌─────────────────────────────────────────────────────────────────┐
│                     OFFLINE-FIRST LAYER MODEL                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │                   UI LAYER (React)                         │ │
│  │  - Always reads from local state                           │ │
│  │  - Optimistic UI updates                                   │ │
│  │  - Loading states only for initial data                    │ │
│  └───────────────────────┬───────────────────────────────────┘ │
│                         │                                       │
│  ┌───────────────────────▼───────────────────────────────────┐ │
│  │                 STATE LAYER (Redux)                        │ │
│  │  - Single source of truth                                  │ │
│  │  - Normalized data structure                               │ │
│  │  - Pending operations queue                                │ │
│  └───────────────────────┬───────────────────────────────────┘ │
│                         │                                       │
│  ┌───────────────────────▼───────────────────────────────────┐ │
│  │              SYNC LAYER (Sync Manager)                     │ │
│  │  - Conflict detection & resolution                         │ │
│  │  - Operation queue management                              │ │
│  │  - Sync orchestrator                                       │ │
│  └──────┬────────────────────────────────┬───────────────────┘ │
│         │                                │                      │
│  ┌──────▼──────────┐            ┌────────▼──────────┐         │
│  │  LOCAL STORAGE  │            │   NETWORK LAYER    │         │
│  │  (AsyncStorage) │            │   (API Client)     │         │
│  │  - IndexedDB    │            │   - RTK Query      │         │
│  │  - MMKV (fast)  │            │   - WebSocket      │         │
│  └─────────────────┘            └───────────────────┘         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Data Ownership Model

```
┌────────────────────────────────────────────────────────────────┐
│                     DATA OWNERSHIP STRATEGY                     │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  SERVER-OWNED DATA                    CLIENT-OWNED DATA        │
│  ┌─────────────────────┐              ┌─────────────────────┐  │
│  │ • Trip definitions  │              │ • Draft messages    │  │
│  │ • Customer profiles │              │ • UI preferences    │  │
│  │ • Agency settings   │              │ • Filter states     │  │
│  │ • Pricing data      │              │ • Local notes       │  │
│  │ • Documents         │              │ • Analytics cache   │  │
│  └─────────────────────┘              └─────────────────────┘  │
│         │                                      │                │
│         │ Read-only (mostly)                   │                │
│         │ Changes require API                  │ Never synced   │
│         │ Optimistic updates allowed           │                │
│                                                                 │
│  SHARED DATA (bidirectional sync, conflict resolution)          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ • Agent status (online/offline)                         │   │
│  │ • Trip assignments                                      │   │
│  │ • Message read receipts                                 │   │
│  │ • Quick actions (archive, label)                        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 1.3 TypeScript Types

```typescript
// Data ownership classification
enum DataOwnership {
  SERVER_OWNED = 'SERVER_OWNED',      // Authoritative on server
  CLIENT_OWNED = 'CLIENT_OWNED',      // Never synced
  SHARED = 'SHARED',                   // Bidirectional sync
}

interface SyncMetadata {
  ownership: DataOwnership;
  lastSyncAt: number;
  version: number;
  pendingChanges: boolean;
  conflictResolution?: 'server-wins' | 'client-wins' | 'manual';
}

// Sync state for each entity
interface SyncState {
  id: string;
  entityType: string;
  syncStatus: 'synced' | 'pending' | 'conflict' | 'error';
  localVersion: number;
  serverVersion: number;
  lastSyncAttempt: number;
  retryCount: number;
  error?: SyncError;
}

// Pending operation queue
interface PendingOperation {
  id: string;
  type: 'create' | 'update' | 'delete';
  entityType: string;
  entityId: string;
  payload: any;
  createdAt: number;
  retryCount: number;
  priority: 'high' | 'normal' | 'low';
}
```

---

## 2. Data Synchronization Strategies

### 2.1 Sync Strategies Comparison

```
┌────────────────────────────────────────────────────────────────────┐
│                      SYNC STRATEGY COMPARISON                      │
├─────────────────┬──────────────┬──────────────┬────────────────────┤
│ Strategy        │ Latency      │ Bandwidth    │ Use Case           │
├─────────────────┼──────────────┼──────────────┼────────────────────┤
│ Real-time (WS)  │ Instant      │ High         │ Chat, assignments  │
│ Polling         │ Periodic     │ Medium       │ Status updates     │
│ Pull-to-Refresh │ On-demand    │ Low          │ Manual refresh     │
│ Background Sync │ Opportunistic│ Medium       │ Large datasets     │
│ Delta Sync      │ Variable     │ Very Low     │ Incremental changes│
└─────────────────┴──────────────┴──────────────┴────────────────────┘
```

### 2.2 Delta Sync Implementation

```typescript
// Delta sync: only transfer changed data
interface DeltaSyncRequest {
  lastSyncTimestamp: number;
  entityTypes: string[];
  clientVersion: string;
}

interface DeltaSyncResponse {
  changes: EntityChange[];
  deletions: EntityDeletion[];
  conflicts: SyncConflict[];
  serverTimestamp: number;
}

interface EntityChange {
  entityType: string;
  entityId: string;
  operation: 'create' | 'update';
  data: any;
  version: number;
  modifiedAt: number;
}

interface EntityDeletion {
  entityType: string;
  entityId: string;
  version: number;
}

// Delta sync manager
class DeltaSyncManager {
  private lastSyncTimestamp: Map<string, number> = new Map();

  async performDeltaSync(entityTypes: string[]): Promise<void> {
    const requests = entityTypes.map(type => ({
      lastSyncTimestamp: this.lastSyncTimestamp.get(type) || 0,
      entityTypes: [type],
      clientVersion: APP_VERSION,
    }));

    const response = await api.post('/sync/delta', requests);

    await this.processChanges(response.changes);
    await this.processDeletions(response.deletions);
    await this.handleConflicts(response.conflicts);

    // Update timestamps
    response.changes.forEach(change => {
      this.lastSyncTimestamp.set(
        change.entityType,
        Math.max(this.lastSyncTimestamp.get(change.entityType) || 0, change.modifiedAt)
      );
    });
  }

  private async processChanges(changes: EntityChange[]): Promise<void> {
    for (const change of changes) {
      const { entityType, entityId, operation, data, version } = change;

      if (operation === 'create') {
        await this.localStore.insert(entityType, entityId, data);
      } else {
        const existing = await this.localStore.get(entityType, entityId);
        if (existing && existing.version < version) {
          await this.localStore.update(entityType, entityId, {
            ...data,
            version,
          });
        }
      }
    }
  }
}
```

### 2.3 Sync Priority System

```typescript
// Prioritize what to sync first
enum SyncPriority {
  CRITICAL = 0,    // User-initiated actions, payments
  HIGH = 1,        // Messages, assignments
  NORMAL = 2,      // Trip updates, status changes
  LOW = 3,         // Analytics, telemetry
  BACKGROUND = 4,  // Prefetch, caching
}

interface PrioritizedSyncOperation {
  operation: PendingOperation;
  priority: SyncPriority;
  deadline?: number;  // Skip if not synced by this time
}

class SyncQueue {
  private queue: PrioritizedSyncOperation[] = [];

  enqueue(operation: PendingOperation, priority: SyncPriority): void {
    this.queue.push({ operation, priority });
    this.sortQueue();
  }

  private sortQueue(): void {
    this.queue.sort((a, b) => {
      // First by priority
      if (a.priority !== b.priority) {
        return a.priority - b.priority;
      }
      // Then by deadline (if any)
      if (a.deadline && b.deadline) {
        return a.deadline - b.deadline;
      }
      if (a.deadline) return -1;
      if (b.deadline) return 1;
      // Finally by creation time
      return a.operation.createdAt - b.operation.createdAt;
    });
  }

  dequeue(): PrioritizedSyncOperation | undefined {
    return this.queue.shift();
  }

  get queuedCount(): number {
    return this.queue.length;
  }
}
```

---

## 3. Conflict Resolution

### 3.1 Conflict Detection

```
┌────────────────────────────────────────────────────────────────┐
│                    CONFLICT DETECTION MODEL                     │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Version Vector Comparison:                                     │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  Server Version     Client Version      Resolution         │ │
│  │  ──────────────     ──────────────     ──────────         │ │
│  │       v5                v5            No conflict         │ │
│  │       v5                v4            Server wins (stale)  │ │
│  │       v5                v6            CONFLICT!            │ │
│  │       v5                v5            CONFLICT!            │ │
│  │                        (different data)                    │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│  Conflict Scenarios:                                            │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  1. Same field modified differently                        │ │
│  │  2. Concurrent modifications to related entities            │ │
│  │  3. Delete vs update conflict                              │ │
│  │  4. Constraint violation (duplicate, reference)             │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 3.2 Resolution Strategies

```typescript
enum ConflictResolutionStrategy {
  SERVER_WINS = 'server_wins',
  CLIENT_WINS = 'client_wins',
  LAST_WRITE_WINS = 'last_write_wins',
  MERGE = 'merge',
  MANUAL = 'manual',
}

interface ConflictResolution {
  strategy: ConflictResolutionStrategy;
  fieldResolutions?: Record<string, ConflictResolutionStrategy>;
  mergeFunction?: (local: any, remote: any) => any;
}

// Field-level merge example
const tripMergeStrategies: Record<string, ConflictResolution> = {
  // Immutable fields: server always wins
  createdAt: { strategy: ConflictResolutionStrategy.SERVER_WINS },
  createdBy: { strategy: ConflictResolutionStrategy.SERVER_WINS },
  id: { strategy: ConflictResolutionStrategy.SERVER_WINS },

  // Single-writer fields: last write wins
  status: { strategy: ConflictResolutionStrategy.LAST_WRITE_WINS },
  assignedTo: { strategy: ConflictResolutionStrategy.LAST_WRITE_WINS },

  // Mergeable fields: custom merge
  tags: {
    strategy: ConflictResolutionStrategy.MERGE,
    mergeFunction: (local, remote) => ({
      tags: [...new Set([...local.tags, ...remote.tags])],
    }),
  },

  // Array append: client adds to server list
  notes: {
    strategy: ConflictResolutionStrategy.MERGE,
    mergeFunction: (local, remote) => ({
      notes: [...remote.notes, ...local.notes.filter(
        ln => !remote.notes.some(rn => rn.id === ln.id)
      )],
    }),
  },

  // Critical fields: manual resolution required
  totalPrice: { strategy: ConflictResolutionStrategy.MANUAL },
  paymentStatus: { strategy: ConflictResolutionStrategy.MANUAL },
};

// Conflict resolver
class ConflictResolver {
  async resolve(
    entityType: string,
    localData: any,
    serverData: any,
    strategies: Record<string, ConflictResolution>
  ): Promise<any> {
    const resolution = { ...serverData };
    const conflicts: string[] = [];

    for (const [field, localValue] of Object.entries(localData)) {
      const serverValue = serverData[field];
      const strategy = strategies[field];

      if (!strategy || localValue === serverValue) continue;

      switch (strategy.strategy) {
        case ConflictResolutionStrategy.SERVER_WINS:
          // Keep server value (already set)
          break;

        case ConflictResolutionStrategy.CLIENT_WINS:
          resolution[field] = localValue;
          break;

        case ConflictResolutionStrategy.LAST_WRITE_WINS:
          // Compare timestamps
          const localTs = localData.modifiedAt || 0;
          const serverTs = serverData.modifiedAt || 0;
          resolution[field] = localTs > serverTs ? localValue : serverValue;
          break;

        case ConflictResolutionStrategy.MERGE:
          if (strategy.mergeFunction) {
            const merged = strategy.mergeFunction(localData, serverData);
            Object.assign(resolution, merged);
          }
          break;

        case ConflictResolutionStrategy.MANUAL:
          conflicts.push(field);
          break;
      }
    }

    if (conflicts.length > 0) {
      // Store for manual resolution
      await this.conflictStore.saveConflict({
        entityType,
        entityId: localData.id,
        conflicts,
        localData,
        serverData,
      });
      throw new ManualResolutionRequiredError(conflicts);
    }

    return resolution;
  }
}
```

### 3.3 Conflict UI

```typescript
// Conflict resolution UI component
interface ConflictDialogProps {
  entityType: string;
  localData: any;
  serverData: any;
  conflicts: string[];
  onResolve: (resolution: any) => void;
}

export const ConflictResolutionDialog: React.FC<ConflictDialogProps> = ({
  entityType, localData, serverData, conflicts, onResolve
}) => {
  const [selectedValues, setSelectedValues] = useState<Record<string, 'local' | 'server'>>({});

  return (
    <Dialog>
      <DialogTitle>Sync Conflict — {entityType}</DialogTitle>
      <DialogContent>
        <Typography>
          This {entityType.toLowerCase()} was modified on another device.
          Choose which version to keep for each field.
        </Typography>

        {conflicts.map(field => (
          <ConflictField
            key={field}
            fieldName={field}
            localValue={localData[field]}
            serverValue={serverData[field]}
            selected={selectedValues[field]}
            onSelect={(version) => setSelectedValues(prev => ({
              ...prev,
              [field]: version
            }))}
          />
        ))}
      </DialogContent>
      <DialogActions>
        <Button onClick={() => onResolve(buildResolution(selectedValues, localData, serverData))}>
          Resolve
        </Button>
      </DialogActions>
    </Dialog>
  );
};
```

---

## 4. Background Sync

### 4.1 Platform Capabilities

```
┌────────────────────────────────────────────────────────────────────┐
│                    BACKGROUND SYNC PLATFORMS                       │
├─────────────────┬─────────────────────────┬────────────────────────┤
│ Platform        │ Mechanism               │ Limitations            │
├─────────────────┼─────────────────────────┼────────────────────────┤
│ iOS             │ Background Tasks API     │ ~30 sec, limited calls │
│                 │ BGTaskScheduler          │ per day                │
├─────────────────┼─────────────────────────┼────────────────────────┤
│ Android         │ WorkManager             │ 10-15 min minimum      │
│                 │ (Doze-compatible)       │ interval               │
├─────────────────┼─────────────────────────┼────────────────────────┤
│ React Native    │ react-native-background │ Cross-platform         │
│                 │ tasks / Expo            │ abstraction            │
└─────────────────┴─────────────────────────┴────────────────────────┘
```

### 4.2 Background Sync Implementation

```typescript
// Background sync scheduler
import * as BackgroundFetch from 'expo-background-fetch';
import * as TaskManager from 'expo-task-manager';

const BACKGROUND_SYNC_TASK = 'BACKGROUND_SYNC_TASK';

// Define the task
TaskManager.defineTask(BACKGROUND_SYNC_TASK, async () => {
  try {
    const syncManager = SyncManager.getInstance();
    const result = await syncManager.syncPendingOperations();

    if (result === 'completed') {
      return BackgroundFetch.BackgroundFetchResult.NewData;
    }
    return BackgroundFetch.BackgroundFetchResult.NoData;
  } catch (error) {
    return BackgroundFetch.BackgroundFetchResult.Failed;
  }
});

// Register the task
async function registerBackgroundSync(): Promise<void> {
  const isRegistered = await TaskManager.isTaskRegisteredAsync(BACKGROUND_SYNC_TASK);

  if (!isRegistered) {
    await BackgroundFetch.registerTaskAsync(BACKGROUND_SYNC_TASK, {
      minimumInterval: 15 * 60 * 1000, // 15 minutes
      stopOnTerminate: false,
      startOnBoot: true,
    });
  }
}

// Sync manager
class SyncManager {
  private syncQueue: SyncQueue;

  async syncPendingOperations(): Promise<'completed' | 'more' | 'error'> {
    const operations = await this.syncQueue.getAll();

    if (operations.length === 0) {
      return 'completed';
    }

    let successCount = 0;
    let failCount = 0;

    for (const op of operations) {
      try {
        await this.executeOperation(op);
        await this.syncQueue.remove(op.id);
        successCount++;
      } catch (error) {
        failCount++;
        await this.syncQueue.updateRetryCount(op.id, op.retryCount + 1);
      }
    }

    const remaining = await this.syncQueue.getAll();
    return remaining.length === 0 ? 'completed' : 'more';
  }

  private async executeOperation(operation: PrioritizedSyncOperation): Promise<void> {
    const { type, entityType, entityId, payload } = operation.operation;

    switch (type) {
      case 'create':
        await api.post(`/${entityType}`, payload);
        break;
      case 'update':
        await api.patch(`/${entityType}/${entityId}`, payload);
        break;
      case 'delete':
        await api.delete(`/${entityType}/${entityId}`);
        break;
    }
  }
}
```

### 4.3 Sync Throttling

```typescript
// Prevent excessive sync calls
class SyncThrottler {
  private minInterval: number = 5000; // 5 seconds minimum
  private lastSync: Map<string, number> = new Map();
  private scheduledSyncs: Map<string, NodeJS.Timeout> = new Map();

  canSync(entityType: string): boolean {
    const lastSyncTime = this.lastSync.get(entityType) || 0;
    return Date.now() - lastSyncTime >= this.minInterval;
  }

  async syncWithThrottle(
    entityType: string,
    syncFn: () => Promise<void>
  ): Promise<void> {
    if (!this.canSync(entityType)) {
      // Schedule for later
      this.scheduleSync(entityType, syncFn);
      return;
    }

    await syncFn();
    this.lastSync.set(entityType, Date.now());
  }

  private scheduleSync(entityType: string, syncFn: () => Promise<void>): void {
    const existing = this.scheduledSyncs.get(entityType);
    if (existing) {
      clearTimeout(existing);
    }

    const delay = this.minInterval - (Date.now() - (this.lastSync.get(entityType) || 0));
    const timeout = setTimeout(() => syncFn(), delay);

    this.scheduledSyncs.set(entityType, timeout);
  }
}
```

---

## 5. Cache Management

### 5.1 Cache Strategy

```
┌────────────────────────────────────────────────────────────────────┐
│                         CACHE STRATEGY                             │
├─────────────────┬─────────────────────────┬────────────────────────┤
│ Data Type       │ Storage                 │ TTL / Size Limit       │
├─────────────────┼─────────────────────────┼────────────────────────┤
│ Trip List       │ AsyncStorage + Memory  │ 5 min / 100 items      │
│ Trip Detail     │ AsyncStorage + Memory  │ 30 min / 50 items      │
│ Customer Data   │ AsyncStorage           │ 1 hour / unlimited     │
│ Pricing Data    │ Memory only            │ 1 min / 20 queries     │
│ Documents       │ File System             │ 7 days / 100 MB        │
│ Images          │ File System (cached)    │ 30 days / 500 MB       │
└─────────────────┴─────────────────────────┴────────────────────────┘
```

### 5.2 Cache Implementation

```typescript
// LRU Cache for memory
class LRUCache<T> {
  private cache: Map<string, { value: T; expiry: number }>;
  private maxSize: number;

  constructor(maxSize: number) {
    this.cache = new Map();
    this.maxSize = maxSize;
  }

  get(key: string): T | undefined {
    const entry = this.cache.get(key);
    if (!entry) return undefined;

    if (Date.now() > entry.expiry) {
      this.cache.delete(key);
      return undefined;
    }

    // Move to end (most recently used)
    this.cache.delete(key);
    this.cache.set(key, entry);
    return entry.value;
  }

  set(key: string, value: T, ttl: number): void {
    // Evict oldest if at capacity
    if (this.cache.size >= this.maxSize && !this.cache.has(key)) {
      const firstKey = this.cache.keys().next().value;
      this.cache.delete(firstKey);
    }

    this.cache.set(key, {
      value,
      expiry: Date.now() + ttl,
    });
  }

  clear(): void {
    this.cache.clear();
  }
}

// Persistent cache with AsyncStorage
class PersistentCache {
  private prefix: string;
  private memoryCache: LRUCache<any>;

  constructor(prefix: string, memorySize: number = 50) {
    this.prefix = prefix;
    this.memoryCache = new LRUCache(memorySize);
  }

  async get<T>(key: string): Promise<T | undefined> {
    // Check memory first
    const memValue = this.memoryCache.get<T>(key);
    if (memValue) return memValue;

    // Check persistent storage
    try {
      const fullKey = `${this.prefix}:${key}`;
      const item = await AsyncStorage.getItem(fullKey);
      if (!item) return undefined;

      const { value, expiry } = JSON.parse(item);
      if (Date.now() > expiry) {
        await AsyncStorage.removeItem(fullKey);
        return undefined;
      }

      // Populate memory cache
      this.memoryCache.set(key, value, 60000); // 1 min in memory
      return value;
    } catch (error) {
      console.error('Cache read error:', error);
      return undefined;
    }
  }

  async set<T>(key: string, value: T, ttl: number): Promise<void> {
    const expiry = Date.now() + ttl;

    // Write to memory
    this.memoryCache.set(key, value, Math.min(ttl, 60000));

    // Write to persistent storage
    try {
      const fullKey = `${this.prefix}:${key}`;
      await AsyncStorage.setItem(fullKey, JSON.stringify({ value, expiry }));
    } catch (error) {
      console.error('Cache write error:', error);
    }
  }

  async invalidate(pattern?: string): Promise<void> {
    if (pattern) {
      const keys = await AsyncStorage.getAllKeys();
      const matchingKeys = keys.filter(k => k.startsWith(`${this.prefix}:${pattern}`));
      await AsyncStorage.multiRemove(matchingKeys);
    } else {
      this.memoryCache.clear();
    }
  }
}
```

### 5.3 Cache Invalidation

```typescript
// Invalidation strategies
enum InvalidationStrategy {
  TIME_BASED = 'time_based',
  EVENT_BASED = 'event_based',
  VERSION_BASED = 'version_based',
  MANUAL = 'manual',
}

// Event-based invalidation
class CacheInvalidator {
  private persistentCache: PersistentCache;
  private invalidationRules: Map<string, InvalidationRule[]> = new Map();

  constructor(persistentCache: PersistentCache) {
    this.persistentCache = persistentCache;
    this.setupRules();
  }

  private setupRules(): void {
    // Trip invalidation rules
    this.addRule('trip', {
      eventType: 'trip_updated',
      invalidate: (event) => [
        `trip:${event.tripId}`,
        `trip_list:*`,
      ],
    });

    // Message invalidation rules
    this.addRule('message', {
      eventType: 'new_message',
      invalidate: (event) => [
        `conversation:${event.conversationId}`,
        `message_list:${event.conversationId}`,
      ],
    });
  }

  async handleEvent(event: SyncEvent): Promise<void> {
    const rules = this.invalidationRule.get(event.type) || [];

    for (const rule of rules) {
      const keysToInvalidate = rule.invalidate(event);
      for (const key of keysToInvalidate) {
        await this.persistentCache.invalidate(key);
      }
    }
  }
}
```

---

## 6. Network State Handling

### 6.1 Connectivity Detection

```typescript
import NetInfo from '@react-native-community/netinfo';

class NetworkMonitor {
  private listeners: Set<NetworkStateListener> = new Set();
  private currentState: NetworkState | null = null;

  async startMonitoring(): Promise<void> {
    // Initial state
    this.currentState = await NetInfo.fetch();

    // Subscribe to changes
    NetInfo.addEventListener(state => {
      this.currentState = state;
      this.notifyListeners(state);
    });
  }

  subscribe(listener: NetworkStateListener): () => void {
    this.listeners.add(listener);
    if (this.currentState) {
      listener(this.currentState);
    }
    return () => this.listeners.delete(listener);
  }

  private notifyListeners(state: NetworkState): void {
    this.listeners.forEach(listener => listener(state));
  }

  isOnline(): boolean {
    return this.currentState?.isConnected === true;
  }

  getConnectionType(): string {
    return this.currentState?.type || 'none';
  }
}

interface NetworkState {
  isConnected: boolean;
  type: string;
  isInternetReachable?: boolean;
}

type NetworkStateListener = (state: NetworkState) => void;
```

### 6.2 Online/Offline Transitions

```typescript
// Handle connectivity changes
class ConnectivityHandler {
  private networkMonitor: NetworkMonitor;
  private syncManager: SyncManager;

  constructor() {
    this.networkMonitor = new NetworkMonitor();
    this.syncManager = SyncManager.getInstance();
  }

  initialize(): void {
    this.networkMonitor.startMonitoring();
    this.networkMonitor.subscribe(this.handleNetworkChange.bind(this));
  }

  private async handleNetworkChange(state: NetworkState): Promise<void> {
    if (state.isConnected) {
      await this.onReconnect();
    } else {
      await this.onDisconnect();
    }
  }

  private async onReconnect(): Promise<void> {
    // Show reconnecting indicator
    showToast('Reconnecting...', 'info');

    try {
      // Sync pending operations
      await this.syncManager.syncPendingOperations();

      // Refresh current data
      await this.syncManager.performDeltaSync(['trips', 'messages']);

      showToast('Back online', 'success');
    } catch (error) {
      showToast('Sync failed. Will retry later.', 'warning');
    }
  }

  private async onDisconnect(): Promise<void> {
    // Show offline indicator
    showToast('You are offline. Changes will sync when connected.', 'warning');

    // Switch to offline mode
    store.dispatch(setOfflineMode(true));
  }
}
```

### 6.3 Request Retry with Exponential Backoff

```typescript
class RetryableAPIClient {
  private maxRetries = 3;
  private baseDelay = 1000;

  async fetchWithRetry(
    url: string,
    options: RequestInit = {},
    attempt: number = 0
  ): Promise<Response> {
    try {
      const response = await fetch(url, options);

      if (!response.ok && this.isRetryableStatus(response.status) && attempt < this.maxRetries) {
        throw new RetryableError(`HTTP ${response.status}`);
      }

      return response;
    } catch (error) {
      if (attempt < this.maxRetries && this.isRetryableError(error)) {
        const delay = this.calculateBackoff(attempt);
        await new Promise(resolve => setTimeout(resolve, delay));
        return this.fetchWithRetry(url, options, attempt + 1);
      }
      throw error;
    }
  }

  private isRetryableStatus(status: number): boolean {
    return [408, 429, 500, 502, 503, 504].includes(status);
  }

  private isRetryableError(error: any): boolean {
    return error instanceof TypeError || // Network error
           error instanceof RetryableError;
  }

  private calculateBackoff(attempt: number): number {
    // Exponential backoff with jitter
    const exponentialDelay = this.baseDelay * Math.pow(2, attempt);
    const jitter = Math.random() * 1000;
    return exponentialDelay + jitter;
  }
}
```

---

## 7. Implementation Patterns

### 7.1 RTK Query with Offline Support

```typescript
import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';

// Offline-aware API base query
const offlineBaseQuery = async (args: any, api: any, extraOptions: any) => {
  const isOnline = api.getState().network.isOnline;

  if (!isOnline) {
    // Queue the operation for later sync
    const syncManager = SyncManager.getInstance();
    await syncManager.queueOperation({
      type: 'api_call',
      args,
      timestamp: Date.now(),
    });

    return {
      data: null,
      meta: { queued: true, offline: true },
    };
  }

  // Normal fetch when online
  const baseQuery = fetchBaseQuery({
    baseUrl: API_BASE_URL,
    prepareHeaders: (headers) => {
      const token = api.getState().auth.token;
      if (token) {
        headers.set('authorization', `Bearer ${token}`);
      }
      return headers;
    },
  });

  return baseQuery(args, api, extraOptions);
};

// Create API with offline support
export const api = createApi({
  reducerPath: 'api',
  baseQuery: offlineBaseQuery,
  tagTypes: ['Trip', 'Message', 'Customer'],
  endpoints: (builder) => ({
    getTrips: builder.query<Trip[], void>({
      query: () => '/trips',
      providesTags: ['Trip'],
    }),
    updateTrip: builder.mutation<Trip, Partial<Trip> & { id: string }>({
      query: ({ id, ...patch }) => ({
        url: `/trips/${id}`,
        method: 'PATCH',
        body: patch,
      }),
      invalidatesTags: (result, error, { id }) => [{ type: 'Trip', id }],
    }),
  }),
});
```

### 7.2 Redux Persist Configuration

```typescript
import { persistStore, persistReducer } from 'redux-persist';
import AsyncStorage from '@react-native-async-storage/async-storage';

// Persist configuration
const persistConfig = {
  key: 'root',
  storage: AsyncStorage,
  whitelist: [
    'auth',        // Keep user logged in
    'trips',       // Offline trip access
    'drafts',      // Preserve draft messages
    'preferences', // User settings
  ],
  blacklist: [
    'api',         // API cache managed by RTK Query
    'network',     // Network state is transient
    'ui',          // UI state should reset
  ],
  // Migration support
  version: 1,
  migrate: (state: any) => {
    // Handle version migrations
    const migratedState = { ...state };
    // Apply migrations...
    return Promise.resolve(migratedState);
  },
};

const persistedReducer = persistReducer(persistConfig, rootReducer);

export const store = configureStore({
  reducer: persistedReducer,
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: [FLUSH, REHYDRATE, PAUSE, PERSIST, PURGE, REGISTER],
      },
    }).concat(api.middleware),
});

export const persistor = persistStore(store);
```

---

## 8. Testing & Monitoring

### 8.1 Sync Testing Scenarios

```typescript
describe('Offline Sync', () => {
  it('should queue operations when offline', async () => {
    // Go offline
    mockNetworkOffline();

    // Perform action
    await store.dispatch(updateTrip({ id: '1', status: 'confirmed' }));

    // Verify queued
    const queue = await SyncQueue.getAll();
    expect(queue).toHaveLength(1);
  });

  it('should sync queued operations when online', async () => {
    // Queue operation while offline
    mockNetworkOffline();
    await store.dispatch(updateTrip({ id: '1', status: 'confirmed' }));

    // Go online
    mockNetworkOnline();

    // Wait for sync
    await waitFor(() => expect(SyncQueue.getAll()).resolves.toHaveLength(0));

    // Verify server updated
    const trip = await api.get('/trips/1');
    expect(trip.status).toBe('confirmed');
  });

  it('should detect and resolve conflicts', async () => {
    // Client modification
    await store.dispatch(updateTrip({ id: '1', notes: 'Client note' }));

    // Simultaneous server modification
    mockServerUpdate({ id: '1', notes: 'Server note' });

    // Go online
    mockNetworkOnline();
    await syncManager.performDeltaSync(['trips']);

    // Verify conflict detected
    const conflicts = await ConflictStore.getConflicts();
    expect(conflicts).toHaveLength(1);
  });
});
```

### 8.2 Sync Health Monitoring

```typescript
interface SyncHealthMetrics {
  lastSuccessfulSync: number;
  lastFailedSync: number | null;
  pendingOperationsCount: number;
  conflictCount: number;
  averageSyncDuration: number;
  errorRate: number;
}

class SyncHealthMonitor {
  private metrics: SyncHealthMetrics = {
    lastSuccessfulSync: 0,
    lastFailedSync: null,
    pendingOperationsCount: 0,
    conflictCount: 0,
    averageSyncDuration: 0,
    errorRate: 0,
  };

  recordSyncSuccess(duration: number): void {
    this.metrics.lastSuccessfulSync = Date.now();
    this.metrics.averageSyncDuration = this.rollingAverage(
      this.metrics.averageSyncDuration,
      duration
    );
    this.metrics.errorRate = this.calculateErrorRate();
  }

  recordSyncFailure(): void {
    this.metrics.lastFailedSync = Date.now();
    this.metrics.errorRate = this.calculateErrorRate();
  }

  getHealthStatus(): 'healthy' | 'degraded' | 'unhealthy' {
    const timeSinceLastSync = Date.now() - this.metrics.lastSuccessfulSync;

    if (this.metrics.errorRate > 0.5 || timeSinceLastSync > 3600000) {
      return 'unhealthy';
    }
    if (this.metrics.errorRate > 0.1 || timeSinceLastSync > 1800000) {
      return 'degraded';
    }
    return 'healthy';
  }

  private rollingAverage(current: number, newSample: number): number {
    return (current * 9 + newSample) / 10;
  }

  private calculateErrorRate(): number {
    // Calculate based on recent sync history
    // Implementation depends on tracking recent attempts
    return 0;
  }
}
```

---

## Summary

The sync system enables a seamless offline-first experience:

| Component | Purpose |
|-----------|---------|
| **Offline-First Architecture** | App works without network, syncs transparently |
| **Delta Sync** | Minimize bandwidth, sync only changes |
| **Conflict Resolution** | Handle concurrent modifications gracefully |
| **Background Sync** | Keep data fresh without user intervention |
| **Cache Management** | Fast data access, intelligent invalidation |
| **Network Monitoring** | Detect connectivity, adapt behavior |

**Key Takeaways:**
- Cache all user-accessible data locally
- Queue operations when offline, sync when online
- Detect conflicts using version vectors
- Provide field-level merge strategies
- Monitor sync health and error rates

---

**Related:** [04: Notifications Deep Dive](./MOBILE_APP_04_NOTIFICATIONS_DEEP_DIVE.md) → Push notifications and in-app messaging
