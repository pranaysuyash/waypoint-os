# Ops Spec: Real-Time Security-Perimeter-Audit (OPS-REAL-019)

**Status**: Research/Draft
**Area**: Physical Safety & Crisis Management

---

## 1. The Problem: "The Blind Traveler"
Travelers often enter "High-Risk-Zones" (protests, high-crime districts, areas with active security incidents) simply because they are following the "Shortest-Path" on a generic map. Traditional maps do not account for real-time volatility (e.g., "A protest just flared up 2 blocks away"), leaving travelers vulnerable to physical harm or transit lockdowns.

## 2. The Solution: 'Urban-Safe-Zone-Logic' (USZL)

The USZL allows the agent to act as a "Tactical-Safety-Officer."

### Safety Actions:

1.  **Multi-Source Volatility-Feed**:
    *   **Action**: Aggregating real-time data from local police scanner APIs, emergency services (911/112), geo-tagged social media clusters (X/Twitter), and official government advisories.
2.  **GPS-Proximity-Watchdog**:
    *   **Action**: Monitoring the traveler's GPS location against the detected "Hot-Zones." If the traveler is within a "Critical-Radius" (e.g., 500m) of an active incident, the agent triggers an immediate alert.
3.  **Autonomous Secure-Re-Route**:
    *   **Action**: If a planned route passes through a high-risk area, the agent autonomously recalculates a "Safety-Optimized-Route" (prioritizing well-lit main streets, public transit hubs, or secure hotel perimeters).
4.  **Safety-Heartbeat-Protocol**:
    *   **Action**: Initiating a "Check-In-Request" (e.g., "I see you're near a protest in Plaça de Catalunya. Are you okay? Respond with '1' for Yes, '2' for Help"). If no response is received T+5m, the agent escalates to the **Emergency-Contact** or **Local-Authorities**.

## 3. Data Schema: `Security_Perimeter_Engagement`

```json
{
  "engagement_id": "USZL-77211",
  "traveler_id": "GUID_9911",
  "incident_type": "CIVIL_UNREST",
  "incident_location": { "lat": 41.3871, "lng": 2.1700, "radius_m": 800 },
  "traveler_proximity_m": 450,
  "action_taken": "REROUTE_SUGGESTED",
  "heartbeat_status": "PENDING_RESPONSE",
  "escalation_path": "HOTEL_SECURITY_DESK",
  "status": "ACTIVE_MONITORING"
}
```

## 4. Key Logic Rules

- **Rule 1: The 'False-Alarm' Filter**: To avoid "Alert-Fatigue," the agent MUST verify the incident across at least two independent sources before triggering a "Critical-Alert" (unless it's an official government 'Red-Alert').
- **Rule 2: Transit-Safety-Priority**: If the traveler is using public transit, the agent MUST check for "Station-Closures" or "Service-Suspensions" in the affected area and suggest "Ride-Share" alternatives.
- **Rule 3: Silent-Mode-Respect**: During "Safety-Incidents," the agent switches to "Visual-Priority" (High-contrast maps and short text) to ensure the user can read the guidance even in stressful, noisy environments.

## 5. Success Metrics (Security)

- **Exposure-Reduction**: Average distance maintained between traveler and active security incidents.
- **Heartbeat-Latency**: Time between incident detection and traveler check-in confirmation.
- **Route-Safety-Compliance**: % of times the traveler follows the agent's "Secure-Re-Route" vs the original path.
