# DD-5: Frontier Simulation Boundary — Deep-Dive

**Date**: 2026-08-01 · **Parent**: `Docs/LAUNCH_AUDIT_BASELINE_2026-08-01.md` (B6, Theme 1)
**Evidence tier**: Tier 1–2 (static trace from trigger → fabrication → persistence → UI surface).
**Framing**: motto §0.12.4 — cut/keep/finish anchored to long-term product shape. Nothing here is "bad code"; it is **unannounced simulation on surfaces that imply reality**.

---

## S0 — The core finding, stated plainly

Waypoint OS's long-term vision (the 2026-07-29 ADR batch) includes autonomous negotiation, a ghost concierge, federated risk intelligence, and supplier yield arbitrage. The code contains all of these — **as simulations that present themselves as real in API responses, operator UIs, settings toggles, and in one case the audit trail.** An agency operator cannot tell from any surface that these are simulated.

## S1 — Inventory of simulated surfaces

| # | Surface | What it fabricates | Where it shows up | Evidence |
|---|---------|--------------------|--------------------|----------|
| 1 | Negotiation engine | Invented suppliers (`Grand {dest} Hotel`, `Premium Lounge Services`), hardcoded prices (1200→950), `status: NEGOTIATING`, `last_message: "Sent automated RFP"` | `frontier_result.negotiation_logs` → run status → workbench; settings toggle `enable_auto_negotiation` (default **True**, pro/enterprise tiers) | `src/intake/negotiation_engine.py:34-90`; `config/agency_settings.py:295,380,391` |
| 2 | Ghost Concierge (pipeline) | `ghost_workflow_id` minted, logged, never persisted or executed; `ghost_triggered=True` propagates | `decision.rationale["frontier"]` → run detail → SafetyTab/workbench | `src/intake/frontier_orchestrator.py:84-86`; `src/intake/orchestration.py:467-477` |
| 3 | Ghost Concierge (router) | Disruption "detection" = keyword match on `agent_notes` ("delay"/"cancel") → fabricated recommendation ("Auto-rebook to next available direct flight departing in 2h") | `POST /api/v1/concierge/monitor/{trip_id}` | `spine_api/routers/concierge.py:41-63` |
| 4 | **Auto-rebook** | Hardcoded `Flight AF128 (SFO -> CDG) - Seat 14A`, fake PNR, `status: REBOOKED` — **and writes `autonomic_rebook_executed` to the AuditStore** | `POST /api/v1/concierge/auto-rebook/{trip_id}` + the audit chain | `spine_api/routers/concierge.py:82-104` |
| 5 | Yield arbitrage | Three hardcoded supplier options with invented economics ("Direct Preferred Resort Contract" 18% commission, "Amadeus GDS" 12%, "Hotelbeds" 10%) computed off `budget_max` | `GET /api/v1/yield/arbitrage/{trip_id}` → YieldArbitragePanel; `POST /swap-supplier` mutates the trip on this basis | `spine_api/routers/yield_arbitrage.py:38-71` |
| 6 | Federated intelligence | Process-local `list` — "In-memory mock for now"; incidents vanish on restart, never federated | `frontier_result.intelligence_hits` | `src/intake/federated_intelligence.py:31-33` |
| 7 | Sentiment monitoring | Heuristic score; module docstring admits "do not use for production decisions" — yet it surfaces in decision rationale and can trigger `anxiety_alert` | `decision.rationale["frontier"]` | `src/intake/frontier_orchestrator.py:57-61` |
| 8 | Checker agent | Pure heuristics labeled a "Checker agent" simulation; drives `requires_manual_audit` | frontier audit path | `src/intake/checker_agent.py:22-27` |
| 9 | Trust scorecard | Hardcoded `safety_score=96`, invented highlights ("2.5h connection buffer", "resort fees included"), invented badges | DD-1 F2 | `spine_api/routers/trust_scorecard.py:58-86` |
| 10 | Proposal demo fallback | Entire fake proposal for unknown tokens | DD-1 F2 | `trust_scorecard.py:159-183` |
| 11 | High-value gate check | On agency mismatch substitutes a hardcoded demo dict | (also a tenancy smell) | `spine_api/routers/team_workflows.py:122-125` |

