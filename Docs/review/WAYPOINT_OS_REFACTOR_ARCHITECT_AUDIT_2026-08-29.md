# Waypoint OS — Refactor Architect Evidence Audit & Doctrine Alignment Review

**Lead reviewing persona:** `PER-0001 — Refactor Decision Architect`
**Co-auditing persona council:** `PER-0923 — Evidence Architect` · `PER-20746 — Technical Director` · `PER-0930 — Shadow-System Investigator`
**Persona source:** `~/Desktop/Understanding_Personas_29aug26/`
**Target system:** `travel_agency_agent` / `waypoint-os` (`pranaysuyash/waypoint-os`)
**Review date:** 2026-08-29
**Governing doctrine:** `OPERATING_DOCTRINE.md` v8.0 · `REVIEW_DOCTRINE.md` v1.1 · `DOCUMENTATION_DOCTRINE.md` v1.1
**Review mode:** Full-repository static analysis + targeted runtime/test/snapshot verification + doctrine-alignment audit.
**Primary plan document:** `~/.commandcode/plans/waypoint-os-refactor-architect-audit.md`

---

## 1. Executive Assessment

Waypoint OS is a **substantially real, mature, doctrine-aware travel OS prototype** — not a facade. The backend is deterministic-first (regex/dictionary intake, `O(1)` geography resolution, rule-based decision engine), multi-tenant PostgreSQL with **actual Row-Level Security** (enforced, fail-closed in production), real OpenTelemetry instrumentation, a real manifest-driven eval/gate framework, and a genuinely honest `reality_tier.py` / `feature_gates.py` self-declaration layer that marks simulated features as `DATA_DEPENDENT` / `PLANNED` instead of claiming them real.

The core **is first-principles and long-term sound** — and, counter-intuitively, the codebase is *more honest than the 2026-08-24 audit claimed*. That audit's recommended "Reality Tier framework" is now **partially implemented**. But its *target* primitives (`EpistemicStatus`, `AssumptionRegister`, `CONNECTIVITY_TIER`) remain **absent from code**.

Four systemic fractures dominate, and they are exactly what the Refactor Decision Architect must gate before any further feature work:

| # | Finding | Verdict | Severity |
|---|---|---|---|
| **A** | **Canonical-path fracture** — 4 stale `v6.1` `OPERATING_DOCTRINE.md` copies under `frontend/`, `frontend/src/`, `frontend/src/types/`, `spine_api/` (declaring a *different* canonical path `~/Downloads/`) alongside the root `v8.0`; `AGENTS.md` + `CLAUDE.md` duplicate instruction surfaces; `Docs/` (626 files) parallel to `frontend/docs/` (921 files) | **Non-aligned** (violates doctrine §5, §17) | **P0** |
| **B** | **Tenant-authority gap** — 5 routers read agency id from the client-controlled `X-Agency-ID` header (`commission`, `group_booking`, `multimodal`, `customer_memory`, `price_lock`); honored in `auth.py` when `TRIPSTORE_BACKEND==file`; 1,375 `data/trips/*.json` files coexist with PostgreSQL (split-brain) | **Non-aligned** (security + data integrity) | **P0** |
| **C** | **Claims-real-but-simulated veneer** — `commission.py` default gross `(cost or 3000)*100` fabricates ₹3000 bookings; `messaging.py /send` returns `status="SENT"` after only an audit-log write; `NoopExtractor` returns `0.85`-confidence `DO_NOT_LOG_*` sentinels; `Mock*Tool` adapters back product agents' `"Attached…"` success events | **Non-aligned** (epistemic honesty, doctrine §8/§13) | **P1** |
| **D** | **Eval / CI theater** — extraction + pipeline gates are *self-consistent baselines* (expected-vs-itself, no-op); the only genuinely live gate (budget) is **red** (`overall_f1=0.2857`, `blocks_ci=true`); ~186 backend tests fail; no mypy; integration tests never run in CI | **Partially non-aligned** (doctrine §3, Testing Doctrine) | **P1** |

