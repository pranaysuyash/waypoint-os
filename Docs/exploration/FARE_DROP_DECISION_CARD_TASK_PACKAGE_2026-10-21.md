# Fare-Drop Decision Card — Implementation Task Package

**Date:** 2026-10-21
**Origin:** Exploration topic 48 (external ideas sweep) → r/travelagents practitioner playbook ("Price drops — Commission losses", top thread of the year) + trvl `watch`/`forecast` design patterns (probe 2026-10-20).
**Roadmap anchor:** `Docs/CANONICAL_PRODUCT_OPPORTUNITY_AND_ROADMAP_REGISTRY_2026-08-04.md` § Explicitly documented → **"Price-drop re-shopping"** (documented, not implemented).
**Owner constraint (hard):** the system NEVER initiates, holds, or receives money, and NEVER contacts suppliers or sends customer messages autonomously. Everything below is tracking + decision support; the advisor executes.

`Checklist applied: IMPLEMENTATION_AGENT_REVIEW_HANDOFF_CHECKLIST.md`

---

## The problem, in the practitioner's words

> "Family reunion cruise group of 14 staterooms, final payment approaching. Another family member asked for a quote to join, and that's when I noticed the prices have dropped significantly. I spent the last hour comparing…" — then the choice: reprice everyone (clients save, agent loses commission) or offer upgrades (clients get more, commission preserved). Community consensus: tell the client, frame it as *"great news, two ways to take advantage"*, use supplier credits to offset commission, "we always give it back — best word-of-mouth advertising."

Today that detection is manual and accidental. The decision is made under commission pressure with no numbers in front of the advisor. That is the gap.

---

## A. Review verdict

`Three adjacent surfaces exist, none covers post-booking fare drops — extend, don't fork.` Foundation is strong (watch-tool seam, disposition pattern, commission ledger all live and tested); the feature is a composition task, not a greenfield build.

## B. What is verified (live codebase, read 2026-10-21)

| Surface | Location | What it does today | Freshness class |
|---|---|---|---|
| `PriceWatchTool` seam | `src/agents/live_tools.py:32` (Protocol), `:113` (`MockPriceWatchTool`, deterministic default), `:296` (`HTTPPriceWatchTool`, env-configured via `TRAVEL_AGENT_PRICE_WATCH_URL_TEMPLATE`) | Returns `drift_percent` for a quote; output validated via `validate_tool_output` | **still valid — reuse as-is** |
| `TicketPriceWatchAgent` | `src/agents/runtime.py:2858–2961` | Scans trips in stages `quoted/proposal/booking/payment`; writes `ticket_price_watch_alert`, `quote_revalidation_required`, `price_watch_risk_level` (thresholds: \|drift\| ≥15 high, ≥5 medium); idempotent per `quote_marker`; `authority` string forbids purchase/contact. **Pre-booking only; direction-agnostic (abs drift).** | **partially valid — extend with a post-booking branch** |
| Price-Lock Sentinel | `spine_api/routers/price_lock.py` (`/api/v1/price-lock`) | 72-hour *quote-window* supplier net-rate audit + advisor re-lock **PREVIEW** (PA-06: simulated rate source, persists nothing). Agency-margin side, pre-booking. Has reusable models: `original_net_rate_cents / current_net_rate_cents / margin_gain_pct`. | **still valid — adjacent, do not duplicate; reuse the cents-math shape** |
| Claim disposition ledger | `spine_api/services/claim_disposition.py`, router `spine_api/routers/passenger_rights.py:293,332` (GET/PATCH on existing router), UI `frontend/src/components/workspace/ClaimDispositionCard.tsx` on `/trips/[tripId]/decision` | 8-state outcome machine, immutable terminals, `history[]`, overdue computed at read time, forbidden custody vocabulary asserted in tests. `tests/test_claim_disposition.py` → **11 passed in 0.43s (fresh, 2026-10-21)** | **done — the pattern to mirror** |
| Commission ledger | `spine_api/services/commission_reconciliation.py` (`AGENCY_COMMISSION_RATE = 0.10`, split tiers 70/30–90/10, `reconcile_trip_commission`), `spine_api/contract.py:1694 commission_pct` | Advisor payout ledger linked to booking totals | **still valid — input to the impact calculator** |
| Frontend read path | `frontend/src/lib/bff-trip-adapters.ts:243–245` → `PacketPanel.tsx:429–431` | Renders the pre-booking alert as a status/next-action/detail row | **still valid — leave; card goes on the decision page** |
| Trip status machine | `spine_api/core/trip_status.py` (`QUOTE_CAPABLE_STATUSES`, `status_history` cap 50, aliases) | Canonical status vocabulary + history writer | **still valid — eligibility must be expressed against this, not string guesses** |

Risk register for the gaps: post-booking eligibility wiring (**medium** — must respect the trip-status invariant), commission-impact provenance (**medium** — booked commission may be an estimate, must carry a basis label per FND-0268), traveler message (**low** — draft-only through the existing dispatch path).

