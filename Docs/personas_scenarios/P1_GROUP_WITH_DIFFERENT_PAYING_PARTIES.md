# P1-S5: Group Trip with Different Paying Parties

**Persona**: Solo Agent
**Scenario**: A coordinator sends a multi-family group trip request where each family has different budgets and payment needs.

---

## Situation

A coordinator wants to book a group trip for three families traveling together.
Each family has different budgets and responsibilities.
The solo agent must manage the group logistics while keeping the quote clean and fair.

### Customer request
- Destination: Singapore
- Travel party: 3 families, 11 people total
- Family A budget: ₹3L
- Family B budget: ₹2L
- Family C budget: ₹2.5L
- Special requests: family A needs accessible rooms, family B prefers pool access, family C wants vegetarian meals
- Planner: wants one consolidated package that can be split by family

### Agent’s internal state
- Worried about splitting costs fairly
- Unsure if suppliers support different room blocks under one booking
- Concerned about handling payment collection and invoicing
- Needs to keep the group organized and avoid confusion

## What the system should do

1. **Detect group coordination**
   - Recognize this as a multi-family, multi-payer booking
   - Treat it as a coordinator-led request, not a single-family quote

2. **Capture per-family constraints**
   - Budget, accessibility, meal preferences, room requirements for each family
   - Show the common itinerary and family-specific options separately

3. **Offer structured pricing**
   - Present a master itinerary with per-family cost splits
   - Highlight which services are shared and which are family-specific
   - Indicate where the group can save by sharing transfers or activities

4. **Support payment complexity**
   - Suggest payment milestones or split billing
   - Warn if a single supplier cannot handle multiple payers
   - Provide clear wording for the coordinator to send to families

## Required system behaviors

- Multi-party booking recognition
- Family-specific preference tracking
- Split pricing presentation
- Coordinator communication support
- Risk flags for shared services and payment complexity

## Why this matters

Group bookings are high-revenue but high-risk.
A solo agent needs the system to manage the complexity without losing control.

## Success criteria

- The request is identified as a coordinator-led group booking.
- The system shows separate budgets and preferences for each family.
- The quote includes a clear per-family split.
- The agent can explain shared costs and payment logistics.
- The proposal does not collapse into a single undifferentiated price.
