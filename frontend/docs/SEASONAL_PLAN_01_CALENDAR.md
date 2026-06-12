# Seasonal Campaign Planner — Travel Marketing Calendar

> Canonical seasonality model for campaign timing, demand shaping, budget allocation, and risk control.

## 1) Purpose and scope

This document is the source of truth for India travel seasonality assumptions. It converts seasonality research into planning inputs for campaigns, pricing, inventory, and operations.

- **Scope:** outbound/international-heavy travel, family and premium segments, monsoon/weather-sensitive campaigns, event windows.
- **Not in scope:** destination-specific tactical editorial calendars (owned by destination/content systems).

## 2) Canonical season taxonomy

- **Peak:** highest demand, tighter capacity, margin stress.
- **Shoulder:** manageable demand, strongest margin opportunity.
- **Off-season:** lowest demand, strongest cash conversion risk, strongest promotion value.

### 2.1 India season matrix (canonical baseline)

| Month window | Primary label | Demand | Booking behaviour | Price level | Core campaign pattern | Primary risk |
|---|---|---|---|---|---|---|
| Jan-Mar | Shoulder / Early planning | Medium-High | 4–10 weeks before peak travel; honeymoon planning rises | Moderate | Early bird for summer and wedding season | Event date shifts, exam-season churn |
| Apr-Jun | Peak (Summer/Academic) | Very High | 8–16 weeks for school vacations and family departures | High-Upper | Summer early bird + destination spotlights + conversion acceleration | Supplier constraint and cash float
| Jul-Aug | Off-season (Monsoon) | Low | 1–4 weeks for opportunistic bookings | Moderate-Low | Monsoon escape + value-led campaigns | weather volatility, expectation gaps |
| Sep-Oct | Shoulder to Peak crossover | Medium | 4–12 weeks; Diwali planning accelerates | Mid-High | Diwali pre-launch + high-intent families | weather interruptions, festival overload |
| Nov-Dec | Peak (Festival/Year-end) | High | 6–10 weeks for international winter plans | Very high | Last-mile urgency + premium package positioning | fatigue after repeated festival campaigns |

### 2.2 Event-driven overlays

- **School holiday windows:** + booking urgency, families and family packages dominate.
- **Republic Day, Holi, Independence Day, Gandhi Jayanti, Dussehra windows:** short-horizon spikes; avoid overusing one-off discount patterns.
- **Diwali and Christmas/New Year windows:** typically premium pricing and high conversion sensitivity to trust markers (refund policy, booking window certainty, clear inclusions).

## 3) Forecast-oriented seasonal model

```ts
interface SeasonalCampaignContext {
  region: 'INDIA_MKTG';
  fiscalYear: string; // e.g., "2026-27"

  windows: SeasonalWindow[];
  eventShocks: EventShock[];
  constraints: SeasonalConstraint[];
  forecast: ForecastAssumptions;
}

interface SeasonalWindow {
  code: 'PEAK_SUMMER' | 'PEAK_FESTIVAL' | 'SHOULDER_WINTER' | 'SHOULDER_WEDDING' | 'OFF_MONSOON';
  months: string; // canonical display alias
  demandBand: 'very_high' | 'high' | 'medium' | 'low';
  leadTimeDaysMin: number;
  leadTimeDaysMax: number;
  campaignIntent: 'capture' | 'activate' | 'clearance' | 'upgrade';
  minBookingVelocityPerWeek: number;
  targetLeadFillPercent: number; // by window close
  guardrail: {
    minMarginPercent: number;
    maxChannelSpendPercentOfRevenue: number;
    inventoryCommitmentPercent: number;
  };
}

interface EventShock {
  name: string;
  dateModel: string;
  demandImpact: 'low' | 'medium' | 'high';
  pricePressure: 'low' | 'medium' | 'high';
  fallbackAction: string;
}

interface SeasonalConstraint {
  id: string;
  area: 'pricing' | 'campaign' | 'inventory' | 'ops';
  description: string;
  validation: string;
}

interface ForecastAssumptions {
  baselineGrowthYoy: number;
  bookingVarianceBand: number; // ± percent
  confidenceLevel: number; // 0-1
}
```

## 4) Canonical monthly view (calendar + campaign objective)

```text
Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep | Oct | Nov | Dec
S   | S   | S   | P   | P   | P   | O   | O   | S   | P   | P   | P
    ^       ^           ^    ^        ^        ^       ^
    A/B     Wedding      Summer  Monsoon  Diwali   Premium

A = Early-bird planning
B = Budget rebalancing
```

| Month | Campaign Objective | Typical Spend Priority | Margin Policy |
|---|---|---|---|
| Jan | Plan summer pipeline, launch early-bird narratives | High | Hold premium + offer lock incentives |
| Feb | Lock summer / wedding conversion | High | Maintain minimum margin, push add-ons |
| Mar | Re-evaluate budget, shift to pre-summer urgency | Medium | Tighten discount depth |
| Apr | Capture booked summer demand | Medium-High | Maintain margin floor, enforce cap |
| May | Conversion acceleration, upsell timing | High | Premium bundling emphasis |
| Jun | Summer exit with carry planning | Medium | Reserve cash for next cycle |
| Jul | Activate monsoon escape campaigns | Medium | Selective discounts by segment |
| Aug | Deepen monsoon capture + long weekend tactics | Medium-Low | Higher discount tolerance with strict caps |
| Sep | Diwali pre-launch and funnel rebuild | High | Reintroduce margin standards after off-season |
| Oct | Festival conversion execution | High | Guardrails to avoid permanent deal dependency |
| Nov | Upsell and premium year-end packages | Medium-High | Keep core margin baseline + ancillaries |
| Dec | Year-end conversion and repeat pipeline reset | High | Reduce over-discounting in final weeks |

## 5) Campaign archetype mapping by season

| Archetype | Trigger window | Core promise | Typical objective |
|---|---|---|---|
| Early Bird | 8–16 weeks before peak | Lock today, avoid last-minute stress | Volume + margin capture |
| Spot Demand Lift | 1–4 weeks before window | Move opportunistic demand into bookings | Inventory utilization |
| Destination Spotlight | 2–12 weeks | Build desire and pre-decide destination choice | Awareness + conversion lift |
| Monsoon Escape | 1–8 weeks | Value-first escape narrative | Revenue stabilization |
| Referral/Trust Burst | Across peak windows | Trusted social reinforcement + urgency | Conversion rate recovery |

## 6) Operational linkage (who uses this file)

- **Marketing:** campaign calendar setup and channel mix decisions.
- **Pricing:** guardrail values for offer depth and seasonal multipliers.
- **Sales ops:** hiring and staffing plan for peak intervals.
- **Finance:** expected cash timing and payment cycle assumptions.

## 7) Open risks and long-term fixes

1. **Weather-driven disruptions** — add weather contingency and destination alternatives in the execution runbook.
2. **Festival date uncertainty** — event dates drift by year; maintain lunar-calendar + regional exceptions process.
3. **Overexposure risk** — repeated peak-season offers reduce perceived urgency.
4. **Downstream data drift** — keep event/cost assumptions versioned with effective dates.

## 8) Next steps (implementation-grade)

- [x] Define canonical season taxonomy and lead-time ranges.
- [x] Encode contracts and assumptions in `SEASONAL_PLAN_03_CONTRACTS_AND_KPIS.md`.
- [x] Link campaign archetypes to execution runbook in `SEASONAL_PLAN_04_EXECUTION_AND_INTEGRATION.md`.
- [ ] Build a governance queue that audits each campaign against this model before dispatch.
- [ ] Add quarterly seasonality recalibration based on booking pace and weather outcomes.
