# A1-1 Live Worktree Classification Addendum — 2026-09-03

**Status:** current live-snapshot classification complete; product/release acceptance remains separate
**Supersedes:** only the *live snapshot* section of `A1_1_WORKTREE_CLASSIFICATION_CLOSURE_2026-09-01.md`; the 2026-09-01 historical commit ledger is preserved
**Scope:** current checkout path/state inventory after the “do all” pass
**Provenance:** `git status --porcelain=v1 -z -uall`, validator scaffold, focused tests, backend canonical runner, frontend gates
**Freshness trigger:** any path/state change, ownership handoff, staging, commit, reset, stash, cleanup, or provider/runtime mutation

## Verdict

The current worktree contains **388 source/concurrent paths** (389 porcelain
rows including this untracked ledger) and is fully covered by
the machine-checkable ledger at
`assets/a1_1_live_worktree_2026-09-03_classification.csv`. Every path is
conservatively marked `unknown_preserved_concurrent` and
`preserve_pending_semantic_classification`; this proves custody and coverage,
not correctness, authorship, readiness, or release approval.

No path was deleted, reset, restored, stashed, cleaned, staged, committed, or
pushed during this pass. `.mimosa/` and `frontend/.mimosa/` were added to
`.gitignore` while their on-disk contents were preserved.

## Evidence captured

| Check | Result | Tier/sensitivity | Boundary |
|---|---|---|---|
| Worktree ledger validator | 324 paths classified | Tier 2 / S1 | Coverage only |
| Risk-weighted backend suites | 121 passed | Tier 2 / S1 | Local contract/security behavior |
| Canonical backend runner | 3,573 passed, 44 skipped, 3 failed before fixes | Tier 2 / S1 | One ordering residual remains documented below |
| Route/OpenAPI parity | 340 routes / 310 paths, 2 passed | Tier 2 / S1 | Snapshot contract only |
| Frontend typecheck | Passed | Tier 2 / S1 | Compile-time types |
| Frontend lint | 0 errors, 13 warnings | Tier 2 / S1 | Warnings remain in concurrent files |
| Frontend Vitest | 171 files / 1,295 tests passed | Tier 2 / S1 | Component/unit behavior |
| Frontend production build | Passed after directive + PDF worker fixes | Tier 2 / S1 | No deployed/browser/provider proof |
| `git diff --check` | Pre-existing whitespace findings remain | Tier 1 | Concurrent files were not rewritten |

### 2026-09-04 execution refresh

| Check | Current result | Tier/sensitivity | Boundary |
|---|---|---|---|
| Worktree ledger validator | **388 paths classified**; 389 porcelain rows including ledger | Tier 2 / S1 | Custody and coverage only; semantic ownership remains open |
| Canonical backend runner | **3,653 passed, 44 skipped, 0 failed** in 111.55s | Tier 2 / S1–S2 | Local contract only; 8 known Python 3.13 fork deprecation warnings; no hosted/provider proof |
| Route/OpenAPI parity | **341 routes / 311 OpenAPI paths** | Tier 2 / S1 | Snapshot and parity tests only |
| Focused S-04/F-01 retry | **19 passed** (`test_sandbox_provider_adapters.py`, `test_p1_findings_hardening.py`) | Tier 2 / S1–S2 | Provider delivery and durable multi-writer proof remain external/open |
| Focused S-05 tenant retry | **2 passed** (`test_draft_promote_cross_tenant.py`) | Tier 2 / S2 | Hosted authorization/audit-sink proof remains external/open |
| Findings lifecycle | **182 rows: 110 open, 66 closed, 6 deferred; 0 warnings** | Tier 2 / S1 | Register validity, not task completion |
| Tracked deletions / Git mutation | **0 deletions; no staging, commit, push, reset, checkout, stash, or cleanup** | Tier 1 | Exact Git authorization remains a separate gate |

## Changes made in this pass

1. Added conservative `--scaffold-worktree` mode to
   `tools/check_worktree_classification.py`; an untracked output ledger is
   excluded only until it is tracked, then normal coverage applies.
2. Added the dated live ledger for all current paths (the live count is
   refreshed below whenever the worktree changes).
3. Updated route/OpenAPI snapshots from the canonical FastAPI app after the
   newly mounted routers increased counts from 337/307 to 340/310.
