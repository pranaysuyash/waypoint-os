# Alignment Evaluation — First-Principles, Long-Term, Doctrine-Aligned (2026-08-31)

**Date:** 2026-08-31 · **Companion to:** `PERSONA_COUNCIL_AUDIT_2026-08-31.md`, `FINDINGS_REGISTER_2026-08-31.md`, `IMPLEMENTATION_PLAN_2026-08-31.md`
**Lens:** Council personas (PER-91002 primitive decomposition · PER-0926 product evolution · PER-0428 doctrine alignment · PER-0922/0923 evidence/epistemic integrity · PER-0930 shadow-system · PER-0164 assumption auditing).

This document answers the user's explicit question: **are all the findings/tasks first-principles, long-term, and doctrine-aligned implementations or not — and what else can be done/improved/added to make it the best?**

---

## Part 1 — Per-finding FP/LT/DOC verdicts (with the reasoning)

Each finding is rated on three axes. **FP** = is the *target* state first-principles correct (does it model the real problem)? **LT** = is it long-term coherent (will it survive evolution, or add a layer)? **DOC** = is it doctrine-aligned (does it honor §5 one-canonical-source, §2 truth taxonomy, §14 decision history, §11 config-as-code)?

### 1.1 Verdicts by cluster

| Cluster | FP | LT | DOC | Why |
|---|---|---|---|---|
| **Deterministic intake core** (destinations/dates/party extraction, F-21, NEW-02) | ✅ sound | ✅ sound | ✅ aligned | The boundary (deterministic-first, LLM-periphery) is correct. The *gaps* are pattern coverage, not architecture. Fixing them is additive rule extension, not redesign. |
| **Reality-tier honesty** (RealityTier, honest gate, R-07) | ✅ sound | ✅ sound | ✅ aligned | The system was made honest about tiers and gates. Strongest epistemic asset; models "what is fake vs real" correctly. |
| **RLS / tenant boundary** (R-02, A-19, F-23) | ✅ sound | ✅ sound | ✅ aligned | Real Postgres RLS, fail-closed, 11/12 routers scoped. The one latent hole is the unscoped `CUSTOMER_MEMORY_STORE` legacy dict (F-23) — a scoping fix, not a redesign. |
| **Epistemic primitives** (R-06, EpistemicStatus/AssumptionRecord) | ✅ sound | ✅ sound | ✅ aligned | Landed and wired. The **label semantics** (NEW-01) are the broken part — the primitive is right, the usage is inverted. |
| **Authority/epistemic labeling** (NEW-01, F-22) | ❌ not FP | ❌ not LT | ❌ not DOC | `set_fact` gates only on authority, not epistemic status; every freeform extractor passes `EXPLICIT_USER`, so derived/default/spurious values claim `FACT`. This **inverts** the epistemic ladder the primitives exist to express. The label vocabulary is the defect, not the per-field transparency UX. |
| **Retirement / canonical-path finish** (NEW-03, A-04, A-05, A-09, A-11) | ❌ not FP | ❌ not LT | ❌ not DOC | Deprecation is a *comment*, not a *state with a date + enforcer*. This is the single systemic failure — the root of 20+ instances. No mechanism to finish a canonical path. |
| **RAG "dense" retrieval** (A-02, NEW-04) | ❌ not FP | ⚠️ partial | ⚠️ partial | Architecture (BM25+dense+RRF, provenance, fail-closed grounding) is right. The "dense" primitive is a md5 hash vector placeholder — claim-reality risk. Replace the embedding behind the existing interface. |
| **False-confidence contracts** (A-06 generated types, A-12 proxy.ts) | ❌ not FP | ❌ not LT | ❌ not DOC | A declared contract nothing enforces is worse than no contract (manufactures false confidence). The drift gates are the fix. |
| **Config as contract** (A-04 config, NEW-03) | ❌ not FP | ❌ not LT | ❌ not DOC | 156 scattered `os.getenv`, no `BaseSettings`. Config is production code per §11 but treated as ad-hoc. |
| **Silently-wrong data** (NEW-02, F-21 party/budget/dest) | ✅ sound target | ✅ sound target | ✅ sound | The *target* (warn-and-preserve, never silently wrong — Pattern 5) is first-principles correct. The *current* behavior (party=1, budget=total when truth is 4×per-person) is a P0 commercial defect. |
| **Memory architecture** (src/memory, NEW-06) | ✅ sound backend | ⚠️ partial | ⚠️ partial | The backend is real (store/retrieval/decay/eligibility/gdpr/provenance/sanitizer/supersession), but the frontend never calls it — the demo card is a UI mock. The wiring is the missing half, and the legacy store must be agency-scoped first. |
| **Agent runtime** (R-11, F-10, NEW-07) | ⚠️ partial | ⚠️ partial | ⚠️ partial | Durable lease exists; heartbeat is dead code; no pipeline-version fence → double-execution + cross-version split risk. |
| **Detection/enforcement gates** (O-8, O-9, O-10, A-20 residual) | ✅ sound | ✅ sound | ✅ sound | Findings-lifecycle gate, alembic drift gate, type drift gate, ESLint bare-fetch ban — invariants as executable gates, not prose. This is the right instinct. |
| **Demo-loop lead persistence** (F-20, ADR) | ✅ sound | ✅ sound | ✅ sound | ADR models the right distinction (gates gate packet completeness, never record existence) and was implemented with E2E + tests. A model first-principles decision. |
| **Doc tree / ADR numbering** (R-09, A-08, A-09, A-10) | ❌ not FP | ❌ not LT | ❌ not DOC | Two doc trees, no ADR supersession, filename drift, stale CHANGELOG → unrecoverable lineage and drift. |

