# Reg Spec: Agentic Shared-Economy-Safety-Audit (REG-REAL-014)

**Status**: Research/Draft
**Area**: Shared Economy Safety & Regulatory Compliance

---

## 1. The Problem: "The Safety Disparity"
Traditional hotels and car rental agencies are subject to strict fire, safety, and operational regulations. Shared economy platforms (Airbnb, Vrbo, Turo) have varying degrees of self-regulation. Travelers often find themselves in properties without smoke detectors, carbon monoxide alarms, or secure locks, or in vehicles with undisclosed maintenance issues. The traveler has no "Third-Party-Auditor" to verify safety claims before arrival.

## 2. The Solution: 'Shared-Safety-Compliance-Protocol' (SSCP)

The SSCP allows the agent to act as a "Virtual-Safety-Inspector."

### Safety Actions:

1.  **Safety-Feature Extraction**:
    *   **Action**: Analyzing property/vehicle listings and reviews using NLP to identify the presence (or conspicuous absence) of "Critical-Safety-Features" (e.g., "Smoke Alarm," "First Aid Kit," "Tire-Tread-Mentions").
2.  **Host-Response-Latency Audit**:
    *   **Action**: Analyzing the host's "Communication-History." If a host takes >4h to respond to safety-related queries, the agent flags the property as "High-Response-Risk."
3.  **Proactive 'Safety-Verification' Script**:
    *   **Action**: Providing the traveler with a specific "Message-Template" to send to the host before booking (e.g., "Can you provide a photo of the fire extinguisher location?").
4.  **Local-Ordinance Cross-Reference**:
    *   **Action**: Checking the property against "Short-Term-Rental-Registries" (where available) to ensure the listing is legally compliant and not a "Ghost-Hotel."

## 3. Data Schema: `Shared_Economy_Safety_Scorecard`

```json
{
  "audit_id": "SSCP-88221",
  "traveler_id": "GUID_9911",
  "listing_platform": "AIRBNB",
  "listing_id": "ABNB_112233",
  "safety_score": 0.68,
  "missing_critical_features": ["CARBON_MONOXIDE_ALARM", "FIRE_EXTINGUISHER"],
  "legal_registration_verified": false,
  "risk_status": "MODERATE_CAUTION_ADVISED",
  "status": "AUDIT_COMPLETE"
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Critical-Life-Safety' Threshold**: If a property lacks a "Smoke Detector" or "Carbon Monoxide Alarm" (in gas-heated regions), the agent MUST trigger a "Strong-Warning" and suggest alternative "Safety-Certified" hotels.
- **Rule 2: Review-Anomaly-Detection**: The agent MUST prioritize safety mentions in "Recent-Negative-Reviews" over the host's "Amenity-Checklist."
- **Rule 3: Turo-Specific Maintenance-Audit**: For vehicle rentals, the agent MUST flag any reviews mentioning "Brake-Squeal," "Tire-Condition," or "Warning-Lights" as "Safety-Blocking" issues.

## 5. Success Metrics (Safety)

- **Safety-Incident-Rate**: % of shared-economy bookings with reported safety failures post-stay.
- **Host-Compliance-Velocity**: Time taken for a host to provide safety verification via the agent's script.
- **Audit-Accuracy**: Correlation between the agent's "Safety-Score" and the traveler's physical inspection upon arrival.