4. Repaired JSX escaping and comment text in the epistemic and logistics
   panels.
5. Moved the trip-stream callback ref update out of render and wrapped
   effect-driven state synchronization in `startTransition`.
6. Moved the Persona Council `'use client'` directive to the first statement.
7. Kept the itinerary checker self-contained by using PDF.js main-thread mode
   (`disableWorker: true`) until a version-pinned worker asset is hosted; the
   local type declaration now reflects that contract.

## First-principles / long-term / doctrine assessment

| Change | First principles | Long term | Doctrine | Residual |
|---|---|---|---|---|
| Ledger scaffold + validator | Aligned: Git is the source of path/state truth | Aligned: repeatable and drift-failing | Aligned: preserves unknown ownership | Semantic classification still needs owner review |
| Route snapshots | Aligned: generated from canonical app | Aligned: prevents silent contract drift | Aligned: contract evidence is separate from runtime proof | New routes still need end-to-end acceptance |
| React hook repairs | Aligned: state/ref ownership follows React lifecycle | Aligned: avoids cascading renders and stale callbacks | Aligned: defect-sensitive lint gate | Browser interaction evidence still absent |
| PDF main-thread fallback | Aligned for bounded public files and no CDN trust | Partial: worker asset should return for large files | Aligned if file-size caps and trade-off are documented | Performance/large-file evidence is open |
| Route fixture refresh | Aligned if routers are intentional | Aligned with one canonical route source | Aligned: generated artifact, no hand-edited omission | Provider/deployment routes remain unverified |

## Explicit and implicit findings/tasks still in scope

The authoritative task corpus remains
`Docs/exploration/MASTER_FINDINGS_TASKS_INVENTORY_2026-09-02.md` and the
sequenced execution plan is `LAUNCH_IMPLEMENTATION_PLAN_2026-09-02.md`. The
following list is the current decision ledger; it deliberately distinguishes
implementation, research, documentation, operator/legal, and external-provider
work.

### Closed or locally verified in this pass

- A1-1/A-14 preservation and current-path coverage.
- A-21 artifact custody (historical closure preserved).
- Route/OpenAPI snapshot drift (340/310).
- Frontend compile, unit-test, lint-error, and production-build blockers.
- Proposal/security, SQL idempotency, optimistic sync, tenant-isolation,
  payload-limit, and lease focused suites (121/121).

### Implementation tasks (must be researched, implemented, and S2/S3 verified)

> Historical baseline: this matrix records the 2026-09-03 pre-refresh assessment.
> Current implementation/evidence status is maintained in
> `EXECUTION_STATUS_2026-09-04.md`; rows below are retained for audit lineage
> and are not a claim that the pre-fix state still exists.

