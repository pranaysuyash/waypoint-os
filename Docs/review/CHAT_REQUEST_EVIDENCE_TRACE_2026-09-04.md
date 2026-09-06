# Chat Request → Evidence Trace — 2026-09-04

**Purpose:** durable, repository-local trace from the user's explicit and
implicit requests in this workstream to the inspected evidence, decisions,
implementation slices, and unresolved gates. This supplements the
row-level findings register; it does not replace it.

**Persona lens:** PER-0164 — Assumption Auditor. Every request is separated
into observed fact, interpretation, action, and evidence boundary.

## Request chronology and disposition

### Goal continuation and long-term-solution annotation — 2026-09-05

The user selected the earlier report that the insurance route now uses the
canonical agency dependency and asked, "is this the long term 1st principles
solution/" (response annotation 1). The answer is now durable in the F-31
research package: accept the shared tenant resolver, but do not equate that
primitive with complete action authorization, actor attribution, consistency,
eligibility evidence or runtime verification. Restoring only the missing import
is rejected as closure; a second auth framework is also rejected.

Current-source main and independent reviews confirmed missing attachment action
permission, `user_id=agency_id`, ignored path/body disagreement, separate SQL
commit/JSONL audit boundaries and a pytest-specific tenant-header override.
The override does not itself bypass upstream authentication; it can change
tenant resolution and disagree with membership/RLS context during tests.
These precise qualifications, tests and existing seams are documented in
`Docs/research/INSURANCE_TIMING_AND_ELIGIBILITY_CONTRACT_2026-09-05.md`.

The prior turn is classified as progress: it produced evidence that changed the
next action. This continuation resumed the exact live gate handles, without
restarting on an observation timeout. Backend `27931` ended exit 1 with
**1 failed, 3,817 passed, 44 skipped, 8 warnings in 886.97s**, missing disruption
`created_at`. Frontend `40980` ended exit 0: typecheck, lint, **174 files / 1,313
tests**, build passed; the font fetch recovered after retry. Dynamic-server-use
diagnostics remain logged, not silently described as a warning-free build.

The 1,394-path fingerprint changed from `ad079a34...` at 14:54:16Z to
`b36d06e6...` at 15:10:35Z (full hashes in execution status). The disruption
handler and strategic fixture changed during the run; this team did not make
those edits and does not know the writer's identity. Generated session context
also now records 14:55:11Z and retrieval timeouts; its earlier 10:00Z/skip record
is historical, not the current generated state. Doctrine SHA remains unchanged.

A focused retry on current source, session `19827`, returned exit 0 with
**8 passed, 3,854 deselected in 31.43s**. The fixture now supplies `created_at`,
so this does not verify the new fallback. Independent review found false
freshness, false-empty responses, malformed shape handling, sensitive validation
logs, stored capability/identity claims, tenant selection and weak fixture
attribution. Main inspected the current handler and tests; the residual
requirements and full implementation sequence are in
`Docs/review/F38_DISRUPTION_DATA_INTEGRITY_REVIEW_2026-09-05.md`.
Canonical F-38 is now partial/P1, preserving original default-fabrication intent
and the remaining in-window scope. F-31 stays partial/P1. No parent finding is
closed merely because existing selected tests pass.

Final independent review added the implicit 100-trip scan-cap gap, which main
verified in both stores and the facade, and required actionable preservation
of E9.1/E9.3 trip-window scope. The F-38 package now has nine explicit
requirements, including over-100-trip coverage and before/start/end/after-window
tests. The historical E-9 suggestion to retain fabricated alerts is not adopted.

This continuation changed evidence/plan/register documents, not application
source. Existing product changes, artifacts and staged content are preserved.
No new staging, commit, push, service stop, provider or production operation
was performed. Systematic-debugging required tracing the failure and changed
fixture before proposing remediation; verification-before-completion prevented
promoting the focused retry or drifting full run into a final candidate pass.
The full goal remains active; current-candidate gates, concrete implementation
requirements and the separate push/deployment decision remain open.

### Goal continuation — 2026-09-05 semantic review

