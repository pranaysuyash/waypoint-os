# Waypoint OS — UI Cleanliness Council Review + FieldCanvas Cross-Project Learnings

**Date:** 2026-09-12
**Status:** Findings current as of this checkout (audited files last touched 12:34 today, `8ece02e`; no uncommitted drift on audited files).
**Method:** Council orchestrator — Lead: Navigation Designer (canonical persona PER-0295), supported by Workspace UX Architect (PER-1228) and a frontend structural lane. Runtime evidence gathered same-day from a logged-in owner session.
**Evidence base:** 13 fresh screenshots at `frontend/design-lab/app-shots/2026-09-12-council/` (1440×900; landing, overview, inbox, quotes, settings, trips-list, workbench-new-inquiry, knowledge, trip-workspace, trip-intake, trip-packet, trip-output, trip-timeline) + current-checkout source. All file:line refs below were read this session.
**Companion finding:** a parallel review of FieldCanvas (`/Users/pranay/Projects/fieldcanvas`, a different product/stack) produced a set of navigation/territory patterns that solved these exact failure classes there. Part B transfers them as patterns, not code (Waypoint = Next.js 14 app router; FieldCanvas = Vite/React 19).

**Headline:** The sidebar is NOT the problem. 13 items in 5 lifecycle-ordered sections (`src/lib/nav-modules.ts:99-139`) with the CTA correctly kept outside nav is disciplined and clean. The failures live one layer up: the shell contradicts itself about location, two live routes serve one action, one nav destination ships sample data, the trip workspace carries three vocabularies for one journey, and a global onboarding overlay occludes real content on every screen.

---

## Part A — Findings (prioritized, with fix targets)

### A1 (HIGH) — The shell lies about location on incomplete-trip pages
`src/components/layouts/Shell.tsx:174-177`: `isLeadReviewRoute` = any `/trips/*` path whose trip status is `new`/`incomplete`. It forces the breadcrumb to "Lead Inbox" (`Shell.tsx:144`) and highlights sidebar `/inbox` while suppressing the true match (`Shell.tsx:258-262`). Meanwhile the page's own trail says "Trips in Planning / …" (`trips/[tripId]/layout.tsx:121-122, 274-284`). Two location claims on one screen; the claim flips between the trips list (correct) and trip detail (wrong).
**Fix:** preserve origin once at arrival (the SidebarTripContext card already exists for exactly this), but once inside the trip workspace, breadcrumb + sidebar active state must agree with the page trail. Kill the remap.

### A2 (HIGH) — Two live routes for one action, with inverted breadcrumb honesty
Canonical CTA + ⌘N route to `/inquiries/new` (`Shell.tsx:160, 222`), but live inbound links still target `/workbench`: `overview/PageClient.tsx:64`, `trips/PageClient.tsx:208`, `trips/new/intake/page.tsx:4` (redirect → `/workbench`), `components/overview/EmptyStateOnboarding.tsx:43`, `lib/routes.ts:56`. Breadcrumb masking hides the internal name on the LEGACY route (`Shell.tsx:143`), while the canonical `/inquiries/new` matches no nav prefix and falls through to a bare "New" breadcrumb (`Shell.tsx:152`). The intake form is now maintained twice.
**Fix:** migrate the five `/workbench` inbound links to `/inquiries/new`, retire `/workbench` per the deprecation note already written at `nav-modules.ts:96-97`, fix the "New" fallthrough.

### A3 (HIGH) — A nav destination that ships SAMPLE DATA
`nav-modules.ts:105` (COMMAND "Quote Review") vs `:112` (PLANNING "Quotes"). Runtime: `/quotes` renders "Quotes & Commercial Proposals" badged SAMPLE DATA with an "ILLUSTRATIVE PRICING MODEL — NOT REAL QUOTES" banner. A first-class nav item whose payload is placeholders trains users to distrust the whole PLANNING section — or worse, to quote from illustrative pricing.
**Fix:** one mental slot for "quotes" — either rename/rescope `/quotes` (e.g., a clearly-quarantined Proposal Studio) or fold it behind Quote Review until real data exists.

