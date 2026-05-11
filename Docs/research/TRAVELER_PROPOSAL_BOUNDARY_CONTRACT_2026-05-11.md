# Traveler Proposal Boundary Contract

Date: 2026-05-11
Status: Boundary contract wired into traveler-bundle persistence; proposal generation still pending
Source audit: `Docs/random_document_audit_nb04_contract_2026-05-11.md`
Supersedes for new work: traveler/output portions of `Docs/research/NOTEBOOK_04_CONTRACT.md`

## Purpose

The historical notebook proposal contract is valuable as product intent, but it must not be implemented literally. The first safe work unit is the boundary between customer-facing proposal data and internal quote/operations data.

Current canonical names:

| Layer | Value |
|---|---|
| Semantic stage | `traveler_proposal` |
| Semantic gate | `proposal_quality` |
| User label | Build Proposal |
| Legacy source name | `NB04` only in historical docs/compat maps |

Naming evidence:

- `Docs/PIPELINE_NAMING_ALLOWED_VS_FORBIDDEN.md:31-43`
- `Docs/PIPELINE_NAMING_REFACTOR_2026-05-03.md:35-44`
- `src/intake/constants.py:23-45`
- `frontend/src/types/spine.ts:325-363`
- `tests/test_pipeline_semantic_contract.py:1-13`

## Boundary Rule

Traveler-facing proposal output must be produced only through an explicit traveler-safe projection. It must not use raw `asdict()` over a combined proposal/internal quote object.

Internal quote sheet output must remain internal-only and use a separate internal projection.

## Data Classification

| Field/data class | Classification | Traveler-safe? | Storage guidance |
|---|---|---:|---|
| Proposal title, summary, highlights | traveler-safe | Yes | Public/proposal artifact |
| Day/activity display name and description | traveler-safe | Yes | Public/proposal artifact |
| Traveler-facing package price | traveler-safe | Yes | Public/proposal artifact |
| Inclusions, exclusions, cancellation policy | traveler-safe | Yes | Public/proposal artifact |
| Why-this-fits rationale | traveler-safe after minimization | Yes | Public/proposal artifact; avoid raw customer-history snippets |
| Assumptions shown to traveler | traveler-safe after review | Yes | Public/proposal artifact |
| Supplier/vendor names | product decision required | Unknown | Default internal until approved |
| Vendor contact name, phone, email | vendor PII / internal ops | No | Encrypted private blob |
| Booking reference / PNR / supplier ref | internal ops | No | Encrypted private blob |
| Net rate, cost breakdown, margin percent, margin amount | commercial confidential | No | Encrypted private blob |
| Internal notes, agency notes, operator review notes | internal ops | No | Encrypted private blob |
| Raw research sources and raw customer history | privacy / provenance | No | Encrypted private blob or audit-only with retention policy |
| Aggregated quality metrics | analytics-safe if source-minimized | Maybe | Analytics-safe projection only |

## Implementation Contract

Code location:

- `src/intake/traveler_proposal.py`
- `spine_api/services/pipeline_execution_service.py`

Required projection methods:

- `TravelerProposal.to_traveler_dict()`
- `InternalQuoteSheet.to_internal_dict()`
- `TravelerProposalBoundaryResult.to_traveler_dict()`
- `TravelerProposalBoundaryResult.to_internal_dict()`

Required guard:

- `assert_traveler_payload_safe(payload)`

Runtime persistence rule:

- `spine_api/services/pipeline_execution_service.py` must persist `traveler_bundle` through `to_traveler_dict()` when the bundle provides that method.
- The generic serializer remains valid for internal-only fields such as `internal_bundle`, but must not be used for traveler-facing bundle persistence because it can include `internal_notes`.

The guard rejects restricted nested field names in traveler-facing payloads, including:

- `internal_quote_sheet`
- `vendor_contacts`
- `supplier_name`
- `contact_name`
- `phone`
- `email`
- `booking_ref`
- `net_rate`
- `margin_percent`
- `margin_by_component`
- `internal_notes`
- `agency_notes`
- `raw_research_sources`
- `raw_customer_history`
- `data_sources_used`

## Acceptance Criteria

- [x] `traveler_proposal` and `proposal_quality` are used for new work.
- [x] Traveler projection excludes internal quote sheet.
- [x] Traveler projection excludes vendor contact fields.
- [x] Traveler projection excludes booking references.
- [x] Traveler projection excludes margin and net-rate fields.
- [x] Traveler projection excludes raw source/audit fields.
- [x] Internal projection retains internal quote sheet fields for operators.
- [x] Tests cover nested restricted field detection.
- [x] Pipeline persistence uses the traveler bundle public projection instead of generic raw serialization.
- [ ] Product decision: whether supplier display names are ever traveler-safe.
- [ ] Future storage work: add SQL raw-row sentinel tests when proposal artifacts are persisted.

## Verification

Targeted tests:

```bash
.venv/bin/python -m pytest tests/test_traveler_proposal_boundary.py tests/test_pipeline_semantic_contract.py -q
# 37 passed in 40.54s
```

Serialization regression subset:

```bash
.venv/bin/python -m pytest tests/test_audit_closure_2026_04_24.py::TestSerializationSafety tests/test_traveler_proposal_boundary.py -q
# 19 passed in 58.48s
```

Pipeline boundary regression:

