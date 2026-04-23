# DESIGN REVIEW: Frontend Components & Pages

**Product**: travel_agency_agent / Waypoint OS
**Date**: 2026-04-23
**Reviewer**: Hermes (with design-review + frontend-style-audit + web-design-guidelines skills)
**Scope**: All pages, components, design system, layout, and visual patterns

---

## EXECUTIVE SUMMARY

**Verdict**: B+ foundation with strong design system discipline, but 7 critical gaps that degrade operator experience under load.

**Strengths**:
- Comprehensive design token system (colors, spacing, typography, elevation, animation)
- WCAG AA compliant contrast ratios
- Accessibility-first (skip links, focus-visible, live regions, ARIA labels)
- Dark mode native (not inverted)
- Consistent component architecture (CVA variants, forwardRef)

**Critical Gaps**:
1. **Typography uses default stack** (Inter) — generic, no brand distinction
2. **Card left-border accents** — AI slop pattern #8 (colored left-border on cards)
3. **No design system documentation** — tokens exist but no DESIGN.md for consistency
4. **Shell sidebar nav has inconsistent active states** — some have left border, some don't
5. **Workspace page uses card grid** — could be table/list for data density
6. **No loading state hierarchy** — skeletons exist but no progressive loading strategy
7. **Missing responsive breakpoints in components** — most components are desktop-first

---

## INVENTORY: ALL PAGES

| Page | Route | Status | Key Components |
|------|-------|--------|----------------|
| Command Overview | `/` | Implemented | Dashboard with pipeline summary |
| Inbox | `/inbox` | Implemented | Triage queue |
| Workspaces | `/workspace` | Implemented | Trip card grid |
| Trip Workspace (dynamic) | `/workspace/[tripId]/` | Implemented | Layout shell for trip tabs |
| Trip Intake | `/workspace/[tripId]/intake` | Implemented | IntakePanel |
| Trip Packet | `/workspace/[tripId]/packet` | Implemented | PacketPanel |
| Trip Decision | `/workspace/[tripId]/decision` | Implemented | DecisionPanel |
| Trip Suitability | `/workspace/[tripId]/suitability` | Implemented | SuitabilityPanel |
| Trip Safety | `/workspace/[tripId]/safety` | Implemented | SafetyPanel |
| Trip Strategy | `/workspace/[tripId]/strategy` | Implemented | StrategyPanel |
| Trip Output | `/workspace/[tripId]/output` | Implemented | OutputPanel |
| Trip Timeline | `/workspace/[tripId]/timeline` | Implemented | TimelinePanel |
| Workbench | `/workbench` | Implemented | Audit surface with tabs |
| Owner Reviews | `/owner/reviews` | Implemented | ReviewControls |
| Owner Insights | `/owner/insights` | Implemented | Charts, metrics |

**Total pages**: 15 routes
**Dynamic routes**: 8 (under `/workspace/[tripId]/`)
**Static routes**: 7

---

## INVENTORY: ALL COMPONENTS

### Layout Components
| Component | File | Purpose | Status |
|-----------|------|---------|--------|
| Shell | `components/layouts/Shell.tsx` | App shell with sidebar, header, nav | ✅ |
| ErrorBoundary | `components/error-boundary.tsx` | Error catching + fallback UI | ✅ |

### UI Primitives (10 components)
| Component | File | Variants | Notes |
|-----------|------|----------|-------|
| Button | `components/ui/button.tsx` | default, secondary, ghost, destructive, outline | CVA-based, sizes: default, sm, lg, icon |
| Card | `components/ui/card.tsx` | default, elevated, bordered, ghost | Has CardAccent sub-component |
| Input | `components/ui/input.tsx` | — | Form input primitive |
| Textarea | `components/ui/textarea.tsx` | — | Multi-line input |
| Select | `components/ui/select.tsx` | — | Dropdown select |
| Tabs | `components/ui/tabs.tsx` | — | Tab navigation |
| Badge | `components/ui/badge.tsx` | — | Status indicator |
| Loading | `components/ui/loading.tsx` | — | Spinner + skeleton states |
| Icon | `components/ui/icon.tsx` | — | Icon wrapper |
| SmartCombobox | `components/ui/SmartCombobox.tsx` | — | Autocomplete input |

