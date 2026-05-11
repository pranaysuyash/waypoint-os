# Random Document Audit Report: Traveler Proposal Contract

Date: 2026-05-11
Workspace: `/Users/pranay/Projects/travel_agency_agent`
Auditor: Codex

Naming note: the randomly selected source is the historical `Docs/research/NOTEBOOK_04_CONTRACT.md`, but current repository naming policy maps legacy `NB04` to semantic stage `traveler_proposal`, semantic gate `proposal_quality`, and user label "Build Proposal". This report uses `NB04` only for exact historical filenames, legacy mappings, and source evidence.

Implementation follow-up on 2026-05-11:

- `src/intake/traveler_proposal.py` now defines the public/internal proposal boundary contract.
- `spine_api/services/pipeline_execution_service.py` now persists existing `traveler_bundle` output through `to_traveler_dict()` when available, preventing generic raw serialization from storing traveler-bundle `internal_notes`.
- `tests/test_pipeline_execution_service_boundaries.py` includes a regression proving generic serialization would leak `internal_notes` and the public projection does not.
- The unrelated order-dependent trip PATCH test isolation failure was repaired by giving the affected tests owned trip fixtures instead of patching ambient `/trips` list items.
- A later full-suite run exposed a separate session auth expiry issue: the session-scoped `TestClient` token expired after 15 minutes during a 31-minute suite. `tests/conftest.py` now gives the test-session token a 12-hour expiry; rerun full-suite verification after concurrent agent pytest processes clear.
- Proposal generation, supplier/cost foundations, and delivery/send behavior remain intentionally pending.

## 1. Document Inventory

Inventory commands:

```bash
rg --files -g '*.md' -g 'README*' -g 'CHANGELOG*' -g 'TODO*' -g 'ROADMAP*' -g 'ADR*'
rg --files -g '*.md' | rg '(^frontend/docs/|^Docs/(UX|FRONTEND|PRODUCT|FEATURE|DIRECTIVE|discussions|research|plans|design|personas_scenarios|travel_agency_flow|INTAKE|ENQUIRY|DASHBOARD|WORKSPACE|PHASE4F|trip_reassessment|MASTER_PHASE|ROADMAP|USER_GUIDE))'
```

Results:

| Doc ID | Path | Type | Why it may matter |
|---|---|---|---|
| INV-001 | `README.md` | root doc | Product entrypoint and setup expectations. |
| INV-002 | `TODO.md` | task doc | Active backlog and deferred decisions. |
| INV-003 | `Docs/PRODUCT_VISION_AND_MODEL.md` | product doc | Source of business model and product thesis. |
| INV-004 | `Docs/UX_DETAILED_USER_FLOWS.md` | UX doc | Operator and traveler workflow expectations. |
| INV-005 | `Docs/research/NOTEBOOK_04_CONTRACT.md` | feature contract | Defines response/proposal generation contract. |
| INV-006 | `Docs/discussions/implementation_roadmap_2026-04-29.md` | roadmap doc | Phase sequencing and stale TODO risk. |
| INV-007 | `frontend/docs/FEATURE_DOCUMENTATION.md` | frontend feature doc | UI feature surface expectations. |
| INV-008 | `specs/SCENARIO_HANDLING_SPEC.md` | spec | Scenario and pipeline behavior contracts. |
| INV-009 | `tests/README.md` | test doc | Verification conventions. |
| INV-010 | code comments from `rg -n "TODO|FIXME|HACK|NOTE|XXX|skip\\(|skipif|xfail"` | embedded docs | Hidden tasks and test-isolation risks. |

Full repo Markdown count: 2,681.
Feature-related candidate pool count: 1,686.

## 2. Random Selection

Chosen document: `Docs/research/NOTEBOOK_04_CONTRACT.md`

Selection method: pseudo-random shell method using current nanosecond timestamp as seed:

```bash
seed=$(date +%s%N)
awk -v seed="$seed" 'BEGIN{srand(seed)} {print rand() "\t" $0}' /tmp/travel_feature_docs.txt | sort -n | head -1
```

Seed: `1778438480279956000`

Selected row: `0.000712449 Docs/research/NOTEBOOK_04_CONTRACT.md`

Why this doc is worth auditing: it is a feature contract for the product’s “last mile” value proposition: traveler proposals, internal quote sheets, pricing, margins, vendor contacts, quality gates, and delivery readiness.

Naming reconciliation:

- `Docs/PIPELINE_NAMING_ALLOWED_VS_FORBIDDEN.md:31-43` forbids raw `NB01`-style identifiers in product docs/help text, new test names, user-facing errors, analytics labels, URL paths, and primary API payloads without semantic fields.
- `Docs/PIPELINE_NAMING_REFACTOR_2026-05-03.md:35-44` maps legacy `NB04` to semantic stage `traveler_proposal` and user label "Build Proposal".
- `src/intake/constants.py:23-45` defines `PipelineStage.TRAVELER_PROPOSAL = "traveler_proposal"` and `GateIdentifier.PROPOSAL_QUALITY = "proposal_quality"`.
- `frontend/src/types/spine.ts:325-363` maps semantic and legacy identifiers through `validationLabelFor()`.
- `tests/test_pipeline_semantic_contract.py:1-13` documents the cross-boundary regression contract for semantic stage/gate naming.

## 3. Chosen Document Deep Analysis

