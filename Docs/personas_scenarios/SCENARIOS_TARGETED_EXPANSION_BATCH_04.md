# Targeted Scenario Expansion - Batch 04 (Tech & Crisis)

This batch targets "High Complexity" failure modes in API infrastructure and life-safety Crisis Management.

---

## 1. Travel Technology & Distribution

### [TECH-001] NDC Content Parity Conflict (P1)
- **Persona**: P1 (Concierge Agent)
- **Scenario**: A traveler finds a fare on the airline's website that is $200 cheaper than what the agent sees in the GDS.
- **Input (Traveler Screenshot)**: "Look, the airline site has this for $800, your system says $1000."
- **N01 Fact**: { "gds_price": 1000, "direct_price": 800, "ndc_available": true, "api_sync_status": "delayed" }
- **N02 Decision**: Investigate. Check the NDC feed directly. If the NDC price is $800, price-match immediately and flag the GDS as "Stale" for this route. Explain the "Content Parity" lag to the traveler to maintain trust.
- **Failure Mode**: Authority Inversion. System insists the GDS price is the "Official" one and loses the sale to the airline direct site.

### [TECH-002] Queue 0 Schedule Change (S1)
- **Persona**: S1 (Individual Traveler)
- **Scenario**: A flight from London to New York has been moved 4 hours earlier, causing a connection miss.
- **Input (GDS Queue Alert)**: "Flight BA-175: DEP 10:00 -> 06:00. MSG: UNABLE TO CONNECT TO AA-101."
- **N01 Fact**: { "old_dep": 1000, "new_dep": 0600, "connection": "missed", "status": "critical" }
- **N02 Decision**: Proactive Recovery. Do not wait for the traveler to find out. Automatically search for the next available connection. Alert the traveler (S1) via WhatsApp with the new itinerary and a "Accept/Modify" button.
- **Failure Mode**: Stage Blindness. System waits until Phase 3 (Travel) for the traveler to arrive at the airport before noticing the schedule change.

---

## 2. Crisis Management & Duty of Care

### [CRIS-001] Proactive Welfare Check (Crisis)
- **Persona**: S1 (Traveler in Disaster Zone)
- **Scenario**: A 6.5 magnitude earthquake has just hit Tokyo. The agency has 3 travelers currently checked into hotels in Shinjuku.
- **Input (Threat Feed Alert)**: "EQ-EVENT: TOKYO. MAG: 6.5. IMPACT: HIGH."
- **N01 Fact**: { "event": "earthquake", "location": "tokyo", "travelers_affected": 3, "hotel_safety_status": "unknown" }
- **N02 Decision**: Execute Duty of Care Protocol. Send an automated "Emergency Welfare Check" message to all 3 travelers. Notify the Agency Owner (P2). Identify the "Nearest Safe Haven" (e.g., The US Embassy) and provide GPS coordinates if they report "Not Safe".
- **Failure Mode**: Stage Blindness. System treats it as a "Normal" travel day until a traveler's family calls in a panic.

### [CRIS-002] Medical Repatriation (VIP)
- **Persona**: S1 (VIP Traveler)
- **Scenario**: A VIP traveler in the Swiss Alps has suffered a severe skiing injury and requires an air ambulance to Zurich and then a private MedEvac to Dubai.
- **Input (Emergency Call)**: "Traveler injured. Need MedEvac now."
- **N01 Fact**: { "injury_type": "spinal", "current_loc": "Zermatt", "target_loc": "Dubai", "insurance": "Amex Plat / AXA" }
- **N02 Decision**: High-Priority Orchestration. Open a Crisis Bridge. Contact the insurance provider to authorize the MedEvac. Coordinate with "Air-Zermatt" for the initial lift. Ensure the medical manifest is shared with the Dubai receiving hospital.
- **Failure Mode**: False Negative. System asks for "Standard Documentation" or "Invoice History" before starting the emergency process, wasting critical minutes.
