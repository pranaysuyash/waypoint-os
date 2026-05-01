# Enquiry Flow E2E Report

Date: 2026-05-01  
Scope: authenticated end-to-end verification of a new Singapore enquiry through the spine run, inbox routing, and overview counts.

## Executive Summary

I created a fresh enquiry through the canonical spine path using the authenticated test user `newuser@test.com` / `testpass123`. The run completed successfully and saved a new trip:

- `run_id`: `828b4d3c-2c64-4b41-b01d-b95856ed82ea`
- `trip_id`: `trip_0bf111cd859b`
- `trip status`: `incomplete`
- `spine stage`: `discovery`
- `decision state`: `ASK_FOLLOWUP`

The flow is working end to end, but the inbox ordering is not surfacing the newest enquiry first. The new record is in the backend and counted in inbox totals, but it is not at the top of the first inbox page. The backend list ordering is effectively oldest-first in this checkout.

## User Story Tested

Input used for the test:

> Caller wants a Singapore family trip around 9-14 Feb 2025 for 5 people, not rushed; child is 1.7 years old, two parents are traveling, and they discussed Universal Studios and nature parks.

Owner note used for the test:

> Follow up within 48 hours. Confirm travel year, origin city, budget, parents mobility, stroller and nap needs, and which activities are must-haves.

## Actual Runtime Flow

1. `POST /run` accepted the enquiry and returned immediately with a queued run.
2. `GET /runs/{run_id}` completed on the first poll window.
3. The run saved a new trip in the backend.
4. The saved trip was classified as `status = incomplete`.
5. Inbox totals increased to `54`.
6. The first inbox page still showed the older `trip_ffd013835018` record, not the new enquiry.

## Evidence

### Run completion

The run completed with:

- `state = completed`
- `total_ms = 3041.7`
- `steps_completed = ["packet", "validation", "decision", "strategy"]`

The run status payload showed the expected extraction:

- `destination_candidates = ["Singapore"]`
- `date_window = around 9-14 feb 2025`
- `date_start = 2025-02-09`
- `date_end = 2025-02-14`
- `date_confidence = tentative`
- `party_size = 5`
- `trip_purpose = family leisure`
- `soft_preferences = ["Universal Studios"]`
- `decision_state = ASK_FOLLOWUP`
- `hard_blockers = []`
- `soft_blockers = ["incomplete_intake", "Temasek is currently very humid (93% relative humidity)."]`

The run status also emitted two follow-up questions:

- origin city
- budget raw text

### Saved trip

The new persisted trip is:

- `id`: `trip_0bf111cd859b`
- `status`: `incomplete`
- `created_at`: `2026-05-01T15:16:30.313007+00:00`
- `source`: `spine_api`
- `user_id`: `323468de-ba3d-437b-aa10-35b281a0c6a6`

Relevant saved extraction fields include:

- `status` on the saved trip: `incomplete`
- `extracted.facts.destination_candidates.value`: `["Singapore"]`
- `extracted.facts.date_window.value`: `around 9-14 feb 2025`
- `extracted.facts.party_size.value`: `5`
- `extracted.facts.soft_preferences.value`: `["Universal Studios"]`

### Inbox counts after the new enquiry

Authenticated inbox counts after the run:

- `GET /api/inbox?page=1&limit=1` → `total = 54`, `items = 1`
- `GET /api/inbox?page=1&limit=20` → `total = 54`, `items = 20`

Backend trip counts after the new enquiry:

- `GET /trips?page=1&limit=1` → `total = 54`
- `GET /trips?page=1&limit=100` → `total = 54`

The new trip is present in the backend list, but it is not the first item:

- `trip_0bf111cd859b` index in `/trips?page=1&limit=100`: `50`
- first items remain older records such as `trip_ffd013835018`

## Where It Should Show

The new enquiry should show in:

- Lead Inbox
- stage label: `intake`
- review state: `needs clarification` / `follow up`

It should also remain out of planning until someone starts planning or assigns it.

## Where It Is Showing

It is showing as a backend trip with:

- `status = incomplete`
- inbox classification: lead/inbox eligible
- but not surfaced at the top of the first page

That means the count is correct, but the list ordering makes the newest lead easy to miss.

## How It Moves Next

Current next step from the saved run:

1. The lead stays in Lead Inbox while the follow-up questions remain open.
2. When the operator starts planning, `Start Planning` transitions the trip into planning.
3. The planning path assigns the trip and moves it into `Trips in Planning`.

From the current code path:

- `frontend/src/components/workspace/panels/IntakePanel.tsx` uses `handleStartPlanning` to assign the lead and move it to planning.
- `frontend/src/lib/bff-trip-adapters.ts` classifies `new` and `incomplete` records as inbox trips, and `assigned` / `in_progress` as workspace trips.

## Count Mismatch Note

The user-observed mismatch is not a missing record. The record exists and the totals increased to `54`. The actual issue is ordering:

- the first inbox page still shows the older first record
- the newest enquiry is buried at index `50` of `54`

If the product expectation is "newest enquiry first", the inbox ordering needs to be changed to descending by creation time or submitted time.

## Code References

- [overview summary hook](/Users/pranay/Projects/travel_agency_agent/frontend/src/app/(agency)/overview/useOverviewSummary.ts)
- [overview page rendering](/Users/pranay/Projects/travel_agency_agent/frontend/src/app/(agency)/overview/page.tsx)
- [inbox BFF route](/Users/pranay/Projects/travel_agency_agent/frontend/src/app/api/inbox/route.ts)
- [inbox adapter and ordering logic](/Users/pranay/Projects/travel_agency_agent/frontend/src/lib/bff-trip-adapters.ts)
- [intake panel planning transition](/Users/pranay/Projects/travel_agency_agent/frontend/src/components/workspace/panels/IntakePanel.tsx)
- [spine run contract](/Users/pranay/Projects/travel_agency_agent/spine_api/server.py)
- [run contract types](/Users/pranay/Projects/travel_agency_agent/spine_api/contract.py)

## Bottom Line

The canonical create-run path is working. The new enquiry is saved and counted. The remaining problem is visibility and ordering, not persistence.
