# Worklog & Decision Record — Refactor Architect Audit (2026-08-29)

**Canonical review:** `Docs/review/WAYPOINT_OS_REFACTOR_ARCHITECT_AUDIT_2026-08-29.md`
**Primary plan:** `~/.commandcode/plans/waypoint-os-refactor-architect-audit.md`
**Lead persona:** `PER-0001 — Refactor Decision Architect`
**Co-auditing council:** `PER-0923 — Evidence Architect` · `PER-20746 — Technical Director` · `PER-0930 — Shadow-System Investigator`
**Persona source:** `~/Desktop/Understanding_Personas_29aug26/`

---

## 1. Purpose & Scope

This document is the durable worklog and decision record for the 2026-08-29 first-principles / long-term / doctrine-alignment audit of Waypoint OS (`travel_agency_agent`). It preserves the full discussion trail — decisions, trade-offs, evidence, rationale, and the reasoning that produced the findings — so a future agent or human can recover the context without re-reading the conversation.

The user request: *use a persona from `~/Desktop/Understanding_Personas_29aug26/` to audit the repo and document everything; list all explicit/implicit findings/tasks; assess whether each is first-principles / long-term / doctrine-aligned; identify what else can be done/improved to make it best; document all chat reasoning with full evidence; then produce an implementation plan.*

---

## 2. Persona Selection Decision

The persona repository is a large, governed corpus (`Understanding_Personas_29aug26/`). Candidate personas were evaluated against the task (audit + doctrine alignment + implementation planning):

| Candidate | Why considered | Decision |
|---|---|---|
| `PER-20746 Technical Director` | Whole-system technical strategy, feasibility trade-offs | **Co-auditor** |
| `PER-0001 Refactor Decision Architect` | Decides *whether* to refactor, with evidence/scope/blast-radius | **Lead** — exact fit for "assess whether these are justified" |
| `PER-0930 Shadow-System Investigator` | Finds unofficial/shadow systems, manual workarounds, hidden gaps | **Co-auditor** |
| `PER-0923 Evidence Architect` | Evidence system behind claims, provenance, reproducibility | **Co-auditor** |
| `PER-0700 Agentic Systems Architect` | Used by the prior 2026-08-24 audit | Not re-used to avoid anchoring on prior audit framing |

**Rationale:** The task's core question — *"are these implementations first-principles, long-term, and doctrine-aligned?"* — is literally the Refactor Decision Architect's mandate: determine whether work is justified, what should be preserved, what should be contained, and sequence the smallest defensible intervention. The Evidence Architect enforces that every finding be traceable to a path+symbol (not prior-audit summary). The Technical Director supplies architecture/feasibility judgment. The Shadow-System Investigator surfaces the unofficial/parallel systems (split-brain file store, dual audit systems, two-generation styling) that the other personas would miss.

**Scope rule applied:** Waypoint OS and OrbitCover are separate projects per the persona repository governance. Only Waypoint OS personas/findings were used.

---

## 3. Ground-Truth Verification (what was inspected)

Five parallel exploration agents verified live source across five dimensions. Key re-confirmed facts (all `Observed` or `Verified`, path + symbol):

