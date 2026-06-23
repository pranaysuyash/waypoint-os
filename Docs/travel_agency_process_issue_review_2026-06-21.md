# Travel Agency Process Issue Review

Date: 2026-06-22

## Issue

The live intake flow was correctly recognizing non-Indian budget amounts in the browser, but it still had a currency-fidelity gap for global markets: a Lagos/Zanzibar inquiry with `NGN 2.5m` could be parsed numerically while still risking an INR fallback in downstream presentation.

## Evidence

- Live authenticated workbench on `:3101` processed the request:
  - `Family of 6 from Lagos for 8N Zanzibar in August, beachfront resort, NGN 2.5m budget, halal meals, kids activities, anniversary + family celebration.`
- The Risk Review tab showed:
  - `PROCEED_INTERNAL_DRAFT`
  - `soft_preferences`
  - `Any specific preferences or must-haves for this trip?`
- Focused tests confirmed the parser now preserves non-Indian market currency:
  - `_extract_budget("Budget NGN 2.5m")`
  - `_extract_budget("NGN 2500000 budget")`
  - `Normalizer.parse_budget("NGN 2500000")`
  - `Normalizer.parse_budget("ZAR 3000000")`

## Root Cause

`Normalizer.parse_budget()` handled compact suffix forms like `NGN 2.5m`, but plain numeric currency forms such as `NGN 2500000` could still fall through to the generic plain-number path and default to INR.

## Fix

- `src/intake/normalizer.py`
  - Preserve currency for explicit plain-number forms like `NGN 2500000` and `ZAR 3000000`
- `src/intake/extractors.py`
  - Keep the trailing-budget extraction path currency-aware for phrases like `NGN 2.5m budget`
- `tests/test_extraction_fixes.py`
  - Added regression tests for:
    - compact non-Indian market budget forms
    - plain-number currency forms
    - trailing `budget` wording with explicit currency

## Validation

- `uv run pytest -q tests/test_extraction_fixes.py -k 'budget or Budget'`
  - Passed: `18 passed`
- Live browser verification
  - The workbench completed the Lagos/Zanzibar request
  - The Risk Review tab rendered the decision state and follow-up question instead of hiding the run result

## Remaining Follow-Up

- The Trip Details drilldown now works in a fresh authenticated browser session, so the earlier route noise was a session artifact rather than a product dead end.
- The broader product takeaway is that global-market budgets need to stay market-specific all the way through the app, not just during parsing.

## Issue

The owner quote-review queue was rendering 19 indistinguishable cards with blank `id` values and `TRIP-UNKNOWN` references in the live authenticated app.

## Evidence

- Live browser session on the clean frontend port `:3101` showed the quote review queue rendering correctly as a page, but the cards were anonymous before the fix.
- Backend payload from `GET /analytics/reviews` returned 19 items with:
  - `blank_ids = 19`
  - `blank_tripIds = 19`
  - `unique_trip_refs = 1`
- After the backend fix and hot reload, the same queue showed real references like `TRIP-83C845`.

## Root Cause

`src/analytics/review.py::trip_to_review()` only used `trip["trip_id"]` to build the review identity.

Some stored trip records expose the canonical identifier as `id` instead of `trip_id`, so the mapper produced blank review ids and fell back to `TRIP-UNKNOWN`.

## Fix

- `src/analytics/review.py`
  - Use `trip.get("trip_id") or trip.get("id")` as the canonical review identity.
- `tests/test_review_logic.py`
  - Added a regression test proving `trip_to_review()` falls back to `id` and emits a stable `tripReference`.

## Validation

- `uv run pytest -q tests/test_review_logic.py`
  - Passed: `5 passed`
- Backend payload check against `GET /analytics/reviews`
  - Confirmed `count = 19`, `unique_ids = 19`
- Browser verification in original Chrome session on `:3101`
  - Quote review queue now shows real trip references and `View Details` links

## Follow-Up Validation

- `uv run python` extraction check for `Couple from Mumbai for 6N Bali in July, beach villa preference, INR 3-4L budget, vegetarian meals, anniversary trip.`
  - `party_size = 2`
  - `party_composition = {"adults": 2}`
