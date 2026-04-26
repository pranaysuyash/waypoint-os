# Con Spec: Hyper-Local Social-Norm-Guardian (CON-REAL-012)

**Status**: Research/Draft
**Area**: Cultural Intelligence & Interaction Safety

---

## 1. The Problem: "The Cultural Faux-Pas"
Travelers often unintentionally violate local social norms, particularly in conservative, religious, or high-friction cultures. These violations (e.g., improper dress in a temple, inappropriate public displays of affection, or offensive hand gestures) can lead to social ostracization, heavy fines, or even physical danger. Generic travel guides are often too broad to provide the "Block-by-Block" etiquette needed for specific districts.

## 2. The Solution: 'Interaction-Safety-Protocol' (ISP)

The ISP allows the agent to act as a "Cultural-Compass."

### Interaction Actions:

1.  **District-Level Etiquette-Mapping**:
    *   **Action**: Mapping the traveler's GPS to specific "Cultural-Zones" (e.g., "Entering a religious district," "Entering a traditional rural village," "Entering a conservative residential area").
2.  **Real-Time 'Dress-Code' Alerts**:
    *   **Action**: If the traveler is entering a zone with strict dress codes (e.g., shoulders and knees must be covered), the agent triggers a "Proactive-Alert" before they exit their vehicle or hotel.
3.  **Behavioral-Norm-Guidance**:
    *   **Action**: Providing "Just-in-Time" guidance on local behaviors (e.g., "In this region, use only your right hand for greeting," "Tipping is considered an insult here," "Avoid eye contact with specific local officials").
4.  **Language-Nuance-Filter**:
    *   **Action**: Alerting the traveler to "High-Risk" phrases or topics of conversation (e.g., "Avoid discussing the royal family in this country," "Certain words have offensive double-meanings in this dialect").

## 3. Data Schema: `Social_Norm_Alert_Event`

```json
{
  "event_id": "ISP-77221",
  "traveler_id": "GUID_9911",
  "current_zone": "CONSERVATIVE_DISTRICT_DUBAI",
  "norm_category": "DRESS_CODE",
  "severity_level": "HIGH",
  "guidance_text": "Please ensure shoulders and knees are covered before entering this district to avoid fines or refusal of entry.",
  "local_law_reference": "ARTICLE_22_PUBLIC_DECENCY",
  "status": "ALERT_DELIVERED"
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Safety-First' Hierarchy**: Cultural alerts related to "Legal-Violation" or "Physical-Safety" MUST be prioritized over generic etiquette tips.
- **Rule 2: Contextual-GPS-Lead-Time**: Alerts for dress codes or behavioral norms MUST be delivered at least 500 meters *before* the traveler enters the specific cultural zone.
- **Rule 3: Respectful-Tone-Constraint**: All guidance MUST be delivered in a "Neutral, Informative" tone that avoids judging the local culture, focusing entirely on the traveler's safety and successful integration.

## 5. Success Metrics (Cultural)

- **Faux-Pas-Incident-Rate**: Target: 0.00% reported cultural or legal incidents.
- **Cultural-Zone-Lead-Time**: Average notice provided before a traveler enters a high-friction zone.
- **Traveler-Interaction-Confidence**: Self-reported comfort levels in high-friction cultural environments.
