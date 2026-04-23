# P3-S5: Comparison Trap

**Persona**: Junior Agent
**Scenario**: A junior agent is asked to compare multiple options, and the system must help them avoid offering too many confusing or poorly differentiated choices.

---

## Situation

A customer asks the agent for two or three travel options, and the junior agent is tempted to provide everything they can think of.
The result can be overwhelming for the customer and unfocused.

### Customer request
- Destination: Spain
- Duration: 10 days in June
- Party: 2 adults, 1 teen
- Preferences: culture, family-friendly, moderate budget
- Want: "Show me a couple of good options"

### Agent’s state
- Wants to impress by offering several options
- Is unsure which ones are truly comparable
- Risk of overloading the customer

## What the system should do

1. **Recommend a focused set**
   - Suggest 2-3 options with distinct value propositions
   - Avoid offering too many similar alternatives

2. **Differentiate clearly**
   - Option A: Best family-friendly itinerary
   - Option B: Best cultural immersion
   - Option C: Best budget balance

3. **Explain why each option matters**
   - "This path is best if you want fewer transfers"
   - "This one is best if you want more local culture"

4. **Prevent overload**
   - Warn if the agent is about to list more than 3 options
   - Encourage comparison with simple tradeoffs

## Required system behaviors

- Option comparison guidance
- Recommendation of a limited set of meaningful alternatives
- Clear differentiation language
- Overload prevention for agent output
- Customer-facing comparison structure

## Why this matters

Too many options confuse customers and slow decisions.
This scenario ensures the agent provides a polished, easy-to-choose proposal.

## Success criteria

- The agent presents 2-3 well-differentiated options.
- Each option has a clear benefit statement.
- The customer can choose confidently.
- The agent avoids dumping a long list of similar quotes.
