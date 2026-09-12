# Modularization Leg — Findings & Tasks Inventory (2026-09-12)

> **Execution addendum (same day):** E1 leg commit `a95a823` (pushed).
> FND-0277..0283 registered. A3 fixed (T6 RED→GREEN, S2) → FND-0279 CLOSED.
> A1 consolidation landed (buildDraftPayload + isConflictError; T7 baseline
> first) → FND-0277 CLOSED. A6 fixed via `useTransientTimers` → FND-0282
> CLOSED. A4 → FND-0280 DEFERRED (NaN is the only honest in-contract
> encoding; sole consumer renders "Confidence unavailable"; type-level fix
> belongs to the spine types pipeline). A5 fixed in tree → FND-0281 CLOSED
> (commit blocked, see gate note). A7/FND-0283 stays open with measured
> trigger. **T2.3 REJECTED with rationale** (~25-prop interface would fail
> the decomposition doctrine's excessive-interfaces anti-pattern; PageClient
> at ~915 lines; reopen only on renewed churn evidence). **GATE NOTE:** the
> Mimosa pre-commit scan now hard-blocks commits on 15 repo-wide highs
> (pre-existing, matching the 2026-09-11 MITIGATED triage; none in this
> wave's change surface) — A5+A3+A6+A1 sit verified in the working tree
> (full FE suite 1,393/1,393) pending the owner's gate decision: fix the
> 15, re-baseline the scanner, or explicitly approve.

Session scope: council deliberation, consolidation commit `f8d8f73`, and the
workbench modularization leg (Tranches 0–2). The repo-wide standing backlog
(151 open / 11 deferred in `FINDINGS_STORE.jsonl`) is NOT duplicated here —
see `Docs/review/FINDINGS_LIVE.md` for that register.

Dispositions: IMPLEMENT (code, gated) · EXPLORE (question needing evidence) ·
DOCUMENT · DECIDE (owner) · DONE (closed this session).

## A. Code/behavior findings — workbench PageClient (behavior commits; must never be smuggled into move commits)

| # | Finding | Evidence | Disposition / priority |
|---|---|---|---|
| A1 | Triplicated draft-payload construction + 409-conflict handling (ensureDraftSaved / handleSaveDraft / autosave) | now `hooks/useWorkbenchDraftPersistence.ts` (moved verbatim from PageClient 335/448/560) | IMPLEMENT — consolidation into single `buildDraftPayload`, gated on characterization tests + review vs PER-0004 hazards (setTimeout(0) deferral, prevContentRef retry protocol). P2 |
| A2 | URL-vs-store config divergence: `store.stage/operating_mode/scenario_id` (written by `hydrateFromDraft`) vs URL params read at render — two sources of truth | `stores/workbench.ts:155-157`, `PageClient.tsx` render reads + the init-vs-arm contentKey split (`useWorkbenchDraftPersistence.ts` init effect uses store values; `buildContentKey` uses URL values) | IMPLEMENT/DECIDE — unify deliberately (behavior commit). P2 |
| A3 | Consequence of A2: autosave arms immediately after every draft load when `scenario_id` is null (JSON `null` vs `''` mismatch) → redundant PATCH ~5s after every load | same init/arm key comparison | IMPLEMENT (same fix as A2 or independent clamp). P3 |
| A4 | NaN confidences synthesized into DecisionOutput (`overall/data_quality/judgment/commercial = NaN`) — JSON-unsafe, poisons downstream comparisons/rendering | `hooks/useWorkbenchRunSync.ts` effect 1 (verbatim from PageClient ~514-519) | IMPLEMENT — clamp/skip + log per data-loss-prevention pattern. P2 |
| A5 | Dead code cluster: `MemoryArchitectPanel` dynamic import declared+never rendered; `OutputPanel` + `FeedbackPanel` dynamic imports declared+never rendered; `draftLoadingRef` written-never-read; `prevStageRef` effect writes-never-read; `discardDraft` imported-unused | `PageClient.tsx` lines 63-69 (dynamic), 51-55 (MemoryArchitect), draft-hydration region (draftLoadingRef), prevStageRef effect ~297 | IMPLEMENT — one justified cleanup commit after confirming no planned consumer. P3 |
| A6 | Uncleaned toast timers: `setTimeout(3000/8000)` fire-and-forget in handleProcessTrip + handleSaveDraft — no unmount cleanup (setState-after-unmount) | `PageClient.tsx` handleProcessTrip/handleSaveDraft regions | IMPLEMENT — cleanup refs on unmount. P3 |
| A7 | Whole-store subscription (`const store = useWorkbenchStore()`, no selector) — every store change re-renders the entire 930-line component; Header/ActionBar extraction alone will not reduce re-renders | `PageClient.tsx` store read; council seat PER-0006 analysis | IMPLEMENT — selector-based subscriptions as a separate perf slice (council deferred as "slice 6"). P3 |
| A8 | `isRunning` local state duplicates `isSpineRunning` semantics (submit guard vs run state) | handleProcessTrip region | DECIDE — likely not worth touching; note only. P4 |

## B. Modularization backlog — churn-selected, gated (doctrine: targets chosen by `git log`, never line count)

| # | Item | Status/trigger |
|---|---|---|
| B1 | T2.3 Header/ActionBar props-only split (PageClient → ~400-600 lines) | IMPLEMENT — optional final slice, behind same gates. PageClient is 930 lines now. |
| B2 | itinerary-checker/PageClient.tsx (3,196 lines, repo's largest, top recent churn 6 commits since Aug 1) | SCHEDULED — start only when visa/checker lane cools (edited Sep 9-10); reuse the workbench pattern + characterization-first protocol. |
| B3 | components/workspace/panels/IntakePanel.tsx (2,112, store-coupled) | QUEUED after B2 — same zustand/useSpineRun blast radius; serialize, never parallel with B2. |
| B4 | seasons (992) / audit (955) / overview (853) / insights (664) PageClients | QUEUED — churn-check each before deciding; several may fail the "change seam actually changes" test and stay as-is. |
| B5 | lib/api-client.ts (1,976 lines, 124 importers) | DO NOT MOVE — highest blast radius; split-by-domain with re-exports only if churn evidence ever justifies it. |

## C. Verification / architecture — EXPLORE

| # | Question | Next check |
|---|---|---|
| C1 | Panel content untested at page level (both page tests stub all dynamic imports; characterization pins mount-by-module only) | Add per-tab content contracts for PacketTab/SafetyTab at cheapest layer. P3 |
| C2 | SSE/run error paths unpinned (`useSpineRun` fully mocked; error/isLoading never exercised through PageClient) | Wire mocked-error journey test before touching run/error UI. P3 |
| C3 | No CI bundle/chunk assertion — the 11 `dynamic()` calls are the chunking strategy; moves verified only by review | EXPLORE: build-manifest diff check (CI artifact compare) post-`next build`. P3 |
| C4 | Does CI run `typecheck` separately or only inside `next build`? | Inspect CI workflow config. P4, 5-minute check. |
| C5 | One order-dependent FE suite flake — never identified to a file; N-08 timeout bump is mitigation, not diagnosis | EXPLORE: run suite with `--sequence.shuffle` locally to name the file. P4 |

## D. Documentation

| # | Item | Status |
|---|---|---|
| D1 | Council decision doc + status addendum | DONE (`Docs/architecture/WORKBENCH_MODULARIZATION_COUNCIL_DECISION_2026-09-12.md`) |
| D2 | Register A1–A7 via `scripts/findings.py open` (mint FND IDs) | PENDING owner go — IDs are permanent; batch-register when authorized |
| D3 | Refresh workbench section in `Docs/architecture/CODEBASE_FEATURES_FLOWS_LOOPS_MAP` (module split: 3 hooks + state module) | DOCUMENT — next map refresh, structure-only note |
| D4 | Clarify ownership of gate-generated `Docs/reviews/motto_review.md` edits (staged by tooling during attestation verify) | VERIFY — does `attest_motto_commit.py --verify --render` write this file? One-command check |
| D5 | `MEMORY.md` index over size limit (29.6KB > 24.4KB) — prune/condense index lines | HOUSEKEEPING |

## E. Owner decisions

| # | Decision | Context |
|---|---|---|
| E1 | Commit authorization for the staged modularization leg (7 files, pathspec-scoped) | Gates all green; `next build` deferred due to parallel-agent tree edits |
| E2 | A1 consolidation go/no-go | Requires A1 hazard review pass first |
| E3 | T2.3 (B1) split go/no-go | Optional; PageClient already 36% smaller |
| E4 | A2 unification direction (URL as single source vs store as single source) | Product-level call: deep-link semantics vs session persistence |
| E5 | Next pilot authorization (B2 itinerary-checker) | Timing gate: visa lane must be cool |

## F. Closed this session

- Gitignore: `data/experiments/**/prompts/` + `cache_*/` (1,083 regenerable run files excluded) — committed `f8d8f73`.
- Characterization gap for workbench deep-slice safety (T1–T5) — CLOSED by `page-characterization.test.tsx` (9 tests).
- Consolidation tranche commit + push through full hook/gate — DONE (`f8d8f73`).
- Council manifest, decision, dissent record — DONE (council doc).

## G. Standing backlog pointer

151 open + 11 deferred findings live in `FINDINGS_STORE.jsonl` /
`FINDINGS_LIVE.md` (aliases A/F/R/GF/…). Known high-signal open threads from
memory: FND-0268 margin-basis DECIDE, PA-35/36/37, TS-03 S2/S3, Wave A
(A2/A4/A6/A7), E-8 persisted-state wiring, checker exposure-scope decision.
Not restated here.