**Net verdict:** Not launch-ready as an enterprise travel OS until fractures A–D are closed. **Do not rewrite.** The deterministic intake + epistemic decision engine + RLS + reality-tier honesty gating are worth preserving. The correct intervention is **gated, evidence-backed hardening at defined boundaries**, then deterministic extension.

---

## 2. Scope & Review Method

- **Method:** Full-repository static analysis (Operating Doctrine Tier 1), targeted runtime/API/DB verification and committed test/eval snapshot inspection (Tier 3), and documentation/doctrine parity audit.
- **Parallel exploration agents** audited five dimensions: (1) backend reality tiers & external integrations, (2) frontend navigation / routes / state, (3) security / tenancy / payments, (4) tests / CI / evals / observability, (5) documentation / doctrine / canonical alignment.
- **Ground-truth** was re-verified from live source and committed artifacts, not taken from prior audit summaries.
- **Epistemic discipline:** every load-bearing claim below is labeled `Observed` (path + symbol) or `Verified` (test / probe / snapshot). No claim is adopted from the Aug-24 audit without independent re-confirmation in code.

---

## 3. System Reconstruction

**Monolithic FastAPI server** (`spine_api/server.py`, **3,719 lines**) imports and mounts 44 routers at lines 1173–1215. It is a single process, not microservices.

**Layered pipeline (all real):**

```
Acquisition & Inbound      (social_inbound, public_checker, messaging webhooks)
  → Intake & Packet        (regex/dict: extractors.py, geography.py, dates.py)
  → Epistemic Decision     (intake/decision.py: hard/soft blockers, authority_level)
  → Strategy / NB03        (intake/strategy.py: session & prompt planner)
  → Proposal & Fulfillment (proposal_lifecycle, payment_queue_service [read-model], commission)
  → Agentic Runtime        (src/agents/runtime.py + live_tools.py [Mock default, live opt-in])
  → Multi-Tenant Governance(RLS via core/rls.py, audit, reality-tier gates)
```

**Reality tier model (real; partially supersedes Aug-24 finding F-02):**
`spine_api/core/reality_tier.py` defines `RealityTier = REAL | CONNECTED_SANDBOX | DETERMINISTIC_PREVIEW | DATA_DEPENDENT | PLANNED`, with `TIER_CAPABILITIES` gating `can_write_success_events`, `can_mutate_booking_state`, and `can_make_financial_claims`. `feature_gates.py` `FEATURE_REGISTRY` lists each feature with `honest_status`, `requires_integration`, and `missing_for_upgrade`. This is the strongest first-principles asset in the codebase — it makes the system self-declare reality.

**Two divergent audit systems (inconsistency):** a file-based `AuditStore` with a real SHA-256 hash chain (`persistence.py:2056–2086`, documented as RULE_015) **and** a separate PostgreSQL `audit_logs` model (`models/audit.py`) that has **no hash chain**. Two parallel audit implementations.

---

## 4. Evidence Ledger

| Evidence ID | Artifact | Location | Observation | Supports |
|---|---|---|---|---|
| E1 | `reality_tier.py` | `spine_api/core` | `RealityTier` enum + `TIER_CAPABILITIES` gate success-event writes and booking mutation | Honesty framework exists |
| E2 | `feature_gates.py` | `spine_api/core` | Each feature carries `honest_status` + `requires_integration` | Self-declaring tier |
| E3 | `extractors.py` | `src/intake` | Deterministic regex pipeline; no LLM used for text extraction | Tier-1 core is real |
| E4 | `rls.py` + `add_rls_*` migrations | `spine_api/core`, `alembic` | `FORCE ROW LEVEL SECURITY` on tenant tables; fail-closed in production | Tenancy is real |
| E5 | `commission.py:84,197` | `spine_api/routers` | Default gross `(cost or 3000)*100`; hardcoded ₹3000 fabrication | **Veneer C** |
| E6 | `messaging.py:47–82` | `spine_api/routers` | `/send` returns `status="SENT"` after audit-log write only, no HTTP dispatch | **Veneer C** |
| E7 | `snapshot.py:98–100` | `src/evals/audit` | extraction + pipeline use self-consistent baseline (`F1=1.0`, cannot fail) | **Eval theater D** |
| E8 | `d6_audit_gate_snapshot.json` | `data/evals` | budget `overall_f1=0.2857`, `blocks_ci=true` | Only real gate is red |
| E9 | `group_booking.py:92`, `multimodal.py:163`, `price_lock.py:84`, `customer_memory.py:100`, `commission.py:63` | `spine_api/routers` | Client-controlled `X-Agency-ID` header | **Tenancy gap B** |
| E10 | `OPERATING_DOCTRINE.md` × 5 | root / frontend / frontend/src / frontend/src/types / spine_api | 4 stale `v6.1` copies vs root `v8.0`; two declared canonical paths; no hashes | **Canonical fracture A** |
| E11 | `data/trips/` | `data` | 1,375 JSON trip files coexist with SQL store | Split-brain B |
| E12 | `auth.py:175–178` | `spine_api/core` | `X-Agency-ID` honored when `TRIPSTORE_BACKEND==file` | Tenancy gap B |
| E13 | docs tree | `Docs/` (626) + `frontend/docs/` (921) | Two parallel documentation trees | Canonical fracture A |

