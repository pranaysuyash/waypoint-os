# Travel Agency Main App Issue Review

Date: 2026-06-19
Mode: Live authenticated app simulation (browser + server truth)
Files in scope:
- `frontend/src/app/(agency)/layout.tsx`
- `frontend/src/components/auth/AuthProvider.tsx`
- `frontend/src/components/overview/ActionRequiredList.tsx`
- `Docs/travel_agency_main_app_simulation_2026-06-18.md`

## What Was Run
- Re-ran the end-to-end scenario harness against the local stack with `npm run dev` on `frontend/` (Next.js on `http://localhost:3000`) and backend start command from repo root.
- Confirmed static overview component path renders locally (`frontend/src/components/overview/ActionRequiredList.tsx`) and is lint-clean after key-stability changes.
- Used the provided credentials in-session where possible: `newuser@test.com` / `testpass123`.
- Confirmed the authenticated travel app is live at `http://localhost:3001`.
- Confirmed `POST /api/auth/login` succeeds with the provided credentials and lands on the agency overview.
- Confirmed a new inquiry can be captured in the workbench and creates a draft id in the URL.
- Confirmed the workbench can enter a blocked state after processing a sample inquiry, and the blocker now reads as trip-details work rather than raw system failure text.
- Confirmed the blocked-state message now comes from a shared helper so the workbench banner and run-progress card stay aligned.
- Confirmed the Trip Details validation card now stays summary-first by default and only shows traveler prompts after the operator opens details.
- Confirmed the packet/details fallback no longer special-cases a city name for the origin source badge; any concrete origin is now labeled manual and missing origin stays system-derived.
- Confirmed the overview planning cards now collapse exact duplicates into a single grouped card with a visible matching-trip badge and grouped-count summary line.
- Confirmed the overview action queue now shows grouped quote counts explicitly, so repeated review clusters read as grouped work instead of silent duplicates.
- Confirmed incomplete planning trips now headline as `Trip details incomplete` instead of a bare trip type like `leisure`.
- Confirmed the planning badge language is now consistent across overview, trips, intake, and shell surfaces as `Missing customer details`.
- Confirmed the `/trips` page still loads after centralizing the workspace-status list in `frontend/src/lib/trip-domain.ts`.
- Confirmed the `/trips` card view now collapses duplicate workspace patterns into grouped cards with a visible grouped-count summary.
- Confirmed frontend compile path: `npx eslint src/components/overview/ActionRequiredList.tsx` succeeded after fix.
- Confirmed the live browser flow with Playwright on Chrome against `http://localhost:3001` using the same credentials.
- Live draft ids observed in this session: `draft_3f2d99fbc0c2`, `draft_e2253fc96b44`, `draft_83e0075fbfaf`.

### Current-Run Execution Notes (2026-06-19)
- Commands attempted: `TRIPSTORE_BACKEND=sql uv run uvicorn spine_api.server:app --port 8000` and `PORT=3001 npm run dev`.
- Frontend dev server is already active on `http://localhost:3001` and serves the Waypoint OS app.
- Backend health is green at `http://localhost:8000/health`.
- Login flow required actual keypress typing in the browser automation; direct fill calls left the form state empty.
- The overview page loaded with live counts and a populated queue, which means the authenticated shell is no longer the main blocker.

## Pass 1 — Dedicated Customer Scenario Simulation (Full Clickthrough)

Goal: prove whether a real agency user can complete the core flow from fresh entry to overview and key cards.

### Scenario A: Small agency, owner-only operator, India

What I simulated:
- Fresh page entry without auth state
- Login and transition into `/overview`
- Review top-priority items and missing detail cues
- Open one in-progress draft and inspect blocked/completion states

What worked:
- App correctly enforced auth when not logged in.
- Login led to stable transition once session landed and hydrated.
- Overview now lands on clear operational sections, with start-priority visible.
- The overview speaks in operator terms the owner can act on immediately: `Action Required`, `Start here`, and top-queue priority.

