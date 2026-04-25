# Fin Spec: Dynamic Service-Fee Logic (FIN-REAL-002)

**Status**: Research/Draft
**Area**: Agency Monetization & Value Measurement

---

## 1. The Problem: "The Flat-Fee Fallacy"
Most travel agencies charge a flat fee (e.g., $50 per booking). This fails to account for the actual "Agentic-Labor" involved. A simple 1-way flight takes 10 seconds of processing, whereas a multi-city, interlined itinerary with visa-checks and ground-transfers takes hours of background research and risk-auditing. The agency needs a way to price its "Intelligence" fairly.

## 2. The Solution: 'Agentic-Labor-Pricing-Protocol' (ALPP)

The ALPP allows the agent to autonomously calculate its fee based on the 'Complexity-Profile' of the journey.

### Pricing Dimensions:

1.  **Itinerary-Complexity-Score (ICS)**:
    *   **Calculation**: Weighted sum of: Number of segments (+5), Number of vendors (+10), Cross-border/Visa requirements (+20), Virtual-Interlining checks (+30).
2.  **Savings-Sharing-Premium (SSP)**:
    *   **Calculation**: If the agent finds a route that is > $200 cheaper than the traveler's baseline or standard OTA price, it captures a 10% "Efficiency-Commission" of the savings.
3.  **Risk-Monitoring-Retainer**:
    *   **Calculation**: A subscription-style fee for "Continuous-Watchdog" monitoring (OPS-001) for the duration of the trip (e.g., $2 per day).

## 3. Data Schema: `Service_Fee_Calculation`

```json
{
  "fee_id": "ALPP-88221",
  "itinerary_id": "ITIN-9911",
  "base_processing_fee": 15.00,
  "complexity_premium": 45.00,
  "savings_commission": 22.50,
  "risk_monitoring_fee": 14.00,
  "total_service_fee": 96.50,
  "logic_rationale": "Multi-vendor virtual interline with 7 days of active disruption monitoring."
}
```

## 4. Key Logic Rules

- **Rule 1: Fee-Transparency**: The agent MUST explain the breakdown of the fee to the traveler (e.g., "Why is it $96? Because we are monitoring 4 different airlines for 7 days").
- **Rule 2: The 'No-Savings-No-Premium' Rule**: If the agent cannot find a route cheaper than the market average, the SSP is waived.
- **Rule 3: Corporate-Volume-Discount**: For B2B clients (CORP-001), the complexity premiums are capped at a negotiated rate.

## 5. Success Metrics (Monetization)

- **Revenue-Per-Booking (RPB)**: Target increase of 30% vs flat-fee models.
- **Traveler-Sentiment-on-Fees**: % of travelers who accept the fee without dispute (Target: > 95%).
- **Margin-Efficiency**: Ratio of "Agentic-Compute-Cost" to "Service-Fee-Captured."