---

## 5. First-Principles / Long-Term / Doctrine-Alignment Review

### 5.1 Epistemic Honesty over Plausible Simulation (doctrine §8, §13; Review §8/§27/§38)
- **Aligned where it matters:** reality-tier gating (`can_write_success_events=False` at lower tiers) and `honest_status` metadata are correct.
- **Non-aligned (P1):** `Mock*Tool`-backed agents still emit `COMPLETED` success events; `commission.py` fabricates amounts. The honesty layer *labels* these but the veneer persists at the data layer.
- **Target:** add an `EpistemicStatus` enum (`FACT / INFERRED / ASSUMED / UNKNOWN`) on every `TripPacket` slot, an `AssumptionRegister`, and a strict `CONNECTIVITY_TIER` (`MOCK / SIMULATED / LIVE`). This remains a first-principles target from the Aug-24 audit and is **not implemented** (verified zero matches in `src/` and `spine_api/`). It is the highest-value epistemic upgrade.

### 5.2 Deterministic Foundations, Adaptive Periphery (doctrine §7)
- **Fully aligned.** Regex/dict intake, `O(1)` geography, rule-based decision engine; the LLM is reserved for conversational nuance, unstructured document/vision extraction. **Maintain this boundary; do not introduce an LLM into deterministic slots.**

### 5.3 Fail-Closed Multi-Tenant Security (doctrine §5, §11; Review §50)
- **Aligned for the core** (RLS real, fail-closed in production). **Non-aligned (P0)** for the 5 routers using the client `X-Agency-ID`, and for the file-store split-brain. `auth.py` honoring `X-Agency-ID` when `TRIPSTORE_BACKEND==file` is the single highest-risk default.
- **Target:** derive agency id solely from JWT membership; remove header trust; reconcile or remove `data/trips/*.json` when `TRIPSTORE_BACKEND=sql`.

### 5.4 Canonical Paths & One Source of Truth (doctrine §5, §17; Documentation §2/§3/§37)
- **Non-aligned (P0):** 5 `OPERATING_DOCTRINE.md` copies, 2 declared canonical paths, no hashes. `CLAUDE.md` is a symlink to `AGENTS.md` (effectively one file, good), but a stale `CLAUDE.md.legacy-20260826` persists. `Docs/` is parallel to `frontend/docs/`. Multiple docs each claim a "Canonical … Roadmap" title.
- **Target:** one canonical `v8.0` doctrine (root authoritative, mirrors labeled with source/version/hash/generation time); retire/archive legacy motto and `CLAUDE.md.legacy` files; reconcile or link `Docs/` ↔ `frontend/docs/`.

### 5.5 Doctrinal Process vs Practice (AGENTS.md 4-phase workflow / 11-dimension audit)
- **Mixed.** Handoff/closure artifacts are present (62 matches across 34 files) — practice is followed. But the prescribed "11-Dimension Audit Checklist" verdict table and the "minimum 2 review cycles" rule are **not visibly projected** into produced artifacts. The process doctrine has partly **outgrown practice**.

