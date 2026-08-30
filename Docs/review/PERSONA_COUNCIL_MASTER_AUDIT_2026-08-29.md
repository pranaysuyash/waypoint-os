# Waypoint OS — Persona Council Master Audit (Project Archaeologist Lead)

**Audit date:** 2026-08-29
**Lead persona:** `PER-1065 — Project Archaeologist`
**Supporting council:**
`PER-0428 — Feedback Doctrine Alignment Reviewer` ·
`PER-0922 — Epistemic Integrity Architect` ·
`PER-0923 — Evidence Architect` ·
`PER-0930 — Shadow-System Investigator` ·
`PER-91002 — Primitive Decomposition Architect` ·
`PER-0926 — Product Evolution Architect` ·
`PER-0164 — Assumption Auditor`

**Persona source:** `/Users/pranay/Desktop/Understanding_Personas_29aug26/`
**Target:** `travel_agency_agent` / `waypoint-os` (repo: `pranaysuyash/waypoint-os`)
**Git HEAD:** `c31dc18` (master, in sync with `origin/master`) — **with a large uncommitted working tree**
**Governing doctrine:** `OPERATING_DOCTRINE.md` v8.0 (root) · `REVIEW_DOCTRINE.md` · `ARCHITECTURE_DOCTRINE.md` · `TESTING_DOCTRINE.md` · `DOCUMENTATION_DOCTRINE.md` · `EXPLORATION_DOCTRINE.md`

> **Lead persona note (PER-1065 core question):** *How did this project arrive at its
> current state, which assumptions and decisions shaped it, and what valuable or
> dangerous knowledge has been lost from the current narrative?*
>
> **Persona failure mode we are explicitly guarding against:** "assuming the newest
> file is authoritative" and "treating old docs as current truth." Both are live
> risks in this repo. See §4.

---

## 0. Why this audit exists (and how it differs from the one already in the repo)

There is already a same-day audit at
`Docs/review/WAYPOINT_OS_REFACTOR_ARCHITECT_AUDIT_2026-08-29.md` (16 findings
R-01…R-16, lead persona `PER-0001 — Refactor Decision Architect`).

This audit **does not repeat it**. Its relationship to that document is:

1. **It re-verifies R-01…R-16 against live code** (§4). Several have been fixed in
   the uncommitted working tree since that audit was written; several were wrong.
2. **It widens the aperture** from "refactor decisions" to the full archaeology
   question: what is actually here, what is real vs simulated, what is duplicated,
   and what has been lost.
3. **It supplies the three things the earlier audit explicitly listed as missing
   evidence:** a fresh test run, a fresh mypy run, and resolution of the
   IDEA-pad ↔ git reconciliation gap.

**Both documents are canonical and must be preserved.** Per `OPERATING_DOCTRINE.md`
§6 (semantic salvage) and §10 (parallel work), neither supersedes the other by date
alone. Where they conflict, this document records the conflict rather than resolving
it by assumption.

---

## 1. Evidence protocol (PER-0922 / PER-0923)

Every load-bearing claim below carries a truth label from `OPERATING_DOCTRINE.md` §2:

| Label | Meaning |
|---|---|
| **Observed** | Directly seen in a live file, command output, or artifact. Path cited. |
| **Verified** | Independently checked against a test, invariant, or executed command. Sensitivity stated. |
| **Inferred** | Best explanation supported by current evidence. Assumption named. |
| **Proposed** | Design or action not yet implemented or checked. |
| **Unknown** | Not established. Exact check needed is stated. |
| **Contested** | Two current sources disagree. Both preserved. |

Evidence tiers per §3: **T0** assumption · **T1** static inspection · **T2** targeted
test/check · **T3** integration/E2E · **T4** live runtime · **T5** production-like.

**Achieved in this audit:** T1 (broad), **T2/T3 (backend test suite executed against
live PostgreSQL — 2,803 pass / 358 fail / 19 errors / 8 skipped)**, **T2 (mypy scoped
gate executed — clean)**, **T2 (ruff, mypy, CI gate scripts inspected)**.
**Not achieved:** T4 (live browser), T5 (deployed/production). No frontend build,
lint, or Vitest run was executed this session.

### Commands actually executed (evidence for this document)

```
# Backend suite, against live local PostgreSQL (port 5432 confirmed open)
.venv/bin/python -m pytest -q
  → 358 failed, 2803 passed, 8 skipped, 19 errors in 528.77s (0:08:48)

# Scoped security/tenancy type gate
.venv/bin/python -m mypy
  → Success: no issues found in 10 source files
```

**Caveat on the test run (Observed):** the local `.env` supplies `TRIPSTORE_BACKEND`,
`JWT_SECRET`, `PUBLIC_CHECKER_AGENCY_ID`, `OPENAI_API_KEY`, `OPENAI_MODEL` but **not**
`DATABASE_URL`. CI supplies `DATABASE_URL` explicitly and passes
`--ignore=tests/test_vision_extraction.py --ignore=tests/test_extraction_fallback.py`
(OpenAI-key-gated). My run did not apply those ignores. **Therefore the local failure
count is an upper bound and is not byte-identical to CI.** Directionally it is
consistent with, and worse than, the ~186 failures the R-audit cited from
2026-08-01. **Tier: T3, sensitivity S1.**

