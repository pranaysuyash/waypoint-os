# Waypoint OS Evidence Architect repository audit addendum

**Date:** 2026-08-31
**Status:** current-checkout audit addendum; not a replacement for the canonical findings register
**Lead persona:** `PER-0923 — Evidence Architect`
**Persona source:** `/Users/pranay/Desktop/Understanding_Personas_29aug26/01 Expanded Personas/14 Meta-Reasoning & Decision Systems/PER-0923 - Evidence Architect.docx`
**Canonical task owners:** `Docs/review/FINDINGS_REGISTER_2026-08-29.md`, `Docs/review/FINDINGS_TASKS_CONSOLIDATED_2026-08-30.md`, `Docs/review/EXPLORATION_RESEARCH_BACKLOG_2026-08-29.md`, and `Docs/review/IMPLEMENTATION_PLAN_2026-08-29.md`
**Freshness trigger:** re-audit after the current dirty work is reconciled, after any canonical-path retirement wave, or before launch/readiness claims

## 1. Decision and scope

### User intent preserved from the current conversation

Use a persona from the Understanding Personas repository to:

1. audit the live repository and document the evidence;
2. list every explicit and implicit finding or task that should be researched,
   documented, decided, implemented, verified, or deliberately deferred;
3. judge whether those tasks are first-principles, long-term, and doctrine
   aligned;
4. identify what can be improved or added to make the product and engineering
   system materially better; and
5. turn the result into an implementation plan.

This request authorizes documentation work. It does not authorize Git mutation,
deployment, provider calls, production changes, secret rotation, payment actions,
or destructive cleanup.

### Scope

Included:

- live repository structure, status, code, contracts, tests, documentation, and
  planning surfaces;
- current explicit findings `R-01..R-16` and `A-01..A-23`;
- consolidated implicit findings and tasks `F-01..F-19`;
- research questions `RQ-01..RQ-06`, explorations `EX-01..EX-14`, doctrine
  candidates `D-01..D-05`, and no-go decisions `NG-01..NG-04`;
- product, business, user, architecture, agentic-workflow, security, privacy,
  accessibility, reliability, operations, evidence, and launch implications;
- first-principles, long-term, and doctrine alignment.

Excluded:

- application-code implementation;
- live browser/product proof;
- full test-suite re-execution;
- external market, regulatory, competitor, supplier, or provider research;
- production readiness or legal-compliance certification.

## 2. Why `PER-0923 — Evidence Architect`

The persona's core question is: what evidence justifies a claim or decision,
where does it come from, and can another reviewer reproduce the reasoning?
Its responsibilities include source hierarchy, provenance, claim-evidence
linkage, freshness, contradiction handling, missing-evidence signals, and audit
trails. Those are the load-bearing needs of this task.

The persona does not replace doctrine. Review, Exploration, Research,
Architecture, Testing, Security/Privacy/Safety, Release Readiness,
Documentation, and Inquiry/Analysis doctrines retain method and authority.

The operational Persona Council router returned `PER-0923` as a council seed and
also surfaced Agent Reliability Engineer, Acceptance Tester, Accessibility &
Inclusive Design Specialist, and Agent Workforce Architect. Their domains are
retained as audit dimensions, not silently treated as additional lead personas.

## 3. Truth model and evidence limits

| Label | Meaning in this document |
|---|---|
| Observed / T1 | Read in the current file tree or command output |
| Verified / T2 | Focused deterministic check executed in this audit |
| Verified / T3 | Integration or end-to-end check executed in this audit |
| Inferred | Best explanation supported by current evidence; falsifier named |
| Proposed | Design or task not yet implemented or verified |
| Unknown | Exact proving check remains open |

This audit contains T1 and focused T2 evidence. It does not contain fresh T3,
browser, deployed, provider, real-customer, market, legal, or production proof.
Historical test results in existing documents remain historical evidence until
re-run against the current checkout.

## 4. Live checkout and command evidence

### 4.1 Working-state observation

`git status --short --branch` reported `master...origin/master`, 31 modified
tracked files, one staged documentation file, and many untracked code, test,
data, build-cache, and documentation artifacts. The dirty changes span intake,
privacy, persistence, analytics, agent execution, frontend workbench copy,
fixtures, migrations, and audit docs.

Consequences:

- the current checkout contains concurrent work and cannot be treated as a clean
  baseline;
- this addendum does not edit the already-modified findings register,
  consolidated task register, implementation plan, or documentation index;
- implementation owners must re-read every target immediately before editing;
- no task whose evidence depends on the dirty files should be called closed
  until the intended diff is classified and freshly verified.

### 4.2 Reproducible command ledger

