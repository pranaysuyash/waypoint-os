# Trip State Contract — Implementation Plan

**Status:** Phase 1 + Phase 1.5 + Phase 2A + Phase 2B + Phase 3A + Phase 3B + Phase 4A complete
**Created:** 2026-05-02
**Updated:** 2026-05-03
**Scope:** Persistence repair, encryption, stage/readiness model, ops panel, booking data, customer collection

---

## Context

The pipeline produces 9 compartments of state, but only 4 are persisted to the database. After a page refresh, the UI shows a different product than what the pipeline actually computed. This is a state-contract bug, not a missing-field bug.

The fix is not "add five JSON columns." It is: define the persisted trip state contract, implement it, encrypt PII-bearing compartments, and add regression tests for refresh parity.

---

## Compartment Registry

Every field the pipeline emits, its classification, and persistence behavior:

| Field | Producer | Consumer | Stages | PII Class | DB Column | Encrypted | Hydrated on Refresh | In Logs? | Frontend Exposure |
|:---|:---|:---|:---|:---|:---|:---|:---|:---|:---|
| `packet` | ExtractionPipeline | PacketPanel, all panels | all | Medium (names, phones) | `extracted` | Yes | Yes | Redacted | Full |
| `validation` | NB01CompletionGate | PacketPanel, DecisionPanel | all | None | `validation` | No | Yes | Yes | Full |
| `decision` | NB02JudgmentGate | DecisionPanel, StrategyPanel | all | None | `decision` | No | Yes | Yes | Full |
| `strategy` | build_session_strategy() | StrategyPanel | shortlist+ | None | `strategy` | No | Yes | Yes | Full |
| `traveler_bundle` | build_traveler_safe_bundle() | OutputPanel, customer | proposal+ | Low (names in context) | `traveler_bundle` | Yes | Yes | Redacted | Customer-safe |
| `internal_bundle` | build_internal_bundle() | OutputPanel, agent | proposal+ | High (margin, vendor, ops) | `internal_bundle` | Yes | Yes (agent only) | No | Agent-only |
| `safety` | check_no_leakage() | SafetyPanel | all | Medium (may flag medical/visa) | `safety` | Yes | Yes | Redacted | Agent-only |
| `fees` | calculate_trip_fees() | OutputPanel, future OpsPanel | proposal+ | Medium (commercial) | `fees` | Yes | Yes | No | Agent-only |
| `frontier_result` | run_frontier_orchestration() | FrontierDashboard | all | High (sentiment, intel) | `frontier_result` | Yes | Yes | No | Agent-only |
| `booking_data` | Agent/OpsPanel edit | OpsPanel | proposal, booking | Critical (passports, DOB) | `booking_data` | Yes (blob) | Lazy (OpsPanel only) | No | Agent + owner |
| `pending_booking_data` | Customer form submission | OpsPanel (review) | proposal, booking | Critical (passports, DOB) | `pending_booking_data` | Yes (blob) | Lazy (accept/reject only) | No | Agent + owner |
| `booking_data_source` | Accept action | OpsPanel (badge) | proposal, booking | Low (provenance) | None | No | Yes | Yes | Agent |

### Authority hierarchy
```
Docs/TRIP_STATE_CONTRACT.md  →  human-readable authority
contract.py / packet_models.py / validation.py  →  executable authority
refresh parity tests  →  behavioral authority
```

---

## Codebase Reality (verified)

### Current persistence gap

Both `save_processed_trip` calls in `server.py` (lines 1017-1034 and 1079-1095) pass dicts with only: `packet`, `validation`, `decision`, `strategy`, `meta`. Five compartments are computed but never persisted.

### Existing infrastructure
- **Encryption**: Fernet (AES-128-CBC) in `src/security/encryption.py`. Dual model: blob encryption for private compartments, recursive PII-key encryption for shared fields.
- **Audit**: `RunLedger` = per-run execution trace (file-based). `AuditStore` = trip lifecycle events (file-based). RunLedger for runs, AuditStore for business events.
- **Stage model**: `CanonicalPacket.stage` has `discovery`/`shortlist`/`proposal`/`booking`. Validation has `INTAKE_MINIMUM` (2 fields) and `QUOTE_READY` (6 fields).

