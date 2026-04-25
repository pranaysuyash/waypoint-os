# Con Spec: Destination-Medical-Support (CON-REAL-002)

**Status**: Research/Draft
**Area**: Traveler Health & Emergency Response

---

## 1. The Problem: "The Clinical Language Barrier"
A medical emergency in a foreign country is a high-stress scenario. Travelers struggle to find English-speaking (or home-language) doctors, understand local hospital hierarchies, or communicate specific symptoms/medication-needs. Furthermore, coordinating "Direct-Billing" with international health insurance is often a manual, bureaucratic hurdle during a crisis.

## 2. The Solution: 'Clinical-Routing-Protocol' (CRP)

The CRP allows the agent to act as a "Medical-Concierge-Bridge" during a health incident.

### Response Actions:

1.  **Vetted-Facility-Routing**:
    *   **Action**: Identifying the nearest English-speaking (or language-matched) clinic or hospital that accepts the traveler's specific insurance (e.g., Allianz, Cigna, AXA).
2.  **Symptom-Translation-Service**:
    *   **Action**: Providing a "Symptom-Brief" in both the traveler's home language and the destination's local language to ensure clear communication with the treating physician.
3.  **Insurance-Liaison-Automation**:
    *   **Action**: Autonomously "Pinging" the insurance provider's emergency-assistance API to initiate a "Guarantee-of-Payment" (GOP), minimizing out-of-pocket costs for the traveler.
4.  **Medical-Repatriation-Trigger**:
    *   **Action**: If the condition is severe (detected via traveler/doctor status updates), the agent MUST autonomously begin the logistics audit for "Medical-Evacuation" (e.g., chartering an air-ambulance or re-booking into Business class for flat-bed support).

## 3. Data Schema: `Medical_Emergency_Event`

```json
{
  "event_id": "CRP-88221",
  "traveler_id": "GUID_9911",
  "incident_type": "URGENT_ILLNESS",
  "assigned_facility": "BUMRUNGRAD_INTL_HOSPITAL_BANGKOK",
  "facility_language_match": "ENGLISH_FLUENT",
  "insurance_gop_status": "REQUESTED",
  "repatriation_required": false,
  "symptom_brief_local": "อาการปวดท้องรุนแรง...",
  "last_status_update": "2026-11-12T10:00:00Z"
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Direct-Billing' Preference**: The agent MUST prioritize facilities that allow for "Direct-Billing" to insurance over "Pay-and-Claim" clinics.
- **Rule 2: Automated-Family-Notification**: If a medical event is logged, the agent MUST autonomously notify the traveler's emergency contacts (ITIN-001) with a structured status report.
- **Rule 3: Privacy-Preservation**: The agent MUST NOT store raw medical records; it only manages the "Logistics-Metadata" (facility location, insurance status, de-identified symptom types).

## 5. Success Metrics (Health)

- **Medical-Intervention-Latency**: Time from "Request-for-Help" to "Facility-Routing-Confirmed."
- **Direct-Billing-Success-Rate**: % of medical incidents where the traveler had zero out-of-pocket spend.
- **Translation-Accuracy**: Accuracy of the de-identified symptom brief in the destination language.
