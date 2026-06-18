# Travel Agency Agent Live Simulation - 2026-06-17

## Scenario

Persona: frontline travel agent

Simulation goal:

- start a brand-new inquiry
- capture the customer request
- process it into the workflow
- resolve missing details
- continue the trip as far as the current product allows

Verification context:

- frontend: `http://localhost:3100`
- backend: `http://localhost:8000`
- live browser simulation run against the repo-started app
- authenticated agent flow using the documented test account

Live simulation path:

1. Sign in
2. Open `New Inquiry`
3. Paste a realistic customer request
4. Submit with `Process Inquiry`
5. Review blocked-validation state
6. Open `Trip Details`
7. Try recovery via `Fix in Intake`
8. Re-submit with more explicit structured details
9. Judge how far the agent can actually push the trip in one session

## Simulation 1: Natural agent note

Input used:

```text
Please plan a 6-night Bali trip for a couple traveling from Bengaluru from 12 October to 18 October. Budget is INR 3.5 lakh total including flights and hotel. They want a beachfront 5-star resort, one easy day trip, private transfers, vegetarian-friendly dining, and a relaxed pace. They do not want too many hotel changes.
```

What happened:

- `Process Inquiry` submitted successfully
- the draft was created
- the run completed structurally
- the app returned a blocked state instead of progressing into a real planning workflow

Observed state:

- draft created, for example: `draft_0feac924d8e2`
- run API returned `200`
- workbench switched into:
  - `Blocked`
  - `Trip Details Need Attention`
  - `Structural validation failed (1 error)`

What the agent sees next:

- `Fix Missing Details`
- `Show run details`
- `Trip Details` tab

Trip Details diagnostics included:

- missing `Origin City`
- missing `Travel Dates`
- missing `Party Size`
- missing `Trip Purpose`

What felt good:

- no crash
- no lost work
- the diagnostic panel is real and specific
- the system does tell the agent what it thinks is missing

What felt weak:

- the agent wrote a perfectly normal customer summary, but the system still behaved as if core basics were absent
- the recovery path is diagnostic-first, not action-first
- the agent is pushed back into rewriting intake instead of smoothly editing the extracted trip

## Simulation 2: Recovery through intake rewrite

Recovery action:

- click `Fix Missing Details`
- review `Trip Details`
- click `Fix in Intake`
- rewrite the message with more explicit structured fields

Improved input used:

```text
Please plan a 6-night Bali honeymoon.
Origin city: Bengaluru.
Travel dates: 12 October 2026 to 18 October 2026.
Party size: 2 travelers.
Trip purpose: honeymoon leisure trip.
Budget: INR 3.5 lakh total including flights and hotel.
Preferences: beachfront 5-star resort, private transfers, vegetarian-friendly dining, relaxed pace, no too many hotel changes.
```

What happened:

- the agent could return to intake without losing the draft
- resubmission worked
- the second run still blocked

Observed result:

- party size was finally extracted
- trip purpose was finally extracted
- but origin and dates still remained missing
- destination/origin ambiguity appeared:
  - `Destinations: Bali, Bengaluru`
  - `Raw: Bali or Bengaluru`

What felt good:

- recovery happens inside the same workbench
- draft continuity is real
- the app does provide a loop rather than forcing a fresh restart

What felt weak:

- the agent has to learn how to write for the parser
- adding more explicit structure still did not unlock the trip
- the system can misclassify origin as destination, which is costly in a real agent workflow

## Simulation 3: Machine-friendly structured format

Most structured input tested:

```text
Trip request
Destination: Bali
Origin city: Bengaluru
Travel start date: 2026-10-12
Travel end date: 2026-10-18
Party size: 2
Trip purpose: honeymoon
Budget: INR 350000 total
Preferences: beachfront 5-star resort, private transfers, vegetarian-friendly dining, relaxed pace
Constraint: avoid too many hotel changes
```

What happened:

- submission still returned a blocked state
- the workbench did not progress beyond the same blocked-intake pattern

What this means:

- this is not only a “customer writes vaguely” problem
- even a fairly parser-friendly format still does not reliably create a usable next-stage trip from the agent workbench

## Journey Map

### Stage 1: Capture a new lead

- Goal: convert raw inquiry into active workflow
- Outcome: partial success
- Emotional state: focused -> encouraged

Why:

- the form works
- submit works
- the draft persists

### Stage 2: Review the first result

- Goal: see the trip become actionable
- Outcome: partial failure
- Emotional state: encouraged -> interrupted

Why:

- the system blocks early
- the next move is recovery, not continuation

### Stage 3: Recover the inquiry

- Goal: fill missing basics and continue
- Outcome: mixed
- Emotional state: interrupted -> effortful

Why:

- the app explains what is missing
- but the actual fix path is “rewrite the intake” rather than “edit the trip”

### Stage 4: Progress to planning

- Goal: reach options / quote / next real planning stage
- Outcome: not achieved in this live simulation
- Emotional state: effortful -> skeptical

Why:

- repeated reprocessing still did not unlock the trip reliably

## Good Stuff

- New Inquiry route works
- `Process Inquiry` works
- drafts persist
- blocked runs do not destroy work
- `Trip Details` diagnostics are visible and concrete
- the workbench gives the agent a recovery loop rather than a dead end

## Gaps

- a normal agent summary is not reliably enough for the parser
- the agent must compensate for extraction fragility
- the main recovery tool is re-authoring intake text, not structured field repair
- even more explicit re-entry can still fail
- origin/destination ambiguity is a serious agent-flow issue
- the agent could not reach a confident “continue to options” state in this simulation

## Time Savers

- as an agent, I can start from a clean inquiry screen quickly
- as an agent, I do not lose work when the run blocks
- as an agent, I get specific prompts for what the system thinks is missing

## Time Wasters

- as an agent, I have to translate a valid customer brief into parser-friendly phrasing
- as an agent, I may need multiple submit/review/rewrite cycles before the product understands basic fields
- as an agent, I am diagnosing the system instead of advancing the trip
- as an agent, blocked recovery still feels like authoring around the model rather than collaborating with the tool

## Workarounds

- write more explicitly than you normally would in customer-facing notes
- separate destination, origin, dates, party size, and trip purpose into very distinct lines
- treat the first blocked run as an extraction check, not as the start of actual planning
- use `Trip Details` as a diagnostic report, then fix via intake rewrite

## Bottom Line

This agent flow is not broken in the old sense of dead routes or crashing pages.

It is broken in a more workflow-specific sense:

- the app accepts the work
- preserves the draft
- returns diagnostics
- but does not yet let the agent move smoothly from “new lead” to “usable planning trip”

Clean agent verdict:

- inquiry capture: works
- submission: works
- draft continuity: works
- diagnostic recovery: exists
- reliable progression to planning: weak

The biggest agent-facing opportunity is:

- reduce the need to rewrite for the parser
- make missing-detail repair more structured and less text-authoring heavy
- ensure a well-specified inquiry reliably becomes a usable trip without multiple retries