### A4 (HIGH) — Three vocabularies for one journey + two orphan routes with wrong-default deep links
The trip workspace carries: a 5-step stepper ("Intake → Details → Options → Quote Review → Output", `layout.tsx:353-367`, non-clickable), 8 clickable stage tabs with different names ("Trip Details", "Quote Assessment" — `layout.tsx:37-46`), and 10 URL segments (`packet`, `strategy`, `decision`, `safety`…). `followups` and `suitability` are live route pages (`trips/[tripId]/followups`, `/suitability`) absent from every tab list, and `getActiveStage` (`layout.tsx:61-65`) silently defaults unknown segments to "intake" — a deep link to `/trips/x/followups` renders followups content with the Intake tab marked active. Panel content has already migrated (SuitabilityCard/SuitabilitySignal inside Decision/Timeline panels) but the routes were left live with no door.
**Fix:** one name-set across stepper/tabs/URLs; give `followups`/`suitability` a door (tab or parent-tab state) or fold their panels in and remove the routes. Never default an unknown segment to a wrong active tab — render an honest not-found like the shell does.

### A5 (HIGH, runtime-verified) — WelcomeModal occludes content on every screen
`src/components/onboarding/WelcomeModal.tsx:127` — `fixed bottom-4 right-4 z-40 w-[min(92vw,28rem)]`, mounted globally in `AuthProvider.tsx:193`. Its own copy claims "These shortcuts won't block the rest of the app"; screenshots falsify this on 7+ surfaces (settings form fields, quotes table STATUS/ACTIONS columns, trip-intake next-move panel all truncated behind it). Dismiss state is per-browser localStorage (`WelcomeModal.tsx:29-48`).
**Fix:** relocate out of the fixed global layer — a first-run takeover scoped to the empty Lead Inbox, or coach-marks anchored to their targets. A fixed overlay must obey panel rules: own a region or be transient with dismissal-on-interaction.

### A6 (MEDIUM) — Trip header: four encodings of one stage state
`trips/[tripId]/layout.tsx:312-426` stacks: status badge + LifecycleChip row, amber lock banner, the "STAGE →" progress row, and the tab strip where 4 locked tabs repeat the identical subtitle "Complete customer details" — that string renders 5× in one header (~150px of chrome before work starts).
**Fix:** keep the tab strip (lock glyph + single tooltip); delete the parallel STAGE row; merge the lock banner into one conditional status line; one shared lock hint instead of 4 copies. Recovers ~60-80px on every trip tab.

### A7 (MEDIUM) — Sidebar current-trip card duplicates the page header in-trip
`Shell.tsx:86-134, 326`: inside a trip, the card shows title/status/next-action/"Open Trip Details" — identical content to the page header ~1,000px away — and its height clips nav items ("Audit" half-cut in trip screenshots).
**Fix:** suppress on the active trip's own routes (it earns its pixels only when *away* from the trip), or convert to a compact trip-switcher popover.

### A8 (MEDIUM) — Three breadcrumb/back devices stacked
Top command-bar breadcrumb (`Shell.tsx:365-392`) + in-page trail (`layout.tsx`) + per-page "Back to Overview" links (trips-list, quotes, knowledge, inbox). Three devices for one relationship.
**Fix:** one doctrine — keep the in-page back link for task flow; demote the command bar to product + page label; drop per-page Back-to-Overview where the sidebar already marks the section.

### A9 (MEDIUM) — Mobile: bottom bar drops home and most modules; trip context vanishes
`Shell.tsx:399-432`: bottom bar = Inbox/Trips/New/Docs/Settings — no Overview (the product home), no Quote Review, no "More" path to the other 8 modules except a stacked horizontally-scrolling sidebar (`Shell.tsx:245-246`). `SidebarTripContext` is `hidden md:block` (`Shell.tsx:95`).
**Fix:** Overview in the bottom bar, a "More" sheet for the long tail, trip context surfaced on mobile.