The prior retry was progress: artifact checks were repaired and source changes
invalidated the old full-suite baseline. This continuation observed the insurance
Header issue corrected in live source, with more edits arriving in source/tests.
No task/process ownership was inferred and no changing product source was
overwritten. Main owned documentation reconciliation; both existing subagents
received bounded read-only source/semantic reviews, not implementation authority.

The user asked for all implicit/explicit work and first-principles alignment.
Accordingly, main mapped 15 master-inventory F/R collisions into reviewed
source-qualified relationships; A-06/A-20/F-17 and existing lease-test follow-ups
were reconciled without false parent closure. Current active overlay references
to simulator-copy, commit-split, deployment and record tasks now name the
inventory source rather than colliding canonical IDs. EV-02/03 remain partial.

Independent insurance review exposed residual invalid-date, certainty, timezone,
bounds and auth-test defects. Main reproduced two arithmetic counterexamples and
researched first-party plan requirements under Research Doctrine 1.0. Published
plan variation falsifies the original universal 14-day premise; replacing that
with another universal constant is rejected. Sources, provenance limitations,
the reviewed source hashes, alternatives, exact task acceptance and release
boundaries are preserved in
`Docs/research/INSURANCE_TIMING_AND_ELIGIBILITY_CONTRACT_2026-09-05.md`.

Verification-before-completion prevented treating changed source, scoped Ruff,
or standard-library arithmetic as full application or insurance-provider proof.
The goal and current Git delivery remain incomplete; no new commit, push,
database or provider action was performed in this continuation.

Terminal evidence: 40 pure lifecycle tests pass; canonical CLI remains
145/91-open/53-closed/one-deferred with zero warnings; nine-document lint passes.
The scoped link gate reports 17 total, 15 OK, one excluded and one Allianz 403,
so documentation delivery is not claimed fully green. Independent reviews
accepted the corrected relationship semantics and required explicit denied-
attempt audit, unverified policy-attachment and privacy boundaries in the F-31
plan; those refinements are recorded. No manual or automated gate was bypassed.

Subsequent safe action: launch fresh full verification without editing the
changing source, using a source/test/config fingerprint and a required post-run
comparison. Backend session `27931` and frontend session `40980` were confirmed
live; commands and initial fingerprint are in the execution status. These
authorized test commands may write normal fixture/cache/runtime state; the
earlier no-runtime-action statement describes the preceding documentation-only
phase, not this newly launched verification phase. No terminal pass, commit or
push is inferred from process startup or partial progress.

### Latest "retry" receipt — 2026-09-05 19:37 IST

The delivery retry repaired newly staged whitespace without dropping historical
evidence, retained exact-byte gzip originals and readable tool transcripts,
verified 38 CSVs against the index, restored the managed refresh's regression
of configured mypy scope, and passed staged whitespace, 146-file Markdown and
413-link checks. `A1_1_DELIVERY_ARTIFACT_REVIEW_2026-09-05.md` records the
independent review and format-preservation rationale.

The backend retry did not pass: 76 focused tests passed but two app setup cases
failed with undefined `Header` in the changing insurance router. A separate
Ruff run confirms that live defect. Source contents also changed in the BFF
trip adapter, disruption router and feedback router during verification, outside
this delivery agent's edits. Their author is unknown. This is direct drift
evidence, not the rejected inference that dirty status implies other ownership.
All changes are preserved; commit creation is paused rather than overwriting
the new edits or claiming the older full-suite receipt covers them. Exact
checkpoint and resumption gates are in `EXECUTION_STATUS_2026-09-04.md`.

Git delivery authorization remains satisfied. No commit/push occurred; the
master/main deployment decision is still separate and unresolved. The main
agent will report the need to coordinate delivery ownership before further
shared-source fixes and to choose a non-deploying push destination or explicitly
authorize the existing Fly deployment effect.

### Current correction — 2026-09-05

The rows below are historical dispositions. This correction controls where
they disagree with current evidence. The user explicitly instructed:
“update gitignore if needed, git add -A, commit, full hook/gate and push.”
That is Git delivery authorization in this conversation; another generic
permission request is not required. Dirty status and placeholder custody
labels do not establish concurrency or another session's ownership.

