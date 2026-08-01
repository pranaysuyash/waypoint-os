# Travel Agency Process Issue Review - 2026-06-24

## Archive Note

Archived on 2026-06-30. The replay, repair-path, and follow-up items in this review are closed, and this copy is retained only for historical reference.

## Simulation Scope

Live browser simulation of the main agency app using the real authenticated session:

- User: `newuser@test.com`
- Agency: default test agency
- Surface: agency workspace and trip workspace
- Scenario: open a trip, review the packet, edit intake details, then check the trip detail surface at narrower widths

This pass was focused on the actual app, not the public landing surface.

## Scenario Tested

Persona: agency operator handling a trip in the workspace.

Flow used:

1. Sign in to the real app.
2. Open the agency overview.
3. Open the trip workspace for an existing trip.
4. Enter intake details for the trip.
5. Review the packet / trip detail screen.
6. Shrink the viewport to simulate devtools taking space.
7. Re-check the same surface for overflow or hidden content.

## What Worked Well

- Login worked with the real test credentials.
- The agency shell and trip workspace loaded consistently.
- The trip page stayed usable when the viewport shrank to a narrower desktop split.
- There was no horizontal overflow in the live browser at the widths we verified.
- The trip detail surface still showed the main trip context, summary cards, facts table, and missing-details state clearly.

## What Did Not Work Well

- The packet / trip detail data was initially losing the manual origin edit on reload until the structured overlay fallback was added.
- The small-screen trip detail experience was readable, but the summary area was still a bit dense before the responsive tweak.

## Responsiveness Notes

Live viewport checks:

- `1280 x 720`: no overflow, shell and packet content fit normally.
- `960 x 720`: no overflow, trip layout still fit inside the viewport.
- `600 x 720`: no overflow, content still stayed visible and scrollable.

Responsive polish applied:

- Reduced the padding on the trip stage wrappers for narrow widths.
- Made the packet summary cards collapse earlier so the page feels less cramped when devtools reduce the available width.

## Time Savers

- The authenticated live session made it possible to test the real agency workspace instead of simulating against assumptions.
- The trip layout already had a proper main/rail structure, so the responsiveness issue was mostly a matter of tightening the narrow-width presentation.
- The packet panel was already organized into cards and sections, which made the small-screen refinement straightforward.

## Time Wasters

- The stale trip detail truth path created a lot of churn because the UI could show one value immediately after save and a different value on fresh read.
- Re-checking the live surface without confirming the browser viewport caused avoidable confusion.
- The browser control script initially lived outside the writable workspace, which slowed down the live probing until it was run from a writable location.

## Workarounds Used

- I verified the live browser viewport directly instead of assuming the devtools state.
- I checked the same trip surface at multiple widths rather than relying on one screen size.
- I kept the responsive tweak narrow and additive: padding and card wrapping only, no route or flow changes.

## Result

The responsive issue reported by the browser check did not reproduce as a horizontal overflow problem in the verified live session.

The trip truth gap is now handled by a durable structured-overlay fallback, so the manual origin survives a fresh backend read.

## Follow-Up

- Keep applying the same structured-overlay pattern to any future manual trip fields that must survive re-extraction.
- Keep the trip detail surface readable at narrow desktop widths.
- Re-run the same live browser flow after any persistence fix so the packet and intake screens stay aligned.

## Live Follow-Up Pass

I replayed the same main-app flow on a fresh dev server at `http://localhost:3102` because the older `3101` instance was serving a stale 500 on the workbench route.

Scenario:

1. Open a new inquiry in the workbench.
2. Submit a family trip request for Bali with a July window, INR 4 lakh budget, and family-friendly preferences.
3. Let the app return the missing-field follow-up.
4. Repair the missing origin city in the trip workspace.
5. Refresh and move into the next stage.

What worked in the live pass:

- The new inquiry flow accepted the request and produced a clear follow-up instead of failing.
- The trip workspace exposed the missing origin directly in the details panel.
- Saving `Mumbai` as the origin immediately cleared the missing-field state.
- The repaired trip moved to the "ready to build options" state.
- The options screen became reachable after the repair, which confirms the loop is usable end to end.

