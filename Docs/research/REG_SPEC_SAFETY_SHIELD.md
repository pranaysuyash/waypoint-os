# Reg Spec: Agentic 'Safety-Shield' Watchdog (REG_REAL-018)

**Status**: Research/Draft
**Area**: Traveler Physical Safety & Security Intelligence

---

## 1. The Problem: "The Security Blind-Spot"
Standard travel insurance and government advisories are too "Macro" (e.g., "Level 2: Exercise Caution in Brazil"). They fail to capture "Hyper-Local-Safety" risks: a recent spike in pickpocketing in a specific square, a known "Taxi-Scam" at a specific terminal, or a sudden "Civil-Disturbance" two blocks away from the traveler's hotel. Travelers are often unaware of these risks until they become victims.

## 2. The Solution: 'Hyper-Local-Security-Protocol' (HLSP)

The HLSP acts as the "Digital-Bodyguard."

### Security Actions:

1.  **Hyper-Local-Crime-Feed**:
    *   **Action**: Integrating real-time local police reports, news alerts, and crowdsourced "Safety-Incident-Feeds" (e.g., "Active pickpocketing alert in Plaka, Athens; suggest keeping valuables in hotel safe").
2.  **Scam-Detection-Watchdog**:
    *   **Action**: Maintaining a database of known "Tourist-Scams" per destination. If a traveler is near a known "Scam-Hotspot," the agent sends a "Tactical-Briefing" (e.g., "You are entering the 'Bracelet-Scam' zone; avoid eye contact with street vendors here").
3.  **Proximity-Civil-Alerting**:
    *   **Action**: Monitoring for protests, strikes, or civil unrest within a 5km radius of the traveler's GPS location. The agent autonomously calculates an "Escape-Route" or "Shelter-in-Place" recommendation.
4.  **Verified-Safe-Zone-Mapping**:
    *   **Action**: Providing the agency owner with a "Safe-Zone-Overlay" for their bookings, ensuring they don't book travelers into high-crime neighborhoods unintentionally.

## 3. Data Schema: `Security_Incident_Alert`

```json
{
  "alert_id": "HLSP-22119",
  "traveler_id": "TRAVELER_Z",
  "incident_type": "PROXIMITY_PROTEST",
  "threat_level": "MODERATE",
  "location_gps": {"lat": 48.8566, "lng": 2.3522},
  "incident_radius_km": 1.5,
  "recommended_action": "RE-ROUTE_VIA_METRO_LINE_1_AVOID_STREET_X",
  "status": "ALERT_SENT_TO_TRAVELER"
}
```

## 4. Key Logic Rules

- **Rule 1: The 'No-Panic' Delivery**: Security alerts MUST be phrased as "Helpful-Guidance," not "Fear-Inducing-Panic." The goal is situational awareness, not terror.
- **Rule 2: Trusted-Source-Validation**: The agent MUST verify safety reports against multiple sources before triggering a "High-Confidence-Alert."
- **Rule 3: Autonomous-Safety-Pivot**: If a "Critical-Threat" is detected (e.g., a natural disaster or major riot), the agent has the authority to autonomously initiate a "Hotel-Relocation-Request" and notify the agency owner immediately.

## 5. Success Metrics (Safety)

- **Security-Incident-Avoidance**: Reduction in travelers reporting thefts, scams, or physical safety incidents.
- **Traveler-Confidence-Score**: Feedback on how "Safe" the traveler felt knowing the agency was monitoring hyper-local security.
- **Alert-Accuracy-Rate**: % of security alerts that were found to be timely and relevant by the traveler.
- **Agency-Trust-Multiplier**: Increase in repeat bookings driven by the "Peace-of-Mind" provided by the Safety-Shield.
