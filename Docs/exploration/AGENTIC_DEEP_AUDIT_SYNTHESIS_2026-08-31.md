# Agentic Deep Audit — Master Synthesis, Findings Inventory & Implementation Plan

*Date: 2026-08-31 · Status: Exploration complete; implementation plan pending ratification*
*Method: 6 skills loaded + 6 personas applied + 4 parallel deep-exploration agents + full chat process documented (§1). Every claim in the four source docs is file:line-cited; this synthesis unifies them.*

**Source explorations (companion docs, each persona-framed):**

1. `AGENTIC_FLOW_DEEP_MAP_2026-08-31.md` — PER-0700 Agentic Systems Architect: the real pipeline map
2. `BROWSER_LLM_SLM_RESEARCH_2026-08-31.md` — PER-0882 Model-Routing Optimization Engineer: browser/on-device inference research
3. `DOCS_CORPUS_SHADOW_AUDIT_2026-08-31.md` — PER-0930 Shadow-System Investigator: docs-vs-reality audit
4. `EVAL_ARCHITECTURE_AND_RED_TEAM_AUDIT_2026-08-31.md` — PER-0897/PER-PDEV-0425/PER-0902: eval architecture + confirmed red-team findings
5. `GEMINI_WAVE_MODULE_AUDIT_2026-09-01.md` — audit of the parallel Gemini wave (~30 new modules): genuine hardening stack vs simulated-capability expansion (GM-01…GM-09)
6. `SIM_VS_REALITY_RECONCILIATION_2026-09-01.md` — chronicle/case-study claims vs code reality: 30 claims adjudicated (7 VERIFIED / 5 PARTIAL / 17 SIMULATED)

---

## 1. Process Record (chat → evidence, per the full-documentation doctrine)

| Step (chat order) | What was done | Evidence artifact |
|---|---|---|
| Skills check | Read all 6 referenced SKILL.md files (agentic-workflow, agent-evaluation, agent-memory-mcp, agent-management, Agent Development, agent-orchestration). Verdicts in §4.5 | This doc §4.5 |
| Personas located | `~/Desktop/Understanding_Personas_29aug26/` — registry + 15 families; converted 6 persona docs to text (PER-0700, PER-0897, PER-PDEV-0425, PER-0902, PER-0882, PER-0930) via `textutil`; applied as audit lenses | `/tmp/personas_txt/` (session), persona docs cited above |
| Exploration A | PER-0700 deep pipeline map — 75 tool calls, full file:line map | Doc 1 |
| Exploration B | PER-0882 browser LLM/SLM web research — 30 calls, 9 sources cited | Doc 2 |
| Exploration C | PER-0930 docs-corpus shadow audit — 43 calls, 23-entry claims ledger | Doc 3 |
| Exploration D | Eval + red-team audit — 115 calls, all red-team claims probe-confirmed | Doc 4 |
| Prior session context (same day) | IMP-01 ADR + implementation (2 review cycles, APPROVE), Wave 2 (IMP-02/03/05/06/07, APPROVE P0:0 P1:0), 4-part demo exploration (DEMO01–06 docs), tool-taster demo report | Handoffs + exploration docs, all INDEX-linked |

## 2.5 Gemini Wave Integration (added 2026-09-02)

A large parallel wave (dated 2026-09-01) landed after this synthesis: 4 live computer-use simulations with BUY verdicts (chronicle + 16 case studies), 12 persona docs, ~30 new src/ modules, ~20 new test files (116/116 green), Dockerfiles, and register updates. Audited in companion docs 5–6 (GEMINI_WAVE_MODULE_AUDIT_2026-09-01.md; SIM_VS_REALITY_RECONCILIATION_2026-09-01.md). Integration into this inventory:

