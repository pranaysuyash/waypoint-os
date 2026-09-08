# Findings & Tasks Register — PER-0700 Persona Audit Companion (2026-09-06)

**Status:** companion addendum; NOT a second lifecycle authority
**Authority note:** per `Docs/review/FINDINGS_LIFECYCLE_2026-08-30.md` (2026-09-05 amendment), the canonical register is `Docs/review/FINDINGS_REGISTER_2026-08-31.md` (145 rows: 91 open / 53 closed / 1 deferred, parser-verified today). This document (a) adds the **new implicit findings** discovered by the PER-0700 audit as promotion-ready candidates, and (b) indexes the **explicit** documented findings without duplicating their status. Identity convention for new rows: `persona-audit-per0700-2026-09-06::PA-nn`. On adoption into the canonical register, rows should be re-keyed per the collision map and this file annotated.
**Parent audit:** [PERSONA_AUDIT_PER0700_AGENTIC_SYSTEMS_ARCHITECT_2026-09-06](PERSONA_AUDIT_PER0700_AGENTIC_SYSTEMS_ARCHITECT_2026-09-06.md) · **Plan:** [IMPLEMENTATION_PLAN_PER0700_2026-09-06](IMPLEMENTATION_PLAN_PER0700_2026-09-06.md)

Action classes: **IMPLEMENT** (code change) · **EXPLORE** (research + document before code) · **DECIDE** (owner ratification) · **RECORD** (documentation). Alignment columns: 1P = first-principles, LT = long-term, DOC = doctrine (§2 truth / §11 engineering / §12 AI-output / §13 claim reality) — ✅ aligned, 🟡 partial, ❌ violated.

---

## Part A — New implicit findings (PA-01…PA-37)

### A.1 P0 — act before anything else

| ID | Finding | Evidence | Class | 1P/LT/DOC | Fix direction (and what "best" adds) |
|---|---|---|---|---|---|
| PA-01 | Unauthenticated public route `/api/public/journey-graph/{trip_id}` returns a **fabricated confirmed itinerary** (minted PNRs, "Amadeus NDC"/"Blacklane"/"Belmond") when no stored graph exists; agency scoping swallowed via bare `except` — **cross-ref: corresponds to F-41 in the parallel 2026-09-06 drift addendum (`Docs/architecture/CODEBASE_FEATURES_FLOWS_LOOPS_MAP_DRIFT_2026-09-06.md`); independent double-discovery** | `spine_api/routers/journey_graph.py:118-237` (working tree); `spine_api/server.py:1468` | IMPLEMENT (block uncommitted commit until fixed) | ❌/❌/❌ §13 | Synthesize nothing: 404 or draft-labeled response when no real graph; require signed proposal token on the public route (minter already exists, `proposal_compiler.py:140-141`); wrap errors as 5xx not "no trip". Best: make "abstain-with-reason" a shared helper so every future public surface inherits fail-closed behavior. |
| PA-02 | Traveler proposal acceptance — the authorization artifact for the whole money path — is stored **only in process-local `_PROPOSAL_REGISTRY`**; `trip["proposal_accepted_at"]` (which the durable record reads) is never written by accept | `public_proposals.py:100,628-629,698-731`; fulfillment trusts it at `booking_fulfillment.py:81-86` | IMPLEMENT | ❌/❌/❌ §13 | Persist acceptance (timestamp, signer, token id, consent) on the trip + audit event atomically; fulfillment must verify against the durable record, not registry state. Best: acceptance becomes an append-only event consumed by fulfillment — the authorization ledger F-04 wants. |

### A.2 P1 — honesty/authority spine