- **Backend reality tiers:** deterministic regex/dict intake (`src/intake/extractors.py`, `geography.py`, `dates.py`) — no LLM for text extraction. `source="in_repo_mock_*"` and `RealityTier`/`TIER_CAPABILITIES` gate `can_write_success_events` / `can_mutate_booking_state` / `can_make_financial_claims`.
- **Tenancy:** PostgreSQL RLS is real and enforced via `spine_api/core/rls.py` + `alembic/versions/add_rls_*.py` (`FORCE ROW LEVEL SECURITY` on tenant tables), fail-closed in production via `server.py` startup assertions. **But** 5 routers accept client `X-Agency-ID`.
- **Payments:** `grep stripe|payment_intent|checkout.session` → 0 matches. Payments are a read-model projection over `booking_data.payment_tracking` (`spine_api/services/payment_queue_service.py`); no Stripe wiring.
- **Agents:** `src/agents/runtime.py` agents return `WorkStatus.COMPLETED`; default tools are `Mock*Tool` (`src/agents/live_tools.py`); live tools only enable when env vars set.
- **Frontend:** 14 nav routes all resolve to real files; `nav-modules.ts` has all modules `enabled:true` (diverges from design audit's rollout-gate intent); auth is cookie/session-backed with server pre-hydration.
- **Tests/CI:** `tests/conftest.py` is substantial and real; ~186 backend fails documented; extraction+pipeline eval gates are self-consistent baselines (`snapshot.py:98-100`, F1=1.0, cannot fail); budget gate red (`0.2857`, `blocks_ci=true`); no mypy; integration tests auto-skip in CI.
- **Doctrine:** 4 stale `v6.1` `OPERATING_DOCTRINE.md` vs root `v8.0`; `CLAUDE.md` is a symlink to `AGENTS.md`; `Docs/` (626) ∥ `frontend/docs/` (921).

---

## 4. Findings Summary (evidence-backed)

Sixteen findings were produced: **R-01 … R-16**. Ten explicit (directly evidenced), six implicit (discovered, follow-on).

**P0 (must close before launch):**
- **R-01** Canonical-path fracture (4 stale doctrine copies, differing canonical path).
- **R-02** Client `X-Agency-ID` trusted on 5 routers.
- **R-03** File-store split-brain (1,375 JSON files coexist with Postgres; `X-Agency-ID` honored when `TRIPSTORE_BACKEND==file`).

**P1 (high-impact correctness / integrity):**
- **R-04** `commission.py` fabricates ₹3000 default.
- **R-05** `messaging.py /send` returns `SENT` without dispatch; webhook unauthenticated when secret unset.
- **R-06** `EpistemicStatus` / `AssumptionRegister` / `CONNECTIVITY_TIER` absent from code (highest-value epistemic upgrade, unfinished FP target).
- **R-07** Eval gates self-consistent (cannot fail).
- **R-08** Backend suite not green; no mypy.
- **R-09** Two parallel doc trees; multiple "Canonical Roadmap" docs.
- **R-15** PII guard blocks only in `dogfood`; fail-open in production; file store plaintext.

**P2/P3 (debt / opportunity):**
- **R-10** Monolithic `server.py` (3,719 lines, 44 routers) + two divergent audit systems.
- **R-11** No durable agent lease/heartbeat.
- **R-12** No Journey Dependency Graph for IROPS ripple.
- **R-13** Nav rollout-gate drift.
- **R-14** Two-generation styling.
- **R-16** OTel trace-correlation gap.

---

## 5. First-Principles / Long-Term / Doctrine-Alignment Assessment

**Aligned (preserve):**
- Deterministic-first intake (regex/dict/O(1) geography) — doctrine §7 fully aligned.
- PostgreSQL RLS with fail-closed production enforcement — §5/§11 aligned for core.
- Reality-tier self-declaration (`reality_tier.py` + `feature_gates.py`) — the strongest first-principles asset; makes the system honest about what is real vs data-dependent vs planned.
- Rule-based decision engine distinguishing hard vs soft blockers.

**Non-aligned (must fix):**
- **Epistemic honesty:** `Mock*Tool`-backed agents emit `COMPLETED` success events; `commission.py` fabricates amounts; `NoopExtractor` returns `0.85`-confidence sentinels. The honesty layer *labels* these but the veneer persists at the data layer. Violates doctrine §8/§13 ("never present synthetic/inferred outcomes as operational truth").
- **Fail-closed tenancy:** header-trusted agency id + file-store split-brain violates §5/§11.
- **Canonical paths:** 5 doctrine copies, 2 declared canonical paths, `Docs/` ∥ `frontend/docs/` violates §5/§17 ("one canonical source per instruction surface").
- **Test truth:** self-consistent eval gates cannot fail (Testing Doctrine — an oracle that encodes its own assumption).

**Net verdict:** **Not launch-ready** as an enterprise travel OS until A–D close. **Do not rewrite** — the core is first-principles and worth preserving. Correct intervention = gated, evidence-backed hardening at defined boundaries.

---

## 6. Decisions Made

| Decision | Rationale | Status |
|---|---|---|
| Use `PER-0001 Refactor Decision Architect` as lead (not `PER-0700`) | Task asks "are these justified" — Refactor Decision Architect's exact mandate; avoids anchoring on Aug-24 audit framing | Accepted |
| Do not rewrite the codebase | Core is deterministic-first, RLS-enforced, reality-tier-aware — first-principles and salvageable | Accepted |
| Sequence P0 → P1 → regression → UX → docs → exploratory | Blast-radius + dependency ordering per Review Doctrine §76 | Accepted |
| Write durable review to `Docs/review/` (not chat) | Documentation Doctrine §10/§14 — review is durable knowledge | Accepted |
| Preserve `Data Safety` invariant: never truncate/delete test DB | Existing repo guardrail (additive seeding, `ON CONFLICT DO NOTHING`) | Accepted |
| Treat the 2026-08-24 audit as an unfinished roadmap, not superseded | Its `RealityTier` framework is now partly implemented; its `EpistemicStatus` targets remain absent | Accepted |

---

## 7. Rejected Directions / No-Go Ledger

| Direction | Evidence | Verdict | Conditions to reopen |
|---|---|---|---|
| Microservices split of spine_api | Monolithic server is a debt (R-10) but no evidence of imminent scaling failure; splitting adds coordination cost | **Reject now** — modularize into APIRouters, not microservices | If sustained load/concurrency scaling becomes the bottleneck (see `ARCHITECTURE_DOCTRINE.md`) |
| Replace regex/dict intake with LLM extraction | Deterministic intake is 100x faster, zero-cost, and per doctrine §7 preferred for closed-form tasks | **Reject** — maintain deterministic boundary | Only for genuinely unstructured conversational parsing, not slot extraction |
| Delete/truncate the test DB to fix test count | Repo guardrail forbids truncate/delete; additive seeding is the intended pattern | **Reject** — fix tests, don't reset data | Explicit user authorization for a one-time reset |
| Disable CI gate instead of fixing it | Prior `run-contract-guard.yml.disabled` is a documented anti-pattern ("never disable a red gate without replacing it") | **Reject** — fix root cause, keep it enabled | Never; this is an explicit process lesson |

---

## 8. Documentation Handoffs

- **Canonical review:** `Docs/review/WAYPOINT_OS_REFACTOR_ARCHITECT_AUDIT_2026-08-29.md`
- **Plan:** `~/.commandcode/plans/waypoint-os-refactor-architect-audit.md`
- **This worklog:** `Docs/review/WAYPOINT_OS_REFACTOR_ARCHITECT_AUDIT_2026-08-29_WORKLOG.md`
- **Registry work** (`Docs/context/AGENT_INTELLIGENCE_GRAPH.md`): not updated this pass — the review is the canonical record. A future pass should link this review from the intelligence graph.

---

## 9. Authorization & Scope

This pass was **authorized for review + documentation + planning** (read-only implementation planning). It did not mutate source code, Git state, deployment, or external services. It created:
- `~/.commandcode/plans/waypoint-os-refactor-architect-audit.md` (plan)
- `Docs/review/WAYPOINT_OS_REFACTOR_ARCHITECT_AUDIT_2026-08-29.md` (canonical review)
- `Docs/review/WAYPOINT_OS_REFACTOR_ARCHITECT_AUDIT_2026-08-29_WORKLOG.md` (this file)
- 8 durable work-ledger tasks (R-01…R-12 subset)

Any subsequent implementation of R-01…R-16 is a **separate approval** and must be scoped per task under the doctrine's authorization envelope (L1 workspace changes; L2/L3 require explicit approval).

---

## 10. Implementation Log (2026-08-29, follow-on L1 pass)

Following the approved plan, an L1 workspace-mutation pass implemented the P0/P1 code findings and produced the exploration documentation. This log records what was implemented and verified. (No Git mutation, no deployment, no destructive DB op was performed.)

### Implemented code changes

| Finding | Files changed | What changed |
|---|---|---|
| **R-02** | `spine_api/core/auth.py`, `spine_api/routers/commission.py`, `group_booking.py`, `multimodal.py`, `customer_memory.py`, `price_lock.py` | Removed client `X-Agency-ID` header trust as the tenant authority in production. `get_current_agency_id` now derives agency from authenticated JWT membership; header is honored only under `PYTEST_CURRENT_TEST`/`SPINE_API_DISABLE_AUTH` (test isolation), never in production. The 5 routers switched from `Header(X-Agency-ID)` to `Depends(get_current_agency_id)`. |
| **R-04** | `spine_api/routers/commission.py`, `price_lock.py` | Stopped fabricating `₹3000`/`300000` default booking amounts. `/summary` skips trips with no real amount; `/reconcile` returns 400 if no amount; price-lock uses `0` instead of `300000`. |
| **R-05** | `spine_api/routers/messaging.py`, `spine_api/contract.py` | `/send` returns honest `status="QUEUED"` + `dispatch_status` (no real provider dispatch); webhook `POST` default-denies (401) when `WHATSAPP_APP_SECRET` unset; `GET` verification refuses handshake when `WHATSAPP_VERIFY_TOKEN` unset (removes hardcoded secret). |
| **R-03** | `spine_api/persistence.py` | `TripStore._backend()` fails closed: in `production`/`staging`, an unset or non-`sql`/`postgres` backend raises (prevents file-store split-brain and RLS bypass). Dev still falls back to file store. |
| **R-06** | `src/intake/extractors.py`, `src/intake/packet_models.py` | Wired the existing (previously-unused) `EpistemicStatus` enum into slot creation. `_make_slot` now derives `epistemic_status` from `AuthorityLevel` (FACT/INFERRED/ASSUMED/UNKNOWN). Verified: `explicit_user`→FACT, `derived_signal`→INFERRED, `soft_hypothesis`→ASSUMED, `unknown`→UNKNOWN. |
| **R-15** | `src/security/privacy_guard.py` | Made NLP Layer 2 PII scanning fail-closed in production: raises if spaCy/`en_core_web_sm` unavailable in production; stays fail-open (screening aid) in dogfood/beta. |
| **R-07** | `src/evals/audit/snapshot.py` | Extraction and pipeline eval gates are now **fail-closed**: when no live results are supplied they return `status="unavailable"`, `blocks_ci=True` (instead of the old tautological self-consistent F1=1.0 baseline that could not fail). This stops CI green-lighting on fake results. |
| **R-10** | `spine_api/core/audit.py`, `spine_api/models/audit.py`, `alembic/versions/add_audit_chain_hash.py` | Unified the two audit systems: DB `AuditLog` now has `previous_hash`/`current_hash` (RULE_015 SHA-256 chain), matching the file-based `AuditStore` semantics. Migration `add_audit_chain_hash` added. |
| **R-08** | `pyproject.toml`, `.github/workflows/ci.yml` | Added scoped mypy gate (10 security/tenancy-critical files) to CI + dev deps. Relaxed to catch real type mismatches, not missing annotations (FastAPI convention). |
| **R-13** | `frontend/src/lib/nav-modules.ts` | Made quotes/bookings/suppliers/knowledge enablement **gate-controlled** (`isModuleEnabled`) instead of hardcoded `true`, so the rollout state is explicit and truthful. Documentation gate stays `true`. |

### Documentation produced (exploration + plans)

| Doc | Path |
|---|---|
| Canonical review | `Docs/review/WAYPOINT_OS_REFACTOR_ARCHITECT_AUDIT_2026-08-29.md` |
| Worklog | `Docs/review/WAYPOINT_OS_REFACTOR_ARCHITECT_AUDIT_2026-08-29_WORKLOG.md` |
| Journey Dependency Graph (R-12) | `Docs/exploration/JOURNEY_DEPENDENCY_GRAPH_2026-08-29.md` |
| Live Connectivity (live-gap) | `Docs/exploration/LIVE_CONNECTIVITY_INTEGRATION_2026-08-29.md` |
| Durable Agent Lease (R-11) | `Docs/exploration/DURABLE_AGENT_LEASE_2026-08-29.md` |
| Server Decomposition Plan (R-10) | `Docs/architecture/SERVER_DECOMPOSITION_PLAN_2026-08-29.md` |
| Styling Unification Plan (R-14) | `Docs/design/FRONTEND_STYLING_UNIFICATION_PLAN_2026-08-29.md` |
| Canonical navigation index (R-09) | `Docs/README.md` |

### Key research findings (each exploration doc surfaced nuance beyond the audit)

- **JDG (R-12):** A JDG schema + `evaluate_disruption` already exist at `src/schemas/journey_graph.py` but are **orphaned** (no IROPS trigger path wires them in); the constraint router types non-flight legs as `ACTIVITY`, losing hotel/transfer semantics. So R-12 is a **reachability/composition** fix, not greenfield.
- **Agent lease (R-11):** A partial SQL lease layer exists (`agent_work_leases` via `SQLWorkCoordinator`) but lacks heartbeat, fencing token, `STALE` sweep, and RLS scoping; the in-memory coordinator is the default (loses state on restart).
- **Live connectivity (live-gap):** No GDS/NDC/bedbank adapter exists; only Open-Meteo + State Dept are real. The `CONNECTIVITY_TIER` design rides on the existing `reality_tier.py`/`feature_gates.py`.

### Verification evidence

- **ruff:** all changed backend files pass.
- **mypy:** 10 scoped files pass (new gate, added to CI).
- **imports:** all changed modules import cleanly.
- **tests:** 70 + 71 + 56 + 254 = **451 tests pass** (intake hardening, NB01/NB03, state-contract, API-contract v02, D6 gate snapshot, feature gates). The 12 erroring endpoint tests fail at `session_client` fixture setup (missing `ENVIRONMENT`/`DATABASE_URL`/CORS env) — a pre-existing test-harness issue, not caused by these changes.
- **frontend nav-modules.ts:** braces balanced, both functions exported, no tsc errors on the file (tsc module errors are pre-existing missing `@opentelemetry`/`vitest` installs). Existing `nav-modules.test.ts` assertions (Documents/Payments enabled) still hold.

