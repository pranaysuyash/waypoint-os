# Fin Spec: Travel-Interruption-Insurance-Claims (FIN-REAL-005)

**Status**: Research/Draft
**Area**: Financial Recovery & Consumer Protection

---

## 1. The Problem: "The Claim Burden"
Filing a travel insurance claim is a tedious process requiring specific "Proof-of-Loss" documentation: delay letters, receipts for essential items, medical reports, and weather certificates. Travelers often give up or submit incomplete claims, leading to denials. The agency has all the data required to automate this.

## 2. The Solution: 'Claim-Evidence-Protocol' (CEP)

The CEP allows the agent to act as a "Recovery-Specialist" by autonomously assembling the "Evidence-Packet" for any covered loss.

### Recovery Actions:

1.  **Incident-Trigger-Detection**:
    *   **Action**: Detecting a "Covered-Event" (e.g., flight delay > 6 hours, trip cancellation due to illness) and proactively asking the traveler: "Shall I file your insurance claim?"
2.  **Evidence-Synthesis-Engine**:
    *   **Action**: Autonomously gathering: 
        - **Official Delay/Cancellation Letter** (from airline API).
        - **Original vs Replacement Itinerary** (from ITIN-001).
        - **Itemized Receipts** (via OCR from traveler's phone/email).
        - **Weather/ATC Reports** (from 3rd party providers).
3.  **Submission-Ready-Packet-Generation**:
    *   **Action**: Compiling all evidence into a single, structured PDF that matches the specific requirements of the traveler's insurance provider (e.g., Allianz, AMEX, World Nomads).

## 3. Data Schema: `Insurance_Claim_Packet`

```json
{
  "claim_id": "CEP-88221",
  "traveler_id": "GUID_9911",
  "incident_type": "TRIP_DELAY",
  "insurance_provider": "ALLIANZ_GLOBAL",
  "policy_number": "POL-992211",
  "evidence_items": [
    {"type": "AIRLINE_DELAY_CERT", "source": "BA_API_CONFIRMED"},
    {"type": "HOTEL_RECEIPT", "source": "OCR_AUDITED"},
    {"type": "WEATHER_REPORT", "source": "MET_OFFICE_DATA"}
  ],
  "estimated_claim_value_usd": 350.00,
  "submission_status": "READY_FOR_TRAVELER_SIGNATURE"
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Max-Recovery' Rule**: The agent MUST check all overlapping insurance policies (e.g., primary travel insurance + credit card trip protection) to identify the highest payout.
- **Rule 2: Automated-Follow-Up**: If the insurance company requests "More Information," the agent MUST autonomously attempt to find that data in its archives before asking the traveler.
- **Rule 3: Deadlines-Watchdog**: The agent MUST alert the traveler 7 days before the claim submission deadline (usually 30-90 days post-trip).

## 5. Success Metrics (Recovery)

- **Claim-Success-Rate**: % of submitted claims that result in a payout.
- **Average-Claim-Value**: Total $ recovered for travelers vs manual submission baseline.
- **Traveler-Effort-Reduction**: Reduction in manual steps required for the traveler to file a claim (Target: > 80% reduction).
