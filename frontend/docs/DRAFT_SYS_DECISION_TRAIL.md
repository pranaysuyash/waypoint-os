# Draft System — Design Decision Trail

> Record of discussions, decisions, user preferences, and architectural reasoning for the Draft-as-first-class-entity system.

---

## Origin

The Draft system emerged from testing the Workbench page. The core insight: the `draft_id` was invisible plumbing. Making it a first-class persistent workspace transforms the agent experience — agents can save incomplete work, return tomorrow, and resume seamlessly.

---

## Discussion & Decisions

### 1. Storage Medium

**Question:** JSON files (data/drafts/) like RunLedger/AuditStore, or SQL like the trips table?

**Analysis (1st Principles):**
The access pattern determines storage choice:
- RunLedger: write-once, read-many, single-key lookup → JSON files ✅
- AuditStore: append-only, keyed by entity → JSON files ✅
- Drafts: **frequent read-write, listed, filtered, status-queried, multi-agent access** → needs both

**Decision:** Hybrid approach
- **SQL** for draft metadata (id, status, name, agent, timestamps, agency) — enables listing, filtering, status queries
- **JSON payload** for full workbench state (customer_message, structured_json, last_run_snapshot) — keeps the heavy/large fields out of SQL
- Reasoning: Drafts need relational queries ("show all my blocked drafts", "find draft for customer X"). JSON files don't support this efficiently. But the customer_message can be large (pasting full WhatsApp conversations), so keeping it in SQL bloats the table.

**User input:** "Think architecturally and 1st principles"

---

### 2. Auto-Save vs Explicit Save

**Question:** Auto-save (debounced like Google Docs) or explicit "Save Draft" button?

**User decision:** BOTH
- Auto-save with minimum time threshold — only triggers when there's meaningful content (don't save blank states like Google Docs does)
- Explicit "Save Draft" button always available for manual control
- Auto-save fires after 5 seconds of inactivity IF at least one of: customer_message, agent_notes, or structured_json is non-empty
- PII concern acknowledged — auto-save should feel intentional, not spooky

**Implementation notes:**
- Debounce: 5 seconds after last meaningful keystroke
- Guard: skip auto-save if all content fields are empty/unchanged
- Visual indicator: subtle "Saving..." / "Saved" / "Draft saved at 10:32 AM" status
- Explicit save: immediate, no debounce

---

### 3. Draft Naming

**Question:** Auto-generate from customer message or use timestamp-based name?

**User decision:** Smart auto-generation with editable name
- Priority order: First line of customer message → First line of agent notes → "Draft - Apr 29, 10:32 AM"
- Name is always editable by the agent
- Max display length: 60 characters, truncated with "..."
- Name updates on first meaningful edit (when name is still auto-generated)

---

### 4. Draft Merging & Attachment

**User raised scenario:** "Suppose today I save something in draft. Later another agent started work on the same customer and created a new draft/trip. User should be able to attach existing draft/trip to another one."

**Analysis:** This is a real operational scenario:
- Agent A starts a draft for customer Sharma, saves, goes on leave
- Agent B receives the same customer inquiry, starts a new draft
- Now there are two drafts for the same customer — need to merge or link

**Features needed:**
1. **Link draft to existing trip** — "This draft is about the same customer as TRIP-442"
2. **Merge drafts** — Combine inputs/notes from two drafts into one
3. **Duplicate detection** — Alert when a new draft seems related to an existing draft/trip (same phone number, same customer name, overlapping dates)
4. **Draft transfer** — Reassign a draft from one agent to another

---

### 5. UI Placement

**Question:** Where do drafts live in the UI?

**User decision:** Option B — New "Drafts" item in the left sidebar (next to Inbox, Workbench, etc.)

**Reasoning:**
- Drafts are a distinct entity, not a filter on Inbox
- Dedicated sidebar item gives visibility and importance
- Can show draft count badge (e.g., "Drafts (3)")
- Inbox is for trips/enquiries; Drafts are pre-trip workspace

---

### 6. Scope of First Implementation

**Recommendation from discussion:**
- Phase 1: Backend plumbing (DraftStore, API, audit integration) + minimal frontend wire
- Phase 2: Drafts list UI in sidebar, naming, auto-save
- Phase 3: Merging, attachment, duplicate detection

---

## Open Questions (Unresolved)

1. **Retention** — How long do unpromoted drafts stay? Auto-delete after 30 days? Manual cleanup?
2. **Concurrent editing** — Two agents editing same draft simultaneously? Optimistic locking?
3. **Draft permissions** — Can any agent see any draft, or only their own? Manager override?
4. **Draft versioning** — Should drafts have version history (like Google Docs), or just last-saved state?
5. **Draft templates** — Can agents create draft templates (pre-filled configs for common scenarios)?

---

**Created:** 2026-04-29
**Status:** Design decisions captured, research series to follow