The read-only retry observed HEAD `2f9a638`, 534 changed/untracked paths,
zero staged paths, local tracking divergence 0/0, and diff-check whitespace
failures in the simulation chronicle and tax test. These are dated snapshots,
not immutable counts. No commit/push occurred in that retry.

Its checker runs reported 194 combined historical/canonical rows and 127
canonical rows, but the parser omitted seven bold NEW IDs and classified
“partially fixed; implementation still open” as closed. These changed the next
action: repair the evidence tool before relying on inventory totals. The ten
additional implicit findings are now durable as EV-01–EV-10 in the canonical
register; EV-11 records the newly discovered push/deployment boundary.

Current implementation continues the original full objective. Main-agent
ownership: findings parser/tests and canonical review records. Delegated
ownership: status reporter/tests/E12 evidence; independent read-only Git
artifact/hook/workflow audit. No repository-wide ownership is inferred.

`agent-start --project travel_agency_agent --skip-index` completed, refreshing
context but warning about busy retrieval and failed hook/guard install attempts.
The context pack records skipped retrieval; it is not complete source retrieval.
Operating Doctrine 8.0 SHA-256:
`ff848618a7431a3b06c7409caa45683bd27c64263d45b93f9fcd36a89803466a`.
Review 1.1, Testing 1.1, and Documentation 1.1 were read from the canonical
family for this work. Skills: systematic-debugging, test-driven-development,
verification-before-completion. Persona: Desktop PER-0923 Evidence Architect.

Concrete delivery boundary discovered: master/main push triggers `flyctl deploy
--remote-only` in `.github/workflows/deploy.yml` independently of CI. Push
destination/deployment direction is needed before that external effect. This
is not a missing ordinary Git approval. Hook source strings point to Downloads,
but live inspection proves that file is a canonical-doctrine symlink with the
same hash; do not claim stale content. The installer auto-refresh's broad
workspace scope still needs care. Shared tooling was not modified.

Evidence-tool regression cycle: eight failures/two passes before the initial
repair, ten passes after; six defensive failures/ten passes before the second
repair, sixteen passes after. The actual repo gate exposed seven missing NEW
status fields; those fields were added with historical descriptions preserved.
Details and exact reproduction commands: `FINDINGS_LIFECYCLE_2026-08-30.md`.

Independent review then exposed sixteen further failing cases (16 previously
passing), followed by six table/date/comment failures (32 passing), then two
inline-comment regressions introduced by the first comment filter (38 passing).
The final focused parser suite passed **40 tests**. Every reproduced bypass
has a regression; the supported Markdown grammar is explicit in the lifecycle
amendment. These are instrument repairs, not automatic product closure.

The reporter worker's implementation was source-reviewed and independently
rerun: **28 tests passed in 5.18s**. The live `both` CLI at
`2026-09-05T11:46:35Z` returned complete observation, no errors, **21,937 SQL
rows** with enforced RLS/read-only transaction for the explicit developer test
agency; the unfiltered file directory contained **1,936 objects**, **1,798
string statuses**, and **138 missing statuses**. SQL groups: active 79,
assigned 19,022, cancelled 2, completed 13, in_progress 880, incomplete 135,
new 1,806. This corrects the prior empty-SQL inference without claiming to
reconstruct historical database state. File and SQL scopes are not equivalent.
Exact command, agency, schema 2, primary references, S2/S3 evidence and limits
are preserved in `../exploration/E12_STATUS_ALIAS_EXPANSION_PLAN_2026-09-02.md`.
EV-06/07 are closed only at this reporting-tool boundary; writer reachability,
canonical vocabulary decisions, telemetry and migration remain open.

Git artifact review identified concrete follow-ups, not inferred authorship:
tracked `data/drafts/index.json` contains runtime identifiers while draft payloads
are ignored; evaluate index-only untracking with local preservation. Two
untracked source-overwrite utilities, `scripts/update_council_panel.py` and
`scripts/write_visualizers.py`, require review/hardening or nonexecuting archival
before inclusion. Forty untracked PNGs require visual/privacy review. Preserve
the existing historical CSV ledgers; do not create another numbered final
snapshot merely to restate custody. A narrow secret-pattern scan found no
high-confidence key, but is not full privacy clearance.