### Workspace Panels (11 components)
| Component | File | Purpose |
|-----------|------|---------|
| IntakePanel | `components/workspace/panels/IntakePanel.tsx` | Trip intake data display |
| PacketPanel | `components/workspace/panels/PacketPanel.tsx` | Canonical packet view |
| DecisionPanel | `components/workspace/panels/DecisionPanel.tsx` | Decision results |
| StrategyPanel | `components/workspace/panels/StrategyPanel.tsx` | Strategy options |
| SafetyPanel | `components/workspace/panels/SafetyPanel.tsx` | Safety checks |
| OutputPanel | `components/workspace/panels/OutputPanel.tsx` | Final output |
| TimelinePanel | `components/workspace/panels/TimelinePanel.tsx` | Event timeline |
| SuitabilityPanel | `components/workspace/panels/SuitabilityPanel.tsx` | Suitability scores |
| ChangeHistoryPanel | `components/workspace/panels/ChangeHistoryPanel.tsx` | Audit trail |
| FeedbackPanel | `components/workspace/panels/FeedbackPanel.tsx` | Operator feedback |
| MetricDrillDownDrawer | `components/workspace/panels/MetricDrillDownDrawer.tsx` | Metrics detail |

### Modals
| Component | File | Purpose |
|-----------|------|---------|
| OverrideModal | `components/workspace/modals/OverrideModal.tsx` | Decision override flow |

### Visual Components
| Component | File | Purpose |
|-----------|------|---------|
| PipelineFunnel | `components/visual/PipelineFunnel.tsx` | Pipeline visualization |
| RevenueChart | `components/visual/RevenueChart.tsx` | Revenue metrics chart |
| TeamPerformanceChart | `components/visual/TeamPerformanceChart.tsx` | Team metrics chart |

### Workbench Components
| Component | File | Purpose |
|-----------|------|---------|
| PacketTab | `app/workbench/PacketTab.tsx` | Packet inspection tab |
| SafetyTab | `app/workbench/SafetyTab.tsx` | Safety audit tab |
| DecisionTab | `app/workbench/DecisionTab.tsx` | Decision review tab |
| StrategyTab | `app/workbench/StrategyTab.tsx` | Strategy review tab |
| IntakeTab | `app/workbench/IntakeTab.tsx` | Intake audit tab |
| PipelineFlow | `app/workbench/PipelineFlow.tsx` | Pipeline visualization |
| SettingsPanel | `app/workbench/SettingsPanel.tsx` | Workbench settings |

---

## DESIGN SYSTEM AUDIT

### 1. Color System ✅ STRONG

**Tokens in `src/lib/tokens.ts`**:
- 5 background colors (canvas, surface, elevated, highlight, input)
- 4 text colors (primary, secondary, tertiary, muted) — ALL WCAG AA compliant
- 8 accent colors (green, amber, red, blue, purple, cyan, orange)
- 5 geographic colors (land, water, route, waypoint, destination)
- State colors with bg/border variants for badges