| Doc Item ID | Type | Short evidence | Location | Interpretation | Confidence |
|---|---|---|---|---|---|
| D-001 | Current-State Claim | Status says specification ready for implementation | `Docs/research/NOTEBOOK_04_CONTRACT.md:3` | The doc claims implementation can begin from this contract. | High |
| D-002 | Architecture Claim | Depends on earlier notebook stages and internal data | `Docs/research/NOTEBOOK_04_CONTRACT.md:6` | The `traveler_proposal` stage should be downstream of existing pipeline and supplier data. | High |
| D-003 | Intended-State Claim | Transform `SessionOutput` into deliverables | `Docs/research/NOTEBOOK_04_CONTRACT.md:11-19` | The `traveler_proposal` stage is intended as a compiler stage, not only a display view. | High |
| D-004 | UX Claim | Reviewable, sendable, tracked, stored | `Docs/research/NOTEBOOK_04_CONTRACT.md:21-25` | Output lifecycle requires review, delivery, analytics, and persistence. | High |
| D-005 | Architecture Claim | `TravelerProposal` model | `Docs/research/NOTEBOOK_04_CONTRACT.md:42-159` | A typed traveler proposal model should exist. | High |
| D-006 | Data Boundary Risk | `booking_ref` is inside `Activity` | `Docs/research/NOTEBOOK_04_CONTRACT.md:96-104` | Traveler-facing model includes operational reference data. | High |
| D-007 | Data Boundary Risk | `margin_percent` appears in `PriceComponent` | `Docs/research/NOTEBOOK_04_CONTRACT.md:146-152` | Internal commercial data is placed under pricing model used by traveler proposal. | High |
| D-008 | Architecture Claim | `InternalQuoteSheet` model | `Docs/research/NOTEBOOK_04_CONTRACT.md:161-220` | Agent-facing quote sheet should exist with vendor contacts and margins. | High |
| D-009 | Privacy/PII Risk Claim | Vendor phone/email fields | `Docs/research/NOTEBOOK_04_CONTRACT.md:191-203` | Vendor contact storage needs classification and encryption. | High |
| D-010 | Operational Safety Claim | Three generation modes | `Docs/research/NOTEBOOK_04_CONTRACT.md:266-401` | Generator should route template, assembly, and research-heavy cases differently. | High |
| D-011 | UX/Quality Claim | Every proposal explains fit | `Docs/research/NOTEBOOK_04_CONTRACT.md:511-555` | Traveler-facing output should explain why it fits the customer. | High |
| D-012 | Test/QA Claim | Proposal quality gates | `Docs/research/NOTEBOOK_04_CONTRACT.md:559-622` | Deterministic `proposal_quality` gates should exist. | High |
| D-013 | Reliability Claim | Fallback behavior for generation errors | `Docs/research/NOTEBOOK_04_CONTRACT.md:627-692` | Generator should handle insufficient data, vendor unavailability, and budget mismatch. | High |
| D-014 | Test/QA Claim | Unit and integration tests listed | `Docs/research/NOTEBOOK_04_CONTRACT.md:696-759` | The repo should eventually test generation, personalization, margin preservation, quality gates, and upstream-to-`traveler_proposal` flow. | High |
| D-015 | Contradiction/Risk | `to_dict()` serializes both proposal and internal sheet | `Docs/research/NOTEBOOK_04_CONTRACT.md:249-261` | The spec lacks a safe projection boundary for traveler delivery. | High |

## 4. Extracted Task Candidates

| Task Candidate ID | Source Doc Item IDs | Task | Explicit or Implicit | Why this is a task | Expected repo area | Initial priority guess |
|---|---|---|---|---|---|---|
| TC-001 | D-005, D-008 | Implement `traveler_proposal` contract models | Explicit | Models are specified but absent. | `src/intake` or new proposal module | P1 |
| TC-002 | D-010 | Implement generation mode router | Explicit | Template, assembly, and research modes are specified. | proposal generation service | P1 |
| TC-003 | D-012 | Implement deterministic proposal quality gates | Explicit | Quality gate pseudocode is specified. | proposal QA module/tests | P1 |
| TC-004 | D-014 | Add `traveler_proposal` unit and integration tests | Explicit | Tests are listed in the contract. | `tests/` | P1 |
| TC-005 | D-006, D-007, D-015 | Add public/internal projection boundary before `traveler_proposal` implementation | Implicit | Spec mixes internal fields into traveler-adjacent objects. | models/serializers/tests | P0 |
| TC-006 | D-008, D-009 | Define storage classification for `traveler_proposal` artifacts | Implicit | Internal quote sheets include vendor PII and margin data. | persistence/security docs/tests | P1 |
| TC-007 | D-004, D-013 | Route send behavior through autonomy gates and audit trail | Implicit | Doc allows direct send, but current product policy defaults to review. | frontend, autonomy policy, audit | P1 |
| TC-008 | D-002, D-008, D-010 | Implement supplier/internal package/cost foundation first | Implicit | `traveler_proposal` depends on internal data and margin/cost truth. | supplier/cost domain | P1 |
| TC-009 | D-011 | Implement personalization rationale safely | Explicit | Doc requires “why this fits” explanation. | proposal generator | P2 |
| TC-010 | D-013 | Add reversible fallback strategy design | Explicit | Spec lists exceptions and fallback modes. | proposal generator | P2 |

## 5. Static Codebase Reality Check