Effective hooks exist under `scripts/hooks`; no pre-push hook was found. The
managed installer must be explicitly repo-scoped if refreshed. Do not rewrite
shared workspace tooling just to replace a canonical-resolving symlink string.
Current doctrine attestation must be refreshed honestly, including required
review duration and integrated section last. Full delivery also requires
backend/FE gates, type-generation parity, import/unscoped-access checks, D6,
Markdown/link gates, staged-diff review, real hook receipts, commit and verified
remote receipt. No gate bypass is authorized or used.

Later in this wave, exact draft-index ignore hygiene and `git rm --cached --
data/drafts/index.json` were completed under the already granted authority.
Only its removal from tracking is staged; the local file's before/after SHA-256
matched. Other-checkout preservation/rebuild is explicitly required before
rollout. All 40 PNGs were viewed with source/scenario provenance review; no new
demonstrated credential disclosure was found, but historical simulator claims
are not provider proof. Both overwrite scripts were semantically compared and
remain preserved, with nonexecuting archival proposed. Full evidence:
`A1_1_DELIVERY_ARTIFACT_REVIEW_2026-09-05.md`.

Fresh terminal full-suite receipts: backend **3,800 passed / 44 skipped /
8 warnings**, exit 0; frontend **174 files / 1,311 tests**, typecheck/lint/build
exit 0; Ruff, scoped mypy, import/tenant-access/D6 checks pass; regenerated API
types match the working copy. Exact commands and limits are in execution status.
The earlier no-staging/only-focused-verification wording describes prior points
in the chronology, not this later state. Commit/push and full managed-hook,
all-document/link, provider/hosted/legal release completion are still not claimed.

Subsequently, full changed-Markdown validation was completed: 145 files, zero
issues after preserving-content formatting and targeted structural corrections.
Both overwrite scripts were archived as exact-byte `.py.txt` evidence under
`Docs/archive/historical_tools/`; post-archive 30 UI/route tests and the production
build passed. These supersede the immediately preceding proposed-archive and
pending-Markdown states. Link validation and final managed-hook/Git delivery
remain distinct gates.

Link validation subsequently passed (408 total, 407 OK, zero errors, one
excluded). The historical walkthrough was found at its existing nested path;
`Docs/INDEX.md` now links there. Tool provenance and checksum are in execution
status. Git Commit Helper was read for staged review/message structure; it
does not replace the managed doctrine gate. Broad staging and local commit
are authorized by the user's explicit A1-1 request; master/main push remains
separate because it triggers Fly deployment without a CI dependency.

Full product implementation, renewed full-suite/hook evidence, commit/push,
provider/hosted/runtime/security/legal closure are not claimed by these tool
checks. Earlier receipts remain historical. The full goal remains active.

