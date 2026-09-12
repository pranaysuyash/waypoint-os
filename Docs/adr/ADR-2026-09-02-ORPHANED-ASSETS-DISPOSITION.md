# ADR-2026-09-02: Orphaned & Simulated Assets — Wire-or-Archive Disposition

**Status:** PROPOSED — pending owner ratification. Every decision record in this ADR is a *draft recommendation* under the repo's ratification model (cf. `Docs/architecture/adr/ADR-008-AGENCY_BOUNDARY_AND_AUTONOMY_RUNGS_2026-09-06.md` §6: nothing is authoritative until ratified). Nothing here changes code.
**Date drafted:** 2026-09-11 (assets audited against the live working tree; source dossiers dated 2026-09-02 / 2026-08-31)
**Persona:** PER-0700 Agentic Systems Architect (central test: *first ask whether deterministic workflow is sufficient*)
**Sources:** `Docs/exploration/C02_WIRE_OR_ARCHIVE_DOSSIERS_2026-09-02.md` (primary), `Docs/exploration/AGENTIC_FLOW_DEEP_MAP_2026-08-31.md` (F-A1…F-A10), `Docs/exploration/C03_ROUTER_DESIGN_2026-09-02.md` (checker_model, tier ladder), `Docs/architecture/adr/ADR-008-AGENCY_BOUNDARY_AND_AUTONOMY_RUNGS_2026-09-06.md` (overlapping ratifications — see §1.2).
**Verification legend:** claims marked **(V)** were re-verified against the working tree on 2026-09-11 with `rg`/direct reads; unmarked file:line citations are carried from the source dossiers and were not re-checked.

---

## 0. Naming note (two-directory ADR split — read before citing)

This repo has **two numbered ADR directories plus an unnumbered root series** (`Docs/adr/ADR_INDEX_2026-09-02.md` §1–§3):

1. `Docs/architecture/adr/` — canonical architecture series, ADR-001…008 (003–005 absent/reserved-unknown, G-15).
2. `Docs/adr/` — Sep-2026 platform series (this directory), currently ADR-001 (routing/tiers) and ADR-002 (epistemic/RLS) — **numbers collide with series 1** (index §2).
3. `Docs/ADR_*.md` root — 20 unnumbered date-suffixed ADRs.

Per the index's own rule ("cite by full file path, not by number alone"), this record uses the **dated form** `ADR-2026-09-02-ORPHANED-ASSETS-DISPOSITION.md` instead of claiming the next number in either series: claiming "003" here would collide with series 1's reserved-unknown 003, and the dated form is collision-free and matches the repo's dominant ADR pattern. **On ratification, extend `Docs/adr/ADR_INDEX_2026-09-02.md` §2 with this file** (checklist item R-10).

---

## 1. Governing principle: never both-and-hidden

### 1.1 The rule

**An asset must occupy exactly one honest state at all times — it may never be both live-looking and dead, or simulated and unlabeled.** This is the single rule every disposition below enforces. Concretely, the four allowed states are:

| State | Meaning | Code posture | Surface posture |
|---|---|---|---|
| **WIRE** (with prerequisites) | Real capability in progress or pending a named gate | Called from a production path, gated by a feature flag | Labeled with its actual authority level |
| **LABEL+KEEP** (simulated, honest) | Deliberately simulated/demo, kept because it has sanctioned value | Never reachable as if production | Every surface shows a SIMULATED badge; honesty test guards it |
| **PARK** (revisit date/trigger) | Real logic, no market/domain yet; too good to delete, too fake to ship | No production callers; router-only or shadow; docstring says `PARKED` | Not presented as a live capability |
| **ARCHIVE** (supersession noted) | Superseded, duplicitous, or impersonating a real control | Archived (in-repo `Archive/` with pointer, or `@deprecated` in place per owner choice — open question Q-3 in the dossier); tests archived with code | Gone from routes/panels or explicitly tombstoned |

The forbidden fifth state is the one most of these assets were in on 2026-09-02: **"both-and-hidden"** — code that *looks* live on a dashboard or in a directory named `providers/`, while actually having zero production callers, or simulating a control (HMAC, compliance erasure, VCC issuance) that does not run. Compliance-shaped and security-shaped orphans are the worst members of this class because they imply a control that doesn't exist (dossier §2.4, retention_enforcer and provider-adapter rows; deep map F-A1/F-A2).

### 1.2 Relationship to ADR-008 (PROPOSED, same persona)

`ADR-008` §3 already proposes ratifications for three assets covered here — the hybrid engine ("deterministic core + credential-gated enrichment; `USE_HYBRID_DECISION_ENGINE` defaults `"0"`", ADR-008:45), suitability Tier-3 ("keep the code, declare it `PLANNED`", ADR-008:49), and Frontier OS/Persona Council ("remain labeled dev/demo surfaces — never operator authority", ADR-008:57). Where ADR-008 speaks, **this ADR inherits its proposal and records the dependency**; it does not contradict it. Ratification of ADR-008 settles those three rows' posture; ratification of this ADR settles the remaining twenty-one.

---

## 2. Summary disposition table

