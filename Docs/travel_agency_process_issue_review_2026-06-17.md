# Travel Agency Process Issue Review - 2026-06-17

## Scenario

Persona: agency owner

Simulation goal:

- Start the day as an owner/operator
- identify the most urgent work
- open a real trip from the queue
- start a brand-new inquiry
- judge whether the product helps move work forward without confusion

Live simulation path:

1. Sign in at `http://localhost:3100/login`
2. Sign in with the documented test account flow
3. Owner overview at `/overview`
4. Lead Inbox at `/inbox`
5. Direct trip route compatibility check at `/trips/trip_163e9879af9a`
6. Lead Inbox row `View` CTA / direct trip route at `/trips/trip_3d151aa7bf80/intake`
7. New Inquiry route via `/workbench?draft=new&tab=intake&capture_mode=call&entry=new`
8. Stale bookmarked path `/trips/new/intake?capture_mode=call&entry=new`
9. Submit a fresh inquiry from the New Inquiry workbench

Code-grounded simulation path:

1. Read route helpers in `frontend/src/lib/routes.ts`
2. Read trip workspace layout in `frontend/src/app/(agency)/trips/[tripId]/layout.tsx`
3. Read overview action builder in `frontend/src/app/(agency)/overview/buildActionRequiredItems.ts`
4. Read workbench redirect behavior in `frontend/src/app/(agency)/workbench/PageClient.tsx`
5. Read backend trip serialization in `spine_api/contract.py`

Verification context:

- Frontend dev server used for the validated run: `http://localhost:3100`
- Backend dev server used for the validated run: `http://localhost:8000`
- Both servers were started from this repo for the final pass
- Backend health: `http://localhost:8000/health` returned `ok`
- `http://localhost:3100/login` returned `200`
- Browser simulation was run against the live app with Playwright
- Cookie-authenticated proxy verification was also run directly against the frontend API routes

Correction:

- `http://localhost:3000` on this machine is a different app (`VerseSignal`), so it is not part of this repo’s validation surface.
- `http://localhost:3004` on this machine was a VS Code live preview server for a different local folder, not this app.
- The validated travel_agency_agent frontend for this review is the repo-started Next.js server on port `3100`.

## Pass 4 Execution Add-on

- Focus: finish remaining implementation around operator pain points after initial route/state fixes.
- Validation run completed live via:
  - `http://localhost:3100/workbench?draft=new&tab=intake&capture_mode=call&entry=new`
  - `POST /api/public-checker/run` + `/api/public-checker/{trip_id}/export` + `/api/public-checker/{trip_id}` on authenticated API proxy
  - Targeted frontend verification of blocked-state copy and run-progress wording

### Pass 4 Outcomes

- Workbench blocked validation messaging now frames the state as recoverable (draft preserved, continue in Trip Details) rather than a terminal failure.
- Blocked-run card CTAs now guide a concrete continuation action.
- Public-checker export/delete flow remains usable in anonymous runs in this verification cycle.

## Clean Simulation

### Scenario 1: Morning owner triage

What I am trying to do:

- open the system
- understand what is urgent
- decide where to start

What happened:

- sign-in worked immediately
- overview loaded with strong urgency framing
- the page made it obvious that enquiries are piling up and need action
- the queue counts and SLA framing helped answer the owner question: "where is the fire right now?"

What felt good:

- strong first screen for operational awareness
- clear prioritization language
- owner can quickly see that enquiries are the biggest pressure point

What felt weak:

- the page is strong at surfacing urgency, but weaker at converting that urgency into a single obvious "start here now" next move
- depending on which card is visible first, the owner may still need a second step of interpretation

### Scenario 2: Open a real trip from the queue

What I am trying to do:

- go from queue to actual work
- open a real trip
- understand what is missing
- continue the trip

What happened:

- inbox loaded well
- row-level `View` actions were easy to understand
- a previously broken trip route now opens successfully
- the trip workspace shows exactly what is missing, such as budget and origin

What felt good:

- moving from inbox to trip is now viable
- trip page explains missing information in practical terms
- the system gives a useful next step instead of a dead end

What felt weak:

- the trip opens into a "needs details" state that is useful, but still a little heavy
- the owner can see what is missing, but the page could be even more action-oriented in how it guides the next outreach

### Scenario 3: Use an old bookmark or stale link

What I am trying to do:

- click an older saved link
- continue work without caring about route structure

What happened:

- `/trips/{id}` now redirects to the canonical intake page
- `/trips/new/intake` now redirects back to the current workbench flow

