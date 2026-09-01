# Consolidated Findings & Tasks Register — Explicit + Implicit (2026-08-31)

**Date:** 2026-08-31 · **Authoritative current-truth register.**
**Companion to:** `PERSONA_COUNCIL_AUDIT_2026-08-31.md`, `ALIGNMENT_EVALUATION_2026-08-31.md`, `IMPLEMENTATION_PLAN_2026-08-31.md`
**Git HEAD:** `8ece02e` · **Working tree:** 48 modified + ~30 untracked (uncommitted P0 remediation; see A-14).
**This register is a live re-verification. It supersedes the status columns of `FINDINGS_REGISTER_2026-08-29.md` and `FINDINGS_TASKS_CONSOLIDATED_2026-08-30.md`, but does not delete them (doctrine §6).**

**Legend**
- **Type:** `E` = explicit (documented elsewhere) · `I` = implicit (discovered by audit)
- **Truth:** Observed / Verified / Inferred / Unknown (doctrine §2)
- **FP** first-principles sound · **LT** long-term coherent · **DOC** doctrine-aligned
  Verdicts: ✅ aligned · ⚠️ partial · ❌ non-aligned · ➖ opportunity
- **Status:** `open` / `fixed` / `partial` / `wontfix` / `no-go` (findings-lifecycle conventions)
- **Sev:** P0 critical · P1 high · P2 important · P3 cleanup

---

## Part 1 — Carry-forward: re-verified findings from the 2026-08-29 Refactor Architect audit (R-01…R-16)

Status is **this register's live re-verification (2026-08-31)**, not the original claim.

