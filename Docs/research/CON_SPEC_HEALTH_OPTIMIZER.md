# Con Spec: Agentic 'Pre-Travel-Health' Optimizer (CON-REAL-034)

**Status**: Research/Draft
**Area**: Traveler Health Preparedness & Medical Risk Reduction

---

## 1. The Problem: "The Last-Minute-Health-Scramble"
Most travelers discover health requirements only days before departure: "I need a Yellow Fever vaccine but the nearest clinic appointment is in 3 weeks." Or they arrive at altitude without acclimatization preparation, or they forget to source antimalarials for a remote safari leg. These "Last-Minute-Health-Failures" cause trip cancellations, medical emergencies abroad, and severe traveler distress — all preventable with intelligent advance planning.

## 2. The Solution: 'Health-Readiness-Protocol' (HRP)

The HRP acts as the "Medical-Concierge-Pre-Brief."

### Health Optimization Actions:

1.  **Destination-Health-Profile-Generation**:
    *   **Action**: For each confirmed destination in the itinerary, generating a "Destination-Health-Profile" covering: required vaccinations, recommended vaccinations, malaria risk zones, altitude acclimatization requirements, water safety, food safety, and endemic disease risk.
2.  **Traveler-Specific-Health-Adaptation**:
    *   **Action**: Cross-referencing the destination health profile with the traveler's "Health-Flags" (stored with consent) — e.g., known allergies, chronic conditions, current medications — to flag specific risks and conflicts (e.g., "Your current blood thinner may interact with the recommended antimalarial for this region").
3.  **Vaccination-Timeline-Sequencing**:
    *   **Action**: Building a precise "Vaccination-Timeline" that accounts for series completion requirements (e.g., Hepatitis B requires 3 doses over 6 months) and books well in advance of the trip.
4.  **Altitude-Acclimatization-Protocol**:
    *   **Action**: For high-altitude destinations (>3000m), generating a personalized "Acclimatization-Schedule" integrated into the itinerary (e.g., "Day 1 in Cusco: no exertion, coca tea only, light meals — full activity only on Day 3").

## 3. Data Schema: `Pre_Travel_Health_Brief`

```json
{
  "brief_id": "HRP-88221",
  "traveler_id": "TRAVELER_ALPHA",
  "itinerary_id": "PERU-2026-09",
  "destinations_analyzed": ["LIMA", "CUSCO_3400M", "MACHU_PICCHU"],
  "vaccinations_required": ["HEPATITIS_A", "TYPHOID"],
  "altitude_risk": "HIGH",
  "traveler_flag_conflicts": ["BETA_BLOCKER_ALTITUDE_INTERACTION"],
  "vaccination_timeline_generated": true,
  "physician_referral_required": true,
  "status": "BRIEF_DELIVERED_TO_TRAVELER"
}
```

## 4. Key Logic Rules

- **Rule 1: The 'No-Medical-Advice' Boundary**: The agent MUST present health information as "Preparation-Guidance" and always direct travelers to a qualified physician or travel medicine clinic for final medical decisions. It MUST NOT diagnose or prescribe.
- **Rule 2: The 'Conflict-Escalation' Rule**: Any identified drug-interaction or chronic-condition conflict MUST trigger an immediate "Physician-Referral" recommendation — it MUST NOT be presented as just an informational note.
- **Rule 3: Consent-Governed-Health-Flags**: Traveler health flags MUST only be stored with explicit, granular consent. Travelers MUST be able to delete specific health flags at any time.

## 5. Success Metrics (Health)

- **Last-Minute-Health-Issue-Rate**: % reduction in health-related trip cancellations or on-trip medical incidents for travelers who completed a Health-Brief.
- **Vaccination-Completion-Lead-Time**: Average days before departure by which travelers complete all required vaccinations.
- **Physician-Referral-Conversion-Rate**: % of "Physician-Referral" recommendations that travelers acted on.
