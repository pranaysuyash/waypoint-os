# P2-S3: The Margin Erosion Problem

**Persona**: Agency Owner
**Scenario**: Revenue looks healthy, but margins are shrinking because agents are underquoting to win business.

---

## Situation

The agency owner is reviewing monthly performance.
Revenue is up, but profit margin is flat.
The owner suspects the team is closing deals too cheaply.

### What the owner sees
- New bookings are coming in regularly
- Gross revenue appears strong
- Profit margin is lower than target
- Several quotes appear to have high discount levels

### What the owner worries about
- Agents are competing on price rather than value
- Customers may perceive the agency as low-quality
- Low-margin deals reduce long-term sustainability
- The team lacks consistent pricing discipline

## What the system should do

1. **Visibility on margins**
   - Display average margin by agent and by booking
   - Highlight quotes below the minimum margin threshold

2. **Automated approvals**
   - Auto-approve quotes with safe margins
   - Require review for quotes near the threshold
   - Block quotes below the minimum unless an owner approves

3. **Root cause analysis**
   - Show if low margins are due to discounts, supplier costs, or scope creep
   - Compare similar trips to identify pricing drift

4. **Coaching and feedback**
   - Notify agents when their average margin is below target
   - Provide examples of better quotes for similar requests
   - Suggest adjustments that keep the customer satisfied while improving margin

## Required system behaviors

- Quote-level margin tracking
- Agent performance dashboards
- Minimum margin enforcement
- Business intelligence around quote decisions
- Feedback mechanisms for agents

## Why this matters

Without this control, revenue growth can mask an unhealthy business.
This scenario ensures the agency remains profitable while still winning clients.

## Success criteria

- The owner can identify low-margin quotes instantly.
- The system enforces a margin approval workflow.
- Agents see clear margin guidance.
- The agency avoids selling profitable volume at loss-making prices.