---

## 2. System reconstruction — what this project actually is

**Observed.** A multi-tenant AI-augmented travel-agency operating system
("Waypoint OS"): a single-process FastAPI monolith plus a Next.js 14 App Router
frontend, with a deterministic-first intake/extraction core and an LLM periphery.

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
| Backend: `spine_api/` | 114 `.py`; `server.py` **3,186 lines**, **50 routers mounted** |
| Backend library: `src/` | ~446 `.py` (intake, llm, rag, evals, agents, security, analytics) |
| Tests: `tests/` | **227 files** (225 `test_*`) |
| Migrations | 28 alembic revisions, single linear chain |
| Frontend | Next 14.2.20 · React 18.3.1 · **47 `page.tsx`** · **30 BFF `route.ts`** · 161 Vitest files |
| Docs | `Docs/` **1,975 `.md`** + `frontend/docs/` **921 files** |
| Data corpus | `data/` ~97k files (72k JSON, 12k JSONL, 9.9k PDF, 3.1k JPG) |

### 2.2 The genuine architectural assets (worth preserving — do not rewrite)

These are **first-principles correct** and are the reason the correct intervention is
hardening, not replacement.

1. **Deterministic intake core.** `src/intake/` contains **zero** LLM imports and 59
   `re.compile` calls. The LLM is reserved for conversational nuance and unstructured
   document/vision extraction. This boundary is correct and must be defended.
   *(Observed; verified by grep for `openai|gemini|anthropic|transformers|torch` → 0 files.)*
2. **Reality-tier self-declaration.** `spine_api/core/reality_tier.py` defines
   `RealityTier = REAL | CONNECTED_SANDBOX | DETERMINISTIC_PREVIEW | DATA_DEPENDENT | PLANNED`
   with `TIER_CAPABILITIES` gating `can_write_success_events`, `can_mutate_booking_state`,
   `can_make_financial_claims`. `core/feature_gates.py` `FEATURE_REGISTRY` carries
   `honest_status` + `requires_integration` per feature. **The system declares what is
   fake rather than implying it is real.** This is the strongest epistemic asset here.
3. **Real Row-Level Security.** PostgreSQL RLS via `app.current_agency_id`
   (`core/rls.py:214-247`), `FORCE ROW LEVEL SECURITY` on 12 tenant tables,
   fail-closed in production. `set_rls_agency()` at `core/auth.py:165`.
4. **Architectural fitness functions as CI gates.** Two custom shell gates that encode
   invariants mechanically:
   - `scripts/check_unscoped_trip_access.sh` — fails CI on any bare
     `TripStore.get_trip(` in a router (forces `get_trip_for_agency`).
   - `scripts/check_f401.sh` — unused-import gate.
   Plus a scoped mypy gate over exactly the tenancy-critical files.
   This is the right instinct: **invariants encoded as executable gates, not prose.**
5. **Epistemic primitives now landed** (uncommitted): `EpistemicStatus` and
   `AssumptionRecord` in `src/intake/packet_models.py:91-119`. See §4 R-06.

---

## 3. Chronology & decision lineage (PER-1065)

**Observed** from `git log`.

| Window | Event |
|---|---|
| 2026-04 | Baseline audits (`ARCHITECTURE_BASELINE_AUDIT_2026-05-02.md`, security/frontend audits). `memory/` last written ~2026-04-28 and **never touched since**. |
| 2026-05-02 | 22 ADRs established; `Docs/BASELINE_AUDIT_INDEX` + action plan. |
| 2026-07-28/29 | `MONTH6_PRODUCT_AUDIT_AND_SIMULATION`; 14 unnumbered ADRs accepted in one batch. |
| 2026-08-01 | `LAUNCH_AUDIT_BASELINE` + DD1–DD8 series. |
| 2026-08-03/04 | 10 CI-repair commits; ADRs 15/16/17 (Edge SLM ONNX, Stress Suite, AutoResearch). |
| 2026-08-07 | `fix(launch): remediate external review items` — the launch audit **was** followed through. |
| 2026-08-08/09 | Four feature commits ship IDEA-120/122/123/124. |
| 2026-08-24 | `WAYPOINT_OS_FIRST_PRINCIPLES_AGENTIC_AUDIT` — **no status/verdict metadata at all**. |
| 2026-08-29 | Refactor Architect audit (R-01…R-16). **This audit.** Large uncommitted working tree in flight. |

### 3.1 Three structural decision-lineage defects

1. **No supersession mechanism in the ADR corpus.** Grep for
   `superseded|deprecated|obsolete|amended by|replaced by` across all 22 ADRs returns
   **0 matches**. Every ADR is terminal `Accepted`. The repo **cannot express "this
   decision was replaced."** *(Observed. Severity: high — it makes ADR-vs-code
   contradiction permanently unresolvable from the record.)*
2. **ADR numbering is broken.** `Docs/architecture/adr/` jumps `002 → 006`; 003/004/005
   absent (**Unknown** whether lost or never written). Only 4 of 22 ADRs carry numbers;
   the 14-strong 2026-07-29 batch is title-only. Two incompatible numbering schemes.
