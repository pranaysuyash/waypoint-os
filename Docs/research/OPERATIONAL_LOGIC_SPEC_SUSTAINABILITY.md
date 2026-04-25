# Operational Logic Spec: Sustainability & Carbon-Budgeting (OE-011)

**Status**: Research/Draft
**Area**: Environmental Compliance & Ethical Commercials

---

## 1. The Problem: "The Green-Washing Gap"
Companies commit to Net-Zero, but their travel agents still default to the fastest/cheapest flight. The traveler has no visibility into their "Individual Carbon Budget" during the booking or recovery phase.

## 2. The Solution: The 'Green Ledger' (Emission-Weighting)

The system must implement a **Carbon-Budgeting Engine** that treats CO2 emissions as a "Currency" alongside USD.

### Ledger Mechanisms:

1.  **Carbon-Quota Enforcement**:
    *   Each traveler/project is assigned a `Carbon_Limit` (e.g., 5,000kg CO2 per year).
    *   The system blocks "Ready-to-Book" if the trip exceeds the remaining quota.

2.  **Emission-Weighted Search**:
    *   A search for "Paris to London" should rank Eurostar (Rail) above Air France (Air) due to the 10x lower emission score.
    *   The `Suitability_Score` is penalized for high-emission routes.

3.  **Autonomous Carbon-Offset**:
    *   If a high-emission route is the ONLY option (e.g., trans-Atlantic), the system auto-calculates and purchases a "High-Integrity Carbon Removal" credit as part of the booking.

## 3. Data Schema: `Carbon_Audit`

```json
{
  "trip_id": "T-1122",
  "project_id": "PRJ-GREEN-2026",
  "estimated_co2_kg": 1250,
  "quota_check": {
    "remaining_before": 2000,
    "remaining_after": 750,
    "status": "PASS"
  },
  "modality_delta": {
    "chosen_air_co2": 1250,
    "available_rail_co2": 150,
    "rationale": "Rail not chosen due to 12-hour time penalty exceeding corporate threshold."
  },
  "offset_id": "OFF-77-VERRA"
}
```

## 4. Key Logic Rules

- **Rule 1: Rail-First Priority**: For any trip < 500km, the system MUST show a Rail alternative as the #1 "Green Choice."
- **Rule 2: The 'Cost-of-Carbon' Internal Tax**: Firms can set an internal price for carbon (e.g., $100 per ton). This "Tax" is added to the quote for internal comparison purposes.
- **Rule 3: Transparency Badge**: Every quote must include a "Green Score" (A-F) based on the route's emission efficiency.

## 5. Success Metrics (Sustainability)

- **Emission Reduction**: Percentage decrease in total corporate travel carbon footprint year-over-year.
- **Rail Adoption Rate**: Increase in rail bookings for eligible short-haul routes.
- **Quota Adherence**: 100% of trips staying within the assigned carbon budget.