What was still weak:
- Initial load still expects user literacy on internal workflow labels.
- A few states are action-oriented but not yet outcome-oriented (what changes in the next 60 seconds is unclear).
- The same queue item repeats in multiple places, which increases scanning cost.

Time savers:
- `Start here` priority framing on overview.
- Clearer blocked-state text and direct recovery CTA.
- The overview immediately exposes the biggest queue pressure without forcing a deep search.

Time wasters:
- Re-checking state after each save in the same session.
- Repeated `NEED CUSTOMER DETAILS` cards and repeated `Open missing details` links make the page feel busier than the actual decision surface.

Workaround:
- Treat overview top action as the source-of-truth before scanning the rest.
- Use the top action as the daily queue anchor and ignore the lower duplicates unless you need a specific trip.

Live result:
- A thin inquiry with no origin, budget, or trip purpose information blocked immediately and told the operator to check the Trip Details tab.
- This is the right direction for a small owner-led agency: the app did not pretend the request was ready when it was not.
- The detailed field prompts are now hidden until the operator asks for them, which makes the default blocked view much easier to scan.
- The overview planning list now collapses exact duplicates into grouped cards, which removes a second source of visual repetition.
- The overview now tells the operator when it is showing grouped cards from a larger raw trip count, so the number readout is honest instead of noisy.
- Incomplete planning trips now speak in a clearer operator-facing headline, which makes the overview cards easier to scan and trust.
- Incomplete planning cards now surface the actual missing-field set instead of only the first missing badge, so the compact overview still tells the truth.
- The `/trips` card list now uses the same grouped-card logic, so the planning workspace is not a wall of repeated cards when the underlying data contains duplicates.
- The badge language now matches across the main planning surfaces, which removes a small but real mental jump between pages.

### Scenario B: Big agency, multi-agent handoff, global

What I simulated:
- Dashboard load in a multi-task context
- Repeated content updates and refresh-like state transitions

What worked:
- Core shell and hydration are now stable and not permanently blocked.
- Protected pages maintain auth boundary integrity.
- The queue model scales to a high-volume shop: counts, urgency, and next actions are visible without opening a deep search UI.

What was still weak:
- Action states can still feel like pipeline status text rather than operational intent.
- Repeated asynchronous card refreshes produce a perception of “loading tax” in high-churn states.
- The busy overview can make a large agency feel even more overloaded if the same trip surfaces repeatedly.

Time savers:
- Deterministic route-level loading/summary pattern gives predictable pacing.
- The `Action Required` section gives a quick command center for the day.

Time wasters:
- Re-reading queue metadata to infer priority vs urgency.
- Duplicate-looking rows make it harder for a multi-agent team to trust what is unique versus repeated.

Workaround:
- Use the highest-priority action as execution anchor during high volume.
- Treat the top queue as the handoff contract and only drill into repeats when ownership is unclear.

Live result:
- A fuller inquiry with budget, travel window, and preferences got past initial capture and moved into processing before asking for remaining trip details.
- That means the workbench can support a larger team’s rhythm: quick intake first, then a clear handoff back to details when the request is still incomplete.
- The action queue now shows a count badge on grouped quote work, which makes the repeated review cluster readable instead of feeling like a duplicate list.
- The `/trips` page now shows grouped workspace cards and a grouped-count summary, which keeps the planning view readable even when the source data accumulates many repeated patterns.
- The same planning badge now reads `Missing customer details` across the overview, trips, intake, and shell context, which keeps the operator in one vocabulary.

### Scenario C: India-focused agency, mixed visa/passport handling, high ambiguity

What I simulated:
- Repeated auth/me and overview actions in the same session
- State transitions in incomplete trip capture

What worked:
- Auth refresh path is usable at runtime and does not force hard failure in normal path.
- The intake surface supports a real human request style and carries the right travel-specific prompts.