| Task Candidate ID | Codebase Status | Evidence | What exists today | Gap | Actual Work Needed |
|---|---|---|---|---|---|
| TC-001 | Missing / Partially Superseded | `src/intake/plan_candidate.py:4-10`, `Docs/research/NOTEBOOK_04_CONTRACT.md:42-260` | `PlanCandidate`, `PromptBundle`, bundles, and readiness exist. | No exact `traveler_proposal` `TravelerProposal`, `InternalQuoteSheet`, or `ResponseGenerationResult`. | Define the current canonical `traveler_proposal` artifact contract or explicitly supersede the historical notebook doc. |
| TC-002 | Missing | `Docs/research/NOTEBOOK_04_CONTRACT.md:266-401`; searches found no `generate_from_template`, `generate_by_assembly`, or `generate_with_research`. | Existing strategy varies prompt bundles by decision/operating mode. | No proposal generator mode router. | Implement only after projection and supplier/cost foundations are designed. |
| TC-003 | Partially Done / Different | `src/intake/constants.py:38-65`, `src/intake/readiness.py:161-235`, `tests/test_readiness_engine.py:132-148` | `traveler_proposal` and `proposal_quality` exist as semantic stage/gate identifiers; readiness checks bundles/fees/safety. | No proposal-specific quality gate for completeness, personalization, pricing, vendor contacts, margin sheet. | Add deterministic quality gate over the future `traveler_proposal` artifact shape. |
| TC-004 | Partial | `tests/test_agent_runtime.py:732-784`, `tests/test_readiness_engine.py:132-148` | Tests cover proposal readiness over existing proposal blobs and readiness tier. | No `traveler_proposal` generation, personalization, margin preservation, or full upstream-to-proposal tests. | Add tests with the contract implementation. |
| TC-005 | Partially Done / still high-value | `Docs/research/NOTEBOOK_04_CONTRACT.md:96-104`, `Docs/research/NOTEBOOK_04_CONTRACT.md:146-152`, `Docs/research/NOTEBOOK_04_CONTRACT.md:249-261`; `spine_api/server.py:868-874`; `tests/test_audit_closure_2026_04_24.py:15-61`; `src/intake/traveler_proposal.py:89-178`; `spine_api/services/pipeline_execution_service.py:46-53`; `tests/test_pipeline_execution_service_boundaries.py:205-274` | Existing prompt bundle persistence now uses traveler public projection; `traveler_proposal` public/internal contract exists. | Future generated proposal artifacts still need storage classification and SQL raw-row sentinel tests before new columns/fields are added. | Build supplier/cost-backed proposal generator only after the boundary remains enforced at every new write path. |
| TC-006 | Partially Done for existing fields only | `spine_api/persistence.py:391-409`, `spine_api/persistence.py:487-505`, `tests/test_state_contract_parity.py:205-213` | SQL store encrypts current private blobs: traveler/internal bundles, safety, fees, booking data. | No `traveler_proposal` artifact fields exist; future `proposal`/`quote_sheet` may bypass encryption if added casually. | Classify artifacts before adding storage fields. |
| TC-007 | Partially Done / Contradicted by doc | `Docs/research/NOTEBOOK_04_CONTRACT.md:21-25`, `src/intake/config/agency_settings.py:28-35`, `tests/test_d1_autonomy.py:31-44`, `frontend/src/components/workspace/panels/OutputPanel.tsx:45-53` | Default policy requires review for `PROCEED_TRAVELER_SAFE`; UI send is mocked and policy-gated. | Doc’s direct-send wording is under-specified and stale relative to autonomy policy. | Keep review/audit gate; update doc before wiring real delivery. |
| TC-008 | Missing foundation | `Docs/VENDOR_COST_TRACKING_DISCOVERY_GAP_ANALYSIS_2026-04-16.md:13-24`, `Docs/VENDOR_COST_TRACKING_DISCOVERY_GAP_ANALYSIS_2026-04-16.md:127-158`, `Docs/VENDOR_COST_TRACKING_DISCOVERY_GAP_ANALYSIS_2026-04-16.md:377-397` | Fee calculation and analytics margin heuristics exist. | No supplier entity, internal package store, cost ledger, or margin policy engine backing trustworthy proposal artifacts. | Build small supplier/cost slice before full `traveler_proposal`. |
| TC-009 | Partial | `src/intake/plan_candidate.py:176-227`; `Docs/research/NOTEBOOK_04_CONTRACT.md:511-555` | Traveler-safe summary and filtered constraints exist. | No proposal-level “why this fits” based on itinerary choices. | Add after artifact model exists; avoid raw customer-history leakage. |
| TC-010 | Missing | `Docs/research/NOTEBOOK_04_CONTRACT.md:627-692` | Existing runtime agents can flag readiness/risk, but no generator fallback exists. | No generator exceptions or fallback outputs. | Add after generator mode router exists. |

## 6. Dynamic Verification and Test Baseline

Existing `.venv` was used for Python commands.

Baseline before any probe:

```bash
.venv/bin/python -m pytest --collect-only -q
```

Result after fresh status check: `2030 tests collected in 6.30s`.

Earlier, before the status check, collection hit `tests/test_spine_hardening_temp.py`; fresh status showed that file is deleted in the current working tree and only stale `__pycache__` entries remain. This is pre-existing parallel/user work, not caused by this audit.

Targeted verification run by main auditor:

```bash
.venv/bin/python -m pytest tests/test_pipeline_semantic_contract.py tests/test_agent_runtime.py::test_proposal_readiness_agent_blocks_thin_or_risky_proposal tests/test_agent_runtime.py::test_proposal_readiness_agent_marks_complete_proposal_reviewable tests/test_audit_closure_2026_04_24.py::TestSerializationSafety -q
```

Result: `26 passed in 17.35s`.

Subagent targeted verification:

```bash
uv run python -m pytest tests/test_readiness_engine.py tests/test_fees.py -q
# 41 passed

uv run python -m pytest tests/test_nb03_v02.py::TestSanitizationPipeline tests/test_nb03_v02.py::TestStructuralSanitization tests/test_e2e_freeze_pack.py::TestScenario3_AuditModeSelfBooked -q
# 13 passed

cd frontend && npm run test -- --run src/components/workspace/panels/__tests__/OutputPanel.test.tsx src/lib/__tests__/bff-trip-adapters.test.ts
# 16 passed
```

No proof-of-concept probe was made. No code changes were needed to verify the selected doc’s current status.

## 7. Critical Implementation and Test Traps Checked

Environment/config loading:

- `src/security/privacy_guard.py:31-33` reads `DATA_PRIVACY_MODE` at call time.
- `src/security/encryption.py:13-35` caches Fernet with an explicit cache clear helper.
- `tests/conftest.py:161-170` has an autouse reset fixture for `DATA_PRIVACY_MODE`.

State/test isolation:

- `tests/conftest.py:60-84` canonicalizes persistence module identity because duplicate imports caused previous isolation failures.
- `tests/conftest.py:137-158` auto-skips integration tests when the API server is not ready, so full-suite evidence can hide live-server gaps.
- `tests/conftest.py:293-297` skips PostgreSQL-marked tests when Postgres is unavailable.

Write paths:

- Existing SQL persistence encrypts private fields on both save/update through `SQLTripStore._encrypt_field_for_storage()` in `spine_api/persistence.py:487-497`.
- `traveler_proposal`-specific fields do not exist yet, so there is no current write path to verify for `traveler_proposal`, `internal_quote_sheet`, or `quote_sheet`.

Duplicate/stale code:

- No duplicate `traveler_proposal` route or module was found.
- The selected document is stale relative to `PlanCandidate` and current bundle/readiness architecture.

## 8. Data, Privacy, and PII Boundary Checks

Relevant because the doc touches traveler output, vendor contacts, customer history, internal margins, research sources, storage, analytics, and possible delivery.

Findings:

- The spec places `booking_ref` under `Activity` and `margin_percent` under `PriceComponent` in the traveler proposal area: `Docs/research/NOTEBOOK_04_CONTRACT.md:96-104`, `Docs/research/NOTEBOOK_04_CONTRACT.md:146-152`.
- `ResponseGenerationResult.to_dict()` serializes traveler and internal artifacts wholesale: `Docs/research/NOTEBOOK_04_CONTRACT.md:249-261`.
- Existing safe serialization pattern exists for prompt bundles: `spine_api/server.py:868-874`, tested by `tests/test_audit_closure_2026_04_24.py:15-61`.
- Privacy guard blocks obvious dogfood-mode PII but beta/production allow persistence: `src/security/privacy_guard.py:318-336`, `tests/test_privacy_guard.py:318-331`.
- SQL storage encrypts current private compartments, but `traveler_proposal` artifact names are absent from `_PRIVATE_BLOB_FIELDS`: `spine_api/persistence.py:391-409`.

