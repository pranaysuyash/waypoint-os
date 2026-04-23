# P2-S4: The Training Time Problem

**Persona**: Agency Owner
**Scenario**: A new junior agent is spending too much time learning the business, and the owner needs the system to accelerate onboarding.

---

## Situation

A new hire is now part of the sales team.
The owner expects them to become productive in days, but they are still dependent after weeks.
Training is consuming senior agents’ time.

### What is happening now
- New agent asks the same questions repeatedly
- Senior agents review every quote manually
- Customers are waiting longer for responses
- The agency is paying for training, not productivity

### Owner concerns
- Training cost is too high
- Consistency across quotes is poor
- New agent confidence is low
- Knowledge is not embedded in the system

## What the system should do

1. **Guided workflows**
   - Provide step-by-step assistance for building a quote
   - Offer recommendations for hotels, budgets, and suitability

2. **Just-in-time coaching**
   - Explain why a recommendation is good or risky
   - Warn the agent before sending low-quality options

3. **Decision support**
   - Surface the customer’s priority clearly
   - Show how each choice affects budget and fit
   - Provide “best next action” suggestions

4. **Performance feedback**
   - Show confidence scores on the agent’s current quote
   - Highlight issues before the quote leaves the system
   - Capture learning outcomes for future review

## Required system behaviors

- Onboarding-focused UI behavior for junior agents
- Explanation of tradeoffs and rationale
- Safe quote validation before send
- Coaching prompts embedded in the workflow
- Tracking of junior agent quote quality over time

## Why this matters

Faster onboarding means lower cost and less dependence on senior staff.
This scenario proves the system can teach while it works.

## Success criteria

- The junior agent can produce a quote with minimal senior help.
- The system flags risky choices before sending.
- The business sees onboarding time drop.
- The agent gains confidence from clear guidance.