### A10 (LOW) — Hygiene
- Internal jargon leaking to users: "Persona Council" (workbench tab), "Memory & Retention" / "Guard" / "AI Agent" (settings tabs, 11 tabs overflowing at 1440px), "Ask Agency Brain" (knowledge).
- `src/app/v2`–`v5` prototype route folders ship at the app root, URL-reachable, zero inbound links. Auth/visibility unverified — check middleware.
- `/knowledge-base` is a pure redirect alias to `/knowledge` (`knowledge-base/page.tsx`), zero inbound links — benign; confirm and keep or remove.
- `/seasons` (sidebar ADMIN) vs the "Seasonal" settings tab — likely duplicate surface; content diff needed.
- Lock-gating UX: 4 toast triggers per header (`layout.tsx:378-406`) teach users tabs are unreliable; a single disabled-state hint is calmer.

---

## Part B — FieldCanvas patterns that solve these failure classes (adopt as patterns)

FieldCanvas (`/Users/pranay/Projects/fieldcanvas`, Vite/React 19 — patterns and governance, not copyable code) independently solved every failure class above. Verified there this session:

### B1 — One route grammar + a manifest that forbids a second authority (kills A2)
FieldCanvas: `src/app/shell/routes.ts:14-32` — one path grammar for all project surfaces; `routeManifest.ts:7-16` — an `APP_ROUTE_PREFIXES` whitelist shared with the dev server, with a comment declaring the redirects file "a checked text projection of this vocabulary, not a second editable authority"; canonical paths are projected in place via `replaceState`.
**Waypoint application:** after retiring `/workbench`, encode the rule — every user-facing action has exactly one route; aliases are permanent redirects, never parallel live surfaces. The deprecation protocol (`@deprecated` → warn → one cycle → delete) then has a mechanical home.

### B2 — Honest not-found instead of a silent wrong default (kills half of A4)
FieldCanvas: `src/app/shell/NotFound.tsx:11-35` — a real 404 with a recovery action, wired via the catch-all; deep links to unknown segments never render someone else's page.
**Waypoint application:** replace `getActiveStage`'s silent "intake" default (`trips/[tripId]/layout.tsx:61-65`) with an honest unknown-stage state (or a redirect to intake that says so).

### B3 — A vocabulary constitution + an enforced test (kills A10 jargon and A4 naming drift)
FieldCanvas: `docs/CONCEPT_VOCABULARY.md:34-46` fixes which nouns are user-facing; `src/app/shell/projectHomeNoviceCopy.ts:1-12` + `noviceVocabulary.test.ts` fail the build when novice-visible strings leak internal terms or off-list nouns. Doc corrections are made by adding a dated correction and marking the old text superseded-but-kept (see `FIELDCANVAS_STUDIO_DESIGN_SYSTEM.md:30-35`) — never silent rewrites, never doc/code drift.
**Waypoint application:** one canonical name per stage/tab/URL (A4); a static test that fails on "Persona Council", "Guard", "Memory & Retention", "Agency Brain", ADR IDs, and any nav label that doesn't come from `NAV_SECTIONS` or the tab model.

### B4 — Single canonical label source, projected everywhere (supports A4)
FieldCanvas: `workflowNavigation.ts:14-55` declares itself "the one canonical human label per workflow mode" and the command palette maps over it; nav entries are projected from the analysis-surface registry with freshness and honest `disabledReason` (`CommandPalette.tsx:285-358`) — gated capabilities render disabled-with-reason instead of vanishing.
**Waypoint application:** Waypoint already has the right machinery in `nav-modules.ts` rollout gates — extend the same discipline to the trip tabs: derive stepper, tabs, and breadcrumbs from ONE stage model (id, label, gate) so three vocabularies cannot drift apart.

