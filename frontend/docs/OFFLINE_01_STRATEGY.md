# Offline & Low-Connectivity Mode — Strategy

> Research document for offline-first architecture strategy, connectivity constraints in Indian travel, and offline capability prioritization.

---

## Key Questions

1. **What travel agency workflows must work offline?**
2. **What are the connectivity constraints for Indian travel agents?**
3. **What offline architecture patterns apply (PWA, local-first, CRDT)?**
4. **How do we prioritize features for offline support?**
5. **What's the sync strategy when connectivity resumes?**

---

## Research Areas

### Connectivity Landscape

```typescript
interface ConnectivityLandscape {
  agentScenarios: AgentConnectivity[];
  customerScenarios: CustomerConnectivity[];
  constraints: ConnectivityConstraint[];
}

// Agent connectivity scenarios:
//
// URBAN OFFICE (Primary):
// Connectivity: Stable broadband (50-100 Mbps)
// Reliability: 99%+ uptime
// Impact: Full platform access, no offline needed
// Users: 40% of agents
//
// CO-WORKING / CAFE:
// Connectivity: Shared WiFi, inconsistent (5-20 Mbps)
// Reliability: 90% (drops during peak hours)
// Impact: Occasional disconnections during heavy use
// Users: 15% of agents (freelancers, remote workers)
//
// HOME OFFICE (Tier 2/3 cities):
// Connectivity: Broadband or mobile hotspot (10-30 Mbps)
// Reliability: 85-95% (power cuts, ISP issues)
// Impact: Intermittent connectivity, especially during monsoon
// Users: 25% of agents
//
// ON-THE-GO (Traveling agents):
// Connectivity: Mobile data (4G, sometimes 3G)
// Reliability: 60-80% (train travel, remote locations)
// Impact: Frequently disconnected, need offline trip access
// Users: 15% of agents
//
// TRADE SHOW / EVENT:
// Connectivity: Event WiFi (congested) or mobile data
// Reliability: 50-70% (high congestion, thousands of users)
// Impact: Need to capture leads and show itineraries offline
// Users: 5% of agents (events, weddings)

// Customer connectivity scenarios:
//
// PRE-TRIP (Home):
// Connectivity: Good (WiFi/broadband)
// Activity: Researching, planning, booking
//
// DURING TRIP (Traveling):
// Connectivity: Variable
//   - Airport/Hotel WiFi: Good but captive portal friction
//   - Flight: No internet (Air India WiFi rare)
//   - Train: 4G but tunnel dead zones
//   - Remote destination: No signal (hills, islands, forests)
//   - International: Expensive roaming, limited data
// Activity: Viewing itinerary, accessing documents, contacting agent
//
// POST-TRIP (Home):
// Connectivity: Good
// Activity: Providing feedback, sharing photos, booking next trip

// India-specific connectivity constraints:
// 1. Mobile data is primary internet for 60%+ of users
// 2. Jio/Airtel 4G covers 90%+ of urban areas, 70% rural
// 3. 5G rolling out but limited coverage (metro cities)
// 4. WiFi penetration: <10% of households (vs 80%+ mobile data)
// 5. Power cuts affect broadband reliability (Tier 2/3 cities)
// 6. International roaming: Expensive, often disabled
// 7. Hotel WiFi: Common but often slow/unreliable
// 8. Speed: Average mobile download 50 Mbps (urban), 15 Mbps (rural)

// Offline capability priority matrix:
// Priority 1 (Must work offline):
// - View downloaded itineraries and vouchers
// - Access customer emergency contacts
// - View trip details (flights, hotels, activities)
// - Access saved customer profiles
// - Compose messages (send when online)
//
// Priority 2 (Should work offline):
// - Search saved trips and customers
// - View destination guides (cached)
// - Create draft trip plans
// - Take notes on customer conversations
// - View pricing templates
//
// Priority 3 (Nice to have offline):
// - Full trip builder
// - Document generation (PDF)
// - Analytics dashboard
// - Commission tracking
```

### Offline Architecture