What was still a little rough:

- The older `3101` server was not trustworthy for replay because it returned a 500 on the workbench route.
- The workbench packet view still feels less direct than the trip workspace when the user needs to fix a missing field.
- The options screen is conservative and still labels the flow as partial intake / awaiting enrichment even after the trip has enough facts to proceed.

Time savers:

- The trip workspace already had an inline `Add origin` repair path, so the missing-field loop was one click away once I moved into the right surface.
- The structured overlay preserved the repaired origin through the fresh read.

Workaround:

- Use the workbench to capture and classify the request, then use the trip workspace as the authoritative repair surface when a concrete field needs to be added.
- Use a fresh dev server on a known-good port for replay until the stale instance is restarted or retired.

Result:

- The live scenario now has a verified repair loop from intake to trip details to options.
- The app is behaving as a coherent operator workspace, not just a capture form.

## CDP Browser Toolchain Pass

I also switched the live browser work over to the system-installed Chrome CDP skill at `/Users/pranay/Projects/external-skills/stellarlinkco__myclaude/skills/browser/` instead of the in-session Playwright browser.

Why this mattered:

- The CDP skill runs against the original Chrome profile, which is closer to the user's real working browser.
- Its `nav.cjs` helper needed a small fix to use `PUT` for Chrome's `/json/new` endpoint, otherwise new-tab navigation failed on current Chrome builds.
- Once the browser skill was usable, I could reproduce the real app flow in the user's browser environment instead of only the MCP browser session.

What the CDP pass found:

- When the backend was down, the login form rendered `Bad Gateway` instead of signing in.
- Restarting the API on `8000` cleared that failure.
- After login, the same test credentials reached the overview and workbench surfaces successfully.
- The workbench processed the family Bali inquiry and moved it to the safety tab with the expected `WAITING_ON_CUSTOMER` state and missing origin follow-up.
- The trip repair surface then accepted `Mumbai` as the origin and unlocked the next planning stage.

Why this is a better simulation:

- It exercises the original browser, persistent profile, auth state, and live backend together.
- It exposed a real operational issue first, then proved the operator flow after recovery.
- It gives us a stronger end-to-end signal than static code inspection or a synthetic browser session alone.

## Options-Stage Wording Fix

During the same replay, the options screen was still showing a stale `Partial intake — awaiting enrichment.` session goal even after the trip had been repaired and marked ready.

I fixed that by teaching the strategy preview layer to treat ready trips with stale partial-intake wording as outdated persisted draft state. After the guard landed:

- the options page showed `Present credible trip options based on confirmed requirements.`
- the suggested opening became options-oriented instead of follow-up-oriented
- the priority sequence and tone matched the ready-to-build-options state

That matters because the operator should not be mentally pulled back into intake once the trip is ready to plan.

## Shared Strategy Guard

The same stale partial-intake wording was still a risk on the workbench strategy tab because that surface was preferring the persisted trip strategy directly.

I fixed that by moving the stale-strategy decision into a shared helper and reusing it in the workbench strategy tab as well as the trip-page preview.

Why this matters:

- the operator now sees the same ready-to-plan wording whether they open the trip page or the workbench view
- stale wording no longer survives in one surface after being corrected in the other
- the UI now follows the actual trip state rather than whichever persisted draft happened to be cached first

## Live Replay Update - 2026-06-26

I ran a fresh browser simulation on the real app with the test login `newuser@test.com` / `testpass123` and a small-agency intake scenario:

- Persona: Indian agency operator handling a family leisure inquiry
- Request: 5-day Mumbai → Singapore family trip for 4 pax, mid-August, about INR 2.5 lakh, direct flights, mid-range hotel, no long transfers
- Surface: authenticated overview → workbench intake → risk review

What was good:

- The login flow now succeeds on the correct backend/runtime pair.
- The overview surface loads cleanly after sign-in.
- The workbench intake form accepts a realistic agency request and saves it as a draft.
- The risk review tab is now a real navigation target instead of a dead click target.
- The tab navigation fix is durable because it now uses real links as well as client-side routing.

What was bad:

- The first browser replay failed because port `8000` belonged to another repo’s backend process, so the app was talking to the wrong service until I moved this repo to `8001`.
- Before the tab fix, the workbench tab buttons looked clickable but did not actually switch the panel in the live browser.
- The process step still needs a cleaner end-to-end replay for the downstream result surface once the draft/run trace is rechecked from the hydrated page.

Time savers:

- Using the real login and real browser surface made the wrong-backend collision obvious immediately.
- The workbench query-state pattern was easy to isolate once the tab controls were tested against a direct URL and a live click.

Workarounds used:

- I ran this repo on `8001` and the frontend on `3103` so the live replay stayed isolated from the unrelated `oc-b2b` backend already occupying `8000`.
- I switched the workbench tabs to link-backed navigation so the browser can change state even when hydration is lagging.

Result:

- The operator workspace now has a confirmed login path, a working workbench entry point, and a reliable tab switch into risk review.
- The processed packet is now rehydrated from backend-backed draft state by resolving the completed trip id back into the workbench URL, so the packet tab survives a refresh instead of collapsing to the empty intake shell.
- The remaining operator focus is now on making that same trip-backed reload path feel obvious and polished in the live UI rather than just technically durable.

## June 24 Workbench Packet Repair Follow-Up

I implemented the June 24 packet-view follow-up so validation-blocked and missing-field states now send the operator to the authoritative trip repair surface instead of nudging them back toward New Inquiry.

What changed in the UI:

- Added a shared `getTripRepairRoute(tripId)` helper that resolves to the trip intake repair surface.
- Updated the workbench blocked-state copy so the primary action says `Open Trip Details`.
- Updated the packet-side blocked/missing-field copy to point directly at the trip details repair surface.
- Updated the trip planning CTA copy to use `Open Trip Details` wherever the authoritative repair route is shown.

Live verification:

- Backend: `http://127.0.0.1:8001`
- Frontend: `http://localhost:3103`
- Draft processed: `draft_d9f1623758f0`
- Trip created by the run: `trip_1bbacc54a58f`
- Outcome: the Bali-style missing-origin flow completed through the workbench, moved into the safety/blocked state, and the trip repair surface opened at `/trips/trip_1bbacc54a58f/intake?draft=draft_d9f1623758f0`
- Repair CTA on that trip surface now reads `Open Trip Details`

Verification notes:

- The workbench safety view showed the blocked follow-up message `Please provide origin city to generate a quote.`
- The trip intake page showed `Missing customer details` and the repair CTA to the trip details surface.
- Targeted frontend tests passed after the copy/path update.

This keeps the operator on the canonical repair path and avoids a brittle back-and-forth to New Inquiry when the actual next step is to fix trip data.

## Source Of Truth Note

The repair-path decision here was validated from the live code and browser runtime, not from documentation.

- Code now owns the canonical repair destination through `getTripRepairRoute()`.
- The live replay starts from the real New Inquiry entrypoint and creates a real trip before checking the blocked packet state.
- Docs should follow this behavior after the fact, but they do not define it.

That is the durable pattern for future follow-ups in this repo: code and runtime first, docs after verification.

## June 27 Follow-Up

I tightened the remaining workbench/trip copy drift around missing-data states:

- `PacketTab` now says `Open Trip Details` when packet data is missing and a trip exists, instead of pointing operators back at New Inquiry.
- `DecisionTab` and `SafetyTab` now show the same repair-surface CTA when they are empty but a trip context is present.
- The blocked packet banner now keeps the trip repair surface phrasing consistent across workbench and trip views.

Verification:

- Frontend focused tests passed for `PacketTab`, `DecisionTab`, `SafetyTab`, and the workbench page route behavior.
- I re-ran a Bali-style intake through the real frontend/backend contract on `http://localhost:3001` with the backend on `http://127.0.0.1:8001`.
- That run produced `trip_bfabd772eebb` with a missing `origin_city` follow-up and a live repair surface at `/trips/trip_bfabd772eebb/intake`.
- The trip intake surface showed the canonical repair affordance (`Add origin`) and the `Missing customer details` state.

The key outcome is that operators are now steered toward the authoritative trip repair surface whenever the workbench is missing the data needed to continue.

## June 28 Frontier Reload Contract Fix

I re-ran the live workbench replay against the persisted frontier trip `trip_e1e875755042` after fixing the trip-response contract to include `frontier_result`.

What I verified:

- The backend trip payload now returns `frontier_result` on `GET /trips/{id}` instead of dropping it at the response-model boundary.
- The workbench shows the Frontier OS tab for the saved trip before reload.
- The same workbench page still shows the Frontier OS tab after a refresh, with the tab selected and the Frontier analysis panel intact.

Live evidence:

- Backend trip fetch: `GET /trips/trip_e1e875755042`
- Browser before reload: `/workbench?trip=trip_e1e875755042&tab=frontier&capture_mode=call&entry=new`
- Browser after reload: `/workbench?trip=trip_e1e875755042&tab=frontier&capture_mode=call&entry=new&draft=draft_97236cd2df84`
- Saved screenshots:
  - `/Users/pranay/.dev-browser/tmp/frontier-trip-before-reload.png`
  - `/Users/pranay/.dev-browser/tmp/frontier-trip-after-reload.png`

What was good:

- The real trip payload preserved the frontier analysis, so the browser could recover it after a reload instead of falling back to the intake shell.
- The workbench kept the Frontier OS tab visible and selected across refresh, which matches the operator expectation for a completed frontier run.

What was bad:

- The first browser replay hit the onboarding modal, which blocked pointer events until I closed it.
- The earlier version of the trip response silently omitted `frontier_result`, which made the live UI appear to lose Frontier even though storage already had the data.

What saved time:

- Reusing the persisted frontier trip from the earlier live run let me verify the exact reload bug instead of synthesizing a new one.
- Checking the raw trip payload directly made the missing contract field obvious quickly.

What was a time waster:

- The modal overlay on the workbench absorbed clicks until I closed it, which slowed the first live replay.

Result:

- The workbench now recovers Frontier OS from the saved trip on refresh, so operators do not lose the intelligence tab when the page reloads.
- The contract gap is closed at the API boundary, not just hidden in the frontend.

## June 28 Persona Matrix

I also ran a broader live replay matrix to see how the workbench behaves across different agency shapes:

- Small India leisure agency: Mumbai to Singapore family trip, ₹2.5L budget, direct flights, mid-range hotel.
- Large Africa corporate agency: Nairobi to Singapore corporate offsite, procurement-managed, KES 4.8M budget.
- African family leisure: Nairobi to Zanzibar family trip, KES 480K budget, beach resort, direct flights.
- Global family leisure: Cape Town to Mauritius family trip, ZAR 95K budget, relaxed pace.

What I learned:

- The workbench consistently kept the trip context visible after processing and after reload.
- The first three persona runs landed in `Risk Review` with the Frontier tab still available on the trip, which suggests the app is conservative and wants stronger completion signals before promoting the intelligence surface.
- The global family replay stayed in `Risk Review` without exposing Frontier, because the input still carried unresolved trip ambiguity and a missing-origin warning.
- The saved Frontier trip from the earlier live run still remained the best proof of the frontier persistence path, while the matrix added breadth across regional and agency-size personas.

What was good:

- Different regions preserved their local commercial language: INR for India, KES for East Africa, ZAR for South Africa.
- The app kept trip state and reload state coherent across all four replays.

What was bad:

- The matrix showed that fairly complete-looking requests still often stall in `Risk Review`, which may be correct but feels stricter than a human operator would expect on the first pass.
- The onboarding modal is still a replay nuisance if the browser session has not already marked the welcome as seen.

What saved time:

