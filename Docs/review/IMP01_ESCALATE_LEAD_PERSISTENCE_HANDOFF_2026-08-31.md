# Handoff — IMP-01: ESCALATE Leads Persist (Lead-Inbox Promise Restored)

*Date: 2026-08-31 · Decision: `Docs/ADR_ESCALATE_LEAD_PERSISTENCE_2026-08-31.md` · Root cause: `Docs/exploration/DEMO01_LEAD_ROUTING_GAP_2026-08-31.md`*
*Checklist applied: IMPLEMENTATION_AGENT_REVIEW_HANDOFF_CHECKLIST.md*

## 1. Executive Summary

Implemented IMP-01 from first principles per the ADR: when the NB01 intake gate **ESCALATEs**, the pipeline now persists the inquiry as a **Trip with `status="incomplete"`** through the canonical save path, links it to the draft, and exposes the `trip_id` on the blocked run — so the workbench banner's promise ("incomplete leads appear in Lead Inbox") is now true and the first-run loop no longer dead-ends. Draft-scoped reprocesses are idempotent across all terminal branches (ESCALATE/DEGRADE/success), and — per review cycle 1 — **ESCALATE never overwrites an existing trip**: when a preserve target exists (auto-reassess-on-edit or a draft's linked trip), the save is skipped and the record stands. Verified live end-to-end (fresh tenant → blocked → lead in inbox) and by 82 backend + 250 frontend tests. Code-ready: **Yes**. Feature-ready: **Yes** (repair loop converges via DEGRADE/success paths). Launch-ready: **Yes for dev**, gated only on the pending visual confirmation of the banner line (environment-blocked, see §6).

## 2. Technical Changes

| File | Change |
|---|---|
| `spine_api/services/pipeline_execution_service.py` | ESCALATE branch: persists lead (new inquiries only), skips save when a preserve target exists (record stands), runs `update_meta` in its own guarded try; new `_resolve_draft_reprocess_target()` (draft→trip 1:1, dead-id-safe); DEGRADE + success branches use it (fixes latent reprocess-duplication bug); `_update_draft_for_terminal_state` no longer discards `trip_id` |
| `spine_api/draft_store.py` | `update_run_state(..., linked_trip_id=None)` records linkage into `Draft.linked_trip_ids` (dedup, cap 25); facade passthrough |
| `src/intake/validation.py` | INTAKE_MINIMUM comment now states the doctrine: gates gate packet completeness, never record existence |
| `frontend/src/lib/workbench-blocking-copy.ts` | `missingFields` from `packet.unknowns`; `formatWorkbenchMissingFields()` (labels, cap 3, "+N more") |
| `frontend/src/app/(agency)/workbench/PageClient.tsx` | Persistent blocked banner renders "Missing: Travel Dates, Trip Purpose" (same source as PacketTab — banner and tab can never disagree) |
| Tests | New: `tests/test_escalate_lead_persistence.py` (6), `tests/test_draft_store_linked_trip.py` (1); updated: `tests/test_spine_pipeline_unit.py` TestEarlyExit to the new contract, frontend copy tests |
| Docs | `Docs/ADR_ESCALATE_LEAD_PERSISTENCE_2026-08-31.md` (decision + refined never-overwrite rule) |

No schema changes; no new routes; no parallel read models.

## 3. Review Findings & Resolutions

- **Cycle 1 (reviewer agent, whole-tree scope per doctrine): FIX-FIRST.**
  - **P0** — ESCALATE save would have clobbered an existing trip during auto-reassess-on-edit (`PATCH /trips/{id}` + `auto_reprocess_on_edit` → pipeline with `target_trip_id` → empty early-exit packet wholesale-replaces the record). Reviewer bisected it live: 5 tests in `tests/test_trip_canonical_roundtrip.py` red with the change, green on HEAD. **Fixed:** save gated on "no preserve target"; existing trips are never written by ESCALATE. Roundtrip tests green again (82/82).
  - **P1** — old-contract test `test_early_exit_blocks_and_does_not_save_trip` left red. **Fixed:** rewritten to the new contract (persists for new inquiry; never saves with target).
  - **P2s** — misleading log on meta-update failure (separated try), dead linked-trip id resurrection (helper returns nothing on lookup miss), shared mutable test state, vacuous log assertion, frontend test hygiene. All fixed.
  - Verified good by reviewer: privacy guard still applies on the ESCALATE save path; strict-leakage/defense-in-depth paths still persist nothing; branch order and emit payloads per contract; frontend null-safety and PacketTab parity.
