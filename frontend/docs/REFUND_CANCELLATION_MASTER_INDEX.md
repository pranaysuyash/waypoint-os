# Refund & Cancellation Management — Master Index

> Exploration of cancellation policies, refund processing, modifications, and cancellation UX.

| # | Document | Focus |
|---|----------|--------|
| 01 | [Policies & Rules](REFUND_01_POLICIES.md) | Policy model, penalty calculation engine, policy hierarchy |
| 02 | [Processing & Workflows](REFUND_02_PROCESSING.md) | Refund pipeline, payment chain reconciliation, dispute resolution |
| 03 | [Modification & Rebooking](REFUND_03_MODIFICATIONS.md) | Modification types, rebooking optimization, modification accounting |
| 04 | [UX & Communication](REFUND_04_UX.md) | Cancellation UX, penalty display, refund tracking, communication templates |

---

## Key Themes

- **Transparent penalties** — Every cancellation shows exactly what the penalty is, why it applies, and where the money goes. No hidden fees or surprise deductions.
- **Modify first, cancel second** — Offer modification as an alternative to cancellation. Keeping the customer's business is always better than processing a refund.
- **Refund tracking is visible** — Customers can see their refund progressing through each step (cancelled → supplier confirmed → processing → completed) with estimated dates.
- **Automated reconciliation** — The platform tracks the full payment chain (customer → agency → supplier) and flags discrepancies automatically.
- **Policy engine is configurable** — Cancellation rules vary by supplier, season, fare class, and contract. The rule engine handles all combinations.

## Integration Points

- **Booking Engine** — Cancellation is a state transition in the booking state machine
- **Payment Processing** — Refunds flow through the payment gateway
- **Financial Reconciliation** — Refund entries sync with accounting (Tally)
- **Commission Management** — Cancelled bookings trigger commission reversal
- **Notification System** — Cancellation and refund status updates use notifications
- **Customer Portal** — Customers can initiate and track cancellations
