# Inbox Intelligence Layer v2 — Comprehensive Directive

**Date**: Thursday, April 23, 2026
**Priority**: High (P1)
**Goal**: Transform the Inbox from a static link-list into a role-aware, progressively disclosed Active Inspection Portal that teaches new operators while accelerating experienced ones.
**Supersedes**: [`DIRECTIVE_INBOX_COCKPIT_EVOLUTION.md`](./DIRECTIVE_INBOX_COCKPIT_EVOLUTION.md) (dated 2026-04-22)

---

## 1. Problem Statement

### What We Know From Code & User Research

The current inbox (`frontend/src/app/inbox/page.tsx`) presents 12+ data points per card with equal visual weight. The `InboxTrip` type defines rich dimensions (priority, stage, SLA, value, assignment, flags, days in stage), but the card renders them as a flat grid of badges and text. This creates three classes of problems:

1. **New Operator Paralysis**: Priority, Stage, and SLA all appear as colored pills in the same visual band. A new agent cannot distinguish "how urgent is this?" (priority) from "where is it in workflow?" (stage) from "is it overdue?" (SLA). The `DIRECTIVE_INBOX_COCKPIT_EVOLUTION` correctly identified this as tribal knowledge, but its proposed solution (a hover legend) keeps the burden on the user to seek help.

2. **Comparison Friction**: Nielsen Norman Group card research confirms that card layouts deemphasize ranking and make comparison harder than list views. Our agents' core job is to compare 20 trips and pick one. The current layout makes this harder because value, days, party size, and date all compete for attention in the same row.

3. **One-Size-Fits-All Failure**: The card assumes every user cares about the same fields in the same order. A finance reviewer scanning for pipeline value has different needs than a vendor coordinator checking booking confirmations. The existing directive had no mechanism for this.

### What the Data Tells Us

From `types/governance.ts`:
- `InboxTrip` carries `priorityScore: number` (0-100) — unused in UI
- `InboxTrip` carries `flags: string[]` — unused in UI
- `InboxFilters` supports multi-select on priority, stage, assignedTo, slaStatus, and value range — UI exposes only single-select tabs
- `PipelineStage.slaHours` exists — could power contextual "% of SLA consumed" but is unused

From personas (`P1_SINGLE_AGENT_HAPPY_PATH.md`, `P2_TRAINING_TIME_PROBLEM.md`):
- Solo agents need to decide "what next?" in under 5 seconds
- Junior agents need the system to teach while they work (P2 scenario)
- Agency owners need workload visibility and risk surfacing

---

## 2. Design Principles

These principles override any specific implementation detail. If a technical constraint forces a tradeoff, reference these in order:

1. **Teach by Doing, Not by Manual**: New operators learn from inline micro-labels that fade after repeat exposure, not from help popovers they must remember to open.
2. **Same Data, Different Lenses**: The card always renders the same `InboxTrip` fields, but their visual hierarchy adapts to the viewer's role.
3. **Progressive Disclosure, Not Progressive Addition**: Start with less. Reveal more on hover, on role-switch, or as the user demonstrates proficiency.
4. **Composable Over Prescriptive**: Filters should combine (AND logic), not substitute (OR logic). Users build their own views.
5. **Contextual Semantics**: A raw number (`6d`) means nothing without knowing the stage's SLA target. Convert durations to semantic expressions (`6d · 600% of intake SLA`).

---

## 3. Architecture Overview

### 3.1 Component Hierarchy

```
InboxPage
├── InboxHeader
│   ├── Title + Subtitle
│   ├── SearchBar (expanded scope)
│   ├── SortDropdown
│   └── ViewProfileToggle ← NEW
├── FilterBar ← REPLACES FilterTabs
│   ├── ActiveFilterChips (removable)
│   ├── FilterDropdowns (multi-select)
│   └── SavedPresets ← NEW
├── BulkActionsToolbar (existing, unchanged)
└── TripGrid
    └── TripCard (restructured)
        ├── CardAccent (left bar, color = priority) ← NEW
        ├── PrimaryRow (destination + customer + stage)
        ├── MetricsRow (role-dependent ordering) ← NEW
        ├── StatusRow (SLA + assignee + flags) ← REORGANIZED
        └── HoverActions (quick-action chips) ← NEW
```

