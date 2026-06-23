# Travel Agency Main App Simulation

Date: 2026-06-22
Mode: Live authenticated app simulation, plus scenario-based reasoning from the current codebase and workspace data

## Scope

This document focuses on the main agency app experience, not the marketing site or the traveler-facing public checker.

What I simulated:
- A small owner-led agency using the app to process new work quickly
- A larger agency using the app as a high-volume command center
- An India-first agency where trip planning is naturally INR- and family-centric
- An Africa-focused distributed team that needs the app to stay clear across time zones and variable connectivity
- A global leisure operator handling repeat planning work and deep links into a specific trip
- A Lagos-based family inquiry for Zanzibar, which stressed non-Indian currency parsing and family/celebration context

Live proof points from the current app session:
- Login succeeded with `newuser@test.com` / `testpass123`
- The clean frontend on `:3101` loaded the authenticated workbench and intake flow
- A live Lagos/Zanzibar inquiry processed successfully from the intake form
- The Risk Review tab showed `PROCEED_INTERNAL_DRAFT`, the soft blocker `soft_preferences`, and the follow-up question about must-haves
- The app kept the customer message visible in the live form while the agent note stayed separate as internal context
- The budget parser now preserves `NGN` and `ZAR` in both compact and plain-number forms, so the app no longer falls back to INR just because the amount is large
- `NGN 2.5m` and `NGN 2500000` now resolve as Nigerian Naira, and the same applies to `ZAR 3m` / `ZAR 3000000`
- The workbench still surfaced the decision state even where the safety bundle was not available, which is better than hiding the run result
- A fresh small-agency intake scenario for `Couple from Mumbai for 6N Bali in July, beach villa preference, INR 3-4L budget, vegetarian meals, anniversary trip` saved correctly as `draft_d8fb558ed0ab` and later autosaved again as `draft_dbafd68b5b8a`
- The same live session showed that the top-level `Process Inquiry` action did not produce a `draft_process_started` event or a visible in-flight state during the test window, so the workflow still has a trust gap at the primary CTA
- The workbench session eventually fell back to the sign-in modal after prolonged interaction, which means long simulations need auth stability checked alongside workflow behavior

Current build wording:
- Decision-state labels now say `Waiting on Customer` instead of `Need More Info`
- The main intake flow is now clearer about when it needs origin and budget versus when it can unlock planning

## Scenario 1: Small Agency, Owner-Only Operator

Who this is:
- One person handles intake, planning, follow-up, and booking
- The operator needs to move fast and cannot spend time decoding internal structure

What worked:
- The overview gives a strong “what needs attention now” feeling
- The planning work is surfaced as an action queue instead of a passive dashboard
- The trip workspace opens directly on a real trip when the id is valid
- The missing-details language is clearer than old status-heavy wording

What felt good:
- The app points to the next move instead of making the operator hunt for it
- Trip detail pages stay anchored to the actual trip instead of a generic shell
- Compact group summaries reduce noise when many similar trips exist

What felt slow or repetitive:
- Repeated-looking rows still make the queue feel busier than it really is
- A small operator still has to scan more than they should before deciding what to touch first

Workaround:
- Treat the top action in overview as the source of truth
- Use the trip deep link once the trip id is known, rather than hunting through lists again
- For the moment, stay in the workbench or queue view after processing instead of relying on the generated trip route

Live intake note:
- The Lagos/Zanzibar inquiry now stays readable as a family request with a real market currency instead of collapsing into an INR assumption
- The workbench gives a follow-up draft rather than pretending the trip is ready when the key traveler preferences are still soft

## Scenario 2: Large Agency, Multi-Agent Command Center

Who this is:
- Several operators are sharing the queue
- One team member may be qualifying, another quoting, another checking review pressure

What worked:
- The app already behaves like a command center rather than a static CRM
- Grouped cards and grouped counts help hide duplicate-looking noise
- The `/trips` list now communicates that it is showing grouped cards from a larger raw trip count

What felt good:
- Queue scale is visible without the page collapsing into chaos
- The app makes it easier to see what is unique work versus repeated work

What still needs help:
- Ownership clarity could be even more explicit in dense queues
- When the queue is very large, repeated work still costs attention even after grouping

Workaround:
- Use the grouped summary first, then drill into the lead card in each cluster
- Let the raw count stay in the background unless a specific repeat needs investigation

Live note:
- The inbox SLA badge now reads as `15X SLA` / `6X SLA` style overages instead of `1500% OF SLA`, which is easier for a team lead to scan in a crowded queue
- That keeps the signal honest while avoiding a metric that looks broken at first glance

Quote review note:
- The live `Quote Review` page now tells the truth when the dashboard summary shows pending review backlog but no detailed review cards are loaded yet
- Instead of a silent contradiction, the page now explains that the summary counts show `22 pending quotes` while the detailed cards are missing in this view
- That matters for larger teams because they need to distinguish “backlog exists” from “the detailed approval queue is ready on this screen”

## Scenario 8: Trip Workspace Follow-Through

Who this is:
- An operator who has already completed intake and now needs to move from trip details into options building
- The operator wants the next step to feel like a real workspace handoff, not a dead button

What worked:
- The live `Open options` control from the completed trip workspace routes to the strategy tab
- The strategy tab renders a concrete options brief instead of a placeholder stub
- The page title and route both reflect the options stage clearly, which makes the handoff feel trustworthy

What felt good:
- The strategy brief starts with a session goal and suggested opening, so the operator has something usable immediately
- The priority sequence and assumptions are visible, which helps an agent understand what needs review before sending anything out

What still needs help:
- The debug-data toggle is intentionally hidden behind a privacy policy gate, so deep technical inspection still requires a secure environment
- The trip workspace still depends on a live authenticated session, so stale browser state can make route verification noisier than the route itself

Workaround:
- Use the strategy tab as the primary “next move” after intake
- Treat the trip URL as the durable workspace handoff, then reopen from the canonical route if the browser session gets stale

## Scenario 9: Workbench Process Path, Small Agency Owner

Who this is:
- A small owner-led agency operator using the new-inquiry workbench as the primary command surface
- The operator expects the app to save the draft quickly, then move into a visible processing state when `Process Inquiry` is pressed

What worked:
- Customer and agent notes saved cleanly in the workbench draft
- Autosave created durable draft records with the same scenario text, so the app is not losing the live intake
- The saved draft remains recoverable after a browser/session interruption

What felt good:
- The intake canvas is legible enough for a real owner to write the traveler request and internal note without extra scaffolding
- The workbench preserves the difference between customer-facing message and internal planning note

What still needs help:
- The primary `Process Inquiry` action did not produce a visible run state during the live test
- No `draft_process_started` event appeared for the saved Bali draft in the audit trail during the interaction window
- The workbench session expired into a sign-in modal during the longer simulation, which interrupts momentum for an operator doing real work

Workaround:
- Save the draft first, then reopen the saved draft if the session goes stale
- Treat the draft itself as the durable work artifact until the process path is made visibly reliable

Live note:
- The saved draft id changed from `draft_d8fb558ed0ab` to `draft_dbafd68b5b8a` through autosave, which confirms persistence but also shows how easy it is for the operator to lose a clear sense of “what just happened” without a stronger processing response

## Scenario 10: Fresh Browser Validation, Global Market Intake

Who this is:
- A live authenticated operator using a clean browser session to confirm that the workbench still works end to end after the earlier stale-server noise
- The operator is handling a global-market request, not an India-only shorthand, so currency and destination framing both matter

What worked:
- The login flow on a fresh frontend instance succeeded and carried the session into the main app
- The workbench accepted the Lagos/Zanzibar inquiry and processed it into a new draft
- The route advanced to the Frontier tab after processing, which is the right trust signal for a completed run
- `Processed successfully`, `View Frontier`, and `View Trip` gave the operator immediate next steps instead of a dead end

What felt good:
- The workbench kept the traveler message visible while the agent note stayed internal
- The processed state gave a clear handoff into frontier analysis without hiding the trip context
- The Frontier tab rendered a live-looking trust bundle with sentiment, intelligence pool, and status flags instead of a blank shell

What still needs help:
- The browser environment can still be misleading if the frontend server is stale, so live verification should always prefer a fresh server before concluding the app is broken

Live note:
- The run completed on a clean `:3102` frontend with `draft_6bb50ae710ab`
- The result surfaced `Frontier OS`, `GHOST CONCIERGE`, `TRAVELER SENTIMENT`, `FEDERATED INTELLIGENCE POOL`, and the live `Trust Anchor`
- That makes the workbench feel like a real operator command surface rather than a toy intake form

## Scenario 11: Seasonal Campaign Planning, Owner Operator

Who this is:
- An owner using the Seasonal Campaigns module to plan a destination push, simulate outcomes, and preflight a dispatch
- The operator wants one place to hold window, budget, channel mix, and guardrail logic without jumping between spreadsheets

What worked:
- The seasonal campaigns route loads cleanly in a fresh authenticated browser session
- Creating a new campaign works with a destination, window, budgets, channel mix, notes, and blocklist
- The simulation action returns projected leads, bookings, margin, and confidence
- The preflight action returns a pass/fail summary with named checks and a risk score
- The dry-run dispatch returns a usable execution summary without needing a live send

What felt good:
- The module behaves like a real planning surface instead of a static form
- The campaign summary card makes the destination, window, budget range, and channel mix visible at a glance
- The operator can see the chain from create to simulate to validate to dispatch in one place

What still needs help:
- Live campaigns are still a new-ish surface, so the module should keep proving itself with more scenario variety

Live note:
- Created `Monsoon Push` with `draft` status, `Bali`, `6 → 8` window, budgets `1000 to 5000`, and a four-channel mix
- `Simulate` returned `335` leads, `140` bookings, `8.5%` margin, and `0.72` confidence
- `Preflight` passed with `budget_boundaries`, `channel_mix_present`, and `window_defined`
- `Dry run` dispatch completed with `email, organic, paid, social`

## Scenario 12: Africa- and Global-Market Intake

Who this is:
- A Lagos-based operator handling a Zanzibar family inquiry
- The agency needs the app to stay clear when the market is not INR-first and the customer is not using India-centric shorthand

What worked:
- The intake flow accepted the request cleanly once the trip purpose was explicit
- NGN-specific input stayed as a non-INR market signal instead of being flattened into a local assumption
- The processed run advanced to a real decision state instead of pretending the request was ready for traveler-facing output