Conclusion: `traveler_proposal` must start with a data classification and projection contract. The current notebook should not be implemented literally.

## 9. Deduped Issue / Task Register

## ISSUE-001: Traveler Proposal Contract Lacks Public/Internal Projection Boundary

Category:
- privacy / data-boundary / architecture / tests

Origin:
- Implicit
- Source doc: `Docs/research/NOTEBOOK_04_CONTRACT.md:96-104`, `Docs/research/NOTEBOOK_04_CONTRACT.md:146-152`, `Docs/research/NOTEBOOK_04_CONTRACT.md:249-261`
- Related doc items: D-006, D-007, D-015

Codebase Evidence:
- `spine_api/server.py:868-874` - current bundle serialization already has a traveler-safe hook.
- `tests/test_audit_closure_2026_04_24.py:15-61` - existing tests prove internal notes are excluded for traveler-safe bundles.
- `src/intake/plan_candidate.py:176-227` - current planning artifact has a filtered traveler-safe projection.

Static Verification:
- No `traveler_proposal` equivalent of `to_traveler_dict()` or separate public/internal models exists.

Dynamic Verification:
- Baseline command: `.venv/bin/python -m pytest --collect-only -q`
- Baseline result: `2030 tests collected`
- Targeted result: serialization safety tests passed in the 26-test targeted run.

Current Behavior:
- Existing bundles have some safety projection.
- The historical notebook spec would serialize internal and traveler artifacts without a typed boundary if implemented literally.

Expected Behavior / Decision Needed:
- `traveler_proposal` artifacts must be split into traveler-safe and internal-only projections before generation or delivery.

Gap:
- Missing contract and tests for margin/vendor/booking-ref/source leakage.

Impact:
- Accidental leakage of margins, vendor contact data, booking references, internal notes, or raw CRM/research source snippets.

Risk:
- High. This is a product trust and commercial confidentiality risk.

Confidence:
- High.

Acceptance Criteria:
- [ ] `traveler_proposal` has explicit traveler-safe model/projection.
- [ ] Internal quote sheet remains internal-only.
- [ ] Tests prove margin, vendor contact, booking refs, internal notes, raw sources, and raw customer history cannot appear in traveler output.
- [ ] Serialization code never calls generic `asdict()` for traveler delivery without safe projection.

Test Plan:
- Automated: unit tests for `to_traveler_dict()` / public schema; leakage sentinel tests.
- Manual: inspect generated sample proposal JSON.

Rollback / Kill Switch:
- Keep `traveler_proposal` generation behind a disabled feature flag until projection tests pass.

Open Questions:
- Should traveler proposals ever expose supplier names, or only hotel/activity display names?

## ISSUE-002: Traveler Proposal Generator Models and Modes Are Missing

Category:
- feature / architecture / tests

Origin:
- Explicit
- Source doc: `Docs/research/NOTEBOOK_04_CONTRACT.md:42-260`, `Docs/research/NOTEBOOK_04_CONTRACT.md:266-401`
- Related doc items: D-005, D-008, D-010

Codebase Evidence:
- `src/intake/plan_candidate.py:4-10` - explicitly not the full historical notebook proposal contract.
- `spine_api/services/pipeline_execution_service.py:345-358` - persists plan candidate and bundles, not `traveler_proposal` artifacts.
- `src/intake/orchestration.py:183-205`, `src/intake/orchestration.py:565-580` - pipeline returns extraction, decision, strategy, bundles, fees, autonomy outcome, and frontier result, not the final proposal artifact.

Static Verification:
- `rg` searches found no `TravelerProposal`, `InternalQuoteSheet`, `ResponseGenerationResult`, `generate_from_template`, `generate_by_assembly`, or `generate_with_research` implementation.

Dynamic Verification:
- Targeted tests confirm adjacent readiness/proposal QA exists, not generation.

Current Behavior:
- The system prepares prompt bundles and a plan candidate. It does not generate the `traveler_proposal` contract.

Expected Behavior / Decision Needed:
- Decide whether to implement the notebook contract or revise it around current `PlanCandidate` + bundle architecture.

Gap:
- No `traveler_proposal` artifact module or generator.

Impact:
- Product cannot produce the full traveler proposal/internal quote sheet envisioned by the doc.

Risk:
- Medium-high, but should follow ISSUE-001.

Confidence:
- High.

Acceptance Criteria:
- [ ] Current `traveler_proposal` contract is reconciled with `PlanCandidate`.
- [ ] Minimal artifact model exists.
- [ ] Generation mode router exists behind a flag.
- [ ] Tests cover at least one deterministic template/package path.

Test Plan:
- Automated: model tests, deterministic generation tests, pipeline smoke.
- Manual: inspect generated sample proposal.

Rollback / Kill Switch:
- Feature flag disables `traveler_proposal` generation and preserves current bundle flow.

Open Questions:
- Is `PlanCandidate` the intended canonical pre-proposal artifact, or should `traveler_proposal` bypass it?

## ISSUE-003: Supplier, Package, Cost, and Margin Foundations Block Trustworthy Traveler Proposal

Category:
- architecture / data-boundary / product-decision

Origin:
- Implicit
- Source doc: `Docs/research/NOTEBOOK_04_CONTRACT.md:6`, `Docs/research/NOTEBOOK_04_CONTRACT.md:161-203`, `Docs/research/NOTEBOOK_04_CONTRACT.md:725-733`

Codebase Evidence:
- `Docs/VENDOR_COST_TRACKING_DISCOVERY_GAP_ANALYSIS_2026-04-16.md:13-24` - prior audit says production vendor/supplier/cost/margin logic is absent.
- `Docs/VENDOR_COST_TRACKING_DISCOVERY_GAP_ANALYSIS_2026-04-16.md:127-158` - supplier entity, internal package entity, cost ledger, margin model, and sourcing engine are missing.
- `tests/test_fees.py:1-35` - current fee tests cover risk-adjusted service fees, not supplier net-cost quote pricing.

Static Verification:
- Existing code has fee calculation and analytics margin heuristics, not supplier-backed pricing.

Dynamic Verification:
- Fee tests passed in subagent targeted run; this proves only adjacent fee logic.

Current Behavior:
- The system can calculate internal service fees and readiness, but not real vendor net rates or quote margin.

Expected Behavior / Decision Needed:
- `traveler_proposal` should not pretend to generate trustworthy quote sheets until supplier/cost truth exists.