| User request / correction | Interpreted obligation | Evidence or artifact | Current disposition |
|---|---|---|---|
| Use any persona from `Understanding_Personas_29aug26`; audit the repo and document everything | Apply a real persona lens, inspect the live checkout, preserve evidence, and create durable audit records | `EXECUTION_STATUS_2026-09-04.md`; `MASTER_FINDINGS_TASKS_INVENTORY_2026-09-02.md`; persona source path recorded in execution status | Completed at the local audit/documentation tier; hosted/provider/legal/ownership proof remains separate |
| List all implicit/explicit findings and tasks | Maintain the complete ID-level union, including research, implementation, decisions, and no-go items | `FINDINGS_REGISTER_2026-08-31.md`; `FINDINGS_TASKS_CONSOLIDATED_2026-08-30.md`; master inventory current overlay | Completed as a documented universe: 183 lifecycle rows, with remaining families and X-series explicitly listed |
| Evaluate first-principles, long-term, and doctrine alignment | Apply falsifiable-contract, honest-reality, ownership, durability, matching-evidence, and rollback criteria | Alignment rule in execution status and master inventory; assumption register | Applied to every disposition; local green tests are not treated as production proof |
| “What’s left?” / “What’s open in A1-1?” | Report residual work and custody state without falsely claiming release readiness | `A1_1_WORKTREE_CLASSIFICATION_CLOSURE_2026-09-03.md`; final29 CSV | 521 live paths are preserved and classified for custody; semantic ownership and release split remain open |
| “Why assume?” | Do not infer authorization, ownership, or product truth from a dirty checkout or prior claims | A1-1 chronology; execution assumption register | Assumptions are labeled; no reset, cleanup, staging, commit, or push was inferred from presence of files |
| “Close this fully as per doctrine aligned work should” / “do all” | Continue the coherent safe unit: inspect, implement bounded fixes, verify, and document; do not collapse separate external gates | Current execution status, launch status, and evidence docs | Local truth-containment and correctness slices were completed where safe; external and owner gates remain explicitly open |
| “Retry” | Revalidate current state rather than repeat stale receipts; continue with the next safe bounded wave | Current isolated 3,733-test backend receipt (44 skips); prior server-present 3,760-test receipt; final29 custody ledger | Completed; stale receipts were replaced in current overlays and the frontend D-08/D-09, lease, browser, fixture-seed, readiness-boundary, A-20 metadata, exact-head readiness, and F-07 inspection waves were reverified; the isolated runner had no :8000 server and therefore skipped server-dependent integration paths |
| A-20 drift follow-up | Research the real migration/model mismatch before wiring a blocking gate | `A20_ALEMBIC_MODEL_MIGRATION_DRIFT_RECONCILIATION_2026-09-04.md`; `tests/test_alembic_metadata_contract.py`; local PostgreSQL probe | Metadata ownership/FK/type slice accepted with 34 focused tests; read-only `alembic check` now reports 37 visible operations; migration tail, nullability/index/legacy-column drift, clean-baseline, rollback, and restore tasks remain open |
| LR-B08/LR-B09 readiness follow-up | Verify the deployment probe reaches dependency-aware readiness without user auth, then keep observability exposure explicit | `LR_B08_B09_READINESS_AUTH_BOUNDARY_2026-09-04.md`; `spine_api/core/middleware.py`; `spine_api/routers/health.py`; `tests/test_readiness_auth_boundary.py`; `.github/workflows/deploy.yml` | Pre-fix `/ready` 401 defect corrected; exact-head readiness now fails closed for stale/empty/multi-row/graph errors; 13 focused tests pass; latest full backend rerun and hosted/fault-injection/timeout proof remain open |
| F-07 poisoned-queue follow-up | Make durable poison state inspectable without promoting unverified replay/purge behavior | `F07_POISONED_QUEUE_INSPECTION_2026-09-04.md`; `spine_api/services/agent_requeue_jobs.py`; `tests/test_agent_requeue_jobs.py` | Payload-free, bounded, deterministic service projection implemented; 34 queue tests and latest isolated full runner pass; tenant scope, authenticated API, replay, purge, audit, and hosted evidence remain open |
| F-17 inventory correction | Separate resolved TimelinePanel behavior from remaining test-hygiene and coverage-policy work | `frontend/src/components/workspace/panels/TimelinePanel.tsx`; frontend suite/lint receipts; `frontend/vitest.config.ts` | F-17a behavior/lint is locally green; F-17b/A-16 warnings and coverage thresholds remain open and are not promoted by aggregate test count |
| Continue the active objective | Keep progressing through independent, evidence-matched slices rather than declaring broad completion | X-09, X-12, D-01–D-03, N-02/N-03, X-14 records; current execution plan | Continued with configuration parity, container hardening, product probes, independent-producer probes, and retention truth correction |
| A1-1 instruction to update `.gitignore`, `git add -A`, commit, run full hook/gate, and push | Perform Git delivery only after exact semantic ownership and release scope are established | `git diff --cached --quiet` → index empty; custody validator; execution Git boundary | Not executed because the live tree contains 483 concurrently dirty paths without semantic ownership. A broad add/commit/push would violate preservation and release-boundary doctrine |

## Implemented evidence slices attributable to this request

