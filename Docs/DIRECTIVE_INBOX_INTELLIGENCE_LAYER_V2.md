# Inbox Intelligence Layer v2 — Comprehensive Directive

**Date**: Thursday, April 23, 2026
**Revised**: Thursday, April 23, 2026 (post-review)
**Priority**: High (P1)
**Goal**: Transform the Inbox from a static link-list into a role-aware, progressively disclosed Active Inspection Portal that teaches new operators while accelerating experienced ones.
**Supersedes**: [`DIRECTIVE_INBOX_COCKPIT_EVOLUTION.md`](./DIRECTIVE_INBOX_COCKPIT_EVOLUTION.md) (dated 2026-04-22)
**Review Status**: Reviewed. Revised per feedback. Ready for implementation.

---

## 1. Problem Statement

### What We Know From Code & User Research

The current inbox (`frontend/src/app/inbox/page.tsx`) presents 12+ data points per card with equal visual weight. The `InboxTrip` type defines rich dimensions (priority, stage, SLA, value, assignment, flags, days in stage), but the card renders them as a flat grid of badges and text. This creates three classes of problems:

1. **New Operator Paralysis**: Priority, Stage, and SLA all appear as colored pills in the same visual band. A new agent cannot distinguish "how urgent is this?" (priority) from "where is it in workflow?" (stage) from "is it overdue?" (SLA). The `DIRECTIVE_INBOX_COCKPIT_EVOLUTION` correctly identified this as tribal knowledge, but its proposed solution (a hover legend) keeps the burden on the user to seek help.

2. **Comparison Friction**: Nielsen Norman Group card research confirms that card layouts deemphasize ranking and make comparison harder than list views. Our agents' core job is to compare 20 trips and pick one. The current layout makes this harder because value, days, party size, and date all compete for attention in the same row.

3. **One-Size-Fits-All Failure**: The card assumes every user cares about the same fields in the same order. A finance reviewer scanning for pipeline value has different needs than a fulfillment coordinator checking booking confirmations. The existing directive had no mechanism for this.

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

**Team Lead view**:
`[Assignee] · [SLA status] · [Days in stage] · [Priority score]`

**Finance view**:
`[Value] · [Stage] · [Date] · [Priority]`

**Fulfillment view**:
`[Date] · [Assignee] · [Stage] · [Party]`

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

**Implementation**: Compute `percentage = (daysInCurrentStage * 24) / slaHours * 100`. Display raw days + percentage.

**Precondition / Verification Gate**: Before Phase 1, confirm the runtime inbox payload includes either:
- `slaHours` per stage (from `PipelineStage` or embedded in trip metadata), or
- Enough information to derive it (e.g., `stage` + a client-side lookup table as fallback)

If `slaHours` is not available at runtime, implement a narrow contract extension (add `slaHours` to the stage metadata in the inbox response) rather than contorting the frontend. This is a data contract addition, not a new endpoint.

**Color logic** (unchanged):
- `on_track`: green (`STATE_COLORS.green`)
- `at_risk`: amber (`STATE_COLORS.amber`)
- `breached`: red (`STATE_COLORS.red`)

**Why**: A fulfillment agent seeing `6d` on a Booking card knows it's fine. An intake agent seeing `6d` knows it's catastrophic. Same number, different meaning.

### 4.4 Progressive Micro-Labels

For users with < `MICRO_LABEL_THRESHOLD` inbox visits (tracked in `localStorage`):

```
[🔴 Critical · needs human review]  [Intake · just arrived]  [On Track · within SLA]
```

After `MICRO_LABEL_THRESHOLD` visits, collapse to:
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

Ship **2 default presets** initially. Gate the rest for post-launch validation.

| Preset | Filters Applied | Rationale | Status |
|--------|-----------------|-----------|--------|
| **My Urgent** | Assigned to me + Priority ≥ High | Agent's daily driver | **Ship** |
| **Needs Owner** | Unassigned + SLA Breached | Team Lead triage | **Ship** |
| **Stale Bookings** | Stage = Booking + Days > 7 | Fulfillment coordination | **Gate** — validate workflow volume first |
| **High Value Pipeline** | Value > $100k + Stage ≠ Booked | Finance review | **Gate** — too speculative without usage data |

