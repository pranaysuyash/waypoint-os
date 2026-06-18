# Travel Agency Agent Live Simulation

Date: 2026-06-17

## Scenario

I simulated a single agency owner/agent handling a new family trip from start to finish inside the authenticated app.

Traveler request used:
- Family of 5
- San Francisco to Singapore
- May 24 to May 29
- Two adults, two grandparents, one toddler
- Comfortable pace
- Minimal long walks
- Marina Bay Sands, Universal Studios, Sentosa
- Budget around USD 8,000

Trip created during the simulation:
- `trip_6ba997f7a5c4`

## Full Flow Tested

1. Logged in to the authenticated agency app.
2. Opened the agency overview surface.
3. Entered the `New Inquiry` workbench.
4. Entered traveler-facing request text and internal agent notes.
5. Processed the inquiry into a trip.
6. Opened the generated trip workspace.
7. Reviewed the intake summary, missing fields, and follow-up guidance.
8. Tested budget entry and checked whether the trip reflected the saved budget.
9. Re-loaded the trip workspace to see whether the saved value was visible to the agent.

## Live Path

1. Signed in to the agency app.
2. Opened `New Inquiry`.
3. Entered the traveler request and agent notes.
4. Processed the inquiry into a trip workspace.
5. Opened the generated trip.
6. Reviewed the intake screen, missing details, and follow-up prompt.
7. Verified the budget field path and the trip refresh behavior.

## What Worked Well

- The app recognized the agency workflow immediately after login.
- The workbench clearly separated traveler-facing input from agent-only notes.
- The trip workspace surfaced the next missing item in plain language.
- The missing-details panel was actionable:
  - It named the blocker.
  - It showed the exact question to ask the traveler.
  - It offered a direct `Add budget` path and a `Draft follow-up` path.
- The trip summary was easy to scan:
  - destination
  - party size
  - dates
  - current state
- The app made it obvious that budget is the gate before quote building.
- The trip workspace gave the agent a usable next action instead of a dead end.
- The app did not force the agent to invent the follow-up wording from scratch.

## Where The Agent Gets Stuck

- Budget remains the main blocker when it is not fully captured.
- In the live session, the trip workspace still showed `Budget missing` after the budget entry flow.
- That means an agent can do the right thing and still not get obvious visual confirmation that the trip moved forward.
- The app needs a clearer “saved successfully” moment for this key field.

## Observed Evidence

- The trip workspace showed:
  - `Need Customer Details`
  - `Confirm budget range before building options`
  - `Add budget range`
  - `Draft follow-up`
- The trip details panel showed:
  - origin
  - destination
  - type
  - party size
  - dates
  - `Budget missing`
- The missing-details panel explicitly called out:
  - `Budget range` as required
  - `Trip priorities / must-haves` as recommended
- The app gave a direct prompt for the traveler:
  - `What budget range should we plan within?`

## Time Savers

- The app already tells the agent what to ask next instead of leaving them to infer it.
- The follow-up prompt is directly usable in a customer message.
- The trip summary is compact enough that an agent can confirm the whole trip in one screen.
- The budget editor is simple and keeps the user on the same workflow surface.
- The app makes the blocker and the next move visible without needing a separate help article.

## Time Wasters

- Having to re-check whether the budget actually stuck after entering it.
- Having to refresh or cross-check the trip state after the save interaction.
- Ambiguous state between “saved locally” and “visible in the trip workspace.”
- When the workspace still says `Budget missing`, the agent has to stop and verify whether the app or the data changed.

## Practical Workarounds

- If the trip still shows “Budget missing,” refresh the trip workspace before assuming the save failed.
- If the trip does not visually update, verify the trip through the trip summary and not just the editor state.
- If budget is still unresolved, use the app’s `Draft follow-up` action immediately and move the trip forward with a traveler question.
- If the UI does not confirm the save clearly, use the trip summary or API readback as a secondary check before continuing.

## Bottom Line

- The agent workflow itself is understandable and usable.
- The app’s strongest part is how clearly it tells the agent what is missing and what to ask next.
- The main friction is confidence: the agent needs a stronger, more obvious confirmation that a budget entry has actually been accepted and reflected in the trip workspace.
- This is a product workflow issue, not just a copy issue.
- The app is close to the right shape, but the save-and-confirm loop for budget needs to feel reliable.

## Second Pass: UX / Features / Agents

### UX

