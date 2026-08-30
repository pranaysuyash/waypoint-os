# Exploration & Research Backlog — Waypoint OS Persona Council Audit

**Date:** 2026-08-29 · **Companion to:** `PERSONA_COUNCIL_MASTER_AUDIT_2026-08-29.md`,
`FINDINGS_REGISTER_2026-08-29.md`, `IMPLEMENTATION_PLAN_2026-08-29.md`

**Doctrine basis:** `OPERATING_DOCTRINE.md` §9 (exploration & durable knowledge),
`EXPLORATION_DOCTRINE.md` (frontier mapping, noun-stripping, negative space, no-go
discipline), `RESEARCH_DOCTRINE.md` (source hierarchy, recency, triangulation),
`ARCHITECTURE_DOCTRINE.md` (load-bearing design)

---

## What belongs here vs. the implementation plan

- **Implementation plan** = things we *know how to do* and should just do.
- **This backlog** = things where **the correct answer is not yet known**, and shipping
  code first would lock in a guess.

Per doctrine §9: *"Separate exploration candidates, hypotheses, research questions,
implementation tasks, and rejected directions. Discovery does not imply implementation."*

Each entry declares: **question · why it matters · why it's not yet implementable ·
method · falsifier · exit state** (becomes an implementation task, or is closed as no-go).

---

## R — Research questions (external or internal facts must be established)

### RQ-01 · Is deterministic extraction actually the right ceiling?
- **Question:** Budget extraction F1 is **0.2857** (precision 1.0, recall 0.1667; medium
  0.0, hard 0.0). Is the ceiling a *tuning* problem, a *rule-coverage* problem, or a
  *paradigm* problem?
- **Why it matters:** The deterministic boundary is the project's strongest architectural
  claim (§2.2 of the master audit). If regex/dictionary extraction plateaus below usable
  recall, the "deterministic core" needs a hybrid design — and *that* is a load-bearing
  architectural change, not a bug fix.
- **Why not yet implementable:** Nobody has measured the ceiling. Adding rules blind is
  effort with no signal.
- **Method:** Error analysis on the failing fixtures by category (entity type, phrasing
  pattern, ambiguity class). Then: for each failure class, ask *could any deterministic
  rule have caught this?* Three buckets: **tunable / needs LLM / genuinely ambiguous**.
- **Falsifier:** If >50% of failures are "needs LLM," the deterministic boundary must be
  redrawn deliberately (with a gated hybrid), not by accretion.
- **Exit:** A bucketed error taxonomy + a go/no-go on hybrid extraction.
- **Depends on:** Implementation Plan 1.5 (real results wired into gates) — you cannot
  analyse what the gate does not measure.

### RQ-02 · What did `motto_v4.md` actually say?
- **Question:** 18 files and all four numbered ADRs cite `motto_v4.md` Rules 0.9/0.10/0.15
  as governing. The file **does not exist**. What were those rules?
- **Why it matters:** The modern ADR corpus is currently governed by unrecoverable rules.
  Any compliance claim about those ADRs is unverifiable.
- **Method:** `git log --diff-filter=D --all -- '*motto_v4*'`; then
  `git log --all --full-history -- '*motto_v4*'`; check `.agent/archives/doctrine-legacy/`
  and `/Users/pranay/Downloads/`. If unrecoverable, mark all 18 references **Unknown**.
- **Falsifier:** If recoverable → re-derive into `OPERATING_DOCTRINE.md` or a dated
  addendum. If not → record the gap honestly; **do not invent the rules.**
- **Exit:** Either the rules are restored, or 18 references are formally marked Unknown.

### RQ-03 · Are the 4 RLS-exempt tables actually reachable cross-tenant?
- **Question:** `rls.py:65-70` exempts `audit_logs`, `emotional_state_logs`,
  `ghost_workflows`, `legacy_aspirations`. Do the routers that read them apply an agency
  filter?
- **Why it matters:** This is a potential P0 tenant-isolation hole, or a documented and
  safe deviation. Both are fine; **not knowing** is not.
- **Method:** Read `routers/frontier.py` and every query site for those 4 tables. Check for
  `where(agency_id == ...)`.
