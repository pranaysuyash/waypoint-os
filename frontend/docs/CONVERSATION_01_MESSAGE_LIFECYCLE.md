# Conversation UX — Message Lifecycle & Persistence

> Research document for message creation, editing, saving, reloading, and lifecycle management.

---

## Current State

The workbench currently stores `customerMessage` and `agentNotes` as flat text fields on the trip object. There is no message model, no editing history, no save/resume, and no reload capability.

---

## Key Questions

1. **Should messages be first-class entities (separate from trips) with their own lifecycle?**
2. **What does "save" mean — auto-save drafts, explicit save, or version snapshots?**
3. **How do we support editing without losing the original message (audit trail)?**
4. **What's the reload/resume story when a user closes the browser and returns?**
5. **How do messages relate to the spine run pipeline — are they inputs, outputs, or both?**
6. **What message types exist beyond free-text (structured data, voice, attachments)?**

---

## Research Areas

### Message Data Model

```typescript
interface Message {
  messageId: string;
  conversationId: string;
  tripId: string;
  type: MessageType;
  role: MessageRole;
  content: MessageContent;
  status: MessageStatus;
  version: number;
  editHistory: MessageEdit[];
  reactions: MessageReaction[];
  metadata: MessageMetadata;
  createdAt: Date;
  updatedAt: Date;
}

type MessageType =
  | 'text'              // Plain text message
  | 'structured'        // Structured data (trip details, options)
  | 'system'            // System-generated notification
  | 'note'              // Agent internal note (not customer-visible)
  | 'instruction'       // Agent instruction to the system
  | 'output'            // System output (itinerary, quote, analysis)
  | 'attachment'        // File or image attachment
  | 'voice'             // Voice message / transcript
  | 'template'          // Template-based message (canned response)
  | 'correction';       // Correction to a previous message

type MessageRole =
  | 'customer'          // End customer / traveler
  | 'agent'             // Travel agent
  | 'system'            // Automated system response
  | 'assistant';        // AI assistant within the platform

type MessageStatus =
  | 'draft'             // Being composed
  | 'sent'              // Sent to recipient
  | 'delivered'         // Confirmed delivered
  | 'read'              // Confirmed read
  | 'edited'            // Modified after initial send
  | 'deleted';          // Soft-deleted

interface MessageContent {
  text?: string;
  structured?: Record<string, unknown>;
  attachments?: Attachment[];
  richText?: RichTextBlock[];
}

interface MessageEdit {
  version: number;
  previousContent: string;
  editedBy: string;
  editedAt: Date;
  editReason?: string;
}
```

### Save & Draft Management

**Questions:**
- Auto-save interval (every 3 seconds? on pause? on blur?)
- Where are drafts stored (localStorage, backend, both)?
- How to handle concurrent editing (agent on two tabs)?

```typescript
interface DraftManager {
  // Auto-save current draft
  saveDraft(conversationId: string, content: string): void;
  // Load last draft on page open
  loadDraft(conversationId: string): string | null;
  // List all unsaved drafts
  listDrafts(): DraftSummary[];
  // Discard a draft
  discardDraft(conversationId: string): void;
}

interface DraftSummary {
  conversationId: string;
  tripId: string;
  lastSavedAt: Date;
  preview: string;            // First 100 chars
  hasUnsavedChanges: boolean;
}
```

**Research needed:**
- What auto-save UX patterns work best (Google Docs-style subtle indicator vs. explicit save button)?
- localStorage vs. IndexedDB vs. backend persistence for drafts?
- How to signal unsaved changes on page close (beforeunload)?

### Edit & Version History

**Questions:**
- Who can edit which messages (agent edits own, agent edits customer input for correction)?
- Is edit history visible to the customer or only internal?
- What's the maximum edit window (indefinite, 24h, until next action)?

**Patterns to study:**
- Slack: Shows "(edited)" with hover tooltip for original
- Email: No editing, only reply/forward
- ChatGPT: Edit regenerates response from that point
- Notion: Full version history with restore

```typescript
interface EditPolicy {
  messageRole: MessageRole;
  canEdit: boolean;
  editWindow: string;         // 'indefinite' | '24h' | 'until_responded'
  showEditIndicator: boolean; // Show "(edited)" to recipient
  preserveOriginal: boolean;  // Keep original in history
  requiresReason: boolean;    // Must provide edit reason
}
```

### Reload & Session Resume

**When a user returns after closing the browser:**

```typescript
interface SessionResume {
  // What was the user doing when they left?
  lastActiveContext: {
    tripId: string;
    conversationId: string;
    activePanel: string;
    draftContent?: string;
    lastMessageTimestamp: Date;
  };
  // What happened while they were gone?
  newActivity: {
    newMessages: number;
    systemUpdates: number;
    spineRunsCompleted: number;
  };
  // Resume options
  resumeOptions: ResumeOption[];
}

type ResumeOption =
  | { type: 'continue_draft'; description: string }
  | { type: 'review_new_messages'; count: number }
  | { type: 'check_spine_results'; runIds: string[] }
  | { type: 'start_fresh'; description: string };
```

**Questions:**
- Should we restore exact scroll position and panel state?
- How to surface "what happened while you were away"?
- What's the balance between helpful restore and feeling intrusive?

---

## Open Problems

1. **Message ↔ Spine run coupling** — Customer messages feed into spine runs. If a message is edited, should previous spine runs be invalidated? Does the edit create a new run?

2. **Draft conflict resolution** — Agent starts a message on desktop, continues on mobile. Two drafts exist. Which wins?

3. **Customer input sanitization** — Customer sends a PDF itinerary or a WhatsApp voice note. How to normalize these into the message model?

4. **Performance at scale** — A conversation with 200+ messages needs virtualized rendering, lazy loading, and efficient diffing for edits.

5. **Offline drafting** — Agent loses internet while composing. Need offline draft persistence with sync on reconnect.

---

## Next Steps

- [ ] Study message lifecycle patterns in Slack, Linear, Notion
- [ ] Design auto-save draft system with localStorage + backend sync
- [ ] Research virtualized message list rendering (react-virtuoso, tanstack virtual)
- [ ] Prototype edit history UI with version diffing
- [ ] Design session resume UX with "what you missed" summary
- [ ] Map message types to spine run inputs and outputs