What is good:
- The shell is organized around an agency operating model, not a generic dashboard.
- The left nav makes the product scope legible:
  - Command
  - Planning
  - Operations
  - Intelligence
  - Admin
- The trip workspace uses strong status language:
  - current trip state
  - stage rail
  - missing details
  - suggested next move
- The right action is usually visible on the same screen as the problem.

What is weak:
- There is still too much visual weight on explanatory panels when the agent just needs a clear answer to:
  - what is missing?
  - what should I do next?
  - did my save take?
- Some labels are product-accurate but still a little internal-feeling:
  - `Need Customer Details`
  - `In planning`
  - `Budget missing`
- The UI asks the agent to infer too much when a save action succeeds or fails.
- The trip workspace can feel dense when the agent is trying to finish a single blocking task.

### Features

What is good:
- The product has a sensible end-to-end workflow:
  - intake
  - follow-up
  - planning
  - review
  - output
- The missing-details system is genuinely useful because it creates a clear working queue.
- The follow-up prompt generation is a real time saver.
- The stage model is consistent with the agency process.

What is missing or underpowered:
- Strong success confirmation for field saves, especially budget.
- A clearer “what changed” diff after edits.
- More visible progress from intake to next stage when the app has enough information.
- Better closed-loop feedback after follow-up drafting.
- More explicit saved-state indicators on key fields like budget, dates, and origin.

### Agents / Operating Model

What is good:
- The app does not blur the agency operator and traveler roles.
- It keeps internal notes and traveler-facing text separate.
- The app supports a real agent workflow:
  - capture
  - qualify
  - ask follow-up
  - resolve blockers
  - continue planning
- The product already assumes the agent is making judgment calls, not just filling forms.

What needs hardening:
- The app should make the agent’s current responsibility sharper:
  - are they still qualifying?
  - are they planning?
  - are they ready to quote?
- The agent needs more obvious state transitions after each meaningful action.
- The system should make it harder to lose confidence in a completed save.
- The “agent model” is present, but the UI should reinforce it with less ambiguity and fewer unlabeled transitions.

### Operational Suggestions

- Keep the command surface compact.
- Make the save confirmation for budget unmistakable.
- Prefer direct next-step CTAs over long explanatory blocks in blocking states.
- Keep internal and traveler wording distinct.
- Use the trip workspace to answer the agent’s immediate question before adding more context.

### Product Verdict

- The app is structurally on the right path.
- The current UX is better at explaining the process than at closing the loop after action.
- The feature set is coherent, but the feedback loop for critical edits still needs tightening.
- The agent model is good; the confidence model around state changes is not yet strong enough.

## Third Pass: Multi-Agency Scenario Matrix

I ran a second live batch to compare the same app flow across five agency shapes:

- small agency
- big agency
- Indian agency
- African agency
- global agency

This was tested live through `POST /run` and then by opening each resulting trip workspace in the browser.

### Live Run Summary

- Small agency, concise trip facts: `completed`, `trip_14d1b665e47a`
- Big agency, concise trip facts: `completed`, `trip_7c77aaed3182`
- Indian agency, concise trip facts: `completed`, `trip_f61082c5bd89`
- African agency, concise trip facts: `completed`, `trip_dd7007f8a0a1`
- Global agency, concise trip facts: `completed`, `trip_e3a84ef55b5a`

I also tried a more verbose version of the same scenarios first. Those runs mostly stopped at `extraction_quality`, which is itself useful signal: the app is much happier when the traveler facts are crisp and linear than when the prompt mixes profile detail with the trip request.

### Scenario 1: Small Agency

Profile used:
- Boutique 3-agent agency
- One operator handling most work
- Low volume, high-touch

What the app did well:
- It produced a clear trip title and a readable stage summary.
- It kept the next action simple: confirm budget and origin.
- The missing-details panel was easy to understand and acted like a working checklist.

What was weak:
- The trip still landed in a generic follow-up state instead of something that felt tailored to a one-person shop.
- The UI does not yet explicitly say, “you are a tiny team, so here is the fastest path.”

Time saver:
- The app tells the operator exactly what to ask next.

Time waster:
- If the agency expects the app to infer the office workflow, it does not. The operator still has to mentally map the generic trip state to a tiny-team workflow.

Workaround:
- Keep the raw note very short and trip-specific.
- Use the missing-details card as the source of truth for the next move.

### Scenario 2: Big Agency