- Backend restart on `:8000`
  - Live workbench rerun now shows `Processed successfully`
  - Trip Details tab now shows `Party Size 2` instead of blocking on the old missing-field state
  - The same run completes with validation passing and the packet showing the correct party count

## Remaining Follow-Up

- Some review cards still say `Trip details incomplete`, which is expected when destination data is missing.
- The stale `:3010` frontend server was still around during the earlier investigation, so future live checks should prefer a fresh server or confirm reload status before assuming a route is broken.

## Follow-Up Issue: Risk Review Hydration Gap

### Evidence

- In the live workbench on `:3101`, the processed couple inquiry initially showed `Processed successfully` but the Risk Review tab rendered `No risk review data yet`
- The backend run status already carried the useful decision fields:
  - `decision_state`
  - `hard_blockers`
  - `soft_blockers`
  - `follow_up_questions`
- After the workbench store was hydrated from the terminal run state, the same tab showed:
  - `Decision State`
  - the decision label
  - `Soft Blockers`
  - the follow-up question text

### Root Cause

`frontend/src/app/(agency)/workbench/PageClient.tsx` only hydrated validation, packet, and frontier from `spineRunState`.

The decision data was present in the run response, but it was not being pushed into the workbench store, so `frontend/src/app/(agency)/workbench/SafetyTab.tsx` had nothing to render when the separate trip record had not yet refreshed.

### Fix

- `frontend/src/app/(agency)/workbench/PageClient.tsx`
  - Hydrate a minimal decision object from `spineRunState` so the Risk Review tab can render immediately after a run
- `frontend/src/app/(agency)/workbench/SafetyTab.tsx`
  - Show decision state and follow-up questions even when no safety bundle is present

### Validation

- Browser verification in the live workbench on `:3101`
  - Risk Review tab now shows `Decision State`, `PROCEED_INTERNAL_DRAFT`, `Soft Blockers`, and the follow-up question
- The same run still completes successfully and the Frontier tab remains intact

### Follow-Up Note

- The terminal run status does not provide a real decision confidence score, so the UI now says `Confidence unavailable` rather than showing a synthetic `0%`

---

## Fresh Browser Recheck

### Evidence

- A clean frontend instance on `:3102` accepted the same login credentials in a fresh browser session.
- The same session processed the Lagos/Zanzibar intake through the workbench and landed on `draft_6bb50ae710ab` with `Processed successfully`.
- The app advanced into `Frontier OS` and exposed the expected post-run affordances:
  - `View Frontier`
  - `View Trip`
  - `Show run details`

### Interpretation

- The earlier `:3101` login and route noise should be treated as stale-server state rather than a product dead end.
- The underlying workbench process path is functional in a clean browser/server combination.
- Session stability is still worth watching during long simulations, but the core path is not blocked.

### Follow-Up

- Prefer a fresh frontend server when validating protected routes or replaying long simulations.
- Keep the workbench process feedback visible, because that remains the main operator trust cue during live intake.

---

## Follow-Up Issue: Quote Review Summary Backlog Mismatch

### Evidence

- In a live authenticated `:3102` browser session, the `Quote Review` page showed:
  - `Pending Quotes 22`
  - `No quotes to review`
  - `Summary counts show 22 pending quotes, but no detailed review cards are loaded in this view yet.`
- The detailed review list was empty while the dashboard-level counts came from the unified state summary.
- The empty-state copy previously told the operator to expect trips later, which contradicted the visible backlog number.

### Root Cause

- The page mixed dashboard summary counts from `useUnifiedState()` with the detailed card list from `useReviews()`.
- When the summary and detailed feed were out of sync, the page exposed an inconsistent empty state.

### Fix

- `frontend/src/app/(agency)/reviews/PageClient.tsx`
  - Added an explicit backlog explanation when summary counts exist but no review cards are loaded.
- `frontend/src/app/(agency)/reviews/__tests__/page.test.tsx`
  - Added regression coverage for the summary-backlog-empty-list case.

### Validation

- `./node_modules/.bin/vitest run "src/app/(agency)/reviews/__tests__/page.test.tsx"`
  - Passed: `3 tests passed`
