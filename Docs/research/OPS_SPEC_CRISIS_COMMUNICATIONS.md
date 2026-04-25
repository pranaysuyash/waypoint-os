# Ops Spec: Crisis-Communication-Routing (OPS-REAL-003)

**Status**: Research/Draft
**Area**: Emergency Operations & Mass Disruption

---

## 1. The Problem: "The Information Firehose"
During a mass disruption (e.g., ATC Strike in France, Snowstorm in NYC), the agency's support-channels are flooded. Travelers are anxious and need "Personalized-Certainty," not generic broadcasts. Traditional support collapses under the load. The agent needs a way to "Triage-and-Talk" to hundreds of people simultaneously.

## 2. The Solution: 'Incident-Broadcast-Protocol' (IBP)

The IBP allows the agent to act as a "Mass-Crisis-Controller" by categorizing and routing communications based on 'Operational-Urgency.'

### Crisis Actions:

1.  **Traveler-Triage-Categorization**:
    *   **Urgency A (Immediate)**: At the airport, flight departs in < 4 hours.
    *   **Urgency B (Active)**: Traveling today, currently in transit.
    *   **Urgency C (Planned)**: Traveling in 24-72 hours.
2.  **Context-Aware-Broadcasting**:
    *   **Action**: Instead of one generic message, the agent sends "Segment-Specific" updates (e.g., "All travelers on BA173: Your gate has changed to A12, your meal-voucher is in your email").
3.  **Autonomous-Rebooking-Queue**:
    *   **Action**: For 'Urgency A' travelers, the agent autonomously identifies the "Next-Best-Option" and "Pre-Holds" seats before even asking the traveler, ensuring they don't lose the slot during the crisis.

## 3. Data Schema: `Crisis_Incident_Manifest`

```json
{
  "incident_id": "IBP-88221",
  "trigger": "LHR_ATC_STRIKE",
  "affected_travelers": 142,
  "triage_buckets": {
    "urgency_a": ["GUID_9911", "GUID_8822"],
    "urgency_b": ["GUID_7733"],
    "urgency_c": ["GUID_6644"]
  },
  "broadcast_templates": [
    {"target": "URGENCY_A", "channel": "WHATSAPP", "template_id": "EMERGENCY_REBOOK_01"}
  ],
  "autonomous_actions_taken": [
    {"action": "PRE_HOLD_SEATS", "count": 12}
  ]
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Golden-Update-Cadence'**: During an active crisis, the agent MUST provide an update every 30 minutes, even if the update is "No change from airline," to maintain traveler trust.
- **Rule 2: Support-Escalation-Inhibition**: The agent MUST NOT escalate to a human agent for 'Urgency C' tasks until all 'Urgency A' tasks are resolved.
- **Rule 3: Multi-Channel-Saturation**: For 'Urgency A,' the agent MUST send updates via all available channels (WhatsApp, Push, Email, SMS) to ensure receipt.

## 5. Success Metrics (Crisis)

- **Rebooking-Latency**: Time from "Flight-Cancellation-Alert" to "New-Option-Proposed" (Target: < 2 mins).
- **Communication-Saturation**: % of affected travelers who acknowledged the crisis update.
- **Deflection-Rate**: % of crisis-related queries resolved autonomously without a human agent.