## S2 — Why S1-4 (auto-rebook audit event) is the worst item

The audit trail is the product's trust backbone — the 2026-07-29 ADR_RULE_015 adds **audit chain hashing** (`persistence.py:1944-1953`) precisely so operators can trust the record. `auto-rebook` writes `autonomic_rebook_executed` for a booking that never happened. Once chain-hashing is live, fabricated events become *cryptographically preserved* fabrications. **No operator action, no audit event — this must hold unconditionally.** Fix: do not write the audit event until a real rebooking provider confirms; until then the endpoint must return "not available" or be gated off.

## S3 — Cut / Keep / Finish (motto §0.12.4, anchored to long-term shape)

The long-term product shape wants these real — boutique agencies *will* pay for negotiation and disruption handling. So "cut the code" is wrong; "ship as-is" is dishonest. The boundary must be made explicit, then each feature finished in discovery-driven order.

**KEEP the code, GATE the surfaces (launch posture, ~2-3 commits):**

1. Change tier defaults: `enable_frontier_orchestration`, `enable_auto_negotiation`, `enable_checker_agent` → **False at every tier** until the feature is real (`config/agency_settings.py:361-395`; the `starter` tier already does this — extend it).
2. Gate the routers: `/api/v1/concierge/*`, `/api/v1/yield/*` return `501 not_available_in_beta` unless an explicit `ENABLE_SIMULATED_FEATURES=1` dev flag is set.
3. Contract-level honesty: any response field that can carry simulated content gets `"simulated": true` (baseline Theme 1 fix) — so future mistakes are machine-detectable, and the UI can badge it.
4. Settings UI: hide or "Coming soon"-badge the toggles (`AiAgentTab.tsx`) so agencies can't enable simulations.
5. S1-4 audit-event fix regardless of gating (it fires only when the endpoint is called, but the guard must be structural, not incidental).

**FINISH in discovery-driven order (post-launch, one ADR each):** disruption monitoring (real flight-status feed) > negotiation (needs supplier connectivity — hardest) > yield arbitrage (needs real rate/commission sources) > federated intelligence (needs multi-tenant volume). Customer discovery (open, per operator) should pick the first.

**CUT now:** the demo fallbacks (S1-9/10/11) — these are not "unfinished features," they are fabricated data on live surfaces. Deletion, not gating (DD-1 already recommends this for proposals).

## S4 — The settings-tier lie

`AiAgentTab` + `_TIER_FEATURE_LIMITS` present `enable_auto_negotiation`, `max_negotiation_rounds`, `enable_call_capture` as plan-differentiating features. Since the features are simulated, the *pricing page's* differentiation rests on vapor. This is a launch-claim-registry item (motto §0.11.1): no plan may advertise a feature that is simulated without a "preview" label.

## Decisions needed from operator

1. Ratify the gate-defaults-False launch posture (S3.1–3.4) vs. shipping simulations with "Preview" labels (cheaper, weaker — not recommended on trust surfaces).
2. Pick the first frontier feature to finish for real, or defer the choice to customer discovery (recommended).
3. Confirm cut of demo fallbacks (S3 CUT paragraph) — no product value, pure risk.

## "Anything else?" (motto §0.1.1)

- Pattern to institutionalize: **every new feature lands with an explicit reality tier** (`real | simulated | planned`) in its contract — the absence of this convention is what let 11 simulated surfaces accumulate silently.
- The honest code here is genuinely good: the frontier module's own comments admit the simulations ("In a real system, this would…", "do not use for production decisions"). The failure is at the *surface* layer — the honesty never made it out of the docstrings into the API contract or UI.
- Interaction with DD-6 (monetization): tier limits will eventually gate real features; the gating machinery (tiers, settings, UI) is already built and correct — only the features behind it are missing. That's actually good news for DD-6.
- Not verified: whether `enable_call_capture` has real implementation behind it (e2e_test_callcapture.py at root suggests a real path exists) — quick check for the DD-5 fix pass.

## Status

S1–S4: **verified static, unfixed.** S3 gating plan is the recommended launch posture awaiting operator ratification. Next: DD-6 (monetization).