Profile used:
- 60-agent multi-branch agency
- Queue-heavy operations
- Manager cares about routing and SLA visibility

What the app did well:
- It still produced a usable trip record and clear missing-detail guidance.
- The workspace stayed stable even when the scenario implied more operational complexity.

What was weak:
- The current workspace does not yet show a true big-agency operating model.
- There was no visible evidence of assignment routing, queue depth, or manager-level triage in the trip workspace itself.
- The first pass of this scenario was also sensitive to extraction quality; if the note gets too elaborate, the pipeline stops earlier.

Time saver:
- The app creates a single clear trip object instead of forcing the team to disentangle a big freeform note.

Time waster:
- A large agency would still need another layer for routing and queue management. Right now the trip workspace is still mainly a single-thread operator view.

Workaround:
- Keep the intake request fact-first.
- Treat scale routing as a downstream operating concern, not as something the trip editor will infer automatically.

### Scenario 3: Indian Agency

Profile used:
- Bengaluru-based agency
- Family travel
- INR budgets
- School-holiday timing

What the app did well:
- This was the cleanest regional fit in the batch.
- The app recognized destination, party size, and month cleanly.
- It produced a very direct missing-field prompt: origin city.

What was weak:
- The workspace still stayed generic; it did not surface any India-specific handling advantages beyond the phrasing of the trip.
- The app did not infer the origin city from the surrounding context, so the operator still has to ask.

Time saver:
- The prompt to the traveler is precise and immediately reusable.

Time waster:
- The app does not turn “Indian family trip” into richer locale-specific defaults yet.

Workaround:
- Ask origin city first.
- Keep INR budgets and family size explicit in the first note, because that dramatically improves the plan state.

### Scenario 4: African Agency

Profile used:
- Nairobi-based agency
- Safari plus honeymoon style trip
- Mobile-first communication
- Mixed route and transfer complexity

What the app did well:
- It preserved the destination and timing clearly.
- It still gave a clean planning start instead of collapsing under a more complex regional use case.

What was weak:
- The current workspace does not yet express safari complexity, road-transfer effort, or cross-border routing in a strong enough way.
- Budget handling was less robust here than in the Indian case.

Time saver:
- The app at least creates a usable trip skeleton from the note.

Time waster:
- The operator still has to manually translate “safari and Zanzibar” into a fuller transfer-and-logistics checklist.

Workaround:
- Use one clean line for destination and dates.
- Add budget and origin in the same note if you want the plan to move forward without back-and-forth.

### Scenario 5: Global Agency

Profile used:
- London, Dubai, Singapore operating footprint
- Multi-currency
- Multi-time-zone
- Multi-language handoff

What the app did well:
- It handled the basic trip extraction path and produced a stable workspace.
- The follow-up prompt remained straightforward instead of becoming overcomplicated.

What was weak:
- The current UI does not yet show timezone, language, or handoff traceability as first-class concerns.
- Multi-currency and global handoff complexity are not surfaced as operational signals in the trip workspace.

Time saver:
- Even with a global profile, the app still gives a simple next step.

Time waster:
- Global agency context is mostly invisible once the trip lands in the workspace.

Workaround:
- Keep the trip request itself short and factual.
- Put any global-operating-model detail in internal notes, not in the traveler-facing request.

### Cross-Scenario Readout

What is good:
- The app is consistent.
- It reliably converts a clear travel request into a trip workspace.
- The missing-details UI is practical and action-oriented.
- The follow-up prompt is one of the strongest parts of the product.

What is bad:
- The app is still quite sensitive to extraction shape.
- If the prompt gets too narrative or mixes too much operational context into the trip request, the run can stop at `extraction_quality`.
- Large-agency, Indian, African, and global workflows are all currently squeezed through the same generic trip workspace.
- Party parsing is strongest when the note says `family of 4`; it is weaker for softer phrasing like `two executives` or `couple`, which is why those scenarios landed as `1 pax` in the workspace.

What to remember:
- Small agency = speed and clarity matter most.
- Big agency = routing and queue visibility are the missing layer.
- Indian agency = family + INR + holiday timing is a strong fit, but origin still matters.
- African agency = logistics complexity is underrepresented.
- Global agency = time zones, multi-currency, and language handoff are underrepresented.
- Family-style intake is the safest default phrasing today if you want the system to extract party size reliably.

### Practical Product Gaps

