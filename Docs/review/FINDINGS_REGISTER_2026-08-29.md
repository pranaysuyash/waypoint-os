# Findings Register — Waypoint OS Persona Council Audit

**Date:** 2026-08-29 · **Companion to:** `PERSONA_COUNCIL_MASTER_AUDIT_2026-08-29.md`
**Git HEAD:** `c31dc18` · **Working tree:** heavily modified, uncommitted

**Legend**
- **Type:** `E` = Explicit (already documented somewhere in repo) · `I` = Implicit (discovered this audit)
- **Truth:** Observed / Verified / Inferred / Unknown (doctrine §2)
- **Tier:** T1 static · T2 targeted check · T3 integration · T4 runtime · T5 production (doctrine §3)
- **FP** = first-principles sound · **LT** = long-term coherent · **DOC** = doctrine-aligned
  Verdicts: ✅ aligned · ⚠️ partial · ❌ non-aligned · ➖ not applicable / opportunity

---

## Part 1 — Carry-forward: re-verified findings from the 2026-08-29 Refactor Architect audit

Source: `Docs/review/WAYPOINT_OS_REFACTOR_ARCHITECT_AUDIT_2026-08-29.md` (R-01…R-16).
Status column is **this audit's live re-verification**, not the original claim.

| ID | Type | Area | Finding | Live status | FP | LT | DOC | Sev |
|---|---|---|---|---|---|---|---|---|
| R-01 | E | Canonical | 4 stale `v6.1` doctrine copies w/ wrong canonical path | ✅ **FIXED** — all 4 now identical 1,357 B "Mirror Pointer" stubs (md5 `6c9d18a1…`) declaring canonical path, v8.0, SHA-256, gen date, "NOT authoritative" | ✅ | ✅ | ✅ | — |
| R-02 | E | Security | Client `X-Agency-ID` trusted on 5 routers | ✅ **FIXED** (uncommitted) — `core/auth.py:170-185` honors header only under `PYTEST_CURRENT_TEST`/`SPINE_API_DISABLE_AUTH` | ✅ | ✅ | ✅ | — |
| R-03 | E | Security *(mis-scoped)* | File-store split-brain (1,635 JSON ∥ SQL) | ✅ **FIXED 2026-08-30** — original P0 premise **wrong**; reframed as test-hygiene (P3) + `list_trips` RLS/offset correctness (P2). See **§5**. | ✅ | ✅ | ⚠️ | — |
| R-04 | E | Integrity | `commission.py` fabricated ₹3000 | ✅ **FIXED** (uncommitted) — `commission.py:88` `if gross_cents <= 0: continue` | ✅ | ✅ | ✅ | — |
| R-05 | E | Integrity | `/send` returned `SENT` with no dispatch | ✅ **FIXED** (uncommitted) — returns `QUEUED` + honest docstring (`messaging.py:76-88`) | ✅ | ✅ | ✅ | — |
| R-06 | E | Epistemic | `EpistemicStatus`/`AssumptionRegister`/`CONNECTIVITY_TIER` absent | ⚠️ **PARTIAL** (uncommitted) — `EpistemicStatus` ✅ `packet_models.py:91`; `AssumptionRecord` ✅ `:101`; mapping ✅ `extractors.py:1738-1749`; **`CONNECTIVITY_TIER` still absent** (grep → 0) | ✅ | ✅ | ⚠️ | P1 |
| R-07 | E | Eval | Extraction + pipeline gates self-consistent | ❌ **OPEN — worse than claimed**; real budget gate (F1 0.2857) excluded from CI on 2 paths (see A-01) | ❌ | ❌ | ❌ | P0 |
| R-08 | E | Quality | ~186 tests fail; no mypy | ⚠️ **SPLIT** — mypy ✅ **FIXED** (configured, CI-blocking, passes clean). Tests ❌ **WORSE**: 358 failed + 19 errors | ⚠️ | ❌ | ⚠️ | P0 |
| R-09 | E | Docs | `Docs/` ∥ `frontend/docs/` | ❌ **OPEN** (1,975 ∥ 921 files) | ❌ | ❌ | ❌ | P1 |
| R-10 | E | Architecture | `server.py` monolith; 2 audit systems | ⚠️ **PARTIAL** — 3,719→3,186 lines; 50 routers. Two audit systems **remain** (hash-chain file vs `audit_logs` w/o chain) | ⚠️ | ⚠️ | ❌ | P2 |
| R-11 | E | Agentic | No durable lease/heartbeat; zombies | ⚠️ **PRIOR AUDIT PARTLY WRONG** — lease ✅ exists & durable (`models/agent_work.py:14-41`, `SELECT…FOR UPDATE`); **heartbeat is dead code** (`ExecutionLease` `runtime.py:52-82`, zero call sites) → >60s tasks re-acquirable | ⚠️ | ⚠️ | ⚠️ | P2 |
| R-12 | E | Domain | No Journey Dependency Graph for IROPS ripple | ❌ **OPEN** — genuine opportunity | ✅ | ✅ | ➖ | P2 |
| R-13 | E | Navigation | Nav rollout-gate drift | ❌ **OPEN** — `nav-modules.ts:60,64,68,73` all `complete: false`; "14/14 active" claim false | ❌ | ⚠️ | ❌ | P2 |
| R-14 | E | UX | Two-generation styling (literal-hex ∥ primitives) | ❌ **OPEN** | ⚠️ | ❌ | ⚠️ | P3 |
| R-15 | E | Security | PII guard fail-open in production — contradictory defaults | ✅ **FIXED 2026-08-31** — investigated: the Layer 2 "fail-closed" `RuntimeError` was **unreachable dead code** (the gate bailed at `:484` before Layer 2 loaded), so real behavior was fail-open at every level. Reconciled at the gate: **dogfood + production+plaintext → fail-closed; production+SQL / beta → fail-open-but-audited** (Layer 1 scan, no block). See `R-15_PII_GUARD_DEFAULT_2026-08-31.md`. | ✅ | ✅ | ✅ | P1 |
| R-16 | E | Observability | No trace-correlation reader; no CI event-flow assertion | ❌ **OPEN** — OTel spans real, no consumer | ⚠️ | ⚠️ | ⚠️ | P2 |

