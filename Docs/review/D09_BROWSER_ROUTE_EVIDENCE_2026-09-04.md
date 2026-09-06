# D-09 repair deep-link browser evidence — 2026-09-04

## Scope and claim boundary

This record covers one local, authenticated browser run of the canonical trip
intake route after the D-09 repair-link implementation. It is route-level
runtime evidence, not hosted, provider, device, screen-reader, production, or
release evidence.

The tested request was:

```text
http://localhost:3005/trips/trip_6f1c8b4e2070/intake?repair=budget
```

The browser viewport was explicitly set to **1280×900**. The run used the
project's local frontend on `:3005`, the local backend on `:8000`, and the
prescribed Playwright browser daemon/Chrome session.

## Fixture and authentication provenance

The test used a newly-created local development/test agency session through
the frontend BFF. The signup response was HTTP 201, and `/api/auth/me` was
HTTP 200. No production account, customer contact, provider account, secret,
or payment data was used or recorded here.

The fixture trip was created through the authenticated BFF pipeline rather
than inserted directly into the database:

1. `POST /api/spine/run` returned HTTP 200 with a queued run id.
2. Polling `GET /api/runs/<run_id>` returned HTTP 200 and `state: completed`.
3. The completed response persisted trip `trip_6f1c8b4e2070` for the test
   agency. The packet was `DEGRADED` with `ASK_FOLLOWUP` for the unresolved
   recommended trip-purpose detail, which is consistent with the route's
   visible “recommended details” state.

## Observed route behavior

The browser daemon navigated to the request above and loaded the real trip
intake surface. The final browser URL was:

```text
http://localhost:3005/trips/trip_6f1c8b4e2070/intake
```

This demonstrates that D-09 consumed the `repair=budget` query while
preserving the canonical route. The rendered DOM contained exactly one
`[data-intake-editor="budget"]` anchor. Its visible content included:

```text
Repair trip detail
Update the field requested by the repair link, then save the change before processing again.
Approximate budget: 500000
Save budget
Cancel
```

The active element was an `INPUT` with value `500000`, so the targeted editor
was not merely present: it was focused and ready for correction. The page also
rendered the persisted trip details (`Mumbai`, `Paris`, `2 pax`, `in Oct 2026`,
and `₹5L`) and the normal intake navigation.

The inspected runtime snapshot was:

```json
{
  "url": "http://localhost:3005/trips/trip_6f1c8b4e2070/intake",
  "viewport": {"w": 1280, "h": 900},
  "editorCount": 1,
  "active": {"tag": "INPUT", "placeholder": "Approximate budget", "value": "500000"},
  "scrollY": 0
}
```

The inspected screenshot is preserved at
[`d09-browser-budget.png`](./d09-browser-budget.png). It was visually
inspected before being treated as evidence; the repair card and focused
budget input are visible without the first-run welcome overlay.

## Local runtime observations and limitations

- `GET http://localhost:8000/health` returned HTTP 200.
- `GET http://localhost:8000/metrics` without authentication returned HTTP
  401. This is an observed auth posture and means the generic preview check
  expecting unauthenticated metrics HTTP 200 does not apply to the current
  server contract.
- Starting the backend with the prescribed command alone failed closed because
  `PROPOSAL_SIGNING_KEY` was missing. The local run was then started with
  explicit development/CI-only configuration values; no secret value is
  recorded in this document.
- `GET /api/trips` for the new test agency returned HTTP 500 while the backend
  attempted its automatic seed path: the seed trip id `trip_alpha_001` already
  existed and violated the database primary-key constraint. No database cleanup
  or deletion was performed. The D-09 evidence therefore uses the persisted
  pipeline-created trip fetched by the canonical intake route, not the broken
  list/seed path. This observation is retained as historical runtime evidence;
  it is not silently rewritten after the remediation below.
- This run does not prove save persistence after editing, downstream
  reprocessing, hosted deployment, provider behavior, production auth, mobile
  layout, or assistive technology behavior. Those remain separate gates.

## Evidence classification

- **Evidence tier:** local authenticated browser/runtime, Tier 2.
- **Sensitivity:** S2 (authenticated test data and local persistence; no
  production/customer/provider data).
- **Positive result:** canonical `?repair=budget` deep link opens the correct
  editor and focuses its editable input; query cleanup is observable.
- **Open follow-up:** verify save/reload persistence and a second repair target
  under the same authenticated route; repeat the list/seed browser check after
  the collision remediation and capture the resulting response.

No Git staging, commit, push, reset, checkout, stash, or cleanup operation was
performed for this evidence capture.

## Post-capture remediation — fixture seed collision

The collision has since been corrected in `spine_api/server.py` without
weakening row-level tenant isolation. `TripStore.get_trip()` may legitimately
return no row when the fixed fixture ID belongs to another agency; the seed
loop now treats only the database's `trips.id` duplicate-key condition as an
idempotent skip, logs the event, and continues with later fixture rows. Other
integrity failures (for example a foreign-key violation) still propagate.

Regression evidence:

- `PYTHONPATH=src .venv/bin/pytest -q tests/test_booking_data.py -k FixtureSeedingNoReassignment`
  → **3 passed** (same-agency idempotency, collision continuation, unrelated
  integrity failure propagation).
- `PYTHONPATH=src .venv/bin/pytest -q tests/test_booking_data.py`
  → **49 passed**.
- `.venv/bin/ruff check spine_api/server.py tests/test_booking_data.py`
  → **All checks passed**.

This is local Tier-1 code/test evidence. It does not yet prove the authenticated
browser `/api/trips` response after the fix, multi-worker race behavior, hosted
database behavior, or durable fixture lifecycle.

## Post-remediation browser rerun attempt — auth unavailable

On 2026-09-04, the existing Chrome tab for the captured intake route was
rechecked after the code/test remediation. The tab was reachable, but its local
auth session had expired: the rendered surface showed **“Workspace unavailable
Unauthorized”**. No new signup, credential entry, fixture creation, database
mutation, or external transmission was performed. Consequently, this attempt
does not upgrade the browser evidence tier or prove the authenticated
post-fix `/api/trips` response. A fresh authenticated local session is a
separate, explicit test setup task.
