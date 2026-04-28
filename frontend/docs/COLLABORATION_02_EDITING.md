# Real-Time Collaboration — Concurrent Editing

> Research document for conflict-free editing, operational transforms, and CRDT-based collaboration.

---

## Key Questions

1. **How do we merge concurrent edits to the same trip data?**
2. **What's the right algorithm — OT (Operational Transform) or CRDT?**
3. **How do we handle edits to structured data (not just text)?**
4. **What's the undo/redo model in a collaborative context?**
5. **How do we ensure consistency across all connected clients?**

---

## Research Areas

### Editing Model

```typescript
interface CollabEdit {
  editId: string;
  tripId: string;
  agentId: string;
  timestamp: Date;
  operation: EditOperation;
  baseVersion: number;              // Version this edit is based on
}

type EditOperation =
  | { type: 'set'; path: string; value: unknown; previousValue: unknown }
  | { type: 'array_insert'; path: string; index: number; value: unknown }
  | { type: 'array_remove'; path: string; index: number; removedValue: unknown }
  | { type: 'array_move'; path: string; fromIndex: number; toIndex: number }
  | { type: 'text_insert'; path: string; offset: number; text: string }
  | { type: 'text_delete'; path: string; offset: number; length: number }
  | { type: 'compound'; operations: EditOperation[] };

// Path notation (JSON pointer style):
// "/itinerary/days/0/activities/1/hotel/name" → Set hotel name on day 1
// "/pricing/hotels/0/rooms/0/rate" → Set room rate for first hotel
// "/travelers/0/passport/number" → Set passport number
// "/notes" → Text field (uses text operations)

// Example concurrent edit scenario:
// Agent A: Set hotel name to "Taj Palace Mumbai" (base version 5)
// Agent B: Set hotel name to "Taj Mahal Palace" (base version 5)
// Resolution: Last-write-wins with notification to Agent A
//   OR: Both changes preserved in history, agent can choose
```

### Conflict Resolution

```typescript
interface ConflictResolution {
  strategy: ConflictStrategy;
  resolutionRules: ResolutionRule[];
}

type ConflictStrategy =
  | 'last_write_wins'               // Simplest, newest edit wins
  | 'field_ownership'               // Each field has an owner
  | 'semantic_merge'                // Merge based on field semantics
  | 'manual_resolution';            // Present conflict to users

interface ResolutionRule {
  path: string;                     // JSON path pattern
  strategy: ConflictStrategy;
  priority?: string[];              // Agent IDs with higher priority
  mergeFunction?: string;           // Custom merge logic name
}

// Resolution rules for travel platform:
// "/itinerary/days/*/activities" → semantic_merge (array operations)
// "/pricing/*" → field_ownership (pricing agent owns pricing)
// "/travelers/*/personal" → last_write_wins (personal details)
// "/notes" → manual_resolution (free text, can't auto-merge)
// "/status" → field_ownership (trip owner controls status)
// "/itinerary/days/*/activities/*/bookings" → manual_resolution (bookings are critical)

interface ConflictEvent {
  conflictId: string;
  tripId: string;
  path: string;
  conflictingEdits: CollabEdit[];
  detectedAt: Date;
  autoResolution?: AutoResolution;
  requiresManualResolution: boolean;
}

interface AutoResolution {
  winningEdit: CollabEdit;
  losingEdits: CollabEdit[];
  reason: string;
  notifiedAgents: string[];
}
```

### Undo/Redo in Collaboration

```typescript
interface CollaborativeUndo {
  // Each agent has their own undo stack
  // Undo reverts the agent's own edits, not others'

  undoStack: UndoEntry[];
  redoStack: UndoEntry[];
}

interface UndoEntry {
  editId: string;
  operation: EditOperation;
  inverseOperation: EditOperation;  // Computed at edit time
  timestamp: Date;
  canUndo: boolean;                 // False if a dependent edit exists
  dependentEdits: string[];         // Edits that depend on this one
}

// Undo rules:
// 1. An agent can undo their own edits
// 2. If edit B depends on edit A, A can't be undone until B is undone
// 3. Undo creates a new edit (not a revert), so others see it in real-time
// 4. Undo is scoped to the current session (clears on disconnect)
// 5. Critical edits (booking confirmation) require confirmation before undo

// Undo limitations:
// Cannot undo another agent's edit
// Cannot undo if the field was subsequently modified by someone else
// Cannot undo a booking that has been confirmed by the supplier
// Undo is not available for ops actions (cancel, delete, submit)
```

### Version Vector Model

```typescript
interface TripVersion {
  tripId: string;
  version: number;
  versionVector: Record<string, number>;  // agentId → last seen version
  lastEditAt: Date;
  lastEditBy: string;
}

// Version tracking:
// Each agent maintains their own version counter
// Server maintains a version vector per trip
// Edits are accepted if based on a version the server has seen
// Edits are rejected if based on a stale version (conflict)

// Version vector example:
// Agent A has version 5 (edited 3 times)
// Agent B has version 5 (edited 2 times)
// Server: { agentA: 3, agentB: 2 } → global version 5
//
// Agent A submits edit based on version 5 → Accepted, server version 6
// Agent B submits edit based on version 5 → Conflict! (stale)
//   → Server transforms Agent B's edit against Agent A's edit
//   → Or rejects and sends full sync to Agent B

// Snapshot strategy:
// Every 50 edits → Create a full snapshot
// Between snapshots → Store edit log
// Restore → Load snapshot + replay edits
// Compaction → Merge edits older than 24 hours into snapshot
```

---

## Open Problems

1. **Structured data merging** — Text collaboration is well-solved (Google Docs). Merging structured JSON (itinerary arrays, pricing objects) is harder. Need custom merge logic per data type.

2. **Booking integrity** — A hotel booking edit can't be "merged." Once confirmed, it's immutable. Need clear boundaries between editable and locked data.

3. **Edit attribution** — When viewing a trip's edit history, each change should show who made it. But merged edits complicate attribution.

4. **Performance at scale** — Each edit broadcasts to all participants. With 10 agents and rapid editing, message volume grows quickly. Need batching and throttling.

5. **Mobile constraints** — Mobile agents have limited bandwidth and processing power. Full CRDT computation may be too expensive. Need lightweight sync for mobile.

---

## Next Steps

- [ ] Evaluate CRDT libraries (Yjs, Automerge) for structured data
- [ ] Design conflict resolution rules per field type for travel data
- [ ] Build version vector tracking for trip edits
- [ ] Design undo/redo system scoped to collaborative editing
- [ ] Study Google Docs-like real-time editing for itinerary sections