What felt good:
- The app asks for the missing thing that actually blocks quoting, not just the first thing it failed to parse
- The non-INR family request stays legible as a real booking scenario, not a special-case edge

What still needs help:
- If the operator omits trip purpose, the run falls back to `WAITING ON CUSTOMER`
- The follow-up question is honest, but the intake form could make that required signal more obvious before processing

Workaround:
- Include a short trip-purpose line in the agent note when the customer message is sparse
- Keep the operator prompt language close to the actual traveler request so the system has enough context to proceed

Live note:
- `Family of 5 from Lagos planning 5N Zanzibar in December...` without trip purpose landed on `WAITING ON CUSTOMER` with `incomplete_intake`
- The same request with `Trip purpose: family vacation` advanced to `PROCEED_INTERNAL_DRAFT` with `soft_preferences`

Clean takeaway:
- The app is better when it asks for the truly missing decision input, but the intake surface still needs to make purpose capture easier for non-India, non-template conversations

## Scenario 13: Browser-Backed Workbench to Trip Details Handoff

Who this is:
- A live authenticated operator using the browser to move a real inquiry from intake into the trip details workspace
- The operator wants the app to show the processed state clearly, then keep the handoff readable in the planning screen

What worked:
- The browser session accepted the login with `newuser@test.com` / `testpass123`
- The intake form processed a fresh inquiry for a Nairobi to Zanzibar family trip
- The live result exposed `Processed successfully`, `View Trip`, and `View Frontier` as clear next actions
- The trip details page rendered the handoff as a concrete workspace, not a generic placeholder
- The page showed `Ready to build options`, which matches the operator's next move

What felt good:
- The trip summary is highly readable at a glance
- Origin, destination, type, purpose, party size, dates, budget, and must-haves are all visible in one place
- The top header now reads `Zanzibar family leisure trip`, which carries the purpose forward instead of flattening the trip into a generic leisure label
- The stage rail makes it obvious that intake is done and options are the next step

What still needs help:
- The planning page is still stronger on operational fields than on the story of why the trip exists
- The header is better now, but the page could still benefit from a slightly richer narrative summary for global-market handoffs

Workaround:
- Keep the purpose in the intake notes for now when running sparse global-market cases
- Use the trip summary cards as the fastest place to recover purpose while the richer narrative view is still being developed

Live note:
- The processed Nairobi/Zanzibar inquiry landed on `http://localhost:3101/trips/trip_688eeacba2de/intake`
- The trip details card showed `Origin Nairobi`, `Destination Zanzibar`, `Type leisure`, `Purpose family leisure`, `Party Size 3 pax`, `Dates in Jan`, `Budget $4,500 - $5,500`, and `Must-haves beach access, kid-friendly`
- The trip header read `Zanzibar family leisure trip` and `Ready to build options`

## Scenario 3: India-First Agency

Who this is:
- The agency works with Indian travelers, Indian pricing expectations, and family-led decision making
- The operator needs clear missing-detail prompts, not generic CRM language

What worked:
- The app’s current operating context already feels India-friendly
- The live settings and pricing assumptions are grounded in INR
- The “Missing customer details” phrasing is much easier to scan than internal process language

What felt good:
- The app is acting on real trip readiness, not just status labels
- The default view now helps an operator know whether they should ask the customer for more information or continue planning

What still needs help:
- Some surfaces still read like internal workflow artifacts instead of plain human outcomes
- The app should continue leaning toward family-travel language, not software-process language
- Stage labels in role-specific metrics must stay humanized so finance and fulfillment do not see backend enum casing
- Example summaries in grouped action-required quotes must keep avoiding repeated title text as more variants are added

Workaround:
- Keep using the top-level banner and trip detail summary as the daily operating vocabulary
- Treat missing details as a checklist, not a failure state

Live intake note:
- A label-style `Budget: USD 4,500` now resolves in the backend after the extractor restart, so clear budget wording can unlock planning instead of stalling
- The Bali intake now works with plain-language dates instead of requiring ISO-like formatting

## Scenario 4: Africa-Focused Distributed Agency

Who this is:
- The team may be split across cities or time zones
- Communication is often asynchronous, and connectivity can be uneven

What worked:
- The app can serve as a shared state container instead of a live call-by-call dependency
- Valid deep links into a trip workspace make handoff possible without re-explaining the whole case
- The fallback on invalid links is at least honest about the record being unavailable

What still needs help:
- The app does not yet signal remote-team friction in a special way
- There is no explicit low-bandwidth or delayed-sync comfort layer in the UI
- The current experience assumes the operator can refresh and re-enter quickly

Workaround:
- Use deep links as the handoff artifact
- If a link is stale, return to the planning list and re-open the trip from the canonical queue

Live intake note:
- The explicit `Origin city: Nairobi` run now promotes to a planning-ready trip after the backend restart, which is the right behavior for a distributed team that needs clear handoff language

## Scenario 5: Global Leisure Operator

Who this is:
- The agency handles trips across destinations and needs repeatable planning behavior
- The team needs the app to stay understandable across many trip types and markets

What worked:
- The same trip workspace pattern held up for a real Bali trip deep link
- The app did not need a special-case route for that trip
- The structure stays consistent across different destinations and trip sizes

What felt good:
- Once the trip exists and the id is valid, the app gets you to the right trip without detours
- The workspace keeps the live trip context visible while still exposing the stage tabs

What still needs help:
- The app still depends on a valid route id; stale ids fall back to a generic unavailable screen
- For global teams, the app should keep getting better at expressing location-specific assumptions in plain language
- The generated trip route now opens cleanly in a fresh authenticated session for the Lagos/Zanzibar trip, so the trip-details drilldown is usable after a completed run

Workaround:
- Treat the trip URL as the durable handoff token
- If a route is stale, go back to Trips in Planning and reopen from the canonical list
- Until the handoff is fixed, use the workbench completion view as the closing step

Live rerun note:
- After the intake/parser fixes, the same workbench flow now lands on a clear risk-review state for the Lagos/Zanzibar request
- The `NGN 2.5m` style note now preserves the full market currency instead of collapsing into the default INR assumption

## Scenario 6: Small Agency Call Capture

Who this is:
- A smaller boutique agency that wants to move fast and keep each inquiry simple
- The operator needs the app to preserve the traveler’s real party size, not just the last partial mention in the note

What worked:
- The intake flow accepted a casual WhatsApp-style call summary without needing special formatting
- The app kept the traveler’s destination, date window, and must-haves visible immediately after processing
- The trip workspace opened from the completed workbench run without the earlier unauthorized bounce

What we found:
- Before the patch, the trip card collapsed `2 adults and 1 child` into `1 pax`
- The budget parser also dropped the `L` in `Budget INR 2.5L`, which made the planning surface show `₹3` instead of the real amount
- That meant the app was technically processing the request, but it was still hiding important planning context from the operator

Fix/workaround:
- Preserve richer party facts when later passes are less complete
- Parse `INR 2.5L` as `250000`
- Render INR budgets in compact form so the UI matches how agents actually speak about them

## Scenario 7: Timeline Review, Human Labels Only

Who this is:
- An operator checking the decision timeline after a trip has moved through several stages
- The operator wants to understand the trip history quickly without decoding raw enum values

What worked:
- The timeline page loaded the real trip history in the original Chrome session
- The page kept the stage/status progression readable enough for a quick scan
- The shared timeline helper now renders `Stage not set` instead of leaking `Unknown`

What felt good:
- The event card reads like a human timeline, not a debugging dump
- The stage badge stays consistent with the rest of the app’s friendly labels

What still needs help:
- The timeline surface still depends on a live authenticated session, so browser auth matters for validation
Date: 2026-06-21
Mode: Live authenticated app simulation, plus scenario-based reasoning from the current codebase and workspace data

## Scope

This document focuses on the main agency app experience, not the marketing site or the traveler-facing public checker.

What I simulated:
- A small owner-led agency using the app to process new work quickly
- A larger agency using the app as a high-volume command center
- An India-first agency where trip planning is naturally INR- and family-centric
- An Africa-focused distributed team that needs the app to stay clear across time zones and variable connectivity
- A global leisure operator handling repeat planning work and deep links into a specific trip

Live proof points from the current app session:
- Login succeeded with `newuser@test.com` / `testpass123`
- The original `:3010` dev server was stale, so I brought up a clean frontend on `:3101` and used that live session for the authenticated validation
- `/overview` loaded the live command center
- `/trips` loaded the grouped planning list
- The planning label now reads `Ready to build options` instead of `Need Trip Options`
- A valid deep link to `/trips/tc_roundtrip_b3bbea85678b/intake` loaded the Bali trip workspace
- A stale or invalid trip id still falls back to `Workspace unavailable`, which is correct behavior for a dead link
- The workbench processed a thin Dubai request into a blocked trip that still asked for origin/budget details
- After the backend restart, the same workbench successfully promoted an explicit `Origin city: Nairobi` / `Budget: USD 4,500` request to `Ready to build options`
- The ready trip now shows optional refinements as `Recommended details` with `Add recommended details or continue to options.` instead of blocker copy
- The underlying Zanzibar scenario now records `destination: Zanzibar` instead of leaking the origin city into destination candidates, so the trip record matches the traveler intent
- The authenticated trip page now opens as `Zanzibar family trip`, confirming the visible title follows the actual destination rather than the departure city
- The lead inbox default operations profile no longer repeats the same age signal twice on each card, which makes dense queues easier to scan at a glance
- Lead inbox rows with missing destinations now fall back to the trip type instead of showing `Unknown leisure`, which reads more like a real intake state
- Lead inbox rows with missing destinations now headline as `Trip details incomplete`, which is clearer than a bare trip type for operators scanning the queue quickly
- The inbox header count label no longer has duplicated wrapper markup, so the row remains visually clean after the role-view updates
- The team-lead inbox profile now shows ownership, SLA, and priority without repeating the same recency signal in the metrics row
- Finance and fulfillment inbox profiles now humanize the stage metric as `Options` instead of leaking the raw lowercase `options` enum
- The grouped quote examples now stop repeating the same title twice, so the example line reads as one title plus supporting detail instead of mirrored text
- The quote review page now falls back to `Trip details incomplete` for unknown destinations instead of showing `Unknown leisure`
- The trips planning stage trail now reads as a clean progress line without the stray arrow-plus-dot punctuation
- The Bali intake now completes when the traveler message uses explicit origin, party size, destination, travel dates, budget, and visa-risk wording
- The date parser now understands common month-day ranges like `July 10 to July 16`
- `visa_concerns_present` now carries heuristic maturity, so discovery packets no longer hard-fail just because the signal exists
- The generated trip route now opens cleanly in a fresh authenticated browser session for the completed Lagos/Zanzibar trip, so the handoff into the trip workspace is working as intended

