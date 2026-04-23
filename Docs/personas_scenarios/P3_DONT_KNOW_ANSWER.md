# P3-S4: "Don't Know the Answer"

**Persona**: Junior Agent
**Scenario**: A junior agent receives a request they don’t know how to price or answer, and the system must give them a safe path forward.

---

## Situation

A new agent receives a customer request for a destination they’ve never booked.
They are unsure about flight costs, visa requirements, and whether the budget will cover the trip.

### Customer request
- Destination: Iceland
- Duration: 7 days in September
- Party: 2 adults
- Preferences: nature, hot springs, moderate hiking
- Budget: ₹4L

### Agent’s state
- Feels out of depth
- Doesn't want to invent numbers
- Wants a safe, professional response
- Needs to avoid looking ignorant to the customer

## What the system should do

1. **Provide destination intelligence**
   - Show typical pricing for Iceland travel in September
   - Indicate visa and passport requirements
   - Flag whether ₹4L is realistic

2. **Give a safe response template**
   - "I’m checking the best options for Iceland and will confirm availability shortly."
   - Offer a follow-up question to clarify flexible dates or travel style

3. **Support with comparison**
   - Show a similar destination the agent can quote immediately
   - If Iceland is too expensive, offer an alternative like Portugal or Greece

4. **Protect the agent**
   - Prevent them from guessing a price
   - Provide an explicit "needs research" workflow

## Required system behaviors

- Destination cost intelligence
- Safe answer templates for uncertainty
- Alternative suggestions when the request is risky
- Research mode or expert fallback for junior agents
- Ability to surface confidence levels

## Why this matters

Junior agents should never lose business by appearing unprepared.
This scenario makes the system their trusted backstop when they don’t know the answer.

## Success criteria

- The agent gets a clear, safe path forward.
- The system provides relevant research data.
- The response to the customer is professional and accurate.
- The agent avoids guessing and still moves the conversation forward.