### 3.2 State Management

| State | Type | Persistence | Notes |
|-------|------|-------------|-------|
| `activeFilters` | `InboxFilters` | URL query params | Shareable, bookmarkable filter combos |
| `viewProfile` | `'operations' \| 'teamLead' \| 'finance' \| 'fulfillment'` | `localStorage` | Per-user preference, survives sessions |
| `sortBy` / `sortDirection` | `SortKey` / `SortDirection` | `localStorage` + URL | URL takes precedence if present; `localStorage` is fallback |
| `showMicroLabels` | `boolean` | `localStorage` + auto-detect | True for first `MICRO_LABEL_THRESHOLD` visits, then false |
| `showMicroLabels` | `boolean` | `localStorage` + auto-detect | True for first 3 visits, then false |
| `sortBy` / `sortDirection` | `SortKey` / `SortDirection` | `localStorage` | Per-user preference |

---

## 4. Card Restructure (TripCard v2)

### 4.1 Visual Layout

```
┌─[accent bar: priority color]─────────────────────────┐
│                                                       │
│  Bali               leisure        [Intake]          │
│  Client: Sharma Family                                │
│                                                       │
│  4 pax · TBD · $0.8k · 4d in stage                   │
│                                                       │
│  [🔴 Critical] [👤 Unassigned] [On Track]             │
│                                                       │
│  trip_ff2...                        [Assign] [View]  │
└───────────────────────────────────────────────────────┘
```

### 4.2 Row Specifications

#### Row 1: Primary Context
- **Left**: Destination (14px, semibold, `text-primary`) + Trip Type (12px, `text-secondary`)
- **Right**: Stage badge (uses `STATE_COLORS` tokens from design system)
- **Below**: Customer name (12px, `text-secondary`)

**Rationale**: Destination + Customer is the human-readable identity. Stage tells you where in the workflow. These are the two things an agent needs to decide "is this mine?"

#### Row 2: Metrics (Role-Dependent)

**Operations view** (default):
`[Party] · [Date] · [Value] · [Days in stage]`

**Manager view**:
`[Assignee] · [Days in stage] · [Value] · [Priority score]`

**Finance view**:
`[Value] · [Priority] · [Stage] · [Date]`

**Vendor view**:
`[Date] · [Stage] · [Destination] · [Party]`

**Rationale**: The same four fields, reordered by what that role compares across cards.

#### Row 3: Status
- **SLA Badge**: Contextual expression (see 4.3)
- **Assignment**: Name or "Unassigned" with distinct styling
- **Flags**: Small icon badges (♿, 👶, etc.) if `trip.flags` populated

#### Row 4: Footer
- **Left**: Trip ID in `text-muted` (10px, de-emphasized)
- **Right**: Hover-revealed quick actions (see 6.2)

### 4.3 Contextual SLA Badge

Replace the current flat `SLABadge` with a semantic expression:

| Stage | SLA Target | Days | Display |
|-------|-----------|------|---------|
| Intake | 24h | 6d | `6d · 600% of SLA` |
| Booking | 14d | 6d | `6d · 43% of SLA` |
| Options | 72h | 3d | `3d · 100% of SLA` |

**Implementation**: Use `PipelineStage.slaHours` from backend. Compute `percentage = (daysInCurrentStage * 24) / slaHours * 100`. Display raw days + percentage.

**Color logic** (unchanged):
- `on_track`: green (`STATE_COLORS.green`)
- `at_risk`: amber (`STATE_COLORS.amber`)
- `breached`: red (`STATE_COLORS.red`)

**Why**: A vendor agent seeing `6d` on a Booking card knows it's fine. An intake agent seeing `6d` knows it's catastrophic. Same number, different meaning.