Current build wording:
- Decision-state labels now say `Waiting on Customer` instead of `Need More Info`
- The main intake flow is now clearer about when it needs origin and budget versus when it can unlock planning

## Scenario 1: Small Agency, Owner-Only Operator

Who this is:
- One person handles intake, planning, follow-up, and booking
- The operator needs to move fast and cannot spend time decoding internal structure

What worked:
- The overview gives a strong “what needs attention now” feeling
- The planning work is surfaced as an action queue instead of a passive dashboard
- The trip workspace opens directly on a real trip when the id is valid
- The missing-details language is clearer than old status-heavy wording

What felt good:
- The app points to the next move instead of making the operator hunt for it
- Trip detail pages stay anchored to the actual trip instead of a generic shell
- Compact group summaries reduce noise when many similar trips exist

What felt slow or repetitive:
- Repeated-looking rows still make the queue feel busier than it really is
- A small operator still has to scan more than they should before deciding what to touch first

Workaround:
- Treat the top action in overview as the source of truth
- Use the trip deep link once the trip id is known, rather than hunting through lists again
- For the moment, stay in the workbench or queue view after processing instead of relying on the generated trip route

Live intake note:
- A small, simple Dubai request still blocks when origin is not captured clearly enough, which is correct because it prevents a bad first quote
- The workbench then gives a follow-up draft rather than pretending the trip is ready

## Scenario 2: Large Agency, Multi-Agent Command Center

Who this is:
- Several operators are sharing the queue
- One team member may be qualifying, another quoting, another checking review pressure

What worked:
- The app already behaves like a command center rather than a static CRM
- Grouped cards and grouped counts help hide duplicate-looking noise
- The `/trips` list now communicates that it is showing grouped cards from a larger raw trip count

What felt good:
- Queue scale is visible without the page collapsing into chaos
- The app makes it easier to see what is unique work versus repeated work

What still needs help:
- Ownership clarity could be even more explicit in dense queues
- When the queue is very large, repeated work still costs attention even after grouping

Workaround:
- Use the grouped summary first, then drill into the lead card in each cluster
- Let the raw count stay in the background unless a specific repeat needs investigation

## Scenario 3: India-First Agency

Who this is:
- The agency works with Indian travelers, Indian pricing expectations, and family-led decision making
- The operator needs clear missing-detail prompts, not generic CRM language

What worked:
- The app’s current operating context already feels India-friendly
- The live settings and pricing assumptions are grounded in INR
- The “Missing customer details” phrasing is much easier to scan than internal process language

What felt good:
- The app is acting on real trip readiness, not just status labels
- The default view now helps an operator know whether they should ask the customer for more information or continue planning

What still needs help:
- Some surfaces still read like internal workflow artifacts instead of plain human outcomes
- The app should continue leaning toward family-travel language, not software-process language
- Stage labels in role-specific metrics must stay humanized so finance and fulfillment do not see backend enum casing
- Example summaries in grouped action-required quotes must keep avoiding repeated title text as more variants are added

Workaround:
- Keep using the top-level banner and trip detail summary as the daily operating vocabulary
- Treat missing details as a checklist, not a failure state

Live intake note:
- A label-style `Budget: USD 4,500` now resolves in the backend after the extractor restart, so clear budget wording can unlock planning instead of stalling
- The Bali intake now works with plain-language dates instead of requiring ISO-like formatting

## Scenario 4: Africa-Focused Distributed Agency

Who this is:
- The team may be split across cities or time zones
- Communication is often asynchronous, and connectivity can be uneven

What worked:
- The app can serve as a shared state container instead of a live call-by-call dependency
- Valid deep links into a trip workspace make handoff possible without re-explaining the whole case
- The fallback on invalid links is at least honest about the record being unavailable

What still needs help:
- The app does not yet signal remote-team friction in a special way
- There is no explicit low-bandwidth or delayed-sync comfort layer in the UI
- The current experience assumes the operator can refresh and re-enter quickly

Workaround:
- Use deep links as the handoff artifact
- If a link is stale, return to the planning list and re-open the trip from the canonical queue

Live intake note:
- The explicit `Origin city: Nairobi` run now promotes to a planning-ready trip after the backend restart, which is the right behavior for a distributed team that needs clear handoff language

## Scenario 5: Global Leisure Operator

Who this is:
- The agency handles trips across destinations and needs repeatable planning behavior
- The team needs the app to stay understandable across many trip types and markets

What worked:
- The same trip workspace pattern held up for a real Bali trip deep link
- The app did not need a special-case route for that trip
- The structure stays consistent across different destinations and trip sizes

What felt good:
- Once the trip exists and the id is valid, the app gets you to the right trip without detours
- The workspace keeps the live trip context visible while still exposing the stage tabs

What still needs help:
- The app still depends on a valid route id; stale ids fall back to a generic unavailable screen
- For global teams, the app should keep getting better at expressing location-specific assumptions in plain language
- The trip workspace is now reachable from a clean authenticated session; stale route handling is still the main edge to watch

Workaround:
- Treat the trip URL as the durable handoff token
- If a route is stale, go back to Trips in Planning and reopen from the canonical list
- Until the handoff is fixed, use the workbench completion view instead of the trip page as the closing step

Live rerun note:
- After the intake/parser fixes, the same workbench flow now lands on the trip page cleanly in the original Chrome session
- The `BUDGET: INR 2.5L` style note now preserves the full amount instead of collapsing to a single-digit rupee value
- The trip detail card now shows `3 pax` and a compact INR budget label instead of the earlier downgraded values

## Scenario 6: Small Agency Call Capture

Who this is:
- A smaller boutique agency that wants to move fast and keep each inquiry simple
- The operator needs the app to preserve the traveler’s real party size, not just the last partial mention in the note

What worked:
- The intake flow accepted a casual WhatsApp-style call summary without needing special formatting
- The app kept the traveler’s destination, date window, and must-haves visible immediately after processing
- The trip workspace opened from the completed workbench run without the earlier unauthorized bounce

What we found:
- Before the patch, the trip card collapsed `2 adults and 1 child` into `1 pax`
- The budget parser also dropped the `L` in `Budget INR 2.5L`, which made the planning surface show `₹3` instead of the real amount
- That meant the app was technically processing the request, but it was still hiding important planning context from the operator

Fix/workaround:
- Preserve richer party facts when later passes are less complete
- Parse `INR 2.5L` as `250000`
- Render INR budgets in compact form so the UI matches how agents actually speak about them

## Scenario 7: Timeline Review, Human Labels Only

Who this is:
- An operator checking the decision timeline after a trip has moved through several stages
- The operator wants to understand the trip history quickly without decoding raw enum values

What worked:
- The timeline page loaded the real trip history in the original Chrome session
- The page kept the stage/status progression readable enough for a quick scan
- The shared timeline helper now renders `Stage not set` instead of leaking `Unknown`

What felt good:
- The event card reads like a human timeline, not a debugging dump
- The stage badge stays consistent with the rest of the app’s friendly labels

What still needs help:
- The timeline surface still depends on a live authenticated session, so browser auth matters for validation
- The event stream is usable, but operators would still benefit from more context on why each event happened

Workaround:
- Keep the shared label helper as the source of truth for any unset or unknown stage
- Verify the live browser session before treating a timeline fetch failure as an app issue

## Scenario 8: Overview Queue Language Cleanup

Who this is:
- An owner checking the overview queue for overdue enquiries and quote work
- The operator needs the queue to describe missing travel dates as a state, not a placeholder

What worked:
- The overview still surfaced the highest-priority enquiry and quote groups clearly
- The live queue now says `Travel Dates to confirm` instead of leaking `Travel TBD`

What felt good:
- The queue copy reads like operational guidance instead of temporary scaffolding
- The same human fallback now appears consistently in both enquiry and quote summaries
- The quote rows also stop surfacing synthetic `TRIP-UNKNOWN` references, so the queue no longer leaks a fake trip id as if it were real data

What still needs help:
- Dense queue rows still carry a lot of signal, so the app should keep trimming noise where possible
- Some records still need a better canonical identifier path, even though the most obvious placeholder reference is now hidden

Workaround:
- Normalize sentinel date values in the shared formatter so every downstream queue card inherits the cleaner wording
- Keep the operator-facing queue anchored on state language like `Dates to confirm`

## What Is Good

- The app now reads more like an operational control room
- Missing details are phrased more clearly
- Duplicate-looking work is less noisy because of grouping
- The main trip workspace loads correctly for a valid trip id
- The app now gives the operator a better answer to “what should I do next?”
- The live intake path now preserves `3 pax` and `₹2.5L` for the small-agency scenario instead of flattening both
- The timeline now shows `Stage not set` for unknown stages instead of leaking a raw placeholder
- The overview queue now says `Travel Dates to confirm` instead of leaking `Travel TBD`

## What Is Bad

- Large queues still cost attention, even when grouped
- Some wording still feels internal instead of customer- or operator-facing
- Stale direct links are handled honestly, but the fallback is still generic
- Remote/distributed operation is supported only implicitly, not with special affordances
- Some ready trips still carry recommended refinements, so the user has to distinguish optional polish from real blockers
- The earlier browser-daemon session made trip-route verification noisy until we checked the same path in a fresh authenticated browser
- Before the parser/display fix, the app also under-read party size and budget for a live small-agency call capture

## Time Savers

- Clear priority framing on the overview
- Grouped cards on the trip list
- Valid trip deep links into the workspace
- Summary-first planning views that keep detail out of the way until needed

## Time Wasters

- Re-reading repeated-looking queue rows
- Hunting for the one true trip in a dense list when the grouping is not yet obvious
- Reopening stale links that have already lost their record
- Closing a successful run only to bounce into an unauthorized trip route instead of the trip workspace
- Reading a processed trip card that rounds a real `2.5L` budget into a meaningless `₹3`
- Seeing raw `Unknown` in the timeline badge before the shared helper was wired through
- Seeing `Travel TBD` in the overview queue before the shared date formatter was normalized

## Clean Takeaway

The main app is heading in the right direction for real agency work:
- It supports a live command-center flow
- It helps the operator decide what to do next
- It reduces repeated noise
- It opens real trip workspaces correctly when the route is valid