- **Cycle 2 (same reviewer, fix diff + independent re-verification): APPROVE-quality.** All cycle-1 findings confirmed RESOLVED (P0-1 clobber path closed and pinned by would-fail-on-revert tests at both unit and service layers; dead-id, meta-log, test-hygiene fixes verified). Reviewer independently re-ran: 29 escalate/draft-store/boundaries/spine-unit tests, roundtrip canary **53/53** (was 5 failed), frontend copy 6/6, ruff clean, plus a broader 194-test sweep. One NEW-P1 found and fixed in this pass: a second superseded-contract assertion in the integration suite (`tests/test_partial_intake_lifecycle.py` — `trip_id is None` on blocked runs) flipped to the ADR contract; **7/7 integration tests green against the live server**. Reviewer's own words: after this one-line change "the tree is APPROVE-quality on all cycle-1 and cycle-2 findings" (P0: 0).

## 4. Test Results (evidence)

- `ruff check` on all touched files: clean.
- Backend: escalate + draft-store + boundaries + spine-unit + trip-roundtrip files → **82 passed**; roundtrip canary alone **53/53** (cycle-1 P0 canary); integration lifecycle suite **7/7** against the live server (incl. the corrected blocked-run contract); reviewer's independent keyword sweep **194 passed / 1 stale assertion (fixed)**.
- Frontend: `workbench-blocking-copy.test.ts` 6/6; workbench+lib sweep **250 passed / 30 files** (11 vitest "unhandled errors" under machine load 74 — environment noise, all tests green; seen on unrelated runs too).
- Typecheck: `tsc --noEmit` clean.
- **Live E2E (API contract, twice — before and after review fixes):** fresh signup → `POST /run` with a note missing dates/purpose → run `BLOCKED`, `validation.status=ESCALATED` → run exposes `trip_id` (`trip_6459a42c915a`, `trip_d616f12b69f9`) → `GET /inbox` total 0→1, lead row present with flags `['details_unclear','incomplete']`.
- Note: backend tests ran while the dev server was live (known F-19 contention) — durations inflated (319s for 13 tests pre-fix), all green regardless.

## 5. Audit (11-dimension, condensed)

Code ✅ · Operational ✅ (blocked leads now visible + actionable in inbox; banner names missing fields) · UX ✅ (loop completes; repair surface reachable via trip) · Logical consistency ✅ (existence vs epistemics separated; never-overwrite invariant tested) · Commercial ✅ (no silent lead loss = no silent revenue loss) · Data integrity ✅ (clobber path closed with a regression canary; idempotent reprocess) · Quality/Reliability ✅ (all terminal branches covered incl. failure isolation) · Compliance ✅ (privacy guard verified on the new path; audit events unchanged) · Operational readiness 🟡 (frontend restart not needed—dev server hot-reloads; banner visual confirmation pending) · Critical path ✅ (unblocks IMP-05 repair UX; IMP-02/03 unaffected) · **Verdict: Merge Yes · Feature-ready Yes · Launch-ready Yes (dev) / visual-pending**.

## 6. Known Limitations & Follow-ups

1. **Banner visual confirmation pending** — the macOS multi-Space environment refused to surface the demo browser window (machine at load 74; the user's active Space occupied). Typecheck + unit tests cover the render logic; a 2-minute manual look at any blocked draft will confirm. Demo harness quirks documented in `Docs/exploration/DEMO08_HARNESS_LIMITATIONS_2026-08-31.md`.
2. Draft repair loop nuance: re-ESCALATE after a repair attempt no longer refreshes the trip's packet (by design — never overwrite). The trip updates once extraction reaches DEGRADE/success quality. If agents report "my edits don't show on blocked leads", that's this tradeoff — revisit with a merge-preserving save.
3. Register integration still pending Pranay's ratification (F-19…F-26 from `Docs/exploration/DEMO_FOLLOWUP_TASK_BRIEFS_2026-08-31.md`).
4. Next in dependency order: IMP-05 (repair-surface anchor+focus — now meaningful since trips exist for blocked drafts), then IMP-02/03 (extraction robustness) to shrink the ESCALATE population itself.

## 7. Explicit Verdicts

- **Code-ready: YES** (82+250 tests, lint, typecheck, live E2E ×2, 2 review cycles).
- **Feature-ready: YES** — the demo's P0 loop is closed end-to-end.
- **Launch-ready: YES (dev)**; production gate = the pending 2-minute visual banner check + register ratification.
