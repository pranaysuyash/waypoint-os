# ADR-008: Agency Boundary & Autonomy Rungs (2026-09-06)

**Status:** PARTIALLY RATIFIED — item 1 ratified 2026-09-09 (implemented: AgencySettings.money_execution_mode tri-state, default fully_human, enforced in booking_fulfillment + payouts); items 2–7 AMENDED AND RATIFIED 2026-09-14 by owner-directed council (PER-0700 lead + memory/LLM-governance/skeptic seats) — see §7 amendments and Docs/architecture/EXTRACTION_REALIGNMENT_BLUEPRINT_2026-09-14.md Addendum 9. Full record: five-seat council re-derived every item against post-ADR evidence; two items falsified as written (hybrid envelope contradiction; routing_health phantom pipeline).
**Context:** the PER-0700 audit found the agency boundary is enforced *by accident* — determinism is credential-conditional (PA-03), the governance registry and dual-control keeper had zero enforcement callers (PA-08), and the DECIDE backlog (C-01…C-04, PA-36, PA-18, G-03) poses the same question four separate times: *which decisions may the system make alone, which need a human, and what seam enforces that?* This ADR answers once.
**Numbering note:** ADR-003…005 are absent from `Docs/architecture/adr/` (G-15); 008 is the next free number regardless.

---

## 1. Principle (first-principles)

