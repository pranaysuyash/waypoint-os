# Trip Visa & Document Risk Scenario

**Date:** 2026-04-15
**Type:** Synthetic document risk investigation note
**Purpose:** Capture one detailed travel scenario whose main risk axis is visas, documents, transit permissions, and entry conditions.

---

## Scenario

- **Destination:** United States + Canada
- **Dates:** 5 November 2026 to 18 November 2026
- **Duration:** 13 nights
- **Group composition:** 2 adults, 1 teen, 1 senior
- **Budget:** ₹7,00,000 total for 4 people
- **Planned itinerary:**
  - 5–9 Nov: New York city stay, museums, Broadway, day trip to Niagara Falls
  - 9–13 Nov: Toronto and Niagara-on-the-Lake, local tours
  - 13–18 Nov: Montreal cultural tour, possibility of a quick Quebec City visit

---

## Input (I/P)

The agent should treat the following as input assumptions for document risk analysis:

1. **Passport status:** Indian passports, no passport expiration details provided in the raw itinerary.
2. **Visa assumptions:** The customer assumes eTA/ESTA may be enough for both the U.S. and Canada.
3. **Transit rules:** The outbound route includes a layover in Doha and the return route includes a transit through Amsterdam.
4. **Entry conditions:** The trip is in November, during potential winter travel disruptions.
5. **Group risk:** A senior traveler is included, so medical insurance and document validity matter more.
6. **Budget note:** ₹7,00,000 may not include visa fees, insurance, or rapid rebooking costs.
7. **Travel behavior:** There are two border-crossing segments (U.S. entry and Canada entry) plus a return via Schengen transit.

---

## Investigation Tasks

The feasibility check should explicitly verify these points.

### 1. Visa & entry requirements

- Confirm whether Indian passport holders need a U.S. visa, Canadian eTA, or both.
- Verify whether any transit visa is required for Doha and Amsterdam layovers.
- Check whether travel through the U.S. to Canada requires a separate Canadian authorization.

### 2. Passport validity

- Confirm the passport validity window required by the U.S. and Canada.
- Determine if the senior or teen passport expiry date must extend beyond the return date.
- Flag if any passport is due to expire within 6 months of departure.

### 3. Insurance and medical documents

- Check whether travel insurance is mandatory for Canadian or U.S. entry under current rules.
- Identify senior-specific medical coverage needs and whether pre-existing condition disclosures matter.
- Flag any documentation needed for COVID, vaccination, or other health entry requirements in November 2026.

### 4. Transit and document handoff risk

- Verify whether the Doha and Amsterdam transfers require a separate transit visa or airport-only transit is permitted.
- Confirm whether the return route through Amsterdam requires Schengen entry conditions even without leaving the airport.
- Check if baggage recheck or separate terminals increases document risk.

### 5. Timing and deadline risk

- If a visa interview or eTA application is required, identify the minimum lead time.
- Flag whether late visa processing could make the itinerary impossible on schedule.
- Estimate whether the current travel dates leave enough time for all document clearance steps.

### 6. Alternative recommendation

- If the plan is document-risk heavy, suggest a safer single-country itinerary or a later departure date.
- Work from the same core goal (North America trip) but reduce border complexity.

---

## Expected Output (O/P)

The evaluator should return a clear verdict with these elements:

1. `verdict`: `realistic` | `borderline` | `not realistic`
2. `document_risks`: list of identified risks such as `US visa required`, `Canada eTA uncertain`, `transit visa gap`, `passport validity`, `insurance omission`.
3. `critical_changes`: concrete document and timing actions to take.
4. `must_confirm`: the exact items to verify before the quote is firm.
5. `alternative`: one lower-risk itinerary option if the current plan is too risky.

Example structure:

- `verdict`: `borderline`
- `document_risks`: [`US visa required`, `Canada eTA unclear`, `Doha transit visa`, `passport 6-month rule`, `insurance not confirmed`]
- `critical_changes`: ["Verify U.S. tourist visa requirement for each traveler", "Confirm Amsterdam transit rules for Indian passport holders", "Add travel insurance with senior coverage before booking"]
- `must_confirm`: [`passport expiry dates`, `visa application timelines`, `airline transit visa policy`, `insurance policy wordings`]
- `alternative`: `Single-country Canada trip with return via non-Schengen transit`

---

## Notes

- This scenario is designed to force the agent to surface document and visa uncertainty, not just travel preference.
- It should treat border crossings and transit permissions as first-class risk buckets.
- The backend currently tracks visa risk at a high level, but this scenario expects deeper evidence and timeline reasoning.

---

## Investigation Result

- `verdict`: `borderline`
- `document_risks`: [`US visa required`, `Canada eTA not confirmed`, `Amsterdam transit rule unclear`, `passport validity unknown`, `insurance gap`]
- `critical_changes`:
  1. Confirm whether each traveler can apply for a U.S. B1/B2 visa or needs a visa interview.
  2. Verify whether the Canada eTA is valid after U.S. entry and before return.
  3. Check whether the Amsterdam transit requires Schengen entry permission or passport stamping.
  4. Add a senior-friendly travel insurance policy and confirm medical coverage limits.
- `must_confirm`: [`passport expiry dates`, `U.S. visa category and timeline`, `Canada eTA eligibility`, `Doha and Amsterdam transfer visas`, `travel insurance premium`]
- `alternative`: `Single-country Canada itinerary via a direct Doha mainline return, removing Schengen transit complexity.`
