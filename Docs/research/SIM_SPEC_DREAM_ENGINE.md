# Simulation Spec: The 'Dream' Engine (SIM-001)

**Status**: Research/Draft
**Area**: Predictive Simulation & Synthetic Risk Analysis

---

## 1. The Problem: "The Single-Path Plan"
Traditional travel plans are linear. If a disruption occurs, the "Plan" breaks and the agent starts from scratch. This is inefficient. For a $10,000 trip, the cost of "Thinking" after the failure is too high.

## 2. The Solution: 'Cascading-Scenario-Rehearsal' (CSR)

The 'Dream' Engine (DE) performs massively parallel simulations of potential failures BEFORE the traveler leaves their house.

### Simulation Layers:

1.  **Monte-Carlo Failure Analysis**:
    *   **Action**: Running 10,000 simulations of the itinerary against current/historical hub performance (e.g., CDG Terminal 2E transfer failure probability).
2.  **Soft-Reservation Stacking**:
    *   **Action**: If failure probability for Leg X > 15%, the agent autonomously places "Soft-Holds" (no-cost backups) for the most likely recovery paths.
3.  **Communication Pre-generation**:
    *   **Action**: The agent pre-drafts the "First-Response" messages for each failure mode, ensuring the tone is calibrated to the traveler's active "Identity Mode."

## 3. Data Schema: `Itinerary_Fragility_Map`

```json
{
  "itinerary_id": "IT-4455",
  "total_fragility_score": 0.38,
  "nodes": [
    {
      "segment": "LHR-CDG",
      "failure_modes": [
        {"type": "MISS_CONNECTION", "prob": 0.22, "impact": "HIGH"},
        {"type": "TECH_DELAY", "prob": 0.05, "impact": "MEDIUM"}
      ],
      "active_dreams": [
        "DREAM-AF-102",
        "DREAM-EUROSTAR-ALT"
      ]
    }
  ],
  "pre_negotiated_holds": [
    "RESERVATION_ID_XYZ_SOFT_HOLD"
  ]
}
```

## 4. Key Logic Rules

- **Rule 1: Probability-Gated Stacking**: The agent only places "Soft-Holds" for scenarios where the probability is > threshold (e.g., 10%) and the "Option-Evaporation-Rate" (how fast backups sell out) is HIGH.
- **Rule 2: 'Dream-to-Reality' Promotion**: The moment a disruption is detected, the agent doesn't "Search"; it "Promotes" the best 'Dream' (simulated path) to the 'Active' itinerary.
- **Rule 3: Simulation Integrity**: Simulations must use REAL "Dynamic Pricing" and "Live Inventory" to ensure the 'Dreams' are executable in reality.

## 5. Success Metrics (Readiness)

- **Promotion Latency**: Time to activate a backup path after disruption (Target: < 2 seconds).
- **Soft-Hold Conversion**: % of disruptions where a pre-negotiated "Soft-Hold" was the final recovery path.
- **Cognitive Load Reduction**: Reduction in "In-Crisis" token usage by pre-computing recovery options.
