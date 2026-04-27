# Fin Spec: Agentic 'Yield-Management' Optimizer (FIN-REAL-033)

**Status**: Research/Draft
**Area**: Agency Revenue Yield, Demand-Based Fee Adjustment & Pipeline Optimization

---

## 1. The Problem: "The Static-Fee-Opportunity-Cost"
Most travel agencies charge a fixed service fee regardless of demand, capacity, or the current value they're delivering. In peak season when they're oversubscribed, they're under-charging and turning away profitable work. In slow periods, they maintain the same pricing even when discounting would convert hesitant travelers. Without "Yield-Intelligence," the agency leaves both peak-season revenue and off-season volume on the table.

## 2. The Solution: 'Revenue-Yield-Protocol' (RYP)

The RYP acts as the "Agency-Yield-Controller."

### Yield Actions:

1.  **Capacity-Utilization-Monitoring**:
    *   **Action**: Tracking the agency's current "Service-Capacity-Utilization" — the ratio of active files to maximum manageable concurrent files — and mapping it to a dynamic "Demand-State" (Under-Utilized, Balanced, Constrained, Over-Subscribed).
2.  **Demand-State-Fee-Adjustment**:
    *   **Action**: Adjusting service fees automatically based on Demand-State:
        - **Under-Utilized (<40%)**: Offer "Incentive-Tier" with reduced or deferred fees, priority access, and bonus inclusions to stimulate new bookings.
        - **Balanced (40–70%)**: Standard fees, standard service.
        - **Constrained (70–90%)**: Premium fee tier applies, waitlist for new files, intake criteria tightened.
        - **Over-Subscribed (>90%)**: Referral-only intake, maximum fees, surplus leads routed to trusted partner agencies (with referral commission).
3.  **Pipeline-Health-Forecasting**:
    *   **Action**: Projecting the agency's 90-day booking pipeline — anticipated completions, renewals, and new enquiries — to predict future capacity states and proactively trigger demand-stimulation campaigns before hitting under-utilization.
4.  **Seasonal-Yield-Calendaring**:
    *   **Action**: Building a rolling 12-month "Yield-Calendar" mapping historical demand patterns to proactive fee and promotion scheduling — so the agency enters each season with a prepared pricing strategy, not a reactive one.

## 3. Data Schema: `Yield_Management_State`

```json
{
  "state_id": "RYP-88221",
  "agency_id": "AGENCY_ALPHA",
  "current_capacity_utilization": 0.73,
  "demand_state": "CONSTRAINED",
  "active_fee_tier": "PREMIUM",
  "pipeline_90_day_projection": "BALANCED_BY_DAY_45",
  "waitlist_active": true,
  "surplus_leads_routed": 3,
  "seasonal_yield_calendar_version": "2026-Q2"
}
```

## 4. Key Logic Rules

- **Rule 1: Fee-Adjustment-Transparency**: Travelers on waitlists or subject to premium fee tiers MUST be informed of the reason (high demand) with a clear, honest explanation. No hidden surcharges.
- **Rule 2: Referral-Partner-Vetting**: Surplus leads routed to partner agencies MUST only go to pre-vetted partners meeting the parent agency's quality standards. No referrals to unknown agencies.
- **Rule 3: Owner-Approval-Gate**: All automatic fee-tier changes MUST require one-time agency-owner configuration approval. The agent cannot change pricing autonomously without the owner's explicit parameter setting.

## 5. Success Metrics (Yield)

- **Revenue-Per-Available-Capacity-Unit**: Revenue generated per slot of available agent capacity — the core yield metric.
- **Over-Subscription-Duration-Reduction**: Reduction in time spent in "Over-Subscribed" state through better pipeline forecasting.
- **Off-Season-Conversion-Lift**: Increase in bookings during historically under-utilized periods following incentive-tier activation.
