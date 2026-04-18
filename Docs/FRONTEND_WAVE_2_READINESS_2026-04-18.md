# Wave 2 — Workspace Layout: Readiness Checklist & Decisions
**Date**: 2026-04-18  
**Status**: ✅ Decisions locked, ready to implement  
**Parent docs**: `FRONTEND_IMPROVEMENT_PLAN_2026-04-16.md` · `FRONTEND_WAVE_1L_6H_NOTES_2026-04-18.md`

---

## Pre-implementation Review Verdict (Wave 1L + 6H)

- ✅ 79/79 tests passing
- ✅ Build clean (one routes.ts doc-comment parse error found and fixed: `*/` in block comment → `<stage>`)
- ✅ All 6 workspace stage routes compile and redirect correctly
- ✅ `getTripRoute()` is the only UI trip-link API across inbox, overview, reviews
- ✅ DecisionTab normalization: `STATE_ALIASES` + `normalizeDecisionState` + `?? fallback`
- ✅ Zero functional downgrade confirmed

---

## Wave 2 Policy Decisions (Locked)

The following were open questions. Answers are final and should not be re-litigated in Wave 2:

| Decision | Answer | Rationale |
|---|---|---|
| Right-rail AI panel | **Toggleable, collapsed by default** | Layout stability; iterative rollout; no locked assumptions about panel content |
| Role-based nav | **Flat nav for v1; enforce at route/data layer** | Auth/RBAC isn't real yet. Nav differentiation in v2 after role model is established |
| Data-fetch strategy | **Layout-level single fetch, fan-out to children via context** | Stage tabs should not each independently fetch the same trip |
| Compat redirect removal | **Only after per-stage parity + telemetry evidence** | Not a time trigger. Remove stage redirect when: (a) real panel exists AND (b) native-stage success rate is measurable |
| Workspace domain boundary | **Frozen**: `IN_WORKSPACE_STATES = {green, amber, red}` | Source of truth: `app/workspace/page.tsx`. State mapping owner: frontend. Backend field TBD Wave 2+. |

---

## 1 · Product Decisions (All Locked)

- [x] Right-rail AI panel policy: toggleable + collapsed by default
- [x] Role-based nav policy: flat v1, enforcement at route/data layer
- [x] Workspace domain boundary frozen: `IN_WORKSPACE_STATES`
- [x] Inbox = intake queue (state: blue), Workspace = active execution (green/amber/red)

---

## 2 · Routing Contract

- [x] `getTripRoute()` is the only UI trip-link API — confirmed no inline strings remain
- [x] Compat redirects stay until per-stage parity is real — do not remove early

**Redirect removal criteria (per stage):**

| Stage | Remove redirect when |
|---|---|
| intake | IntakePanel exists in workspace + handles `tripId` route param |
| packet | PacketPanel extracted + accepts trip data as props |
| decision | DecisionPanel extracted + accepts trip data as props |
| strategy | StrategyPanel extracted + accepts trip data as props |
| output | OutputPanel built (new) + renders traveller bundle |
| safety | SafetyPanel extracted + accepts trip data as props |

All removals gated on build green + regression tests.

**URL invariants (must hold for all Wave 2+ work):**
- Canonical URL shape: `/workspace/<tripId>/<stage>` — no change
- Query-param policy: none in canonical workspace routes (trip context from URL params + layout fetch)
- Deep-link behavior: direct URL to any stage must load the workspace layout with trip context before rendering the stage

---

## 3 · Layout Architecture for `app/workspace/[tripId]/layout.tsx`

**Responsibilities:**
1. Fetch trip record once via `useTrip(tripId)` — single source for all child pages
2. Render persistent trip header: `destination | stage badge | assigned agent`
3. Render stage tab navigation (links to `/workspace/[tripId]/<stage>`)
4. Provide `TripContext` to all children
5. Mount right-rail container (collapsed by default, toggle in header)
6. Own error boundary for trip-not-found and fetch errors

**State ownership:**
| State | Owner |
|---|---|
| Trip data | Layout fetch → `TripContext` |
| Current stage | URL params (active tab derived from `usePathname`) |
| Right-rail open/closed | Local layout state (`useState`) |
| Stage-level panel data | Per-stage page (from workbench store during Wave 1L → server state Wave 3+) |

**Loading/error semantics:**
- Full-page skeleton while trip header is loading (not panel-level — header is always needed)
- Panel-level skeletons for per-stage content (independent from trip header load)
- Retry scope: trip fetch → full layout retry; stage content → panel-level retry

