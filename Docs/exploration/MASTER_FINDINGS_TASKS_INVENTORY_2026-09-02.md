# Master Findings & Tasks Inventory — All Sources, Classified (2026-09-02)

## Current authority clarification — 2026-09-05

This inventory preserves discovery categories, aliases and historical research
decisions. It is **not a second current lifecycle authority**. Current canonical
row states are owned by `../review/FINDINGS_REGISTER_2026-08-31.md`; execution
receipts by `../review/EXECUTION_STATUS_2026-09-04.md`; sequencing by
`../review/IMPLEMENTATION_PLAN_2026-08-31.md`. Do not infer that every older
`Open` below still requires implementation, or that an older `Done` proves
release readiness. Source-qualified ID reconciliation remains EV-02 and
overlay reconciliation remains EV-03; neither is silently claimed complete.

The [reviewed source-qualified collision map](../review/FINDINGS_LIFECYCLE_2026-08-30.md#source-qualified-identity-and-reviewed-collision-map)
now disambiguates this inventory's F-01–F-05 and R-01–R-10 from identically named
canonical rows. Use `inventory-2026-09-02::F-03` for simulator-copy work and
`canonical::F-03` for actor/signoff integrity. Related/subtask/split mappings do
not inherit completion automatically; unmapped decisions remain visible.

The current evidence-tool wave repaired lifecycle parsing and tenant-scoped
status reporting (EV-01/06/07). The canonical CLI now counts **145 rows:
91 open, 53 closed, 1 deferred**, excluding historical companions. These are
dated mechanical row counts, not a deduplicated count of all implicit research,
implementation, decision and release work in this inventory. The earlier
combined counts and generic Git-authorization/concurrency statements below
remain historical, superseded by the current request/evidence trace.

*Sources: Tool-taster demo (DEMO-01…15), IMP-01/Wave-2 handoffs, Agentic Deep Audit (G-01…G-19), Gemini wave (GF-01…10, GM-01…09, REC-1/2/3), Spine audit (PT-01…09), eval/red-team audit, docs shadow audit, carried register items (A-xx open rows).*
*Status basis: verified against the working tree 2026-09-02. Companion: `AGENTIC_DEEP_AUDIT_SYNTHESIS_2026-08-31.md` (§2.5, §3, §5).*
*Checklist applied: IMPLEMENTATION_AGENT_REVIEW_HANDOFF_CHECKLIST.md*

**Classification:** ✅ DONE (shipped + verified) · 🔬 EXPLORE (research → document first) · 🛠 IMPLEMENT (code change, brief exists or is trivial to write) · ⚖ DECIDE (owner call) · 📝 RECORD (documentation-only).

---

## A. Security (highest priority)

| ID | Item | Source | Class | Status |
|---|---|---|---|---|
| S-01 | Proposal signing secret hardcoded fallback (`public_proposals.py:86`) | PT-01 | 🛠 | Open |
| S-02 | ≥16-char "legacy" token bypass → `trip_legacy` (:117/:132); signature-rejection dead code | PT-02 | 🛠 | Open |
| S-03 | Agency guess-loop in verify incl. test-agency UUID; agency_id signed but unused (root cause of S-02 design) | PT-03/04 | 🛠 | Open |
| S-04 | Stripe `verify_webhook_signature` returns True unconditionally (`stripe_issuing_adapter.py:84-90`) | GM-03 | 🛠 | Open |
| S-05 | Draft-promote accepts cross-tenant trip_id | GM-06? (audit doc §3) / G-09 | 🛠 | Open |
| S-06 | Egress prompt delimiter escapeable (`llm_egress.py:193`); hybrid engine interpolates raw packet facts undelimited (flag-gated) | G-08 / red-team | 🛠 + 🔬 (threat-model doc) | Open |
| S-07 | Public-checker DoS: unauth 100KB notes (≈4s CPU + 14s cold-start), `structured_json` depth-unbounded RecursionError | G-10 / red-team | 🛠 | Open |
| S-08 | Legacy `CUSTOMER_MEMORY_STORE` unpartitioned (poisoning latent; blocks memory-recall wiring) | G-11 | 🛠 | Open |
| S-09 | "Production" provider adapters: zero callers, zero network; Amadeus docstring claims live OAuth2 | GM-02 | 🛠 (rename/gate) | Open |
| S-10 | 12 new routers rely on global AuthMiddleware ordering only | GM-07 / PT-09 | 🛠 | Open |
| S-11 | Token revocation in-memory only; sig truncated to 64 bits | PT-05/06 | 🛠 | Open |
| S-12 | RLS posture: FORCE verified holding (positive) — keep verified in CI | red-team confirmation | 🔬 (CI probe) | Open |
| S-13 | Staging auth kill-switch gap — CLOSED (startup_assertions extended) ✅ | PT-OK-2 | ✅ | Done |
| S-14 | DATABASE_URL committed-default — CLOSED (hard fail) ✅ | PT-OK-1 | ✅ | Done |

## B. Eval & Verification (the leverage layer)

| ID | Item | Source | Class | Status |
|---|---|---|---|---|
| E-01 | Extraction/pipeline gate lanes "expected-as-actual" (grade nothing) → live collectors | G-05 / eval audit | 🛠 | Open |
| E-02 | 30-scenario corpus unwired → wire into gate | G-05 / eval audit | 🛠 | Open |
| E-03 | Holdout leak: colloquial fixtures verbatim in dev tests → hidden-holdout dir + visibility policy | G-06 / eval audit | 🛠 + ⚖ (governance) | Open |
| E-04 | Journey smoke (signup→intake→blocked→inbox) into CI | G-07 / ADR §5 | 🛠 | Open |
| E-05 | Findings gate wired into CI (checker exists) + single consolidated register + A-18 split + BUILD_QUEUE truthfulness | G-12 / REC-2 | 🛠 | Open |
| E-06 | Trajectory evaluation over run ledger; real routing metrics (routing_health currently computed over `[]`) | eval audit | 🔬 then 🛠 | Open |
| E-07 | Production shadow-eval + calibrated model-judge (PER-PDEV-0425 protocol) | eval audit Phase 6 | 🔬 then 🛠 | Open |
| E-08 | Red-team regression corpus (from confirmed findings S-04…S-08) | eval audit Phase 5 | 🛠 (after fixes) | Open |
| E-09 | Failure-becomes-fixture rule as doctrine (practiced informally) | process | 📝 | Open |
| E-10 | Warnings (PARTY_*) not assertable in gate format — format extension design | IMP-07 note | 🔬 | Open |
| E-11 | Adversarial corpus lane (Hinglish, voice-transcript, emoji, mixed-language) | four-gap #4 | 🔬 then 🛠 | Open |

## C. Agentic Boundary & Simulated Systems

| ID | Item | Source | Class | Status |
|---|---|---|---|---|
| C-01 | Frontier OS / Persona Council: simulated subsystems behind dashboards — **label now**; wire-or-archive after eval core | G-01-amp | ⚖ then 🛠 | Open (amplified: 12 new panels, GDSSandboxPanel "Live") |
| C-02 | Orphaned-asset dossiers: hybrid decision engine, suitability Tier-3 scorer, ghost concierge (0 callers), 9 zero-caller modules, yield-arbitrage engine → wire-or-archive each | G-03 / GM-06 | 🔬 then ⚖ | Open |
| C-03 | Routing: no runtime router exists; routing_health = eval reducers. Design real router ONLY after E-01…E-04 provide ground truth | G-02 / PER-0882 | 🔬 then ⚖ | Open |
| C-04 | Browser-LLM: on-device draft+verify experiment — gated on SLM golden-set benchmark + disagreement-rate telemetry (in-browser checker rejected) | G-16 / PER-0882 | 🔬 (benchmark first) | Parked |
| C-05 | Agent runtime (18 agents, SQL leases, prod) — first-class architecture doc | Doc 1 | 📝 | Open |
| C-06 | LLM wiring candidates (vision-extraction pattern as template) — human-gated review loop | Doc 1 | ⚖ (post-eval) | Open |

## D. Product/Extraction (from demo wave; residual + new)

| ID | Item | Source | Class | Status |
|---|---|---|---|---|
| D-01 | Contract: `trip_duration` field (schema + extractor + frontend) | DEMO-02 §9 | ⚖ then 🛠 | Open |
| D-02 | Contract: `flights_inclusiveness` ambiguity tri-state | DEMO-02 §9 | ⚖ then 🛠 | Open |
| D-03 | Contract: country-vs-city multi-destination model (+ semantics: semi_open vs definite for committed sets) | DEMO-02 §7/§9 | ⚖ then 🛠 | Open |
| D-04 | GF-01…GF-04 fixes (salutation/colon/labels) — verify interplay with new city-set pass | Gemini chronicle §7 | 🔬 (probe) | Open |
| D-05 |硬 constraint false positives ("idea of the name" in hard_constraints) — negation handling | DEMO-02 §9 Q7 | 🛠 | Open |
| D-06 | Season regex edge: multi-word canonical names in `_is_origin_candidate` | reviewer P3 nit | 🛠 (tiny) | Open |
| D-07 | Banner visual confirmation (IMP-01 residue; 2-min manual) | IMP-01 handoff | 📝 (manual) | Open |
| D-08 | Sibling sample panels (MemoryArchitectPanel, CrisisEvacuationPanel, MemorySettingsTab) need sample treatment | P2-6 / GM-wave | 🛠 | **Closed locally 2026-09-04** — sample/preview/not-dispatched states and 21 focused frontend assertions |
| D-09 | `?repair=<field>` deep-link + focus/auto-open (machinery exists at IntakePanel.tsx:1032, :1231-1237) | P2-7 / DEMO-06 | 🛠 | **Closed locally 2026-09-04** — canonical resolver, async hydration, route updates, scroll anchor, focus, and query cleanup verified |
| D-10 | VCC fetch: revert `127.0.0.1:8000` hardcode → BFF-relative + proxy rewrite | GF-05/PT-07 | 🛠 | **Closed 2026-09-02** — canonical BFF-relative `/api/v1/settlement/vcc/issue` path and route-map proxy are verified in-tree |

## E. Security follow-ups (Gemini wave, non-token)

| ID | Item | Source | Class | Status |
|---|---|---|---|---|
| F-01 | Stripe fake verify (dup of S-04 — kept for source traceability) | GM-03 | 🛠 | Open |
| F-02 | HMAC proposal tokens: hardcoded default secret + bypass + guess-loop (dup of S-01…S-03) | GM-04 | 🛠 | Open |
| F-03 | "Live" copy strings: GDSSandboxPanel, "transmitted to U.S. Embassy", VCC "issued", "ACCEPTED BY SUPPLIER" (React array), "18m hold" vs 145s code | REC-1 | 🛠 (copy) | Open |
| F-04 | Commit split: land hardening stack (A) separately from simulator expansion (B) | GM-01 | ⚖ then 🛠 | Open |
| F-05 | Dockerfiles + deploy posture: workers=1 constraint vs PT-08 idempotency seam; Dockerfile security review | Gemini wave | 🔬 | Open |

## F. Record & Process

| ID | Item | Source | Class | Status |
|---|---|---|---|---|
| R-01 | Chronicle + 16 case studies: simulator-caveat annotations | REC-1 | 📝 | Open |
| R-02 | MEMORY.md rewrite (business-model contradiction) + falsified-baseline caveats | G-13 | 📝 | Open (needs ⚖ business-model confirm) |
| R-03 | RAG doc rewrite to reality (hash-vector ≠ dense; substring ≠ graph) | G-04 | 📝 | Open |
| R-04 | Seasonal campaigns doc (built, zero docs) | G-14 | 📝 | Open |
| R-05 | Agent runtime doc (= C-05) | Doc 1 | 📝 | Open |
| R-06 | ADR consolidation (19 unnumbered; 003–005 missing); backlog consolidation (3 registers → 1); F-ID allocation | G-15 | 🛠 (scripted) | Open |
| R-07 | Personas adoption into `Docs/personas/` (6 applied + travel stack) | G-17 | 📝 | Partial (12 Gemini personas exist; add audit set) |
| R-08 | INDEX the 08-31/09-02 cluster (partially done); idea-pad statuses stale | G-13/audit | 📝 | Open |
| R-09 | Signup posture: email verification + "WORK EMAIL" framing | DEC-01 | ⚖ | Open |
| R-10 | Business model record (platform-led vs white-label) | Doc 3 | ⚖ | Open |

## G. Closed this cycle (for the record — no action)

DEMO-01 (IMP-01: ESCALATE persists leads, ADR + 2 review cycles APPROVE) ✅ · DEMO-02 (IMP-02 colloquial extraction) ✅ · DEMO-03 party warnings ✅ · DEMO-04 (IMP-03 sample-profile honesty) ✅ · DEMO-05 (IMP-05 repair navigation) ✅ · DEMO-06 copy (IMP-06) ✅ · DEMO-07 (IMP-07 gate fixtures + revert-proof) ✅ · GF-06/07/08 (A-14/A-21/0.4 closures) ✅ · S-13/S-14 ✅ · /inbox crash = dev-noise watch-item ✅

---

## Summary counts

| Class | Count | Notes |
|---|---|---|
| ✅ Done | 12 | All evidence-cited in handoffs |
| 🛠 Implement | 27 | Security (S-01…S-11) first; then eval (E-01…E-04); then record |
| 🔬 Explore | 9 | E-06/07, C-02…C-04, D-04, E-10/11, F-05 |
| ⚖ Decide | 8 | C-01 final, C-02, C-03, C-04, D-01…D-03, R-09/R-10, F-04 split |
| 📝 Record | 9 | R-01…R-08, D-07 |

**Recommended execution order:** (1) S-01…S-04 + S-05/S-06/S-07 hotfixes [~2 days] → (2) E-01…E-05 honest-eval core [~3.5–6.5 days] → (3) F-04 commit split + C-01 labeling + R-01 annotations [~1 day] → (4) record consolidation R-02…R-08 [~1–2 days] → (5) explore lanes (C-03, C-04, D-01…D-03) after eval ground truth exists.

---

## POST-WAVE REFRESH (2026-09-03) — state after the 27-item IMPLEMENT wave

All Section-A/B/C IMPLEMENT items shipped (see `SECURITY_HONESTY_WAVE_HANDOFF_2026-09-02.md`). This refresh supersedes the counts above: **39 DONE · 12 EXPLORE · 10 IMPLEMENT (new/residual) · 10 DECIDE · 8 RECORD.**

### New findings surfaced by the wave itself (implicit → explicit)

| ID | Item | Source | Class |
|---|---|---|---|
| N-01 | 13 drifting scenarios in the new live scenario lane (composite 0.5667) — each is a candidate extraction/decision defect; triage individually, flip lane to gating after | E-02 outcome | 🔬 (triage) → 🛠 |
| N-02 | Extraction fixtures (50) carry no `raw_input` (document-vision targets) — author runnable content so the lane flips to live grading | E-01 outcome | 🛠 |
| N-03 | Pipeline fixtures (7) expect document/agent/trip-status contracts with no deterministic producer — build producer or re-scope lane | E-01 outcome | 🛠 |
| N-04 | YieldArbitragePanel ↔ `/api/v1/yield*` contract mismatch — route-map intentionally unmapped (GM-06); align backend or panel | frontend batch | 🛠 |
| N-05 | Demo proposal serves any valid signed token regardless of trip_id (`public_proposals.py:361-431`) — pre-existing fabrication surface; fold into C-01 honesty follow-ups | review P3-6 | 🛠 |
| N-06 | Idempotency SQL backend: live-DB integration run needed (JSONB variant, true cross-process INSERT race) — module docstring marks the seam | PT-08 | 🔬 (integration) |
| N-07 | Proposal revocations: multi-replica boundary — shared volume or Postgres promotion before replicas | PT-05 note | 🛠 (deploy) |
| N-08 | Frontend vitest flake under machine contention (66s vs 17s wall, unreproducible on retry) — longer `waitFor` timeouts for CI | review P3-5 | 🛠 (tiny) |
| N-09 | GF-01…04 fixes (salutation/colon/labels) never probed for interplay with the new city-set pass | review follow-up | 🔬 (probe) |
| N-10 | MemorySettingsTab has no backend persistence (copy now says so honestly) — decide build-vs-scote | Gemini wave | ⚖ |
| N-11 | `GDSSandboxPanel.tsx:91` booking POST payload still carries `'Alex Morgan'` (never rendered; rename optional) | frontend batch | 🛠 (tiny) |
| N-12 | Register rows marked "in-flight" during the wave (S-08/S-10/PT-08 partial closures) — verify live tree and close them | E-05 note | 📝 |

### Remaining pre-existing items (unchanged)

- 🔬 EXPLORE: E-06 trajectory eval · E-07 production shadow-eval + calibrated judge · E-10 warnings-assertable gate format · E-11 adversarial corpus lane · C-02 wire-or-archive dossiers (hybrid engine, suitability Tier-3, ghost concierge, zero-caller modules) · C-03 real router design (eval ground truth now exists) · C-04 SLM benchmark · D-04 GF-fix interplay probe (= N-09) · F-05 Dockerfile security review · N-06
- ⚖ DECIDE: C-01 wire-or-archive (labels done) · C-02 outcomes · C-03 router ratification · C-04 posture · D-01 trip_duration · D-02 flights_inclusiveness · D-03 country-vs-city · R-09 signup posture · R-10 business model · F-04 commit split authorization · N-10
- 📝 RECORD: R-01 chronicle/case-study simulator caveats (annotations on Docs, not done by frontend batch) · R-02 MEMORY.md rewrite (needs R-10) · R-03 RAG doc rewrite · R-04 seasonal campaigns doc · R-05 agent-runtime doc · R-06 ADR/backlog consolidation · R-07 audit-personas adoption into Docs/personas/ · R-08 idea-pad/INDEX stale statuses · D-07 banner visual check · N-12

### Recommended order (updated)

1. N-01 scenario triage (the eval lane is live — act on what it found) + N-02/N-03 fixture-content work
2. Security residue: N-05, N-07, N-11 + register N-12 closure
3. RECORD batch R-01…R-05 (cheap, high trust-value)
4. DECIDE batch with Pranay (C-01…C-04, D-01…03, R-09/10, F-04)
5. EXPLORE lanes that unblock the next build wave (C-02 dossier → wire/archive; E-06/07 production eval)

---

## EXPLORATION RESULTS (2026-09-02/03) — the 12 EXPLORE items are now researched & documented

Companion docs: `N01_SCENARIO_TRIAGE` · `EVAL_EVOLUTION_DESIGN_E06_E07_E10` · `E11_ADVERSARIAL_CORPUS_DESIGN` + `data/fixtures/adversarial/adversarial_seed_v1.json` (40 records) · `C02_WIRE_OR_ARCHIVE_DOSSIERS` · `C03_ROUTER_DESIGN` · `C04_SLM_BENCHMARK_PROTOCOL` · `MISC_PROBES_N06_N09_D04_F05`.

### New findings the explorations surfaced (all probe/code-verified)

| ID | Finding | Sev | Class |
|---|---|---|---|
| X-01 | Prompt-injection hijack CONFIRMED in deterministic layer: injected "budget 999999" overrides real budget; "Cancun" enters candidates (extractors.py:1168-1194) — poison forwards to any downstream LLM | P0-adj | 🛠 |
| X-02 | `party_size=2027`: `_PEOPLE_RE` reads "June 2027\n- Travelers" as headcount in ordinary bullet notes (extractors.py:272-275) | P1 | 🛠 |
| X-03 | Verb-less notes ("Bali in June 2027") demote destination into `origin_city`; past/far-future years unchecked (extractors.py:511-609) | P1 | 🛠 |
| X-04 | Decision escalation gap: high-priority conflicts (party/origin) don't escalate (only "critical" does) — ASK decisions are dead intent; silent wrong-count quotes | P1 | 🛠 |
| X-05 | MVB double-counts budget (requires BOTH budget_raw_text AND budget_min) — demotes CRM budgets to draft; conf<0.6 gate is dead code | P2 | 🛠 |
| X-06 | Blank-value fills hard blockers (only None rejected) | P2 | 🛠 |
| X-07 | Season-homonym leak ("…kyoto next spring" → Spring TX city); trailing time truncates city sets; "Let's do japan" → ["Let"] | P2 | 🛠 |
| X-08 | 2 hard crashes on malformed structured_json travelers (extractors.py:2718-2719); fragment-cities "Ba"/"Bal" at definite confidence; raw SQL strings stored as destination_candidates on structured path | P1→P2 | 🛠 |
| X-09 | H-01: hybrid decision engine now wired default-ON in prod while CI forces OFF — D6 lane grades a system prod doesn't run (deep map was stale; also: agent registry is 19 not 18) | P1 (record) | 📝/⚖ |
| X-10 | `checker_model` setting stored + UI-editable but consumed by nothing at runtime | P2 | 🛠/⚖ |
| X-11 | Idempotency mark_completed CAS gap CONFIRMED live (5/5 rounds exactly-one-winner on acquire; stale-owner overwrite possible on mark) — compare-and-set on created_at | P2 | 🛠 |
| X-12 | F-05 HIGH: `uv run` at container start without uv.lock; `.env*` in build context (no .dockerignore entries); 666MB `data/` baked into image; root user; unpinned deps | P1 (deploy) | 🛠 |
| X-13 | Scenario corpus: 6 fixture errors (corpus corrections proposed; validated composite ≥0.93 after the 4 fixes) | P2 (record) | 🛠 |
| X-14 | Retention-enforcer module = compliance-shaped shadow (worst orphan class) | P2 | ⚖ |

### Fix order validated by N-01 (counterfactual: composite ≥0.93)

1. X-04 escalation gap → 2. X-05 budget OR-group → 3. X-06 blank-value guard → 4. X-13 corpus corrections → flip scenario lane to gating. Then X-01/X-02/X-03 extraction defects (adversarial corpus lane protects the fixes).

---

## FINAL CONSOLIDATION (2026-09-03, post-EXPLORE wave)

**51 items DONE to date** (12 demo cycle + 27 IMPLEMENT wave + 12 EXPLORE research). Every remaining task below is classified from the exploration results (X-series + N-series + carried items). The EXPLORE class is now largely empty — the research wave converted it into concrete implementation targets.

### 🛠 IMPLEMENT — remaining (22, in validated execution order)

**Group 1 — Decision-layer fixes (N-01 validated order; flips scenario lane to gating, composite ≥0.93):**
| 1a | X-04 escalation gap: high-priority conflicts must escalate (decision.py:372-373 vs :2034-2040) |
| 1b | X-05 budget MVB OR-group (budget_raw_text OR budget_min; dead conf<0.6 gate) |
| 1c | X-06 blank-value guard (field_fills_blocker rejects ""/[] not just None) |
| 1d | X-13 scenario corpus corrections (6 fixture errors) |

**Group 2 — Extraction defects (adversarial-corpus + probe confirmed):**
| 2a | X-01 prompt-injection sanitization (injected budget/destination overrides) |
| 2b | X-02 party_size=2027 (_PEOPLE_RE year capture) |
| 2c | X-03 verb-less destination→origin demotion + year bounds |
| 2d | X-07 season-homonym leak + trailing-time set truncation + "Let's do japan"→["Let"] |
| 2e | X-08 malformed structured_json crashes + fragment cities + raw SQL in candidates |

**Group 3 — Infra/deploy security:**
| 3a | X-12 Docker HIGHs: uv.lock at build, .dockerignore .env*, 666MB data/, root user, pinned deps |
| 3b | X-11 idempotency mark CAS (compare-and-set on created_at; live-verified gap) |
| 3c | N-07 revocations multi-replica boundary (shared volume / Postgres) |

**Group 4 — Product/records residue:**
| 4a | X-10 checker_model: wire or remove |
| 4b | N-02 extraction fixtures raw_input authoring (50) |
| 4c | N-03 pipeline fixtures deterministic producer (7) |
| 4d | N-04 YieldArbitrage contract alignment |
| 4e | N-05 demo-proposal token surface (fold into C-01) |
| 4f | N-08 vitest timeouts · N-11 GDS payload rename · D-07 banner visual check · N-12 close in-flight register rows |
| 4g | E-08 red-team regression corpus (encode the 22 adversarial known-defects) |

### 🔬 EXPLORE — residual (2)

- Benchmark execution analysis (C-04 protocol is designed; running it + analyzing = the next research artifact)
- C-02 follow-through: the wire-or-archive *implementation* ADRs per ratified disposition (design done)

### ⚖ DECIDE — 10 (unchanged, all recommendations on file)

C-01 wire-or-archive Frontier/Council · C-02 per-module outcomes · C-03 router ratification · C-04 SLM posture · D-01 trip_duration · D-02 flights_inclusiveness · D-03 country-vs-city (D-04 research recommends option b) · R-09 signup posture · R-10 business model · F-04 commit split authorization

### 📝 RECORD — 8 (unchanged)

R-01 chronicle/case-study caveats · R-02 MEMORY.md rewrite (needs R-10) · R-03 RAG doc rewrite · R-04 seasonal doc · R-05 agent-runtime doc · R-06 ADR/backlog consolidation · R-07 personas adoption · R-08 idea-pad statuses (+ D-07 banner check, N-12 register rows)

## CURRENT RETRY RECONCILIATION (2026-09-04)

This addendum supersedes stale counts or statuses above without deleting the
historical inventory. It is the current implementation/evidence overlay for
the same explicit and implicit task universe.

### Bounded slices completed in this retry

- **Financial settlement/VCC truth boundary:** FX quote, commission split, and
  payment schedules return deterministic `COMPUTED_PREVIEW` metadata; VCC
  issuance is an explicit `PREVIEW_ONLY`/`NOT_ISSUED` no-op with no card,
  credential, or external reference. Frontend uses BFF-relative calls and
  labels schedules as examples. Backend focused suite: **9 passed**;
  simulated-panel suite: **11 passed**.
- **IROPS recovery truth boundary:** the workbench surface is explicitly an
  `IROPS Recovery Plan Preview`; local fallback is review-only and does not
  claim provider execution, compensation, payment, or ticketing. Focused
  panel suite: **3 passed**.
- **A-17 onboarding semantics:** the implementation is `WelcomeCard`, not a
  modal; both responsive branches expose a labelled `role="region"`, retain
  the `WelcomeModal` compatibility export, and preserve native keyboard
  controls. The authoritative finding remains **PARTIAL**: local semantic
  contract is corrected and desktop/390×844 local renders were inspected after
  live health checks, while computed accessibility-tree, screen-reader,
  focus-order, contrast, and hosted/device evidence remain open. Focused
  component suite: **6 passed**. See
  `Docs/review/A17_BROWSER_RENDER_EVIDENCE_2026-09-04.md`.
- **X-04 decision escalation:** the historical N-01 reproduction is confirmed
  against `HEAD` (Phase 7 admitted only `priority == "critical"`, so high-
  priority party/origin ASK actions fell through to `PROCEED_INTERNAL_DRAFT`).
  The shared tree now contains the explicit `party_conflict`/
  `origin_conflict` escalation set, field-targeted follow-ups, and STOP-over-ASK
  precedence; focused party/origin regressions are present and the 30-fixture
  corpus is 30/30. **Current status: CLOSED locally; independent-producer,
  holdout, and promotion evidence remain open.** See
  `Docs/review/DECISION_CORRECTNESS_X04_X05_X06_X13_2026-09-04.md`.
- **N-09/GF-01/GF-03 extraction probe:** salutation, bounded honorific,
  `Budget: Around`, parenthetical city-set, explicit-label precedence, and
  trailing-season cases are locally verified; the focused tranche passes
  **274 tests**. GF-01 and GF-03 are closed at this deterministic tier. The
  repeated-currency/shared-suffix range follow-up is now implemented and
  covered by a four-test regression; mixed-currency input abstains. Country-
  vs-city containment remains separate design work.
- **X-10 checker-model audit:** `checker_model` is a compatibility setting
  that round-trips through agency settings/API/UI but is not consumed by the
  deterministic checker. The reviewed disposition is **DEFER WIRE; RETAIN
  COMPATIBILITY; CORRECT CLAIMS BEFORE ACTIVATION**. The reserved contract is
  covered by 53 focused settings/gate tests; provider/model routing, advisory
  semantics, consent/spend/fallback controls, telemetry, holdout evaluation,
  and rollback remain explicit future gates. See
  `Docs/review/X10_CHECKER_MODEL_WIRE_OR_REMOVE_2026-09-04.md`.
- **X-09 hybrid configuration parity:** production-facing manifests and CI now
  declare `USE_HYBRID_DECISION_ENGINE=1`; D6 preserves explicit caller mode,
  restores the environment, and records effective configuration plus
  deterministic authority axes. The focused parity tranche passes 59 tests;
  hybrid model quality, provider permission, and owner ratification remain
  open. See `Docs/review/X09_HYBRID_CONFIGURATION_RECONCILIATION_2026-09-04.md`.
- **X-12/F-05 container hardening:** root and nested build contexts exclude
  secrets and runtime state, production images pin verified digests and run as
  non-root users, and Postgres/Redis are internal-only in compose. Six static
  tests, lock validation, digest revalidation, and compose parsing pass;
  actual image build, scanner, runtime, and hosted deployment proof remain
  open. See `Docs/review/CONTAINER_HARDENING_X12_F05_2026-09-04.md`.
- **D-01/D-02/D-03 contract probes:** executable probes now establish that
  duration is not a canonical typed fact, flight inclusiveness is absent, and
  country/city values share one untyped destination list. The evidence and
  post-ratification implementation package are in
  `Docs/review/PRODUCT_CONTRACT_DECISIONS_D01_D03_2026-09-04.md`; 280 focused
  tests pass. Product-owner ratification is required before schema/API/UI
  changes.
- **D-10 VCC BFF routing reconciliation:** the historical hardcoded-localhost
  defect is already closed in the canonical register. `FinancialSettlementPanel`
  uses the BFF-relative `/api/v1/settlement/vcc/issue` path and
  `route-map.ts` maps it to the backend route; no new code change is needed.
  The prior “Open” inventory row was stale and is superseded by this overlay.
- **D-08/D-09 frontend follow-through:** sibling memory/crisis surfaces now
  expose explicit sample/preview boundaries, and the canonical `?repair=`
  resolver opens, anchors, focuses, and cleans repair editors across hydration
  and route updates. Focused frontend coverage is **21 passed**. Hosted,
  screen-reader, contrast, and provider evidence remain separate gates. See
  `Docs/review/D08_D09_FRONTEND_TRUTH_2026-09-04.md`.
- **N-02/N-03 independent-producer probes:** three executable shadow tests now
  prove that the 50 document fixtures have no raw artifact references or
  hashes, live extraction/pipeline collectors are empty, and expected
  document/stage labels are not being passed off as actual outputs. N-02/N-03
  remain open until owner-ratified artifacts, canonical stage schemas,
  independent producers, and private holdouts exist. See
  `Docs/review/INDEPENDENT_EVAL_PRODUCERS_N02_N03_2026-09-04.md`.
- **X-14 retention-enforcer disposition:** the module is retained as a design
  prototype, its GDPR/DPDP/cryptographic-erasure claims are demoted, and its
  machine-readable status is explicitly `shadow` with external erasure
  disabled. Ten focused tests pass. Canonical cross-store erasure remains an
  F-05 production task requiring durable inventory, policy versions, legal
  holds, lifecycle anchors, provider purge, reconciliation, audit, RLS, and
  recovery. See
  `Docs/review/X14_RETENTION_ENFORCER_WIRE_OR_ARCHIVE_2026-09-04.md`.

### Current verification receipt

- Backend: **3,718 passed, 44 skipped, 0 failed** (`scripts/run_backend_tests.sh`).
- Current combined retry tranche (currency ranges, N-09/GF extraction,
  extraction safety/fixes, and X-10 settings/gate contracts): **331 passed**.
- Converged implementation tranche (container hardening, X-09 parity,
  D-01/D-02/D-03 probes, N-02/N-03 shadow producers, X-14 retention truth,
  sandbox-card formatting, D6 snapshot, and extraction regressions): **369
  passed**.
- A-06/A-20 drift-gate disposition: generated API type regeneration is wired
  into CI; Alembic drift is documented and remains open pending safe schema
  reconciliation (the local post-upgrade check found substantive deltas).
- Frontend: **174 files / 1,311 tests passed** (`npm test -- --run`).
- Frontend lint: **0 errors / 0 warnings**; typecheck: **pass**; production
  build: **pass**. Build-time dynamic-route diagnostics are expected for
  request-cookie/URL access and did not fail the build.
- Findings lifecycle: **183 rows — 108 open, 69 closed, 6 deferred; 0
  warnings**.
- Full-repository Ruff: **pass**. `git diff --check` still reports only the
  two preserved owner-controlled residues documented in the execution status.
- A1-1 custody: final24 ledger validates **496 live paths** (**497 porcelain
  rows including the ledger**); all remain preserved pending semantic
  ownership and explicit Git release authorization.

### Complete remaining task universe (current truth)

The canonical register remains the ID-level authority. Remaining work is
classified as follows:

- **Architecture, security, contracts, and operations:** R-09, R-10, R-12,
  R-13, R-14, R-16; A-02–A-12 (excluding closed rows), A-15–A-17, A-20;
  F-01–F-17, F-19, F-21–F-26; NEW-01–NEW-07.
- **Agentic/evaluation/product truth:** G-01–G-06, G-12–G-17 (G-16 is
  explicitly deferred), GM-01, GM-02, GM-05, GM-06, GM-08, GM-09, PT-08,
  GF-04, REC-1.
- **Research/design candidates:** EX-01, EX-02, EX-03, EX-05, EX-07–EX-10,
  EX-11–EX-14. NG-01–NG-04 remain explicit no-go/deferred items until their
  prerequisites exist.
- **Validated implementation targets from the exploration wave:** X-01–X-09,
  X-11, and X-13 are locally implemented and regression-verified (including
  the extraction-safety, decision-correctness, and hybrid-parity suites);
  X-12 has source hardening but still needs runtime/image/deployment proof;
  X-14 has an honest shadow disposition while the F-05 canonical wire remains
  open. X-10 remains deliberately deferred (wire-or-remove). Independent
  producers, private holdouts, provider, hosted, and release-promotion proof
  remain separate gates.

X-04 is no longer a remaining implementation target: it is locally closed by
the current decision implementation and regression/evaluation evidence above.
The historical X-04 row and ordering are retained for audit lineage; do not
re-open it unless an independent producer, holdout, or promotion falsifier
fails.

### Alignment rule applied to every task

A task is **first-principles, long-term, and doctrine aligned** only when its
canonical path has a falsifiable contract, honest reality metadata, an owner,
durable state and idempotency semantics, matching evidence tier, and a
retirement or rollback path. Anything lacking one of those is labelled
partial, deferred, or no-go—not promoted by local green tests alone.

## KDD HYBRID EVAL LANE — COMMISSIONING (2026-09-11)

Owner-ratified sequencing: ratification #1 (hybrid flag, ADR row A1 option b)
advances via an evidence experiment before any posture change. Protocol and
results: `Docs/exploration/HYBRID_KDD_EXPERIMENT_2026-09-11.md`; harness:
`scripts/run_hybrid_kdd_experiment.py`.

**Commissioning outcome (this date):**

- Three latent engine defects found and fixed while commissioning — broken
  `from llm import …` (LLM path never reachable; `LLM_AVAILABLE` stuck False),
  `UnboundLocalError` in the `_call_llm` failure handler, and the lru-cached
  env flag (harness now calls `_reset_hybrid_engine()` per arm). All are
  in-blast-radius fixes for the experiment itself; 39 hybrid tests green.
- Cache isolation added (per-model run-scoped `cache_<model>/`), making the
  cold/warm passes measurement-valid.
- Full dry run executed: 175 rows (35 records × 5 arms). Arm A baseline is
  valid (6 risk flags on 6/35 records). Arm B is 401-contaminated — the
  `.env` OpenAI key (sk-proj-…VeQA) is revoked/expired: 124/124 LLM attempts
  rejected. Incidentally proves graceful failover (defaults, guards record
  failures, no crash).
- **Blocker:** valid `OPENAI_API_KEY` required for the model-comparison arms
  (B1 gpt-4o-mini, B2 gpt-4o). One command re-runs the full matrix once the
  key is in `.env`. Est. cost of the full matrix: ≈₹2–8.

**Status:** arm A DONE (valid baseline). Arm B BLOCKED on credentials. The
three engine fixes are regression-tested and lint-clean; full-suite receipt
recorded in this file's verification section when the background run lands.

**Verification receipt (2026-09-11, post-commissioning):** full backend suite
**4,319 passed / 22 skipped / 0 failed**; Ruff clean on all touched files
(`src/decision/hybrid_engine.py`, `scripts/run_hybrid_kdd_experiment.py`,
`tools/validation/hybrid_engine_validator.py`); hybrid validator tool now
runs standalone (dual sys.path fix: repo root for `src.*` engine imports +
`src/` for the tool's `intake.*` style).

**KDD full matrix VALID (2026-09-11, later same day):** key rotated; 175-row
run with 16 real LLM escalations/arm. Results in KDD doc §6.4. Headlines:
hybrid is strictly additive (A=6 flags → B=32, all added visa_timeline_risk,
zero removed); gpt-4o-mini ≡ gpt-4o coverage at 19× lower cost (₹0.11 vs
₹2.10/run) → mini recommended; warm cache 100% hit at ₹0; **new finding: LLM
path lacks abstention** — spurious high-severity visa flag on a
destination-less packet, propagated by cache to 7 identical-context records
(cache amplifies precision defects). ADR A1 posture: stay OFF-by-default;
opt-in only after abstention guard + lane re-run.

**KDD wave 2 COMPLETE (2026-09-11): model ladder (19 models, 2022→2026) +
architecture patterns.** Client made model-aware (gpt-5/6/o-series need
max_completion_tokens + no temperature; legacy gpt-4 no json_mode) + PRICING
extended to 24 models. Headlines: all models strictly additive vs arm A;
aggressiveness varies 12× by model (4-turbo +3 vs nanos +35) with no
monotonic era-quality signal; flagship models (6-astra ₹11.45/run) show no
advantage over nano-class (₹0.09–0.28) → knee at nano/mini tier; warm cache
₹0 at every tier; spurious dest-less visa flag emitted by EVERY 2024+ model
(abstention is an architecture problem, not a model problem). Pattern
verdicts: **guard (LLM+fact-gate) = free + surgical = recommended**; vote
halves escalation at 2× cost; critic is model-dependent (terra rejected
14/16 mini escalations, approved 20/22 of luna's) — not a reliable quality
gate; llm_first disqualified (101–109 flag flood; rules are load-bearing).
New: run-to-run LLM nondeterminism (+26 vs +15 same corpus) → multi-seed
protocol required. Full results KDD doc §7.4; follow-ups §7.5 (engine-side
guard, ground-truth labels, promptfoo CI port — promptfoo 0.123.0 available).

**KDD §7.5 remediation LANDED (2026-09-11):** two-layer fix in production code
— (1) engine abstention gate (`_FACT_REQUIREMENTS`: visa escalation requires
destination fact; skips LLM call entirely when absent) and (2) default-source
decisions no longer emitted as risk flags (an unassessed "unable to assess"
medium is not evidence; conversion skips `source=="default"`). Live
confirmation: spurious dest-less visa flags 11→0, total 32→19, escalations all
destination-bearing; hybrid semantics now strictly additive over arm A.
Harness gained `--runs N` multi-seed protocol. Promptfoo CI port shipped:
`tools/generate_promptfoo_config.py` → 35-case lane, **35/35 pass in 1s at
zero cost** (deterministic degradation without creds; documented venv
requirement). 3 new engine/decision tests; related suites 146 green. Open
from §7.5: ground-truth visa labels (E-07 judge), Gemini/local arms
(credential-blocked).

**Local-tier ladder DONE + pruned (2026-09-12, disk-pressure protocol):**
8 local models test→graded→deleted per-model. **llama3.2:3b = local champion
(F1 0.737, P=1.0, 2.0GB, 2.5s/call — recommended local default); gemma3:12b
kept as 16GB rep (0.629); qwen2.5vl:7b kept (vision-feature-coupled); DELETED
gemma3:4b, aya-expanse:8b, qwen2.5:7b/3b, mistral:7b (F1 0.34–0.40) → ~15GB
freed, disk 421MB→31Gi.** Bigger ≠ better locally (7B/8B underperform the 3B
while 8–9× slower — repeats the API-tier flagship pattern). P=1.000 everywhere:
engine gate makes free local models precision-clean. Ops: background shells
silently fail ollama pulls (foreground required); harness `--tag` per model is
mandatory (the "w"-mode JSONL overwrote earlier arms once). Tier landscape
(browser-WASM/WebGPU/8GB/16GB/MLX) + untested 2026-gen one-command pulls
documented in KDD §9.3.

**Multi-vendor serving experiment DESIGNED (2026-09-12, pre-experiment per
owner):** `Docs/exploration/MULTI_VENDOR_SERVING_EXPERIMENT_DESIGN_2026-09-12.md`.
Landscape researched: OpenRouter (7 routers + :nitro/:floor/:free variants,
BYOK, ZDR), Groq (gpt-oss-20b ~1000 t/s, $0.075/$0.30/M — the exact model
we couldn't fit locally), Cerebras (2000+ t/s, $5 free, OpenAI-compat), HF
Inference Providers (router.huggingface.co/v1, :fastest/:cheapest policies,
17 partners, works with the HF token we already hold), ollama-cloud (already
in our store). xAI to-verify. Design: same-weights matrix across venues
(Q10 quantization-drift on F1, Q11 latency frontier, Q12 cost/run, Q13
router quality vs manual choice, Q14 privacy), reuses corpus+labels+grader+
sheet; 4 phases; Phase 1 = HF-router only, near-zero cost, no new keys.
Owner decisions requested: keys (OpenRouter/Groq/Cerebras), ~₹40–80 budget
(or Phase-1-only ₹10–20), 14GB disk window for the local gpt-oss:20b leg.

**Phase 1 (HF router) EXECUTED (2026-09-12):** keychain HF token discovered
working; `hf-router/` provider added to harness; 6 arms (gpt-oss-20b,
Qwen3-4B-2507, Llama-3.1-8B × :fastest/:cheapest). **Llama-3.1-8B:fastest F1
0.800 @ 1.2s/call — beats local champion on both axes**; :fastest dominated
:cheapest 3/3 (latency + directional quality); same-weights F1 drift up to
0.171 across venues (single-pass caveat, multi-seed needed); hosted
gpt-oss-20b confirms under-flagging is a model trait (0.286 even at 792ms);
P=1.000 and 15-escalation engagement stable on all arms. Harness bug fixed:
slash-containing arm ids broke prompt-archive paths (finally-block masked
successful results). Spend ≈ a few cents. Comparison sheet now 39 rows with
venue arms. Phases 2–4 (OpenRouter, multi-seed confirmation, Cerebras/xAI)
ready on request. Design doc §6 = execution record.

**Phase 1b (large models hosted) EXECUTED (2026-09-12):** 7 arms 20B→235B on
HF router per owner's "don't limit to small models hosted" directive.
**Headline: scale does NOT rescue the lane** — best large = gemma-3-27b 0.629
< hosted Llama-3.1-8B 0.800 < nano tier 0.909; gpt-oss-120b 0.286 @ 734ms;
Qwen3-235B 0.452 w/ worst severity calibration (0.14). Calibration is a model
property, not scale. Production hardening landed: `_recover_json_object()`
multi-vendor JSON repair in openai_client (DeepSeek doubled-brace; 6 unit
tests) + 4096-token headroom for reasoning models. Qwen3.5-9B hosted =
documented failed-run (empty content client-side-unrecoverable). One shell-
quoting pass invalidated + re-run (zsh `$m:fastest` expansion). Sheet now 46
rows. Recommendation stack updated (design doc §6.1).

**Extreme-case reasoning tier SIMULATED + multi-seed confirmation (2026-09-12):**
Owner asked whether reasoning models can serve in extreme cases despite poor
default performance. Simulated second-opinion-on-negatives architecture
(tier-1 llama-8B:fastest; tier-2 reviews only tier-1 lows, 19/35 records):
gpt-oss-20b and Qwen3-235B recover +1 TP each (F1 0.800→0.829, severity
correct); others +0. **Structural insight: conservative reasoning models are
ideal tier-2 validators — they never override (P stays 1.000) and only
augment. Worst standalone arm became best second opinion.** Honest verdict:
+0.029 is within the 3-seed variance band (tier-1 confirmed at F1
0.829/0.769/0.737 ±0.05, P=1.000 + 15 escalations every pass) → not
statistically justified on this corpus; kept as a policy knob for a
reasoning-bound corpus. Multi-seed receipt: records_hf1_llama8b_multi.jsonl.

**Local store fully pruned (2026-09-12, final):** all lane-tested local
models deleted after grading — llama3.2:3b (champion), gemma3:12b, and
qwen2.5vl:7b — following the owner directive; grades + one-command re-pull
recipes preserved in the comparison sheet. Verified zero production code
references before deletion. Store now: deepseek-ocr + nomic-embed only
(untested, non-lane); ~16GB freed this step. All serving comparisons now run
hosted; local re-pull is a documented one-command path per model.

## FINDINGS STATUS CORRECTION (2026-09-14)

FND-0273 and FND-0275 closed — both halves landed, tested, and live-verified
(scope guard + origin cue-guard + per-traveler binding + decision risk flags).
FND-0274 remains open: the L0 speaker-segment parser exists in
`src/intake/attribution.py` (used by `build_travelers`) but the MAIN
extraction path (`_extract_from_freeform`) still runs constraint and
preference patterns on the full concatenated text, so transcript fragments
can still appear in packet-level fields on multi-voice threads. The fix is
to wire segment-scoped extraction into `_extract_from_freeform` (run
constraints/preference patterns per speaker segment rather than on the raw
concatenation), which requires care to preserve group-level facts. Tracked
as the remaining FND-0274 implementation surface.