### Deterministic extraction and decision truth

- Repeated currency and shared-suffix budget ranges are parsed without
  implicit conversion; mixed currencies abstain.
- N-09/GF-01/GF-03 salutation, label, city-set, and trailing-season cases are
  covered at the deterministic tier.
- X-04/X-05/X-06/X-13 decision escalation, blocker, precedence, and fixture
  behavior is locally verified.

Evidence: 331-test combined tranche; full backend gate; Ruff.

### Simulator/provider honesty

- Financial settlement and VCC responses are explicit computed previews;
  VCC remains `NOT_ISSUED` with no credential-shaped payload.
- IROPS recovery is a review-only plan preview.
- Crisis, bookings, GDS/distribution, FX, duty-of-care, proposal/persona,
  supplier, and MRZ surfaces carry preview/sample/format-only boundaries.

Evidence: focused route/panel suites and the linked truth-boundary records in
the execution status. Provider, customer, legal, and hosted effects remain
unproven.

### X-10 checker-model truth

`checker_model` is persisted and exposed by the settings contract but has no
runtime consumer. The deterministic checker does not accept a model or
provider. The disposition is **DEFER WIRE; RETAIN COMPATIBILITY; CORRECT
CLAIMS BEFORE ACTIVATION**.

Evidence: [X-10 decision record](X10_CHECKER_MODEL_WIRE_OR_REMOVE_2026-09-04.md),
settings/gate/router tests, and the full backend gate. The future router,
provider registry, consent, budget, telemetry, evaluation, and rollback
package is listed there.

### Agent-lease liveness and fencing

The bounded R-11/F-10 slice hardens the in-memory `DurableAgentLeaseManager`:
shared transitions are synchronized, expiry/release/token mismatches fail closed,
acquisition metadata is copied, and fencing counters advance atomically. The
repository-native lease state-machine and router contract tests report 11 passing
tests and Ruff is clean. This is
S2 local state-machine evidence only. It does not establish SQL durability,
supervisor heartbeat wiring, pipeline-version compatibility, agency/RLS scope,
restart recovery, or multi-host behavior; those remain explicit tasks in the lease
dossier.

### D-09 authenticated browser evidence

The D-09 browser follow-up exercised
`/trips/trip_6f1c8b4e2070/intake?repair=budget` at 1280×900 through the
authenticated frontend BFF. Signup/auth-me and pipeline creation completed;
the final URL consumed `repair=budget`, the DOM contained exactly one budget
editor, and the active element was its focused input. The screenshot was
visually inspected and preserved as `d09-browser-budget.png`. This is local
authenticated Tier-2 evidence only. Save/reload persistence, mobile and
assistive-technology behavior, hosted auth, provider effects, and the existing
`/api/trips` seed-ID collision were open at capture time. The collision is now
remediated locally: only a `trips.id` duplicate-key conflict is skipped per
fixture row, later rows continue, and unrelated integrity errors propagate.
The 3-test collision/idempotency suite and 49-test booking-data module pass;
the post-fix authenticated browser list/seed response and hosted race proof
remain open. The existing Chrome tab was rechecked after remediation but had
expired auth and rendered “Workspace unavailable Unauthorized”; no new local
account or data mutation was created to force a browser receipt.

## Evidence boundary and unresolved obligations

The following are not proved by local tests or static inspection and remain
open tasks:

- hosted deployment, secret management, migrations, rollback, backup/restore,
  failover, RPO/RTO, and multi-replica convergence;
- real provider OAuth/webhook/order/reconciliation/cost/failure contracts;
- browser/device, screen-reader, keyboard, focus-order, and visual evidence;
- independent extraction and pipeline producers, private holdouts, calibrated
  judging, trajectory evaluation, adversarial/mutation coverage;
- legal/privacy/DPA/TOS/consent/retention and customer-data review;
- semantic ownership of the dirty tree and an exact authorized Git release
  snapshot;
- owner ratification for signup posture, business model, worker topology,
  wire-versus-label decisions, and D-01/D-03 product contracts.

## Current receipts