What felt good:

- stale links no longer punish the operator
- the product feels more forgiving

What felt weak:

- none serious in this scenario after the fix

### Scenario 4: Start a brand-new inquiry

What I am trying to do:

- capture a fresh lead quickly
- submit it
- continue the workflow

What happened:

- New Inquiry opened correctly
- I entered a realistic honeymoon request
- submit created a draft and ran the backend flow successfully
- instead of breaking, the app returned a blocked validation state and preserved the work

What felt good:

- no dead route
- no crash
- draft is preserved
- the system clearly signals that more details are needed before planning can continue

What felt weak:

- the first post-submit moment feels more like "you failed validation" than "here is the fastest way to complete this inquiry"
- this is now a workflow-guidance problem, not a broken-app problem
- for an owner or agent in a hurry, this moment still creates friction

## Good Stuff

- The sign-in flow works cleanly on the repo-started frontend.
- The owner overview does a good job surfacing urgency:
  - counts for trips in planning, enquiries, and quote review
  - direct calls to action for the oldest enquiry and open enquiries
  - visible operational sections in the left nav
- The Lead Inbox is genuinely useful:
  - priority-based sorting
  - visible SLA/status metadata
  - direct `View` links on each lead row
  - clear filter tabs for Operations, Team Lead, Finance, and Fulfillment
- The stale route compatibility fixes now behave correctly:
  - `/trips/trip_163e9879af9a` redirects to `/trips/trip_163e9879af9a/intake`
  - `/trips/new/intake?capture_mode=call&entry=new` redirects to `/workbench?draft=new&tab=intake&capture_mode=call&entry=new`
- The previously failing trip payload now loads through the authenticated frontend API after the backend restart:
  - `/api/trips/trip_3d151aa7bf80` returned `200`
  - `/trips/trip_3d151aa7bf80/intake` rendered the intake workspace instead of `Workspace unavailable`
- The New Inquiry entry point no longer dead-ends:
  - `/workbench?draft=new&tab=intake&capture_mode=call&entry=new` stays on the workbench
  - submitting a fresh inquiry creates a draft and returns a blocked-validation state instead of a broken route

## Gaps

- A freshly submitted inquiry still produces a sharp validation wall:
  - the app creates draft `draft_cbe523da6b7c`
  - `POST /api/spine/run` returned `200`
  - the run is surfaced as `Blocked`
  - the page tells the operator to check `Trip Details`, but the initial landing state still feels more like a failure than guided continuation
- The overview CTA issue is fixed at the route layer, but the overview page did not expose a stable `Open trip` item during this rerun because the top CTA set was dominated by enquiry-level links.
- The owner experience still depends on backend validation being very legible:
  - after submit, the operator sees `Structural validation failed (1 error)`
  - that is technically correct, but not yet as coaching-oriented as it could be for a fast intake workflow
- The protected shell still performs a lot of background loading and can briefly show loading-heavy states before settling.

## Time Savers

- As an owner, the overview gives a fast sense of where team attention is needed.
- As an operator, the inbox `View` action gets me into a live trip quickly.
- As a returning user, old links and bookmarks now recover instead of failing.
- As someone handling a new lead, draft preservation saves me from retyping or restarting after submit.

## Time Wasters

- As an owner, I can see urgency quickly, but I still have to interpret which action is the true best next move.
- As an agent, opening a trip tells me what is missing, but it still takes effort to convert that into the next concrete customer follow-up.
- As someone starting a fresh inquiry, the blocked state after submit slows momentum because the experience becomes corrective too early.
- As a busy operator, "validation failed" is accurate language, but it is not yet the most supportive workflow language.

## Workarounds

- If I am triaging the day, start from Overview for prioritization and then jump into Inbox for execution.
- If I need to continue a trip, use the trip intake workspace as the source of truth for what information is missing.
- If a lead is incomplete, treat the blocked result as a saved checkpoint rather than a failed attempt, because the draft now survives.
- If older team SOPs or bookmarks still point to stale paths, they are now safe to use because the product redirects them to the current flow.

## Bottom Line

The corrected live run is materially better than the original broken pass:

- overview works
- inbox works
- `/trips/{id}` compatibility now works
- the formerly failing inbox trip now opens after the backend restart
- the stale `/trips/new/intake` path now resolves back to the workbench
- urgency cues work
- a fresh New Inquiry can be submitted and preserved as a draft

From the owner persona point of view, the product is now usable for triage and continuation. From the agent/operator point of view, the remaining friction is mostly about workflow tone and guided recovery, especially right after submitting a new inquiry.