The remaining product work is less about “can the app run?” and more about making the live scenarios feel even more human, clearer, and easier to trust at scale.

## Scenario 9: Large Agency Call Capture -> Options Preview

Who this is:
- A larger agency handling a higher-stakes, multi-traveler itinerary with several operational constraints
- The operator needs the app to keep origin, party size, budget, and special handling visible all the way into the options stage

Live note:
- The original Chrome session on `http://localhost:3010` was used for this verification via CDP/Playwright
- The live trip route for `trip_a4cd135cf395` now shows a concrete options brief instead of the previous dead stub

What worked:
- The trip page keeps the full party size, origin, and compact INR budget visible after processing
- The strategy page now renders a real session goal, opening, priority sequence, tone, and guardrails
- The old `Options builder not connected yet` dead end is gone
- The page now reads like an actionable operator brief, not a placeholder

What was good:
- The app is now telling the operator what to do next in plain language
- The preview is grounded in the live trip context, so the surface still feels tied to the actual request
- The strategy route no longer forces the user to infer whether the system is connected

What was bad:
- The strategy surface was previously hiding behind a generic placeholder even when the trip context was already good enough to brief options
- The backend trip contract did not expose `strategy`, so the UI had to act blind even though persistence already had the data
- The route-level experience was therefore lagging behind the real processing state

Workaround:
- Use a strategy preview synthesized from the live trip context whenever a persisted strategy bundle is absent
- Expose `strategy` on the trip response so future consumers do not need to guess

Time savers:
- Operators can now scan the session goal and priority sequence immediately
- The live trip context carries enough detail to brief the next step without jumping back to intake

Time wasters:
- A placeholder that says the builder is not connected even though the trip already has enough data to work with
- Contract drift between stored trip data and what the trip response exposed to the frontend

Clean takeaway:
- The main app now handles the options handoff more honestly and more usefully
- The remaining work is less about wiring and more about making every live trip surface the same level of concrete next-step guidance

## Scenario 10: Nairobi-Based Agency Request -> Destination Disambiguation

Who this is:
- A Nairobi-based agency handling an international family request with a clear real destination
- The operator needs the app to keep agency metadata separate from traveler intent

Live note:
- The same original Chrome session was used for this run
- The first draft of this scenario misread the agency prefix as the destination, which surfaced a parser bug
- After the parser fix, the rerun resolved to `Zanzibar leisure trip` with `Origin Nairobi` and `Destination Zanzibar`

What worked:
- The intake flow preserved the family composition, budget, and senior-friendly constraints
- The trip handoff still worked after processing
- The corrected rerun produced a clean trip title and the right destination

What was bad:
- `Nairobi-based agency request` was initially treated as a destination candidate
- That caused the trip to open as a `Nairobi leisure trip`, which was obviously wrong for the traveler
- The strategy brief also repeated the same internal-data warning twice, which made the review surface noisier than it should be

Fix/workaround:
- Ignore city names when they are only part of a `city-based` agency descriptor
- Deduplicate repeated risk flags before rendering the strategy brief

Time savers:
- The corrected trip title now gives the operator the real destination immediately
- The trip page stays aligned with the actual request instead of forcing a manual mental correction

Time wasters:
- Agency-origin text masquerading as destination intent
- Repeated internal warnings that add clutter without adding new information

Clean takeaway:
- The app is now better at separating source metadata from trip intent
- The live rerun confirmed the destination fix in the stored trip record, not just the UI

## Scenario 11: Ready Trip Continue Button -> Real Stage Advance

Who this is:
- An operator on a planning-ready trip who expects the last CTA on intake to take them to options
- The operator should not have to guess whether the button is actionable when the copy says `Continue to options`

Live note:
- On the Zanzibar trip, the `Continue to options` CTA was live-checked in Chrome
- Before the fix it was a no-op; after the fix it routes to `/trips/[tripId]/strategy`

What worked:
- The button now actually matches the promise in its label
- The live page moved from intake to the strategy route when the operator clicked it

What was bad:
- The CTA was enabled but silently did nothing in the no-recommended-details state
- That created a broken promise right at the point where the app says the trip is ready

Fix/workaround:
- Route the no-recommended-details branch to the strategy page instead of leaving it empty

Time savers:
- Operators can now continue without hunting for a second control
- The CTA no longer forces a mental checkpoint about whether it is wired

Time wasters:
- Clicking a button that says `Continue to options` and staying on the same page

Clean takeaway:
- The intake surface is now more trustworthy because the last action on a ready trip actually advances the workflow

## Scenario 12: India-Style Ready Trip -> CTA Copy Alignment

Who this is:
- A planning operator working a small India-style leisure trip with INR budget, destination, and date window already captured
- The operator expects the final ready-state button to tell the truth about what it does

Live note:
- In the original Chrome session, the ready-trip footer CTA initially read `Continue to options` even though it was a processing action
- The live trip was then completed to `Ready to build options`, and the CTA copy was corrected to `Build trip options`
- The same live page still exposes the real route to options through the top `Open options` link

What worked:
- Budget, destination, and travel window could be saved incrementally in the live intake editor
- The trip card and intake header updated immediately as each required field was saved
- The options route remained available once the trip became ready

What was bad:
- The footer CTA copy implied navigation when the code path was actually a processing action
- That made the ready state feel like it promised one thing and did another

Fix/workaround:
- Rename the footer CTA to `Build trip options` so the label matches the actual action
- Keep the explicit `Open options` route link for direct navigation

Time savers:
- The operator can now distinguish between route navigation and processing at a glance
- The ready state reads more honestly for live agency work

Time wasters:
- A button that says `Continue to options` when the real action is process/build rather than navigation

Clean takeaway:
- The main app is clearer when each CTA names the thing it truly does

## Scenario 13: Ready Options Preview -> Placeholder Cleanup

Who this is:
- A planning operator reviewing a ready Bali trip where the live trip has a destination and dates but no meaningful origin value
- The operator should never have to read placeholder words like `TBD` inside the options brief

Live note:
- In the original Chrome session, the strategy page initially rendered `Check TBD and Bali together` in the priority sequence
- That phrasing came from the preview builder turning a missing origin into literal text instead of a neutral fallback
- After tightening the preview logic, the same live page now says `Check the trip details around Bali`

What worked:
- The strategy page still gave a useful destination-focused session goal and suggested opening
- The route remained usable even when origin was missing

What was bad:
- A generated options brief should not surface placeholder tokens like `TBD`
- The old phrasing made the plan sound less polished than the rest of the page

Fix/workaround:
- Fall back to a human sentence when origin is missing instead of inserting the missing token into the sequence

Time savers:
- The operator reads a coherent brief without mentally correcting placeholder text

Time wasters:
- Any generated sentence that leaks raw placeholder data into the sequence

Clean takeaway:
- The options preview is stronger when it treats missing context as a prompt to simplify, not as text to echo back

## Scenario 14: Quote-Ready Output Page -> Smarter Handoff

Who this is:
- A planning operator on the output surface of a quote-ready Bali trip
- The trip already has strategy and quote-assessment context, but no traveler-ready bundles yet

Live note:
- In the original Chrome session, the output page was initially sending the user back to `Options`
- After the fix, the same page now sends the operator to `Quote Assessment` when quote context exists
- The empty-state copy also explains that the traveler-safe output bundle still needs to be generated

What worked:
- The output page clearly stayed distinct from the strategy and quote-assessment routes
- The operator now lands on the most relevant next step instead of being bounced back one stage too far

What was bad:
- The old empty state assumed the next step was always options, even when the trip had already moved beyond that
- That made the output page feel less aware of the trip’s real lifecycle

Fix/workaround:
- Use the presence of quote context to route the empty state to `Quote Assessment`

Time savers:
- The operator can move toward the actual missing artifact without detouring

Time wasters:
- A stale fallback that sends the operator back to a stage they’ve already passed

Clean takeaway:
- The output page is more trustworthy when its empty-state handoff reflects the current trip stage instead of a generic fallback

## Scenario 15: Owner Quote Review Queue -> Trip Identity Contract

Who this is:
- An owner or senior operator reviewing quotes that need approval before they go out to travelers
- The operator needs each card to be uniquely identifiable, actionable, and legible in a dense queue

Live note:
- In the original Chrome session on `:3101`, the quote review page loaded successfully after login
- Before the backend fix, the queue contained 19 anonymous cards with `TRIP-UNKNOWN` and blank `id` values
- After fixing the canonical review mapper, the same queue now shows real references such as `TRIP-83C845`

What worked:
- Authenticated owner review rendered in the live app instead of crashing
- The page now gives each quote card a real trip reference and a usable `View Details` link
- The queue is finally skimmable as a review surface instead of a wall of identical placeholders

What was bad:
- The backend review mapper only read `trip_id`, but stored reviewable trips can carry `id`
- That caused the review queue to emit blank ids and `TRIP-UNKNOWN`, which also made review actions unreliable
- The stale `:3010` server was still serving the old broken shape, which made the problem look worse in the original browser session

Fix/workaround:
- Use `trip.get("trip_id") or trip.get("id")` as the canonical review identity
- Keep the frontend rendering logic simple; it should display the canonical id, not invent a second identity system

Time savers:
- The owner can now distinguish cards at a glance and click through to a specific trip
- Review actions now have a stable id to target

Time wasters:
- Blank review ids
- Identical placeholder references that make every card look like the same trip
- Debugging against a stale local server instead of a fresh live session

Clean takeaway:
- The review queue only feels like a command center when the backend owns a stable identity contract for each card

## Scenario 16: Small Agency Couple Inquiry -> Natural-Language Party Size

Who this is:
- A small owner-led agency capturing a real inquiry from a traveler who says “couple” instead of spelling out a headcount
- The operator wants the app to understand normal human wording and keep the flow moving

Live note:
- The exact inquiry used in the live browser session was: `Couple from Mumbai for 6N Bali in July, beach villa preference, INR 3-4L budget, vegetarian meals, anniversary trip.`
- After the backend restart, the same inquiry now processes successfully and the Trip Details tab shows `Party Size 2`
- The processed run is also materially better than the old blocked state: the page now shows `Processed successfully`, `View Trip`, and `Promote Draft`

What worked:
- “Couple” now resolves to a two-person party in the real pipeline
- The Trip Details tab shows `Party Size 2` and `Party Composition Adults: 2`
- The inquiry no longer gets stuck on a missing party-size prompt when the user already implied it