- Live browser verification on `:3102`
  - The Quote Review page now explains the mismatch instead of implying that no work exists

### Follow-Up

- The page should continue to keep dashboard summary language and detailed queue language clearly separated.

---

## Follow-Up Issue: Invitation Copy Permission Noise

### Evidence

- In the live settings `People` tab on a fresh authenticated `:3102` browser session, clicking `Copy` on the workspace invitation link completed without any console warnings or errors.
- The same copy action previously produced a browser permission error in longer live sessions when `navigator.clipboard.writeText()` was attempted directly.

### Fix

- `frontend/src/lib/clipboard.ts`
  - Check clipboard-write permission before using the browser clipboard API.
  - Fall back to the textarea/`execCommand('copy')` path when permission is denied or unavailable.
- `frontend/src/lib/__tests__/clipboard.test.ts`
  - Added regression coverage for the denied-permission fallback path.

### Validation

- `./node_modules/.bin/vitest run "src/lib/__tests__/clipboard.test.ts" "src/app/(agency)/reviews/__tests__/page.test.tsx"`
  - Passed: `4 tests passed`
- Live browser verification on `:3102`
  - Clicking `Copy` on the invite link no longer surfaces console noise

### Follow-Up

- Keep using the shared clipboard helper for copy affordances so permission handling stays centralized.

---

## Follow-Up Issue: Seasonal Campaign Channel Mix Fallback

### Evidence

- The seasonal campaigns page loaded cleanly in a fresh authenticated browser session.
- A new campaign could be created, simulated, preflighted, and dry-run dispatched successfully.
- The live data payload in that first pass had no campaigns at all, so the fallback was primarily defensive against older or partially migrated records rather than a user-triggered crash.

### Fix

- `frontend/src/app/(agency)/seasons/PageClient.tsx`
  - Render `No mix set` when `channel_mix` is missing instead of assuming the field is present.
- `frontend/src/app/(agency)/seasons/__tests__/page.test.tsx`
  - Added a regression test for the missing-channel-mix render path.

### Validation

- `./node_modules/.bin/vitest run "src/app/(agency)/seasons/__tests__/page.test.tsx"`
  - Passed: `1 test passed`
- Live browser verification on `:3102`
  - Campaign creation, simulation, preflight, and dry-run dispatch all worked for a fresh `Monsoon Push` campaign

### Follow-Up

- Keep the seasonal-campaign model tolerant of older records so partial migrations don’t break the planning surface.

---

## Follow-Up Issue: Workbench Process Path and Session Stability

### Evidence

- In a fresh authenticated browser session, the small-agency intake scenario for:
  - `Couple from Mumbai for 6N Bali in July, beach villa preference, INR 3-4L budget, vegetarian meals, anniversary trip. Prefer direct flights if possible and can shift by 2 days.`
  - plus agent notes about premium inventory and margin
  saved correctly as `draft_d8fb558ed0ab` and later autosaved again as `draft_dbafd68b5b8a`.
- The audit trail shows `draft_created` events for both drafts, but no matching `draft_process_started` event appeared during the live interaction window.
- The live workbench never showed a visible `Processing…` or `Processed successfully` state while the CTA was being tested.
- After a longer interaction window, the workbench session fell back to the sign-in modal again, which interrupts the operator flow during live simulation.

### What This Means

- The draft persistence path works.
- The main workbench processing path still lacks trustworthy visible feedback in the live browser session we tested.
- Session stability needs to be treated as part of the operator experience, not just a backend concern.

### Practical Fix Direction

- Keep the draft state obvious while processing is underway.
- Make the `Process Inquiry` action unmistakably visible when it starts and when it finishes.
- Reduce session churn so an operator can complete a full intake-to-processing flow without being bounced back to sign-in mid-run.

---

## Follow-Up Issue: Auth JSON Body Serialization

### Evidence

- A fresh browser session on `:3102` initially failed login with `422` when using the shared `api.post()` path.
- The root cause was in the shared frontend API client: POST/PUT/PATCH were double-encoding the request body before sending it to the BFF.
- After the fix, a clean browser replay on `:3103` successfully logged in and reached `/overview`.

