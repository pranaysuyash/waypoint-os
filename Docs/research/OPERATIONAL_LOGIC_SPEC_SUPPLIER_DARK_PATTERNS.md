# Operational Logic Spec: Supplier 'Dark Pattern' Detection (OE-008)

**Status**: Research/Draft
**Area**: Supply Chain Integrity & Ethical Sourcing

---

## 1. The Problem: "The Predatory Supplier"
Travelers often face "Dark Patterns" from suppliers:
- **Artificial Scarcity**: "Only 1 room left!" (when the hotel is half empty).
- **Overbooking Optimization**: Hotels that intentionally overbook 110% to account for cancellations, leading to "Walking" the guest to a lower-tier property.
- **Drip Pricing**: Hiding mandatory "Resort Fees" or "Cleaning Fees" until the final payment page.
- **Hidden-City Ticketing**: Airlines that penalize travelers for not flying the final leg of a cheaper indirect flight.

## 2. The Solution: Supplier Reputation Index (SRI)

The system must implement a **Supplier Reputation Index** that monitors real-world outcomes against supplier promises.

### Audit Mechanisms:

1. **Walking Detection**:
   - If a traveler reports "Relocated by Hotel," flag the property for `Overbooking_Fraud`.
   - Action: Temporary de-ranking in the recommendation engine.

2. **Drip-Price Scraper**:
   - AI must perform a "Shadow Checkout" to capture all hidden fees before presenting the quote to the traveler.
   - Action: Show `True_Total_Cost` vs. `Supplier_Stated_Base`.

3. **Insolvency Signal Monitor**:
   - Tracking social media sentiment and financial news for "Mass Refund Delays."
   - Action: Trigger `Pre-emptive_Stop_Sell` for high-risk suppliers.

## 3. Data Schema: `Supplier_Reputation_Report`

```json
{
  "supplier_id": "AIRLINE-XYZ-01",
  "pattern_type": "DRIP_PRICING",
  "evidence": {
    "base_price": 400,
    "mandatory_hidden_fees": 120,
    "delta_percentage": "30%",
    "detected_at": "2026-04-24T12:00:00Z"
  },
  "trust_score": 45,
  "system_action": "DE_RANK_IN_SEARCH",
  "owner_alert": "Supplier XYZ has increased hidden fees by 15% this month. Recommend alternative: Supplier ABC."
}
```

## 4. Key Logic Rules

- **Rule 1: Ethical Bias**: The recommendation engine must default to the supplier with the highest `Trust_Score`, even if it is 5% more expensive than a "Dark Pattern" competitor.
- **Rule 2: Transparency Shield**: Any detected "Hidden Fee" must be rendered in **Bold Red** in the traveler's quote as a "Warning: This supplier hides fees."
- **Rule 3: Collective Defense**: If 3 travelers from the agency are "Walked" by the same hotel in 30 days, the system must trigger an automatic "Stop-Sell" for that property for 6 months.

## 5. Success Metrics

- **Price Integrity**: Zero "Surprise Fees" at checkout for travelers.
- **Walking Rate**: Percentage of travelers successfully housed in their original chosen property.
- **Supplier Pivot**: Percentage of bookings shifted from low-trust to high-trust suppliers.