What was bad:
- Before the restart, the live workbench kept showing the old `Party Size` missing blocker even though the extractor logic had already been improved
- That made the flow feel broken even when the underlying extraction code was actually ready

Fix/workaround:
- Teach the extractor that `couple`, `pair`, and `duo` imply two adults when no other party structure is present
- Restart the backend worker so the live pipeline picks up the new extraction logic

Time savers:
- The operator can speak naturally instead of translating every inquiry into a structured form first
- The app accepts a common shorthand and keeps the inquiry moving

Time wasters:
- Forcing users to type an explicit `2 pax` when they already said `couple`
- A stale backend worker that keeps surfacing an old blocker after the code is fixed

Clean takeaway:
- The intake flow is better when it understands ordinary agent language first and only asks follow-up questions for genuinely missing information

## Scenario 17: Workbench Risk Review -> Run-State Decision Visibility

Who this is:
- A small agency operator staying inside the workbench after processing an inquiry
- The operator needs the Risk Review tab to show the run decision and follow-up questions immediately, without waiting for a separate trip-shell refresh

Live note:
- In the fresh browser session on `:3101`, the inquiry `Couple from Mumbai for 6N Bali in July, beach villa preference, INR 3-4L budget, vegetarian meals, anniversary trip.` was processed again through the workbench
- The live run completed with a decision state and follow-up data, but the Risk Review tab initially showed an empty state because the workbench store was not hydrating the run decision from `spineRunState`
- After wiring the run-state decision into the store, the same Risk Review tab now shows `Decision State`, `PROCEED_INTERNAL_DRAFT`, `Soft Blockers`, and the follow-up question `Any specific preferences or must-haves for this trip?`

What worked:
- The workbench now exposes the operator-facing decision state in the same place the operator expects to review risk and follow-up state
- The decision view appears even when there is no separate safety bundle yet
- The follow-up question is readable in the live app instead of being hidden behind a blank panel
- The UI now says `Confidence unavailable` instead of inventing a fake percentage when the terminal run status does not provide a score

What was bad:
- The Risk Review tab only rendered when a safety bundle existed, so a valid run could look like “no risk review data” even though the pipeline had already produced a decision and follow-up request
- The run response itself already contained the useful state, but the workbench never hydrated it into the UI store
- The confidence box originally showed `0%`, which was misleading because it looked like an actual score rather than a missing one

Fix/workaround:
- Hydrate `decision_state`, `hard_blockers`, `soft_blockers`, and `follow_up_questions` from the terminal run status into the workbench decision store
- Keep the Risk Review tab useful for both safety-backed and decision-only runs

Time savers:
- The operator can stay in one tab and immediately see why the system wants follow-up
- Follow-up phrasing is visible at the same time as the decision state

Time wasters:
- A blank Risk Review panel after a successful run
- Requiring a full trip-shell refresh just to see the decision that already exists in the run response

Clean takeaway:
- The workbench should surface run-state decisions directly, because the operator’s next move depends on that state more than on the later trip-shell handoff

## Scenario 18: Fresh auth replay + origin extraction fix

Who this is:
- A small owner-operated agency using a clean browser session on a fresh frontend server
- The operator wants the app to accept a normal conversational inquiry without first translating it into a rigid form

Live note:
- Browser target for the clean replay: `http://localhost:3103`
- Login credentials used: `newuser@test.com` / `testpass123`
- The frontend auth client was fixed so login no longer double-encodes the JSON body and fails validation
- The intake parser was then hardened so a phrase like `from Nairobi planning 7 nights in Bali...` now resolves origin city correctly

What worked:
- Login now lands on the real app shell instead of stalling on the sign-in page
- A natural-language inquiry that includes origin in plain English now gets past the missing-origin blocker
- The same inquiry then proceeds to a real decision state instead of stopping at `incomplete_intake`

What changed in the live result:
- Before the parser fix, the same style of input stayed on `WAITING ON CUSTOMER` with `incomplete_intake`
- After the parser fix, the browser shows `PROCEED_INTERNAL_DRAFT` with `budget_feasibility` as the blocker instead of missing origin
- That means the app is now asking about the actual limiting factor rather than the first thing it failed to parse

What was bad:
- The origin extractor was too brittle for a normal sentence like `from Nairobi planning...`
- The live intake flow felt like it needed structured phrasing even though the product promise is conversational capture

Workaround:
- Broaden the origin-delimiter set in the canonical extraction pipeline so common continuation words like `planning`, `going`, `traveling`, and `with` do not swallow the city

Time savers:
- The operator can keep typing the way a customer actually speaks
- The app now spends less time asking for obviously recoverable origin details

Time wasters:
- A login transport bug that makes the whole browser flow look broken even when the backend logic is fine
- An extraction parser that misses plain-English origin phrasing and forces an unnecessary follow-up

Clean takeaway:
- The main app feels much closer to its promise when auth transport is clean and origin city can be recovered from ordinary intake language

## Scenario 19: Larger Agency Family Replay, Trust-Repair Pass

Who this is:
- A larger-agency operator replaying a family inquiry that mixes global-market language, a realistic origin city, and a budget range
- The operator needs the trip page to preserve the real headcount and the real budget band, not just the first number the parser saw

Live note:
- Browser target: `http://localhost:3103`
- Inquiry used: `Family of 4 from Nairobi planning 7 nights in Bali in August. Budget USD 7000-9000. Wants a kid-friendly villa, smooth airport transfers, and two flexible sightseeing days. First international trip for the kids.`
- The same flow now lands on the trip page as `4 pax` instead of `1 pax`
- The same flow now shows `Budget` as `$7,000 - $9,000` instead of collapsing the range to a single lower bound

What worked:
- Origin city stayed correct as `Nairobi`
- Destination stayed correct as `Bali`
- Party size now survives the intake and appears correctly in the trip shell
- Budget range now survives the intake and appears correctly in the trip shell

What was bad:
- The party extractor was letting later generic child wording overwrite an explicit `family of 4`
- The budget extractor was flattening the range too early, which made the trip page look more certain than the traveler actually was

Fix/workaround:
- Prefer explicit family/group counts over generic child keywords when both appear in the same intake sentence
- Preserve both budget bounds in the canonical packet and render the range in the shared budget display helper

Time savers:
- The operator can trust the trip shell as a real summary of what the customer said
- The app now avoids a second round of clarification caused by its own parsing mistakes

Time wasters:
- A family inquiry that becomes `1 pax` after processing
- A range budget that gets shown like a single point estimate

Clean takeaway:
- Bigger-agency handling feels materially better when the app respects the headcount and budget shape that were actually stated

## Scenario 20: Canonical Trip-Purpose Cue for Global Intake

Who this is:
- A global-market operator handling sparse requests where the trip purpose is easy to omit
- The operator needs the workbench to ask for the missing thing before the run is processed, not after the app has already fallen back to `WAITING ON CUSTOMER`

What changed:
- The intake screen now surfaces the canonical purpose prompt from the shared traveler prompt registry
- The same prompt now appears in the workbench helper copy, so the operator sees exactly which missing detail matters
- The trip-details packet summary now includes a purpose card, so the extracted trip story keeps the trip intent visible alongside destination, dates, budget, and party size

What worked:
- The prompt is consistent with the rest of the app’s vocabulary
- The operator gets a visible reminder before processing the inquiry
- After a run settles, clicking `Trip Details` now leaves the operator on the packet view instead of snapping them back to the terminal review tab
- The live packet view shows the purpose card alongside the other trip summary details
- The same pattern held for a different market mix too: a Nairobi/Zanzibar family replay surfaced the purpose card, kept the budget range readable, and preserved the party count

What was bad:
- Global requests could make it all the way to the run result before the missing purpose was obvious
- The earlier guidance existed only in post-run documentation

Time savers:
- The operator no longer has to infer that trip purpose is required for sparse international requests
- The workbench now points to the exact question to ask next
- The trip summary now carries purpose forward instead of hiding it in the extracted signal list
- The operator can inspect Trip Details after the run without losing context to an automatic tab override
- The purpose/budget/party behavior is now consistent across at least two global-market family scenarios, not just one replay

Clean takeaway:
- The app is better when the missing purpose cue is visible at intake time, because global-market requests can then move forward without a needless detour into `WAITING ON CUSTOMER`

## Scenario 21: Compact India-First Honeymoon Replay

Who this is:
- A small India-first operator handling a shorter, more natural couple request
- The operator wants the app to keep the intent readable without requiring a verbose template

What worked:
- The intake accepted a short honeymoon note without needing extra structure
- The packet view preserved purpose, budget, origin, destination, and party size
- INR formatting stayed human-readable for the compact budget range

What felt good:
- The summary reads cleanly for a real owner/operator who just wants the core planning facts
- The app recognizes `honeymoon` as a useful trip purpose, not just a free-text note

Clean takeaway:
- The same purpose/budget/party handling that helped global-market family scenarios also holds up on a concise India-first couple request

## Scenario 22: Browser-Backed Main App, Four Persona Pass

Who this is:
- A small owner-led agency that needs the app to feel fast and obvious
- A larger agency that needs the queue to stay scannable under volume
- An India-first operator who expects the app to stay concise and natural
- An Africa/global operator who needs the app to preserve purpose, currency, and headcount without flattening the request

Live note:
- Fresh browser session on `http://localhost:3103`
- Logged in with `newuser@test.com` / `testpass123`
- Overview, workbench, and inbox all loaded in the browser
- The inbox search for `9E7D` returned the fresh Zanzibar family inquiry as a live queue item
- The inbox response carried `tripPurpose: family leisure` for `trip_9e7d8d596519`

What worked:
- Sign-in now lands on the live app shell instead of stalling
- The workbench helper copy asks for trip purpose up front, which is the right missing signal for sparse requests
- The inbox queue now shows purpose-first titles for the fresh Zanzibar case
- Searching by reference makes it easy to recover a specific inquiry in a dense queue
- The queue count and summary labels still read like an operations surface, not a developer debug panel

What felt good:
- The main app stays coherent across overview, workbench, and inbox
- The Zanzibar family trip reads like a real customer request instead of a generic leisure record
- The app keeps purpose visible in the trip shell and the inbox queue, which helps owners and team leads make quicker decisions

What was bad:
- The first sign-in attempt rejected the submission until the inputs were filled in the browser the way the app expected
- Dense inbox pages are still visually busy, so the operator has to lean on search and grouped summaries
- The planning workspace is still more functional than narrative, so the trip story can feel slightly thin after the run completes

