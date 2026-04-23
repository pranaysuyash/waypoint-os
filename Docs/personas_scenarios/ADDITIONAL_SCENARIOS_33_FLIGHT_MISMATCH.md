# Additional Scenario 33: Flight Mismatch

**Scenario**: A traveler’s outgoing flight and hotel dates do not align, and the system must detect and fix the mismatch before confirmation.

---

## Situation

A booking request includes a flight arriving late on the first day while hotel check-in is the same afternoon.
The customer expects the agency to know the details and resolve the conflict.

## What the system should do

- Cross-check travel dates across flight, hotel, and transfer bookings
- Flag any misalignment automatically
- Recommend either a later hotel check-in or an earlier flight
- Explain the issue clearly to the customer

## Why this matters

Date mismatches are an easy source of itinerary failure.
Catching them before confirmation prevents customer pain and service recovery costs.

## Success criteria

- The system detects the mismatch before finalizing the itinerary
- It offers a specific correction with minimal customer friction
- The customer trusts the agency’s attention to detail
