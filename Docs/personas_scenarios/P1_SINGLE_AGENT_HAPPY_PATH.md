# P1-S0: Solo Agent Happy Path

**Persona**: Solo Agent (the one-person travel agency)
**Scenario**: The agent wants to process the next incoming trip request quickly, reliably, and without switching between multiple tools.

---

## Situation

A solo travel agent is working a busy morning.
A new customer request has arrived and the agent wants to move it from inbox to proposal as quickly as possible.
The agent is under time pressure and needs the system to behave like a real assistant, not just a collection of pages.

## Goal

Move one trip from inbound request to review-ready proposal in a single coherent flow.
The agent should feel like they are opening a file, processing it, and getting a useful customer-facing package without reinventing the work.

## User flow

### 1. Homepage / dashboard
- Agent opens the app and lands on the homepage.
- They expect to see a snapshot of active work: urgent trips, current pipeline status, and a clear path to the inbox.
- The agent decides which request to work on next.

### 2. Open the inbox
- The agent clicks `Inbox`.
- The inbox shows trip cards with destination, party size, dates, priority/SLA status, and a quick summary.
- The agent expects to see the next request at the top and the ability to open it immediately.

### 3. Select the trip
- The agent clicks the trip card for the request they want to handle.
- The app opens the trip workspace for that exact request.
- The agent expects the workspace to already show the trip reference, destination, and current status.

### 4. Review trip details
- In the workspace, the agent reviews the loaded trip details.
- The trip should display the customer message, party composition, travel window, budget, and any special notes.
- The agent expects no blank screen and no additional manual loading.

### 5. Add or confirm input
- The agent pastes or types the incoming customer note into the “Customer Message” field.
- They add any internal context in “Agent Notes”.
- The agent expects the system to keep this input visible and editable.

### 6. Choose the right mode
- The agent selects the request type:
  - normal request
  - audit
  - emergency
  - cancellation
- The agent expects the selected mode to affect the analysis and output.

### 7. Process the trip
- The agent clicks `Process Trip` or the equivalent action.
- The agent expects the system to analyze the request and return results quickly.
- The app should show progress and then populate downstream sections.

### 8. Inspect pipeline results
- The agent moves through the workspace sections:
  - Trip details / intake packet
  - Decision recommendation
  - Strategy bundle
  - Safety review / traveler-safe output
- The agent expects each section to show real output from the analysis, not placeholders.

### 9. Prepare customer output
- The agent reviews the proposed customer-facing message and the internal summary.
- They expect the customer message to be clean, safe, and aligned with the customer request.
- They expect the internal notes to capture the decision rationale and any follow-up questions.

### 10. Finish and move on
- The agent saves or marks the trip as ready.
- They expect to return to the inbox and handle the next request without losing the previous work.

## Success criteria

The scenario is successful if:
- The agent can open the next request from the inbox.
- The exact trip loads immediately in the workspace.
- The agent can enter or confirm the customer note and agent notes.
- The selected mode is respected.
- Clicking the process button returns structured results.
- The packet, decision, strategy, and safety sections are populated.
- The agent can review the traveler-facing output.
- The agent does not need to switch out of the app or manually stitch results.

## System behaviors required

- **Trip selection persistence**: Inbox click opens the right trip, not a blank workspace.
- **Trip context loading**: Workspace must hydrate the selected trip immediately.
- **Input capture**: Customer and agent notes must stay editable and connected to the processing action.
- **Mode-aware processing**: Request mode must influence the pipeline.
- **Pipeline execution**: The system must run the analysis and return results.
- **Result visibility**: Downstream sections must render actual output.
- **Review-ready output**: The traveler message and internal notes must be usable.

## Why this matters

This scenario is the closest thing to the product’s core promise:
helping a solo agent move from inbound request to a usable proposal in one flow.
If this narrative breaks, the product feels like a prototype instead of a working tool.
