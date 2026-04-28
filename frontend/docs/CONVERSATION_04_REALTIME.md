# Conversation UX — Real-Time Updates & Collaboration

> Research document for real-time messaging, multi-user collaboration, and live updates.

---

## Current State

No real-time features exist. Messages are saved via REST API calls with page refresh needed to see updates. No WebSocket, no SSE, no polling. Single-user only — no collaboration features.

---

## Key Questions

1. **What real-time events need to push to the client (new messages, spine run progress, booking updates)?**
2. **What transport layer — WebSocket, SSE, or polling?**
3. **How do we handle multiple agents viewing/editing the same trip simultaneously?**
4. **What presence indicators are needed (who's online, who's viewing, who's typing)?**
5. **How do we handle reconnection and missed events?**
6. **What's the real-time architecture — direct WebSocket or through a message broker?**

---

## Research Areas

### Real-Time Event Types

```typescript
type RealtimeEvent =
  // Conversation events
  | { type: 'message.created'; message: Message }
  | { type: 'message.updated'; message: Message }
  | { type: 'message.deleted'; messageId: string }
  | { type: 'typing.started'; userId: string; conversationId: string }
  | { type: 'typing.stopped'; userId: string; conversationId: string }
  // Spine events
  | { type: 'spine.started'; runId: string; tripId: string }
  | { type: 'spine.progress'; runId: string; stage: string; percent: number }
  | { type: 'spine.completed'; runId: string; tripId: string; result: unknown }
  | { type: 'spine.failed'; runId: string; error: string }
  // Trip events
  | { type: 'trip.updated'; tripId: string; changes: string[] }
  | { type: 'trip.status_changed'; tripId: string; newStatus: string }
  | { type: 'trip.assigned'; tripId: string; agentId: string }
  // Booking events
  | { type: 'booking.confirmed'; bookingId: string; tripId: string }
  | { type: 'booking.failed'; bookingId: string; error: string }
  // Presence events
  | { type: 'presence.online'; userId: string }
  | { type: 'presence.offline'; userId: string }
  | { type: 'presence.viewing'; userId: string; tripId: string }
  // Alert events
  | { type: 'alert.received'; alertId: string; severity: string }
  | { type: 'alert.acknowledged'; alertId: string; userId: string };
```

### Transport Layer Options

| Option | Pros | Cons | Best For |
|--------|------|------|----------|
| **WebSocket** | Full-duplex, low latency, efficient | Connection management, scaling | Primary real-time channel |
| **SSE** | Simple, auto-reconnect, HTTP-based | One-way only (server→client) | Read-only updates (spine progress) |
| **Long polling** | Simple, works everywhere | High overhead, latency | Fallback only |
| **Short polling** | Simplest to implement | Wasteful, delayed | Low-frequency updates |

**Likely architecture: WebSocket as primary, SSE as fallback for restricted networks**

```typescript
interface RealtimeClient {
  connect(userId: string): void;
  subscribe(channel: string, handler: EventHandler): void;
  unsubscribe(channel: string): void;
  publish(event: RealtimeEvent): void;
  getStatus(): ConnectionStatus;
  getMissedEvents(since: Date): RealtimeEvent[];
}

type ConnectionStatus =
  | 'connected'
  | 'connecting'
  | 'disconnected'
  | 'reconnecting';
```

### Collaboration Features

```typescript
interface CollaborationState {
  tripId: string;
  activeUsers: ActiveUser[];
  locks: ResourceLock[];
  cursors: UserCursor[];
}

interface ActiveUser {
  userId: string;
  name: string;
  avatarUrl: string;
  currentlyViewing: string;    // Which panel/section
  lastActivity: Date;
  status: 'active' | 'idle' | 'away';
}

interface ResourceLock {
  resourceId: string;           // e.g., message being edited
  lockedBy: string;
  lockedAt: Date;
  lockType: 'exclusive' | 'advisory';
  expiresAt: Date;
}

interface UserCursor {
  userId: string;
  location: CursorLocation;
  selection?: CursorSelection;
}
```

**Collaboration patterns to research:**
- Google Docs-style real-time editing (CRDT/OT)
- Figma-style presence cursors
- Linear-style optimistic locking
- Notion-style page-level collaboration

### Typing & Presence Indicators

```typescript
interface PresenceManager {
  // Announce this user is viewing a trip
  announcePresence(tripId: string): void;
  // Announce typing in a conversation
  announceTyping(conversationId: string): void;
  // Get who's currently viewing a trip
  getViewers(tripId: string): ActiveUser[];
  // Subscribe to presence updates
  onPresenceChange(handler: PresenceHandler): void;
}
```

**Questions:**
- Is typing indicator needed for internal notes, customer messages, or both?
- How to handle "agent appears to be typing but is actually idle" (debounce strategy)?
- Should customers see agent presence (e.g., "Agent is looking at your request")?

---

## Open Problems

1. **Reconnection and event ordering** — If WebSocket disconnects for 5 seconds, the client needs to catch up on missed events without re-ordering or duplicating. Need sequence numbers and deduplication.

2. **Optimistic updates** — When an agent sends a message, it should appear immediately in the UI before server confirmation. If the server rejects it, need rollback UX.

3. **Conflict resolution for concurrent edits** — Two agents editing the same message simultaneously. Last-write-wins? Operational transform? CRDT?

4. **Spine run real-time progress** — Spine runs can take 30-60 seconds. Streaming intermediate results (extraction done, routing done, pricing in progress) requires structured progress events.

5. **Scalability of presence** — With 100 agents online, presence events create significant traffic. Need intelligent aggregation and throttling.

6. **Offline → online sync** — Agent composes a message offline, then reconnects. How to sync the draft with the server and handle any conflicts?

---

## Next Steps

- [ ] Evaluate WebSocket libraries for Next.js (Socket.IO, Pusher, Ably, Soketi)
- [ ] Research real-time collaboration patterns (CRDT vs. OT)
- [ ] Design event ordering and deduplication strategy
- [ ] Study spine run progress streaming architecture
- [ ] Prototype presence indicator component
- [ ] Design optimistic update patterns with rollback
