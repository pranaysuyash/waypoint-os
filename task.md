# Launch Readiness Remediation Task List (Post-ChatGPT Audit 2026-08-03)

## Completed Core Milestones

### Phase 1: Feature Honesty Foundation
- [x] `spine_api/core/reality_tier.py`: Reality tier enum (`REAL`, `CONNECTED_SANDBOX`, `DETERMINISTIC_PREVIEW`, `DATA_DEPENDENT`, `PLANNED`), capability matrix, `TierMetadata.for_response()`, and `assert_tier_capability()`.
- [x] `spine_api/core/feature_gates.py`: Central feature registry detailing status, data sources, and integration requirements.
- [x] `spine_api/core/startup_assertions.py`: Fail-closed boot checks (DATABASE_URL, auth safety, SECRET_KEY, ENVIRONMENT, TRIPSTORE_BACKEND).
- [x] `spine_api/core/llm_egress.py`: Single egress boundary enforcing field allowlisting, PII redaction (email, phone, passport, credit card, SSN, Aadhaar, PAN), prompt delimiters, and audit logging.
- [x] Server lifespan integration: Startup assertions & feature gates status logging registered in `spine_api/server.py`.
- [x] Unit test suites: `test_reality_tier.py` (20 tests), `test_startup_assertions.py` (17 tests), `test_llm_egress.py` (18 tests).

### Phase 2: Tenant Isolation (P0-1 Security Blocker)
- [x] Storage layer: Enforced `TripStore.get_trip_for_agency(trip_id, agency_id)` across all routers.
- [x] Public projection: Added `TripStore.get_trip_for_public_access(trip_id)` stripping internal notes, fees, and operator data.
- [x] Router audits & fixes: Updated 34 calls across `analytics.py`, `followups.py`, `inbound.py`, `legacy_ops.py`, `messaging.py`, `team_workflows.py`, `trip_actions.py`, `trip_lifecycle.py`, `trip_observability.py`, `public_checker.py`, `trust_scorecard.py`, `social_inbound.py`, `corporate.py`, `supplier.py`, `concierge.py`, `yield_arbitrage.py`.
- [x] CI gate script: `scripts/check_unscoped_trip_access.sh` (fails build if bare `TripStore.get_trip` appears in routers).
- [x] Unit test suite: `tests/test_tenant_isolation.py` (4 tests).

### Phase 3: First-Principles Feature Implementation & Exploration Docs
- [x] **Trust Scorecard**:
  - Exploration doc: `Docs/explorations/trust_scorecard_first_principles.md`
  - Implementation: `spine_api/routers/trust_scorecard.py` (computes completeness, budget fit, and honest badges from real packet data; 404 on unknown tokens)
  - Unit tests: `tests/test_trust_scorecard_honesty.py` (8 tests)
- [x] **Social Inbound**:
  - Exploration doc: `Docs/explorations/social_inbound_first_principles.md`
  - Implementation: `spine_api/routers/social_inbound.py` (sanitizes PII, routes DMs through `ExtractionPipeline` & decision rules, honest unmasked supplier details)
  - Unit tests: `tests/test_social_inbound_real.py` (4 tests)
- [x] **Corporate Duty-of-Care**:
  - Exploration doc: `Docs/explorations/corporate_duty_of_care_first_principles.md`
  - Implementation: `spine_api/routers/corporate.py` (requires JWT auth, scopes per-diem audit to agency trips, constructs cockpit from real agency trips)
  - Unit tests: `tests/test_corporate_real.py` (4 tests)
- [x] **Supplier Management**:
  - Exploration doc: `Docs/explorations/supplier_management_first_principles.md`
  - Implementation: `spine_api/routers/supplier.py` (requires JWT auth, scopes contracts/holds by `agency_id`, computes margin from real rate tables)
  - Unit tests: `tests/test_supplier_real.py` (4 tests)
- [x] **Concierge & Disruption**:
  - Exploration doc: `Docs/explorations/concierge_first_principles.md`
  - Implementation: `spine_api/routers/concierge.py` (monitors structured trip state, records rebooking proposal workflow, returns real disruptions without demo fallbacks)
  - Unit tests: `tests/test_concierge_real.py` (4 tests)
- [x] **Yield Arbitrage**:
  - Exploration doc: `Docs/explorations/yield_arbitrage_first_principles.md`
  - Implementation: `spine_api/routers/yield_arbitrage.py` (scopes trip access by `agency_id`, integrates uploaded supplier contracts, margin-sorted options)
  - Unit tests: `tests/test_yield_arbitrage_real.py` (4 tests)