| ID | Finding | Evidence | Class | 1P/LT/DOC | Fix direction |
|---|---|---|---|---|---|
| PA-03 | Serving-path determinism is **credential-accidental**: `USE_HYBRID_DECISION_ENGINE` defaults `"1"`; `fly.toml:29` + `docker-compose.yml:21` enable it; live LLM path taken whenever `GEMINI_API_KEY` exists | `src/intake/decision.py:37`; `decision.py:1213-1215,2225`; `hybrid_engine.py:594,629-631` | IMPLEMENT + RECORD (amend map honesty note + G-03 register row; DECIDE default) | 🟡/🟡/❌ §12 | Default `"0"` (or ratify "deterministic core + credential-gated enrichment" as the documented contract and pin it in `startup_assertions`). Best: startup log/warning that names the effective agency rung — one line, permanent clarity. |
| PA-04 | Production trip timeline is **structurally blind to decisions**: spine audit events fire only when `stage_callback is None`, and production always passes one; id-space mismatch (`packet_id` vs `trip_id`) | `orchestration.py:270-280,308-320,496-506`; `pipeline_execution_service.py:300`; `trip_observability.py:54` | IMPLEMENT | 🟡/🟡/🟡 §2 | Emit decision/escalation events on the production path into `AuditStore` keyed by trip_id (join run→trip at event time). Best: one canonical `emit_decision_event` used by both paths — kills the dual-store split at the root. |
| PA-05 | Fulfillment **self-asserts** `FULFILLED_CONFIRMED` from sandbox adapters; TripStore write failure swallowed; no read-back/version check; VCC issued before verification | `booking_fulfillment.py:96-181` (swallow `:150-151`) | IMPLEMENT | ❌/❌/❌ §13 | Verify-after-execute: re-read trip + version check before terminal status; fail loud on store failure; `TierMetadata` envelope (exists at `core/reality_tier.py`) on the whole response. Best: terminal status only after persistence confirmed — "environment-demonstrated completion" as a shared postcondition helper. |
| PA-06 | Price-lock "current rate" fabricated from first in-memory contract row w/ hardcoded fallbacks; re-lock **permanently writes it** as price-of-record; `expected_version` optional; no release/rollback | `price_lock.py:117-127,169-179,198-285` | IMPLEMENT | ❌/❌/❌ §13 | Abstain when no real rate source (preview metadata, no trip mutation); make version + idempotency required; add release/compensation path (F-01 rides this). Best: re-lock becomes proposal→validate→authorize→execute→verify with a compensating ledger entry per F-01's design. |
| PA-07 | No failure-class taxonomy; `stage_at_failure` not in ledger meta; recovery ladder class-blind (same 2×→escalate for tool outage vs verification failure vs state divergence) | `run_ledger.py:277-296`; `pipeline_execution_service.py:616-624`; `recovery_agent.py:245-249` | IMPLEMENT | ❌/🟡/🟡 §11 | Enumerate failure classes (model/tool/environment/state/memory/verification/authority) on the ledger record; route recovery per class (retry vs requeue vs DLQ vs human). Best: `run_state.py` gains a `failure_class` field consumed by recovery — turns "retry twice" into a recovery architecture. |
| PA-08 | Governance registry (`max_budget_impact` ≤$50k) and `AuthorityGateKeeper` dual-control enforced by **zero** execution paths | `registry.py:72-81` (sole ref `boundaries.py:134` catalog GET); `boundary_engine.py:230-317` | IMPLEMENT | ❌/❌/❌ §13 | Wire `evaluate_action_authority` + budget caps into fulfillment and payout as pre-execution gates. Best: one `authorize(action, context)` seam every consequential path must call — authority becomes a property, not a diagram. |
| PA-09 | Money-adjacent routers mounted unauthenticated: `subagent_payouts` (payout authorization, **no internal auth dep**), plus unauthed `negotiation`/`crisis_ops`/`distribution` (stateless/preview, lower severity) | `server.py:1470-1473`; `subagent_payouts.py:37` | IMPLEMENT | ❌/🟡/❌ §13 | Add `get_current_agency_id` internally to payouts; wrap preview routers in `_auth_or_skip` or an explicit public-allowlist rationale row. |
| PA-10 | `/metrics` claims Prometheus, returns static JSON — no counters, cost, latency | `server.py:2009-2012` | IMPLEMENT | 🟡/❌/🟡 | Real counters (run outcomes, loop health, usage-guard spend, queue depth) or rename endpoint. Best: exporter with run-outcome + failure-class + cost gauges — PA-07/PA-20 become observable. |
| PA-11 | Autoresearch loop grades hardcoded simulations and writes `{"accepted": true}` authoritative-looking lineage | `autoresearch_loop.py:71-108,120` | EXPLORE → IMPLEMENT | ❌/❌/❌ §2 | Either wire its `run_eval_suite` to the real D6 lanes (the honest producer exists) or mark lineage records `simulated: true`. Best: point composite scoring at live lanes — then the flywheel becomes real. |

### A.3 P2 — state, lifecycle, economics