### Fix

- `frontend/src/lib/api-client.ts`
  - Move JSON serialization into the shared request layer and pass raw objects from `post`/`put`/`patch`.
  - Keep direct string bodies intact if callers ever provide them explicitly.
- `frontend/src/lib/__tests__/api-client.auth.test.ts`
  - Added regression coverage proving `api.post()` sends the login payload once, not as an escaped JSON string.

### Validation

- `./frontend/node_modules/.bin/vitest run src/lib/__tests__/api-client.auth.test.ts`
  - Passed: `2 tests passed`
- Browser replay on `:3103`
  - Login request returned `200`
  - Browser reached `/overview`

### Follow-Up

- Keep the shared API client as the only place that owns JSON body encoding, so the BFF routes continue to receive valid request bodies.

---

## Follow-Up Issue: Origin Extraction From Natural Language Intake

### Evidence

- A live New Inquiry run with the traveler phrasing `Family of 4 from Nairobi planning 7 nights in Bali in August...` initially stayed on `incomplete_intake` because origin city was not captured.
- After broadening the origin parser, the same style of input moved past the missing-origin blocker and into `PROCEED_INTERNAL_DRAFT` with `budget_feasibility` as the remaining blocker.

### Fix

- `src/intake/extractors.py`
  - Expand the origin continuation delimiter set so natural phrases like `planning`, `going`, `traveling`, `looking`, `seeking`, `staying`, and `with` do not swallow the city.
- `tests/test_extraction_fixes.py`
  - Added a regression test for `from Nairobi planning...` to lock the behavior in.

### Validation

- `./.venv/bin/pytest tests/test_extraction_fixes.py -k 'origin or hinglish'`
  - Passed: `35 passed, 146 deselected`
- `./.venv/bin/pytest tests/test_extraction_fixes.py -k 'nairobi or from_bangalore'`
  - Passed: `1 passed, 180 deselected`
- Browser replay on `:3103`
  - The same intake phrasing now resolves origin city and advances to a real decision state

### Follow-Up

- Keep origin extraction strict enough to avoid swallowing unrelated nouns, but broad enough to accept conversational intake without forcing the operator to rewrite it.

---

## Follow-Up Issue: Party Size and Budget Range Preservation

### Evidence

- A live browser replay of the family inquiry `Family of 4 from Nairobi planning 7 nights in Bali in August. Budget USD 7000-9000...` originally showed:
  - the intake processed successfully
  - but the trip page rendered `1 pax`
  - and the budget line rendered only `$7,000`
- After the extractor and display fixes:
  - the trip page now renders `4 pax`
  - and the budget line now renders `$7,000 - $9,000`

### Fix

- `src/intake/extractors.py`
  - Prefer explicit `family of N` counts over later generic child keywords.
  - Preserve range budgets as both `budget_min` and `budget_max`.
- `spine_api/contract.py`
  - Surface raw budget text when the canonical budget range is non-singular.
- `frontend/src/lib/lead-display.ts`
  - Render range budgets as a human-readable range instead of collapsing them to the first number.
- `frontend/src/lib/__tests__/lead-display.test.ts`
  - Added regression coverage for both USD and INR range formatting.
- `tests/test_extraction_fixes.py`
  - Added regression coverage for the live family-of-four replay shape.

### Validation

- `./.venv/bin/pytest tests/test_extraction_fixes.py -k 'budget_range_with_currency_parses_min_and_max or family_of_four_with_kid_friendly_language_keeps_full_party_size'`
  - Passed: `2 passed`
- `cd frontend && ./node_modules/.bin/vitest run src/lib/__tests__/lead-display.test.ts`
  - Passed: `4 tests passed`
- Browser replay on `:3103`
  - Trip page now shows `4 pax`
  - Trip page now shows `$7,000 - $9,000`

### Follow-Up

- Keep preserving explicit range semantics wherever the app summarizes customer intent.
- If later surfaces still display only the minimum budget, treat that as a display-contract choice to review, not a parser regression.

---

## Follow-Up Issue: Intake Purpose Is Too Easy to Omit in Global Scenarios

