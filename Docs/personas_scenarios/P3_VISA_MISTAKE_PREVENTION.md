# P3-S2: Visa Mistake Prevention

**Persona**: Junior Agent
**Scenario**: A new agent handles a travel request and must identify document, visa, or passport issues before the customer books.

---

## Situation

A junior agent is booking a family trip abroad.
The customer says they are ready to book, but the agent is not yet confident about visa or passport requirements.

### Customer request
- Destination: Turkey
- Travel dates: May 10-18
- Party: 2 adults, 2 teens
- Note: "We already have passports"

### Agent’s internal state
- Wants to complete the booking quickly
- Doesn’t know whether Turkey requires e-visas for this nationality
- Unsure if passport validity is sufficient
- Fears missing a compliance issue and causing a customer emergency

## What the system should do

1. **Ask the right questions early**
   - Confirm passport expiry date
   - Determine traveler nationality
   - Identify visa requirements for Turkey

2. **Catch common document issues**
   - Passport validity less than 6 months
   - Single-entry visa requested instead of multiple-entry
   - Missing visa documents for tourists

3. **Prevent unsafe progression**
   - Block final quote approval if required documents are not verified
   - Display a hard-stop warning when the agent attempts to proceed

4. **Provide remediation steps**
   - Suggest passport renewal or visa application steps
   - Offer alternative destinations with simpler document rules

## Required system behaviors

- Document and visa requirement validation
- Clear hard-block warnings for passport/visa issues
- Agent guidance on next steps
- Policy support for destination-specific compliance
- Failure prevention in booking workflows

## Why this matters

A single visa or passport mistake can ruin a trip and damage the agency’s reputation.
This scenario ensures junior agents are shielded from compliance failures.

## Success criteria

- The system identifies a document check need before quote approval.
- The agent receives a clear warning with next steps.
- The agent does not send a booking recommendation until compliance is verified.
- The customer is not left with an unexpected visa problem.
