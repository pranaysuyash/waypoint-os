# Additional Scenario 53: Multi-Vendor Refund Coordination

**Scenario**: A trip cancellation requires refunds from airlines, hotels, and tour operators, and the system must coordinate the timing and messaging.

---

## Situation

A customer cancels a trip with multiple vendors, and each has different refund rules and processing timelines.
The agency needs to manage customer expectations and the refund process.

## What the system should do

- Map each refundable component to its vendor and policy
- Estimate when the customer will see funds return
- Communicate partial refunds and pending items clearly
- Keep a single coordination thread for the customer and agents

## Why this matters

Refund complexity can create distrust if poorly explained.
A coordinated process with clear timelines preserves customer confidence.

## Success criteria

- The system documents refund status for each vendor
- It gives customers a consolidated view of what is paid and pending
- The agency avoids confusion over mixed timelines and fees
