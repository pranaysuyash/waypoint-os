# Ops Spec: Accessibility Preference-Sync (OPS-A11Y-001)

**Status**: Research/Draft
**Area**: Inclusive Design & Vendor Coordination

---

## 1. The Problem: "The Accessibility Gap"
Travelers with disabilities often have to "Explain-Themselves" at every step of the journey: to the airline for a wheelchair, to the airport for terminal assistance, and to the hotel for an ADA-compliant room. If one link in the chain fails (e.g., the airline forgets to notify the airport), the traveler's journey is compromised.

## 2. The Solution: 'Accessibility-Manifest-Protocol' (AMP)

The AMP allows the agent to act as a "Continuous-Advocate" by syncing a structured manifest across all vendors in the itinerary.

### Coordination Actions:

1.  **A11y-Need-Profiling**:
    *   **Action**: Capturing specific, technical needs (e.g., "Wheelchair dimensions: 60x100cm, Battery type: Dry-cell," "Service animal registration: ID-8822").
2.  **Cross-Vendor-Manifest-Push**:
    *   **Action**: Autonomously "Injecting" the accessibility requirements into the OSI (Other Service Information) fields of the GDS (GDS-001) and the "Special-Requests" fields of hotel/car APIs.
3.  **Last-Mile-Verification**:
    *   **Action**: 24 hours before the trip, the agent "Pings" each vendor's support-agent (or bot) to "Confirm-Receipt" of the accessibility manifest.

## 3. Data Schema: `Accessibility_Manifest`

```json
{
  "manifest_id": "AMP-88221",
  "traveler_id": "GUID_9911",
  "mobility": {
    "wheelchair_support": "REQUIRED",
    "stowage_type": "IN_CABIN_IF_POSSIBLE",
    "battery_spec": "LITHIUM_ION_SPILL_PROOF"
  },
  "sensory": {
    "visual_assistance": "REQUIRED_AT_TERMINAL",
    "quiet_room_preference": true
  },
  "medical": {
    "cpap_power_outlet": "REQUIRED_NEAR_BED",
    "refrigerated_medication_storage": true
  }
}
```

## 4. Key Logic Rules

- **Rule 1: Proactive-A11y-Audit**: If a traveler has a mobility-need, the agent MUST NOT book a hotel that is "Not-ADA-Verified" or has "Limited-Elevator-Access" without an explicit warning.
- **Rule 2: Transfer-Wait-Time-Scaling**: The agent must autonomously "Double" the connection-buffer (OPS-VINT-001) for travelers requiring airport assistance to account for boarding/deplaning delays.
- **Rule 3: Compensation-on-Failure**: If a vendor fails to provide the requested assistance, the agent MUST autonomously file a "Service-Failure-Claim" (REG-REAL-001).

## 5. Success Metrics (Inclusion)

- **A11y-Fulfillment-Rate**: % of requested assistance successfully provided by vendors.
- **Traveler-Stress-Score**: Reduction in reported stress for A11y travelers vs baseline.
- **Support-Escalation-Rate**: % of A11y trips requiring manual intervention by a human agent.
