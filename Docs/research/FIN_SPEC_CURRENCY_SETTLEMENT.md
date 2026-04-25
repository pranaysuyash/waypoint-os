# Fin Spec: Multi-Currency & FX Settlement (FIN-REAL-003)

**Status**: Research/Draft
**Area**: Cross-Border Payments & FX Optimization

---

## 1. The Problem: "The FX Markup Trap"
When a traveler from the USA books a hotel in Paris, they are often hit with a 3-5% "Dynamic-Currency-Conversion" (DCC) fee at the terminal or a hidden FX markup from their bank. Over a 10-day trip across multiple countries, these "Leaking-Dollars" can add up to hundreds of dollars in unnecessary fees.

## 2. The Solution: 'Currency-Arbitrage-Protocol' (CAP)

The CAP allows the agent to autonomously decide the "Settlement-Strategy" for every transaction in the itinerary.

### Settlement Actions:

1.  **Local-vs-Home-Currency-Audit**:
    *   **Action**: Comparing the "Pay-Now-in-USD" price on the OTA vs the "Pay-Later-in-EUR" price at the hotel. The agent MUST account for the "FX-Volatility-Buffer" (usually 1-2%) before making a recommendation.
2.  **Card-Capability-Matching**:
    *   **Action**: Checking the traveler's `Identity Vault` (ID-REAL-001) for credit card attributes (e.g., "Does this card have 0% foreign transaction fees?"). If yes, the agent defaults to "Pay-in-Local-Currency."
3.  **Real-Time-Rate-Hedging**:
    *   **Action**: If the traveler is booking a high-value trip 6 months in advance, the agent can recommend "Pre-Paying-Now" if it detects a favorable FX trend or high volatility risk.

## 3. Data Schema: `Currency_Settlement_Instruction`

```json
{
  "instruction_id": "CAP-88221",
  "transaction_id": "TXN-9911",
  "vendor_local_currency": "EUR",
  "traveler_home_currency": "USD",
  "current_spot_rate": 1.08,
  "settlement_verdict": "PAY_IN_LOCAL",
  "estimated_savings_usd": 42.50,
  "rationale": "Traveler has Chase Sapphire (0% FX fee). Local rate is 4.2% cheaper than OTA's USD price."
}
```

## 4. Key Logic Rules

- **Rule 1: Always-Decline-DCC**: The agent MUST autonomously instruct the vendor (or traveler) to "Decline-DCC" (Dynamic Currency Conversion) unless the home-currency price is lower (extremely rare).
- **Rule 2: The 'FX-Volatility-Cap'**: If the target currency has > 5% volatility in the last 30 days, the agent MUST recommend "Pay-Now" to lock in the rate.
- **Rule 3: Multi-Wallet-Routing**: If the traveler has multiple currency accounts (e.g., Revolut/Wise), the agent MUST route the payment from the matching local-currency bucket.

## 5. Success Metrics (Savings)

- **Average-FX-Savings**: % reduction in total FX fees per trip.
- **DCC-Avoidance-Rate**: Target: 100%.
- **Settlement-Accuracy**: Deviation between "Estimated-Savings" and "Actual-Settlement-Cost."
