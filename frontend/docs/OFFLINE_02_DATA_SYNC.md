# Offline & Low-Connectivity Mode — Data Synchronization

> Research document for sync engine design, conflict resolution strategies, data prioritization, and sync state management.

---

## Key Questions

1. **What sync engine architecture handles offline-first data?**
2. **How do CRDTs and operational transforms apply to travel data?**
3. **What's the data prioritization model for sync ordering?**
4. **How do we communicate sync status to users?**
5. **What's the sync recovery strategy after extended offline periods?**

---

## Research Areas

### Sync Engine Architecture

```typescript
interface SyncEngine {
  outbound: OutboundSync;              // Local → Server
  inbound: InboundSync;                // Server → Local
  conflict: ConflictResolution;
  state: SyncState;
}

interface OutboundSync {
  capture: ChangeCapture;
  queue: SyncQueue;
  transform: ChangeTransform;
  transmit: ChangeTransmit;
}

// Change capture — Intercept all local writes:
// Approach: Wrap database operations with sync-aware layer
//
// Agent creates trip update (offline):
// 1. UI dispatches action: updateTrip(tripId, { hotel: "Taj Palace" })
// 2. Local database updated immediately (optimistic)
// 3. Change capture records: {
//      id: "sync_001",
//      entityType: "trip",
//      entityId: "TRV-45678",
//      operation: "update",
//      field: "hotel",
//      oldValue: "Leela Palace",
//      newValue: "Taj Palace",
//      timestamp: "2026-04-28T14:30:00Z",
//      agentId: "agent_005",
//      priority: "high"
//    }
// 4. Change added to sync queue
// 5. UI shows as saved (green checkmark)

// Sync queue management:
interface SyncQueueManager {
  add: (entry: SyncEntry) => void;
  process: () => Promise<SyncResult[]>;
  prioritize: (entries: SyncEntry[]) => SyncEntry[];
  retry: (failedEntry: SyncEntry) => void;
  compact: () => void;                 // Merge multiple edits to same entity
}

// Queue compaction:
// Agent updates trip 3 times while offline:
//   Edit 1: Change hotel → "Taj Palace"
//   Edit 2: Change dates → "Dec 15-20"
//   Edit 3: Change price → "₹48,000"
// Compact into single sync entry:
//   Combined: { hotel: "Taj Palace", dates: "Dec 15-20", price: "₹48,000" }
// Only the final state is synced (saves bandwidth and reduces conflicts)
//
// Compaction rules:
// - Same entity, same session: Always compact
// - Same entity, different sessions: Compact if no conflicting fields
// - Different entities: Never compact (independent sync entries)
// - Delete after create: Remove both (entity never existed on server)
// - Multiple updates: Keep only final state per field

// Change transform:
// Convert local changes to server API format:
// Local change: { tripId: "TRV-45678", field: "hotel", value: "Taj Palace" }
// Server API: PATCH /api/trips/TRV-45678 { hotel: "Taj Palace" }
//
// Transform rules per entity type:
// Trip update: Merge local fields into PATCH request
// Message send: Queue with sendAt timestamp, create POST on sync
// Customer update: Merge fields into PATCH request
// Document generation: Queue for server-side generation on reconnect

// Change transmission:
// When connectivity restored:
// 1. Acquire sync lock (prevent concurrent sync from multiple tabs)
// 2. Process queue in priority order
// 3. Batch small changes (max 50 operations per request)
// 4. Send batch to server
// 5. Process response:
//    - Success: Remove from queue, update local with server state
//    - Conflict: Apply conflict resolution
//    - Error: Increment retry count, re-queue with backoff
// 6. Release sync lock
// 7. Notify UI of sync completion

interface InboundSync {
  subscription: ServerSubscription;
  application: ChangeApplication;
  notification: ChangeNotification;
}

// Server → Local sync (when online):
// Real-time via WebSocket:
// - Server pushes changes made by other agents or customers
// - Changes applied to local database immediately
// - UI updates reactively
//
// Subscription model:
// Agent subscribes to:
// - Their assigned trips (all changes)
// - Their customer conversations (new messages)
// - Agency-wide notifications
// - Booking status changes
//
// Change application:
// Server push: { type: "trip_updated", tripId: "TRV-45678", changes: {...} }
// Local application:
// 1. Check if trip exists locally
// 2. If yes: Apply changes to local record
// 3. If no: Fetch full trip from server, store locally
// 4. If conflict with pending local changes: Queue for resolution
// 5. Notify UI of update

// Sync state machine:
// DISCONNECTED → Queueing changes locally
// CONNECTING → Attempting to establish sync channel
// SYNCING → Processing queued changes
// SYNCED → All changes synced, real-time updates flowing
// CONFLICT → Manual resolution needed
// ERROR → Sync failed, retry scheduled

// Sync state UI indicators:
// 🟢 All synced (green checkmark)
// 🟡 Syncing... (yellow spinner, "3 changes uploading")
// 🔴 Offline (red indicator, "5 changes pending")
// ⚠️ Conflict (yellow warning, "1 conflict needs resolution")
// 🔴 Sync error (red, "Last sync failed 2 min ago, retrying...")
//
// Detailed sync panel (accessible from indicator):
// ┌─────────────────────────────────────────┐
// │  Sync Status                              │
// │                                            │
// │  📤 Pending uploads: 5                     │
// │     - Trip TRV-45678 update (high)         │
// │     - Message to Rajesh (critical)         │
// │     - Customer profile update (normal)     │
// │     - Trip note (low)                      │
// │     - Read status update (low)             │
// │                                            │
// │  📥 Last sync: 2 min ago                   │
// │  📊 Queue size: 23 KB                      │
// │                                            │
// │  [Force Sync Now]                          │
// └─────────────────────────────────────────────┘
```

