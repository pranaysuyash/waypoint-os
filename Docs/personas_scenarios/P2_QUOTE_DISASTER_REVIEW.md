# P2-S1: Quote Disaster Review

**Persona**: Agency Owner
**Scenario**: The owner reviews a weekend quote that was sent by a junior agent and discovers it misses the customer’s budget and suitability requirements.

---

## Situation

It is Monday morning and the owner is reviewing quotes produced by the team over the weekend.
One quote stands out because the customer has already declined it.

### Customer context
- Customer: Mr. Mehta
- Request: family trip to Singapore
- Budget: ₹2-3L flexible
- Preference: kid-friendly, easy walking, vegetarian food

### Quote delivered
- Hotel: Marina Bay Sands
- Duration: 5 nights
- Flights: Singapore Airlines business class
- Total: ₹6.5L

### Owner reaction
The owner immediately recognizes the mismatch:
- The quote is over double the stated budget
- The hotel is premium luxury with a casino focus, not a family resort
- No alternative options were offered
- The customer’s request was not honored

## What went wrong

In this scenario:
- The agent prioritized luxury over fit
- The agent did not verify budget feasibility
- There was no automated check for suitability
- The quote lacked a customer-centered alternative

## What the system should show

1. **Quote review summary**
   - Customer request: ₹2-3L family, kid-friendly, vegetarian
   - Quote provided: ₹6.5L, Marina Bay Sands, business-class flights
   - Gap: 217% over budget
   - Suitability risk: not family-friendly

2. **Issue detection**
   - Budget mismatch alert
   - Suitability warning for hotel choice
   - Missing alternatives warning

3. **Corrective suggestion**
   - Suggested option 1: Hard Rock Sentosa, family-friendly, within budget
   - Suggested option 2: Hotel Jen Orchard Gateway, lower cost with good location
   - Suggested fix text: "This option is more aligned with your budget and children’s needs."

4. **Owner action**
   - Approve a revised quote before sending
   - Coach the junior agent on budget/suitability
   - Mark the quote as "needs correction"

## Why this scenario matters

This scenario tests whether the system protects agency quality.
If the owner can identify and correct quote disasters quickly, the agency avoids lost customers and poor reputation.

## Success criteria

- The owner sees a clear warning when a quote exceeds the stated budget.
- The owner sees a suitability mismatch for the suggested hotel.
- The system proposes better alternatives.
- The quote can be marked for revision and routed back to the agent.