| Command / inspection | Outcome | Evidence tier |
|---|---|---:|
| `git status --short --branch` | dirty concurrent checkout; application, tests, data, docs, and build artifacts all represented | T1 |
| `git worktree list --porcelain` | one listed worktree at this project root, `master`, HEAD `8ece02e...` | T1 |
| `git diff --stat` | 31 unstaged tracked files, 1,097 insertions and 217 deletions | T1 |
| `git diff --cached --stat` | `Docs/reviews/motto_review.md`, one-line staged change | T1 |
| operational Persona Council router | selected Level 1 council and a seven-person panel; `PER-0923` chosen for this audit | T2, deterministic routing trace |
| `textutil -convert txt -stdout <PER-0923.docx>` | canonical persona text inspected from the Desktop snapshot | T1 |
| `python3 tools/architecture_route_inventory.py --format md` | 297 backend routes, 64 router modules, 95 BFF mappings, 0 unmatched mapped backend paths, 17 routes still in `server.py` | T2, static deterministic inventory |
| `frontend/package.json` inspection | Next `^14.2.20`, React `^18.3.1`, `eslint-config-next ^16.2.4` | T1 |
| production-source `fetch(` count | 105 matches outside test paths | T1, lexical upper bound |
| product-source debt-marker count | 8 `TODO/FIXME/HACK/XXX` matches outside test paths | T1, lexical lower bound |
| `find Docs frontend/docs -type f` | 3,176 files; 2,950 Markdown files | T1 |
| task-ID extraction across canonical registers | 88 distinct IDs across R/A/F/RQ/EX/D/NG families | T2, lexical coverage check |

### 4.3 Evidence contradictions and drift

1. **Frontend-version contradiction.** `README.md` says Next.js 16 and React 19;
   the live manifest declares Next.js 14 and React 18, while only the Next ESLint
   configuration is 16.x. This is confirmed drift, not a stylistic disagreement.
2. **Documentation counts drift.** Earlier audit counts are snapshots. The live
   tree now contains 3,176 files across `Docs/` and `frontend/docs/`, including
   2,950 Markdown files. Counts must carry a date and command.
3. **Test results are historical.** Existing docs cite clean and failing baselines
   under different environment and server-contention conditions. No result is
   promoted to current truth in this addendum.
4. **Generated context retrieval timed out.** The 2026-08-31 session context is
   current by timestamp, but all project/shared retrieval sections reported busy
   or timed out. Direct live inspection was therefore required.

## 5. System-level verdict

Waypoint OS has a strong conceptual core: canonical trip intake, explicit
uncertainty primitives, tenant-aware persistence, reality/connectivity concepts,
operator review, traveler-safe separation, auditability, and a broad travel
operations model. Its largest risk is not lack of capability. It is **unclosed
breadth**:

- routes exist without explicit consumer/reachability classification;
- replacements coexist with legacy paths;
- simulation, mock, sandbox, and live behavior are incompletely unified;
- documentation and ADRs proliferate faster than retirement and freshness;
- evidence is generated, but not always promoted through a canonical lifecycle;
- launch-shaped interfaces are ahead of real provider, fulfillment, payment,
  regulatory, accessibility, and operator evidence.

The first-principles direction is mostly sound. The long-term implementation
system is not yet sound because it lacks enforceable completion conditions for
canonicalization, reachability, retirement, evidence freshness, and real-world
adoption.

## 6. Alignment rubric

Every task is judged against three separate questions:

1. **First principles (FP):** does the task protect a real user/business outcome,
   truth boundary, invariant, failure mode, or decision need rather than merely
   polish an implementation?
2. **Long term (LT):** does it reduce duplicate ownership, scale safely, expose
   operations, support migration/rollback, and avoid an unowned parallel path?
3. **Doctrine (DOC):** does it preserve canonical ownership, evidence status,
   authorization, security/privacy boundaries, verification, and durable
   history?

Ratings: `YES`, `CONDITIONAL`, `NO-AS-WRITTEN`, `CLOSED/RETAIN`, or
`DEFERRED-CORRECTLY`.

## 7. Exhaustive finding and task alignment matrix

### 7.1 Original refactor findings `R-01..R-16`

| IDs | Current disposition | FP | LT | DOC | Required correction or continuation |
|---|---|---|---|---|---|
| R-01, R-02, R-04, R-05, R-07 | fixes reported in existing ledgers | CLOSED/RETAIN | CONDITIONAL | CONDITIONAL | Re-verify against the classified current diff; retain regression and canonical-owner evidence. |
| R-03 | original split-brain premise corrected; narrower pagination/RLS/token issues remain | CLOSED/RETAIN | YES | YES | Preserve the self-correction. Continue A-22/A-23 rather than resurrecting the false P0 claim. |
| R-06 | reality/connectivity/epistemic boundary | YES | CONDITIONAL | YES | Implement one authoritative capability/reality contract, not flags in each adapter. Require visible user/operator states and provider-backed proof before `LIVE`. |
| R-08, R-09 | documentation and canonical-source defects | YES | YES | YES | Fold into EA-01 documentation control plane; never bulk-delete historical docs. |
| R-10 | server decomposition and single audit owner | YES | YES | YES | Use `create_app()` and modular routers within one deployable service first. Require contract parity and migration steps; no premature microservice split. |
| R-11 | durable agent lease | YES | YES | YES | Add heartbeat, fencing, scope, version compatibility, stale sweep, idempotency, observability, and recovery tests as one lease contract. |
| R-12 | journey graph IROPS reachability | CONDITIONAL | CONDITIONAL | YES | Do not build another graph. Establish real disruption source, segment distribution, and trigger ROI before wiring the existing canonical graph. |
| R-13 | navigation rollout truth | YES | YES | YES | Product owner must decide availability. Generate nav status from one capability registry and verify visible behavior. |
| R-14 | styling unification | CONDITIONAL | YES | YES | Proceed only through the existing design-system plan with a visual baseline, accessibility checks, and component retirement. |
| R-15 | PII guard posture | YES | CONDITIONAL | CONDITIONAL | Current dirty implementation is a useful posture matrix, but long-term protection also requires data inventory, encryption boundary, retention/DSAR, egress, and failure telemetry. |
| R-16 | trace correlation | YES | YES | YES | Trace ID existence is insufficient. Add a consumer, cross-layer journey assertion, retention/privacy rules, and operator investigation path. |