Workaround:
- Use the browser session itself for validation, not just terminal output
- Search inbox by reference when you already know the lead id or short code
- Keep the purpose in the intake note for sparse global-market requests until the narrative summary grows richer

Time savers:
- Purpose-first titles make the queue easier to scan
- Search by reference gets you back to the right lead quickly
- The workbench and inbox now carry the same trip purpose cue, so the operator does not have to infer it twice

Time wasters:
- A stale browser session can make the app look broken even when the route is fine
- Repeating the same trip type when purpose already exists adds noise for small agencies

Clean takeaway:
- The main app is getting closer to the actual operating model: intake captures the request, inbox surfaces what matters, and the trip workspace preserves the why as well as the where

Live processing note:
- The same live workbench draft also proved the primary `Process Inquiry` path does submit and return a real run.
- On the Nairobi/Zanzibar family replay, the run advanced the workbench to `Risk Review`, surfaced `Processed successfully`, and exposed the follow-up `Please provide trip purpose to generate a quote.`
- That is the right sort of outcome for this sparse request: the app did not invent certainty, it asked for the missing planning intent.
- The browser tool click path was noisy, but a direct form submit still exercised the app contract end to end, which makes the run-state result authoritative.

## Scenario 23: Quote Review Backlog Visibility

Who this is:
- A quote owner scanning a backlog of approvals
- A team lead who needs to know whether the screen shows the whole queue or just the currently loaded subset

Live note:
- Fresh browser session on `http://localhost:3103/reviews`
- The summary bar reported `Pending Quotes 47`
- The loaded card list showed 25 quotes and now calls that out explicitly

What worked:
- The review page keeps the queue scannable with clear titles, trip references, and review reasons
- The page now tells the truth when the loaded card set is smaller than the summary backlog
- The operator no longer has to infer that some pending quotes are outside the visible list

What was bad:
- Before the fix, the summary count and visible cards could be read as if the page was complete when it was only showing the loaded subset
- That is exactly the kind of quiet mismatch that causes owners to distrust queue pages

Time savers:
- The new backlog notice tells the operator to refresh instead of hunting for missing cards
- The page stays useful even when the upstream review queue is partially loaded

Time wasters:
- A backlog count that says 47 while the visible list only shows 25, with no explanation

Clean takeaway:
- The review queue is better when it explicitly distinguishes the loaded card subset from the broader pending backlog

## Scenario 24: Ops Gate Returns the Operator to the Right Next Step

Who this is:
- A trip owner trying to enter booking operations from a trip that is not yet proposal-ready
- A planner who needs the locked ops page to point to the next useful workspace instead of a generic dead-end

Live note:
- Fresh browser session on `http://localhost:3103/trips/tc_roundtrip_a069120cb3c6/ops`
- The backend still considers this trip `discovery`, so booking operations stay locked
- The gate now sends the operator back to `Options` rather than dropping them all the way back into Intake

What worked:
- The ops gate is honest about the trip not being ready for booking operations yet
- The fallback now points to the more useful planning surface for a trip that already has an options plan

What felt good:
- The operator can continue the actual next step without losing the trip context
- The page now matches the mental model of “I need to keep building options before booking ops” instead of “go back and start over”

Time savers:
- `Return to Options` gets the planner back to the right workspace faster than Intake

Time wasters:
- Sending a planning-ready trip back to Intake when the real work belongs in the options surface

Clean takeaway:
- The locked ops page is better when it routes to the next useful planning step, not just the earliest step

## Scenario 25: Live Browser Main-App Replay With Source-City Fix

Who this is:
- A small agency operator handling a family leisure lead in the main workbench
- A support-minded agent checking whether the app can turn a natural request into a real planning packet without inventing a fake ambiguity

Live note:
- Browser login with `newuser@test.com` and `testpass123` works, and the authenticated workbench loads on `:3101`
- The first replay showed a real bug: `from Mumbai to Bali` was being split into `["Mumbai", "Bali"]` as destination candidates
- After the parser fix, the same request now resolves to `["Bali"]` and the workflow advances to `tab=frontier`

What worked:
- The workbench accepts the real intake form and creates a draft
- Explicit origin/destination phrasing now moves through the workflow instead of stalling on a false choice
- The Frontier OS panel appears once the packet is complete enough to progress

What was bad:
- Before the fix, the app asked the operator to choose between Mumbai and Bali, which was a parser mistake
- The processed state used to expose duplicate `View Trip` actions; that duplication is now removed

Time savers:
- Explicit `from X to Y` wording now gives the workflow enough signal to proceed
- The live browser flow makes parser regressions obvious immediately

Time wasters:
- False destination disambiguation
- Replaying the same lead without the fix would keep the operator stuck on a made-up choice

Clean takeaway:
- The main app is better when the intake parser respects source-city context and does not turn a clear trip into a false destination fork

## Scenario 26: Processed State Now Keeps One Clear Trip Escape Hatch

Who this is:
- A planner reading the post-run result in the workbench
- A frontline operator who needs a single obvious path from the result card to the trip workspace

Live note:
- The processed workbench state now shows one `View Trip` action and one `View Frontier` action instead of duplicating the same trip action in two places
- The button count in the live browser replay is now `View Trip = 1`, `View Frontier = 1`

What worked:
- The result surface still gives the operator both the trip workspace and the frontier analysis escape hatch
- The action row is easier to scan because each action now means something different

What was bad:
- The previous duplicate `View Trip` copy made the processed state feel noisier than it needed to be

Time savers:
- One trip action is enough when the progress panel already owns the trip escape hatch

Time wasters:
- Two identical `View Trip` buttons in the same result area

Clean takeaway:
- The processed result is cleaner when the app uses one canonical trip-opening action and leaves the other slot for a genuinely different next step

## Scenario 27: Large Agency USD Budget Does Not Get Misread As INR

Who this is:
- A procurement-heavy agency handling a 18-traveler Singapore quote
- A planner who needs the app to respect currency before deciding whether budget is feasible

Live note:
- The large-agency replay used `Budget is USD 42,000`
- Before the fix, the workflow treated the numeric amount as if it were INR and surfaced a false `budget_feasibility` block
- After the fix, the same request advances to `tab=frontier` and no longer invents an INR-based budget feasibility problem

What worked:
- The app still captures the real trip context and moves the request into the next surface
- Foreign-currency budgets no longer get punished by the INR heuristic table

What was bad:
- Comparing a USD budget against an INR heuristic table created a fake negative feasibility signal

Time savers:
- Letting non-INR budgets skip the INR table prevents a lot of pointless back-and-forth on global requests

Time wasters:
- Telling a planner the budget is too low when the budget was simply in another currency

Clean takeaway:
- Global agency workflows need currency-aware feasibility, not one-size-fits-all INR math

## Scenario 28: Large Agency Rooming and Procurement Details Stay Visible

Who this is:
- A procurement-heavy agency planning a group quote with multiple rooming lists
- A planner who needs the packet summary to preserve the operational details that make the quote reusable

Live note:
- The same large-agency replay now surfaces `Group Logistics`
- The packet details show `2 rooming lists · Shareable with procurement`
- The extracted info table also keeps `Rooming List Count`, `Rooming List Requested`, `Rooming Requirements`, `Procurement Share Needed`, and `Procurement Notes`

What worked:
- The operator summary now carries the group-booking signal instead of dropping it on the floor
- Rooming and procurement context are visible without opening the raw JSON

What was bad:
- Before the fix, the packet had no first-class rooming/procurement signal even though the request clearly needed one

Time savers:
- Seeing rooming and procurement in the packet summary makes the next planning step much clearer for a big agency

Time wasters:
- Forcing the operator to reread the raw note just to remember that two rooming lists were requested

Clean takeaway:
- Group bookings are more usable when the packet summary carries the logistics signal, not just the destination and budget

## Scenario 29: Privacy Guard Must Ignore Generated Draft IDs

Who this is:
- The same large-agency operator using dogfood mode while the app persists packet data
- A developer trying to keep privacy protection strict without blocking internal ids

Live note:
- The workbench initially failed because the privacy guard misread the generated draft id as a phone number
- After the guard fix, the same replay completes and the operator can see the packet summary normally

What worked:
- Real phone-number detection still blocks actual contact data
- Generated ids like `draft_...` no longer trip the phone heuristic

What was bad:
- A generated draft id should never stop a legitimate workbench run

Time savers:
- Internal ids are now treated as internal ids, not as user phone numbers

Time wasters:
- Failing a whole processed packet because the draft id happened to contain digits

Clean takeaway:
- Privacy guardrails should be strict about real PII, not overreact to system-generated identifiers

## Scenario 30: Corporate Group Purpose Should Read As Business

Who this is:
- A procurement-heavy agency planning a corporate group quote
- A planner who needs the purpose label to reflect an internal business trip rather than a sightseeing trip

Live note:
- The same Nairobi-to-Singapore corporate replay previously showed `PURPOSE cultural`
- After the intent classifier fix, the packet now shows `PURPOSE business`
- The rest of the packet still preserves the rooming-list and procurement logistics

What worked:
- The trip purpose now matches the corporate/procurement framing of the lead
- The operator summary is no longer nudging the planner toward a leisure interpretation

What was bad:
- `cultural` was too weak and misleading for a procurement-heavy corporate quote

Time savers:
- A correct purpose label helps the planner choose the right supplier/contracting path faster

Time wasters:
- Reading a corporate quote as sightseeing and picking the wrong planning lens

Clean takeaway:
- Corporate agency requests should classify as business when the lead clearly reads like a procurement-managed group quote

## Scenario 31: Cape Town Family Trip Should Not Re-Ask The Destination

Who this is:
- A small Cape Town agency quoting a family trip for 5 travelers
- An operator who already knows the destination and needs a fast internal draft, not a destination clarification loop

Live note:
- The dedicated browser pass used the real app with `newuser@test.com` / `testpass123`
- The request was `Small Cape Town agency handling a family trip for 5 travelers from Cape Town to Dubai in December 2026...`
- The extractor regression now keeps `destination_candidates = ["Dubai"]` and does not synthesize a `destination_candidates / unresolved_alternatives` ambiguity from the rooming-list wording

What worked:
- The destination parsing fix now respects the explicit single destination
- Rooming and procurement language are handled as logistics signals instead of being mistaken for destination ambiguity
- The regression test covers the exact scenario so the parser does not drift back