So the cleaner simulation verdict is:

- triage works
- queue-to-trip continuation works
- stale links recover
- new inquiry works structurally
- the remaining weakness is that incomplete inquiries still feel corrected rather than coached

## Owner Journey Map

### Stage 1: Arrive and orient

Goal:

- understand the state of the business quickly

What the owner sees:

- clear operational shell
- counts for trips, enquiries, and quote review
- urgency-heavy language

Good:

- strong situational awareness
- fast understanding of where pressure is building

Gap:

- the owner still has to decide which exact action is the best immediate move

Time saver:

- overview compresses a lot of operational context into one screen

Time waster:

- deciding between multiple urgent-looking actions still takes a moment of interpretation

### Stage 2: Move from awareness to action

Goal:

- open live work from the queue

What the owner sees:

- inbox rows with priorities, SLA pressure, and a `View` action

Good:

- queue feels real and actionable
- continuation into a trip now works

Gap:

- the product is better at showing what is wrong than driving the fastest business follow-up sequence

Time saver:

- direct queue-to-trip transition

Time waster:

- the owner still needs to translate "missing details" into a concrete outbound step mentally

### Owner summary

- strong dashboard for operational visibility
- decent continuation into real work
- main opportunity is sharper action design, not core stability

## Agent Journey Map

### Stage 1: Pick up a lead

Goal:

- open an assigned or urgent lead and continue it

What the agent sees:

- inbox row
- trip intake page
- missing information summary

Good:

- trip workspace now loads instead of breaking
- missing details are visible and practical

Gap:

- the system says what is missing, but does not yet feel maximally assistive in composing the next customer outreach

Time saver:

- no more route dead-end
- saved drafts prevent total restart

Time waster:

- blocked or incomplete states still create a context-switch into problem-solving mode too early

### Stage 2: Start a new inquiry

Goal:

- move fast from raw message to active workflow

What the agent sees:

- clean New Inquiry surface
- ability to paste the customer message and notes
- saved draft after submit

Good:

- the new inquiry route works
- the draft survives
- the system does not lose work

Gap:

- the first blocked state is structurally correct but emotionally abrupt

Time saver:

- preserved draft and visible next tab

Time waster:

- agent momentum slows when the submit moment feels like correction instead of progression

### Agent summary

- reliable enough to work in now
- biggest improvement area is guided recovery and coaching language after submit

## Customer Journey Map

### Stage 1: Discover the itinerary checker

Goal:

- understand whether this is useful before talking to an agent

What the customer sees:

- a clear, free, no-sign-up checker
- multiple input modes
- strong promises around clarity, friction spotting, and sharing

Good:

- very good top-of-funnel positioning
- clear value proposition
- low-friction entry

Gap:

- the experience is strongest in the promise layer; the live submission path was not the focus of this simulation, so the main validated strength here is entry clarity rather than full report depth

Time saver:

- customer immediately understands what the tool is for

Time waster:

- none obvious at landing; the main unknown is deeper report experience, not entry friction

### Customer summary

- strong acquisition and trust-building surface
- good self-service framing
- worth a dedicated deeper traveler simulation later

## Scenario Table

| Scenario | Persona | Goal | What worked | Main gap | Workaround | Time saver | Time waster |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Morning triage | Owner | Find the most urgent work | Overview makes urgency clear | Best next action is not always singularly obvious | Start on Overview, then move to Inbox for execution | Fast operational awareness | Small interpretation step before acting |
| Open a real trip | Owner / Agent | Continue work on a live lead | Inbox-to-trip path works and trip page loads | Missing-details state could guide next outreach better | Use trip intake page as the source of truth for next follow-up | Direct `View` action | Turning missing data into the next customer message still takes effort |
| Use stale bookmark | Owner / Agent | Continue from an old link | Redirects now recover correctly | No major remaining gap in this slice | Keep old SOP links; redirects are now safe | No need to reconstruct URLs | Minimal after fix |
| Start new inquiry | Agent | Capture and progress a new lead | Workbench works, submit works, draft persists | Post-submit blocked state feels corrective too early | Treat blocked state as a saved checkpoint and continue in Trip Details | No lost work after submit | Momentum drops at the first validation wall |
| Try the public checker | Customer | Judge whether the product is useful | Strong landing page, strong value proposition, low-friction entry | Full traveler report depth was not the main validated slice here | Use it as a lightweight pre-agent clarity tool | Clear promise without sign-up | No obvious landing friction; deeper report quality still needs a dedicated pass |