| ID | Type | Area | Finding | Live status (2026-08-31) | FP | LT | DOC | Sev |
|---|---|---|---|---|---|---|---|---|
| R-01 | E | Canonical | 4 stale `v6.1` doctrine copies | ✅ **FIXED** — all 4 are identical 1,357 B "Mirror Pointer" stubs (canonical path, v8.0, SHA-256, gen date, "NOT authoritative") | ✅ | ✅ | ✅ | — |
| R-02 | E | Security | Client `X-Agency-ID` trusted on 5 routers | ✅ **FIXED** — `core/auth.py:170-185` honors header only under `PYTEST_CURRENT_TEST`/`SPINE_API_DISABLE_AUTH`; all 5 routers use `get_current_agency_id` | ✅ | ✅ | ✅ | — |
| R-03 | E | Integrity *(mis-scoped)* | File-store split-brain (1,635 JSON ∥ SQL) | ✅ **FIXED + REFRAMED** — files are gitignored test effluent; SQL mode fail-closed; no production split-brain. Original P0 premise was **wrong**. | ✅ | ✅ | ✅ | — |
| R-04 | E | Integrity | `commission.py` fabricated ₹3000 | ✅ **FIXED** — `commission.py:88` `if gross_cents <= 0: continue` | ✅ | ✅ | ✅ | — |
| R-05 | E | Integrity | `/send` returned `SENT` with no dispatch | ✅ **FIXED** — returns `QUEUED` + honest docstring | ✅ | ✅ | ✅ | — |
| R-06 | E | Epistemic | `EpistemicStatus`/`AssumptionRecord`/`CONNECTIVITY_TIER` absent | ✅ **FIXED** — `EpistemicStatus` (`packet_models.py:91`), `AssumptionRecord` (`:100`), slot-level `epistemic_status` (`:164`), wired (`extractors.py:1829-1842`). **`CONNECTIVITY_TIER` is SUPERSEDED by `RealityTier`** (`reality_tier.py:36`) — resolved differently, not lost. | ✅ | ✅ | ✅ | — |
| R-07 | E | Eval | Extraction + pipeline gates self-consistent | ✅ **FIXED** — `_check_blocks_ci()` reads `budget_health` (`verify_d6_gate_snapshot.py:57-63`); budget has `min_accuracy:0.85` (`manifest.yaml`); budget gate F1 0.9524, status `passing`, `blocks_ci:false`. **Self-correction:** only *budget* is live-wired; extraction/pipeline gates remain expected-vs-itself. | ✅ | ✅ | ✅ | — |
| R-08 | E | Quality | ~186 tests fail; no mypy | ✅ **FIXED (split, prior claim wrong on mypy)** — mypy configured + CI-blocking + clean. "358 failed" was an **env artifact**; CI-identical baseline **3,206 passed / 10 skipped / 0 failed** (`run_backend_tests.sh`). Residual F-19 (order-dependence under live-server contention). | ✅ | ⚠️ | ⚠️ | — |
| R-09 | E | Docs | `Docs/` ∥ `frontend/docs/` | ❌ **OPEN** — 2,020 ∥ 932 `.md`, no reconciliation | ❌ | ❌ | ❌ | P1 |
| R-10 | E | Architecture | `server.py` monolith; 2 audit systems | ⚠️ **PARTIAL** — `server.py` 3,195 lines, **64 routers**, 17 direct routes, 19 inline pydantic. **`audit_bridge` corrected**: it is an intentional sync/async shim to the same `AuditLog` table, NOT a dead duplicate. | ⚠️ | ⚠️ | ❌ | P2 |
| R-11 | E | Agentic | No durable lease/heartbeat; zombies | ⚠️ **PARTLY WRONG** — durable lease EXISTS (`AgentWorkLease`, `SELECT…FOR UPDATE`). **Heartbeat is still dead code** (`runtime.py:52-82`, 0 call sites) → >60s tasks re-acquirable → double-execution. | ⚠️ | ⚠️ | ⚠️ | P2 |
| R-12 | E | Domain | No Journey Dependency Graph for IROPS | ❌ **OPEN** — design + code exist (`journey_graph.py`, 4 importers); only the **IROPS trigger** missing | ✅ | ✅ | ➖ | P2 |
| R-13 | E | Navigation | Nav rollout-gate drift | ❌ **OPEN** — `nav-modules.ts` `complete:false`; needs product decision | ❌ | ⚠️ | ❌ | P2 |
| R-14 | E | UX | Two-generation styling (literal-hex ∥ primitives) | ❌ **OPEN** | ⚠️ | ❌ | ⚠️ | P3 |
| R-15 | E | Security | PII guard fail-open in production | ✅ **FIXED 2026-08-31** — Layer 2 fail-closed was unreachable dead code; posture reconciled (dogfood/prod+plaintext → fail-closed; prod+SQL/beta → fail-open-audited). ADR `R-15_PII_GUARD_DEFAULT_2026-08-31.md`. | ✅ | ✅ | ✅ | — |
| R-16 | E | Observability | No trace-correlation reader; no CI event-flow assertion | ❌ **OPEN** — OTel spans real, no consumer | ⚠️ | ⚠️ | ⚠️ | P2 |

**Carry-forward score: 8 fixed · 3 partial · 8 open · 3 prior-audit errors corrected.**

---

## Part 2 — New-finding re-verification (A-01…A-21)