| ID | Finding | Evidence | Class | Alignment | Fix direction |
|---|---|---|---|---|---|
| PA-12 | Run ledger unbounded: 18,987 dirs/648MB, O(N) full scans on list/status/sweep | `run_ledger.py:389,409-453` | IMPLEMENT | 🟡/❌/🟡 §11 | Retention policy (e.g., 30d + terminal-only compaction), index file or SQL projection. Best: ledger read-model in SQL (F-09 direction) with files as cold archive. |
| PA-13 | `POST /run`/reassess: fresh uuid4 per submission, no idempotency key, no per-trip in-flight lease → concurrent same-trip runs last-writer-wins | `server.py:1982+`; `trip_lifecycle_service.py:121-136` | IMPLEMENT | ❌/❌/🟡 §11 | Optional `Idempotency-Key` header + per-trip lease reuse (leases already exist, `agent_work_coordinator.py`). |
| PA-14 | Inbound SSE `while True` (client-disconnect only); `_TRIP_EVENT_LISTENERS` never pruned | `inbound.py:528-561` | IMPLEMENT | 🟡/🟡/🟡 | Max-lifetime + listener dict pruning (F-12 rides this). |
| PA-15 | Undo/redo: in-memory per-process, cross-agency (no scoping on `/history/*`), unbounded stack, restored state bypasses status guard/CAS, lost on restart | `mutation_history_stack.py:42-44,77-99`; `trip_history.py:30-73` | IMPLEMENT | ❌/❌/❌ §11 | Agency-scoped, bounded, guard-respecting restore (route through `update_trip_if_version`). |
| PA-16 | Collection token single-use not atomic (validate read → unconditional mark-used; replay window) | `collection_service.py:75-104,153-165` | IMPLEMENT | ❌/🟡/🟡 | CAS `UPDATE … WHERE status='active'` (pattern exists in price-lock). |
| PA-17 | Lazy stale-run sweep races live daemon threads → run FAILED, trip saved, `complete()` raises on illegal transition and is swallowed → ledger/trip divergence | `run_status.py:57-58`; `pipeline_execution_service.py:561-569` | IMPLEMENT | ❌/🟡/🟡 §11 | Don't sweep runs whose lease/thread is provably alive; allow failed→completed reconciliation or record `completed_after_failure`. |
| PA-18 | Durable 5-tier memory never read by decision/suitability (write-only machine) | zero callers of `MemoryStore.query`/`MemoryRetriever.retrieve` in run path; UI-only via `customer_memory.py:27,254` | EXPLORE → IMPLEMENT (sharpens F-13) | 🟡/🟡/🟡 §1 | Wire the two named slot points (F-13) behind confidence gates, or DECIDE archive. Best: preference memory feeding question-generation is the highest-value, lowest-risk first read-path. |
| PA-19 | Audit SHA-256 chain never verified outside tests; unanchored; 10k tail-compaction breaks predecessor continuity; `/api/audit` reads a different unchained store | `persistence.py:2400-2500`; `routers/audit.py` | IMPLEMENT (extends F-06) | 🟡/❌/❌ §2 | Scheduled/head-anchored verification; re-anchor on compaction; single audited store. |
| PA-20 | Cost not decision-attributable: `usage_events` lacks trip/run/decision id; `/metrics` empty | `usage_store.py:99-127` | IMPLEMENT | 🟡/❌/🟡 | Correlation ids on usage records; cost-per-decision rollup. Best: cost joins PA-07 failure classes → cost-per-outcome, the persona's economics primitive. |
| PA-21 | Closed-loop "shadow test" = string equality of layer names; `proceed` verdicts asserted, never demonstrated by re-execution | `closed_loop_learning.py:117-197,421` | IMPLEMENT | ❌/❌/❌ §2 | Verdict requires real re-execution against fixture corpus (D6 lanes) or is labeled `heuristic`. |
| PA-22 | LLM-as-judge default scores output shape; uncalibrated; no prod consumer | `judge/scorer.py:74-230` | DECIDE (wire-or-archive, extends C-02) | ❌/🟡/❌ | Calibrate against human labels before any gating role, or archive. |
| PA-23 | Commission payout ledger: in-memory, fake-seeded balances, clock-derived collision-prone ids, unauthed write path, never reconciled against settlement | `commission_reconciliation.py:13,27-71`; `server.py:1473` | IMPLEMENT | ❌/❌/❌ §11 | SQL-backed ledger + auth + settlement join (links to F-04/F-16 money-ledger family). |
| PA-24 | `CAPABILITY_TOKEN_SECRET` committed default fallback (vs fail-closed `PROPOSAL_SIGNING_KEY`) | `boundary_engine.py:31` | IMPLEMENT | ❌/🟡/❌ | Fail-closed at startup like the proposal key. |
| PA-25 | Compiler mints **signed share tokens for synthetic inventory** — credential-backed identity for fabricated packages — **cross-ref: corresponds to F-42 (ProposalCompilerPanel honesty regression) in the parallel drift addendum** | `proposal_compiler.py:38,140-145,161` + fabricated content `:95-103,162-166` | IMPLEMENT | ❌/🟡/❌ §13 | Share token only when inventory source is real, or package carries `TierMetadata` end-to-end (token payload includes tier). |
| PA-26 | Corporate policy override self-certifying: free-text approver, no role, no dual-control, ignores `require_pre_approval` | `corporate_policy.py:110-147` | IMPLEMENT | ❌/❌/❌ | Authenticated approver identity + role check + dual-control for over-threshold (F-03 family). |
| PA-27 | ESCALATE early-exit lead-save failure doesn't fail the run — lead silently lost with a log line | `pipeline_execution_service.py:378-395` | IMPLEMENT | ❌/🟡/❌ §11 | Persist-then-verify before `block()`; surfaced repair path on failure. |
| PA-28 | IVR API returns `"status":"success"` for calls never placed (synthesized DTMF, no carrier) | `ivr_bypass.py:38-46`; `ivr_bypass_bot.py:51-94` | IMPLEMENT | ❌/🟡/❌ §13 | `"status":"simulated"` until a real carrier adapter exists (GM-01 residual). |