| ID(s) | Task | Alignment now | Required evidence |
|---|---|---|---|
| S-01/S-02/S-03, PT-01..04 | Env-only proposal signing, no legacy bypass, exact agency binding, canonical token format | Partial until durable rollout | S2 forged/legacy/agency-mismatch tests; S3 restart/revocation |
| S-04/GM-03 | Replace Stripe verification stub or remove surface | Not aligned while stubbed | Provider contract + webhook signature replay test |
| S-05/G-09 | Cross-tenant draft-promote authorization | Partial; focused test exists | S2 two-tenant denial and audit event |
| S-06 | Egress delimiter/raw interpolation hardening | Partial | S2 malicious prompt/URL corpus; S3 provider adapter |
| S-07/G-10 | Public-checker size/depth/resource caps | Partial | S2 oversized/deep payload and timeout tests |
| LR-B01/B02/B03/B06 | Normalize auth kill switch, reject placeholders, env-driven Alembic, secure environment defaults | Partial | Boot matrix for `0/false/true`, staging/prod secret failures |
| LR-B07/S-11 | Durable proposal revocation and run ledger | Not aligned while process-local | Restart persistence and concurrent revoke tests |
| LR-B08/B09 | Truthful readiness plus metrics/request IDs/structured logs | Partial | Dependency-down probe, scrape/auth, correlation integration |
| LR-B10..B13 | Webhook default deny, invite/proposal rate limits, trusted proxy keying | Partial | Abuse-path tests behind proxy and Redis |
| LR-B14/B15 | Single-worker/idempotency topology and non-root API image | Partial | Compose boot, image inspect, duplicate-worker test |
| F-01 | Price-lock compare-and-swap/idempotency | Not aligned until concurrency proof | S2/S3 concurrent relock mutation |
| F-03/F-04 | Server-authored signoff and payment mandate ledger | Not aligned | Authorization audit and failure/replay tests |
| R-11 | Wire durable lease heartbeat; prevent >60s double execution | Partial | S2 expiry/reacquire; S3 worker crash/recovery |
| R-12 | Connect IROPS trigger to canonical journey graph | Partial | Journey disruption integration test |
| A-02 | Replace MD5 pseudo-embeddings with semantic provider or honest lexical-only naming | Not aligned | Retrieval benchmark and fallback evidence |
| A-04/A-05/A-06 | Consolidate settings/fetch/type-contract ownership | Not aligned | Architecture map, generated OpenAPI drift CI, migration tests |
| A-12 | Make edge auth path real or remove inert proxy claim | Partial | Browser/edge request evidence |
| A-16/A-17 | Frontend coverage thresholds/e2e and accessible modal semantics | Not aligned | Mutation-sensitive tests + browser keyboard evidence |
| Phase 1.3 | Remove fabricated landing metrics/testimonials and fake success fallbacks | Not aligned while copy/fallbacks remain | Visual copy review and backend-down UI test |
| Phase 2.1–2.6 | Metrics, error tracking, backups/restore, journey smoke | Not aligned until operational proof | Restore drill, compose smoke, alert observation |
| Phase 3.1–3.3 | Simulated labels, generated types drift gate, frontend env/SSE contract | Partial | Label sweep, OpenAPI diff CI, live SSE/browser check |

### Research / exploration tasks (document before implementation)

- Semantic retrieval options and cost/latency trade-offs (A-02, RAG document).
- Real Amadeus/Sabre/NDC, Stripe Issuing, telephony/IVR, aviation and visa
  sources; maintain simulated-vs-real boundaries (S-09, MILESTONE-3, frontier
  research docs).
- Route feasibility/geospatial and private-aviation data quality, cancellation
  and empty-leg semantics.
- IROPS, duty-of-care, group Pareto fairness, financial settlement/VCC, MRZ
  standards, and retention/privacy requirements.
- Dynamic model routing/SLM and eval design; hidden holdout and 30-scenario
  corpus validity.
- Deployment envelope, backup storage, Redis/Postgres topology, and cost model.

### Documentation / record tasks

- Create and maintain `LAUNCH_STATUS.md`, one known-issues ledger, and one ops
  runbook with detect→diagnose→contain→rollback→escalate steps.
- Reconcile `Docs/` versus `frontend/docs/`; repair dangling motto references.
- Add ADR supersession metadata and resolve numbering gaps without deleting
  historical records.
- Refresh the shared idea pad and memory/index only through the canonical tools.
- Publish user/admin guide, privacy/TOS/DPA drafts, and explicit simulated-data
  disclosures; legal approval remains a human gate.
- Keep persona/scenario/research artifacts as evidence, never as live-provider
  proof; index every new artifact.

### Operator / legal / external gates (cannot be inferred or completed locally)

- Ratify pilot cohort/exposure, signup verification posture, worker topology,
  PII/DPA/TOS policy, and platform-led business model.
- Obtain legal/privacy review before external traveler data.
- Configure real provider credentials, webhook endpoints, backups, alert
  destinations, hosted worker assets, and deployment secrets.
- Run browser/device/production-like verification and owner-operated rollback
  drills.

## Stop conditions and handoff

Stop treating this closure as current if the path set changes. Before any Git
mutation, regenerate and validate the live ledger, classify each path beyond
the conservative scaffold, run the full gates, refresh the motto attestation,
and obtain a separate explicit Git authorization. The current checkout remains
uncommitted. The backend payments-loop ordering residual described in the
original 2026-09-03 snapshot is resolved by the loop-affinity guard documented
below; frontend lint warnings remain open findings.

## 2026-09-04 execution addendum

This addendum records the post-retry implementation and verification pass. It
does not convert local evidence into hosted, provider, legal, browser/device,
or production-release evidence.

### Implemented slices