### 7.2 Audit findings `A-01..A-23`

| IDs | Current disposition | FP | LT | DOC | Required correction or continuation |
|---|---|---|---|---|---|
| A-01 | honest quality gate reported resolved | CLOSED/RETAIN | YES | YES | Preserve live producer wiring, failure semantics, and S3 mutation proof. |
| A-02 | hash-vector RAG | YES | YES | YES | Do not replace it merely for semantic fashion. Define retrieval use cases and gold set; compare lexical, hybrid, and semantic systems on relevance, latency, cost, privacy, and abstention. |
| A-03 | mock agent tools | YES | YES | YES | Resolve through R-06 capability tiers. Mock modes remain valid for tests/demos only when visibly labeled and fail-loud outside their envelope. |
| A-04 | duplicate backend systems | YES | YES | YES | Inventory unique behavior, designate owners, migrate callers, prove parity, then retire. A single sweeping deletion is not aligned. |
| A-05 | frontend API-client fragmentation | YES | YES | YES | Classify 105 lexical `fetch` matches, preserve streaming/special cases, migrate to one typed client, then enforce the boundary. |
| A-06 | stale generated contract | YES | YES | YES | Generate from the authoritative OpenAPI contract, diff in CI, version breaking changes, and test actual FE/BE responses. |
| A-07 | doc-tree consolidation | YES | YES | YES | Use EA-01 inventory, canonical map, redirects/supersession, and archive policy. Preserve history. |
| A-08 | dangling motto references | YES | YES | YES | Repair exact references and add a scoped link/reference checker; do not rewrite doctrine history. |
| A-09 | ADR supersession | YES | YES | YES | Add stable IDs/status/supersession/revisit triggers. Renumbering is lower value than preserving stable references. |
| A-10 | idea-pad reconciliation | CONDITIONAL | YES | YES | Reconcile only through the canonical idea-pad tool and explicit lifecycle; product code remains source evidence, not automatic status authority. |
| A-11 | multiple marketing generations | YES | YES | YES | First identify the intended public route and preserve unique content/experiments. Retire by redirect/archive with analytics and rollback, not deletion by version number. |
| A-12 | inert proxy/version skew | YES | YES | YES | Resolve framework version first, then choose the supported auth boundary. Add an integration test that proves protected navigation, not only file existence. |
| A-13 | test baseline | CLOSED/RETAIN | YES | YES | Keep the canonical runner and environment isolation. Do not reuse old counts as current evidence. |
| A-14 | uncommitted remediation | CONDITIONAL | NO-AS-WRITTEN | CONDITIONAL | “Commit one atomic unit” is not automatically architecturally correct and is not authorized here. First classify mixed ownership and split coherent changes; preserve all work. |
| A-15 | frontend debt | YES | CONDITIONAL | YES | Do not optimize for zero markers or zero `any`. Prioritize unsafe boundary casts, large volatile components, and unowned disables with behavior tests. |
| A-16 | coverage/e2e | YES | CONDITIONAL | YES | Ratchet meaningful risk-based coverage; do not chase an arbitrary percentage. Add critical operator and traveler flows with failure/recovery cases. |
| A-17 | modal accessibility | YES | YES | YES | Use the canonical modal/dialog primitive or deliberately rename/re-specify the component; verify keyboard, screen reader semantics, zoom/reflow, and reduced motion. |
| A-18 | secrets/auth posture | YES | YES | YES | Rotation is an external credential action requiring a separate gate. Code work should remove unsafe defaults, enforce environment policy, scan history, and document recovery. |
| A-19 | RLS coverage reported resolved | CLOSED/RETAIN | YES | YES | Retain per-route authority tests and S3 cross-tenant probes. Recheck new routers automatically. |
| A-20 | migration drift | YES | YES | YES | Keep additive migration, add `alembic check`, boot-time revision visibility, rollback/runbook, and production-like migration proof. |
| A-21 | parallel ownership | YES | YES | YES | Assign owners and refresh status. Do not turn an inventory into a second scheduler. |
| A-22 | public token lookup authority | YES | YES | YES | Design a capability-scoped lookup using hashed, expiring, revocable tokens and explicit agency binding; never disable RLS globally for convenience. |
| A-23 | token data hidden in `_extra` | YES | YES | YES | Promote durable access/lookup fields into an owned schema or separate token table; migrate and verify all projections. Avoid adding more magic extras. |