### B5 — Assistance surfaces that are gated, capped, and decayed (kills A5)
FieldCanvas: `src/app/ui/assistance/FirstRunCoach.tsx:41-58` (first-run-only), `:156-160` (skip persists), `src/app/studio/firstRunCoach.ts:178-190` (≤3 steps, returning sessions auto-skip), `helpExposure.ts` (progressive verbosity decay shared by all assistance surfaces), `FailedGestureHint.tsx` (suppressed after 2 persisted dismissals). Non-modal, never a fixed global overlay.
**Waypoint application:** rebuild the WelcomeModal as scoped coach-marks or an empty-state takeover on the Lead Inbox; route all dismiss/cadence state through one exposure policy so a future overlay can't regrow.

### B6 — One encoding per state, enforced in code (kills A6 and supports A8)
FieldCanvas encodes the anti-duplication rule in the components themselves: `CanvasHUD.tsx:15-19` deliberately excludes the `view` group ("would duplicate a stable affordance"); `ContextActionBar.tsx:63-67` excludes `panel`/`view` for the same reason. Where a second encoding exists it must justify itself (control+status pairs where effective ≠ selected).
**Waypoint application:** the trip header is the case study — one stage encoding (the tabs), one lock hint, one status line. Anything that re-states stage state needs a justification comment like FieldCanvas's, or it gets deleted.

### B7 — Orphan-route door discipline (completes A4/A10)
FieldCanvas: every route id resolves to a live surface (`AppShell.tsx:53-63`), and deliberate unlinked routes get their rationale recorded in the route map (the N-02 pattern) so future audits don't re-litigate them.
**Waypoint application:** for `/suitability`, `/followups`, `/v2`–`/v5`, `/knowledge-base`, `/seasons`-vs-settings: each gets a door, a recorded deliberate-unlinked rationale, or deletion. No route-level page without a door.

### B8 — Reference screenshots as review evidence (method, not code)
This review's findings are screenshot-backed (`frontend/design-lab/app-shots/2026-09-12-council/`, captured via `design-lab/capture-app-screens.py` — note its trip-probe list misses plain `/inbox`, which is where trips actually live; the probe should add it). FieldCanvas's doctrine: rendered screenshots are the verification standard for any UI claim; geometry-derived claims get confirmed with before/after captures. Adopt the same bar here — each A-item fix above should land with a before/after pair in `design-lab/app-shots/`.

---

## Part C — Suggested order

1. **A5 WelcomeModal** (worst runtime offender, first thing every new owner sees; independent of everything else).
2. **A1 location lie** (trust in the shell's location claim underpins every other cue).
3. **A2 route convergence** (mechanical: 5 inbound links + breadcrumb fallthrough; do before B1's rule is encoded).
4. **A4 stage-model unification** (one stage model → labels, tabs, stepper, breadcrumbs; resolves orphan routes and the wrong-default in the same stroke; biggest lift, biggest payoff).
5. **A3 Quotes decision** (product call: quarantine/rescope or fold behind Quote Review).
6. **A6/A7/A8 header + card + breadcrumb dedup** (one pass over the trip header region).
7. **A9 mobile** and **A10 hygiene** (batch: naming test, v2–v5 disposition, settings tabs, seasons diff).

Parts of A6/A7 interact with A1 (the trip-context card is the proposed home for origin preservation) — do A1 and A6/A7 in one design pass.

## Explicitly settled (do not relitigate)

- The primary sidebar model (5 lifecycle sections, CTA outside nav, rollout-gated enablement) is clean and correct. The problem was never "everything stuffed into one sidebar."
- Rollout-gate machinery in `nav-modules.ts` is the right pattern — keep and extend it (B4).
- Deep-linkable trip stages and honest locked-tab gating are right; they need the naming/default fixes from A4, not removal.

## Limitations

- Runtime screenshots are same-day at one viewport (1440×900) and one role (owner); mobile findings (A9) are code-read plus layout reasoning, not device captures.
- `/v2`–`/v5` auth exposure and the `/seasons` content diff were not verified.
- The exact rendered breadcrumb on `/inquiries/new` ("New" fallthrough) is derived from `Shell.tsx:152`, not captured.
- FieldCanvas references were verified on FieldCanvas's current checkout this session; its line numbers will drift — treat them as pointers, not contracts.
