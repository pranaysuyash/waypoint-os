# Seasonal Campaign Planner — Execution & Integration Runbook

> Integration points and operator workflow that turn seasonal campaign contracts into real product behavior.

## 1) System integration boundaries

### 1.1 Pricing layer

- Seasonal multipliers and margin floors should source from `PRICING_ENGINE` config and `SEASONAL_PLAN_03_CONTRACTS_AND_KPIS.md`.
- Any seasonal campaign offer must pass through a single price-policy evaluator.
- If a campaign requires temporary price floor exceptions, it must be explicit in `requiredChecksPassed`.
- Simulation fallback is policy-visible: if campaign budgets are unset, simulation defaults to a conservative baseline budget of 10000 before projection.

### 1.2 Revenue and finance layer

- Campaign economics feed into forecasting and cash-flow assumptions.
- Revenue attribution must map campaignId to margin, channel, and segment.
- Booking close and cancellation outcomes should update forecast variance at least daily.

### 1.3 Deals and promotion layer

- `DEALS_PROMO_01_ENGINE` and seasonal planner share campaign type definitions.
- Seasonal promotions should not bypass contract-defined floor margins.
- Escalation rules from promo execution should return to this planner for post-window learning.

### 1.4 Marketing and channel layer

- Canonical channels: WhatsApp, email, Instagram, app, website.
- `MARKETING_AUTOMATION` consumes the contract and can only schedule approved campaign types.
- WhatsApp templates need pre-approval for repeated seasonal patterns to avoid delivery failures.

### 1.5 Destination intelligence layer

- Event overlays and destination feasibility come from seasonal destination intelligence.
- Destination-level weather/advisory exceptions require explicit fallback alternatives in the contract.

## 2) Integration pipeline (operational)

1. **Plan creation** in seasonal planner (season code + campaign type + window).
2. **Contract compilation** with economics/owners/channels and guardrails.
3. **Validation checks** (pricing, margin floor, inventory, schedule, channel policy).
4. **Approval gate** by owner and risk owner.
5. **Launch orchestration** by marketing automation.
6. **Monitoring loop** using KPI envelope and risk checks.
7. **Auto-pause or hold** if guardrails breached.
8. **Post-mortem** and revision before next window.

## 3) Channel-specific responsibilities

- **Marketing ops:** campaign schedule, audience slices, creative review.
- **Pricing owner:** margin and discount policy adherence.
- **Revenue owner:** forecast and cash-flow impact check.
- **Destination analyst:** event/weather override recommendations.
- **Customer support lead:** support quality and fallback risk response.

## 3) Product surface map (where this behavior lands)

- **Campaign orchestration view**: campaign planner dashboard entry point and contract detail pane.
- **Campaign builder**: offer block, budget guardrails, channel matrix, and stop criteria fields.
- **Pricing review view**: season code, discount floor, and margin projection inspector.
- **Ops capacity view**: staffing and supplier pressure signals for high-demand windows.
- **Financial planning view**: campaign spend-to-revenue variance and cash-flow timing.
- **Post-campaign analytics**: campaign KPI ledger and trust-score trendcards.

Acceptance criteria for each surface:
- Every seasonal campaign shown in the planner can be traced to one contract in `SEASONAL_PLAN_03_CONTRACTS_AND_KPIS.md`.
- The UI surfaces margin floor and max discount before launch.
- High-risk campaigns require explicit risk-owner acknowledgment and show stop conditions inline.

## 4) Pre-launch checklist (mandatory)

- [ ] Season code and window align with `SEASONAL_PLAN_01_CALENDAR.md`.
- [ ] Contract file has owner + approver + risk owner.
- [ ] Margin floor and max discount values validated against pricing policy.
- [ ] Inventory cap and fallback alternatives populated.
- [ ] Communication assets include pricing validity date and support path.
- [ ] Tracking tags configured for all primary KPIs.
- [ ] Stop criteria logged and agreed.

## 9) Seasonal campaign integration checklist (runtime smoke list)

- [ ] Open `/seasons`, create a draft campaign, then save and confirm list refresh.
- [ ] Load an existing campaign into edit mode, update one field, save, and verify no duplicate network payloads.
- [ ] Delete draft-only fields from a campaign via the edit form and confirm clear behavior in update request.
- [ ] Run Simulation (`baseline` and `conservative`) and verify returned scenario notes match live window input.
- [ ] Run Preflight and verify risk score is returned with explicit budget/window/channel checks.
- [ ] Run Dispatch (dry run) and verify executed channel list reflects current campaign mix.
- [ ] Confirm API payload shape on each action still matches `SeasonalCampaign*` contracts in `spine_api/contract.py`.

## 5) In-flight controls

- Decision checks every defined cadence (default 12h).
- Stop conditions:
  - sustained negative margin,
  - trust spike (support escalations),
  - inventory mismatch,
  - campaign quality regression.

## 6) Post-window review

- Compare outcomes vs contract (bookings/revenue/margin/CAC/quality).
- Record model drift and assumptions change.
- Publish one-line verdict: Proceed / Iterate / Pause.
- Update destination/event assumptions if repeated drift is observed.

## 7) Failure-mode playbooks

### Over-discount drift
- Pause new discounted inventory, hold messaging, re-balance to upgrade offers.

### Inventory mismatch
- Freeze campaign caps, notify support and operations, activate fallback destinations.

### Channel delivery friction
- Re-route campaign share to healthier channels and notify creative/comms if template fails.

## 8) Long-term integration goals

- Replace ad-hoc campaign spreadsheets with contract-based campaign registry.
- Build contract validation lint checks in CI for release safety.
- Add scenario-based weather and event simulation for all major peak windows.
