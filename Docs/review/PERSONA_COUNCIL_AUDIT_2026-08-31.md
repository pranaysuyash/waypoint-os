# Waypoint OS — Persona Council Audit (Project Archaeologist Lead)

**Audit date:** 2026-08-31
**Lead persona:** `PER-1065 — Project Archaeologist`
**Council:**
`PER-0923 — Evidence Architect` · `PER-0930 — Shadow-System Investigator` · `PER-91002 — Primitive Decomposition Architect` · `PER-0926 — Product Evolution Architect` · `PER-0428 — Feedback/Doctrine Alignment Reviewer` · `PER-0922 — Epistemic Integrity Architect` · `PER-0164 — Assumption Auditor`
**Persona source:** `/Users/pranay/Desktop/Understanding_Personas_29aug26/`
**Target:** `travel_agency_agent` / `waypoint-os`
**Git HEAD:** `8ece02e` (master) with a large uncommitted working tree (48 modified + ~30 untracked)
**Governing doctrine:** `OPERATING_DOCTRINE.md` v8.0 (loaded) · `REVIEW_DOCTRINE.md` (loaded) · `EXPLORATION_DOCTRINE.md` · `ARCHITECTURE_DOCTRINE.md` · `TESTING_DOCTRINE.md` · `DOCUMENTATION_DOCTRINE.md`

---

## 0. Why this audit exists, and how it differs from the one already in the repo

There is a prior audit corpus (2026-08-29/30):
- `Docs/review/PERSONA_COUNCIL_MASTER_AUDIT_2026-08-29.md` (R-01…R-16, A-01…A-21; lead PER-1065)
- `Docs/review/FINDINGS_REGISTER_2026-08-29.md` (explicit + implicit register)
- `Docs/review/IMPLEMENTATION_PLAN_2026-08-29.md` (Waves 0–6)
- `Docs/review/EXPLORATION_RESEARCH_BACKLOG_2026-08-29.md` (RQ/EX/D/NG)
- `Docs/review/FINDINGS_TASKS_CONSOLIDATED_2026-08-30.md` (the consolidated register)

This audit **does not repeat it**. Its relationship is:

1. **It re-verifies every prior finding against live code** (4 parallel read-only explorers; evidence cited per item). The repo moved significantly in 48 hours — many "non-aligned" findings are now fixed, several prior claims were wrong.
2. **It corrects the prior errors.** R-08 ("no mypy") was wrong; R-11 ("no durable lease") was wrong; R-03 ("split-brain") was reframed; A-04's `audit_bridge` "dead duplicate" is actually an intentional sync/async shim; F-18's "S1–S6 rule package" over-claims (only S1/S3/S5 present); the consolidated register lists R-15 as open P1 when it is FIXED 2026-08-31.
3. **It adds the 2026-08-31 demo findings** (DEMO-01…15 / F-20…F-26, pending ratification).
4. **It identifies genuinely new findings** (NEW-01…NEW-07) not in any prior register.
5. **It assigns FP/LT/DOC alignment verdicts** to every finding and **expands the opportunity set** (O-1…O-12).

Both documents are canonical and must be preserved. Per doctrine §6, neither supersedes the other by date alone; where they conflict, this record preserves the conflict and states the live verdict.

---

## 1. Evidence protocol (PER-0922 / PER-0923)

Truth labels per doctrine §2: **Observed / Verified / Inferred / Proposed / Unknown / Contested**.
Evidence tiers per §3: T0 assumption · T1 static · T2 targeted check · T3 integration/E2E · T4 live runtime · T5 production.

**Achieved in this audit:** T1 (broad static, 4 parallel explorers) + T2 (targeted probes) + **T3 (live backend suite baseline verified = 3,206 passed / 10 skipped / 0 failed)** via `scripts/run_backend_tests.sh`.
**Not achieved:** T4 (live browser UI E2E), T5 (production). Frontend typecheck/lint/Vitest was not re-run this session.

### Commands/checks actually executed (evidence)
- 4 parallel read-only explorers covering backend governance, frontend governance, eval gates/tests, and docs/ADR/demo findings. Each returned file:line evidence.
- `scripts/run_backend_tests.sh` baseline (recorded 2026-08-30: 3,206 passed / 10 skipped / 0 failed; CI-identical env).
- Targeted in-process probes on the canonical extractors (from the EX-DEMO-02/03 docs) reproducing the demo note's exact packet output.