3. **The governing-rule chain has filename drift (corrected — see §5.13).** `motto_v4.md`
   **does not exist** anywhere in the tree, yet **18 files reference it** and all four
   numbered ADRs declare *"Governing Rule: `motto_v4.md` (Rule 0.9 / 0.10 / 0.15…)"*.
   Only `motto.md` (5,895 B, 2026-05-17) survives. Earlier doctrine survives only as
   hash-suffixed corpses in `.agent/archives/doctrine-legacy/`
   (`motto_v5.md.7c323cecc4fd.md`, `motto_v3.md.0f1341a5bbd3.md`, …).
   **Correction:** the *content* is **not** lost — `Docs/FIRST_PRINCIPLES_MOTTO_V4_DOCTRINE.md`
   (107 lines) is the canonical declaration of first-principles under motto_v4. The defect
   is **filename drift**: 18 references point at a filename that was renamed/absorbed.
   *(Observed. Severity reduced from P1-knowledge-loss to P2-reference-hygiene.)*

### 3.2 The audit treadmill (a process finding, not a code finding)

**Observed.** The repo has accumulated ~25 audits across 2026-04 → 2026-08. The
pattern is consistent:

- Each new audit selects a **different lead persona** to "avoid anchoring on prior
  audit framing" (stated explicitly in the 08-29 audit, §2).
- Each therefore **closes zero findings from its predecessor** — the 08-29 audit
  reports closing zero 08-24 findings.
- Completion claims are falsifiable and sometimes false:
  - `NAVIGATION_TASKS.md` declares **14/14 DONE** and "Full 14/14 Modules Active".
    Verified false: `nav-modules.ts:60,64,68,73` all carry
    `{ id: 'value-surface-complete', complete: false }`. The change only converted
    hardcoded `false` → a gate expression; it never flipped them on. *(Observed.)*
  - `Docs/UNIT1_FINAL_COMPLETION_SUMMARY.md` line 1: *"✅ UNIT-1 IMPLEMENTATION: 100%
    COMPLETE & LAUNCH-READY"* vs. the 08-29 verdict *"Not launch-ready."*
  - `Docs/AUDIT_VERIFICATION_REPORT_2026-04-15.md` and
    `ADD_DATES_INVESTIGATION_COMPLETE.md` both say "FULLY RESOLVED"; **Unknown**
    whether regression-tested.

**Assessment (PER-0428):** this is not doctrine violation — it is a **doctrine gap**.
`OPERATING_DOCTRINE.md` §14 requires decisions to record "revisit trigger" and to
"append decision updates instead of rewriting history," and §6 requires supersession
to preserve provenance. Neither mechanism exists for *audit findings*, as distinct
from ADRs. **Recommendation: an audit-findings register with explicit
`open | fixed | wontfix | superseded` state and a re-verification date.** That is the
missing control, and its absence is why the same repo can be "100% complete" and
"not launch-ready" simultaneously.

---

## 4. Re-verification of the 2026-08-29 Refactor Architect audit (R-01…R-16)

**This is the highest-value section.** Each R-item was re-checked against live code
today. Status changes are the headline result.