### 1.2 Verdict summary

- **FP: sound core (13), partial (5), non-aligned (8).** The deterministic intake, RLS, reality tiers, executable gates, and epistemic primitives are real assets. Failures cluster in the periphery and are now *visible* rather than silent.
- **LT: sound (10), partial (6), non-aligned (10).** The weakest dimension. The defining long-term risk: **no finish mechanism.** Every improvement adds a layer instead of replacing one.
- **DOC: sound (10), partial (6), non-aligned (10).** §5 (one canonical source) most violated. §2 (truth taxonomy) now inverted on per-field labels.

---

## Part 2 — What is genuinely first-principles sound (keep, defend)

These are the reasons the correct intervention is **hardening, not replacement**:

1. **Deterministic intake core.** Zero LLM in `src/intake/`, 59 `re.compile`. The LLM is reserved for nuance/vision. Correct boundary.
2. **Reality-tier honesty.** `RealityTier` + `TIER_CAPABILITIES` + `honest_status`. The system declares what is fake vs real.
3. **Real RLS.** `FORCE ROW LEVEL SECURITY`, fail-closed, 11/12 routers scoped.
4. **Executable architectural gates.** Six shell/mypy gates encode invariants, not prose.
5. **Epistemic primitives landed.** `EpistemicStatus`, `AssumptionRecord`, slot-level `epistemic_status`.
6. **The honest quality gate is now wired.** Budget F1 0.9524, `blocks_ci` honored — the single most important fix.
7. **ADR for the lead-loop decision** (gates gate completeness, never record existence) and **R-15 posture matrix** (fail-closed where the encryption boundary is absent, fail-open-but-audited elsewhere).

---

## Part 3 — What is NOT first-principles / long-term / doctrine-aligned (and the root cause)

The three root causes (PER-0930), stripped of domain nouns:

1. **Migration started, never finished.** `TeamStore` DEPRECATED-not-removed, legacy 1D scoring, `audit_bridge` ambiguity, 4 marketing generations, 2 doc trees. Root cause: **no retirement primitive** — deprecation is a comment, not a state with a date + enforcer.
2. **Two owners of the shared auth/config boundary by accretion.** No `BaseSettings`; 156 `os.getenv`; `server.py` defines 19 inline pydantic alongside `contract.py` + routers. Root cause: **config/contract never treated as a first-class, single-owner resource** (§5, §11).
3. **Trust-label vocabulary inverted.** `set_fact` gates only on authority; every freeform extractor passes `EXPLICIT_USER`; derived/default/spurious values claim `FACT`. Root cause: **the epistemic primitive exists but its usage discipline does not** (§2).

