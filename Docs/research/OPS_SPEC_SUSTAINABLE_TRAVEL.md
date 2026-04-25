# Ops Spec: Sustainable-Travel-Weighting (OPS-CO2-001)

**Status**: Research/Draft
**Area**: Environmental Responsibility & Route Optimization

---

## 1. The Problem: "The Invisible Footprint"
Most travelers want to "Travel-Sustainably" but lack the data to make informed choices. Standard CO2 calculators are often vague. A traveler might choose a "Green" flight that is actually on an older, less efficient aircraft, or miss a rail-alternative that is 90% cleaner with only a minor time-increase.

## 2. The Solution: 'Eco-Impact-Protocol' (EIP)

The EIP allows the agent to act as a "Sustainability-Advisor" by integrating high-fidelity carbon data into the decision-loop.

### Optimization Actions:

1.  **Tail-Number-Efficiency-Audit**:
    *   **Action**: Identifying the specific aircraft type (e.g., A350-1000 vs B777-200) for a route and weighting the "Fuel-Burn-Per-Seat."
2.  **Inter-Modal-Alternative-Scouting**:
    *   **Action**: If a flight-segment is < 500km, the agent MUST autonomously propose a "High-Speed-Rail" alternative, highlighting the CO2 savings vs time-loss.
3.  **Verified-Offset-Integration**:
    *   **Action**: Linking the `Sovereign Wallet` (FIN-002) to verified carbon-removal projects (e.g., direct-air-capture, reforestation) to allow "1-Click-Auto-Offsetting."

## 3. Data Schema: `Sustainability_Impact_Report`

```json
{
  "report_id": "EIP-8822",
  "itinerary_id": "ITIN-9911",
  "total_estimated_co2_kg": 450,
  "reduction_achieved_via_optimization": 120,
  "optimization_rationales": [
    "SWITCHED_TO_A350_FROM_B777",
    "PROPOSED_RAIL_FOR_LHR_PAR_SEGMENT"
  ],
  "offset_status": "PENDING_APPROVAL",
  "offset_cost_usd": 12.50
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Green-Tie-Break'**: If two itineraries have identical price and duration (within 5%), the agent MUST default to the one with the lower carbon-score.
- **Rule 2: Carbon-Budget-Enforcement**: Corporate clients can set a "Carbon-Cap" per traveler/year. The agent MUST warn or block bookings that exceed this cap (CORP-001).
- **Rule 3: Transparency-of-Scoring**: The agent must explain "Why" a route is green (e.g., "This airline uses 30% Sustainable Aviation Fuel (SAF) on this route").

## 5. Success Metrics (Sustainability)

- **Average-CO2-Reduction**: % reduction in carbon-footprint per traveler vs baseline travel patterns.
- **Rail-Adoption-Rate**: % of short-haul segments switched from air to rail.
- **Offset-Conversion-Rate**: % of travelers who opted-in for verified carbon offsetting.