---

## 4 · Data Contract

**Minimum trip fields required by all stage pages** (layout header + stage navigation):

| Field | Used by |
|---|---|
| `trip.id` | Stage tab hrefs, breadcrumb |
| `trip.destination` | Header title |
| `trip.state` | Stage badge color/label |
| `trip.type` | Header subtitle |
| `trip.age` | Header meta |
| `trip.assigned_to` | Header agent display (fallback: "Unassigned") |

All of these exist in the current Trip type from `lib/api-client.ts`. No backend changes needed for Wave 2 layout header.

**Missing-field behavior:**
- `assigned_to` absent → render "Unassigned" (already common in current data)
- `destination` absent → render trip ID (should not occur in practice)
- Trip not found (404) → full error state with back-to-Inbox link

**Stale data:**
- No auto-refresh for Wave 2. Manual refresh via header reload button (future)
- Stage tabs do not independently re-fetch Trip; they consume TripContext

---

## 5 · UX Guardrails

- [x] Zero-downgrade rule: every route must still land in a usable flow (enforced by compat redirects)
- [ ] Keyboard-accessible stage navigation: tab navigation + enter activation for stage tabs
- [ ] Mobile: stage tabs scroll horizontally; right-rail hidden by default on mobile, accessible via toggle
- [ ] Breadcrumbs: `Waypoint > Inbox > <destination>` — deterministic from route params + trip context

---

## 6 · Observability During Migration

Log the following events during Wave 2 rollout (can be `console.info` with a `[waypoint-migration]` prefix until proper analytics is wired):

| Event | Where to emit |
|---|---|
| `workspace:listing-hit` | `app/workspace/page.tsx` mount |
| `workspace:stage-redirect` | Each compat redirect page (currently server-side, can add to a client wrapper if needed) |
| `workspace:stage-native` | Each real stage page once compat redirect is removed |
| `decision:unknown-state` | `normalizeDecisionState()` when no alias matches |

The ratio of `stage-redirect` vs `stage-native` events is the signal for knowing when to remove compat redirects.

---

## 7 · Verification Plan (Wave 2 Pre-merge Gate)

**Route tests:**
- [ ] `getTripRoute(id)` returns correct URL
- [ ] `getTripRoute(id, 'packet')` returns correct URL
- [ ] Each stage redirect resolves to correct workbench tab

**Layout tests:**
- [ ] Stage tab switch preserves trip context (no re-fetch)
- [ ] Right-rail toggle opens/closes without layout shift
- [ ] Trip header renders with all required fields
- [ ] Trip-not-found state renders correctly

**Regression checks:**
- [ ] Inbox card click → workspace route → compat redirect → workbench (same tab as before)
- [ ] Overview activity click → same chain
- [ ] Owner review "View Details" → same chain

**Gate:** Full test suite (currently 79 tests) + production build must pass on fresh run.

---

## 8 · Wave 2 Exit Criteria

Wave 2 is complete **only if all of the following are true**:

- [ ] `app/workspace/[tripId]/layout.tsx` is live with trip header + stage tabs + rail toggle
- [ ] `contexts/TripContext.tsx` provides trip data to all children
- [ ] Right-rail is toggleable, collapsed by default, hidden on mobile
- [ ] No user-facing flow regressed from Wave 1L baseline
- [ ] All canonical trip links still route via `getTripRoute`
- [ ] Breadcrumbs are correct and keyboard-accessible
- [ ] Tests/build green on fresh run
- [ ] Per-stage redirect removal plan documented (which telemetry threshold triggers each removal)

---

## Files to Create in Wave 2

| File | Purpose |
|---|---|
| `app/workspace/[tripId]/layout.tsx` | Shared trip header, stage tabs, right-rail container, error boundary |
| `contexts/TripContext.tsx` | Trip data context + hook (`useTripContext()`) |

No other files change in Wave 2. Stage pages remain as compat redirects until Wave 3.

---

## Wave 3 Preview (After Wave 2 is merged)

Panel extraction in this order (least risky first):
1. `PacketTab` → `PacketPanel` (most self-contained, no mutation)
2. `DecisionTab` → `DecisionPanel`
3. `StrategyTab` → `StrategyPanel`
4. `SafetyTab` → `SafetyPanel`
5. `IntakeTab` adaptation (requires `useSpineRun` wiring — Wave 4 dependency)
6. `OutputPanel` (new, renders `result_traveler_bundle`)

---

*Decisions locked 2026-04-18. Do not modify without explicit approval.*