**Carry-forward score: 5 fixed · 4 partial · 8 open · 2 prior-audit errors corrected.**

---

## Part 2 — New findings (this audit)

### A-01 · The only honest quality gate is structurally excluded from CI
- **Type:** I · **Truth:** Verified · **Tier:** T2 · **Severity:** **P0**
- **Evidence:** `scripts/verify_d6_gate_snapshot.py:29-67` (`_check_blocks_ci()` never reads
  `budget_health.blocks_ci`) · `src/evals/audit/manifest.yaml:3-7` (budget has no
  `min_accuracy`) · `src/evals/audit/gates.py:28,39` (`min_accuracy` defaults `0.0`;
  guard `if min_accuracy > 0.0` never fires) · `src/evals/audit/snapshot.py:98-100,143-145,206-214,353-355`
  · `data/evals/d6_audit_gate_snapshot.json` (budget `overall_f1: 0.2857`, `recall 0.1667`,
  `status "failing"`, `blocks_ci: true`) · `tests/evals/test_d6_gate_snapshot.py:27,56,142`
  (**asserts** `blocks_ci is False`)
- **Detail:** Two gates are tautologies (expected-vs-itself, F1 = 1.0, cannot fail). The one
  real gate measures live pipeline output and is **failing** — and is neutralised twice:
  (a) the CI script doesn't read it, (b) the manifest omits its threshold. Tests then assert
  the muted state is correct.
- **FP ❌ · LT ❌ · DOC ❌** (doctrine §3 "Passing counts are not proof")
- **Fix:** add `budget_health` to `_check_blocks_ci()`; add `min_accuracy` to `manifest.yaml`
  budget entry; rewrite the three `blocks_ci is False` assertions to expect the real value;
  regenerate the snapshot (it is stale — generated 2026-06-23 by older code).

### A-02 · RAG embeddings are md5 hash vectors, not semantic
- **Type:** I · **Truth:** Observed · **Tier:** T1 · **Sev:** P1
- **Evidence:** `src/rag/indexer.py:20-35` (`generate_local_embedding()`, 64-dim hashed
  bag-of-words), called unconditionally at `:81`, `:107`; docstring `:4` claims an "API
  path" that does not exist. Groundedness = word-overlap heuristic (`:45-53`).
- **Credit:** real store schema (`store.py:46-95`), **BM25 + dense + RRF fusion**
  (`retriever.py:36-102`), real citation provenance (`grounding.py:73-86`), fail-closed
  `must_confirm` (`:25-34`). Only BM25 does real work today.
- **FP ❌ · LT ⚠️ · DOC ⚠️** (claim-reality risk, doctrine §13)
- **Fix:** replace `generate_local_embedding` with a real embedding call behind the existing
  `BaseLLMClient`-style interface; keep the deterministic path as an explicit offline tier.

### A-03 · Agent tools default to Mock; shipped config is 100% mock
- **Type:** I · **Truth:** Observed · **Tier:** T1 · **Sev:** P1
- **Evidence:** `src/agents/live_tools.py` — Mock at `:41,72,97,123`; real at
  `:151,236,275,314,348`; switch `:405-408` (`TRAVEL_AGENT_ENABLE_LIVE_TOOLS`, **absent from
  `.env`**); `:412-419,423-430,434-443` URL-template-gated, all default to Mock;
  `StateDept` needs a *second* opt-in (`:441`) and is **not** behind `ENABLE_LIVE_TOOLS`.
