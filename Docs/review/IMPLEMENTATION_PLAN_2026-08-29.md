# Implementation Plan — Waypoint OS Persona Council Audit

**Date:** 2026-08-29 · **Companion to:** `PERSONA_COUNCIL_MASTER_AUDIT_2026-08-29.md`,
`FINDINGS_REGISTER_2026-08-29.md`
**Doctrine basis:** `OPERATING_DOCTRINE.md` v8.0 §3 (proportional rigor), §4 (authorization),
§5 (canonical paths), §6 (semantic salvage), §15 (completion contract)

---

## 0. Ordering principle

Sequenced by **blast radius × dependency**, per the prior audit's §9 and Review Doctrine
§76. The rule applied throughout:

> **Finish a canonical path before starting a new one.**

That single rule resolves 12 of the 20 findings in this register, because most of them are
the same defect — *a replacement was built and the original was never retired.*

### Wave gates

Each wave has an **exit gate**. Do not start wave N+1 until N's gate passes.
Every item declares: invariant, blast radius, acceptance evidence (doctrine §15).

---

## Wave 0 — Preserve (do this first; it is cheap and it de-risks everything)

**Rationale:** A-14. The R-02/R-04/R-05 tenant-authority and integrity fixes, plus the new
epistemic primitives, exist **only in the uncommitted working tree**. Everything below
assumes they survive.

| # | Action | Invariant | Blast radius | Acceptance evidence |
|---|---|---|---|---|
| 0.1 | Classify every dirty file: *remediation* / *unrelated WIP* / *generated* | No dirty file is deleted unclassified | Working tree only | `git status --short` annotated, recorded in this doc's appendix |
| 0.2 | Commit the R-02/R-04/R-05 + epistemic remediation as **one atomic unit** | The tenant fix is durable | Git only | `git show --stat` reviewed; suite no worse |
| 0.3 | Resolve `frontend/next.config.ts` (deleted) vs `next.config.mjs` (untracked) | Exactly one Next config, tracked | Frontend build | `next build` succeeds; `git ls-files` shows one config |
| 0.4 | Save this audit's evidence artifacts (test output, mypy output) | Evidence is reproducible | Docs only | Files committed under `Docs/review/` |

> ⚠️ **Authorization note (doctrine §4 / §4.1).** 0.2 is a **git mutation (L3)**. Per the
> standing project rule it requires **explicit authorization from Pranay in this session.**
> Do not execute it on the audit's authority alone. Items 0.1, 0.3, 0.4 are L1
> (workspace mutation) and are authorized by the "audit and document" request.

**Exit gate 0:** Working tree classified; remediation durable or explicitly held with an
owner and a date; one Next config tracked.

---

## Wave 1 — Stop the evidence apparatus from lying (P0)

**Rationale:** A-01. You cannot prioritise anything else while the only honest measurement
is muted and two placebo gates report green. This is the highest-leverage item in the plan
and it is **small** — roughly four edits.

| # | Finding | Action | Invariant | Blast radius | Acceptance |
|---|---|---|---|---|---|
| 1.1 | A-01 | Add `budget_health` to `_check_blocks_ci()` in `scripts/verify_d6_gate_snapshot.py:29-67` | A failing `blocks_ci` gate fails CI | CI only | **S2:** revert the change → CI red; re-apply → CI red on a seeded failing budget. **S3:** seed `blocks_ci: true` → CI must fail |
| 1.2 | A-01 | Add `min_accuracy` to the `budget` entry in `src/evals/audit/manifest.yaml:3-7` | Budget category has a real threshold | Eval gates | **S2:** set `min_accuracy: 0.6` → `categories.budget` reports `blocks_ci: true` (today it reports `false` at F1 0.2857) |
| 1.3 | A-01 | Rewrite the three assertions in `tests/evals/test_d6_gate_snapshot.py:27,56,142` that assert `blocks_ci is False` | Tests assert the real invariant, not the muted one | Eval tests | **S2:** seeded failing budget → tests fail |
| 1.4 | A-01 | Regenerate `data/evals/d6_audit_gate_snapshot.json` (stale — generated 2026-06-23 by older code) | Snapshot reflects current `snapshot.py` | Eval data | Snapshot notes match current code strings |
| 1.5 | A-01 | Wire real pipeline results into `build_gate_snapshot()` defaults (`snapshot.py:314-316`) so extraction/pipeline stop comparing expected-to-itself | Gates measure real output | Eval core | `blocks_ci` becomes falsifiable; expect **extraction F1 to drop from 1.0** — that is the point |

