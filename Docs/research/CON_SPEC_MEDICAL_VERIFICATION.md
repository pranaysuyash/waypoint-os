# Concierge Spec: Medical-Infrastructure-Verification (CON-REAL-005)

**Status**: Research/Draft
**Area**: Traveler Safety & Medical Readiness

---

## 1. The Problem: "The Medical Blindspot"
Travelers with chronic conditions (e.g., severe allergies, heart conditions, or limited mobility) often book destinations without understanding the "Medical-Response-Density" of the area. A beautiful boutique hotel in a remote village might be 2 hours away from a hospital capable of treating an anaphylactic shock, creating a hidden "Survival-Risk."

## 2. The Solution: 'Critical-Care-Proximity-Protocol' (CCPP)

The CCPP allows the agent to act as a "Medical-Safety-Officer."

### Verification Actions:

1.  **Trauma-Network-Audit**:
    *   **Action**: Identifying the nearest Level 1/2 Trauma Centers relative to the traveler's hotel and transit routes.
2.  **Specialist-Availability-Mapping**:
    *   **Action**: If the traveler has a "Cardiac-Flag," the agent audits for the presence of a "Cath-Lab" within a 30-minute response window.
3.  **Emergency-Response-Simulation**:
    *   **Action**: Calculating "Drive-Time-Under-Traffic" from the hotel to the nearest ER at different times of day (e.g., rush hour vs midnight).
4.  **Local-Pharmacy-Inventory-Check**:
    *   **Action**: Identifying the nearest 24-hour pharmacy and verifying if they stock common "Emergency-Meds" (e.g., EpiPens, Insulin) in case the traveler's supply is lost.

## 3. Data Schema: `Medical_Safety_Audit`

```json
{
  "audit_id": "CCPP-88221",
  "traveler_id": "GUID_9911",
  "hotel_id": "ST_REGIS_BANGKOK",
  "nearest_er": "BUMRUNGRAD_INTERNATIONAL",
  "distance_km": 1.2,
  "drive_time_peak": "15m",
  "drive_time_off_peak": "5m",
  "specialist_matching": {
    "cardiac_ready": true,
    "pediatric_ready": true
  },
  "pharmacy_24h_nearby": true
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Golden-Hour' Threshold**: If the nearest critical care facility is >60 minutes away, the agent MUST flag this to the traveler as a "Safety-Warning" during the booking process.
- **Rule 2: The 'Language-Bridge' Rule**: The agent autonomously generates an "Emergency-Medical-Summary" in the local language (e.g., Thai) explaining the traveler's condition and blood type, ready to be shown to paramedics.
- **Rule 3: Transit-Safety-Buffer**: The agent ensures that "Airport-to-Hotel" transfers use vehicles with enough space for medical equipment (e.g., oxygen tanks) if flagged in the persona.

## 5. Success Metrics (Safety)

- **Safety-Warning-Accuracy**: % of medical risks correctly identified before booking.
- **Response-Time-Precision**: Difference between predicted and actual emergency transit time (audited via simulation).
- **Traveler-Peace-of-Mind**: Qualitative feedback from high-risk travelers on the CCPP's impact on their travel confidence.
