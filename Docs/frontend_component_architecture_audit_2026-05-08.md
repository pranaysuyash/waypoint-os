# Frontend Component Architecture Audit

**Date:** 2026-05-08  
**Project:** Waypoint OS — AI travel agency workspace  
**Auditor:** Autonomous frontend architecture review  
**Scope:** Component architecture, reuse, extraction, missing UI, design system, premium polish

---

## 1. Actual Frontend Stack and Structure

### Detected Stack

| Layer | Technology | Notes |
|---|---|---|
| **Framework** | Next.js 16 (App Router) | Turbopack enabled |
| **UI Library** | React 19.2.4 | Server components + `"use client"` client boundaries |
| **Type System** | TypeScript 5 | Strong typing throughout, some `as any` escapes |
| **Styling** | Tailwind CSS 3.4 + CSS Modules | Dual approach: Tailwind inline + CSS modules (`*.module.css`) |
| **State (Server)** | TanStack React Query 5 | ~8 hooks using `useQuery`/`useMutation` |
| **State (Client)** | Zustand 5 | 3 stores: `auth`, `workbench`, `themeStore` |
| **State (DI)** | React Context | `TripContext` (DI), `CurrencyContext` (stub) |
| **Icons** | Lucide React | ~30+ distinct icons imported across components |
| **Animation** | GSAP 3.15 | Marketing pages only (ScrollTrigger) |
| **Charts** | Recharts 3.8 | `RevenueChart`, `PipelineFunnel`, `TeamPerformanceChart` |
| **Testing** | Vitest + React Testing Library | 74 test files, 741+ test cases |
| **Accessibility** | Custom utilities + ARIA | `src/lib/accessibility.tsx` (300 lines of ARIA helpers) |
| **Form Components** | Custom (no shadcn/ui) | `Input`, `Select`, `Textarea`, `SmartCombobox` |
| **Design System** | Custom CSS variables + `src/lib/tokens.ts` | OKLCH color tokens defined but **not used** anywhere in components |

### App Entry Points

- **Root layout:** `src/app/layout.tsx` — bare HTML shell, imports `globals.css`
- **Root page:** `src/app/page.tsx` — Marketing landing page (server component + client sub-components)
- **v2 page:** `src/app/v2/page.tsx` — Alternate marketing page (A/B variant)

### Route Groups

| Route Group | Layout | Auth | Purpose |
|---|---|---|---|
| `(agency)/` | `Shell` + `AuthProvider` + `Providers` | Required | Agency workspace (overview, inbox, trips, workbench, insights, reviews, settings, audit) |
| `(auth)/` | Branded centered card | None | Login, signup, forgot/reset password, join via code |
| `(public)/` | Passthrough | None | Booking collection (token-gated) |
| `(traveler)/` | Passthrough | None | Public itinerary checker (no auth needed) |

### Layout Files

- **Root:** `src/app/layout.tsx` — minimal HTML wrapper
- **(auth):** `src/app/(auth)/layout.tsx` — centered card + brand icon + gradient background
- **(agency):** `src/app/(agency)/layout.tsx` — `Providers` > `AuthProvider` > `Shell` > children
- **Trip detail:** `src/app/(agency)/trips/[tripId]/layout.tsx` — workspace header + stage tabs + timeline rail
- **(public), (traveler):** Passthrough

### Screen/Page Files (21 pages)

| Page | File | Lines | Complexity |
|---|---|---|---|
| Home (Marketing) | `src/app/page.tsx` | 455 | Medium (server + client) |
| Itinerary Checker | `src/app/(traveler)/itinerary-checker/page.tsx` | ~2018 | **Very high** — two-view, PDF/OCR, GSAP |
| Workbench | `src/app/(agency)/workbench/page.tsx` | ~1128 | **Very high** — multi-tab, auto-save, spine run |
| Inbox | `src/app/(agency)/inbox/page.tsx` | ~520 | High — sort/filter/paginate/bulk |
| Insights | `src/app/(agency)/insights/page.tsx` | ~621 | High — charts, drill-down, time ranges |
| Overview | `src/app/(agency)/overview/page.tsx` | ~677 | High — stats, pipeline, recent trips |
| Settings | `src/app/(agency)/settings/page.tsx` | ~266 | Medium — multi-tab draft-based save |
| Reviews | `src/app/(agency)/reviews/page.tsx` | ~391 | Medium — filter/approve/reject |
| Audit | `src/app/(agency)/audit/page.tsx` | ~50 | Low |
| Trips list | `src/app/(agency)/trips/page.tsx` | ~387 | Medium — card/table toggle |
| Auth pages (5) | login, signup, forgot, reset, join | ~50-120 each | Low |
| Booking collection | `src/app/(public)/booking-collection/[token]/page.tsx` | ~400 | Medium |
| Trip stages (7) | intake, packet, decision, strategy, suitability, output, safety, timeline, followups | 100-250 each | Medium |

### Shared UI Component Folders

| Folder | Files | Purpose |
|---|---|---|
| `src/components/ui/` | 11 | Primitives: `Button`, `Card`, `Input`, `Select`, `Textarea`, `Tabs`, `Badge`, `Spinner`/`Skeleton`, `PriorityIndicator`, `SmartCombobox`, `Icon` components |
| `src/components/marketing/` | 7 | Server components (`PublicPage`, `PublicHeader`, `PublicFooter`, `SectionIntro`, `Kicker`, `ProofChip`) + client components (`CtaBand`, `DemoButton`, `HeroScene`, `DataTransformationHero`, `AgencyHeroCockpit`, `NotebookAnalyzer`, `GsapInitializer`) |
| `src/components/layouts/` | 2 | `Shell` (app sidebar + header), `UserMenu` |
| `src/components/navigation/` | 1 | `BackToOverviewLink` |
| `src/components/error-boundary.tsx` | 1 | Class boundary, inline error, HOC, hook |

### Feature-Specific UI Folders

| Folder | Files | Purpose |
|---|---|---|
| `src/components/inbox/` | 6 | `TripCard`, `InboxEmptyState`, `InboxFilterBar`, `FilterPill`, `ComposableFilterBar`, `ViewProfileToggle` |
| `src/components/workspace/` | ~20 | Panel components (Intake, Packet, Decision, Strategy, Safety, Output, Timeline, etc.) + `FollowUpCard`, `OverrideModal`, `CaptureCallPanel`, `SuitabilitySignal`, `ActivityTimeline`, etc. |
| `src/components/visual/` | 3 | `RevenueChart`, `PipelineFunnel`, `TeamPerformanceChart` + `AnalyticsEmptyState` |
| `src/components/auth/` | 1 | `AuthProvider` |
| `src/components/overview/` | 1 | `EmptyStateOnboarding` |

### Theme/Design-Token Files

| File | Purpose | Status |
|---|---|---|
| `src/app/globals.css` | CSS custom properties (colors, spacing, typography, radii) | Active, used everywhere |
| `src/lib/tokens.ts` | OKLCH design tokens (COLORS, SPACING, FONT_SIZE, ELEVATION, RADIUS, TRANSITION, Z_INDEX) | **Defined but unused by components** |
| `tailwind.config.js` | Tailwind theme extension mapping CSS vars to classes | Active |
| `DESIGN.md` | 1112-line design system spec | Reference only |
| `src/lib/contrast-utils.ts` | WCAG contrast calculation utilities | Active |
| `src/lib/currency.ts` | Multi-currency formatting + parsing | Active |

### Styling Files

| File | Lines | Purpose |
|---|---|---|
| `src/app/globals.css` | 246 | CSS variables, base styles, utility classes, animations |
| `src/components/marketing/marketing.module.css` | 2672 | Marketing page CSS (gradients, grid, animations, responsive) |
| `src/components/marketing/marketing-v2.module.css` | 2058 | Alternate marketing CSS (hardcoded colors, no custom properties) |
| `src/components/marketing/marketing.bak.module.css` | 1938 | Backup (earlier version) |
| `src/components/workbench/workbench.module.css` | 632 | Workbench panel CSS (uses **different** variable naming: `--color-*` vs `--accent-*`/`--bg-*`) |
| `src/app/(auth)/auth.css` | ~200 | Auth pages CSS |
| `tailwind.config.js` | 120 | Tailwind theme config |

### State Management Files That Influence UI