---

## 6. Explicit & Implicit Findings / Tasks

### Explicit tasks (directly evidenced)

| ID | Type | Area | Finding / Gap | FP / Doctrine Verdict | Long-Term Solution |
|---|---|---|---|---|---|
| **R-01** | Explicit | Canonical | 4 stale `v6.1` doctrine copies + differing canonical path | **Non-aligned (P0)** | Consolidate to root `v8.0`; label mirrors with hash/gen-time; archive legacy |
| **R-02** | Explicit | Security | Client `X-Agency-ID` trusted on 5 routers | **Non-aligned (P0)** | Derive agency from JWT membership only; add `RequireAgencyContext` dependency |
| **R-03** | Explicit | Security | `X-Agency-ID` honored when `TRIPSTORE_BACKEND==file`; 1,375 JSON files split-brain | **Non-aligned (P0)** | Remove header trust; reconcile / remove file store when SQL |
| **R-04** | Explicit | Integrity | `commission.py` fabricates ₹3000 default | **Non-aligned (P1)** | Require real booking data; fail loudly instead of fabricating |
| **R-05** | Explicit | Integrity | `messaging.py /send` returns `SENT` w/o dispatch; webhook unauthenticated when secret unset | **Non-aligned (P1)** | Real dispatch or honest `QUEUED`; default-deny webhook verification |
| **R-06** | Explicit | Epistemic | `EpistemicStatus` / `AssumptionRegister` / `CONNECTIVITY_TIER` absent from code | **Unfinished FP target** | Add enums; attach assumptions to `TripPacket` |
| **R-07** | Explicit | Eval | Extraction + pipeline gates are self-consistent (cannot fail) | **Test theater (P1)** | Wire real pipeline results; make gates falsifiable |
| **R-08** | Explicit | Quality | Budget gate red (0.2857); ~186 backend tests fail; no mypy | **Non-aligned (P1)** | Fix failing clusters; add type-check; gate on real threshold |
| **R-09** | Explicit | Docs | `Docs/` (626) ∥ `frontend/docs/` (921); multiple "Canonical Roadmap" docs | **Non-aligned (P1)** | One canonical index; reconcile or link trees |
| **R-10** | Explicit | Architecture | `server.py` 3,719 lines; 44 routers; two divergent audit systems | **Debt (P2)** | Modularize routers; unify audit to one hash-chained store |

### Implicit tasks (discovered, follow-on)

| ID | Type | Area | Finding / Gap | Verdict |
|---|---|---|---|---|
| **R-11** | Implicit | Agentic | No durable lease/heartbeat for agents; zombie tasks on restart | Non-aligned (P2) |
| **R-12** | Implicit | Domain | No Journey Dependency Graph for IROPS ripple analysis | Opportunity (P2) |
| **R-13** | Implicit | Navigation | Quotes/Bookings/Suppliers/Knowledge all `enabled:true` vs design audit's rollout-gate intent | Drift (P2) |
| **R-14** | Implicit | UX | Literal-hex page styling coexists with shadcn-style primitive layer (two-generation styling) | Debt (P3) |
| **R-15** | Implicit | Security | PII guard blocks only in `dogfood`; fail-open in production; file store persists plaintext | Non-aligned (P1) |
| **R-16** | Implicit | Observability | OTel spans are real but no trace-correlation reader; no CI assertion of event flow | Gap (P2) |

---

## 7. Priority Matrix

