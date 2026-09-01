# Docs Corpus Shadow Audit — Documentation vs Code Reality (2026-08-31)

**Persona:** `PER-0930 — Shadow-System Investigator`
**Scope:** audit of the documentation corpus (`Docs/`) against code reality. READ-ONLY; this document is the only output.
**Method:** corpus inventory by headings/sizes; deep-read of the 2026-08-29/30/31 active wave + `RAG_PIPELINE_ARCHITECTURE_EXPLORATION_2026-07-25.md` + `PRODUCT_VISION_AND_MODEL.md` + `V02_GOVERNING_PRINCIPLES.md`; targeted code verification of every significant claim (file:line cited); `rg`-based subsystem coverage sweep.
**Git state at audit:** HEAD `8ece02e` (master), working tree **86 dirty files** (uncommitted remediation, grew from the 78 recorded by the 08-31 register — drift continues).
**Companion relationship:** complements `Docs/review/PERSONA_COUNCIL_AUDIT_2026-08-31.md` (which audits *code*) — this document audits the *record about the code*. Neither supersedes the other.

---

## 1. Corpus Inventory

**Totals:** `Docs/` = **2,025 `.md`** files · `frontend/docs/` = **932 `.md`** (R-09's parallel-trees finding re-verified: the split grew from 2,020). `Docs/exploration/` = 37 files · `Docs/review/` = 47 items · root `Docs/ADR_*.md` = 19 files · `Docs/architecture/adr/` = 3 numbered files (001, 002, 006 — **003–005 missing**, gap unexplained in-repo).

### 1.1 `Docs/exploration/` (selected; dates from mtime + headers)

| File | Date | Claimed status | Subject (one line) |
|---|---|---|---|
| `DEMO_FOLLOWUP_TASK_BRIEFS_2026-08-31.md` | 08-31 | Handoff; pending ratification | 15 demo findings (DEMO-01…15) → EXPLORE/IMPLEMENT/DECISION packages |
| `DEMO01_LEAD_ROUTING_GAP_2026-08-31.md` | 08-31 | Investigation (P0, now implemented) | ESCALATE branch never persisted a lead; Option A adopted |
| `DEMO02_COLLOQUIAL_EXTRACTION_GAPS_2026-08-31.md` | 08-31 | Investigation (P1, now implemented) | Lowercase/colloquial extraction misses + 10 fixtures |
| `DEMO03_PACKET_COVERAGE_AND_CONFIDENCE_2026-08-31.md` | 08-31 | Investigation | 16 facts captured vs 5 UI-visible; party=1/budget=total silent-wrong |
| `DEMO04_SAMPLE_PROFILE_PROVENANCE_2026-08-31.md` | 08-31 | Investigation (remediated) | Alex Morgan card 100% hardcoded + fabricated-fact injection |
| `DEMO05_INBOX_CRASH_INVESTIGATION_2026-08-31.md` + `DEMO08_HARNESS_LIMITATIONS` | 08-31 | Investigation (watch) | `/inbox` crash = dev noise; automation-harness quirks |
| `DEMO06_REPAIR_SURFACE_UX_2026-08-31.md` | 08-31 | Investigation (P2, now implemented) | Repair banner dead-ends; copy audit |
| `RQ01_BUDGET_EXTRACTION_CEILING_2026-08-30.md` | 08-30 | Resolved | Falsifier not triggered; rules beat "deterministic ceiling" |
| `F18_BUDGET_RULE_PACKAGE_IMPLEMENTATION_2026-08-30.md` | 08-30 | Implemented | Budget gate green (F1 0.9524) via extraction fix |
| `DURABLE_AGENT_LEASE_2026-08-29.md` (41 KB) | 08-29 | Research | Lease/heartbeat/fencing design — **premise partially wrong** (lease exists; heartbeat exists but dead) |
| `JOURNEY_DEPENDENCY_GRAPH_2026-08-29.md` (42 KB) | 08-29 | Research (open) | JDG schema+evaluator orphaned; IROPS trigger missing |
| `LIVE_CONNECTIVITY_INTEGRATION_2026-08-29.md` (44 KB) | 08-29 | Research (confirmed open) | No real supplier adapter exists; CONNECTIVITY_TIER design |
| `OTEL_TRACE_CORRELATION_GAP_2026-08-29.md` | 08-29 | Research (open) | OTel spans real, no consumer/dashboard/CI assertion |
| `RAG_PIPELINE_ARCHITECTURE_EXPLORATION_2026-07-25.md` | 07-25 | "Exploration Completed — Ready for Discussion" | 5-pillar knowledge architecture + hybrid graph-vector engine blueprint — **partially implemented; "dense" claim misleading** (see §2) |
| `CORPORATE_EA_AND_DMC_SUPPLIER_PARADIGM_2026-08-03.md`, `TRAVEL_CREATOR_INFLUENCER_PARADIGM_2026-08-03.md` | 08-03 | Exploration | B2B DMC portal / creator-economy paradigms |
| `backlog.md` (89 KB) | 07-02 | "Living backlog" | Catch-all brainstorm — **one of three competing backlogs** (see §3c) |
| May-wave (9 files: KDD ×2, ML_STRATEGY, MESSAGING_BY_ICP, OFF_MAP_CANDIDATES, OPEN_EXPLORATION_IDEATION, PRIORITY_SCORING, PROCESS_MINING, SUITABILITY_SIGNAL_MINING, ASSIGNMENT_ROUTING, WAYPOINT_AGENT_ENQUIRY_REVIEW) | 05-18/19 | Exploration | ML/learning-layer ideation — **no lifecycle statuses; never reconciled with later registers** |
| Jun-wave (4 synthesis docs) | 06-26 | Synthesis | Deployment ops, knowledge mgmt, onboarding setup, institutional-memory compat |

### 1.2 `Docs/review/` (the active audit machinery)

| File | Date | Status | Subject |
|---|---|---|---|
| `PERSONA_COUNCIL_AUDIT_2026-08-31.md` | 08-31 22:10 | Canonical (latest audit) | PER-1065-led council re-verification of R-01…R-16/A-01…A-21 + NEW-01…07 |
| `FINDINGS_REGISTER_2026-08-31.md` | 08-31 22:11 | Claims "Authoritative current-truth register" | Consolidated R/A/F/NEW register — **stale at publication for F-21/F-23/F-25** (see §4) |
| `ALIGNMENT_EVALUATION_2026-08-31.md` | 08-31 22:12 | Canonical companion | FP/LT/DOC verdict per finding |
| `IMPLEMENTATION_PLAN_2026-08-31.md` | 08-31 22:13 | Canonical companion | Waves 0+ with exit gates |
| `DEMO_WAVE2_REMEDIATION_HANDOFF_2026-08-31.md` | 08-31 21:41 | Handoff (APPROVE P0:0 P1:0) | IMP-02/03/05/06/07 implemented — **the doc that proves the register stale** |
| `IMP01_ESCALATE_LEAD_PERSISTENCE_HANDOFF_2026-08-31.md` | 08-31 | Handoff | IMP-01 implemented |
| `PER_0923_EVIDENCE_ARCHITECT_AUDIT_ADDENDUM_2026-08-31.md` (44 KB) | 08-31 | Audit addendum | Evidence-architecture pass |
| `FINDINGS_REGISTER_2026-08-29.md` | 08-29 (modified in working tree) | Superseded statuses per 08-31 | First full register — **being edited in place, violating dated-register immutability** |
| `FINDINGS_TASKS_CONSOLIDATED_2026-08-30.md` | 08-30 | "Single classified register" → superseded statuses | 47 tasks + F-01…F-16 — still cited as "the canonical register" by the ADHD doc |
| `PERSONA_COUNCIL_MASTER_AUDIT_2026-08-29.md` (39 KB) | 08-29 | Superseded verdicts, preserved | First council audit; "358 failed" baseline later shown to be an env artifact |
| `IMPLEMENTATION_PLAN_2026-08-29.md`, `EXPLORATION_RESEARCH_BACKLOG_2026-08-29.md`, `SESSION_RECORD_PERSONA_AUDIT_2026-08-29.md`, `FINDINGS_LIFECYCLE_2026-08-30.md`, `WAVE1_…`, `A13_…`, `A19_…`, `R03_…`, `R-15_…` | 08-29/30 | Superseded/resolved companions | Audit-wave scaffolding |
| `WAYPOINT_OS_REFACTOR_ARCHITECT_AUDIT_2026-08-29.md` (+ WORKLOG) | 08-29 | Superseded by council re-verification | R-01…R-16 origin |
| Older (May): payments/coming-soon/E2-security reviews, `EXPLORATION_MAP_CODEBASE_AUDIT` ×2 | 05-02…05-19 | Historical | Payments readiness thread — no lifecycle tie to current registers |

### 1.3 Root `Docs/ADR_*.md` (19 files, 2026-07-29 → 08-31) + `Docs/architecture/adr/`

- All root ADRs are **date-suffixed, unnumbered**; only `ADR_ESCALATE_LEAD_PERSISTENCE_2026-08-31.md` carries any supersession language. No `Supersedes:`/`Superseded-By:` elsewhere (A-09 verified).
- `Docs/architecture/adr/` holds ADR-001, ADR-002, ADR-006 — **ADR-003/004/005 absent with no tombstone**; the 08-31 audit flags this as "lost or never written" (§6 gap table) and the check was never run.
- Indexed by `Docs/INDEX.md` lines 33–65 (a flat bulleted list, not a registry: no status column, no supersedes chains).

### 1.4 `Docs/INDEX.md` (52 KB)

Structure: a reverse-chronological ⭐ bullet list (Aug 31 → Aug 2 waves), then topic sections (Business Model, Strategy/Operations, UX, ADR pointers). **Stale:** no reference to any 08-31 audit-cluster file (`PERSONA_COUNCIL_AUDIT_2026-08-31`, `FINDINGS_REGISTER_2026-08-31`, `ALIGNMENT_EVALUATION_2026-08-31`, `IMPLEMENTATION_PLAN_2026-08-31`, `PER_0923_…ADDENDUM`) — the newest "authoritative" layer of the record is unindexed.

### 1.5 `Docs/ADHD_APP_AUDIT_EXPLORATION_2026-08-30.md`

30-idea divergent audit (5 cognitive frames), scored/clustered, top-3 deepened, full 30/30 register mapping into the 08-30 consolidated register. Quality artifact; **carries a since-falsified ground-truth line** ("backend suite 358 failed / 2803 passed / 19 errors" — later proven an env artifact by A-13) and its §6 points to the 08-30 register as canonical, which the 08-31 register has since superseded.

---

## 2. Verified-Claims Ledger (claim → verdict → evidence)

| # | Claim (source) | Verdict | Evidence |
|---|---|---|---|
| 1 | RAG retriever provides "dense semantic search" (`retriever.py:1-14` docstring; `RAG_PIPELINE_…07-25.md` §2.1; also repeated in `EXPLORATION_TOPICS.md:358`) | **FALSE in substance** | `src/rag/indexer.py:16-35` `generate_local_embedding()` = md5 word-hash into a 64-dim bag; `retriever.py:34` feeds it as the "dense" leg. Only BM25 does real lexical work. Matches register NEW-04/A-02. |
| 2 | RAG doc: "Current State: `specialty_knowledge.py` = static 5-item dictionary with naive string search" | **STALE (code moved past doc, opposite direction)** | `src/intake/specialty_knowledge.py` is now 124 lines importing `RAGService` (`:3`) — already RAG-wired. Doc's integration table describes the past as present. |
| 3 | RAG doc Phase 2/3: `citations.py`, `graph_store.py`, `graph_extractor.py` | **DO NOT EXIST** | `ls src/rag/` → grounding, indexer, models, retriever, service, store only. Citation formatting folded into `grounding.py:73` (`format_citation_text`). "Graph traversal" is actually label-substring boosting (`retriever.py:92-103`: multiply RRF score ×1.5 when a node label appears in the query text) — no edges, no multi-hop. |
| 4 | ADR_RAG_GROUNDING: groundedness evaluator (0.75 threshold), citation footers, test suite | **TRUE** | `src/rag/grounding.py:13` (`min_confidence_threshold=0.75`), `:73` citation formatter; `tests/test_rag_grounding_pipeline.py` exists. (Inherits claim 1's "dense" mislabel.) |
| 5 | ADR_AUTONOMIC_GHOST_CONCIERGE: "Continuously scans active trips… 24/7 autonomic protection" | **OVERSTATED** | `spine_api/routers/concierge.py:35,38,73,118` — the three endpoints exist, but there is no watcher loop/thread/scheduler anywhere in `concierge.py` or `services/ghost_concierge.py`; `scanned_at` is stamped per request (`:147`). Pull-based evaluation dressed as an autonomic watcher. |
| 6 | `V02_GOVERNING_PRINCIPLES.md`: `operating_mode` is a top-level packet field, not inside facts | **TRUE** | `src/intake/packet_models.py:422` (comment), `:432-436` (field, `Literal[...]`). |
| 7 | Register NEW-01/F-22: every freeform extractor stamps `EXPLICIT_USER` unconditionally | **TRUE** | 33 occurrences in `src/intake/extractors.py` (e.g. `:2160`, `:2165`, `:2211-2262`); derived (`budget_flex` @0.85 `:2262`), default (`currency="INR"` `:2244`) and spurious values all carry user-stated authority. |
| 8 | Register R-11/NEW-07: `ExecutionLease.heartbeat` is dead code | **TRUE** | Defined `src/agents/runtime.py:61-66`; repo-wide `rg "heartbeat"` finds only SSE comments (`spine_api/routers/inbound.py:368,378`) and an unrelated docstring. Zero callers → >60s leases expire and are re-acquirable. |
| 9 | Register R-10: `server.py` = 3,195 lines, 64 routers, 19 inline pydantic models | **TRUE (exact)** | `wc -l spine_api/server.py` = 3195; `rg -c "include_router"` = 64; `rg -c "^class .*(BaseModel)"` = 19. |
| 10 | Register NEW-03: "156 scattered `os.getenv`, no BaseSettings" | **DIRECTIONALLY TRUE, NUMBER KEY-DEPENDENT** | Pure `os.getenv` in `src/`+`spine_api/` = **40** (53 repo-wide); `os.getenv|os.environ` = **170**. The 156 figure matches no clean counting key — direction correct, magnitude unverifiable as stated. No `BaseSettings` anywhere — confirmed. |
| 11 | Register R-03: `TeamStore` deprecated-not-removed | **TRUE** | `spine_api/persistence.py:2568` "DEPRECATED — Use spine_api.services.membership_service instead." |
| 12 | Register A-11: four marketing generations (`app/v2`–`v5`) all routed | **TRUE** | `frontend/src/app/v2 v3 v4 v5` all exist. |
| 13 | Register R-09: `Docs/` ∥ `frontend/docs/` parallel doc trees | **TRUE and growing** | 2,025 vs 932 `.md` (register said 2,020 vs 932 — the shadow grew by 5 files in a day). |
| 14 | Register NEW-05: findings-lifecycle gate exists but is not wired into CI | **TRUE** | `scripts/check_findings_register.py` exists; `rg "findings" .github/workflows/ci.yml` → no match. |
| 15 | Register A-09: no ADR supersession mechanism; numbering broken | **TRUE** | 0 `Supersedes:` in 18 of 19 root ADRs; `adr/` numbering 001→002→**006** (003–005 missing, no tombstone). |
| 16 | Register A-08: `motto_v4.md` deleted, ~20 files still reference it | **TRUE, count drifted up** | No `motto_v4*` file exists anywhere in the repo; **27** `Docs/` files still reference the name. |
| 17 | Register F-20 / ADR_ESCALATE: ESCALATE persists an incomplete lead | **TRUE** | `spine_api/services/pipeline_execution_service.py:324-373` — `save_processed_trip(...)` on the early-exit branch, `trip_status="incomplete"`, no-overwrite guard. |
| 18 | Register F-21/F-23/F-25 = **open** | **FALSE — stale at publication** | Code landed 21:16–21:34 (`src/intake/extractors.py:177` "late march", `:280-296` "me and 3 friends" patterns; `tests/test_extraction_fixes.py`; `RepeatTravelerRecallCard.tsx:21,37` Sample-data badge + zeroed loyalty + `onApply` injection removed). Handoff doc written 21:41. Register written **22:11** — after all of it — and still says open. See §4. |
| 19 | F-01: `price_lock.py` re-lock is a blind read-modify-write | **TRUE** | `spine_api/routers/price_lock.py:184-213` — no version field, no idempotency key, no CAS before `TripStore.save_trip`. Bonus finding: `cost = 3000.0` fabricated fallback at `:196` — the R-04 "no fabricated numbers" fix was scoped to `commission.py` only; the same defect class survives one module over. |
| 20 | F-03: signoff identity is client-supplied | **TRUE** | `spine_api/routers/team_workflows.py:86` `trip["reviewer_id"] = body.reviewer_id`; `spine_api/routers/corporate_policy.py:49` `approved_by: str` populated from `body.approver_name` (`:125,146`). No JWT-subject binding. |
| 21 | ADHD audit header: "backend suite 358 failed / 2803 passed / 19 errors" as ground truth | **FALSIFIED, still circulating** | A-13 resolution (`review/A13_TEST_BASELINE_RESOLUTION_2026-08-30.md`): env artifact; CI-identical baseline 3,206/10/0. The falsified number is still quoted in `ADHD_APP_AUDIT_EXPLORATION_2026-08-30.md:5,146` and `PERSONA_COUNCIL_MASTER_AUDIT_2026-08-29.md`. |
| 22 | `PRODUCT_VISION_AND_MODEL.md` sourcing hierarchy (internal → preferred → network → open market) | **VISION, not implemented (by declared design)** | `src/intake/sourcing_path.py:1-15` — "Currently a stub implementation — no supplier/package database exists yet." Consistent with `ARCHITECTURE_DECISION_D3` ("Implementation blocked on Gap #01"), but the vision doc carries no status marker, so a reader cannot tell vision from reality. |
| 23 | Register chronology: "8ece02e ships IDEA-120/122/123/124" | **PARTIALLY VERIFIABLE ONLY OUTSIDE THE REPO** | Shared idea pad (`/Users/pranay/Projects/idea_pad/IDEA_PAD.md:1941-1950`) still shows IDEA-120 as `stage: inbox` with placeholder fields — shipped code, unrecorded completion (A-10 verified). Pad also mixes other projects into the same ID space (IDEA-124 = a B2C coloring app). |

**Ledger score: 19 verified-true/false-as-claimed, 2 directionally-true with imprecise magnitude, 2 stale-at-publication, 1 vision-unmarked.**

---

## 3. Shadow Systems Found

### (a) Docs describing mechanisms that do not exist (or not as described)

1. **"Dense semantic" RAG + Knowledge-Graph traversal.** Three documents (`RAG_PIPELINE_…07-25.md`, `EXPLORATION_TOPICS.md` §6e, `retriever.py`'s own docstring) claim semantic vectors and graph traversal; the code has md5 bag-vectors and label-substring score boosting (ledger #1, #3). The system's own honesty doctrine (RealityTier) is not applied to its retrieval vocabulary.
2. **Ghost Concierge as a 24/7 autonomic watcher.** ADR + product-features doc describe continuous monitoring; code is three pull-request endpoints with no loop (ledger #5).
3. **`memory/MEMORY.md` — the fossil memory.** Root `memory/MEMORY.md` still asserts "⚠️ CRITICAL: This is a white-label B2B SaaS platform, NOT a direct-to-consumer agency" and "Single-Tenant MVP Strategy — start with one agency," while the canonical `Docs/INDEX.md` (Business Model section) says the exact opposite ("platform-led SaaS like Calendly/Typeform, NOT white-label"; SINGLE_TENANT_MVP marked DEPRECATED) and its pricing differs (₹999–₹19,999 vs ₹6k default plan draft). Two official records assert opposite business models; the stale one sits in the repo root under `memory/`.
4. **The "358 failed" test baseline.** A falsified measurement continues to circulate as ground truth in the 08-29 master audit and the 08-30 ADHD audit headers (ledger #21).

### (b) Code mechanisms with no doc (the shadow exceeds the record)

1. **Seasonal campaigns — fully built, zero docs.** Backend: `spine_api/routers/settings.py:369+` (`/api/settings/seasonal`, campaign CRUD models `:24-37`), `spine_api/persistence.py:2656-2724` (`SEASONAL_CAMPAIGNS_FILE`, `seasonal_policy`, `micro_seasonality_window_days`). Frontend: `frontend/src/app/(agency)/seasons/`, `useSeasonalCampaigns.ts`, `SeasonalTab.tsx`. `rg "seasonal_campaign" Docs frontend/docs` → **no matches**. An entire product surface exists outside the official record.
2. **Routing-health gate.** `src/evals/agentic_feedback.py`, `src/evals/audit/snapshot.py`, `tests/evals/test_routing_health_gate.py` — documented only in `Docs/research/AGENTIC_EVAL_ROUTING_HEALTH_OPERATOR_CONTRACT_2026-07-01.md`, which is **absent from `Docs/INDEX.md`** (0 hits) and has no ADR. Documented, but orphaned from the index.
3. **Frontier orchestration.** `src/intake/frontier_orchestrator.py` (ghost concierge + emotional-state monitoring + federated intelligence) and `spine_api/routers/frontier.py` are covered only by the April-era `SCHEMA_HARDENING_FRONTIER_MODELS_SPEC.md` and aspirational `product_features/*` docs. Critically, the frontier **tables had no migrations and the endpoints were runtime-broken** until the A-20 `add_frontier_tables` migration was added on 08-30 — the record never said the frontier was broken because the record never described the frontier's real state.
4. **Insights/analytics surface.** `spine_api/routers/analytics.py` exists; doc coverage is limited to April planning docs (`DASHBOARD_GOVERNANCE_WIRING_PLAN_2026-04-20.md`) with no current-state reconciliation.

### (c) Duplicates / contested ownership

1. **Three findings registers.** `FINDINGS_REGISTER_2026-08-29.md` → `FINDINGS_TASKS_CONSOLIDATED_2026-08-30.md` ("Single classified register") → `FINDINGS_REGISTER_2026-08-31.md` ("Authoritative current-truth register"). The chain is *declared* (08-31 §0) but not *enforced*: the ADHD doc still points to the 08-30 file as canonical, and `FINDINGS_REGISTER_2026-08-29.md` is being **modified in place** in the working tree (`git status`: ` M Docs/review/FINDINGS_REGISTER_2026-08-29.md`) even though doctrine §6 and AGENTS.md require dated registers be preserved, not edited.
2. **Three exploration backlogs.** `Docs/exploration/backlog.md` (Jul 2, "living"), `Docs/EXPLORATION_TOPICS.md` (Jun 25, calls itself "the master index"), `Docs/review/EXPLORATION_RESEARCH_BACKLOG_2026-08-29.md` (Aug 29, register-tracked with falsifiers). `Docs/INDEX.md` links only the oldest one. Same-day docs disagree about which backlog is real.
3. **F-ID collision inside one day.** `DEMO_FOLLOWUP_TASK_BRIEFS_2026-08-31.md` proposes new IDs "F-19…F-26" while `FINDINGS_REGISTER_2026-08-31.md` Part 4 keeps F-19 = frontend phantom failures and starts demo findings at F-20. The briefs' proposal and the register's allocation silently diverge — a reader cross-referencing F-19 gets two different findings.
4. **Two persona-council audits** (08-29 master vs 08-31) — explicitly reconciled by the 08-31 document ("both canonical; conflicts preserved"). This is the *good* version of duplication; it should be the template, not the exception.

### (d) Institutional memory living outside the repo

1. **Persona definitions on the Desktop.** `PERSONA_COUNCIL_AUDIT_2026-08-31.md:7` cites `/Users/pranay/Desktop/Understanding_Personas_29aug26/` as the persona source. The audit identities (PER-1065, PER-0923, PER-0930…) that drive the entire review machinery are not in the repo; the repo's own `Docs/personas/` holds *product* personas (a different concept).
2. **The shared idea pad.** `/Users/pranay/Projects/idea_pad/IDEA_PAD.md` is the canonical ideation store per AGENTS.md but sits outside the repo, is cross-project (Daily Hue entries share the ID space with Waypoint entries), and never records completion (IDEA-120 shipped; pad says `stage: inbox`).
3. **Session-transcript evidence.** The audits' strongest evidence tier ("4 parallel read-only explorers… each returned file:line evidence", `PERSONA_COUNCIL_AUDIT_2026-08-31.md:44-46`) is chat-session output — the explorer transcripts and the in-process probe outputs are not persisted anywhere; the record asserts evidence that cannot be re-derived from the repo.
4. **Workspace-level context** (`Docs/context/agent-start/*` + `.agent/` mirrors, `OPERATING_DOCTRINE.md` generated copy) is in-repo — this part of the memory stack is healthy.

---

## 4. Staleness / Contradiction Map

| # | Doc | Contradicted by | Nature |
|---|---|---|---|
| 1 | `review/FINDINGS_REGISTER_2026-08-31.md` (F-21, F-23, F-25 "open") | `review/DEMO_WAVE2_REMEDIATION_HANDOFF_2026-08-31.md` (APPROVE P0:0 P1:0) + code (`extractors.py:177,280-296` 21:34; `RepeatTravelerRecallCard.tsx` 20:40; tests 21:16) | **Self-contradiction within the same wave**: the register was written at 22:10–22:13, *after* the handoff (21:41) and after the code landed, yet records the findings as open. The "Authoritative current-truth register" was stale at the moment of its own publication. This is the sharpest possible demonstration of the audit-treadmill finding (council §3.1) — and the findings-lifecycle gate that would have caught it exists but is not in CI (NEW-05). |
| 2 | `ADHD_APP_AUDIT…08-30.md` + `PERSONA_COUNCIL_MASTER_AUDIT_08-29.md` | `review/A13_TEST_BASELINE_RESOLUTION_2026-08-30.md` | Falsified baseline number (358 failed) still quoted as ground truth in two headers. |
| 3 | `ADHD_APP_AUDIT…08-30.md` §6 | `review/FINDINGS_REGISTER_2026-08-31.md` | Points to 08-30 register as canonical; 08-31 superseded its status columns the next day. |
| 4 | `exploration/RAG_PIPELINE_…07-25.md` + `EXPLORATION_TOPICS.md` §6e | `src/rag/indexer.py:16-35`, `retriever.py` | "Ready for Discussion" while Phases 1–2 already shipped; "dense semantic"/"graph traversal" claims false; "static 5-item dictionary" current-state false (already RAG-wired). |
| 5 | `ADR_AUTONOMIC_GHOST_CONCIERGE_07-29.md` + `product_features/GHOST_CONCIERGE_AUTONOMIC_ENGINE.md` | `spine_api/routers/concierge.py` (no loop), `services/ghost_concierge.py` (pure functions) | "Continuous/24-7 autonomic" wording; reality is pull-request evaluation. |
| 6 | `memory/MEMORY.md` | `Docs/INDEX.md` Business Model section | Opposite business-model declarations (white-label vs platform-led); stale pricing; deprecated single-tenant strategy presented as current. |
| 7 | `Docs/INDEX.md` | existence of the 08-31 audit cluster | Index omits the newest authoritative layer (4 files) and the newest ADRs' audit context; links only the oldest of three backlogs. |
| 8 | `exploration/DURABLE_AGENT_LEASE_08-29.md` | `src/agents/runtime.py:51-86` + R-11 correction | Research premise ("no durable lease exists") half-wrong at birth; the doc survives as if fully valid. |
| 9 | Root `Docs/ADR_*` (07-29/08-02 cluster) | `review/FINDINGS_REGISTER_2026-08-31.md` Part 2 (A-03) | Several Priority/ADR docs describe "implemented" engines whose agent-tool connectivity remains Mock-by-default (`live_tools.py:406-408`) and is not tied to `RealityTier` — the ADRs describe wiring that exists only as endpoints, not as live behavior. |
| 10 | `review/FINDINGS_REGISTER_2026-08-29.md` | working tree (` M`) | Historical register edited in place, violating the repo's own preserve-dated-registers doctrine. |

---

## 5. Doc-Action List (prioritized)

**P0 — make the current-truth layer trustworthy (hours, no code):**
1. **Amend `FINDINGS_REGISTER_2026-08-31.md` statuses** for F-21 → fixed, F-23 → fixed-partial (card de-fanged/badged; frontend wiring + legacy-store scoping still open), F-25 → fixed-partial (banner reaches editable surface; ?repair deep-link deferred) — with an explicit "amended 2026-08-31 after Wave-2 handoff" note rather than silent edits, and update the same rows in `FINDINGS_TASKS_CONSOLIDATED_2026-08-30.md` via the lifecycle tool, not by hand.
2. **Wire `scripts/check_findings_register.py` into `.github/workflows/ci.yml`** (NEW-05). This is the single control that prevents recurrence of contradiction #1; without it every register is best-effort prose.
3. **Add the 08-31 audit cluster to `Docs/INDEX.md`** (4 files + PER_0923 addendum) and add a one-line "current-truth pointer" at the top of the index naming `FINDINGS_REGISTER_2026-08-31.md` as authoritative so no reader has to guess which of three registers to trust.

**P1 — kill the falsified and inverted records (half a day):**
4. **Rewrite `memory/MEMORY.md` as a pointer file** to `Docs/INDEX.md` (archive its April content with a "superseded 2026-04-14" banner). Two opposite business-model declarations in one repo is the most damaging single contradiction for any future agent or reader.
5. **Add truth-caveats to the falsified baseline**: one-line correction at the top of `ADHD_APP_AUDIT…08-30.md` and `PERSONA_COUNCIL_MASTER_AUDIT_2026-08-29.md` pointing to A-13 (per doctrine: record the correction in place, don't rewrite history).
6. **Write the missing subsystem doc: `Docs/architecture/SEASONAL_CAMPAIGNS.md`** (or a README beside the router) documenting the seasonal-policy + campaign CRUD surface, and a stub `ROUTING_HEALTH.md` linking the existing operator contract; add both to INDEX. This closes the largest code-without-doc shadow (seasonal = full product surface, zero record).
7. **Correct the RAG vocabulary** where it is cheapest: fix `retriever.py`/`service.py` docstrings ("dense" → "hash-based lexical fallback; not semantic"), add a `RealityTier.DETERMINISTIC_PREVIEW` honest_status note to `EXPLORATION_TOPICS.md` §6e and the RAG exploration doc header, and log A-02/NEW-04 as the owning finding (already in register — no new doc needed).

**P2 — structural consolidation (1–2 days):**
8. **Retire two of the three backlogs**: declare `review/EXPLORATION_RESEARCH_BACKLOG_2026-08-29.md` the canonical queue; convert `Docs/exploration/backlog.md` and `EXPLORATION_TOPICS.md` into archived snapshots with forward pointers (preserving history per repo rules). Update the INDEX backlog link.
9. **Fix the F-ID collision**: rename the demo briefs' proposed IDs (F-19…F-26 → the register's actual F-20…F-26 allocation) or annotate the briefs with a mapping table, so cross-references resolve.
10. **Restore edit-immutability of dated registers**: `git checkout`-free fix — revert the in-place edits to `FINDINGS_REGISTER_2026-08-29.md` into an appended "Status amendments (2026-08-31)" section, and add a guard note in `FINDINGS_LIFECYCLE_2026-08-30.md` that dated registers are append-only.
11. **Resolve ADR-003/004/005**: run the council's own proposed check (`git log --diff-filter=D -- '*ADR-00[345]*'`); either restore, or add tombstone stubs so the numbering gap stops implying lost decisions.

**P3 — external-memory hygiene (when convenient):**
12. **Copy the PER-* persona definitions into the repo** (`Docs/personas/audit_personas/` or `Docs/review/personas/`) so the audit machinery's identity layer survives Desktop cleanup; leave the shared idea pad external but add `stage: shipped + link-to-evidence` updates for IDEA-120/122/123 (AGENTS.md's append/update flow supports this).

---

## 6. Open Questions

1. **Who closes the register?** The lifecycle checker exists and is CI-ready, but nothing assigns an owner to run it daily during an active remediation wave. Should the wave handoff template gain a mandatory "update register before handoff APPROVE" step?
2. **Is the AI-generation IDEA-124 collision benign?** The pad's IDEA-124 belongs to another product (Daily Hue) while audits cite "IDEA-124 shipped" for Waypoint. Are pad IDs namespaced per project? If not, every cross-reference between pad and repo is ambiguous.
3. **What was ADR-003/004/005?** Deleted, never written, or on another branch? The repo record cannot answer; only git archaeology outside this audit's scope can.
4. **Which marketing generation is canonical?** `app/v2–v5` are all routed (A-11) and none of the four docs that describe "the" landing experience names the live one. Product decision needed before any doc can describe the front door truthfully.
5. **Should `frontend/docs/` (932 files) be reconciled, archived, or deleted?** R-09 is open with no proposed mechanism; the two trees already disagree by construction (frontend-facing vs repo-facing audiences), so the answer may be "formalize the split with a cross-link policy" rather than "merge."
6. **Do the explorer transcripts need persistence?** If T3-tier evidence claims remain admissible, the session outputs behind them (4 explorers, in-process probes) need a durable home; otherwise the evidence tiers in the audit docs overstate what the repo can prove.

---

*Audit performed read-only; no files outside this document were created or modified. Evidence current as of 2026-08-31 working tree.*