---

## Part 4 — "What else can be done / improved / added" (the expansion)

This is the highest-value part. These go **beyond** defect repair — they are opportunities derived from the persona categories (07 Agentic AI, 09 Travel, 14 Meta-Reasoning, 15 Platform Ops) and noun-stripping.

### 4.1 Additive opportunities (proposed — each deserves a design sketch before build)

| # | Opportunity | Persona | Why high-value | Level |
|---|---|---|---|---|
| O-1 | **Retirement gate enforced by CI** (target + deletion date; fail when a `DEPRECATED` file exceeds its date) | PER-0926/0930 | Prevents the entire defect class (20+ instances) instead of fixing each | systemic |
| O-2 | **Single `BaseSettings` config module** replacing 156 scattered `os.getenv` | PER-0930/0940 | Config becomes a first-class contract (§11); fail-fast on missing required var | systemic |
| O-3 | **One canonical pydantic contract layer** (server.py's 19 inline models → contract.py/routers) | PER-0930 | Removes byte-level duplicates; single FE/BE contract | systemic |
| O-4 | **Authority/epistemic relabel** (reserve `explicit_user/FACT` for verbatim-stated values; `INFERRED`/`ASSUMED` for pattern/default) + render epistemic in UI | PER-0922/0923 | Makes the "honest gauges" honest — the demo's differentiator is currently mislabeled | **highest leverage** |
| O-5 | **Negative-space map** (payment execution, ticketing/GDS, refunds, APIS, WCAG, i18n, PCI) — each absence classed deliberate/oversight/unknown | PER-91002/1003 | Prevents absence-assumed-from-vocabulary while surfacing real gaps | explore |
| O-6 | **TemporalObligation primitive** — every deadline (visa, price-lock, payment, insurance, ticketing, SLA, 72h re-shop) as a first-class obligation with a deadline | PER-0964/0929 | Subsumes F-14 + half of Cluster A | high-leverage design |
| O-7 | **Customer-memory real wiring** (backend real; wire frontend; gate card on real recall; fix legacy store scoping first) | PER-0870/0872 | Converts a mock into the production memory surface; closes a latent isolation hole | **high** |
| O-8 | **Findings-lifecycle CI wiring** (run `check_findings_register.py` in CI) | PER-0922/0428 | Makes the register authoritative; prevents stale-open drift (R-15 case) | systemic |
| O-9 | **Alembic drift gate** (`alembic check`) + **type drift gate** (regenerate → diff → fail) | PER-0410/0428 | Closes A-20 residual + A-06 with executable gates | systemic |
| O-10 | **ESLint bare-`fetch` ban + `any` threshold** | PER-0410 | Enforces single-fetch-layer mechanically | systemic |
| O-11 | **IROPS trigger for JDG** (measure segment-count distribution first as a falsifier) | PER-0446/0969 | Completes R-12 with evidence-driven trigger | extension |
| O-12 | **Agent runtime hardening** (durable lease heartbeat/fencing, pipeline-version stamp, latency-aware routing) | PER-0702/0706 | Closes R-11/F-10 double-execution + version-split | extension |

### 4.2 Structural improvements to how the system *claims* things (the trust layer)

The demo's praised differentiator is "honest gauges" — confidence + authority per field. But the labels are **currently inverted** (NEW-01). The single highest-value improvement beyond defect repair:

- **Reserve `explicit_user/FACT`** for values whose evidence excerpt is a verbatim user span.
- **`INFERRED`** for pattern-inferred values (extractor deduced from text).
- **`ASSUMED`** for system defaults (unmarked budget → soft; unknown scope → total).
- **Render epistemic status next to authority** in the Trip Details table.
- **Forbid canned excerpts** ("Derived from destination text") on `explicit_user` slots.

This converts the "honest gauge" from a *label* into a genuinely *trustworthy* one — the highest business-value improvement because it compounds with every downstream decision (quote, suitability, strategy).

### 4.3 The product-layer end state (what "best" looks like)

Noun-stripping the travel domain, Waypoint OS is a **provenance-first decision system over labelled beliefs**. "Best" means:

1. **Every field carries truth + authority + provenance** (value, confidence, epistemic_status, evidence citation, freshness, authority grade). Almost there — the slot model supports it; the extractors just don't use it correctly (NEW-01).
2. **Every external capability declares its connectivity** (MOCK/SANDBOX/LIVE) orthogonally to RealityTier — partially there; tool connectivity not yet tied to tier (A-03).
3. **No capability is retired by comment; retirement is an enforced state** (O-1, NEW-03).
4. **Every deadline is a first-class obligation** (O-6, TemporalObligation) — subsumes F-14 + Cluster A.
5. **The funnel never leaks**: a customer contact is always persisted as a lead, gated only on quote-readiness, never on existence (F-20 — done, ADR).
6. **Memory is real, provenance-weighted, and trust-scoped** (O-7, F-13).

### 4.4 What can be improved without new code (process/doctrine)

| Improvement | Why |
|---|---|
| Wire `check_findings_register.py` into CI (O-8) | The register becomes authoritative, not aspirational |
| Add the `Supersedes:`/`Superseded-By:` ADR field + renumber (A-09) | ADR-vs-code contradiction becomes resolvable; lineage preserved |
| Enforce the retirement gate (O-1) | Turns the #1 systemic defect into a mechanical check |
| D-01 absence-claims-need-executed-evidence (backlog) | Prevents the exact prior-audit errors (R-08, R-11) |
| D-03 generated-mirror placement guard | Prevents doctrine stubs landing inside `frontend/src/types/` |
| D-04 deleting doctrine requires re-homing dependents same-change | Prevents `motto_v4`/`motto_v5` orphaned-reference class |

---

## Part 5 — The one control that fixes the most

**A retirement gate (target + deletion date + CI enforcer) + an authority/epistemic label fix** removes the majority of the non-aligned instances, because:

- **Retirement gate** → fixes A-04 (TeamStore, inline pydantic), A-05 (fetch layers), A-09 (ADR numbering), A-11 (marketing gens), R-09 (doc trees), NEW-03.
- **Authority/epistemic fix** → fixes NEW-01, F-22, and the epistemic half of A-03, making the "honest gauges" genuinely honest.

Not one control fixes all — but these two are the highest-leverage.

---

## Part 6 — Decision-ready summary (for Pranay)

| # | Question | Recommendation |
|---|---|---|
| 1 | Is the project first-principles correct at the core? | **Yes.** Deterministic intake, RLS, reality tiers, gates, epistemic primitives. Harden, don't rewrite. |
| 2 | What is the single systemic defect? | **No retirement primitive.** 20+ instances of "built canonical path, never retired original." |
| 3 | What is the most surprising new finding? | **NEW-01:** the trust labels (confidence/authority per field) are **inverted** — derived/default values claim `explicit_user/FACT`. The "honest gauges" are mislabeled. |
| 4 | What is the highest-value *addition*? | **O-4 authority/epistemic relabel + O-1 retirement gate.** |
| 5 | What is the biggest latent risk? | **F-23 NEW-06:** customer-memory backend is real but the frontend never calls it, and the legacy `CUSTOMER_MEMORY_STORE` is unscoped — a latent isolation hole the moment wiring lands. Fix scoping first. |
| 6 | Is the measurement apparatus honest now? | **Mostly.** Budget F1 gate is honest and wired. Extraction/pipeline gates remain self-consistent (expected-vs-itself) — a residual F-18 over-claim corrected. |
