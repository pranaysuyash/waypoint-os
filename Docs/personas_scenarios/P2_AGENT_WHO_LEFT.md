# P2-S2: The Agent Who Left

**Persona**: Agency Owner
**Scenario**: A high-performing agent resigns suddenly and leaves several active bookings mid-progress. The owner must keep service quality and customer confidence intact.

---

## Situation

A valued agent has hand-delivered a set of active bookings, but the agency owner gets a surprise resignation notice on Friday.
Several customers are in the middle of critical booking stages.
The owner needs to transfer ownership without losing context or making customers feel abandoned.

### Customer impact
- Some customers have ongoing follow-ups: passport checks, hotel confirmations, special meal requests.
- Some quotes are pending approval.
- One customer has a flight hold expiring in 24 hours.

### Owner challenges
- Recover the knowledge that lived in the departed agent’s head
- Reassign active work quickly
- Avoid customer confusion and ship delays
- Maintain trust across the team

## What the system should do

1. **Capture the departing agent’s context**
   - Aggregate active bookings, customer notes, priority issues, and next actions
   - Show a handover dashboard for each customer

2. **Transfer ownership smoothly**
   - Automatically reassign the work to a replacement agent
   - Mark each active booking with the new owner and inherited notes

3. **Preserve customer confidence**
   - Provide the new agent with a summary: what was decided, what remains open, and what the customer expects
   - Keep follow-up deadlines visible

4. **Prevent repetition**
   - Avoid asking customers the same questions again
   - Make the knowledge base the single source of truth for customer history

## Required system behaviors

- Knowledge persistence for customers and bookings
- Active handover workflow when an agent leaves
- Alerts for time-sensitive follow-ups
- Visibility into which trips were reassigned
- Ability to resume without re-asking the customer

## Why this matters

This scenario tests whether the agency can survive staff turnover without service breakdown.
For a small team, losing one agent should not mean losing half the customer knowledge.

## Success criteria

- The owner can see all active bookings owned by the departed agent.
- The system auto-generates handover summaries.
- Reassigned agents get clear next actions.
- Customers do not receive duplicate or contradictory questions.
- No critical booking deadlines are missed due to the transition.
