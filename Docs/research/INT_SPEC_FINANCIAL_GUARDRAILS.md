# Integration Spec: Transactional-Safety-Thresholds (INT-001)

**Status**: Research/Draft
**Area**: Agentic Autonomy & Financial Security

---

## 1. The Problem: "The Rogue Agent Wallet"
Granting an agent autonomous payment capabilities is a massive security risk. Without strict guardrails, an agent might accidentally double-book a $5,000 suite or be manipulated into sending funds to a malicious vendor. However, asking for user permission for every $5 taxi ride destroys the "Set-and-Forget" utility of the agency.

## 2. The Solution: 'Transactional-Safety-Thresholds' (TST)

The TST creates a "Tiered-Autonomy" model for spending.

### Autonomy Tiers:

1.  **Tier 1: Full-Autonomy (Low-Stakes)**:
    *   **Threshold**: <$150 USD.
    *   **Examples**: Taxis, baggage fees, coffee/meals, airport parking.
    *   **Action**: Agent pays autonomously using the 'Virtual-Travel-Card' and sends a post-transaction receipt.
2.  **Tier 2: Semi-Autonomy (Medium-Stakes)**:
    *   **Threshold**: $150 - $1,000 USD.
    *   **Examples**: Standard hotel nights, re-booked domestic flights, rental cars.
    *   **Action**: Agent "Soft-Holds" the reservation and sends a "Quick-Tap-Approval" notification (WhatsApp/Push). If the user doesn't respond within 15 mins and it's a "Crisis-Rebooking," the agent escalates to Tier 1 logic if 'Emergency-Override' is enabled.
3.  **Tier 3: Zero-Autonomy (High-Stakes)**:
    *   **Threshold**: >$1,000 USD.
    *   **Examples**: Long-haul international flights, multi-week luxury stays, group bookings.
    *   **Action**: Agent prepares the "Ready-to-Book" state. User MUST provide Biometric/MFA approval before the transaction is fired.

## 3. Data Schema: `Spending_Authorization_Audit`

```json
{
  "auth_id": "TST-77221",
  "traveler_id": "GUID_9911",
  "requested_amount": 850.00,
  "currency": "USD",
  "category": "HOTEL_REBOOKING",
  "tier_detected": "TIER_2",
  "approval_method": "WHATSAPP_QUICK_TAP",
  "timestamp_requested": "2026-11-12T14:00:00Z",
  "timestamp_approved": "2026-11-12T14:02:11Z",
  "virtual_card_last_4": "9922"
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Velocity-Limit' Rule**: Regardless of tier, the agent has a "Daily-Aggregate-Limit" (e.g., $2,000). If total spending in 24h exceeds this, all further transactions drop to Tier 3.
- **Rule 2: Vendor-Whitelisting**: The agent can only exercise Tier 1/2 autonomy with "Verified-Vendors" (e.g., major airlines, hotel chains, known OTAs). New or "Boutique" vendors always require Tier 3 approval.
- **Rule 3: Conflict-of-Interest-Detection**: If the agent is re-booking a flight that it originally booked, it MUST audit if a "Free-Change" or "Credit" is available before spending new funds.

## 5. Success Metrics (Financial)

- **Frictionless-Transaction-Ratio**: % of low-stakes purchases handled without user interruption.
- **Unauthorized-Spend-Rate**: Target: 0.00%.
- **Approval-Latency**: Average time taken for users to approve Tier 2/3 transactions.