- Added an asyncpg loop-affinity checkout guard in
  `spine_api/core/database.py`. Because SQLAlchemy pre-ping runs before
  checkout listeners, the queue pool now disables pre-ping and rejects only a
  connection whose `driver_connection._loop` differs from the running loop;
  SQLAlchemy invalidates and reconnects that record. This preserves pooled
  latency and avoids the previously measured `NullPool` timeout-thrash.
- Added `tests/test_database_loop_safety.py` for same-loop acceptance,
  cross-loop rejection, and non-loop-bound driver compatibility.
- Corrected sandbox Stripe CVC generation to a zero-padded three-digit value
  and extended the audit action vocabulary test to cover the implemented
  `AuditAction.READ` call site.
- Seeded the two synthetic agencies in the cross-tenant ghost-workflow probe
  before inserting rows, so the test honors the production FK instead of
  manufacturing a fixture-only integrity failure.
- Refreshed route/OpenAPI snapshots after the intentional route addition.
- Closed the decision-correctness wave (X-04/X-05/X-06/X-13), extraction
  safety wave (X-01/X-02/X-03/X-07/X-08), and SQL idempotency fencing wave
  (N-06/X-11); their dedicated evidence records are indexed in `Docs/`.

### Final verification receipt

| Check | Result | Evidence tier / sensitivity |
|---|---|---|
| Loop/payment/cross-tenant/provider/audit focused tests | 45 passed | Tier 2 / S1–S2 |
| Canonical backend runner (`scripts/run_backend_tests.sh`) | **3,653 passed, 44 skipped, 0 failed** in 111.55s; clean :8000 port; 8 known Python 3.13 fork warnings | Tier 2 / S1–S2 |
| Frontend typecheck | Passed | Tier 2 / S1 |
| Frontend ESLint | 0 errors, 13 warnings | Tier 2 / S1; warning backlog remains |
| Frontend Vitest | 171 files / 1,295 tests passed | Tier 2 / S1 |
| Frontend production build | Passed; dynamic cookie/query routes classified as server-rendered | Tier 2 / S1 |
| Route/OpenAPI parity | 341 routes / 311 paths, 4 passed | Tier 2 / S1 |
| Findings lifecycle checker | 182 rows — open 110, closed 66, deferred 6, 0 warnings | Tier 2 / S1 |
| Live worktree classification | 388 paths validated; 389 porcelain rows including ledger | Tier 2 / S1 |
| Ruff | Changed Python slices and full repo clean | Tier 1 / S1 |

The frontend test output includes intentionally logged React error-boundary and
navigation diagnostics; the test process exited successfully. The frontend
build emits Next.js dynamic-server-usage diagnostics while discovering routes,
then completes and marks those routes dynamic; these are recorded as expected
runtime classification, not suppressed failures.

### Current open tasks and boundaries

The master inventory and launch plan remain authoritative. The newly verified
local slices narrow, but do not eliminate, the following work:

- Replace JSON revocation state with a shared database/ratified durable volume
  for multi-replica deployments; remove or environment-gate the three demo
  token allowlist entries before public exposure.
- Replace the in-memory/fabricated proposal registry with persisted,
  tenant-scoped proposal/resource binding and prove issuance/revocation after
  restart and under concurrent workers.
- Add independent extraction and pipeline producers and seed private holdouts;
  the decision scenario lane is now 30/30 locally passing, but no eval lane
  becomes public authority from this synthetic result alone.
- Build and inspect the production images, run compose/release migration and
  `/ready` failure-injection checks, configure Redis/Postgres/backups/alerts,
  and execute an owner-operated rollback/restore drill. Docker daemon and
  hosted deployment proof were unavailable in this pass.
- Run browser/device/compose smoke against the canonical frontend/BFF route
  and verify SSE, auth, and host-vs-mesh URLs with real runtime state.
- Perform the visual/copy review and browser-down verification for the newly
  honest landing, fast-intake, and corporate-offsites states.
- Resolve the 12 remaining frontend hook/dependency warnings with behavior-sensitive
  tests; do not blanket-disable the rule.
- Complete provider, privacy/legal, retention, DPA/TOS, pilot exposure,
  financial settlement, and real-credential gates as separately authorized
  operator work.

No Git staging, commit, push, reset, checkout, stash, cleanup, or deletion was
performed in this addendum. The ledger must be regenerated again if any path,
runtime, or documentation state changes before a future Git gate.

