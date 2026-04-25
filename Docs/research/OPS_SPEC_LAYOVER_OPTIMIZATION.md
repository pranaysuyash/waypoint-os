# Ops Spec: Autonomous Layover-Optimization (OPS-REAL-012)

**Status**: Research/Draft
**Area**: Itinerary Design & Traveler Comfort

---

## 1. The Problem: "The Airport Purgatory"
Long layovers (6-12 hours) are often spent in "Airport Purgatory"—expensive lounges or uncomfortable terminal seats. Travelers rarely leave the airport because of the logistical complexity: "Do I need a visa?", "Where can I store my bags?", "Will I make it back in time for my flight?". They miss the opportunity for a "Mini-Vacation" in a world-class city.

## 2. The Solution: 'Mini-Vacation-Protocol' (MVP)

The MVP allows the agent to act as a "Layover-Logistics-Manager."

### Optimization Actions:

1.  **Layover-Threshold-Detection**:
    *   **Action**: For every itinerary, the agent identifies layovers > 6 hours and autonomously audits the "City-Access-Viability" (distance to city center, transit-visa requirements).
2.  **Day-Room-Sourcing**:
    *   **Action**: Autonomously sourcing a "Day-Room" (e.g., via HotelsByDay or airport-hotels) to provide the traveler with a shower, nap, and secure base for their belongings.
3.  **Express-Urban-Routing**:
    *   **Action**: Designing a "Time-Boxed" city tour (e.g., "The 3-Hour Singapore Express") that fits perfectly within the departure window, including pre-booked high-speed transit.
4.  **T-Minus-Departure-Watchdog**:
    *   **Action**: Continuously monitoring local traffic and airport security wait-times. If the "Security-Threshold" is breached, the agent autonomously pings the traveler to return to the airport immediately.

## 3. Data Schema: `Layover_Optimization_Event`

```json
{
  "event_id": "MVP-88221",
  "airport_code": "SIN",
  "layover_duration_mins": 480,
  "city_access_status": "VETTED_HIGH_VIABILITY",
  "day_room_id": "CROWNE_PLAZA_SIN_DAY_ROOM",
  "urban_activity": "GARDENS_BY_THE_BAY_EXPRESS",
  "transit_mode": "MRT_FAST_TRACK",
  "must_return_by_utc": "2026-11-12T18:00:00Z",
  "security_buffer_mins": 90
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Golden-Window' Rule**: The agent MUST NOT suggest leaving the airport if the net "In-City-Time" (after immigration and transit) is less than 3 hours.
- **Rule 2: Transit-Visa-Automation**: The agent MUST autonomously check and (if possible) apply for a "Transit-Visa-on-Arrival" or "Layover-Visa" before the traveler lands.
- **Rule 3: Luggage-Storage-Optimization**: If a day-room is not used, the agent MUST autonomously identify the nearest "Left-Luggage" facility and provide the traveler with a digital storage voucher.

## 5. Success Metrics (Experience)

- **Layover-Utility-Yield**: % of long layovers converted into successful city experiences.
- **On-Time-Departure-Rate**: 100% (The traveler MUST never miss their connection due to a city excursion).
- **Traveler-Recovery-Score**: Post-layover energy levels (nap/shower) vs. traditional terminal stays.
