# Execution Status and Complete Findings/Tasks Register — 2026-09-04

## Latest continuation: semantic reconciliation — 2026-09-05

### Full-gate terminal receipts and source drift — 2026-09-05

At `2026-09-05T14:54:16.722Z`, a read-only fingerprint covered 1,394 existing
source/test/config/fixture paths selected from Git's tracked and nonignored
untracked inventory (backend, frontend, scripts/tools, fixtures and CI plus root
dependency/build config). SHA-256:
`ad079a34cd80576216ab93810131617bf57d0a943e54f5c5ced7d4f412635e2a`.
Docs and runtime outputs are not part of that source fingerprint. It is drift
detection, not a checkout lock or an immutable snapshot; compare after the run
and do not promote a changed candidate from an older test result.

Full backend session `27931` ran
`USE_HYBRID_DECISION_ENGINE=1 PYTHONDONTWRITEBYTECODE=1 scripts/run_backend_tests.sh -p no:cacheprovider`.
Terminal result: **exit 1; 1 failed, 3,817 passed, 44 skipped, 8 warnings in
886.97s**. Failure:
`tests/test_strategic_phases_6_to_9.py::test_strategic_phases_6_to_9_lifecycle_end_to_end`,
`DisruptionAlert.created_at` missing during alert construction. The eight
warnings concern Python 3.13 multi-threaded `fork()` in ledger durability tests.

Full frontend session `40980` ran
`npm run typecheck && npm run lint && npm test -- --run && npm run build`.
Terminal result: **exit 0; typecheck, lint, 174 test files / 1,313 tests and
build passed**. Vitest duration: **185.74s**. A Google Fonts TLS/download retry
recovered; request-dependent routes emitted dynamic-server-use diagnostics,
then the build completed. No hosted or browser-flow proof follows from this.

At `2026-09-05T15:10:35.822Z`, the same 1,394-path fingerprint was
`b36d06e6e8ba4a01f53c34513be3034c44bb563276035a67ddf5acc1a1602395`.
**The candidate changed during verification.** These terminal receipts describe
the runs, not an immutable current candidate. Live source now backfills missing
disruption timestamps and the strategic test now supplies `created_at`; neither
change was made by this delivery lane. Writer identity remains unknown.

Focused current-source retry, session `19827`:
`USE_HYBRID_DECISION_ENGINE=1 PYTHONDONTWRITEBYTECODE=1 scripts/run_backend_tests.sh -k 'strategic_phases_6_to_9 or f31 or f38' -p no:cacheprovider`
returned **exit 0; 8 passed, 3,854 deselected in 31.43s**. This establishes the
selected local behavior, not the missing-timestamp fallback, production auth,
insurance eligibility, or a new full-suite pass. The insurance test still
expects invalid deposit input to become a fresh quote-time window.

Testing wrote its normal fixture/cache/runtime state; no application source was
edited by this delivery lane. No service was stopped to force a clean result.
Commit/push remain pending actual candidate gates and EV-11. Independent review
of the new disruption behavior is required before treating the fallback as a
long-term fix; malformed stored rows, false freshness and operator visibility
must be covered rather than merely returning a successful list.

### Completed semantic and research work

The prior turn made progress, not a verified wait: it repaired delivery gates
and found source drift. This continuation rechecked live files rather than
repeating the old blocker. The insurance quote now uses
`Depends(get_current_agency_id)`; the undefined-Header failure below is historical.
The insurance/disruption scoped Ruff check passes. No fresh full-app gate,
commit or push is claimed; new source/tests continued to appear outside this
delivery lane, whose writer identity is still unknown.

Safe work completed while preserving those edits:

- EV-02: reviewed all 15 colliding F/R labels between the master inventory and
  canonical register; documented same-issue/subtask/related/split/unmapped
  relationships in `FINDINGS_LIFECYCLE_2026-08-30.md`. Structural check verified
  15 unique references, existing source rows and existing canonical targets.
  This is not automatic alias-coverage enforcement or a lifecycle closure.
- EV-03: independent source review corrected A-06's obsolete no-CI-gate claim,
  added A-20's dated metadata/37-operation residual, split F-17 local test/lint
  repair from production race/coverage policy, and replaced the instruction
  to recreate four existing lease-router tests with the actual auth/runtime gaps.
- F-31: independent review and primary-source research showed invalid-date
  fallback, unconditional eligibility, time-zone inconsistency, bounds and auth
  evidence gaps. Main independently reproduced 13 versus 14 days for the same
  instant and an extreme-date OverflowError. The universal 14-day premise was
  corrected; plan-specific evidence is required. See the
  [research and implementation package](../research/INSURANCE_TIMING_AND_ELIGIBILITY_CONTRACT_2026-09-05.md).

The canonical CLI remains 145 rows: 91 open, 53 closed, one deferred; the status
refinements do not silently close parent findings. Documentation updates in this
continuation are unstaged. No application source was edited by this delivery
lane; no generated types, shared runtime, database, external provider or Git
delivery state was changed by these reconciliation edits.

Continuation verification: 40 pure lifecycle tests passed in 1.07s; the canonical
plus historical-companion CLI returned zero warnings. Nine changed documents
passed Markdown lint. The focused 17-link check is **not fully green**: 15 OK,
one excluded, and the Allianz research article returned HTTP 403 to Lychee.
The research note retains the accessible-tool/content evidence and provenance
limitations; no blanket status-code acceptance or link exclusion was added.
Independent review approved the bounded identity/status corrections after
removing GM-01's stale commit-split veto, and accepted the F-31 research after
adding privacy and recorded-versus-verified attachment requirements.

## Latest retry: delivery gate paused — 2026-09-05 19:37 IST

This receipt supersedes the earlier full-suite results as a statement of the
current checkout, without erasing those historical passes. No commit or push
was created. HEAD remains `2f9a6384b42a90db415fbf012d94b60b5eaaa3bc`.

- 542 paths are staged. The complete staged `git diff --cached --check` passes.
- 146 changed Markdown files pass lint. Lychee reports 413 total links,
  412 OK, zero errors, one excluded.
- All 38 historical classification CSVs match their staged bytes (4,592,468
  bytes total). Both compressed script originals roundtrip to their recorded
  hashes; readable transcripts match after trailing-whitespace normalization.
- Focused backend retry: 76 passed, two setup errors. The app cannot import
  `spine_api/routers/insurance.py`: `generate_insurance_quotes` still references
  `Header` at line 72, but the import now contains `Depends` instead of `Header`.
  A fresh Ruff check confirms F821. This is not a passing application gate.
- The first Ruff retry also caught `now_iso` unused in the disruption router.
  A subsequent direct diff showed that line removed along with the fabricated
  default-disruption branch. The second Ruff check has only the insurance error.
- Changes appeared during verification in `frontend/src/lib/bff-trip-adapters.ts`,
  `spine_api/routers/disruption_radar.py`, and `spine_api/routers/feedback.py`.
  They are unstaged and were not made by this delivery agent or its two bounded
  reviewers. Their author/owning task is unknown; changing file contents are
  observed, but authorship is not inferred from Git status.
- Frontend retry completed: typecheck, lint, 30 focused tests across two files,
  and production build all passed, exit 0. Dynamic-server-use diagnostics were
  emitted for request-dependent API routes. This is local evidence, not a
  frozen-candidate or hosted receipt.
- Final drift check also found new unstaged edits in
  `frontend/src/components/workspace/panels/PacketPanel.tsx` and
  `src/intake/packet_models.py`, again outside this delivery agent's edits.
  The two retry-record documentation updates remain unstaged as well. No
  further broad staging was done after the change-in-flight condition appeared.

Delivery must resume from a coordinated, stable candidate: preserve and review
the new changes, resolve the insurance import/auth contract with its owner,
regenerate affected API types, rerun relevant/full gates, finish truthful
attestation, then use normal commit hooks. No gate was bypassed. The already
authorized Git operation is not the missing approval; the unresolved boundary
is ongoing shared-checkout mutation, plus master/main's automatic Fly deployment
before push (EV-11). Other writers need coordination, not a speculative owner
classification. The full project objective remains open.

## Current evidence-system correction — 2026-09-05

This is an execution summary, not an independent lifecycle register. Current
IDs/status are owned by `FINDINGS_REGISTER_2026-08-31.md`; this file retains
historical receipts and scoped implementation detail. Its older counts and
blanket authorization/concurrency wording are superseded by this correction
and the request trace's 2026-09-05 section.

- The user already authorized A1-1 `.gitignore` hygiene, `git add -A`, commit,
  full hooks/gates, and push. Placeholder custody labels do not establish
  active concurrency or another session's ownership. Actual artifact/privacy
  review and full delivery receipts remain required.
