# TPM Training Blueprint → Product Mapping (Wide-Open Brainstorm)

**Date:** 2026-09-01
**Context:** Pranay's ongoing ChatGPT TPM/system-design training discussion (fictional "Waypoint" travel system) produced a system-design blueprint. This session mined that blueprint for product improvements to `travel_agency_agent`, with a full role panel: Grounding Cartographer (code-auditor), Operator, Skeptic, Champion, Executioner, plus an external Outsider pass (codex). Gemini CLI is dead (Google discontinued the individual tier) — noted for future role panels.
**Deliverable:** explicit + implicit learnings inventory → verified exists/partial/missing map → net-new tasks (register-ready) → defer list → build conditions.
**Canonical register:** `Docs/review/FINDINGS_REGISTER_2026-08-31.md` (authoritative; supersedes the 08-30 consolidated doc). Nothing below may be worked without passing `scripts/check_findings_register.py` intake.

---

## 1. Kill-test verdict first (read this before acting)

The Executioner returned **KILL** on the premise "mine the TPM blueprint for a product task stream," and the argument is one-sided:

1. **This repo already is Waypoint OS.** `Waypoint OS Design _offline_.html`, `waypoint_os_master_product_opportunity_feature_idea_exploration_registry_2026-08-04.md`, and the 2026-08-03 launch audit show the blueprint's source material was already mined into this codebase months ago, at far greater depth than the training discussion.
2. **The residue of blueprint-thinking is the repo's current liability.** The launch audit's central verdict — "mixes four reality levels", simulated capabilities presented as real — is exactly what blueprint-derived material produced. HEAD commits (`fix(launch): enforce reality boundary`) exist to fence it.
3. **The register is the immune system.** The findings lifecycle + `NG` (no-go) taxonomy + RealityTier evidence labels evolved specifically to metabolize blueprint material. A parallel "blueprint-derived" stream is the `EX-03` pathology ("built the replacement, never retired the original") pre-installed.

**Arbitration (Champion vs Executioner) — build conditions.** The Champion's case survives *conditionally*: the blueprint is a north-star reference architecture, and the codebase already contains its primitives — but they are **unbound** (defined, tested, called by nothing). The Executioner's salvage clause (one-time gap-diff, output only net-new non-duplicate rows through the existing register) is the correct operating mode. That gap-diff was run in this session, and it produced **exactly three net-new tasks** (§5) plus one derived read-model UI task (§6). Everything else is already implemented or already tracked. **Do not create a blueprint initiative; file the three rows and stop.**

---

## 2. Learning inventory (explicit + implicit), with verified product mapping

Verdicts audited against HEAD (`2f9a638 feat(platform): harden trip operations`), 3,215 backend tests green, D6 gate F1 0.9524.