**Exit gate 1:** A deliberately seeded budget failure **fails CI**. Until that is true, the
quality signal is decorative.

> **Expectation setting:** 1.5 will make previously-green gates red. That is the correct
> outcome — the gates were never measuring anything. Announce it before it happens so it is
> not mistaken for a regression.

---

## Wave 2 — Close the tenant-authority and security gaps (P0/P1)

| # | Finding | Action | Invariant | Blast radius | Acceptance |
|---|---|---|---|---|---|
| 2.1 | R-03 | Determine whether `data/trips/*.json` (1,635 files) is written under `TRIPSTORE_BACKEND=sql`; if yes, stop it; if no, retire the store | Exactly one trip store in SQL mode | Persistence | Runtime probe + mtime observation; then `DEPRECATED` marker with deletion date |
| 2.2 | A-19 | Convert `Depends(get_db)` → `get_rls_db` in the remaining routers (`analytics.py:21`, `audit.py:23`, `auth.py:30`, `team.py:21`, `frontier.py:18`, `integrations.py:23`) — or record a reasoned deviation per router | Every router resolving agency data is RLS-scoped | 6 routers | **S2:** cross-tenant probe fails closed. **S3:** mutation removing `set_rls_agency` → test fails |
| 2.3 | A-19 | Audit the 4 `RLS_EXCLUDED_AGENCY_TABLES` (`audit_logs`, `emotional_state_logs`, `ghost_workflows`, `legacy_aspirations`) for agency filters | No cross-tenant read path | 4 tables | Documented per-table verdict; add filters where missing |
| 2.4 | A-19/R-10 | Add a CI drift gate: `alembic check` (or autogenerate diff) — closes A-20 | Models and migrations cannot diverge | CI + migrations | **S3:** add a column to a model → CI fails |
| 2.5 | R-15 | Make `privacy_guard.check_trip_data()` **log an audit event** at minimum when it no-ops outside dogfood (`privacy_guard.py:484-486`) | Silent no-op is impossible | PII guard | Audit event observable in tests |
| 2.6 | R-15 | Reconcile the disagreement: Layer 2 (SpaCy) is fail-closed in prod (`:412-428`) while the trip-data gate is fail-open | One PII posture, explicitly chosen | PII guard | ADR recording the decision + rationale |
| 2.7 | A-18 | Rotate the `OPENAI_API_KEY` in `.env`; move `DATABASE_URL` to env with no committed-password default | No live credential at rest in repo | Secrets | `git log -p` shows the committed dev password removed from `core/database.py:22` |
| 2.8 | A-18 | Make `SPINE_API_DISABLE_AUTH` **hard-fail** outside test (today `startup_assertions.py:162-167` only warns) | Auth cannot be silently off | Security core | **S2:** set the flag in staging → process refuses to start |

**Exit gate 2:** Cross-tenant probe fails closed across all routers; no credential in-repo;
auth kill switch is fail-closed.

---

## Wave 3 — Consolidate canonical paths (P1 — the systemic fix)

**Rationale:** A-04, A-05, A-06, A-07, A-09, A-11. Doctrine §5 is the most-violated rule.
These are **one problem with many instances**. Each consolidation must ship with a
**deletion date** for the retired side — that is the missing control (see §Retirement gate
below).