- Read-only workflow inspection found master/main push triggers Fly deployment
  independently of CI. Resolve destination/deployment direction before push
  (EV-11), not another generic Git permission gate.
- The findings parser now reads explicit status columns, includes formatted
  NEW IDs, excludes historical rows from current counts, preserves explicit
  verification dates, and rejects ambiguous canonical state. Forty focused
  checks pass following failing-first and independent-review cycles; the
  always-closed mutation fails.
  Evidence is Tier 2 / S2, with S3 for the lifecycle-state invariant.
- Seven previously skipped NEW rows now have explicit status, and EV-01–EV-11
  capture additional implicit findings. After EV-06/07 local reporter closure,
  the current gate reports 145 canonical rows: 91 open,
  53 closed, 1 deferred. Re-run the canonical CLI rather than copying counts
  from older snapshots. Counts still represent rows, not unique semantic work.
- `agent-start --skip-index` refreshed context but warned of busy retrieval
  and failed hook/guard installation attempts. Effective hook Downloads-path
  strings resolve through a verified canonical symlink with matching hash;
  stale doctrine content is not established. No shared tools were modified.
- The simulation chronicle's three trailing-space lines were changed to
  explicit paragraph breaks; the tax-test extra EOF blank line was removed.
  Historical content and executable assertions are preserved.
- Reporter independent verification: 28 tests pass; live `both` CLI at
  `2026-09-05T11:46:35Z` returned no errors, 21,937 SQL rows under explicit
  agency RLS/read-only transaction, and 1,936 unfiltered file objects including
  138 missing statuses. These are different populations. E12 evidence and
  `tools/README.md` document schema 2, scope, error handling and residual limits.
- Full backend and frontend gates were started after these repairs; until
  their terminal receipts are appended, earlier full-suite results below are
  historical and are not promoted by the focused tests.

Parser contract/evidence: `FINDINGS_LIFECYCLE_2026-08-30.md`. Request and
authorization history: `CHAT_REQUEST_EVIDENCE_TRACE_2026-09-04.md`.
Fresh full-worktree verification (2026-09-05):

| Gate | Command / result | Evidence limit |
|---|---|---|
| Backend | `USE_HYBRID_DECISION_ENGINE=1 PYTHONDONTWRITEBYTECODE=1 scripts/run_backend_tests.sh -p no:cacheprovider` — **3,800 passed, 44 skipped, 8 warnings**, 1126.84s, exit 0 | No backend server detected; server-dependent cases skipped. Warnings concern Python 3.13 fork in a multithreaded process. |
| Frontend | `npm run typecheck && npm run lint && npm test -- --run && npm run build` — exit 0; **174 files / 1,311 tests pass** | Build logged dynamic-server-use diagnostics for dynamic auth/proxy routes; production build completed. No hosted or new browser proof. |
| Ruff | `.venv/bin/ruff check .` — exit 0, all checks pass | Whole-repository configured lint, not semantic correctness. |
| Mypy | `.venv/bin/mypy --config-file pyproject.toml` — exit 0, 10 source files | Scoped security/tenancy coverage, not all backend modules. |
| Imports / tenant access | `bash scripts/check_f401.sh`; `bash scripts/check_unscoped_trip_access.sh` — exit 0 | No F401 violations or detected unscoped router trip access; static boundaries only. |
| D6 | `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/verify_d6_gate_snapshot.py` — `ok: true`, exit 0 | LLM unavailable/default-decision warnings; no new live-provider evaluation proof. |
| Generated types | Canonical `scripts/generate_types.py` — exit 0, working-copy SHA unchanged, 39,316 bytes | SHA `a457a71b4cee25e8f33c1bc4dff26e352059d3658fca905dddcab99870a81917`; exact staged/committed parity still belongs to delivery. |
| Markdown | First seven-document check: 93 issues; formatter repaired 85; remaining eight corrected without deleting historical content | Full changed-document/link gate still must be distinguished from this subset. |
| Git hygiene | Exact runtime draft-index ignore + index-only untracking; local file SHA unchanged | This one removal from tracking is staged. Other-checkout preservation/rebuild caveat in artifact review. No commit/push. |

Documentation gate follow-through: the full changed-Markdown set initially had
474 issues across 76 of 145 files. Mechanical formatting applied 409 repairs
across 72 files; remaining fence-language, inline-table-pipe, source-marker and
duplicate-heading issues were corrected with content preserved. Fresh full
check: **145 files, zero issues**, exit 0. No Markdown rule was weakened.
The newly added archive README is included in the subsequent final check.