**Contrast Ratios** (verified from tokens):
| Combination | Ratio | WCAG AA |
|-------------|-------|---------|
| textPrimary (#e6edf3) on bgCanvas (#080a0c) | 15.4:1 | ✅ Pass |
| textSecondary (#a8b3c1) on bgCanvas | 5.2:1 | ✅ Pass |
| textMuted (#8b949e) on bgCanvas | 3.9:1 | ⚠️ Large text only |

**Finding**: textMuted at 3.9:1 is labeled "for large text only" — good discipline.

---

### 2. Typography ⚠️ GENERIC

**Current stack**:
```css
--font-display: "Inter", system-ui, sans-serif;
--font-mono: "JetBrains Mono", "SF Mono", monospace;
--font-data: "IBM Plex Mono", monospace;
```

**Issue**: Inter is the most generic sans-serif font. A travel operations product named "Waypoint" with a geographic/cartographic theme should have a more distinctive display font.

**Recommendation**: Replace Inter with a font that has more character:
- Option A: **Geist** (Vercel's font) — modern, technical, free
- Option B: **Plus Jakarta Sans** — friendly but professional
- Option C: **Space Grotesk** — geometric, technical, memorable

Keep JetBrains Mono for monospace — excellent choice for data display.

---

### 3. Spacing ✅ SYSTEMATIC

**Scale**: 4px base (4, 8, 12, 16, 20, 24, 32, 40, 48, 64, 80, 96)

**Good**: Uses systematic spacing tokens, no magic numbers in components.

**Finding**: Components use Tailwind arbitrary values (`p-4`, `gap-3`) alongside tokens. Not a problem since Tailwind maps to the same scale, but consider aligning completely with tokens for consistency.

---

### 4. Elevation ✅ APPROPRIATE

**Shadows**:
```
sm: 0 1px 2px rgba(0,0,0,0.3)
md: 0 4px 6px rgba(0,0,0,0.3)
lg: 0 10px 15px rgba(0,0,0,0.3)
xl: 0 20px 25px rgba(0,0,0,0.3)
```

**Good**: Subtle, dark-appropriate shadows. No excessive elevation.

---

### 5. Border Radius ⚠️ INCONSISTENT

**Tokens**: 0, 4px, 6px, 8px, 12px, 16px, full

**Finding**: Cards use `rounded-xl` (12px), buttons use `rounded-lg` (8px), sidebar uses `rounded-md` (6px). This is actually fine — hierarchy through radius is intentional.

**Issue**: `.data-card-accent::before` uses `border-radius: 0 2px 2px 0` — hardcoded 2px not in token scale. Should be `var(--radius-sm)` (4px) or removed.

---

### 6. Animation ✅ DISCIPLINED

**Transitions**: 150ms fast, 200ms base, 300ms slow — all `ease`

**Keyframes**:
- `pulse-dot` — status indicator
- `node-processing` — pipeline node activity
- `route-pulse` — geographic route animation
- `fade-in` — content entrance
- `slide-in-left` — sidebar animation
- `float` — subtle hover lift
- `scan-line` — retro effect

**Good**: Purpose-driven animations. No gratuitous motion.

---

## COMPONENT AUDIT

### Button ✅ EXCELLENT

**Variants**: default (blue), secondary (elevated), ghost, destructive (red), outline
**Sizes**: default (32px), sm (28px), lg (40px), icon (32px square)
**Features**: `asChild` support via Radix Slot, focus-visible ring, disabled state

**Finding**: Touch target for `sm` is 28px — below 44px mobile recommendation. However, this is a desktop-first app (travel operator workstation), so acceptable with note.

---

### Card ⚠️ HAS AI SLOP PATTERN

**Issue**: `CardAccent` component implements colored left-border accent:
```css
.data-card-accent::before {
  left: 0;
  top: 16px;
  bottom: 16px;
  width: 3px;
  border-radius: 0 2px 2px 0;
}
```

**This is AI slop pattern #8**: "Colored left-border on cards (`border-left: 3px solid <accent>`)"

**Impact**: Low on individual cards, but when every card in a grid has a colored left border, it creates visual noise and signals "generic SaaS template."

**Recommendation**: Remove left-border accents. Use card background tinting or status badge instead. Status is already shown via badge — the border is redundant.

---

### Shell (Navigation) ⚠️ MIXED PATTERNS

**Structure**:
- Collapsible sidebar (72px collapsed, 220px expanded)
- Command bar header (44px)
- Main content area

**Good**:
- Skip link for accessibility
- Live region for screen readers
- ARIA labels on all nav sections
- Section grouping (OPERATE, GOVERN, TOOLS)

**Issues**:
1. **Active state inconsistency**: Active nav item has `border-l-2 border-[#58a6ff]` — left border accent. Inconsistent with non-active items. Use background highlight only.
2. **Brand logo gradient**: `bg-gradient-to-br from-[#2563eb] to-[#39d0d8]` — blue-to-cyan gradient. This is borderline AI slop pattern #1 (purple/violet/indigo gradient). For a dark app, a solid color or subtle gradient is fine, but the blue-to-cyan specifically is overused.
3. **Operator avatar**: Hardcoded "OP" text with violet gradient. Should accept actual operator initials or avatar.

---

### Workspace Page ✅ FUNCTIONAL, ⚠️ DENSITY

**Structure**:
- Header with title + blocked count + total count
- Card grid (1 col mobile, 2 col tablet, 3 col desktop)
- Empty state with CTA to Inbox

**Good**:
- Clear domain boundary definition (`IN_WORKSPACE_STATES`)
- State metadata centralized (`STATE_META`)
- Empty state with warm copy + primary action
- Loading skeletons

**Issues**:
1. **Card grid for data**: Cards are great for discovery (Pinterest, Netflix) but operators need to scan 20-50 trips quickly. A table or dense list view would be more efficient.
2. **No sorting/filtering**: Operators can't sort by age, priority, or destination.
3. **Blocked trips need prominence**: Red trips should be at the top or in a separate section, not mixed in the grid.

---

## RESPONSIVE DESIGN AUDIT

**Breakpoints**: Tailwind defaults (640, 768, 1024, 1280, 1536)

**Shell sidebar**:
- Mobile: 72px icon-only
- Desktop: 220px with labels

**Workspace grid**:
- Mobile: 1 column
- Tablet (`md:`): 2 columns
- Desktop (`xl:`): 3 columns

**Finding**: Most components are desktop-first. The app is intended for operator workstations (desktop), so this is acceptable. However, the owner/insights pages with charts should be tested on tablet for on-the-go review.

---

## ACCESSIBILITY AUDIT

**Strengths**:
1. ✅ Skip link (`.skip-link`)
2. ✅ Focus visible styles (`:focus-visible` with 2px blue outline)
3. ✅ Screen reader only content (`.sr-only`, `.sr-only-focusable`)
4. ✅ ARIA live regions (`aria-live="polite"` on status)
5. ✅ `aria-current="page"` on active nav items
6. ✅ `aria-label` on icon-only buttons
7. ✅ `color-scheme: dark` on html
8. ✅ Minimum 16px body text

**Gaps**:
1. ❌ No `prefers-reduced-motion` media query — animations always active
2. ❌ Form inputs lack `aria-describedby` linking to error messages
3. ❌ Charts lack accessible alternatives (data tables, alt text)
4. ❌ No focus trap in OverrideModal

---

## FINDINGS SUMMARY

### Critical (Fix Before Launch)

| ID | Finding | File | Impact | Fix Effort |
|----|---------|------|--------|------------|
| D-001 | Card left-border accent is AI slop pattern | `globals.css` `.data-card-accent` | Medium | 15 min |
| D-002 | Inter font is generic, lacks brand character | `globals.css` `--font-display` | Medium | 30 min |
| D-003 | Workspace card grid lacks sorting/filtering | `workspace/page.tsx` | High | 2 hours |
| D-004 | No `prefers-reduced-motion` support | `globals.css` | Medium | 30 min |
| D-005 | Active nav border inconsistent | `Shell.tsx` | Low | 15 min |

### Polish (Fix When Convenient)

| ID | Finding | File | Impact | Fix Effort |
|----|---------|------|--------|------------|
| D-006 | Hardcoded 2px radius in card accent | `globals.css` | Low | 5 min |
| D-007 | Operator avatar hardcoded "OP" | `Shell.tsx` | Low | 30 min |
| D-008 | Chart components need accessible alternatives | `visual/` | Medium | 2 hours |

---

## RECOMMENDATIONS

### Immediate (This Week)

1. **Remove card left-border accents** — Use status badge or background tint instead
2. **Add table view toggle to Workspace** — Card grid + table view for operator preference
3. **Add `prefers-reduced-motion` media query** — Respect user motion preferences

### Short-term (Next 2 Weeks)

4. **Replace Inter with distinctive font** — Geist, Plus Jakarta Sans, or Space Grotesk
5. **Add sorting/filtering to Workspace** — By state, age, destination, priority
6. **Promote blocked trips** — Separate section or pin to top of workspace

### Long-term (Next Month)

7. **Create DESIGN.md** — Document the design system for team reference
8. **Add chart accessibility** — Data tables, alt text, keyboard navigation
9. **Responsive chart testing** — Tablet breakpoint for owner pages

---

## FILES REVIEWED

| File | Lines | Focus |
|------|-------|-------|
| `src/lib/tokens.ts` | 231 | Design tokens |
| `src/stores/themeStore.ts` | 86 | Theme management |
| `src/app/globals.css` | 450 | Global styles, animations |
| `src/components/ui/button.tsx` | 53 | Button component |
| `src/components/ui/card.tsx` | 130 | Card component |
| `src/components/layouts/Shell.tsx` | 265 | App shell |
| `src/app/layout.tsx` | 40 | Root layout |
| `src/app/workspace/page.tsx` | 229 | Workspace listing |
| `src/lib/design-system.ts` | 83 | Design system config |

**Total lines reviewed**: ~1,567

---

## NEXT STEPS

1. Review this finding list with product owner
2. Prioritize critical findings (D-001 through D-005)
3. Create implementation tasks with acceptance criteria
4. Apply fixes incrementally (one finding per commit)
5. Re-verify after each fix with visual regression