### 7.3 Implicit findings `F-01..F-19`

| IDs | FP | LT | DOC | Required correction or continuation |
|---|---|---|---|---|
| F-01 | YES | YES | YES | Model price-lock change as an idempotent, versioned state transition with immutable financial facts and compensating actions. “Undo” must not erase history. |
| F-02 | YES | YES | YES | Consolidate public-link security across proposals and collections: scoped token table, TTL, revocation, single-use/limited-use policy, consent, rate limit, minimization, audit, and abuse monitoring. |
| F-03 | YES | YES | YES | Bind approvals to authenticated actor, role/capability, artifact version/hash, decision reason, time, and revocation/override history. |
| F-04 | YES | YES | YES | A mandate ledger is necessary but not sufficient: include jurisdiction/provider authorization, amount/currency, beneficiary, refunds, disputes, reconciliation, and least-privilege execution. |
| F-05 | YES | YES | YES | Build a data-inventory-driven retention/DSAR system with legal-hold exceptions, deletion receipts, backups, derived data, audit tombstones, and operator runbooks. Do not promise regulatory compliance from code alone. |
| F-06 | YES | CONDITIONAL | YES | First select one audit owner. Add sequence/fork verification, writer identity, signature/key lifecycle, and coverage. External anchoring is conditional on threat model and operating cost. |
| F-07 | YES | YES | YES | Quarantine must preserve payload safety, reason taxonomy, retry budget, idempotency, redaction, role-gated replay, and terminal disposition. |
| F-08 | YES | YES | YES | Fail-fast when distributed exclusion is required. Also expose the active locking mode and test each supported deployment profile. |
| F-09 | YES | CONDITIONAL | YES | Do not make indefinite dual-write the target. Choose SQL as canonical checkpoint state, make file output diagnostic/export-only, migrate, compare, and retire. |
| F-10 | YES | YES | YES | Version fence must include code/build, prompt, schema, policy, and capability compatibility. Define safe resume, migrate, restart, and terminal failure rules. |
| F-11 | YES | YES | YES | Add hierarchical budgets, reservation/commit/release, per-tenant circuit breaker, alerting, recovery, and accepted-output cost metrics. Human override must be audited. |
| F-12 | YES | YES | YES | Add authenticated per-tenant connection and event budgets, heartbeat, cursor replay, backpressure, eviction, privacy-safe retention, and reconnect tests. |
| F-13 | YES | YES | YES | Use provenance and purpose-bound memory, verification status, confidence/decay, sensitive-category rules, correction/forgetting, retrieval quarantine, and user visibility. |
| F-14 | YES | CONDITIONAL | YES | Prefer EX-14’s generic temporal-obligation primitive if a bounded design proves common semantics; keep domain-specific policies and avoid a universal timer god-object. |
| F-15 | YES | YES | YES | Use a versioned supplier-confirmation exception taxonomy, source evidence, retry eligibility, human claim lane, and provider-specific mappings. |
| F-16 | YES | CONDITIONAL | YES | “Reverse logistics” is a useful analogy, not the domain model. Use travel-native refund, exchange, reissue, credit, chargeback, compensation, and write-off dispositions. |
| F-17 | YES | YES | YES | Fix async-test race, eliminate unhandled errors, clear rule violations, then ratchet. Require tests to fail for the defect where practical. |
| F-18 | CLOSED/RETAIN | YES | YES | Preserve the falsifier, gold fixtures, decision D1/D2 status, and regression traps. Unratified product decisions remain visibly provisional. |
| F-19 | YES | YES | YES | Isolate integration databases/services by run or worker and define explicit test profiles. Default-excluding integration tests is only aligned if a required integration lane still runs. |

### 7.4 Research questions `RQ-01..RQ-06`

| IDs | Disposition | Alignment judgment |
|---|---|---|
| RQ-01, RQ-03, RQ-06 | CLOSED/RETAIN | First-principles and doctrine aligned because each had an exit criterion and produced a concrete disposition. Reopen only on its stated trigger. |
| RQ-02, RQ-04 | CLOSED/RETAIN | Preserve the corrected history and reference hygiene. Do not re-litigate without new evidence. |
| RQ-05 | MERGED | Continue under A-12. The real question is the supported framework/auth boundary plus runtime reachability. |

### 7.5 Explorations `EX-01..EX-14`

