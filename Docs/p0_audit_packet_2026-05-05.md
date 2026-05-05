# P0 Audit Packet — Three Findings Before Code Change

**Date**: 2026-05-05
**Prepared for**: Code change decision — Finding 1 (duplicate types), Finding 2 (dual nav model), Finding 3 (stale backup)
**Evidence verified**: All files read, references collected, git state confirmed, tests passing.

---

## Finding 1: Duplicate API Type Files

### 1.1 File Locations

| File | Path | Size | Lines |
|------|------|------|-------|
| `spine-api.ts` (hyphen) | `frontend/src/types/generated/spine-api.ts` | ~15KB | 522 |
| `spine_api.ts` (underscore) | `frontend/src/types/generated/spine_api.ts` | ~14KB | 489 |

### 1.2 Both Files (Full Content)

**Both files included above** — They are structurally identical in content (same interfaces, same order, same JSDoc headers). The only difference:
- `spine-api.ts` (522 lines) — has 4 extra blank lines around `PublicCheckerArtifactUpload`, `PublicCheckerArtifactManifest`, `PublicCheckerExportResponse`, `PublicCheckerDeleteResponse` interfaces
- `spine_api.ts` (489 lines) — missing those 4 interfaces entirely. Also has different blank line counts in a few places.

**Missing from `spine_api.ts` (underscore) that are present in `spine-api.ts` (hyphen):**
- `PublicCheckerArtifactUpload`
- `PublicCheckerArtifactManifest`
- `PublicCheckerExportResponse`
- `PublicCheckerDeleteResponse`

This means `spine_api.ts` is **stale** — generated from an older version of the Pydantic models before the public checker types were added.

### 1.3 Codegen Script

The canonical generator is at **`scripts/generate_types.py`**. It writes **both** files:

```python
OUTPUT_FILE = OUTPUT_DIR / "spine_api.ts"         # line 30 — underscore
ALIAS_OUTPUT_FILE = OUTPUT_DIR / "spine-api.ts"   # line 31 — hyphen
```

Then at lines 56-60 it writes the same body to both files. The script was designed to produce an alias for compatibility, but the underscore version (`spine_api.ts`) is the **primary** output and the hyphen version (`spine-api.ts`) is the **alias**.

**Problem**: The alias has **not** been reliably updated. The underscore version (`spine_api.ts`) is missing the 4 `PublicChecker*` interfaces that exist in the hyphen version (`spine-api.ts`). This means the alias contains fresher types than the primary.

### 1.4 All Imports / References in Codebase

**Code imports (`from '@/types/generated/...'`):**

| File | Import Path | Which File It Resolves To |
|------|------------|--------------------------|
| `src/types/spine.ts:32` | `from '@/types/generated/spine-api'` | **spine-api.ts** (hyphen) |
| `src/types/governance.ts:24` | `from '@/types/generated/spine-api'` | **spine-api.ts** (hyphen) |
| `src/app/api/trips/route.ts:7` | `from '@/types/generated/spine-api'` | **spine-api.ts** (hyphen) |

**No code imports from `@/types/generated/spine_api`** (underscore). The underscore file is **dead code** — nothing in the frontend imports it.

**Comment-only references to `spine_api` (the Python backend, not the type file):**

| File | Context |
|------|---------|
| `src/app/api/reviews/route.ts:7` | Comment: "Types returned by the spine_api /analytics/reviews endpoint" |
| `src/app/api/reviews/route.ts:103` | `console.error("Error fetching reviews from spine_api:", error);` |
| `src/app/api/reviews/action/route.ts:42` | `console.error("Error processing review action via spine_api:", error);` |
| `src/app/api/trips/[id]/route.ts:13` | Comment: "Forward request to spine_api" |
| `src/app/api/trips/[id]/route.ts:89` | Comment: "Forward request to spine_api" |
| `src/app/api/trips/route.ts:18` | Comment: "Strip our custom param before forwarding to spine_api" |
| `src/app/api/trips/route.ts:46` | `console.error("Error fetching trips from spine_api:", error);` |
| `src/app/api/[...path]/route.ts:2` | Comment: "Catch-all proxy: /api/[...path] → FastAPI spine_api" |
| `src/app/api/followups/route.ts:22` | `console.error("Error fetching followups dashboard from spine_api:", error);` |
| `src/app/api/inbox/[tripId]/snooze/route.ts:41` | `console.error("Error snoozing trip via spine_api:", error);` |