| ID | Finding | R-audit verdict | Status today | Evidence |
|---|---|---|---|---|
| **R-01** | 4 stale `v6.1` doctrine copies | Non-aligned **P0** | ✅ **FIXED** | Each of the 4 is now a 1,357 B *"Mirror Pointer"*: declares canonical path, v8.0, SHA-256 `ff848618…`, generation date, and "NOT authoritative / do not edit by hand". All 4 byte-identical (md5 `6c9d18a1…`). Fully satisfies doctrine §17. |
| **R-02** | Client `X-Agency-ID` trusted on 5 routers | Non-aligned **P0** | ✅ **FIXED** (uncommitted) | `core/auth.py:170-185`: header honored **only** if `PYTEST_CURRENT_TEST` or `SPINE_API_DISABLE_AUTH`. All 5 routers (`commission`, `group_booking`, `multimodal`, `customer_memory`, `price_lock`) now depend on `get_current_agency_id`. Docstring states the invariant explicitly. |
| **R-03** | File-store split-brain; header honored when `TRIPSTORE_BACKEND==file` | Non-aligned **P0** | ⚠️ **PARTIAL** | Header trust fixed. **Split-brain remains:** `data/trips/` holds **1,635 JSON** files; `persistence.py:110-114` still defines `TRIPS_DIR`/`AUDIT_DIR`/etc. Whether SQL mode still writes them is **Unknown** (needs runtime probe). |
| **R-04** | `commission.py` fabricates ₹3000 | Non-aligned **P1** | ✅ **FIXED** (uncommitted) | `commission.py:88`: `if gross_cents <= 0: continue` with comment *"Require a real booking amount; do not fabricate a ₹3000 default."* Zero trips fabricated. |
| **R-05** | `/send` returns `SENT` without dispatch | Non-aligned **P1** | ✅ **FIXED** (uncommitted) | `messaging.py:76-88`: returns `status="QUEUED"`, `dispatch_status="QUEUED"`, with an honest docstring explaining no provider HTTP call is made. |
| **R-06** | `EpistemicStatus` / `AssumptionRegister` / `CONNECTIVITY_TIER` absent | Unfinished FP target **P1** | ⚠️ **PARTIAL** (uncommitted) | `EpistemicStatus` ✅ at `packet_models.py:91` (FACT/INFERRED/ASSUMED/UNKNOWN); `AssumptionRecord` ✅ at `:101`; mapping ✅ at `extractors.py:1738-1749`. **`CONNECTIVITY_TIER` still absent** (grep → 0). Not in `HEAD` — uncommitted. |
| **R-07** | Eval gates self-consistent (cannot fail) | Test theater **P1** | ❌ **OPEN** | Confirmed and *worse than claimed*. See §5.1. |
| **R-08** | ~186 tests fail; no mypy | Non-aligned **P1** | ⚠️ **SPLIT** | **mypy: FIXED** — configured in `pyproject.toml:119-152`, scoped to 10 tenancy-critical files, wired as a **blocking CI step** (`ci.yml:85-86`), and **passes clean** (`Success: no issues found in 10 source files`). The R-audit's "no mypy" claim is **stale/wrong**. **Tests: WORSE** — 358 failed + 19 errors (vs ~186 on 08-01). |
| **R-09** | `Docs/` ∥ `frontend/docs/` | Non-aligned **P1** | ❌ **OPEN** | 1,975 + 921 files, no reconciliation. |
| **R-10** | `server.py` 3,719 lines; 44 routers; two audit systems | Debt **P2** | ⚠️ **PARTIAL** | `server.py` reduced to **3,186 lines** (−533); 50 routers (up from 44). Two audit systems **remain**: file hash-chain (`persistence.py:2056-2086`) vs PostgreSQL `audit_logs` model with **no** hash chain. |
| **R-11** | No durable lease/heartbeat; zombie tasks | Non-aligned **P2** | ⚠️ **PARTLY WRONG** | **Lease EXISTS and is durable**: `models/agent_work.py:14-41` `AgentWorkLease` + `services/agent_work_coordinator.py` with `SELECT … FOR UPDATE` (`:161-173`), 60s lease, poison-on-exhaust. Expired-lease reacquisition works (`:95-113`) → **no zombies**. **Heartbeat is dead code**: `ExecutionLease` (`runtime.py:52-82`) has `heartbeat()` with **zero call sites**. Real residual risk: a task running >60s is re-acquirable → **double-execution**. |
| **R-12** | No Journey Dependency Graph for IROPS | Opportunity **P2** | ❌ **OPEN** | Not present. Genuine opportunity. |
| **R-13** | Nav rollout-gate drift | Drift **P2** | ❌ **OPEN** | Verified: `nav-modules.ts` gates all resolve `complete: false`. |
| **R-14** | Two-generation styling | Debt **P3** | ❌ **OPEN** | Literal-hex pages + shadcn-style primitive layer coexist. |
| **R-15** | PII guard fail-open in production | Non-aligned **P1** | ❌ **OPEN** | Confirmed: `src/security/privacy_guard.py:484-486` `if not is_dogfood_mode(): return` — **returns with no log line**. Layer 2 (SpaCy) *is* fail-closed in prod (`:412-428` raises), so loader and gate disagree. |
| **R-16** | No trace-correlation reader; no CI event-flow assertion | Gap **P2** | ❌ **OPEN** | OTel spans real; no reader, no CI assertion. |

### 4.1 Net R-status

**Fully fixed: 5** (R-01, R-02, R-04, R-05, and the mypy half of R-08)
**Partially fixed: 4** (R-03, R-06, R-10, R-11)
**Open: 8** (R-07, R-09, R-12, R-13, R-14, R-15, R-16, and the test-count half of R-08)
**Demonstrably wrong in the prior audit: 2** (R-08 "no mypy"; R-11 "no durable lease")

> **PER-0164 Assumption Auditor note.** The prior audit's two errors point the same
> direction: it asserted absence from **grep-and-memory** rather than from executed
> checks. R-08's mypy claim was falsifiable in one command; R-11's lease claim was
> falsifiable by reading `models/agent_work.py`. **Rule to adopt: absence claims
> require an executed command, not a grep.** This is a process defect, not a
> competence defect, and it should be encoded as a review checklist item.

---

## 5. New findings — shadow systems, epistemic gaps, and decay (PER-0930 / PER-0922)

### 5.1 A-01 — The only honest quality gate is structurally excluded from CI (P0, Observed/Verified)

**Verified** by reading `scripts/verify_d6_gate_snapshot.py:29-67` and
`src/evals/audit/manifest.yaml:3-7`.

The eval system has three gates. Two are tautologies; one is real.

- **Extraction gate — tautology.** `snapshot.py:143-145` builds
  `saved = {f.fixture_id: f.expected_extracted_fields …}` and the code's own comment
  reads *"Self-consistent baseline: expected extraction used as actual."*
  `EXPECTED_EXTRACTION_BASELINE_F1 = 1.0` (`:98-100`). `blocks_ci: false`.
- **Pipeline gate — tautology.** `snapshot.py:206-214` builds `actual_results` from
  `expected_*` fields. `blocks_ci: false`.
- **Budget gate — REAL, and failing.** `data/evals/d6_audit_gate_snapshot.json`:
  `overall_f1: 0.2857`, `precision 1.0`, `recall 0.1667`, `status: "failing"`,
  **`blocks_ci: true`**, `baseline_drifted: true`, with the note *"Live pipeline
  extraction results used for budget F1 evaluation."* By difficulty: easy 0.56,
  **medium 0.0, hard 0.0**.

