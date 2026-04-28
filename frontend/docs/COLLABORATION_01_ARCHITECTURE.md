# Real-Time Collaboration — Architecture & Presence

> Research document for multi-agent collaborative editing, presence awareness, and conflict resolution.

---

## Key Questions

1. **How do multiple agents work on the same trip simultaneously without conflicts?**
2. **What's the presence model — who's viewing, who's editing, who's away?**
3. **How do we handle concurrent edits to the same field or section?**
4. **What's the latency budget for real-time updates to feel "live"?**
5. **How do we recover from disconnections without losing work?**

---

## Research Areas

### Presence Model

```typescript
interface PresenceState {
  tripId: string;
  participants: ParticipantPresence[];
  locks: ResourceLock[];
  lastActivity: Date;
}

interface ParticipantPresence {
  agentId: string;
  agentName: string;
  status: PresenceStatus;
  cursor: CursorPosition;
  activeSection: string;            // Which panel/section they're viewing
  activeField?: string;             // Which field they're editing
  color: string;                    // Assigned color for cursor/selection
  joinedAt: Date;
  lastHeartbeat: Date;
  device: 'desktop' | 'mobile' | 'tablet';
}

type PresenceStatus =
  | 'active'                // Currently interacting
  | 'viewing'               // Looking at the trip but not editing
  | 'editing'               // Actively modifying content
  | 'idle'                  // No interaction for 2+ minutes
  | 'away';                 // Explicitly set away / no heartbeat for 5+ min

interface CursorPosition {
  panelId: string;
  sectionId?: string;
  fieldId?: string;
  offset?: number;                   // Character offset for text fields
  selection?: { start: number; end: number };
}

// Presence display:
// 1. Avatar stack in trip header showing active participants
// 2. Colored cursor/selection overlay on shared fields
// 3. "Agent X is editing Pricing" status bar
// 4. Idle indicators (faded avatar, "last seen 3 min ago")
// 5. Device indicator (mobile agent gets priority for calls)
```

### Resource Locking

```typescript
interface ResourceLock {
  lockId: string;
  tripId: string;
  resourceType: 'field' | 'section' | 'panel' | 'trip';
  resourceId: string;
  lockedBy: string;
  lockedAt: Date;
  expiresAt: Date;                   // Auto-release after timeout
  lockType: 'exclusive' | 'shared';
}

// Locking strategy:
// Field-level: When agent clicks into a field, soft-lock it
//   - Other agents see "Agent X is editing this field"
//   - Other agents CAN override (with warning) for emergencies
// Section-level: When agent is actively editing a panel section
//   - Other agents can view but get warning before editing
// Trip-level: Reserved for destructive operations (delete, submit)
//   - Exclusive lock, other agents are read-only

// Lock timeout rules:
// Field lock → 30 seconds of inactivity → auto-release
// Section lock → 2 minutes of inactivity → auto-release
// Trip lock → Manual release only (with confirmation)

// Conflict prevention:
// 1. Optimistic UI — Show edit immediately for the editor
// 2. Server validates — Check version before committing
// 3. Merge on conflict — Server sends merge resolution to both parties
// 4. Last-write-wins with notification — If merge impossible, notify loser
```

### Transport Layer

```typescript
interface CollaborationTransport {
  protocol: TransportProtocol;
  messageTypes: CollabMessage[];
  reconnection: ReconnectionConfig;
}

type TransportProtocol =
  | { type: 'websocket'; url: string; heartbeatIntervalMs: number }
  | { type: 'webrtc'; signalingServer: string }
  | { type: 'sse'; url: string; fallbackPollingMs: number };

type CollabMessage =
  | { type: 'presence_update'; agentId: string; presence: ParticipantPresence }
  | { type: 'lock_acquire'; lock: ResourceLock }
  | { type: 'lock_release'; lockId: string }
  | { type: 'edit'; edit: CollabEdit }
  | { type: 'edit_ack'; editId: string; serverVersion: number }
  | { type: 'edit_reject'; editId: string; reason: string }
  | { type: 'sync'; fullState: TripCollabState }
  | { type: 'cursor_move'; agentId: string; cursor: CursorPosition }
  | { type: 'comment'; comment: CollabComment }
  | { type: 'notification'; notification: CollabNotification };

interface ReconnectionConfig {
  maxRetries: number;
  backoffMs: number;
  maxBackoffMs: number;
  offlineBufferMax: number;         // Max edits to buffer while disconnected
  syncOnReconnect: boolean;
}

// Latency targets:
// Cursor movement: < 100ms (perceived as instant)
// Presence updates: < 500ms (avatar appears/disappears)
// Field edits: < 200ms (see changes reflected)
// Lock acquisition: < 300ms (feedback on lock status)
// Full sync: < 2s (reconnection catch-up)
```

---

## Open Problems

1. **Spine run contention** — Two agents trigger spine runs for the same trip simultaneously. Need coordination to prevent duplicate processing and conflicting results.

2. **Mobile presence** — Mobile agents have intermittent connectivity. Presence should show "on mobile, may be slow to respond" without constant disconnection/reconnection noise.

3. **Offline editing** — Agent edits while disconnected, reconnects later. Need offline edit buffer with conflict resolution on sync.

4. **Scalability** — How many concurrent editors per trip? For MICE events with 5+ agents, the system needs to handle real-time collaboration at scale.

5. **Presence fatigue** — Constant avatar updates and cursor movements can be distracting. Need "focus mode" to hide presence while keeping collaboration features.

---

## Next Steps

- [ ] Design presence API with heartbeat and reconnection
- [ ] Build resource locking system with auto-release
- [ ] Evaluate transport options (WebSocket vs. SSE vs. WebRTC) for travel platform
- [ ] Study collaborative editing algorithms (OT vs. CRDT)
- [ ] Design offline edit buffer and sync protocol