These are all comments and log messages referring to the **Python FastAPI application** named `spine_api`, not the TypeScript type file.

### 1.5 Actual Schema Drift (Verified via `diff`)

The stale `spine_api.ts` (underscore) is missing from `spine-api.ts` (hyphen):

**Missing interfaces (4):**
- `PublicCheckerArtifactUpload`
- `PublicCheckerArtifactManifest`
- `PublicCheckerExportResponse`
- `PublicCheckerDeleteResponse`

**Missing fields on existing interfaces (2):**
- `SpineRunRequest.retention_consent: boolean` (present in hyphen, absent in underscore)
- `TimelineEvent.actor: string | null` (present in hyphen, absent in underscore)

**Total drift**: 4 interfaces + 2 field-level schema differences. This is more than cosmetic — `retention_consent` is a functional field affecting data flow.

### 1.6 Verdict

| Question | Answer |
|----------|--------|
| **Which is canonical?** | **`spine-api.ts` (hyphen)** — more complete, all imports use it |
| **Which is stale/duplicate?** | **`spine_api.ts` (underscore)** — missing 4 interfaces + 2 fields, no runtime consumers |
| **Which runtime paths import which?** | All consumer code imports `@/types/generated/spine-api` (hyphen). Zero code imports `spine_api` (underscore) |
| **Root cause?** | Having **two generated outputs** creates drift risk. `scripts/generate_types.py` writes `spine_api.ts` first, reads it back, then writes the same body to `spine-api.ts`. A fresh successful run should make both identical — but they can diverge through: (a) partial/stale generator runs, (b) manual edits to one file, (c) one file committed without regenerating the other, (d) alternate generation workflows that target only one path. The root fix is to have **one canonical output path**, not two. |

**Fix**: Delete `spine_api.ts` (underscore). Update `scripts/generate_types.py` to write only to `spine-api.ts` (single canonical file). No compatibility re-export needed — zero imports reference the underscore path.

---

## Finding 2: Dual Nav Model

### 2.1 File Locations

| File | Path | Size | Lines |
|------|------|------|-------|
| `nav-modules.ts` | `frontend/src/lib/nav-modules.ts` | 2.1KB | 70 |
| `design-system.ts` | `frontend/src/lib/design-system.ts` | 2.0KB | 74 |

### 2.2 Both Files (Full Content Above)

### 2.3 All Imports / References

**`nav-modules.ts` (imported by 2 files + 1 test):**

| File | Import Line |
|------|-------------|
| `src/components/layouts/Shell.tsx:32` | `import { NAV_SECTIONS } from '@/lib/nav-modules';` |
| `src/lib/__tests__/nav-modules.test.ts:2` | `import { NAV_SECTIONS } from '../nav-modules';` |

**`design-system.ts` (imported by 0 files):**

```
Zero imports found.
```

No component, hook, store, or test imports from `design-system.ts`. The grep for `from ".*design-system.*"` or `from '.*design-system.*'` returned zero results.

### 2.4 Direct Comparison

