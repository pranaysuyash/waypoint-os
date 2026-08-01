# DD-8: Documentation Truth Reconciliation — Deep-Dive

**Date**: 2026-08-01 · **Parent**: `Docs/LAUNCH_AUDIT_BASELINE_2026-08-01.md` (H10, Theme 3)
**Evidence tier**: Tier 2 (file-existence checks, git history, `gh` runs, cross-referenced with DD-7's executed test results).

---

## W1 — The 2026-07-29 "verified" review is falsified twice over

`Docs/travel_agency_process_issue_review_2026-07-29.md` declares all 8 turnaround priorities "Implemented & Verified … Tier 3 (Integration Test Verified)" with per-priority "PASSED" test citations.

- **3 of 8 cited test files do not exist**: `test_proposal_link_router.py` (P5), `test_ghost_concierge_router.py` (P7 — no `ghost_concierge` match anywhere in `tests/`), `test_agency_team_router.py` (P8).
- **The tests that DO exist fail today**: DD-7's executed run — `test_trust_scorecard_router.py` (P3) 2 failures, `test_team_workflows_router.py` (P8's nearest real file) 2 failures, `test_yield_arbitrage_router.py` (P6) 1 failure, `test_concierge_router.py` (P7) 2 failures, `test_messaging_router.py` (P4) 1 failure.
- So even its *verifiable* claims are currently false. **Rule going forward (process fix, not blame)**: a review may only cite a test as PASSED with a pasted command + timestamp; status tables must be regenerable. Add as a line to the review checklist doc.

## W2 — Same-day self-contradiction in the planning docs

`Docs/ACTIONABLE_POINTS_SUMMARY_2026-07-29.md` ("Active Execution Plan") frames the same 8 priorities as a **12-week future rollout** (Phase 1 weeks 1–4 … Phase 3 weeks 9–12). The review says done; the plan says not started. A new agent or operator cannot tell which is true — the code says: implemented-but-simulated and partially broken (DD-1, DD-5). Reconcile by rewriting the review's status table to three honest states: `real & verified`, `implemented-simulated (gated)`, `not started` — using DD-5's inventory.

## W3 — Motto v3/v4: the commit gate enforces a retired doctrine

- **Still v3**: `AGENTS.md:62`, `CLAUDE.md:63`, `frontend/AGENTS.md:62`, `frontend/CLAUDE.md:60`; the **installed** `.git/hooks/{pre-commit,commit-msg,prepare-commit-msg}` (zero v4 matches); `scripts/hooks/pre-commit` is internally inconsistent (header says v4, body enforces `motto_v3.md` at line 218); stale mirrors under `spine_api/Docs/context/agent-start/`.
- **Already v4**: workspace tooling (`attest_motto.py:36`, `install_git_precommit_agent_hook.py`), root context pack, `scripts/hooks/{commit-msg,prepare-commit-msg}`.
- Net: the commit gate checks attestation against a doctrine file the workspace has retired. **Fix**: re-run `python3 /Users/pranay/Projects/workspace_memory/scripts/install_git_precommit_agent_hook.py` + `attest_motto.py --repo "$PWD"` (per AGENTS.md's own gate section), fix `scripts/hooks/pre-commit:218`, update the four instruction files, delete stale mirrors. motto_v4 §0.17 (one canonical motto) is currently violated by the repo's own gate.

## W4 — Stale operational docs

- `TODO.md` generated 2026-04-30: 56 unchecked items (9 P0 + 33 P1 + others), 0 checked, predates the entire July program. It is the first doc a new contributor reads and it describes a different company.
- `CHANGELOG.md`: last entry 2026-04-29, only 3 headings total, and mislabeled as frontend-only. Three months of the highest-churn period unrecorded.
- Streamlit ghosts: **24** `Docs/*.md` files still reference Streamlit (baseline said 27 — corrected; the count shifted because this audit's own docs now mention it). DECISION_LOG.md:64 correctly records the retirement. Most recent offenders: `ACTIONABLE_POINTS_SUMMARY_2026-07-29.md` (cites "Streamlit scripts" as a live example).

## W5 — The truth is uncommitted (cross-links DD-2)

The repo's most important recent artifacts exist only locally: the applied-at-DB-head alembic migration (`0cd0399e2c3c`), all 16 Jul-29 ADRs, both Jul-29 planning docs, `Docs/INDEX.md` updates, `deploy.yml` (all staged); and `ci.yml` + the guard-disable sit in the unpushed `d13f38b` commit (master is 1 ahead of origin). Combined with W1–W4: **the durable record of what this product is, lives in a working tree, not in history.** One `rm -rf` / disk failure / careless `git reset --hard` loses the quarter. This is the highest-severity doc finding — ahead of any content issue.

## W6 — What's healthy (preserve)

`Docs/INDEX.md` exists, is curated, and links the Jul-28/29 program accurately. The ADR naming/dating convention is consistent. Doc-preservation rules in AGENTS.md are working (nothing deleted; archives kept). The audit trail itself (this engagement's 7 documents) slots into the existing convention.

## Reconciliation plan (commit-sized)

1. **Commit/push the truth** (operator git approval): migration + ADRs + Jul-29 docs + `d13f38b` + `deploy.yml`. One "sync the record" commit series.
2. **Rewrite the Jul-29 review status table** to the three-state honest version (W2), with a pointer to DD-5's simulation inventory and DD-7's failing-test list. Do not delete the original table — annotate (doc-preservation rule).
3. **Motto v4 cutover** (W3 fix list).
4. **TODO.md refresh**: mark discovery-open status explicitly, fold in this audit's blocker registers as the new P0, archive the 2026-04-30 version with a pointer.
5. **CHANGELOG catch-up**: one entry per DD + the July program, dated honestly.
6. **Streamlit scrub**: append a one-line "retired 2026-06-23, see DECISION_LOG" note to the ~5 most-referenced stale docs rather than editing 24 files.
7. **Cleanup of audit-created artifacts**: DD-3's probe agency/user (`idor-probe-0801@test.com`, agency `2838f049-…`) — additive test data; recommend deletion with operator approval or keep flagged `is_test`.

## "Anything else?" (motto §0.1.1)

- The deepest pattern across DD-1…DD-8: **claims drift from reality wherever nothing machine-checks the claim.** Tests fix it for code; for docs the equivalent is: status tables must cite runnable evidence (command + date), and the launch-readiness verdict should live in exactly one place (proposal: `Docs/LAUNCH_STATUS.md`, regenerated each audit pass, everything else links to it).
- This engagement's own baseline already needed two errata (H7 reframe, Streamlit count) — recorded as appends per §0.12.1. The errata mechanism works; keep using it.
- Not verified: full accuracy of the remaining ~570 Docs files (only launch-relevant ones were reconciled); a full corpus pass is out of scope for launch and should stay out — reconcile what operators/agents actually read.

## Status

W1–W6 verified; reconciliation plan proposed. **This completes DD-1 → DD-8.** Master synthesis follows in `LAUNCH_AUDIT_SYNTHESIS_2026-08-01.md`.
