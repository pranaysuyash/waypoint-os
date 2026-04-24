# Additional Scenario 317: Federated Intelligence Threat Detection

**Scenario**: A high-risk visa rejection pattern is detected at Agency A. The system shares an anonymized report to the Federated Intelligence Pool, which proactively warns Agency B before they book a similar trip.

---

## Situation

- **Agency A**: Has 3 travelers rejected for "Digital Nomad Visas" in Indonesia due to a sudden undocumented policy change at the local consulate.
- **Agency B**: Is currently drafting a proposal for 5 Digital Nomads headed to the same location.

## What the system should do

- **Pattern Recognition**: Agency A's system detects the 3x rejection pattern.
- **Anonymize & Report**: Create an `IntelligencePoolRecord`: `incident_type: "consulate_policy_pivot"`, `severity: 5`, `anonymized_data: {"consulate": "Denpasar", "visa_type": "E33G"}`.
- **Broadcast**: Share the record via the federated network.
- **Proactive Warning (Agency B)**: Agency B's `NB02: Decision` engine receives the alert.
- **Internal Alert**: Before the agent at Agency B sends the proposal, they see: "⚠️ WARNING: High-confidence intelligence indicates immediate visa rejection risks for this route. Review policy before proceeding."

## Why this matters

- Network Effect: Every failure at one agency becomes a protection layer for all others.
- Professional Credibility: Preventing a trip that is guaranteed to fail before it's even booked.

## Success criteria

- `IntelligencePoolRecord` is successfully created with zero PII.
- Agency B receives the "Risk Alert" in real-time.
- The proposal is paused for human review, preventing customer disappointment.