| ID | Finding | Sev | Disposition |
|---|---|---|---|
| GM-01 | Wave = two interleaved bodies: **(A) genuine hardening to land** (intake idempotency+409, optimistic concurrency, merge precedence, status machine in both stores, RLS flush/commit, staging auth kill-switch, credential purge, truthful route snapshots) | ok | Split-commit: land (A) separately from (B) |
| GM-02 | "Production … Adapter" provider modules: zero callers, zero network calls; Amadeus docstring claims "live OAuth2" vs in-process simulator | P1 | Rename to sandbox/simulated or gate; never "Production" without network |
| GM-03 | Stripe `verify_webhook_signature` returns True unconditionally — fake security control | P0-adj | Replace with real verification or remove the control surface |
| GM-04 | New HMAC proposal tokens: hardcoded default secret, ≥16-char "legacy" bypass, test-agency UUID in verify loop | P0-adj | Close bypasses before any public surface |
| G-01-amp | 12 NEW unlabeled simulated panels; GDSSandboxPanel says "Live" for uuid-fabricated offers | P1 | Label-or-gate per the never-both-and-hidden rule |
| SIM-REC | 30 chronicle claims adjudicated: extraction claims VERIFY (post-IMP-02: dates, party, wheelchair, urgency — warm 3–7ms); 17 SIMULATED incl. "ACCEPTED BY SUPPLIER" (React array) and "transmitted to U.S. Embassy" (zero network calls) | P1 (record) | Annotate chronicle + 16 case studies with simulator caveat; fix the 5 worst "Live/transmitted/issued" copy strings |
| REC-2 | Audit findings G-01…G-19 + GM-01…GM-09 captured NOWHERE in review/status registers; BUILD_QUEUE records shadow modules as "Completed"; A-18 has opposite statuses in the two registers | P1 (record) | Register-integration pass (expands G-19) + resolve the A-18 split |
| REC-3 | Positive: extraction sim claims verify against the real pipeline post-fixes — the deterministic core's record is strengthening | ok | Keep anchoring simulations to the deterministic core |

**Plan impact:** Phase 1 (honest eval core) unchanged and more urgent — the simulated surface grew ~5x. Phase 2 gains GM-03/GM-04 (same immediate-hotfix class as G-08/G-09). Phase 3 gains chronicle annotation, the A-18 split resolution, and BUILD_QUEUE truthfulness. The commit-split recommendation (land hardening (A) separately from simulator expansion (B)) is Phase-0 ratification material.

---

## 2. The Headline Discoveries

1. **The "agentic" serving path is 100% deterministic — zero LLM calls.** `POST /run → run_spine_once` is regex extraction + rule decisions + policy gates. LLM code exists in 4 places; only vision-doc-extraction is wired (human-gated, default `noop`). The hybrid decision engine and suitability Tier-3 LLM scorer are **built but orphaned** (Doc 1).
2. **`fallback_trigger_rate`/`false_escalation_rate` measure a router that doesn't exist** — they are eval-harness reducers over ExecutionEvent metadata, not runtime model-routing telemetry (Doc 1 §2; Doc 4 confirms `routing_health` computed over `[]`).
3. **Frontier OS and Persona Council are simulated subsystems** — fabricated ghost ids, hardcoded `trip_council_demo` — rendered behind agentic dashboards; meanwhile the honest ghost-concierge engine has **zero callers** (Doc 1 F-A1/F-A2).
4. **The RAG pipeline's documented architecture is false**: "dense semantic search" is an md5 hash-vector (`src/rag/indexer.py:16-35`); "graph traversal" is label-substring boosting (`retriever.py:92-103`) (Doc 3).
5. **The eval system grades mirrors**: `extraction` (50 fixtures) and `pipeline` (7) gating lanes are "expected-as-actual" (self-fulfilling); colloquial fixtures are verbatim leaked into `tests/test_extraction_fixes.py` — the F1=1.0 measures memorization, not generalization (Doc 4, holdout leak CONFIRMED).
6. **Confirmed red-team findings**: escapeable egress prompt delimiter (`llm_egress.py:193`); hybrid engine interpolates raw packet facts into prompts undelimited; draft-promote accepts **cross-tenant trip_id**; 100KB note ≈4s CPU + 14s cold-start via the **unauthenticated** public-checker endpoint; `structured_json` depth-unbounded → RecursionError; legacy `CUSTOMER_MEMORY_STORE` unpartitioned (memory-poisoning latent). RLS FORCE verified holding live (Doc 4 §3).
7. **Browser LLM/SLM**: only WebLLM (XGrammar) and Chrome Prompt API (stable Chrome 148) give constrained JSON in-browser; a fully in-browser checker is **REJECTED** on quality-economics (cloud ≈ $0.001/note vs weaker SLM silent-wrong-values); deterministic extractors are correctly understood as routing tier 0; the justified experiment is an opt-in on-device draft + server-verify path (Doc 2).
8. **The record is trustworthy only where a gate enforces it**: 3 competing findings registers; the authoritative register was stale at publication (listed shipped fixes as open); MEMORY.md asserted the opposite business model; seasonal campaigns fully built with zero docs (Doc 3).