## C. Gaps to close (ordered by dependency)

1. No **post-booking** fare-drop detection anchored to the *booked* price (agent stops at pre-booking quote drift).
2. No **decision ledger** for what the advisor chose (reprice / upgrade / defer) and its recorded outcome.
3. No **commission-impact calculator** putting the two options side by side with provenance.
4. No **operator card** on the decision surface.
5. No **traveler-facing draft** in the consensus framing (depends on E1 channel DECIDE; draft-only regardless).

## D. Task package

### T-FD1 — Post-booking fare-drop detection (extend `TicketPriceWatchAgent`)

- **Objective:** When a trip is past booking and the current fare for the booked itinerary is **lower** than the booked price by ≥ `FARE_DROP_MIN_PERCENT` (default 5), attach a `fare_drop_signal` to the trip and append an observation to a bounded `price_observations[]` history.
- **Scope (in):** add a post-booking eligibility branch to `TicketPriceWatchAgent.scan/execute` — eligibility derived from `spine_api/core/trip_status.py` vocabulary (post-booking statuses) and presence of a booked-price anchor (`booking.total` / accepted quote — implementer verifies the canonical field via the trip contract, not by guessing); signed drift (drop = negative) alongside the existing abs-based pre-booking logic; new `fare_drop_signal = {booked_price, booked_currency, current_price, current_currency, drop_amount, drop_percent, observed_at, tool_evidence[], confidence, authority}`; append to `price_observations[]` capped at 90 entries; honesty rule — stale/failed tool → `confidence: "unknown"`, no signal fabricated; env `FARE_DROP_MIN_PERCENT`, `FARE_DROP_OBSERVATION_CAP`. Update the `AgentDefinition` trigger/output/idempotency contract strings to describe both branches.
- **Scope (out):** no new agent class; no change to the pre-booking alert semantics; no supplier calls; no currency conversion beyond refusing to compare mismatched currencies (emit `currency_mismatch` reason — topic 44 owns FX).
- **Files:** `src/agents/runtime.py` (agent), `src/agents/live_tools.py` only if the tool contract needs a `booked_price` passthrough, `tests/test_agent_runtime.py` (new cases), `Docs/operations/MULTI_AGENT_RUNTIME_OPERATIONS_RUNBOOK_2026-05-04.md` (env vars).
- **Acceptance:** (a) booked trip + mock drift −12% → `fare_drop_signal` present, `drop_percent = -12`, observation appended; (b) drift −3% → no signal, observation still appended; (c) pre-booking trip behaves exactly as before (existing tests green); (d) tool failure → no signal, `confidence: unknown`; (e) mismatched currencies → no signal, reason recorded; (f) idempotent: same marker + same observation window does not duplicate.
- **Verification:** `uv run pytest tests/test_agent_runtime.py tests/test_agent_runtime_deep.py -q` · `uv run ruff check --fix .`
- **Non-goals:** auto-rebook, repricing execution, forecasting.

### T-FD2 — Fare-drop disposition ledger + commission impact + endpoints

- **Objective:** Record the advisor's decision and recorded outcome for each detected drop, with both options quantified and provenance-labelled.
- **Scope (in):** new service `spine_api/services/fare_drop_disposition.py` mirroring `claim_disposition.py`: states `DETECTED → PRESENTED → REPRICED | UPGRADED | DEFERRED | DISMISSED`; `DEFERRED → PRESENTED` (new observation) `| CLOSED`; `REPRICED | UPGRADED | DISMISSED → CLOSED`; `CLOSED` terminal and immutable; `history[]` with `by/at/note`; **forbidden custody substrings asserted in tests** (reuse the `ESCROW/FUNDS/HOLD/SETTLE` list — note the state is `DEFERRED`, not `HELD`, by design). Pure function `compute_fare_drop_options(booked_price, current_price, commission_pct, basis)` → `{reprice: {client_saving, commission_delta}, upgrade: {upgrade_budget, commission_delta: 0 or estimate}, basis: "ledger_backed" | "estimate", commission_source}` where `commission_pct` comes from the trip/agency contract (`commission_pct`) falling back to `AGENCY_COMMISSION_RATE` with `basis: "estimate"`. Outcome record on terminal transitions: `{option, client_delta, supplier_reference, executed_by, recorded_at}` — plain recorded data about money the supplier and client moved between themselves. Endpoints **added to the existing** `spine_api/routers/price_lock.py` (the Re-Shopping engine): `GET /api/v1/price-lock/{trip_id}/fare-drop/disposition`, `PATCH …/disposition` (illegal transition → 409; `expected_version` + `idempotency_key` required, matching `ReLockRequest`). Agency scoping via `get_current_agency_id` like the sibling endpoints. Expose `fare_drop_signal`, `fare_drop_disposition`, `fare_drop_options` on the trip response model.
- **Scope (out):** no new router file; no payment fields; no supplier API; no background scheduler (read-time computation like `compute_overdue`).
- **Files:** `spine_api/services/fare_drop_disposition.py` (new), `spine_api/routers/price_lock.py`, `spine_api/contract.py` (response model fields), `tests/test_fare_drop_disposition.py` (new; include a `test_no_payment_code_paths` twin), `tests/` endpoint tests alongside the price-lock tests.
- **Acceptance:** every legal/illegal transition covered; terminal immutability; forbidden-vocabulary test; options math: booked 100,000 / current 88,000 / commission 10% → reprice `client_saving 12,000`, `commission_delta −1,200`; upgrade `upgrade_budget 12,000`, `commission_delta 0`, `basis` set; GET on a trip without a signal → 404 with reason; PATCH illegal → 409; agency mismatch → 403/404 per sibling convention.
- **Verification:** `uv run pytest tests/test_fare_drop_disposition.py tests/test_claim_disposition.py -q` · `uv run ruff check --fix .` · contract check against a running backend before any frontend work: `curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/price-lock/$TRIP/fare-drop/disposition | python3 -m json.tool`
- **Non-goals:** money movement, autonomous supplier contact, forecasting.

