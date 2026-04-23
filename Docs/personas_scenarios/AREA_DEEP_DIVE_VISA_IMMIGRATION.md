# Area Deep Dive: Visa & Immigration Mastery

**Domain**: Statutory Compliance & Border Control  
**Focus**: Complex visa types, reciprocity, and documentation automation.

---

## 1. Visa Types & Complexity

Border control is the single biggest "Friction Point" in international travel. Failure here results in immediate "Deportation" or "Boarding Denied" (Phase 2/3 failure).

### Standard vs. Specialized Visas
- **Tourist (L)**: Standard entry for leisure.
- **Business (B1/B2)**: Requires an invitation letter from a local company.
- **Digital Nomad / Remote Work**: Emerging visas (e.g., UAE, Portugal, Bali) that allow long-term stays without local employment.
- **Transit Visas**: Often overlooked for 1-stop flights in countries like China or the UK.

### Reciprocity & Diplomacy
- **Logic**: A country's visa rules for Traveler A depend entirely on Traveler A's passport.
- **System Action**: Cross-referencing "Passport Nationality" with "Destination Country" using a live API (e.g., Sherpa or VisaCentral).

---

## 2. Documentation & Invitation Letters

### The "Invitation" Workflow
- **Process**: For business or MICE travel, the host company must provide a signed, stamped invitation letter.
- **System Action**: Automating the request-and-tracking of these letters in Phase 1 (Planning).

### E-Visas vs. Stamped Visas
- **E-Visas**: Fast, digital, but high risk of "Typo Rejection".
- **Physical Stamps**: Requires courier logistics to an Embassy.
- **System Action**: Managing the "Courier Tracking" and "Embassy Appointment" manifest for P3 agents.

---

## 3. Statutory Compliance (VTL/Health/Criminal)

### Entry Requirements beyond Visas
- **Health Declarations**: Yellow Fever certificates, PCR (where applicable), or health insurance mandates.
- **Criminal Disclosures**: (e.g., Canada’s strictness on DUI records).
- **System Action**: Prompting the traveler (S1/S2) to disclose "Entry Blockers" early in the funnel.

---

## 4. Proposed Scenarios for this Domain

| Scenario ID | Title | Persona | Category |
|-------------|-------|---------|----------|
| VISA-001 | Transit Visa Oversight Catch | P3 | Compliance |
| VISA-002 | Digital Nomad Tax Residency Warning | S1 | Legal |
| VISA-003 | E-Visa Typo Correction | S1 | Recovery |
| VISA-004 | Missing Business Invitation Letter | P1 | Fulfillment |
| VISA-005 | Passport Validity < 6 Months | S1 | Compliance |
| VISA-006 | Reciprocity Rule Change Alert | P2 | Risk |