Gap:
- No supplier table/API/import, package templates, cost ledger, or margin policy engine.

Impact:
- Any full quote sheet would be fake or heuristic-only.

Risk:
- High if implemented as real commercial output; medium if explicitly labeled as draft/scaffold.

Confidence:
- High.

Acceptance Criteria:
- [ ] Minimal supplier/package/cost data model exists or `traveler_proposal` explicitly uses draft placeholders.
- [ ] Margin policy and quote pricing are backed by stored data, not only hardcoded heuristics.
- [ ] Tests cover margin floor and supplier-backed budget feasibility.

Test Plan:
- Automated: supplier fixture, cost ledger, pricing calculation, margin risk tests.
- Manual: compare generated quote sheet against fixture supplier data.

Rollback / Kill Switch:
- Keep commercial quote sheet disabled until supplier/cost feature flag is enabled.

Open Questions:
- Should the first `traveler_proposal` release produce non-commercial proposal drafts only, deferring internal quote sheet?

## ISSUE-004: Direct Traveler Send Is Stale Relative to Autonomy Policy

Category:
- operational-safety / UX / product-decision

Origin:
- Implicit
- Source doc: `Docs/research/NOTEBOOK_04_CONTRACT.md:21-25`

Codebase Evidence:
- `src/intake/config/agency_settings.py:28-35` - `PROCEED_TRAVELER_SAFE` defaults to review.
- `tests/test_d1_autonomy.py:31-44` - tests lock the review/block defaults.
- `frontend/src/components/workspace/panels/OutputPanel.tsx:45-53`, `frontend/src/components/workspace/panels/OutputPanel.tsx:162-190` - send is mocked and gated.

Static Verification:
- Existing product behavior is review-first, not automatic traveler send.

Dynamic Verification:
- Targeted OutputPanel tests passed in subagent run.

Current Behavior:
- Review gates block/allow UI send; actual delivery is mocked.

Expected Behavior / Decision Needed:
- `traveler_proposal` should state that delivery is review/audit gated unless the autonomy policy explicitly allows auto-send.

Gap:
- Doc direct-send language is stale and unsafe.

Impact:
- Future implementation could bypass review and create externally visible mistakes.

Risk:
- High operational risk.

Confidence:
- High.

Acceptance Criteria:
- [ ] `traveler_proposal` doc/implementation requires autonomy policy check before delivery.
- [ ] Delivery emits audit event.
- [ ] UI cannot send if review/policy blocks.
- [ ] Tests cover blocked and allowed states.

Test Plan:
- Automated: autonomy policy, frontend disabled state, backend delivery audit tests.
- Manual: attempt send in review-required state.

Rollback / Kill Switch:
- Disable delivery feature flag; preserve generation-only mode.

Open Questions:
- What should be the first real delivery channel: email, WhatsApp draft, downloadable PDF, or internal preview only?

## ISSUE-005: Traveler Proposal Storage Classification Is Undefined

Category:
- privacy / persistence / compliance

Origin:
- Implicit
- Source doc: `Docs/research/NOTEBOOK_04_CONTRACT.md:161-203`, `Docs/research/NOTEBOOK_04_CONTRACT.md:242-259`

Codebase Evidence:
- `spine_api/persistence.py:391-409` - encrypted private blob field list does not include `traveler_proposal` artifact names because they do not exist.
- `spine_api/persistence.py:487-505` - save/update encryption helper covers configured fields only.
- `tests/test_state_contract_parity.py:205-213` - existing private blobs hide margin-like sentinel data.

Static Verification:
- Storage classification for future `traveler_proposal` artifacts is absent.

Dynamic Verification:
- Existing storage sentinel tests were cited; no `traveler_proposal` storage test exists.

Current Behavior:
- Current bundles/fees are encrypted; new proposal fields would need explicit classification.

Expected Behavior / Decision Needed:
- Define which `traveler_proposal` fields are encrypted private blobs, key-encrypted PII, public summaries, analytics-safe, and retention-limited.

Gap:
- No storage or retention contract.

Impact:
- Future implementation could store vendor contact/margin/customer-history data in plaintext or wrong compartment.

Risk:
- High for launch privacy/commercial confidentiality.

Confidence:
- High.

Acceptance Criteria:
- [ ] `traveler_proposal` storage classification table exists.
- [ ] Persistence fields are encrypted where required.
- [ ] Save and update paths have sentinel tests.
- [ ] Retention and analytics-safe projections are documented.

Test Plan:
- Automated: SQL raw-row sentinel tests for `traveler_proposal` artifacts.
- Manual: inspect serialized stored row in local DB.

Rollback / Kill Switch:
- Do not persist `traveler_proposal` artifacts unless classification flag is enabled.

Open Questions:
- Should traveler proposal drafts be encrypted as private blobs even if eventually customer-facing?

## 10. Prioritization

| ID | Title | Severity | Blast Radius | Effort | Confidence | Priority | Why |
|---|---|---:|---:|---:|---:|---|---|
| ISSUE-001 | Traveler proposal projection boundary | 5 | 4 | 2 | 5 | P0 | Prevents margin/vendor/internal leakage before any implementation. |
| ISSUE-004 | Direct send policy mismatch | 4 | 4 | 2 | 5 | P1 | Prevents externally visible unsafe delivery. |
| ISSUE-005 | Storage classification undefined | 5 | 3 | 3 | 5 | P1 | Prevents privacy/commercial persistence mistakes. |
| ISSUE-003 | Supplier/cost foundations missing | 4 | 4 | 5 | 5 | P1 | Blocks truthful quote sheet and margin preservation. |
| ISSUE-002 | Traveler proposal generator missing | 3 | 4 | 4 | 5 | P2 | Important, but should not precede projection/storage/commercial foundation. |

## Priority Queues

### P0
- ISSUE-001

### P1
- ISSUE-004
- ISSUE-005
- ISSUE-003

### P2
- ISSUE-002

### P3
- None from this audit.

### Quick Wins
- Update/supersede `Docs/research/NOTEBOOK_04_CONTRACT.md` to mark public/internal projection as a prerequisite.
- Add a small `traveler_proposal` leakage contract test scaffold before implementation.

### Risky Changes
- Full `traveler_proposal` generation.
- Internal quote sheet with vendor contacts and margins.
- Real traveler delivery.

### Needs Discussion Before Work
- Whether first `traveler_proposal` release should exclude internal quote sheet.
- Whether supplier names are traveler-safe.
- Whether `PlanCandidate` is canonical or transitional.