### Evidence

- A live Lagos/Zanzibar browser replay without an explicit trip purpose processed successfully but stopped at `WAITING ON CUSTOMER` with `incomplete_intake`.
- The same request with `Trip purpose: family vacation` in the agent note advanced to `PROCEED_INTERNAL_DRAFT` with `soft_preferences`.

### Why It Matters

- The app is correctly asking for the missing thing that blocks quoting, but the intake surface does not make purpose capture obvious enough for non-INR, non-template conversations.
- For global-market operators, that means an otherwise clear request can still feel stalled because the operator did not know which signal was mandatory.

### Follow-Up

- Add a clearer purpose hint or required-field cue in the intake surface so global-market requests do not bounce unnecessarily into `WAITING ON CUSTOMER`.
- Keep the follow-up wording honest, but make the pre-submit affordance more explicit for operators.

---

## Follow-Up Issue: Purpose Cue Was Documented But Not Visible Enough

### Evidence

- The post-run documentation already called out the missing global-market purpose cue.
- The live intake surface still did not make that requirement visible enough before processing.

### Fix

- `frontend/src/app/(agency)/workbench/IntakeTab.tsx`
  - Surface the canonical `trip_purpose` prompt from `frontend/src/lib/traveler-prompts.ts` in the intake helper copy.
- `frontend/src/app/(agency)/workbench/PacketTab.tsx`
  - Add `Purpose` to the summary cards so the extracted trip summary keeps the travel intent visible after processing.
- `frontend/src/app/(agency)/workbench/__tests__/IntakeTab.test.tsx`
  - Add a regression test that verifies the canonical prompt is rendered.
- `frontend/src/app/(agency)/workbench/__tests__/PacketTab.test.tsx`
  - Add regression coverage for the purpose summary card and inferred purpose visibility.

### Validation

- `cd frontend && ./node_modules/.bin/vitest run 'src/app/(agency)/workbench/__tests__/IntakeTab.test.tsx'`
  - Passed: `1 test passed`
- `cd frontend && ./node_modules/.bin/vitest run 'src/app/(agency)/workbench/__tests__/PacketTab.test.tsx'`
  - Passed: `2 tests passed`
- `cd frontend && ./node_modules/.bin/vitest run 'src/app/(agency)/workbench/__tests__/page.test.tsx'`
  - Passed: `3 tests passed`
- Live browser replay on `:3103`
  - After the run settled, clicking `Trip Details` switched the workbench to `tab=packet`
  - The packet surface showed the `Purpose` card and the extracted `family leisure` trip purpose

### Follow-Up

- Keep the intake helper copy aligned with the shared traveler prompt registry so the operator sees the same vocabulary the extraction pipeline expects.
- Keep the packet summary visible as a first-class part of the workbench handoff so the operator can revisit purpose, destination, budget, and party size after the run completes.

---

## Follow-Up Issue: Quote Review Backlog Could Look Complete When It Is Not

### Evidence

- Live browser replay on `:3103/reviews` showed `Pending Quotes 47` in the summary bar.
- The visible review card list only showed 25 loaded cards in the current view.
- Before the fix, the page did not explicitly tell the operator that the queue was showing a loaded subset rather than the full backlog.

### Why It Matters

- Owners and team leads need to know whether the queue they see is complete or partially loaded.
- If the page looks complete when it is not, people can miss approvals and lose trust in the review surface.

### Fix

- `frontend/src/app/(agency)/reviews/PageClient.tsx`
  - Add a backlog notice when the loaded review list is smaller than the summary backlog.
- `frontend/src/app/(agency)/reviews/__tests__/page.test.tsx`
  - Add regression coverage for the loaded-subset notice.

### Validation

- `cd frontend && ./node_modules/.bin/vitest run 'src/app/(agency)/reviews/__tests__/page.test.tsx'`
  - Passed: `4 tests passed`
- Live browser replay on `:3103/reviews`
  - Summary now shows `Pending Quotes 47`
  - The page now says `Showing 25 loaded quotes while the summary reports 47 pending quotes. Refresh if you expect the queue to have grown since the last load.`

### Follow-Up

