# Frontend Performance Fixes: React Best Practices Audit

> Based on **react-best-practices** skill (`~/Projects/skills/react-best-practises/`)
> Lighthouse baseline: 54/100 (LCP 7.3s, TBT 580ms, CLS 0.138, 420KB wasted JS)

## Task 1: Remove next-devtools from Production Build

**Rule reference:** `bundle-conditional` — Load modules only when feature is activated

**Current state:** `node_modules_next_dist_compiled_next-devtools_index_0553esy.js` ships at 135KB, 63% unused.

**File(s) to modify:**
- `frontend/next.config.ts`

**Implementation:**
Add `serverComponentsExternalPackages` or configure webpack to exclude next-devtools in production:

```ts
// next.config.ts
const nextConfig: NextConfig = {
  // ... existing config ...
  webpack: (config, { dev }) => {
    if (!dev) {
      // Exclude devtools in production
      config.plugins = config.plugins?.filter(
        (p) => p.constructor.name !== 'DevToolsPlugin'
      );
    }
    return config;
  },
};
```

Alternatively, if next-devtools is only in `devDependencies`, ensure the build step uses `NODE_ENV=production` properly.

**Verification:**
```bash
# Before
lighthouse http://localhost:3000 --output=json --chrome-flags="--headless" | python3 -c "import sys,json; d=json.load(sys.stdin); u=d['audits']['unused-javascript']['details']['items']; n=[i for i in u if 'next-devtools' in i['url']]; print('devtools present' if n else 'devtools removed')"

# After
# Run the same command — should show "devtools removed"
```

---

## Task 2: Dynamic Import GSAP

**Rule reference:** `bundle-dynamic-imports` — Use `next/dynamic` for heavy components

**Current state:** `GsapInitializer.tsx` imports `gsap` + `gsap/ScrollTrigger` as static imports (71KB+). GSAP is marketing-only (scroll animations), so it should not load on agency pages at all. Lighthouse shows 44KB wasted.

**File(s) to modify:**
- `frontend/src/components/marketing/GsapInitializer.tsx`
- Any file that imports `GsapInitializer` (likely the marketing landing page)

**Implementation:**
```tsx
// In the component/page that uses GsapInitializer:
import dynamic from 'next/dynamic'

const GsapInitializer = dynamic(
  () => import('@/components/marketing/GsapInitializer').then(m => m.GsapInitializer),
  { ssr: false }
)
```

**Constraints:**
- `GsapInitializer` is `'use client'` already — no SSR issue
- Must only load on marketing/public pages, not in the `(agency)` route group

**Verification:**
Run Lighthouse audit on the agency pages — GSAP should not appear in unused JS.

---

## Task 3: Dynamic Import Recharts

**Rule reference:** `bundle-dynamic-imports` — Use `next/dynamic` for heavy components

**Current state:** `RevenueChart.tsx` and `PipelineFunnel.tsx` statically import from `recharts`. This library should only load when the user visits the insights/analytics pages.

**File(s) to modify:**
- `frontend/src/components/visual/RevenueChart.tsx`
- `frontend/src/components/visual/PipelineFunnel.tsx`
- Any page that imports these components

**Implementation:**
```tsx
// In the page/component that renders the chart:
import dynamic from 'next/dynamic'

const RevenueChart = dynamic(
  () => import('@/components/visual/RevenueChart'),
  { ssr: false }
)
```

**Constraint:**
- Recharts components are likely client-only — `ssr: false` is appropriate

**Verification:**
Check bundle analyzer output — recharts should move to a separate chunk loaded only on insight pages.

---

## Task 4: GSAP Gating — Only Load on Marketing Pages

**Rule reference:** `bundle-conditional` — Load modules only when feature is activated

**Current state:** If `GsapInitializer` (or GSAP) is referenced anywhere in the shared component tree or layout that wraps both marketing and agency routes, it gets loaded on every page.

**File(s) to check:**
- `frontend/src/app/layout.tsx` — root layout
- `frontend/src/app/(marketing)/layout.tsx` — marketing layout (if exists)
- Any shared providers or shell components

**Implementation:**
Ensure `GsapInitializer` is only imported in the marketing route group, not in the root layout or agency layout.

**Verification:**
Navigate to an agency page (e.g., `/trips`). Lighthouse should show zero GSAP-related JS.

---

## Acceptance Criteria

| # | Criteria | How to verify |
|---|----------|---------------|
| 1 | next-devtools not in production build | Lighthouse unused JS list no longer shows next-devtools |
| 2 | GSAP not loaded on agency pages | Agency page Lighthouse shows 0KB GSAP |
| 3 | Recharts lazy-loaded on insight pages only | Recharts appears as separate chunk in network tab |
| 4 | Performance score improves | Lighthouse re-audit shows score >= 65 |

## Verification Command

After all fixes:

```bash
lighthouse http://localhost:3000 --output=json --chrome-flags="--headless" --only-categories=performance --output-path=/tmp/lighthouse_post_fix.json && python3 -c "
import json
with open('/tmp/lighthouse_post_fix.json') as f:
    r = json.load(f)
s = r['categories']['performance']['score'] * 100
u = r['audits']['unused-javascript']['details']['items']
w = sum(i.get('wastedBytes', 0) for i in u) / 1024
print(f'Score: {s:.0f}/100')
print(f'Wasted JS: {w:.0f}KB')
print(f'Performance improved: {\"YES\" if s >= 65 else \"NO — needs more work\"}')
"
```

## Reference

This audit was conducted using the **react-best-practices** skill at `~/Projects/skills/react-best-practices/SKILL.md` (45 rules across 8 categories). The full rule reference is in `AGENTS.md` within that skill directory.
