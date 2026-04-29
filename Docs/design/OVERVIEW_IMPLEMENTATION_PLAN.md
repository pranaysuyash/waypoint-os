# Implementation Plan: /overview Visual System Pass

Reference screenshot taken 2026-04-29. URL: http://localhost:3000/overview (empty state, zero trips).

---

## Visual Assessment of Screenshot

### What's Working
1. Severity grammar is **correct**: blue = primary/action, green = ready/success, amber = pending, red = critical.
2. Cards are visible against canvas (borders exist, surfaces separate).
3. Sidebar structure is sound (brand, nav sections, footer status).
4. Layout grid is balanced (`grid-cols-4` stats + `grid-cols-3` content).

### What's Broken

#### 1. Weak Visual Hierarchy (P0)
- **Stat card labels** ("ACTIVE TRIPS") compete with the metric value (`0`). The label is uppercase tracking-widest but uses gray (`#8b949e`) which is too close to background.
- **Metric values** (`0`) are colored but not large enough to anchor attention. They should be the dominant element.
- **Page title** "Operations Overview" is clear but "Waypoint OS · your travel agency workspace" is placeholder copy, not operational context.
- **Subtexts** ("0 total", "new entries") use monospace but don't communicate meaning. They feel like raw data, not summary.

#### 2. Cards Feel Like Empty Bordered Boxes (P0)
- Stat cards have no internal hierarchy. All elements are similarly weighted.
- No spatial separation between label, value, and subtext.
- Hover state (`hover:border-[#30363d]`) is too subtle.

#### 3. Empty State Looks Accidental (P0)
- Briefcase icon inside a 48px gray circle is too small and too dim.
- "No trips yet" is centered but the entire area feels like unfinished wiring, not an intentional first-run experience.
- "Process Your First Trip" button is generic solid-blue Bootstrap style.

#### 4. Sidebar Active State Is Not Obvious (P1)
- "Overview" active row uses `var(--bg-elevated)` + blue icon. This is visible but not immediate.
- The `rounded-md` on active nav items makes them feel like buttons, not nav selections.
- Missing left-edge accent line (decorative in old docs, but functional here: it creates directional hierarchy).

#### 5. Right Rail Is Disconnected (P1)
- "Trip Progress" with `0` total and a thin gray bar is meaningless when empty.
- "Jump To" icon containers are 8px with rounded corners but icons vary in color per link — creates visual noise.
- Decision state dots are 6px — functional but easily missed.

#### 6. Broken Text Size System (P1)
- `text-ui-sm`, `text-ui-xs`, `text-ui-3xl` etc. are used throughout but their CSS variables (`--ui-text-xs`, `--ui-text-sm`) **do not exist in globals.css**. Tailwind resolves them to nothing at build time. This means text sizes are unpredictable.

---

## Implementation Plan

### Phase 1: Fix Token Foundation (globals.css)

Add missing CSS variables for the app UI text scale. These are referenced in tailwind.config.js but never defined.

| Variable | Value | Purpose |
|----------|-------|---------|
| `--ui-text-2xs` | `10px` | Metadata, timestamps |
| `--ui-text-xs` | `11px` | Section labels, captions |
| `--ui-text-sm` | `12px` | Secondary labels, descriptions |
| `--ui-text-base` | `13px` | Body text, nav labels |
| `--ui-text-lg` | `14px` | Emphasized body |
| `--ui-text-xl` | `16px` | Section headings |
| `--ui-text-2xl` | `18px` | Page title |
| `--ui-text-3xl` | `24px` | Metric values |
| `--ui-text-4xl` | `32px` | Hero metrics |

Also add missing spacing/structural tokens that will be needed:
- `--sidebar-active-indicator: var(--accent-blue)`
- `--card-stat-metric-color` (maps to severity color dynamically)

### Phase 2: Rewrite /overview/page.tsx

**StatCard rewrite:**
- Metric value becomes the anchor: 24px bold, colored by severity.
- Label becomes secondary: 11px uppercase tracking-wide, gray, positioned ABOVE the value.
- Icon badge shrinks to 28px container, metric-colored, placed top-right (decorative, not competing).
- Subtext becomes tertiary: 12px, gray, below value, NOT monospace (reads better).
- Hover: border lightens to `var(--border-hover)`, background shifts to `var(--bg-elevated)`.
- Error state: red left border strip, not full red card.

**RecentTrips (empty state) rewrite:**
- Larger empty-state icon: 24px inside a 56px container with subtle border.
- Title: "Start with your first trip" — active, not passive.
- Description: actual next step, not generic "process your first customer inquiry".
- CTA button: ghost style (border + text) on dark, not solid blue.

**RecentTrips (populated) rewrite:**
- ActivityRow: destination is 13px medium (primary). Type and ID are 11px gray (secondary). State badge is compact pill. Age is 11px right-aligned.
- Chevron is 16px, muted, appears on hover.
- Hover background shifts subtly.