- If the review backlog eventually gets server-side pagination, keep this notice aligned with the loaded page state so the operator still knows whether they are seeing the whole queue.

---

## Follow-Up Issue: Source-City Descriptors Were Polluting Destination Candidates

### Evidence

- Live browser replay on the main workbench with `Small Mumbai agency handling a family holiday for 4 adults and 2 kids from Mumbai to Bali in August 2026...` initially produced `destination_candidates = ["Mumbai", "Bali"]`.
- The workbench then asked `Between Mumbai and Bali, which are you leaning toward?`, which is wrong because Mumbai was the source city and Bali was the destination.
- A direct parser reproduction confirmed the exact sentence returned `(['Mumbai', 'Bali'], 'semi_open', 'Mumbai, Bali')`.

### Why It Matters

- The app should not force the operator to resolve a false choice that was introduced by the parser.
- Source-city noise is especially common in agency workflows because the operator often writes the city where the lead came from before the actual trip destination.
- If this stays broken, the app feels uncertain even when the human request is clear.

### Fix

- `src/intake/extractors.py`
  - Treat immediate `to` phrases as origin context.
  - Drop source descriptors like `agency`, `request`, `lead`, `team`, `office`, `market`, and `branch` when they are attached to the city mention.
- `tests/test_extraction_fixes.py`
  - Add a regression test for the exact `from Mumbai to Bali` source-city descriptor sentence.

### Validation

- `./.venv/bin/pytest tests/test_extraction_fixes.py -q`
  - Passed: `184 passed`
- Direct parser check
  - Now returns `(['Bali'], 'definite', 'Bali')`
- Live browser replay on the main workbench
  - The same request now advances to `tab=frontier`
  - The Frontier OS panel renders instead of stopping on the false destination ambiguity

### Follow-Up

- Keep source-city and agency-descriptor filtering in sync with future destination extraction changes.
- If another operator phrasing produces a false destination split, add it to the regression set immediately so the main intake handoff stays trustworthy.

---

## Follow-Up Issue: Processed Workbench State Had a Duplicate Trip CTA

### Evidence

- Live browser replay on the processed workbench state showed two `View Trip` buttons before the cleanup.
- The duplicate came from the page-level action row and the compact run-progress panel both offering the same trip-opening escape hatch.

### Why It Matters

- Duplicate actions make the result surface feel less intentional and can slow a planner down when they are scanning for the next move.
- The progress panel already owns the compact trip handoff, so the page-level duplicate was not adding new capability.

### Fix

- `frontend/src/app/(agency)/workbench/PageClient.tsx`
  - Remove the page-level `View Trip` button from the completed run action row.
- `frontend/src/app/(agency)/workbench/__tests__/RunProgressPanel.test.tsx`
  - Add a regression test that the compact result panel still shows one `View Trip` and one `View Frontier` action.

### Validation

- `./node_modules/.bin/vitest run 'src/app/(agency)/workbench/__tests__/RunProgressPanel.test.tsx' 'src/app/(agency)/workbench/__tests__/page.test.tsx'`
  - Passed: `2 passed`
- Live browser replay on the main workbench
  - `View Trip` count: `1`
  - `View Frontier` count: `1`

### Follow-Up

- Keep the page-level result row focused on actions that are not already owned by the compact run panel.
- If another duplicate escape hatch appears, prefer removing the redundant copy rather than renaming both buttons into different kinds of ambiguity.

---

## Follow-Up Issue: USD Budgets Were Being Evaluated Against INR Heuristics

### Evidence

- Live browser replay for a large agency request with `Budget is USD 42,000` initially produced a `budget_feasibility` soft blocker.
- The parser extracted `budget_min = 42000` and `budget_currency = USD`, but the feasibility rule still treated the number as if it were INR.
- After the fix, the same replay advanced to `tab=frontier` and no longer surfaced a false budget-feasibility problem.

### Why It Matters

- Global agency work often starts in USD or another non-INR currency.
- If the app compares that raw number to an INR heuristic table, it can invent a budget problem that does not actually exist.
- That breaks trust faster than a vague placeholder because it sounds authoritative while being wrong.

