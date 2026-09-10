# TS-02 — Quote Freshness / Recheck-Before-Execution Contract

**Status:** exploration (design contract) — 2026-09-09
**Source:** training-session register TS-02 (`CHATGPT_SYSTEMS_TRAINING_SESSION_FINDINGS_2026-09-09.md` §3); tutor's `APPROVED → freshness recheck → materially-changed → back to AWAITING_CUSTOMER_APPROVAL` state.
**Blocks / rides:** B6/B7 provider work (this contract only becomes executable against a live rate source); ADR-008 §6 money rungs; roadmap A5 (price-lock preview-only).
**Doctrine:** Operating 8.0 §2 truth taxonomy (this doc labels every claim); Architecture 1.1 §13A progressive autonomy.

---

## 1. Problem

The system's next-action vocabulary already *names* the recheck but nothing *does* it:

| Surface | Current state | Evidence |
|---|---|---|
| `revalidate_quote_before_payment` | priority-band token only (band 60, Money/quote) — no logic behind it | `src/orchestration/travel_next_action.py:18,30` |
| Fulfillment charge path | charges stored `proposal.selected_total_price_usd` directly, no staleness gate | `src/orchestration/booking_fulfillment.py:202,318` |
| `price_lock_expires_at` | written (72h quote window) and read (`is_expired`) but the endpoints are **PREVIEW-ONLY** — no real rate behind them | `spine_api/routers/price_lock.py:9,61-81,88-137`; `social_inbound.py:137,172` |
| `ToolFreshnessPolicy` | exists with `max_age_seconds`/`expires_at` — but only for flight/destination/weather *intelligence tools*, never prices | `src/agents/tool_contracts.py:28,283-299`; used at `src/agents/runtime.py:1046,1312,2883` |

**Observed:** the gap is real but currently *unexecutable*: with deterministic-preview inventory there is no live rate to recheck against, so any recheck implemented today would be theater (the exact class of simulated-capability findings the register tracks: G-01/GM-03 family).

## 2. The contract (design — Proposed)

When a real rate source lands (B6/B7: Mystifly/TBO), every priced artifact gains three fields:

```json
{
  "priced_at": "<ISO timestamp when the provider returned this price>",
  "price_source": "<provider + product id, joins to provenance actor 'provider' (TS-04)>",
  "freshness_ttl_seconds": 900
}
```

### Rules

1. **R1 — freshness class, not binary.** A price is `fresh` (within TTL), `stale` (past TTL, recheck required), or `unknown` (no `priced_at` — treat as stale; never fabricate freshness).
2. **R2 — staleness gates by commitment rung** (progressive commitment, JDG):
   - `quoted` node → advisory only (TTL exceeded surfaces as a soft note).
   - `held` node → must be fresh at hold time; hold carries the provider's own expiry.
   - `booked`/`ticketed` → **hard gate**: fulfillment refuses to charge a `stale` price. It re-fetches; on refetch it applies R3.
3. **R3 — materially-changed re-approval.** On re-fetch, if the new total exceeds the approved total by more than a materiality delta, execution does NOT proceed on the old approval. The trip returns toward the customer-approval state with the updated number, via the existing lifecycle vocabulary (`AWAITING_CUSTOMER_APPROVAL`-class states, `revision_needed` review status) — no new state machine.
   - Materiality delta ( Proposed, needs owner DECIDE ): absolute + % hybrid, e.g. `max(3%, ₹2,000)` per line item. Below delta: proceed and record the delta; above: re-approve.
4. **R4 — who rechecks.** Deterministic code, never the LLM. The recheck is a provider call + comparison — `AUTHORITATIVE DATA → DETERMINISTIC VALIDATION`; no AI in the loop (tutor's invariant: AI must never alter provider facts).
5. **R5 — token-to-logic wiring.** `revalidate_quote_before_payment` (band 60) stays the operator-facing next-action token; the fulfillment engine becomes its executor, so token and behavior can't diverge.

## 3. What is implementable now (small, honest)

- Add `priced_at`/`price_source`/`freshness_ttl_seconds` to the proposal schema and populate with `provider_connected: false` + `reality_tier: deterministic_preview` values, so downstream consumers already know freshness is `unknown`, not silently absent.
- Add a *labeled* staleness indicator to the operator panel (preview-tier): "prices are simulated; freshness tracking activates when a live rate source connects." This is honest-degradation copy, not a fake gauge.
- Reuse, don't duplicate: extend `ToolFreshnessPolicy` rather than inventing a parallel price-freshness class.

## 4. Decision gates

| Decision | Owner | Options |
|---|---|---|
| Materiality delta (R3 threshold) | Pranay | flat % vs hybrid vs per-category |
| Whether stale-but-unchanged re-fetched prices restart the approval clock | Pranay | restart vs preserve approval if total unchanged |
| Where freshness fields live | architect | proposal object vs journey-node metadata (node-level aligns with JDG rungs) |

## 5. Sequencing

Implement §3 now (schema + honest panel copy); implement R1–R5 inside the B6/B7 provider lane when a live rate source exists. Do not build a recheck engine against simulated inventory.