Link validation also passed: **408 total, 407 OK, zero errors, one excluded**
using Lychee 0.24.2 with the CI exclusions and no credentials. A broken
`Docs/INDEX.md` pointer was corrected to the existing historical Wave 5 section
in `Docs/Wave_3_Verification/walkthrough.md`; no replacement narrative was invented.
The ARM macOS binary came from the
[official Lychee release](https://github.com/lycheeverse/lychee/releases/tag/lychee-v0.24.2),
with archive SHA-256 verified against release metadata:
`c9d3740ea2d891854d37116c9fba840f37b6e7c89d330e7db84ac333631c4977`.
It and the isolated Markdown cache are ignored tool state under `.runtime/`,
not source artifacts. Four distinct public documentation URLs were inspected
before the online check; no cookie jar, auth token or mail checking was enabled.

Both source-overwrite scripts are now exact-byte `.py.txt` artifacts under
`Docs/archive/historical_tools/`; original hashes match. After archival,
30 UI/route tests passed and the production build passed again (exit 0).
No product capability was removed; maintained TSX files already contained all
useful generated behavior.

Retry checkpoint: all 537 original delivery paths were staged before the final
whitespace check. That check exposed historical CSV CRLF and newly added source/
Markdown whitespace not covered by the earlier tracked-only check. The artifact
review now records the narrow CSV line-ending policy, exact-byte gzip originals
with readable script transcripts, and formatting-only source/Markdown repairs.
Managed refresh briefly regressed the existing configured-mypy-scope hook logic;
the exact reviewed behavior was restored. These are gate repairs, not additional
product-completion claims. Commit and push still require terminal receipts.

Screenshot/source/runtime artifact evidence and exact dispositions:
`A1_1_DELIVERY_ARTIFACT_REVIEW_2026-09-05.md` (40/40 PNGs viewed). Full hook,
commit/push and external readiness are not claimed. Original full project goal
remains open. All older full-suite/count/authorization tables below are historical.

**Purpose:** current status overlay for the full findings corpus, after the
2026-09-03/04 implementation and verification wave. The historical inventory
at `Docs/exploration/MASTER_FINDINGS_TASKS_INVENTORY_2026-09-02.md` remains the
source of discovery and provenance; this document is the current execution
view and does not delete or rewrite that history.

**Checklist applied:** `IMPLEMENTATION_AGENT_REVIEW_HANDOFF_CHECKLIST.md`

**Persona lens:** **PER-0164 — Assumption Auditor** from
`/Users/pranay/Desktop/Understanding_Personas_29aug26/01 Expanded Personas/05 Feedback, Critique & Review/PER-0164 - Assumption Auditor.docx`.
Its governing question—“What must be true for this reasoning to hold, and
which conditions have actually been demonstrated?”—is applied below by
separating observed facts, inferences, normative decisions, environmental
dependencies, and unsupported release claims.

**Evidence boundary:** local tests, static checks, generated snapshots, and
local configuration are Tier 1/2 evidence. They do not establish hosted,
provider, browser/device, legal/privacy, customer, backup/restore, or
production-release proof.

## Current truth

| Surface | Current evidence | Status |
|---|---|---|
| Backend | Latest complete local runner: **3,733 passed, 44 skipped, 0 failed** in 382.49s with no :8000 server detected; prior server-present run: **3,760 passed, 10 skipped, 0 failed** in 304.49s | No-server run is more isolated but skips server-dependent integration; server-present run is broader but non-hermetic; 8 known Python 3.13 fork warnings |
| Frontend | Typecheck pass; 174 Vitest files / **1,311 tests pass**; production build pass | Local gate green |
| Frontend lint | **0 errors, 0 warnings** | Audit, IntakePanel, Workbench, and generated-type warning surfaces are clean |
| Route contract | 341 routes / 311 OpenAPI paths; parity tests pass | Local contract green |
| Findings lifecycle | Current checker: **194 rows: 118 open, 70 closed, 6 deferred, 0 warnings** (the earlier 183-row receipt is retained as historical evidence) | Register valid; open work remains |
| Worktree custody | Latest A1-1 ledger: final32 covers **533 live paths** (534 porcelain rows including the ledger); earlier final29/final31 counts are retained as historical receipts | Preserved, not semantically classified |
| Git | No staging, commit, push, reset, checkout, stash, cleanup, or deletion in this wave | Separate Git gate required |

## Assumption register (persona output)

| Assumption behind a closure claim | Classification | Evidence status | Falsification / next check |
|---|---|---|---|
| A green local test suite represents production readiness | Inferred, decision-critical | **False as a general premise**; it proves only the exercised local contract | Run hosted/provider/browser/device/restore gates before release |
| The asyncpg pool can safely reuse connections across ASGI test loops | Environmental/dependency | **Falsified** by the original Future-attached-to-different-loop traceback; fixed and covered by 3 tests plus the current local runner receipts | Recheck under dedicated multi-worker deployment |
| A signed proposal token identifies a real persisted tenant resource | Dependency-related | **Locally demonstrated** through agency-bound lookup and fail-closed projection; process-local cache/shared-host revocation are bounded | Prove shared revocation/issuance durability and hosted/browser/provider behavior |
| A fixture mirror measures extraction or pipeline quality | Factual-looking but unsupported | **Rejected** by evaluator provenance gate; lanes remain shadow | Add independent producers and runnable raw inputs |
| A reachable `/health` endpoint proves all required dependencies are ready | Environmental | **False**; `/health` is liveness-only and `/ready` checks DB/migration/Redis | Run dependency fault injection in compose/release environment |
| One worker is a durable topology decision, not just a local default | Normative/environmental | **Partially demonstrated** in manifests; worker ownership and crash recovery are unproven | Execute worker crash/reacquire/duplicate-run drill |
| Synthetic provider adapters can be described as live business capability | Normative | **Rejected**; they are explicitly sandbox/simulation surfaces | Wire real providers only after contract, secrets, webhook, and cost review |
| The dirty worktree can be safely committed as one coherent change | Ownership/environmental | **Not demonstrated**; current paths remain conservatively concurrent/unknown | Semantic owner classification and separate Git authorization |
| Deployment can call `/ready` without credentials | Contract/environmental | **Falsified before this wave**; middleware returned 401 although deployment manifests named `/ready` | Public-path fix is locally covered; run compose/Fly/Render and dependency fault-injection probes |
| A protected static `/metrics` endpoint is automatically a valid monitoring contract | Normative/operational | **Undecided**; current endpoint is static JSON, protected, and version-inconsistent | Ratify format, exposure, auth/network, labels, privacy, and alerting before wiring a public scrape |

## Implemented and locally verified (promotion is still bounded)

| IDs | Finding/task | Current decision | Evidence / remaining boundary |
|---|---|---|---|
| S-01, S-02, S-03, PT-01..04 | Proposal secret, legacy bypass, agency guess-loop, canonical HMAC payload | **ACCEPT — local complete** | 40 proposal tests + Ruff; explicit demo gate and shared-host revocation/issuance durability remain open |
| S-04 / GM-03 | Stripe webhook HMAC verification, timestamp tolerance, multi-signature support, and fail-closed configuration | **ACCEPT — local complete** | Provider-adapter signature suite passes; live Stripe endpoint, replay store, and webhook delivery proof remain external |
| S-05 / G-09 | Agency-scoped draft promotion with indistinguishable 404 denial and metadata-only denial audit | **ACCEPT — local complete** | Two-tenant denial/positive-control suite passes; hosted authorization and audit sink evidence remain external |
| S-06 | Per-call nonce delimiters for untrusted egress and packet facts | **ACCEPT — local complete** | Egress/hybrid malicious-content regressions pass; provider-specific threat corpus and live adapter evidence remain open |
| N-04 | YieldArbitragePanel route/protocol mismatch and fabricated reticket fallback | **ACCEPT — local complete** | Legacy and app-local panels use canonical `/api/v1/yield`/BFF routes; 21 focused and 174-file/1,311-test full frontend suite passes; live provider/reticket evidence remains open |
| N-05 / F-03 | Public proposal token could mint fabricated content without persisted tenant/resource binding | **ACCEPT+MODIFY — local complete** | Both public proposal routes bind to persisted agency-owned resources and fail closed; explicit demo gate is startup-rejected in staging/production; 65 proposal + 49 startup tests pass; shared revocation, hosted issuance, and browser/provider evidence remain open |
| F-01 | Price-lock optimistic version guard and replay idempotency | **ACCEPT+MODIFY — local complete** | Version-conflict and replay tests pass; durable multi-writer CAS/compensating-action proof remains open |
| S-07 | Public-checker payload/depth limits | **ACCEPT — local complete** | Focused limits suite; provider/abuse load proof remains open |
| S-08, S-10 | Memory/tenant middleware hardening slices | **PARTIAL** | Focused tenant tests pass; full multi-replica and route-order proof remains open |
| S-11, PT-05/06 | Revocation persistence, full SHA-256 digest | **PARTIAL** | Atomic locked JSON restart/merge/corrupt-store tests pass; shared DB/volume needed for replicas |
| S-11 / N-07 / LR-B07 | Crash-safe run ledger and event publication | **ACCEPT+MODIFY — local complete** | Atomic fsync/replace plus process-safe locks; dedicated durability/concurrency tests pass; durable-volume/PostgreSQL, backup/restore, and multi-replica convergence remain open |
| S-13, S-14 | Auth kill-switch and committed DATABASE_URL defaults | **ACCEPT — local complete** | Startup matrix and Alembic fail-closed tests; hosted secret-manager proof remains open |
| E-01, E-02, E-03, E-05 | Honest eval provenance, 30-scenario completeness, holdout policy, register roles | **ACCEPT+MODIFY — shadow where required** | 67 focused tests, D6 verifier green; decision corpus is 30/30, extraction/pipeline have no independent producers, holdout empty |
| E-04 | Journey smoke | **PARTIAL** | Included in backend suite; compose/deployed browser smoke absent |
| LR-B01..B06 | Environment parsing, Redis/SQL requirements, secret strength, Alembic ownership | **ACCEPT — local complete** | 56 focused startup/readiness tests; real deployment matrix remains external |
| LR-B08..B15 | Readiness, containers, compose, Fly/Render manifests, worker topology | **PARTIAL** | Static/semantic checks pass; Docker daemon, image inspect, release migration, rollback, and restore proof absent |
| LR-B08 / LR-B09 | Readiness auth boundary and deployment probe target | **ACCEPT+MODIFY — local contract fixed; runtime proof open** | `/ready` is public, dependency-aware, and now requires exactly one current Alembic revision matching the artifact head; 13 focused readiness/auth tests and the latest full backend gate pass. Bounded-timeout, dependency fault-injection, hosted, multi-replica, and metrics-contract evidence remain open. See [readiness dossier](LR_B08_B09_READINESS_AUTH_BOUNDARY_2026-09-04.md) |
| A1-1 / A-14 / A-21 | Worktree custody and current-path coverage | **ACCEPT — custody complete** | Current final29 validator covers 521 live paths; semantic owner classification and Git mutation are separate gates |
| Route/OpenAPI drift | Generated snapshots refreshed to 341/311 | **ACCEPT — local contract complete** | End-to-end route authorization/provider behavior still requires runtime proof |
| Asyncpg loop affinity | Pooled connections crossing short-lived TestClient loops | **ACCEPT — local complete** | Checkout guard + 3 regression tests; full backend suite green; monitor under real worker topology |
| N-06 / X-11 | Durable SQL JSONB race and stale-owner terminal CAS | **ACCEPT — local/live-DB complete** | Local focused regression 25 passed; live Postgres JSONB + 8-session race (1 winner/7 losers); live TTL stale CAS false/new CAS true; hosted/provider and unknown-outcome evidence remain open |
| S-12 | RLS catalog, policy, and cross-tenant write enforcement | **ACCEPT — local/live-DB complete** | Live rollback-only probe proves agency A cannot update/delete agency B rows and cannot insert a mismatched agency_id (`SQLSTATE 42501`); combined live/mock RLS 20 passed; 12 protected tables, 4 documented exemptions; hosted role provisioning and raw-SQL path coverage remain open |
| A-02 / R-03 | Retrieval implementation and documentation honesty | **ACCEPT+MODIFY — local truth corrected; semantic provider remains open** | Code/docs now identify MD5 hash-bucket vectors, substring BM25-style heuristic, label/entity boost (no edge traversal), and heuristic grounding; 14 focused RAG tests and Ruff pass; provider selection, benchmark, calibrated scores, claim-level entailment, and hosted privacy/cost evidence remain open |
| S-09 / C-01 | Disruption radar execute path | **ACCEPT+MODIFY — local fail-closed complete; provider work open** | `DETERMINISTIC_PREVIEW` capability guard now rejects execution with 403 before mutation/audit; strategic lifecycle regression and Ruff pass; real flight/booking provider, external reference, reconciliation, and hosted approval remain open |
| S-09 / C-01 | GDS/distribution sandbox and order routes | **ACCEPT+MODIFY — local preview truth complete; provider work open** | Search, booking preview, EDIFACT, NDC shopping/order, fare-penalty, and Cat35 routes emit reality metadata; synthetic PNR/e-ticket/charge/provider-confirmation fields are cleared; 11 focused tests pass; real provider submission and reconciliation remain open |
| S-09 / C-01 | FX sentinel and IROPS healer routes | **ACCEPT+MODIFY — local preview truth complete; provider/legal work open** | FX rates/exposure and IROPS recovery plans carry deterministic-preview metadata; missing-cost FX abstains; lock path is non-operative; VCC, legal compensation, rebooking, waiver, and supplier effects are cleared; 8 focused tests pass; provider/hosted/legal evidence remains open |
| S-09 / C-01 | Financial settlement and VCC routes | **ACCEPT+MODIFY — local arithmetic preview complete; financial/provider work open** | Currency conversion, FX quote, payment schedule, and commission routes return computed-preview envelopes; VCC route returns `NOT_ISSUED` with no credential-shaped fields; 9 focused tests pass; payment authorization, PCI, treasury, supplier, and durable-ledger evidence remain open |
| S-09 / C-01 | Duty-of-care cockpit route and panel | **ACCEPT+MODIFY — local preview truth complete; provider/operations work open** | Cockpit route returns preview metadata and marks beacon/STEP/dispatch/SOS states unverified/draft/not-sent; panel uses sample wording; 2 focused route/engine tests pass; threat feeds, trusted beacons, consular, dispatch, messaging, and operator evidence remain open |
| inventory-2026-09-02::F-03 / N-11 | Public proposal and Persona Council demo surfaces | **ACCEPT+MODIFY — local copy/state containment complete; persisted/provider work open** | Sample banner, non-persisted acceptance wording, preview pricing, demo IDs, simulation-labeled selectors, and sample-token copy are covered by 13 focused tests; canonical persisted proposal and authenticated provider actions remain open |
| S-09 / N-11 | Supplier directory and MRZ/document workbench surfaces | **ACCEPT+MODIFY — local sample/authenticity boundary complete; provider/document evidence open** | Supplier records and rate intake are explicitly sample/unavailable; MRZ checksum is format-only and failure clears stale output; 4 focused tests pass; canonical supplier contracts, OCR/authenticity, PII, and browser evidence remain open |
| F-06 | Audit-chain predecessor race | **ACCEPT+MODIFY — local continuity and verifier complete; anchoring and operational recovery open** | Read/hash/append now shares one cross-process lock with fsync; 32-writer regression, tamper/fork verifier, and full backend gate pass; external head anchoring, gap/replay handling, shared replicas, and restore remain open |
| R-11 / F-10 / NEW-07 | Agent lease liveness and fencing | **ACCEPT+MODIFY — local state-machine and route contract complete; integration open** | Manager and in-memory router are synchronized/explicit for expiry, release, fencing, validation, contention, and inspection; 11 focused tests and Ruff pass; SQL fencing, supervisor heartbeat wiring, pipeline-version stamps, agency scope, restart, multi-host evidence, auth integration, and fenced trip-write proof remain open |
| F-08 | Locking semantics and distributed mutual exclusion | **OPEN — audit complete; implementation deferred pending ownership** | 62 focused locking/startup tests pass, but they exercise only the process-local fallback; no production mutation invokes the lock, non-PostgreSQL strict boot is accepted, and transaction lifetime is untested. See [F-08 dossier](F08_LOCKING_SEMANTICS_AUDIT_2026-09-04.md); Add explicit strict-mode dialect policy, PostgreSQL two-session contention/transaction tests, canonical mutation wiring, fenced writes, and multi-worker evidence |
| F-07 | Poisoned queue inspection | **ACCEPT+MODIFY — durable service projection complete; API/replay open** | Canonical `RequeueJobStore.list_poisoned()` is deterministic, payload-free, bounded, and filterable; 34 PostgreSQL-backed queue tests pass and the isolated full runner is green (3,733/44). Agency scope, authenticated route, replay execution, purge/retention, audit, and hosted evidence remain open. See [F-07 dossier](F07_POISONED_QUEUE_INSPECTION_2026-09-04.md) |
| X-01..X-03, X-07, X-08 | Extraction prompt-injection, date/party, destination, homonym, and malformed-structured-input defects | **ACCEPT — local complete** | 7 safety tests + 318 extraction/trap regressions + 52 validation/NB01 regressions; adversarial records abstain or warn as designed |
| X-04..X-06, X-13 | Decision escalation, budget OR-group, blank blockers, and scenario-fixture correctness | **ACCEPT — local complete** | 146 focused tests; D6 live decision corpus 30/30 with 1.0 state/blocker/contradiction accuracy |
| X-09 | Production-vs-CI hybrid configuration parity | **ACCEPT+MODIFY — local truth/parity complete; release ratification open** | Serving/CI declare hybrid mode explicitly; D6 preserves caller mode, records effective configuration and deterministic authority axes; 59 focused tests and 30/30 provider-free parity run pass; model-quality/provider/owner gates remain open |
| X-12 / F-05 | Container build-context, digest, privilege, and stateful-service hardening | **PARTIAL — source contract complete; runtime build/scan/deploy open** | Digest pins, non-root layers, nested `.dockerignore`, internal Postgres/Redis ports, and 6 static tests pass; Docker daemon, image scanner, runtime, and hosted deployment evidence unavailable on this host |
| A-06 | Generated frontend API type drift | **ACCEPT+MODIFY — CI gate wired; clean-commit verification pending** | Backend-lint regenerates `frontend/src/types/generated/spine-api.ts` and fails on a diff; the intentionally dirty checkout makes HEAD comparison non-green, while generation is deterministic/idempotent |
| A-20 | Alembic model/migration drift | **ACCEPT+MODIFY — metadata ownership repaired; reconciliation remains open** | Registry now includes `AuditLog`/`TripRoutingState`, routing FK actions and PostgreSQL JSONB parity are explicit, and only raw `agent_requeue_jobs` is excluded; 34 focused tests pass. Read-only `alembic check` still reports 37 visible operations, so no migration or blocking CI gate was added. See [reconciliation dossier](A20_ALEMBIC_MODEL_MIGRATION_DRIFT_RECONCILIATION_2026-09-04.md) |
| D-01..D-03 | Trip duration, flight inclusiveness, and country/city destination contracts | **EXPLORE/DECIDE — current gaps executable; implementation intentionally gated** | 280 probes document current untyped/missing behavior and ratification-ready value-object/migration package; no new canonical fields were guessed |
| N-02 / N-03 | Independent extraction and pipeline evaluation producers | **ACCEPT+MODIFY — shadow probe complete; producer implementation open** | Three executable probes confirm missing raw-artifact provenance, empty live collectors, and disjoint expected/actual stage facts; no fixture mirror is promoted |
| X-14 / F-05 | Retention-enforcer wire-or-archive disposition | **ACCEPT+MODIFY — claims corrected; canonical wire open** | Prototype is explicitly `shadow` and non-erasing; 10 focused tests pass; durable cross-store inventory, legal holds, lifecycle anchors, provider purge, reconciliation, and recovery remain open |
| A-17 | WelcomeCard browser render | **PARTIAL — local visual evidence added; accessibility/hosted gates open** | Prior browser artifact was inspected; fresh unauthenticated recheck returns `/health` 200, `/metrics` 401, and frontend 200, so metrics reachability remains an LR-B09 auth/observability task; computed accessibility tree, keyboard/focus, screen-reader, contrast, and hosted/device evidence remain open |
| D-08 | Sibling panel sample treatment | **ACCEPT+MODIFY — local truth containment complete; browser/provider evidence open** | MemoryArchitectPanel, MemorySettingsTab, and CrisisEvacuationPanel expose sample/preview/not-dispatched states; focused D-08 coverage is included in 21 passing tests |
| D-09 | Repair deep-link and focus/auto-open | **ACCEPT+MODIFY — local route and authenticated browser contract complete; persistence/hosted evidence open** | Canonical `?repair=<field>` resolver handles machine names, async hydration, route updates, scroll anchoring, focus, and query cleanup; 41/41 lifecycle tests plus a 1280×900 authenticated BFF browser run prove one focused budget editor and URL cleanup; save/reload persistence, mobile/accessibility, hosted auth, and provider evidence remain open |
| D-10 | VCC BFF-relative routing | **ACCEPT — closed in-tree** | FinancialSettlementPanel uses the BFF-relative route and route-map proxy; historical PT-07/GF-05 defect retained as lineage |
| D-09 follow-up | Test-agency list auto-seed could 500 on a fixed trip ID hidden by RLS but globally present | **ACCEPT — local remediation complete** | `spine_api/server.py` skips only `trips.id` duplicate-key conflicts per fixture row and preserves unrelated integrity failures; 3 focused / 49 booking-data tests plus Ruff pass. Historical browser 500 remains recorded; post-fix browser response and hosted race evidence are open |
| Sandbox card shape | Variable-width decimal CVC/`last4` output | **ACCEPT — local complete** | CVC and `last4` now use bounded zero-padded decimal contracts; sandbox adapter suite 14/14; live Stripe contract is not claimed. See `Docs/review/SANDBOX_CARD_FIXED_WIDTH_CONTRACT_2026-09-04.md` |
| Cross-tenant ghost probe fixture | Synthetic agencies missing before FK insert | **ACCEPT — test corrected** | Probe now honors production FK and isolation contract; no schema weakening |
| Phase 1.3 landing/offline honesty | Fabricated operator metrics and offline success fallbacks | **ACCEPT — local complete** | Landing now uses capability claims; intake/offsites show explicit unavailable states; browser/copy review remains |

## Remaining implementation tasks (must be researched/implemented and then

verified at the matching evidence tier)

