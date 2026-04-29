# Draft System — UI & Experience Design

> Research document for the Draft sidebar, Drafts list, Workbench integration, status badges, and the complete agent experience with persistent drafts.

---

## Key Questions

1. **Where and how do drafts appear in the sidebar?**
2. **What does the Drafts list look like?**
3. **How does the Workbench integrate draft loading/saving?**
4. **What status indicators and feedback does the agent see?**

---

## Research Areas

### Sidebar: Drafts Section

```typescript
// ── Left sidebar layout ──
// ┌─────────────────────────────────────────────────────┐
// │  Waypoint OS                                          │
// │                                                       │
// │  ── Navigation ──                                     │
// │  📥 Inbox (12)                                       │
// │  📋 Drafts (3)          ← NEW SECTION                │
// │  🔧 Workbench                                       │
// │  📊 Reports                                         │
// │  ⚙️ Settings                                        │
// │                                                       │
// │  ── Drafts Preview ──                                 │
// │  ┌───────────────────────────────────────────────┐   │
// │  │ 📝 Singapore trip for family    [BLOCKED] ⚠️  │   │
// │  │    Priya · 2h ago                              │   │
// │  │                                               │   │
// │  │ 📝 Kerala backwaters enquiry     [OPEN]       │   │
// │  │    Rahul · Yesterday                           │   │
// │  │                                               │   │
// │  │ 📝 Dubai corporate offsite       [OPEN]       │   │
// │  │    Priya · 3 days ago                          │   │
// │  │                                               │   │
// │  │ [+ New Draft]     [View All Drafts →]         │   │
// │  └───────────────────────────────────────────────┘   │
// └─────────────────────────────────────────────────────┘
```

### Drafts List View (Full Page)

```typescript
// ── Drafts list page ──
// ┌─────────────────────────────────────────────────────┐
// │  Drafts (3)                            [+ New Draft] │
// │                                                       │
// │  Filter: [All ▼] [Mine ▼] [🔍 Search drafts...]     │
// │                                                       │
// │  ┌───────────────────────────────────────────────┐   │
// │  │ 📝 Singapore trip for family                    │   │
// │  │ Status: ⚠️ BLOCKED (NB01 — missing fields)    │   │
// │  │ Agent: Priya · Created: Apr 29, 10:30 AM      │   │
// │  │ Last saved: 12:46 PM · 2 runs (1 blocked)     │   │
// │  │ Customer: "Planning Singapore trip, family..." │   │
// │  │                                               │   │
// │  │ [Continue] [Rename] [Transfer] [Discard]       │   │
// │  └───────────────────────────────────────────────┘   │
// │                                                       │
// │  ┌───────────────────────────────────────────────┐   │
// │  │ 📝 Kerala backwaters enquiry                    │   │
// │  │ Status: ✅ OPEN                                 │   │
// │  │ Agent: Rahul · Created: Apr 28, 3:15 PM       │   │
// │  │ Last saved: Apr 28, 3:45 PM · No runs yet     │   │
// │  │ Notes: "Customer wants houseboat, budget ₹2L" │   │
// │  │                                               │   │
// │  │ [Continue] [Rename] [Transfer] [Discard]       │   │
// │  └───────────────────────────────────────────────┘   │
// │                                                       │
// │  ┌───────────────────────────────────────────────┐   │
// │  │ 🎉 Dubai corporate offsite                      │   │
// │  │ Status: ✅ PROMOTED → TRIP-442                  │   │
// │  │ Agent: Priya · Created: Apr 26, 9:00 AM       │   │
// │  │ Promoted: Apr 26, 10:15 AM                     │   │
// │  │                                               │   │
// │  │ [View Trip] (read-only)                         │   │
// │  └───────────────────────────────────────────────┘   │
// │                                                       │
// │  ── Filters ──                                        │
// │  Status: [All] [Open] [Blocked] [Promoted] [Discarded]│
// │  Agent:  [All] [Mine] [Unassigned]                   │
// │  Sort:   [Last Modified] [Created] [Name]            │
// └─────────────────────────────────────────────────────┘
```

### Workbench Header with Draft Context

```typescript
// ── Workbench header with draft info ──
// ┌─────────────────────────────────────────────────────┐
// │  ┌─ Pipeline ────────────────────────────────────┐   │
// │  │  Intake ──▶ Packet ──▶ Decision ──▶ Strategy  │   │
// │  └───────────────────────────────────────────────┘   │
// │                                                       │
// │  📝 Singapore trip for family          ⚠️ BLOCKED    │
// │  Draft: dft_abc123 · Saved at 12:46 PM              │
// │                                                       │
// │  ┌─ Actions ──────────────────────────────────────┐  │
// │  │ [▶️ Process Trip] [💾 Save Draft] [↩️ Reset]     │  │
// │  │                                [⚙️ Settings]    │  │
// │  └─────────────────────────────────────────────────┘  │
// │                                                       │
// │  Status details:                                      │
// │  ┌───────────────────────────────────────────────┐   │
// │  │ ⚠️ Blocked — 3 missing fields                  │   │
// │  │ Gate NB01: destination, travel_dates, budget   │   │
// │  │ Last run: 10:32 AM (blocked after 45s)        │   │
// │  │ [Fix in Packet Tab →]                          │   │
// │  └───────────────────────────────────────────────┘   │
// │                                                       │
// │  Auto-save: Saved at 12:46 PM ✅                      │
// └─────────────────────────────────────────────────────┘
```