### Encryption model

Two tiers, enforced by `_encrypt_field_for_storage` / `_decrypt_field_from_storage`:

| Tier | Fields | Method | Stored shape |
|:---|:---|:---|:---|
| Private blob | `traveler_bundle`, `internal_bundle`, `safety`, `fees`, `frontier_result`, `booking_data`, `pending_booking_data` | Entire JSON → single Fernet token | `{"__encrypted_blob": true, "v": 1, "ciphertext": "..."}` |
| PII-key redaction | `extracted`, `raw_input` | Recursive: encrypt string values whose key is in `_PII_FIELDS` | Same JSON structure, PII values replaced with tokens |
| None | `validation`, `decision`, `strategy`, all scalar fields | Plaintext | As-is |

### Persistence paths

| Path | Compartments persisted | Reason |
|:---|:---|:---|
| Authenticated `/run` (normal + partial) | All 9 | Full agent pipeline |
| Public checker `/api/public-checker/run` | 5 only (`packet`, `validation`, `decision`, `strategy`, `meta`) | Customer-facing, no agent-only private compartments |
| `update_trip()` | Same encryption as `save_trip()` via unified helper | Prevents bypass |

### Flat JSON vs. split tables

**Stay flat for now.** Single `trips` table with encrypted JSON columns.

Exit criteria for splitting into `trip_state`, `trip_private_state`, `booking_data`:
- Real PII pilot begins
- Multiple roles/permissions need field-level access
- Reporting/querying across private state
- Customer-facing document collection
- Audit/compliance obligations

---

## Implementation Phases

### Phase 1: Persistence Repair + Encryption (one merge) — IMPLEMENTED

All 5 missing compartments fixed together. Dual encryption model: blob encryption for private compartments, PII-key encryption for shared fields.

**Status:** Code complete. All 5 blockers from ChatGPT review resolved:
1. Private compartment blob encryption (not just key-level PII)
2. `update_trip()` uses same unified encryption helper as `save_trip()`
3. Public checker reduced persistence contract documented
4. BFF adapter maps all compartments including `strategy`, `traveler_bundle`, `internal_bundle`
5. `resetAll()` clears `result_fees`
6. Sentinel encryption tests verify no plaintext in encrypted storage

**What was done:**
- `spine_api/models/trips.py`: Added `frontier_result`, `fees` columns
- `spine_api/persistence.py`: Dual encryption model (`_PRIVATE_BLOB_FIELDS` + `_PII_KEY_FIELDS`), unified `_encrypt_field_for_storage` / `_decrypt_field_from_storage`, `_to_dict` / `save_trip` / `update_trip` all use same helpers
- `spine_api/server.py`: Both authenticated save dicts include all 5 missing compartments; public checker documented as reduced contract
- `alembic/versions/add_frontier_result_and_fees_to_trips.py`: Migration
- `frontend/src/lib/api-client.ts`: Added `frontier_result` to Trip type
- `frontend/src/lib/bff-trip-adapters.ts`: Maps `strategy`, `traveler_bundle`, `internal_bundle`, `fees`, `frontier_result`
- `frontend/src/stores/workbench.ts`: `resetAll()` clears `result_fees`
- `frontend/src/components/workspace/FrontierDashboard.tsx`: Rewritten to read from store (still parked — not mounted)
- `tests/test_state_contract_parity.py`: 32 tests covering blob encryption, PII-key encryption, sentinel tests, FileTripStore parity, update_trip parity, SQL raw-row sentinel (full save_trip path)

**Specialty Knowledge Salvage (Phase 1.5):**
- `src/intake/orchestration.py`: Added `specialty_knowledge` to `decision.rationale["frontier"]` dict
- `frontend/src/app/(agency)/workbench/SafetyTab.tsx`: Added "Special Handling Checklist" section (niche, urgency badge, checklists, compliance, safety notes)
- `frontend/src/app/(agency)/workbench/page.tsx`: Added Safety Review tab (SafetyTab now mounted)
- `tests/test_specialty_knowledge_salvage.py`: 14 tests (detection, serialization, rationale shape)