### Security, data, and provider boundaries

- **S-09:** rename or environment-gate Amadeus/Sabre/telephony/aviation,
  GDS/distribution, FX, IROPS, and duty-of-care adapters that are simulations;
  wire only after real OAuth/webhook contracts, trusted source provenance,
  idempotent order semantics, external references, reconciliation, and
  cost/failure semantics are documented.
- **S-11 / N-07 / LR-B07:** promote revocations and the run ledger to a shared
  PostgreSQL/ratified durable volume; prove restart, concurrent writers,
  multi-replica visibility, and recovery.
- **inventory-2026-09-02::F-03 / N-05:** the normal public proposal path now requires persisted,
  agency-bound trip/resource projection; the three demo tokens are gated by
  `PUBLIC_PROPOSAL_DEMO_MODE`, and startup rejects that mode in
  staging/production. Remaining work is shared revocation/issuance durability
  and correction of any remaining “live/issued/accepted” copy.
- **inventory-2026-09-02::F-03 / N-11:** remove remaining simulator identity/payload residue and
  preserve explicit simulated-data labels in all user-facing paths.
- **S-09 / C-01:** complete the remaining preview containment for VCC,
  financial conversion/quote, ghost-concierge, and any residual IROPS/duty-of-
  care client fallback; retain provider/legal/operator gates for real effects.
