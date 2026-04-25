# Ops Spec: Real-Time Weather-Itinerary-Pivot (OPS-REAL-016)

**Status**: Research/Draft
**Area**: Itinerary Resilience & Climate Adaptation

---

## 1. The Problem: "The Rainout"
Travelers often book outdoor-dependent activities (e.g., helicopter tours, boat trips, hiking) weeks in advance. When the actual weather forecast turns bad (T-48h), the traveler is often left to manually find an alternative, navigate cancellation policies, and re-book their day while already on the trip, leading to stress and lost value.

## 2. The Solution: 'Adaptive-Climate-Logic-Protocol' (ACLP)

The ACLP allows the agent to act as a "Weather-Resilient-Coordinator."

### Pivot Actions:

1.  **Forecast-Itinerary-Interrogation**:
    *   **Action**: Continuously cross-referencing the 48-hour forecast with the traveler's scheduled activities.
2.  **Risk-Threshold-Trigger**:
    *   **Action**: If the probability of adverse weather (e.g., Rain > 60%, Wind > 30 knots) exceeds the "Activity-Tolerance-Level," the agent triggers a "Pivot-Search."
3.  **Indoor-Alternative-Sourcing**:
    *   **Action**: Identifying high-value indoor alternatives (e.g., private museum tours, thermal baths, culinary workshops) that fit the same time-slot and interest-profile.
4.  **Cancellation-Policy-Audit**:
    *   **Action**: Autonomously auditing the 'Force-Majeure' or 'Flexible-Cancellation' window for the primary activity to ensure a full refund is possible before re-booking the alternative.

## 3. Data Schema: `Weather_Pivot_Event`

```json
{
  "event_id": "ACLP-11221",
  "traveler_id": "GUID_9911",
  "primary_activity": "NAPALI_COAST_BOAT_TOUR",
  "weather_risk": "HIGH_RAIN_WIND",
  "forecast_source": "OPENWEATHER_API",
  "alternative_proposed": "KAUAI_MUSEUM_PRIVATE_TOUR",
  "cancellation_status": "REFUND_CONFIRMED",
  "itinerary_updated": false,
  "user_approval_required": true
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Tolerance-Matching' Rule**: The agent MUST NOT suggest a pivot if the weather risk is below the traveler's stated preference (e.g., some travelers don't mind light rain for a hike).
- **Rule 2: The 'Window-Safety' Guardrail**: The agent MUST NOT re-book the alternative until the primary activity's refund is "Contractually-Secure."
- **Rule 3: One-Tap-Confirmation**: The agent presents the pivot as a single choice: "Heavy rain forecasted for your boat tour. I've found a private museum tour at the same time. Tap to swap and process refund."

## 5. Success Metrics (Resilience)

- **Pivot-Conversion-Rate**: % of weather-related suggestions accepted by the user.
- **Lost-Value-Avoidance**: Total USD saved by processing cancellations before the no-refund window closes.
- **Itinerary-Continuity**: Reduction in "Dead-Time" caused by cancelled weather-dependent activities.
