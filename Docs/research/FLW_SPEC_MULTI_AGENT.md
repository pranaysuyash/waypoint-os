# Flow Spec: Multi-Agent Coordination (FLW-002)

**Status**: Research/Draft
**Area**: Distributed Agentic Systems

---

## 1. The Problem: "The Siloed Agent"
A 'Flight-Agent' might optimize for the cheapest 6 AM flight, but a 'Hotel-Agent' knows the destination hotel doesn't allow check-in before 3 PM, leaving the traveler stranded for 9 hours. Without a coordination layer, specialized agents produce locally optimal but globally broken itineraries.

## 2. The Solution: 'Agent-Negotiation-Protocol' (ANP)

The ANP facilitates a "Cross-Specialist-Handshake."

### Negotiation Flow:

1.  **Draft-Itinerary-Publication**:
    *   **Action**: The **Logistics-Agent** publishes a "Base-Timeline" (Flights + Hotels) to the internal `Itinerary-Bus`.
2.  **Constraint-Propagation**:
    *   **Action**: The **Experience-Agent** receives the timeline and identifies "Activity-Windows" (e.g., "User lands at 8 AM, check-in at 3 PM. 7-hour gap detected.").
3.  **Specialist-Bid**:
    *   **Action**: The **Experience-Agent** "Bids" to fill the gap with a high-value activity (e.g., "Private Morning Food Tour with Luggage-Storage").
4.  **Conflict-Resolution (The Harmonizer)**:
    *   **Action**: An **Itinerary-Harmonizer** (Supervisory Agent) audits the bid. If the activity ends too close to the hotel check-in or exceeds the budget, it sends a "Revision-Request" to the Experience-Agent.
5.  **Unified-Commit**:
    *   **Action**: All agents sign off on the final timeline. If one agent's tool fails (e.g., flight price changes), a "Global-Rollback" is triggered across all affected segments.

## 3. Data Schema: `Multi_Agent_Message_Bus`

```json
{
  "message_id": "ANP-11223",
  "itinerary_id": "GUID_882",
  "sender": "EXPERIENCE_AGENT",
  "receiver": "LOGISTICS_AGENT",
  "message_type": "GAP_FILL_PROPOSAL",
  "payload": {
    "gap_start": "2026-11-12T08:00:00Z",
    "gap_end": "2026-11-12T15:00:00Z",
    "proposed_activity": "TOKYO_FISH_MARKET_TOUR",
    "logistics_req": "LUGGAGE_TRANSFER_NEEDED"
  },
  "status": "AWAITING_HARMONIZATION"
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Logistics-is-Anchor' Rule**: Flight and Hotel segments are "Hard-Anchors." Activity agents MUST adapt to these anchors unless they can prove a "Better-Global-Anchor" (e.g., moving a flight to save $500).
- **Rule 2: Asynchronous-Commitment**: Agents must not block each other. They work in parallel on drafts and only synchronize during the "Harmonization-Phase."
- **Rule 3: Escalation-Threshold**: If specialists cannot agree on a solution after 3 negotiation cycles, the problem is escalated to the User as a "Preference-Conflict."

## 5. Success Metrics (Coordination)

- **Itinerary-Cohesion-Score**: % of activities that align with check-in/out and transit times without "Dead-Time."
- **Negotiation-Latency**: Time taken for the agent group to reach a consensus.
- **Rollback-Efficiency**: % of dependent segments successfully cancelled/modified when a primary segment fails.