- **Falsifier:** Any query without an agency filter that is reachable by an authenticated
  non-owner → P0 confirmed.
- **Exit:** Per-table verdict; filters added or deviation documented.

### RQ-04 · Is `data/trips/*.json` still written under `TRIPSTORE_BACKEND=sql`?
- **Question:** 1,635 JSON files coexist with PostgreSQL. Is this live split-brain or dead
  seed data?
- **Why it matters:** Determines whether R-03 is a P0 data-integrity bug or a P2 cleanup.
- **Method:** Set `TRIPSTORE_BACKEND=sql`, exercise a trip write, observe file mtimes.
  Grep for write paths that bypass the backend switch.
- **Exit:** Binary verdict → Implementation Plan 2.1 gets a concrete scope.

### RQ-05 · Does `src/proxy.ts` represent a lost auth control?
- **Question:** The file is inert (no `middleware.ts`, 0 imports). Did it ever run, and did
  the app lose an edge auth gate when it stopped?
- **Why it matters:** If a real auth control silently disappeared, that is a live security
  regression, not dead code.
- **Method:** `git log --follow frontend/src/proxy.ts`; correlate with Next version history
  (`eslint-config-next@^16` vs `next@14` suggests a reverted Next 16 attempt). Check
  `components/auth/AuthProvider.tsx` for what actually gates routes today.
- **Exit:** Either restore `middleware.ts` or delete `proxy.ts` — with the decision recorded.

### RQ-06 · What is the frontend's real state?
- **Question:** 161 Vitest files exist but were **never executed in this audit**. What is
  the actual pass rate, coverage, typecheck and lint status?
- **Why it matters:** This is the **largest evidence hole in the audit** (Assumption 7 in
  the findings register). Every frontend claim here is Tier 1 (static) only.
- **Method:** `cd frontend && npm run typecheck && npm run lint && npm test -- --run`
- **Exit:** Real numbers replace Tier-1 inference; may reclassify A-15/A-16 severity.

---

## E — Exploration candidates (frontier mapping — may or may not become work)

### EX-01 · Journey Dependency Graph — ⚠️ **DEFERRED: design and code already exist**

> **Status changed after discovery of parallel work (A-21).** Do **not** re-explore this.
> Extend the existing canonical artifacts:
> - Design: `Docs/exploration/JOURNEY_DEPENDENCY_GRAPH_2026-08-29.md` (402 lines)
> - Code: `src/schemas/journey_graph.py` (14,616 B, created 2026-08-29 18:09, **untracked**)
>
> **Remaining question (narrowed):** the graph is imported by four modules —
> `src/decision/counterfactual_recovery.py:15`, `src/decision/constraint_engine.py:20`,
> `spine_api/routers/counterfactual.py:28`, `spine_api/routers/constraints.py:32` — so it is
> **not** orphaned as `Docs/INDEX.md` claims. What is missing is the **IROPS trigger path**.
> - **Research question:** which real-world disruption signal should mutate a JDG node, and
>   what is the source of truth for it? (The `Mock*Tool` findings in A-03 apply: today no
>   live disruption source is connected.)
> - **Falsifier:** if trips are overwhelmingly single-segment, ripple analysis has low value.
>   **Measure the segment-count distribution before building the trigger.**
> - **Exit:** IROPS trigger design + segment-count distribution + go/no-go.
>
> *(Doctrine §5: extend the canonical path; do not fork it.)*

### EX-02 · Epistemic status as a first-class product surface *(extends R-06 / Wave 5)*
- **Noun-stripped:** Every field in the system is a **labelled belief with provenance**,
  not a value. The product question is: *what does the UI do when a belief is ASSUMED or
  UNKNOWN?*
- **Why interesting:** `EpistemicStatus` + `AssumptionRecord` are landed. The unexplored
  half is the **operator experience of uncertainty** — how an agent acknowledges an
  assumption, and what "UNKNOWN" looks like in a proposal. Most systems either hide
  uncertainty or drown the user in it.
- **Why exploration, not implementation:** The right interaction pattern is genuinely
  undetermined and cheap to get wrong.
- **Falsifier:** If operators ignore the status entirely in observation, the surface is
  decoration and the value is only internal.