| File | Lines | Pattern | What It Owns |
|---|---|---|---|
| `src/stores/auth.ts` | 138 | Zustand | User, agency, membership, auth status |
| `src/stores/workbench.ts` | 275 | Zustand | Workbench inputs, draft, config, results (4 slices) |
| `src/stores/themeStore.ts` | 86 | Zustand + persist | Theme, component variants, density, debug mode |
| `src/hooks/useGovernance.ts` | 273 | React Query | Reviews, inbox, insights, team, alerts |
| `src/hooks/useTrips.ts` | 151 | React Query | Trips CRUD, stats, pipeline |
| `src/hooks/useUnifiedState.ts` | 61 | React Query | System health/counts |
| `src/hooks/useIntegrityIssues.ts` | 25 | React Query | Integrity issues |
| `src/hooks/useSpineRun.ts` | 114 | useState+useRef | Spine run execution + polling |
| `src/hooks/useAgencySettings.ts` | 124 | useState+useEffect | Settings (should be React Query) |
| `src/hooks/useRuntimeVersion.ts` | 66 | useState+useEffect | Version labels (should be React Query) |
| `src/hooks/useFieldAuditLog.ts` | 223 | useState+useEffect | Field change audit (localStorage) |
| `src/contexts/TripContext.tsx` | 32 | Context DI | Trip data pass-through |
| `src/contexts/CurrencyContext.tsx` | 66 | Context | Currency preference (stub formatter) |
| `src/components/providers.tsx` | 25 | React Query | QueryClient provider setup |

### Key Structural Observations

1. **Three CSS variable naming conventions coexist:**
   - `--accent-*`, `--bg-*`, `--text-*`, `--border-*` in `globals.css` and most inline styles
   - `--color-*` in `workbench.module.css`
   - Hardcoded hex values inline (marketing components, some cards)

2. **`src/lib/tokens.ts` is defined but unused.** It has OKLCH versions of all colors, spacing objects, typography config, elevation, radius, layout, and z-index — but no component imports it. This is dead code in spirit (a design intent that was never wired in).

3. **Two marketing CSS modules diverge:** `marketing.module.css` uses CSS custom properties; `marketing-v2.module.css` uses hardcoded hex. MarketingVisuals.tsx imports from `marketing.module.css` but uses classes only defined in `marketing-v2.module.css` — likely a bug.

4. **Dual state patterns:** 4 hooks (`useAgencySettings`, `useRuntimeVersion`, `useFieldAuditLog`, `useSpineRun`) use raw `useState`+`useEffect` for what should be React Query. This means no caching, no dedup, and inconsistent error patterns.

5. **`themeStore.ts` is not re-exported from `stores/index.ts`** — inconsistent with auth + workbench stores.

---

## 2. Existing Component/Widget Inventory

### UI Primitives (`src/components/ui/`)

| Component | File | Type | Lines | Reusability | Assessment |
|---|---|---|---|---|---|
| `Button` | `ui/button.tsx` | Shared | ~80 | **Excellent** | 5 variants, 7 sizes, `asChild` via Radix Slot, forwardRef, CVA. Well-tested (14 tests). |
| `Card` + sub-components | `ui/card.tsx` | Shared | ~120 | **Excellent** | 4 variants, `CardHeader/Title/Description/Content/Footer`, dynamic heading levels, forwardRef. Well-tested (6 tests). |
| `Input` | `ui/input.tsx` | Shared | ~90 | **Excellent** | 3 sizes, label/error/description, left/right icons, accessible with generated IDs. Well-tested (15 tests). |
| `Select` | `ui/select.tsx` | Shared | ~90 | **Excellent** | Same API as Input, options/placeholder/empty, custom chevron. Accessible. Not tested. |
| `Textarea` | `ui/textarea.tsx` | Shared | ~60 | **Good** | Same API as Input, configurable resize. Not tested. |
| `Tabs` | `ui/tabs.tsx` | Shared | ~120 | **Excellent** | Full ARIA tab pattern, keyboard nav, count badges, live regions, screen reader announcements. Well-tested (13 tests). |
| `Badge` | `ui/badge.tsx` | Shared | ~50 | **Good** | CVA variants for authority badges (user/owner/derived/hypothesis/manual), 3 sizes. Under-tested. |
| `Spinner`, `Skeleton*`, `LoadingOverlay`, `InlineLoading` | `ui/loading.tsx` | Shared | ~200 | **Excellent** | 7 components: `Spinner` (3 sizes, 5 colors), `Skeleton` (3 variants, 3 animations), `SkeletonText/Avatar/Card`, `LoadingOverlay` (with blur), `InlineLoading`. Well-tested (20 tests). |
| `PriorityIndicator` | `ui/PriorityIndicator.tsx` | Shared | ~100 | **Good** | 3 variants (dual-badge/compact/dot-only), urgency+importance, 4 levels. Memoized. Well-tested (6 tests). |
| `SmartCombobox` | `ui/SmartCombobox.tsx` | Shared | ~280 | **Good** | Fuzzy matching, custom values, duplicate detection, keyboard nav, click-outside, grouped sections. Complex but well-bounded. |
| `IconWrapper`, `IconButton`, `IconLink` | `ui/icon.tsx` | Shared | ~120 | **Good** | 3 icon utilities with proper ARIA, sizes, colors. Not tested. |

### Layout-Level Components

| Component | File | Type | Lines | Assessment |
|---|---|---|---|---|
| `Shell` | `layouts/Shell.tsx` | **Layout** | 294 | Well-architected. Left sidebar (220px/72px responsive), brand, nav sections, CTA, status footer, integrity bar, breadcrumb header, skip-link. ARIA proper. 18 lucide icon imports — some likely unused. |
| `UserMenu` | `layouts/UserMenu.tsx` | **Layout** | 132 | Dropdown with initials avatar, email, agency, role, settings/signout. ARIA menu pattern, outside-click. Clean. |
| `AuthProvider` | `auth/AuthProvider.tsx` | **Layout** | 68 | Hydration gate, redirect logic, public path whitelist. Clean. |
| `Providers` | `providers.tsx` | **Layout** | 25 | QueryClient wrapper. Minimal, correct. |
| `PublicPage` | `marketing/marketing.tsx` | **Layout** | 5 | Marketing page wrapper. Clean. |
| `PublicHeader` | `marketing/marketing.tsx` | **Layout** | ~40 | Sticky nav with brand + links + CTAs. Clean. |
| `PublicFooter` | `marketing/marketing.tsx` | **Layout** | ~20 | Site footer. Clean. |

### Feature-Specific UI

| Component | File | Type | Lines | Assessment |
|---|---|---|---|---|
| `TripCard` | `inbox/TripCard.tsx` | Feature | 425 | Well-modularized. 6 internal sub-components. Priority, SLA, stage, urgency. Memoized, tested (15 tests). |
| `InboxEmptyState` | `inbox/InboxEmptyState.tsx` | Feature/Shared | 113 | 5 contextual messages. Memoized. Reusable pattern. |
| `ComposableFilterBar` | `inbox/ComposableFilterBar.tsx` | Feature | 432 | Data-driven filters, presets, active chips, dropdowns. 3 memoized sub-components. Well-built but **too large** — should split. |
| `FilterPill` | `inbox/FilterPill.tsx` | Feature/Shared | 110 | 4 tones, count, icon, active states. Memoized. **Good extraction candidate for shared UI.** |
| `InboxFilterBar` | `inbox/InboxFilterBar.tsx` | Feature | 54 | Thin wrapper over `FilterPill`. Slightly redundant. |
| `ViewProfileToggle` | `inbox/ViewProfileToggle.tsx` | Feature/Shared | 57 | Radio group for view profiles. Memoized. Clean. |
| `PlanningTripCard` | `workspace/PlanningTripCard.tsx` | Feature | 163 | Rich trip card with gradient, freshness, missing details badges. Memoized. Good. |
| `ReviewControls` | `workspace/ReviewControls.tsx` | Feature | 196 | Review workflow with validation, suitability block check. Good. |
| `FollowUpCard` | `workspace/cards/FollowUpCard.tsx` | Feature | 360 | Rich card with 2 modals (Snooze, Reschedule). Urgency styling. Tested (18 tests). **Too large** — modals should extract. |
| `CaptureCallPanel` | `workspace/panels/CaptureCallPanel.tsx` | Feature | 342 | Full form with 8 fields, validation, API submit. Tested (30 tests). **Self-contained.** |
| `OverrideModal` | `workspace/modals/OverrideModal.tsx` | Feature | 285 | Full form modal with 3 actions, scope, severity, reason validation. Tested (10 tests). Good. |
| `SuitabilitySignal` | `workspace/panels/SuitabilitySignal.tsx` | Feature | 285 | Tier 1/2 flags, 50+ labels, acknowledge buttons. Tested (43 tests across 2 files). **Well-built.** |
| `SuitabilityPanel` | `workspace/panels/SuitabilityPanel.tsx` | Feature | 302 | Self-contained flag management + override modal. Tested (15 tests). **Well-built.** |
| `ActivityTimeline` | `workspace/panels/ActivityTimeline.tsx` | Feature | 249 | Date-grouped, collapsible, sortable. Tested (15 tests). **Well-built, possibly reusable.** |
| `MetricDrillDownDrawer` | `workspace/panels/MetricDrillDownDrawer.tsx` | Feature | 222 | Full drawer with overlay, API fetch, trip cards. Tested (14 tests). **Well-built, reusable drawer pattern.** |
| `ChangeHistoryPanel` | `workspace/panels/ChangeHistoryPanel.tsx` | Feature | 202 | Expandable change items, JSON export. **Good extraction candidate.** |
| `ExtractionHistoryPanel` | `workspace/panels/ExtractionHistoryPanel.tsx` | Feature | 236 | Grouped by run, retry, metadata. **Good extraction candidate.** |
| `FrontierDashboard` | `workspace/FrontierDashboard.tsx` | Feature | 164 | Experimental/placeholder. **Unfinished.** |
| `PipelineFlow` | `workbench/PipelineFlow.tsx` | Feature | ~100 | 5-step pipeline progress. Accessible. Tested (12 tests). Good. |
| `RunProgressPanel` | `workbench/RunProgressPanel.tsx` | Feature | ~150 | Live timer, step progress, status derivation. Good. |
| `IntakeTab`, `PacketTab`, `DecisionTab`, `StrategyTab`, `SafetyTab` | `workbench/*.tsx` | Feature | 50-550 each | Workbench tab panels. `IntakeTab` (1749L) is the **largest component in the codebase** — needs splitting. |
| `OpsPanel` | `workbench/OpsPanel.tsx` | Feature | ~1126 | Booking readiness, documents, extractions. Tested (17 tests). **Very large — could split.** |

