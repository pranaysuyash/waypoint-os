# Consolidated Findings & Tasks Register — Explicit + Implicit (2026-08-30)

**Purpose:** one list of every finding/task that can or should be **explored** (researched + documented) or **implemented**, consolidated from:

1. `FINDINGS_REGISTER_2026-08-29.md` — R-01…R-16 (explicit carry-forward, live-verified) + A-01…A-21 (new, mostly implicit)
2. `EXPLORATION_RESEARCH_BACKLOG_2026-08-29.md` — RQ-01…06, EX-01…06, D-01…D-05
3. `IMPLEMENTATION_PLAN_2026-08-29.md` — Waves 0–6 (scheduling reference)
4. `ADHD_APP_AUDIT_EXPLORATION_2026-08-30.md` — 30 divergent candidates; **16 new implicit defect findings (F-01…F-16 below) not previously in any register**

**Legend:** Type `E` = explicit (already documented) · `I` = implicit (discovered by audit). Class: **IMP** = implement (known how) · **EXP** = explore (research + document first). Status drift as of 2026-08-30 noted inline.

**Drift corrections applied (2026-08-30):**
- **R-03 / RQ-04 largely RESOLVED** — `review/R03_SPLIT_BRAIN_RESOLUTION_2026-08-30.md` verified `data/trips/*.json` are gitignored test artifacts; SQL mode never reads them; fail-closed guard added (uncommitted — must be committed, see A-14).
- **R-12 narrowed** — `src/schemas/journey_graph.py` has 4 live importers; only the IROPS trigger path is missing (EX-01 narrowed).
- R-01, R-02, R-04, R-05 fixed (partly still uncommitted).

---

## Section 1 — IMPLEMENT (known how; do in dependency order)

### 1a. Scheduled in Implementation Plan Waves 0–6