**Caveat (Observed):** the 08-29 record's "358 failed" was an **environment artifact** (ran without CI env vars, without CI's `--ignore` flags, with cross-test `TRIPS_DIR` leakage, with `pytest tmp_path` failing under the sandbox shim, and with the dev server up). The CI-identical baseline is green. This is recorded rather than silently amended (doctrine §1).

---

## 2. System reconstruction — what this project actually is

**Observed.** A multi-tenant AI-augmented travel-agency operating system ("Waypoint OS"): a single-process FastAPI monolith plus a Next.js 14 App Router frontend, with a deterministic-first intake/extraction core and an LLM periphery.

```
Acquisition & Inbound     social_inbound · public_checker · messaging webhooks
  → Intake & Packet       src/intake/  (regex + dictionary, NO LLM — 59 re.compile)
  → Epistemic Decision    src/intake/decision.py  (hard/soft blockers, authority_level)
  → Strategy / NB03       src/intake/strategy.py
  → Proposal & Fulfilment proposal_lifecycle · payment_queue (read-model) · commission
  → Agentic Runtime       src/agents/runtime.py + live_tools.py (Mock by default)
  → Governance            RLS (core/rls.py) · audit · reality_tier · feature_gates
```

### 2.1 Shape of the codebase (Observed)

| Surface | Size |
|---|---|
| Backend: `spine_api/server.py` | **3,195 lines**, **64 routers**, **17 direct `@app` routes** |
| Backend library: `src/` | ~446 `.py` (intake, llm, rag, evals, agents, security, analytics, memory) |
| Tests: `tests/` | ~251 `test_*.py` files; CI-identical baseline 3,206 passed / 10 skipped / 0 failed |
| Migrations | 29 alembic revisions, single linear chain |
| Frontend | Next 14.2.20 · React 18.3.1 · 47 `page.tsx` · 30 BFF `route.ts` · 161 Vitest files · 44 `any` in prod |
| Docs | `Docs/` **2,020** `.md` + `frontend/docs/` **932** `.md` |
| Data corpus | `data/` ~97k files (72k JSON, 12k JSONL, 9.9k PDF, 3.1k JPG) |

### 2.2 The genuine architectural assets (worth preserving — do not rewrite)

These are first-principles correct and are the reason the correct intervention is **hardening**, not **replacement**.

1. **Deterministic intake core.** `src/intake/` has zero LLM imports and 59 `re.compile` calls. The LLM is reserved for conversational nuance and unstructured document/vision extraction. This boundary is correct and must be defended. *(Observed; verified by grep.)*
2. **Reality-tier honesty.** `spine_api/core/reality_tier.py:36` defines `RealityTier = REAL | CONNECTED_SANDBOX | DETERMINISTIC_PREVIEW | DATA_DEPENDENT | PLANNED` with `TIER_CAPABILITIES` gating `can_write_success_events`, `can_mutate_booking_state`, `can_make_financial_claims`. `core/feature_gates.py` carries `honest_status`. **The system declares what is fake rather than implying it is real.**
3. **Real Row-Level Security.** PostgreSQL RLS via `app.current_agency_id` (`core/rls.py`), `FORCE ROW LEVEL SECURITY` on tenant tables, fail-closed in production. 11 routers use `get_rls_db`; `auth.py` is a documented chicken-and-egg exception.
4. **Executable architectural gates.** `scripts/check_unscoped_trip_access.sh`, `scripts/check_f401.sh`, scoped mypy — invariants encoded as gates, not prose.
5. **Epistemic primitives landed** (`EpistemicStatus`, `AssumptionRecord`, slot-level `epistemic_status`) and **the honest quality gate is now wired** (budget F1 0.9524, `blocks_ci` honored).
6. **ADR for the lead-loop decision** (`ADR_ESCALATE_LEAD_PERSISTENCE_2026-08-31.md`) and the **R-15 posture matrix** are models of first-principles reasoning.

---

## 3. Chronology & decision lineage (PER-1065)

**Observed** from `git log`.

| Window | Event |
|---|---|
| 2026-08-29 | Refactor Architect audit (R-01…R-16) + Persona Council audit. |
| 2026-08-30 | A-01/A-13/A-19/R-15/RQ-01/RQ-03/RQ-06/EX-06/F-18 remediation landed (uncommitted); `8ece02e` ships IDEA-120/122/123/124 + traveler-memory + persona-council workbench. |
| 2026-08-31 | Tool-Taster demo (DEMO-01…15); P0 lead-loop ADR + implementation; R-15 PII reconciliation; 14 new docs. |