**UX note**: Since we have no launched usage data, presets are hypotheses. The preset system should support applying saved combos, but **preset CRUD (create, rename, update, delete) is out of scope for the first implementation wave**. Add CRUD only after proving preset usage > 15% of sessions.

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
- `View workspace`: Standard navigation
- `Snooze`: *Only if snooze already exists in the current workflow backend*. If snooze mutation does not exist, omit this action from first pass. Do not invent new workflow state for UI sugar.

**Touch fallback**: On touch devices where hover is unavailable, quick actions are always visible as compact icon buttons (not hover-dependent).

### 6.3 View Profile Toggle

A subtle icon-toggle near the sort dropdown:

```
[👤 Operations] [📊 Team Lead] [💰 Finance] [📦 Fulfillment]
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

### 6.5 Sort Behavior Definition

The directive must define how sort interacts with filters, presets, and view profiles:

**Canonical sort options**:
| Sort Key | Default Direction | Rationale |
|----------|-------------------|-----------|
| `priority` | `desc` | Most urgent first |
| `sla` | `asc` | Most at-risk first |
| `value` | `desc` | Highest value first |
| `destination` | `asc` | Alphabetical |
| `party` | `desc` | Larger groups first |
| `dates` | `asc` | Soonest first |

**Interaction rules**:
- Sort is independent of filters and view profiles
- Presets do NOT override sort; they only set filters
- View profiles do NOT override sort; they only reorder visible metrics
- Default sort: `priority` descending
- Sort state persists to URL query params (`?sort=priority&dir=desc`) and `localStorage`
- URL sort params take precedence over `localStorage` on load

---

## 7. Design Token Compliance

### 7.1 Mandatory Token Usage

The current `TripCard` uses inline styles (`style={{ color: meta.color }}`). V2 must use existing design tokens where available:

- `STATE_COLORS` from `tokens.ts` for all status badges
- `COLORS` tokens for text, backgrounds, borders
- `SPACING` tokens for padding/gaps
- `RADIUS` tokens for border radius
- `FONT_SIZE` / `FONT_WEIGHT` for typography

**Verification gate (before Phase 1)**: Confirm `STATE_COLORS` and `CardAccent` are importable and compile in the inbox context. If token names differ from what is documented in `DESIGN.md`, adapt to the canonical token surface rather than inventing aliases. Do not add new token definitions unless the existing system is genuinely missing a required value.

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

### 8.1 Backend Changes: Target Minimal, Verify First

**Target**: No new backend endpoints.

**Precondition verification required** before Phase 1:

| Field / Capability | Where Defined | Runtime Verification Needed |
|--------------------|---------------|----------------------------|
| `trip.flags` | `InboxTrip` type | Confirm populated in actual API response |
| `trip.priorityScore` | `InboxTrip` type | Confirm populated in actual API response |
| `trip.customerName` | `InboxTrip` type | Confirm populated in actual API response |
| `trip.assignedToName` | `InboxTrip` type | Confirm populated in actual API response |
| `daysInCurrentStage` | `InboxTrip` type | Already used; confirmed |
| Stage-to-SLA mapping | `PipelineStage.slaHours` | Confirm available in runtime payload or deriveable |
| Multi-select filtering | `InboxFilters` type | Confirm `useInboxTrips` hook + API support multi-select, not just type definition |

**Fallback**: If any field is absent in the runtime payload, allow a narrow contract extension (add field to response shape) rather than contorting the frontend. This is data contract evolution, not new endpoint creation.

**No changes to `InboxTrip` or `InboxFilters` types** — V2 is a pure UI/UX layer on top of existing contracts, assuming runtime data matches type definitions.

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

---

---

## 9. Implementation Phases

**Reordering rationale**: Do semantic correctness before behavioral sugar. Data helpers and contextual SLA affect meaning. Micro-label fade logic and presets are convenience layers that belong last.

---

### Phase 1: Semantic Foundation + Data Helpers
**Effort**: Small | **Files**: 1-2 new

1. Verify runtime payload fields (`flags`, `priorityScore`, `customerName`, `assignedToName`)
2. Verify `STATE_COLORS`, `CardAccent` imports compile in inbox context
3. Build `frontend/src/lib/inbox-helpers.ts`:
   - SLA percentage computation
   - Filter serialization / deserialization
   - Sort behavior definitions (see 9.6)
   - `MICRO_LABEL_THRESHOLD` constant (default: 3)
4. Expand search logic to include `customerName`, `assignedToName`

**Success criteria**:
- Runtime payload audit documented (which fields present/absent)
- Token imports compile without error
- Helpers unit-tested
- Search finds trips by customer name and agent name

---

### Phase 2: Card Restructure
**Effort**: Medium | **Files**: 2 new, 1 modified

1. Extract `TripCard` to standalone component (`frontend/src/components/inbox/TripCard.tsx`)
2. Implement left accent bar (`CardAccent`), row grouping, de-emphasized trip ID
3. Implement contextual SLA badge (using helpers from Phase 1)
4. Implement status row (SLA + assignee + flags)
5. Use verified design tokens throughout

**Success criteria**:
- Card renders all existing data with new hierarchy
- Contextual SLA displays correctly per stage
- No visual regressions on existing functionality
- All tests pass

---

### Phase 3: Composable Filters
**Effort**: Medium | **Files**: 2-3 new, 1 modified

1. Build `FilterBar` with multi-select dropdowns
2. Wire to existing `useInboxTrips(filters)` hook
3. Add active filter chips with remove functionality
4. Add URL serialization for filter state
5. Replace existing tab bar
6. Define canonical sort behavior (see 9.6)

**Success criteria**:
- User can combine Priority + SLA + Assignment filters
- Filter state survives page refresh (URL)
- Sort state persists to URL and `localStorage`
- "Clear all" resets to default
- No performance degradation with 20 trips

---

### Phase 4: View Profiles
**Effort**: Small | **Files**: 1-2 new, 1 modified

1. Build `ViewProfileToggle` with 4 profiles (Operations, Team Lead, Finance, Fulfillment)
2. Implement role-dependent `MetricsRow` ordering
3. Add `localStorage` persistence for selected profile

**Success criteria**:
- Switching profile reorders metrics instantly
- Selected profile persists across sessions
- All 4 profiles render correctly

---

### Phase 5: Onboarding + Presets + Quick Actions + Polish
**Effort**: Small-Medium | **Files**: 2-3 new, 2 modified

1. Implement progressive micro-labels (`localStorage` visit counting)
2. Add persistent tooltips to all badges
3. Implement hover-revealed quick-action chips (Assign, View workspace; Snooze only if backend exists)
4. Add touch fallback for quick actions (always-visible icon buttons)
5. Implement 2 default presets (My Urgent, Needs Owner)
6. Add smooth transitions (200ms, ease)
7. Keyboard accessibility audit
8. Mobile responsiveness check

**Success criteria**:
- New user sees micro-labels; returning user sees clean badges
- Hover/touch actions visible and clickable
- Presets apply correct filter combinations
- Keyboard navigable throughout
- Mobile layout functional (single column stack)

---

## 10. Testing Strategy

### 10.1 Unit Tests

| Component | Test |
|-----------|------|
| `TripCard` | Renders correct row order for each view profile |
| `TripCard` | Shows micro-labels when visitCount < `MICRO_LABEL_THRESHOLD` |
| `TripCard` | Hides micro-labels when visitCount >= `MICRO_LABEL_THRESHOLD` |
| `FilterBar` | Applies multiple filters correctly |
| `FilterBar` | URL serialization round-trips |
| `useInboxView` | Persists to localStorage |
| `inbox-helpers` | SLA percentage computation correct |

### 10.2 Integration Tests

| Flow | Test |
|------|------|
| Filter → Sort → View Profile | All three states compose correctly |
| Preset apply → clear → URL share | Preset loads, clears, and link shares correctly |
| New user journey | First visit shows labels, `MICRO_LABEL_THRESHOLD+1` visit hides them |

### 10.3 Visual Regression

- Screenshot comparison for all 4 view profiles
- Screenshot comparison for filter active / inactive states

---

## 11. Rollback Plan

If any phase causes issues:
1. **Phase 1-2**: Feature-flag the new card/filter components. Keep old components in codebase under `_legacy` suffix. Toggle via env var.
2. **Phase 3-5**: Purely additive. Can be disabled individually.
3. **Data safety**: Target is frontend-only. If a narrow backend contract extension was needed for SLA data, rollback includes reverting that extension.

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

*This directive was written through code-level analysis, persona review, design system audit, and UX research synthesis. It was reviewed against project standards (`IMPLEMENTATION_AGENT_REVIEW_HANDOFF_CHECKLIST.md`, `DESIGN.md`, and persona documents) and revised to address verification gaps, role-model overfitting, and scope discipline. All implementation work should reference this document. Questions or ambiguities should be resolved by re-reading the Problem Statement and Design Principles sections before making assumptions.*