**The defect:** `_check_blocks_ci()` inspects `routing_health`, `extraction_health`,
`pipeline_health`, and `categories.*` — **it never reads `budget_health.blocks_ci`.**
So the single genuine measurement cannot fail the build.

**A second, independent bypass exists:** `budget_health.overall_f1` *is* injected into
`category_accuracy["budget"]` (`snapshot.py:353-355`), but `manifest.yaml:3-7` defines
budget **without** `min_accuracy`, so it defaults to `0.0` (`gates.py:28`) and the
guard `if accuracy is not None and min_accuracy > 0.0` (`gates.py:39`) never fires.
Result: `categories.budget` reports `blocks_ci: false, meets_thresholds: true`.

**And the tautology is now protected by tests:** `tests/evals/test_d6_gate_snapshot.py:27,56,142`
*assert* `blocks_ci is False` — baking "this gate can never fail" in as expected behaviour.

**Verdict: non-aligned (doctrine §3 — "Passing counts are not proof"; Testing Doctrine).**
This is worse than "eval theater." It is eval theater **with a failing real gate
deliberately muted on two independent paths and defended by assertions.**

**Primitive decomposition (PER-91002):** strip the domain nouns and this is
*"a measurement system whose only true instrument is disconnected from the alarm, and
whose placebo instruments are wired to the alarm and read green."* The fix is not
"improve the model" — it is **reconnecting the instrument and unmuting the alarm.**

### 5.2 A-02 — RAG embeddings are hash vectors, not semantic (P1, Observed)

`src/rag/indexer.py:20-35` `generate_local_embedding()` produces a
*"deterministic normalized pseudo-embedding"* by hashing each word into a 64-dim
bucket (`:28-29`) — effectively **md5 bag-of-words**. It is called **unconditionally**
at `:81` and `:107`. The module docstring (`:4`) claims "API and deterministic local
fallbacks"; **no API path exists.**

The surrounding plumbing is genuinely good and worth keeping: SQLite store with real
schema/indices (`store.py:46-95`), **BM25 sparse + dense + RRF fusion**
(`retriever.py:36-102`), tenant scoping, and real citation provenance
(`grounding.py:73-86` emits title, `section_heading`, `page_number`, `document_id`)
with fail-closed `must_confirm` when ungrounded (`:25-34`). Groundedness scoring is
word-overlap heuristic (`:45-53`), not entailment.

**Verdict: partially aligned.** Architecture is right; the embedding primitive is a
placeholder masquerading as a capability. Today only BM25 does real work.
**This is a claim-reality risk (doctrine §13)** if retrieval quality is ever described
as "semantic search."

### 5.3 A-03 — Agent tools default to Mock; the shipped config is 100% mock (P1, Observed)

`src/agents/live_tools.py` has 9 tools: **4 Mock, 5 real.**
Mock: `MockWeatherTool:41`, `MockFlightStatusTool:72`, `MockPriceWatchTool:97`,
`MockSafetyAlertTool:123` — all return `mode: "mock"`, confidence 0.50–0.55.
Real: `OpenMeteoWeatherTool:151` (live, keyless), `HTTPFlightStatusTool:236`,
`HTTPPriceWatchTool:275`, `HTTPSafetyAlertTool:314`, `StateDeptTravelAdvisoryTool:348`.

The switch, `live_tools.py:405-408`:
```python
if os.getenv("TRAVEL_AGENT_ENABLE_LIVE_TOOLS", "").strip().lower() in {"1","true","yes"}:
    return OpenMeteoWeatherTool()
return MockWeatherTool()          # ← DEFAULT
```
`.env` sets none of these → **the shipped dev config runs 100% mock tools.**

