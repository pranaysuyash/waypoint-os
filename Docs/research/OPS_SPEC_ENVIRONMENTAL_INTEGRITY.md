# Ops Spec: Agentic 'Environmental-Integrity' Monitor (OPS-REAL-024)

**Status**: Research/Draft
**Area**: Traveler Health & Environmental Intelligence

---

## 1. The Problem: "The Invisible Travel Stressor"
Travelers often face environmental stressors that are not captured in standard itineraries: "High-Pollution" (AQI) levels in urban centers, "Intense-UV" radiation, "Extreme-Heatwaves," or "High-Pollen" counts. For travelers with respiratory issues, allergies, or heat sensitivity (identified in the TWO), these stressors can ruin a trip. Current travel agencies rarely provide "Proactive-Environmental-Protection."

## 2. The Solution: 'Atmospheric-Intelligence-Protocol' (AIP)

The AIP acts as the "Environmental-Guardian."

### Intelligence Actions:

1.  **Hyper-Local-AQI-Monitoring**:
    *   **Action**: Monitoring real-time Air Quality Index (AQI) and pollution levels (PM2.5, NO2) for the traveler's specific location (e.g., "The AQI in Bangkok is currently 180; recommend indoor activities for the next 4 hours").
2.  **Climate-Stressor-Alerting**:
    *   **Action**: Monitoring for UV index peaks, heatwave warnings, and extreme humidity. The agent autonomously suggests "Comfort-Pivots" (e.g., "UV index is 11+ in Santorini; suggest moving the hike to 6 PM and providing an umbrella").
3.  **Allergy-Watchdog**:
    *   **Action**: Cross-referencing the traveler's "Allergy-Profile" with local pollen counts or specific environmental triggers (e.g., "High cedar pollen in Kyoto; suggest pharmacy locations and indoor garden alternatives").
4.  **Eco-Impact-Transparency**:
    *   **Action**: Providing the agency owner with data on the "Environmental-Suitability" of destinations, allowing them to advise travelers on the best times to visit based on "Atmospheric-Health."

## 3. Data Schema: `Environmental_Incident_Alert`

```json
{
  "alert_id": "AIP-33221",
  "traveler_id": "TRAVELER_Y",
  "incident_type": "HIGH_POLLUTION_PEAK",
  "location": "BEIJING_DOWNTOWN",
  "current_aqi": 210,
  "risk_category": "RESPIRATORY_HEALTH",
  "recommended_action": "PIVOT_TO_INDOOR_MUSEUM_TIER_2",
  "status": "ALERT_SENT_TO_TRAVELER"
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Vulnerability-Linkage'**: Environmental alerts MUST be filtered through the traveler's "Health-Profile" in the TWO. A healthy traveler gets a "Warning," while a traveler with asthma gets a "Critical-Pivot-Recommendation."
- **Rule 2: Proactive-Alternative-Sourcing**: The agent MUST NOT just report a problem; it MUST provide a "Suitability-Equivalent" indoor or low-impact alternative.
- **Rule 3: Agency-Branded-Safety**: Alerts MUST be branded as the agency's "Wellness-Care-Service," reinforcing the value of the agency owner's expertise.

## 5. Success Metrics (Environment)

- **Respiratory-Incident-Reduction**: Decrease in travelers reporting health issues related to air quality or allergies.
- **Itinerary-Comfort-Score**: Traveler feedback on how well the agent managed environmental stressors during the trip.
- **Environmental-Awareness-Rate**: % of travelers who take the agent's recommended "Comfort-Pivot."
