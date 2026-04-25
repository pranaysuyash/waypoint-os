# Supply Spec: Automated Contractual Clawbacks (SU-002)

**Status**: Research/Draft
**Area**: Financial Recovery & SLA Enforcement

---

## 1. The Problem: "The Lost Refund"
Agencies lose millions in unclaimed refunds and penalties because tracking every flight delay or hotel walk-out against the specific contract terms is manually impossible.

## 2. The Solution: 'SLA-Enforcement-Engine' (SEE)

The SEE monitors the `AuditStore` and automatically matches "Failure Events" against the "Supplier Contract Library."

### Clawback Triggers:

1.  **Flight Delay/Cancellation (EC 261/2004)**:
    *   **Action**: If a flight to/from EU is delayed > 3 hours, AI auto-files the claim for the €250-€600 compensation.
2.  **Hotel 'Walk-out' (Overbooking)**:
    *   **Action**: If a traveler arrives and the hotel has no room, AI triggers the "Penalty-Charge" (e.g., 1st night refund + 50% inconvenience credit).
3.  **No-Show Default**:
    *   **Action**: If a vendor (e.g., car rental) fails to have a vehicle available at the reserved time, AI auto-claims the "Service-Failure" credit.

## 3. Data Schema: `Clawback_Claim`

```json
{
  "claim_id": "CLW-7766",
  "vendor_id": "HOTEL-MARRIOT-NYC",
  "event_id": "WALK-9922",
  "contract_clause_id": "SLA-NON-PERF-01",
  "claim_amount": 450.00,
  "currency": "USD",
  "evidence": {
    "arrival_timestamp": "2026-05-10T22:00:00Z",
    "vendor_refusal_log": "No rooms available due to boiler failure."
  },
  "status": "FILED_AUTONOMOUSLY"
}
```

## 4. Key Logic Rules

- **Rule 1: Auto-Offsetting**: If a vendor owes the agency a clawback, the system can "Auto-Offset" this against the next payment to that vendor (if contractually permitted).
- **Rule 2: The 'Volume-Leverage' Threshold**: If a vendor has > 5% failure rate in a month, the system auto-notifies the "Procurement Agent" to renegotiate the contract.
- **Rule 3: Settlement-Matching**: The system must verify that the refund/credit was actually received in the `Financial_Audit_Store`.

## 5. Success Metrics (Clawback)

- **Recovery Rate**: % of eligible refunds and penalties successfully collected.
- **Manual Labor Reduction**: Reduction in human time spent filing and tracking supplier claims.
- **Vendor Performance Improvement**: Decrease in SLA violations after automated enforcement is enabled.
