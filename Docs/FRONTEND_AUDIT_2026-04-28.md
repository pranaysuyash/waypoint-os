# Frontend Technical Audit -- travel_agency_agent

**Date:** 2026-04-28

---

## Framework & Library Overview

| Aspect | Details |
|--------|---------|
| Framework | Next.js 16 (App Router) + Turbopack |
| UI Library | React 19.2.4 |
| Language | TypeScript 5 (strict mode) |
| Styling | Tailwind CSS 3.4 + custom CSS variables design system |
| State | Zustand 5 (3 stores: auth, workbench, theme) |
| Component Lib | Custom UI kit (CVA variants, Radix Slot, tailwind-merge) |
| Icons | Lucide React (optimized via `optimizePackageImports`) |
| Charts | Recharts + TanStack React Table |
| Animation | GSAP 3.15 (marketing pages only) |
| HTTP | Custom `ApiClient` class with retry, timeout, exponential backoff |
| Testing | Vitest + Testing Library (jsdom), bundle analyzer |

---

## Strengths

1.  **Design system maturity** -- `globals.css` has a well-structured CSS-custom-property design system with WCAG-aware tokens, fluid `clamp()` typography, state color maps, and a Liquid Garden premium theme layer. (`src/app/globals.css:5-142`)
2.  **Layered error handling** -- Class-based `ErrorBoundary`, per-route `error.tsx`, `InlineError` component, and API-level `normalizeErrorPayload` with retry/exponential backoff. (`src/components/error-boundary.tsx`, `src/app/error.tsx`, `src/lib/api-client.ts:163-194`)
3.  **Accessibility foundation** -- Skip link, `aria-live` regions (`LiveRegion` component), `sr-only` utilities, proper ARIA tab pattern with keyboard navigation (`ArrowLeft/Right/Home/End`), `focus-visible` ring styles, `aria-invalid`/`aria-describedby` on form controls. (`src/lib/accessibility.tsx`, `src/components/ui/tabs.tsx`)
4.  **Good component architecture** -- Consistent `forwardRef` + `displayName` pattern, CVA variant-based styling, composition with `asChild` via Radix Slot. (`src/components/ui/button.tsx`, `src/components/ui/card.tsx`)
5.  **Auth security** -- Cookie-based httpOnly auth, Zustand as in-memory cache only, explicit hydrate/refresh/logout lifecycle with redirect guards. (`src/stores/auth.ts`, `src/components/auth/AuthProvider.tsx`)
6.  **API Client design** -- Clean class-based `ApiClient` with typed generics, abort-controller timeout, selective non-retry on 401/403/404, normalized error payload extraction. (`src/lib/api-client.ts:61-228`)
7.  **TypeScript discipline** -- `strict: true`, minimal `any` usage (only `result_frontier`), well-typed API responses, dedicated generated types from backend contract. (`src/types/spine.ts`)
8.  **Dynamic import for heavy tabs** -- All workspace tabs use `next/dynamic` with `Suspense` fallbacks, keeping initial bundle lean. (`src/app/workbench/page.tsx:40-56`)
9.  **Contrast validation** -- Dedicated `contrast-utils.ts` with WCAG AA/AAA compliance checker and `ensureContrast` correction utility. (`src/lib/contrast-utils.ts`)
10. **Testing infrastructure** -- Vitest with jsdom, Testing Library setup, mocked router + Image components, `matchMedia` polyfill for GSAP compatibility. (`vitest.setup.tsx`)

---

## Issues Found

### P0 -- Critical

1.  **Stale closure risk in store hydration** -- `useHydrateStoreFromTrip` depends on individual store setter refs. If setters change, the effect re-runs and overwrites in-progress user edits. The `hydratedRef` guard only prevents infinite loops, not data loss. (`src/app/workbench/page.tsx:118-152`)

2.  **`handleProcessTrip` callback instability** -- The `useCallback` depends on the entire `store` object (not individual selectors), meaning every zustand state change recreates the callback, causing unnecessary child re-renders. (`src/app/workbench/page.tsx:229-272`)

3.  **`dangerouslySetInnerHTML` for display content** -- Lines 279-280 use `dangerouslySetInnerHTML` with `${k}` and `${v}`. Currently mock label data, but a future data source change could introduce XSS. (`src/app/page.tsx:279-280`)

### P1 -- Medium

4.  **Massive hook boilerplate duplication** -- The `LoadingWithDelay` pattern is copy-pasted ~15 times across `useTrips.ts` and `useGovernance.ts`. Each hook has identical `loadingTimeoutRef`, cleanup, and state boilerplate. Should extract `useAsyncData<T>` hook. (`src/hooks/useTrips.ts`, `src/hooks/useGovernance.ts`)

5.  **Fragile `JSON.stringify` dependency serialization** -- `paramsKey = JSON.stringify(params)` for effect dependency. Different key ordering produces different strings, risking infinite refetch loops if parent passes inline objects. (`src/hooks/useTrips.ts:37`)