### 4.4 Progressive Micro-Labels

For users with < 3 inbox visits (tracked in `localStorage`):

```
[🔴 Critical · needs human review]  [Intake · just arrived]  [On Track · within SLA]
```

After 3 visits, collapse to:
```
[🔴 Critical]  [Intake]  [On Track]
```

**Hover behavior**: Always show full explanation tooltip, even for experienced users.

**Rationale**: From P2 Training Time Problem — "the system should teach while it works." Inline labels teach passively. No click required.

---

## 5. Composable Filter Panel

### 5.1 Replace Tab Bar

Current:
```
All (20) | At Risk (7) | Critical (19) | Unassigned (20)
```

New:
```
[All]  [Priority ▼]  [SLA Status ▼]  [Assignment ▼]  [Stage ▼]  [Value ▼]
```

Each pill is a multi-select dropdown. Selected options appear as removable chips below the bar.

### 5.2 Filter Dropdown Specifications

| Filter | Options | Multi? | Default |
|--------|---------|--------|---------|
| Priority | Low, Medium, High, Critical | Yes | All selected |
| SLA Status | On Track, At Risk, Breached | Yes | All selected |
| Assignment | Specific agents + Unassigned | Yes | All selected |
| Stage | Intake, Details, Options, Review, Booking | Yes | All selected |
| Value Range | Min/Max input | No | unset |
| Date Range | From/To picker | No | unset |

### 5.3 Active Filter Chips

When filters are active, show removable chips:
```
Active: [Priority: Critical ✕] [SLA: At Risk ✕] [Unassigned ✕]  [Clear all]
```

Clicking ✕ removes that criterion. "Clear all" resets to defaults.

### 5.4 Quick Presets

Below the filter bar, offer 3-4 saved presets that apply common combos:

| Preset | Filters Applied | Rationale |
|--------|-----------------|-----------|
| **My Urgent** | Assigned to me + Priority ≥ High | Agent's daily driver |
| **Needs Owner** | Unassigned + SLA Breached | Manager triage |
| **High Value Pipeline** | Value > $100k + Stage ≠ Booked | Finance review |
| **Stale Bookings** | Stage = Booking + Days > 7 | Vendor coordination |

**UX note**: Since we have no launched usage data, these presets are hypotheses. They should be easy to rename/replace. The preset system should support CRUD (create, rename, update, delete) for power users.

### 5.5 URL Persistence

Filter state is serializable to URL query params:
```
/inbox?priority=critical,high&sla=at_risk,breached&assigned=unassigned
```

This enables:
- Bookmarking common views
- Sharing links ("hey, look at these 4 trips")
- Back button behavior

---

## 6. Interaction Patterns

### 6.1 Card Hover State

On hover:
- Border lightens (`border-hover` token)
- Background subtly elevates (`bg-elevated`)
- Quick-action chips fade in (200ms, ease-out)

Never hide critical information on hover. Hover only reveals actions, not data.

### 6.2 Quick-Action Chips (Replaces Kebab Menu)

On card hover, show compact text buttons:

```
[Assign] [Snooze] [View workspace]
```

**Rationale**: The original P1-05 kebab menu hid actions behind an extra click. Text chips are immediately scannable and reduce interaction cost. For bulk selection mode (checkbox checked), these individual actions are suppressed in favor of the BulkActionsToolbar.

**Actions**:
- `Assign`: Opens inline agent dropdown (same as bulk assign)
- `Snooze`: Opens date picker for temporary hide
- `View workspace`: Standard navigation

### 6.3 View Profile Toggle

A subtle icon-toggle near the sort dropdown:

```
[👤 Operations] [📊 Manager] [💰 Finance] [📦 Vendor]
```

- Default: Operations
- Persisted to `localStorage`
- Changes `TripCard` MetricsRow ordering instantly (no re-fetch)

### 6.4 Search Expansion

Current search fields: `destination`, `id`, `tripType`
Expanded search fields: `destination`, `id`, `tripType`, `customerName`, `assignedToName`

