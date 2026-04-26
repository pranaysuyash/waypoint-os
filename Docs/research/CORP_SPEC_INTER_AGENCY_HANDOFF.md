# Corp Spec: Agentic Inter-Agency-Handoff-Protocol (CORP-REAL-019)

**Status**: Research/Draft
**Area**: Agency Collaboration & Ecosystem Fluidity

---

## 1. The Problem: "The Agency Silo"
Travelers often have multifaceted needs that a single agency may not be equipped to handle (e.g., a high-end safari agency might not have expertise in "Medical-Evacuation-Logistics" for a disabled traveler). Currently, these handoffs are manual, leading to "Context-Loss" for the traveler and "Commercial-Disputes" between agencies regarding commission splits and liability.

## 2. The Solution: 'Ecosystem-Fluidity-Protocol' (EFP)

The EFP acts as the "Inter-Agency-Broker."

### Handoff Actions:

1.  **Specialization-Gap Detection**:
    *   **Action**: Identifying when a traveler's request falls outside the "Primary-Agency's" core competencies (e.g., a request for a private jet in a region the primary agency doesn't serve).
2.  **Ecosystem-Matchmaking**:
    *   **Action**: Identifying "Partner-Agencies" within the SaaS network that have the required specialization and a high "Reliability-Rating."
3.  **Context-Bridge (Secure-Transfer)**:
    *   **Action**: Securely transferring the traveler's "Preference-Profile" (TWO) and current "Itinerary-State" to the partner agency, ensuring the traveler doesn't have to repeat their requirements.
4.  **Automated Commercial-Split Settlement**:
    *   **Action**: Autonomously calculating and routing "Referral-Fees" or "Commission-Splits" between the two agencies based on the "Ecosystem-Ruleset."

## 3. Data Schema: `Inter_Agency_Handoff_Event`

```json
{
  "handoff_id": "EFP-88221",
  "primary_agency_id": "AGENCY_ALPHA",
  "partner_agency_id": "SPECIALIZED_MED_TRANS",
  "traveler_id": "GUID_9911",
  "specialization_required": "MEDICAL_LOGISTICS_AFRICA",
  "context_transferred": ["TWO_PROFILE", "FLIGHT_ITINERARY"],
  "commission_split_ratio": 0.20,
  "status": "HANDOFF_ACTIVE"
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Informed-Consent' Rule**: The traveler MUST be informed and provide consent before their data is shared with a partner agency.
- **Rule 2: Liability-Demarcation**: The agent MUST clearly define the "Responsibility-Boundary" for the incident (e.g., "Agency B is responsible for medical logistics; Agency A remains the primary for flights").
- **Rule 3: Success-Fee Protection**: If both agencies are involved in a "Save," the agent MUST autonomously adjudicate the "Success-Fee-Split" based on the "Effort-Weighted-Contribution" of each agency's logic.

## 5. Success Metrics (Collaboration)

- **Handoff-Conversion-Rate**: % of identified specialization gaps that result in a successful inter-agency partnership.
- **Context-Transfer-Fidelity**: Traveler's rating of how "Seamless" the transition felt.
- **Inter-Agency-Revenue-Yield**: Total revenue generated for the ecosystem through cross-agency collaboration.
