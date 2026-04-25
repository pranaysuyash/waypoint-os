# Reg Spec: Passenger Rights Automation (REG-REAL-001)

**Status**: Research/Draft
**Area**: Legal Automation & Traveler Protection

---

## 1. The Problem: "The Unclaimed Refund"
Millions of dollars in passenger compensation (e.g., EC 261/2004 for EU flights) go unclaimed every year because travelers are unaware of their rights or the filing process is too complex. An agent needs to autonomously detect qualifying disruptions and "Fight" for the traveler's refund.

## 2. The Solution: 'Claim-Enforcement-Protocol' (CEP)

The CEP allows the agent to act as a "Digital-Legal-Advocate" for the traveler.

### Enforcement Actions:

1.  **Disruption-Detection-Audit**:
    *   **Action**: Monitoring real-time flight status (SENSOR-001). If a delay > 3 hours or a cancellation occurs, the agent triggers a "Rights-Eligibility-Check."
2.  **Autonomous-Claim-Generation**:
    *   **Action**: Generating a formal legal claim packet including: flight info, proof of delay, traveler ID, and the specific regulatory clause (e.g., "Article 7 of Regulation (EC) No 261/2004").
3.  **Submission-and-Follow-Up**:
    *   **Action**: Autonomously "Uploading" the claim to the airline's portal and "Pinging" their support agent every 7 days until a resolution is reached.

## 3. Data Schema: `Passenger_Rights_Claim`

```json
{
  "claim_id": "CEP-88112",
  "traveler_id": "GUID_9922",
  "disruption_event": {
    "flight": "BA217",
    "scheduled": "2026-11-10T10:00:00Z",
    "actual_arrival": "2026-11-10T14:30:00Z",
    "delay_minutes": 270
  },
  "regulation": "EC_261_2004",
  "expected_compensation": "600_EUR",
  "claim_status": "SUBMITTED",
  "evidence_links": ["FLIGHT_STATUS_LOG_77", "TICKET_STUB_88"]
}
```

## 4. Key Logic Rules

- **Rule 1: Pre-Emptive-Notification**: As soon as a delay is detected, the agent MUST notify the traveler: "You are currently eligible for X compensation. We have started the claim process for you."
- **Rule 2: 'Duty-of-Care' Enforcement**: During the delay, the agent must autonomously "Request" (or book and charge-back) meals and hotel vouchers from the airline as required by law.
- **Rule 3: Refusal-Escalation**: If the airline refuses the claim citing "Extraordinary-Circumstances" (e.g., weather), the agent MUST autonomously verify the weather report for that hub at that time. If the report contradicts the airline, the agent escalates to the "National-Enforcement-Body" (NEB).

## 5. Success Metrics (Passenger Rights)

- **Claim-Capture-Rate**: % of qualifying disruptions where a claim was successfully filed.
- **Compensation-Recovery-Time**: Average days from disruption to payout.
- **Recovery-ROI**: Total compensation recovered vs. agent compute/API cost.