What was still weak:
- The app can surface a valid authenticated context but user-facing text still carries internal jargon in some branches.
- Processing a sample inquiry lands in a blocked state without a very explicit plain-language reason.

Time savers:
- Recovery cues after partial save point to concrete next steps.
- The intake form already tells the agent what belongs in customer language versus internal notes.

Time wasters:
- Distinguishing “status” from “next agent action” still requires memory of internal language.
- A blocked outcome with no reason text slows down a solo operator trying to rescue the draft quickly.

Workaround:
- Train teams to use top-priority banner + next-step text as immediate execution signal.
- Keep the customer message and agent notes short and specific so the processor has enough signal to work with.

Live result:
- The sample India-style inquiry surfaced missing origin, budget, and trip purpose fields in plain language.
- The new copy makes the missing information feel like a checklist, not a dead end.
- The field prompts only appear after expanding the validation details, which keeps the default card readable for first-time operators.

### Scenario D: Africa-focused agency, connectivity- and time-zone-aware operations

What I simulated:
- Standard app navigation and protected endpoint behavior
- Revisit patterns after token expiry path

What worked:
- Session logic recovers when valid refresh credentials are present.
- The login/session path is straightforward and the app snaps back into the workspace quickly.

What was still weak:
- No visible network-quality fallback state for slow links; user may misread transient refresh delays as functional failure.
- The processing surface does not yet explain slow or blocked states in a way that helps remote teams self-correct.

Time savers:
- Predictable shell flow and protected-page handling.
- Fast entry back into the workspace after signing in.

Time wasters:
- Multiple retry loops with only error-toasting can feel opaque.
- A blocked processing state without a short reason line would cost more for distributed teams than for local ones.

Workaround:
- Keep an explicit fallback path in playbook: re-login flow if refresh repeatedly fails.
- Use a team convention for what `Blocked` means until the UI explains it better.

Live result:
- The richer Nairobi-to-Zanzibar example did not break the app; it started processing normally and then returned to the exact missing details the team would need to finish the quote.
- That is a good fit for distributed teams because it preserves momentum without hiding incompleteness.
- The cleaner collapsed default means multi-agent teams can scan the blocker quickly and only expand when they need the prompt-level guidance.
- The same grouped-card behavior keeps repeated planning patterns from overwhelming the overview.
- The grouped-count summary makes the difference between raw queue volume and visible cards obvious at a glance.
- The planning card headline now uses `Trip details incomplete` for incomplete trips, which is clearer than a raw trip type.

### Scenario E: Global distributed team, multiple operators

What I simulated:
- Repeated sign-in and overview entry over one long session
- Quick context handoff from one task to another

What worked:
- Auth/session boundary allows real operators to keep working from the same canonical login pattern.
- The overview is strong enough to support a shared command-center model.

What was still weak:
- No hard guarantee that queue labels are unambiguous across regions/teams.
- Duplicated rows and terse queue copy can make team handoff slower than it needs to be.

Time savers:
- Single canonical authenticated workspace and shared overview.
- One place to see live work instead of multiple disconnected status pages.

Time wasters:
- Manual interpretation of queue names to infer urgency in cross-team environments.
- Wasting time deciding whether repeated cards represent separate work or the same work repeated.

Workaround:
- Define team-level interpretation rules in onboarding docs and training.
- Establish a single rule for ownership and repeats, then teach the team to trust that rule.

Live result:
- In a global-team framing, the app now gives a shared command-center view, then drops the operator back into trip-specific details when the request is not ready.
- That keeps ownership localized without forcing everyone to decode a generic failure state.
- Quote-review clusters now carry an explicit matching-count badge, which helps cross-team operators distinguish grouped work from single-item work at a glance.

## Pass 2 — UX, Features, and Agent Role Simulation

### UX Pass Findings
- Good: higher-priority action now appears without requiring full screen scan.
- Good: blocked state is more recoverable.
- Weak: some labels still speak like process stages rather than human outcomes.
- Good: the overview now behaves like a control room instead of a blank dashboard.
- Weak: repeated items still make the page feel busier than the actual day’s work.