## 3. Unified Findings & Tasks Inventory (explicit + implicit)

Severity: P0 security/data-loss · P1 product-correctness/economics · P2 quality/consistency · P3 hygiene. Alignment: ✓ = aligned, ✗ = violates, ? = undecidable without a ratification call. (Sources: [1]=Doc 1, [2]=Doc 2, [3]=Doc 3, [4]=Doc 4, [D]=prior demo wave docs.)

| ID | Finding / Task | Sev | FP¹ | LT² | Doc³ | Disposition |
|---|---|---|---|---|---|---|
| G-01 | Simulated subsystems (Frontier OS, Persona Council) render fabricated data behind dashboards while honest concierge engine is orphaned | P1 | ✗ (epistemic-integrity doctrine: traceable decisions) | ✗ | [1] | Decide: wire honest engine OR clearly label simulated; never both-and-hidden |
| G-02 | No runtime model router exists; routing_health metrics measure nothing real | P1 | ✓ concept ✗ reality | ✓ | [1], [4] | Either build the router (post-eval) or re-scope the metrics honestly until then |
| G-03 | Orphaned LLM assets: hybrid decision engine + suitability Tier-3 scorer built, unwired, untested-in-prod | P2 | ? | ✓ | [1] | Ratify: wire behind gates with eval evidence, or archive per supersession |
| G-04 | RAG doc claims false (hash-vector ≠ dense; substring ≠ graph); doc-vs-code schism | P1 | ✗ (no-dummy-fallbacks; traceable decisions) | ✗ | [3] | Rewrite RAG doc to reality; decide RAG's real roadmap separately |
| G-05 | Eval: extraction/pipeline lanes "expected as actual" (grade nothing); 30-scenario corpus unwired | P1 | ✗ | ✓ | [4] | Phase 1 of eval architecture: live collectors + scenario wiring |
| G-06 | Holdout leak: colloquial fixtures verbatim in dev tests — F1 measures memorization | P1 | ✗ | ✓ | [4] | Hidden-holdout directory + development-visibility policy |
| G-07 | Journey-level tests absent from CI (the four-gap closure) | P1 | ✗ | ✓ | [4] | ADR §5 journey tests as pytest in CI |
| G-08 | Red-team: escapeable egress delimiter + undelimited fact interpolation in hybrid prompts | P0-adjacent | ✗ | ✓ | [4] | Delimiter hardening + delimited interpolation + red-team regression corpus |
| G-09 | Red-team: draft-promote accepts cross-tenant trip_id | P0-adjacent | ✗ (tenant isolation doctrine) | ✓ | [4] | Tenant ownership check on promote |
| G-10 | Public-checker DoS surface: unauth 100KB notes, depth-unbounded structured_json | P1 | ✗ | ✓ | [4] | Size/depth limits + rate posture decision |
| G-11 | Legacy CUSTOMER_MEMORY_STORE unpartitioned (poisoning latent; blocks Option-A memory wiring) | P1 | ✗ | ✓ | [4] | Partition by agency before wiring memory recall |
| G-12 | 3 competing findings registers; authoritative register stale at publication; findings gate exists but unwired in CI | P1 | ✗ | ✗ | [3] | Consolidate to one register + wire findings gate into CI |
| G-13 | MEMORY.md asserted opposite business model; falsified baselines circulate | P1 | ✗ | ✗ | [3] | Rewrite as pointer doc; caveat falsified numbers |
| G-14 | Seasonal campaigns: fully built, zero docs (code-ahead-of-record) | P2 | ✗ | ✓ | [3] | Write the missing doc |
| G-15 | 19 unnumbered root ADRs; ADR 003–005 missing; 3 exploration backlogs; F-ID collisions | P2 | ✗ | ✗ | [3] | Consolidate; renumber; single backlog |
| G-16 | Browser-LLM: in-browser checker rejected; on-device draft+verify justified only as opt-in experiment pending benchmark + disagreement telemetry | P3 (defer) | ✓ (PER-0882: evidence-first) | ✓ | [2] | Park behind golden-set SLM benchmark + telemetry gate |
| G-17 | Personas: repo persona stack dir (09 Travel) is thin (INDEX-only) vs rich desktop registry — Waypoint-specific personas under-leveraged | P3 | ✓ | ✓ | [personas repo] | Adopt relevant personas into Docs/personas/ over time |
| G-18 | Skills assessment: agent-evaluation + agentic-workflow + agent-orchestration patterns already embedded in our practice; agent-memory-mcp concept duplicates our Docs/memory; agent-management (AI Maestro) not applicable to product | P3 (record) | — | — | §4.5 | No action; recorded |
| G-19 | Register/bookkeeping: integrate today's wave + audit findings as proposed rows (pending-veto) | P3 | ✓ | ✓ | [chat] | Register integration pass |