### T-FD3 — `FareDropDecisionCard` on the decision page

- **Objective:** Put the two options in front of the advisor with the numbers, and let them record the decision.
- **Scope (in):** `frontend/src/components/workspace/FareDropDecisionCard.tsx` next to `ClaimDispositionCard` on `frontend/src/app/(agency)/trips/[tripId]/decision/PageClient.tsx`; shows booked vs current, drop %, observation freshness, the two option tiles (client saving / upgrade budget, commission delta) with a **basis badge** (`ledger-backed` vs `estimate`), confidence/unknown states rendered honestly (no number shown when `confidence: unknown`); actions call PATCH transitions through the BFF; copy uses the consensus framing ("two ways to take advantage"). **Types first:** regenerate/update `frontend/src/types/spine.ts` from the verified real response (API Contract Verification rule) before writing the component; optional chaining on every nested field.
- **Scope (out):** no edits to `PacketPanel` row; no new page/route.
- **Files:** the component, its test `frontend/src/components/workspace/__tests__/FareDropDecisionCard.test.tsx` (mocks must match the *real* backend schema — Test Schema Validation rule), `PageClient.tsx`, `frontend/src/lib/bff-trip-adapters.ts` + `api-client.ts` (new fields), `spine.ts`.
- **Acceptance:** renders both options from a real-shaped fixture; hides numbers on `unknown`; disabled actions on terminal state; transition errors (409) surface as a message, not a crash; a11y: tiles are buttons with labels; screenshot of the rendered card viewed before claiming done (Strict Visual E2E rule).
- **Verification:** `cd frontend && npx vitest run FareDropDecisionCard` · `npm run build` · live: backend on `:8000`, frontend on `:3005`, open a booked trip's decision page.
- **Non-goals:** traveler-facing UI, charts.

### T-FD4 — Traveler notification draft (draft-only, gated)

- **Objective:** On `PRESENTED`, generate the consensus-framed traveler message as `DRAFT_AWAITING_OPERATOR` through the existing dispatch path — never auto-sent.
- **Scope (in):** compose via `spine_api/services/message_dispatch.py` adapters (honest `NOT_CONFIGURED` where channels aren't set up), reuse the T1 ask-loop token page if an answer is wanted ("refund or upgrade?"); template lives beside the existing follow-up templates. **Gate:** sequence after the E1 channel DECIDE (topic 36); link-only is the floor.
- **Files:** `spine_api/services/message_dispatch.py`, followups templates, tests.
- **Acceptance:** draft produced, status `DRAFT_AWAITING_OPERATOR`, zero sends without an explicit operator action; grader check that the draft contains no fabricated numbers beyond the computed options.
- **Verification:** `uv run pytest tests/ -k "dispatch or followup" -q`
- **Non-goals:** auto-send, channel onboarding.

## E. Decision gate

**GO for T-FD1 + T-FD2 once the owner says yes to the feature** (DECIDE #2 from topic 48). Both are small, tracking-only, reuse live seams, and the practitioner demand is documented in their own words. **T-FD3 only after the T-FD2 contract is curl-verified** (the 2026-04-29 `validation.errors.length` crash is the reason this is a gate, not a suggestion). **T-FD4 is gated on E1**; it is additive and can wait.

Sequencing note: the `MockPriceWatchTool` default means T-FD1 is testable end-to-end today without a provider; the producer DECIDE (topic 48 probe: commercially-licensed MCP rails, FX/unpriced/converted clamps at the boundary) supplies a *real* drift source later without changing this package.

What would make me say no: if the owner wants autonomous repricing. That crosses the money/supplier boundary and is explicitly out of every task above.
