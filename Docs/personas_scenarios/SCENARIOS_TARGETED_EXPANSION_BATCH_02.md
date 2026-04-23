# Targeted Scenario Expansion - Batch 02 (Luxury & MICE)

This batch targets "Zero Coverage" buckets in Luxury Concierge and MICE/Event logistics.

---

## 1. Luxury & Concierge Services

### [LUX-001] Private Jet AOG (Aircraft on Ground) Recovery (P1)
- **Persona**: P1 (Solo Agent)
- **Scenario**: A high-profile traveler (S1) is at a private terminal (FBO) in Nice. Their chartered jet has a mechanical failure (AOG). They have a speaking engagement in London in 3 hours.
- **Input (WhatsApp from Assistant)**: "The pilot just said there's a technical issue. We're stuck in Nice. Mr. X needs to be in London by 2 PM for the keynote. Find a solution NOW."
- **N01 Fact**: { "location": "Nice FBO", "dest": "London", "deadline": "14:00", "status": "AOG" }
- **N02 Decision**: Proceed. Call the charter broker for an immediate "Sub-Charter" (backup aircraft). Check commercial first-class options as a plan B. Coordinate a "Ramp Transfer" to the new aircraft.
- **Failure Mode**: Stage Blindness. System tries to "troubleshoot" the mechanical issue instead of rerouting.

### [LUX-002] Dual-Route Briefing - Assistant vs Traveler (P3)
- **Persona**: P3 (Junior Agent)
- **Scenario**: Confirming a $40k Maldives villa booking.
- **Input (System Trigger)**: Booking Confirmed.
- **N01 Fact**: { "traveler": "VIP_X", "assistant": "EA_Y", "amount": 40000, "villa": "Soneva Fushi" }
- **N02 Decision**: Proceed. Draft two distinct messages. 
    1. **To EA**: Technical brief (Invoice PDF, check-in logistics, airport transfer confirmation, payment receipt).
    2. **To Traveler**: Emotional brief (Welcome letter, curated villa highlights, weather forecast, spa menu).
- **Failure Mode**: False Positive. System sends the technical invoice to the traveler directly, breaking the "Luxury Experience" flow.

---

## 2. MICE (Meetings, Incentives, Conferences, Exhibitions)

### [MICE-001] Manifest Deadline Near-Miss (P3)
- **Persona**: P3 (Junior Agent)
- **Scenario**: 100 people are traveling for a sales kickoff in Dubai. The "Group Air Block" name deadline is in 2 hours. 15 people haven't submitted their passport details.
- **Input (System Alert)**: Manifest Deadline in 120 mins. 15/100 names missing.
- **N01 Fact**: { "group": "Sales_Kickoff_2026", "missing_count": 15, "time_left": 120 }
- **N02 Decision**: Proceed. Identify the missing individuals. Send an "Urgent Action Required" ping to the Corporate Admin. Prepare to "Release" the 15 seats to avoid financial penalties if data isn't received in 60 mins.
- **Failure Mode**: False Negative. System waits for the deadline to pass before alerting the agent.

### [MICE-002] On-Site Dietary Crisis (S1)
- **Persona**: S1 (Individual Traveler - Corporate Guest)
- **Scenario**: During the Gala Dinner for a tech conference, a guest with a severe nut allergy realizes the "Nut-Free" dish served contains almond garnish.
- **Input (Urgent WhatsApp to Agent)**: "I'm at the dinner. They just served me nuts after I told everyone I'm allergic. This is dangerous."
- **N01 Fact**: { "traveler": "Guest_Z", "issue": "allergy_violation", "urgency": "critical" }
- **N02 Decision**: Stop. Contact the on-site Banquet Manager immediately. Ensure medical assistance is on standby. Document the failure in the `AuditStore` for supplier accountability.
- **Failure Mode**: Authority Inversion. System tries to "apologize" first instead of escalating to the venue manager/medical team.
