# P3-S3: "Is This Right?" Check

**Persona**: Junior Agent
**Scenario**: A new agent is unsure whether their quote is correct and needs the system to validate it before sending.

---

## Situation

A junior agent has put together a quote for a customer and is hesitating.
They want confirmation that the proposal aligns with the customer’s request and is not missing anything important.

### Customer request
- Destination: Vietnam
- Duration: 9 days in October
- Party: 2 adults, 2 children
- Preferences: culture, beach, moderate pace
- Budget: ₹3.5L

### Agent’s state
- Anxious about sending the wrong thing
- Wants to avoid having to redo the quote
- Needs a quick check that the quote is good enough

## What the system should do

1. **Assess the quote quality**
   - Review alignment to customer preferences
   - Confirm budget sanity and itinerary balance
   - Detect any missing items (visa, transport, meals)

2. **Provide a confidence signal**
   - "This quote is 82% aligned with the request"
   - Show the main mismatch if any

3. **Offer explicit review guidance**
   - "The budget is within range, but beach time is limited"
   - "Add an alternative for a slower pace if the family prefers less travel"

4. **Highlight risk areas**
   - If the budget is tight, warn the agent
   - If the itinerary has too many long travel days, flag it

## Required system behaviors

- Quote validation against customer request
- Confidence scoring or guidance
- Plain-language feedback for junior agents
- Risk highlighting before send
- Support for learning from the review

## Why this matters

Junior agents need confidence and quick feedback.
This scenario prevents low-quality quotes from leaving the agency.

## Success criteria

- The agent receives clear validation feedback.
- Any mismatch is explained in plain language.
- The quote is improved before sending.
- The agent learns why the quote was or was not right.