| # | Learning (from the ChatGPT discussion) | Codebase verdict | Evidence |
|---|---|---|---|
| L1 | Trip state ≠ customer memory. State = "what we currently believe is true about THIS trip"; memory = preferences that enrich decisions | **PARTIAL** — memory side is excellent, state side is a freeform string | `src/memory/` (store/retriever/provenance/supersession/decay/gdpr) vs `trip_status: str = "IN_PROGRESS"` (`spine_api/contract.py:1451`) |
| L2 | Lifecycle state machine: INTAKE → NEEDS_INFORMATION → FEASIBILITY → PLANNING → AWAITING_APPROVAL → APPROVED+recheck → BOOKING → BOOKED → CHANGE_REQUESTED → IN_TRIP → COMPLETED, ESCALATED from many states | **PARTIAL** — six disjoint vocabularies, one guarded transition | `spine_api/run_state.py`, `src/intake/lifecycle.py` LeadStage, `VALID_STAGES` (`trip_lifecycle_service.py:19`), quote Literal (`contract.py:56`), routing (`routing_service.py`); only guard = `expected_current_stage` |
| L3 | State vs Action vs Event vs Transition; per-state 4-question contract (what is true / allowed / forbidden / what moves us out) | **MISSING** — no per-state contracts anywhere | All six vocabularies carry no allowed/forbidden action semantics |
| L4 | Constrain AI inside a deterministic operating envelope | **IMPLEMENTED (run-level), not trip-level** | `GateVerdict`/`AutonomyOutcome` (`src/intake/gates.py`); nothing binds it to trip mutations |
| L5 | Gates ≠ dependencies ≠ parallelizable; gate economics (latency benefit vs wasted-work cost); short-circuit cheap trip-killers first | **PARTIAL** — ordering real, economics implicit, no fan-out | `run_spine_once` sequence + NB01/NB02 + early_exit (`src/intake/orchestration.py:181+,172`) |
| L6 | Request failure vs goal failure; recoverable gate → replan, goal failure → escalate | **PARTIAL** — recovery engine exists but unwired to ESCALATE | `src/decision/counterfactual_recovery.py:51+` (IROPS path only) |
| L7 | Progressive validation ∝ consequence: feasibility search → recommendation → booking need progressively stronger certainty | **PARTIAL** (concept echoed in gates) | `gates.py` three-layer model; no tier ladder on actions |
| L8 | CHECK ≠ RESERVE ≠ PURCHASE; cost-of-mistake determines autonomy | **PARTIAL — dormant matrix, live heuristic** | `AuthorityTier`/`ScopedCapabilityToken` (`src/schemas/boundary_contracts.py:17-58`, router `boundaries.py`) with **zero pipeline callers**; live `evaluate_autonomy_dispatch_gate` ($10k ceiling etc., `autonomy_gates.py:31+`) |
| L9 | Deterministic-filter → AI-rank → deterministic-validate; AI never alters provider facts | **PARTIAL** — convention, not checked contract | hybrid engine `source: rule\|cache\|llm` (`src/decision/hybrid_engine.py:63,232`); no post-AI fact re-validation on the LLM-ranking path (`src/suitability/llm_scorer.py`) |
| L10 | Validation taxonomy: travel-time feasibility, budget ≤ approved, passport expiry vs destination rule, no overlaps, party vs occupancy, child-age fares, source freshness | **PARTIAL** | Exist: budget/visa-timeline/elderly/toddler/composition rules, Schengen 90/180. Missing: travel-time feasibility, passport-validity (data captured, never validated), overlap check, occupancy check |
| L11 | Idempotency: retries must not duplicate effects | **PARTIAL — the net-new gap is at the intake mouth** | Draft→trip reprocess idempotent (`draft_store.py:402-414`); `IdempotencyRegistry` (`src/agents/idempotency.py:42-63`) **with no webhook consumer**; `messaging_webhooks.py` has zero dedup/replay handling |
| L12 | Freshness recheck between approval and execution; never silently book drifted prices | **PARTIAL** | Price-lock sentinel (72h, `price_lock.py:7-9`) exists but has no trip-state consequence and no approval→execution binding; re-lock is blind RMW (F-01) |
| L13 | Partial-failure saga: per-component CONFIRMED/FAILED/NOT_STARTED | **PARTIAL** | `confirmation_service.py:318-519` per-component draft→recorded→verified/voided — proposal-dispatch only, no booking saga |
| L14 | Dual-writer consistency: customer msg + operator edit + agent replan → which state wins? | **MISSING (fragments)** | `/optimistic-sync` is blind last-write-wins (`inbound.py:180+`); `locking.py` degrades in-process (F-08); `ExecutionLease` dead (R-11) |
| L15 | Provenance on every proposal fact (source, freshness, inference) | **IMPLEMENTED (memory), PARTIAL (trip facts)** | `src/memory/provenance.py` SHA-256 lineage; trip-field provenance tracked only via F-13/R-06 |
| L16 | Observability: why failed, which tool/model/prompt/state/rule | **IMPLEMENTED, two caveats** | Hash-chained audit (`models/audit.py:99-105`), timeline+SSE (`trip_observability.py`), run-ledger steps — but ledger files outside hash chain (F-06), no model/prompt version on step records, actor identity self-asserted (F-03) |
| L17 | Auditability: who decided what (customer/agent/human/rule) | **PARTIAL** | Approvals accept client `reviewer_id` (F-03) |
| L18 | Privacy/PII | **IMPLEMENTED, one tracked residual** | `privacy_guard.py` + jurisdiction policy; fail-open/closed reconciliation = R-15 |
| L19 | Operator-facing vs traveler-facing outputs | **IMPLEMENTED** | `traveler_bundle` vs `internal_bundle` split (`inbound.py`) |
| L20 | Feedback → memory (explicit corrections, implicit signals, outcomes) | **PARTIAL** | Survey + supplier scorecard (`feedback.py`); survey→memory loop not closed |
| L21 | Scale taxonomy (state consistency, providers, cost routing/caching/budgets, observability, privacy, reliability, drift→evals) | **IMPLEMENTED at current scale** | `LLMUsageGuard` budgets (`usage_guard.py:74-135`), D6 gate `blocks_ci`, agentic feedback loop; gaps F-11 (subagent spend bypass) already tracked |
| L22 | Multi-message intake merge without silent loss; source routing (parse/OCR/fetch/transcribe); normalization with confidence | **PARTIAL — merge precedence is the hole** | Colloquial extraction + 20 fixtures, multimodal routing shipped; but `/optimistic-sync` lets a customer reply silently clobber an operator-corrected field |
| L23 | Incremental refinement: hard deps vs soft deps; refine as inputs arrive | **IMPLEMENTED** (intake-side) | Draft reprocess loop + follow-up prompts |
| L24 | Ambiguity preservation: "around Oct 5" is *accurate data about the conversation*, not incomplete data (Outsider add) | **PARTIAL** | Confidence + season-window extraction exist; no epistemic status (ASSUMED/UNKNOWN) surface — already tracked as EX-02 |
| L25 | Operator model = prioritized queue + next-best-action; the state machine stays underneath as audit/control substrate (Outsider add) | **MISSING as product surface; the enabling data all exists** | See §6 derived read-model task |