### Feature Pass Findings
- Good: onboarding and save recovery are materially improved in guided context.
- Good: queue-first UX is stronger for daily ops.
- Weak: action-result confirmation is still partially generic in edge flows.
- Good: new inquiry intake can capture a realistic travel request and route it into a draft.
- Good: blocked processing now explains the missing trip details in plain language.

### Agent Role Pass Findings
- Good: app supports internal operator reality, not just traveler surface.
- Weak: role transition from capture → planning → execution still has hidden context switches.
- Good: the app makes sense for an owner/operator at a small agency and still scales to a high-volume queue.
- Weak: first-time operators may still need orientation to understand where the next action lives.

## Known Remaining Technical Gaps (from live trace and UI run)

1. Clipboard permission failures on some secure contexts (`Failed to execute 'writeText'`).
   - Risk: copy/paste workflows become fragile in certain browser/device policies.
   - Priority: P2 (UX reliability, mostly env-dependent).

2. HMR websocket logs in dev environment noise (`ws://127.0.0.1:3101/_next/webpack-hmr` handshake errors).
   - Risk: debug signal-to-noise; not a blocking runtime issue.
   - Priority: P3 (diagnostic clarity).
3. Workbench processing now shows trip-detail guidance, and the default view is compact; the full field list is still available on demand for deeper follow-up.
   - Risk: operators cannot tell whether the draft is missing fields, waiting on the pipeline, or genuinely failed.
   - Priority: P1 (operator clarity).
   - Status: shared helper implemented and verified on live blocked runs; the compact default remains intact as the details view grows.

4. Overview and action-queue repetition can still feel dense when the queue is genuinely large, but exact duplicates and grouped clusters are now labeled.
   - Risk: dense queues still require scanning skill even after collapse.
   - Priority: P2 (scannability).
   - Status: grouped-card dedupe and quote-count badge implemented and live-verified.

## Fresh Live Validation Addendum (2026-06-23)

Scenario:
- Large Nairobi agency handling a corporate quote for 18 travelers to Singapore in October 2026
- Budget: USD 42,000
- Logistics: 6 nights, mid-to-upscale hotel blocks, airport transfers, two rooming lists, fast quote for procurement

What worked:
- The workbench accepted the intake and kept the customer request separate from the internal agent note
- A direct form submit produced both `POST /api/drafts` and `POST /api/spine/run`
- The draft advanced into a visible processing state and then into the safety/decision workspace
- The live result showed `PROCEED_INTERNAL_DRAFT`, a `soft_preferences` blocker, and a concrete follow-up question
- `View Trip` and `View Frontier` gave immediate next actions after processing

What felt good:
- The app preserves the commercial shape of the request, which matters for procurement-heavy group quotes
- The operator can see that the system is moving, not just saving text
- The decision state is clear enough to use even when the safety bundle is not available

What still needs help:
- The safety bundle was not present for this run, so the operator must interpret the decision state manually
- The follow-up question is good, but it still places a small reading burden on the agent when a quote is nearly ready
- The itinerary-mismatch detector now catches the live `hotel check-in is afternoon on 10 July` phrasing, and the trip intake page now echoes it in a compact critical-issue card, but the safety/workbench view is still the clearest first-glance surface
- The corporate quote now preserves rooming-list detail on the trip page as `Group logistics`, but that signal still lives below the top blocker strip rather than in the very first line of the trip shell

Time savers:
- `View Trip` and `View Frontier` are immediate handoff actions
- The draft id appears quickly, which keeps the work anchored to one record

Time wasters:
- If the operator has not supplied must-haves, the system still pauses at the follow-up question before it can finalize the quote direction

Workaround:
- Use the follow-up question as the exact prompt for the customer or account owner
- Treat the decision state as the operator truth source when the safety bundle is missing