- **inventory-2026-09-02::F-05 / X-12:** finish image hardening with a version-pinned lock build,
  `.dockerignore` secret/data exclusions, non-root inspection, vulnerability
  scan, and measured startup/healthcheck evidence.
- **inventory-2026-09-02::F-04:** retain the historical split-commit proposal
  as decision history. The user's explicit all-path A1-1 delivery instruction
  controls the current delivery; do not turn the older proposal into another
  authorization veto or equate Git preservation with release readiness.
- **canonical::R-11 / canonical::F-10 / canonical::NEW-07:** extend the four
  existing isolated lease-router tests to actual server auth/agency boundaries,
  trace each route to a supervisor/worker fenced write, then choose
  one canonical SQL-versus-memory lease source and document migration/rollback.
- **LR-B08 / LR-B09:** keep `/ready` as the narrow unauthenticated,
  dependency-aware deployment probe (the pre-fix 401 is recorded in the linked
  dossier); the exact artifact-head comparison is now locally implemented;
  still prove bounded DB/Redis timeouts, dependency
  fault injection, restart/multi-replica behavior, and compose/Fly/Render
  receipts. Separately ratify the `/metrics` format, version source,
  low-cardinality labels, scrape authentication/private-network mechanism,
  privacy exclusions, and alert delivery before exposing it.

### Eval, decision, and extraction correctness

- **N-01 / X-04:** high-priority conflict escalation is fixed and the live
  decision corpus is 30/30; retain the pre-fix failures as regression lineage
  and continue independent-producer work before promotion.
- **N-02:** author runnable raw document inputs for the 50 extraction fixtures
  or explicitly replace that fixture contract; then add an independent
  document-vision collector.
- **N-03:** add deterministic independent producers for the seven pipeline
  fixtures and promote only with actual stage evidence.
- **E-06/E-07/E-08/E-10/E-11:** add trajectory/production shadow evaluation,
  calibrated judging, a red-team regression corpus, warning-capable gate
  format, and adversarial Hinglish/voice/emoji/mixed-language lanes.
- **X-10:** the audit confirms `checker_model` is declared, persisted, exposed
  by the settings API, and editable in the UI, but has no runtime consumer;
  the deterministic checker accepts no model/provider input. **Disposition:
  DEFER WIRE; RETAIN COMPATIBILITY; CORRECT CLAIMS BEFORE ACTIVATION.** The
  reserved round-trip contract is covered by 53 focused settings/gate tests.
  Remaining work is an owner-ratified router/provider registry, advisory
  proposal boundary, human-review/fallback/consent/spend controls, telemetry,
  golden/holdout/adversarial evaluation, and rollback evidence. See
  `Docs/review/X10_CHECKER_MODEL_WIRE_OR_REMOVE_2026-09-04.md`.
- **N-06 / X-11:** live SQL JSONB race and stale-owner fencing are now verified;
  see `Docs/review/IDEMPOTENCY_FENCING_N06_X11_2026-09-04.md`. Hosted/provider
  release evidence remains separate.
- **E-12 / E-1:** status-alias audit confirms `normalize_trip_status()` has no
  production callers and the persisted `Trip.status` axis is still freeform.
  The read-only distribution-report slice is now implemented and tested; the
  file-store receipt is 1,936 files with four explicit tokens, 138 missing-key
  records, and no malformed or explicit-null records in the current checkout.
  Telemetry-only
  normalizer reachability, alias expansion, strict enum/DB checks, and verified
  frontend active/archived semantics remain product-contract work. SQL reporting
  is no longer an unresolved zero-row observation: the repaired RLS/read-only
  reporter returned 21,937 rows for the explicitly selected test agency at
  2026-09-05T11:46:35Z. The old zero-row run remains historical; its cause was
  not independently reconstructed and is not established as an environment
  limitation. File and SQL scans cover different populations. See
  `Docs/exploration/E12_STATUS_ALIAS_EXPANSION_PLAN_2026-09-02.md`.

### Product contracts and frontend hardening

- **canonical::F-17 split:** recorded TimelinePanel test/lint repairs pass
  locally; production stale-response/race safety is not established. Remaining
  asynchronous React `act(...)` warnings, expected error-boundary console
  output, the non-boolean `fill` warning, and absent Vitest coverage thresholds
  remain **F-17/A-16** quality-policy work (`F-17b` was only a subscope label,
  not an independently registered finding). Do not close F-17 wholesale on the
  basis of test count alone.

- **D-01:** decide and implement the `trip_duration` contract across schema,
  extractor, API, and frontend.
- **D-02:** model `flights_inclusiveness` as a tri-state/ambiguous value with
  explicit user-facing resolution.
- **D-03:** define country-vs-city multi-destination semantics and committed
  versus semi-open sets.
- **D-04 / N-09:** the salutation/colon/label interplay probe is locally
  complete (274 focused extraction tests; GF-01/GF-03 reconciled closed).
  Keep country-vs-city semantics and repeated-currency budget ranges as
  separate contract work.
- **D-08/D-09:** local implementation is complete and covered by the focused
  contract suite. The test-agency seed collision observed during D-09 browser
  capture is remediated locally with per-row duplicate-key handling; repeat the
  authenticated browser list/seed check and verify save/reload persistence,
  mobile/accessibility, hosted, and provider evidence separately. **D-10 is already closed**: the VCC panel uses the canonical
  BFF-relative route and the route-map proxy; retain PT-07/GF-05 as historical
  lineage, not an open implementation task.
- **N-08:** harden Vitest timing under machine contention with bounded retries
  and evidence, not unbounded timeouts.