| IDs | FP | LT | DOC | Go/no-go condition |
|---|---|---|---|---|
| EX-01 | CONDITIONAL | YES | YES | Real disruption source and multi-segment frequency justify the existing JDG trigger. |
| EX-02 | YES | YES | YES | Operator research proves that uncertainty states improve decisions without overload; accessibility included. |
| EX-03 | YES | YES | YES | Implement as a repository lifecycle contract, not a new product microservice. |
| EX-04 | YES | YES | YES | Merge with R-06 and the existing connectivity design; no second tier taxonomy. |
| EX-05 | YES | YES | YES | Every absent capability classified as deliberate, external dependency, future research, or launch blocker with owner/revisit trigger. |
| EX-06 | CLOSED/RETAIN | YES | YES | Wire the existing lifecycle checker into the canonical gate only after current ownership is reconciled. |
| EX-07 | CONDITIONAL | CONDITIONAL | YES | Real supplier/GDS need, licensing/test fixtures, connectivity tier, and canonical document-ingestion path established. |
| EX-08 | CONDITIONAL | CONDITIONAL | YES | Measured queue/SLA pressure proves capacity planning is a current constraint. |
| EX-09 | YES | YES | YES | Build after epistemic and audit-chain ownership; include reproducible inputs, policy versions, redaction, and access controls. |
| EX-10 | CONDITIONAL | YES | YES | F-07 basic quarantine lane demonstrates enough volume and operator value to justify automation. |
| EX-11 | CONDITIONAL | CONDITIONAL | YES | Agency-specific, opt-in risk policy with bounded capability, refundability, veto timing, rollback, and outcome evaluation. Never replace mandatory approvals. |
| EX-12 | CONDITIONAL | CONDITIONAL | YES | Customer research establishes repeated planning intent and acceptable privacy/notification burden. |
| EX-13 | CONDITIONAL | CONDITIONAL | YES | User research proves collaborative branch/merge semantics are understandable and more useful than simpler alternatives. |
| EX-14 | YES | CONDITIONAL | YES | Design a small obligation contract and prove shared semantics across at least three current deadline families before implementation. |

### 7.6 Doctrine candidates `D-01..D-05`

| ID | Alignment judgment | Required treatment |
|---|---|---|
| D-01 | YES | Absence claims require search scope and executed evidence. Promote only through doctrine review. |
| D-02 | YES | Finding lifecycle is necessary; keep canonical owner and transition evidence. |
| D-03 | YES | Generated-mirror placement/provenance guard is aligned and testable. |
| D-04 | CONDITIONAL | Re-home active dependents before retirement, but do not prohibit justified deletion forever. Preserve history and canonical pointers. |
| D-05 | YES | Completion claims should cite current verification command, date, result, tier, and residual limits. |

These are proposals only. This audit does not authorize or perform canonical
doctrine edits.

### 7.7 No-go decisions `NG-01..NG-04`

| IDs | Disposition | Alignment judgment |
|---|---|---|
| NG-01 | DEFERRED-CORRECTLY | An event-log-as-SSOT rewrite is disproportionate until canonical SQL/checkpoint ownership proves insufficient. |
| NG-02 | DEFERRED-CORRECTLY | No supplier-side negotiation endpoint before real connectivity and counterparty contracts. |
| NG-03 | DEFERRED-CORRECTLY | No autonomous JIT ticketing without issuance/PNR authority, provider proof, and recovery. |
| NG-04 | DEFERRED-CORRECTLY | No programmable RFQ rounds without a real supplier channel, identity, consent, and commercial operating model. |

## 8. Newly surfaced evidence findings and tasks

These additions are not yet incorporated into the canonical findings register.
They should be reconciled there by its current owner after the dirty shared
documents stabilize.

### EA-01 — Documentation control plane is itself a product reliability risk

- **Truth:** Observed, T1.
- **Evidence:** 3,176 files across `Docs/` and `frontend/docs/`; 2,950 are
  Markdown. Multiple master/canonical/roadmap/audit documents coexist. The
  current README and dependency manifest disagree.
- **Risk:** operators and agents retrieve stale plans, duplicate work, and make
  invalid framework assumptions.
- **Task:** build a generated documentation inventory with stable document ID,
  knowledge type, canonical owner, status, supersedes/superseded-by, evidence
  date, freshness trigger, and backlinks. Emit contradiction and orphan reports.
- **FP/LT/DOC:** YES / YES / YES.
- **Keep if:** a reviewer can find the current architecture, finding, decision,
  and implementation owner in a few searches, and seeded contradictions fail CI.
- **Revert if:** it becomes a second editable catalog or requires rewriting every
  historical document before producing value.

### EA-02 — README frontend generation is false

- **Truth:** Verified by manifest inspection, T2.
- **Evidence:** README says Next 16/React 19; package manifest says Next
  `^14.2.20`, React `^18.3.1`, with `eslint-config-next ^16.2.4`.
- **Task:** decide and execute one supported dependency generation. Until then,
  correct the README to the live manifest and flag the lint/runtime skew. Add a
  doc-manifest consistency check for declared major versions.
- **FP/LT/DOC:** YES / YES / YES.
- **Falsifier:** lockfile resolves a different supported generation and current
  build/runtime evidence proves the README rather than the manifest text.

### EA-03 — Endpoint existence lacks a reachability and reality contract

- **Truth:** Observed/T2.
- **Evidence:** 297 backend routes, 95 BFF mappings, 17 routes still in
  `server.py`; zero unmatched paths among mappings.
- **Task:** generate a route reachability ledger: backend owner, frontend/BFF
  consumer, external consumer, scheduler/agent consumer, auth/tenant boundary,
  reality/connectivity tier, evidence tier, deprecation status, and tests.
- **FP/LT/DOC:** YES / YES / YES.
- **Keep if:** every launch-relevant route is classified and at least one
  contract/runtime check proves its intended consumer path.
- **Revert if:** it rewards route count or assumes every internal endpoint needs
  a frontend mapping.