| # | Finding | Consolidate | Retire (with date) | Acceptance |
|---|---|---|---|---|
| 3.1 | A-04 | `core/audit.py:145 audit_logger()` | `core/audit_bridge.py` — **zero prod callers, delete** | Test suite unchanged after deletion |
| 3.2 | A-04 | `services/membership_service.py` | `persistence.py:2511 TeamStore` (already marked DEPRECATED) | No import remains; marker removed by deletion, not by comment |
| 3.3 | A-04 | `scoring/__init__.py` 2D engine | `services/inbox_projection.py:461-475` legacy 1D fallback | Priority output identical on a golden set |
| 3.4 | A-04 | One audit store — **recommend the PostgreSQL `audit_logs` + hash chain** | File hash-chain `persistence.py:2056-2086` | Chain verification preserved in the surviving store; **S3:** tamper a row → verification fails |
| 3.5 | A-04 | One auth pass — collapse `core/middleware.py:46-109` into the `core/auth.py` dependency path | The middleware's duplicate JWT decode | **S3:** remove the decode → no auth bypass test passes |
| 3.6 | A-04 | One `BaseSettings` config module (replaces 150 scattered `os.getenv`) | Ad-hoc `os.getenv` reads | **S2:** unset a required var → fail fast at startup |
| 3.7 | A-04 | One vision client path (`src/llm/*`) | `src/extraction/*_vision*.py` third path | Golden-set extraction parity |
| 3.8 | A-05 | One frontend API client (`lib/api-client.ts`) | 104 raw `fetch(` sites; 30 ad-hoc files | New ESLint rule bans bare `fetch(`; rule is CI-blocking |
| 3.9 | A-06 | Generated TS types as the single contract | Hand-written `types/spine.ts`, `audit.ts`, `governance.ts`, `auth-session.ts` | **Drift gate in CI:** regenerate → diff → fail on delta |
| 3.10 | A-11 | One marketing surface | `app/v2`, `app/v3`, `app/v4` (keep `v5`) | 3 dirs deleted; routes 301 or removed |
| 3.11 | A-12 | Real `middleware.ts` **or** delete `src/proxy.ts` | The inert file | Decision recorded in an ADR |
| 3.12 | A-07 | One doc tree | Decide `Docs/` vs `frontend/docs/`; fix the `index.md`/`INDEX.md` inode collision | One tree; collision resolved; CI catches case-duplicates |
| 3.13 | A-09 | ADR template with `Supersedes:` / `Superseded-By:` | Ad-hoc ADR naming | 22 ADRs back-filled; renumbering plan for 003/004/005 |
| 3.14 | A-10 | Reconcile `IDEA_PAD.md` against git | The 121-item stale `inbox` | Shipped IDEA-120/122/123/124 marked `done`; WIP registry re-dated |

### Retirement gate (new control — this is the systemic fix)

> **No new canonical path may merge without the old path's deletion date recorded in the
> same change.** A `DEPRECATED:` comment is not a retirement plan (doctrine §5 requires the
> plan *before* creating the parallel path).

Implement as: a PR/ADR checklist item + a CI grep that fails when a file marked
`DEPRECATED` exceeds its recorded deletion date.

**Exit gate 3:** Every duplicate pair has one survivor and one deletion date; the
retirement gate is enforced mechanically.

---

## Wave 4 — Quality and regression protection (P1)