| ID | Type | Area | Finding | Live status | FP | LT | DOC | Sev |
|---|---|---|---|---|---|---|---|---|
| A-01 | I | Quality | The only honest quality gate excluded from CI | ✅ **FIXED/closed** — budget gate wired & honest; F1 0.9524, blocks_ci honored | ✅ | ✅ | ✅ | closed |
| A-02 | I | RAG | Embeddings are md5 hash vectors, not semantic | ❌ **OPEN** — `generate_local_embedding` md5 64-dim (`indexer.py:20-35`); hybrid BM25+dense+RRF added (`retriever.py:36-102`) but "dense" not semantic | ❌ | ⚠️ | ⚠️ | P1 |
| A-03 | I | Agentic | Agent tools default to Mock; shipped config 100% mock | ⚠️ **PARTIAL** — `MockWeatherTool` default (`live_tools.py:406-408`); `RealityTier` exists but tool connectivity not tied to it; `CONNECTIVITY_TIER` removed | ⚠️ | ⚠️ | ⚠️ | P1 |
| A-04 | I | Architecture | Backend duplicate / shadow systems (9 pairs) | ⚠️ **PARTIAL** — `audit_bridge` corrected (intentional); `TeamStore` DEPRECATED not removed; **19 inline pydantic in server.py**; **156 scattered os.getenv, no BaseSettings**; vision clients NOT duplicates (text vs vision) | ❌ | ❌ | ❌ | P1 |
| A-05 | I | Frontend | Three competing data-fetch layers | ⚠️ **PARTIAL** — 80 raw `fetch(` in 44 files; 6 files use both; **no ESLint bare-fetch ban** | ❌ | ❌ | ❌ | P1 |
| A-06 | I | Contract | Generated type contract orphaned & stale | ❌ **OPEN** — 5 importers; not in CI; no drift gate | ❌ | ❌ | ❌ | P1 |
| A-07 | I | Docs | Documentation decay | ❌ **OPEN** | ❌ | ❌ | ❌ | P1 |
| A-08 | I | Docs | `motto_v4.md` filename drift (content recoverable) | ❌ **OPEN** — 20 files still reference deleted file; restore target exists; no CI dangling check | ❌ | ❌ | ⚠️ | P1 |
| A-09 | I | ADR | No supersession mechanism; numbering broken | ❌ **OPEN** — 0 `Supersedes:`/`Superseded-By:`; 002→006 gap; 22 ADRs repo-wide, only 3 numbered in `adr/` | ❌ | ❌ | ❌ | P1 |
| A-10 | I | Backlog | IDEA pad no longer reflects shipped reality | ❌ **OPEN** — pad out-of-workspace, known stale; IDEA-120/122/123/124 not marked done | ❌ | ❌ | ❌ | P2 |
| A-11 | I | Frontend | Four concurrent marketing generations live | ❌ **OPEN** — `app/v2`–`v5` all routed | ❌ | ❌ | ❌ | P2 |
| A-12 | I | Security | `src/proxy.ts` inert; edge auth gate may not run | ⚠️ **PARTIAL** — `proxy.ts` exists, only imported by test; no `middleware.ts`; version skew (Next14 vs eslint-config-next16/@types/react19) | ⚠️ | ❌ | ⚠️ | P1 |
| A-13 | I | Quality | 358 test failures | ✅ **FIXED** — env artifact; true CI-identical baseline green | ⚠️ | ❌ | ❌ | closed |
| A-14 | I | Process | Uncommitted P0 remediation exposed | ❌ **OPEN (process)** — 48 modified + ~30 untracked; no commit without authorization | ✅ | ✅ | ❌ | P0 |
| A-15 | I | Frontend | Frontend debt is undocumented, not absent | ⚠️ **PARTIAL** — 44 `any` prod (down from 65); 0 TODO/FIXME; 2,932-line `itinerary-checker/PageClient.tsx`; 1 `@ts-expect-error` | ⚠️ | ❌ | ⚠️ | P2 |
| A-16 | I | Frontend | Coverage thresholds unenforced; no e2e | ❌ **OPEN** — no thresholds in `vitest.config.ts`; `frontend/tests/` empty | ❌ | ❌ | ❌ | P2 |
| A-17 | I | A11y | `WelcomeModal` is not a modal | ❌ **OPEN** — no `role="dialog"`/`aria-modal`; plain card | ❌ | ⚠️ | ➖ | P3 |
| A-18 | I | Security | Secrets posture | ⚠️ **PARTIAL** — live `OPENAI_API_KEY` (rotate); committed `DATABASE_URL` dev password; `SPINE_API_DISABLE_AUTH` warns-not-crashes outside prod | ⚠️ | ⚠️ | ⚠️ | P1 |
| A-19 | I | Security | Coverage gap in RLS enforcement | ✅ **FIXED 2026-08-30** — 11 routers `get_rls_db`; `auth.py` documented exception; 4 exempt tables verified safe (RQ-03) | ✅ | ✅ | ✅ | closed |
| A-20 | I | Migrations | 4 model tables had zero migration files | ⚠️ **PARTIAL** — frontier-table migration added & in chain (`add_frontier_tables`); **CI `alembic check` drift gate still open** | ✅ | ✅ | ⚠️ | P2 |
| A-21 | I | Process | Parallel remediation in flight | ✅ **Resolved** — tracked & consolidated; this audit defers to existing designs | ✅ | ✅ | ✅ | closed |