- **A-16/A-17:** establish coverage thresholds, browser E2E, keyboard/focus
  modal semantics, and mutation-sensitive tests.
- **Frontend lint backlog:** no warnings remain after behavior-sensitive fixes
  in audit, Workbench, IntakePanel, and the generated-type generator. Continue
  to avoid blanket-disabling `exhaustive-deps`.
- **Phase 3.1–3.3:** complete the simulated-label sweep, enforce generated-type
  drift, and prove frontend env/SSE/BFF contracts in a browser. The landing
  metrics and offline success fallbacks were removed in this wave; visual copy
  review is still required.

## Explore/research tasks (document before code)

- **A-02 / R-03:** compare semantic retrieval providers, lexical fallback,
  cost/latency, privacy, and benchmark methodology; rewrite the RAG document
  to match actual hash-vector/substring behavior until a provider is chosen.
- **C-02:** produce wire-or-archive ADRs for the hybrid engine, suitability
  scorer, ghost concierge, retention enforcer, yield modules, and every
  zero-caller subsystem.
- **C-03:** design a real runtime router only after independent eval ground
  truth exists; define ownership, fallback, budget, and telemetry contracts.
- **C-04:** execute the SLM/on-device benchmark protocol and analyze
  disagreement-rate, latency, privacy, and battery trade-offs.
- **C-05/C-06/R-05:** document the 19-agent runtime, lease ownership, and
  human-gated LLM wiring candidates as first-class architecture.
- **S-12:** retain FORCE-RLS positive probes in CI and add production-like
  migration/role coverage.
- **Provider research:** Amadeus/Sabre/NDC, Stripe Issuing, telephony/IVR,
  aviation/visa/MRZ, cancellation/empty-leg semantics, and data-quality SLAs.
- **Operational research:** IROPS/duty-of-care, group Pareto fairness,
  financial settlement/VCC, retention/privacy, backup topology, cost model,
  and Redis/Postgres failure modes.

## Decisions, records, and external gates

- **C-01/C-02:** ratify whether Frontier/Persona Council and each orphaned
  module is a labeled simulator to wire or an archived experiment.
- **inventory-2026-09-02::R-09/R-10:** decide signup verification posture and platform-led versus
  white-label business model before rewriting memory/business docs.
- **inventory-2026-09-02::R-01/R-02/R-04/R-06/R-07/R-08:** annotate simulator caveats, reconcile
  memory/RAG/seasonal docs, consolidate ADR/register numbering without
  deleting history, adopt personas into `Docs/personas/`, and refresh INDEX/
  idea-pad statuses through canonical tools.
- **D-07:** perform the manual banner visual check and preserve a screenshot
  with route/viewport evidence.
- **Operational docs:** create/maintain `LAUNCH_STATUS.md`, one known-issues
  ledger, and a detect→diagnose→contain→rollback→escalate runbook.
- **Legal/privacy:** obtain human review for traveler PII, retention, DPA/TOS,
  consent, simulated-data disclosures, and provider data processing.
- **Release/operator:** choose Fly or Render, configure real secrets/providers,
  webhook endpoints, backups, alerts, hosted worker assets, browser/device
  smoke, migration release, rollback, and restore drills.
- **Git:** classify the dirty tree semantically, refresh motto attestation,
  run full hooks/gates, then stage/commit/push only under a separate explicit
  authorization for that exact snapshot.

## Alignment verdict

The completed slices are first-principles aligned where they enforce a real
trust, lifecycle, or failure boundary (env-only secrets, canonical token
binding, truthful eval provenance, dependency-aware readiness, loop-safe pool
ownership, schema-honoring tests, and persisted proposal/resource binding).
They are long-term aligned where they
retain one canonical source and make unsupported capabilities fail closed.
They are intentionally **not launch-complete**: simulated providers, the
explicitly gated demo proposal seam, absent independent eval producers/holdouts, dirty
ownership, missing hosted/operator/legal evidence, and unresolved simulator
surfaces are known constraints, not hidden behind green local aggregates. The proposal demo
seam and local revocation cache are explicitly bounded rather than presented as
hosted production controls.

## Retry refresh — 2026-09-04

- Live ledger was re-scaffolded and revalidated in the final29 refresh after
  this documentation/test wave; path counts are recorded only after all
  current artifacts settle. Zero tracked deletions and no staging, commit,
  push, reset, checkout, stash, or cleanup are permitted in this wave.
- Focused security/price-lock retry:
  `PYTHONPATH=src .venv/bin/pytest -q tests/test_sandbox_provider_adapters.py
  tests/test_p1_findings_hardening.py` → **19 passed**.
- Focused tenant authorization retry:
  `PYTHONPATH=src .venv/bin/pytest -q tests/test_draft_promote_cross_tenant.py`
  → **2 passed**, including the metadata-only denial-audit assertion.
- Focused proposal resource-binding retry:
  `PROPOSAL_SIGNING_KEY=… .venv/bin/pytest -q tests/test_public_proposals.py
  tests/test_p1_findings_hardening.py tests/test_trust_scorecard_honesty.py
  tests/test_trust_scorecard_router.py tests/test_public_proposal_http.py` →
  **65 passed**.
- Startup demo-mode safety retry:
  `.venv/bin/pytest -q tests/test_startup_assertions.py
  tests/test_production_boot.py` → **49 passed**.
- Focused run-ledger durability retry: `pytest -q
  tests/test_run_ledger_durability.py tests/test_run_state_unit.py
  tests/test_journey_smoke.py` → **51 passed** across the durability/lifecycle
  slice.
- Focused yield contract retry: **21 passed** across panel and route-map
  contract tests; invented routes remain explicitly denied.
- UI lifecycle warning slice: stable modal/drawer escape callbacks and the
  quick-preset apply dependency; **10 focused tests passed**, reducing the
  frontend lint backlog from 16 to 13 warnings without suppressing the rule.
- Overview stale-count warning slice: `useOverviewSummary` now depends on the
  SSOT-derived `inboxCount` rather than raw `inbox.total`; the hook regression
  proves grouped enquiry counts refresh when unified state changes. **8 focused
  tests passed**, and the repository lint backlog is now **12 warnings**.
- RLS write-enforcement retry: rollback-only live PostgreSQL probe added for
  cross-tenant UPDATE/DELETE/WITH-CHECK rejection; **1 focused probe passed,
  20 combined live/mock RLS tests passed**, and `scripts/check_rls_coverage.py`
  reported 12 protected / 4 exempted tables. This is local/live-DB evidence,
  not hosted or production-role proof.
- Retrieval-honesty retry: canonical RAG modules and model contract now state
  the actual local hash-vector, substring-lexical, label-boost, and heuristic
  grounding semantics; **14 focused RAG tests passed** with Ruff and diff-check
  green. A real embedding provider, benchmark, and claim-level truth contract
  remain deliberately open.
- Workbench lint retry: explicit stable Zustand action dependencies and
  `draft_name` autosave dependency landed with **35 focused tests passing**;
  frontend typecheck now passes after repairing the `UnifiedState` test
  fixture. Repository lint is now **0 errors / 0 warnings** after the audit,
  IntakePanel, and generated-type surfaces were corrected.
- Simulator/provider truth audit: read-only review identified S0/S1 residuals
  in hardcoded bookings/suppliers/legacy proposal UI and backend disruption,
  crisis, GDS, VCC, IROPS, FX, and ghost-concierge routes. Crisis, GDS,
  disruption, FX, IROPS, and duty-of-care now have local preview/abstention
  boundaries; bookings, suppliers, proposal/persona copy, VCC, and
  ghost-concierge still require containment or provider evidence before launch.
- Crisis preview truth boundary: `crisis_ops.py` now returns explicit
  `PREVIEW_ONLY`/`DRAFT_NOT_TRANSMITTED` metadata, clears fabricated provider
  identities and operational writes, and passes **8 focused tests**.
- Bookings truth containment: bookings UI now presents sample/unverified rows,
  removes fabricated PNR/voucher/hold/live-GDS claims, and passes **2 focused
  tests** plus targeted typecheck/ESLint. Persisted tenant-bound bookings and
  provider reconciliation remain open.
- GDS/distribution truth containment: sandbox search, booking preview, EDIFACT,
  NDC shopping/order, fare-penalty, and Cat35 routes now emit canonical
  `PREVIEW_ONLY`/`COMPUTED_PREVIEW` reality metadata and clear synthetic PNR,
  e-ticket, charge, and provider-confirmation fields; **11 focused tests pass**.
  Provider connectivity, real order submission, and external-reference
  reconciliation remain open.
