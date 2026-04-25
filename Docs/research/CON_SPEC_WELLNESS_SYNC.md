# Con Spec: Hyper-Personalized Wellness-Sync (CON-REAL-008)

**Status**: Research/Draft
**Area**: Traveler Wellbeing & Bio-Resilience

---

## 1. The Problem: "The Jet-Lag Deficit"
Long-haul travelers often suffer from "Circadian-Dysregulation" (jet-lag), which can waste the first 2-3 days of a trip. Generic advice (e.g., "Drink water," "Stay awake") fails to account for individual biometric recovery speeds, current sleep-debt, and the specific light/temperature environment of the traveler's hotel room.

## 2. The Solution: 'Circadian-Alignment-Logic' (CAL)

The CAL allows the agent to act as a "Bio-Regulatory-Coach."

### Wellness Actions:

1.  **Biometric Recovery-Audit**:
    *   **Action**: Analyzing real-time data from the traveler's smart-watch (Apple Health, Oura, Garmin) to assess sleep-quality, HRV (Heart Rate Variability), and core-temperature.
2.  **Environment-IoT-Sync**:
    *   **Action**: Coordinating with "Connected-Hotels" (via property management APIs) to autonomously adjust the traveler's room lighting (Blue-light for alertness, Amber for sleep-prep) and temperature to match the "Optimal-Circadian-Shift."
3.  **Meal-Timing-Optimization**:
    *   **Action**: Pushing "Metabolic-Pings" to the traveler's device, suggesting specific times to eat (and what to avoid, e.g., "Avoid caffeine after 3 PM Tokyo time") to reset their internal clock.
4.  **Activity-Load-Balancing**:
    *   **Action**: Autonomously re-scheduling "High-Cognitive-Demand" activities (e.g., business meetings, complex tours) to the traveler's predicted "Peak-Alertness-Windows" based on their biometric trend.

## 3. Data Schema: `Circadian_Sync_Engagement`

```json
{
  "engagement_id": "CAL-99221",
  "traveler_id": "GUID_9911",
  "timezone_shift": "+9h",
  "biometric_readiness": 0.78,
  "optimal_sleep_window_utc": "2026-11-15T13:00:00Z",
  "room_temp_target_c": 18.5,
  "light_mode": "CIRCADIAN_DUSK",
  "metabolic_advice": "High-protein snack at T+2h",
  "status": "SYNCED_TO_HOTEL_IOT"
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Gradual-Shift' Rule**: The agent MUST initiate the circadian shift T-48h before departure by incrementally adjusting the traveler's "Sleep-Reminders" in their home time-zone.
- **Rule 2: Light-Exposure-Anchor**: The agent MUST identify "Outdoor-Light-Windows" at the destination (e.g., "Walk in Hyde Park between 9 AM and 11 AM") to provide the necessary ocular light-reset.
- **Rule 3: Privacy-Sovereignty**: Biometric data is analyzed "In-Memory" only; the agent MUST NOT store raw biometric values, only the resulting "Wellness-Recommendations."

## 5. Success Metrics (Wellness)

- **Recovery-Speed-Index**: Number of days taken for HRV to return to baseline at the destination.
- **Alertness-Window-Accuracy**: Correlation between agent-predicted "Peak-Windows" and traveler-reported energy levels.
- **IoT-Sync-Reliability**: % of hotel environments successfully automated without traveler intervention.
