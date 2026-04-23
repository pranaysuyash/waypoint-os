# Targeted Scenario Expansion - Batch 01

This batch of scenarios specifically targets "Low Coverage" buckets identified in the [COVERAGE_GAP_ANALYSIS.md](COVERAGE_GAP_ANALYSIS.md).

---

## 1. Phase 2: Fulfillment & Booking (Low Coverage)

### [BOOK-001] Payment Failure Mid-Transaction (S2)
- **Persona**: S2 (Family Coordinator)
- **Scenario**: The agent is booking a group of 12 people for a villas stay. The deposit payment of $5,000 fails due to a bank limit.
- **Input (WhatsApp)**: "Hey, the payment link you sent isn't working. It says 'Limit Exceeded'. Can we split this into 3 payments? We need to lock this villa in the next hour or we lose it."
- **N01 Fact**: { "amount": 5000, "reason": "limit_exceeded", "urgency": "high" }
- **N02 Decision**: Proceed. Generate 3 split payment links and confirm with the villa owner that the deposit is coming in parts.
- **Failure Mode**: Stage Blindness. System tries to re-quote instead of facilitating the booking fix.

### [BOOK-002] Passport Expiry Detection (P3)
- **Persona**: P3 (Junior Agent)
- **Scenario**: A traveler sends their passport copy for a flight to Bali next week. The passport expires in 5 months.
- **Input (Image Data)**: [Passport Copy attached]
- **N01 Fact**: { "document_type": "passport", "expiry": "2026-09-15", "travel_date": "2026-04-30" }
- **N02 Decision**: Stop. Flag "Indonesian entry requires 6 months validity". Alert Junior Agent to notify traveler immediately.
- **Failure Mode**: False Positive. System ignores the expiry and proceeds with booking.

---

## 2. Phase 4: Post-Trip & Loyalty (Low Coverage)

### [POST-001] GST/Tax Reconciliation Dispute (P2)
- **Persona**: P2 (Agency Owner)
- **Scenario**: A corporate client (P3) returns from a trip and claims the GST invoice has the wrong company address, preventing them from claiming input tax credit.
- **Input (Email)**: "The GST invoice for the London trip has our old address. We can't file this. Please issue a corrected one by EOD."
- **N01 Fact**: { "document": "invoice", "error": "wrong_address", "client_type": "corporate" }
- **N02 Decision**: Proceed. Validate the new address against company records. Issue credit note for old invoice and generate new GST invoice.
- **Failure Mode**: Contradiction Blind. System thinks the address in the CRM is "Ground Truth" and refuses to update.

### [POST-002] "Welcome Back" Loyalty Nurture (S1)
- **Persona**: S1 (Individual Traveler)
- **Scenario**: Traveler returns from a 10-day Japan trip.
- **Input (Trigger)**: { "trip_end_date": "Yesterday" }
- **N01 Fact**: { "trip_id": "JP-102", "status": "completed", "satisfaction_signal": "high (based on in-trip chat)" }
- **N02 Decision**: Proceed. Draft a personalized welcome back message. Ask for feedback. Offer a 5% "Loyalty Discount" for their next booking if they share a review on Google/Socials.
- **Failure Mode**: Stage Blindness. System sends a generic "Rate us" email without trip context.

---

## 3. Specialized Verticals (Zero Coverage)

### [VERT-001] Seaman Fare Baggage Dispute (P3)
- **Persona**: P3 (Junior Agent)
- **Scenario**: A ship crew member is at the airport. The airline agent says they only have 20kg allowance, but the agent booked a "Seaman Fare" which should have 40kg.
- **Input (Urgent Call/Chat)**: "I'm at the check-in counter. They are charging me for extra bags. I have my Seaman's Book! Help!"
- **N01 Fact**: { "fare_type": "seaman", "allowance_expected": 40, "allowance_denied": 20, "urgency": "critical" }
- **N02 Decision**: Stop. Fetch the specific GDS baggage rule for that ticket. Send the PDF of the "Fare Rules" to the traveler and the Agency's Airline Helpdesk.
- **Failure Mode**: Authority Inversion. System trusts the airline agent's verbal claim over the ticket's fare rules.

### [VERT-002] Vessel Diversion - Port Change (P1)
- **Persona**: P1 (Solo Agent)
- **Scenario**: A ship was supposed to dock in Singapore, but is diverted to Port Klang due to port congestion. 5 crew members are mid-air to Singapore.
- **Input (Supplier Alert)**: "Vessel 'Star Voyager' diverted. New ETA Port Klang: 2026-04-25."
- **N01 Fact**: { "vessel": "Star Voyager", "new_port": "Port Klang", "crew_count": 5, "status": "in-transit" }
- **N02 Decision**: Proceed. Book ground transfer from Singapore Changi to Port Klang (approx 5 hours drive). Notify crew via WhatsApp. Alert local DMC to assist with immigration clearance at the land border.
- **Failure Mode**: False Negative. System asks the agent "What should I do?" instead of proposing the standard maritime rerouting logic.
