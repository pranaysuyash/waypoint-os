# Coming-Soon Features Revalidation (Status + Architecture + Context)

Date: 2026-05-19
Mode: Non-coding review (read-only analysis + runtime verification)
Scope: Quotes, Bookings, Payments, Suppliers, Knowledge Base, and related maps/docs/contracts

## 1) What was reviewed

Instruction/governance stack reloaded for this pass:
- `/Users/pranay/Projects/travel_agency_agent/motto_v2.md`
- `/Users/pranay/Projects/AGENTS.md`
- `/Users/pranay/Projects/travel_agency_agent/AGENTS.md`
- `/Users/pranay/Projects/travel_agency_agent/frontend/AGENTS.md`
- `/Users/pranay/Projects/travel_agency_agent/CLAUDE.md`
- `/Users/pranay/Projects/travel_agency_agent/frontend/CLAUDE.md`
- `/Users/pranay/.claude/CLAUDE.md`
- `/Users/pranay/.codex/AGENTS.md`
- `/Users/pranay/AGENTS.md`
- `/Users/pranay/Projects/travel_agency_agent/Docs/context/agent-start/AGENT_KICKOFF_PROMPT.txt`
- `/Users/pranay/Projects/travel_agency_agent/Docs/context/agent-start/SESSION_CONTEXT.md`

Implementation/runtime/docs surfaces checked:
- Frontend nav + route surfaces (`nav-modules`, app routes, shell behavior)
- Backend route surfaces (`/payments`, booking/confirmation routers)
- BFF catch-all route-map contract
- Tests (payments queue, nav contract, route-map tests)
- Exploration/research map + status/review docs with coming-soon assumptions

## 2) Direct answer: Are coming-soon features planned? Are docs present?

Yes, they are planned. Documentation exists for all five module families.

Current status is split:
- Payments is now partly implemented and enabled in nav.
- Quotes, Bookings, Suppliers, Knowledge Base remain planned at top-level module surface.

## 3) Current module inventory (runtime truth)

### Source of truth for nav state
- `frontend/src/lib/nav-modules.ts`
  - `/quotes` enabled: `false`
  - `/bookings` enabled: `false`
  - `/payments` enabled: `true`
  - `/suppliers` enabled: `false`
  - `/knowledge` enabled: `false`

### Route/runtime inventory

| Module | Nav state | Top-level route | Backend module API surface | Notes |
|---|---|---|---|---|
| Quotes | Disabled | Missing (`/quotes` returns 404) | No canonical top-level quotes module endpoint | Quote Review exists at `/reviews` but not `/quotes` module |
| Bookings | Disabled | Missing (`/bookings` returns 404) | Booking tasks + confirmations exist (trip-scoped) | Capabilities exist inside trip ops, no top-level module surface |
| Payments | Enabled | Present (`/payments` returns 200) | `GET /payments` exists (read-model) + booking-data payment patch owner | Queue/read surface now active |
| Suppliers | Disabled | Missing (`/suppliers` returns 404) | No canonical top-level suppliers module endpoint | Deep docs exist |
| Knowledge Base | Disabled | Missing (`/knowledge` returns 404) | No canonical top-level KB module endpoint | Domain helper exists, no product module |

### Key implementation evidence
- Payments frontend route exists:
  - `frontend/src/app/(agency)/payments/page.tsx`
  - `frontend/src/app/(agency)/payments/PageClient.tsx`
- Payments backend endpoint exists:
  - `spine_api/server.py` (`@app.get("/payments")`)
- Payments BFF route exists:
  - `frontend/src/lib/route-map.ts` maps `payments -> payments`
- Payment mutation owner preserved under trip path:
  - `spine_api/server.py` (`@app.patch("/trips/{trip_id}/booking-data/payment")`)

- Booking trip-scoped APIs exist:
  - `spine_api/routers/booking_tasks.py`
  - `spine_api/routers/confirmations.py`
- But no top-level `/bookings` route exists in frontend app tree.

## 4) Exploration/research map coverage and drift

Primary map reviewed:
- `/Users/pranay/Projects/exploration_maps/travel_agency_agent/EXPLORATION_MAP.md`

Relevant map entries:
- `C2. Booking & Supplier Integration` = partial
- `C2. Payments & Finance` = partial
- `R. Booking Lifecycle` = not researched in map narrative (critical)
- `AD. Travel Knowledge Domains` = not researched

### Drift found (important)

Multiple status/review docs are now stale against runtime reality for Payments.

Examples of stale assumptions still present in docs:
- Claims that `/payments` route is missing
- Claims that `/payments` nav remains disabled
- Claims that `GET /payments` backend endpoint does not exist

