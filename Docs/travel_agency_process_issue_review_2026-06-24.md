# Travel Agency Process Issue Review - 2026-06-24

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
- The remaining simulation gap was the post-submit result surfacing from Process Inquiry, and the follow-up run showed a deeper persistence issue: the processed packet is visible in-session, but a fresh reload still falls back to the empty intake shell instead of restoring the processed packet from backend state.
- That means the live operator experience still needs durability work on the post-submit packet/review path, not just a better click path.