**Credit where due:** the mocks self-declare (`"mode": "mock"`,
`source="in_repo_mock_weather"`). Combined with `reality_tier.py`, the system is
honest about being simulated. **Verdict: aligned in spirit, incomplete in plumbing.**
The gap is that `CONNECTIVITY_TIER` (R-06's third primitive) would let the *system*
assert this globally instead of each tool individually.

### 5.4 A-04 — Backend duplicate systems inventory (PER-0930) (P1/P2, Observed)

| Concern | Side A | Side B |
|---|---|---|
| DB session factory | `core/database.py:28-44` | `persistence.py:82-90` — second `create_async_engine` |
| Auth | Dependency `core/auth.py:34-167` | ASGI `core/middleware.py:46-109` — decodes JWT **again** (`:70`), opens its **own** session (`:92`). **Two full auth passes per request.** |
| Audit | `core/audit.py:145` `audit_logger()` | `core/audit_bridge.py:39` `audit()` — **zero production callers** (dead) |
| File vs SQL audit | `persistence.py:2056-2086` SHA-256 hash chain (**RULE_015**) | `models/audit.py` PostgreSQL `audit_logs` — **no hash chain** |
| Membership | `services/membership_service.py` | `persistence.py:2511` `TeamStore`, docstring `DEPRECATED … will be removed after migration` |
| Pydantic schemas | `routers/trip_documents.py:30,34,51,56` · `routers/public_collection.py:27,44,57` | `server.py:2394,2411,2502,2810,2828,2832,2836` — byte-level duplicates |
| Scoring | `spine_api/scoring/__init__.py` (canonical 2D urgency×importance) | `services/inbox_projection.py:461-475` legacy 1D `_DEFAULT_PRIORITY_SCORE` fallback |
| LLM vision | `src/llm/{base,openai_client,gemini_client,local_llm}.py` | `src/extraction/{vision_client,gemini_vision_client,openai_vision_extractor}.py` — **3rd path** |
| Config | 150 scattered `os.getenv` sites | No `BaseSettings`/`pydantic_settings` anywhere |

**Verdict: non-aligned (doctrine §5 — "One canonical source per resource … Extend the
canonical path. Do not create v2, shadow routes, parallel stores…").** Each pair is a
second source of truth. Notably, several carry `DEPRECATED` markers that have not been
retired — i.e. the team *knows* and hasn't had a migration-and-retirement plan, which
is exactly what §5 requires before creating the parallel path in the first place.

### 5.5 A-05 — Frontend: three competing data-fetch layers (P1, Observed)

**104 raw `fetch(` call sites** (excl. tests) alongside a canonical
`lib/api-client.ts` (1,976 lines). **70 files** use the canonical client;
**16 files use BOTH.** `hooks/useUnifiedState.ts:28` documents the bypass:
*"Keeps raw fetch() (not api-client.ts) because this is a polling endpoint."*

Layers: (1) canonical `api-client.ts`; (2) BFF server layer (`proxy-core.ts`,
`server-auth.ts`, `bff-auth.ts`, 30 `route.ts`); (3) ad-hoc client fetch in 30 files;
(4) store-level fetch (`stores/auth.ts:57,75,97`).

**Verdict: non-aligned (doctrine §5).** Same defect class as A-04.

### 5.6 A-06 — Generated type contract is orphaned and stale (P1, Observed)

`scripts/generate_types.py` generates `src/types/generated/spine-api.ts` (918 lines)
from `spine_api/contract.py` via `pydantic2ts`. Its own docstring says *"This is the
only canonical generated type file … all frontend imports must use this single path."*

**Reality: only 5 of 449 files import it.** Everything else uses hand-written
`types/spine.ts`, `types/audit.ts`, `types/governance.ts`, `types/auth-session.ts`.

**And it is stale:** last generated at commit `5a544ba` (Aug 1); `contract.py` has
changed since (`18465bb`, Aug 7) **plus ~299 lines of uncommitted change today**.
`generate_types.py` is **not in CI** and **not a package.json script** — regeneration
is manual. `contract.py` contains no reference to it.

**Verdict: non-aligned (doctrine §5, §12).** A declared contract that nothing enforces
is worse than no contract: it manufactures false confidence.

### 5.7 A-07 — Documentation decay and parallel trees (P1, Observed)

- **Two trees:** `Docs/` 1,975 `.md` ∥ `frontend/docs/` 921 files.
- **Category is encoded in filename, not directory.** ADRs and audits are flat-filed
  at `Docs/` root; `Docs/decisions/` has 6 files and **none are ADRs**; `Docs/audit/`
  has 2. Three parallel archive locations: `Archive/`, `Docs/archives/`,
  `.agent/archives/`.
- **`Docs/index.md` and `Docs/INDEX.md` are the same inode** (519210385) — a
  case-duplicate that will break on case-sensitive Linux CI.
- **CHANGELOG is ~3.5 months stale** (last modified 2026-04-29) and its stated scope
  is *"changes to the Waypoint OS **frontend**"* — so it never covered backend work
  even when current. Six feature commits (IDEA-119…124) and 4 launch-remediation
  commits from August are absent.
- **Dangling references:** 6 docs reference `next.config.ts` (deleted; only
  `next.config.mjs` exists). 3 docs reference `motto_v5.md` (deleted).
- **Empty dirs:** `Docs/responsive-audit/`, `Docs/artifacts/`.
- **`CHANGELOG.md` scope line is itself the finding:** a changelog scoped to one
  surface in a full-stack repo silently becomes a lie of omission.

### 5.8 A-08 — Idea-pad reconciliation is broken (P2, Observed)

`IDEA_PAD.md`: 134 cards. **Stage distribution: `inbox` 121 · `committed` 6 ·
`qualified` 4 · `active` 1 · `done` 1.** Only **1 of 133** real ideas is done.

**Git proves the pad is stale:** IDEA-120/122/123/124 **shipped** in commits dated
2026-08-08/09, yet the pad still marks them `inbox`. Pad last touched 2026-08-12.
The §0 WIP registry rows all carry `last_check_in: 2026-02-20` — ~6 months dead while
the cards themselves are current.

`IDEA_DUMP.md` (104 lines) has **zero `IDEA-NNN` IDs** → no join key; promotion can
only be matched by free-text theme. **Unreconciled.**

**Verdict: non-aligned (doctrine §9 — "Keep research maps and worklogs current").**
The backlog no longer reflects shipped reality, so it cannot be used for prioritisation.

### 5.9 A-09 — Four concurrent marketing generations are live (P2, Observed)

Root-level routes `/v2`, `/v3`, `/v4`, `/v5` (`app/v2/page.tsx` … `app/v5/page.tsx`)
all ship simultaneously, outside every route group and therefore outside every group
layout. Plus `/pricing`, `/corporate/offsites`, `/intake/fast`.

**Verdict: non-aligned (doctrine §5 — shadow routes; PER-0926 — "additive-only product
growth" failure mode).** Four generations of the same surface = four sources of truth.

### 5.10 A-10 — `src/proxy.ts` is dead code and the edge auth gate may not run (P1, Inferred)

`src/proxy.ts` (4,452 B) claims to be a Next.js proxy/edge middleware. **No
`middleware.ts` exists anywhere**, and `proxy.ts` is **never imported** (0 references).
Under Next 14 this file is inert.

**Inferred:** the edge auth gate it describes does not currently run.
**Unknown:** whether it functioned under a newer Next previously (relevant because
`package.json` carries `eslint-config-next@^16.2.4` and `@next/bundle-analyzer@^16.2.4`
— **two major versions ahead of Next 14** — and `@types/react@^19` against React 18).

**Verdict: needs a decision, not a fix.** Either restore a real `middleware.ts` or
delete `proxy.ts`. Leaving an inert file that *looks* like an auth gate is a security
clarity hazard.

### 5.11 A-11 — Secrets posture (P1, Observed — no values reproduced)

- `.env` (gitignored, `.gitignore:17`) contains a live `OPENAI_API_KEY`. **Rotate it.**
- `core/database.py:22` defaults `DATABASE_URL` to a **committed dev password**
  (same value hardcoded in `ci.yml:105,128,142`).
- `SPINE_API_DISABLE_AUTH` is a global kill switch returning a synthetic owner
  (`auth.py:62,72,96-97,152-156`) and disabling `AuthMiddleware` entirely
  (`middleware.py:46`). Guarded only by `core/startup_assertions.py:118`, which
  **warns but does not crash** outside production/staging (`:162-167`).
- PII: `services/private_fields.py`, `core/logging_filter.py`,
  `core/llm_egress.py:180 strip_pii` all exist — good.

**Verdict: partially aligned.** Real controls exist; the auth kill switch's
fail-open-by-default is the risk.

### 5.12 A-12 — Frontend debt is undocumented, not absent (P2, Observed)

**Zero** `TODO`, `FIXME`, `HACK`, `XXX`, `@ts-ignore` markers exist in `frontend/src`.
**1** `@ts-expect-error` (`app/api/stream-events/[runId]/route.ts:76`).
**5** `eslint-disable`, of which **4 are in files modified in the current changeset**
(`workbench/PageClient.tsx:307,324`; `ui/drawer.tsx:46`; `ui/modal.tsx:50`).

Meanwhile: **34 non-test files exceed 400 lines** (worst:
`itinerary-checker/PageClient.tsx` **2,932**; `IntakePanel.tsx` 2,005;
`api-client.ts` 1,976) and **65 `any` in production code** (hotspot:
`workbench/DecisionTab.tsx`, 9 × `as any`).

**Verdict: the absence of markers is itself the signal.** Given 34 oversized files,
debt has not been eliminated — it has been **left unlabelled**. A clean grep is being
mistaken for a clean codebase. *(PER-0922: "missing evidence treated as negative
evidence" — a named failure mode.)*

### 5.13 A-13 — Parallel remediation work is in flight right now (process risk)

**Observed.** Discovered late in this audit, via `Docs/INDEX.md`. A parallel agent
produced, **within the last few hours**, design and code for four items this audit had
scoped as future work:

| Artifact | Size | Covers | Status |
|---|---|---|---|
| `Docs/exploration/JOURNEY_DEPENDENCY_GRAPH_2026-08-29.md` | 402 lines | R-12 | untracked |
| `src/schemas/journey_graph.py` | 14,616 B | R-12 **code** | **untracked, created 18:09** |
| `Docs/exploration/LIVE_CONNECTIVITY_INTEGRATION_2026-08-29.md` | 773 lines | `CONNECTIVITY_TIER` (R-06's missing primitive) | untracked |
| `Docs/exploration/DURABLE_AGENT_LEASE_2026-08-29.md` | 669 lines | R-11 heartbeat/fencing/STALE | untracked |
| `Docs/architecture/SERVER_DECOMPOSITION_PLAN_2026-08-29.md` | 70 lines | R-10 | untracked |
| `Docs/design/FRONTEND_STYLING_UNIFICATION_PLAN_2026-08-29.md` | 53 lines | R-14 | untracked |

**Two corrections this forces:**

1. **`CONNECTIVITY_TIER` is designed, not merely absent.** The progression
   `MOCK → SANDBOX → LIVE` with an explicit mapping onto `RealityTier` is specified at
   `LIVE_CONNECTIVITY_INTEGRATION_2026-08-29.md:201-252`, including the key rule that the
   two enums are orthogonal (a supplier router can be `REAL` while its provider is `MOCK`).
   **The remaining work is implementation, not design.**
2. **`journey_graph.py` is wired, not orphaned.** `Docs/INDEX.md` describes it as
   *"orphaned (no IROPS trigger path wires it in)"*. That is imprecise — it has **four**
   live importers: `src/decision/counterfactual_recovery.py:15`,
   `src/decision/constraint_engine.py:20`, `spine_api/routers/counterfactual.py:28`,
   `spine_api/routers/constraints.py:32`. What is genuinely missing is the **IROPS
   trigger**, not all consumers.

**Verdict: not a defect — a coordination risk.** This audit's Wave 6 and exploration
items EX-01/EX-04 **would have duplicated work already done**. They have been rewritten to
defer to the existing designs (doctrine §5 — extend the canonical path, do not fork it).

> **Meta-observation (PER-0428).** This is the same failure the audit diagnoses in the
> codebase, occurring *within the audit process itself*: work started in parallel without
> a shared register, discovered only by reading an index. **It validates EX-06** — the
> findings-lifecycle primitive — as the highest-leverage process fix available, and it is
> the reason this audit's register carries explicit status fields.

---

## 6. Cross-cutting: shadow-system root causes (PER-0930)

Stripping domain nouns, the duplicate systems in §5.4 fall into three root causes:

1. **Migration started, never finished.** `TeamStore` and the legacy 1D scoring path
   both carry "use the new thing instead" markers. The new thing exists; the old thing
   was never deleted. **Root cause: no retirement step in the migration plan**
   (doctrine §5 requires "a migration and retirement plan" *before* creating the
   parallel path).
2. **Two auth passes by accident, not design.** `core/middleware.py` and
   `core/auth.py` independently decode the JWT and independently check
   `SPINE_API_DISABLE_AUTH`. This is not a shadow system someone chose — it is
   accretion. **Root cause: no single owner of the auth boundary** (doctrine §5:
   "Give each shared mutation boundary one owner").
3. **Config read at import time in 150 places.** No `BaseSettings`. `core/database.py:22`
   builds the engine at import; `core/security.py:21` raises at import.
   **Root cause: config was never treated as a first-class contract** (doctrine §11:
   "Treat … configuration as production code").

---

## 7. Net verdict

**As PER-1065 (Project Archaeologist):** this is a genuinely substantial system, not a
facade. The deterministic core, RLS, reality-tier honesty layer, and executable
architectural gates are real assets built on correct first principles. **Do not rewrite.**

But the repo has a **specific, repeating failure mode**: it *starts* canonical paths
and *doesn't finish* them. `TeamStore` → `membership_service`: started, not retired.
Legacy 1D scoring → 2D: started, not retired. `audit_bridge` → `audit_logger`: started,
not retired. `contract.py` → generated TS: started, not wired. `EpistemicStatus`:
landed, not committed. Four R-fixes: done, **sitting uncommitted in a dirty tree.**

**As PER-0926 (Product Evolution Architect):** the long-term risk is not any single
defect. It is that the project has no mechanism to *finish* a canonical path, so every
improvement adds a layer instead of replacing one. The fix is a **retirement gate**:
no new canonical path is merged without the old one's deletion date.

**As PER-0428 (Doctrine Alignment Reviewer):** doctrine §5 (one canonical source) is
the single most-violated rule in this repo, and it is violated on **both** sides of the
stack (backend duplication §5.4, frontend fetch layers §5.5, doc trees §5.7, marketing
generations §5.9). This is not many independent problems — it is **one systemic
problem with many instances**, which is good news: one control fixes most of them.

**As PER-0922 (Epistemic Integrity Architect):** the most serious finding is **A-01**
(§5.1). The repo has one honest measurement — budget extraction F1 = 0.2857, failing —
and it is excluded from CI on two independent paths and defended by tests that assert
it must not block. Meanwhile two placebo gates report 1.0. **The system's evidence
apparatus is inverted: it reports green where it is blind and stays silent where it
sees a failure.** Everything else is recoverable; this one actively misleads.

---

## 8. What this audit did NOT establish

| Gap | Next check |
|---|---|
| Frontend build/lint/Vitest pass rate | `cd frontend && npm run typecheck && npm run lint && npm test -- --run` |
| Whether `data/trips/*.json` is written in SQL mode | Runtime probe: set `TRIPSTORE_BACKEND=sql`, exercise a write, observe mtimes |
| CI-identical test count | Re-run with CI's env + `--ignore` flags |
| ADR 003/004/005 — lost or never written | `git log --diff-filter=D -- '*ADR-00[345]*'` |
| Whether `src/proxy.ts` ever ran | `git log --follow frontend/src/proxy.ts` + Next version history |
| Per-router Pydantic boundary validation | 50 routers, not individually audited |
| Actual cross-tenant exploitability of the 4 RLS-exempt tables | Read `routers/frontier.py` + `frontier.py` models for agency filters |
| `Docs/INDEX.md` orphan-doc coverage | Script: docs not linked from any index |
| Retail value of the 121-item `inbox` backlog | Item-level reconciliation against git |

---

## 9. Deliverables from this audit

| Document | Purpose |
|---|---|
| `Docs/review/PERSONA_COUNCIL_MASTER_AUDIT_2026-08-29.md` | This document |
| `Docs/review/FINDINGS_REGISTER_2026-08-29.md` | Full explicit + implicit findings register with alignment verdicts |
| `Docs/review/IMPLEMENTATION_PLAN_2026-08-29.md` | Sequenced, gated implementation plan |
| `Docs/review/EXPLORATION_RESEARCH_BACKLOG_2026-08-29.md` | Research / exploration backlog |
| `Docs/review/SESSION_RECORD_PERSONA_AUDIT_2026-08-29.md` | Session record with full evidence trail |