What was bad:
- Broad destination-context ambiguity detection was overreaching into adjacent logistics copy
- That caused a false `Where would you like to go?` style detour even though the destination was already explicit

Time savers:
- Keep the explicit destination as the source of truth when the request already says `from X to Y`
- Use rooming/procurement extraction to enrich the packet without reopening destination choice

Time wasters:
- Asking for a destination that the customer already gave
- Letting an `or` in rooming copy masquerade as a destination alternative

Clean takeaway:
- If the request already has one explicit destination, the parser should not downgrade it just because nearby logistics language contains the word `or`

## Scenario 32: Date Flexibility Should Not Become Budget Flexibility

Who this is:
- The same small Cape Town family-booking agency
- An operator who is flexible on travel dates, but not asking for a stretched budget

Live note:
- The first live rerun of the Cape Town/Dubai case produced a clean packet but still surfaced a bogus `budget_flexibility` ambiguity because the sentence contained `flexible on exact dates`
- After narrowing the ambiguity trigger to actual budget-flex phrases, the rerun came back with an empty ambiguity report

What worked:
- Date flexibility is now interpreted as a date signal, not a budget signal
- The packet stays focused on the real planning question instead of raising a fake pricing concern

What was bad:
- Any occurrence of the word `flexible` was enough to trigger budget ambiguity
- That made ordinary date flexibility look like a commercial warning

Time savers:
- Keep budget ambiguity tied to budget language, not generic flexibility wording
- Let date flexibility live in the date signal path where it belongs

Time wasters:
- Making the planner mentally discount a fake pricing concern that came from date wording

Clean takeaway:
- A trip can be date-flexible without being budget-flexible, and the parser should keep those apart

## Scenario 33: Large Nairobi Corporate Quote, Fresh Browser Submit

Who this is:
- A larger Nairobi agency handling a procurement-heavy corporate quote
- The operator needs one clear internal path from intake to processing, with rooming lists and a quick quote handoff

What I simulated:
- Fresh authenticated workbench entry on `draft=new`
- A corporate request for 18 travelers from Nairobi to Singapore in October 2026
- Budget and logistics context: USD 42,000, 6 nights, mid-to-upscale hotel blocks, airport transfers, two separate rooming lists
- Direct submit from the intake form into live processing

What worked:
- The workbench accepted the intake and kept customer message and internal note separate
- The live run produced `POST /api/drafts` and `POST /api/spine/run`
- The page advanced into a `Processing` state, then into the safety/decision view
- The decision state surfaced `PROCEED_INTERNAL_DRAFT` with a `soft_preferences` blocker
- `View Trip` and `View Frontier` appeared as immediate next actions

What felt good:
- The app preserves the shape of a real procurement-heavy quote instead of flattening it into a generic inquiry
- The operator can see that the system is actively processing, not just storing text
- The follow-up question is specific enough to use with the customer or account owner

What still needs help:
- The safety bundle was not available for this run, so the operator has to read the decision state manually
- The follow-up step still adds one extra reading hop before the quote can move forward

Time savers:
- `View Trip` and `View Frontier` give immediate handoff paths after processing
- The draft id appears quickly, so the work stays anchored to one record

Time wasters:
- Sparse global-market requests still need a short must-haves pass before the app can finish the quote direction

Workaround:
- Use the follow-up question as the exact prompt back to the customer or account owner
- Treat the decision state as the operator truth source when the safety bundle is missing

## Scenario 34: Flight Arrives After Hotel Check-In

Who this is:
- A small owner-led agency handling a straightforward leisure booking where the traveler has already picked the destination and dates
- The operator needs the app to catch a practical itinerary mismatch without making them decode internal terminology

What I simulated:
- A Bangalore-to-Bali family inquiry with dates, budget, and preferences already supplied
- A natural-language schedule conflict: the flight lands at 22:30 on 10 July, while hotel check-in is afternoon on 10 July
- A live browser replay on the authenticated workbench and a follow-through into the trip intake page

What worked:
- The workbench now surfaces a plain-language follow-up question on the safety tab
- The trip packet stores the contradiction as `flight_hotel_mismatch` with both values preserved
- The browser replay shows the run as `Processed successfully`, so the operator is not left staring at a silent failure
- The trip intake page now surfaces procurement-heavy rooming details as a `Group logistics` card, so the same workspace also preserves the corporate-quote context
- The live saved trip kept the rooming detail as `2 rooming lists` instead of flattening it into a generic procurement note

What felt good:
- The app asks for the exact fix instead of making the operator infer the problem
- The mismatch is visible in the same session that processed the inquiry, so there is no separate forensic step
- The trip workspace still feels like a real record, not a transient preview

What still needs help:
- The trip intake page now shows the same contradiction in a compact critical-issue card, but the workbench is still the more explicit first glance
- The main intake summary still keeps the follow-up a level deeper than the top-line blocker strip

Time savers:
- The question text is already phrased in customer-facing language
- The contradiction label can be reused by support, ops, or the booking team without translation
- The rooming list detail is now visible on the trip page, which saves a second lookup when procurement needs the quote

Time wasters:
- If the sentence says `hotel check-in is afternoon on 10 July`, older detector wording could miss it
- Rebuilding the mismatch as a manual note would waste time the app should save
- Flattening rooming lists into a single procurement note would have forced the agent to reconstruct the group shape by hand

Workaround:
- Keep the follow-up question as the operator script: move hotel check-in or choose an earlier flight
- Use the saved packet contradiction as the durable record when handing the trip to the next agent

## Scenario 35: Family Trip Child Ages

Who this is:
- A family-booking agency handling a standard Bali leisure trip
- The operator needs child ages to survive into the saved trip record so rooming and hotel suggestions stay accurate

What I simulated:
- A Mumbai-to-Bali family inquiry with `2 adults and 3 children ages 6, 9, and 12`
- A live browser replay on the authenticated workbench
- A follow-through into the saved trip workspace

What worked:
- The packet now keeps the child ages as `[6, 9, 12]`
- The trip workspace shows a `Family details` card with `3 children · ages 6, 9, 12`
- The summary still keeps the main trip legible without burying the family context

What felt good:
- The app no longer invents or drop-shifts a child age from the notes
- The family context is now visible where the quote team will actually use it

What still needs help:
- Family details are still a secondary summary card rather than a top-line blocker or warning

Time savers:
- The quote team can see child ages without reopening the raw message

Time wasters:
- Reconstructing child ages from notes or memory would be error-prone and slow

Workaround:
- Use the family details card as the quick rooming reminder when building options

## Scenario 36: Zanzibar Family Trip, Beach-Resort False Positive Removed

Who this is:
- A small Nairobi agency handling a standard family leisure booking
- The operator needs the destination to stay on Zanzibar even when the traveler mentions a beach resort preference

What I simulated:
- A fresh Nairobi-to-Zanzibar family inquiry for 4 adults and 2 children
- Budget KES 480,000, 6 nights, beach resort preference, airport transfers, vegetarian meals
- A full browser replay from new inquiry to workbench processing and then into the saved trip and options views

What worked:
- The workbench advanced the trip to `PROCEED_INTERNAL_DRAFT`
- The saved trip page kept the destination as `Zanzibar`
- The trip shell showed `Zanzibar family leisure trip` with `6 pax · in Aug 2026`
- The trip details page stayed readable and showed the family context without inventing extra age data
- The options page generated the expected internal-draft strategy instead of a contradiction escalation

What felt good:
- The operator no longer has to explain why `Beach` appeared as a second destination
- The saved trip now reads like a real Zanzibar family request, not a parser artifact
- The planning surface and the saved-trip surface agree with each other

What still needs help:
- Family details still stop at child count when ages are not supplied
- Date flexibility was not captured on this request, so that secondary summary card remains empty

Time savers:
- One clear destination means the operator can move straight into options planning
- The saved trip summary is aligned enough that the next agent can work from it without cross-checking the intake note

Time wasters:
- Treating `Beach` as a destination would have forced the operator into an unnecessary choice
- Having to mentally discard amenity words before planning is pure friction

Workaround:
- Keep generic amenity nouns out of destination candidates so preferences stay preferences
- Use the family summary card only for rooming context, not for destination resolution

## Scenario 37: Nairobi Budget Stays in KES

Who this is:
- A Nairobi agency handling a family leisure booking for Zanzibar
- The operator needs the money to stay in the traveler’s currency so the quote does not drift into an INR-only mental model

What I simulated:
- A fresh Nairobi-to-Zanzibar family inquiry with `KES 480,000`
- A browser replay through the saved trip page after the budget parser fix

What worked:
- The trip page now shows `KSh480,000` instead of `₹4.8L`
- The browser kept the budget aligned with the African-market request
- The rest of the trip summary stayed unchanged

What felt good:
- The operator can read the budget without translating currencies in their head
- The budget now matches the traveler market and the agency market

What still needs help:
- The saved trip still hides child ages when they are not provided

Time savers:
- One currency label means less mental normalization for the quote team
- The budget now matches the live conversation context

Time wasters:
- Showing INR for a KES budget would force a needless conversion step

Workaround:
- Keep currency parsing and budget display aware of the original source currency

## Scenario 38: Cape Town to Mauritius Now Resolves as a Real Destination

Who this is:
- A South African agency handling a family leisure booking
- The operator needs Mauritius to resolve as a destination instead of dropping into `Unknown`

What I simulated:
- A Cape Town-to-Mauritius family inquiry with 2 adults and 2 children
- Budget ZAR 160,000, 7 nights, beach resort, airport transfers, vegetarian meals
- A live browser replay through intake, frontier, and the saved trip page

What worked:
- The trip now resolves to `Mauritius family leisure trip`
- The saved trip page shows `Origin: Cape Town` and `Destination: Mauritius`
- The trip moved into a normal planning state with no missing-destination blocker

What felt good:
- The operator no longer has to explain a destination that the app should already know
- Mauritius now behaves like a real planning target instead of a blank slot

What still needs help:
- The budget is still rendered in the locale style `R 160 000`, which is readable but a little more spaced than the other compact displays

Time savers:
- The trip can now move straight into options planning
- No extra destination clarification is needed for a clearly stated Mauritius request

Time wasters:
- Treating Mauritius as unknown would have forced the agent back into unnecessary clarification

Workaround:
- Keep Mauritius in the canonical destination synonym set so the trip can progress immediately

## Scenario 39: Seychelles Resolves as a Real Destination

