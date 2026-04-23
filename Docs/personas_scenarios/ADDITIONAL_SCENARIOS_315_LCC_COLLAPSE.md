# Additional Scenario 315: The Low-Cost Carrier Collapse

**Scenario**: A low-cost carrier (LCC) used in several active bookings suddenly declares bankruptcy and ceases operations. The system must identify all affected travelers and initiate re-protection flows.

---

## Situation

- Carrier "BlueSky Air" (LCC) has grounded all flights effective immediately.
- 12 active travelers are mid-trip; 45 have future bookings within the next 30 days.
- The agency owner (P2) is notified by a system alert and needs an immediate impact report and recovery plan.

## What the system should do

- Cross-reference the "Insolvency Alert" with all active PNRs in the database.
- Segment travelers by "Urgency" (Mid-trip > Departing < 24h > Future).
- For mid-trip travelers: Identify alternative flights on legacy carriers and check "Chargeback Protection" eligibility.
- For future bookings: Trigger "Price-Drop Re-shopping" logic on alternative carriers to minimize loss.
- Draft proactive notifications for travelers, explaining the situation and the recovery steps being taken.

## Why this matters

Supplier failure is the ultimate "Agency Stress Test." 
Autonomous recovery prevents human panic, protects traveler trust, and minimizes financial liability for the agency.

## Success criteria

- All affected travelers are identified within < 60 seconds of the alert.
- A prioritized recovery plan is presented to the Agency Owner.
- Mid-trip travelers receive an "Emergency Update" with at least one viable alternative.
