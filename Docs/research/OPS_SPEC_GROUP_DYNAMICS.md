# Ops Spec: Agentic 'Group-Dynamics' Optimizer (OPS-REAL-032)

**Status**: Research/Draft
**Area**: Group Travel Social Intelligence, Payment Orchestration & Conflict Prevention

---

## 1. The Problem: "The Group-Travel-Entropy"
Group travel is exponentially more complex than individual travel. Every additional traveler multiplies the potential for preference conflicts, payment disputes, scheduling friction, and interpersonal tension. Most agencies manage groups as a simple headcount problem. The real challenge is "Social-Cohesion" — ensuring that 8 people with different energy levels, spending comfort, and expectation sets actually enjoy traveling together.

## 2. The Solution: 'Social-Cohesion-Protocol' (SCP)

The SCP acts as the "Group-Harmony-Architect."

### Group Dynamics Actions:

1.  **Individual-Preference-Aggregation**:
    *   **Action**: Collecting individual preference surveys from each group member (activity intensity preference, dietary needs, budget comfort band, wake-up time preference, solo-time vs. group-time ratio) and building a "Group-Preference-Map."
2.  **Cohesion-Tension-Detection**:
    *   **Action**: Analyzing the Group-Preference-Map to identify likely friction zones before the trip: e.g., "3 members prefer early starts; 4 prefer late mornings — this scheduling conflict will cause daily tension." Surfacing these to the agency to resolve at the design stage, not during the trip.
3.  **Payment-Split-Intelligence**:
    *   **Action**: Managing complex group payment structures: equal splits, proportional splits (based on room type or activity selection), and "Opt-Out-Components" for members who skip certain activities. Generating transparent payment schedules with individual installment reminders.
4.  **Group-Energy-Pacing**:
    *   **Action**: Designing the itinerary's activity intensity curve to respect the group's weakest energy link — avoiding "Death-March" itineraries where the slowest member is permanently stressed while fast members are bored. Building in "Free-Afternoon" buffers to allow natural self-segregation.

## 3. Data Schema: `Group_Dynamics_Profile`

```json
{
  "group_id": "GRP-77221",
  "lead_traveler_id": "TRAVELER_ALPHA",
  "group_size": 8,
  "preference_surveys_collected": 8,
  "cohesion_tension_zones": [
    {"dimension": "WAKE_TIME_CONFLICT", "severity": "MODERATE", "resolution": "9AM_SOFT_START_COMPROMISE"},
    {"dimension": "BUDGET_VARIANCE", "severity": "LOW", "resolution": "OPT_OUT_PREMIUM_ACTIVITIES"}
  ],
  "payment_structure": "PROPORTIONAL_BY_ROOM_TYPE",
  "installments_scheduled": 3,
  "group_energy_pacing": "MODERATE_WITH_FREE_AFTERNOONS"
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Weakest-Link' Pacing Standard**: All group itineraries MUST be designed around the physical and energy limitations of the least capable group member — not the average or the majority.
- **Rule 2: The 'No-Forced-Consensus' Rule**: When individual preference gaps are irreconcilable (e.g., one member hates beaches while others love them), the agent MUST design structured "Divergence-Windows" — periods where the group formally splits for different activities.
- **Rule 3: Payment-Dispute-Prevention**: All payment splits MUST be documented in a signed "Group-Payment-Agreement" before any deposits are collected. No informal verbal agreements.

## 5. Success Metrics (Group)

- **Group-Cohesion-Score**: Post-trip survey rating of interpersonal harmony during the trip vs. pre-trip baseline.
- **Payment-Dispute-Rate**: % of group bookings that generate a payment dispute during or after the trip.
- **Group-Rebooking-Rate**: % of groups that rebook another group trip with the agency within 24 months.