---

## Part 3 — F-rows (2026-08-30 ADHD audit implicit defects)

| ID | Finding | Status | FP | LT | DOC | Sev |
|---|---|---|---|---|---|---|
| F-01 | `price_lock.py` re_lock blind read-modify-write (no version/idempotency) → concurrent re-locks double-book | **open** | ❌ | ❌ | ❌ | P1 |
| F-02 | `public_proposals.py` in-memory unbounded 16-hex unauthenticated tokens → full trip data; no TTL/revocation/consent | **open** | ❌ | ❌ | ❌ | P1 |
| F-03 | `team_workflows`/`corporate_policy` store client-supplied signoff; who-authorized is self-asserted | **open** | ❌ | ❌ | ❌ | P1 |
| F-04 | No payment authorization mandate ledger (split deposits + ACH move money w/o consent artifact) | **open** | ❌ | ❌ | ❌ | P1 |
| F-05 | `jurisdiction_policy.py` declares retention/erasure SLAs; zero enforcement wiring | **open** | ❌ | ❌ | ❌ | P1 |
| F-06 | Audit-chain gaps: file hash-chain unsigned/unanchored; run-ledger outside chain; no fork/gap detector | **open** | ❌ | ❌ | ❌ | P2 |
| F-07 | `agent_requeue_jobs.py` `JOB_STATUS_POISONED` accumulates invisibly; no inspect/redact/replay | **open** | ❌ | ❌ | ❌ | P1 |
| F-08 | `core/locking.py` silently falls back to in-process locks off-Postgres → differing mutual-exclusion semantics | **open** (small) | ❌ | ❌ | ❌ | P2 |
| F-09 | `run_ledger.py` checkpoints disk-only while state is SQL-backed → rolling deploys orphan RUNNING runs | **open** | ❌ | ❌ | ❌ | P2 |
| F-10 | `agent_work_coordinator.py` leases have no pipeline-version check → deploy splits a run across code generations | **open** | ❌ | ❌ | ❌ | P2 |
| F-11 | `usage_guard` meters spend at call time only; no auto-quiesce; no parent→child spend reservation | **open** | ❌ | ❌ | ❌ | P2 |
| F-12 | SSE fan-out no per-tenant connection cap, heartbeat, or eviction | **open** | ❌ | ❌ | ❌ | P2 |
| F-13 | `src/memory/` writes sanitized but not trust-weighted; cross-trip prefs inject into suitability scoring | **open** | ❌ | ❌ | ❌ | P1 |
| F-14 | Dated perishables (visa, quote TTL, insurance, payment deadlines) no owner as a class | **open** | ❌ | ❌ | ❌ | P1 |
| F-15 | `confirmation_service.py` treats defective supplier confirmations as generic failure → retry loops, no claims | **open** | ❌ | ❌ | ❌ | P2 |
| F-16 | Refund/compensation pipeline dead-ends; no disposition grading or re-shop credit path | **open** | ❌ | ❌ | ❌ | P2 |

---

## Part 4 — F-17…F-26 (2026-08-30/31 frontend + demo findings)

