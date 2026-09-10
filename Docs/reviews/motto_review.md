# Operating Doctrine Review

- Doctrine path: /Users/pranay/Projects/travel_agency_agent/OPERATING_DOCTRINE.md
- SHA-256: ff848618a7431a3b06c7409caa45683bd27c64263d45b93f9fcd36a89803466a
- Generated: 2026-09-10T18:51:30Z
- This is a generated review artifact, not an instruction source.

## SECTION_0

- Label: §0 Start from live truth
- Reviewed: True
- Evidence: Live truth: suite re-run at 4350 of 0 via scripts/run_backend_tests.sh with the dev server stopped; working tree re-inspected before staging (22 paths, all accounted for: TS wave files plus envelope-tool drift verified earlier).

## SECTION_00_INTEGRATED

- Label: Full doctrine integrated audit
- Reviewed: True
- Evidence: Integrated audit of the staged second TS wave: TS-08 UNKNOWN idempotency outcome with TTL exemption and fenced resolution in src/agents/idempotency.py plus fulfillment classification in spine_api/routers/fulfillment.py; trip-level commitment aggregation and verdict on the journey-graph GET in spine_api/routers/journey_graph.py; TS-07 operation-keyed requiredness with prioritized follow-up consumers in src/intake/validation.py and src/intake/decision.py; TS-06 deterministic route-structure enumerator in src/decision/route_structures.py with additive decision enrichment and the DecisionTab dual-shape render fix; TS-03 S1 attachment envelope in spine_api/contract.py with storage-lane persistence in spine_api/routers/inbound.py; verification: 51 new tests, full backend suite 4350 of 0, mypy clean, ruff clean, tsc clean, 1380 frontend vitest; envelope-tool drift verified and riding along; register and roadmap synchronized.

## SECTION_1

- Label: §1 Outcomes and retained value
- Reviewed: True
- Evidence: Retained value: TS-08 UNKNOWN outcome protects the money path from duplicate bookings (src/agents/idempotency.py); TS-07 required_for prioritizes customer questions (src/intake/validation.py); TS-06 route structures enrich proposals (src/decision/route_structures.py); TS-03 S1 opens the attachment funnel (spine_api/contract.py).

## SECTION_10

- Label: §10 Parallel work and contested state
- Reviewed: True
- Evidence: Parallel work engaged: the envelope-tool drift in tools/strip_envelope_fragments.py that arrived mid-commit was verified (10 of 10 tests in tests/test_strip_envelope_fragments.py, corpus 2240 clean) and rides this commit; drift re-checked before staging.

## SECTION_11

- Label: §11 Engineering and data integrity
- Reviewed: True
- Evidence: Data integrity: UNKNOWN records are exempt from TTL reclaim in both backends of src/agents/idempotency.py so unresolved outcomes are never silently reset; fenced CAS on resolve_unknown prevents stale-owner closure; attachment manifest is content-addressed (sha256) in spine_api/routers/inbound.py.

## SECTION_12

- Label: §12 AI output boundary
- Reviewed: True
- Evidence: AI output boundary: route-structure generation is pure combinatorics with no LLM (documented in src/decision/route_structures.py); the LLM may narrate trade-offs but never alters skeletons; no agent claims accepted without in-repo evidence.

## SECTION_13

- Label: §13 Product, operator, and claim reality
- Reviewed: True
- Evidence: Claim reality: the 504 outcome_unknown response explicitly tells operators not to retry blindly (spine_api/routers/fulfillment.py); attachments_accepted honestly reports degradation; the commitment_verdict abstains when no non-void nodes exist (spine_api/routers/journey_graph.py).

## SECTION_14

- Label: §14 Documentation and decisions
- Reviewed: True
- Evidence: Documentation and decisions: TS-06/07/08 marked DONE and TS-03 S1 marked done with named S2/S3 seams in Docs/exploration/CHATGPT_SYSTEMS_TRAINING_SESSION_FINDINGS_2026-09-09.md; roadmap table synchronized in Docs/review/OPEN_WORK_ROADMAP_2026-09-08.md.