- **Credit:** mocks self-declare `"mode": "mock"`. Honesty plumbing exists.
- **FP ✅ · LT ⚠️ · DOC ⚠️**
- **Fix:** implement `CONNECTIVITY_TIER` (R-06's third primitive) so the *system* asserts
  mock/live globally; unify all four switches behind one env var; fail loud when mock is
  active outside dev.

### A-04 · Backend duplicate / shadow systems (9 pairs)
- **Type:** I · **Truth:** Observed · **Tier:** T1 · **Sev:** P1
- **Evidence:** DB session (`core/database.py:28-44` ∥ `persistence.py:82-90`) · auth
  (`core/auth.py:34-167` ∥ `core/middleware.py:46-109` — **two full JWT decode passes per
  request**) · audit (`core/audit.py:145` ∥ `core/audit_bridge.py:39` **dead, zero prod
  callers**) · audit store (file hash-chain `persistence.py:2056-2086` ∥ `models/audit.py`
  PostgreSQL, **no chain**) · membership (`services/membership_service.py` ∥
  `persistence.py:2511` `TeamStore`, marked DEPRECATED, not retired) · Pydantic schemas
  (`routers/trip_documents.py` + `routers/public_collection.py` ∥ `server.py:2394…2836`)
  · scoring (`scoring/__init__.py` 2D ∥ `services/inbox_projection.py:461-475` legacy 1D)
  · vision clients (`src/llm/*` ∥ `src/extraction/*_vision*.py`, 3rd path) · config
  (**150 scattered `os.getenv`**, no `BaseSettings` anywhere)
- **FP ❌ · LT ❌ · DOC ❌** (doctrine §5 — one canonical source; §11 — config is production code)
- **Fix:** consolidation plan with **deletion dates**, not just migration notes. See §6 of
  the master audit for the three root causes.

### A-05 · Frontend: three competing data-fetch layers
- **Type:** I · **Truth:** Observed · **Tier:** T1 · **Sev:** P1
- **Evidence:** canonical `lib/api-client.ts` (1,976 lines) ∥ **104 raw `fetch(` sites**;
  **16 files use BOTH**; `hooks/useUnifiedState.ts:28` documents the bypass in a comment;
  30 BFF `route.ts`; `stores/auth.ts:57,75,97` fetch direct.
- **FP ❌ · LT ❌ · DOC ❌** (doctrine §5)
- **Fix:** one client; migrate the 30 ad-hoc files; add an ESLint rule banning bare `fetch(`.

### A-06 · Generated type contract is orphaned and stale
- **Type:** I · **Truth:** Observed · **Tier:** T1 · **Sev:** P1
- **Evidence:** `scripts/generate_types.py` → `src/types/generated/spine-api.ts` (918 lines);
  its docstring claims *"the only canonical generated type file"*; **only 5 of 449 files
  import it**; last generated at `5a544ba` (Aug 1) vs `contract.py` changed at `18465bb`
  (Aug 7) **plus ~299 uncommitted lines today**; **not in CI**, **not an npm script**;
  `contract.py` never mentions it.
- **FP ❌ · LT ❌ · DOC ❌** (doctrine §5, §12 — false confidence)
- **Fix:** wire generation into CI as a **drift gate** (regenerate → diff → fail on delta).

### A-07 · Documentation decay
- **Type:** E+I · **Truth:** Observed · **Tier:** T1 · **Sev:** P1
- **Evidence:** `Docs/` 1,975 `.md` ∥ `frontend/docs/` 921 files · category encoded in
  **filename not directory** (ADRs flat at `Docs/` root; `Docs/decisions/` has 6 files,
  **none are ADRs**) · 3 parallel archives (`Archive/`, `Docs/archives/`, `.agent/archives/`)
  · **`Docs/index.md` == `Docs/INDEX.md` same inode** — breaks on Linux CI · CHANGELOG
  stale since 2026-04-29 **and scoped to frontend only**, so 6 August feature commits are
  absent by design · 6 docs reference deleted `next.config.ts` · 3 reference deleted
  `motto_v5.md` · empty dirs `Docs/responsive-audit/`, `Docs/artifacts/`
- **FP ❌ · LT ❌ · DOC ❌** (doctrine §9, §14)

### A-08 · Governing-rule references have filename drift *(CORRECTED — content is NOT lost)*
- **Type:** I · **Truth:** Observed · **Tier:** T1 · **Sev:** **P2** *(downgraded from P1)*
- **Evidence:** `motto_v4.md` **does not exist** anywhere in the tree, yet **18 files
  reference it** and all four numbered ADRs declare *"Governing Rule: `motto_v4.md`
  (Rule 0.9 / 0.10 / 0.15…)"*. Only `motto.md` (5,895 B, 2026-05-17) survives; v2/v3/v5
  exist only as hash-suffixed corpses in `.agent/archives/doctrine-legacy/`.
- **Correction (found late via `Docs/INDEX.md`):** the content is **recoverable** —
  `Docs/FIRST_PRINCIPLES_MOTTO_V4_DOCTRINE.md` (107 lines) is the canonical declaration of
  first-principles under motto_v4. The defect is **filename drift**, not knowledge loss.
- **FP ❌ · LT ❌ · DOC ⚠️** (doctrine §1 — the reasoning survived; the references did not)
- **Fix:** repoint the 18 references at `Docs/FIRST_PRINCIPLES_MOTTO_V4_DOCTRINE.md`;
  add a CI link/dangling-reference check.

> **Self-correction note (PER-0164).** The original finding asserted content was
> unrecoverable — an absence claim made from a filename grep without checking whether the
> content existed under another name. This is the **exact failure mode** this register
> flags in the prior audit (R-08, R-11). Recorded rather than silently amended.

### A-09 · ADR corpus has no supersession mechanism; numbering broken
- **Type:** I · **Truth:** Observed · **Tier:** T1 · **Sev:** P1
- **Evidence:** 22 ADRs; grep `superseded|deprecated|obsolete|amended by|replaced by`
  → **0 matches**; all terminal `Accepted`. `Docs/architecture/adr/` jumps **002 → 006**
  (003/004/005 **Unknown** — lost or never written). Only 4 of 22 carry numbers; the
  14-strong 2026-07-29 batch is title-only. Two incompatible numbering schemes.
- **FP ❌ · LT ❌ · DOC ❌** (doctrine §14 — "Append decision updates instead of rewriting history")
- **Fix:** add `Supersedes:` / `Superseded-By:` front-matter to the ADR template; renumber.

### A-10 · Idea-pad no longer reflects shipped reality
- **Type:** I · **Truth:** Observed · **Tier:** T1 · **Sev:** P2
- **Evidence:** 134 cards — `inbox` 121 · `committed` 6 · `qualified` 4 · `active` 1 ·
  **`done` 1**. Git shows IDEA-120/122/123/124 **shipped** 2026-08-08/09 but the pad still
  marks them `inbox`. Pad last touched 2026-08-12. §0 WIP registry `last_check_in:
  2026-02-20` (~6 months dead). `IDEA_DUMP.md` has **zero `IDEA-NNN` IDs** → no join key.
- **FP ❌ · LT ❌ · DOC ❌** (doctrine §9)

### A-11 · Four concurrent marketing generations live simultaneously
- **Type:** I · **Truth:** Observed · **Tier:** T1 · **Sev:** P2
- **Evidence:** root-level `app/v2`…`app/v5` `page.tsx` all present and routed, outside
  every route group (thus outside every group layout); plus `/pricing`,
  `/corporate/offsites`, `/intake/fast`.
- **FP ❌ · LT ❌ · DOC ❌** (doctrine §5 shadow routes; PER-0926 "additive-only growth")

### A-12 · `src/proxy.ts` is inert; edge auth gate may not run
- **Type:** I · **Truth:** Observed (inert) / Inferred (consequence) · **Tier:** T1 · **Sev:** P1
- **Evidence:** `src/proxy.ts` (4,452 B) claims Next.js proxy convention; **no
  `middleware.ts` exists anywhere**; **0 imports** of `proxy.ts`. Under Next 14 it is dead.
  Version skew: `eslint-config-next@^16.2.4`, `@next/bundle-analyzer@^16.2.4`,
  `@types/react@^19` against Next 14.2.20 / React 18.3.1.
- **FP ⚠️ · LT ❌ · DOC ⚠️**
- **Fix:** restore a real `middleware.ts` **or** delete `proxy.ts`; resolve the version skew.

### A-13 · Test debt: 358 failures concentrated in 4 clusters
- **Type:** I · **Truth:** Verified · **Tier:** T3 (S1) · **Sev:** P0
- **Evidence:** executed `.venv/bin/python -m pytest -q` → **358 failed, 2,803 passed,
  19 errors, 8 skipped in 528.77 s**. Top clusters:

  | Failures | File | Cluster |
  |---|---|---|
  | 49 | `test_trip_canonical_roundtrip.py` | canonical trip field round-trip |
  | 39 | `test_booking_collection.py` | booking collection |
  | 29 | `test_booking_documents.py` | documents |
  | 27 | `test_document_extractions.py` | extractions |
  | 26 (E) | `test_call_capture_phase2.py` | call capture |
  | 21 | `test_booking_data.py` | booking data |
  | 17 (E) | `test_run_state_unit.py` | run state |
  | 17 (E) | `test_override_api.py` | overrides |
  | 14 | `test_extraction_attempts.py` | extractions |
  | 13 | `test_product_b_events.py` | events |
  | 12 (E) | `test_state_contract_parity.py` | contract parity |
  | 11 (E) | `test_run_lifecycle.py` | lifecycle |
  | 11 (E) | `tests/evals/test_d6_gate_snapshot.py` | **eval gates** |
  | 11 | `test_settings_router_contract.py` | settings |
  | 10 | `test_payments_queue_api.py` | payments |
  | 10 | `test_legacy_ops_router_behavior.py` | legacy ops |

  The **booking/documents/extraction super-cluster** (39+29+27+14+21 = **130**) plus
  `test_trip_canonical_roundtrip` (49) = **179 ≈ half of all failures**.
  **Caveat (Observed):** local `.env` lacks `DATABASE_URL` and CI passes two `--ignore`
  flags I did not; local count is an **upper bound, not CI-identical**.
- **FP ⚠️ · LT ❌ · DOC ❌** (doctrine §3; "Defect fixes require S2")
- **Fix:** triage the two super-clusters first — highest failures per unit of effort.

### A-14 · Uncommitted P0 remediation is exposed to loss
- **Type:** I · **Truth:** Observed · **Tier:** T1 · **Sev:** **P0 (process)**
- **Evidence:** R-02/R-04/R-05 fixes and the R-06 epistemic primitives exist **only in the
  working tree**. `git status` shows 40+ modified tracked files, `frontend/next.config.ts`
  **deleted** (replacement `next.config.mjs` **untracked**), `motto_v5.md` **deleted**,
  4 doctrine stubs **modified**. Nothing is committed.
- **Risk:** a `git checkout`/`reset`/`stash` — or another agent's cleanup pass — destroys
  the tenant-authority fix. Doctrine §10 requires preserving dirty work until classified.
- **FP ✅ · LT ✅ · DOC ❌**
- **Fix:** classify and commit the remediation as its own unit **before** any new work.
  *(This is a git mutation — requires explicit authorization from Pranay per standing rule.)*

### A-15 · Frontend debt is undocumented, not absent
- **Type:** I · **Truth:** Observed · **Tier:** T1 · **Sev:** P2
- **Evidence:** **0** `TODO`/`FIXME`/`HACK`/`XXX`/`@ts-ignore` in `frontend/src`; **1**
  `@ts-expect-error` (`app/api/stream-events/[runId]/route.ts:76`); **5** `eslint-disable`
  (**4 in files modified in the current changeset** — `workbench/PageClient.tsx:307,324`,
  `ui/drawer.tsx:46`, `ui/modal.tsx:50`). Meanwhile **34 non-test files >400 lines**
  (worst `itinerary-checker/PageClient.tsx` **2,932**) and **65 `any` in prod code**
  (hotspot `workbench/DecisionTab.tsx`, 9 × `as any`).
- **FP ⚠️ · LT ❌ · DOC ⚠️**
- **Note (PER-0922):** a clean grep is being read as a clean codebase — this is the named
  failure mode *"missing evidence treated as negative evidence."*

### A-16 · Frontend coverage thresholds are unenforced
- **Type:** I · **Truth:** Observed · **Tier:** T1 · **Sev:** P2
- **Evidence:** `vitest.config.ts` configures v8 coverage but sets **no `lines`/`branches`
  thresholds** → `test:coverage` **can never fail**. 161 test files, **no e2e** at all
  (`frontend/tests/` is empty; no playwright/cypress). `testTimeout: 60000`,
  `pool: 'forks'` with the comment *"reduces Vitest RPC stalls."*
- **FP ❌ · LT ❌ · DOC ❌** (doctrine §3)
- **Fix:** set ratcheting thresholds; add at least one smoke e2e for the booking path.

### A-17 · WelcomeModal is not a modal (a11y)
- **Type:** I · **Truth:** Observed · **Tier:** T1 · **Sev:** P3
- **Evidence:** canonical `components/ui/modal.tsx` (181 lines, focus trap, `aria-modal`)
  is correctly wrapped by `confirm-dialog.tsx:38` and `OverrideModal.tsx:160`.
  `components/onboarding/WelcomeModal.tsx` (260 lines) **does not** — it is a hand-rolled
  `fixed inset-x-2 bottom-2` toast-sheet (`:65`) with **no `role="dialog"`/`aria-modal`**,
  misleadingly named.
- **FP ❌ · LT ⚠️ · DOC ➖**

### A-18 · Secrets posture
- **Type:** I · **Truth:** Observed (no values reproduced) · **Tier:** T1 · **Sev:** P1
- **Evidence:** `.env` holds a live `OPENAI_API_KEY` (gitignored, `.gitignore:17`) →
  **rotate**. `core/database.py:22` defaults `DATABASE_URL` to a **committed dev password**
  (same value in `ci.yml:105,128,142`). `SPINE_API_DISABLE_AUTH` returns a synthetic owner
  (`auth.py:62,72,96-97,152-156`) and disables `AuthMiddleware` entirely
  (`middleware.py:46`); guarded by `core/startup_assertions.py:118` which **warns but does
  not crash** outside production/staging (`:162-167`).
- **Credit:** `core/logging_filter.py`, `core/llm_egress.py:180 strip_pii`,
  `services/private_fields.py` all exist and are real.
- **FP ⚠️ · LT ⚠️ · DOC ⚠️**

### A-19 · Coverage gap in RLS enforcement
- **Type:** I · **Truth:** Observed · **Tier:** T1 · **Sev:** P1
- **Evidence:** only **6 of 50 router modules** use `get_rls_db`
  (`trip_documents`, `confirmations`, `assignments`, `extraction`, `workspace`,
  `booking_tasks`). `analytics.py:21`, `audit.py:23`, `auth.py:30`, `team.py:21`,
  `frontier.py:18`, `integrations.py:23` use plain `Depends(get_db)`.
  `RLS_EXCLUDED_AGENCY_TABLES` (`rls.py:65-70`) leaves `audit_logs`,
  `emotional_state_logs`, `ghost_workflows`, `legacy_aspirations` **unprotected**.
  **Unknown:** whether the 4 exempt tables are reachable cross-tenant.
- **FP ❌ · LT ❌ · DOC ❌** (doctrine §11; security doctrine)
- **Fix:** convert `Depends(get_db)` → `get_rls_db` across routers, or document a reasoned
  deviation per router; audit the 4 exempt tables for agency filters.

### A-20 · Migrations drift: 4 model tables have zero migration files
- **Type:** I · **Truth:** Observed (tables) / Unknown (drift magnitude) · **Tier:** T1 · **Sev:** P2
- **Evidence:** `models/frontier.py` tables `ghost_workflows`, `emotional_state_logs`,
  `intelligence_pool`, `legacy_aspirations` appear in **no** migration file. 28 revisions,
  single linear chain, head `add_audit_chain_hash`. `Base.metadata.clear()` at
  `core/database.py:53` is a reload-time hack.
- **Fix:** run `alembic check` / autogenerate diff to quantify; add a CI drift gate.

### A-21 · Parallel remediation is in flight; this audit nearly duplicated it
- **Type:** I · **Truth:** Observed · **Tier:** T1 · **Sev:** **P2 (coordination risk)**
- **Discovered:** late, via `Docs/INDEX.md` — **after** Wave 6 and EX-01/EX-04 were drafted.
- **Evidence:** six artifacts produced by a parallel agent within hours, all **untracked**:

  | Artifact | Covers | Lines |
  |---|---|---|
  | `Docs/exploration/JOURNEY_DEPENDENCY_GRAPH_2026-08-29.md` | R-12 design | 402 |
  | `src/schemas/journey_graph.py` | R-12 **code** (created 18:09) | 14,616 B |
  | `Docs/exploration/LIVE_CONNECTIVITY_INTEGRATION_2026-08-29.md` | `CONNECTIVITY_TIER` (R-06 third primitive) | 773 |
  | `Docs/exploration/DURABLE_AGENT_LEASE_2026-08-29.md` | R-11 heartbeat/fencing/STALE | 669 |
  | `Docs/architecture/SERVER_DECOMPOSITION_PLAN_2026-08-29.md` | R-10 | 70 |
  | `Docs/design/FRONTEND_STYLING_UNIFICATION_PLAN_2026-08-29.md` | R-14 | 53 |

- **Two forced corrections:**
  1. **`CONNECTIVITY_TIER` is designed, not absent.** `MOCK → SANDBOX → LIVE` with an
     explicit orthogonal mapping onto `RealityTier` is specified at
     `LIVE_CONNECTIVITY_INTEGRATION_2026-08-29.md:201-252`. Remaining work is
     **implementation only**.
  2. **`journey_graph.py` is wired, not orphaned.** `Docs/INDEX.md` calls it orphaned; it
     has **4** live importers — `src/decision/counterfactual_recovery.py:15`,
     `src/decision/constraint_engine.py:20`, `spine_api/routers/counterfactual.py:28`,
     `spine_api/routers/constraints.py:32`. Missing is the **IROPS trigger**, not all consumers.
- **FP ➖ · LT ⚠️ · DOC ⚠️** (doctrine §5 — this audit must not fork a canonical path)
- **Fix:** Wave 6 and EX-01/EX-04 rewritten to **defer to** these designs rather than
  re-specify them. Add all six to the shared register (see EX-06).

---

## Part 3 — Alignment summary

| Dimension | ✅ | ⚠️ | ❌ | Systemic read |
|---|---|---|---|---|
| **First-principles (PER-91002)** | 6 | 7 | 12 | The **core** is sound: deterministic intake, RLS, reality tiers, executable gates. Failures cluster in duplicated/placeholder *peripheries*, not primitives. |
| **Long-term (PER-0926)** | 3 | 7 | 15 | Weakest dimension. No mechanism to **finish** a canonical path — every improvement adds a layer instead of replacing one. |
| **Doctrine-aligned (PER-0428)** | 5 | 7 | 15 | **§5 (one canonical source)** is the most-violated rule, breached on both sides of the stack. Not many problems — **one problem with many instances.** |

### The one-sentence version
> The project is architecturally right and executionally unfinished: it keeps building the
> correct canonical path and then stopping one step short of retiring the old one — and its
> one honest quality signal (budget F1 = 0.2857) is wired to stay silent.

---

## Part 4 — Assumptions this register depends on (PER-0164)

| # | Assumption | Criticality | Falsification check |
|---|---|---|---|
| 1 | Local test failures (~358) approximate CI failures | **High** | Re-run with CI env + `--ignore` flags |
| 2 | `data/trips/*.json` is no longer written in SQL mode | Medium | Runtime probe: write a trip under `TRIPSTORE_BACKEND=sql`, observe mtimes |
| 3 | `audit_bridge.py` has no dynamic/importlib caller | Medium | Grep for `importlib`, `__import__` across `spine_api/` |
| 4 | The 4 RLS-exempt tables are not cross-tenant reachable | **High** | Read `routers/frontier.py` for agency filters |
| 5 | R-02/R-04/R-05 fixes are complete, not partial | Medium | Security review of all 5 routers' dependency chains |
| 6 | `motto_v4.md` is unrecoverable | Low | `git log --diff-filter=D --all -- '*motto_v4*'` |
| 7 | Frontend tests pass at all (never executed) | **High** | `cd frontend && npm test -- --run` |

**Assumption 7 is the largest evidence hole in this audit.**

---

## Part 5 — R-03 reframe and remediation (2026-08-30)

R-03 was re-investigated against live code and `.env` after the audit was filed.
The **original finding was wrong**; the reframe is recorded here rather than
silently amended (doctrine §1 — the reasoning survives; the claim did not).

### 5.1 Why the P0 premise was wrong

- `TRIPSTORE_BACKEND=sql` **is set** in `.env`. `TripStore._backend()`
  (`spine_api/persistence.py:1408-1447`) is **fail-closed**: in production/staging an
  unset or non-SQL backend raises `RuntimeError`.
- Every production read/write dispatches through the facade; **all** direct
  `FileTripStore.save_trip` call sites are inside `tests/`.
- `get_trip_by_group_token` was initially suspected of bypassing the backend — it does
  **not** (`:1540-1541` honors `_backend()`). Recorded as a self-correction.
- `data/trips/*.json` is **gitignored** (`.gitignore:115`); 1,602 of 1,646 files were
  **test-generated**. The "1,635 JSON ∥ SQL" were test effluent, not a production
  split-brain.

**Verdict: not a P0 security defect.** Downgraded to test-hygiene (P3) + one
correctness defect (P2).

### 5.2 The two real defects, both fixed

| # | Defect | Fix |
|---|---|---|
| 1 | `get_trip_by_proposal_token` fetched a **single page of 1000** trips, so any token belonging to a trip past the first 1000 **silently failed to resolve**. Same cap in `get_trip_by_group_token`. | New `TripStore._iter_all_trips()` paging helper (`:1520+`); both token lookups now page the full corpus. |
| 2 | `FileTripStore.list_trips` **ignored `offset`**, and `SQLTripStore.list_trips` set RLS from the **auth ContextVar even when an explicit `agency_id` was passed** — so it returned an empty list in any context without auth (background tasks, sync facade, tests). | `FileTripStore.list_trips` now slices `offset`; facade passes offset to both branches; `SQLTripStore.list_trips` uses `_rls_session_for_agency(agency_id)` when an agency is supplied, matching its sibling methods. |

Also fixed the cause of the 1,600-file litter: the conftest autouse fixture reset
`TRIPS_DIR` to the **real** `data/trips`; it now points at an isolated session temp dir.

### 5.3 New findings surfaced by the fix

| ID | Finding | Sev |
|---|---|---|
| A-22 | **Cross-tenant token lookups need a deliberate read path.** Proposal/group tokens are resolved with **no** `agency_id`, so they rely on the ContextVar session. Via the sync facade the ContextVar is on a different task, so the lookup returns `None`. Public proposal links have no agency context by definition — the pagination fix is necessary but **not sufficient**. | **P1** |
| A-23 | **Token fields are not Trip columns.** `proposal_link_token`, `proposal_token_hash`, `group_booking` are absent from `models/trips.py`; they ride in `analytics._extra` (restored by `_to_dict`). Works, but `_to_summary_dict` does **not** restore `_extra`, so summary projections silently lack tokens. | P2 |

### 5.4 Evidence

- New `tests/test_trip_store_sql_coverage.py` — **4 passed** against live Postgres:
  pagination regression (DB-free, always runs), SQL round-trip + tenant isolation,
  `offset` paging, proposal-token `_extra` round-trip.
- Regression check: `test_booking_data.py` + `test_state_contract_parity.py` +
  `test_public_checker_path_safety.py` → **102 passed**.
- Pollution check: `data/trips` count **unchanged** (1,934) across a trip-writing run.

**Full re-baseline (fresh `--basetemp`, 47 GiB free, 290.61 s):**
**355 failed · 2,893 passed · 9 skipped · 13 errors** vs the recorded baseline of
358 failed · 2,803 passed · 19 errors · 8 skipped.

> **Self-correction (PER-0164).** An earlier draft of this section claimed the
> `TRIPS_DIR` isolation had fixed "a share of the 358-failure baseline", inferred from
> `test_trip_canonical_roundtrip.py` passing **53/53 standalone** where the register
> recorded 49 failures. The full run does **not** support that: failures moved only
> 358 → 355. That file passes in isolation and fails in the full run, i.e. it is
> **order-dependent**, but the isolated `TRIPS_DIR` was not the cause. The claim was
> an inference from a single file, recorded before the suite-wide evidence existed.

**Order-dependence is the real story.** `test_trip_canonical_roundtrip.py` passes alone
and fails within the full suite. Only `TRIPS_DIR` was isolated; `AUDIT_DIR`,
`ASSIGNMENTS_DIR`, `OVERRIDES_DIR` and friends still reset to the shared real `data/`
tree in the autouse fixture (`tests/conftest.py`), so cross-test leakage persists by
another route. Isolating the remaining directories is the natural next step and the
honest way to test whether order-dependence explains the 355.

### 5.5 Open

- Re-run the full backend suite to quantify the new failure baseline. The 358 figure
  was recorded while the volume was at 100% (ENOSPC) **and** with cross-test
  `TRIPS_DIR` leakage present, so it is likely inflated.
- A-22 needs a product decision: a public/system read path for token resolution.

### 5.6 Environment confound — pytest `tmp_path` fails under the sandbox shim

An initial re-baseline reported **167 errors** that looked like a regression. They are
**not**. The environment's `sitecustomize.py` broker raises on `mkdir(exist_ok=True)`
when the target already exists:

```
PermissionError: EEXIST: file already exists,
    mkdir '/private/var/folders/.../T/pytest-of-pranay'
```

Every test using the `tmp_path` fixture errors **at setup**, before any application code
runs. Running with a fresh temp root (`--basetemp=<new dir>`) clears it completely —
the same three files went from *66 passed / 33 errors* to **99 passed / 0 errors**.

**Any failure count produced without a fresh `--basetemp` is unreliable.** Use
`--basetemp=/tmp/wp-<timestamp>` when re-baselining. This is a second, independent
confound on the 358 baseline alongside ENOSPC and the `.env` divergence.

---

## Part 6 — R-15 PII guard default reconciliation (2026-08-31)

The R-15 framing ("fail-open in prod; Layer 2 fail-closed") was **partly wrong**.
Investigation (`src/security/privacy_guard.py`, full read) showed the Layer 2
fail-closed `RuntimeError` in `_get_nlp_model()` is **unreachable dead code** — the
gate returned at the old `:484` before Layer 2 loaded, so production was fail-open at
*every* level. The real defect: a contradiction between two defaults (one dead) plus a
**silent no-op** that abandons PII protection on misconfiguration.

**Fix (three parts, all in `privacy_guard.py`):**
1. Layer 2 (`_get_nlp_model`) now **consistently fail-open** — removed the dead prod
   `RuntimeError`; degrades to Layer 1 when the model is absent.
2. `check_trip_data` is **observable, not silent** — safe config (prod+SQL / beta) runs
   a non-blocking Layer 1 `AUDIT` scan and logs findings (closes plan item 2.5).
3. **Misconfiguration failsafe** — `production` + plaintext store (`file`/`json`) now
   **fails closed** (blocks real PII), mirroring `TripStore._backend()`'s unsafe branch;
   an unset backend is left to that module's own enforcement.

**Posture matrix:** dogfood → fail-closed · prod+plaintext → fail-closed · prod+SQL/beta
→ fail-open-but-audited. First-principles: the guard is the safety net for the *plaintext
store*, not the production encryption boundary; it substitutes (fail-closed) only when that
boundary is absent.

**Tests:** new `tests/test_privacy_guard.py::TestR15ProductionDefaults` (7 tests) covering
each posture; full file **55 passed**. `test_real_data_save_blocked` assertion updated from
the old `"dogfood mode"` string to `"plaintext"`.

**Evidence:** verified by read + test. **Self-correction:** initially repeated the
"Layer 2 fail-closed" premise; call-graph read disproved it before implementing.

**Full record:** `Docs/review/R-15_PII_GUARD_DEFAULT_2026-08-31.md`.
