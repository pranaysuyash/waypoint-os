# Area Deep Dive: Crisis Management & Duty of Care

**Domain**: Traveler Safety & Emergency Response  
**Focus**: Emergency extraction, medical repatriation, and traveler tracking.

---

## 1. Duty of Care (DoC) Obligations

Agencies have a legal and ethical "Duty of Care" to know where their travelers are and to assist them during emergencies.

### Traveler Tracking (The "Heatmap")
- **Logic**: Real-time monitoring of all active travelers against global "Threat Feeds" (e.g., Riskline, International SOS).
- **System Action**: Triggering an "Immediate Welfare Check" (Phase 3) if a traveler's coordinates match a disaster zone.

### Communication Redundancy
- **Requirement**: Reaching travelers via SMS, WhatsApp, and App Push during a crisis.
- **System Action**: Automating a "Safe/Not Safe" polling sequence if a local emergency is detected.

---

## 2. Emergency Extraction & Repatriation

### Medical Evacuations (MedEvac)
- **Complexity**: Coordinating with air ambulance providers, insurance companies, and hospital discharge teams.
- **System Action**: Opening a "High-Priority Crisis Ticket" (P2) and routing all communication to the Medical Concierge team.

### Political Extractions
- **Logic**: Moving travelers to the "Nearest Safe Haven" or "Neutral Border" during civil unrest or war.
- **System Action**: Identifying "Safe Havens" (Embassies, Vetted 5-star Hotels with Security) in the destination domain.

---

## 3. Post-Crisis Recovery

### Repatriation Logistics
- **Focus**: Getting travelers home once the immediate danger has passed.
- **System Action**: Managing "Emergency Travel Documents" (Phase 2) and booking "Humanitarian Fares".

### Trauma Support
- **Requirement**: Offering psychological support or "Trip Credits" after a traumatic event.
- **System Action**: Tagging the traveler profile as "Post-Crisis sensitive" to ensure softer communication in the future.

---

## 4. Proposed Scenarios for this Domain

| Scenario ID | Title | Persona | Category |
|-------------|-------|---------|----------|
| CRIS-001 | Proactive Welfare Check during Earthquake | S1 | Safety |
| CRIS-002 | MedEvac Coordination for VIP | S1 | Medical |
| CRIS-003 | Nearest Safe Haven Routing | S1 | Extraction |
| CRIS-004 | Emergency Document Loss in Crisis | S1 | Document |
| CRIS-005 | Humanitarian Fare Booking | S1 | Recovery |
| CRIS-006 | Insurance Coverage Dispute for Extraction | P2 | Legal |
