# Reg Spec: Agentic 'Traveler-Advocacy' Legal Shield (REG-REAL-032)

**Status**: Research/Draft
**Area**: Statutory Rights Enforcement & Proactive Legal Advocacy

---

## 1. The Problem: "The Rights-Ignorance-Gap"
The vast majority of travelers don't know their statutory rights. They don't know that EU261/2004 entitles them to €600 compensation for a long-delayed flight. They don't know the Package Travel Directive (EU) 2015/2302 entitles them to a full refund if an insolvency causes their package to fail. Airlines and hotels routinely exploit this ignorance to avoid paying legitimate compensation. Without a "Legal-Advocacy-Shield," travelers leave enormous sums on the table every year.

## 2. The Solution: 'Rights-Enforcement-Protocol' (REP)

The REP acts as the "Traveler's-Legal-Counsel."

### Advocacy Actions:

1.  **Rights-Trigger-Detection**:
    *   **Action**: In real-time, monitoring for events that trigger statutory traveler rights: flight delays >2 hours, cancellations, denied boarding, significant hotel downgrades, package insolvencies, visa refusals due to government error.
2.  **Jurisdiction-Specific-Entitlement-Calculation**:
    *   **Action**: Mapping the specific event to the applicable legal framework (EU261, ANAC regulations, DOT rules, UK CAA standards, DGCA India, etc.) and calculating the exact cash compensation the traveler is entitled to claim.
3.  **Claim-Package-Assembly**:
    *   **Action**: Assembling a complete, ready-to-file claim package: the legal citation, the specific entitlement amount, the required supporting evidence, the airline/hotel's official claims portal URL, and the regulatory escalation path if the airline refuses.
4.  **Airline-Refusal-Escalation**:
    *   **Action**: If the airline or vendor refuses a valid claim, the agent autonomously escalates: filing with the National Enforcement Body (EU), the Aviation Consumer Authority (UK), the DOT Aviation Consumer Protection (US), or equivalent — providing the traveler with a pre-populated formal complaint.

## 3. Data Schema: `Rights_Enforcement_Case`

```json
{
  "case_id": "REP-88221",
  "traveler_id": "TRAVELER_ALPHA",
  "trigger_event": "FLIGHT_DELAY_4H_EU_ROUTE",
  "applicable_law": "EU261_2004",
  "entitlement_eur": 600,
  "claim_package_assembled": true,
  "airline_response": "REFUSED",
  "escalation_body": "NATIONAL_ENFORCEMENT_BODY_DE",
  "complaint_status": "FILED"
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Proactive-Rights-Brief'**: The agent MUST NOT wait for the traveler to ask. When a rights-triggering event occurs, it MUST immediately brief the traveler on their entitlements — even before the traveler realizes they have a claim.
- **Rule 2: Accuracy-Before-Speed**: The agent MUST verify the applicable legal framework before asserting an entitlement. An incorrect legal claim damages the traveler's credibility with the airline. No claims without confirmed jurisdiction.
- **Rule 3: No-Legal-Representation**: The agent MUST clarify that it is providing "Rights-Information" not "Legal-Representation." For complex cases exceeding a threshold value, it MUST recommend a qualified travel law solicitor.

## 5. Success Metrics (Advocacy)

- **Rights-Identification-Rate**: % of rights-triggering events that are correctly identified and briefed to the traveler within 30 minutes.
- **Successful-Claim-Rate**: % of assembled claim packages that result in confirmed compensation payment.
- **Escalation-Success-Rate**: % of airline-refused claims that are successfully resolved via regulatory body escalation.
