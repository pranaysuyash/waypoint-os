# Operational Logic Spec: Adversarial Integrity (OE-004)

**Status**: Research/Draft
**Area**: AI Hallucination Defense & Truth Grounding

---

## 1. The Problem: "Creative Hallucinations"
In high-stakes disruption recovery (e.g., Bankruptcy OE-001), the AI is incentivized to find a solution quickly. This can lead to "Creative Hallucinations" where the AI proposes a flight that doesn't exist, a visa-free route that requires a visa, or a price that is unavailable.

## 2. The Solution: Double-Blind Verification (DBV)

The system must implement a **Double-Blind Verification** protocol where the "Action Agent" (who proposes the solution) and the "Validator Agent" (who checks the constraints) are logically separated.

### Protocol Steps:

1. **Solution Proposal (Agent A)**:
   - Proposes a recovery plan (e.g., "Re-book on BA123 via LHR").
   - Includes the rationale and the assumed constraints (e.g., "Transit visa not required for UK stay < 24h").

2. **Constraint Verification (Agent B - The Red-Team)**:
   - Receives ONLY the raw itinerary from Agent A.
   - Does NOT see Agent A's rationale.
   - Independently queries the **Ground-Truth Source** (e.g., Timatic, IATA, Real-time GDS).
   - Generates its own "Constraint Report" (e.g., "British citizen: Visa not required. Indian citizen: Transit visa REQUIRED").

3. **Conflict Resolution**:
   - If `Agent_A_Assumptions == Agent_B_Reality`, proceed to execution.
   - If `Agent_A_Assumptions != Agent_B_Reality`, block the action and escalate to the `Human_Review_Queue` with a "Hallucination Risk" flag.

## 3. Data Schema: `Integrity_Check_Payload`

```json
{
  "solution_id": "RECOV-12345",
  "proposal": {
    "segments": ["SIN-LHR-JFK"],
    "carrier": "BA",
    "total_cost": 1200
  },
  "constraints_checked": [
    "passport_validity",
    "visa_requirements",
    "health_documentation",
    "inventory_liveness"
  ],
  "validator_status": "FAIL",
  "conflict_details": "Agent A assumed SIN-LHR transit is visa-free for Indian passports. Validator confirmed Transit Visa required."
}
```

## 4. Key Logic Rules

- **Rule 1: Isolation**: The Validator must have no access to the Action Agent's "Chain of Thought." It must work only from the final proposed output.
- **Rule 2: Negative Priority**: The Validator is rewarded for finding "Why this will FAIL" rather than confirming success.
- **Rule 3: GDS-Lock**: Before any autonomous booking, the Validator must perform a "Liveness Ping" to the GDS to ensure the seat and price still exist.

## 5. Success Metrics

- **Zero-False-Recovery**: No traveler is ever sent to a gate where they are denied boarding due to a system-proposed invalid route.
- **Latency-Budget**: DBV must complete within 30 seconds to maintain the 120s recovery SLA.
- **Hallucination-Capture-Rate**: Percentage of invalid AI-proposed plans caught before traveler notification.