Files with stale payments assumptions include:
- `Docs/review/COMING_SOON_FEATURES_STATUS_ARCHITECTURE_REVIEW_2026-05-17.md`
- `Docs/review/COMING_SOON_READINESS_CONTRACT_02_PAYMENTS_2026-05-17.md`
- `Docs/review/PAYMENTS_V1_OWNERSHIP_READ_MODEL_DECISION_NOTE_2026-05-18.md`
- `Docs/review/PAYMENTS_OPEN_BLOCKERS_REVALIDATION_2026-05-18.md`
- `Docs/review/PAYMENTS_OPEN_ITEMS_WRITEUP_2026-05-18.md`
- `Docs/status/PAYMENTS_READ_MODEL_API_V1_IMPLEMENTATION_2026-05-18.md` (frontend route status line)

Conclusion: documentation has high temporal drift across 48–72 hour windows during active parallel work.

## 5) Runtime + contract evidence (live checks)

Timestamp (UTC): 2026-05-19T04:53:39Z

HTTP results:
- `200` `http://localhost:3000/overview`
- `200` `http://localhost:3000/payments`
- `404` `http://localhost:3000/quotes`
- `404` `http://localhost:3000/bookings`
- `404` `http://localhost:3000/suppliers`
- `404` `http://localhost:3000/knowledge`
- `401` `http://localhost:3000/api/payments` (auth enforced)
- `404` `http://localhost:3000/api/bookings`
- `401` `http://localhost:8000/payments` (auth enforced)

Additional BFF route-contract probes:
- `404` `/api/booking-tasks/trip_dummy`
- `404` `/api/trips/trip_dummy/confirmations`
- `404` `/api/trips/trip_dummy/execution-timeline`
- `401` `/api/trips/trip_dummy/booking-data`
- `401` `/api/trips/trip_dummy/booking-data/payment`

Interpretation:
- Payments read-model and booking-data endpoints are wired into route-map.
- Booking/confirmation/execution-timeline trip APIs are not wired in catch-all route-map and no explicit Next API routes were found for them.
- This is a contract gap between frontend client calls and BFF route registry.

## 6) Pattern-level adjacent issue discovered (systemic)

### Issue class
BFF deny-by-default + incomplete route-map coverage for APIs actively used by `api-client`.

### Evidence chain
- Catch-all explicitly denies unknown routes:
  - `frontend/src/app/api/[...path]/route.ts`
- `api-client` calls:
  - `/api/booking-tasks/{tripId}`
  - `/api/trips/{tripId}/confirmations...`
  - `/api/trips/{tripId}/execution-timeline`
- Route-map currently includes payments + booking-data, but not booking-tasks/confirmations/execution-timeline.
- Live probes return 404 on those missing mappings.

### Why this matters
This is not a one-off. It is the same root cause pattern seen whenever new APIs are added but route-map/tests are not updated as part of one contract unit.

## 7) Test evidence snapshot

Backend:
- `tests/test_payments_queue_api.py` exists and includes >5000-scope regression and validation checks.

Frontend:
- `frontend/src/lib/__tests__/nav-modules.test.ts` confirms payments enabled.
- `frontend/src/lib/__tests__/route-map.test.ts` covers payments and booking-data mappings.
- No dedicated `/payments` page test file found under `frontend/src/app/(agency)/payments`.

## 8) Readiness verdict

### Module-by-module
- Payments: **Partially ready / active**
  - Route + backend + BFF read-model are live.
  - Still exposed to broader contract-drift and missing adjacent route-map parity issues.
- Quotes: **Planned only** (docs-heavy, no top-level route/module)
- Bookings: **Partially implemented in trip context only** (no top-level module)
- Suppliers: **Planned only**
- Knowledge Base: **Planned only**

### System-level
- Architecture direction is reasonable (module-first IA + deny-by-default BFF), but execution discipline is inconsistent across doc freshness and route-map parity.

## 9) Recommended next decisions (non-coding)

1. Declare a canonical status update replacing stale Payments assumptions in all review/status docs listed above.
2. Decide whether Bookings remains trip-context-only for now or gets a top-level `/bookings` queue module in next wave.
3. Enforce “API path added => route-map + route-map tests + runtime probe” as one mandatory gate.
4. For remaining planned modules (Quotes/Suppliers/Knowledge), explicitly choose one of:
   - defer with no route placeholders, or
   - scaffold route shells with read-only safe state and contract tests.
5. Add one single “coming-soon state ledger” doc to reduce conflicting status notes across multiple files.

## 10) Bottom line

- Yes, coming-soon features are planned and documented.
- Payments has moved past “coming soon” and is now live at route + API level.
- Other modules remain planned-only at top-level UX.
- Exploration/research coverage exists, but status drift is real and currently the biggest governance risk.
- Adjacent contract risk discovered: missing BFF mappings for booking/confirmation timeline APIs despite client usage.