### EA-04 — Error swallowing and degraded-mode observability need a policy

- **Truth:** Observed, T1 lexical lead; semantic classification not complete.
- **Evidence:** many `pass` exception handlers across persistence, events,
  document storage/scanning, metrics, cache, and service paths; several may be
  deliberate best-effort boundaries.
- **Task:** classify every swallowed exception in load-bearing paths as retry,
  degrade-with-event, terminal failure, compensating action, or intentionally
  ignored. Add structured events and tests for high-risk cases.
- **FP/LT/DOC:** YES / YES / YES.
- **Falsifier:** semantic audit proves each match is abstract/interface-only,
  cleanup-only, or already observably handled.

### EA-05 — Document storage has an explicit production capability gap

- **Truth:** Observed, T1.
- **Evidence:** `spine_api/services/document_storage.py` raises
  `NotImplementedError("S3 document storage not yet implemented")`.
- **Task:** classify local storage as development-only, select a production
  object-store interface through search-first evaluation, and define encryption,
  malware scanning, signed URL, tenant namespace, retention/DSAR, regionality,
  backup, and failure behavior before implementation.
- **FP/LT/DOC:** YES / YES / YES.
- **Note:** this is a capability/launch task, not proof that S3 specifically is
  the right provider.

### EA-06 — Mock notifications and federated intelligence can create false completion

- **Truth:** Observed, T1.
- **Evidence:** `spine_api/notifications.py` logs and returns success as a mock;
  `src/intake/federated_intelligence.py` is an in-memory mock and may add static
  demonstration data.
- **Task:** bring both under the R-06 capability/reality contract. Return explicit
  simulated/unavailable outcomes, never business success, and instrument callers
  so mock completion cannot advance a real workflow.
- **FP/LT/DOC:** YES / YES / YES.

### EA-07 — Frontier models retain weak relational ownership

- **Truth:** Observed, T1.
- **Evidence:** TODOs in `spine_api/models/frontier.py` retain loose
  `traveler_id`/`trip_id` pending SQL normalization.
- **Task:** decide canonical entity ownership and migration. Add foreign keys only
  after orphan analysis, backfill, tenant-scope proof, delete/update behavior,
  and rollback are defined.
- **FP/LT/DOC:** YES / YES / YES.

### EA-08 — User and business outcome evidence is missing from the engineering backlog

- **Truth:** Inferred from the reviewed task system; T1 basis.
- **Evidence:** the registers are rich in architecture and defects but rarely
  attach adoption, operator time, conversion, margin, service-quality, traveler
  trust, or support-burden baselines to implementation waves.
- **Task:** add an outcome contract to each product-facing epic: actor, job,
  baseline, target, leading/guardrail metrics, qualitative evidence, instrumentation,
  decision threshold, and rollback/revisit trigger.
- **FP/LT/DOC:** YES / YES / YES.
- **Falsifier:** a separate current canonical artifact already links every
  product-facing task to these outcome measures.

### EA-09 — Accessibility is a single defect, not a system acceptance lane

- **Truth:** Observed/inferred, T1.
- **Evidence:** A-17 identifies one modal, while the route breadth includes
  operator, traveler, public collection, proposal, document, payment, and
  disruption workflows. No current repository-wide accessibility acceptance
  matrix was established in this audit.
- **Task:** create critical-task accessibility acceptance lanes for keyboard,
  screen reader semantics, reflow/zoom, color independence, reduced motion,
  cognitive clarity, error recovery, localization expansion, and mobile/touch.
- **FP/LT/DOC:** YES / YES / YES.
- **Falsifier:** current evidence demonstrates equivalent-outcome coverage for
  all critical workflows.

### EA-10 — Implementation plan needs an explicit real-world pilot lane

- **Truth:** Proposed from the evidence gap.
- **Evidence:** existing waves emphasize code and governance foundations, but a
  clean test suite cannot establish agency adoption, operational fit, supplier
  reality, traveler comprehension, or economic value.
- **Task:** after foundation gates, run a controlled design-partner pilot with
  defined supported journeys, manual fallback, consent, incident handling,
  success/stop metrics, and structured operator feedback.
- **FP/LT/DOC:** YES / YES / YES.

### EA-11 — AI workflow evidence remains incomplete without canonical feedback records

- **Truth:** Inferred from existing eval doctrine and source inventory; T1.
- **Task:** ensure each meaningful agentic workflow emits or joins one canonical
  evidence record containing workflow unit, input artifact, provider/model,
  prompt/schema/routing/normalization versions, validation, fallback, review,
  escalation, acceptance, latency, and cost. Add failure-layer reducer and
  keep/revert rerun rules.
- **FP/LT/DOC:** YES / YES / YES.
- **Required metrics:** default success, useful/wasteful fallback, false/missed
  escalation, review correction, p50/p95 latency by path, cost per accepted output.

### EA-12 — Research backlog lacks current external-evidence refresh contracts

- **Truth:** Observed/inferred, T1.
- **Task:** for regulation, passenger rights, payments, GDS/NDC, privacy,
  accessibility standards, provider capabilities, and competitive claims, add
  source hierarchy, jurisdiction, effective date, freshness window, contrary
  evidence, owner, and refresh trigger. Use primary sources for load-bearing
  decisions.
