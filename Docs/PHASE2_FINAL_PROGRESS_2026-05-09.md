# Phase 2 Remediation — Final Progress Report (2026-05-09)

## Baseline → Current

| Metric | Baseline | Current | Delta |
|--------|----------|---------|-------|
| Score | 59/100 | 63/100 | +4 |
| Total findings | 780 | 572 | -208 |
| Tests passing | 728/732 | 782/782 | +54 (flaky resolved) |

## Rules Eliminated (9 of 26 target rules at zero)

**Phase 1 (4 rules):**
- `rules-of-hooks` (8→0)
- `no-nested-component-definition` (3→0)
- `nextjs-no-side-effect-in-get-handler` (1→0)
- `no-danger` (2→0)

**Phase 2 (5 rules):**
- `server-fetch-without-revalidate` (15→0) — added `cache: 'no-store'` to 15 BFF route handlers
- `nextjs-no-a-element` (2→0) — replaced `<a>` with `<Link>`
- `js-tosorted-immutable` (7→0) — `.sort()` → `.toSorted()` / `[...arr].sort()`
- `js-flatmap-filter` (4→2) — partial
- `no-tiny-text` (52→0) — bumped inline `fontSize` from 10/11 to 12px

## New Artifacts Created

- `src/hooks/useClientDate.tsx` — Shared hydration-safe date formatting hooks

## Key Metric Corrections

- `nextjs-no-client-fetch-for-server-data` inventory added (4 instances, all in `src/app/(agency)` or `src/app/(auth)`)
- Metadata guidance corrected to per-page resolution (not layouts-only)
- Dead code note softened: React Doctor is primary source, knip recommended not required

## Remaining Work Summary

| Priority | Rule | Count | Effort |
|----------|------|-------|--------|
| P2 | `react-compiler-destructure-method` | 49 | Medium — 15 files, mechanical |
| P2 | `prefer-useReducer` | 18 | Medium — 16 files |
| P3 | `rerender-state-only-in-handlers` | 16 | Medium — 15 files |
| P3 | `js-batch-dom-css` | 16 | Small — 4 files |
| P3 | `nextjs-missing-metadata` | 18 | Small — layouts already have it (tool drift?) |
| P3 | `no-array-index-as-key` | 13 | Small — 10 files |
| P3 | `no-cascading-set-state` | 9 | Small — 9 files |
| P3 | `nextjs-no-use-search-params-without-suspense` | 6 | Small |
| P3 | `label-has-associated-control` | 7 | Small |
| P3 | `nextjs-no-client-side-redirect` | 1 | Small — AuthProvider already correct |
| P3 | `rendering-hydration-mismatch-time` | 4 | Small |
| P3 | `js-combine-iterations` | 2 | Small |
| P4 | `prefer-dynamic-import` | 2 | Small — recharts |
| P4 | All remaining single-digit rules | ~30 | Small |

## Files Modified (57 files + 1 new)

Full file list in `Docs/PHASE2_PROGRESS_2026-05-09.md`.