| ID | Type | Task | Wave | Priority |
|----|------|------|------|----------|
| A-14 | I | Commit the uncommitted P0 remediation (R-02/R-04/R-05 fixes, epistemic primitives, R-03 guard) as one atomic unit — **requires Pranay's explicit authorization in-session** | 0.2 | **P0** |
| A-13 | I | ~~Triage 358 backend test failures~~ **RESOLVED 2026-08-30** — 358 were an env artifact (audit ran without CI env vars); true CI-identical baseline **3,206 passed / 10 skipped / 0 failed**. 2 real defects fixed (audit-store test pollution, brittle integration polling). Runner: `scripts/run_backend_tests.sh`. Evidence: `review/A13_TEST_BASELINE_RESOLUTION_2026-08-30.md`. Remaining Wave 4.5–4.9 items stay open | 4.1–4.4 done | **closed** |
| A-01 / R-07 | I | ~~Un-mute the honest quality gate~~ **RESOLVED 2026-08-30** — implemented by parallel agent (`8ece02e` + unstaged manifest/snapshot), verified end-to-end: 43/43 eval tests pass; guard exits 1 with real blockers (budget F1 0.2857, blocks_ci true). CI now honestly red until F1 improves (RQ-01 unblocked). Residual 1.5: live-results params exist, no producer wired. Evidence: `review/WAVE1_A01_RQ06_EX06_OUTCOMES_2026-08-30.md` | 1.1–1.5 | **closed** |
| A-19 | I | ~~RLS coverage~~ **RESOLVED 2026-08-30** — 5 routers converted (12 deps; integrations' hand-rolled session-scoped set_config retired), auth.py documented deviation; RQ-03 verdicts: all 4 exempt tables safe (filtered / write-only / unwired). Probe suite added. Evidence: `review/A19_RLS_COVERAGE_RESOLUTION_2026-08-30.md` | 2.2–2.3 done | **closed** |
| A-18 | I | Rotate live `OPENAI_API_KEY`; remove committed `DATABASE_URL` default password; make `SPINE_API_DISABLE_AUTH` hard-fail outside test | 2.7–2.8 | **P1** |
| R-15 | E | PII guard posture: audit-event on fail-open no-op; reconcile Layer-1 fail-open vs Layer-2 fail-closed in an ADR | 2.5–2.6 | **P1** |
| A-20 | I | Migrations drift: 4 frontier tables had NO migrations (endpoints runtime-broken — probe caught `relation does not exist`); **fixed 2026-08-30** with additive migration `add_frontier_tables` (applied, DB at new head). **Still open:** CI drift gate (`alembic check`) so the class cannot recur | 2.4 | P2 |
| A-04 | I | Consolidate 9 duplicate/shadow systems (audit stores, dual auth decode, audit_bridge deletion, membership, scoring, vision clients, config → one `BaseSettings`) — each with a deletion date | 3.1–3.7 | **P1** |
| A-05 | I | One frontend API client; migrate 104 raw `fetch(` sites / 30 ad-hoc files; ESLint ban bare `fetch(`, CI-blocking | 3.8 | **P1** |
| A-06 | I | Generated TS types as single contract; CI drift gate (regenerate → diff → fail) | 3.9 | **P1** |
| A-07 | I | Doc-tree consolidation (`Docs/` vs `frontend/docs/`), inode collision fix, CHANGELOG backfill | 3.12, 4.9 | P1/P2 |
| A-09 | I | ADR template `Supersedes:`/`Superseded-By:`; back-fill 22 ADRs; renumber 003/004/005 gap | 3.13 | P1 |
| A-10 | I | Reconcile IDEA_PAD against git (mark IDEA-120/122/123/124 done; re-date WIP registry) | 3.14 | P2 |
| A-11 | I | One marketing surface (retire `app/v2`–`v4`, keep `v5`) | 3.10 | P2 |
| A-12 | I | Resolve inert `src/proxy.ts`: restore real `middleware.ts` or delete; resolve Next 16/14 version skew (ADR the decision) | 3.11 | **P1** |
| A-08 | I | Repoint 18 `motto_v4.md` references at `FIRST_PRINCIPLES_MOTTO_V4_DOCTRINE.md`; CI dangling-reference check | 4.8 | P2 |
| A-16 | I | Ratcheting vitest coverage thresholds; first booking-path smoke e2e (zero e2e exist) | 4.5–4.6 | P2 |
| A-15 | I | Reduce 65 `any` in prod code (hotspot `DecisionTab.tsx`); justify the 4 `eslint-disable`s | 4.7 | P2 |
| A-17 | I | Fix `WelcomeModal` a11y (no `role="dialog"`/`aria-modal`; hand-rolled toast-sheet) | 6.7 | P3 |
| R-06 / A-03 | E/I | Implement `CONNECTIVITY_TIER` (design exists, `LIVE_CONNECTIVITY_INTEGRATION_2026-08-29.md` §3); unify all agent-tool mock/live switches behind it; fail loud on mock outside dev — **and** wire `EpistemicStatus` onto every TripPacket slot, populate `AssumptionRecord` from intake, epistemic UI surface, `assert_tier_capability` on every financial-claim endpoint | 5.1–5.5, 6.9 | **P1** |
| R-11 | E | Implement durable agent lease per design: heartbeat refresh, fencing token, STALE sweep, agency scoping (`ExecutionLease` is dead code; >60s tasks re-acquirable → double-execution risk) | 6.1 | P2 |
| R-16 | E | OTel trace-correlation reader + CI event-flow assertion (spans exist, no consumer) | 6.3 | P2 |
| R-14 | E | Frontend styling unification per design doc | 6.4 | P3 |
| R-13 | E | Nav rollout-gate drift (`nav-modules.ts` `complete: false` vs "14/14 active" claim) — needs product decision first | 6.5 | P2 |
| R-10 | E | Server decomposition per plan (`create_app()` factory; rejects microservices); single audit store decision (recommend Postgres `audit_logs` + hash chain) | 3.4, 6.6 | P2 |
| A-21 | I | Track the 6 untracked in-flight artifacts (JDG design+code, connectivity, lease, decomposition, styling plans) in this register with owners | 6.8 | P2 |

### 1b. New implicit defect findings from the 2026-08-30 ADHD audit (not previously registered — proposed IDs F-01…F-16)

**Source-frame mapping (every idea from the 2026-08-30 wide set is tracked here):** F-01←O6+C2 · F-02←C1+R6 · F-03←R2 · F-04←R5 · F-05←R3 · F-06←R1+C4 · F-07←O2 · F-08←O3 · F-09←O1 · F-10←O4 · F-11←O5+C6 · F-12←C5 · F-13←C3 · F-14←L2 · F-15←L6 · F-16←L3 · EX-07←L1 · EX-08←L5 · EX-09←R4 · EX-10←O2-children · EX-11←A2 · EX-12←A3 · EX-13←A4 · EX-14←provocation · NG-01←A1 · NG-02←A5 · NG-03←L4 · NG-04←A6. Coverage: **30/30 wide-set ideas.**

| ID | Type | Finding (evidence file) | Implement task | Priority |
|----|------|------------------------|----------------|----------|
| F-01 | I | `price_lock.py` `re_lock_lower_rate` is a blind read-modify-write: no `strategy.version`, no idempotency key → concurrent/replayed re-locks double-book `margin_saved_cents` and corrupt undo | Add optimistic `strategy.version` + Idempotency-Key; then **compensating-action records + one-command revert** (top-ranked O6 ★: invertible re-shopping, audit-chained) | **P1** |
| F-02 | I | `public_proposals.py` `_PROPOSAL_REGISTRY`: in-memory, unbounded, 16-hex unauthenticated tokens → full trip data; no TTL, revocation, or consent trail; `public_collection.py` accepts outside-tenancy PII unlogged | Atomic single-use accept claims; token TTL/revocation; PII minimization; consent events | **P1** |
| F-03 | I | `team_workflows.py` stores client-supplied `reviewer_id`; `corporate_policy.py` accepts free-text `approved_by`; audit logs record tenant id, not acting human — "who authorized what" is self-asserted | Bind signoffs to authenticated JWT subject + artifact-version hash | **P1** |
| F-04 | I | No payment authorization mandate ledger: split deposits + `subagent_payouts.py` ACH move money with no consent/mandate artifact chained to the audit hash | Mandate ledger: payer consent, amount, counterparty, executor per movement | **P1** |
| F-05 | I | `src/security/jurisdiction_policy.py` declares retention/erasure/residency/breach SLAs; **zero enforcement wiring**; run_ledger leaves unencrypted PII step files forever | DSAR execution engine: retention sweeps, erasure cascades (Postgres + run-ledger files + tombstones in audit chain) | **P1** |
| F-06 | I | Audit-chain evidence gaps: file hash-chain unsigned/unanchored; run-ledger step files entirely outside the chain; no fork/gap detector; overlaps A-04 3.4 single-store decision | After 3.4: sign + extend chain coverage to run ledger; monotonic sequence + writer identity; periodic external anchoring; background verifier | P2 |
| F-07 | I | `agent_requeue_jobs.py` `JOB_STATUS_POISONED` accumulates invisibly; no inspect/redact/replay; recovery never fires for dead trips | Quarantine drain lane: `list_poisoned()`, poison taxonomy, permission-gated replay via idempotency registry (dedup verdict surfaced), audit-chained, workbench tab | **P1** |
| F-08 | I | `core/locking.py` silently falls back to in-process asyncio locks when not on Postgres → dev/tests/misconfigured prod have different mutual-exclusion semantics | Fail-fast boot assertion in production mode | P2 (small) |
| F-09 | I | `run_ledger.py` checkpoints only to local disk while state is SQL-backed → rolling deploys orphan RUNNING runs (3am invisible split brain) | Dual-write run checkpoints to SQL | P2 |
| F-10 | I | `agent_work_coordinator.py` leases have no pipeline-version check → a deploy splits a run across two code generations silently | Stamp git SHA + schema/gate version in run meta; fence mismatched-version resumes (checkpoint-and-defer) | P2 |
| F-11 | I | `usage_guard` meters spend at call time only: no auto-quiesce when a tenant goes berserk; no parent→child spend reservation, so nested subagent loops bypass the top-level check | Freeze-breaker auto-pause (drain in-flight, queue review) + lease-scoped spend reservations | P2 |
| F-12 | I | SSE fan-out (`run_events.py`, `run_status.py`) has no per-tenant connection cap, heartbeat, or eviction | Per-agency stream budgets + ping frames + resumable cursors | P2 |
| F-13 | I | `src/memory/` writes are sanitized but not trust-weighted; `retriever.py` injects cross-trip preferences straight into suitability scoring → traveler/vendor text can poison medical/mobility claims | Provenance-tiered memory writes (channel + verification tags, confidence decay, retrieval-time quarantine of unverifiable claims) | **P1** |
| F-14 | I | Dated perishables (visas, quote TTLs, insurance windows, payment deadlines, ticketing limits) tracked per-artifact only; no owner of "expiring inventory" as a class | **Cold-chain spoilage sweep** in `watchdog.py` (top-ranked L2): tiered escalation, event-vocabulary extension, dedupe on tier transitions | **P1** |
| F-15 | I | `confirmation_service.py` treats every defective supplier confirmation (missing segments, mismatched names) as generic failure → retry loops instead of claims | OS&D exception codes at the transition boundary + dedicated claims lane | P2 |
| F-16 | I | Refund/compensation pipeline dead-ends (`passenger_rights_claims.py` + payment refund constants); no disposition grading or re-shop credit path | Reverse-logistics RMA lane: disposition codes (resell / re-shop / write-off) feeding existing re-shop machinery | P2 |

### 1c. Capability implementations (opportunities, not defects — from ADHD audit, post-Wave-1)

| ID | Type | Candidate (src) | Notes / sequencing | Priority |
|----|------|-----------------|--------------------|----------|
| EX-07 | E | Cross-dock EDIFACT/NDC payloads straight into trip documents (src: L1) | Parsers exist in `src/distribution/`; requires connectivity tier ≥ SANDBOX to be honest | P3 |
| EX-08 | E | Forward-loaded capacity planning: departure-date demand vs lease capacity (src: L5) | Extends `agent_work_coordinator.py` + `sla_service.py` | P3 |
| EX-09 | E | AI-decision explanation dossier: replayable hashed evidence bundle per trip (src: R4) | Best after Wave 5 epistemic wiring + F-06 chain coverage | P3 |
| EX-10 | E | Quarantine follow-ons: auto-classifier, unified ledger, dry-run + batch replay (src: O2 children) | Follow-ons to F-07 | P3 |

---

## Section 2 — EXPLORE (research + document before building)

| ID | Type | Question / exploration | Method → exit | Priority |
|----|------|------------------------|---------------|----------|
| RQ-06 | I | ~~Frontend real state~~ **EXECUTED 2026-08-30**: typecheck PASS · tests 896/897 (1 TimelinePanel race) · 49 unhandled vitest errors · lint 4 errors/17 warnings. Audit Assumption 7 closed. Evidence: `review/WAVE1_A01_RQ06_EX06_OUTCOMES_2026-08-30.md`; defects → F-17 | — | **closed** |
| EX-06 | I | ~~Findings lifecycle~~ **DELIVERED 2026-08-30**: 4-state machine + `scripts/check_findings_register.py` (CI-ready, ruff-clean); both registers validate; spec + D-02 amendment text at `review/FINDINGS_LIFECYCLE_2026-08-30.md`. CI wiring deferred (coordination) | — | **closed** |
| F-17 | I | Frontend suite debt (from RQ-06): TimelinePanel test races its async fetch (asserts before `Loading timeline…` resolves); 49 unhandled vitest errors unexamined; 4 lint errors (2 setState-in-effect, 1 refs-during-render, 1 unescaped entity) + 17 exhaustive-deps warnings | Fix the race (waitFor), triage unhandled errors, clear lint errors, then add ratcheting coverage thresholds (A-16) | P2 |
| F-18 | I | ~~Budget extraction rule package (RQ-01 exit)~~ **RESOLVED 2026-08-30** — S1–S6 implemented in `_extract_budget` (+ eval-side amount composition, 8 negative precision traps added: 12→20 fixtures, 0 FP). Budget gate **passing: F1 0.9524, P 1.0, R 0.9091, blocks_ci False; guard exit 0 — CI green**. Decisions D1 (unmarked currency → USD, lakh/crore stay INR) and D2 (unmarked flexibility → soft, scope → total) implemented per RQ-01 recommendation — ratification pending. H1 (hard_004 revision resolution) deferred. Full suite 3,215 passed / 0 failed. Evidence: `exploration/F18_BUDGET_RULE_PACKAGE_IMPLEMENTATION_2026-08-30.md` | — | **closed** |
| F-19 | I | Full-suite phantom failures under live-server contention: with the dev server up on :8000, integration tests run mid-suite against the shared DB — three consecutive full runs produced three different failure sets (1/4/13), 25-min runtime vs ~70s clean; every failing test passes in isolation. Runner now warns; clean baselines require the server stopped | Systemic fix: default-exclude integration tests (opt-in flag) or per-test DB namespacing | P2 |
| RQ-01 | I | ~~Is deterministic extraction the right ceiling?~~ **CLOSED 2026-08-30 — verdict: rule-coverage problem, falsifier NOT triggered** (1/12 fixtures = 8% needs-LLM, far under the 50% threshold). Prototype rules: 2/12 → 11/12 fixtures. Deterministic boundary survives; no hybrid redesign needed. Path to green CI = implement F-18, not threshold re-baseline. Evidence: `exploration/RQ01_BUDGET_EXTRACTION_CEILING_2026-08-30.md` | — | **closed** |
| RQ-03 | I | ~~Are the 4 RLS-exempt tables cross-tenant reachable?~~ **CLOSED 2026-08-30 — verdict: none reachable cross-tenant.** audit_logs: single read agency-filtered · ghost_workflows: id+agency 404 probe · emotional_state_logs: write-only JWT-scoped · legacy_aspirations: no endpoints at all. Evidence: `review/A19_RLS_COVERAGE_RESOLUTION_2026-08-30.md` | — | **closed** |
| EX-01 | E | **JDG IROPS trigger (narrowed)** — design + schema exist with 4 importers; only the trigger is open. Which real disruption signal mutates a JDG node, and what is its source of truth? (Mock-tool caveat: no live disruption source is connected — A-03) | Measure segment-count distribution first (falsifier: single-segment trips ⇒ low value) → trigger design + go/no-go | 5th |
| EX-02 | I | **Epistemic status as product surface** — what does the UI do when a belief is ASSUMED/UNKNOWN; operator experience of uncertainty | Interaction proposal + operator observation (Tier 4); depends on Wave 5 | 6th |
| EX-03 | I | **Retirement as a first-class primitive** — the repo's dominant failure mode is "built the replacement, never retired the original" (9 duplicate pairs, 4 marketing generations, 2 doc trees) | Design retirement state (target + deletion date + CI enforcer) → becomes Wave 3 retirement gate | 7th |
| EX-05 | E | **Negative-space map** — deliberately absent capabilities: payment execution, ticketing/GDS, supplier contracts, refund/chargeback flows, multi-currency settlement, PCI scope, APIS data, WCAG, i18n | Reconcile vs existing readiness contracts (2026-05-17) → each absence classified deliberate/oversight/unknown | 8th |
| D-01…D-05 | I | **Doctrine amendments** (Pranay's decision): D-01 absence claims need executed evidence; D-02 finding lifecycle; D-03 generated-mirror placement guard; D-04 deleting doctrine requires re-homing dependents same-change; D-05 completion claims must cite verification command + date | Write amendments into doctrine family; record per §16.9 | 9th |
| EX-14 | I | **`TemporalObligation` primitive** (ADHD provocation) — every deadline in the system (visa, price lock, payment, insurance, ticketing, SLA, 72h re-shop window) is an independent timer; no first-class "obligation with a deadline" exists. Would subsume F-14 + half of Cluster A as special cases | Design doc: table, sweep, escalation policy → decide whether to build before or instead of F-14 standalone | high-leverage design |
| EX-11 | I | **Veto-window governance** (src: A2) — dispatch-then-veto inside a time-boxed window feeding the override learner | Only as an additive per-agency opt-in mode; must not replace D1 signoff gates. Design + falsifier first | conditional |
| EX-12 | I | Standing travel-intent subscriptions: warm plan shelf, trips materialize on trigger (src: A3) | Market-fit + data-model sketches; materialize only after foundation waves | later |
| EX-13 | I | Git-like itinerary branch-and-merge with constraint re-validation on merge (src: A4) | Design sketch; materialize only after foundation waves | later |
| NG-01 | I | **No-go-for-now: event-log-as-SSOT rewrite** (src: A1) — premature architecture rewrite, contradicts canonical-path-first doctrine; F-09 dual-write serves the real need | Re-open only if F-09 proves insufficient | deferred |
| NG-02 | I | **No-go-for-now: A2A negotiation endpoint** (src: A5) — no supplier adapter exists; a negotiation surface without supply-side connectivity is a demo, not a product | Re-open after connectivity tier 1 | deferred |
| NG-03 | I | **No-go-for-now: JIT ticketing scheduler** (src: L4) — autonomous deferred issuance has no real fulfillment/PNR path | Re-open after connectivity tier 1 | deferred |
| NG-04 | I | **No-go-for-now: programmable supplier RFQ rounds** (src: A6) — same blocker as NG-02; `bargaining_engine.py` has no structured counterparty to bargain with | Re-open after connectivity tier 1 | deferred |

**Closed since backlog was written:** RQ-02 (motto_v4 content recovered → folded into Wave 4.8 reference hygiene) · RQ-04 (resolved by `R03_SPLIT_BRAIN_RESOLUTION_2026-08-30.md`; remaining action is committing the guard, see A-14) · RQ-05 (folded into Wave 3.11 decision).

---

## Section 3 — Recommended sequencing

1. **Wave 0 (A-14 commit, with authorization) + RQ-06 + EX-06** — preserve uncommitted P0 work; close the two cheapest evidence holes.
2. **Wave 1 (A-01)** — make the quality instrument honest before touching anything that reads it. Expect gates to go red; that is the point.
3. **Wave 2 security (A-19, A-18, R-15, F-02, F-03)** — tenant boundary + identity binding + public token surface before any new money-moving feature.
4. **Wave 3 consolidation** — retirement gate (EX-03 output) governs every consolidation here.
5. **F-01 → F-04 → F-05** (money/mandate/DSAR spine) — F-01's version/idempotency discipline is the shared prerequisite for F-02/F-04.
6. **F-07 (quarantine) + F-14 (spoilage)** — highest operator value per unit effort once gates are honest.
7. Wave 5 epistemic completion, then Wave 6 extensions (lease, JDG trigger, OTel, styling, decomposition).
8. Explore items run continuously in parallel per the backlog's priority table; each exit becomes an implementation task or a recorded no-go.

## Counts

- **Implement:** 27 scheduled wave items (1a) + 16 new implicit defect findings (1b) + 4 capability candidates (1c, EX-07…10) = **47**
- **Explore:** backlog items (RQ/EX/D, 2 closed, rest open) + 4 ADHD design candidates (EX-11…14)
- **Recorded no-go-for-now:** 4 (NG-01…04, tracked rows with re-open conditions)
- **Closed since 2026-08-29:** RQ-02, RQ-04, RQ-05, A-01, A-13, RQ-06, EX-06, RQ-01, F-18 (see rows)
- **ADHD wide-set coverage: 30/30 ideas tracked** (16 defect findings, 8 candidates, 4 no-gos, 2 already covered by F-rows)