Who this is:
- A Nairobi agency handling a family leisure booking
- The operator needs Seychelles to resolve cleanly so the trip can move straight into planning

What I simulated:
- A fresh Nairobi-to-Seychelles family inquiry with 2 adults and 1 child
- Budget USD 12,000, 6 nights, beach resort, airport transfers, vegetarian meals
- A live browser replay through intake and into the saved trip page

What worked:
- The trip now resolves to `Seychelles family leisure trip`
- The saved trip page shows `Origin: Nairobi` and `Destination: Seychelles`
- The trip advanced to a normal planning-ready state

What felt good:
- Seychelles now behaves like a real destination instead of dropping to Unknown
- The trip shell stays consistent with the live inquiry wording

What still needs help:
- The budget line still renders as a raw USD amount rather than a more market-specific compact format

Time savers:
- No destination clarification is needed for a clearly stated Seychelles request
- The trip can move directly into options planning

Time wasters:
- Unknown destination fallback would have sent the agent back to clarification unnecessarily

Workaround:
- Keep Seychelles in the canonical destination synonym set and validate it with geography tests

## Scenario 40: Namibia Resolves in a Southern Africa Replay

Who this is:
- A Johannesburg agency handling a family leisure booking
- The operator needs Namibia to resolve as a normal destination so the trip can move directly into planning

What I simulated:
- A fresh Johannesburg-to-Namibia family inquiry with 2 adults and 1 child
- Budget ZAR 90,000, 6 nights, desert lodge, airport transfers, vegetarian meals
- A live browser replay through intake and into the saved trip page

What worked:
- The trip now resolves to `Namibia family leisure trip`
- The saved trip page shows `Origin: Johannesburg` and `Destination: Namibia`
- The trip advanced to a normal planning-ready state

What felt good:
- Namibia now behaves like a real destination instead of falling back to Unknown
- The operator can go straight to options planning

What still needs help:
- The budget display stays readable but could still be made slightly more compact for ZAR in the summary shell

Time savers:
- No destination clarification is needed for a clearly stated Namibia request
- The trip can move directly into options planning

Time wasters:
- Unknown destination fallback would have forced a needless clarification loop

Workaround:
- Keep Namibia in the canonical destination synonym set and protect it with a geography regression

## Scenario 41: Iceland Resolves as a Real Destination

Who this is:
- A Reykjavik agency handling a family leisure booking
- The operator needs Iceland to resolve as a normal destination so the trip can move directly into planning

What I simulated:
- A fresh Reykjavik-to-Iceland family inquiry with 2 adults and 1 child
- Budget USD 8,000, 5 nights, northern lights, airport transfers, vegetarian meals
- A live browser replay through intake and into the saved trip page

What worked:
- The trip now resolves to `Iceland family leisure trip`
- The saved trip page shows `Origin: Reykjavik` and `Destination: Iceland`
- The trip advanced to a normal planning-ready state

What felt good:
- Iceland now behaves like a real destination instead of falling back to Unknown
- The trip shell stays consistent with the live inquiry wording

What still needs help:
- The budget display is still a plain USD amount rather than a richer compact summary

Time savers:
- No destination clarification is needed for a clearly stated Iceland request
- The trip can move directly into options planning

Time wasters:
- Unknown destination fallback would have forced a needless clarification loop

Workaround:
- Keep Iceland in the canonical destination synonym set and protect it with a geography regression

## Scenario 42: Georgia Resolves in a Tbilisi Replay

Who this is:
- A Tbilisi agency handling a family leisure booking
- The operator needs Georgia to resolve as a real destination instead of falling back to Unknown

What I simulated:
- A fresh Tbilisi-to-Georgia family inquiry with 2 adults and 1 child
- Budget USD 6,000, 4 nights, beach resort, airport transfers, vegetarian meals
- A live browser replay through intake and into the saved trip page

What worked:
- The trip now resolves to `Georgia family leisure trip`
- The saved trip page shows `Origin: Tbilisi` and `Destination: Georgia`
- The trip advanced to a normal planning-ready state

What felt good:
- Georgia now behaves like a real destination instead of a missing placeholder
- The trip shell stays aligned with the actual request

What still needs help:
- The budget line is still a plain USD amount rather than a market-specific compact summary

Time savers:
- No destination clarification is needed for a clearly stated Georgia request
- The trip can move directly into options planning

Time wasters:
- Unknown destination fallback would have forced an unnecessary clarification loop

Workaround:
- Keep Georgia in the canonical destination synonym set and protect it with a geography regression

## Scenario 43: Bahrain Resolves in a Dubai Replay

Who this is:
- A Dubai agency handling a family leisure booking
- The operator needs Bahrain to resolve as a normal destination instead of falling back to Unknown

What I simulated:
- A fresh Dubai-to-Bahrain family inquiry with 2 adults and 1 child
- Budget AED 18,000, 5 nights, beach resort, airport transfers, vegetarian meals
- A live browser replay through intake and into the saved trip page

What worked:
- The trip now resolves to `Bahrain family leisure trip`
- The saved trip page shows `Origin: Dubai` and `Destination: Bahrain`
- The trip advanced to a normal planning-ready state

What felt good:
- Bahrain now behaves like a real destination instead of a missing placeholder
- The trip shell stays aligned with the actual request

What still needs help:
- The AED budget is readable, but the summary shell could still be more compact for a faster scan

Time savers:
- No destination clarification is needed for a clearly stated Bahrain request
- The trip can move directly into options planning

Time wasters:
- Unknown destination fallback would have forced an unnecessary clarification loop

Workaround:
- Keep Bahrain in the canonical destination synonym set and protect it with a geography regression

## Scenario 44: Accra Resolves Cleanly for a Small Ghana Agency

Who this is:
- A small Accra-based agency handling a straightforward family leisure request
- The operator needs Ghana to resolve as a real destination so the trip can move straight into planning

What I simulated:
- A fresh Accra-to-Ghana family inquiry with 2 adults and 1 child
- Budget USD 6,500, 5 nights, beach resort, airport transfers, vegetarian meals
- A live browser replay through intake and into the saved trip page

What worked:
- The trip now resolves to `Ghana family leisure trip`
- The saved trip page shows `Origin: Accra` and `Destination: Ghana`
- The trip advanced to a normal planning-ready state

What felt good:
- The app treats a simple African regional request like a normal trip instead of a special case
- The trip shell preserves the family shape, budget, and must-haves without extra ceremony

What still needs help:
- The saved trip page is clear, but the operator still has to read a few separate fields to reconstruct the full request at a glance

Time savers:
- No destination clarification is needed for a clearly stated Ghana request
- The trip can move directly into options planning

Time wasters:
- Unknown destination fallback would have forced an unnecessary clarification loop

Workaround:
- Keep Ghana in the canonical destination synonym set and protect it with a geography regression

## Scenario 45: Singapore Survives a Procurement-Heavy Mumbai Corporate Replay

Who this is:
- A larger Mumbai agency handling a corporate group and procurement-heavy quote
- The operator needs the app to keep rooming lists, procurement context, and trip purpose visible without flattening the request into a generic leisure trip

What I simulated:
- A fresh Mumbai-to-Singapore corporate inquiry with 18 travelers
- Budget USD 42,000, 6 nights, mid-to-upscale hotel blocks, airport transfers, two separate rooming lists
- A live browser replay through intake and into the saved trip page

What worked:
- The trip now resolves to `Singapore business trip`
- The saved trip page preserves `Origin: Mumbai`, `Destination: Singapore`, `Party Size: 18`, and `Trip Purpose: business`
- Group logistics survive as `2 rooming lists · Shareable with procurement`
- The live trip intake view now shows `Type: business` instead of the stale `leisure` default
- The options/strategy page now opens with a business-trip brief instead of the old generic internal-draft boilerplate
- The options brief now formats the budget cleanly as `$42,000` instead of a raw lowercase string
- The remaining operator copy now says `priorities or must-haves` instead of leaking the internal field label `Trip priorities / must-haves`

What felt good:
- The app keeps the procurement shape visible instead of collapsing it into a generic generic quote
- The Agent Operations view exposes the extracted facts clearly enough for a manager to sanity-check the run
- The strategy handoff now speaks the operator's language instead of hiding the business shape behind boilerplate
- The budget line now reads like a real planning artifact, not an unpolished string dump

What still needs help:
- The intake/summary shell still feels a little sparse for a high-context corporate quote; the operator may want the most important procurement cues surfaced even earlier

Time savers:
- The group logistics and purpose are already carried forward, so the operator can move toward options with minimal re-entry
- The saved trip page stays readable even with multiple rooming lists

Time wasters:
- If the app hid procurement context behind generic trip language, the operator would have to restate the same facts in later steps

Workaround:
- Keep the corporate extraction path explicit and continue testing it against bigger agency shapes, not just leisure-family requests

## Scenario 46: Processed Workbench Draft Survives Refresh and Promotes Cleanly

Who this is:
- A small owner-led agency operator who processed a sparse global-market inquiry and then returned to the same draft later
- The operator expects the workbench to remember the completed run and keep the trip handoff reachable after a refresh

What I simulated:
- A Lagos-to-Zanzibar family inquiry with budget NGN 2.5m, halal meals, airport transfers, and beach resort preference
- A processed draft reload in a fresh browser pass using the same authenticated profile
- Promotion of the restored draft into the saved trip workspace

What worked:
- The reloaded workbench recovered the completed trip id from the saved draft payload
- The post-run state brought back `Promote Draft` instead of collapsing to a blank intake shell
- Promoting the draft landed on `/trips/trip_c5cc2e04e021/intake`
- The trip workspace showed `Zanzibar family leisure trip`, `Ready to build options`, `5 pax`, `in Dec`, and the correct `₦2,500,000` budget

What felt good:
- The operator can leave and come back without losing the processed handoff
- The restored state keeps the workflow continuous, which matters for owner-led agencies that switch between tasks
- The saved trip page reads like the same request the operator just processed, not a new anonymous shell

What still needs help:
- The intake shell still leans on a later button click to reveal the trip workspace, so the first post-run view could be more direct

Time savers:
- The draft keeps the trip id around in its persisted run snapshot
- Promotion can happen from the restored workbench without reprocessing the inquiry

Time wasters:
- Without rehydration, a refresh would have hidden the successful run and made the operator hunt for the trip again

Workaround:
- Keep the run snapshot trip id in the workbench rehydration path so completed drafts stay actionable after reload
