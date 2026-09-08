# Sim-Surface Disposition Register (2026-09-06)

**Status:** exploration package E-F output (PER-0700). Extends [SIMULATOR_PROVIDER_TRUTH_AUDIT_2026-09-04](../review/SIMULATOR_PROVIDER_TRUTH_AUDIT_2026-09-04.md); consumes the 2026-09-03 map + 2026-09-06 drift addendum verdicts.
**Purpose:** one complete map of every product surface's reality tier, with a required action per surface, so ad-hoc honesty labeling stops regressing (the PA-01/PA-05/PA-25/PA-28 class). This register is the checklist that ends the class; each surface gets `TierMetadata`/badge/labeling **or removal**.
**Tier vocabulary** (canonical, `spine_api/core/reality_tier.py`): `REAL` · `CONNECTED_SANDBOX` · `DETERMINISTIC_PREVIEW` · `DATA_DEPENDENT` · `PLANNED`. Frontend display vocabulary (`SimulatedBadge.tsx:10-11`): `Sample data` (hardcoded fixture) · `Simulated` (deterministic backend simulator, no external calls/holds/issuance).
**Epistemic status:** tier assignments marked ✅ were verified read-only 2026-09-06 (code read / diff read / grep). Entries marked ◯ are inherited from the audited map/sweeps and not independently re-verified this pass. The tree is actively changing (parallel Phase-0 wave); re-verify a row before acting on it.

---

## 1. Backend routers / endpoints

### 1.1 Self-labeled via `RealityTier` (10 router files + inline endpoints) — ✅ verified by grep

| Surface | Tier | Labeling | Residual action |
|---|---|---|---|
| `irops_healer` | DETERMINISTIC_PREVIEW / PREVIEW_ONLY | reality-tier metadata, effect artifacts stripped | FE panel badge — covered by honesty test ✅ |
| `distribution` | PREVIEW_ONLY, `provider_connected: false` | same | none beyond FE badge ✅ |
| `gds_sandbox` | DETERMINISTIC_PREVIEW | same | none beyond FE badge ✅ |
| `financial_settlement` | DETERMINISTIC_PREVIEW | same; VCC tab proves no issuance call | none beyond FE badge ✅ |
| `fx_sentinel`, `crisis_ops`, `duty_of_care_radar` | tiered | metadata | verify each FE surface shows tier (◯) |
| `fulfillment` (parallel Phase-0 rewrite) | DETERMINISTIC_PREVIEW, `provider_connected: false` | tier travels on result (PA-05) | panel honesty copy — F-42 (in flight, same wave) |
| `price_lock` sentinel | DATA_DEPENDENT (real contract reads; fabricated fallback being removed per PA-06) | partial | PA-06 abstain-when-no-source |

### 1.2 Simulated, honestly named, **no tier metadata yet** — action: add `TierMetadata` or reality-tier field

| Surface | Reality | Evidence | Action |
|---|---|---|---|
| `negotiation` bargaining engine | deterministic game-theoretic sim, no counterparty | map §2.4 ◯ | tier field on responses |
| `charter_aviation` / `empty_leg_scraper` | deterministic sim | map §2.5 ◯ | tier field |
| `yield_arbitrage` / `yield_benchmark` | scans without live bedbank/GDS connectivity | GM-06 wire-or-archive list | tier field + wire-or-archive DECIDE |
| `ivr_bypass` | synthesized DTMF, no carrier — returns `"status":"success"` for calls never placed | PA-28 ✅ | `"status":"simulated"` + tier field |
| `stress_benchmark` | simulated load, no per-agency rate cap | GM-08 ✅ | tier field + rate limit |
| `itinerary_export` | live computation over a sample payload, standalone | drift addendum §1.5 ✅ | sample-payload disclosure on default route |
| `logistics` (8 endpoints) | deterministic local computation, no external provider | drift addendum §1.5 ✅ | tier field (computation is real; data is trip-local) |
| `proposal_compiler` compile | deterministic sim engines over fabricated sample inventory; **mints signed share tokens** | PA-25 ✅ | tier in token payload; token only when inventory is real |

### 1.3 Fabrication-class defects — action: de-fabricate (owned by parallel Phase-0 wave, in flight)