| Dimension | `nav-modules.ts` (canonical) | `design-system.ts` (stale) |
|-----------|------------------------------|---------------------------|
| **Interface** | `NavItem { href, label, icon, description, enabled }` | `NavItem { label, href, description }` |
| **Icon support** | ✅ Icon map via string key (LayoutDashboard, Inbox, etc.) | ❌ No icon field |
| **Feature flags** | ✅ `enabled: boolean` per item (5 items enabled, 5 planned) | ❌ No feature flagging |
| **Sections / Items** | **5 sections, 10 items** | **2 sections, 4 items** |
| | COMMAND: Overview, Lead Inbox, Quote Review | Operate: Lead Inbox, Trip Workspace |
| | PLANNING: Trips in Planning, Quotes, Bookings | Govern: Approval Queue, Insights |
| | OPERATIONS: Documents, Payments, Suppliers | |
| | INTELLIGENCE: Insights, Audit, Knowledge Base | |
| | ADMIN: Settings | |
| **Route `/workbench`** | NOT present (intentionally — see architectural note: "Routes represent product modules, not personas. /workbench is not a durable user-facing module name.") | PRESENT as "Trip Workspace" → `/workbench` |
| **Route `/overview`** | PRESENT in COMMAND section | NOT present |
| **Route `/trips`** | PRESENT as "Trips in Planning" | NOT present |
| **Planned routes** | `/quotes`, `/bookings`, `/documents`, `/payments`, `/suppliers`, `/knowledge`, `/audit` | None |
| **Extra features** | Icon map, `enabled` flags, architectural notes | `isRouteActive()`, `getPageTitle()`, `PRODUCT_COPY` constants |

### 2.5 What Actually Consumes These

- **Shell.tsx** imports and renders `NAV_SECTIONS` from `nav-modules.ts` — this is the real navigation in production.
- **nav-modules.test.ts** tests the canonical module.
- **design-system.ts** is **dead code**. Its `isRouteActive()` and `getPageTitle()` functions are never called anywhere in the codebase.

### 2.6 Verdict

| Question | Answer |
|----------|--------|
| **Do they duplicate route labels?** | Yes, but `design-system.ts` has an outdated/wrong set (only 4 routes vs 10) |
| **Feature flags?** | Only `nav-modules.ts` has them. `design-system.ts` has none. |
| **Permissions?** | Neither file handles permissions |
| **Ordering?** | Both have ordering, `design-system.ts` is incomplete |
| **Icons?** | Only `nav-modules.ts` has icon references |
| **Visibility rules?** | Only `nav-modules.ts` has `enabled` flags |
| **Which is canonical?** | **`nav-modules.ts`** — consumed by Shell.tsx, has tests, has feature flags, has icons, has all routes |
| **Which is stale/duplicate?** | **`design-system.ts`** — zero imports, missing 6 routes, no icon map, no feature flags, routes to `/workbench` (intentionally avoided by canonical) |