### A.4 P3 — durability, hygiene, dead code

| ID | Finding | Evidence | Class |
|---|---|---|---|
| PA-29 | `agent_work_leases`/`agent_requeue_jobs` terminal rows never expire (unbounded) | `agent_work_coordinator.py:31-50`; `agent_requeue_jobs.py:489` | IMPLEMENT |
| PA-30 | `CheckpointStore`/work coordinator in-memory despite durable-sounding names; fleet guarantees single-process | `runtime.py:109-111,271,386`; `checkpoints.py:41-86` | IMPLEMENT |
| PA-31 | RetentionEnforcer purges nothing (declared-only policy) | `retention_enforcer.py:105-111` | EXPLORE (extends X-14/F-05) |
| PA-32 | Memory provenance `verify_integrity` zero callers (write-time only) | `memory/provenance.py:40-43` | IMPLEMENT |
| PA-33 | RAG groundedness = lexical overlap; echo-vocabulary hallucinations pass | `rag/grounding.py:43-61` | EXPLORE (A-02 family) |
| PA-34 | Evals measure accuracy only — no cost/latency/human-intervention dims anywhere | `manifest.yaml`; `metrics.py` | EXPLORE → IMPLEMENT |
| PA-35 | Theater components: `MultiPersonaDebateCouncil` (hardcoded, zero callers), `ModelCapabilityRouter` (zero callers), ghost workflows `pending` forever, CheckerAgent naming | `debate_council.py:43-148`; `model_router.py:31-90`; `frontier.py:70-93`; `checker_agent.py:22-26` | DECIDE (C-01/C-03) → IMPLEMENT |
| PA-36 | Suitability Tier-3 LLM scorer unwired (legit design, deliberate exclusion undocumented) | `llm_scorer.py:216,234-240` vs `integration.py:281` | DECIDE (G-03) → RECORD |
| PA-37 | Watchdog detects only dashboard-sum drift; blind to decision drift/tampering/cost/stale completions | `watchdog.py:70-100` | EXPLORE |

### A.5 Pass-2 addendum (independent verification re-run, 2026-09-06)

The three rate-limited sweeps were re-run as fresh independent passes and reconciled (full disposition: audit doc §12). Result: **P0 count is now three.**