- Latest backend (isolated/no server): **3,733 passed, 44 skipped, 0 failed** in
  382.49s, eight known Python 3.13 fork warnings; prior server-present runner:
  **3,760 passed, 10 skipped, 0 failed** in 304.49s. The isolated run skips
  server-dependent integration paths, while the server-present run is broader
  but non-hermetic. Both receipts are retained because they prove different
  evidence dimensions.
- Frontend: **174 files / 1,311 tests passed**; lint, typecheck, and build
  pass.
- D-09 lifecycle subset: **3 files / 41 tests passed**; the combined D-08/D-09
  command remains **3 files / 21 tests passed**.
- Combined retry tranche: **331 passed**.
- Converged implementation tranche (container, X-09, D-01/D-02/D-03, N-02/N-03,
  X-14, sandbox-card, D6, and extraction regressions): **369 passed**.
- Findings lifecycle: **183 rows — 108 open, 69 closed, 6 deferred; 0
  warnings**.
- Custody: final29 validates **521 live paths** (**522 porcelain rows including
  the ledger**); all paths are preserved pending semantic ownership.
- Git index: empty; no commit or push performed.
- Fresh running-server probe: `/health` returned 200, `/metrics` returned 401
  without credentials, and frontend `:3005` returned 200. Earlier A-17 browser
  notes recorded `/metrics` as 200 under their captured runtime context; the
  current unauthenticated result is retained as the stronger current truth for
  the LR-B09 scrape-authentication task.

This trace is append-only in meaning: later waves should add a dated section
when a request, decision, or evidence boundary changes. Historical records
must not be deleted to make the current state appear cleaner.

## 2026-09-05 retry continuation — F-08 and E-12 specialist audits

The retry requested a fresh live check of the remaining A1-1/open-slice
inventory. Two read-only specialist audits were completed:

- **F-08 locking:** `spine_api/core/locking.py` still falls back silently to a
  process-local `asyncio.Lock` for absent/uninspectable/non-PostgreSQL binds;
  no production trip mutation invokes it; and PostgreSQL transaction lifetime
  is undocumented/unproved. The focused locking/startup command reports
  **62 passed in 6.84s**, but this is Tier-2/S1 evidence of current tests, not
  distributed locking proof. The durable disposition is open and recorded in
  `Docs/review/F08_LOCKING_SEMANTICS_AUDIT_2026-09-04.md`.
- **E-12 status aliases:** `normalize_trip_status()` has no production callers;
  `Trip.status` remains freeform; `active` and `archived` are read-model
  decisions, while `escalated`/`assigned` and similar tokens cross routing,
  review, follow-up, or provider axes. Blind alias expansion, strict enum, and
  DB checks remain deferred. The safe slice is now implemented as the
  read-only `tools/status_vocabulary_report.py` with **2 focused tests passed**.
  Current file evidence is **1,936 files / 1,798 explicit status values / 138
  missing keys / 0 malformed / 0 explicit-null**. Current SQL invocations
  returned **0 visible groups and rows** both unscoped and for the test agency;
  this is retained as an environment/RLS limitation, not a production-empty
  claim. The E-12 plan and tool documentation were updated accordingly.

The final31 custody ledger was revalidated after this continuation: **529 live
paths covered**, with the Git index still empty. No staging, commit, push,
reset, checkout, stash, cleanup, or deletion was performed.

After the F-30 dossier and this trace update, final32 superseded final31 and
was revalidated at **533 live paths**; the index remains empty.

## 2026-09-05 F-30 authorization remediation

The isolated F-30 route fix removed raw agency-header/test-tenant selection
from the corporate-policy audit and override handlers and injected the
canonical JWT-derived agency dependency. Hermetic AST/source assertions report
**2 passed**; Ruff and compilation are clean. A TestClient runtime attempt was
terminated after the app lifespan hung for more than five minutes, so no HTTP
401/200 or cross-tenant runtime claim is made. F-30 remains partial/open for
runtime, RLS, authenticated-principal, audit, and hosted evidence. The full
record is `Docs/review/F30_CORPORATE_POLICY_AUTH_BOUNDARY_2026-09-05.md`.