- The workspace needs stronger agency-shape signaling.
- The app should preserve the same trip flow, but it should also adapt the operational framing for different agency sizes and regions.
- The app should expose when it is operating as a single-operator workbench versus a multi-agent queue.
- Regional patterns should become first-class planning hints, not just incidental wording in a note.

### Best Workaround Today

- Use short, fact-dense trip notes.
- Put the traveler facts first.
- Use internal notes only for agency context.
- Treat missing origin and missing budget as the two fastest blockers to clear.
- In the live browser clickthrough, `View Trip` from the processed workbench draft opened a real trip workspace with the expected missing-details panel, so the correct handoff path is the post-process button rather than guessing the draft URL directly.

## Prioritized Issue List

This is split by pass so the action items stay tied to the exact behavior that produced them.

### Pass 1: Single Agency Owner / Agent

1. P1 - Save confirmation is too weak for budget edits.
   - User impact: the agent cannot tell whether the budget actually stuck after editing it.
   - Why it matters: budget is the main gate before quote building, so uncertainty here blocks momentum.
   - Best fix direction: show an unmistakable saved state on the trip workspace and in the field editor.

2. P1 - The workspace still reads `Budget missing` after the save flow.
   - User impact: the agent has to refresh or re-check the trip to regain confidence.
   - Why it matters: the app is asking for a second verification step immediately after the edit.
   - Best fix direction: sync the displayed trip state immediately after a successful save.

3. P2 - The blocking copy is accurate but still feels internal.
   - User impact: the agent has to translate `Need Customer Details` and `In planning` into a real workflow state.
   - Why it matters: a busy operator needs the next move, not only the status label.
   - Best fix direction: make the state label and next action more operationally explicit.

4. P2 - The save-and-confirm loop is too easy to miss.
   - User impact: the agent may continue working without knowing whether the previous action was accepted.
   - Why it matters: this creates unnecessary re-checks and friction.
   - Best fix direction: add a visible diff or acknowledgement after key field edits.

5. P3 - The trip workspace is denser than needed for a single blocking task.
   - User impact: the agent has to scan explanatory panels when they mostly want the next action.
   - Why it matters: density slows down the simplest handoff loop.
   - Best fix direction: reduce explanation weight in blocking states and elevate the CTA.

### Pass 2: Multi-Agency Scenario Matrix

1. P1 - Extraction quality is fragile when the intake note becomes narrative.
   - User impact: verbose agency descriptions can stop the run before a trip is created.
   - Why it matters: this blocks real intake on more complex or less structured messages.
   - Best fix direction: improve tolerance for mixed context, or guide users toward a structured intake pattern.

2. P1 - Party parsing is weak for softer phrasing.
   - User impact: `two executives` or `couple` can land as `1 pax`.
   - Why it matters: party size is core trip data, and wrong extraction damages downstream planning.
   - Best fix direction: teach the extractor to infer passenger count from more natural phrasing.

3. P1 - The workspace does not adapt to agency shape.
   - User impact: small, big, Indian, African, and global agencies all land in the same generic trip view.
   - Why it matters: different operating models need different cues.
   - Best fix direction: expose agency-size and regional operating signals in the trip workspace.

4. P2 - Big-agency routing and queue visibility are missing.
   - User impact: a 60-agent agency still looks like a single-thread operator view.
   - Why it matters: large teams need assignment, triage, and SLA visibility.
   - Best fix direction: add a routing layer or at least queue metadata in the workspace.

5. P2 - Regional planning hints are too thin.
   - User impact: Indian, African, and global workflows all require manual translation into working assumptions.
   - Why it matters: the product is not yet using market shape as a planning advantage.
   - Best fix direction: surface locale-specific hints for INR, safari/logistics, time zones, and multi-language handoff.

6. P3 - The app is strong at fact capture but weak at operational framing.
   - User impact: the trip is captured, but the team still has to decide how to run it.
   - Why it matters: this is a lost opportunity to turn the product into a real agency operating system.
   - Best fix direction: keep the same core trip flow, but add agency-shape overlays and smarter defaults.

### Cross-Pass Theme

- The product is already good at getting to a usable trip object when the request is short and factual.
- The biggest gap is not raw capture, it is confidence and framing.
- The agent needs the app to say not only `what is missing`, but also `what kind of agency work this is`.
- The more the workflow looks like a real operating system, the more useful it becomes for both small teams and larger agencies.
