# Fin Spec: Dynamic Baggage-Claims-Arbitrator (FIN-REAL-006)

**Status**: Research/Draft
**Area**: Financial Recovery & Passenger Rights Enforcement

---

## 1. The Problem: "The Administrative Wall"
When luggage is delayed or damaged, airlines are legally liable for compensation under the Montreal Convention (up to ~$1,700 USD). However, the process for filing a claim—gathering "Property-Irregularity-Reports" (PIR), submitting receipts for "Essential-Purchases," and citing specific legal clauses—is so complex that most travelers abandon the claim or accept a sub-optimal voucher.

## 2. The Solution: 'Compensation-Automation-Protocol' (CAP)

The CAP allows the agent to act as a "Claims-Arbitrator."

### Recovery Actions:

1.  **Automated Evidence-Gathering**:
    *   **Action**: Analyzing the traveler's digital evidence (PIR photos, bag-tag receipts, photos of damage) and cross-referencing it with the "Logistics-Telemetry" (OPS-018) to verify the delay duration.
2.  **Montreal-Convention Audit**:
    *   **Action**: Autonomously identifying the specific legal clauses (e.g., Article 19 for delay, Article 17 for damage) that apply to the traveler's specific route and airline.
3.  **Essential-Expense-Optimization**:
    *   **Action**: Analyzing the traveler's receipts for items purchased during the delay (e.g., toiletries, clothing) and categorizing them as "Reasonable-Expenses" to maximize the claim payout.
4.  **Demand-Letter Generation**:
    *   **Action**: Drafting a formal, legally-cited "Demand-Letter" to the airline's legal department, demanding the maximum eligible cash settlement rather than generic vouchers.

## 3. Data Schema: `Baggage_Claim_Engagement`

```json
{
  "claim_id": "CAP-99112",
  "traveler_id": "GUID_9911",
  "airline": "BRITISH_AIRWAYS",
  "incident_type": "DELAYED_BAGGAGE",
  "pir_number": "LHRBA112233",
  "delay_duration_hours": 42,
  "eligible_convention": "MONTREAL_1999",
  "total_expenses_claimed_usd": 350.00,
  "max_potential_recovery_usd": 1720.00,
  "status": "DEMAND_LETTER_SUBMITTED"
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Voucher-Rejection' Default**: The agent MUST explicitly reject the airline's first offer of "Travel-Vouchers" and demand "Cash-Settlement" unless the voucher value is >150% of the cash eligibility.
- **Rule 2: Essential-Item-Audit**: The agent MUST ensure receipts are dated *after* the reported bag delay and *before* the bag was returned to the traveler.
- **Rule 3: Statutory-Deadline-Watchdog**: The agent MUST monitor the filing deadlines (e.g., 21 days for delayed baggage, 7 days for damaged) and push high-severity alerts to the traveler to finalize evidence before the claim expires.

## 5. Success Metrics (Financial)

- **Recovery-Fulfillment-Ratio**: Actual cash recovered vs. legal maximum eligibility.
- **Claim-Submission-Velocity**: Time from incident detection to formal demand-letter submission (target: <24h).
- **Administrative-Effort-Reduction**: Traveler time spent on claim paperwork (target: <10 mins).
