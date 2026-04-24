# Area Deep Dive: Regulatory & Compliance (Hard Scenarios)

**Domain**: Compliance & Risk Management  
**Focus**: Data privacy, visa emergencies, sanctions, and biosecurity protocols.

---

## 1. Data Privacy & Sovereign Compliance
The system must handle PII (Personally Identifiable Information) with extreme discipline, especially across jurisdictions like GDPR (Europe) and local Indian data localization rules.

### Scenario A: Right to be Forgotten (Post-Trip)
- **Trigger**: Traveler (S1) requests deletion of all personal data 30 days after trip completion.
- **Complexity**: The agency must delete PII (Passports, PAN) but *retain* commercial records for tax/GST audit purposes (7 years).
- **System Action**: 
    1. Scrutinize `CanonicalPacket` for all `traveler_pii` fields.
    2. Execute "Soft-Anonymization" (Replace names with IDs in logs).
    3. Issue a "Deletion Certificate" to the traveler while preserving the financial audit trail in `AuditStore`.

### Scenario B: HIPAA/Medical Data Leakage
- **Trigger**: A traveler shares detailed medical history (e.g., specific heart condition requirements) in the chat.
- **Risk**: This data is "Special Category" and should not be stored in standard `CanonicalPacket` fact slots without encryption or specific consent.
- **System Action**: 
    1. Detect medical terminology.
    2. Flag as "Restricted Data".
    3. Move to a "Vaulted Slot" (Non-indexed, restricted access).
    4. Warn the agent: "Medical data detected. Ensure compliance with health privacy protocols."

---

## 2. Visa & Border Logic Exceptions
Border rules are dynamic and often contradictory. The AI must manage "Mid-Air Disruptions".

### Scenario C: The "Mid-Air" Visa Rule Change
- **Trigger**: While a traveler is flying from Delhi to London, the destination country changes its entry requirements for their specific passport (e.g., immediate quarantine or new PCR mandate).
- **Action**:
    1. Intelligence Pool (Playbook F) detects the change globally.
    2. System identifies all "In-Air" or "Pre-Departure" travelers on that route.
    3. AI drafts an "Emergency Brief" for the traveler to read upon landing.
    4. Proactively identifies "Return Flight" or "Diversion" options if entry is denied.

---

## 3. Commercial & Sanctions Enforcement
Financial compliance is a binary success/fail.

### Scenario D: Sanctioned Entity Detection
- **Trigger**: A traveler requests a booking at a specific hotel that has recently been added to a trade sanctions list (OFAC/EU).
- **Risk**: Agency liability for "Trading with Sanctioned Entities".
- **System Action**:
    1. Cross-reference supplier ID against the "Global Sanction Intelligence Pool".
    2. Hard-block the `NB02: Decision` engine with `STOP_NEEDS_REVIEW`.
    3. Rationale: "Commercial Sanction Alert: Entity ID #12345 is on the restricted list."

---

## 4. Implementation Grounding: Compliance Models

To support these "Hard Scenarios", the `spine_api` requires specific compliance-aware extensions:

| Model | Purpose in Compliance |
|-------|-----------------------|
| `AuditStore` | Primary source for regulatory audits; must be immutable. |
| `IntelligencePoolRecord` | Tracking global rule changes (Visa/Sanctions) as they happen. |
| `ConsentLog` | (Proposed) Tracking explicit traveler consent for PII/Medical data usage. |

---

## 5. Targeted Evaluation Scenarios

The following scenarios should be generated to test these boundaries:
1. `sc_comp_gdpr_deletion_request.json`
2. `sc_comp_medical_data_vaulting.json`
3. `sc_comp_mid_air_visa_pivot.json`
4. `sc_comp_sanctioned_hotel_block.json`