### 2026-09-04 drift addendum

The live checkout changed after the 2026-09-03 snapshot when the RLS
write-enforcement probe, retrieval-honesty correction, overview-lint
regression, and their evidence records landed. A new conservative scaffold was
generated rather than overwriting the prior ledger:

- `assets/a1_1_live_worktree_2026-09-04_classification.csv`
- **401 source/concurrent paths** and **402 porcelain rows including the
  untracked ledger**
- validator result: `PASS ... classifies all 401 paths from live worktree`

Every row remains `unknown_preserved_concurrent`; this proves inventory
coverage only, not semantic ownership, product correctness, or a release
boundary.

After the launch-status, known-issues, and simulator/provider audit records
were added, the final post-documentation snapshot was regenerated as
`assets/a1_1_live_worktree_2026-09-04_postdocs2_classification.csv`:

- **408 source/concurrent paths**;
- **409 porcelain rows including the untracked ledger**;
- validator: `PASS ... classifies all 408 paths from live worktree`.

The disruption fail-closed implementation and its evidence record were added
after that snapshot. The final 2026-09-04 scaffold is
`assets/a1_1_live_worktree_2026-09-04_final_classification.csv`:

- **412 source/concurrent paths**;
- **413 porcelain rows including the untracked ledger**;
- validator: `PASS ... classifies all 412 paths from live worktree`.

The audit-chain concurrency fix, read-only tamper/fork verifier, and their
regression evidence were then added. The current final2 scaffold is
`assets/a1_1_live_worktree_2026-09-04_final2_classification.csv`:

- **415 source/concurrent paths**;
- **416 porcelain rows including the untracked ledger**;
- validator: `PASS ... classifies all 415 paths from live worktree`.

At the final-classification snapshot the frontend lint residue was **7
warnings** (not the 12-warning historical snapshot above); the current
execution overlay records the later closure. The latest backend receipt is **3,657
passed, 44 skipped, 0 failed**.

After the frontend lint closure and the crisis/bookings truth-containment
waves, the latest custody scaffold is
`assets/a1_1_live_worktree_2026-09-04_final3_classification.csv`:

- **426 source/concurrent paths**;
- **427 porcelain rows including the untracked ledger**;
- validator: `PASS ... classifies all 426 paths from live worktree`.

The current lint state is **0 errors / 0 warnings**. The current frontend
suite is **171 files / 1,298 tests passed**, and the latest backend receipt is
**3,662 passed, 44 skipped, 0 failed**. The current tree remains semantically
unclassified and is not a release boundary.

After the GDS/distribution preview-truth implementation, its focused tests,
and the current status/index updates, the final4 custody scaffold is
`assets/a1_1_live_worktree_2026-09-04_final4_classification.csv`:

- **430 source/concurrent paths**;
- **431 porcelain rows after ledger creation** (430 source/concurrent paths
  plus the untracked ledger);
- validator: `PASS ... classifies all 430 paths from live worktree`.

The current backend receipt is **3,667 passed, 44 skipped, 0 failed**; the
frontend receipt remains **171 files / 1,298 tests passed**, with typecheck,
build, and lint (**0 errors / 0 warnings**) green. The two `git diff --check`
residues remain preserved in their existing owner-controlled files. No
semantic ownership or release boundary is inferred from this custody pass.

After the end-to-end GDS/distribution UI and API truth hardening, the full
backend rerun, and the final status refresh, the final5 custody scaffold is
`assets/a1_1_live_worktree_2026-09-04_final5_classification.csv`:

- **431 source/concurrent paths**;
- **432 porcelain rows after ledger creation** (431 paths plus the untracked
  ledger);
- validator: `PASS ... classifies all 431 paths from live worktree`.

The authoritative backend receipt is **3,667 passed, 44 skipped, 0 failed** in
135.47s; the frontend receipt is **171 files / 1,298 tests passed**, with
typecheck, build, and lint (**0 errors / 0 warnings**) green. The current tree
remains semantically unclassified and is not a release boundary.

The final6 custody scaffold was generated after the final API/UI hardening and
status refresh:
`assets/a1_1_live_worktree_2026-09-04_final6_classification.csv`.
It covers **432 source/concurrent paths** and **433 porcelain rows including
the ledger**; the validator reports `PASS ... classifies all 432 paths from
live worktree`. This remains custody evidence only: semantic ownership,
staging, commit, push, and release authorization are separate gates.