- FX/IROPS truth containment: deterministic FX rates/exposure and IROPS plans
  now carry preview metadata; missing-cost FX abstains and lock/rebooking/VCC/
  waiver/supplier effects are non-operative. **8 focused tests pass**; provider,
  hosted, legal, and reconciliation evidence remain open.
- IROPS/financial workbench containment: IROPS recovery renders only local
  candidate analysis, with compensation `Not assessed`, payment `Not issued`,
  and rerouting `Review only`; financial settlement performs arithmetic and
  timing previews without issuing cards, charging funds, or calling providers.
  **14 simulated-panel + 3 IROPS focused frontend tests pass**; browser,
  provider, PCI, and operator evidence remain open.
- Duty-of-care truth containment: cockpit and panel now label threat, beacon,
  STEP, dispatch, and SOS state as sample/unverified/draft/not-sent. **2 focused
  tests pass**; trusted feeds, consular, dispatch, messaging, and operator
  evidence remain open.
- Proposal/persona and suppliers/MRZ truth containment: public proposal and
  Persona Council copy is demo/preview-only; supplier records are sample and
  MRZ checksum is format-only with stale-output clearing. **13 + 4 focused
  frontend tests pass**; persisted/provider/OCR/authenticity evidence remains
  open.
- Frontend lint closure: generator header correction, AuditPage dependency
  stabilization, and IntakePanel dependency fixes reduce the repository to
  **0 errors / 0 warnings**; focused Audit tests **9/9** and Intake suites
  **38/38** pass.
- Canonical backend runner after proposal, ledger, startup, crisis, bookings,
  GDS/distribution, FX, IROPS, duty-of-care, financial-route, and fixture-seed
  collision hardening: latest isolated run **3,733 passed, 44 skipped, 0
  failed** in 382.49s with no `:8000` server detected; prior broader
  server-present run was **3,760 passed, 10 skipped, 0 failed** in 304.49s.
  The isolated run skips server-dependent integration paths, while the
  server-present run is broader but non-hermetic; eight known Python 3.13
  multiprocessing fork deprecation warnings remain.
- Audit-chain verifier retry: `PYTHONPATH=. .venv/bin/pytest -q
  tests/test_cryptographic_audit_ledger.py` → **3 passed**; the new
  read-only verifier detects modified details (hash mismatch) and changed
  predecessors (fork/predecessor mismatch). The full backend receipt above
  includes this regression.
- Findings checker invocation (canonical register plus declared historical
  companion): **183 rows — 108 open, 69 closed, 6 deferred; 0 warnings**.
- Full-repository Ruff remains green. `git diff --check` reports only the
  two preserved formatting residues recorded in the handoff (trailing
  Markdown spaces in the simulation chronicle and a blank EOF line in
  `tests/test_tax_compliance_sourcing.py`); these were not rewritten because
  the owning dirty slices remain semantically unclassified.

## Current retry receipt — 2026-09-04

- Latest isolated full backend gate (no server): `scripts/run_backend_tests.sh`
  → **3,733 passed, 44 skipped, 0 failed** in 382.49s; eight known Python 3.13 fork
  warnings. This run was more isolated but skipped server-dependent integration
  paths; the earlier broader server-present receipt remains in the chronology.
- Current retry regression tranche: currency-range, N-09/GF extraction,
  extraction safety/fixes, X-10 settings, feature-gate, and settings-router
  contracts → **331 passed** in 8.18s.
- Converged implementation tranche: container hardening, X-09 parity,
  D-01/D-02/D-03 probes, N-02/N-03 shadow producers, X-14 retention truth,
  sandbox-card formatting, D6 snapshot, and extraction regressions →
  **369 passed** in 8.72s.
- CI drift-gate retry: generated API type regeneration is deterministic and
  the blocking diff step is wired in `.github/workflows/ci.yml`; post-upgrade
  `alembic check` remains intentionally unwired after exposing real A-20
  schema deltas. See `Docs/review/CI_DRIFT_GATES_A06_A20_2026-09-04.md`.
- Fresh running-server probe before the readiness fix recorded `/ready` as
  401; focused post-fix ASGI tests now prove it reaches the readiness handler.
  The same probe recorded `GET http://127.0.0.1:8000/health` → 200,
  `GET http://127.0.0.1:8000/metrics` → 401 without credentials, and
  `GET http://127.0.0.1:3005` → 200. Define and verify the intended scrape
  authentication/internal-network contract before launch.
- Full frontend gate: `npm test -- --run` → **174 files / 1,311 tests passed**;
  `npm run lint` → **0 errors / 0 warnings**; `npm run typecheck` → pass;
  `npm run build` → pass. Build-time dynamic-route diagnostics for cookie,
  URL, and search-parameter access are expected for server routes and did not
  fail the build.
- Findings lifecycle: `python3 scripts/check_findings_register.py
  Docs/review/FINDINGS_REGISTER_2026-08-31.md
  Docs/review/FINDINGS_TASKS_CONSOLIDATED_2026-08-30.md` → **183 rows — 108
  open, 69 closed, 6 deferred; 0 warnings**.
- Custody: the latest validator covers the refreshed live-path set; all live
  paths are classified as preserved pending semantic ownership. See the
  final29 ledger entry and current custody section below (**521 live paths,
  522 porcelain rows including the ledger**).
- `git diff --check` retains only the documented owner-controlled residues in
  `MASTER_PRODUCT_DEMO_SIMULATION_CHRONICLE_2026-09-01.md` and
  `tests/test_tax_compliance_sourcing.py`; no unrelated formatting was
  rewritten.

## Task universe and first-principles alignment

The authoritative lifecycle checker covers **183 rows: 108 open, 69 closed,
and 6 deferred**. The complete ID-level source remains
`FINDINGS_REGISTER_2026-08-31.md` (current truth) plus the preserved historical
task companion `FINDINGS_TASKS_CONSOLIDATED_2026-08-30.md`. The open/partial
families are:

- **Canonical architecture, security, contracts, and operations:** R-09,
  R-10, R-12, R-13, R-14, R-16; A-02 through A-12 (excluding closed rows),
  A-15 through A-17, A-20; F-01 through F-17, F-19, F-21 through F-26; and
  NEW-01 through NEW-07.
- **Agentic/evaluation/product truth:** G-01 through G-06, G-12 through G-17,
  GM-01, GM-02, GM-05, GM-06, GM-08, GM-09, PT-08, GF-04, and
  REC-1. G-16 is explicitly deferred, not silently dropped.
- **Research/design candidates retained in the companion:** EX-01 (JDG/IROPS
  trigger), EX-02 (epistemic UI), EX-03 (retirement primitive), EX-05
  (negative-space capability map), EX-07/EX-08/EX-09/EX-10 (provider, capacity,
  evidence-dossier, and quarantine follow-ons), EX-11/EX-12/EX-13
  (veto-window, intent subscriptions, itinerary branching), and EX-14
  (`TemporalObligation`). NG-01 through NG-04 remain explicit no-go/deferred
  items until their prerequisites exist.
- **Current truth-containment slices implemented in this wave:** crisis,
  bookings, GDS/distribution, FX, IROPS, duty-of-care, proposal/persona,
  suppliers, and MRZ/document surfaces. Their local status is preview,
  sample, abstention, or format-only; their provider-backed, persisted,
  hosted, legal, and operator tasks remain open under S-09/C-01/F-03/N-11.
- **N-09/GF-01/GF-03 probe:** salutation/honorific exclusion, colon-budget
  connective, parenthetical city-set composition, explicit-label precedence,
  and trailing-season handling are locally verified (274 focused tests). GF-01
  and GF-03 are closed at this deterministic tier. Repeated-currency and
  shared-suffix ranges are now covered by a separate four-test regression;
  country-vs-city semantics remain separate contract work.

Alignment rule: a task is **first-principles/long-term/doctrine aligned** only
when the canonical path has a falsifiable contract, honest reality metadata,
an owner, durable state semantics, matching evidence tier, and a retirement or
recovery path. Local green tests promote an implementation slice; they do not
promote an unproven external effect to “complete.”

## 2026-09-05 retry continuation — newly filed F-30…F-40 and current counts

The live findings checker now reports **194 rows — 118 open, 70 closed, 6
deferred; 0 warnings**. The increase from the earlier 183-row receipt is
caused by the concurrent register addendum, not by silently changing prior
statuses. The newly filed open findings are:

- **F-30:** corporate-policy routes accept raw agency headers without JWT
  subject binding.