- **FP/LT/DOC:** YES / YES / YES.

## 9. Complete research and exploration frontier

The following should be researched and documented before implementation where
the external fact or product choice is not established:

### Users and workflows

- Boutique agency operator day-in-the-life, interruption cost, handoff patterns,
  trust thresholds, and manual fallback expectations.
- Traveler comprehension and consent for uncertainty, assumptions, public links,
  document requests, memory, and AI-assisted recommendations.
- Corporate travel manager policy, duty-of-care, approval, audit, and exception
  requirements.
- Creator/group-host coordination, split responsibility, payments, and public
  communication needs.
- Accessibility and inclusive-service constraints across operator and public
  workflows.

### Business and operating model

- Which narrow design-partner segment has the highest pain, willingness to pay,
  data availability, and acceptable integration burden.
- Unit economics: operator time saved, lead response time, conversion, margin,
  rework, support, provider cost, and cost per accepted output.
- Liability and service-boundary model for advice, booking, payments, disruption,
  duty of care, insurance, visas, and passenger-rights claims.
- Human-in-the-loop staffing, escalation SLAs, after-hours operations, and
  incident ownership.

### Travel supply and fulfillment

- Real connectivity needs and sequencing across content, availability, pricing,
  booking, ticketing, servicing, refunds, NDC/EDIFACT/GDS, DMCs, and direct
  suppliers.
- Supplier identity, commercial permission, rate/commission provenance,
  contractual restrictions, caching, staleness, and auditability.
- Fulfillment failure, partial success, duplicate booking, schedule change,
  reissue, exchange, refund, chargeback, and reconciliation workflows.

### Security, privacy, compliance, and safety

- Data inventory and classification including passports/APIS, payment data,
  health/mobility, minors, location, preferences, communications, and agent logs.
- Jurisdiction-specific retention, DSAR, residency, breach, consent, passenger
  rights, marketing, and automated-decision obligations.
- Threat models for public links, tenant crossover, prompt injection, memory
  poisoning, supplier content, webhook replay, agent tool abuse, and insider
  access.
- PCI scope and payment-provider architecture before handling payment credentials
  or mandates.

### Architecture and reliability

- Canonical route/reachability inventory and unused-capability retirement.
- SQL/file/checkpoint/audit ownership and migration/rollback.
- Agent leases, idempotency, version fencing, budgets, quarantine, retry,
  temporal obligations, stream backpressure, and disaster recovery.
- Object storage/provider selection and document-security lifecycle.
- Deployment profiles, database isolation, migrations, observability, SLOs,
  capacity, backup/restore, and incident drills.

### AI, data, and evaluation

- Representative gold sets by workflow and persona, including missing/unknown/
  inferred/present-but-missed states.
- Prompt, parser, schema, dictionary, routing, fallback, and review failure-layer
  attribution.
- Semantic retrieval value against lexical/hybrid baselines; privacy, latency,
  cost, and abstention.
- Memory provenance, correction, decay, sensitive-category handling, and user
  control.
- Bias/fairness and unsafe recommendation testing across budgets, nationalities,
  families, disability, age, language, and high-risk travel contexts.

### Product experience and adoption

- One coherent information architecture across agency workbench, traveler portal,
  public flows, collaboration, and disruption operations.
- Epistemic-status UX, action consequence previews, recovery, explanation, and
  override mental models.
- Mobile/responsive, localization, time zone, currency, names, addresses, and
  international text/format handling.
- Design-partner pilot protocol and post-pilot keep/revert decisions.

## 10. Revised implementation plan

The existing wave plan is directionally strong but should be governed by the
following outcome gates. Wave numbers indicate dependency order, not a promise
that every item in a wave ships together.

### Wave 0 — Preserve, classify, and restore one current truth

1. Classify the dirty working tree by owner, intent, dependency, and evidence.
2. Reconcile this addendum into the canonical register without overwriting
   concurrent edits.
3. Implement EA-01 documentation inventory and contradiction report.
4. Resolve EA-02 frontend-generation truth.
5. Establish one current baseline profile for backend, frontend, integration,
   lint, typecheck, build, migration, and eval gates.

**Exit:** no unowned in-scope diff; current docs identify canonical owners;
commands, environment, date, and residual failures are recorded. Git mutation
remains a separate authorization.

### Wave 1 — Make truth and reachability executable

1. Complete the honest eval producer and S3 gate falsification (A-01 residual).
2. Build EA-03 route reachability/reality ledger.
3. Unify R-06/A-03/EA-06 under one capability and reality contract.
4. Make current nav/product availability derive from that contract (R-13).
5. Add canonical AI feedback evidence records and reducer (EA-11).

**Exit:** no launch-relevant capability can report real success while mock,
unavailable, unmapped, or unverified; seeded false claims fail checks.

### Wave 2 — Close authority, data, and irreversible-action boundaries