Add a small hint below the search bar:
```
Search by destination, customer, agent, or trip ID
```

Future: Consider value-range search (`value:>50000`) as advanced syntax.

---

## 7. Design Token Compliance

### 7.1 Mandatory Token Usage

The current `TripCard` uses inline styles (`style={{ color: meta.color }}`). V2 must use:

- `STATE_COLORS` from `tokens.ts` for all status badges
- `COLORS` tokens for text, backgrounds, borders
- `SPACING` tokens for padding/gaps
- `RADIUS` tokens for border radius
- `FONT_SIZE` / `FONT_WEIGHT` for typography

### 7.2 Card Accent Bar

Use the existing `CardAccent` component from `components/ui/card.tsx`:
```tsx
<CardAccent color={priorityToColorKey[trip.priority]} position="left" />
```

Map priority to color keys:
- `critical` → `accentRed`
- `high` → `accentAmber`
- `medium` → `accentBlue`
- `low` → `neutral`

### 7.3 Accessibility

- All color-coded badges must have text labels (never icon-only status)
- Tooltips must be keyboard-triggerable (`focus` state, not just `hover`)
- Filter dropdowns must support keyboard navigation
- Role toggle must have `aria-pressed` state

---

## 8. Data Flow & API

### 8.1 No New Backend Endpoints Required