## Fresh Live Validation Addendum: Beach Resort Is Not a Destination

Scenario:
- Small Nairobi agency handling a family holiday from Nairobi to Zanzibar in August 2026
- Budget: KES 480,000
- Preferences: 6 nights, beach resort, airport transfers, vegetarian meals

What broke:
- The destination parser treated `Beach` as a second destination candidate alongside `Zanzibar`
- That forced the workbench to ask an unnecessary `Between Zanzibar and Beach` follow-up

What we fixed:
- Added a generic-amenity exclusion for destination candidates
- Wired that exclusion into both the main destination match path and the fallback path

What the browser now shows:
- The saved trip page reads `Zanzibar family leisure trip`
- The options page now shows `Generate internal trip draft with documented assumptions for agent review.`
- The workbench no longer surfaces the bogus two-choice destination prompt

Why this matters:
- Beach preference should stay a preference signal, not become a competing trip target
- The operator should not have to mentally filter out amenity words before planning starts

## Fresh Live Validation Addendum: KES Budgets Should Stay KES

Scenario:
- Nairobi family leisure replay for Zanzibar
- Budget: KES 480,000

What broke:
- The trip page rendered the budget as `₹4.8L`, which made the African-market request look like an INR trip

What we fixed:
- Added KES to the shared frontend currency helper
- Taught budget parsing to recognize `KSh` and `KES`
- Standardized KES display so the UI now renders `KSh480,000`

What the browser now shows:
- The saved trip page reads `KSh480,000`
- The surrounding trip summary still shows Zanzibar, origin Nairobi, and family leisure context

Why this matters:
- Budget currency is part of the trip’s commercial truth
- Converting it implicitly can mislead the operator and distort quote judgment

## Fresh Live Validation Addendum: Mauritius Must Be a Known Destination

Scenario:
- Cape Town family leisure replay for Mauritius
- Budget: ZAR 160,000

What broke:
- The extractor returned `destination = Unknown` even though the request said `from Cape Town to Mauritius`

What we fixed:
- Added Mauritius to the canonical destination synonym set
- Added a regression test that proves Cape Town to Mauritius resolves correctly

What the browser now shows:
- The trip page reads `Mauritius family leisure trip`
- Origin is `Cape Town`
- Destination is `Mauritius`

Why this matters:
- A clearly stated country destination should not require extra clarification
- Mauritius is a real planning target and should behave like one in the canonical trip flow

## Fresh Live Validation Addendum: Seychelles Must Resolve Cleanly Too

Scenario:
- Nairobi family leisure replay for Seychelles
- Budget: USD 12,000

What broke:
- The extractor initially returned no destination candidates, which forced the trip into a missing-destination state

What we fixed:
- Added Seychelles to the canonical destination synonym set
- Added a geography regression to keep Seychelles resolvable

What the browser now shows:
- The trip page reads `Seychelles family leisure trip`
- Origin is `Nairobi`
- Destination is `Seychelles`

Why this matters:
- Seychelles is a real, common trip target in this market
- The canonical destination layer should keep up with the destinations the app is meant to support

## Fresh Live Validation Addendum: Namibia Must Resolve Cleanly

Scenario:
- Johannesburg family leisure replay for Namibia
- Budget: ZAR 90,000

What broke:
- The extractor returned no destination candidates, which forced the trip into a missing-destination state

What we fixed:
- Added Namibia to the canonical destination synonym set
- Added a geography regression for Johannesburg to Namibia

What the browser now shows:
- The trip page reads `Namibia family leisure trip`
- Origin is `Johannesburg`
- Destination is `Namibia`

Why this matters:
- Namibia is a common regional travel target and should resolve the same way as the other supported destinations
- The trip should not need extra clarification when the destination is already explicit

## Fresh Live Validation Addendum: Iceland Must Resolve Cleanly

Scenario:
- Reykjavik family leisure replay for Iceland
- Budget: USD 8,000