¹ FP = first-principles alignment (real-world behavior before code symmetry; explicit over implicit; existence vs epistemics split).
² LT = long-term coherence (Wave-2/3 autonomy, multi-tenant scale, evolvability).
³ Doc = primary evidence source.

**Explicit carry-overs still open from the demo wave:** IMP-01 banner visual check; P2-6 sibling sample panels; P2-7 `?repair=` deep-link; three contract decisions (trip_duration, flights-inclusiveness, country-vs-city); DEC-01 signup posture; register ratification.

## 4. Cross-Cutting Assessment

### 4.1 Is the agentic flow first-principles-aligned?

**The deterministic core: yes — more than the marketing implies.** The pipeline's honesty (explicit gates, blocked-as-first-class, epistemics/existence split from the ADR) is textbook PER-0700: "first ask whether deterministic workflow… is sufficient" — it is, and it is. **The agentic theater: no.** Simulated dashboards (G-01), metrics for a nonexistent router (G-02), and self-grading eval lanes (G-05) violate the same doctrines the deterministic core honors. The pattern is consistent: *where the code is honest, it is excellent; where the record or dashboard outruns the code, doctrine is violated.*

### 4.2 Long-term coherence risks

The eval architecture (Doc 4's 6 phases) is the single highest-leverage investment: every other wave's correctness becomes checkable only when evals grade reality. Second: the record consolidation (G-12/13/15) — parallel registers and stale "authoritative" docs are how the next agent repeats yesterday's mistakes. Third: wiring decisions (G-01/G-03) should follow, not precede, the eval work — wire only what evaluation can judge.

### 4.3 What else can be improved/added (net-new, doctrine-derived)

- **Failure-becomes-fixture rule** as doctrine: every confirmed real-world failure merges a fixture before/with its fix (already practiced informally in Wave 2).
- **Journey smoke in CI** (signup → intake → blocked → inbox), closing the manual-E2E gap.
- **Agent runtime documentation**: Doc 1 found an 18-agent production runtime with SQL leases that no exploration doc had ever mapped — give it a first-class architecture doc.
- **Personas into the repo**: adopt the 6 applied personas (+ travel stack) under `Docs/personas/` so audits are repeatable without the Desktop dependency.
- **Decision-rights register**: G-01/G-03/G-16 are ratification-class; capture them in one place with recommended dispositions (done in §5).

### 4.5 Skills assessment (per request)

- `agentic-workflow` / `agent-orchestration` / `Agent Development`: patterns already embedded in how we run subagents (parallel, file-artifact handoffs, read-only reviewers); no change needed.
- `agent-evaluation`: its anti-pattern list (single-run testing, happy-path only, aggregate scores hiding slices) is now effectively our eval-lane design rationale — worth citing in the eval ADR.
- `agent-memory-mcp`: concept duplicates what Docs + findings register + auto-memory already provide; not adopting the MCP server.
- `agent-management` (AI Maestro CLI): manages coding-agent sessions — not applicable to the product.

## 5. Implementation Plan (phased, dependency-ordered, pending ratification)

**Phase 0 — Ratification block (Pranay):** G-01 disposition (label vs wire), G-03 (wire vs archive), G-16 posture, DEC-01 signup posture, eval-phase ordering, register IDs. Nothing below needs these except where marked.

**Phase 1 — Honest eval core (est. 3.5–6.5 days; highest leverage):**

1. Live collectors + 30-scenario wiring for extraction/pipeline lanes (G-05).
2. Hidden-holdout directory + development-visibility policy (G-06).
3. Journey smoke tests into CI (G-07, ADR §5).
4. Findings-gate wired into CI + register consolidation (G-12) — this makes Phase 2's record trustworthy.

**Phase 2 — Red-team hardening (est. 2–3 days):**
5. Egress delimiter + delimited interpolation (G-08); red-team regression corpus.
6. Draft-promote tenant ownership check (G-09).
7. Public-checker size/depth limits + rate posture (G-10).
8. CUSTOMER_MEMORY_STORE agency partitioning (G-11 — precondition for memory recall wiring).

**Phase 3 — Record consolidation (est. 1–2 days):**
9. RAG doc rewrite to reality (G-04); MEMORY.md rewrite + falsified-baseline caveats (G-13); seasonal-campaigns doc (G-14); ADR/backlog consolidation (G-15); personas adoption (G-17).

**Phase 4 — Agentic boundary decisions (needs Phase 0 ratification + Phase 1 evidence):**
10. G-01: label simulated subsystems immediately (cheap, honest) → wire-or-archive decision after eval core exists.
11. G-02/G-03: re-scope routing_health to ops-health-only until a real router exists; then wire hybrid engine behind NB02 with eval evidence (PER-0700: gates stay deterministic).
12. G-16: SLM benchmark on the golden set before any on-device tier; opt-in draft+verify experiment only after disagreement telemetry.

**Ongoing:** failure-becomes-fixture rule; register integration (G-19); IMP-01 visual check; P2-6/P2-7 slices; contract decisions (trip_duration/flights/country).

## 6. Open Questions for Pranay

1. G-01: label Frontier/Persona Council as simulated now, and decide wire-vs-archive when? (Recommend: label now, decide post-Phase-1.)
2. G-09/G-10 severity: treat cross-tenant promote + public-checker DoS as immediate hotfixes (pre-Phase-2) or fold into Phase 2? (Recommend: immediate — they're small diffs.)
3. Holdout governance: who may add holdout fixtures, and do dev-visible mirrors exist at all? (Recommend: fixtures dir 0700-equivalent = evals/audits lane only.)
4. Business-model record: confirm platform-led (vs white-label) so MEMORY.md can be rewritten truthfully.
5. Register: approve G-19 integration pass with F-ID allocation against the consolidated register.