- Reusing the same authenticated browser context let me compare multiple personas without redoing the auth flow each time.
- The trip payloads made it easy to see whether Frontier was actually preserved or whether the branch simply stayed in risk review.

What was a time waster:

- The first-login welcome modal would have blocked the matrix replay if I had not seeded the seen flag in browser storage.

Result:

- The app is now verified across several persona shapes, and the exploration map captures the regional/currency behavior as well as the current threshold for reaching Frontier.

## June 28 Welcome Card UX Fix

I changed the first-login welcome flow from a blocking modal into a floating, dismissible card so it no longer interferes with workbench replays.

What changed:

- The onboarding surface still appears for first-time authenticated users.
- It now lives as a non-modal card in the corner of the app instead of a modal that inerted the rest of the page.
- The quick links and dismissal still work, but the rest of the workbench stays interactive immediately.

Live evidence:

- Fresh browser profile with no welcome flag set showed the card text `Welcome to Waypoint` and `dialog-count 0`.
- On the same page, `Process Inquiry` remained clickable after filling the inputs.
- The replay completed normally and advanced to `/workbench?draft=draft_a956aa03f853&tab=safety&capture_mode=call&entry=new&trip=trip_35893e0b3ed2`.

What was good:

- The onboarding content still exists for first-time users.
- The app no longer hides the main workflow behind an overlay.

What was bad:

- The old modal version blocked the first action until it was dismissed, which was bad for both real users and live QA.

What saved time:

- The issue was reproducible in a clean browser profile, so I could verify the fix without guessing about cached state.

Result:

- First-login onboarding is now supportive instead of obstructive, which better fits the workbench’s “start processing right away” promise.

## June 28 Origin/Destination Fix

I also replayed a global-family note that previously produced a false destination ambiguity:

- Scenario: `Cape Town family of 4 wants Mauritius in April, ZAR 95,000 budget, relaxed pace, one resort near the beach, direct flight preferred.`
- Live app result: `Mauritius family leisure trip`
- Trip details surface: `Origin = Cape Town`, `Destination = Mauritius`

What changed:

- The intake extractor now treats a leading known city as the origin when the remainder of the note clearly contains trip-context cues or a later destination.
- The destination candidate filter now rejects that leading origin city instead of counting it as a second destination.

What was good:

- The live app processed the note cleanly once the heuristic was fixed.
- The live trip details page makes the result visible and auditable.

What was bad:

- Before the fix, the same note was turned into an ambiguous `Cape Town or Mauritius` destination choice, which is the wrong mental model for an operator.

What saved time:

- The exact scenario from the simulation reproduced the bug immediately in the extractor, so the unit fix and the live replay lined up.

What was a time waster:

- The first browser replay attempt used a stale localhost port assumption, which had nothing to do with the actual parsing bug.

Result:

- The parser now keeps origin and destination separate for this common agency-note shape, and the live browser confirms it on the trip surface.

## June 28 Corporate Ops Priorities Fix

I also replayed a corporate group note that was dropping important operational asks:

- Scenario: `Nairobi corporate offsite for 18 travelers wants Singapore in October, KES 4.8M budget, premium hotel, meeting room, airport transfers, flexible dates.`
- Live app result: the trip details page now shows `MUST-HAVES = premium hotel, airport transfers, meeting room`
- This matters because the previous pass left the must-have field empty for a corporate note that clearly had operational requirements.

What changed:

- The trip-priority extractor now recognizes operational corporate signals like `airport transfers`, `meeting room`, and `premium hotel`.

What was good:

- The live trip page now surfaces the asks where operators expect them.
- The corporate workflow stays scannable instead of forcing the team to reread the raw note.

What was bad:

- The old extraction left those requirements buried, which made the trip look less complete than it really was.

Result:

- Corporate notes now keep their operational scoping visible in the trip details surface, which makes supplier planning and quoting closer to the actual request.

## June 28 Mid-Range Hotel Fix

I replayed the small-India family note again after widening the hotel-tier extraction:

