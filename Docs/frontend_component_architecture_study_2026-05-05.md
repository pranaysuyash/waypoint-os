# Frontend Component Architecture Study

**Date**: 2026-05-05
**Author**: Architecture Study Agent
**Scope**: Full component-level analysis of `frontend/src/` (80+ component files, hooks, stores, contexts, types, lib utilities)
**Status**: Complete — Findings, Recommendations, and Handoff

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Component Tree (Complete)](#2-component-tree)
3. [Detailed Component Analysis](#3-detailed-component-analysis)
4. [Routing Architecture Analysis](#4-routing-architecture)
5. [Data Flow & State Management Analysis](#5-data-flow--state-management)
6. [Type System Analysis](#6-type-system)
7. [Anti-Patterns & Issues](#7-anti-patterns--issues)
8. [Gaps & Missing Infrastructure](#8-gaps)
9. [Consolidation Opportunities](#9-consolidation-opportunities)
10. [Prioritized Recommendations](#10-prioritized-recommendations)
11. [11-Dimension Audit](#11-11-dimension-audit)
12. [Routing Dual-Pattern Deep Dive](#12-routing-dual-pattern-deep-dive)
13. [Open Questions](#13-open-questions)
14. [Next Steps / Handoff](#14-next-steps)

---

## 1. Executive Summary

**What this study covers**: Every `.tsx` and `.ts` file in `frontend/src/components/`, all hooks, contexts, stores, types, and the lib/ utility directory — analyzed for architectural soundness, component composition quality, duplication, anti-patterns, and gaps.

### Current State Verdicts

| Dimension | Verdict | Key Issue |
|-----------|---------|-----------|
| **Code Quality** | ✅ Good | Components well-structured, accessibility-first, consistent patterns |
| **Architecture** | 🟡 Moderate | Two major structural issues: dual routing + dual type system |
| **Scalability** | 🟡 Moderate | 1300-line IntakePanel monolith will not scale |
| **Consistency** | 🟡 Moderate | Data fetching patterns differ across components |
| **Launch Readiness** | 🟡 Partial | Feature-complete but 6 consolidation items block launch polish |

### Key Numbers

- **80+** component files across 10 subdirectories
- **1300 lines**: Largest component (IntakePanel.tsx) — an anti-pattern
- **2** parallel routing patterns (workbench vs trips/[tripId])
- **2** generated type files that are near-duplicates
- **3** different data fetching patterns (react-query, direct fetch, manual useState)
- **1** stale backup file (marketing.bak.tsx)
- **1** duplicate nav definitions (design-system.ts vs nav-modules.ts)

### Immediate Next Action

Address P0 items first: route consolidation strategy (decide which pattern wins), then decompose IntakePanel.

---

## 2. Component Tree

```
src/
├── components/
│   ├── ui/                             9 files
│   │   ├── button.tsx                  Polymorphic with Slot/Radix, CVA
│   │   ├── card.tsx                    Compound: Card + CardHeader + CardTitle + CardDescription + CardContent + CardFooter
│   │   ├── badge.tsx                   CVA with semantic variants (explicit_user, derived, etc.)
│   │   ├── input.tsx                   Label + error + description + icons + size variants
│   │   ├── select.tsx                  Native select + custom chevron overlay + label/error/description
│   │   ├── textarea.tsx                Mirrors Input pattern
│   │   ├── loading.tsx                 Spinner + Skeleton (4 variants) + LoadingOverlay + InlineLoading
│   │   ├── icon.tsx                    IconWrapper + IconButton + IconLink
│   │   ├── tabs.tsx                    Custom accessible tabs (keyboard nav, aria)
│   │   └── SmartCombobox.tsx           Combobox with fuzzy matching + custom entry
│   │
│   ├── auth/
│   │   └── AuthProvider.tsx            Session hydration + redirect guard
│   │
│   ├── layouts/
│   │   ├── Shell.tsx                   App shell: sidebar + header + breadcrumb + integrity warning
│   │   └── UserMenu.tsx                Dropdown with user info, settings, logout
│   │
│   ├── navigation/
│   │   └── BackToOverviewLink.tsx      Simple back-link
│   │
│   ├── overview/
│   │   └── EmptyStateOnboarding.tsx    First-run 3-step guide
│   │
│   ├── inbox/                          6 files
│   │   ├── TripCard.tsx                Trip card with SLA, assignment, flags, priority — 426 lines
│   │   ├── InboxEmptyState.tsx         Contextual empty state with CTAs
│   │   ├── InboxFilterBar.tsx          Quick filter pills (tab-like)
│   │   ├── ComposableFilterBar.tsx     Advanced multi-select filter bar — 432 lines
│   │   ├── FilterPill.tsx              Reusable filter pill with tones/variants
│   │   └── ViewProfileToggle.tsx       Role-based view toggle
│   │
│   ├── workspace/
│   │   ├── panels/                     17 files
│   │   │   ├── IntakePanel.tsx         ~1300 lines — MONOLITH (inline sub-components)
│   │   │   ├── PacketPanel.tsx         ~550 lines — large fallback inline
│   │   │   ├── DecisionPanel.tsx       ~244 lines
│   │   │   ├── StrategyPanel.tsx       unknown
│   │   │   ├── TimelinePanel.tsx       ~286 lines — direct fetch (no react-query)
│   │   │   ├── TimelineSummary.tsx     unknown
│   │   │   ├── OutputPanel.tsx         unknown
│   │   │   ├── SafetyPanel.tsx         unknown
│   │   │   ├── SuitabilityPanel.tsx    ~302 lines — overlaps with SuitabilitySignal
│   │   │   ├── SuitabilitySignal.tsx   ~285 lines — overlaps with SuitabilityPanel
│   │   │   ├── SuitabilityCard.tsx     unknown
│   │   │   ├── StageAdvanceButton.tsx  unknown
│   │   │   ├── FeedbackPanel.tsx       unknown
│   │   │   ├── CaptureCallPanel.tsx    ~342 lines — uses gray/dark gray color tokens (different system)
│   │   │   ├── ChangeHistoryPanel.tsx  ~202 lines — localStorage audit log
│   │   │   ├── MetricDrillDownDrawer.tsx ~222 lines — inline Trip type (duplicated)
│   │   │   ├── ActivityTimeline.tsx    unknown
│   │   │   ├── ActivityProvenance.tsx  unknown
│   │   │   └── OverrideTimelineEvent.tsx unknown
│   │   ├── cards/
│   │   │   └── FollowUpCard.tsx        ~360 lines — inline modals (SnoozeModal, RescheduleModal)
│   │   ├── modals/
│   │   │   └── OverrideModal.tsx       ~285 lines — full form
│   │   ├── PlanningStageGate.tsx       unknown
│   │   └── ReviewControls.tsx          unknown
│   │
│   ├── visual/                         4 files
│   │   ├── index.ts                    Barrel export
│   │   ├── RevenueChart.tsx            Recharts ComposedChart
│   │   ├── PipelineFunnel.tsx          Recharts horizontal BarChart
│   │   ├── TeamPerformanceChart.tsx    Pure CSS grid
│   │   └── AnalyticsEmptyState.tsx     Empty state
│   │
│   ├── marketing/                      5 files + 1 .module.css
│   │   ├── marketing.tsx               Server components
│   │   ├── marketing-client.tsx        Client components
│   │   ├── marketing.bak.tsx           STALE BACKUP (should be archived)
│   │   ├── MarketingVisuals.tsx        Visual scenes
│   │   ├── dynamic-visuals.tsx         Dynamic imports
│   │   └── GsapInitializer.tsx         GSAP init
│   │
│   └── providers.tsx                   React Query QueryClientProvider
│   └── error-boundary.tsx              ErrorBoundary class + DefaultErrorFallback + InlineError + useErrorHandler HOC
│
├── contexts/                          2 files
│   ├── TripContext.tsx                 Trip-scoped context
│   └── CurrencyContext.tsx             localStorage-persisted currency
│
├── hooks/                             9 files with 20+ hooks
│   ├── useTrips.ts                    react-query (CRUD + list)
│   ├── useGovernance.ts               react-query (10+ hooks)
│   ├── useSpineRun.ts                 Manual fetch + polling
│   ├── useUnifiedState.ts             react-query
│   ├── useRuntimeVersion.ts           useEffect + fetch (single mount)
│   ├── useAgencySettings.ts           Manual useState + fetch (NOT react-query!)
│   ├── useFieldAuditLog.ts            localStorage
│   ├── useIntegrityIssues.ts          react-query
│   └── useScenarios.ts                react-query
│
├── stores/                            4 files (Zustand)
│   ├── auth.ts                        User, agency, membership, hydrate from cookie
│   ├── workbench.ts                   Input, config, results, draft, acknowledged flags
│   ├── themeStore.ts                  Theme + component variants (persisted)
│   └── index.ts                       Re-exports
│
├── types/                             5 files
│   ├── spine.ts                       Frontend types + re-exports from generated
│   ├── governance.ts                  Reviews, team, inbox
│   ├── audit.ts                       FieldChange, AuditLog
│   ├── pdfjs-dist.d.ts                Type declaration
│   └── generated/
│       ├── spine-api.ts               Auto-generated (522 lines)
│       └── spine_api.ts               DUPLICATE auto-generated (489 lines)
│
├── lib/                               30+ files
│   ├── api-client.ts                  Centralized HTTP client (894 lines)
│   ├── governance-api.ts              Governance-specific API calls
│   ├── bff-auth.ts                    Auth cookie forwarding
│   ├── bff-trip-adapters.ts           Backend-to-frontend transformers (581 lines)
│   ├── route-map.ts                   Backend route registry
│   ├── proxy-core.ts                  FastAPI proxy engine
│   ├── routes.ts                      URL builders
│   ├── nav-modules.ts                 CANONICAL nav model
│   ├── design-system.ts               DUPLICATE nav/layout definitions
│   ├── label-maps.ts                  FIELD_LABELS, STAGE_LABELS, etc.
│   ├── tokens.ts                      Design tokens: COLORS, SPACING, FONT, etc.
│   ├── utils.ts                       cn() helper
│   ├── accessibility.tsx              LiveRegion, ARIA helpers
│   ├── combobox.ts                    Fuzzy match, options
│   ├── currency.ts                    Multi-currency
│   ├── planning-status.ts             Planning field logic
│   ├── planning-list-display.ts       Trip card display helpers
│   ├── inbox-helpers.ts               SLA, filters, view profiles
│   ├── lead-display.ts                Formatting helpers
│   ├── timeline-rail.ts               Timeline helpers
│   └── ...others
│
└── app/                               Next.js App Router
    ├── (agency)/                      Authenticated routes
    │   ├── overview/
    │   ├── inbox/
    │   ├── trips/[tripId]/{intake,packet,decision,strategy,output,safety,suitability,timeline,followups}/
    │   ├── workbench/                  LEGACY tab-based workspace
    │   ├── insights/
    │   ├── reviews/
    │   ├── audit/
    │   └── settings/
    ├── (auth)/                        login, signup, reset-password, forgot-password, join
    ├── (public)/                      booking-collection
    ├── (traveler)/                    itinerary-checker
    └── api/                           BFF API routes + catch-all proxy
```

---

## 3. Detailed Component Analysis

### 3.1 `ui/` — Design System Primitives

**Strength**: Strong foundation. Every component uses `forwardRef`, `cn()`, exported interfaces, and CVA for variants. Accessibility is first-class (`useId()`, `aria-*`, `role` attributes).

**Findings**:
- **SmartCombobox.tsx** (334 lines) — Uses hard-coded hex colors like `#58a6ff`, `#161b22`, `#30363d` instead of design tokens `var(--accent-blue)`, `var(--bg-elevated)`. Needs token migration.
- **tabs.tsx** — Custom keyboard nav with `onMouseEnter`/`onMouseLeave` inline styles. Should use CSS classes instead.
- **select.tsx** — Inline SVG for chevron instead of lucide-react icons (minor inconsistency).
- **No barrel export**: Each component is imported individually. Adding an `index.ts` would simplify imports.
- **SmartCombobox hard-codes `bg-[rgba(var(--accent-blue-rgb)/0.1)]`** pattern but `--accent-blue-rgb` CSS variable may not exist (uses `rgba()` with CSS var that is a color string, not an RGB triple). Potential bug.

### 3.2 `layouts/` — Shell & UserMenu

**Strength**: Solid layout architecture with responsive sidebar (72px collapsed, 220px expanded), breadcrumb navigation, integrity warning banner.

**Findings**:
- **Shell.tsx** reads data from 4 hooks on every render: `useTrip`, `useRuntimeVersion`, `useUnifiedState`, `useAgencySettings`. Since Shell wraps all authenticated pages, these run on every page navigation. Consider using `staleTime` more aggressively.
- **Shell.tsx** has inline `onMouseEnter`/`onMouseLeave` handlers for hover color changes (lines 132-139, 324-331). Should use CSS `hover:` instead.
- **UserMenu.tsx** shows inline `bg-gradient-to-br from-[var(--accent-blue)] to-[var(--accent-cyan)]` for avatar — this works but is unconventional for a gradient on a 24x24 avatar.

### 3.3 `inbox/` — TripCard, Filter Components

**Strength**: Excellent composition pattern. TripCard uses `memo` correctly, decomposes into sub-components (TripCardMetrics, FlagBadge, TripCardSLA, etc.), uses profile-based metric display. InboxEmptyState is well-structured with contextual messaging.

**Findings**:
- **TripCard.tsx** defines inline `PRIORITY_BAR`, `SLA_BADGE`, `STAGE_BG`, `ASSIGNED_BG` color maps with hard-coded hex colors. These should be consolidated into `tokens.ts` or a shared constants file.
- **TripCard.tsx** uses `onMouseEnter`/`onMouseLeave` for hover effects. These are handled with `group-hover` in some places and inline JS in others — inconsistent.
- **ComposableFilterBar.tsx** (432 lines) — Complex but well-structured with 4 sub-components (FilterDropdown, ActiveFilterChips, QuickPresets, main). However, hard-coded colors throughout (`#161b22`, `#30363d`, `#e6edf3`, `#58a6ff`). Needs token migration.
- **FilterPill.tsx** has well-designed tone system (neutral, attention, ownership, risk) but mixes CSS classes with inline `border` styles.

### 3.4 `workspace/panels/` — Core Panels

**Critical findings**:
- **IntakePanel.tsx (~1300 lines)** — Largest component. Inline sub-components: `EditableField`, `BudgetField`, `PlanningDetailSection`. Direct `fetch()` calls alongside react-query. Multiple inline utility functions that duplicate logic in `lib/`. **Must be decomposed**.
- **PacketPanel.tsx** has inline `TripDetailsFallback` component (~150+ lines) that should be extracted.
- **SuitabilityPanel.tsx vs SuitabilitySignal.tsx** — Overlapping concerns. Both render suitability flags. `SuitabilityPanel` has override capabilities; `SuitabilitySignal` is simpler but also shows flags. Need unification or clear separation of concerns.
- **TimelinePanel.tsx** uses `fetch()` directly with `credentials: "include"` instead of using react-query or the api-client. TimelineSummary similarly does direct fetch in the layout. This means no caching, no deduplication, no retry.
- **CaptureCallPanel.tsx** uses `gray-*` / `dark:gray-*` Tailwind colors for dark mode — different from every other component which uses `var(--bg-surface)` CSS variable pattern. This component is isolated from the design system.
- **MetricDrillDownDrawer.tsx** defines an inline `Trip` interface (lines 7-16) that duplicates types from `types/spine.ts`. This will drift.

### 3.5 `workspace/modals/`

**OverrideModal.tsx** — Well-structured form with validation, severity checks, and radio group pattern. However, hard-codes colors throughout (`#0d1117`, `#30363d`, `#e6edf3`, `#238636`). Needs token migration.

### 3.6 `visual/` — Charts

**Strength**: Good use of Recharts, hydration-safe with `isMounted` guard, barrel export from `index.ts`.

**Findings**:
- `TeamPerformanceChart.tsx` uses a pure CSS grid (no chart library) — intentional and fine.
- Only `visual/` has a barrel export. All other component directories lack one.

### 3.7 `marketing/`

**Findings**:
- **marketing.bak.tsx** (163 lines) — Stale backup file preserved in source. Should be archived to `Archive/` per repo conventions.

### 3.8 `error-boundary.tsx`

**Strength**: Comprehensive error handling infrastructure — class component `ErrorBoundary`, `DefaultErrorFallback`, `InlineError`, `useErrorHandler` hook, `withErrorBoundary` HOC. Well-designed.

---

## 4. Routing Architecture

### The Dual-Pattern Problem

The frontend has **two parallel routing patterns** for workspace functionality:

| Pattern A: Per-Stage Trip Pages | Pattern B: Legacy Workbench |
|----------------------------------|------------------------------|
| `/trips/[tripId]/intake` | `/workbench?tab=intake` |
| `/trips/[tripId]/packet` | `/workbench?tab=packet` |
| `/trips/[tripId]/decision` | `/workbench?tab=decision` |
| `/trips/[tripId]/strategy` | `/workbench?tab=strategy` |
| `/trips/[tripId]/output` | `/workbench?tab=safety` |
| `/trips/[tripId]/safety` | Uses separate tab components: |
| `/trips/[tripId]/suitability` | `IntakeTab.tsx`, `PacketTab.tsx`, |
| `/trips/[tripId]/timeline` | `DecisionTab.tsx`, `StrategyTab.tsx`, |
| `/trips/[tripId]/followups` | `SafetyTab.tsx` |

**Workbench components** (`app/(agency)/workbench/`):
- `OpsPanel.tsx` — Main workbench orchestrator
- `IntakeTab.tsx`, `PacketTab.tsx`, `DecisionTab.tsx`, `StrategyTab.tsx`, `SafetyTab.tsx`
- `SettingsPanel.tsx`, `PipelineFlow.tsx`, `ScenarioLab.tsx`, `IntegrityMonitorPanel.tsx`, `RunProgressPanel.tsx`

**Analysis**:
- The per-stage `/trips/[tripId]` pages are the **target architecture** — they have proper layout with timeline sidebar, stage gating, and breadcrumbs.
- The `/workbench/` pattern is legacy — it uses a tab-based interface within a single page.
- **Both patterns are functional and being used**. The Shell.tsx "New Inquiry" CTA routes to `/workbench?draft=new&tab=intake`.
- The workbench tabs consume from the same Zustand workbench store as the per-stage panels.

**Recommendation**: This is NOT a simple replacement. The workbench has unique features (ScenarioLab, IntegrityMonitor, PipelineFlow, RunProgressPanel) that the per-stage pages don't. The right approach is:
1. Keep both for now
2. Move workbench-unique features into new dedicated routes or panels
3. Once migration is complete, archive workbench components

---

## 5. Data Flow & State Management

### Current Architecture

```
                     ┌──────────────────────┐
                     │   Zustand (Auth)      │  Global: user, agency, membership
                     │   Zustand (Workbench) │  Session: input, config, results
                     │   Zustand (Theme)     │  Persistent: theme, component variants
                     └──────────┬───────────┘
                                │
    ┌───────────────────────────┼───────────────────────────┐
    │                           │                           │
    ▼                           ▼                           ▼
┌──────────┐           ┌──────────────┐           ┌──────────────────┐
│ React-Query│          │ TripContext  │           │ CurrencyContext   │
│ (Server   │          │ (Per-trip)   │           │ (Persisted)       │
│  State)   │          │              │           │                   │
└──────────┘           └──────────────┘           └──────────────────┘
    │                           │
    │                           │
    ▼                           ▼
┌──────────────────────────────────────────┐
│            Components                     │
│  Some use react-query hooks              │
│  Some use direct fetch()                 │
│  Some use manual useState + fetch         │
└──────────────────────────────────────────┘
```

### Inconsistency: 3 Data Fetching Patterns

| Pattern | Used By | Missing Features |
|---------|---------|-----------------|
| **react-query** (useTrips, useGovernance, useScenarios, useUnifiedState) | Most data hooks | N/A — correct pattern |
| **Direct `fetch()`** | TimelinePanel, TimelineSummary, MetricDrillDownDrawer | No caching, no dedup, no retry, no error shaping |
| **Manual `useState` + `useEffect`** | useAgencySettings, useRuntimeVersion | No caching, no loading/error state consistency |

**Root cause**: The codebase grew organically. Different developers/agents contributed different patterns. The direct `fetch()` calls predate the react-query migration, and `useAgencySettings` was written after react-query was established but didn't adopt it.

### TripContext Pattern

`TripContext` is created at `trips/[tripId]/layout.tsx` with `{ tripId, trip, isLoading, error, refetchTrip, replaceTrip }`. This is used by DecisionPanel, OutputPanel, IntakePanel.

**Observation**: The context value is the same data available from `useTrip()` hook. The context adds convenience (no need to pass `tripId` through every level) but creates a second data path that can diverge from react-query cache. If a panel calls `useTrip(tripId)` directly and another uses `TripContext`, they could see different data.

### Workbench Store Bloat

The `workbench.ts` Zustand store (275 lines) manages:
- Input state (4 fields + setters)
- Config state (11 fields + setters including PARKED frontier features)
- Result state (10 fields + setters)
- Draft state (10 fields + setters)

The store has **35 individual setter functions** and **no slices** — it's a single flat store. As features grow, this will become unmanageable. Zustand supports slicing but it's not used here.

---

## 6. Type System

### The Duplicate Generated Types Problem

Two near-identical auto-generated files:
- `types/generated/spine-api.ts` (522 lines)
- `types/generated/spine_api.ts` (489 lines)

These are generated from Pydantic models. The second is likely a stale copy from a different generation run or naming convention. They have overlapping but not identical exports.

**Risk**: Importers may use either file. If one gets updated and the other doesn't, types will diverge silently.

### Inline Type Duplications

- **MetricDrillDownDrawer.tsx** defines inline `Trip` interface (7 fields) that partially overlaps with `types/spine.ts` `Trip` (100+ fields).
- **SuitabilityPanel.tsx** defines its own `SuitabilityFlag` interface that partially overlaps with `types/spine.ts` `SuitabilityFlagData`.

These inline types will drift from the canonical types.

### Nav Model Duplication

- `lib/nav-modules.ts` — Canonical nav model with 5 sections, 10 items, `enabled` flags
- `lib/design-system.ts` — Contains different `NAV_SECTIONS` (only 2 sections: "Operate" and "Govern" with 4 items total)

The `design-system.ts` version is outdated and has fewer items. Both are exported.

---

## 7. Anti-Patterns & Issues

### P0 — Blocking / Must Fix Before Launch

| # | Issue | Location | Impact |
|---|-------|----------|--------|
| 1 | **Dual file type generation** | `types/generated/spine-api.ts` vs `spine_api.ts` | Type drift; silent import errors |
| 2 | **Dual nav model** | `lib/nav-modules.ts` vs `lib/design-system.ts` | Navigation inconsistency; confused imports |
| 3 | **marketing.bak.tsx** | `components/marketing/marketing.bak.tsx` | Stale backup in source tree |

### P1 — Major / Must Fix Before Launch

| # | Issue | Location | Impact |
|---|-------|----------|--------|
| 4 | **IntakePanel.tsx ~1300 lines** | `components/workspace/panels/IntakePanel.tsx` | Monolith; impossible to test/maintain |
| 5 | **SuitabilityPanel vs SuitabilitySignal overlap** | Both in `panels/` | Duplicate flag rendering; behavioral inconsistency |
| 6 | **Inconsistent data fetching** | TimelinePanel, TimelineSummary, useAgencySettings | No caching; unpredictable performance |
| 7 | **Hard-coded hex colors in SmartCombobox, ComposableFilterBar, TripCard** | Multiple files | Theme drift; dark mode inconsistencies |
| 8 | **CaptureCallPanel uses gray/dark:gray** | `panels/CaptureCallPanel.tsx` | Isolated from design system token hierarchy |

### P2 — Minor / Fix When Convenient

| # | Issue | Location | Impact |
|---|-------|----------|--------|
| 9 | **No barrel exports for component directories** | All except `visual/` | Import verbosity |
| 10 | **Inline Trip type in MetricDrillDownDrawer** | `panels/MetricDrillDownDrawer.tsx` | Type drift risk |
| 11 | **Workbench store is flat, no slices** | `stores/workbench.ts` | Scalability limit as features grow |
| 12 | **TripContext duplicates react-query data** | `contexts/TripContext.tsx` | Dual data paths |
| 13 | **Inline hover handlers in Shell, TripCard** | Shell.tsx, TripCard.tsx | Should use CSS `hover:` |
| 14 | **Zustand acknowledged_flags uses ReadonlySet** | `stores/workbench.ts:225-228` | Novel but valid; creates new Set on every update |

### P3 — Polish / Optional

| # | Issue | Location | Impact |
|---|-------|----------|--------|
| 15 | **select.tsx inline SVG** | `ui/select.tsx` | Minor icon inconsistency |
| 16 | **tabs.tsx inline hover styles** | `ui/tabs.tsx` | Should use CSS classes |
| 17 | **UserMenu.tsx gradient on small avatar** | `layouts/UserMenu.tsx` | Visual inconsistency |

---

## 8. Gaps & Missing Infrastructure

| Gap | Current State | Impact |
|-----|--------------|--------|
| **Global toast/notification system** | Error handling is per-component (InlineError, local alerts) | No user-facing feedback for async operations |
| **Consistent loading skeletons** | Some pages show "Loading..." text; SkeletonCard exists but not consistently used | Inconsistent UX |
| **End-to-end testing** | No Playwright/Cypress tests found | Cannot verify integration flows |
| **i18n/l10n** | No infrastructure | English-only; blocks internationalization |
| **Feature flags** | Basic `enabled` flag in nav-modules.ts only | Hard to roll out features gradually |
| **Server-side audit trail** | `useFieldAuditLog` is localStorage-only | Audit data is device-specific; lost on browser change |
| **Service worker / PWA** | Nothing | No offline capability |

---

## 9. Consolidation Opportunities

### Opportunity 1: SuitabilityPanel ↔ SuitabilitySignal

| Feature | SuitabilityPanel | SuitabilitySignal |
|---------|-----------------|-------------------|
| Flag rendering | ✅ | ✅ |
| Tier grouping (critical/high/etc) | ✅ | ✅ (tier1/tier2) |
| Acknowledge support | ✅ | ✅ |
| Override modal | ✅ | ❌ |
| Drill-down callback | ❌ | ✅ |
| Uses design tokens | ❌ (gray colors) | ✅ (CSS vars) |

**Recommendation**: Make `SuitabilitySignal` the canonical lightweight renderer. Move override functionality from `SuitabilityPanel` into a new composable wrapper (`SuitabilityWithOverrides` or similar) that composes `SuitabilitySignal` + `OverrideModal`. Then remove `SuitabilityPanel`.

### Opportunity 2: Type System Cleanup

1. Delete duplicate `spine_api.ts` (underscore version)
2. Remove inline `Trip` type from `MetricDrillDownDrawer.tsx` — import from `@/types/spine`
3. Remove inline `SuitabilityFlag` from `SuitabilityPanel.tsx` — use `SuitabilityFlagData` from spine types
4. Consolidate `design-system.ts` nav model — either delete it or merge missing items into `nav-modules.ts`

### Opportunity 3: Data Fetching Unification

1. Convert `TimelinePanel` and `TimelineSummary` from direct `fetch()` to react-query hooks
2. Convert `useAgencySettings` from manual `useState` to react-query
3. Convert `useRuntimeVersion` from `useEffect` + fetch to react-query (or keep as-is for single-mount)

### Opportunity 4: Design Token Migration

The following files use hard-coded hex colors instead of CSS variables:

| File | Hard-coded Colors |
|------|------------------|
| SmartCombobox.tsx | `#58a6ff`, `#161b22`, `#30363d`, `#e6edf3` |
| ComposableFilterBar.tsx | `#161b22`, `#30363d`, `#e6edf3`, `#58a6ff`, `#0f1115` |
| OverrideModal.tsx | `#0d1117`, `#30363d`, `#e6edf3`, `#238636`, `#8b949e` |
| TripCard.tsx | `#f85149`, `#d29922`, `#58a6ff`, `#3fb950` |
| CaptureCallPanel.tsx | Tailwind `gray-*` / `dark:gray-*` |

### Opportunity 5: Decompose IntakePanel

Extract inline sub-components:
- `EditableField` → `workspace/panels/intake/EditableField.tsx`
- `BudgetField` → `workspace/panels/intake/BudgetField.tsx`
- `PlanningDetailSection` → `workspace/panels/intake/PlanningDetailSection.tsx`
- Spine progress stages → Move to `lib/spine-progress.ts`
- Inline utility functions → Move to `lib/trip-intake.ts`

### Opportunity 6: FollowUpCard Modals

`FollowUpCard.tsx` has inline `SnoozeModal` and `RescheduleModal` components. These should be extracted to `workspace/modals/` as reusable components.

---

## 10. Prioritized Recommendations

### Phase 1: Clean Up (Estimated: 1-2 days)

1. **Delete duplicate type file**: Remove `types/generated/spine_api.ts`, verify all imports use `spine-api.ts`
2. **Consolidate nav models**: Remove duplicate `NAV_SECTIONS` from `design-system.ts`, verify all imports
3. **Archive marketing.bak.tsx**: Move to `Archive/`
4. **Add barrel exports**: Create `index.ts` for `ui/`, `inbox/`, `workspace/panels/`, `workspace/modals/`

### Phase 2: Decompose (Estimated: 3-5 days)

5. **Extract IntakePanel sub-components**: EditableField, BudgetField, PlanningDetailSection → separate files
6. **Extract TripDetailsFallback from PacketPanel**
7. **Extract SnoozeModal + RescheduleModal from FollowUpCard**
8. **Unify SuitabilityPanel + SuitabilitySignal**: Make SuitabilitySignal canonical

### Phase 3: Unify Data Fetching (Estimated: 2-3 days)

9. **Create useTimeline hook**: react-query hook replacing direct `fetch()` in TimelinePanel, TimelineSummary
10. **Convert useAgencySettings to react-query**

### Phase 4: Token Migration (Estimated: 2-3 days)

11. **Migrate SmartCombobox, ComposableFilterBar, OverrideModal, TripCard colors** to CSS variables
12. **Migrate CaptureCallPanel to design system tokens**

### Phase 5: Architecture (Estimated: 3-5 days, depends on roadmap)

13. **Decide routing strategy**: Keep `/trips/[tripId]/*` as canonical. Plan migration of workbench-unique features
14. **Slice workbench store**: Group state into input/config/results/draft slices
15. **Evaluate TripContext relevance**: Can be replaced with direct react-query usage

---

## 11. 11-Dimension Audit

| Dimension | Verdict | Evidence & Gaps |
|-----------|---------|-----------------|
| **Code** | ✅ Good | TypeScript compiles, tests pass, consistent CVA/forwardRef/cn patterns across UI primitives |
| **Operational** | 🟡 Partial | UI is feature-complete but 6 consolidation items block launch polish. Dual routing confuses navigation |
| **User Experience** | 🟡 Partial | Good accessibility (aria attributes, keyboard nav, screen reader support). Hard-coded colors in SmartCombobox may break in non-default themes |
| **Logical Consistency** | 🟡 Partial | Dual nav model, dual type files, inline type definitions — data model drift risk |
| **Commercial** | ✅ Good | Feature-complete for current product needs. No blocking issues |
| **Data Integrity** | 🟡 Partial | Audit log is localStorage-only (device-specific). Direct fetch() calls have no retry logic |
| **Quality & Reliability** | 🟡 Partial | Tests exist but 1300-line IntakePanel has low test coverage per LOC. Inconsistent error handling (toast vs inline vs nothing) |
| **Compliance** | ✅ Good | Accessible forms (label/error/description pattern), PII handled through backend, no client-side secrets |
| **Operational Readiness** | 🟡 Partial | No E2E tests, no monitoring integration, no error tracking service |
| **Critical Path** | 🟡 Partial | Phase 1 (clean up) can start immediately. Phase 2-5 depend on product roadmap priorities |
| **Final Verdict** | **Code: ✅ Ready. Feature: 🟡 Partial. Launch: 🟡 Pending Phase 1-2** | |

---

## 12. Routing Dual-Pattern Deep Dive

### The Two Patterns Are NOT Identical

The `/workbench/` pattern has **features the per-stage pages don't**:
- `ScenarioLab.tsx` — Scenario testing/debugging interface
- `IntegrityMonitorPanel.tsx` — System integrity monitoring
- `PipelineFlow.tsx` — Pipeline visualization
- `RunProgressPanel.tsx` — Run progress tracking
- `SettingsPanel.tsx` — Workbench settings

And vice versa, the per-stage pages have features the workbench doesn't:
- Timeline sidebar with `TimelineSummary`
- Stage gating with `PlanningStageGate`
- Breadcrumb navigation with trip identity
- Role-based stage tab access

### Migration Strategy (Not Urgent — Architectural Guidance)

Short-term: Keep both. The workbench acts as a "developer mode" with debugging/scenario tools. The per-stage pages are the "operator mode" for production use.

Long-term:
1. Move ScenarioLab → `/scenarios` or `/debug/scenarios`
2. Move IntegrityMonitor → `/admin/integrity` or as a panel in `/settings`
3. Move PipelineFlow → integrate into `/trips/[tripId]/timeline`
4. Move RunProgressPanel → integrate into `/trips/[tripId]/intake`
5. Move SettingsPanel → integrate into `/settings`
6. Once all features are migrated, archive workbench components

---

## 13. Open Questions

1. **Are both routing patterns intentionally maintained for different audiences** (operator vs developer)? The workbench has scenario/debug features that suggest it may be intentional. Clarify before starting Phase 5.

2. **Should `useFieldAuditLog` be migrated to a server-side audit trail?** The localStorage approach means audit data is device-specific and non-portable. Is this acceptable for the current phase?

3. **What is the long-term plan for the `workbench` Zustand store?** It currently holds both the old workbench state AND the new panel state. Should it be replaced by react-query + local state as panels are migrated?

4. **Are the PARKED frontier features in `workbench.ts` (ghost concierge, sentiment analysis, etc.) still planned?** These fields add complexity to the store and are gated by explicit comments not to expose them.

---

## 14. Next Steps

### Immediate (can start now, no decisions needed):
1. Delete duplicate `spine_api.ts` type file
2. Consolidate nav models (remove from `design-system.ts`)
3. Archive `marketing.bak.tsx`
4. Add barrel exports to component directories

### Needs Discussion:
5. Decompose IntakePanel — decide on file organization strategy
6. SuitabilityPanel vs SuitabilitySignal unification approach
7. Routing strategy for workbench migration
8. Whether to migrate `useFieldAuditLog` to server-side

### Verification After Any Changes:
```bash
cd frontend && npx tsc --noEmit  # TypeScript check
cd frontend && npx vitest run      # Test suite
```

---

*This document was produced as part of the Frontend Component Architecture Study. All findings are based on the actual codebase state as of 2026-05-05. No code was modified during the study.*