```typescript
interface OfflineArchitecture {
  pattern: OfflinePattern;
  storage: OfflineStorage;
  sync: SyncStrategy;
  conflictResolution: ConflictResolution;
}

type OfflinePattern =
  | 'cache_first'                      // Serve from cache, update in background
  | 'network_first'                    // Try network, fall back to cache
  | 'stale_while_revalidate'           // Serve stale, fetch fresh simultaneously
  | 'offline_first';                   // Always write locally, sync when connected

// Architecture choice: OFFLINE-FIRST with event sourcing
// - All writes go to local database first
// - Changes queued for sync when online
// - Optimistic UI updates (show as saved immediately)
// - Background sync when connectivity detected
// - Conflict resolution on merge
//
// Why offline-first:
// 1. Indian agents face frequent disconnections
// 2. Train travel = extended offline periods
// 3. Customer meetings in hotels with poor WiFi
// 4. Better perceived performance (instant local reads)
// 5. Graceful degradation rather than hard failure
//
// Technology stack:
// Service Worker (PWA): Caching and background sync
// IndexedDB: Local database for offline data
// CRDT (Conflict-free Replicated Data Types): For conflict resolution
// WebSocket: Real-time sync when connected
// Local-first sync engine: Custom or PowerSync / ElectricSQL

interface OfflineStorage {
  database: LocalDatabase;
  cache: CacheStrategy;
  limits: StorageLimits;
}

// Local database (IndexedDB via Dexie.js or PowerSync):
// Tables replicated locally:
// - trips: All trips where agent is assigned (last 90 days + upcoming)
// - customers: Customers with active trips or recent interactions
// - messages: Recent conversation threads (last 30 days)
// - documents: Generated itineraries, vouchers (PDF blobs)
// - destinations: Popular destinations with cached guides
// - settings: Agent preferences, agency config
//
// Storage limits:
// Mobile app: 200MB local storage
// PWA (desktop): 500MB local storage
// Prioritization when approaching limit:
//   1. Delete oldest cached destinations
//   2. Delete oldest completed trips (>90 days)
//   3. Delete read messages (>30 days)
//   4. Keep active trips and customer profiles until sync
//
// Cache strategy by data type:
// Trip data: Offline-first (local writes, sync on reconnect)
// Customer profiles: Cache-first (read from local, update from server)
// Messages: Offline-first (send queue, sync on reconnect)
// Documents: Cache-first (download when online, available offline)
// Destination guides: Cache-first with periodic refresh
// Search: Local search only when offline (limited results)
// Pricing: Network-only (too volatile to cache meaningfully)
// Analytics: Network-only (requires fresh data)

interface SyncStrategy {
  detection: ConnectivityDetection;
  queue: SyncQueue;
  processing: SyncProcess;
  notification: SyncNotification;
}

// Connectivity detection:
// navigator.onLine: Boolean (unreliable — doesn't detect degraded connectivity)
// Fetch heartbeat: GET /api/health every 30 seconds when "online"
// WebSocket: Connection state monitoring
// Network Information API: connection.effectiveType ('4g', '3g', '2g', 'slow-2g')
//
// Connection quality assessment:
// Great: >10 Mbps, <100ms latency → Full sync, real-time features
// Good: 1-10 Mbps, <500ms latency → Sync with image optimization
// Poor: 0.1-1 Mbps, <2000ms latency → Sync text only, defer media
// Offline: 0 Mbps → Queue all operations, show offline banner

// Sync queue:
// Every local write creates a sync queue entry:
interface SyncQueueEntry {
  id: string;
  entityType: string;                  // "trip", "message", "customer"
  entityId: string;
  operation: 'create' | 'update' | 'delete';
  localTimestamp: Date;
  localData: any;                      // The data to sync
  status: 'pending' | 'syncing' | 'conflicted' | 'failed';
  retries: number;
  priority: SyncPriority;
}

type SyncPriority =
  | 'critical'                         // Messages to customers, booking confirmations
  | 'high'                             // Trip updates, customer profile changes
  | 'normal'                           // Notes, preferences, read status
  | 'low';                             // Analytics events, usage telemetry

// Sync process:
// 1. Connectivity restored → Begin sync
// 2. Process queue in priority order (critical first)
// 3. For each entry:
//    a. Send to server
//    b. Server responds: success / conflict / error
//    c. If conflict → Apply conflict resolution
//    d. If error → Retry (exponential backoff, max 3 retries)
//    e. If max retries exceeded → Mark as failed, notify user
// 4. Update local data with server response (server is truth)
// 5. Notify UI of sync completion
//
// Sync batching:
// Bundle multiple small changes into single API call
// Avoid syncing individual field changes separately
// Batch size: Up to 50 operations per sync request
// Frequency: Every 30 seconds when connected (or on demand)

// Conflict resolution:
// Last-write-wins: Simple but can lose data
// Server-wins: Safe but ignores offline work
// Field-level merge: Best for non-overlapping edits
// CRDT merge: Best for concurrent edits on same field
//
// Recommended: FIELD-LEVEL MERGE with manual resolution fallback
// Example:
// Agent A (offline) updates trip hotel to "Taj Palace"
// Agent B (online) updates trip dates to "Dec 15-20"
// Merge: Both changes kept (different fields)
//
// Agent A (offline) updates trip price to ₹48,000
// Agent B (online) updates trip price to ₹52,000
// Conflict: Same field, different values
// Resolution: Show both versions to agent who syncs last
//   "Your change: ₹48,000 | Server version: ₹52,000
//    [Keep Mine] [Use Server] [Manual Entry]"
```

---

## Open Problems

1. **Sync conflict complexity** — Two agents editing the same trip simultaneously (one offline) creates conflicts. Field-level merge handles most cases but complex objects (itineraries with multiple components) need deeper conflict resolution.

2. **Storage management** — Mobile devices have limited storage. Aggressive caching fills up quickly. Intelligent eviction (LRU with priority) is needed but getting it wrong means critical data is unavailable offline.

3. **Offline search quality** — Local search on cached data is inherently limited. Full-text search on 500+ destinations and 100+ trips in IndexedDB is slower than server-side Meilisearch.

4. **Partial connectivity handling** — "Offline" is binary in most APIs. Real-world connectivity exists on a spectrum: intermittent, degraded, captive portal (connected but not authenticated). Handling each case gracefully adds significant complexity.

5. **Security of offline data** — Locally cached customer data (passports, payment info) on a laptop or phone is a security risk if the device is lost or stolen. Local encryption and remote wipe capability are essential.

---

## Next Steps

- [ ] Design offline-first architecture with local database and sync engine
- [ ] Implement service worker caching strategy for PWA
- [ ] Build sync queue with priority-based processing
- [ ] Create field-level conflict resolution with manual fallback
- [ ] Study offline-first frameworks (PowerSync, ElectricSQL, RxDB, WatermelonDB, PouchDB)