| # | Asset | Disposition | Key prerequisite / first action | Effort |
|---|---|---|---|---|
| 1 | Hybrid decision engine (`src/decision/hybrid_engine.py`) | **WIRE** (keep wired; ratify OFF-by-default posture per ADR-008) | Owner ratifies ADR-008 hybrid row; hybrid-specific eval lane before any deployment opts in | S |
| 2 | Suitability Tier-3 scorer (`src/suitability/llm_scorer.py`) | **WIRE** (gated) | Tier-3 flag-quality eval lane; wire behind critical-flag escalation; record `PLANNED` in docstring now (ADR-008:49) | M |
| 3 | Ghost concierge engine (`spine_api/services/ghost_concierge.py`) | **WIRE** (later, as agent-runtime scanner) | Delete fake trigger `frontier_orchestrator.py:83-86` now; live flight-data contract | M |
| 4 | Retention enforcer (`src/security/retention_enforcer.py`) | **WIRE** (or annotate not-operating) | Wire to lifecycle/agent path, else demote GDPR/DPDP framing in docstrings — owner picks | S |
| 5 | DLQ inspector (`src/agents/dlq_inspector.py`) | **WIRE** (later, ops) | Wire against `WorkStatus.POISONED` states or archive; never imply a live DLQ process | S |
| 6 | Pre-departure cadence (`src/briefing/pre_departure_cadence.py`) | **WIRE** (preferred) — fallback ARCHIVE | Product call: Communicator-agent output contract; if declined → archive | S |
| 7 | Payment mandates (`src/financial/payment_mandates.py` + service/models) | **WIRE** (in progress) | Ratify R1 mandate gate in booking fulfillment (ADR-008 §3); dossier's ARCHIVE verdict is stale | M |
| 8 | Frontier OS + Persona Council panels | **LABEL+KEEP** (simulated, honest) | Ratify ADR-008:57 dev/demo status; labels + honesty test already shipped; retire or graduate later | — |
| 9 | Vision-doc extraction (`spine_api/services/extraction_service.py`) | **LABEL+KEEP** (wired, human-gated — status quo) | None — reference pattern for all future wires | — |
| 10 | Route geometry + pipeline bridge (`src/logistics/route_geometry.py`, `pipeline_bridge.py`) | **LABEL+KEEP** (already live; protect) | None — protect as eval-lane + agent-tool dependency | — |
| 11 | `checker_model` setting | **LABEL+KEEP** (honest copy now; becomes T1 knob later) | Fix settings UI copy per C-03 §7; consumed at C-03 release R5 | S |
| 12 | Logistics operations suite (connection_risk, rooming_list, fleet_allocation, timed_entry, accessibility) | **PARK** | Trigger: wire `connection_risk` into ghost concierge when #3 wires | — |
| 13 | MRZ parser (`src/intake/mrz_parser_engine.py`) | **PARK** | Trigger: vision-doc intake attaches OCR/MRZ text | — |
| 14 | Group Pareto engine (`src/decision/group_pareto_engine.py`) | **PARK** | Trigger: `coordinator_group` mode ships (`packet_models.py:432-435`) | — |
| 15 | Charter aviation engine (+ empty-leg scraper) | **PARK** | Trigger: premium-segment go-decision + live operator feed | — |
| 16 | Financial settlement engine (`src/fees/settlement_engine.py`) | **PARK** (constrained) | VCC issuance wired only behind a real VCC provider; IR-ROPS use stays proposal-only | M |
| 17 | Yield arbitrage (`src/yield_arbitrage/*`) | **ARCHIVE** | Unless a real bedbank/GDS feed is contracted; fix/delete YieldArbitragePanel (N-04) | S |
| 18 | Telephony IVR bypass (`src/telephony/ivr_bypass_bot.py`) | **ARCHIVE** | Until a real telephony provider exists (Twilio adapter is itself a simulator) | S |
| 19 | Corporate policy engine (`src/corporate/policy_engine.py`) | **ARCHIVE** | Until a corporate-travel segment exists | S |
| 20 | Visa workflow (`src/documents/visa_workflow.py`) | **ARCHIVE** | Visa risk already canonical in `src/decision/rules/visa_timeline.py` — two visa subsystems is drift | S |
| 21 | Perishable sentinel (`src/monitoring/perishable_sentinel.py`) | **ARCHIVE** | No inventory domain in the current product | S |
| 22 | Accounting export bridge (`src/accounting/export_bridge.py`) | **ARCHIVE** | Until an accounting integration is contracted | S |
| 23 | Epistemic engine (`src/intake/epistemic_engine.py`) | **ARCHIVE** (superseded) | Superseded by `Slot` provenance fields (`packet_models.py:151-164`) + audit snapshots | S |
| 24 | Epistemic arbiter (`src/intake/epistemic_arbiter.py`) | **ARCHIVE-or-MERGE** | Field-by-field supersession check vs `Slot` first; merge unique checks into packet validation, then remove | S |
| 25 | "Production" provider adapters (`spine_api/providers/{amadeus_enterprise,stripe_issuing,twilio_telephony}_adapter.py`) | **ARCHIVE** (move + rename; delete fake HMAC) | Move out of `providers/` before the first real client lands; delete fake webhook HMAC (GM-02/GM-03 hotfix class) | S |

**Counts:** WIRE 7 · LABEL+KEEP 3 · PARK 5 · ARCHIVE 9 · total 25 records.

---

## 3. Current-state corrections to the source dossiers (drift found while drafting, 2026-09-11)

The instruction stack treats drift as normal; four dossier claims moved. Records below reflect the **current tree**, not the dossier text.

1. **Hybrid engine flag: dossier said default-ON; tree is now default-OFF.** C-02 §0 recorded `USE_HYBRID_DECISION_ENGINE` default `"1"` (`decision.py:36` as of 2026-09-02). PA-03 (P1, 2026-09-06) flipped it: the in-tree comment now reads "default is now OFF so serving determinism is architectural, not credential-accidental" (`src/intake/decision.py:33-40` **(V)**; `src/decision/hybrid_engine.py:815,831` **(V)**; `.env.example:91` sets `USE_HYBRID_DECISION_ENGINE=0` **(V)**). The dossier's H-01 "prod ON / CI OFF" split-brain is therefore resolved *in the opposite direction from its recommendation* — and ADR-008:45 codifies exactly this OFF-by-default posture. This ADR ratifies that outcome rather than the dossier's "explicit ON" recommendation.
2. **CI lane parity changed.** The D6 scenario lane no longer forces the flag OFF; it now "preserve[s] the caller's configured mode so D6 exercises the same mode as the serving path," supplying `1` explicitly in CI and defaulting it locally only when unset — and the graded axes (decision_state/hard_blockers/contradictions) are produced by the deterministic rule machine regardless (`src/evals/audit/snapshot.py:749-762` **(V)**). C-03 §5.4's "remove the forced-OFF block" is done.
3. **Payment mandates are no longer shadow.** The dossier (§2.4) recorded `src/financial/payment_mandates.py` as SHADOW with "no producer or consumer." Today it is consumed by `spine_api/services/payment_mandate_service.py`, `spine_api/services/authority_approval_service.py`, `spine_api/services/advisor_payout_store.py`, and `src/orchestration/booking_fulfillment.py` **(V)**, with a backing table (`alembic/versions/add_payment_mandates_table.py` **(V)**). ADR-008 §3's booking-fulfillment row ("auto only under a ratified payment mandate (F-04)") depends on it. Disposition changes ARCHIVE → WIRE (record 7).
4. **Settlement engine gained an orchestration caller.** `src/orchestration/irops_healer.py:15` imports `FinancialSettlementEngine` and `VirtualCreditCard` **(V)** (IR-ROPS auto-healer wave, 2026-09-06), moving it from ROUTER-ONLY to having a non-router consumer — but VCC issuance remains hash-seeded pseudo-issuance (`settlement_engine.py:109-110` **(V)**), and the consuming panel is SIMULATED-badged (record 16 constrains this).

---

## 4. Decision records

