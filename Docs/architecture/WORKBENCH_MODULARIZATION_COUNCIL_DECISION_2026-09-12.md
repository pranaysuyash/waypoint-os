# Workbench Modularization — Council Decision (2026-09-12)

> **Status addendum (2026-09-12, same day):** Tranches 0–2 EXECUTED.
> T0.1 landed (vitest.setup N-08 in f8d8f73). T0.2: 9 characterization tests
> green on pre-refactor HEAD (`__tests__/page-characterization.test.tsx`).
> T1.1 `workbench-state.ts`, T1.2 `useHydrateStoreFromTrip`, T2.1
> `useWorkbenchRunSync`, T2.2 `useWorkbenchDraftPersistence` (triplication
> preserved; consolidation deferred) — all pure moves, gates green per slice.
> PageClient.tsx: 1,463 → 930 lines (T2.3 Header/ActionBar split still open). Full FE suite at tranche end:
> 185 files / 1,391 tests, zero regressions. `next build` deferred until the
> parallel agent's in-flight edits land (tree ambiguity). Consolidation commit
> (single buildDraftPayload) remains gated per §Execution plan T2.2.

Council orchestrated via `$council-orchestrator` over the canonical persona repo
(`/Users/pranay/Desktop/Understanding_Personas_sept6`, resolver confidence: high).
Task: refactor very large files to modular structure without losing
features/functionality, keeping upgrades, no regressions, doctrine- and
first-principles-aligned. Pilot target named by the owner: the workbench route
(36 source files / 9,762 lines; `PageClient.tsx` 1,463 lines).

## Council Manifest

**Lead:** PER-0001 Refactor Decision Architect — owns "what should change, in
what order, why, with what evidence."

**Supporting seats (all read-only analysis, parallel):**

| Seat | Persona | Mission |
|---|---|---|
| Decomposition | PER-0006 Decomposition Architect | Responsibility map, boundary design, migration slices |
| Preservation | PER-0004 Semantic Preservation Reviewer | Semantic contract inventory, preservation ruleset, hazards |
| Blast radius | PER-0013 Blast Radius Analyst | Import fan-out, parallel-agent collision, rollback units |
| Verification | PER-0052 Test Architecture Engineer | Coverage map, characterization baseline, per-commit gates |
| Skeptic | PER-0287 Architecture Critic | Falsify: do-nothing case, wrong-target case, end-state failure modes |

**Skills activated:** `react-best-practices` (repo), `react-effect-discipline`
(`~/Projects/skills/`), `nextjs-best-practices`, `request-refactor-plan`
(tiny-commit method), `verification-before-completion` (`~/Projects/skills/`).

**Rejected candidates:** PER-0002 Refactoring Strategist (overlap: boundary +
sequencing covered), PER-0011 Regression Hunter (overlap: PER-0004 + PER-0052),
PER-0276 Scope & Bloat Critic (overlap: PER-0287), PER-0442 Travel OS Architect
(product lens covered by repo doctrine read by all seats + Lead framing).

## Verified facts (evidence, this session)

1. `frontend/src/app/(agency)/workbench/` = 36 source `.tsx` files + 18 test
   files; `PageClient.tsx` = 1,463 lines; `WorkbenchContent()` is ONE component
   spanning ~lines 234–1423.
2. The route is **not** purely route-local — external consumers exist:
   - `(agency)/inquiries/new/page.tsx:2` imports `PageClient` from
     `'../../workbench/PageClient'` (cross-route reuse).
   - `(agency)/trips/[tripId]/ops/PageClient.tsx:7` and
     `(agency)/documents/PageClient.tsx:6` import workbench `OpsPanel`
     (plus 2 test mocks).
3. `@/stores/workbench` (zustand) has **39 importers** (21 outside the route) —
   behavior coupling spans far beyond import coupling.
4. `SpineStage`/`OperatingMode` canonical types already exist at
   `frontend/src/types/spine.ts:96-98`; PageClient re-validates locally.
5. Churn: `workbench/PageClient.tsx` is the most-churned FE page file
   (54 commits all-time, 6 since Aug 1, last touched Sep 6 — currently in a
   quiet window). `itinerary-checker/PageClient.tsx` (3,196 lines, repo's
   largest) was edited Sep 9–10 by the active visa/checker lane. `api-client.ts`
   has 124 importers. `route-map.ts` is the hottest infra file and is dirty.
6. Existing page tests stub all dynamic imports and mock save-state static —
   panel mounting, autosave debounce/retry/conflict, URL-write mechanisms, and
   SSE error paths are **unpinned**.
7. Dirty shared tree: ~60 uncommitted entries; FE-relevant: `vitest.setup.tsx`
   (N-08 flake mitigation, test-infra only), `lib/route-map.ts`,
   deleted `components/workspace/panels/YieldArbitragePanel.tsx` (correct
   supersession — workbench copy is canonical; do not restore).

## Key findings from seats

