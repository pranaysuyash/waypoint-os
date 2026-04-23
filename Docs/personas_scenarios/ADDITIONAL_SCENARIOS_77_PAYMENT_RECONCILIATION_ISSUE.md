# Additional Scenario 77: Payment Reconciliation Issue

**Scenario**: A customer payment does not match the invoice, and the system must reconcile the difference and decide whether to credit, collect, or absorb the shortfall.

---

## Situation

A customer pays for a booking, but the received amount differs from the expected invoice due to currency, fees, or a partial payment.
The agent must resolve the gap before service delivery.

## What the system should do

- Detect payment mismatch as soon as the payment is received
- Identify whether the difference is due to exchange rates, fees, or partial amounts
- Recommend the correct resolution and communicate it to the customer
- Keep the agency’s accounting and customer expectations aligned

## Why this matters

Payment mismatches are a common operational risk.
Resolving them cleanly prevents service failure and customer friction.

## Success criteria

- The system flags discrepancies promptly
- It offers a sensible resolution path with minimal customer effort
- The booking remains intact and transparent for the customer