1. A-18 environment/auth/secret posture, with separate credential-rotation gate.
2. A-22/A-23 and F-02 public-token authority/data model.
3. F-03 approval identity and artifact binding.
4. F-04 payment mandate and reconciliation architecture before money movement.
5. R-15/F-05/F-13 privacy, retention, DSAR, egress, and memory trust.
6. Preserve A-19 cross-tenant probes and automate coverage for new routers.

**Exit:** every sensitive/irreversible action identifies actor, authority,
tenant, artifact/version, consent/mandate, audit event, recovery, and test.

### Wave 3 — Consolidate canonical state and contracts

1. A-04 backend duplicate-system migrations.
2. A-05/A-06 typed API boundary and contract generation.
3. R-10 server decomposition inside one service.
4. F-09 canonical SQL checkpointing, migration, comparison, and file-path
   retirement.
5. F-06 single audit owner and integrity verification.
6. A-20/EA-07 migrations and relational ownership.
7. EA-05 production document-storage contract and implementation.

**Exit:** one owner per state/contract; all callers migrated; parity and rollback
proved; predecessor has a retirement state and date.

### Wave 4 — Reliability, recovery, and operational control

1. R-11/F-10 durable leases and version-safe resume.
2. F-01 idempotent financial state transitions and compensation.
3. F-07 quarantine and safe replay.
4. F-11 hierarchical spend budgets and circuit breaker.
5. F-12 streams/backpressure/replay.
6. EX-14/F-14 temporal obligations and spoilage escalation.
7. F-15/F-16 travel-native exception, refund, exchange, and claims disposition.
8. R-16/EA-04 observability, error disposition, and operator investigation.
9. F-19 isolated integration-test infrastructure.

**Exit:** retry, duplicate, timeout, partial failure, stale work, deploy transition,
quarantine, compensation, and recovery are observable and deliberately tested.

### Wave 5 — Product quality and inclusive operator/traveler experience

1. R-14 design-system consolidation with visual baselines.
2. A-17/EA-09 critical-task accessibility acceptance lanes.
3. A-16/F-17 risk-based frontend verification and E2E.
4. EX-02 epistemic-status UX and operator research.
5. A-11 marketing-surface retirement after route/analytics decision.
6. Localization, currency, time-zone, mobile, offline/degraded, and recovery
   acceptance matrices.

**Exit:** critical agency and traveler tasks work end-to-end at named viewports
and accessibility conditions, with failure and recovery evidence.

### Wave 6 — Real connectivity and controlled design-partner pilot

1. Complete source-first research for the selected narrow design-partner segment.
2. Add only the minimum real supplier/provider connectivity needed for supported
   journeys, behind R-06 gates.
3. Run EA-10 controlled pilot with manual fallback, incident runbook, consent,
   supported-scope disclosure, and outcome instrumentation.
4. Compare operator time, response latency, acceptance, conversion, rework,
   margin, trust, support, cost, and reliability against baseline.

**Exit:** a defined user cohort completes supported real workflows; all manual
and provider boundaries are visible; keep/revert decisions are evidence-backed.

### Wave 7 — Conditional differentiation

Only after Waves 0–6 establish demand and operating truth:

- EX-01 real IROPS journey-graph triggers;
- EX-07 supplier message ingestion;
- EX-08 capacity planning;
- EX-09 explanation dossiers;
- EX-10 quarantine automation;
- EX-11 veto-window autonomy;
- EX-12 standing intent;
- EX-13 itinerary branching;
- advanced retrieval, marketplace, negotiation, ticketing, or RFQ systems when
  their explicit go/no-go conditions are met.

## 11. Cross-wave completion contract

No task is complete merely because code exists or a test passes. A complete
slice records:

1. user/business/internal outcome and owner;
2. canonical source, consumers, and data owner;
3. current truth status and evidence tier;
4. security/privacy/authority and failure model;
5. migration, compatibility, rollback, and retirement;
6. targeted checks plus integration/runtime proof proportional to risk;
7. test sensitivity, including S2/S3 where required;
8. observability, operator recovery, and support path;
9. documentation, decision, and freshness updates;
10. residual risk, external gates, and next revisit trigger.

For agentic workflows also require:

- prompt/schema/routing/normalization versioning;
- fallback and review trigger/outcome;
- failure signature/layer;
- rerun subset;
- keep/revert gate;
- latency and cost per accepted output.

## 12. Artifacts preserved and coordination notes

- No application code was changed by this audit.
- No existing documentation was deleted, renamed, or overwritten.
- The currently modified canonical findings, task, plan, and index files were
  deliberately not edited.
- No test, server, browser, provider, or deployment claim was made.
- No Git staging, commit, push, fetch, branch, stash, reset, checkout, or hook
  mutation was performed.
- This file is an addendum pending owner-led reconciliation into the canonical
  registers after concurrent edits settle.

## 13. Immediate next implementation slice

The highest-leverage safe next slice is **Wave 0 + Wave 1 truth control**:

1. classify current ownership and baseline;
2. reconcile findings without duplication;
3. fix README/dependency truth;
4. generate documentation contradiction inventory;
5. generate route reachability/reality inventory; and
6. unify mock/sandbox/live outcomes under one capability contract.

This slice makes later security, reliability, and product work cheaper because
it establishes what exists, who consumes it, what is real, and which evidence
can close a finding.