**Fix**: Delete the `NAV_SECTIONS` export from `design-system.ts`. The `PRODUCT_COPY` constants can be preserved if they have consumers (but they don't appear to). Or remove the entire file since nothing imports from it.

**Pre-cleanup check**: Verify nothing imports from `design-system.ts` across the entire frontend.
Result: Already done — zero imports.

---

## Finding 3: marketing.bak.tsx

### 3.1 File Location

`frontend/src/components/marketing/marketing.bak.tsx` (163 lines)

### 3.2 Full Content (above)

### 3.3 The Current Live File

`frontend/src/components/marketing/marketing.tsx` (119 lines)

The live `marketing.tsx` has these **differences from the bak**:
- Uses `next/image` with proper `width/height/priority` (bak uses `<img>`)
- Uses `'waypoint-logo-primary.svg'` (bak uses `'waypoint-logo-compass.svg'`)
- Has proper `aria-label` on brand link (bak doesn't)
- Removed `CtaBand` and `DemoButton` (moved to `marketing-client.tsx` for client-side interactivity)
- Removed the `brandLogo` inline `<span>` with tagline text (simplified header)

### 3.4 References in Codebase

```
Zero results from `rg "marketing\.bak|bak\.tsx"` across the entire frontend directory.
```

The file is **not imported**, **not routed**, **not referenced anywhere** in the codebase. It's entirely dead.

### 3.5 AGENTS.md Code Preservation Rules

The relevant sections from `AGENTS.md`:

- **Line 359**: "All new, revised, or recovered code must be additive, better, and comprehensive against the current codebase."
- **"Redundant superseded code"** rule: "If a component/function is fully replaced by another that does the same job better, removal is preferred over keeping dead code."
- **"Unused but potentially useful"** rule: "This is different from redundant. A utility hook, type definition, or helper that isn't currently called but serves a clear purpose for upcoming work — keep it."

Since `marketing.bak.tsx` is:
1. Fully superseded by `marketing.tsx` + `marketing-client.tsx`
2. Not imported by anything
3. Contains no unique functionality (all its exports exist in current files)
4. The live files have **improvements** over the bak (proper images, better a11y, correct component split)

**Recommendation**: Move to `Archive/` per repo convention. The file has historical value (it shows a prior version of the marketing components) but should not stay in the source directory.

### 3.6 Verdict

| Question | Answer |
|----------|--------|
| **Is it imported?** | No — zero imports found |
| **Is it routed?** | No — Next.js only uses `page.tsx` files |
| **Is it dead?** | Yes — completely unreferenced |
| **Unique content?** | `CtaBand` and `DemoButton` exist here — BUT they live in `marketing-client.tsx`. `PublicPage`, `PublicHeader`, `SectionIntro`, `Kicker`, `CtaBand` exist here AND in `marketing.tsx`. `PublicFooter` and `ProofChip` exist here AND in `marketing.tsx`. |
| **Recover anything?** | No — all exports are covered by `marketing.tsx` or `marketing-client.tsx` |

**Fix**: Move `marketing.bak.tsx` to `Archive/marketing/marketing.bak.tsx` for historical reference.

---

## Finding 4: Verification State

### 4.1 Git Status

Branch: **`master`**, up to date with `origin/master`.

Working tree has uncommitted modifications but **none to the three files in question**. The changes are:
- `data/overrides/` — test/override data files (unrelated)
- `src/app/(agency)/inbox/page.tsx` — inbox page
- `src/components/inbox/TripCard.tsx` — trip card (modified from prior work)
- `frontend/vitest.config.ts` — test config
- `spine_api/persistence.py`, `tests/` — backend test changes

**None** of the three P0 findings involve modified files. They are existing-state issues.

### 4.2 Recent Commits (last 10)

```
0203f1b Add repo-local stash/reset recovery guardrails
ba11bc8 Update scenario handling coverage status for regional risk flow
8ec0630 Recover intake regional risk flow and runtime coverage
0cb3b61 Refresh agent-start session context after recovery handoff
193c281 Consolidate runtime, docs, recovery forensics, and workspace cleanup
533d39a Add comprehensive test coverage for various components
49db205 Add comprehensive tests for booking collection, tenant isolation, recovery agent, workspace invite flow, and multi-agent runtime scenarios
1afbe20 feat: Enhance booking readiness validation and add booking_data support
87eb233 chore(naming): add contract tests, handoff docs, and allowed/forbidden rule doc
7a0d487 feat: Refactor pipeline naming from NB codes to semantic identifiers
```

None directly relate to the three findings.

### 4.3 TypeScript Check

**Result**: `npx tsc --noEmit` — **passed with zero errors** (no output = clean).

### 4.4 Test Suite

**Result**: `npx vitest run` — **72 test files, 667 tests, all passed**.

```
 Test Files  72 passed (72)
      Tests  667 passed (667)
```

The 2 "errors" at the bottom are vitest worker-communication timeouts (infrastructure, not test failures). All 72 test files and 667 individual tests passed.

### 4.5 Baseline Confirmed

| Check | Result |
|-------|--------|
| TypeScript (`tsc --noEmit`) | ✅ Clean |
| Tests (`vitest run`) | ✅ 72 files, 667 passed |
| Git status | Clean for all 3 target files |
| No pre-existing breakage | Confirmed — all 3 issues are latent, not introduced by recent work |

---

## Summary: What to Change

| # | File | Action | Rationale |
|---|------|--------|-----------|
| 1 | `frontend/src/types/generated/spine_api.ts` | **Delete** | Stale copy missing 4 types. Zero runtime imports. |
| 2 | `scripts/generate_types.py` line 31, 59-60 | **Remove alias output** | Only write one canonical file. Fix the stale-alias problem at source. |
| 3 | `frontend/src/lib/design-system.ts` — `NAV_SECTIONS` | **Remove stale nav** | Duplicate with wrong routes. Zero consumers. Keep `PRODUCT_COPY` if desired. |
| 4 | `frontend/src/components/marketing/marketing.bak.tsx` | **Move to Archive/** | Dead file, no unique content, superseded by live components. |