| ID | Finding | Priority | Category | Truth status | User impact | Architecture impact | Evidence tier | Dependency | Recommended action |
|---|---|---|---|---|---|---|---|---|---|
| R-01 | Stale doctrine copies | P0 | Canonical | Observed | Text-search confusion for future agents | High | Tier 1 | none | Consolidate; label mirrors |
| R-02 | Client `X-Agency-ID` trust | P0 | Security | Observed | Cross-tenant read/write risk | High | Tier 1 | R-03 | Derive from JWT; add dep |
| R-03 | File-store split-brain | P0 | Security | Observed | Data divergence / tenant leak | High | Tier 3 | none | Reconcile; fail-closed default |
| R-04 | Commission fabrication | P1 | Integrity | Observed | Misleading financial output | Medium | Tier 1 | none | Fail loudly; require real data |
| R-05 | `/send` fake SENT | P1 | Integrity | Observed | Misleading status semantics | Medium | Tier 1 | none | Honest `QUEUED`; deny webhook |
| R-06 | Missing epistemic enum | P1 | Epistemic | Observed | Unknown treated as fact | High | Tier 1 | none | Add `EpistemicStatus` |
| R-07 | Self-consistent eval | P1 | Eval | Observed | CI gate cannot catch regressions | Medium | Tier 3 | none | Real pipeline results |
| R-08 | Failing tests / no mypy | P1 | Quality | Observed | False green / latent breakage | Medium | Tier 3 | R-07 | Fix, type-check, gate |
| R-09 | Doc trees parallel | P1 | Docs | Observed | Duplicate/conflicting truth | Medium | Tier 1 | none | Canonical index |
| R-10 | Monolithic server | P2 | Architecture | Observed | Change amplification / regression | Medium | High | R-02 | Modularize routers |
| R-11 | Agent lease/heartbeat | P2 | Agentic | Inferred | Work loss on crash | Medium | Medium | none | Durable state machine |
| R-12 | Journey graph | P2 | Domain | Inferred | Missed IROPS ripple | Medium | Medium | none | Graph-based trip model |
| R-13 | Nav rollout-gate drift | P2 | Navigation | Observed | Confusing module availability | Low | Low | none | Align flags to intent |
| R-14 | Two-generation styling | P3 | UX | Observed | Visual inconsistency | Low | Low | none | Unify onto primitive layer |
| R-15 | PII fail-open | P1 | Security | Observed | Privacy exposure in prod | High | Medium | none | Fail-closed; encrypt file store |
| R-16 | Trace-correlation gap | P2 | Observability | Inferred | Hard to diagnose incidents | Medium | Medium | none | Trace reader; CI assertion |

---

## 8. Cross-Cutting Analysis

### 8.1 Source-of-Truth Analysis
- `TripPacket` owns trip intent; `authority_level` + `confidence` exist but there is no explicit epistemic-status model — the highest authority flag (`AuthorityLevel`) does not clearly separate *known from customer* vs *inferred by NLP* vs *assumed* vs *unknown*. This is the source-of-truth ambiguity behind R-06.
- `spine_api/server.py` owns routing; agency context is established via `get_current_membership()` + RLS, but the 5 header-trusting routers bypass it (R-02).

### 8.2 Contract & Vocabulary Analysis
- `hard_blockers` vs `soft_blockers` (intake/decision.py) is directly analogous to `MISSING_REQUIRED` vs `MISSING_PREFERENCE` but uses different vocabulary — a terminology divergence that should be reconciled to one canonical vocabulary.
- Both `RealityTier` and the absent `CONNECTIVITY_TIER` attempt to classify honesty of data sources; two parallel classification systems risk drift (R-06).

### 8.3 Composition & Future Integration Risks
- The reality-tier gate (`assert_tier_capability`) is correct but only enforced on a subset of mutating endpoints (`concierge`). Not all financial-mutation paths are gated — compose the gate into *every* endpoint that writes success events or financial claims.
- Two audit stores (file hash-chain vs DB model) produce inconsistent provenance when both are exercised (part of R-10).

### 8.4 Test & Verification Gaps
- Backend suite not green (last executed CI documented ~2,775 pass / 186 fail). No mypy. Integration tests auto-skip because CI never starts uvicorn on `:8000`. Extraction + pipeline eval gates are self-consistent and cannot fail. Budget gate is genuinely live and red.

### 8.5 Observability Gaps
- OTel spans are real in the intake pipeline and exported when an endpoint is configured, but there is no trace-to-log correlation reader, no dashboards, and no CI assertion that event flow works.

### 8.6 Documentation Gaps
- Four stale `v6.1` doctrine copies; two parallel doc trees; multiple docs claiming "Canonical … Roadmap"; stale root `*.SUMMARY.txt`, `TODO.md`, `.bak` files; a `CLAUDE.md.legacy-20260826` and live `motto.md` despite v5–v2 being archived.