### Marketing Page Components

| Component | File | Lines | Assessment |
|---|---|---|---|
| `SectionIntro` | `marketing/marketing.tsx` | ~15 | Eyebrow + title + body pattern. Clean. |
| `Kicker` | `marketing/marketing.tsx` | ~15 | Decorative label with teal dot. Clean. |
| `ProofChip` | `marketing/marketing.tsx` | ~10 | Trust badge with shield icon. Clean. |
| `CtaBand` | `marketing/marketing-client.tsx` | ~80 | CTA section with waitlist form. Local state for email/submitted. Clean. |
| `DemoButton` | `marketing/marketing-client.tsx` | ~15 | Thin wrapper. Could be simpler. |
| `HeroScene` | `marketing/MarketingVisuals.tsx` | ~80 | Decorative background. Static. `mode` prop unused. |
| `DataTransformationHero` | `marketing/MarketingVisuals.tsx` | ~120 | Toggle between raw/structured views. Uses `useMemo` for interval (wrong hook). |
| `AgencyHeroCockpit` | `marketing/MarketingVisuals.tsx` | ~100 | Static dashboard mockup. Clean. |
| `NotebookAnalyzer` | `marketing/MarketingVisuals.tsx` | ~150 | Interactive playground with file upload, textarea, step animation. Complex but well-bounded. |
| `GsapInitializer` | `marketing/GsapInitializer.tsx` | 71 | Side-effect only (renders null). Registers GSAP + ScrollTrigger. |

### Error/Empty State Components

| Component | File | Type | Assessment |
|---|---|---|---|
| `ErrorBoundary` (class) + `DefaultErrorFallback` + `InlineError` + `useErrorHandler` + `withErrorBoundary` | `error-boundary.tsx` | **Shared utility** | Comprehensive. Class boundary, inline alert, hook, HOC. **One of the best patterns in the codebase.** |
| Root `error.tsx` | `app/error.tsx` | **App-level** | Full error card with retry/home. Dev-only details. |
| Root `loading.tsx` | `app/loading.tsx` | **App-level** | Spinner + "Loading...". Minimal. |
| `AnalyticsEmptyState` | `visual/AnalyticsEmptyState.tsx` | **Shared/Feature** | 3 props, sensible defaults. Clean. |
| `EmptyStateOnboarding` | `overview/EmptyStateOnboarding.tsx` | **Feature** | First-run specific. 3-step onboarding. Tested (6 tests). |

---

## 3. UI That Should Be Extracted From Existing Code

### P0 Extractions (High-Impact)

#### 3.1 `FilterPill` → Shared `Pill`/`Chip` Component

- **Current location:** `src/components/inbox/FilterPill.tsx` (110 lines)
- **Why extract:** Currently trapped inside `inbox/` but has no inbox-specific logic. The tone system (4 tones + muted) + count badge + icon + active state is a general pattern needed throughout the app (reviews, insights, settings).
- **Target layer:** `src/components/ui/pill.tsx` — shared UI primitive
- **Expected props:** `label`, `count?`, `isActive?`, `onClick?`, `icon?`, `variant: 'default' | 'primary' | 'success' | 'warning' | 'danger'`, `size: 'sm' | 'md'`, `className?`
- **State it should own:** None (controlled by parent)
- **Risk:** Low. `FilterPill` is already clean and standalone. The inbox pages and inbox components currently import from `./FilterPill` — update 2-3 imports.
- **Tests:** Move existing 14 test cases to new location + add 2 for new variants.

#### 3.2 `InboxEmptyState` → Shared `EmptyState` Component

- **Current location:** `src/components/inbox/InboxEmptyState.tsx` (113 lines)
- **Why extract:** The pattern of contextual empty states (search no results, filter active, nothing to show) appears in inbox, insights, reviews, trips, followups. At least 6+ pages reimplement this.
- **Target layer:** `src/components/ui/empty-state.tsx`
- **Expected props:** `icon?`, `title: string`, `description?: string`, `action?: { label: string; href?: string; onClick?: () => void }`, `variant: 'default' | 'search' | 'filter' | 'empty'`
- **State it should own:** None
- **Risk:** Low. `InboxEmptyState` already has the right abstraction. Need to genericize the 5 message variants.
- **Tests:** Add 6-8 tests for the new component.

#### 3.3 `AnalyticsEmptyState` → Merge into Shared `EmptyState`

- **Current location:** `src/components/visual/AnalyticsEmptyState.tsx` (51 lines)
- **Why extract:** Duplicates the empty state pattern. Should be replaced by the shared `EmptyState` above.
- **Risk:** Low. Only used by `InsightsPage`.

#### 3.4 Drawer Component (from `MetricDrillDownDrawer`)

- **Current location:** `src/components/workspace/panels/MetricDrillDownDrawer.tsx` (222 lines)
- **Why extract:** Slide-out drawer with overlay, close-on-escape, click-outside-to-close, animated slide is a **general UI pattern** needed by settings panels, integrity monitor, timeline details, extraction history.
- **Target layer:** `src/components/ui/drawer.tsx`
- **Expected props:** `isOpen: boolean`, `onClose: () => void`, `title?: string`, `children: ReactNode`, `position: 'left' | 'right'`, `width?: string`, `showCloseButton?: boolean`
- **State it should own:** Just the open/close. Content state is the parent's responsibility.
- **Risk:** Medium. The current drawer fetches its own data and manages loading/error states. Those must move to the parent.
- **Tests:** Add 8-10 tests for drawer open/close/escape/click-outside/a11y.

#### 3.5 Modal Component (from `OverrideModal` + `FollowUpCard` modals)

- **Current location:** `src/components/workspace/modals/OverrideModal.tsx` (285 lines) — modal shell is baked into the form
- **Why extract:** Two modals (`SnoozeModal`, `RescheduleModal`) are inside `FollowUpCard.tsx`. `OverrideModal` has its own modal shell. No shared Modal primitive exists.
- **Target layer:** `src/components/ui/modal.tsx`
- **Expected props:** `isOpen: boolean`, `onClose: () => void`, `title: string`, `description?: string`, `children: ReactNode`, `footer?: ReactNode`, `size: 'sm' | 'md' | 'lg'`, `closeOnOverlay?: boolean`
- **State it should own:** null (controlled component). But should handle focus trap + escape key + body scroll lock.
- **Risk:** Medium. Need to refactor `OverrideModal` to use the new `Modal` shell while keeping its form logic.
- **Tests:** Add 10-12 tests for modal (focus trap, escape, overlay click, ARIA).

### P1 Extractions (Product Polish)

#### 3.6 `ActivityTimeline` → Shared Timeline Component

- **Current location:** `src/components/workspace/panels/ActivityTimeline.tsx` (249 lines)
- **Why extract:** The timeline pattern (date-grouped events, collapsible, sortable) appears in timeline panel, change history, and extraction history. Genericizing it reduces duplication.
- **Target layer:** `src/components/ui/timeline.tsx`
- **Expected props:** `items: TimelineItem[]`, `sortOrder?: 'newest' | 'oldest'`, `onSortChange?`, `className?`, `showEmpty?: boolean`, `groupByDate?: boolean`
- **Risk:** Low. `ActivityTimeline` already takes data as prop and is well-abstracted.
- **Tests:** Move existing 15 tests + add 4 for new props.

#### 3.7 `PlanningTripCard` Rich Card Pattern → `DataCard` Component