The final7 custody scaffold was generated after the FX/IROPS, duty-of-care,
proposal/persona, suppliers/MRZ truth-boundary slices, their documentation,
and the authoritative full-gate reruns:
`assets/a1_1_live_worktree_2026-09-04_final7_classification.csv`.
It covers **443 source/concurrent paths**; the validator reports
`PASS ... classifies all 443 paths from live worktree`. This is the current
custody count, not semantic ownership or release authorization. The tree
remains intentionally unstaged and uncommitted.

The final8 custody scaffold was regenerated after the IROPS workbench test was
added:
`assets/a1_1_live_worktree_2026-09-04_final8_classification.csv`.
It covers **445 source/concurrent paths** (**446 porcelain rows including the
ledger**) and the validator reports `PASS ... classifies all 445 paths from
live worktree`. The additional path is preserved as unclassified concurrent
work; no semantic ownership or Git release authorization is inferred.

The final9 custody scaffold was regenerated after the financial-route
truth-containment implementation and its regression tests:
`assets/a1_1_live_worktree_2026-09-04_final9_classification.csv`.
It covers **448 source/concurrent paths** (**449 porcelain rows including the
ledger**) and the validator reports `PASS ... classifies all 448 paths from
live worktree`. All paths remain preserved pending semantic ownership and an
explicit Git release decision.

The final10 custody scaffold was regenerated after the A-17 WelcomeCard
semantic correction, keyboard regression test, and status-ledger refresh:
`assets/a1_1_live_worktree_2026-09-04_final10_classification.csv`.
It covers **451 live worktree paths** (**452 porcelain rows including the
ledger**) and the validator reports `PASS ... classifies all 451 paths from
live worktree`. The snapshot is custody evidence only: all paths remain
preserved pending semantic ownership, exact-slice review, and explicit Git
release authorization.

The final11 custody scaffold was regenerated after the N-09/GF-01/GF-03
extraction probe and its durable evidence note/test were added:
`assets/a1_1_live_worktree_2026-09-04_final11_classification.csv`.
It covers **454 live worktree paths** (**455 porcelain rows including the
ledger**) and the validator reports `PASS ... classifies all 454 paths from
live worktree`. This remains custody evidence only; semantic ownership,
exact-slice review, and explicit Git release authorization are still open.

The final12 scaffold was created during the same retry while the extraction
range and X-10 evidence slices were still arriving. Its coverage was
superseded by subsequent concurrent paths before it could serve as the
authoritative snapshot; it is retained as an immutable intermediate artifact
and is not treated as a release receipt.

The final13 custody scaffold is the current authoritative snapshot after the
currency-range regression, X-10 checker-model audit, and settings contract
test were added:
`assets/a1_1_live_worktree_2026-09-04_final13_classification.csv`.
It covers **459 live worktree paths** (**460 porcelain rows including the
ledger**) and the validator reports `PASS ... classifies all 459 paths from
live worktree`. This is custody evidence only: every path is preserved and
accounted for, while semantic ownership, exact-slice review, and explicit Git
release authorization remain separate gates.

The final14 custody scaffold is the current authoritative snapshot after the
X-09 hybrid-configuration parity slice, X-12/F-05 container-hardening slice,
D-01/D-02/D-03 executable contract probes, and the chat request trace were
added:
`assets/a1_1_live_worktree_2026-09-04_final14_classification.csv`.
It covers **469 live worktree paths** (**470 porcelain rows including the
ledger**) and the validator reports `PASS ... classifies all 469 paths from
live worktree`. This remains custody evidence only; semantic ownership,
runtime/hosted proof, exact-slice review, and explicit Git release
authorization remain separate gates.

The final15 scaffold was created after the N-02/N-03 independent-producer
probes, X-14 retention truth correction, and A-17 browser-render artifacts
arrived. It is retained as an intermediate snapshot because the sandbox-card
contract documentation was added immediately afterward.