---

## 9. Recommended Sequencing

**Blast-radius + dependency order (per Review Doctrine §76):**

1. **Safety / correctness / truth blockers (P0):** R-01 (canonical doctrine), R-02 (X-Agency-ID), R-03 (file-store split-brain). Lowest risk to fix, highest blast radius to leave.
2. **Canonical primitive / contract corrections (P1):** R-06 (EpistemicStatus / AssumptionRegister / ConnectivityTier), R-04 / R-05 (stop fabricating), R-15 (PII fail-closed).
3. **Regression protection:** R-07 (make eval gates falsifiable), R-08 (fix failing tests + add mypy).
4. **Consumer / UX updates:** R-13 (nav rollout-gate alignment), R-14 (component styling unification).
5. **Documentation:** R-09 (reconcile doc trees + single index), and write the durable review.
6. **Exploratory follow-ons:** R-11, R-12, R-16 (journey graph, agent leases, trace reader).

---

## 10. Review Completeness

### Reviewed
- **Backend:** `src/intake`, `src/decision`, `src/fees`, `spine_api/core` (`reality_tier`, `feature_gates`, `rls`, `auth`, `security`, `env`), `spine_api/routers` (44), `spine_api/services` (`payment_queue`), `spine_api/models`, `src/agents` (`runtime`, `live_tools`), `src/evals` (`manifest`, `snapshot`, `gates`), `src/security` (`privacy_guard`).
- **Frontend:** `app/(agency)/` routes, `components/navigation`, `components/layouts/Shell`, `lib/nav-modules`, `stores`, `components/ui`.
- **Tests / CI:** `tests/`, `conftest.py`, `.github/workflows/ci.yml`, `src/evals/audit/manifest.yaml`, `data/evals/d6_audit_gate_snapshot.json`.
- **Docs / doctrine:** all 5 `OPERATING_DOCTRINE.md`, `AGENTS.md`/`CLAUDE.md`, `Docs/` structure, `Docs/INDEX.md`, root static artifacts.

### Not reviewed
- Not a full line-by-line of all 247 `.py` files, 448 TS files, or all 1,026 docs.
- Not executed a live build/CI run this session (evidence is static inspection + committed test/eval snapshots). Runtime claims are Tier 3, not Tier 5 live deploy.
- Not audited the Chrome-extension / mobile persona families (out of scope for this travel-OS backend review).

### Remaining uncertainties
- Exact current CI pass/fail count (committed `audit_test_results.txt` is stale; DD-7 documents `2,775 pass / 186 fail` as of 2026-08-01). Needs a fresh `uv run pytest -q tests/` against Postgres.
- Whether `data/trips/*.json` is actively written by any runtime path in SQL mode, or only by seeds/tests (blast radius of R-03).
- Exact intended rollout-gate state for the new nav modules (design audit vs implementation disagree; needs a product decision).

### Evidence needed
- A fresh green/red backend test run against PostgreSQL.
- A decision on whether `Docs/` + `frontend/docs/` should be one tree or two (ownership).

### Evidence tier achieved
- **Tier 3** (targeted test / snapshot / probe) for the major claims; **Tier 1** (static) for line-level details. Not Tier 5 (live deploy).

### Known blind spots
- The 2 OpenAI-key-gated vision/extraction test files were not executed.
- Mobile / Chrome-extension surfaces and the `v2`–`v5` frontend app directories were not deeply audited.
- Functional/behavioral correctness of each individual rule in the decision engine was not exhaustively tested.

---

## 11. Closing Verb

As **Refactor Decision Architect**: **do not rewrite.** The core is first-principles and worth preserving. The correct intervention is **gated, evidence-backed hardening at defined boundaries** — canonicalize the instruction/documentation surface, seal the tenant-authority gap, stop fabricating financial/status truth, make the eval gate actually falsifiable — then extend deterministically (journey graph, live connectivity) on top. Every change must declare its invariant, blast radius, and acceptance evidence before it starts; the smallest intervention that removes the constraint is the target.