- **Current location:** `src/components/workspace/PlanningTripCard.tsx` (163 lines)
- **Why extract:** The pattern of a rich data card with gradient background, freshness badge, status badges, missing-detail badges, metadata grid, and CTA is repeated for trip cards, review cards, and inbox cards. These share ~60% visual structure.
- **Target layer:** `src/components/ui/data-card.tsx`
- **Expected props:** `variant: 'default' | 'elevated' | 'bordered'`, `header: ReactNode`, `badges?: BadgeDef[]`, `metadata?: { label: string; value: string }[]`, `footer?: ReactNode`, `href?: string`, `onClick?`
- **Risk:** Medium. Requires careful refactoring of `TripCard`, `PlanningTripCard`, `FollowUpCard`, and `ReviewCard` to use the shared primitive. Start with one consumer, verify, then expand.
- **Tests:** Add 6-8 tests for `DataCard`.

#### 3.8 `CaptureCallPanel` Form Pattern → `FormSection` Component

- **Current location:** `src/components/workspace/panels/CaptureCallPanel.tsx` (lines ~50-200, the form layout)
- **Why extract:** The form field layout (label + field + description/error) is repeated in every settings tab, capture call, and booking form. The `Input`/`Select`/`Textarea` primitives already exist, but there's no `FormField` wrapper for layout.
- **Target layer:** `src/components/ui/form-field.tsx`
- **Expected props:** `label: string`, `error?: string`, `description?: string`, `required?: boolean`, `children: ReactNode`, `layout: 'vertical' | 'horizontal'`
- **Risk:** Low. Thin wrapper over existing primitives.
- **Tests:** Add 4-6 tests.

#### 3.9 State Encoding Color Utilities → Centralized Helpers

- **Current location:** Scattered across `PlanningTripCard.tsx` (gradient generation), `FilterPill.tsx` (tone colors), `PriorityIndicator.tsx` (level->color), `inbox-helpers.ts` (SLA colors)
- **Why extract:** At least 6 components define their own color mapping from state names to CSS variable references. This leads to drift (e.g., `workbench.module.css` uses `--color-*` while globals use `--accent-*`).
- **Target layer:** `src/lib/color-utils.ts`
- **Expected API:** `getStateColor(state: 'green' | 'amber' | 'red' | 'blue' | 'purple' | 'neutral', role: 'text' | 'bg' | 'border'): string`
- **Risk:** Low. Pure function extraction.
- **Tests:** Add 8-10 tests.

#### 3.10 `RunProgressPanel` → Shared `ProgressSteps` Component

- **Current location:** `src/components/workbench/RunProgressPanel.tsx` (~150 lines)
- **Why extract:** The "step-by-step progress with live status" pattern (pending → active → completed → error) appears in pipeline flow, run progress, and suitablity panel. A generic `ProgressSteps` would unify.
- **Target layer:** `src/components/ui/progress-steps.tsx`
- **Expected props:** `steps: { id: string; label: string; status: 'pending' | 'active' | 'completed' | 'error' }[]`, `orientation: 'horizontal' | 'vertical'`, `showLabels?: boolean`, `size: 'sm' | 'md'`
- **Risk:** Low. `RunProgressPanel` data flow is already clean.
- **Tests:** Add 6-8 tests.

### P2 Extractions (Future-Facing)

#### 3.11 Responsive Layout Wrapper

- **Current location:** Ad-hoc in every page (`md:flex-row`, `flex-col`, responsive grid classes)
- **Why extract:** No consistent responsive pattern. Pages independently decide breakpoints.
- **Target:** `src/components/ui/responsive.tsx` with `Stack`, `Columns`, `Grid` components that encode the app's spacing/breakpoint decisions.
- **Risk:** Low but broad. Many pages would need updating.

#### 3.12 Animation/Motion Wrappers

- **Current location:** GSAP classes sprinkled in marketing pages (`animate-fade-up`, `animate-stagger-container`). CSS animations in globals (`animate-fade-in`, `animate-pulse-dot`).
- **Why extract:** No consistent motion system. Marketing uses GSAP; app uses CSS animations. A `FadeIn`, `Stagger`, `SlideIn` component set would unify.
- **Risk:** Low. Additive (existing code keeps working).

---

## 4. Existing Components/Widgets That Need Redesign or Refactoring

### 4.1 `IntakePanel.tsx` (1749 Lines) — **Too Large**

- **Problem:** The single largest component in the codebase. Handles trip processing (Spine run), inline field editing (7 fields), planning details, follow-up drafting, capture call panel, advanced config, and status feedback.
- **Has it already extracted anything?** Yes — `EditableField`, `BudgetField`, `PlanningDetailSection` are internal sub-components. But they remain in the same file.
- **Recommendation:** Split into:
  - `IntakePanel` (orchestrator, 200 lines)
  - `IntakeFieldEditor` (the editable field system, extracted from lines ~300-700)
  - `IntakePlanningDetails` (planning detail section, extracted from lines ~700-1000)
  - `IntakeStatusFeedback` (status banners, progress, extracted from lines ~1000-1200)
  - `IntakeAdvancedConfig` (advanced config drawer, extracted from lines ~1200-1400)
- **Risk:** High — this is the core workflow. Must preserve all state interactions.
- **Tests:** 18 existing tests must still pass. Add 6 new tests for extracted sub-components.

### 4.2 `InboxPage` (520 Lines) — **Too Much Inline Logic**

- **Problem:** The inbox page handles URL state serialization/deserialization, sort dropdown, bulk actions toolbar, pagination, selection state, search bar, and filter composition all inline.
- **Recommendation:** Extract URL state management into a `useInboxUrlState` hook. Extract `BulkActionsToolbar` into its own component. Extract `InboxPagination` into its own component.
- **Risk:** Medium. URL state is complex (filters, sort, page, search all in URL params).
- **Tests:** 2 existing tests. Add 6-8 for extracted hooks/components.

### 4.3 `ComposableFilterBar.tsx` (432 Lines) — **Too Large**

- **Problem:** Contains `FilterDropdown`, `ActiveFilterChips`, and `QuickPresets` as internal sub-components. `minValue`/`maxValue` state is defined but never rendered.
- **Recommendation:** Extract `FilterDropdown`, `ActiveFilterChips`, and `QuickPresets` into separate files. Remove dead `minValue`/`maxValue` code.
- **Risk:** Low. Internal sub-components are already memoized and clean.
- **Tests:** 0 dedicated tests (tested through inbox page tests). Add 6-8.

### 4.4 `themeStore.ts` DOM Manipulation in Store Action

- **Problem:** `setTheme` directly modifies `document.body.className` (line 50-53). This is a side effect in a Zustand action, coupling the store to the browser DOM.
- **Recommendation:** Remove DOM manipulation from the store. Create a `ThemeProvider` component that uses `useEffect` to subscribe to `useThemeStore` and apply classes.
- **Risk:** Low. No functional change, just architectural hygiene.
- **Tests:** 0 existing. Add 2.

### 4.5 `CurrencyContext.formatAsPreferred` — **Stub That Pretends to Work**

- **Problem:** `formatAsPreferred` accepts a `fromCurrency` parameter but always formats as `en-IN` regardless (lines 46-51). The signature promises currency conversion; the implementation doesn't deliver.
- **Recommendation:** Either implement real currency formatting via `@/lib/currency.ts`'s `formatMoney`, or rename to `formatDefault` and document the limitation. Remove the unused `fromCurrency` parameter.
- **Risk:** Low.
- **Tests:** 0 existing. Add 2.

### 4.6 `workbench.module.css` — **Inconsistent CSS Variable Naming**

- **Problem:** Uses `--color-primary`, `--color-danger`, `--color-text` naming convention while the rest of the codebase uses `--accent-blue`, `--text-primary`, `--bg-surface`. This means workbench styles don't participate in the theme system.
- **Recommendation:** Migrate workbench styles to use the canonical `--accent-*`, `--bg-*`, `--text-*`, `--border-*` variables. Remove `--color-*` duplication.
- **Risk:** Medium. Visual changes need careful review.
- **Tests:** Run visual regression check.

### 4.7 `useMemo` as `setInterval` in `DataTransformationHero`

- **Problem:** Line 54 uses `useMemo(() => { setInterval(...); return ... }, [])` to toggle a binary state every 4 seconds. `useMemo` is not guaranteed to run synchronously and should not contain side effects. Should be `useEffect`.
- **Recommendation:** Replace `useMemo` with `useEffect` + `useState` + cleanup.
- **Risk:** Very low. Cosmetic animation component.
- **Tests:** 0 existing. Not critical.

### 4.8 `useFieldAuditLog.ts` — **`confirm()` Dialog in a Hook**

- **Problem:** Line 157: `clearChanges()` contains a `window.confirm()` call. Hooks should not trigger browser dialogs.
- **Recommendation:** Move `confirm()` call to the consumer component. The hook should provide `clearChanges: () => void` and let the component handle confirmation UI.
- **Risk:** Low. Behavioral change — confirm dialog moves from hook to component.
- **Tests:** 0 existing for this specific behavior.

