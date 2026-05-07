# Travel Agency Agent - TODO List

## Immediate Product B TODOs (Queued 2026-05-07)
- [x] Lock deployment config: add `PUBLIC_CHECKER_AGENCY_ID` to `.env.example`, deployment templates, and startup runbook with SQL preflight requirement (`agencies.id` must exist).
- [x] Add API-level tests for `/api/public-checker/run`, `/api/public-checker/events`, and `/analytics/product-b/kpis` including auth failures and malformed payloads.
- [x] Run full verification sweep: full backend pytest, frontend lint + build, and one SQL-seeded end-to-end smoke run.
- [x] Eliminate environment ambiguity: choose one canonical non-prod public-checker agency id and seed it in dev/staging DB bootstrap.
- [x] KPI closure check: ensure observed revision, inferred/unknown buckets, and dark-funnel/non-return metrics are visible in dashboard/query outputs; add missing instrumentation if needed.

## Immediate server.py refactor safety gates (Phase 0, queued 2026-05-07)
- [x] Add route parity snapshot harness (`scripts/snapshot_server_routes.py`, `tests/test_server_route_parity.py`).
- [x] Add startup invariant characterization tests (`tests/test_server_startup_invariants.py`) covering file-mode skip + SQL fail-fast/success matrix.
- [x] Add OpenAPI path parity snapshot/diff check to block accidental contract drift.
- [x] Baseline and store evidence under `Docs/status/SERVER_PY_REFACTOR_PHASE0_BASELINE_2026-05-07.md` before any extraction PR.

## Completed (End-to-End Flow with Real Data)
- [x] Fixed JSON serialization errors in spine_api persistence layer
- [x] Fixed import path issues in spine_api server
- [x] Updated all frontend API routes to proxy to spine_api (no more mock data)
- [x] Implemented proper data transformation from spine_api format to frontend-expected format
- [x] Added safe nested value extraction with fallback values
- [x] Implemented correct status mapping (spine_api status → frontend state)
- [x] Verified end-to-end workflow: frontend → spine_api → storage → frontend
- [x] Confirmed real data displays correctly in frontend components

## Architecture TODOs

### Pipeline Stage Data Scope Review
- [ ] Review each pipeline stage one-by-one to define what data belongs where
- [ ] Intake stage: lightweight trip intent ONLY (who's roughly going, where, when, budget) — no full roster
- [ ] Booking stage: full traveler roster, legal names, passport numbers, DOB, relationships, third-party relationships
- [ ] Payment stage: payer details, payment allocation, EMI structure
- [ ] Pre-trip/Output stage: emergency contacts, medical info, document ownership (who holds which visa/passport/ticket)
- [ ] Design principle: "Park full people management until later stages. Don't jam it into Intake."
- [ ] See SESSION_CONTEXT.md §8 for full context on this decision

### Frontier OS Data Pipeline
- [ ] Backend: populate `frontier_result` field in API response (field exists in contract but never written)
- [ ] Frontend: call `setResultFrontier()` in useSpineRun (setter exists in store but never called)
- [ ] Backend: replace mock sentiment (keyword heuristic) with real LLM analysis
- [ ] Backend: replace mock federated_intelligence (in-memory mock) with real data sources

### Frontend Gap: Backend Endpoints Without UI
- [ ] Analytics dashboard: 12 backend endpoints with zero frontend consumer
- [ ] Settings UI: all settings endpoints unused
- [ ] Team management: all team endpoints unused
- [ ] Assignment management: assign/reassign endpoints unused
- [ ] Follow-up dashboard: management endpoints unused

---

## Pending Improvements (Optional Refinements)
- [ ] Implement proper PATCH proxy in `/api/trips/[id]/route.ts` (currently uses local updates)
- [ ] Refine inbox API enrichment logic (e.g., `daysInCurrentStage` calculation)
- [ ] Verify if empty arrays in insight endpoints reflect correct spine_api state
- [ ] Check if review data placeholder values need updating when spine_api analytics improve
- [ ] Consider adding caching layer for frequently accessed endpoints
- [ ] Add error handling improvements for API proxy failures
- [ ] Implement request/response logging for debugging API interactions
- [ ] Add validation for incoming data from spine_api before transformation
- [ ] Consider implementing retry logic for failed spine_api requests
- [ ] Add monitoring/metrics for API proxy performance

## Verification Checklist
- [ ] Manual testing: Create trip via frontend/API, verify it appears in trips list
- [ ] Manual testing: Check that trip details show real data (not mock)
- [ ] Manual testing: Verify inbox shows correct prioritization flags
- [ ] Manual testing: Confirm insights display real pipeline/summary data
- [ ] Automated testing: Ensure API route tests pass with mocked spine_api responses
- [ ] Performance testing: Verify reasonable response times for proxied endpoints
- [ ] Error testing: Confirm graceful handling when spine_api is unavailable