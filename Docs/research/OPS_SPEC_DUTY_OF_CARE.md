# Ops Spec: Duty-of-Care-Reporting (OPS-REAL-008)

**Status**: Research/Draft
**Area**: Corporate Safety & Risk Management

---

## 1. The Problem: "The Visibility Gap"
Corporate "Duty-of-Care" is often a paper-based exercise. In the event of a geopolitical crisis, natural disaster, or local unrest, companies struggle to identify exactly where their travelers are (e.g., "Are they in the hotel or at a meeting across town?") and how to reach them if local cellular networks are congested.

## 2. The Solution: 'Active-Pulse-Protocol' (APP)

The APP allows the agent to act as a "24/7-Security-Operations-Center" for every traveler.

### Monitoring Actions:

1.  **Geo-Fenced-Risk-Alerting**:
    *   **Action**: Integrating with real-time risk feeds (e.g., GeoSure, International SOS) to set "Risk-Radii" around the traveler's PNR locations. If an incident occurs within the radius, the agent initiates an immediate "Pulse-Check."
2.  **Autonomous-Pulse-Check**:
    *   **Action**: Sending a multi-channel "Safety-Query" (WhatsApp, SMS, App-Push, Satellite-Ping). The agent parses the response (e.g., "I'm safe," "I need help") using NLP.
3.  **Instant-Extraction-Logistics**:
    *   **Action**: If "Help" is requested or a "Critical-Risk" is detected, the agent autonomously audits the nearest "Extraction-Points" (e.g., private airfields, secure transport hubs) and reserves seats on the last remaining outgoing flights.
4.  **Stakeholder-Compliance-Reporting**:
    *   **Action**: Providing the company's HR/Security team with a real-time "Safety-Heatmap" showing the status of all employees in the region.

## 3. Data Schema: `Duty_of_Care_Event`

```json
{
  "event_id": "APP-88221",
  "traveler_id": "GUID_9911",
  "current_location_pnr": "SINGAPORE_CHANGI",
  "local_risk_score": 78.5,
  "incident_detected": "LOCAL_UNREST_ZONE_3",
  "pulse_status": "CONFIRMED_SAFE",
  "extraction_plan_id": "EXTRACT-SG-01",
  "last_telemetry_ping": "2026-11-12T14:30:00Z"
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Multi-Path' Communication**: The agent MUST NOT rely on a single communication channel. It must rotate through all available contact methods until a "Pulse-Match" is confirmed.
- **Rule 2: The 'Silent-Distress' Trigger**: The agent MUST allow for a "Safe-Word" or "Silent-Distress-Gesture" (e.g., a specific emoji sequence) that triggers an emergency extraction without alerting local observers.
- **Rule 3: Sovereign-Data-Erasure**: Once a traveler is confirmed back in a "Low-Risk-Home-Zone," the high-fidelity location telemetry (GPS/Satellite data) MUST be autonomously purged to maintain privacy.

## 5. Success Metrics (Safety)

- **Pulse-Response-Latency**: Time from "Incident-Detection" to "Traveler-Status-Confirmed."
- **Extraction-Readiness**: Time to generate a viable multi-modal extraction route (Target: < 10 mins).
- **Security-Compliance-Yield**: % of corporate travelers who remained within "Safe-Operating-Parameters."
