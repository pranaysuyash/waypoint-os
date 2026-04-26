# Reg Spec: Agentic 'Geopolitical-Atmosphere' Monitor (REG-REAL-019)

**Status**: Research/Draft
**Area**: Geopolitical Risk & Stability Intelligence

---

## 1. The Problem: "The Macro-Stability Gap"
While the "Safety-Shield" handles hyper-local crime, agencies also need to monitor "Macro-Geopolitical-Stability." Protests in a capital city, national transport strikes, or a sudden change in diplomatic relations can disrupt travel across an entire country. Agencies often lack the resources to monitor these macro-trends in real-time across all their destinations.

## 2. The Solution: 'Stability-Intelligence-Protocol' (SIP)

The SIP acts as the "Geopolitical-Intelligence-Analyst."

### Intelligence Actions:

1.  **National-Stability-Tracking**:
    *   **Action**: Monitoring global news wires, social media sentiment, and diplomatic advisories for signs of "National-Instability" (e.g., "General strike announced in France for next Tuesday; impact on all rail travel").
2.  **Proactive-Itinerary-Stress-Testing**:
    *   **Action**: When a stability event is detected, the agent autonomously runs a "Stress-Test" on all active itineraries in that region to identify potential disruptions (e.g., "Traveler X is taking the train from Paris to Lyon on the day of the strike; suggest rescheduling or private transfer").
3.  **Diplomatic-Risk-Alerting**:
    *   **Action**: Monitoring changes in visa requirements or entry bans resulting from "Geopolitical-Friction" (e.g., "Sudden suspension of E-visas for Country A; alert all travelers with pending applications").
4.  **Agency-Strategic-Briefing**:
    *   **Action**: Providing the agency owner with a "Regional-Stability-Index," allowing them to proactively advise travelers on "Safe-vs-Risky" destinations for future bookings.

## 3. Data Schema: `Geopolitical_Stability_Event`

```json
{
  "event_id": "SIP-11221",
  "jurisdiction": "FRANCE",
  "stability_category": "TRANSPORT_STRIKE",
  "severity_level": "HIGH",
  "duration_estimate_days": 3,
  "impacted_travelers_count": 42,
  "status": "STRESS_TEST_COMPLETE"
}
```

## 4. Key Logic Rules

- **Rule 1: The 'No-Speculation' Mandate**: Stability alerts MUST be based on "Verified-Events" and high-confidence predictions, not rumors or social media noise.
- **Rule 2: Commercial-Neutrality**: The agent MUST provide objective stability data regardless of the commercial impact on the agency (e.g., "Do not hide a strike warning just to protect a booking").
- **Rule 3: Tiered-Escalation**: Macro-stability events MUST be escalated to the agency owner for strategic decision-making (e.g., "Should we stop promoting this destination temporarily?").

## 5. Success Metrics (Stability)

- **Disruption-Avoidance-Rate**: % of travelers who successfully avoid delays or cancellations by acting on SIP alerts.
- **Strategic-Decision-Velocity**: Time taken by the agency owner to respond to a macro-stability event based on SIP data.
- **Traveler-Trust-Index (Stability)**: Feedback on the agency's perceived "Inside-Track" on global events.