- Scenario: `Mumbai family of 4 wants Singapore in August, INR 2.5 lakh budget, direct flights, mid-range hotel, 5 nights, vegetarian meals.`
- Live app result: the trip details page now shows `MUST-HAVES = mid-range hotel, direct flights, vegetarian food`

What changed:

- The trip-priority extractor now recognizes `mid-range hotel` as a first-class accommodation tier signal.

What was good:

- The live trip view now keeps the hotel tier visible alongside flight and food constraints.

What was bad:

- Before the fix, the note only surfaced the flight and dietary priorities, which made the trip look less complete than the request actually was.

Result:

- Small family leisure requests now preserve the accommodation tier in the operator-facing trip details surface, which makes quote scoping more faithful to the original ask.

## June 28 Activity Interests Surface Fix

I replayed the corporate-offsite note after wiring the extracted activity interests into the live trip view:

- Scenario: `Nairobi corporate offsite for 18 travelers wants Singapore in October, KES 4.8M budget, premium hotel, partial sightseeing, airport transfers, flexible dates.`
- Live app result: the trip details page now shows `ACTIVITY INTERESTS = sightseeing, business offsite` as a separate card, while `ACTIVITY PROVENANCE` remains distinct.

What changed:

- `activity_interests` is now part of the canonical trip response and the intake panel reads it as its own signal.
- The trip surface labels it as derived from the intake note so operators know it came from extraction, not manual provenance entry.

What was good:

- The trip now reflects the actual activity ask from the traveler instead of leaving the section empty.
- The separate card keeps the mental model clean: interests on one side, provenance on the other.

What was bad:

- Before the fix, the page had a visible activity area that looked blank even though the extractor had already found the signal.

Result:

- Corporate trip review now preserves activity interests in the live trip surface, which makes the operator handoff more faithful to the request and easier to scan quickly.

## June 28 Welcome Card Responsiveness Fix

I replayed the app at a 390px-wide viewport and the onboarding welcome card was covering too much of the workbench controls.

What changed:

- The welcome card now renders a compact mobile banner on narrow screens and the full shortcut card only on larger screens.
- The mobile banner keeps a clear dismiss path and a small onboarding action without eating the whole screen.

What was good:

- The main workbench controls are now reachable on a narrow viewport.
- The onboarding still exists, but it no longer behaves like a modal blocker on small screens.

What was bad:

- Before the fix, the fixed welcome card was visually dominating the mobile layout and obscuring the lower workflow area.

Result:

- The first-login helper is now responsive instead of obstructive, which keeps the app usable on smaller browser windows and devtools-shrunk layouts.

## June 28 Risk Review Persistence Fix

I ran a live browser replay on `http://localhost:3103` with `newuser@test.com / testpass123` and a new Cape Town leadership-offsite scenario:

- Scenario: `London-based events team of 42 wants Cape Town in March for a leadership offsite, GBP 68k budget, premium hotel, meeting room, airport transfers, flexible dates, child-free, sunset cruise, winery visit, VIP airport fast track.`
- Live run ID: `b5eb66ff-268d-4252-94da-4e29480c2c98`
- Trip ID: `trip_c0af509ebf83`

What was good:

- The browser replay reached the workbench and the Risk Review tab.
- After the contract fix, the live page now renders the actual leaked terms list:
  - `decision_state`
  - `confidence_score`
  - `owner_constraint`
- The safety payload survives the read path now, so the leak list is visible again after a reload instead of collapsing back to a generic safe state.

What was bad:

- Before the contract fix, the trip storage contained a populated `safety` blob but `GET /trips/{id}` dropped it from `TripResponse`, so the workbench could not rehydrate safety on refresh.
- That meant the UI could show safety from a live run state, but the persisted trip read path lost the detail the operator needs later.

What was missing:

- The canonical trip response had no `safety` field even though the database record already had one.
- That made the workbench reload path incomplete and hid an important operator signal.

Result:

- `TripResponse` now includes `safety`, the frontend mirror was regenerated, and the Risk Review panel can rehydrate the actual leak list from the persisted trip instead of showing only a generic failure message.
