# P3-S1: First Solo Quote

**Persona**: Junior Agent
**Scenario**: A new hire is asked to produce their first full trip quote and needs the system to guide them through the process without causing a major customer mistake.

---

## Situation

A junior agent has just completed training and is now asked to handle their first solo quote.
The customer is a family of 4 traveling to Bali with a modest budget.
The agent is uncertain about hotel selection, budget allocation, and how to keep the proposal safe.

### Customer request
- Destination: Bali
- Dates: 10 days in August
- Party: 2 adults, 2 kids
- Budget: ₹3L total
- Preferences: beach, culture, easy transport, vegetarian food

### Agent’s internal state
- Nervous about making a mistake
- Unsure what hotels are realistic for 4 people in August
- Worried about proposing too much or too little
- Wants to feel supported by the system

## What the system should do

1. **Guide the intake**
   - Show the customer’s request clearly
   - Highlight budget, family size, destination, and special needs
   - Suggest likely hotel categories for the budget

2. **Check feasibility**
   - Evaluate whether ₹3L is realistic for Bali 10 days for 4 people
   - If necessary, generate a friendly budget warning
   - Offer alternatives like shorter trip length or lower-cost region

3. **Provide options**
   - Present 2-3 package suggestions:
     - Basic family resort near the beach
     - Mid-range villa with kitchenette
     - Cultural stay near Ubud with easy transport
   - Show a simple comparison: cost, location, family fit

4. **Explain the tradeoffs**
   - If the budget is tight, say: "This option gives you more beach time but less luxury."
   - If additional spend is needed, say: "To include airport transfers and meals, budget should be closer to ₹3.5-4L."

5. **Validate before sending**
   - Run a checklist: budget, food preferences, family suitability, activity mix
   - If any issue appears, warn the agent in plain language
   - Offer a “send-safe” recommendation

## Desired outcome

The junior agent should finish the quote feeling confident that:
- They understood the customer’s priorities
- The proposal fits the budget or clearly explains why it doesn’t
- The customer gets better options, not just the first idea
- They are protected from making a dangerous recommendation

## Success criteria

- The quote includes at least 2 suitable alternatives
- The system explains any budget risk in simple terms
- The output is safe and aligned with the family request
- The junior agent can see why the system suggested each option
- The agent can send a customer-facing message with confidence