### Not Worth Doing
- Implementing the notebook literally as-is. It would carry preventable leakage and policy risks.

## 11. Proof-of-Concept Validation

No proof-of-concept probe was needed. Static and existing dynamic evidence were sufficient. The selected contract is missing as source code, and its highest-risk boundary issue is visible directly in the document.

## 12. Assumptions Challenged by Implementation

| Assumption | Why it seemed true | What disproved it | Evidence | How recommendation changed |
|---|---|---|---|---|
| `traveler_proposal` can be implemented directly from the spec | The doc says ready for implementation. | The spec places internal fields in traveler-adjacent structures and serializes wholesale. | `Docs/research/NOTEBOOK_04_CONTRACT.md:96-104`, `Docs/research/NOTEBOOK_04_CONTRACT.md:146-152`, `Docs/research/NOTEBOOK_04_CONTRACT.md:249-261` | Start with projection/storage contract, not generation. |
| Existing privacy guard is enough | It blocks dogfood PII. | Beta/production allow persistence; launch safety relies on encryption/projection. | `src/security/privacy_guard.py:318-336`, `tests/test_privacy_guard.py:318-331` | Treat guard as dogfood-only, not `traveler_proposal` launch control. |
| `PROCEED_TRAVELER_SAFE` means send directly | The doc says deliverables can be sent directly. | Current autonomy policy defaults that state to review. | `src/intake/config/agency_settings.py:28-35`, `tests/test_d1_autonomy.py:31-44` | Keep delivery review/audit gated. |
| Earlier pytest collection failure was a code failure | Initial collection saw `tests/test_spine_hardening_temp.py`. | Fresh status showed the file deleted and fresh collection passed. | `git status --short`; `.venv/bin/python -m pytest --collect-only -q` | Mark as pre-existing parallel-tree churn, not an audit regression. |

## 13. Parallel Agent / Multi-Model Findings

Three subagents were used.

Agent A, document/source verifier:

- Confirmed `traveler_proposal` is mostly missing as specified by the historical notebook.
- Found `PlanCandidate` explicitly says it is not the full historical notebook proposal contract.
- Found no exact `traveler_proposal` models/functions.
- Highlighted current bridge artifacts: `PlanCandidate`, `PromptBundle`, fees, readiness.

Agent C, test/runtime verifier:

- Confirmed no `traveler_proposal` contract surface exists in source/tests/frontend source.
- Ran targeted tests:
  - `tests/test_readiness_engine.py tests/test_fees.py`: 41 passed.
  - NB03 sanitization/e2e freeze subset: 13 passed.
  - Frontend OutputPanel/BFF adapter subset: 16 passed.
- Flagged broader test-suite auto-skip risks in `tests/conftest.py`.

Agent D/E/F, security/privacy/product skeptic:

- Found the strongest blocker: traveler-side spec includes internal booking refs and margin fields.
- Confirmed existing autonomy policy contradicts direct-send wording.
- Confirmed current storage encryption protects existing bundles, not future `traveler_proposal` artifact names.
- Recommended projection, storage classification, autonomy-gated delivery, and minimization rules before generation.

Reconciliation:

- All agents agree `traveler_proposal` is not implemented as specified by the historical notebook.
- The main recommendation follows the skeptic’s stronger evidence: do not start with generator implementation; start with boundary and classification.

## 14. Discussion Pack

## My Recommendation

I recommend working on:

1. ISSUE-001 - `traveler_proposal` public/internal projection boundary.
2. ISSUE-005 - `traveler_proposal` storage classification.
3. ISSUE-004 - Delivery policy alignment.

Reason:

- These are the safety rails that prevent a future `traveler_proposal` implementation from leaking margins, vendor contacts, booking refs, internal notes, or raw source/customer-history data.
- They are smaller and safer than building the generator.
- They let the team decide whether the notebook is canonical or should be superseded by the current `PlanCandidate` architecture.

## Why These Matter Now

- The selected doc is implementation-ready only on paper.
- A literal implementation would create privacy and commercial confidentiality risks.
- The repo already has patterns for safe projections and encrypted private compartments; `traveler_proposal` should reuse those instead of inventing a parallel path.

## What Breaks If Ignored

- Traveler proposals could expose margin or supplier ops metadata.
- Internal quote sheets could be stored outside encrypted compartments.
- Auto-send could bypass the current review-first autonomy policy.
- Full proposal work could become a second architecture parallel to `PlanCandidate`.

## What I Would Not Work On Yet

- Full LLM-backed `traveler_proposal` generator.
- Research-intensive generation mode.
- Real customer delivery channel.
- Margin-preserving quote sheet backed only by heuristics.

## What Is Ambiguous

- Whether `PlanCandidate` is the intended canonical bridge to `traveler_proposal` or a temporary artifact.
- Whether the first `traveler_proposal` release should produce traveler-safe drafts only or also internal quote sheets.
- Whether supplier names are safe customer-facing facts or internal-only until booking.

## Questions For You

1. Should the first `traveler_proposal` release be traveler-safe proposal draft only, leaving internal quote sheet for a later supplier/cost phase?
2. Should traveler output ever include supplier/vendor identifiers, or only display-friendly hotel/activity names?
3. Should `PROCEED_TRAVELER_SAFE` remain review-required by default for all customer delivery, even when the generated proposal passes leakage tests?

## Needs Runtime Verification

- Full suite after current parallel edits settle.
- SQL raw-row sentinel tests once `traveler_proposal` artifact fields exist.
- End-to-end UI send policy test once delivery becomes real.

## Needs Online Research

No online research needed. Current findings are repo-evidence based.

## Needs ChatGPT / External Review

Not needed yet. The next decision is product/architecture intent, not an external-fact question.

## 15. Online Research

No online research used. Current findings are repo-evidence based.

## 16. ChatGPT / External Review Escalation Writeup

Not needed for this audit.

## 17. Recommended Next Work Unit

## Unit-1: Traveler Proposal Boundary Contract Before Generation

Goal:

- Define and test the public/internal boundary for `traveler_proposal` artifacts before any proposal generator is implemented.

Issues covered:

- ISSUE-001
- ISSUE-005
- ISSUE-004, documentation alignment only

Scope:

- In:
  - Add or update `traveler_proposal` contract documentation to require separate traveler-safe and internal projections.
  - Define a small artifact classification table: traveler-safe, internal-only, encrypted private blob, analytics-safe.
  - Add failing-first tests or test plan for margin/vendor/booking-ref/source leakage if implementation is approved.
  - Align direct-send language with autonomy policy.