- **Decomposition (PER-0006):** WorkbenchContent has ~14 responsibility
  clusters; the real "changes-together" smell is draft persistence logic
  triplicated (three payload builders, three 409-conflict handlers:
  `PageClient.tsx:621-633, 729-773, 856-901`). Proposed: pure module
  `workbench-state.ts` (~130), `WorkbenchHeader.tsx` (~180),
  `WorkbenchActionBar.tsx` (~230), hooks `useHydrateStoreFromTrip`,
  `useWorkbenchRunSync`, `useWorkbenchDraftPersistence`; PageClient lands ~400
  lines as composition root. Explicit do-NOT-extract list: URL-sync effects,
  `completedTripId` (server-derived), the localStorage `useDraftAutosave`
  (different concern despite name), no panel moves.
- **Preservation (PER-0004):** Three distinct URL-write mechanisms are each
  load-bearing (deliberate `setTimeout(0)` + raw `history.replaceState` at
  650–663; `router.replace` elsewhere; mount-only entry redirect at 337–351).
  Eight top hazards incl. the `.then(m => m.MemoryArchitectPanel)` named-import
  idiom (55) — which is also a **dead** import — effect-order coupling
  (537–553 vs 560–601), the auto-save `prevContentRef` retry protocol, and the
  bound `searchParams.get` (238). Verdict: approve with conditions; pure
  extractions now, deeper slices gated on characterization tests.
- **Blast radius (PER-0013):** Workbench is the LOWEST-risk pilot (clean dir,
  3 external refs, quiet churn window). Rank order: workbench <
  itinerary-checker < IntakePanel < api-client (124 importers — never move).
  `OpsPanel` stays in place. Do-not-touch-concurrently list recorded.
- **Test architecture (PER-0052):** 5 characterization tests to write BEFORE
  deeper slices (T1 tab→panel-mount, T2 invalid-tab fallback, T3 autosave happy
  path with fake timers, T4 409→conflict + error branches + retryability,
  T5 unmount timer cleanup). Gate: route dir suite + whole-project typecheck
  per move commit (~≤90s); full suite + `next build` at tranche end. Land the
  uncommitted N-08 `vitest.setup.tsx` change as commit 0.
- **Skeptic (PER-0287):** Attempted falsification of "the structure costs
  nothing" FAILED — workbench/PageClient is the top historical FE hotspot, so
  do-nothing abandons real value. But the plan's load-bearing property is
  **sequencing discipline under concurrent agents**, not the decomposition map:
  a rebase against moved paths produces semantic drift no pre-move test run can
  catch. Recommended surgical scope + freeze window; endorses workbench pilot
  on the quiet-window logic.

## Council Decision

### Recommendation

**Proceed — but as a preconditioned, three-tranche, moves-first surgical
modularization of the workbench route, not a big-bang restructure.** The same
pattern then becomes the repo doctrine for the other large files
(itinerary-checker/PageClient 3,196; IntakePanel 2,112; several 650–1,000-line
PageClients), each scheduled by change-hotspot churn, never by line count alone.

**Doctrine (generalizable, first-principles):**
1. Modularization pays only where it improves a *change seam that actually
   changes* (churn evidence required; `git log` is the selector, not `wc -l`).
2. Pure moves first, consolidations later, behavior changes never mixed in.
3. Characterization coverage before structure surgery: you may not move code
   whose observable contract nothing pins.
4. One directory/topic per commit; every commit is a revert unit; moves-only
   commits contain byte-identical bodies (only import/export lines change).
5. Re-export shims only where an export has consumers that would break; prefer
   keeping the composition root in place over moving it.
6. Composition root stays a composition root: PageClient.tsx remains the
   file that wires dynamic imports, URL contract, and store — it shrinks, it
   does not move.

### Execution plan (task packages)