What broke:
- The extractor returned no destination candidates, which forced the trip into a missing-destination state

What we fixed:
- Added Iceland to the canonical destination synonym set
- Added a geography regression for Reykjavik to Iceland

What the browser now shows:
- The trip page reads `Iceland family leisure trip`
- Origin is `Reykjavik`
- Destination is `Iceland`

Why this matters:
- Iceland is a common travel destination and should resolve without extra clarification
- The canonical destination layer should keep pace with the markets the app is intended to serve

## Fresh Live Validation Addendum: Georgia Must Resolve Cleanly

Scenario:
- Tbilisi family leisure replay for Georgia
- Budget: USD 6,000

What broke:
- The extractor returned no destination candidates, which forced the trip into a missing-destination state

What we fixed:
- Added Georgia to the canonical destination synonym set
- Added a geography regression for Tbilisi to Georgia

What the browser now shows:
- The trip page reads `Georgia family leisure trip`
- Origin is `Tbilisi`
- Destination is `Georgia`

Why this matters:
- Georgia is a real travel destination and should resolve without extra clarification
- The canonical destination layer should keep up with the markets the app is meant to serve

## Fresh Live Validation Addendum: Bahrain Must Resolve Cleanly

Scenario:
- Dubai family leisure replay for Bahrain
- Budget: AED 18,000

What broke:
- The extractor returned no destination candidates, which forced the trip into a missing-destination state

What we fixed:
- Added Bahrain to the canonical destination synonym set
- Added a geography regression for Dubai to Bahrain

What the browser now shows:
- The trip page reads `Bahrain family leisure trip`
- Origin is `Dubai`
- Destination is `Bahrain`

Why this matters:
- Bahrain is a real regional travel destination and should resolve without extra clarification
- The canonical destination layer should keep up with the markets the app is intended to serve

## Fresh Live Validation Addendum: Ghana Must Resolve Cleanly Too

Scenario:
- Accra family leisure replay for Ghana
- Budget: USD 6,500

What broke:
- The extractor had been missing several real country destinations in this region cluster, which would have turned a normal request into a clarification loop

What we fixed:
- Added Ghana to the canonical destination synonym set
- Added a geography regression for Accra to Ghana

What the browser now shows:
- The trip page reads `Ghana family leisure trip`
- Origin is `Accra`
- Destination is `Ghana`

Why this matters:
- Small local agencies should not have to re-explain an obvious Ghana request just to get the trip into planning
- The canonical destination layer should keep up with the markets the app is intended to serve

## Fresh Live Validation Addendum: Croatia Must Resolve Cleanly Too

Scenario:
- Zagreb family leisure replay for Croatia
- Budget: EUR 4,800

What broke:
- The extractor had also been missing some Europe-region destinations that real agencies would treat as ordinary trip targets

What we fixed:
- Added Croatia to the canonical destination synonym set
- Added a geography regression for Zagreb to Croatia

What the browser now shows:
- The trip page reads `Croatia family leisure trip`
- Origin is `Zagreb`
- Destination is `Croatia`

Why this matters:
- Regional Europe requests should resolve the same way as the better-covered destinations
- The operator should not lose time on destination clarification when the traveler already named the country clearly

## Fresh Live Validation Addendum: Corporate Procurement Replay Stayed Intact

Scenario:
- Mumbai corporate group replay for Singapore
- Budget: USD 42,000

What we verified:
- The app preserved `Trip Purpose: business`
- The app preserved `2 rooming lists` and `Shareable with procurement`
- The saved trip page stayed planning-ready instead of flattening the request into a generic leisure quote

Why this matters:
- Larger agencies need the app to keep procurement shape visible all the way through intake
- The operator should not have to re-enter rooming-list or procurement context after the first pass

## Fresh Live Validation Addendum: Corporate Trip Type Now Reads Correctly

Scenario:
- Mumbai corporate group replay for Singapore
- Budget: USD 42,000

