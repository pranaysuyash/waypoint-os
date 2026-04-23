# Domain Knowledge: NDC & Modern Retailing

**Category**: Travel Technology  
**Focus**: New Distribution Capability (NDC), dynamic pricing, and rich content.

---

## 1. What is NDC?

New Distribution Capability (NDC) is a travel industry-supported program (launched by IATA) for the development and market adoption of a new, XML-based data transmission standard.

### The Problem it Solves
- **GDS Limitation**: Traditional GDS (Edifact) is limited in its ability to show "Rich Content" (e.g., photos of seats, Wi-Fi details, baggage options).
- **Control**: Airlines wanted to take back control of their pricing and offer "Dynamic Bundles" directly to the agent.

---

## 2. Key NDC Mechanics

### Dynamic Pricing
- **Logic**: Unlike GDS (which has 26 "buckets" of fares), NDC allows airlines to change the price by a single dollar in real-time based on the traveler's profile.
- **SOP**: The agent must explain to the traveler that an NDC quote is often valid for only a few minutes.

### Continuous Pricing
- **Logic**: Moving away from static fare classes (Y, B, M, etc.) to a fluid price curve.

---

## 3. The "GDS Surcharge" Strategy

To push agents toward NDC, many airlines (Lufthansa, Air France-KLM, American Airlines) now add a "GDS Surcharge" (e.g., $15-$30 per ticket) if booked via traditional Edifact GDS.

### Agency Impact
- **Logic**: Agencies must use an "NDC Aggregator" (like Travelfusion or Aaron Group) or a GDS-integrated NDC solution (Amadeus Travel API) to avoid these surcharges.
- **SOP**: Prioritize NDC sources for "Simple" round-trips to save the client money.

---

## 4. Servicing Challenges (The "NDC Gap")

### Post-Booking Friction
- **Logic**: GDS is excellent at "Automatic Reissues" after a flight change. NDC is still maturing — many changes require "Manual Intervention" via the airline's agent portal.
- **SOP**: Document that NDC bookings may have higher "Service Fees" due to the increased manual labor required for disruptions.

---

## 5. Proposed Scenarios
- **The "Invisible Surcharge"**: An agent quotes a GDS fare but the traveler finds a cheaper fare on the airline's website (the NDC fare). The agent must explain the difference or switch to NDC.
- **NDC Re-issue Failure**: A flight is cancelled. The GDS tool cannot "touch" the NDC booking to re-issue it. The agent must call the airline's "Trade Desk."
- **Bundle Confusion**: An NDC fare includes "Free Wi-Fi" and "Preferred Seating," but the traveler's corporate policy only allows "Basic Economy."