| Surface | Defect | Fix in flight |
|---|---|---|
| `journey_graph` public + tenant routes | synthesized confirmed-itinerary DAG when no stored graph; public route unauthenticated | PA-01/F-41 — verified in working diff 2026-09-06 ✅ |
| `public_proposals` accept | acceptance stored only in process-local registry | PA-02 — in flight ✅ |
| `booking_fulfillment` | self-asserted `FULFILLED_CONFIRMED`, nonexistent TripStore calls | PA-05 — in flight ✅ |
| `ProposalCompilerPanel` + companion | live-theater copy over simulated effects | F-42 — in flight ✅ |
| `corporate_policy` override | self-certifying approver, no dual-control | PA-26/F-03/EV-08 — **not started** |
| `feedback` survey + scorecard | fabricated URL, no ingestion, demo-static scorecard | F-36 honest layer done; ingestion open (E-10) |

### 1.4 Landed but unwired (`PLANNED` in tier vocabulary) — action: wire-or-archive DECIDE, do not badge as live

`src/financial/margin_engine.py` · `src/accounting/export_bridge.py` · `src/agents/debate_council.py` · `src/concierge/messaging_router.py` · `src/logistics/pipeline_bridge.py` · `src/logistics/irrops_healer.py` (duplicate, zero consumers) · `src/adapters/stripe_issuing_adapter.py` (zero callers besides simulated fulfillment) · `perishable_sentinel` (orphaned) · `retention_enforcer` (declared-only, PA-31) · `model_capability_router` (PA-35/G-02) — all ✅ zero-non-test-consumers verified in drift addendum §1.5 / GM-06.

### 1.5 Real (no tier metadata needed; listed so the register is complete)

Intake spine pipeline (deterministic rules, no LLM in path) · run lifecycle + file ledger · `TripStore` persistence + status invariant + status history · auth/tenancy/RLS · D6 gating eval lanes (`budget`, `colloquial`) · lifecycle read-model (`trip-lifecycle.ts`, `/stats`) · idempotency (SQL backend + fencing) · agent leases (SQL backend) · escalated queue (I-1) · inbox projection · field-merge precedence · collection tokens (CAS gap open: PA-16).

---

## 2. Frontend surfaces

- **Badged (23 files consume `SimulatedBadge`) ✅** — all major workbench panels incl. GDS Sandbox, Negotiation, CrisisEvacuation, IVR, FinancialSettlement, IROPS, Distribution, PersonaCouncil, Yield, Charter, RouteLogistics, MemoryArchitect, Epistemic, PacketPanel synthesized slots (`derived_signal @0.6`), bookings/suppliers/proposals pages. CI-enforced by `simulated-panels-honesty.test.tsx`.
- **Gap: ProposalCompilerPanel not in the honesty test** (F-42, gate hole — test coverage in flight with the panel rewrite ✅).
- **Gap: tier metadata from backend is not systematically rendered** — panels show badges but ignore per-response `reality_tier` fields; action: single shared renderer that prefers response tier over the static badge (small, one component + adoption).
- **Gap: `JourneyGraphVisualizer` and companion** consume the journey-graph routes — must render the abstention state honestly (in flight with PA-01).
- **Trusted/real surfaces:** workbench intake/packet/safety tabs, trips lifecycle chip, inbox, payments queue, settings — no badge needed (◯ spot-check remaining).

## 3. Disposition rules going forward (the part that ends the class)

1. **New backend surface ⇒ tier field mandatory.** No router ships without a `reality_tier` (or an explicit `REAL` declaration) in responses; startup route inventory asserts presence for non-real tiers.
2. **New FE surface consuming a non-REAL tier ⇒ `SimulatedBadge` + honesty-test row mandatory** (`simulated-panels-honesty.test.tsx` is the enforcement seat — every new panel adds a block).
3. **Response tier overrides static badge.** The shared renderer (§2 gap) becomes the only badging path; static badges are fallback, not source of truth.
4. **No credential-backed identity for synthetic data** — share tokens/capability tokens mint only for real inventory (PA-25).
5. **Unwired modules declare `PLANNED`** in their docstring and in `tools/`-checkable inventory; a module with zero non-test consumers cannot be described in present tense anywhere (GM-06 / G-14 rule).
6. **CI:** extend the findings-register/lint gate family with a tier-presence check when route inventory next regenerates (cheapest enforcement seat; not built yet).

## 4. Open items exiting this exploration

- PA-26/EV-08 corporate-policy de-fabrication (no owner wave yet)
- TierMetadata on `negotiation`/`charter`/`yield`/`ivr`/`stress`/`logistics`/`itinerary_export` (small IMPLEMENT, mechanical)
- Shared FE tier renderer (small IMPLEMENT)
- Wire-or-archive DECIDEs per §1.4 (C-01/C-03/PA-35 family — see ADR-008)
- Spot-check ◯ rows before relying on them