What broke:
- The trip intake page was still showing `Type: leisure` even though the live request was a corporate quote with `tripPurpose: business`

What we fixed:
- Updated the canonical trip-field resolver so `tripType` now follows the stored business purpose instead of falling back to the default leisure label
- Added a roundtrip regression that asserts `tripType == business` after patching `tripPurpose = business`

What the browser now shows:
- The trip intake page reads `Type: business`
- Purpose remains `business`

Why this matters:
- The operator-facing label should not contradict the actual request shape
- Corporate quotes need to read as corporate at a glance, not as leisure work with a business note attached

## Fresh Live Validation Addendum: Strategy Handoff Now Speaks Corporate Language

Scenario:
- Mumbai corporate group replay for Singapore
- Budget: USD 42,000

What broke:
- The strategy/options page was still showing the old generic internal-draft boilerplate even after the rest of the trip had enough context to talk about a business brief

What we fixed:
- Taught the strategy preview and backend strategy builder to recognize corporate context from trip purpose and group size
- Taught the strategy tab to prefer the smarter preview when the stored strategy is just the stale boilerplate
- Cleaned up the remaining operator-facing wording so the priority/assumption copy now reads `priorities or must-haves` instead of echoing the raw internal field label

What the browser now shows:
- Session goal: `Prepare a clear options plan for Singapore for the business trip while keeping budget usd 42,000 aligned.`
- Suggested opening: `Here’s the options plan for Singapore with the business requirements in view.`
- Priority sequence now starts with the corporate/group shape instead of the generic draft boilerplate
- The budget line now renders as `$42,000` instead of a raw lowercase input string

Why this matters:
- Operators should see the business framing immediately when they open options
- The first read on the strategy page should help the agent act, not make them decode stale internal boilerplate
- A clean budget line helps the options page feel trustworthy at a glance
- Operator wording should sound like a planning conversation, not a schema dump

## Fresh Live Validation Addendum: Processed Draft Handoff Survives Refresh

Scenario:
- Lagos-to-Zanzibar family inquiry with sparse trip purpose
- Budget: NGN 2.5m

What broke:
- The workbench showed a successful processed run in one session, but reopening the same draft lost the post-run trip handoff because the completed trip id only lived in local UI state

What we fixed:
- Rehydrated the completed trip id from the persisted draft payload, preferring `promoted_trip_id` and then the latest `run_snapshots[].snapshot.trip_id`
- Exposed the helper through the page entrypoint so the same logic can be tested directly

What the browser now shows:
- Reopening the same draft restores `Promote Draft`
- Promoting the restored draft lands on `/trips/trip_c5cc2e04e021/intake`
- The trip workspace shows `Zanzibar family leisure trip`, `Ready to build options`, `5 pax`, and `₦2,500,000`

Why this matters:
- A processed draft must stay actionable after refresh, not evaporate into a blank intake shell
- Operators should be able to come back later and continue the same real trip without re-running the workflow

## Prioritized Follow-up (motto_v3, 1st-principles)

1. P1: Improve top-level result phrasing to map directly to operator action, not internal process names.
   - Output: stronger completion confidence within 5 seconds of each save/action.

2. P1: Add concise, explicit recovery copy for auth-refresh edge cases.
   - Output: eliminate ambiguity between temporary and terminal auth failures.

3. P1: Explain blocked inquiry processing in plain language right where the blocker occurs.
   - Output: one-line reason plus next action.

4. P2: Standardize cross-agent role handoff labels in overview queues.
   - Output: fewer regional misinterpretations.

5. P3: Reduce non-critical dev console noise in local run documentation.
   - Output: cleaner production-adjacent simulation logs for faster debug.

## Decision
The main app is now usable as an authenticated production-leaning workspace. The next highest-value work is not more shell polish; it is making blocked states and repeated queue rows explain themselves in plain operator language so the first five seconds feel trustworthy.
