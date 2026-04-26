# Int Spec: Agentic Baggage-Telemetry-Standard (INT-REAL-003)

**Status**: Research/Draft
**Area**: Logistics Interoperability & Data Normalization

---

## 1. The Problem: "The Visibility Gap"
Airlines provide baggage tracking via "Scan-Events" (e.g., "Bag scanned into aircraft"). However, if a bag is left on the tarmac or misrouted, the airline's data often goes "Dark" for hours or days. Travelers using personal trackers (AirTags, Tile) have "Hyper-Accurate" location data, but this data is siloed in their personal apps and cannot be easily communicated to the airline's ground-handling staff or the travel agent's recovery engine.

## 2. The Solution: 'IoT-Logistics-Normalization-Protocol' (ILNP)

The ILNP allows the agent to act as a "Logistics-Integrator."

### Integration Actions:

1.  **Consumer-Tracker Data-Normalization**:
    *   **Action**: Ingesting the "Raw-Coordinates" and "Timestamp" from the traveler's personal tracker (via authorized API or traveler-input) and normalizing it into the agency's **Logistics-Schema** (OPS-018).
2.  **Telemetry-Discrepancy-Detection**:
    *   **Action**: Autonomously comparing the airline's "Logistics-Status" (e.g., "Bag in Transit") with the IoT "Physical-Location" (e.g., "Bag at Terminal 2, Gate B12").
3.  **The 'Misroute-Alert' Trigger**:
    *   **Action**: If the IoT location is >500 meters from the airline's expected location (or the traveler's current aircraft), the agent triggers an "Immediate-Misroute-Alert" and autonomously identifies the **Ground-Handling-Contractor** at that specific terminal.
4.  **Proof-of-Position Generation**:
    *   **Action**: Generating a "Verified-Position-Report" (including timestamped coordinates and a map-snippet) that the traveler can provide to the airline's "Lost-and-Found" desk to expedite recovery.

## 3. Data Schema: `Normalized_Baggage_Telemetry`

```json
{
  "tracking_id": "ILNP-77221",
  "traveler_id": "GUID_9911",
  "iot_source": "APPLE_AIRTAG",
  "iot_last_seen_coords": [51.4700, -0.4543],
  "airline_status": "SCANNED_AT_CHECK_IN",
  "discrepancy_detected": true,
  "physical_state": "MISROUTED_STATIC",
  "status": "RECOVERY_ALERT_TRIGGERED"
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Source-Hierarchy'**: In cases of discrepancy, the **IoT-Physical-Location** MUST be treated as the "Ground-Truth" for location, while the **Airline-Status** is treated as the "Administrative-Truth."
- **Rule 2: Privacy-Firewall**: The agent MUST ONLY access IoT telemetry during the active trip window (T-2h before departure to T+2h after final arrival) and must delete all coordinate history post-trip.
- **Rule 3: Recovery-Escalation**: If a bag remains "Static" in an IoT location for >4h after the traveler's arrival, the agent MUST autonomously initiate the **FIN-REAL-006 (Baggage-Claims)** workflow.

## 5. Success Metrics (Integration)

- **Misroute-Detection-Latency**: Time from actual bag misroute to agentic alert (target: <15 mins).
- **Recovery-Velocity-Improvement**: Reduction in "Time-to-Return" for misrouted bags when IoT data is used.
- **Data-Normalization-Accuracy**: % of IoT raw-coordinates correctly mapped to specific airport gate/terminal zones.