| ID | Finding | Status | FP | LT | DOC | Sev |
|---|---|---|---|---|---|---|
| F-17 | Frontend suite debt: TimelinePanel test races async fetch; 49 unhandled vitest errors; 4 lint errors + 17 exhaustive-deps warnings | **open** | ⚠️ | ❌ | ⚠️ | P2 |
| F-18 | Budget rule package (RQ-01 exit) | ✅ **FIXED** — F1 0.9524, gate green; **only S1/S3/S5 present** (S2/S4/S6 not found — prior claim overstated) | ✅ | ✅ | ✅ | closed |
| F-19 | Full-suite phantom failures under live-server contention (order-dependence) | **open** | ⚠️ | ⚠️ | ⚠️ | P2 |
| F-20 | DEMO-01/IMP-01: ESCALATE never persists a lead (P0) | ✅ **IMPLEMENTED 2026-08-31** — `save_processed_trip` on `early_exit` (`pipeline_execution_service.py:346`, `trip_status="incomplete"`, never overwrites); ADR `ADR_ESCALATE_LEAD_PERSISTENCE_2026-08-31.md` | ✅ | ✅ | ✅ | closed |
| F-21 | DEMO-02/03: Colloquial extraction gaps (destinations verb-object, party "me and N friends", season/"late march", "plus or minus", city sets, budget "each", duration) | **open** | ✅ | ✅ | ✅ | **P1** |
| F-22 | DEMO-11: Systemic authority/epistemic mislabeling (derived/default stamped `explicit_user/FACT`) | **open** | ❌ | ❌ | ❌ | **P1** |
| F-23 | DEMO-04: Alex Morgan card hardcoded + unconditional + fake-facts injection; legacy `CUSTOMER_MEMORY_STORE` unscoped (latent isolation) | **open** | ❌ | ❌ | ❌ | **P1** |
| F-24 | DEMO-05: `/inbox` renderer crash — verdict: dev-noise, not product defect | **watch** | ✅ | ✅ | ✅ | P3 |
| F-25 | DEMO-06/09: Repair-surface UX no-op; banner lacks missing-field names | **open** | ⚠️ | ⚠️ | ⚠️ | P2 |
| F-26 | DEMO-07: Copy/label drift (WORK EMAIL / you@agency.com / Waypoint HQ / runtime chip) | **open** | ⚠️ | ⚠️ | ⚠️ | P3 |

---

## Part 5 — NEW findings identified by THIS audit (not in any prior register)

| ID | Finding | FP | LT | DOC | Sev |
|---|---|---|---|---|---|
| **NEW-01** | **Inverted evidence apparatus on the facts path.** Every freeform extractor passes `AuthorityLevel.EXPLICIT_USER` unconditionally (`extractors.py:1863-2290`), so pattern-inferred (`party_size=1` from "me"), default-filled (`budget_flexibility="soft"`, `budget_scope="total"`), and spurious (`destination_status="open"` from an unrelated "somewhere") values all carry `explicit_user/FACT`. `set_fact` gates only on authority, not epistemic status. | ❌ | ❌ | ❌ | **P1** |
| **NEW-02** | **Silently-wrong extraction (worse than missing).** Truth = Japan+Tokyo/Kyoto/Osaka, party=4, budget=per-person; packet emitted `party_size=1 @0.9`, `budget_scope="total"`, `destination_candidates=[]`. A quote built on party=1 × trip-total when truth is 4 pax × per-person is ~4x commercial error. Isolated to destination/party/budget-scope/date-flex pattern gaps + the "somewhere" fallback trigger. | ✅ | ✅ | ✅ | **P0** |
| **NEW-03** | **Retirement is not a primitive.** 156 scattered `os.getenv` (no `BaseSettings`), `TeamStore` DEPRECATED-not-removed, 19 inline pydantic in `server.py`, 4 marketing generations, 2 doc trees, 0 ADR supersession. Deprecation is a comment, not a state with a date + enforcer. | ❌ | ❌ | ❌ | **P1 (systemic)** |
| **NEW-04** | **RAG "dense" is a hash vector, not semantic** — `retriever.py` claims "dense semantic search" but its dense path is the md5 pseudo-embedding; only BM25 does real work. Claim-reality risk if ever called "semantic search." | ❌ | ⚠️ | ⚠️ | P1 |
| **NEW-05** | **Findings-lifecycle gate exists but is not wired into CI** (`check_findings_register.py`, CI-ready, absent from `ci.yml`). Evidence of drift: consolidated register lists R-15 as open P1, but R-15 is FIXED 2026-08-31. | ❌ | ❌ | ❌ | P2 |
| **NEW-06** | **Customer-memory backend is real; frontend never calls it.** `src/memory/` (store/retrieval/decay/eligibility/gdpr/provenance/sanitizer/supersession) + `routers/customer_memory.py` (`/api/v1/customers/*`) exist; `api-client.ts` has zero customer-memory functions. The Alex Morgan card is a UI mock of a backend it was never pointed at. | ❌ | ❌ | ❌ | **P1** |
| **NEW-07** | **Agent runtime liveness gaps.** `ExecutionLease.heartbeat` dead code; >60s task re-acquirable (double-execution); leases have no pipeline-version stamp (deploy splits a run across two code generations); mock-vs-live not tied to `RealityTier`. | ⚠️ | ⚠️ | ⚠️ | P2 |