- Out:
  - Full generator.
  - Supplier/cost ledger.
  - Real delivery integration.
  - LLM generation.

Likely files touched:

- `Docs/research/NOTEBOOK_04_CONTRACT.md`
- Possibly `Docs/research/TRAVELER_PROPOSAL_BOUNDARY_CONTRACT_2026-05-11.md`
- Future tests under `tests/`

Acceptance criteria:

- [ ] Historical notebook/supersession doc no longer implies raw `asdict()` output is safe for traveler delivery.
- [ ] Public/internal projection rules are explicit.
- [ ] Storage classification for proposal artifacts is explicit.
- [ ] Direct-send behavior references autonomy policy and audit requirements.
- [ ] Test plan names exact leakage sentinels: margin, vendor phone/email, booking refs, internal notes, raw research sources, raw customer-history snippets.

Tests to run:

- Baseline:
  - `.venv/bin/python -m pytest --collect-only -q`
- Targeted:
  - `.venv/bin/python -m pytest tests/test_audit_closure_2026_04_24.py::TestSerializationSafety -q`
  - `.venv/bin/python -m pytest tests/test_readiness_engine.py tests/test_fees.py -q`
- Full suite:
  - `.venv/bin/python -m pytest -q`

Manual verification:

- Read the proposal contract and confirm no traveler-facing model contains internal-only fields without safe projection.

Docs to update:

- `Docs/research/NOTEBOOK_04_CONTRACT.md` or a dated supersession note.

Operational safety:

- Kill switch / rollback:
  - Keep `traveler_proposal` generation disabled; documentation-only boundary work has no runtime effect.

Risks:

- Low if documentation/test-only.
- Main risk is choosing a boundary that conflicts with future product intent; resolve through the questions above.

Rollback plan:

- Revert the documentation/test-contract patch if product decision rejects the boundary.

## 18. Appendix: Searches Performed

Main searches:

```bash
rg --files -g '*.md' -g 'README*' -g 'CHANGELOG*' -g 'TODO*' -g 'ROADMAP*' -g 'ADR*'
rg --files -g '*.md' | rg '(^frontend/docs/|^Docs/(UX|FRONTEND|PRODUCT|FEATURE|DIRECTIVE|discussions|research|plans|design|personas_scenarios|travel_agency_flow|INTAKE|ENQUIRY|DASHBOARD|WORKSPACE|PHASE4F|trip_reassessment|MASTER_PHASE|ROADMAP|USER_GUIDE))'
rg -n "TODO|FIXME|HACK|NOTE|XXX|skip\\(|skipif|xfail" -g '*.py' -g '*.ts' -g '*.tsx' -g '*.md'
rg -n "NB04|Notebook 04|ResponseGeneration|TravelerProposal|InternalQuoteSheet|PricingBreakdown|PriceComponent|PaymentMilestone|generate_from_template|generate_by_assembly|generate_with_research|run_nb04|quality_gates|PROPOSAL_QUALITY_GATES|proposal_readiness|ProposalReadiness|margin_preservation|quote_sheet|internal_quote|traveler_proposal" src spine_api frontend tests Docs specs
rg -n "class .*Proposal|proposal|quote|pricing|margin|vendor|booking_ref|agency_notes|internal_notes|customer_history|to_traveler_dict|traveler-safe|traveler_safe|PROCEED_TRAVELER_SAFE|ASK_FOLLOWUP" src spine_api frontend tests
rg -n "os\\.getenv|environ\\[|environ\\.get|lru_cache|@cache|DATA_PRIVACY_MODE|SPINE_API_DISABLE_AUTH|TRIPSTORE_BACKEND|target_margin|proposal|quote|margin" src spine_api tests frontend/src
```

Instruction/status checks:

```bash
sed -n '1,220p' /Users/pranay/AGENTS.md
sed -n '1,260p' /Users/pranay/Projects/AGENTS.md
sed -n '1,260p' AGENTS.md
/Users/pranay/Projects/agent-start --skip-index
sed -n '1,220p' Docs/context/agent-start/AGENT_KICKOFF_PROMPT.txt
sed -n '1,260p' Docs/context/agent-start/SESSION_CONTEXT.md
git status --short
find . -maxdepth 4 \( -iname 'AGENTS.md' -o -iname 'CLAUDE.md' -o -iname '.impeccable.md' -o -iname 'SKILL.md' -o -iname '*copilot*' -o -iname '*qwen*' -o -iname '*codex*' -o -iname 'GEMINI.md' -o -iname 'CURSOR.md' \) -print
find .claude .agents .qwen .codex .commandcode .kiro -maxdepth 4 -type f
```

Verification commands:

```bash
.venv/bin/python -m pytest --collect-only -q
.venv/bin/python -m pytest tests/test_pipeline_semantic_contract.py tests/test_agent_runtime.py::test_proposal_readiness_agent_blocks_thin_or_risky_proposal tests/test_agent_runtime.py::test_proposal_readiness_agent_marks_complete_proposal_reviewable tests/test_audit_closure_2026_04_24.py::TestSerializationSafety -q
```

## 19. Corrective Instruction and Skill Sweep

After the first report draft, the user correctly pointed out that the instruction/skill sweep was not exhaustive enough. Corrective pass performed on 2026-05-11:

```bash
find /Users/pranay -maxdepth 4 \( -iname 'AGENTS.md' -o -iname 'CLAUDE.md' -o -iname 'GEMINI.md' -o -iname 'QWEN.md' -o -iname 'CURSOR.md' -o -iname '.cursorrules' -o -iname '.impeccable.md' -o -iname '*copilot*' -o -iname '*codex*' \) -print
find /Users/pranay/.claude /Users/pranay/.agents /Users/pranay/.hermes /Users/pranay/.codex /Users/pranay/Projects/openai-skills -maxdepth 3 \( -iname 'AGENTS.md' -o -iname 'CLAUDE.md' -o -iname 'GEMINI.md' -o -iname 'QWEN.md' -o -iname 'README.md' -o -iname '*instructions*' \) -print
find /Users/pranay/.claude/skills /Users/pranay/.agents/skills /Users/pranay/.hermes/skills /Users/pranay/Projects/skills /Users/pranay/Projects/external-skills /Users/pranay/Projects/openai-skills /Users/pranay/.codex/skills /Users/pranay/.codex/skills/.system -maxdepth 5 -iname 'SKILL.md'
```

