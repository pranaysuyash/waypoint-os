# Ops Spec: Agentic In-Flight-Amenity-Watchdog (OPS-REAL-018)

**Status**: Research/Draft
**Area**: Passenger Experience & Comfort Integrity

---

## 1. The Problem: "The Bait and Switch"
Travelers booking premium cabins (Business/First) often choose specific flights based on the "Aircraft-Type" or "Cabin-Product" (e.g., the "QSuite" on Qatar or the "New-Club-World" on British Airways). However, airlines frequently perform "Last-Minute-Aircraft-Swaps" due to mechanical issues or fleet management. A traveler who paid for a lie-flat bed may find themselves in an older-generation "Angled-Flat" seat, with no proactive communication from the airline.

## 2. The Solution: 'Comfort-Integrity-Protocol' (CIP)

The CIP allows the agent to act as a "Cabin-Auditor."

### Comfort Actions:

1.  **Aircraft-Registration-Monitoring**:
    *   **Action**: Monitoring the specific "Tail-Number" assigned to the traveler's flight. Cross-referencing the registration with a "Cabin-Configuration-Database" (e.g., AeroLOPA, SeatGuru) to identify the specific seat product.
2.  **Downgrade-Detection-Trigger**:
    *   **Action**: If the aircraft is swapped to a configuration with "Lower-Tier" amenities (e.g., "Angled-Flat" vs. "Full-Flat," "No-Door" vs. "Suite"), the agent triggers an "Immediate-Comfort-Alert."
3.  **The 'Proactive-Re-Route' Pivot**:
    *   **Action**: If the downgrade is detected >12h before departure, the agent autonomously identifies alternative flights (on the same or partner airlines) that still offer the original "Flagship-Product."
4.  **Automated Partial-Refund-Claim**:
    *   **Action**: If the traveler proceeds with the downgraded flight, the agent autonomously files a "Service-Failure-Claim" citing the "Differential-in-Value" between the booked product and the delivered product.

## 3. Data Schema: `Amenity_Integrity_Event`

```json
{
  "event_id": "CIP-77221",
  "traveler_id": "GUID_9911",
  "flight_id": "QR-10",
  "original_aircraft_config": "QSUITE_FULL_FLAT",
  "new_aircraft_config": "OLD_REGIONAL_ANGLED_FLAT",
  "integrity_failure_detected": true,
  "compensation_eligibility_usd": 450.00,
  "pivot_options_found": 2,
  "status": "COMPENSATION_CLAIM_PENDING"
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Amenity-Hierarchy'**: A "Downgrade" is defined as any swap that moves the traveler from a "Superior" to an "Inferior" cabin class *or* specific seat-product (e.g., "Full-Aisle-Access" to "2-2-2 configuration").
- **Rule 2: The 'Silent-Swap' Defense**: The agent MUST NOT rely on airline notifications. It MUST pull real-time tail-number data from independent tracking sources (e.g., FlightRadar24) to detect swaps the airline has not yet disclosed.
- **Rule 3: Compensation-Arbitrage**: The agent MUST calculate the "Differential-in-Market-Price" between the two products to provide a specific, defensible dollar amount in the compensation claim.

## 5. Success Metrics (Comfort)

- **Downgrade-Capture-Rate**: % of aircraft swaps detected by the agent before the traveler arrives at the gate.
- **Comfort-Recovery-Rate**: % of travelers successfully re-routed to their original product standard.
- **Compensation-Yield**: USD recovered for travelers who experienced a "Product-Downgrade."