6.  **`result_frontier` typed as `any`** -- Bypasses type safety for the frontier intelligence result. Should be typed from the generated Spine contract. (`src/stores/workbench.ts:63`)

7.  **`IntakeTab` select triggers `router.replace` per change** -- Each `<select>` change calls `updateUrlParam` which constructs new `URLSearchParams` and calls `router.replace`, causing full-page rerender. Should debounce or batch. (`src/app/workbench/IntakeTab.tsx:51-55`)

8.  **SmartCombobox missing WAI-ARIA combobox pattern** -- No `role="combobox"`, no `aria-expanded`, no `aria-controls`, no `aria-activedescendant`. Keyboard navigation works but screen readers won't announce the combobox relationship. (`src/components/ui/SmartCombobox.tsx`)

9.  **`error.tsx` uses `<a>` instead of Next.js `Link`** -- Line 62 `<a href="/">` triggers full page navigation on error recovery instead of client-side transition. (`src/app/error.tsx:62-68`)

10. **No dynamic page `<title>` management** -- Layout sets fixed "Waypoint OS" title. Dynamic pages (workspace, inbox, overview) don't set page-specific titles via `metadata` or `useDocumentHead`. (`src/app/layout.tsx:29-32`)

### P2 -- Minor

11. **Sidebar breakpoint too high for tablets** -- `md:` (768px) collapses sidebar to icon-only. Tablets in landscape (1024x768) get cramped layout. (`src/components/layouts/Shell.tsx:131`)

12. **`text-muted` (#8b949e) fails WCAG AA for small text** -- At 3.9:1 contrast on `bg-canvas`, this passes only for large text. Comment acknowledges this but doesn't warn consumers to restrict usage. (`src/app/globals.css:17`)

13. **Duplicate `:focus-visible` rules** -- Defined twice in globals.css (identical styles). Redundant but not harmful. (`globals.css:215-218` and `492-495`)

14. **`CurrencyContext.formatAsPreferred` is a stub** -- Always formats with `en-IN` locale regardless of target currency, ignores `fromCurrency`. No actual conversion. (`src/contexts/CurrencyContext.tsx:45-51`)

15. **`themeStore.setTheme` directly accesses `document.body`** -- Will throw during SSR if a component calls `setTheme` before hydration. Missing `typeof window` guard. (`src/stores/themeStore.ts:50-53`)

16. **`page.tsx` and `v2/page.tsx` -- Duplicate marketing pages** -- Two very similar marketing landing pages create maintenance burden and potential SEO confusion. (`src/app/page.tsx`, `src/app/v2/page.tsx`)

17. **Tab panel focusable but no focus management** -- `tabIndex={0}` on the tabpanel makes it focusable, but focus isn't managed when tabs change. Keyboard users may need to re-navigate. (`src/app/workbench/page.tsx:494`)

18. **GSAP loaded on all marketing pages** -- GSAP (non-trivial bundle) is imported and initialized via `GsapInitializer` on the main marketing page, even if animations aren't visible above the fold. (`src/app/page.tsx:117`)

---

## Scores

| Category | Score | Rationale |
|----------|-------|-----------|
| Frontend Quality | 7.5/10 | Well-architected design system and API layer. Strong TS/accessibility patterns. Deducted for hook boilerplate duplication and missing combobox ARIA pattern. |
| Accessibility | 7/10 | Skip link, live regions, proper tab ARIA, focus-visible, aria-describedby on forms all present. Deducted for combobox ARIA violation, `text-muted` contrast gap, no focus management on tabpanel. |
| Performance | 8/10 | Dynamic imports on all tabs, lucide-react optimized, Next.js 16 Turbopack, compress/gzip enabled, no obvious re-render hot loops. Deducted for unstable `useCallback` deps and GSAP on initial load. |

## Remediation Recommendations

### Immediate (P0)
1.  Refactor `useHydrateStoreFromTrip` to use individual store selectors instead of the full store object, or guard against overwriting dirty state with a `isDirty` check.
2.  Extract `useAsyncData<T>` hook to eliminate the 15x copy-pasted loading-timeout pattern.
3.  Remove `dangerouslySetInnerHTML` usage on homepage -- render labels as static React children instead.

### Short-term (P1)
4.  Add proper `role="combobox"`, `aria-expanded`, `aria-activedescendant` to SmartCombobox following WAI-ARIA 1.2 combobox pattern.
5.  Type `result_frontier` properly from generated Spine contracts instead of `any`.
6.  Add dynamic page title metadata via `generateMetadata` or `useDocumentHead` for workspace/inbox/overview pages.
7.  Replace `<a href="/">` in error.tsx with Next.js `<Link>`.
8.  Fix `CurrencyContext` format logic or add a real FX rate service.

### Long-term (P2)
9.  Add `typeof window !== 'undefined'` guard in `themeStore.setTheme`.
10. Consolidate `page.tsx` and `v2/page.tsx` into a single canonical marketing page with feature flags.
11. Consider lazy-loading GSAP only when scroll-triggered animations are detected.
12. Audit all `#8b949e` usages to ensure they're only applied to text >=18px or bold >=14px.
