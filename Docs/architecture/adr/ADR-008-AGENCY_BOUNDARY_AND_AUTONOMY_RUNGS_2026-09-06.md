# ADR-008: Agency Boundary & Autonomy Rungs (2026-09-06)

**Status:** PROPOSED — exploration package E-A output (PER-0700). Ratification block at §6; nothing here is authoritative until ratified.
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
