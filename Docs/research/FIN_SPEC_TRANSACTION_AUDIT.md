# Financial Spec: Real-Time Transaction Auditing (FI-001)

**Status**: Research/Draft
**Area**: Financial Verification & Budget Integrity

---

## 1. The Problem: "The Over-Refund Trap"
In the chaos of re-booking, agents (AI or human) often issue refunds or credits that exceed the original booking value, or fail to account for "Non-Refundable" segments already consumed.

## 2. The Solution: 'Money-Flow-Validator' (MFV)

The MFV sits between the `Action_Engine` and the `Payment_Gateway`, performing a "Look-Ahead" audit of every financial intent.

### Validation Rules:

1.  **Net-Zero Integrity**:
    *   **Rule**: `Sum(Refunds + Credits + New_Bookings) <= Original_Booking_Value + Authorized_Disruption_Budget`.
    *   **Alert**: If the AI attempts to spend more than the "Authorized Cap" for a specific traveler tier.
2.  **Segment-Consumption Check**:
    *   **Rule**: Verify that a refund is not being issued for a segment that has already been "Flown" or "Checked-In."
3.  **Currency-Parity Audit**:
    *   **Rule**: Verify that the currency conversion used in the refund matches the "Transaction-Date" rate or the "Booking-Date" rate (per policy).

## 3. Data Schema: `Audit_Intent_Verification`

```json
{
  "verification_id": "VFY-7766",
  "intent_id": "REF-9922",
  "traveler_id": "TRV-123",
  "original_value": 1250.00,
  "proposed_action": {
    "type": "REFUND",
    "amount": 450.00,
    "reason": "Segment Cancellation"
  },
  "verdict": "REJECTED",
  "rejection_reason": "Proposed refund exceeds the 'Unconsumed_Balance' of $320.00",
  "remediation": "Capping refund to $320.00 and issuing $130.00 in 'Goodwill-Credit' instead."
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Inventory-Lock'**: Before authorizing a refund, the MFV must "Lock" the segment in the `CanonicalPacket` to prevent a "Double-Refund" from a simultaneous tool call.
- **Rule 2: Tax-Symmetry**: The AI must ensure that "Airport Taxes" and "Surcharges" are refunded in the same proportion as the base fare, unless local law requires 100% tax refund.
- **Rule 3: Multi-Party Split Integrity**: If a booking was paid by multiple parties (e.g., Company + Employee), the MFV ensures the refund is split back to the **original payment methods** in the same ratio.

## 5. Success Metrics (Audit)

- **Budget Leakage**: Dollars saved by preventing over-refunds and incorrect credits.
- **Audit Accuracy**: % of autonomous transactions that pass a post-hoc human financial audit.
- **Remediation Speed**: Time taken to detect and "Cap" an incorrect financial intent (Target: < 100ms).