Each record: **Context** (what it is, code state, callers) → **Options** → **Recommendation (Proposed — pending owner ratification)** → **Consequences** → **Evidence that would change the decision**.

### Group A — WIRE (with prerequisites)

---

#### A1. Hybrid decision engine — keep wired; ratify OFF-by-default

**Status: Proposed — pending owner ratification (inherits ADR-008:45; ratifying ADR-008 §3 settles this record).**

**Context.** Cache → rules (incl. explicit `not_applicable` negative rules) → LLM fallback (Gemini primary, OpenAI fallback) → static default, with successful LLM decisions cached as future rules — the V02 graduation doctrine in executable form (`hybrid_engine.py:4-9,335,419-477`; deep map F-A4). 26 tests (`tests/test_hybrid_engine.py`); G-08 egress delimiting landed around it (`hybrid_engine.py:24,721,731`); per-agency usage guard + telemetry + health wired (`hybrid_engine.py:549-586,374-411`). **Callers (V):** integrated into the serving decision path behind the flag — `src/intake/decision.py:33-40` (read at call time), `decision.py:75-149` (`_generate_risk_flags_with_hybrid_engine`), `decision.py:1192`, `decision.py:2166`; plus `tools/validation/hybrid_engine_validator.py`. **Flag default is `"0"`** (PA-03, 2026-09-06): `decision.py:40`, `hybrid_engine.py:831`, `.env.example:91` **(all V)**. CI D6 lane preserves the caller's mode and supplies `1` explicitly in CI; graded axes are the deterministic rule machine's either way (`snapshot.py:749-762` **(V)**).