Additional instruction files opened in the corrective pass:

- `/Users/pranay/.claude/CLAUDE.md`
- `/Users/pranay/.codex/AGENTS.md`
- `/Users/pranay/.codex/instructions.md`
- `/Users/pranay/.gemini/GEMINI.md`
- `frontend/AGENTS.md`
- `frontend/CLAUDE.md`
- `.qwen/settings.json`

Skill store counts found:

- `/Users/pranay/.claude/skills`: 43 `SKILL.md` files.
- `/Users/pranay/.agents/skills`: 150 `SKILL.md` files.
- `/Users/pranay/.hermes/skills`: 876 `SKILL.md` files.
- `/Users/pranay/Projects/skills`: 127 `SKILL.md` files.
- `/Users/pranay/Projects/external-skills`: 2,819 `SKILL.md` files.
- `/Users/pranay/Projects/openai-skills`: 0 `SKILL.md` files found at checked depth.
- `/Users/pranay/.codex/skills`: 42 `SKILL.md` files.

Relevant skills found across stores:

- `search-first`
- `verification-before-completion`
- `systematic-debugging`
- `tdd-workflow`
- `webapp-testing`
- `security-review`
- `qa`
- `qa-only`
- `review`
- `design-review`
- `wide-open-brainstorm`
- additional Hermes audit/review skills including `documentation-verification-exploration`, `comprehensive-audit`, `full-stack-audit`, `multi-lens-codebase-review`, and `code-review`.

Outcome:

- The corrective pass did not change the technical conclusion of this audit.
- It did change the process record: the initial report should be read as amended by this section.
- For any next implementation/review unit, load the most specific applicable skill body from the full discovered skill set before starting, rather than relying only on the initial system-provided skill list.

## 20. Corrective Naming Reconciliation Pass

After the user flagged that another agent had worked on renaming `NB*` identifiers to meaningful names, a second corrective pass was performed on 2026-05-11 before using this audit for work selection.

Fresh status/instruction checks:

```bash
git status --short
/Users/pranay/Projects/agent-start --skip-index
find . -maxdepth 4 \( -name 'AGENTS.md' -o -name 'CLAUDE.md' -o -name 'QWEN.md' -o -name 'GEMINI.md' -o -name 'COPILOT*.md' -o -name '.impeccable.md' -o -name '.qwen*' -o -name '.cursorrules' \) -print | sort
nl -ba .qwen/settings.json
nl -ba /Users/pranay/.qwen/settings.json
nl -ba /Users/pranay/.codex/AGENTS.md
nl -ba /Users/pranay/.codex/instructions.md
nl -ba /Users/pranay/.claude/CLAUDE.md
nl -ba /Users/pranay/.gemini/GEMINI.md
```

Relevant skills opened for this pass:

- `/Users/pranay/Projects/skills/search-first/SKILL.md`
- `/Users/pranay/Projects/skills/verification-before-completion/SKILL.md`
- Hermes `documentation-verification-exploration/SKILL.md`

Naming evidence checked:

- `Docs/PIPELINE_NAMING_ALLOWED_VS_FORBIDDEN.md:31-43` - raw legacy notebook codes are forbidden in product docs/help text, new tests, user-facing errors, analytics labels, and routes.
- `Docs/PIPELINE_NAMING_REFACTOR_2026-05-03.md:35-44` - legacy `NB04` maps to `traveler_proposal` and "Build Proposal".
- `src/intake/constants.py:23-45` - semantic enum values include `traveler_proposal` and `proposal_quality`.
- `frontend/src/types/spine.ts:325-363` - UI labels resolve through `validationLabelFor()`.
- `tests/test_pipeline_semantic_contract.py:1-13` - backend/frontend naming parity is protected by a dedicated regression test.

Changes made to this report:

- Changed the report title and recommended work unit from legacy `NB04` wording to `traveler_proposal` / "Traveler Proposal".
- Kept `Docs/research/NOTEBOOK_04_CONTRACT.md` as the selected historical source and preserved `NB04` only for exact filenames, legacy mappings, or source evidence.
- Changed the suggested supersession filename away from legacy notebook-code wording to `TRAVELER_PROPOSAL_BOUNDARY_CONTRACT_2026-05-11.md`.

Verification:

```bash
.venv/bin/python -m pytest tests/test_pipeline_semantic_contract.py -q
# 21 passed in 1.22s
```

Conflict note:

- `.qwen/settings.json` allows some git write commands, but `/Users/pranay/AGENTS.md`, `/Users/pranay/Projects/AGENTS.md`, and repo `AGENTS.md` forbid commit/push without explicit approval. The stricter repo/global rule controls; only read-only git status was used.

## 21. Implemented Work Unit Verification

After the user approved proceeding, Unit-1 was implemented as a boundary contract, not a generator.

Files added:

- `src/intake/traveler_proposal.py` - semantic `traveler_proposal` boundary dataclasses, explicit traveler/internal projections, and restricted-field guard.
- `tests/test_traveler_proposal_boundary.py` - leakage tests for internal quote sheet fields, vendor contact data, booking refs, margins, net rates, raw sources, and semantic stage/gate naming.
- `Docs/research/TRAVELER_PROPOSAL_BOUNDARY_CONTRACT_2026-05-11.md` - dated contract and handoff documentation.

Files updated:

- `Docs/research/NOTEBOOK_04_CONTRACT.md` - marked as historical/superseded for new implementation and points to the semantic boundary contract.
- `Docs/random_document_audit_nb04_contract_2026-05-11.md` - updated with this implementation and verification record.

Verification:

```bash
.venv/bin/python -m pytest tests/test_traveler_proposal_boundary.py tests/test_pipeline_semantic_contract.py -q
# 37 passed in 40.54s

.venv/bin/python -m pytest tests/test_audit_closure_2026_04_24.py::TestSerializationSafety tests/test_traveler_proposal_boundary.py -q
# 19 passed in 58.48s

.venv/bin/python -m pytest --collect-only -q
# 2046 tests collected in 75.90s

.venv/bin/python -m pytest -q
# 2039 passed, 7 skipped in 187.07s
```

Scope intentionally not implemented:

- No generator.
- No persistence fields.
- No delivery path.
- No new API route.

Remaining product decisions:

- Whether supplier display names are ever traveler-safe.
- Whether first proposal release should include an internal quote sheet or traveler-safe draft only.
- When persisted proposal artifacts exist, add SQL raw-row sentinel tests for encrypted/private fields.