**Already shipped and NOT to be re-registered** (Skeptic-verified): ESCALATE lead persistence + idempotent reprocess + no-overwrite invariants (IMP-01); colloquial extraction (IMP-02); D6 gate with 15 colloquial fixtures (F-18); deterministic gate boundary that survived the RQ-01 falsifier; privacy guard (residual = R-15); repeat-traveler memory graph (commit `a877406`); LLM cache ADRs NB05/NB06; run-ledger/checkpoint items F-09, locking F-08, provenance F-13/R-06, deadlines F-14/EX-14.

---

## 3. The load-bearing insight (four roles converged independently)

**The gap in this codebase is almost never a missing module — it is a missing caller.**

- Grounding Cartographer: AuthorityTier, IdempotencyRegistry, CounterfactualReplanningEngine, locking, jurisdiction_policy all exist as tested classes at ~zero call sites. "A class exists" and "an invariant is enforced" are different products.
- Champion: authority is defined but not bound — "operator must sign off before supplier action" means nothing unless the trip *cannot leave AWAITING_APPROVAL without the sign-off event*. The state machine is the single binding artifact that turns six dormant assets into one enforceable system.
- Operator: the backend already contains nearly every blueprint state — across **six unjoined vocabularies** keyed by the same trip_id. The operator's daily work is mentally joining them per trip. The product gap is one derived read-model, not new states.
- Skeptic: the codebase independently converged on the blueprint's core stance via its own ADRs ("gates gate the quote, not the record"; the deterministic boundary survived a falsifier test).

Champion's inversion (the actual architecture bet): **a state machine doesn't restrict AI — it makes AI freedom cheap to grant.** Once every consequential mutation must be a named, validated transition, models can propose anything and the machine refuses the invalid — moving safety from prompts (probabilistic, drift-prone) into invariants (deterministic, testable, free at runtime). `src/intake/gates.py` already wrote this thesis; it just never got applied to the trip itself.

---

## 4. Deferred (with reasons — do not build now)

| Blueprint item | Why deferred |
|---|---|
| AuthorityTier→pipeline binding as a build | Honest slice is already tracked (R-06/A-03 CONNECTIVITY_TIER + F-03 approval identity + F-04 mandate ledger). When revisited: audit-only shadow mode first, then enforce |
| Booking sagas / CHANGE_REQUESTED / IN_TRIP states | No live booking rails (NG-01/NG-03, EX-05). A saga with no compensating action is untestable theater. Declare dormant placeholders only when a validator exists for entering the state |
| Freshness-recheck as standalone task | No execution step to guard pre-connectivity; quote/price TTL belongs inside F-14/EX-14 (already P1) |
| 1M-trips/month scaling taxonomy | One modest tenant; per-repo perf doctrine applied; shard talk is cosplay until load signal exists |
| Dual-writer locking as a build | Real needs already tracked (F-08, F-09, F-01); the only *live* collision is merge precedence → task N-3 below |
| Travel-time / passport / overlap / occupancy validators | Genuine gaps but only matter at quote-quality level; batch with existing rules work rather than opening a new stream |