**A rung is real only if a named enforcement seam executes it.** Autonomy that lives in docs, dashboards, or defaults is decoration (the audit's PA-08 finding). Every capability therefore gets: a rung, an enforcing seam, and an audit event at the seam — or it is not autonomous at all.

## 2. The rung model

| Rung | Meaning | Enforcement seam (exists today?) |
|---|---|---|
| **R0 human-only** | System proposes; a human must act | UI-only actions, refund/compensation disposition (F-16) |
| **R1 approve-per-action** | Auto-prepared, human approves before execution | ✅ dual-control (`AuthorityGateKeeper.evaluate_action_authority`, `boundary_engine.py:322`) — **unwired until PA-08 lands** |
| **R2 auto + review queue** | System acts; action lands in a human review queue | ✅ NB02/D1 `effective_action = review` (`src/intake/gates.py:58-62`) |
| **R3 auto + post-hoc audit** | System acts; humans audit after the fact | ✅ D1 `auto` + audit events; registry budget caps (PA-08 seam) |
| **R4 full-auto** | No human in the loop, ever | Intake classification only — inside gate invariants (`STOP_NEEDS_REVIEW` always blocks) |

Safety invariant (non-negotiable, already implemented): safety-critical flags and `STOP_NEEDS_REVIEW` can never be auto-suppressed at any rung.

## 3. Proposed canonical rung per capability

| Capability | Rung | Enforced by |
|---|---|---|
| Intake extraction / decision / strategy | R3 | NB01/NB02 gates + D1 policy; hybrid engine only as credential-gated enrichment (§4.1) |
| Suitability scoring | R3 | deterministic scorer; Tier-3 LLM scorer archived/dormant (§4.2) |
| Proposal compilation | R3 (R2 for high-margin or low-confidence packages) | feasibility gate + tier metadata |
| **Traveler acceptance** | — (human act, R0 by definition) | e-sign consent; durable recording (PA-02) |
| **Booking fulfillment** | **R1 default** | governance registry `enforce_action_authority` (now wired) **+** durable acceptance check (PA-02) **+** verify-after-execute (PA-05) **+** auto only under a ratified payment mandate (F-04) |
| **Payouts, refunds, VCC issuance, settlement** | **R1** | dual-control keeper wired at the same seam (PA-08) + mandate ledger (F-04) |
| Price-lock re-lock | R2 | sentinel proposes; re-lock executes only with version + idempotency + real rate source (PA-06) |
| Escalation resolve | R0 | human-only by design (`escalated` never sync-promotes — already enforced in the status invariant) |
| Operator overrides | R0 input | feed override learning (existing loop) |
| Corporate policy override | R1 | authenticated approver + role + dual-control over threshold (PA-26 — **open**) |
| Frontier / Persona Council / dev demos | n/a | not autonomy — labeled simulations (see sim register §1) |

## 4. Ratifying the four repeated questions

### 4.1 Hybrid decision engine default (PA-03, G-03, supersedes map §8 wording)

**Proposed:** *deterministic core + credential-gated enrichment* is the documented contract. `USE_HYBRID_DECISION_ENGINE` defaults `"0"` in prod deployment envelopes (fly.toml, docker-compose); when a credential makes it effectively `"1"`, startup logs the effective rung in one line (`decision path: hybrid/LLM enrichment ACTIVE — rung R3`). CI keeps running both modes explicitly. The 2026-09-03 map's "orphaned, default off" note and G-03's wording are superseded by this ADR on ratification.

### 4.2 Suitability Tier-3 LLM scorer (PA-36)

**Proposed:** keep the code, declare it `PLANNED`, and do not wire it until (a) the memory read-path (4.3) and (b) cost-per-outcome attribution (E-C) exist — an LLM scorer without cost attribution or calibrated labels is ungovernable. Record the deliberate exclusion in the suitability module docstring so the next audit does not re-discover it.

### 4.3 Memory read-path (PA-18, sharpens F-13)

**Proposed:** wire the **two named slot points** (question generation and suitability preference context) behind confidence gates, after the E-D slot spec lands. Preference memory feeding question generation is the highest-value, lowest-risk first read. Forgetting/GDPR paths gain their enforcement purpose at the same time. If E-D is not ratified within the current planning cycle, archive instead of leaving a write-only machine.

### 4.4 Frontier / Persona Council / model router / SLM (C-01…C-04)

**Proposed:** Frontier and Council remain **labeled dev/demo surfaces** (they already carry badges + honesty tests) — never operator authority. `routing_health` metrics stop claiming to measure a router (G-02): either implement the minimal tier ladder (deterministic → cached → LLM, which `hybrid_engine.py` already embodies) or rename the metric. SLM posture (C-04) waits for E-C cost data — no benchmark target without a cost model.

## 5. What this ADR does **not** decide

Product contracts (D-01…D-04), signup/business model (R-09/R-10), payment-execution connectivity (NG-02…NG-04 stay no-go), and the retirement of specific theater components (PA-35 — follows the supersession workflow, separate task).

## 6. Ratification block (owner)

| # | Decision | Default if unanswered |
|---|---|---|
| 1 | **RATIFIED 2026-09-09 (owner, with amendment):** money path becomes a **per-agency tri-state setting** — `money_execution_mode: fully_human \| hybrid \| fully_autonomous` in agency settings. **Default `fully_human`**: every booking/payout/refund/VCC movement requires an authenticated human operator as the approving principal (recorded in audit); the system never moves money alone. `hybrid` = auto within governance-registry caps + required payment mandate (F-04); `fully_autonomous` = auto under registry authority, mandate recorded not required. All three modes are built into the backend contract; the settings UI exposes **only `fully_human` for now** (the other two are valid API values, hidden until product-ready). Supersedes the env-flag approach (`SPINE_API_REQUIRE_PAYMENT_MANDATES` becomes the pre-setting fallback, removable once the setting lands). Enforcement seam: fulfillment + payouts + settlement read the trip's agency mode; violations → 403 escalation-required with the approver-identity requirement stated. | — (DECIDED) |
| 2 | Hybrid engine: prod default `"0"` + startup rung log | stays credential-accidental |
| 3 | Tier-3 scorer: `PLANNED`, unwired until 4.3+E-C | stays silently dormant |
| 4 | Memory read-path: wire two slot points post-E-D, else archive | stays write-only |
| 5 | Frontier/Council: labeled demo surfaces, never authority | current ambiguity persists |
| 6 | Model router: implement minimal tier ladder **or** rename `routing_health` | metric keeps lying |
| 7 | Fulfillment/payouts/refunds: **R1 default**, auto only under F-04 mandate | money path stays auto (not recommended) |

On ratification: update the map honesty section + G-03 wording, wire §3 rows into the enforcing seams (PA-08 completion = the R1 seam), and record the decision per doctrine §16.9.


---

## 7. Ratification amendments (2026-09-14, council — blueprint Addendum 9)

The owner-directed council re-derived items 2–7 against post-ADR evidence.
Amendments supersede the §6 defaults. Evidence: five independent seat
reports, file:line-verified 2026-09-14.

| # | Amended decision | Enforcement seam | Reopen trigger |
|---|---|---|---|
| 1 | Money tri-state stands. AMENDMENTS: approving principal bound to the JWT user at the fulfillment router (client `holder_id` ignored — the client-asserted denylist passed the fully_human gate by default); payouts read + refuse on the mode; audit event on mode change; mode read-only exposed; settlement/refunds read the mode **when executors exist** (none today — overclaim corrected) | `booking_fulfillment.py` (positive `user:` principal check), `subagent_payouts.py` (mode read), `agency_settings.save` (change audit) | Any money movement without a mode read; any non-fully_human value in the store |
| 2 | **Declared posture, zero implicit defaults.** Dockerfile no longer bakes `=1` (it silently made Fly prod hybrid-ON while its comment claimed deterministic); fly.toml pins `"0"` explicitly (real traveler data; X-09 PII-egress gate open); compose/render explicit `0`; CI `"1"` deliberately exercises hybrid (eval envelope); **startup rung log landed** in server lifespan | Startup rung log in `server.py` lifespan | PII-egress gate closes → opt-in review with KDD benchmark (champion F1 0.808, ₹0.09–0.28/run); any envelope observed running a mode different from its declaration |
| 3 | Tier-3 stays **PLANNED, unwired**; gate rewritten: drop 4.3 coupling (E-D forbids memory-feeding-suitability); wire requires (i) suitability-surface corpus ≥50 verdicts graded via the KDD harness at pre-registered thresholds, (ii) E-C decision_id + cost rollups, (iii) shadow run ≥ +0.05 marginal F1 on the trigger band. **PLANNED docstring landed** in `llm_scorer.py` | Zero non-test importers (holds); import test added | Graded suitability corpus + thresholds met → shadow activation; any wiring without them → revert |
| 4 | **WIRE** (archive branch struck — E-D spec + E-10 governed write path landed; the write-only machine no longer exists). Slot 1: promotion-only question reorder in `strategy.py`, shadow-first (`MEMORY_SLOT_READ_MODE`, default shadow, audit events). Slot 2: E-D display-only FreshnessCard (suitability is a NON-slot). Preconditions: import-containment test (landed: `tests/test_memory_slot_wiring.py`), X-14 purge propagation (**landed 2026-09-15**: `test_x14_gdpr_forget_propagates_to_slot_candidates` + HTTP forget-propagation e2e), close the hydrate-trip GDPR leak (**closed 2026-09-15**: hydrate is display-only — durable-store-primary facts labeled `source: memory` + `observed_at`, registry fallback labeled, never writes the packet; supersedes the packet-mutating prototype). Store-sharing hardening the same day: `get_memory_store()` singleton — the whole-file-rewrite save path made per-consumer `MemoryStore()` instances lose each other's writes (silent data loss) and forget never reached other instances' caches. **Slot 2 end-to-end landed 2026-09-15**: `memory_on_file_facts()` (one freshness policy, display dedupe), BFF routes + `OnFileMemoryCard` chips with purge affordance on the decision page, `/remember` room_preference durably ingested (passport fields deliberately excluded — PASSPORT_MRZ 30-day SLA). **Shadow-window review contract landed 2026-09-15**: `src/memory/slot_review.py` (`python -m src.memory.slot_review`) — per-ask audit events carry the asked set (true promotion-rate denominator); pre-registered guardrails G1–G4 with automation-usable exit codes; flip = REVIEW_READY + owner-set `MEMORY_SLOT_READ_MODE=active`. Remaining: run the window, owner flip decision; chips render once trips carry resolvable identity (X-09) | `src/memory/slot_candidates.py` — the sole sanctioned read seam | Any inventory/price/selection influence (E-D invariant) = immediate revoke; trust-weighting regression = unwire |
| 5 | Ratified as written — badges + honesty CI + tier gate real. Amendment: `frontier.py` responses carry `reality_tier` = PLANNED + TierMetadata (register rule 1) | `SimulatedBadge` + honesty test + backend tier field (landed) | Any frontier surface touching a real provider/credential without tier metadata |
| 6 | **Implemented: producer wired + rename.** `src/decision/route_health.py` evaluates rolling decision-route metrics (fallback/error rates) after every `telemetry.record_decision`; emits deduped alerts via the existing paging logger. Renamed honestly: event types `decision_route_health_alert`/`_paging_alert`; legacy types readable via alias; `log_decision_route_health_alert` canonical, old name aliased | The telemetry→route_health seam (landed); legacy_ops accepts both types | Alert events without a decision-path source = phantom again; hybrid engine archived → seam void |
| 7 | SLM **HOLD retained, reason replaced** (cost model + venue data landed, so the old reason is stale): experiment cost ≠ production cost-per-outcome; no routing seam. **Ratified benchmark:** F1 ≥ 0.8, ≤ 3s/call, ≤ ₹0.50/run on the KDD fixture — deployment re-enters as a check when E-C rollups + the item-6 seam exist | Item-6 seam + E-C rollups (both open) | Benchmark met + seams exist → deploy review |

### 7.1 Missing rungs registered (landed post-ADR)

- iROPS auto-heal loop → proposed **R3 sim-tier**; hard rule: any real-provider
  healing action inherits the agency tri-state at that seam.
- Agent memory write loop → **R3**; seam = eligibility gate (confidence ≥ 0.75).
- Trip lifecycle write gate (Addendum 8) → §2-class invariant; LOG→RAISE
  graduation per the distribution harness.
- **Fulfillment lifecycle precondition (RAISE-class):** money moves only from
  approved / booking_in_progress / booked (+ change_requested/in_trip flows) —
  landed in booking_fulfillment, cross-links Addendum 8's machine to the money
  seam.
- §3 staleness fixes: PA-08 landed (R1 real); PA-26 landed (corporate-policy R1
  real, unconditional dual-control); price-lock is honestly **R0+preview** until
  a real rate source lands (R2 was decoration).

### 7.2 Residual execution receipt (PER-0700 lead re-verification pass, 2026-09-14)

Post-council drift re-verification: every §7 seam was re-derived against the
live tree this session (file:line-checked), then the residuals this pass found
were executed. The council's item-1 correction is confirmed in-tree: no real
settlement/payout executors exist (`financial_settlement` is honest
DETERMINISTIC_PREVIEW with `operational_write: false`; the iROPS VCC call sits
in the orphaned `irops_healer` — zero consumers), so the settlement seam stays
correctly conditional per the §7 table.

**Residuals found and fixed in this pass:**

1. `Dockerfile.spine_api:11` still baked `USE_HYBRID_DECISION_ENGINE=1` — the
   wave fixed the main Dockerfile but missed the alternate prod image, so any
   envelope built from it silently ran hybrid-ON (the exact accident §7 item 2
   ends). Fixed to `=0`. Root cause of the miss: the envelope test covered only
   fly.toml/compose. New regression seat:
   `test_no_dockerfile_bakes_hybrid_on` (both Dockerfiles must declare `0`
   explicitly and never `1`). FND-0294 opened + closed with evidence.
2. `frontier.py` item-5 amendment was only partially landed: ghost-workflow
   endpoints carried `reality_tier` + TierMetadata, but `/emotions/log` and
   `/intelligence/report` returned untiered payloads, and the
   `GhostWorkflowResponse` default tier `"simulated"` was outside the canonical
   `spine_api/core/reality_tier` vocabulary. Fixed: emotions → DATA_DEPENDENT
   (real storage, no mitigation consumer), intelligence pool → PLANNED (no
   retrieval consumer), default aligned to `"planned"`. Regression seats added
   in `TestFrontierRealityTiers` (every handler declares tier + TierMetadata;
   vocabulary canonicity; honest tier choice).

**Seam re-verification (all file:line-checked this pass):**

- Item 1: positive `user:` principal gate `booking_fulfillment.py`; payouts
  mode read + refusal `subagent_payouts.py`; mode-change audit
  `agency_settings.py`; read-only exposure `settings.py` GET autonomy.
- Item 2: all four serving envelopes explicit `0` (now including
  `Dockerfile.spine_api`); startup rung log live in `server.py` lifespan.
- Item 3: PLANNED docstring + gate in `llm_scorer.py`; zero non-test importers.
- Item 4: `src/memory/slot_candidates.py` sole seam; slot 1 shadow hook in
  `strategy.py`; containment + audit tests in `test_memory_slot_wiring.py`.
- Item 6: `src/decision/route_health.py` fed from `telemetry.record_decision`;
  legacy alias handling in `legacy_ops.py`.

**Verification:** `ruff` clean on all touched files;
`pytest tests/test_frontier_tenant_isolation.py tests/test_pa_agentic_remediations.py`
= 62 passed; money/memory seam suites (lifecycle, mandate ledger, slot wiring)
= 55 passed; slot-wiring file x10 green.

**Open from this pass:** FND-0293 (P3, open) — one unexplained flake of
`test_strategy_hook_emits_audit_event` (`len(events)==1` failed once in a trio
run; 16 subsequent greens; correlated 72.5s outlier suggests load sensitivity;
no lock/retry/provider path found; no guess-fix applied). Reopen on recurrence
with captured output.

**Docs:** the 2026-09-06 map-drift addendum's "hybrid default ON" entry now
carries a dated correction pointing here (the entry described the envelope
accident as if it were the posture).