```bash
.venv/bin/python -m pytest tests/test_pipeline_execution_service_boundaries.py::test_execute_spine_pipeline_persists_traveler_bundle_public_projection -q
# Red before fix: generic serialization persisted `internal_notes`.
# Green after fix: 1 passed in 34.20s
```

Post-wiring targeted subset:

```bash
.venv/bin/python -m pytest tests/test_pipeline_execution_service_boundaries.py tests/test_traveler_proposal_boundary.py tests/test_audit_closure_2026_04_24.py::TestSerializationSafety -q
# 26 passed in 32.90s
```

Full suite after persistence-boundary wiring:

```bash
.venv/bin/python -m pytest -q
# 2038 passed, 7 failed, 7 skipped in 129.93s
```

The 7 failures were in `tests/test_api_trips_post.py::TestTripFollowUpDueDate` and `tests/test_call_capture_phase2.py::TestPhase2StructuredFields`. Both failing areas passed when run directly after the full-suite run:

```bash
.venv/bin/python -m pytest tests/test_api_trips_post.py -q
# 8 passed in 2.80s

.venv/bin/python -m pytest tests/test_call_capture_phase2.py -q
# 21 passed in 3.82s

.venv/bin/python -m pytest tests/test_api_trips_post.py::TestTripFollowUpDueDate tests/test_call_capture_phase2.py::TestPhase2StructuredFields -q
# 25 passed in 5.77s
```

Interpretation: current full-suite evidence has an order-dependent trip PATCH/state-isolation failure unrelated to traveler-bundle serialization. Treat this as a separate test isolation issue before claiming a globally green suite.

Baseline collection:

```bash
.venv/bin/python -m pytest --collect-only -q
# 2046 tests collected in 75.90s
```

Full suite:

```bash
.venv/bin/python -m pytest -q
# 2039 passed, 7 skipped in 187.07s
```

Follow-up verification after trip PATCH isolation repair:

```bash
.venv/bin/python -m pytest tests/test_api_trips_post.py tests/test_call_capture_phase2.py -q
# 29 passed in 307.36s
```

The previous order-dependent trip PATCH failures were removed by making the affected tests seed and clean up their own patch targets instead of selecting `items[0]` from shared `/trips` state.

Long full-suite run after that repair:

```bash
.venv/bin/python -m pytest -q
# 1975 passed, 59 failed, 5 skipped, 18 errors in 1865.79s
```

Interpretation: the earlier trip PATCH failures were absent from the failure list. The new broad failure cluster was caused by shared test auth/session behavior and concurrent environment load, not the traveler proposal boundary:

- `tests/conftest.py` used one session-scoped `TestClient` token.
- `spine_api/core/security.py` keeps default access tokens to 15 minutes.
- The full suite took about 31 minutes, so protected `session_client` endpoints started returning `401 Invalid or expired token` after the token expired.
- `tests/conftest.py` now creates the session test token with `expires_delta=timedelta(hours=12)`.
- A representative previously failing protected route passed alone: `.venv/bin/python -m pytest tests/test_team_router_behavior.py::test_list_members_is_agency_scoped -q` -> `1 passed in 72.11s`.
- Live-server lifecycle verification remains noisy while other agents have long-running pytest jobs and a live uvicorn process active in the same workspace; rerun the full suite after those processes clear.

Final full-suite verification after auth-session and suite-order test hardening:

```bash
.venv/bin/python -m pytest tests/evals/test_d6_audit_scaffold.py::test_d6_seed_fixture_corpus_loads -q
# 1 passed in 5.47s

.venv/bin/python -m pytest tests/test_public_checker_agency_config.py::test_validate_public_checker_agency_configuration_passes_when_agency_exists tests/test_public_checker_agency_config.py::test_validate_public_checker_agency_configuration_raises_when_agency_missing -q
# 2 passed in 20.56s

.venv/bin/python -m pytest tests/test_vision_extraction.py::TestSchemaValidationProof::test_wrong_type_fields_create_failed_row_no_pii -q
# 1 passed in 29.52s

.venv/bin/python -m pytest -q
# 2080 passed, 7 skipped, 1 xfailed in 176.07s

cd frontend && npm test -- --run
# 106 test files passed, 852 tests passed in 106.03s
```

Notes recorded 2026-05-11 22:16 IST:

- `tests/evals/test_d6_audit_scaffold.py` was already repaired by concurrent work to avoid assuming the first loaded fixture has expected findings.
- `tests/test_public_checker_agency_config.py` now models the startup `set_config(...)` timeout query before agency invariant checks.
- `tests/test_vision_extraction.py` now scopes the failed-extraction audit assertion to the test trip, removing dependence on the last 20 global audit events in the full suite.
- The pasted frontend missing-export error for `getPlanningStageProgressItems` is no longer present in the current source because `frontend/src/lib/planning-list-display.ts` exports that helper and frontend tests pass.
- No durable product behavior was changed in this final hardening pass; the edits are test-fake and test-isolation hardening.

## Operational Safety

This boundary contract does not enable proposal generation or delivery. It does affect traveler-bundle persistence by forcing the existing public projection at the save boundary.

Rollback is small and localized: revert `_serialize_traveler_bundle_for_persistence()` usage in `spine_api/services/pipeline_execution_service.py`. That rollback would re-open the `internal_notes` persistence risk and must be paired with an equivalent public projection enforcement.

Future generator work must depend on this boundary instead of introducing a parallel response-generation model.
