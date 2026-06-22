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