---

## Part 6 — Alignment summary

| Dimension | ✅ | ⚠️ | ❌ | Systemic read |
|---|---|---|---|---|
| **First-principles (PER-91002)** | 13 | 5 | 8 | The **core** is sound: deterministic intake, RLS, reality tiers, executable gates, epistemic primitives. Failures cluster in the **periphery** (per-field authority labels, RAG placeholder, duplicated config/contracts) — and are now largely *visible* rather than silent. |
| **Long-term (PER-0926)** | 10 | 6 | 10 | Weakest dimension. **No finish mechanism**: every improvement adds a layer instead of replacing one. The retirement gate is the single missing control. |
| **Doctrine-aligned (PER-0428)** | 10 | 6 | 10 | **§5 (one canonical source)** is the most-violated rule, breached on both sides of the stack. **§2 (truth taxonomy)** is now inverted on the facts path (NEW-01) — the system declares tiers honestly but not per-field authority. |

### The one-sentence version
> The project is architecturally right and — after 48 hours of hard work — its *measurement instruments* are finally honest. The remaining risk is **per-field truthfulness** (derived/default claims stamped as user-stated FACT) and **no mechanism to finish a canonical path**. The single highest-leverage intervention is a **retirement gate + an authority/epistemic label fix**.

---

## Part 7 — Counts

- **Open (implement):** R-09, R-12, R-13, R-14, R-16, A-02, A-03, A-04, A-05, A-06, A-07, A-08, A-09, A-10, A-11, A-12, A-14, A-15, A-16, A-17, A-18, A-20 + F-01…F-16 + F-17, F-19, F-21…F-26 + NEW-01…NEW-07
- **Fixed/closed since prior register:** R-01, R-02, R-03, R-04, R-05, R-06, R-07, R-08, R-15 + A-01, A-13, A-19, A-21 + F-18, F-20
- **No-go / watch:** F-24 (dev-noise), NG-01…NG-04 (recorded from backlog)

---

## Part 8 — Assumptions this register depends on (PER-0164)

| # | Assumption | Criticality | Falsification check |
|---|---|---|---|
| 1 | CI-identical baseline is green (3,206/10/0) | Low | Re-run `scripts/run_backend_tests.sh` (server stopped) |
| 2 | `customer_memory.py` legacy store is unscoped latent (not active) | **High** | Grep for actual caller reaching `/memory` with no agency filter; it's not wired to FE today |
| 3 | `audit_bridge` is intentional (not dead) | Low | Confirm zero unexpected callers + docstring |
| 4 | Frontend suite state per RQ-06 evidence (typecheck PASS, 896/897 tests) | Medium | Re-run frontend typecheck/lint/test this session |
| 5 | The 4 RLS-exempt tables are safe | Low | Already verified by RQ-03; keep documented |
| 6 | "S1-S6 rule package" overstated (only S1/S3/S5) | Low | Grep `# S<n> (RQ-01)` markers |

**Assumption 2 is the largest evidence hole if customer-memory wiring (Wave 2.1) is attempted.** Fix the legacy store scoping first.