## SECTION_15

- Label: §15 Completion contract
- Reviewed: True
- Evidence: Completion contract: verdicts explicit in the handoff addendum of Docs/review/TS_REGISTER_EXECUTION_HANDOFF_2026-09-09.md (code ready, seams enumerated, Wave A recommended next); nothing silently dropped.

## SECTION_16

- Label: §16 Specialist doctrine routing
- Reviewed: True
- Evidence: Specialist routing: Testing doctrine paired fail-pass sensitivity per family; Architecture doctrine owned boundary placement (registry extension, decision enrichment, storage-lane reuse); Documentation doctrine for the register and handoff updates under Docs/.

## SECTION_17

- Label: §17 Propagation contract
- Reviewed: True
- Evidence: Propagation: no doctrine or hook changes in this diff (the workspace_memory installer fix landed in commit 1ceaf91); this wave touches only src/, spine_api/, frontend/src/, tests/, tools/, and Docs/.

## SECTION_2

- Label: §2 Truth taxonomy
- Reviewed: True
- Evidence: Truth labels: every TS item was gap-verified in code before implementation (register section 6 of Docs/exploration/CHATGPT_SYSTEMS_TRAINING_SESSION_FINDINGS_2026-09-09.md cites file:line for what existed vs not); the UNKNOWN classification is a deterministic exception shape, not a live-provider claim.

## SECTION_3

- Label: §3 Proportional rigor and evidence
- Reviewed: True
- Evidence: Proportional rigor: 51 new tests across tests/test_ts06_route_structures.py, tests/test_ts07_operation_keyed_requiredness.py, tests/test_ts08_unknown_outcome_and_aggregation.py, tests/test_ts03_inbound_attachments.py; adversarial cases for fences and TTL; full suite 4350 of 0; mypy and ruff clean; frontend tsc and 1380 vitest clean.

## SECTION_4

- Label: §4 Authorization and side effects
- Reviewed: True
- Evidence: Authorization: owner directed work on all pending items with no other agent active, continuing the commit-and-push flow authorized earlier in this conversation; staging scoped to the 22 inspected paths across src/, spine_api/, frontend/src/, and tests/; no destructive git operations.

## SECTION_5

- Label: §5 Canonical paths and ownership
- Reviewed: True
- Evidence: Canonical paths: UNKNOWN extends the existing registry in src/agents/idempotency.py (no parallel store); route structures live in src/decision/ beside the constraint engine; attachments persist via the existing document-storage lane in spine_api/services/document_storage.py; no new routers created.

## SECTION_6

- Label: §6 Semantic salvage and supersession
- Reviewed: True
- Evidence: Supersession: the DecisionTab dual-shape render supersedes the string-only renderer (frontend/src/app/(agency)/workbench/DecisionTab.tsx) while keeping string support; INTAKE_MINIMUM and QUOTE_READY tiers preserved in src/intake/validation.py (extended, not forked); no deletions.

## SECTION_7

- Label: §7 Capability routing
- Reviewed: True
- Evidence: Capability routing: the prior wave used a dedicated code-reviewer subagent on src/decision/constraint_engine.py; this wave followed the same discipline with paired fail-pass tests in tests/test_ts08_unknown_outcome_and_aggregation.py and siblings.

## SECTION_8

- Label: §8 Skills lifecycle
- Reviewed: True
- Evidence: n/a: no skill store files changed in this diff; only src/, spine_api/, frontend/src/, tests/, and Docs/ artifacts.

## SECTION_9

- Label: §9 Exploration and durable knowledge
- Reviewed: True
- Evidence: Durable knowledge: register statuses updated in Docs/exploration/CHATGPT_SYSTEMS_TRAINING_SESSION_FINDINGS_2026-09-09.md; roadmap rows updated in Docs/review/OPEN_WORK_ROADMAP_2026-09-08.md; handoff addendum appended to Docs/review/TS_REGISTER_EXECUTION_HANDOFF_2026-09-09.md with named seams for deferred work.