### 3.1 The audit treadmill (still a process finding)

The repo has ~25 audits across 2026-04 → 2026-08, each selecting a different lead persona to avoid anchoring, each closing zero findings from its predecessor. The **findings-lifecycle control** (`scripts/check_findings_register.py`, 3-state machine) was created 2026-08-30 but **not wired into CI** (NEW-05). Evidence of drift: the consolidated register lists R-15 as open P1, but R-15 is FIXED 2026-08-31.

**Assessment (PER-0428):** this is a doctrine gap, not a competence failure. The fix is to **wire the findings-register gate into CI** + make every audit **re-verify** the prior register rather than create a parallel one. This audit is the first to do so.

---

## 4. Cross-cutting: shadow-system root causes (PER-0930)

Stripping domain nouns, the duplicate systems fall into three root causes:

1. **Migration started, never finished.** `TeamStore` (DEPRECATED) vs `membership_service`; the retirement step was never part of the migration plan. Root cause: **no retirement primitive** (NEW-03).
2. **Two auth/shared-boundary owners by accretion, and one config contract missing.** No `BaseSettings` — **156 scattered `os.getenv`** (no config-as-contract), and `server.py` defines **19 inline pydantic models** alongside `contract.py` + routers.
3. **Trust-label vocabulary inverted.** Every freeform extractor passes `EXPLICIT_USER` unconditionally (`extractors.py:1863-2290`), so derived/default/spurious values claim `FACT` (NEW-01).

---

## 5. Net verdict

**As PER-1065:** this is a genuinely substantial system, not a facade. The deterministic core, RLS, reality-tier honesty, executable gates, and epistemic primitives are real, first-principles assets. **Do not rewrite.** The repeating failure is *"built the canonical path, never retired the original."*

**As PER-91002 (Primitive Decomposition):** the highest-value missing primitive is **retirement** (a state with a date + enforcer, not a comment). The second is a **correct authority/epistemic label taxonomy** (currently inverted).

**As PER-0926 (Product Evolution):** long-term risk is not any single defect — it is the absence of a *finish* mechanism. Every improvement adds a layer instead of replacing one. Fix = retirement gate.

**As PER-0428 (Doctrine):** §5 (one canonical source) is the most-violated rule, on both sides of the stack. But this is **one systemic problem with many instances** — one control (retirement gate) + one labelling fix removes most of them.

**As PER-0922 (Epistemic Integrity):** the most serious finding is **NEW-01** — the evidence apparatus is **inverted on the facts path**. The system was just made honest about **tiers** (RealityTier, honest gates); it is not yet honest about **per-field authority** (derived/default = `FACT`). Second: **NEW-04** — RAG "dense" retrieval is a hash-vector placeholder, a claim-reality risk if ever called "semantic search."

---

## 6. What this audit did NOT establish

| Gap | Next check |
|---|---|
| Frontend typecheck/lint/Vitest this session | `cd frontend && npm run typecheck && npm run lint && npm test -- --run` |
| Live browser UI E2E for the demo loop | Strict visual E2E standard; dev servers on :8000/:3005; pre-hydrated auth |
| Whether "dense" RAG can be made semantic cheaply | Research + replace `generate_local_embedding` behind a real interface |
| ADR 003/004/005 lost or never written | `git log --diff-filter=D -- '*ADR-00[345]*'` |
| The 4 marketing generations' real traffic | Vercel analytics |
| Actual cross-tenant exploitability post-memory-wiring | Re-audit `customer_memory.py` legacy store scoping before wiring |

---

## 7. Deliverables from this audit

| Document | Purpose |
|---|---|
| `Docs/review/PERSONA_COUNCIL_AUDIT_2026-08-31.md` | This document |
| `Docs/review/FINDINGS_REGISTER_2026-08-31.md` | Consolidated explicit + implicit register with FP/LT/DOC verdicts |
| `Docs/review/ALIGNMENT_EVALUATION_2026-08-31.md` | Per-finding FP/LT/DOC evaluation + "what else" expansion |
| `Docs/review/IMPLEMENTATION_PLAN_2026-08-31.md` | Sequenced, gated implementation plan |