### Save Status Indicator

```typescript
// ── Save status states ──
// ┌─────────────────────────────────────────────────────┐
// │  Save Status Indicator (shown in workbench header)    │
// │                                                       │
// │  State 1: Idle (nothing to show)                      │
// │    (no indicator)                                     │
// │                                                       │
// │  State 2: Unsaved changes                            │
// │    "● Unsaved changes" (subtle dot + text)           │
// │                                                       │
// │  State 3: Auto-save pending (debounce timer)          │
// │    "● Saving..." (animated dot)                       │
// │                                                       │
// │  State 4: Auto-save in flight                         │
// │    "● Saving..." (API call in progress)              │
// │                                                       │
// │  State 5: Auto-save succeeded                         │
// │    "✓ Saved at 12:46 PM" (fades after 5 seconds)    │
// │                                                       │
// │  State 6: Auto-save failed                            │
// │    "✗ Save failed — [Retry]" (stays until resolved) │
// │                                                       │
// │  State 7: Manual save                                 │
// │    "✓ Draft saved" (green flash, fades after 3s)     │
// └─────────────────────────────────────────────────────┘
```

### URL and Routing

```typescript
// ── URL patterns for drafts ──
// ┌─────────────────────────────────────────────────────┐
// │  URL Routing                                           │
// │                                                       │
// │  New draft (blank workbench):                          │
// │  /workbench?draft=new                                  │
// │  → Auto-creates draft on first save                   │
// │                                                       │
// │  Existing draft:                                       │
// │  /workbench?draft=dft_abc123                           │
// │  → Loads draft state from API                         │
// │                                                       │
// │  Draft with specific tab:                              │
// │  /workbench?draft=dft_abc123&tab=packet                │
// │                                                       │
// │  Draft processing (run in progress):                   │
// │  /workbench?draft=dft_abc123&run=run_xyz789            │
// │                                                       │
// │  After promotion (auto-redirect):                      │
// │  /workbench?draft=dft_abc123                           │
// │  → Redirects to /workspace/WP-442/intake              │
// │                                                       │
// │  Drafts list:                                          │
// │  /drafts                                              │
// │                                                       │
// │  Shareable links:                                      │
// │  Agent copies URL: ?draft=dft_abc123                  │
// │  Another agent opens it → loads same draft            │
// │  (permission check: same agency, has access)          │
// └─────────────────────────────────────────────────────┘
```

### Status Badge System

```typescript
// ── Status badges across UI ──
// ┌─────────────────────────────────────────────────────┐
// │  Draft Status Badges                                   │
// │                                                       │
// │  Status     | Badge          | Color    | Icon        │
// │  ─────────────────────────────────────────────────── │
// │  OPEN       | "Open"         | Blue     | 📝         │
// │  PROCESSING | "Processing"   | Yellow   | ⏳         │
// │  BLOCKED    | "Blocked: NB01"| Red      | ⚠️         │
// │  FAILED     | "Failed"       | Red      | ❌         │
// │  PROMOTED   | "→ TRIP-442"   | Green    | 🎉         │
// │  DISCARDED  | "Discarded"    | Gray     | 🗑️         │
// │                                                       │
// │  Badge locations:                                      │
// │  • Sidebar draft list item                            │
// │  • Workbench header (next to draft name)              │
// │  • Drafts full page list                              │
// │  • Browser tab title: "⚠️ Singapore trip — Waypoint" │
// └─────────────────────────────────────────────────────┘
```

---

## Open Problems

1. **Sidebar real estate** — Adding "Drafts" to the sidebar adds clutter. Solution: collapsible section that shows only when drafts exist, or always show with count badge.

2. **Draft-to-workspace transition** — When a draft promotes, the agent is auto-navigated. But what if they had unsaved state? Need to confirm before redirect.

3. **Mobile responsiveness** — The draft sidebar section needs to work on mobile (hamburger menu). Drafts list should be a full-page view on mobile.

4. **Notification fatigue** — Showing "Saved at 12:46 PM" every 5 seconds when auto-save fires could be distracting. Solution: only show on explicit save; auto-save is silent (indicator only appears when there are unsaved changes).

---

## Next Steps

- [ ] Build Drafts sidebar section with count badge and preview
- [ ] Create Drafts list page with filters and actions
- [ ] Implement Workbench header draft context (name, status, save indicator)
- [ ] Design URL routing for draft-based workbench
- [ ] Build status badge component system
