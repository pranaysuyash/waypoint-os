# Game Spec: Multi-Agent Slot-Trading (GAME-001)

**Status**: Research/Draft
**Area**: Agentic Negotiation & Resource Allocation

---

## 1. The Problem: "The Zero-Sum Scramble"
In a mass-cancellation, everyone wants the same 5 seats. Traditional systems use "First-Come-First-Served" (latency-based) or "Highest-Tier" (loyalty-based). This leaves high-value situational needs (e.g., a traveler needing to reach a funeral or medical surgery) unaddressed if they aren't "Gold Status."

## 2. The Solution: 'Secondary-Market-Negotiation' (SMN)

The SMN allows agents to "Communicate" and "Trade" slots using a value-based exchange protocol.

### Negotiation Layers:

1.  **Direct-Trade (Peer-to-Peer)**:
    *   **Action**: Agent A (representing a business traveler) offers Agent B (representing a flexible leisure traveler) a $200 travel credit to "Swap" their seat on the last flight out.
2.  **Autonomous Bidding (Pool-based)**:
    *   **Action**: Multiple agents bid for a "Shadow-Inventory" of seats that airlines keep for irregular operations (IROPS).
3.  **Collaborative Chartering (Group-based)**:
    *   **Action**: Agents 1-20 realize they have 20 travelers stuck at Hub X. Instead of fighting for seats on Hub Y, they pool budgets and autonomously "Request" a 20-seat charter or bus.

## 3. Data Schema: `Slot_Negotiation_Payload`

```json
{
  "negotiation_id": "NEG-GAME-5544",
  "resource": "FLIGHT_SEAT_LH400_10MAY",
  "requesting_agent": "AGENT_WAYPOINT_001",
  "offering_agent": "AGENT_SABRE_VIRTUAL_09",
  "offer_type": "VALUE_EXCHANGE",
  "offer_value": {
    "currency": "USD",
    "amount": 250,
    "source": "TRAVELER_CONTINGENCY_BUDGET"
  },
  "justification_code": "CRITICAL_MEDICAL_NECESSITY",
  "verdict": "ACCEPTED"
}
```

## 4. Key Logic Rules

- **Rule 1: Hard-Budget-Caps**: Agents can only bid/trade within the traveler's pre-authorized "Contingency Budget."
- **Rule 2: Proof-of-Urgency**: To prevent "Budget-Bullying" (rich travelers buying all seats), agents must provide an 'Urgency-Token' (vetted by the agency's internal logic) to participate in the 'Sovereign' tier of negotiation.
- **Rule 3: Transparency Audit**: Every "Trade" or "Bid" is recorded in the `AuditStore` and the `Evidence Vault` to prevent collusive or predatory agent behavior.

## 5. Success Metrics (Negotiation)

- **Utility Maxima**: Increase in the total "Weighted-Urgency" of travelers who successfully reached their destinations.
- **Fairness-Coefficient**: % of "Urgent-but-Low-Budget" travelers served vs. "Non-Urgent-but-High-Budget."
- **Market Liquidity**: Number of successful "Agent-to-Agent" trades completed during a disruption.