| # | Finding | Action | Acceptance |
|---|---|---|---|
| 4.1 | A-13 | Triage the **booking/documents/extraction super-cluster** (130 failures: `test_booking_collection` 39, `test_booking_documents` 29, `test_document_extractions` 27, `test_extraction_attempts` 14, `test_booking_data` 21) | Cluster green; **S2** per fix (fails before, passes after) |
| 4.2 | A-13 | Triage `test_trip_canonical_roundtrip.py` (49 failures) | Green; **S2** |
| 4.3 | A-13 | Triage the ERROR clusters (`test_call_capture_phase2` 26, `test_run_state_unit` 17, `test_override_api` 17, `test_state_contract_parity` 12, `test_run_lifecycle` 11, `evals/test_d6_gate_snapshot` 11) — **errors usually mean fixture/conftest faults, not product bugs** | Errors → 0 |
| 4.4 | A-13 | Establish the CI-identical baseline (supply `DATABASE_URL`, apply CI's two `--ignore` flags) | A committed, dated baseline number so drift is measurable |
| 4.5 | A-16 | Add ratcheting coverage thresholds to `vitest.config.ts` (today none → coverage can never fail) | `test:coverage` fails below threshold |
| 4.6 | A-16 | Add one smoke e2e for the booking path (`frontend/tests/` is empty; no e2e exists) | E2E runs in CI |
| 4.7 | A-15 | Reduce `any` in prod code (65 today; hotspot `workbench/DecisionTab.tsx` 9 × `as any`); resolve the 4 newly-added `eslint-disable`s | Threshold gate; no new suppressions without justification |
| 4.8 | A-08 | Recover `motto_v4.md` from git history; if unrecoverable, mark all 18 references **Unknown** and re-derive the rules into `OPERATING_DOCTRINE.md` | No file references a nonexistent governing rule |
| 4.9 | A-07 | Fix CHANGELOG: remove the frontend-only scope line, backfill the 6 August feature commits | CHANGELOG reflects full-stack reality |

**Exit gate 4:** Backend suite green (or a documented, triaged residual list with owners);
frontend coverage gates enforced; no dangling doctrine references.

---

## Wave 5 — Complete the epistemic layer (P1 — the long-term payoff)

**Rationale:** R-06 is 2/3 landed and is the highest-value *architectural* upgrade in the
repo. It is what makes the system able to say "I know this" vs "I assumed this."

| # | Action | Invariant | Acceptance |
|---|---|---|---|
| 5.1 | Add `CONNECTIVITY_TIER` (`MOCK / SIMULATED / LIVE`) — the missing third primitive | Every external capability declares its connectivity | `live_tools.py` reports it; **S3:** flip to MOCK → `can_make_financial_claims` is False |
| 5.2 | Attach `EpistemicStatus` to **every** `TripPacket` slot (enum exists at `packet_models.py:91`; mapping at `extractors.py:1738-1749` — wiring is the remaining work) | No slot is unlabelled | Packet schema validation rejects an unlabelled slot |
| 5.3 | Populate `AssumptionRecord` (exists at `packet_models.py:101`) from the intake path | Assumptions are explicit and operator-acknowledgeable | A defaulted slot produces an `AssumptionRecord` with rationale |
| 5.4 | Surface epistemic status in the UI — unknown must **look** unknown | User can distinguish fact from inference | Visual review + a11y check |
| 5.5 | Compose `assert_tier_capability` into **every** endpoint that writes success events or makes financial claims (today gated on a subset — `concierge` only) | No ungated financial-mutation path | **S3:** remove the gate from one endpoint → test fails |

**Exit gate 5:** A trip packet can be inspected and every field's truth-state read; no
financial claim can be emitted from a MOCK/SIMULATED tier.

---

## Wave 6 — Extensions and opportunities (P2 — after the foundation is sound)

> ⚠️ **Read before executing this wave.** A parallel agent has already produced designs for
> four of these items (A-21). **Do not re-specify — implement against the existing
> artifacts.** Verify each is still current before starting (doctrine §10).

| # | Finding | Action | Notes |
|---|---|---|---|
| 6.1 | R-11 | **Implement per `Docs/exploration/DURABLE_AGENT_LEASE_2026-08-29.md`** — heartbeat refresh, fencing token, `STALE` sweep, agency scoping. `ExecutionLease` (`runtime.py:52-82`) is dead code with zero call sites | Real risk: a task running >60s is re-acquirable → double-execution. The design independently reached the same diagnosis: the gap is *liveness/conflict/reconciliation*, not the lease itself |
| 6.2 | R-12 | **Do NOT re-design.** `src/schemas/journey_graph.py` (untracked) + `Docs/exploration/JOURNEY_DEPENDENCY_GRAPH_2026-08-29.md` exist. Remaining work: the **IROPS trigger path** (the graph already has 4 importers — it is not orphaned) | See backlog EX-01, narrowed |
| 6.3 | R-16 | Trace-correlation reader + CI assertion of event flow | OTel spans are real but have no consumer. No existing design — this is genuinely open |
| 6.4 | R-14 | **Implement per `Docs/design/FRONTEND_STYLING_UNIFICATION_PLAN_2026-08-29.md`** | Two-generation styling |
| 6.5 | R-13 | Resolve nav rollout-gate drift (`nav-modules.ts` `complete: false`) | Needs a **product decision**, not a code fix |
| 6.6 | R-10 | **Implement per `Docs/architecture/SERVER_DECOMPOSITION_PLAN_2026-08-29.md`** (`create_app()` factory + runtime lifecycle; the plan explicitly rejects microservices — consistent with this audit's "do not rewrite") | `server.py` already reduced 3,719 → 3,186 |
| 6.7 | A-17 | Fix `WelcomeModal` a11y (no `role="dialog"`/`aria-modal`) | Small; bundle with other frontend work |
| 6.8 | A-21 | **Track the six in-flight artifacts** (all untracked) in the shared register and confirm ownership | Prevents this wave from being duplicated again |
| 6.9 | R-06 | Implement `CONNECTIVITY_TIER` per `LIVE_CONNECTIVITY_INTEGRATION_2026-08-29.md:201-252` — **design exists, code does not** | Also listed as 5.1; the orthogonality rule (tier ⊥ `RealityTier`) is the key design element |

---

## Sequencing rationale (why this order)

1. **Wave 0** because uncommitted P0 security work is the single largest loss risk.
2. **Wave 1 before Wave 4** — fixing tests while the gates are tautological produces
   effort with no signal. Make the instrument honest, then read it.
3. **Wave 2 before Wave 3** — consolidation touches persistence and auth; doing it over
   an unsealed tenant boundary risks reintroducing R-02/R-03.
4. **Wave 3 before Wave 6** — every Wave-6 item would otherwise be built on a duplicated
   foundation and inherit the split.
5. **Wave 5 last-but-one** because it is the highest-value *architectural* item but
   depends on stable canonical paths to attach to.

---

## Deliberately excluded (and why)

| Candidate | Why excluded |
|---|---|
| Rewriting the backend | Doctrine §1/§6: the deterministic core, RLS, reality tiers and executable gates are real assets. The prior audit reached the same conclusion — **do not rewrite**. |
| Replacing the eval framework | The framework is fine; the *wiring* is wrong (A-01). Fix the wiring. |
| Deleting `data/trips/*.json` before 2.1 | Blast radius unknown until the runtime probe resolves whether SQL mode still writes them. |
| Bulk-renaming all ADRs | Wait until the `Supersedes:` mechanism exists, or the rename destroys lineage. |
| Committing anything | Git mutation (L3) requires explicit authorization from Pranay in-session (standing rule; doctrine §4.1). |

---

## Residual risk after full execution

| Risk | Why it remains | Next check |
|---|---|---|
| Extraction quality is genuinely poor (budget F1 0.2857; medium 0.0, hard 0.0) | Wave 1 only makes the number **visible**, not better | After 1.5, decide: improve the extractor, or lower the threshold with a documented rationale |
| Wave 1.5 will turn gates red | Correct outcome, but will look like a regression | Announce before execution |
| Cross-tenant exposure on the 4 RLS-exempt tables | Unknown until 2.3 is done | 2.3 |
| Parallel agents may touch the same surfaces | The tree is already being edited concurrently (doctrine §10) | Re-read live files before each edit; re-run gates before claiming done |
| `AssumptionRecord`/`EpistemicStatus` may be partially wired when shipped | Landed uncommitted; needs the Wave-5 wiring work | 5.2/5.3 |

---

## Appendix A — Working-tree classification (Wave 0.1)

Recorded 2026-08-29 from `git status --short`. 40+ tracked files modified.

| Class | Files | Notes |
|---|---|---|
| **Remediation (must be preserved)** | `spine_api/core/auth.py`, `spine_api/routers/{commission,messaging,customer_memory,group_booking,multimodal,price_lock}.py`, `src/intake/{packet_models,extractors}.py` | R-02/R-04/R-05/R-06 fixes. **Not in HEAD.** |
| **Refactor in progress** | `spine_api/server.py` (−639/+ lines), `spine_api/contract.py` (+299), `spine_api/core/audit.py`, `spine_api/models/audit.py` | R-10 partially addressed |
| **Generated context (regenerable)** | `Docs/context/agent-start/*`, `frontend/docs/context/agent-start/*`, `spine_api/Docs/context/agent-start/*`, `frontend/src/Docs/context/agent-start/*` | Regenerate via `/Users/pranay/Projects/agent-start` |
| **New doctrine mirror stubs** | `frontend/OPERATING_DOCTRINE.md`, `frontend/src/OPERATING_DOCTRINE.md`, `frontend/src/types/OPERATING_DOCTRINE.md`, `spine_api/OPERATING_DOCTRINE.md` | R-01 fix. Correct content. **Why one landed inside `frontend/src/types/` is unexplained — generator runaway.** |
| **Deletions needing decision** | `frontend/next.config.ts` (deleted, replacement untracked), `motto_v5.md` (deleted), `frontend/motto_v2.md` (deleted), `spine_api/motto_v{2,3}.md` (deleted, −1,278) | Doctrine-archival rule: archive, do not silently delete. Verify these are recoverable from git. |
| **Frontend nav/UI in progress** | `frontend/src/lib/nav-modules.ts`, `components/layouts/Shell.tsx`, `components/navigation/BackToOverviewLink.tsx`, `app/(agency)/documents/*`, `app/(agency)/workbench/PageClient.tsx` | Related to R-13/R-14 |
| **Hooks/scripts** | `scripts/hooks/{commit-msg,pre-commit,prepare-commit-msg}` | Commit-gate tooling — review before trusting |
| **Other** | `pyproject.toml`, `frontend/package.json`, `frontend/pnpm-workspace.yaml`, `frontend/tsconfig.json`, `.github/workflows/ci.yml`, `notebooks/*`, `inspect_page.py`, `frontend/instrumentation.ts` | Mixed; classify before any commit |
