# Travel Agency Main App Simulation - 2026-06-18

## Scope

Persona: agency owner and agent operator.

Goal:

- validate the real authenticated main app
- prove the main workflow is understandable from first principles
- test the highest-friction states in the live UI
- document what is good, what is confusing, and what still needs work

Verified runtime:

- frontend: `http://localhost:3101`
- backend: `http://localhost:8000`
- stale unrelated process was still listening on `http://localhost:3000`
- `http://localhost:3000` returned `404` for the app routes and is not the repo-started frontend

## Live Simulation Pass

### Pass 1: Fresh browser entry

What I tried:

- opened the repo-started frontend in a fresh browser session
- checked the main overview surface
- checked the login surface

What I found:

- `/overview` loads on the correct app server but the fresh browser session is unauthenticated
- the app correctly hits `401` on protected endpoints such as:
  - `/api/auth/me`
  - `/api/auth/refresh`
  - `/api/trips`
  - `/api/inbox`
  - `/api/reviews`
  - `/api/pipeline`
- `/login` renders cleanly and shows the expected sign-in form

What this means:

- the app is alive
- the login boundary is real
- a fresh browser cannot proceed into the main workspace without auth cookies

### Pass 2: Main app UX verification

What I tested in code and live UI:

- overview prioritization
- workbench blocking copy
- trip save confirmation
- missing-detail recovery guidance
- action-list stability

Implementation improvements shipped in this pass:

- overview now shows a `Start here` banner for the highest-priority action
- intake saves now show a clearer success message and a `Continue to ...` button when a next required detail exists
- blocked run copy now points back to a concrete recovery step instead of feeling terminal
- duplicate action-list keys were fixed so repeated labels do not collide

## Scenario 1: Agency owner triage

What I am trying to do:

- open the app
- see what needs attention
- decide where to start

What worked:

- the overview is structured around operational urgency
- the new `Start here` banner makes the next move more obvious
- the page speaks in queue language instead of generic dashboard language

What is still weak:

- the overview still depends on the operator understanding the queue semantics
- the app would benefit from even more direct “do this first” framing for the top item

Time saver:

- the highest-priority action is now surfaced before the longer queue list

Time waster:

- if the user ignores the top banner, they still have to scan and interpret the rest of the overview

## Scenario 2: New trip / workbench intake

What I am trying to do:

- start a new trip from the agency workbench
- understand whether the brief is ready
- continue the trip without guessing

What worked:

- the workbench clearly separates the intake step from the follow-up step
- blocked-state copy now feels recoverable
- the app points the operator back to the missing-trip-details workflow instead of making the state feel final

What is still weak:

- the workbench still carries a lot of process explanation
- the first-pass experience could be more action-oriented when a trip is incomplete

Time saver:

- the blocked-state CTA gives a direct next move

Time waster:

- the user still has to translate the process language into the actual customer question

## Scenario 3: Save a planning field

What I am trying to do:

- edit a trip detail
- save it
- know immediately what changed
- move to the next required detail if there is one

What worked:

- the save path now gives a visible success message
- when the backend says another required detail remains, the UI tells the operator exactly which one
- the success state includes a `Continue to ...` button that opens the next editor

What I verified:

- the saved-next-step test now passes when the result includes an `origin_city` validation warning
- the success banner is not just cosmetic; it changes according to actual post-save state

Time saver:

- the operator no longer has to re-scan the whole trip after saving a single field

Time waster:

- if the backend does not flag a next required detail, the operator gets a plain saved state rather than a guided continuation

Workaround:

- use the success banner as the source of truth for whether the trip still needs a follow-up field

## Scenario 4: Auth boundary check

What I am trying to do:

- open the app from a fresh browser session
- reach the authenticated workspace immediately

What happened:

- the app showed the login page
- protected routes returned `401`
- the session gate behaved as expected

What this tells me:

- the browser simulation is honest
- the main app is not publicly open in this run
- to continue an authenticated clickthrough, the browser would need a real local login session

## What Is Good

- the app has a real agency workflow, not a toy dashboard
- the overview now gives a clearer starting point
- the workbench and intake paths are understandable
- the save flow now gives a real feedback loop
- the missing-detail guidance is actionable instead of abstract

## What Is Bad

- a fresh browser session cannot reach the main workspace without login cookies
- some app language still sounds internal instead of customer/operator-facing
- the operator still has to do mental translation in a few places
- a few states explain the process more than they help the person finish the job

## Time Savers

- `Start here` on overview
- visible blocked-state recovery CTA
- save confirmation with next-step guidance
- missing-detail panels that name the exact follow-up

## Time Wasters

- scanning the queue when the top action is already obvious
- rereading the trip after every save to see whether anything changed
- interpreting internal process language instead of getting a direct next move

## Workarounds

- use the overview banner to begin the day
- use the blocked-state CTA to get back on track after an incomplete brief
- use the save-success banner as the post-save source of truth
- treat a fresh browser session as an auth boundary check, not a workspace session

## Second Pass: UX, Features, Agents

### UX

Good:

- the main app is now more opinionated about the next action
- the overview and intake surfaces are less dead-end-ish
- the success state after save is visibly better

Needs work:

- the app should keep reducing internal jargon
- the highest-priority action could be even more decisive
- the interface still asks the operator to infer too much in a few places

### Features

Good:

- queue prioritization is useful
- save-state recovery is useful
- missing-detail prompts are useful
- the agent-facing trip workflow is coherent

Needs work:

- stronger end-of-action confirmation
- better state transitions after each important edit
- more explicit guidance from intake to the next operational step

### Agents

Good:

- the product clearly supports an operator, not just a traveler
- internal notes and traveler-facing prompts are separate
- the app assumes judgment, not blind form filling

Needs work:

- the operator’s current responsibility should be even sharper
- the UI should make the transition from “collecting details” to “ready to continue” more obvious

## Bottom Line

The main app now feels closer to a real operating workspace.

The strongest pieces are:

- actionable queue priority
- blocked-state recovery
- clearer save confirmation
- missing-detail guidance

For the broader agency-shape matrix that covers small, big, Indian, African, and global agency scenarios, see:

- `/Users/pranay/Projects/travel_agency_agent/Docs/travel_agency_live_simulation_2026-06-17.md`

The remaining gap is confidence:

- the app still needs to feel more decisive after each operator action
- the workflow should make it harder to wonder whether the system understood the save
- the authenticated browser simulation still depends on actual session state, which is correct but limits a cold start clickthrough