### 4.9 `useRuntimeVersion.ts` — **Dead Fetch Pattern**

- **Problem:** Fetches `/api/version` but ignores the `version` field entirely (hardcodes `"Operations live"`). Only `gitSha` and `environment` are used for the `detailsLabel`.
- **Recommendation:** Either use the server's `version` field, or remove the API call and show static labels. If kept, migrate to React Query for consistency.
- **Risk:** Very low.
- **Tests:** 2 tests that assert the current (broken) behavior. Update them.

### 4.10 Marketing CSS Module Import Bug

- **Problem:** `MarketingVisuals.tsx` imports `styles` from `./marketing.module.css` but uses classes (`transformationContainer`, `packetGrid`, `blockerAlert`, `rawText`, `scanLine`) that only exist in `marketing-v2.module.css`. The import is likely pointing at the wrong file, or the classes were added to v2 but not migrated to v1.
- **Recommendation:** Either import from `marketing-v2.module.css` (if that's the intended active stylesheet), or migrate the missing classes into `marketing.module.css`.
- **Risk:** Low — may currently be rendering unstyled elements.
- **Tests:** Check visually.

---

## 5. Missing Components/Widgets Not Currently Hinted in Code

### P0 — Missing But Critical

#### 5.1 `Drawer` Component

- **Purpose:** Reusable slide-out drawer (right/left) with overlay, focus trap, escape-to-close, body scroll lock, and animation.
- **Why it's missing:** 3+ components build their own drawer approximation (`MetricDrillDownDrawer`, `SettingsPanel`, `IntegrityMonitorPanel`). Each has subtle differences in behavior. A shared Drawer would standardize and fix edge cases.
- **Where it should live:** `src/components/ui/drawer.tsx`
- **Example usage:** `SettingsPanel` wrapping its config form; `MetricDrillDownDrawer` wrapping agent trip data; extraction history, change history.
- **Priority:** P0

#### 5.2 `Modal` Component

- **Purpose:** Accessible modal dialog with focus trap, escape, overlay click, body scroll lock, and ARIA `dialog` pattern.
- **Why it's missing:** `OverrideModal` and `FollowUpCard`'s `SnoozeModal`/`RescheduleModal` each build their own. No shared focus trap, no consistent ARIA.
- **Where it should live:** `src/components/ui/modal.tsx`
- **Example usage:** Review confirmation, delete confirmation, override form, settings confirmation.
- **Priority:** P0

#### 5.3 `EmptyState` Component

- **Purpose:** Contextual empty state for every data view (no items, no search results, no filters match, first run).
- **Why it's missing:** 4+ components implement their own (`InboxEmptyState`, `AnalyticsEmptyState`, inline in followups/insights/reviews). Each has different icon, copy, and action patterns.
- **Where it should live:** `src/components/ui/empty-state.tsx`
- **Priority:** P0

### P1 — Product Polish & Reusable UX

#### 5.4 `Toast`/`Notification` System

- **Purpose:** Transient notifications for success, error, and info states. Currently absent — errors surface as inline alerts or are silently caught.
- **Where it should live:** `src/components/ui/toast.tsx` + `src/lib/toast-store.ts` (Zustand)
- **Example usage:** "Trip saved successfully" toast, "Document uploaded" toast, "Follow-up snoozed" toast.
- **Priority:** P1

#### 5.5 `CommandPalette` / `QuickActionBar`

- **Purpose:** Cmd+K searchable command palette for power users (navigate to trip, create inquiry, switch views).
- **Where it should live:** `src/components/ui/command-palette.tsx`
- **Example usage:** Press Cmd+K → search "italy" → navigate to Italy Honeymoon trip.
- **Priority:** P1

#### 5.6 `StatusBadge` — Unified Status Indicator

- **Purpose:** Single component for all status badges (planning stage, review status, follow-up status, integrity status). Currently 4+ different badge implementations.
- **Where it should live:** `src/components/ui/status-badge.tsx`
- **Expected props:** `status: string`, `variant: 'stage' | 'review' | 'followup' | 'integrity'`, `size: 'sm' | 'md'`, `showLabel?: boolean`
- **Priority:** P1

#### 5.7 `Timeline` Component (Generic)

- **Purpose:** Vertical/horizontal timeline with events, dates, status dots, and collapsible groups.
- **Where it should live:** `src/components/ui/timeline.tsx`
- **Example usage:** Activity timeline, extraction history, change history, trip timeline.
- **Priority:** P1

#### 5.8 `ProgressSteps` Component

- **Purpose:** Multi-step progress indicator with per-step status (pending/active/completed/error).
- **Where it should live:** `src/components/ui/progress-steps.tsx`
- **Example usage:** Pipeline flow, run progress, stage advancement.
- **Priority:** P1

#### 5.9 `DataTable` Component

- **Purpose:** Sortable, filterable table with selection, pagination, and responsive behavior.
- **Why it's missing:** `WorkspaceTable.tsx` is a bespoke table with sort headers. The inbox uses card grid, not table. Insights has a team table. A shared table component would unify.
- **Where it should live:** `src/components/ui/data-table.tsx`
- **Note:** `@tanstack/react-table` is already in `package.json`.
- **Priority:** P1

#### 5.10 `Pagination` Component

- **Purpose:** Page navigation control with page numbers, prev/next, and total count.
- **Why it's missing:** Inbox and trips pages implement their own pagination inline.
- **Where it should live:** `src/components/ui/pagination.tsx`
- **Priority:** P1

#### 5.11 `SplitView` Component

- **Purpose:** Resizable split panel layout (used in output panel, workbench).
- **Where it should live:** `src/components/ui/split-view.tsx`
- **Priority:** P1

### P2 — Future-Facing Design System

#### 5.12 `Avatar` Component

- **Purpose:** User avatar with initials gradient, optional image, size variants, and status dot.
- **Where it should live:** `src/components/ui/avatar.tsx`
- **Example usage:** UserMenu, team member list, activity timeline, assignment dropdowns.

#### 5.13 `DropdownMenu` Component

- **Purpose:** Accessible dropdown menu with hover/click trigger, keyboard nav, and positioning.
- **Where it should live:** `src/components/ui/dropdown-menu.tsx`
- **Example usage:** Sort dropdown in inbox, actions dropdown in trip cards, user menu (currently hand-rolled).

#### 5.14 `Tooltip` Component

- **Purpose:** Hover/focus tooltip with positioning, delay, and ARIA.
- **Where it should live:** `src/components/ui/tooltip.tsx`
- **Example usage:** Icon-only buttons, truncated text, status indicators.

#### 5.15 `Breadcrumbs` Component

- **Purpose:** Navigation breadcrumbs with current page indicator and separators.
- **Where it should live:** `src/components/ui/breadcrumbs.tsx`
- **Example usage:** Trip detail header, settings pages.

#### 5.16 `Banner` Component

- **Purpose:** Contextual banners (info, warning, error, success) with dismiss and action.
- **Where it should live:** `src/components/ui/banner.tsx`
- **Example usage:** Integrity warning bar, recovery mode banner, validation blocked banner.

#### 5.17 `StatCard` Component

- **Purpose:** Metric display card with label, value, trend, and optional chart.
- **Where it should live:** `src/components/ui/stat-card.tsx`
- **Example usage:** Overview dashboard, insights dashboard (currently implemented inline).

#### 5.18 `SkeletonPage` Component

- **Purpose:** Full-page skeleton placeholder matching the app's layout structure.
- **Where it should live:** `src/components/ui/loading.tsx` (add to existing loading module)
- **Example usage:** Page-level loading states, replacing the minimal spinner.

#### 5.19 `AnimatePresence` / Motion Wrappers

- **Purpose:** Framer-motion-like mount/unmount animations for lists, drawers, modals.
- **Where it should live:** `src/components/ui/motion.tsx`
- **Note:** GSAP is installed but only used on marketing pages. App-level transitions use CSS animations. A lightweight motion wrapper would improve perceived performance.

#### 5.20 `ConfirmDialog` Component

- **Purpose:** Confirmation dialog for destructive actions (delete, discard, override).
- **Where it should live:** `src/components/ui/confirm-dialog.tsx`
- **Example usage:** "Are you sure you want to discard this draft?" — currently uses browser `confirm()` in `useFieldAuditLog`.

#### 5.21 `SearchInput` Component

- **Purpose:** Search input with debounce, clear button, and loading state.
- **Where it should live:** `src/components/ui/search-input.tsx`
- **Example usage:** Inbox search, trips search, settings search.

#### 5.22 `Sheet` / `BottomPanel` Component

- **Purpose:** Slide-up panel for mobile/compact views (alternative to Drawer for small screens).
- **Where it should live:** `src/components/ui/sheet.tsx`

---

## 6. Design-System Audit

### Current State

The project has a **well-documented but partially implemented design system**.

#### What's Good

1. **CSS custom properties** in `globals.css` provide a comprehensive token set:
   - 8 background layers (`--bg-canvas` through `--bg-rationale`)
   - 7 text levels (`--text-primary` through `--text-rationale`)
   - 7 accent colors (blue, cyan, green, amber, red, purple, orange)
   - 3 border styles (default, hover, active)
   - 8 spacing values (4px through 32px)
   - Typography scale (fluid rem + fixed px)
   - 3 font families (display, body, mono/data)

2. **`tailwind.config.js`** maps all CSS vars to Tailwind utility classes — enabling `bg-surface`, `text-primary`, `border-default`, etc.

3. **DESIGN.md** is a thorough 1112-line specification with cartographic dark theme, color roles, typography rules, component patterns, and layout principles.

4. **Accessibility basics** are solid:
   - `skip-to-content` link in Shell
   - `focus-visible` ring styling
   - `sr-only` utility classes
   - WCAG contrast utilities in `src/lib/contrast-utils.ts`
   - Custom scrollbar styling
   - ARIA roles throughout
   - `prefers-reduced-motion` support in marketing CSS

#### What's Missing or Inconsistent

| Dimension | Current State | Gap |
|---|---|---|
| **Typography** | Two parallel scales (fluid rem for marketing, fixed px for app UI) | No clear rules for when to use which scale |
| **Spacing** | 8px grid (space-1 through space-8) in CSS vars; `space-*` aliases in Tailwind | Components use arbitrary values (`px-3`, `gap-5`, `p-space-6`) inconsistently |
| **Radii** | `--radius-sm/md/lg` (4/6/8px) in globals.css | No `xl`, `2xl`, `full` in CSS vars (only in Tailwind config as `rounded-premium`) |
| **Shadows** | `glow-*`, `premium`, `soft` in Tailwind config | No `--shadow-*` CSS variables; shadows are only accessible via Tailwind classes |
| **Colors** | 7 accent colors + background/text hierarchy in globals | Color naming inconsistency: `--accent-blue` in globals vs `--color-primary` in workbench.module.css vs hardcoded hex in components |
| **Semantic colors** | `--accent-green` (success), `--accent-amber` (warning), `--accent-red` (error) | No explicit `--color-success`, `--color-warning`, `--color-error` semantic aliases |
| **Button styles** | 5 variants, 7 sizes via CVA | Good |
| **Card styles** | 4 variants via CVA | Good |
| **Icon usage** | Lucide React, consistent import pattern | Some Shell icons may be unused (18 imports) |
| **Illustrations** | SVG logos only (waypoint-logo-primary/compass/notebook) | No illustration system |
| **Animation** | GSAP (marketing) + CSS animations (app) | No app-level motion system; GSAP is a heavy dependency for marketing-only use |
| **Screen layout consistency** | Shell provides consistent sidebar + header | Pages implement their own responsive behavior independently |
| **Responsive behavior** | Shell responsive (72px/220px sidebar). Pages use Tailwind responsive prefixes ad-hoc | No consistent responsive grid/stack components |
| **Dark mode** | Dark-only (CSS vars defined for `:root` only). `color-scheme: dark` | No light mode. DESIGN.md describes "Theme B: Minimalist Document" but it's unimplemented. |
| **Platform conventions** | Web app (no mobile app) | No platform-specific adaptations |

### Token File (`src/lib/tokens.ts`) — Defined But Unused

The `tokens.ts` file is a well-structured OKLCH token file covering colors, spacing, typography, elevation, radius, transitions, layout, and z-index. **No component imports it.** This means:

- Components use CSS vars directly via Tailwind (`bg-surface`, `text-primary`) or inline style objects (`style={{ color: 'var(--accent-blue)' }}`)
- The JS-level token system is dormant
- `STATE_COLORS` (green/amber/red/blue/purple/neutral with bg+border) is defined but unused — components define their own color maps

### Suggested Design Token Hierarchy

```
LAYER 1: CSS Custom Properties (globals.css)
  --bg-canvas, --text-primary, --accent-blue, --border-default, etc.
  → Accessed via Tailwind utility classes (bg-surface, text-primary)

LAYER 2: Semantic Aliases (globals.css or tailwind.config.js) — MISSING
  --color-success: var(--accent-green)
  --color-warning: var(--accent-amber)
  --color-error: var(--accent-red)
  --color-info: var(--accent-blue)

LAYER 3: JS Tokens (tokens.ts) — DEFINED BUT UNUSED
  COLORS, SPACING, FONT_SIZE, ELEVATION, RADIUS, STATE_COLORS
  → Should be imported by components for dynamic styling (inline styles, chart themes)

LAYER 4: Component Primitives (ui/*)
  Button, Card, Input, Select, Textarea, Tabs, Badge, Spinner, etc.
  → Use Tailwind classes → reference Layer 1
  → Tests validate behavior, not class names

LAYER 5: Shared UI (components/ui/)
  EmptyState, Drawer, Modal, Toast, ProgressSteps, DataTable, etc.
  → Compose Layer 4 primitives

LAYER 6: Feature UI (components/inbox/, components/workspace/)
  TripCard, FollowUpCard, SuitabilitySignal, etc.
  → Compose Layer 5 and Layer 4

LAYER 7: Pages (app/*)
  → Compose Layer 6 and Layer 5
```

---

## 7. Suggested Target Frontend Architecture

### Proposed Folder Structure

```
src/
├── app/                          # Next.js App Router pages (routing only)
│   ├── (agency)/                 # Agency routes
│   ├── (auth)/                   # Auth routes
│   ├── (public)/                 # Public routes
│   ├── (traveler)/               # Traveler routes
│   └── api/                      # BFF API routes
│
├── components/
│   ├── ui/                       # Design-system primitives (no business logic)
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── input.tsx, select.tsx, textarea.tsx
│   │   ├── tabs.tsx
│   │   ├── badge.tsx, pill.tsx           ← ADD: Pill from FilterPill
│   │   ├── modal.tsx, drawer.tsx         ← ADD: Missing
│   │   ├── empty-state.tsx               ← ADD: Missing
│   │   ├── toast.tsx                     ← ADD: Missing
│   │   ├── progress-steps.tsx            ← ADD: Missing
│   │   ├── timeline.tsx                  ← ADD: Missing
│   │   ├── data-table.tsx                ← ADD: Missing
│   │   ├── pagination.tsx                ← ADD: Missing
│   │   ├── status-badge.tsx              ← ADD: Missing
│   │   ├── icon.tsx
│   │   ├── loading.tsx
│   │   ├── PriorityIndicator.tsx
│   │   └── SmartCombobox.tsx
│   │
│   ├── layout/                    # App shell, navigation, providers
│   │   ├── Shell.tsx
│   │   ├── UserMenu.tsx
│   │   ├── AuthProvider.tsx
│   │   └── providers.tsx
│   │
│   ├── marketing/                 # Marketing page components
│   │   ├── marketing.tsx           # Server components
│   │   ├── marketing-client.tsx    # Client components
│   │   ├── MarketingVisuals.tsx
│   │   ├── GsapInitializer.tsx
│   │   └── marketing.module.css
│   │
│   ├── inbox/                     # Feature: Inbox
│   │   ├── TripCard.tsx
│   │   ├── InboxFilterBar.tsx
│   │   ├── ComposableFilterBar.tsx
│   │   ├── ViewProfileToggle.tsx
│   │   └── __tests__/
│   │
│   ├── workspace/                 # Feature: Trip workspace
│   │   ├── panels/
│   │   │   ├── IntakePanel.tsx         → SPLIT into IntakePanel/ + sub-components
│   │   │   ├── PacketPanel.tsx
│   │   │   ├── DecisionPanel.tsx
│   │   │   ├── StrategyPanel.tsx
│   │   │   ├── SafetyPanel.tsx
│   │   │   ├── OutputPanel.tsx
│   │   │   ├── TimelinePanel.tsx
│   │   │   ├── TimelineSummary.tsx
│   │   │   ├── SuitabilitySignal.tsx
│   │   │   ├── SuitabilityPanel.tsx
│   │   │   ├── SuitabilityCard.tsx
│   │   │   ├── CaptureCallPanel.tsx
│   │   │   ├── ActivityTimeline.tsx
│   │   │   ├── MetricDrillDownDrawer.tsx
│   │   │   ├── ChangeHistoryPanel.tsx
│   │   │   └── ExtractionHistoryPanel.tsx
│   │   ├── cards/
│   │   │   ├── FollowUpCard.tsx
│   │   │   └── PlanningTripCard.tsx
│   │   ├── modals/
│   │   │   └── OverrideModal.tsx
│   │   ├── workbench/              # Workbench-specific components
│   │   │   ├── IntakeTab.tsx          → SPLIT
│   │   │   ├── PacketTab.tsx
│   │   │   ├── DecisionTab.tsx
│   │   │   ├── StrategyTab.tsx
│   │   │   ├── SafetyTab.tsx
│   │   │   ├── OpsPanel.tsx           → SPLIT
│   │   │   ├── SettingsPanel.tsx
│   │   │   ├── IntegrityMonitorPanel.tsx
│   │   │   ├── PipelineFlow.tsx
│   │   │   ├── RunProgressPanel.tsx
│   │   │   └── ScenarioLab.tsx
│   │   ├── ReviewControls.tsx
│   │   └── FrontierDashboard.tsx
│   │
│   ├── visual/                    # Feature: Analytics / charts
│   │   ├── RevenueChart.tsx
│   │   ├── PipelineFunnel.tsx
│   │   ├── TeamPerformanceChart.tsx
│   │   └── AnalyticsEmptyState.tsx
│   │
│   ├── overview/                  # Feature: Dashboard
│   │   └── EmptyStateOnboarding.tsx
│   │
│   ├── navigation/                # Shared navigation utilities
│   │   └── BackToOverviewLink.tsx
│   │
│   └── error-boundary.tsx         # Error boundaries (could stay at root)
│
├── hooks/                         # Data-fetching and state hooks
│   ├── useGovernance.ts
│   ├── useTrips.ts
│   ├── useUnifiedState.ts
│   ├── useIntegrityIssues.ts
│   ├── useScenarios.ts
│   ├── useSpineRun.ts             → REFACTOR to use React Query
│   ├── useAgencySettings.ts       → REFACTOR to use React Query
│   ├── useRuntimeVersion.ts       → REFACTOR or remove
│   └── useFieldAuditLog.ts        → REFACTOR to use React Query + remove confirm()
│
├── stores/                        # Zustand stores
│   ├── index.ts                   → ADD: export themeStore
│   ├── auth.ts
│   ├── workbench.ts
│   └── themeStore.ts              → REFACTOR: remove DOM manipulation
│
├── contexts/                      # React contexts (minimal)
│   ├── TripContext.tsx
│   └── CurrencyContext.tsx
│
├── lib/                           # Utilities, helpers, API client
│   ├── api-client.ts              → SPLIT by domain
│   ├── tokens.ts                  → START USING in components
│   ├── color-utils.ts             → ADD: centralized state→color mapping
│   ├── contrast-utils.ts
│   ├── currency.ts
│   ├── combobox.ts
│   ├── accessibility.tsx
│   ├── bff-auth.ts
│   ├── route-map.ts
│   ├── routes.ts
│   ├── utils.ts
│   └── ... (other helpers)
│
├── types/                         # TypeScript types
│   ├── spine.ts
│   ├── governance.ts
│   ├── audit.ts
│   └── generated/
│       └── spine-api.ts
│
└── __tests__/                     # Cross-cutting / integration tests
```

### Guiding Principles for this Structure

1. **`components/ui/`** — Only components that know nothing about trips, agencies, inbox, or business logic. These are design-system primitives. They take data and callbacks. They don't fetch data. They don't know about auth.

2. **Feature folders (`inbox/`, `workspace/`, `visual/`)** — Business-aware components that use `ui/` primitives. They can fetch data, know about Trip types, etc. They should NOT contain CSS that defines colors or spacing — those come from design tokens.

3. **Pages (`app/*/page.tsx`)** — Thin orchestrators. 100-200 lines max. They compose feature components, handle URL state, and wire data flow. Most logic should be in hooks or feature components.

4. **Hooks** — Data fetching and state logic. No rendering. No DOM manipulation. No `confirm()` dialogs.

5. **How reusable before moving up:**
   - If used in 2+ features → belongs in `components/ui/`
   - If used in 1 feature but the pattern is generic → still move to `components/ui/`
   - If used in 1 page and tightly coupled → keep in feature folder

---

## 8. Prioritized Extraction/Refactor Roadmap

### P0 — High-Impact Cleanup (Do Next)

| # | Item | Files Affected | Benefit | Risk | Tests |
|---|---|---|---|---|---|
| **P0.1** | Extract `Modal` component | NEW: `ui/modal.tsx`. Refactor: `OverrideModal.tsx`, `FollowUpCard.tsx` | Standardized focus trap, escape, ARIA. Eliminates 3+ modal implementations. | Medium | Add 10-12 |
| **P0.2** | Extract `Drawer` component | NEW: `ui/drawer.tsx`. Refactor: `MetricDrillDownDrawer.tsx`, `SettingsPanel.tsx`, `IntegrityMonitorPanel.tsx` | Standardized slide-out panel. Fixes edge cases in 3 implementations. | Medium | Add 8-10 |
| **P0.3** | Extract `EmptyState` component | NEW: `ui/empty-state.tsx`. Refactor: `InboxEmptyState.tsx`, `AnalyticsEmptyState.tsx`, inline empty states in 5+ pages | One true empty state pattern. Eliminates 4+ implementations. | Low | Add 6-8 |
| **P0.4** | Extract `Pill`/`Chip` from `FilterPill` | NEW: `ui/pill.tsx`. Refactor `FilterPill.tsx` to use it. | General chip/tag primitive usable outside inbox. | Low | Move existing 14 tests |
| **P0.5** | Fix `MarketingVisuals.tsx` CSS module import | `MarketingVisuals.tsx` — fix import path | Fixes potentially unstyled elements on marketing page. | Low | Visual check |
| **P0.6** | Fix `useRuntimeVersion.ts` dead fetch | `useRuntimeVersion.ts`, `useRuntimeVersion.test.tsx` | Eliminates useless API call or uses real data. | Very low | Update 2 tests |
| **P0.7** | Fix `themeStore.ts` DOM manipulation | `themeStore.ts`, NEW: `ThemeProvider.tsx` | Decouples store from browser DOM. SSR-safe. | Low | Add 2 tests |
| **P0.8** | Fix `CurrencyContext.formatAsPreferred` stub | `CurrencyContext.tsx` | Removes misleading API. Either implements real formatting or renames. | Very low | Add 2 tests |

### P1 — Product Polish and Reusable UX

| # | Item | Files Affected | Benefit | Risk | Tests |
|---|---|---|---|---|---|
| **P1.1** | Add `Toast` notification system | NEW: `ui/toast.tsx`, `lib/toast-store.ts` | First-class success/error feedback. Eliminates silent error handling. | Low | Add 6-8 |
| **P1.2** | Add `StatusBadge` component | NEW: `ui/status-badge.tsx` | Unifies status display across stages, reviews, followups, integrity. | Low | Add 6-8 |
| **P1.3** | Add `ProgressSteps` component | NEW: `ui/progress-steps.tsx`. Refactor `PipelineFlow.tsx`, `RunProgressPanel.tsx` | Single progress visualization primitive. | Low | Add 6-8 |
| **P1.4** | Add `Timeline` component | NEW: `ui/timeline.tsx`. Refactor `ActivityTimeline.tsx` | Generic timeline primitive. | Low | Move existing 15 tests |
| **P1.5** | Split `IntakePanel.tsx` (1749 lines) | NEW: 3-4 sub-components. Refactor existing imports. | Manageable files. Clear responsibilities. | High | 18 existing + 6 new |
| **P1.6** | Split `ComposableFilterBar.tsx` (432 lines) | Extract `FilterDropdown`, `ActiveFilterChips`, `QuickPresets` | Clearer separation. Dead code removal. | Low | Add 6-8 |
| **P1.7** | Extract `Pagination` component | NEW: `ui/pagination.tsx`. Refactor inbox, trips pages. | Consistent pagination across the app. | Low | Add 4-6 |
| **P1.8** | Create `useInboxUrlState` hook | Extract from `InboxPage.tsx` (520L) | Thinner page. Separates URL state concerns. | Medium | Add 4-6 |
| **P1.9** | Migrate workbench CSS to canonical variables | `workbench.module.css` | Consistent theming. No more `--color-*` divergence. | Medium | Visual regression check |
| **P1.10** | Create `BulkActionsToolbar` component | Extract from `InboxPage.tsx` | Reusable bulk action bar. | Low | Add 2-4 |
| **P1.11** | Add `SearchInput` component | NEW: `ui/search-input.tsx`. Refactor inbox, trips search. | Debounced search with loading state. | Low | Add 4-6 |
| **P1.12** | Unify color state mappings | NEW: `lib/color-utils.ts`. Refactor 6+ components. | Single source of truth for state→color mapping. | Low | Add 8-10 |

### P2 — Future-Facing Design System

| # | Item | Files Affected | Benefit | Risk | Tests |
|---|---|---|---|---|---|
| **P2.1** | Start using `src/lib/tokens.ts` | `tokens.ts` — wire into components that use inline styles | JS token system becomes alive. Enables programmatic color use. | Low | None needed (no behavior change) |
| **P2.2** | Add `Avatar` component | NEW: `ui/avatar.tsx`. Refactor `UserMenu.tsx`, team tables. | Consistent user representation. | Low | Add 4-6 |
| **P2.3** | Add `DropdownMenu` component | NEW: `ui/dropdown-menu.tsx`. Refactor `UserMenu.tsx`, sort dropdowns. | Accessible dropdown with keyboard nav. | Medium | Add 8-10 |
| **P2.4** | Add `Tooltip` component | NEW: `ui/tooltip.tsx` | Standardized hover tooltips. | Low | Add 4-6 |
| **P2.5** | Add `Breadcrumbs` component | NEW: `ui/breadcrumbs.tsx`. Refactor trip detail header. | Consistent breadcrumb navigation. | Low | Add 2-4 |
| **P2.6** | Add `Banner` component | NEW: `ui/banner.tsx`. Refactor integrity bar, recovery banner. | Standardized contextual banners. | Low | Add 4-6 |
| **P2.7** | Add `StatCard` component | NEW: `ui/stat-card.tsx`. Refactor overview + insights stat cards. | Unified metric display. | Low | Add 4-6 |
| **P2.8** | Add `ConfirmDialog` component | NEW: `ui/confirm-dialog.tsx`. Refactor `useFieldAuditLog.ts`. | Eliminates browser `confirm()`. Accessible. | Low | Add 6-8 |
| **P2.9** | Add `SkeletonPage` component | Add to `ui/loading.tsx`. Refactor page-level loading states. | Better loading UX than generic spinner. | Low | Add 2-4 |
| **P2.10** | Add `DataTable` component | NEW: `ui/data-table.tsx`. Refactor `WorkspaceTable.tsx`. | Sortable, selectable, paginated table. `@tanstack/react-table` already installed. | Medium | Add 8-10 |
| **P2.11** | Split `api-client.ts` (1148 lines) | Split by domain: trips, settings, drafts, booking, documents | Manageable API client modules. | Very low | Move existing tests |
| **P2.12** | Migrate `useAgencySettings` + `useRuntimeVersion` to React Query | `useAgencySettings.ts`, `useRuntimeVersion.ts` | Consistent data fetching. Caching. Dedup. | Low | Update existing tests |
| **P2.13** | Add `useSpineRun` React Query polling | `useSpineRun.ts` | Eliminate manual polling. Built-in retry + cache. | Medium | Update 0 existing (no tests) |
| **P2.14** | Add `SplitView` component | NEW: `ui/split-view.tsx`. Refactor output panel, workbench. | Resizable split panels. | Low | Add 4-6 |
| **P2.15** | Re-export `themeStore` from `stores/index.ts` | `stores/index.ts` | Consistent store exports. | Very low | None |

---

## 9. Specific Implementation Guidance for the Next Coding Agent

### Order of Implementation

Start with P0 items, then P1, then P2. Within each tier, the order matters:

1. **First:** `Modal` component → immediately useful for `OverrideModal` and `FollowUpCard` refactors
2. **Second:** `Drawer` component → enables `MetricDrillDownDrawer`, `SettingsPanel`, `IntegrityMonitorPanel` cleanup
3. **Third:** `EmptyState` component → eliminates 4+ inline implementations
4. **Fourth:** `Pill` extraction → unlocks broader chip usage
5. **Fifth:** Fix bugs (`MarketingVisuals` import, `useRuntimeVersion`, `themeStore`, `CurrencyContext`)
6. **Then:** P1 items in any order (they are mostly additive, not dependent)
7. **Then:** P2 items (largely independent)

### Which Files to Avoid Touching Unless Necessary

- **`src/lib/api-client.ts`** — 1148 lines, many imports. Only split if you can do it without breaking any import paths. The `ApiClient` class is exported as `api` and also has standalone function exports — this dual export is fragile.
- **`src/app/(agency)/workbench/page.tsx`** — 1128 lines of complex orchestration (auto-save, draft management, spine run, URL state). Only touch if adding a specific feature.
- **`src/stores/workbench.ts`** — 275 lines with 4 slices. All workbench panels depend on it. Changes here ripple everywhere.
- **`src/hooks/useGovernance.ts`** — 273 lines with 10+ hooks. Many pages depend on it. Splitting is safe but high-impact.
- **`src/app/(traveler)/itinerary-checker/page.tsx`** — 2018 lines with PDF/OCR/GSAP. The most complex page. Only refactor if specifically tasked.

### Existing Behavior That Must Be Preserved

1. **Draft auto-save** (workbench) — 5s debounce, content key diffing, conflict detection (409). This is delicate and critical.
2. **URL state persistence** (inbox, workbench, settings, insights) — Filters, sort, page, tab, and panel state in URL params must not break.
3. **Auth flow** — Redirect to login, preserve `?redirect` param, handle `?next`. AuthProvider hydration must block until resolved.
4. **Spine run polling** — The run-until-complete loop must not break even during component re-renders. The abort mechanism must work.
5. **Stage gating** (PlanningStageGate) — Logic that controls which stages are accessible must be preserved exactly.
6. **Suitability flag acknowledgment** — Cross-tab session state tracking must work.
7. **Review action submission** — The approval/reject/request-changes workflow with suitability block check.

### Tests That Should Be Added or Updated

For every extraction:

1. **Behavioral tests** — Test the new component's public API (props, callbacks, rendering)
2. **Integration tests** — Update existing page/panel tests that used the inlined code
3. **Accessibility tests** — ARIA attributes, keyboard nav, focus management, screen reader
4. **Edge case tests** — Loading state, error state, empty state, disabled state

Do NOT add:

- **Style tests** (class name assertions) — These break on refactoring. Test behavior, not classes.
- **Snapshot tests** — Too brittle for active development.

### Visual Regressions to Watch For

| Area | What to Check |
|---|---|
| Marketing hero section | GSAP animations, gradient background, grid overlay |
| Workbench panels | Tab switching, inline editing, run progress, validation display |
| Inbox | Filter pills, trip cards, sort dropdown, pagination |
| Settings | Multi-tab form, draft save, approval rules table |
| Insights | Charts rendering, time range selector, drill-down drawer |
| Trip detail | Stage tabs, header color strip, timeline rail |
| Modal/Drawer changes | Close behavior, escape key, overlay click, focus trap |

### Framework-Specific Constraints

1. **Next.js 16 App Router:** All interactive components need `"use client"`. Server components cannot use hooks, state, or browser APIs.
2. **`next/navigation` must be mocked** in Vitest (already done in `vitest.setup.tsx`).
3. **`next/image` must be mocked** in Vitest (already done).
4. **`window.matchMedia` must be mocked** for GSAP ScrollTrigger (already done).
5. **Zustand with persist middleware:** Test cleanup must reset store state between tests to avoid leakage.
6. **React Query:** Tests must wrap in `QueryClientProvider`. Use `@tanstack/react-query`'s `QueryClient` with `defaultOptions: { queries: { retry: false } }`.
7. **GSAP:** Only used on marketing pages. The `GsapInitializer` renders `null` and runs side effects. Tests may need to mock `gsap` and `ScrollTrigger`.
8. **CSS Modules:** Imported as `styles` object. Classes are accessed as `styles.className`. Only the `workbench/` and `marketing/` components use CSS modules — all others use Tailwind inline.

### Key Anti-Patterns to Avoid in New Code

1. **Do NOT put DOM manipulation in Zustand stores** (`document.body.className` in `themeStore`).
2. **Do NOT put `confirm()`, `alert()`, or `prompt()` in hooks** (`useFieldAuditLog`).
3. **Do NOT use `useMemo` for side effects** like `setInterval` (`DataTransformationHero`).
4. **Do NOT create components >500 lines** without extracting sub-components.
5. **Do NOT use `transitionTripStage` endpoint without `/api/` prefix** (current bug in `api-client.ts` line 600).
6. **Do NOT mock what you don't own** — prefer integration tests over isolated mock-heavy tests.
7. **Do NOT hardcode CSS variable names** — use the `--accent-*`, `--bg-*`, `--text-*` system. Don't introduce a new convention.

---

## Summary

This codebase is **architecturally strong** for a startup-stage product. It has:

- A well-defined (if partially implemented) design system
- Clean component primitives (Button, Card, Input, Tabs)
- Good accessibility practices
- Comprehensive test coverage (741+ tests)
- Consistent state management patterns (mostly)

The main opportunities are:

1. **3 missing primitives** that are reimplemented ad-hoc: Modal, Drawer, EmptyState (P0)
2. **2 oversized files** that need splitting: IntakePanel (1749L), api-client.ts (1148L) (P0/P1)
3. **3 data-fetching hooks** that should use React Query instead of `useState`+`useEffect` (P1)
4. **4 small bugs/anti-patterns** in hooks and stores (P0)
5. **12+ additive components** for product polish and future velocity (P1/P2)

The recommended implementation order is: fix P0 bugs first → extract P0 primitives → tackle P1 extraction/splitting → add P2 design-system components → adopt tokens.ts.
