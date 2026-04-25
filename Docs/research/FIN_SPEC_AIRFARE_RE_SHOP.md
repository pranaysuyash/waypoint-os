# Fin Spec: Dynamic Airfare-Re-Shop (FIN-REAL-006)

**Status**: Research/Draft
**Area**: Price Protection & Yield Management

---

## 1. The Problem: "The Sunk-Cost-Fallacy"
Once an airfare is ticketed, travelers assume the price is fixed. However, prices often drop. If the drop exceeds the airline's change/cancellation fee, the traveler is "Leaving-Money-on-the-Table." Manual monitoring of thousands of ticketed PNRs is impossible for human agents.

## 2. The Solution: 'Post-Ticket-Yield-Management' (PTYM)

The PTYM allows the agent to act as a "Price-Vigilante" by monitoring fares even after a transaction is finalized.

### Re-Shop Actions:

1.  **PNR-Shadow-Polling**:
    *   **Action**: Continuously querying the GDS/API for the exact route/date/class of ticketed PNRs to identify "Price-Deltas."
2.  **Net-Savings-Calculation**:
    *   **Action**: Calculating the "Net-Gain" after subtracting:
        - Airline Change/Cancellation Fee.
        - Agency Re-Issue Fee (FIN-REAL-002).
        - Risk of losing seat assignment/loyalty-upgrade status.
3.  **Autonomous-Re-Issue-Execution**:
    *   **Action**: If "Net-Gain" > $50 (or traveler's threshold), the agent autonomously cancels the old PNR and issues the new one, capturing the difference as an "Airline-Credit" or "Refund."

## 3. Data Schema: `Price_Protection_Audit`

```json
{
  "audit_id": "PTYM-88221",
  "pnr_id": "PNR-992211",
  "original_fare_usd": 1250.00,
  "current_market_fare_usd": 980.00,
  "airline_penalty_usd": 150.00,
  "net_savings_usd": 120.00,
  "execution_verdict": "TRIGGER_RE_ISSUE",
  "traveler_benefit_form": "FUTURE_TRAVEL_CREDIT"
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Seat-Preservation' Filter**: The agent MUST NOT re-issue the ticket if the "New-Fare-Class" doesn't allow for the same (or better) seat assignment as the original.
- **Rule 2: Refundable-Preference**: The agent MUST prioritize re-booking into "Refundable" classes if the price-delta allows, to maximize future flexibility.
- **Rule 3: Agency-Share**: The agent captures a 20% "Savings-Success-Fee" (FIN-REAL-002) of the net savings achieved.

## 5. Success Metrics (Savings)

- **Total-Price-Protection-Yield**: Aggregate $ saved for travelers through post-ticket re-shopping.
- **Yield-Success-Rate**: % of ticketed PNRs that resulted in a successful re-issue for savings.
- **Customer-Lifetime-Value (CLV)**: Increase in traveler retention due to "Found-Money" delight.