- **canonical::F-31:** deposit-based timing is now present; invalid/unknown
  evidence, plan-specific rules, unconditional eligibility and date/auth
  regressions remain. The current research package supersedes the older
  no-deposit-reading description and universal 14-day assumption.
- **F-32:** `price_lock_expires_at` is written at trip top-level but read from
  `strategy`, creating a split-brain sentinel.
- **F-33:** `active` and `archived` trips fall out of frontend operator views.
- **F-34:** approval writes `delivered` while the read model recognizes only
  `completed`.
- **F-35:** booked-revenue metrics count a status with no confirmed writer.
- **F-36:** feedback survey URL, ingestion trigger, and supplier scorecard are
  fabricated/unwired demo behavior.
- **F-37:** assumptions are neither populated nor serialized, while the UI
  synthesizes authoritative-looking fallback facts.
- **F-38:** `GET /alerts` fabricates a critical disruption per trip by default.
- **F-39:** webhook deduplication exists only in an uncalled production path.
- **F-40:** the frontend calls `/api/stats`, but no backend route is present;
  verify the source-of-truth contract before wiring or correcting it.

F-30 has a partial local remediation: both corporate-policy trip routes now
derive agency scope from `get_current_agency_id` and no longer read
`X-Agency-ID`/`TEST_AGENCY_ID` in handler code. Two hermetic source-contract
assertions plus Ruff/compile checks pass. The running TestClient gate could not
complete because the repository app lifespan hung in this environment, so
anonymous HTTP denial, cross-tenant runtime proof, authenticated principal
binding, and hosted/RLS evidence remain open. See
`Docs/review/F30_CORPORATE_POLICY_AUTH_BOUNDARY_2026-09-05.md`.

These rows are now part of the authoritative register and must be sequenced
with the existing F-03, E-1/E-12, feedback, disruption, and frontend contract
work. Each is explicitly open; none is promoted by the existence of a test or
simulation-shaped module.

## Source and evidence pointers

- `Docs/review/A1_1_WORKTREE_CLASSIFICATION_CLOSURE_2026-09-03.md` — custody,
  final local receipts, and 2026-09-04 execution addendum.
- `Docs/review/PROPOSAL_TOKEN_SECURITY_ADDENDUM_2026-09-03.md` — token and
  revocation contract/boundaries.
- `Docs/review/PROPOSAL_RESOURCE_BINDING_N05_F03_2026-09-04.md` — both public
  proposal issuance/read paths, fail-closed projection, and demo seam.
- `Docs/review/S11_N07_LRB07_LOCAL_DURABILITY_2026-09-04.md` — crash-safe
  run-ledger/event persistence and the durable-volume/PostgreSQL boundary.
- `Docs/review/YIELD_CONTRACT_N04_2026-09-04.md` and
  `Docs/review/N04_YIELD_ARBITRAGE_CONTRACT_REPAIR_2026-09-04.md` — canonical
  yield API/BFF wiring and negative invented-route evidence.
- `Docs/review/PRODUCT_CONTRACT_DECISIONS_D01_D03_2026-09-04.md` — observed
  duration, flight-inclusiveness, and destination-scope ambiguity with a
  ratification-ready canonical contract.
- `Docs/review/EVAL_GATES_E01_E05_2026-09-03.md` — evaluator provenance,
  shadow lanes, 30-scenario and holdout boundaries.
- `Docs/review/S12_RLS_WRITE_PROBE_2026-09-04.md` — live rollback-only RLS
  write-side evidence and remaining role/deployment boundary.
- `Docs/review/RAG_RETRIEVAL_HONESTY_A02_R03_2026-09-04.md` — corrected
  retrieval/grounding claims, focused tests, and provider-research boundary.
- `Docs/review/DEPLOYMENT_LAUNCH_ENVELOPE_2026-09-03.md` — readiness,
  migration, container, topology, and operator gates.
- `Docs/exploration/MASTER_FINDINGS_TASKS_INVENTORY_2026-09-02.md` — complete
  discovery history, IDs, source links, and prior sequencing decisions.
- `Docs/review/FINDINGS_REGISTER_2026-08-31.md` — authoritative lifecycle
  register; A-02/G-04 now record the local retrieval-claim correction while
  leaving provider/benchmark implementation explicitly open.
- `Docs/LAUNCH_STATUS.md` and `Docs/review/KNOWN_ISSUES_LEDGER_2026-09-04.md`
  — canonical launch decision and operator-facing unresolved-risk ledger.
- `Docs/review/SIMULATOR_PROVIDER_TRUTH_AUDIT_2026-09-04.md` — line-level
  S0/S1 evidence for hardcoded public/agency state and backend operational
  statuses without provider evidence.
- `Docs/review/INDEPENDENT_EVAL_PRODUCERS_N02_N03_2026-09-04.md` — fixture
  contract audit explaining why raw documents and deterministic stage
  producers are required before promotion.
- `Docs/review/DISRUPTION_PREVIEW_FAIL_CLOSED_2026-09-04.md` — fail-closed
  disruption execution and provider-evidence boundary.
- `Docs/review/CRISIS_ROUTER_PREVIEW_TRUTH_BOUNDARY_2026-09-04.md` — crisis,
  STEP, ground-dispatch, and safety-beacon preview-only contract.
- `Docs/review/BOOKINGS_TRUTH_CONTAINMENT_2026-09-04.md` — bookings sample
  containment, unavailable provider state, and local document-preview limits.
- `Docs/review/GDS_DISTRIBUTION_PREVIEW_TRUTH_BOUNDARY_2026-09-04.md` — GDS,
  EDIFACT, NDC, fare-rule, and markup preview-only response contract;
  synthetic PNR/e-ticket/charge/confirmation fields are cleared locally.
- `Docs/review/FX_IROPS_PREVIEW_TRUTH_BOUNDARY_2026-09-04.md` — deterministic
  FX and IROPS routes now abstain or return preview-only plans without lock,
  payment, legal, rebooking, waiver, or supplier effects.
- `Docs/review/DUTY_OF_CARE_PREVIEW_TRUTH_BOUNDARY_2026-09-04.md` — duty-of-
  care cockpit and panel preview contract for threat, beacon, STEP, dispatch,
  and SOS fixtures.
- `Docs/review/PROPOSAL_PERSONA_TRUTH_BOUNDARY_2026-09-04.md` — public proposal
  and Persona Council sample-state and simulation-copy containment.
- `Docs/review/SUPPLIERS_MRZ_FRONTEND_TRUTH_CONTAINMENT_2026-09-04.md` —
  supplier records and MRZ/document format-only boundary.
- `Docs/review/AUDIT_CHAIN_CONCURRENCY_F06_2026-09-04.md` — local audit-chain
  concurrency root cause, fix, regression, and remaining anchoring boundary.

## A-17 Welcome surface semantics — 2026-09-04

**Decision:** `ACCEPT+MODIFY — local semantic correction complete; browser and
full accessibility evidence remain open.`

`WelcomeModal` was named as a modal but its live behavior was intentionally a
non-blocking fixed card: it did not trap focus, lock body scrolling, dismiss on
Escape, or prevent interaction with the underlying route. Adding
`role="dialog"`/`aria-modal="true"` without those modal invariants would have
misrepresented the interaction contract and could have made keyboard and
screen-reader navigation worse.

The implementation therefore keeps the non-blocking onboarding UX and makes
the semantics explicit:

- the implementation is now `WelcomeCard`; the historical `WelcomeModal`
  export remains as a compatibility alias for `AuthProvider`;
- both responsive render branches expose a labelled `role="region"` with
  `aria-labelledby` and `aria-describedby` tied to the visible heading and
  description;
- the card has a stable `data-testid` for contract tests;
- no false dialog semantics, focus trap, scroll lock, or unsupported Escape
  behavior was added;
- the existing dismiss and navigation buttons remain native keyboard-reachable
  controls, with an Enter-key dismissal regression test.

Focused evidence from `frontend/`:

```text
pnpm exec vitest run \
  'src/components/onboarding/__tests__/WelcomeModal.test.tsx'
  Test Files  1 passed (1)
  Tests       6 passed (6)

pnpm exec eslint \
  'src/components/onboarding/WelcomeModal.tsx' \
  'src/components/onboarding/__tests__/WelcomeModal.test.tsx'
  passed with no diagnostics

pnpm exec tsc -p tsconfig.json --noEmit
  passed
```

This is Tier 2 / S1 evidence for the local semantic and keyboard contract. It
does not prove visual contrast, responsive reflow, screen-reader output,
focus order in a real browser, or a complete authenticated onboarding journey.
Those remain part of the broader A-16/A-17 browser and accessibility gate.