| ID | Change | Class | Notes |
|---|---|---|---|
| PA-05 | **Upgraded P1 → P0**: `booking_fulfillment.py:137,149` calls nonexistent `TripStore.get`/`TripStore.update`; `AttributeError` swallowed; `FULFILLED_CONFIRMED` returned with nothing persisted. Broken write path, not just self-assertion. | IMPLEMENT (Phase 0) | Lead-verified |
| PA-38 | **NEW P2 — escalation split-brain (in-flight work)**: recovery agent writes `trips.review_status="escalated"` (`recovery_agent.py:323` → `agent_runtime_adapters.py:31`); new queue reads `TripRoutingState.status` (`assignments.py:121-122`). Recovery-escalated trips invisible in the new queue. | IMPLEMENT (Phase 0/1) | Lead-verified |
| PA-39 | **NEW P3**: draft promote bypasses its store's optimistic-version support; second promote overwrites trip linkage | IMPLEMENT | `draft_store.py:374-384` |
| PA-40 | **NEW P3 (context)**: durable idempotency CAS wired to only 2 ingress paths; POST /run, price-lock, fulfillment, promote all bypass it | IMPLEMENT | Context for PA-02/13/05 |
| PA-18 | Strengthened: decay/GDPR/eligibility engines have **zero callers** — forgetting never executes; GDPR erasure dead on both paths | EXPLORE → IMPLEMENT | Pass 2 |
| PA-30 | Strengthened: CheckpointStore/DLQInspector zero external callers; DLQ `replay_job` flips status without executing (`dlq_inspector.py:90-92`) | IMPLEMENT | Lead-verified |
| PA-17 | Demonstrated: run stayed `running` 48,310s until polled (`error_message` in sampled ledger meta) | IMPLEMENT | Pass 2 observation |
| PA-01 | Nuance: `test_journey_graph_hydration.py` currently **pins the fabricated-fallback path** — must be rewritten with the route, not just the route fixed; `DISABLE_AUTH` + `X-Agency-ID` widens exposure | IMPLEMENT (Phase 0) | Lead-verified |
| PA-15 | Corrected: undo/redo never writes TripStore (returns payload for client) — cannot corrupt, but also cannot restore; non-authoritative theater | IMPLEMENT | Mechanism corrected |
| PA-27 | Corrected: lead-save failure is loud (logged + BLOCKED) but unrecoverable — not silent | IMPLEMENT | Wording corrected |
| PA-32 | Refined: epistemic `ProvenanceSlot` write-only (no consumers) AND memory authority weights consumed — different subsystems, both recorded | IMPLEMENT | Pass 2 |
| F-42 detail | ProposalCompilerPanel fulfill flow calls 404 via BFF route-map — dead wiring, not just dishonest labeling | IMPLEMENT | S5 refresh |

### A.6 Implementation record (2026-09-06, same day as the audit)

Owner directed the P0+P1+P2 wave (25 findings). **All 25 implemented, S2-verified locally, zero ruff warnings, nothing committed.** Per-finding fix shapes and S2 evidence: audit doc §13. **Canonical promotion done:** all 40 PA rows now live as Part 4g of `FINDINGS_REGISTER_2026-08-31.md` (parser-validated; fixed-locally rows deliberately open-partial per the verify-first convention). Per the no-second-status-store rule, this companion is now historical discovery context — **do not update statuses here; the canonical register owns them.** Full-suite baseline + honest boundaries: audit §13.3–13.4.

Standing open items after this wave (register Part 4g): PA-11, PA-18, PA-19, PA-22 (DECIDE), PA-29…PA-37 (incl. DECIDEs PA-35/36), PA-39, PA-40; plus the open halves of PA-13 (per-trip lease), PA-15 (durable restore), PA-20 (schema columns, A-20 custody), PA-23 (SQL ledger, F-04).

---

## Part B — Explicit (already-documented) findings: index

Not duplicated here (single status authority). Counts and pointers:

- **Canonical register** `Docs/review/FINDINGS_REGISTER_2026-08-31.md`: at audit-sweep time **145 rows — 91 open / 53 closed / 1 deferred** (point-in-time figure; the register is live and moved to 147 rows / 93 open the same day when the parallel drift addendum's F-41/F-42 were promoted — parser is authoritative at any moment).
- **Owner-gated DECIDE items** (all open): C-01 wire-or-archive Frontier/Council · C-02 per-module outcome ADRs · C-03 model-router ratification · C-04 SLM posture · D-01 duration · D-02 flights-inclusive · D-03 country-vs-city · R-09 signup posture · R-10 business model · F-04 commit-split authorization.
- **RECORD items** (8 open): R-01 chronicle caveats · R-02 MEMORY.md rewrite · R-03 RAG doc rewrite · R-04 seasonal doc · R-05 agent-runtime doc · R-06 ADR/backlog consolidation · R-07 personas adoption · R-08 idea-pad statuses.
- **Launch posture** (`Docs/LAUNCH_STATUS.md`): NO-GO public/paid; CONDITIONAL-GO invite-only pilot. Blockers L1-L8 + pilot gates (deployment envelope, migration/backup proof, simulator-gating, durable shared state, eval core, legal review, browser smoke, release custody).
- **Known conflicts this audit creates (owner decision needed):** PA-03 supersedes map honesty note + G-03 wording ("orphaned, default-off" → "wired, default-on, credential-gated"); PA-18 sharpens F-13 from "two slot points identified" to "zero read-path, verified"; PA-09 partially supersedes the stale corporate-policy no-JWT finding (write endpoints now have JWT; override is self-certifying instead).

---

## Part C — Items that should be EXPLORED (researched and documented) before/instead of code

| # | Exploration | Why first-principles exploration precedes code | Produces |
|---|---|---|---|
| E-A | **Agency-boundary ratification ADR**: which rungs are canonical for which capability; hybrid-engine default; Tier-3 scorer and memory read-path wire-or-archive | PA-03/PA-18/PA-36 show the boundary is enforced by accident; the DECIDE backlog (C-01…C-04) needs one coherent answer, not four separate ones | `Docs/architecture/ADR_AGENCY_BOUNDARY_*.md` + register row updates |
| E-B | **Failure-taxonomy design**: enumerate classes, map each to recovery action, define ledger schema | PA-07 — recovery architecture requires the taxonomy first; wrong taxonomy now = re-migration later | Design doc + migration sketch |
| E-C | **Cost-per-outcome model**: what to attribute (model/tool/retry/latency/human) and where it lands (usage_events → decision → trip) | PA-20/PA-34 — economics primitive must be designed before instrumentation scatters | Metrics + schema design doc |
| E-D | **Memory read-path product design**: which decision slots consume which memory tiers at which confidence | PA-18 — wiring without a product answer creates context soup (persona failure mode) | Slot spec per F-13, expanded |
| E-E | **Timeline-as-evidence spec**: single event stream, one id-space, operator-visible rationale; audit-chain anchoring cadence | PA-04/PA-19 — observability consolidation needs one design, not three patches | Observability ADR |
| E-F | **Sim-surface disposition register**: complete real/sandbox/sim tier map incl. fulfillment, IVR, compiler, journey graph; each surface gets TierMetadata or removal | PA-01/PA-05/PA-25/PA-28 — ad-hoc labeling keeps regressing; a complete map ends the class | Extends SIMULATOR_PROVIDER_TRUTH_AUDIT_2026-09-04 |
| E-G | **Durable-store endgame**: run-ledger/revocation/undo/checkpoints → shared durable SQL (multi-worker, restart-safe) | S2 shows the file/in-memory substratum is the systemic LT risk (F-09/S-11/N-07 family) | Migration design feeding L4 blocker |
| E-H | **Adversarial evaluation lane activation** (E-10/E-11 already seeded: 40-record corpus, confirmed prompt-injection + routing holes) | The audit found reviewer illusion; adversarial lanes are the established antidote and the corpus exists | Lane activation plan + first run |

---

## Part D — Improvement opportunities beyond fixes ("what else can make it the best")

1. **Publish the autonomy ladder as a product artifact** (L0-L5 per action class, from §5.2 authority map) — operators and reviewers currently cannot see what the system may do without a human; the data to generate it already exists in `agency_settings` + gates.
2. **Environment-demonstrated completion helper**: one `verify_terminal(effect)` postcondition (re-read + version + tier check) used by fulfillment, lead-save, and run completion — converts PA-05/PA-27 classes into a checked property.
3. **Cost-per-decision in the operator UI**: once PA-20 lands, surface it next to the rationale — the rationale already persisted is the perfect anchor for "this decision cost X and fired rule Y".
4. **Failure-class-driven ops views**: escalated queue (shipped, uncommitted) + DLQ + failure-class counters = the operator recovery cockpit the persona describes ("who has authority to recover").
5. **Delete the theater, keep the lesson**: council/router/ghost-workflow removal with a recorded ADR prevents re-introduction (supersession workflow per repo rules).
6. **Memory trust-weighting at the two slot points** would let the 5-tier graph finally pay rent — and gives the GDPR machinery a purpose beyond storage.
7. **Real `/metrics` + failure classes** turn the watchdog from one drift class into a health surface (PA-10/PA-37).
