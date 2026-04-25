# Ops Spec: Autonomous In-Flight-Service-Audit (OPS-REAL-017)

**Status**: Research/Draft
**Area**: Passenger Rights & Quality Assurance

---

## 1. The Problem: "The Bait and Switch"
Airlines often market a specific "Premium-Product" (e.g., the new United Polaris pod or JetBlue Mint Suite) but swap aircraft at the last minute for an older model with inferior seats, broken Wi-Fi, or no power outlets. Passengers rarely realize they are entitled to compensation for this "Downgrade-of-Service" unless the seat class itself changes.

## 2. The Solution: 'Amenity-Verification-Protocol' (AVP)

The AVP allows the agent to act as a "Passenger-Rights-Auditor."

### Auditing Actions:

1.  **Baseline-Amenity-Mapping**:
    *   **Action**: At the time of booking, the agent captures the "Service-Snapshot" (e.g., "Lie-Flat-Seat," "Direct-Aisle-Access," "High-Speed-Wi-Fi") from the NDC/GDS marketing data.
2.  **Tail-Number-Tracking**:
    *   **Action**: T-24h before flight, the agent identifies the specific aircraft tail-number assigned to the route.
3.  **Real-Time-Capability-Check**:
    *   **Action**: Cross-referencing the tail-number with technical databases (e.g., AeroLOPA, FlightRadar24) to verify the *actual* cabin configuration and Wi-Fi hardware.
4.  **Autonomous-Claim-Initiation**:
    *   **Action**: If a "Feature-Mismatch" is detected (e.g., promised pods but delivered old recliners), the agent autonomously drafts a "Service-Failure-Claim" and notifies the traveler: "Your flight was swapped to an older aircraft. I am filing for a 15,000-mile compensation on your behalf."

## 3. Data Schema: `Amenity_Audit_Result`

```json
{
  "audit_id": "AVP-99221",
  "traveler_id": "GUID_9911",
  "pnr": "XY77ZA",
  "promised_amenity": "LIE_FLAT_POD",
  "delivered_amenity": "ANGLE_FLAT_SEAT",
  "discrepancy_detected": true,
  "tail_number": "N123UA",
  "claim_status": "DRAFTED_PENDING_LANDING",
  "estimated_compensation": "15000_MILES"
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Significant-Delta' Rule**: The agent only flags discrepancies that significantly impact the "Passenger-Experience" (e.g., seat type, Wi-Fi, power) to avoid noise.
- **Rule 2: The 'Pre-Boarding-Warning'**: If a major swap occurs, the agent notifies the user *before* they board, allowing them to potentially switch to a different flight with the original product.
- **Rule 3: Evidence-Capture**: The agent autonomously archives the "Marketing-Offer" screenshot/JSON as evidence for the airline's customer relations department.

## 5. Success Metrics (Audit)

- **Downgrade-Detection-Precision**: % of aircraft swaps correctly identified by the agent.
- **Compensation-Recovery-Value**: Total USD/Miles recovered for travelers due to service failures.
- **User-Awareness-Lift**: % of travelers who were unaware of a service downgrade until the agent notified them.