**Not yet done (separate PRs):**

### Phase 2A: Readiness Engine (Complete)

**Architecture:**
- `src/intake/readiness.py` — Pure computation module, no side effects
- Readiness computed AFTER all pipeline outputs exist (after fee calculation, Phase 9.6 in orchestration)
- Stored in `validation.readiness` (nested dict within the validation JSON blob)
- `should_auto_advance_stage` always `False` — stage transitions require explicit action

**Tier model (cumulative, gated by real outputs):**
```
intake_minimum  — packet.facts: destination_candidates + date_window (usable values)
quote_ready     — packet.facts: 6 MVB fields with usable values
proposal_ready  — quote_ready + traveler_bundle + internal_bundle + fees + safety pass + no critical blockers
booking_ready   — booking_data must exist (cannot be faked from packet facts alone)
```

**Key design decisions:**
- `intake_minimum` and `quote_ready` check packet facts with usable-value checks (not just key existence — empty strings, None, [], {} don't count)
- `proposal_ready` requires pipeline outputs: traveler_bundle, internal_bundle, fees, safety.is_safe=True, no critical suitability blockers in decision.hard_blockers
- `booking_ready` is always `false` until `booking_data` is provided — packet facts alone cannot unlock it
- Signature: `compute_readiness(packet, validation, decision, traveler_bundle, internal_bundle, safety, fees, booking_data)`
- Frontend reads readiness from `result_validation || trip.validation` (store-first for live runs, trip for persisted)

**Implementation files:**
- `src/intake/readiness.py`: `compute_readiness()`, `ReadinessResult`, `TierDetail`, tier constants
- `src/intake/validation.py`: Added `readiness: Dict[str, Any]` field to `PacketValidationReport`
- `src/intake/orchestration.py`: Wired `compute_readiness()` after fee calculation (Phase 9.6)
- `frontend/src/types/spine.ts`: `ReadinessAssessment` interface, added to `ValidationReport`
- `frontend/src/lib/bff-trip-adapters.ts`: Maps `validation.readiness` from backend (skips empty)
- `frontend/src/components/workspace/panels/DecisionPanel.tsx`: Minimal readiness banner (tier badge + missing fields count)

**Tests:**
- `tests/test_readiness_engine.py`: 31 tests — all tiers, usable-value checks, booking_ready gating, pipeline-output checks, serialization, mutation guard
- `frontend/src/lib/__tests__/bff-trip-adapters.test.ts`: 2 readiness preservation tests
- `frontend/src/components/workspace/panels/__tests__/DecisionPanel.readiness.test.tsx`: 5 frontend tests (store vs trip, preference, missing data)

### Phase 2B: Stage Lifecycle + Audit (Complete)

**Architecture:**
- Durable `stage` column on Trip model (separate from `status`)
- Default `"discovery"`, valid values: `discovery`, `shortlist`, `proposal`, `booking`
- `PATCH /trips/{trip_id}/stage` endpoint for manual transitions with optimistic concurrency
- AuditStore logs `stage_transition` events with readiness snapshot
- Frontend shows "Advance to [Stage]" button when readiness suggests next stage
- No auto-advance — `should_auto_advance_stage` always `False`

**Key design decisions:**
- `stage` vs `status`: `status` = inbox/ops state (new, assigned, incomplete, completed); `stage` = commercial workflow phase
- Optimistic concurrency: `expected_current_stage` field, 409 Conflict on mismatch
- Same-stage transition returns `changed: false` (idempotent)
- AuditStore events include `from`, `to`, `trigger` (always `"manual"`), `reason`
- Stage transition does not affect `status`
- `_build_processed_trip()` derives stage from `meta.stage` or `packet.stage`, defaulting to `"discovery"`

**Implementation files:**
- `spine_api/models/trips.py`: Added `stage: Mapped[str]` column with `"discovery"` default
- `spine_api/persistence.py`: `_to_dict()` includes stage, `save_trip()` persists stage, `_build_processed_trip()` derives stage
- `spine_api/server.py`: `PATCH /trips/{trip_id}/stage` endpoint with `StageTransitionRequest` model
- `alembic/versions/add_stage_to_trips.py`: Migration adding stage column
- `frontend/src/lib/api-client.ts`: `StageTransitionResponse` interface, `transitionTripStage()` function, `stage` on Trip
- `frontend/src/lib/bff-trip-adapters.ts`: Maps `trip.stage` with `"discovery"` default
- `frontend/src/components/workspace/panels/StageAdvanceButton.tsx`: Standalone advance button component
- `frontend/src/components/workspace/panels/DecisionPanel.tsx`: Readiness banner with conditional advance button

**Tests:**
- `tests/test_stage_transitions.py`: 13 tests — persistence (4), endpoint behavior (6), readiness integration (3)
- `frontend/src/components/workspace/panels/__tests__/StageAdvanceButton.test.tsx`: 6 tests — button appearance, same-stage hiding, PATCH call, reload, no-readiness hiding, no auto-advance

### Phase 3: OpsPanel (stage-gated) — COMPLETE

Named "Ops" not "Booking" — room for documents, payments, confirmations, emergency later.

**Phase 3A** (complete): OpsPanel shell, passport extraction gating, readiness signals, URL bypass fix.

**Phase 3B** (complete): Booking data encrypted column, dedicated GET/PATCH endpoints, OpsPanel edit surface.

**Phase 4A** (complete): Customer booking-data collection link. Tokenized, time-limited URL; public form (no login); pending encrypted data; agent accept/reject review gate.

#### Phase 4A Architecture

**Review gate**: Customer submissions land in `pending_booking_data` (encrypted). Agent must explicitly accept before data becomes trusted `booking_data`. `_check_booking_ready()` only checks trusted `booking_data`.

**Token model**: `BookingCollectionToken` — SHA-256 hashed, single-use, revocable, expirable. Follows `PasswordResetToken` pattern. Default TTL: 7 days.

**Privacy**: `pending_booking_data` is NOT in `_to_dict()`. Public endpoint returns safe trip summary only — no PII, no internal fields.

**Async boundary**: Agent endpoints are `async def`, using `asyncio.to_thread()` for sync TripStore calls (avoids deadlock with TestClient's anyio loop). Public endpoints use `async_session_maker` directly for collection service, `_ts()` for TripStore calls.

**Endpoints**:
- Agent: POST/GET/DELETE `/trips/{trip_id}/collection-link`
- Agent: GET `/trips/{trip_id}/pending-booking-data`
- Agent: POST accept/reject `/trips/{trip_id}/pending-booking-data/accept|reject`
- Public: GET/POST `/api/public/booking-collection/{token}` (rate-limited)

**Implementation files:**
- `alembic/versions/add_booking_collection.py` — Table + columns migration
- `spine_api/models/tenant.py` — `BookingCollectionToken` model
- `spine_api/models/trips.py` — `pending_booking_data`, `booking_data_source` columns
- `spine_api/persistence.py` — `_PRIVATE_BLOB_FIELDS` + `get_pending_booking_data()`, NOT in `_to_dict()`
- `spine_api/services/collection_service.py` — Token lifecycle: generate, validate, revoke, mark_used
- `spine_api/server.py` — 8 endpoints + `_ts()` async helper

**Tests:**
- `tests/test_booking_collection.py` — 33 tests: encryption, token CRUD, public form/submit, accept/reject, privacy boundaries, audit

#### Phase 3B Architecture

**Privacy boundary**: `booking_data` is NOT included in `_to_dict()` or generic `GET /trips/{trip_id}` responses. Dedicated accessors only:
- `SQLTripStore.get_booking_data(trip_id)` — loads ORM object, decrypts just booking_data
- `FileTripStore.get_booking_data(trip_id)` — reads JSON, returns just booking_data
- `TripStore.get_booking_data(trip_id)` — facade that delegates to correct backend

**Endpoints**:
- `GET /trips/{trip_id}/booking-data` — returns envelope `{trip_id, booking_data, updated_at, stage, readiness}`
- `PATCH /trips/{trip_id}/booking-data` — stage-gated (proposal/booking only), optimistic lock (409), audit (metadata only, no raw PII), readiness recompute + persist
- Generic `PATCH /trips/{trip_id}` rejects booking_data (400)

**Encryption**: `booking_data` is in `_PRIVATE_BLOB_FIELDS` — entire JSON encrypted as single Fernet token.

**Readiness**: `_check_booking_ready()` validates semantic minimum: travelers non-empty, each has `traveler_id`/`full_name`/`date_of_birth`, payer with `name`. Passport optional.

**Frontend**: OpsPanel lazy-fetches booking_data via dedicated endpoint, keeps in local state only (not in global workbench store).

**Implementation files:**
- `alembic/versions/add_booking_data_to_trips.py` — Guarded migration (SQLAlchemy inspector)
- `spine_api/models/trips.py` — `booking_data` column
- `spine_api/persistence.py` — `_PRIVATE_BLOB_FIELDS`, dedicated `get_booking_data()`, NOT in `_to_dict()`
- `spine_api/server.py` — Pydantic models, GET/PATCH endpoints, audit, stage gate, optimistic lock, readiness recompute
- `src/intake/readiness.py` — `_check_booking_ready()` with field validation
- `frontend/src/lib/api-client.ts` — `BookingData` types, `getBookingData()`, `updateBookingData()`
- `frontend/src/app/(agency)/workbench/OpsPanel.tsx` — Full edit surface with local state

**Tests:**
- `tests/test_booking_data.py` — 24 tests: encryption, readiness, endpoints, stage gate, optimistic lock, mutation guards, audit PII absence, Pydantic validation, privacy boundary (generic GET excludes booking_data)
- `tests/test_readiness_engine.py` — 31 tests (including updated booking_ready with new schema)
- `frontend/src/app/(agency)/workbench/__tests__/OpsPanel.test.tsx` — 5 frontend tests

---

## Design Principles

1. **Planning state helps the agent think; booking state lets the agency execute; private state must be protected. Do not mix them.**
2. **Persist every first-class compartment emitted by pipeline. Test refresh parity.**
3. **Auto-compute readiness, manual-confirm stage transitions. Never silently mutate business stage.**
4. **Encrypt by risk of re-identification, not field name.**
5. **Flat JSON is an implementation tactic, not the architecture. The architecture is the contract + refresh parity + explicit PII boundaries.**
6. **Ship thin, iterate.** OpsPanel starts with Booking Readiness only.
7. **RunLedger for execution traces. AuditStore for business lifecycle events.**

---

## File Change Summary

| File | Change | Phase |
|:---|:---|:---|
| `spine_api/models/trips.py` | Add `frontier_result`, `fees` columns | 1 |
| `spine_api/persistence.py` | Update `_to_dict`, `save_trip`, `_build_processed_trip`, extend `_PII_FIELDS`, encrypt new compartments | 1 |
| `spine_api/server.py` | Add 5 missing fields to both save dicts | 1 |
| `alembic/versions/add_frontier_result_and_fees.py` | New migration | 1 |
| `frontend/src/app/(agency)/workbench/page.tsx` | Add `setResultFrontier`, `setResultFees` to hydration | 1 |
| `frontend/src/components/workspace/FrontierDashboard.tsx` | Read from store, remove hardcoded defaults | 1 |
| `src/intake/readiness.py` | New — `compute_readiness()` with 4 tiers, pipeline-output gating | 2A |
| `src/intake/validation.py` | Added `readiness` field to `PacketValidationReport` | 2A |
| `src/intake/orchestration.py` | Wire `compute_readiness()` after fee calculation | 2A |
| `frontend/src/types/spine.ts` | `ReadinessAssessment` interface, added to `ValidationReport` | 2A |
| `frontend/src/lib/bff-trip-adapters.ts` | Maps `validation.readiness` from backend | 2A |
| `frontend/src/components/workspace/panels/DecisionPanel.tsx` | Readiness banner (store-first hydration) | 2A |
| `spine_api/models/trips.py` | Add `stage` column with `"discovery"` default | 2B |
| `spine_api/persistence.py` | `_to_dict`/`save_trip`/`_build_processed_trip` include stage | 2B |
| `spine_api/server.py` | `PATCH /trips/{trip_id}/stage` endpoint with AuditStore | 2B |
| `alembic/versions/add_stage_to_trips.py` | Migration adding stage column | 2B |
| `frontend/src/lib/api-client.ts` | `transitionTripStage()`, `StageTransitionResponse`, `stage` on Trip | 2B |
| `frontend/src/lib/bff-trip-adapters.ts` | Maps `trip.stage` with default | 2B |
| `frontend/src/components/workspace/panels/StageAdvanceButton.tsx` | New — stage advance button component | 2B |
| `frontend/src/components/workspace/panels/DecisionPanel.tsx` | Advance button in readiness banner | 2B |
| `src/intake/extractors.py` | Gate passport extraction by stage | 3A |
| `src/intake/readiness.py` | `_check_booking_ready()` field validation, `signals` dict | 3A/3B |
| `frontend/src/types/spine.ts` | `signals` on `ReadinessAssessment` | 3A |
| `frontend/src/app/(agency)/workbench/OpsPanel.tsx` | New — Readiness tiers + booking data edit surface | 3A/3B |
| `frontend/src/app/(agency)/workbench/page.tsx` | Ops tab with `effectiveTab` normalization | 3A |
| `alembic/versions/add_booking_data_to_trips.py` | Guarded migration (SQLAlchemy inspector) | 3B |
| `spine_api/models/trips.py` | Add `booking_data` column | 3B |
| `spine_api/persistence.py` | `_PRIVATE_BLOB_FIELDS`, `get_booking_data()`, NOT in `_to_dict()` | 3B |
| `spine_api/server.py` | Pydantic models, GET/PATCH booking-data endpoints | 3B |
| `frontend/src/lib/api-client.ts` | `BookingData` types, `getBookingData()`, `updateBookingData()` | 3B |
| `tests/test_booking_data.py` | 24 tests — encryption, endpoints, audit, privacy boundary | 3B |
| `tests/test_passport_gating.py` | 29 tests — extraction gating, signals, stage gate | 3A |
| `alembic/versions/add_booking_collection.py` | Table + columns migration | 4A |
| `spine_api/models/tenant.py` | `BookingCollectionToken` model | 4A |
| `spine_api/models/trips.py` | `pending_booking_data`, `booking_data_source` columns | 4A |
| `spine_api/persistence.py` | `pending_booking_data` in blob fields + dedicated accessor | 4A |
| `spine_api/services/collection_service.py` | Token lifecycle: generate, validate, revoke, mark_used | 4A |
| `spine_api/server.py` | 8 endpoints (6 agent + 2 public) + `_ts()` helper | 4A |
| `tests/test_booking_collection.py` | 33 tests — encryption, token CRUD, public form, accept/reject, privacy | 4A |

---

## Verification

1. **Phase 1**: `alembic upgrade head` → run pipeline → query DB (all 9 compartments present, encrypted fields not plaintext) → refresh workbench → full state survives
2. **Phase 2**: Submit discovery note → see readiness scores → manual stage advance → transition event in AuditStore
3. **Phase 3A**: Set stage to proposal → OpsPanel appears → shows booking blockers → `?tab=ops` at discovery redirects
4. **Phase 3B**: At proposal → click "Add booking details" → fill traveler info → save → booking_ready becomes true → generic GET does not include booking_data
5. **Phase 4A**: Generate collection link → customer submits via public form → pending data stored encrypted → agent accepts → booking_data populated → readiness recomputed
6. **Refresh parity test**: Automated test that runs pipeline, saves, reloads, asserts all compartments match