**Options.** (a) Wire now: flip default ON with CI parity (the 2026-09-02 dossier's recommendation). (b) Keep wired, default OFF, credential-gated opt-in per deployment until a hybrid-specific eval lane passes (ADR-008:45; current code state). (c) Archive the LLM half, keep only the rules.

**Recommendation.** **(b)** — keep wired; ratify OFF-by-default as the standing posture (supersedes the dossier's ON recommendation; PA-03 already implemented it and ADR-008:45 documents the contract: startup logs the effective rung when a credential makes it effectively `1`). The PER-0700 test is satisfied *because* rules + negative rules cover the six decision types deterministically first; the LLM is the last resort and each hit graduates to a rule. Prerequisites before any deployment opts in: a hybrid-specific eval lane proving hybrid risk flags ≥ legacy risk flags on the scenario corpus, and `src/decision/telemetry.py` fields bridged into `ExecutionEvent` metadata so `routing_health` grades the real tier/source/latency/cost (C-03 §6, release R3).

**Consequences.** Prod determinism is architectural rather than credential-accidental — the strongest possible answer to "which decisions may the system make alone." Cost: the graduation loop stays dormant until a deployment opts in, so LLM-graduated rules accumulate only in opt-in environments; `routing_health` remains null-input until R3 lands.

**Evidence that would change the decision.** A hybrid eval lane passing on the scenario corpus plus a deployment that actually opts in (→ consider default-ON); conversely, evidence that LLM risk flags under-perform the legacy `decision.py:1207-1211` risky-destinations set (→ strip to rules-only, archive the LLM half).

**Addendum 2026-09-11 — KDD eval lane commissioned (in progress).** The
hybrid-specific eval lane this row names as its prerequisite is now under
construction: `Docs/exploration/HYBRID_KDD_EXPERIMENT_2026-09-11.md` +
`scripts/run_hybrid_kdd_experiment.py` (arm A deterministic baseline vs arm B
per-model LLM-enabled, cold+warm cache passes, 35-record graded corpus).
Commissioning found and fixed three latent defects proving the orphan-rot
thesis of this ADR: broken `from llm import …` (LLM path had *never* been
reachable — `LLM_AVAILABLE` permanently False), an UnboundLocalError in the
`_call_llm` failure handler, and harness-adjacent flag-cache coupling
(`_reset_hybrid_engine()` now used per-arm). 39 hybrid tests green; arm A
baseline complete; arm B awaits a valid `OPENAI_API_KEY` (current key 401s —
124/124 attempts). No disposition change; this addendum records progress on
the row's own gate.

---

#### A2. Suitability Tier-3 LLM contextual scorer — WIRE, gated

**Status: Proposed — pending owner ratification (inherits ADR-008:49 "declare it PLANNED").**

**Context.** `src/suitability/llm_scorer.py` (334 L): contextual activity-suitability scoring with verdict schema, cache, injectable `llm_client` (`llm_scorer.py:65-71`). Serving tiers remain Tier-1 static catalog + Tier-2 itinerary coherence (`src/suitability/integration.py:235-280`); a Tier-3 *heuristic* pacing flag already exists (`integration.py:372-376`). 5 tests. **Callers (V):** zero production callers — `rg LLMContextualScorer` hits only `src/suitability/__init__.py`, the module itself, and `tests/test_suitability_tier3.py`. The authority boundary it must respect already exists: critical suitability flags force `STOP_NEEDS_REVIEW` + hard blocker (`src/intake/orchestration.py:418-436`).

**Options.** (a) Wire now behind the critical-flag escalation. (b) WIRE gated on a Tier-3 flag-quality eval lane, docstring `PLANNED` note now (ADR-008:49). (c) Archive.

**Recommendation.** **(b)** — wire behind the existing critical-flag escalation (the LLM only *adds* flags; STOP stays deterministic), but **not before the eval core produces a Tier-3 flag-quality lane** (golden fixtures where Tier-3 changes the verdict vs Tier-1/2; flag-level P/R vs advisor review; usage-guard + egress integration copied from the hybrid engine's pattern). Immediate zero-code action: record the deliberate exclusion in the suitability module docstring so the next audit does not re-discover it (ADR-008:49). Tier-1's blind spot is real — "73-year-old, recent surgery, 5-activity hill-country day" is invisible to a static catalog — so this is the repo's own deep-map recommendation (F-A10 rationale); it is sequencing that differs, not direction.

**Consequences.** Short term: silent under-flagging on the long tail continues (the pain the dossier names). After wiring: advisor review load increases by the true-positive flag volume; cost bounded by cache + usage guard.

**Evidence that would change the decision.** A completed C-04/eval-core lane showing net flag gain ≥ 0 on golden fixtures (→ wire immediately); evidence that Tier-1/2 coverage plus the Tier-3 *heuristic* flag already captures the long tail in practice (→ archive with a documented coverage study).

---

#### A3. Ghost concierge engine — WIRE LATER as agent-runtime scanner; delete the fake trigger now

**Status: Proposed — pending owner ratification.**

**Context.** `spine_api/services/ghost_concierge.py` (144 L): pure, deterministic `evaluate_flight_teletelemetry`-style classification — delay/cancellation, connection-cascade MCT math, intervention drafting (`ALERT_AGENT`, `NOTIFY_HOTEL_LATE_CHECKIN`, `SEARCH_FALLBACK_FLIGHTS`, `DRAFT_EU261_CLAIM`, `ghost_concierge.py:47-57`). 2 tests. **Callers (V):** zero production callers — only `tests/test_ghost_concierge.py` and the scenario tool `tools/generate_frontier_scenarios.py`. Meanwhile the live frontier pass still **mints fake ghost workflow ids** on `ESCALATE_RECOVERY`/`emergency` (`src/intake/frontier_orchestrator.py:83-86` **(V)**: `result.ghost_workflow_id = f"ghost_{packet.packet_id}_{uuid.uuid4().hex[:12]}"`), and the ghost CRUD router stores id-strings with no executor (`spine_api/routers/frontier.py:70-95`; deep map F-A3). The runtime already provides the scan→WorkItem→execute machinery with leases, idempotency, retry/poison states (`src/agents/runtime.py:581`; `agent_work_coordinator.py:20-60`), and the flight-status tool contract exists (`src/agents/live_tools.py:26`, env-templated providers `live_tools.py:412-441`).

**Options.** (a) Wire now as a runtime scanner/executor. (b) Wire later as agent-runtime scanner; archive the *trigger* (fake id-minting) now, keep the engine. (c) Archive both.

**Recommendation.** **(b)** — the disposition split the dossier got right. Keep `evaluate_flight_telemetry` (honest, tested, doctrine-compatible; in-trip disruption is the one genuinely time-pressured domain where an autonomous monitor pays for itself — deep map §5.2.3 rank #3). Delete or rebrand the fabricated `ghost_{id}` minting at `frontier_orchestrator.py:83-86` **now** — it is C-01's cheap-honesty action and the "both-and-hidden" class. Wiring prerequisites: live flight-data contract from the existing env-templated tool; interventions draft-only until an advisor sends; false-positive rate tracked; the CRUD router either backed by real WorkItems or retired.

**Consequences.** Nothing user-visible changes until wiring; the win is honesty (no "ACTIVE" ghost workflows). When wired, the runtime's lease/idempotency machinery carries the monitor with bounded authority.

**Evidence that would change the decision.** A contracted live flight-telemetry feed and a ratified agent-runtime slot (→ wire now); product decision that in-trip disruption is out of scope for the current product (→ archive engine + trigger together, retire `tools/generate_frontier_scenarios.py` per dossier open question 6).

---

#### A4. Retention enforcer — WIRE or annotate not-operating (owner picks; never leave as-is)

**Status: Proposed — pending owner ratification.**

**Context.** `src/security/retention_enforcer.py` (147 L): erasure/retention enforcement framed as GDPR Art-17 / DPDP SLA machinery. **Callers (V):** SHADOW — self-file only, `rg retention_enforcer` returns no other production module. This is the dossier's "worst kind of orphan": compliance-shaped code implies a legal control that does not run (dossier §2.4; G-13-class record risk).

**Options.** (a) Wire to the lifecycle/agent path now (small). (b) Keep code, demote docstrings to "design artifact — not operating," and record the gap in the findings store. (c) Archive.

**Recommendation.** **(a) preferred, (b) acceptable — owner call — (c) only if the compliance requirement itself is deferred.** If retention/erasure is a real obligation for the current product, wire the enforcer to the trip/customer lifecycle path as a scheduled or event-driven job (the runtime's lease machinery fits); if it is not yet an obligation, option (b) is mandatory honesty: code that cites Art-17 while running nowhere is a liability, not an asset. Never leave the framing as-is.

**Consequences.** (a) buys a real (auditable) erasure control cheaply; (b) removes the implied control from the record and makes the gap legible; both close the both-and-hidden state.

**Evidence that would change the decision.** Confirmation from product/legal that no erasure SLA applies to stored trips today (→ b); a ratified data-retention policy with SLAs (→ a, immediately).

---

#### A5. DLQ inspector — WIRE later (small, natural ops fit)

**Status: Proposed — pending owner ratification.**

**Context.** `src/agents/dlq_inspector.py` (124 L): inspection/reporting helper for dead-letter queue contents. **Callers (V):** SHADOW — self-file only. The runtime it would serve is real: `WorkStatus.POISONED` poison states exist (`src/agents/runtime.py:561` area; dossier row).

**Options.** (a) Wire later as an ops utility against the poison states. (b) Archive.

**Recommendation.** **(a)** — wire it when ops tooling for the agent runtime is next touched; it is small and matches an existing real mechanism. Until then it must not appear anywhere as if a DLQ process runs (no route, no panel).

**Consequences.** Minimal either way; the risk being managed is a future reader assuming dead-letter handling is operational.

**Evidence that would change the decision.** Poisoned WorkItems accumulating in production with no inspection path (→ wire sooner); runtime redesign that removes poison states (→ archive).

---

#### A6. Pre-departure cadence (`src/briefing/pre_departure_cadence.py`) — WIRE to Communicator (preferred); fallback ARCHIVE

**Status: Proposed — pending owner ratification (explicit product call).**

**Context.** 196 L cadence generator for pre-departure communications. **Callers (V):** SHADOW — self-file only. The runtime already registers a **Communicator agent** (18-agent registry, `src/agents/runtime.py:3150-3178`; deep map §5.1), making a cadence generator a natural agent output rather than dead code.

**Options.** (a) Wire as Communicator-agent output (draft-only, advisor-sends). (b) Archive.

**Recommendation.** **(a)** — cheapest honest path to value: the consuming agent exists, the output class (advisory briefings) is exactly R1/R2 territory (auto-prepared, human sends). Prerequisite: a product decision that pre-departure comms are in scope, plus the Communicator agent's output contract. If the owner declines the product call, **fallback = archive** — do not leave it parked indefinitely.

**Consequences.** (a) gives the Communicator agent a concrete, testable output type; (b) removes one more shadow module.

**Evidence that would change the decision.** Owner declines pre-departure comms scope (→ archive); Communicator agent gains a scheduled-output contract sooner than expected (→ wire immediately).

---

#### A7. Payment mandates — WIRE (in progress; dossier verdict stale)

**Status: Proposed — pending owner ratification (consistent with ADR-008 §3 booking-fulfillment row).**

**Context.** `src/financial/payment_mandates.py` (170 L) + `spine_api/models/payment_mandate.py`, `spine_api/services/payment_mandate_service.py`, migration `alembic/versions/add_payment_mandates_table.py`. **Callers (V):** no longer shadow — consumed by `spine_api/services/authority_approval_service.py`, `spine_api/services/advisor_payout_store.py`, and `src/orchestration/booking_fulfillment.py`; exposed via `spine_api/routers/financial_ops.py`. ADR-008 §3 gates booking-fulfillment autonomy on "a ratified payment mandate (F-04)" — i.e., this module is now load-bearing for the proposed R1 seam. The 2026-09-02 dossier's ARCHIVE verdict ("no producer or consumer") is **superseded by tree state** (§3.3 above).

**Options.** (a) Ratify the mandate ledger as the F-04 producer and finish the booking-fulfillment R1 wiring. (b) Archive anyway and find another mandate mechanism.

**Recommendation.** **(a)** — the supersession workflow points this way: the ledger has unique live consumers (authority approvals, payouts, booking fulfillment) that the dossier predates. Prerequisites: verify mandate lifecycle states against `booking_fulfillment`'s checks end-to-end (contract verification, not code-path assumption), and confirm `financial_ops` routes are operator-facing rather than demo-badged.

**Consequences.** Booking-fulfillment autonomy (ADR-008 R1) gains its intended authority token; leaving it un-ratified while consumers already exist recreates the both-and-hidden state one layer up.

**Evidence that would change the decision.** `booking_fulfillment` shown to be demo-surface-only with no runtime path (→ re-park); mandate states found diverging from what `authority_approval_service` checks (→ fix contract first, then ratify).

---

### Group B — LABEL+KEEP (simulated, honest, or already load-bearing)

---

#### B1. Frontier OS + Persona Council panels — LABEL+KEEP as dev/demo surfaces; wire-or-archive stays open, ratification closes the honesty question

**Status: Proposed — pending owner ratification (inherits ADR-008:57).**

**Context.** FrontierDashboard renders "ACTIVE" ghost workflows that are fabricated id strings (`frontier_orchestrator.py:83-86` **(V)**), simulated negotiation rows (`negotiation_engine.py:39-53`), and keyword-heuristic sentiment explicitly "advisory only" in-code (`frontier_orchestrator.py:58-63`). Persona Council drives real engines with hardcoded `trip_council_demo` (`PersonaCouncilPanel.tsx:68-168`). **Since the deep map, labels shipped (V):** `frontend/src/components/ui/SimulatedBadge.tsx` exists and is applied across `PersonaCouncilPanel`, `ProposalCompilerPanel`, `StressBenchmarkPanel`, `IROPSAutoHealerPanel`, `EpistemicPanel`, plus quotes/bookings/suppliers/proposals pages; a dedicated honesty test guards it (`frontend/src/app/(agency)/workbench/__tests__/simulated-panels-honesty.test.tsx` **(V)**). What remains open — per this ADR's charter — is wire-or-archive of the underlying subsystems.

**Options.** (a) Wire the panels to real subsystems (ghost executor, negotiation, Council on real trip ids). (b) LABEL+KEEP as sanctioned dev/demo surfaces (badges + honesty test), never operator authority; graduate or retire per-surface later. (c) Archive the panels now.

**Recommendation.** **(b)** — the labels + honesty test satisfy the never-both-and-hidden rule for the *surfaces*; ratify that status explicitly (ADR-008:57: "never operator authority"). Two carve-outs ride along and are **not** deferred: (1) the fake ghost-trigger minting is C-01's to delete (A3); (2) `routing_health` must stop claiming to measure a router until C-03 R2/R3 land (G-02; ADR-008:57 restates it). Re-decide per-surface when the corresponding real capability exists (ghost executor → A3; T1 router → C-03 R5).

**Consequences.** Demo value retained at zero honesty cost; the deferred wire-or-archive is now a *scheduled* decision tied to named prerequisites rather than an open question.

**Evidence that would change the decision.** Any panel shown to an operator as authority-bearing despite badges (→ archive immediately); a real subsystem landing that the panel can bind to with a trip-id contract (→ graduate that panel).

---

#### B2. Vision document extraction — status quo (wired, human-gated); the reference pattern

**Status: Proposed — pending owner ratification (ratification here means "confirm as the template").**

**Context.** `spine_api/services/extraction_service.py`: provider selection with default `noop` (`extraction_service.py:116-117` **(V)**; a model-chain primary path now precedes the legacy env fallback), invoked only from trip-documents upload/retry routes (`spine_api/routers/trip_documents.py:492,527`), schema validation, per-field confidence, cost tracking, provider fallback chain, review states `applied/rejected/pending_review` (`extraction_service.py:63-65,271,527`). The one place a model output enters trip state — only after operator approval (deep map §2.1 item 1).

**Options.** (a) Status quo. (b) Loosen the gate. (c) Archive.

**Recommendation.** **(a)** — confirm status quo and codify the shape ("model proposes → deterministic validation → human/authority decides → provenance recorded") as the mandatory template for every wire in Group A (C-03 §2 already adopts it for the router contract; A2, A3, A6 all cite it).

**Consequences.** None immediate; the template constraint pays off at each subsequent wire by preventing authority drift.

**Evidence that would change the decision.** Provider quality so high and eval lane so stable that a lower review rung is justified for specific field classes (→ revisit review posture per field, per deep map open question 5).

---

#### B3. Route geometry + pipeline bridge — already live; protect

**Status: Proposed — pending owner ratification (trivially confirmatory).**

**Context.** `src/logistics/route_geometry.py` (491 L) is LIVE: `haversine_distance` consumed by `src/agents/live_tools.py:661-662` **(V)** and, via `src/logistics/pipeline_bridge.py` (175 L), by the CI 30-scenario gate (`tests/evals/test_30_scenario_corpus_gate.py:8`) and journey smoke. Real deterministic logic, not simulation.

**Options.** (a) Protect as load-bearing. (b) Refactor away.

**Recommendation.** **(a)** — no action beyond protecting them as eval-lane dependencies in refactor planning. Recorded here only so the disposition register is complete.

**Evidence that would change the decision.** None expected; only a full eval-lane migration away from `RouteAssessmentBridge`.

---

#### B4. `checker_model` setting — LABEL+KEEP (fix the copy now; becomes the T1 knob at C-03 R5)

**Status: Proposed — pending owner ratification.**

**Context.** Stored, UI-editable, **never consumed at runtime (V)**: defined `src/intake/config/agency_settings.py:304` (`"gemini-2.0-flash"`), surfaced in `spine_api/contract.py:436`, `spine_api/routers/settings.py:762,805-806`, `frontend/src/lib/api-client.ts:809`, `AiAgentTab.tsx:343-344`; `rg checker_model` in `src/` finds no client call site **(V)**. The public checker path is deterministic. This is C-03's G-02 finding verbatim.

**Options.** (a) Leave as-is. (b) Fix UI copy to "applies once AI extraction is enabled" and wire it as the agency-scoped T1 model id when the router lands (C-03 §7, release R5). (c) Remove the knob.

**Recommendation.** **(b)** — the honest-label action now (same rule as IMP-03's sample-profile gating), the wire at R5. C-03 open question 4 (per-agency variance vs platform-pinned model) is an owner call to settle *at* R5, not now.

**Consequences.** Copy fix removes one " knob wired to nothing" surface; R5 wiring gives agencies real model choice only if C-03 open question 4 answers yes.

**Evidence that would change the decision.** An owner decision to pin models platform-side (→ copy fix + remove per-agency variance at R5); a T1 path that consumes the knob via any other setting name (→ dedupe before two knobs diverge).

---

### Group C — PARK (real logic, revisit trigger named)

---

#### C1. Logistics operations suite — PARK as libraries

**Status: Proposed — pending owner ratification.**

**Context.** `src/logistics/{connection_risk,rooming_list,fleet_allocation,timed_entry,accessibility}.py` (1,268 L total), 11 tests. ROUTER-ONLY: reachable via `spine_api/routers/logistics.py:18-35,134,150` **(V)** (import lines verified); real deterministic logic, no live feeds.

**Options.** (a) Wire now. (b) PARK; wire `connection_risk` into the ghost concierge when A3 wires (MCT math overlaps). (c) Archive.

**Recommendation.** **(b)** — deterministic-first test passes for the math itself, but there is no production consumer story today; the named trigger (ghost concierge wiring) is the cheapest first integration. Add `PARKED` docstring notes so the next audit doesn't re-discover them.

**Evidence that would change the decision.** A group/event product line that needs rooming lists or fleet allocation (→ wire those modules); A3 wiring (→ `connection_risk` joins it).

---

#### C2. MRZ parser — PARK as library (highest-quality orphan in the wave)

**Status: Proposed — pending owner ratification.**

**Context.** `src/intake/mrz_parser_engine.py` (183 L): genuine ICAO 9303 7-3-1 mod-10 checks (`mrz_parser_engine.py:70,133`). ROUTER-ONLY: `rg mrz_parser_engine` → `spine_api/routers/document_extraction.py:14` only **(V)**; nothing feeds it scans. Tests: `test_document_mrz_extraction.py` (3), `test_passport_mrz.py`.

**Options.** (a) Wire now (needs an OCR/scan source). (b) PARK; attach to vision-doc intake when the OCR/MRZ text path exists. (c) Archive.

**Recommendation.** **(b)** — the natural attachment point is B2's vision-doc path (passport scan → vision OCR → MRZ text → this parser → validated fields with confidence), which is exactly the B2 template. Until an OCR producer exists there is nothing honest to wire it to.

**Evidence that would change the decision.** Any document-intake work that emits raw MRZ text (→ wire into that path immediately); two quarters of no document-scan work (→ keep parked, refresh trigger).

---

#### C3. Group Pareto engine — PARK; revisit with the coordinator-group mode

**Status: Proposed — pending owner ratification.**

**Context.** `src/decision/group_pareto_engine.py` (161 L), 2 tests, real deterministic math. ROUTER-ONLY (`spine_api/routers/group_pareto.py:14`); note `src/orchestration/model_router.py:63` **(V)** already maps a `group_pareto` task_type to Tier-2 — a router mapping anticipating a producer that the serving path never invokes (router-only anticipation, not a caller).

**Options.** (a) Wire now. (b) PARK; revisit when `coordinator_group` mode ships (`packet_models.py:432-435`). (c) Archive.

**Recommendation.** **(b)** — the operating mode that would consume it is a data-model placeholder today. The `model_router.py:63` mapping should be annotated or removed when the tier ladder is implemented so the router doesn't reference a parked engine as if it were a live task producer.

**Evidence that would change the decision.** `coordinator_group` mode shipping (→ wire as its consensus step); mode removed from the packet model (→ archive).

---

#### C4. Charter aviation engine (+ empty-leg scraper) — PARK

**Status: Proposed — pending owner ratification.**

**Context.** `src/charter/aviation_engine.py` (357 L), 4 tests; sim, no fleet feed. ROUTER-ONLY (`spine_api/routers/charter_aviation.py`), plus a sibling scraper module `src/charter/empty_leg_scraper.py` **(V)**.

**Options.** (a) Wire now. (b) PARK behind a live-operator-feed trigger. (c) Archive.

**Recommendation.** **(b)** — without a feed it is a calculator presenting as a market capability; the premium-segment trigger should also name the operator/feed provider before any wiring.

**Evidence that would change the decision.** A contracted charter-operator or empty-leg feed (→ wire); premium charter segment descoped from the product roadmap (→ archive).

---

#### C5. Financial settlement engine — PARK, constrained

**Status: Proposed — pending owner ratification.**

**Context.** `src/fees/settlement_engine.py`: FX/interchange math real; VCC issuance is hash-seeded pseudo-issuance (`settlement_engine.py:109-110` **(V)**). Since the dossier, the engine has a new non-router caller: `src/orchestration/irops_healer.py:15` **(V)** imports `FinancialSettlementEngine` and `VirtualCreditCard` (IR-ROPS auto-healer wave); the IR-ROPS surface is SIMULATED-badged (`IROPSAutoHealerPanel` **(V)**, honesty test) and the engine remains reachable via `spine_api/routers/financial_settlement.py`. The Stripe Issuing adapter that would make VCC real is itself a simulator with a fake webhook HMAC (`spine_api/providers/stripe_issuing_adapter.py:84-90`; GM-03).

**Options.** (a) Wire now behind the current fake provider. (b) PARK, constrained: FX/interchange math may serve deterministic calculators (including IR-ROPS *proposal* amounts); VCC issuance wires only behind a real VCC provider, after the fake adapter dies (record 25). (c) Archive.

**Recommendation.** **(b)** — the new IR-ROPS caller makes (c) wrong, but (a) would ship a settlement *theater* under a compliance-adjacent name. Constraint is the point: pseudo-issued VCCs must never be presented as executed settlement in any surface, badged or not.

**Consequences.** IR-ROPS keeps its deterministic cost math while its settlement actions remain proposals; when a real VCC provider is contracted (and record 25's fake adapter is gone), this flips to WIRE with a real integration task.

**Evidence that would change the decision.** A contracted VCC provider + real adapter (→ WIRE); IR-ROPS scope dropped (→ re-evaluate archive).

---

### Group D — ARCHIVE (supersession or duplication noted)

Archive mechanics per dossier open question 3 (ratification item R-9): in-repo `Archive/` exists at the repo root **(V)**; doc deletion is prohibited by repo rules, so archival = move + pointer stub + `@deprecated` note, tests archived with code. Supersession analysis follows the repo's mandatory workflow (AGENTS.md §Supersession Workflow).

---

#### D1. Yield arbitrage (`src/yield_arbitrage/*`, 360 L) — ARCHIVE unless a real feed is contracted

**Status: Proposed — pending owner ratification.**

**Context.** Self-described simulator ("Simulates real-time multi-channel rate comparison", `rate_parity_engine.py:30`). **Callers (V):** SHADOW — `supplier_yield.py`'s `evaluate_supplier_yield_arbitrage` has no callers beyond its own file; `src/orchestration/model_router.py:63` matches the string only as a Tier-2 task-type mapping (anticipation, not invocation); production reach is `spine_api/routers/yield_arbitrage.py` (self-contained). 2 tests + benchmark tests. ADR `Docs/ADR_SUPPLIER_YIELD_ARBITRAGE_2026-07-29.md` is marked Accepted — the ADR-vs-reality gap is itself a supersession candidate (record it on archive). Panel↔backend contract mismatch already registered (N-04).

**Options.** (a) Keep parked. (b) Archive engine + panel; fix or delete the panel per N-04; annotate the ADR with a reality correction. (c) Wire behind a real bedbank/GDS feed.

**Recommendation.** **(b)** — archive unless a feed is contracted. The engine cannot produce real arbitrage without real channel data; keeping it any state other than archived-with-pointer invites "margin optimization" claims the system cannot back.

**Evidence that would change the decision.** A contracted bedbank/GDS feed (→ exhumation task becomes a WIRE); a customer segment where simulated yield quotes are an accepted demo (→ move to LABEL+KEEP with badges, which today it lacks).

---

#### D2. Telephony IVR bypass bot — ARCHIVE until a real telephony provider exists

**Status: Proposed — pending owner ratification.**

**Context.** `src/telephony/ivr_bypass_bot.py` (98 L), 3 tests, self-labeled simulator with invented DTMF trees (`ivr_bypass_bot.py:26-44,61`). ROUTER-ONLY (`spine_api/routers/ivr_bypass.py` **(V)**). The "Production Twilio Adapter" it would ride on is itself a simulator (`spine_api/providers/twilio_telephony_adapter.py`, present in `spine_api/providers/` **(V)**; GM-02).

**Options.** (a) Keep. (b) Archive until a real telephony provider + navigation-data source exists. (c) Wire.

**Recommendation.** **(b)** — two stacked simulations (bot on simulated provider) is pure both-and-hidden; archive with pointer, resurrect only when a real provider contract and a lawful navigation source exist (note: IVR navigation of third-party phone trees may also carry ToS exposure — flag at resurrection time).

**Evidence that would change the decision.** A real telephony provider integration with a legitimate data source (→ re-evaluate as WIRE).

---

#### D3. Corporate policy engine (`src/corporate/policy_engine.py`) — ARCHIVE until a corporate-travel segment exists

**Status: Proposed — pending owner ratification.**

**Context.** 181 L, shadow (self-file only **(V)**), tests inside `test_industry_blindspots_expansion.py`. Corporate-travel policy compliance has no segment, buyer, or settings surface in the current product.

**Options.** (a) Keep parked. (b) Archive with pointer. (c) Wire speculatively.

**Recommendation.** **(b)** — unlike the logistics suite, no adjacent capability (no ghost-concierge-style future consumer) gives it a wiring trigger; archive avoids a growing pile of segment-shaped orphans.

**Evidence that would change the decision.** Corporate-travel ICP added to the roadmap (→ exhumation → WIRE behind agency settings).

---

#### D4. Visa workflow (`src/documents/visa_workflow.py`) — ARCHIVE (two visa subsystems is drift)

**Status: Proposed — pending owner ratification.**

**Context.** 213 L workflow builder, shadow (self-file only **(V)**). Visa *risk* is already canonical in `src/decision/rules/visa_timeline.py` (199 L), which the serving decision rules actually consume. Keeping both invites divergent visa truth — the exact drift the no-duplicate-systems rule exists to prevent.

**Options.** (a) Keep both. (b) Archive `visa_workflow`, keep `rules/visa_timeline.py` as the single visa subsystem; salvage any unique check first. (c) Wire `visa_workflow` instead.

**Recommendation.** **(b)** — apply the supersession workflow: field-compare `visa_workflow` against `rules/visa_timeline.py`, merge any unique logic into the canonical rule module, then archive. The canonical consumer (`decision.py` rules import chain) already proves `visa_timeline` is live.

**Evidence that would change the decision.** A product need for traveler-facing visa *workflow tracking* (distinct from decision-time risk) (→ re-evaluate as its own WIRE with a named consumer).

---

#### D5. Perishable sentinel (`src/monitoring/perishable_sentinel.py`) — ARCHIVE

**Status: Proposed — pending owner ratification.**

**Context.** 143 L, 6 tests, shadow (self-file only **(V)**). Monitors perishable inventory — a domain the product does not have (trips are not stock).

**Options.** (a) Keep. (b) Archive.

**Recommendation.** **(b)** — no plausible in-product trigger exists; archive with pointer.

**Evidence that would change the decision.** Any inventory-bearing product line (unlikely for this product; treat as effectively permanent).

---

#### D6. Accounting export bridge (`src/accounting/export_bridge.py`) — ARCHIVE until an accounting integration is contracted

**Status: Proposed — pending owner ratification.**

**Context.** 156 L, shadow (self-file only **(V)**). Export formats for accounting systems with no contracted integration.

**Options.** (a) Keep parked. (b) Archive. (c) Wire speculatively.

**Recommendation.** **(b)** — export formats are cheap to regenerate but expensive to keep accidentally-wrong; archive, exhume on contract signature.

**Evidence that would change the decision.** A signed accounting integration (Tally/Zoho/QuickBooks-class) (→ WIRE).

---

#### D7. Epistemic engine (`src/intake/epistemic_engine.py`) — ARCHIVE (superseded)

**Status: Proposed — pending owner ratification.**

**Context.** Decay, conflict detection, JSON-LD proof-graph design (deep map F-A7). **Callers (V):** SHADOW — self-file only (`rg epistemic_engine` → module only; its test imports it). Superseded in practice by `Slot` provenance fields — `epistemic_status`/`authority_level`/`evidence_refs` on `src/intake/packet_models.py:151-164` — plus audit snapshots.

**Options.** (a) Keep as design reference. (b) Archive with pointer to `packet_models.py` Slot fields + audit store as the live implementation. (c) Merge back in.

**Recommendation.** **(b)** — the supersession comparison favors the Slot fields on every dimension (canonical, consumed, tested via packet validation). Record the supersession in the archive pointer.

**Evidence that would change the decision.** A ratified need for full proof-graph serialization (JSON-LD) beyond slot-level provenance (→ re-evaluate as a WIRE against the audit store).

---

#### D8. Epistemic arbiter (`src/intake/epistemic_arbiter.py`) — ARCHIVE-or-MERGE (merge first, then remove)

**Status: Proposed — pending owner ratification.**

**Context.** 163 L, 4 tests. ROUTER-ONLY (`spine_api/routers/epistemic.py` **(V)**) + `src/orchestration/proposal_compiler.py` **(V)**; **not in canonical intake**. Field-level duplication with what `Slot` already records (`packet_models.py:151-164`).

**Options.** (a) Keep both arbiter and Slot fields. (b) Field-by-field supersession comparison; merge any unique check into packet validation; then archive/remove. (c) Archive untouched.

**Recommendation.** **(b)** — step 2 of the supersession workflow is mandatory here because the arbiter has *some* live consumers (proposal compiler, router): audit those call sites, move unique checks into the canonical validation path, migrate `proposal_compiler`, then remove the arbiter. Note the consumer panels are SIMULATED-badged (`EpistemicPanel` **(V)**), which lowers migration urgency but does not remove it.

**Consequences.** One provenance implementation instead of two; `proposal_compiler` keeps behavior via the merged checks.

**Evidence that would change the decision.** Supersession comparison finding checks in the arbiter with no Slot equivalent and real downstream value (→ merge-first remains the plan; only the archive date moves).

---

#### D9. "Production" provider adapters (`spine_api/providers/{amadeus_enterprise,stripe_issuing,twilio_telephony}_adapter.py`) — ARCHIVE (move + rename; delete the fake HMAC now)

**Status: Proposed — pending owner ratification (GM-02/GM-03 hotfix class — recommend fast-tracking this one).**

**Context.** Three simulators **(V: all three files present)** living in `spine_api/providers/` — the directory where real clients will land — named "Production…", including a fake webhook HMAC verification (`stripe_issuing_adapter.py:84-90`). Tests: `test_production_provider_adapters.py`. These are the most dangerous orphans in the wave because they *impersonate the directory* (dossier §2.4 final row).

**Options.** (a) Rename in place. (b) Move to `Archive/` (or a clearly-named `simulators/` location per owner preference) + drop the "Production" prefix + delete the fake HMAC control; leave `providers/` empty until a real client exists. (c) Leave as-is.

**Recommendation.** **(b)** — never both-and-hidden is at its most literal here: a fake security control (HMAC that verifies nothing) must be deleted, not annotated; a simulator must not occupy the namespace of real clients. Archive with pointer; when a real Amadeus/Stripe/Twilio client is built, it starts from the real SDK in a clean `providers/`.

**Consequences.** `spine_api/providers/` becomes honestly empty; any code referencing the adapters breaks visibly at the move (call-site audit is part of the move task — the dossier records them as SHADOW, so expected callers are tests only; verify before moving).

**Evidence that would change the decision.** A live client for any of the three providers landing sooner than the archive (→ real client goes in `providers/`, simulator moves to `Archive/` in the same PR).

---

## 5. What ratification changes (cross-record effects)

1. **The both-and-hidden class closes.** After ratification + the first-action items (fake trigger deletion A3, retention framing A4, adapter move D9, checker_model copy B4), no asset in this register simultaneously claims liveness on a surface and lacks a production caller, and no simulated control (HMAC, erasure SLA, VCC issuance) remains presented as real.
2. **ADR-008 dependency.** Records A1, A2, B1 are settled by ADR-008 §3 ratification; ratifying both ADRs in one pass is the clean path.
3. **The dossier disposition register** (`C02` §4) is superseded by §2 of this ADR on ratification — specifically the hybrid posture (ON → OFF ratified), payment_mandates (ARCHIVE → WIRE), and settlement (PARK constraint added).
4. **Index maintenance:** `Docs/adr/ADR_INDEX_2026-09-02.md` §2 gains this file; the reality corrections (D1's Accepted-status yield ADR; D7's superseded engine) should be reflected there per the index's own rule.

## 6. Owner ratification checklist

- [ ] **R-1 — Hybrid engine posture (A1):** ratify OFF-by-default + credential-gated enrichment as the standing contract (or overrule PA-03 with explicit ON + parity lane). *Default recommendation: ratify OFF.*
- [ ] **R-2 — Retention enforcer (A4):** pick WIRE-to-lifecycle or annotate-not-operating. *Default recommendation: WIRE if any erasure SLA applies; else annotate.*
- [ ] **R-3 — "Production" adapters (D9):** approve the move+rename+HMAC-deletion hotfix. *Default recommendation: approve; fast-track.*
- [ ] **R-4 — Ghost concierge path (A3 + B1 carve-out):** approve deleting the fake trigger at `frontier_orchestrator.py:83-86` now, engine wired later as runtime scanner.
- [ ] **R-5 — Payment mandates (A7):** ratify the mandate ledger as the F-04 producer for the booking-fulfillment R1 seam (with ADR-008 §3).
- [ ] **R-6 — Pre-departure cadence (A6):** product call — Communicator-agent output (wire) or archive.
- [ ] **R-7 — Suitability Tier-3 (A2):** confirm PLANNED + docstring note; commit to the Tier-3 flag-quality lane as the wiring gate.
- [ ] **R-8 — Panels (B1):** ratify Frontier OS / Persona Council as labeled dev/demo surfaces, never operator authority; note the two carve-outs (ghost trigger, routing_health claim).
- [ ] **R-9 — Archive mechanics:** choose location convention (in-repo `Archive/` vs in-place `@deprecated`) and apply uniformly to D1–D9.
- [ ] **R-10 — Register upkeep:** extend `Docs/adr/ADR_INDEX_2026-09-02.md` with this file; record the reality corrections for the yield ADR (D1) and epistemic engine (D7).

---

*Drafted 2026-09-11 by PER-0700 (Agentic Systems Architect) from C-02/C-03 + the 2026-08-31 deep map, with `rg` re-verification of caller claims against the live tree. Documentation only — no code changed, no commits.*