**Tranche 0 — preconditions (no structure change):**
- T0.1: Land the in-flight `vitest.setup.tsx` (N-08) change as its own commit
  (owner gate: it is another agent's uncommitted work — coordinate).
- T0.2: Write characterization tests T1–T5 (per PER-0052 spec above); all
  green on pre-refactor HEAD. Register `extractCompletedTripIdFromDraft` unit
  tests already exist (page.test.tsx:377–395) — keep green via re-export.
- T0.3: Freeze/announce: record the refactor window in shared memory
  (`MEMORY.md`) and re-check `git status --porcelain frontend/src` before
  every commit. Stop condition: new dirty files appear inside `workbench/`
  from another agent, or `route-map.ts`/`vitest.setup.tsx` change mid-flight.

**Tranche 1 — pure moves (zero behavior risk, one commit each):**
- T1.1: Extract `workbench-state.ts` (route-local): `safeParseJson`,
  `workspaceTabs`, `toSpineStage`/`toOperatingMode`/`toWorkspaceTabId` + Sets,
  `extractCompletedTripIdFromDraft`, `getPipelineStageForWorkbench`, review
  control classes. PageClient re-exports `extractCompletedTripIdFromDraft`
  (page.test.tsx:6 keeps working; `inquiries/new` unaffected since PageClient
  does not move).
- T1.2: Move `useHydrateStoreFromTrip` → `frontend/src/hooks/` verbatim.
- Gate per commit: workbench dir vitest suite + whole-project `tsc --noEmit`.

**Tranche 2 — gated moves (only after T1–T5 green):**
- T2.1: `useWorkbenchRunSync.ts` — move effects 473–601 into one hook called
  at the same position (preserves effect ordering contract), deps arrays
  verbatim, `handleTabChange` passed in.
- T2.2: `useWorkbenchDraftPersistence.ts` — FIRST a pure move of the three
  draft functions into one hook file (triplication preserved). Only after
  review against PER-0004's hazard list may a separate consolidation commit
  introduce a single `buildDraftPayload` — never in the same commit as the move.
- T2.3 (optional, last): `WorkbenchHeader.tsx` / `WorkbenchActionBar.tsx`
  props-only presentational split. NOT in scope: store-selector re-render
  optimization (separate future slice), removing the dead
  `MemoryArchitectPanel` dynamic import, dead refs (`draftLoadingRef`,
  `prevStageRef`), unused `discardDraft` import, NaN-confidence synthesis
  (514–519), uncleaned toast timers — all are **behavior commits**, to be
  individually proposed and registered as findings, not smuggled into moves.

**Exclusions (this round):** `itinerary-checker/PageClient.tsx` (active
parallel lane, edited this week), `IntakePanel.tsx` (store-coupled blast
radius), `lib/api-client.ts` (124 importers), `OpsPanel.tsx` (2 external
route consumers), `route-map.ts` (hottest infra file, dirty).

### Why

- Workbench/PageClient is the highest-churn FE page file with a real,
  evidenced cost concentration (triplicated draft logic; whole-store
  subscription; 1,190-line component) — doing nothing abandons value
  (skeptic's falsification attempt failed).
- It is simultaneously the lowest-risk first target: quiet window, 3 external
  references, self-contained test dir, and an existing in-route precedent
  (YieldArbitragePanel already moved here with its contract test).
- The dominant failure mode is process, not technique: concurrent agents.
  Preconditions T0.1–T0.3 attack exactly that.

### Important trade-offs

- Shims: rejected where pointless (PageClient never moves, so no shim for
  `inquiries/new` is needed); kept where they prevent breakage (test-consumed
  export re-exported from PageClient).
- Bundle safety: the 11 `dynamic()` calls are the chunking strategy; moves
  preserve specifier strings character-for-character. No bundle-manifest
  assertion gate exists in CI (known gap, listed below).
- Full suite cost: ~17s clean / ~66s contended — full suite only at tranche
  ends, dir suite + typecheck per commit.

### Material dissent (preserved)

PER-0287 would go further than the council consensus in two directions:
(a) start only after an explicit multi-agent freeze window agreed by all
active agents (council accepted this as T0.3 but with memory-announcement +
per-commit re-check as the lighter mechanism); (b) skip the Header/ActionBar
split entirely (council keeps it as optional T2.3 behind the characterization
gate). PER-0004 would gate even slice T2.1 on a written ref/timer/effect
closure map reviewed before moving — adopted: T2 commits must include that
mapping in their commit message.

### Unknowns / what would change the recommendation

- Whether `next build` prerenders the workbench route (Gate/Suspense
  build-enforcement unverified — medium confidence).
- Whether CI runs typecheck separately or only inside `next build`.
- Whether another agent lands FE changes against workbench mid-tranche
  (mitigated by stop conditions, not eliminated).
- No CI bundle-graph assertion exists, so chunk-boundary changes are caught
  only by review, not gates.

### Next action / owner / falsifier

- **Owner decision required (single gate):** authorize Tranche 0 start —
  specifically committing another agent's `vitest.setup.tsx` change and
  declaring the freeze window. Everything after Tranche 0 is mechanical and
  gated by tests.
- **Falsifier:** if T1–T5 characterization tests cannot be made green on
  current HEAD (i.e., behavior is already ambiguous/broken), the plan halts —
  that would mean the route has pre-existing uncontracted behavior and the
  first wave becomes defect-fixing, not refactoring.
- Register the behavior-commit candidates (triplicated draft payload, URL-vs-
  store stage/mode divergence, dead import/refs, NaN confidences, uncleaned
  timers) via `scripts/findings.py` as separate remediation findings.

### What remains unverified

Full frontend suite was not run this session (mid-flight parallel edits;
baseline protocol defined instead). Wall-time of the dir-suite gate unmeasured.
The 18 workbench test files were inventoried via full reads of the two page
tests + skims of the rest.

---

*Evidence tier: runtime/source (git log, grep, full file reads) > tests
(inventory only) > docs. Seat reports archived in session; this document is
the canonical record.*
