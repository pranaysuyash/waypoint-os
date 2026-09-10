# Operating Doctrine Review

- Doctrine path: /Users/pranay/Projects/travel_agency_agent/OPERATING_DOCTRINE.md
- SHA-256: ff848618a7431a3b06c7409caa45683bd27c64263d45b93f9fcd36a89803466a
- Generated: 2026-09-10T06:09:38Z
- This is a generated review artifact, not an instruction source.

## SECTION_0

- Label: §0 Start from live truth
- Reviewed: True
- Evidence: Grounded in live probes: 4,274-test full suite green, register validator 0 warnings, src/memory/store.py and spine_api/routers/feedback.py read in full before changes.

## SECTION_00_INTEGRATED

- Label: Full doctrine integrated audit
- Reviewed: True
- Evidence: Integrated audit: 4,274 passed / 0 failed full suite; 12 loop tests + updated capability-batch green; register validator clean; shadow-influence design holds (writes durable, ranking unweighted until F-13 slot 2 + evidence cycle); docs and register updated with closure evidence.

## SECTION_1

- Label: §1 Outcomes and retained value
- Reviewed: True
- Evidence: Retained value: F-36 closed (E-10 loop), F-13 slot 1 closed (trust-weighted retrieval), scorecard honesty restored; docs in Docs/review/E10_FEEDBACK_MEMORY_LOOP_HANDOFF_2026-09-06.md.

## SECTION_10

- Label: §10 Parallel work and contested state
- Reviewed: True
- Evidence: Parallel work: src/security/privacy_guard.py and tests/test_privacy_guard.py changes are the parallel stream's — untouched; earlier failure was F-19 contention, verified green in isolation.

## SECTION_11

- Label: §11 Engineering and data integrity
- Reviewed: True
- Evidence: Data integrity: write-time sanitization in src/memory/store.py (summaries + hashes describe sanitized content); half_life_days override honored; supplier namespace isolates aggregate outcomes from traveler preferences.

## SECTION_12

- Label: §12 AI output boundary
- Reviewed: True
- Evidence: AI boundary: free-text sanitized against prompt injection BEFORE hashing/persistence; sanitizer output verified by test in src/memory/store.py path.

## SECTION_13

- Label: §13 Product, operator, and claim reality
- Reviewed: True
- Evidence: Operator reality: spine_api/routers/feedback.py records responses via operator transcription with real aggregation visible in the scorecard; influence deliberately shadow until F-13 evidence (documented in the endpoint docstring).

## SECTION_14

- Label: §14 Documentation and decisions
- Reviewed: True
- Evidence: Docs: Docs/review/E10_FEEDBACK_MEMORY_LOOP_HANDOFF_2026-09-06.md (11-section structure); register F-36 row updated with closure evidence.

## SECTION_15

- Label: §15 Completion contract
- Reviewed: True
- Evidence: Completion: F-36 CLOSED in Docs/review/FINDINGS_REGISTER_2026-08-31.md; F-13 slot 1 closed in src/memory/retriever.py; remaining scope (slot 2, influence activation, self-service, auto-trigger) enumerated in Docs/review/E10_FEEDBACK_MEMORY_LOOP_HANDOFF_2026-09-06.md §5.

## SECTION_16

- Label: §16 Specialist doctrine routing
- Reviewed: True
- Evidence: Specialist routing: fastapi + pydantic validation patterns in spine_api/routers/feedback.py; memory-subsystem conventions followed in src/memory/store.py and src/memory/feedback_bridge.py (enum source types, provenance engine).

## SECTION_17

- Label: §17 Propagation contract
- Reviewed: True
- Evidence: Propagation: scorecard contract change propagated to tests/test_capability_routers_batch.py and tests/test_register_wave_f30_f40.py; route snapshots regenerated via scripts/snapshot_server_routes.py; register and Docs/review/E10_FEEDBACK_MEMORY_LOOP_HANDOFF_2026-09-06.md cross-linked.

## SECTION_2

- Label: §2 Truth taxonomy
- Reviewed: True
- Evidence: Truth taxonomy: demo scorecard rows deleted not labeled; NPS never becomes a memory fact; empty states are true empties in spine_api/routers/feedback.py.

## SECTION_3

- Label: §3 Proportional rigor and evidence
- Reviewed: True
- Evidence: Evidence proportionate: 12 tests in tests/test_feedback_memory_loop.py; trust-ordering proven by test (traveler-direct 0.7 outranks system-inferred 0.9 at identical text); design sourced from Docs/exploration/E10_SURVEY_MEMORY_FEEDBACK_LOOP_2026-09-02.md.

## SECTION_4

- Label: §4 Authorization and side effects
- Reviewed: True
- Evidence: Authorization: commit+push explicitly approved by Pranay; no destructive ops; new endpoint is canonical-auth only; /stats-style read-only patterns preserved.

## SECTION_5

- Label: §5 Canonical paths and ownership
- Reviewed: True
- Evidence: Canonical paths: ingestion routes in the existing feedback router; all memory writes through src/memory/store.py ingest_memory; no parallel store created (src/memory/feedback_bridge.py only translates).

## SECTION_6

- Label: §6 Semantic salvage and supersession
- Reviewed: True
- Evidence: Supersession: fabricated scorecard rows superseded by computed aggregation in spine_api/routers/feedback.py; tests/test_capability_routers_batch.py and tests/test_register_wave_f30_f40.py updated from the old fabricated contract.

## SECTION_7

- Label: §7 Capability routing
- Reviewed: True
- Evidence: Capability routing: MemoryStore gate/sanitizer/provenance/supersession reused, not duplicated; HybridMemoryRetriever extended in place at src/memory/retriever.py.

## SECTION_8

- Label: §8 Skills lifecycle
- Reviewed: True
- Evidence: Skills lifecycle: scripts/check_findings_register.py and scripts/snapshot_server_routes.py exercised on this diff; tests/test_feedback_memory_loop.py follows repo fixture conventions (fresh agencies, file-store isolation).

## SECTION_9

- Label: §9 Exploration and durable knowledge
- Reviewed: True
- Evidence: Exploration: E-10 design doc drove the build; handoff at Docs/review/E10_FEEDBACK_MEMORY_LOOP_HANDOFF_2026-09-06.md records decisions (shadow, namespaces, decay-as-mechanism).