Discipline (Champion's caveat, adopted): **name a state only when a validator exists for entering it.** The full blueprint list would recreate the freeform-string problem with better branding.

---

## 5. Net-new register-ready tasks (the entire deliverable output)

**STATUS 2026-09-02: ALL FOUR IMPLEMENTED, review-hardened (2 cycles), register-filed (F-27/F-28/F-29), tests green.** Full evidence: `Docs/review/TPM_BLUEPRINT_TASKS_IMPLEMENTATION_HANDOFF_2026-09-01.md`. Not committed — awaiting Pranay's explicit commit approval.

Three tasks survived both the diff against `FINDINGS_REGISTER_2026-08-31.md` (no duplicates) and the Skeptic's scrutiny. File these through the normal findings lifecycle; validate with `scripts/check_findings_register.py`.

**N-1 — Intake-boundary idempotency: webhook/message dedup.** [P1, money/token-adjacent]
Every provider retry on any inbound channel (parse, voice/image path, social adapter) can mint a duplicate draft/lead and burn duplicate LLM spend. Zero idempotency/dedup/replay handling in `spine_api/routers/inbound.py` or `spine_api/services/messaging_webhooks.py` (`ADR_OMNICHANNEL_WEBHOOK_SECURITY_2026-07-29.md` confirms). Fix: canonical fingerprint upsert before draft creation, reusing `src/agents/idempotency.py` (first real consumer of the dormant registry). Small, additive, and it is the blueprint's idempotency learning applied where duplicates actually occur today.

**N-2 — Codify trip-status as a typed state machine with enforced legal transitions.** [P1, foundation]
Status semantics are currently ad-hoc across `pipeline_execution_service.py`, `draft_store.py`, `run_state.py`, and inbox projection; the ESCALATE ADR had to patch semantics by hand (never-overwrite, dead-ID guard, `incomplete` reuse). Scope (no booking states): typed enum + transition table for {incomplete → active/quote-ready → completed}, ESCALATED/incomplete never quote-ready; enforce inside `TripStore.save`; audit each transition; CI assertion that no path treats an incomplete/escalated trip as quote-ready; legacy-value string mapper so `contract.py:1451` flips additive-enum-first, mapper-second, per-state-action-enforcement-third. The `expected_current_stage` guard (`trip_lifecycle_service.py:159-176`) proves the pattern works — this unifies six axes onto one machine. Structural side effect: the 2026-05-03 dual-store split-brain becomes structurally impossible rather than env-dependent.

**N-3 — Merge precedence + provenance on trip fields (`/optimistic-sync`).** [P1, operator trust]
`inbound.py:180+` accepts client-supplied fields with no precedence rule — a customer reply can silently clobber an operator-corrected field (same class as F-03 approvals and F-13 memory, untracked for trip fields). Fix: precedence contract (operator edit > verified client artifact > extracted client text; customer > operator for preferences, operator > customer for commercial fields), provenance tag on merged fields, NB01 re-gate after merge, E2E test that incomplete→complete upgrade stays 1:1 with the trip. `packet_version` check while touching the router; fail-fast locking assertion per F-08.

**N-4 — Derived lifecycle read-model for the operator UI (no backend change).** [P2, UX]
From the Operator lens: one `getTripLifecycle(trip)` client derivation (stage + status + decision_state + routing status) rendered as a LifecycleStrip in `trips/[tripId]/layout.tsx`; one `getTripBlockers()` in `frontend/src/lib/planning-status.ts` merging the four blocker computations; `view=escalated` queue (data already in `TripRoutingState` — escalated trips currently vanish from every queue via the `management_queue` synthetic assignee with zero UI); approval-freshness card wired to existing `/api/v1/price-lock` + `/trips/{trip_id}/reassess`; grow `DecisionTab.tsx:47-51` label map into an allowed/next-actions list. This is L25 made real: queue + next-best-action visible, machine underneath.

---

## 6. Time horizons

- **6 months:** N-1..N-4 shipped + generated TS contract with CI drift gate (A-06) + run-ledger checkpoints dual-written to SQL (F-09). Operator console: every row of every queue says why it's there.
- **12 months:** persisted server-side `TripLifecycleState` (superseding six-way inference); allowed-actions API; per-component saga view aggregating confirmations + booking tasks; automated expiry→reassess→re-approval loop behind the freshness card; trust-weighted memory writes (F-13); epistemic status surface (EX-02); budget auto-quiesce (F-11); DSAR enforcement wired (F-05).
- **24 months:** queue-per-state console with SLA/aging per state; ESCALATED as a first-class queue rendering `handoff_history` (data already persisted); disruption radar/crisis ops feeding an IN_TRIP mode automatically; event-sourced timeline only if F-09 proves insufficient (NG-01 sequencing call is correct); counterfactual replanning promoted from IROPS to the default ESCALATE branch so "replan" and "escalate" are two exits of one failure classifier; per-agency connectivity tiers (R-06).
- **Leapfrog:** make the state machine invisible to operators entirely (Outsider's "sounds wrong but is right"): operators see ranked next-best-actions with deadlines, reasons, and required permissions; states remain the audit/control substrate. Plus freshness policies **per fact** ("recheck any fact whose cost of staleness exceeds the cost of rechecking") instead of one ceremonial recheck transition.

---

## 7. Bridge to the training thread (answer-key section)

Pranay's current homework is modeling NEEDS_INFORMATION and BOOKING_IN_PROGRESS with the four-question contract. The codebase is the answer key:

**NEEDS_INFORMATION (this repo's real version):**

- What is true: partial packet persisted as an incomplete lead (IMP-01), `missing_fields` + `decision_state = ASK_FOLLOWUP`, followup dashboard row exists.
- Allowed: ask customer, snooze/reschedule followup, operator manual field fill, reminders.
- Forbidden: quote generation (NB01 blocks), promotion to quote-ready (N-2 will make this structurally enforced), overwrite of any existing linked trip.
- Out-transitions: `CUSTOMER_DETAILS_RECEIVED` (= followup response / `/optimistic-sync` merge) → idempotent reprocess (1:1, draft→trip).

**BOOKING_IN_PROGRESS (closest existing artifact):**

- `confirmation_service.py` per-component statuses (draft → recorded → verified/voided) + `BookingExecutionPanel` task gates = the per-component saga, at proposal-dispatch tier.
- Freshness = the 72h price-lock window — exists but, as L12 notes, unwired to trip state (deferred to F-14/EX-14 until connectivity).
- The four-question contract exposes exactly why it's not a real BOOKING state yet: there is no "what cannot happen" enforcement, because money-touching autonomy is unbound (§4, revisit with R-06).

Use these as the worked examples in the ChatGPT thread — every answer can cite a real file, which is precisely what the TPM discussion is training for.

---

## 8. Six-hat coverage (session record)

- **White:** 25-learning inventory, 13-cluster audit with file:line evidence, register diff clean for N-1..N-3, baseline 3,215 tests / D6 F1 0.9524.
- **Yellow:** three P1 net-new tasks are small, additive, and land at the intake mouth where duplicates and untrustworthy facts are created *today*.
- **Black:** biggest danger was re-registering six solved workstreams and having an implementation agent rebuild the ESCALATE loop that shipped yesterday; secondary danger: blueprint cosplay widening the "four reality levels" gap the launch audit flagged.
- **Green:** guard-as-substrate inversion; per-fact freshness policies; ambiguity-as-data (EX-02); invisible-state-machine operator UX.
- **Red:** operators don't want a state machine to maintain — they want to know what's blocking, what's next, and what changed since approval (four-tab problem).
- **Blue:** decisions = file N-1..N-3 via register, implement N-4 as read-model-only UI, defer list in §4 is binding; next action = register intake validation, then implementation per normal review cycles.

---

## Appendix: failed panel member

Gemini CLI (`/opt/homebrew/lib/node_modules/@google/gemini-cli`) now hard-fails with `IneligibleTierError: UNSUPPORTED_CLIENT` — Gemini Code Assist for individuals is discontinued (migration path: Antigravity). Future role panels should use codex (working, used for Outsider) or a subagent for the external/future-self lens.