**PipelineBar rewrite:**
- Empty state: show placeholder text "No active pipeline data" + link to Workbench.
- Collapsed state: single stacked bar with segments proportional to counts.
- Expanded: vertical list with thin proportional bars.

**Header rewrite:**
- Breadcrumb: quieter, 12px.
- Title: 18px semibold.
- Subtitle: 13px gray, operational (e.g., "12 trips · 3 need attention" when populated).
- CTA link: ghost style, not blue text.

**Right Rail rewrite:**
- Jump To: remove individual icon color variance. All icons `#8b949e`, all containers uniform. Only the dot + count conveys severity.
- Decision States: dots increase to 8px. Labels are 12px, not monospace.
- Trip Progress: when empty, show placeholder "Pipeline will appear here" instead of a useless `0`.

### Phase 3: Shell.tsx Refinements

- Active nav: add 2px left edge blue indicator (not decoration — directional hierarchy signal).
- Active nav background: `var(--bg-elevated)` stays, but border-radius reduced from `rounded-md` to `rounded-sm` (less button-like).
- Section labels (WORK, MANAGE, REVIEW): 10px bold uppercase tracking-wider, `var(--text-muted)`.
- Brand block: make version label (`v0.1.0`) smaller (10px) and dimmer. Agency name prominent.
- Footer status: green pulse dot stays, but move to a single line with icon + text.

### Phase 4: Component Grammar Additions

**Card grammar** (for app use, not marketing):
- Stat cards: metric-first, label-above, explanation-below.
- List panels: header row with icon + title + action link, content area scrolls.
- Right-rail modules: compact, no internal card borders, header is 11px uppercase.

**Icon grammar**:
- Nav icons: 15px, gray (`#8b949e`) inactive, blue (`#58a6ff`) active.
- Metric icons: 16px inside 28px container, colored by severity.
- Empty-state icons: 24px inside 56px container, border + gray.
- Action icons: 16px, consistent placement.

**Severity grammar** (already correct, formalize):
- Blue = action/primary/link/active.
- Green = ready/success/approved.
- Amber = pending/needs options/at-risk.
- Red = critical/error/needs attention.
- Gray = inactive/metadata/placeholder.

### Phase 5: Button Grammar

- Remove solid-blue `default` variant from /overview usage.
- Use `secondary` (bordered gray) or `ghost` (text only) for most actions.
- `default` (solid blue) reserved for: primary CTAs, form submissions, create actions.
- On dark backgrounds, buttons must have visible borders or distinct text color — never rely on background alone.

---

## Files To Modify (Exact List)

1. `frontend/src/app/globals.css` — add missing `--ui-text-*` and `--sidebar-*` variables.
2. `frontend/src/app/(agency)/overview/page.tsx` — full rewrite of StatCard, RecentTrips, ActivityRow, PipelineBar, header, right rail.
3. `frontend/src/components/layouts/Shell.tsx` — active nav indicator, brand block sizing, footer.
4. `frontend/src/components/ui/button.tsx` — variants already decent, but verify no Bootstrap solid-blue usage in overview.
5. `frontend/src/components/ui/card.tsx` — fix `text-[var(--ui-text-*)]` to use actual var or explicit sizes.

## Files NOT To Touch

- `frontend/src/components/marketing/*` — marketing is isolated, not part of this system.
- `frontend/src/app/workbench/*` — out of scope for this pass.
- `frontend/src/app/inbox/*` — out of scope for this pass.
- `frontend/src/lib/tokens.ts` — superseded, but don't delete yet.

---

## Verification Steps

1. Build passes: `cd frontend && npm run build`.
2. Typecheck passes: `npx tsc --noEmit`.
3. Screenshot /overview empty state, compare to "before".
4. Screenshot /overview with populated data (need to create a trip via workbench or mock).
5. Document remaining weaknesses.

---

## Acceptance Criteria

- [ ] /overview empty state looks intentional, not accidental.
- [ ] Stat cards have clear metric-first hierarchy (number is dominant).
- [ ] Sidebar active state is obvious at a glance.
- [ ] All text sizes render correctly (no broken `text-[var(--ui-text-*)]` classes).
- [ ] Icons follow one grammar (sizes, containers, colors governed).
- [ ] No solid-blue generic buttons on /overview (except primary CTAs).
- [ ] Severity colors are meaningful, not decorative.
- [ ] Screenshot comparison shows visible improvement.

## Effort Estimate

- Phase 1 (globals.css): 15 minutes.
- Phase 2 (overview/page.tsx): 2 hours.
- Phase 3 (Shell.tsx): 45 minutes.
- Phase 4–5 (grammar docs): 30 minutes (after code, before handoff).
- Verification + screenshots: 30 minutes.
- **Total: ~4 hours**.
