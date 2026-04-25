# Ops Spec: Virtual Interlining & Connection-Risk (OPS-VINT-001)

**Status**: Research/Draft
**Area**: Logistics Optimization & Risk Management

---

## 1. The Problem: "The Broken Connection"
Virtual interlining (combining flights from carriers that don't have a formal interline agreement, e.g., Southwest + Lufthansa) can save travelers 30-50% on fare. However, if the first flight is delayed, the second carrier has no obligation to rebook the traveler. The traveler is stranded and loses the cost of the second ticket.

## 2. The Solution: 'Connection-Buffer-Protocol' (CBP)

The CBP allows the agent to safely construct virtual interline routes by quantifying and mitigating the "Connection-Risk."

### Logistics Actions:

1.  **Carrier-Reliability-Audit**:
    *   **Action**: Querying the "On-Time-Performance" (OTP) for the specific flight-segment over the last 90 days. If OTP < 75%, the connection is flagged as "High-Risk."
2.  **Dynamic-Buffer-Calculation**:
    *   **Action**: Calculating the "Minimum-Connection-Time" (MCT) plus a "Risk-Buffer" based on: airport size, terminal changes, and "Checked-Bag-Reprocess-Time."
3.  **Automatic-Protection-Trigger**:
    *   **Action**: If a virtual interline is booked, the agent MUST autonomously purchase a "Missed-Connection-Insurance" policy or reserve a "Shadow-Seat" on a later flight.

## 3. Data Schema: `Virtual_Interline_Risk_Profile`

```json
{
  "route_id": "VINT-8811",
  "segments": [
    {"carrier": "FR", "flight": "FR221", "otp": 0.82},
    {"carrier": "EK", "flight": "EK44", "otp": 0.94}
  ],
  "connection_point": "DXB",
  "layover_duration_minutes": 240,
  "calculated_risk_score": 0.12,
  "required_protection": "FULL_REBOOK_GUARANTEE",
  "shadow_seat_id": "RSV-9922"
}
```

## 4. Key Logic Rules

- **Rule 1: Hard-Veto-on-Buffer**: The agent is FORBIDDEN from booking a virtual interline with a connection time < 180 minutes for international-to-international transits.
- **Rule 2: The 'Self-Insurance' Fund**: The agency may use its `Sovereign Wallet` (FIN-002) to "Self-Insure" the connection for high-value travelers, avoiding 3rd party insurance fees.
- **Rule 3: Real-Time-Divert-Monitoring**: The agent MUST monitor the first flight's "Actual-Departure-Time." If delay > 60 mins, the agent MUST start searching for "Backup-Leg-2" before the traveler even lands.

## 5. Success Metrics (Logistics)

- **Connection-Success-Rate**: % of virtual interlines completed without a missed connection.
- **Average-Savings-Per-Route**: Fare difference vs. a standard interline booking.
- **Rebooking-Cost-Efficiency**: Cost of missed-connection payouts vs. total revenue from V-Interline fees.