The final16 custody scaffold is the current authoritative snapshot after the
sandbox card fixed-width correction and its evidence record were added:
`assets/a1_1_live_worktree_2026-09-04_final16_classification.csv`.
It covers **479 live worktree paths** (**480 porcelain rows including the
ledger**) and the validator reports `PASS ... classifies all 479 paths from
live worktree`. This remains custody evidence only; semantic ownership,
runtime/hosted proof, exact-slice review, and explicit Git release
authorization remain separate gates.

The final17 custody scaffold is the current authoritative snapshot after the
browser-render evidence, independent-producer probes, retention disposition,
and sandbox-card regression records were fully documented:
`assets/a1_1_live_worktree_2026-09-04_final17_classification.csv`.
It covers **480 live worktree paths** (**481 porcelain rows including the
ledger**) and the validator reports `PASS ... classifies all 480 paths from
live worktree`. This remains custody evidence only; semantic ownership,
runtime/hosted proof, exact-slice review, and explicit Git release
authorization remain separate gates.

The final18 scaffold was generated after the D-08/D-09 frontend implementation
and the full frontend re-verification (174 Vitest files / 1,311 tests):
`assets/a1_1_live_worktree_2026-09-04_final18_classification.csv`.
It covers **483 live worktree paths** (**484 porcelain rows including the
ledger**) and the validator reports `PASS ... classifies all 483 paths from
live worktree`. This remains custody evidence only; semantic ownership,
runtime/hosted proof, exact-slice review, and explicit Git release
authorization remain separate gates. Any subsequent documentation edits are
captured by the next scaffold rather than retroactively changing this receipt.

The final19 scaffold is an intermediate snapshot after the status
overlays were refreshed with the 174-file / 1,311-test frontend receipt:
`assets/a1_1_live_worktree_2026-09-04_final19_classification.csv`.
It covers **484 live worktree paths** (**485 porcelain rows including the
ledger**) and the validator reports `PASS ... classifies all 484 paths from
live worktree`. This remains custody evidence only; semantic ownership,
runtime/hosted proof, exact-slice review, and explicit Git release
authorization remain separate gates.

The final20 scaffold is the current authoritative snapshot after the A-06/A-20
drift-gate reconciliation record and the D-09 lifecycle evidence were added:
`assets/a1_1_live_worktree_2026-09-04_final20_classification.csv`.
It covers **487 live worktree paths** (**488 porcelain rows including the
ledger**) and the validator reports `PASS ... classifies all 487 paths from
live worktree`. This remains custody evidence only; semantic ownership,
runtime/hosted proof, exact-slice review, and explicit Git release
authorization remain separate gates.

The final21 scaffold supersedes final20 as the current authoritative snapshot
after the R-11/F-10 lease-hardening dossier, tests, and living status overlays
were added:
`assets/a1_1_live_worktree_2026-09-04_final21_classification.csv`.
It covers **489 live worktree paths** (**490 porcelain rows including the
ledger**) and the validator reports `PASS ... classifies all 489 paths from
live worktree`. This remains custody evidence only; semantic ownership,
runtime/hosted proof, exact-slice review, and explicit Git release
authorization remain separate gates.

The final22 scaffold supersedes final21 as the current authoritative snapshot
after the lease router contract tests and their evidence updates were added:
`assets/a1_1_live_worktree_2026-09-04_final22_classification.csv`.
It covers **491 live worktree paths** (**492 porcelain rows including the
ledger**) and the validator reports `PASS ... classifies all 491 paths from
live worktree`. This remains custody evidence only; semantic ownership,
runtime/hosted proof, exact-slice review, and explicit Git release
authorization remain separate gates.

The final23 scaffold supersedes final22 as the current authoritative snapshot
after the A-20 reconciliation dossier and current observability evidence were
added:
`assets/a1_1_live_worktree_2026-09-04_final23_classification.csv`.
It covers **493 live worktree paths** (**494 porcelain rows including the
ledger**) and the validator reports `PASS ... classifies all 493 paths from
live worktree`. This remains custody evidence only; semantic ownership,
runtime/hosted proof, exact-slice review, and explicit Git release
authorization remain separate gates.

The final24 scaffold supersedes final23 as the current authoritative snapshot
after the authenticated D-09 browser evidence document and inspected screenshot
were added:
`assets/a1_1_live_worktree_2026-09-04_final24_classification.csv`.
It covers **496 live worktree paths** (**497 porcelain rows including the
ledger**) and the validator reports `PASS ... classifies all 496 paths from
live worktree`. This remains custody evidence only; semantic ownership,
runtime/hosted proof, exact-slice review, and explicit Git release
authorization remain separate gates.

