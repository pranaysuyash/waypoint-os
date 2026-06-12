# Seasonal Campaign Planner — Strategy Playbook

> Canonical playbook for how teams execute seasonal campaigns with predictable outcomes and controlled downside.

## 1) Operating principles

1. **Plan backward from booking windows.** Build from planned inquiry-to-booking conversion targets, not from creative deadlines.
2. **Use one canonical campaign pipeline.** No duplicate execution rails.
3. **Protect margin first, then volume.** Discounting without minimum margin rules is deferred to controlled experiments only.
4. **Respect seasonality, not assumptions.** Every campaign gets explicit season code + window + forecast assumptions.
5. **Stop loss on trust.** No fake urgency, no unverified availability claims, and no blanket discounts during repeated season windows.

## 2) Pre-season planning playbook

### 2.1 10-week pre-planning (T-10 weeks)

- Finalize top 3-5 destination priorities.
- Set guardrail values:
  - minimum margin floor
  - max campaign spend
  - allowed discount band
- Resolve supplier commitments by destination/segment.
- Define capacity forecast and escalation threshold.
- Pre-approve recurring high-impact assets (for WhatsApp + email).

### 2.2 6-week campaign design window (T-6 weeks)

- Convert destination priority into offer stack:
  - core price offer,
  - optional upgrade ladder,
  - contingency alternative destination.
- Map each campaign to source of truth contract in `SEASONAL_PLAN_03_CONTRACTS_AND_KPIS.md`.
- Define owner, approver, and campaign kill switch.

### 2.3 2-week launch readiness window (T-2 weeks)

- Validation checklist:
  - pricing floor met,
  - inventory cap exists,
  - legal/comms review complete,
  - channel sequence approved,
  - reporting mapping in place.
- Lock launch sequence: email/whatsapp first, social reinforcement, app/website landing reinforcement.

## 3) Execution patterns by campaign archetype

### Early Bird

- **Intent:** Capture advance demand with commitment incentives.
- **Offer structure:** time-bound lock-in, limited discount, optional flexible add-on credit.
- **Primary risk:** margin compression if campaign spills into non-target segments.
- **Guardrail:** stop if margin floor breach, even if volume is healthy.

### Last-minute / Clearance

- **Intent:** Fill remaining demand within narrow departure windows.
- **Offer structure:** higher urgency, explicit cap on per-booking margin.
- **Primary risk:** channel trust loss from repeated “limited stock” claims.
- **Guardrail:** no fake scarcity; inventory source must support counters.

### Destination Spotlight

- **Intent:** Build future demand, improve average value, smooth shoulder demand.
- **Offer structure:** trip narrative + value map + limited-time booking gate.
- **Primary risk:** one-off spikes with low conversion.
- **Guardrail:** require at least one secondary KPI target (CTR, conversions, CPA).

### Monsoon Escape

- **Intent:** Activate demand during demand troughs.
- **Offer structure:** weather-resilient messaging + alternatives for risk.
- **Primary risk:** weather mismatch and expectation drift.
- **Guardrail:** prebuilt fallback destination alternatives and rebooking support script.

## 4) 1-page campaign run pattern

1. Campaign hypothesis
2. Contract ID and season code assignment
3. Channel sequence definition
4. Spend and margin limits set
5. Launch conditions met
6. Real-time monitoring and stop/scale decision cadence
7. Post-mortem: conversion, margin, retention impact, channel quality

## 5) In-season governance and controls

### Daily
- Lead booking velocity vs target.
- Channel conversion drift.
- Remaining budget and planned-day pacing.
- Any trust-risk violations (misaligned inventory claims, broken links, refund issues).

### Weekly
- Window-level campaign profitability.
- Segment-level conversion quality.
- Supplier utilization and renegotiation signal.
- Season model drift from forecast to actual.

### End-of-window
- Campaign debrief with post-booking quality checks.
- Campaign score against defined contract KPIs.
- Adjust assumptions in `SEASONAL_PLAN_03_CONTRACTS_AND_KPIS.md` for next cycle.

## 6) Long-term exploration paths

1. **Message sequencing A/B:** sequence length and interval optimization for WhatsApp and email.
2. **Channel mix optimizer:** dynamic budget shifts based on marginal margin per rupee.
3. **Weather-aware fallback routing:** campaign redirection when disruption risk rises.
4. **Segment-intent matching:** deeper profile-level timing based on historical seasonality behaviours.

## 7) Completion checklist

- [x] Defined seasonal archetypes and play pattern.
- [x] Added pre-launch checks and kill switches.
- [x] Added governance cadence tied to data and margin outcomes.
- [x] Added explicit long-term exploration vectors.