- **Exit:** An interaction proposal with operator observation (Tier 4).

### EX-03 · Retirement as a product capability
- **Observation:** The repo's dominant failure mode is *"built the replacement, never
  retired the original"* — 9 duplicate pairs, 4 marketing generations, 2 doc trees,
  parallel ADR numbering.
- **Noun-stripped:** This is not laziness; it is the **absence of a retirement primitive**.
  Deprecation is currently a *comment*, not a *state with a date and an enforcer*.
- **Why interesting:** A first-class retirement state (target + deletion date + enforced
  by CI) would prevent the entire defect class rather than fixing 9 instances.
- **Exit:** Design for a retirement primitive; if adopted, becomes the Wave 3 "retirement
  gate."

### EX-04 · Connectivity tier as a product claim — ⚠️ **DEFERRED: design already exists**

> **Status changed after discovery of parallel work (A-21).** The `CONNECTIVITY_TIER`
> design is **already written**: `Docs/exploration/LIVE_CONNECTIVITY_INTEGRATION_2026-08-29.md`
> §3 (lines 201-252) specifies:
> - progression `MOCK → SANDBOX → LIVE` (`:233-235`)
> - **the key rule:** `CONNECTIVITY_TIER` and `RealityTier` are **orthogonal** (`:238`) — a
>   supplier router can be `REAL` while its provider is `MOCK` (`:249`)
> - a mapping table between the two enums (`:244-246`)
>
> **This is better than what this audit would have proposed** — the orthogonality rule
> resolves the exact ambiguity flagged in the prior audit §8.2 ("two parallel classification
> systems risk drift").
> - **Remaining work: implementation only** (Implementation Plan 5.1), plus one open
>   question: **what may the UI claim at each tier?** (doctrine §13 — customer-facing claim
>   reality). That claim-policy is the one genuinely unexplored piece.
> - **Exit:** claim-policy document; then implement per the existing design.

### EX-05 · Negative space: what is deliberately NOT here?
- **Question:** For a travel OS, what capabilities are conspicuously **absent** — and is
  that a choice or an oversight?
- **Method (PER-91002):** Strip the domain noun and compare against the primitive
  inventory: payment *execution* (only a read-model exists), ticketing/GDS integration,
  supplier *contracts* (only uploaded-contract parsing), refund/chargeback flows,
  multi-currency settlement, PCI scope, passenger identity/APIS data, accessibility
  (WCAG) as a declared standard, localization/i18n (no i18n library found).
- **Why interesting:** `Docs/review/` already contains readiness contracts for bookings and
  payments (2026-05-17) — the repo has *thought* about these. Reconciling intent vs reality
  is cheap and likely to surface real gaps.
- **Exit:** Negative-space map; each absence classified **deliberate / oversight / unknown**.

### EX-06 · The audit treadmill as a system property
- **Observation:** ~25 audits in 5 months; each selects a different lead persona to avoid
  anchoring; each therefore closes zero findings from its predecessor; completion claims
  are sometimes false (14/14 nav modules, "100% COMPLETE & LAUNCH-READY").
- **Noun-stripped:** The repo has a **finding lifecycle with no state machine**. Findings
  are emitted with no `open | fixed | wontfix | superseded` state, no owner, no
  re-verification date — so they cannot be closed, only re-discovered.
- **Why interesting:** This is the highest-leverage *process* primitive available, and it
  is nearly free. This audit's own `FINDINGS_REGISTER_2026-08-29.md` is a first instance.
- **Exit:** A findings-register template + CI check that a register's items are re-verified
  on a cadence.

---

## D — Doctrine gaps (the doctrine itself is missing a rule)

Per doctrine §16.9, recurring gaps should produce **explicit amendments**, not silent
workarounds. These are candidates for Pranay's decision.

| ID | Gap | Observed instance | Proposed amendment |
|---|---|---|---|
| D-01 | **Absence claims need executed evidence, not grep** | The prior audit asserted "no mypy" (false — configured and CI-blocking) and "no durable lease" (false — `AgentWorkLease` exists). Both falsifiable in one command. | Review Doctrine: *a claim that X does not exist must cite the executed command that would have found it.* |
| D-02 | **No lifecycle for review findings** | ~25 audits; zero cross-closure; false completion claims. | A Review Doctrine section on finding state (`open/fixed/wontfix/superseded`), owner, and re-verification date. |
| D-03 | **No rule for generated-mirror placement** | 4 doctrine mirror stubs; **one landed inside `frontend/src/types/`** — generator runaway. 190 `OPERATING_DOCTRINE.md` copies exist workspace-wide. | Propagation contract: define **where** mirrors may be written and add a guard against propagation into source trees. |
| D-04 | **No rule against deleting doctrine without recovery** | `motto_v4.md` deleted; 18 dependents orphaned. `motto_v5.md` deleted; 3 dependents orphaned. | Documentation Doctrine: deleting a governing document requires recovering or re-homing its dependents **in the same change**. |
| D-05 | **No completion-claim standard** | `NAVIGATION_TASKS.md` "14/14 DONE" (false); `UNIT1_FINAL_COMPLETION_SUMMARY.md` "100% COMPLETE & LAUNCH-READY" (contradicted). | Require completion claims to cite the verification command and its date. |

---

## Priority

| Rank | Item | Why |
|---|---|---|
| 1 | **RQ-06** (frontend state) | Largest evidence hole; cheap to close; may reclassify other findings |
| 2 | **EX-06** (findings lifecycle) | **Promoted.** This audit nearly duplicated six artifacts of in-flight parallel work. Highest-leverage process primitive; near-zero cost |
| 3 | **RQ-01** (extraction ceiling) | Blocks the most important architectural decision in the repo |
| 4 | **RQ-03** (RLS-exempt tables) | Potential P0; unknown whether safe or exposed |
| 5 | **RQ-04** (file split-brain) | Sizes R-03 |
| 6 | **RQ-05** (`proxy.ts`) | Possible lost security control |
| 7 | **RQ-02** (motto_v4 references) | Downgraded — content recovered; reference hygiene only |
| 8 | **EX-02** (epistemic UX) | Depends on Wave 5; genuinely unexplored |
| 9 | **EX-01** (IROPS trigger only) | **Narrowed** — design + code exist; only the trigger is open |
| 10 | **EX-03 / EX-05 / D-01…D-05** | Design and doctrine work; no code dependency |
| — | **EX-04** (connectivity tier) | **Deferred** — design exists; implement per Implementation Plan 5.1 |

---

## ⚠️ Coordination note — read before starting any item here

A **parallel agent is actively producing work in this repo right now** (confirmed
2026-08-29). Six artifacts appeared within hours:

```
Docs/exploration/JOURNEY_DEPENDENCY_GRAPH_2026-08-29.md            (R-12 design)
src/schemas/journey_graph.py                                        (R-12 code)
Docs/exploration/LIVE_CONNECTIVITY_INTEGRATION_2026-08-29.md        (CONNECTIVITY_TIER)
Docs/exploration/DURABLE_AGENT_LEASE_2026-08-29.md                  (R-11)
Docs/architecture/SERVER_DECOMPOSITION_PLAN_2026-08-29.md           (R-10)
Docs/design/FRONTEND_STYLING_UNIFICATION_PLAN_2026-08-29.md         (R-14)
```

All are **untracked** (`??` in `git status`). Before starting any exploration item:

1. `git status --short` and check `Docs/INDEX.md`.
2. Grep `Docs/` for the topic.
3. **Extend the existing artifact; do not create a parallel one** (doctrine §5).
4. Re-read live files immediately before editing (doctrine §10).

---

## Handoff rules

Per doctrine §16.2 / §16.3 / §16.8:
- A research conclusion becomes **decision-grade evidence** and is recorded under
  `DOCUMENTATION_DOCTRINE.md` — in the register or a dated ADR, **not only in chat**.
- An exploration result that survives becomes an **implementation task** in
  `IMPLEMENTATION_PLAN_2026-08-29.md`, preserving hypothesis, falsifier, and owner.
- A closed-as-no-go item is **recorded with its reason** so it is not re-proposed
  (doctrine §9: rejected directions are part of the record).
