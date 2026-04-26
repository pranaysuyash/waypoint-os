# Fin Spec: Agentic 'Affiliate-Arbitrage' Engine (FIN-REAL-021)

**Status**: Research/Draft
**Area**: Agency Partner Revenue & Commission Optimization

---

## 1. The Problem: "The Untapped Commission"
Travel agencies often have "Tiered-Affiliate-Agreements" with various vendors (Hotels, Car Rentals, Tour Operators). However, human agents (and simple search engines) often fail to prioritize the most "Lucrative-Partners" because the commission data is siloed or complex to calculate in real-time. This leads to "Revenue-Leakage" where a traveler is booked into a suitable property that pays 5% commission, when an equally suitable property pays 12%.

## 2. The Solution: 'Commercial-Alignment-Protocol' (CAP)

The CAP allows the agent to act as a "Revenue-Optimizer."

### Arbitrage Actions:

1.  **Commission-Data Aggregation**:
    *   **Action**: Ingesting the agency's "Partner-Commission-Grids" and identifying the "Net-Profit-per-Booking" for every available option.
2.  **Suitability-Equivalence-Testing**:
    *   **Action**: Using the "Suitability-Engine" to identify "Tied-Options" (e.g., two 5-star hotels in Paris with similar amenities and locations that both meet the traveler's TWO).
3.  **Revenue-Weighted Ranking**:
    *   **Action**: If options are "Suitability-Equivalent," the agent re-ranks the suggestions to prioritize the option with the "Highest-Agency-Margin."
4.  **Incentive-Gap Alerting**:
    *   **Action**: If a specific vendor is "Near-a-Tier-Bonus" (e.g., "5 more bookings this month triggers a 2% override across all bookings"), the agent flags this "Revenue-Opportunity" to the agency owner.

## 3. Data Schema: `Affiliate_Arbitrage_Result`

```json
{
  "arbitrage_id": "CAP-77221",
  "traveler_id": "GUID_9911",
  "original_top_pick": "HOTEL_LUXE_PARIS",
  "arbitraged_top_pick": "PALACE_VENDOME_PARIS",
  "suitability_delta": 0.02,
  "margin_differential_usd": 125.00,
  "reasoning": "Palace Vendome pays 12% commission (Tier 3) vs Hotel Luxe 5%. Suitability remains >95%.",
  "status": "ARBITRAGE_APPLIED"
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Suitability-First' Guardrail**: The agent MUST NOT suggest a higher-commission option if it significantly reduces the "Traveler-Suitability-Score" (e.g., a delta of >5%). The traveler's needs remain the primary constraint.
- **Rule 2: Conflict-of-Interest Disclosure**: If an agency policy requires transparency, the agent MUST be able to tag the suggestion as a "Preferred-Partner" to the traveler.
- **Rule 3: Dynamic-Override-Logic**: Agencies MUST be able to manually "Boost" specific partners for a limited time (e.g., during a specific promotional campaign).

## 5. Success Metrics (Arbitrage)

- **Commission-Yield-Increase**: Average increase in agency commission % per booking after applying CAP.
- **Suitability-Retention-Rate**: % of "Arbitraged" bookings where the traveler provides positive feedback on the specific property.
- **Tier-Bonus-Capture**: Number of annual volume-based commission bonuses successfully triggered by agentic steering.
