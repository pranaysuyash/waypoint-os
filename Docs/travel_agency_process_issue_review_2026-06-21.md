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