All V2 features consume existing data:
- `InboxTrip` fields already carry everything needed
- `InboxFilters` already supports multi-select (UI didn't expose it)
- `PipelineStage.slaHours` is available for contextual SLA computation

### 8.2 Frontend-Only Changes

| File | Change |
|------|--------|
| `frontend/src/app/inbox/page.tsx` | Restructure layout, add FilterBar, add ViewProfileToggle |
| `frontend/src/components/inbox/TripCard.tsx` | Extract from page.tsx, implement v2 layout |
| `frontend/src/components/inbox/FilterBar.tsx` | NEW: Composable filters |
| `frontend/src/components/inbox/QuickPresets.tsx` | NEW: Saved filter presets |
| `frontend/src/components/inbox/ViewProfileToggle.tsx` | NEW: Role selector |
| `frontend/src/hooks/useInboxView.ts` | NEW: localStorage persistence for view state |
| `frontend/src/lib/inbox-helpers.ts` | NEW: SLA computation, filter serialization |

### 8.3 Type Safety

No changes to `InboxTrip` or `InboxFilters` types. V2 is a pure UI/UX layer on top of existing contracts.

---

## 9. Implementation Phases

### Phase 1: Foundation (Card Restructure + Progressive Labels)
**Effort**: Medium | **Files**: 3-4 new, 1 modified

1. Extract `TripCard` to standalone component
2. Implement left accent bar, row grouping, de-emphasized ID
3. Add progressive micro-labels system (`localStorage` visit counting)
4. Add persistent tooltips to all badges
5. Use `STATE_COLORS` tokens throughout

**Success criteria**:
- Card renders all existing data with new hierarchy
- New user sees micro-labels; returning user sees clean badges
- No visual regressions on existing functionality
- All tests pass

### Phase 2: Composable Filters
**Effort**: Medium | **Files**: 2-3 new, 1 modified

1. Build `FilterBar` with multi-select dropdowns
2. Wire to existing `useInboxTrips(filters)` hook
3. Add active filter chips with remove functionality
4. Add URL serialization for filter state
5. Replace existing tab bar

**Success criteria**:
- User can combine Priority + SLA + Assignment filters
- Filter state survives page refresh (URL)
- "Clear all" resets to default
- No performance degradation with 20 trips

### Phase 3: Role-Based Views + Presets
**Effort**: Medium | **Files**: 3-4 new, 2 modified

1. Build `ViewProfileToggle` with 4 profiles
2. Implement role-dependent `MetricsRow` ordering
3. Add `localStorage` persistence for selected profile
4. Build `QuickPresets` system with 4 default presets
5. Add preset CRUD (save current filters as new preset)

**Success criteria**:
- Switching profile reorders metrics instantly
- Selected profile persists across sessions
- Presets apply correct filter combinations
- Users can save custom presets

### Phase 4: Contextual SLA + Search Expansion
**Effort**: Small | **Files**: 1 new, 2 modified

1. Add SLA percentage computation using `PipelineStage.slaHours`
2. Update `SLABadge` to show contextual expression
3. Expand search to `customerName` and `assignedToName`
4. Add search hint text

**Success criteria**:
- Same `daysInCurrentStage` shows different percentages per stage
- Search finds trips by customer name or agent name
- No backend changes required

### Phase 5: Polish & Quick Actions
**Effort**: Small | **Files**: 1 modified

1. Implement hover-revealed quick-action chips
2. Add smooth transitions (200ms, ease)
3. Keyboard accessibility audit
4. Mobile responsiveness check

**Success criteria**:
- Hover actions visible and clickable
- Keyboard navigable throughout
- Mobile layout functional (may stack to single column)

---

## 10. Testing Strategy

### 10.1 Unit Tests

| Component | Test |
|-----------|------|
| `TripCard` | Renders correct row order for each view profile |
| `TripCard` | Shows micro-labels when visitCount < 3 |
| `TripCard` | Hides micro-labels when visitCount >= 3 |
| `FilterBar` | Applies multiple filters correctly |
| `FilterBar` | URL serialization round-trips |
| `useInboxView` | Persists to localStorage |
| `inbox-helpers` | SLA percentage computation correct |

### 10.2 Integration Tests

| Flow | Test |
|------|------|
| Filter → Sort → View Profile | All three states compose correctly |
| Preset apply → modify → save | Custom preset created and reloads |
| New user journey | First visit shows labels, 4th visit hides them |

### 10.3 Visual Regression

- Screenshot comparison for all 4 view profiles
- Screenshot comparison for filter active / inactive states

---

## 11. Rollback Plan

If any phase causes issues:
1. **Phase 1-2**: Feature-flag the new card/filter components. Keep old components in codebase under `_legacy` suffix. Toggle via env var.
2. **Phase 3-5**: Purely additive. Can be disabled individually.
3. **Data safety**: No backend changes. Frontend-only. Rollback = revert commit + redeploy.

---

## 12. Metrics to Watch Post-Launch

Since we have no pre-launch usage data, define success metrics now:

| Metric | Target | How Measured |
|--------|--------|--------------|
| Time-to-first-trip-open | < 5 seconds | Frontend analytics |
| Filter usage rate | > 30% of sessions | Track filter apply events |
| Preset usage rate | > 15% of sessions | Track preset apply events |
| View profile switch rate | > 10% of sessions | Track profile changes |
| New user support tickets mentioning "confusing" | Zero | Support ticket tagging |

---

## 13. References

- [`DIRECTIVE_INBOX_COCKPIT_EVOLUTION.md`](./DIRECTIVE_INBOX_COCKPIT_EVOLUTION.md) — Superseded predecessor
- [`DESIGN.md`](./DESIGN.md) — Design system tokens and patterns
- [`frontend/src/types/governance.ts`](../frontend/src/types/governance.ts) — InboxTrip, InboxFilters types
- [`frontend/src/app/inbox/page.tsx`](../frontend/src/app/inbox/page.tsx) — Current implementation
- [Nielsen Norman Group: Cards Component](https://www.nngroup.com/articles/cards-component/) — Card layout research
- [P1 Solo Agent Happy Path](../Docs/personas_scenarios/P1_SINGLE_AGENT_HAPPY_PATH.md) — Primary persona
- [P2 Training Time Problem](../Docs/personas_scenarios/P2_TRAINING_TIME_PROBLEM.md) — Onboarding persona

---

*This directive was written through code-level analysis, persona review, design system audit, and UX research synthesis. All implementation work should reference this document. Questions or ambiguities should be resolved by re-reading the Problem Statement and Design Principles sections before making assumptions.*
