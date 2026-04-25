# Reg Spec: Pet-Travel-Compliance (REG-REAL-002)

**Status**: Research/Draft
**Area**: Biological Transit & Safety Compliance

---

## 1. The Problem: "The Stranded Pet"
Pet travel is one of the most stressful and complex travel verticals. Rules for vaccines, microchips, crate dimensions, and breed-restrictions vary by airline, country, and season (e.g., temperature bans). A single missing USDA endorsement can lead to a pet being quarantined for months or denied entry at the gate.

## 2. The Solution: 'Biological-Transit-Protocol' (BTP)

The BTP allows the agent to act as a "Vet-Coordination-Guardian" by managing the complex timeline of pet travel.

### Compliance Actions:

1.  **Vaccine-Timeline-Watchdog**:
    *   **Action**: Calculating the "Biological-Window" for required shots (e.g., "Rabies must be given > 30 days but < 365 days before arrival").
2.  **Breed-Restriction-Audit**:
    *   **Action**: Autonomously checking the specific aircraft's cargo-hold capabilities against the pet's breed (e.g., "Air France does not fly Bulldogs on the 777-300 in August due to heat").
3.  **Endorsement-Fulfillment-Tracking**:
    *   **Action**: Providing a "Step-by-Step" checklist for the traveler to obtain local vet signatures and government (USDA/DEFRA) endorsements.
4.  **In-Flight-Safety-Pings**:
    *   **Action**: 2 hours before the flight, the agent "Pings" the ground-crew to "Verify-Loading" of the pet and notifies the traveler via Push/WhatsApp.

## 3. Data Schema: `Pet_Compliance_Manifest`

```json
{
  "manifest_id": "BTP-88221",
  "pet_name": "LUNA",
  "species": "DOG",
  "breed": "GOLDEN_RETRIEVER",
  "destination": "UNITED_KINGDOM",
  "compliance_checklist": [
    {"type": "ISO_MICROCHIP", "status": "CONFIRMED"},
    {"type": "RABIES_CERT", "status": "EXPIRING_SOON", "due_date": "2026-11-12"},
    {"type": "TAPEWORM_TREATMENT", "window": "24_120_HOURS_BEFORE_ARRIVAL"}
  ],
  "airline_approval_code": "PETC-BA-9911",
  "crate_dimensions_cm": "90x60x65"
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Season-Heat-Ban' Rule**: If the destination temperature is predicted to be > 85°F (29°C), the agent MUST autonomously recommend "Evening-Flights" or "Climate-Controlled-Routing."
- **Rule 2: Hard-Stop-on-Incomplete-Vax**: The agent MUST NOT "Finalize" a pet-booking if the vaccine window is mathematically impossible to meet before the flight.
- **Rule 3: Cargo-vs-Cabin-Inference**: The agent must autonomously identify if the pet's weight + crate-size allows for "In-Cabin" travel vs "Manifest-Cargo."

## 5. Success Metrics (Safety)

- **Quarantine-Incidents**: Target: 0 (due to documentation errors).
- **Traveler-Peace-of-Mind**: % of pet travelers who report "High Confidence" in the agent's guidance.
- **Loading-Verification-Latency**: Time from "Cargo-Loading" to "Traveler-Notification" (Target: < 15 mins).
