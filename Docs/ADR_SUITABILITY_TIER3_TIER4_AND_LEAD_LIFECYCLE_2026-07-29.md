# ADR: Tier 3/4 Suitability Engine & Lead Lifecycle Retention

**Status**: Accepted  
**Date**: 2026-07-29  
**Context**: Waypoint OS Advanced Suitability & Retention State Machine

---

## Context

Static single-activity suitability rules fail to catch itinerary-level pacing conflicts (e.g. relaxed preference vs. >4 packed activities per day) or traveler fatigue risks (e.g. senior travelers without rest windows). Additionally, agency churn occurs when stale leads ghost without automated intervention.

---

## Decision

Implemented Tier 3/4 Suitability Evaluation and Lead Lifecycle Retention:

1. **Tier 3 Contextual Pacing (`src/suitability/integration.py`)**:
   - Evaluates daily activity counts against `pace_preference` to flag pacing overload risks.
2. **Tier 4 Fatigue & Environmental Adjustments**:
   - Detects senior/elderly participants and inserts mandatory 90-minute rest window warnings.
3. **Lead Lifecycle State Machine (`src/intake/lifecycle.py`)**:
   - Tracks lead stages (`new_inquiry`, `proposal_sent`, `ghosted_stale`, `churned`).
   - Computes `ghosting_risk` based on interaction recency and assigns automated retention interventions (WhatsApp re-engagement, price lock expiring email, senior human planner call).

---

## Consequences

- Comprehensive 4-tier suitability matrix protecting traveler comfort and safety.
- Automated retention interventions preventing high-intent lead churn.