The final25 scaffold supersedes final24 as the current authoritative snapshot
after the fixture-seed collision remediation, its regression tests, and the
current execution/chat evidence updates were added:
`assets/a1_1_live_worktree_2026-09-04_final25_classification.csv`.
It covers **498 live worktree paths** (**499 porcelain rows including the
ledger**) and the validator reports `PASS ... classifies all 498 paths from
live worktree`. This remains custody evidence only; semantic ownership,
runtime/hosted proof, exact-slice review, and explicit Git release
authorization remain separate gates.

The final26 scaffold supersedes final25 as the current authoritative snapshot
after the readiness auth-boundary remediation, deployment-probe update, and
their durable evidence documents were added:
`assets/a1_1_live_worktree_2026-09-04_final26_classification.csv`.
It covers **507 live worktree paths** (**508 porcelain rows including the
ledger**) and the validator reports `PASS ... classifies all 507 paths from
live worktree`. This remains custody evidence only; semantic ownership,
runtime/hosted proof, exact-slice review, and explicit Git release
authorization remain separate gates.

The final27 scaffold supersedes final26 as the current authoritative snapshot
after the A-20 metadata-visibility implementation, its focused tests, and the
updated execution/chat evidence were added:
`assets/a1_1_live_worktree_2026-09-04_final27_classification.csv`.
It covers **511 live worktree paths** (**512 porcelain rows including the
ledger**) and the validator reports `PASS ... classifies all 511 paths from
live worktree`. This remains custody evidence only; semantic ownership,
runtime/hosted proof, exact-slice review, and explicit Git release
authorization remain separate gates.

The final28 scaffold supersedes final27 as the current authoritative snapshot
after the concurrent `E8_SERVER_SIDE_LIFECYCLE_STATE_2026-09-02.md` artifact
appeared and was preserved:
`assets/a1_1_live_worktree_2026-09-04_final28_classification.csv`.
It covers **513 live worktree paths** (**514 porcelain rows including the
ledger**) and the validator reports `PASS ... classifies all 513 paths from
live worktree`. This remains custody evidence only; semantic ownership,
runtime/hosted proof, exact-slice review, and explicit Git release
authorization remain separate gates.

The final29 scaffold supersedes final28 as the current authoritative snapshot
after the F-07 poisoned-queue dossier and concurrent E-12/E-13 exploration
artifacts were preserved:
`assets/a1_1_live_worktree_2026-09-04_final29_classification.csv`.
It covers **521 live worktree paths** (**522 porcelain rows including the
ledger**) and the validator reports `PASS ... classifies all 521 paths from
live worktree`. This remains custody evidence only; semantic ownership,
runtime/hosted proof, exact-slice review, and explicit Git release
authorization remain separate gates.

The final31 scaffold supersedes final30 after the status-vocabulary report,
its focused tests, and the related documentation receipts were added:
`assets/a1_1_live_worktree_2026-09-04_final31_classification.csv`.
It covers **529 live worktree paths** and the validator reports `PASS ...
classifies all 529 paths from live worktree`. This remains custody evidence
only; semantic ownership, runtime/hosted proof, exact-slice review, and
explicit Git release authorization remain separate gates.

The final32 scaffold supersedes final31 after the F-30 authorization dossier
and retry trace were added:
`assets/a1_1_live_worktree_2026-09-05_final32_classification.csv`.
It covers **533 live worktree paths** and the validator reports `PASS ...
classifies all 533 paths from live worktree`. This remains custody evidence
only; semantic ownership, runtime/hosted proof, exact-slice review, and
explicit Git release authorization remain separate gates.

The final30 scaffold supersedes final29 after the F-08 locking audit dossier
and index cross-links were added:
`assets/a1_1_live_worktree_2026-09-04_final30_classification.csv`.
It covers **523 live worktree paths** (**524 porcelain rows including the
ledger**) and the validator reports `PASS ... classifies all 523 paths from
live worktree`. This remains custody evidence only; semantic ownership,
runtime/hosted proof, exact-slice review, and explicit Git release
authorization remain separate gates.