### Fix

- `src/intake/decision.py`
  - Skip the INR feasibility table when the extracted budget currency is not INR.
  - Return an `unknown` feasibility state instead of making a false comparison.
- `tests/test_settings_behavioral.py`
  - Add a regression test for a USD budget on a Singapore group quote.

### Validation

- `./.venv/bin/pytest tests/test_settings_behavioral.py -q`
  - Passed: `3 passed`
- `./.venv/bin/pytest tests/test_decision_rules.py -q`
  - Passed: `14 passed`
- Live browser replay on the main workbench
  - The same request now advances to `tab=frontier`
  - The false `budget_feasibility` blocker is gone

### Follow-Up

- If future currency conversion support lands, make the feasibility table explicitly conversion-aware instead of silently comparing raw numbers across currencies.
- Keep global-market agency workflows currency-sensitive at the point of decision, not only at the point of display.

---

## Follow-Up Issue: Group Booking Rooming and Procurement Details Were Missing From the Packet Summary

### Evidence

- Live browser replay for the large-agency Singapore request included `two separate rooming lists` and `shared with procurement` in the raw note.
- Before the fix, the canonical packet exposed destination, origin, dates, budget, purpose, and party size, but no rooming/procurement signal.
- The new packet summary now shows `Group Logistics` with `2 rooming lists · Shareable with procurement`.

### Why It Matters

- Large agencies need rooming-list and procurement context to reuse the packet in internal approval and contracting workflows.
- If the summary drops those signals, the operator has to reopen the raw note and manually reconstruct them.

### Fix

- `src/intake/extractors.py`
  - Capture rooming-list count and procurement-sharing intent as packet facts.
- `frontend/src/app/(agency)/workbench/PacketTab.tsx`
  - Add a `Group Logistics` summary card.
- `frontend/src/components/workspace/panels/PacketPanel.tsx`
  - Add the same `Group Logistics` summary card to the fallback packet view.
- `tests/test_extraction_fixes.py`
  - Add a regression test for the large-agency request.
- `frontend/src/app/(agency)/workbench/__tests__/PacketTab.test.tsx`
  - Add a regression test for the summary card.
- `frontend/src/components/workspace/panels/__tests__/PacketPanel.test.tsx`
  - Add a regression test for the operator fallback panel.

### Validation

- `./.venv/bin/pytest tests/test_extraction_fixes.py -q`
  - Passed: `185 passed`
- `./node_modules/.bin/vitest run 'src/app/(agency)/workbench/__tests__/PacketTab.test.tsx' 'src/components/workspace/panels/__tests__/PacketPanel.test.tsx'`
  - Passed: `8 tests passed`
- Live browser replay on the main workbench
  - Trip Details tab now shows `GROUP LOGISTICS`
  - The value reads `2 rooming lists · Shareable with procurement`

### Follow-Up

- Keep any future group-booking extraction signals in the same packet-summary pattern so the operator can scan the whole planning picture quickly.
- If later work adds rooming-list structure, preserve the concise summary card too; it is the fast scan layer.

---

## Follow-Up Issue: Draft IDs Triggered the Phone Detector in Dogfood Mode

### Evidence

- Live browser replay failed with `Detected phone number: 'draft_7384426978f4...'`.
- The string was a system-generated draft id, not a customer phone number.

### Why It Matters

- Dogfood mode should block real PII, not internal identifiers.
- A false-positive privacy block prevents real operator testing and makes the app look broken when the payload is actually safe.

### Fix

- `src/security/privacy_guard.py`
  - Ignore obvious generated ids when scanning strings for phone-like patterns.
- `tests/test_privacy_guard.py`
  - Add a regression test that a generated draft id is allowed.

### Validation

- `./.venv/bin/pytest tests/test_privacy_guard.py -q`
  - Passed: `48 passed`
- Live browser replay on the main workbench
  - The packet now persists and the Trip Details tab renders normally

### Follow-Up

- Keep the id exemption narrow so real contact information still triggers the guard.
- If new generated id formats are introduced, extend the exemption list explicitly rather than broadening the phone detector.

---

