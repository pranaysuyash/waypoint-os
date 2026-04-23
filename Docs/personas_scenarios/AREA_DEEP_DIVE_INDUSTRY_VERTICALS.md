# Area Deep Dive: Industry Verticals (Maritime, Energy, Healthcare)

**Domain**: B2B Specialized Verticals  
**Focus**: Niche operational requirements and high-stakes logistics.

---

## 1. Maritime & Offshore Travel

This vertical moves crew members to ships, rigs, and offshore platforms.

### Key Requirements
- **Seaman Fares**: Specialized airfares that allow high baggage allowance (40kg+) and 100% refundability.
- **Vessel Tracking**: Integration with "Vessel Tracking" APIs to ensure the crew arrives at the right port at the right time.
- **Letters of Guarantee (LoG)**: Mandatory documents issued by ship owners to facilitate crew entry.

### System Challenges
- **Last-Minute Rerouting**: If a ship is delayed by weather, the entire crew's travel must be rerouted to a different port.
- **24/7 Urgency**: Ships operate 24/7; travel failures can cost $50k+ per day in port fees.

---

## 2. Energy & Resource Logistics

Moving engineers and specialists to remote sites (mines, solar farms, oil fields).

### Key Requirements
- **Remote Site Management**: Booking "Camp" accommodation, not just hotels.
- **Rotational Travel**: Managing fixed 2-week-on / 2-week-off schedules for hundreds of employees.
- **Safety Charter Flights**: Coordinating private or chartered flights to non-commercial airstrips.

### System Challenges
- **Complex Approval Chains**: Site Managers must approve travel based on "Operational Priority" vs "Budget".
- **Manifest Management**: Ensuring the flight manifest matches the safety training records (HUET/BOSIET).

---

## 3. Healthcare & Medical Concierge

High-empathy, high-accuracy travel for patients and medical staff.

### Key Requirements
- **Accessibility Logic**: Ensuring 100% wheelchair / stretcher compatibility across the entire chain (Car -> Flight -> Hotel).
- **Oxygen & Medical Equipment**: Coordinating airline approvals for portable oxygen concentrators (POC).
- **Confidentiality**: Extreme PII protection (HIPAA-level sensitivity).

### System Challenges
- **The "Fit to Fly" Gate**: Travelers often need a doctor's certificate signed within 48 hours of departure.
- **Companion Logic**: Patient travel almost always involves a medical or family companion whose travel must be perfectly synced.

---

## 4. Proposed Scenarios for this Domain

| Scenario ID | Title | Persona | Vertical |
|-------------|-------|---------|----------|
| VERT-001 | Seaman Fare Baggage Dispute | P3 | Maritime |
| VERT-002 | Vessel Diversion - Port Change | P1 | Maritime |
| VERT-003 | Rotational Travel Manifest Conflict | P2 | Energy |
| VERT-004 | Remote Site Camp Overbooking | S1 | Energy |
| VERT-005 | Stretcher Support Failure at Gate | S1 | Healthcare |
| VERT-006 | Medical Companion Visa Rejection | S2 | Healthcare |
