# Ops Spec: Group-Travel-Coordination (OPS-REAL-005)

**Status**: Research/Draft
**Area**: Group Logistics & Event Coordination

---

## 1. The Problem: "The Logistics Nightmare"
Coordinating travel for 10+ people (weddings, retreats, family reunions) is a manual nightmare. Travelers arrive at different times, stay in different room types, and have different dietary needs. If one flight is delayed, the entire "Master-Transfer" schedule collapses.

## 2. The Solution: 'Synchronized-Arrival-Protocol' (SAP)

The SAP allows the agent to act as a "Mass-Logistics-Coordinator" by maintaining a unified view of the group's state.

### Coordination Actions:

1.  **Group-Manifest-Consolidation**:
    *   **Action**: Autonomously aggregating booking data for all group members into a single "Master-Manifest," even if they booked through different channels.
2.  **Synchronized-Transfer-Optimization**:
    *   **Action**: Grouping travelers into "Arrival-Windows" (e.g., 60-minute blocks) to minimize the number of shuttle runs and maximize cost-efficiency.
3.  **Real-Time-Delay-Propagation**:
    *   **Action**: If "Traveler A" is delayed, the agent autonomously checks if they can be moved to a later "Transfer-Window" and notifies the group leader.
4.  **Room-Block-Audit**:
    *   **Action**: Reconciling the hotel's room-block list against the agent's manifest to ensure all group members received the correct discount and amenity-package.

## 3. Data Schema: `Group_Travel_Manifest`

```json
{
  "group_id": "SAP-WEDDING-99",
  "coordinator_id": "GUID_LEAD_01",
  "members": [
    {"traveler_id": "GUID_9911", "status": "CONFIRMED", "arrival_window": "WINDOW_1"},
    {"traveler_id": "GUID_8822", "status": "DELAYED", "arrival_window": "WINDOW_2"}
  ],
  "logistics": {
    "master_transfer_schedule": [
      {"window": "WINDOW_1", "time": "2026-12-10T10:00:00Z", "capacity": 8, "assigned": 6}
    ]
  },
  "compliance_audit": {
    "group_rate_applied": true,
    "amenity_kits_reserved": 20
  }
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Buffer-Inhibition' Rule**: The agent MUST NOT book the final transfer for the group until the "Last-Confirmed-Traveler" has cleared customs.
- **Rule 2: Automated-Payment-Splitting**: For shared expenses (e.g., a $10k villa), the agent MUST autonomously calculate and request "Micro-Payments" from each member based on their room-tier.
- **Rule 3: Privacy-Tier-Gating**: Group members can see the "Arrival-Status" of others (e.g., "Arrived" or "Delayed") but NEVER sensitive data like passport numbers or credit card details.

## 5. Success Metrics (Coordination)

- **Transfer-Efficiency**: % reduction in unused transfer capacity vs manual scheduling.
- **Group-Policy-Compliance**: % of members who successfully received the group rate/amenities.
- **Coordinator-Time-Savings**: Estimated hours saved for the group leader (Target: > 90% reduction).
