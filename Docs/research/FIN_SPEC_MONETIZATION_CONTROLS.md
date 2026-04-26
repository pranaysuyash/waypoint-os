# Fin Spec: Agency-Specific Monetization-Controller (FIN-REAL-019)

**Status**: Research/Draft
**Area**: Agency Revenue & Monetization

---

## 1. The Problem: "The Static Service Fee"
In a competitive travel market, agencies need flexible monetization strategies. A flat service fee often fails to capture the "Value-Created" by an agentic intervention (e.g., saving a traveler $1,000 on a re-booked flight). Agencies need the ability to define dynamic, multi-layered revenue models that align with their specific business goals and traveler tiers.

## 2. The Solution: 'Commercial-Autonomy-Protocol' (CAP)

The CAP allows each agency to define its "Revenue-Stack."

### Monetization Actions:

1.  **Success-Fee Arbitrage**:
    *   **Action**: Configuring the agent to charge a "Success-Fee" (e.g., "15% of the delta") when it achieves a "Significant-Saving" (e.g., re-booking a canceled flight for less than the original cost).
2.  **Incident-Complexity Surcharge**:
    *   **Action**: Automatically applying a "Service-Surcharge" for complex incidents that require high-intensity agentic logic or human-escalation (e.g., "Crisis-Management-Fee").
3.  **Tiered Markup-Logic**:
    *   **Action**: Defining different "Markup-Thresholds" based on traveler segments (e.g., 5% for VIPs to maintain loyalty, 12% for one-off leisure bookings to maximize margin).
4.  **Agentic 'Value-Capture' Report**:
    *   **Action**: Generating a "Transparent-Value-Statement" for the traveler, showing exactly how much the agent saved them (in time and money) to justify the service fees.

## 3. Data Schema: `Agency_Revenue_Model`

```json
{
  "agency_id": "AGENCY_ALPHA_99",
  "success_fee_percentage": 0.15,
  "min_save_threshold_usd": 100.00,
  "complexity_surcharges": {
    "FLIGHT_CANCEL_REBOOK": 25.00,
    "VISA_EMERGENCY_SUPPORT": 50.00
  },
  "tiered_markups": {
    "VIP": 0.05,
    "STANDARD": 0.10
  },
  "status": "REVENUE_LOGIC_ACTIVE"
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Transparency-Mandate'**: All service fees and markups MUST be clearly disclosed to the traveler in the "Final-Invoice" or "Value-Statement" to avoid "Hidden-Cost" complaints.
- **Rule 2: Cap-on-Complexity**: Agencies MUST be able to define a "Maximum-Total-Fee" per trip to ensure costs don't spiral during high-volatility events.
- **Rule 3: Refund-Integrity**: If an agentic action fails or is reverted (e.g., a re-booked flight is also canceled), the associated "Success-Fee" MUST be autonomously credited back to the traveler.

## 5. Success Metrics (Monetization)

- **Revenue-per-Incident (RPI)**: Average agency profit generated per agentic intervention.
- **Value-Statement-Acceptance**: % of travelers who express satisfaction or neutral sentiment after viewing the "Value-Capture" report.
- **Monetization-Agility**: Time taken to update and apply a new fee structure across the tenant's bookings.