### Conflict Resolution

```typescript
interface ConflictResolution {
  strategies: ConflictStrategy[];
  autoResolve: AutoResolution;
  manualResolve: ManualResolution;
  escalation: ConflictEscalation;
}

// Conflict scenarios in travel:
//
// SCENARIO 1: Different fields (auto-resolve)
// Agent A (offline): Updates hotel → "Taj Palace"
// Agent B (online): Updates price → "₹48,000"
// Resolution: Merge both (no conflict — different fields)
//
// SCENARIO 2: Same field, different values (manual resolve)
// Agent A (offline): Sets price to ₹48,000
// Agent B (online): Sets price to ₹52,000
// Resolution: Show both versions, let syncing agent choose
//
// SCENARIO 3: Structural conflict (complex)
// Agent A (offline): Removes Day 3 activity, adds Day 4 activity
// Agent B (online): Adds different activity on Day 3
// Resolution: Show both itineraries side by side for merge
//
// SCENARIO 4: Delete conflict
// Agent A (offline): Edits trip details
// Agent B (online): Cancels the trip
// Resolution: Trip cancelled, Agent A's edits discarded
//   (show notification: "Trip was cancelled while you were offline")
//
// SCENARIO 5: Message conflict
// Agent A (offline): Composes message to customer
// Customer (via WhatsApp): Sends message asking to change dates
// Resolution: No conflict — message sent + customer's message received

// Auto-resolution rules:
// Rule 1: Different fields → Merge both
// Rule 2: Structural changes to different sub-entities → Merge both
//   (e.g., change flight vs. change hotel on same trip)
// Rule 3: One side is a delete → Delete wins (data is gone)
// Rule 4: Timestamp-based for non-critical data → Server wins (newer)
// Rule 5: Financial data → Server is truth (prevent discrepancies)
//
// Manual resolution UI:
// ┌─────────────────────────────────────────┐
// │  ⚠️ Sync Conflict                          │
// │                                            │
// │  Trip TRV-45678 — Price                    │
// │                                            │
// │  Your version:      ₹48,000               │
// │  Server version:    ₹52,000               │
// │  Changed by:        Priya (2 hours ago)    │
// │                                            │
// │  [Keep Mine]  [Use Server]  [Enter Custom] │
// │                                            │
// │  Note: Financial data should be verified   │
// │  with the customer before changing.        │
// └─────────────────────────────────────────────┘

// Extended offline recovery:
// If agent is offline for >24 hours:
// 1. On reconnect, don't blindly sync all queued changes
// 2. First, fetch current state of all modified entities from server
// 3. Compare local changes against current server state
// 4. Present a reconciliation dashboard:
//    "You were offline for 3 days. 12 changes need review."
//    - 8 auto-merged (no conflicts)
//    - 3 need your decision (same-field conflicts)
//    - 1 already superseded (server has newer change)
// 5. Agent reviews conflicts and resolves
// 6. Final sync pushes resolved state to server
//
// Sync after extended offline:
// Queue may contain 50+ changes
// Batch processing:
//   - Compact queue first (merge same-entity edits)
//   - Process in dependency order (customer before trip)
//   - Critical first (messages > trip updates > notes)
//   - Show progress: "Syncing 3 of 12 changes..."
```

---

## Open Problems

1. **CRDT overhead** — True CRDTs (Yjs, Automerge) add metadata overhead (2-5x data size) and complexity. For most travel data, field-level merge with manual conflict resolution is simpler and sufficient.

2. **Large file sync** — Itinerary PDFs and passport scans (2-10 MB each) need offline access but syncing them is bandwidth-intensive. Differential sync for PDFs is impractical; full re-download is often required.

3. **Multi-tab sync coordination** — If an agent has the platform open in multiple browser tabs, each tab may have its own sync queue. Coordinating sync across tabs without conflicting requires shared worker or broadcast channel coordination.

4. **Sync during degraded connectivity** — Partial connectivity (3G with high packet loss) is worse than full offline. Sync attempts may partially succeed, leaving data in an inconsistent state. Transactional sync (all-or-nothing per batch) prevents this but reduces throughput.

5. **Testing offline sync** — Reproducing sync conflicts in testing requires simulating concurrent offline edits, which is difficult. Automated conflict simulation tools are needed for confidence in the sync engine.

---

## Next Steps

- [ ] Build sync engine with outbound queue and inbound subscription
- [ ] Implement field-level merge conflict resolution with manual fallback
- [ ] Create queue compaction algorithm for efficient syncing
- [ ] Design extended-offline reconciliation dashboard
- [ ] Study sync engines (PowerSync, ElectricSQL, Firebase Offline, CouchDB/PouchDB, RxDB)