## Follow-Up Issue: Corporate Procurement Trips Were Misclassified As Cultural

### Evidence

- The live Nairobi-to-Singapore corporate replay initially showed `PURPOSE cultural` in the Trip Details tab.
- The same request clearly described a procurement-managed corporate group of 18 travelers, rooming lists, and internal approval flow.
- After the classifier fix, the live packet now shows `PURPOSE business`.

### Why It Matters

- Purpose is part of the operator’s decision frame.
- A corporate procurement quote should not be routed mentally like a sightseeing or heritage trip.
- Misclassifying the purpose can push the planner toward the wrong supplier, tone, or proposal structure.

### Fix

- `src/intake/extractors.py`
  - Recognize corporate/procurement/offsite/work-trip language as business purpose.
- `tests/test_extraction_fixes.py`
  - Add a regression test for the exact corporate-group replay.

### Validation

- `./.venv/bin/pytest tests/test_extraction_fixes.py -q`
  - Passed: `186 passed`
- Live browser replay on the main workbench
  - Trip Details now shows `PURPOSE business`

### Follow-Up

- Keep purpose inference conservative enough to avoid leisure overreach when the input mentions sightseeing as a secondary detail.
- If new business-oriented corporate phrases appear, extend the purpose lexicon with explicit tests rather than relying on generic context guessing.

---

## Follow-Up Issue: Explicit Single Destinations Were Being Downgraded By Rooming Copy

### Evidence

- The live Cape Town family-trip replay explicitly said `from Cape Town to Dubai in December 2026`.
- The packet correctly held `destination_candidates = ["Dubai"]`, but the broader destination-context ambiguity scan could still synthesize `destination_candidates / unresolved_alternatives` from nearby rooming phrasing like `family room or adjacent rooms`.
- In the browser, that pattern is exactly the kind of false detour that turns a simple quote into an unnecessary destination question.

### Why It Matters

- When the customer already named the destination, the operator should not be asked to restate it.
- False destination ambiguity wastes time and makes the intake flow feel less trustworthy.
- The issue is especially visible in small-agency family bookings, where rooming language often sits next to destination and budget in the same sentence.

### Fix

- `src/intake/extractors.py`
  - Keep contextual destination ambiguity scans limited to non-definite destination states.
- `tests/test_extraction_fixes.py`
  - Add a regression for the Cape Town to Dubai family-trip scenario.

### Validation

- `./.venv/bin/pytest tests/test_extraction_fixes.py -q`
  - Passed: `187 passed`
- Live browser replay on the main workbench
  - The real app now receives the Cape Town/Dubai input without the destination-specific regression reappearing in the packet

### Follow-Up

- Keep the destination-context scan narrow unless we have a strong reason to reopen explicit single-destination leads.
- If another adjacency pattern triggers false alternatives, add a targeted regression rather than broadening the context window again.

---

## Follow-Up Issue: Date Flexibility Was Falsely Interpreted As Budget Flexibility

### Evidence

- The live Cape Town/Dubai rerun initially produced a clean single-destination packet, but the ambiguity report still contained `budget_flexibility` because the request said `They are flexible on exact dates within the month.`
- That phrase is about timing, not budget stretch.
- After narrowing the trigger, the same replay returned an empty ambiguity report.

### Why It Matters

- Budget warnings should mean budget warnings.
- If date wording can trip budget ambiguity, the planner gets unnecessary noise on a simple family quote.
- This is especially important in small-agency work, where one line often carries destination, budget, rooming, and timing all at once.

### Fix

- `src/intake/extractors.py`
  - Only synthesize budget-flex ambiguity when budget-flex phrases are actually present.
- `tests/test_extraction_fixes.py`
  - Add a regression for the exact Cape Town/Dubai wording.

### Validation

- `./.venv/bin/pytest tests/test_extraction_fixes.py -q`
  - Passed: `188 passed`
- Live browser replay on the same scenario
  - The rerun came back with `ambiguity_report: []`

### Follow-Up

- Keep flexibility signals typed by domain, not by generic wording.
- If a new ambiguity class appears, keep the trigger tied to its own semantic domain instead of reusing a broad keyword like `flexible`.
