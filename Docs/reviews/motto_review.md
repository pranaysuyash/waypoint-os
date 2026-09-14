# Operating Doctrine Review

- Doctrine path: /Users/pranay/Projects/travel_agency_agent/OPERATING_DOCTRINE.md
- SHA-256: ff848618a7431a3b06c7409caa45683bd27c64263d45b93f9fcd36a89803466a
- Generated: 2026-09-14T11:58:35Z
- This is a generated review artifact, not an instruction source.

## SECTION_0

- Label: §0 Start from live truth
- Reviewed: True
- Evidence: Live truth refreshed: probes of src/intake/extractors.py guards, route_health seam, gdpr propagation in spine_api/routers/customer_memory.py; full suite 4,545 passed.

## SECTION_00_INTEGRATED

- Label: Full doctrine integrated audit
- Reviewed: True
- Evidence: Integrated audit 2026-09-14: no-decisions batch landed across spine_api/core/trip_lifecycle_harness.py, src/decision/telemetry.py, src/intake/airport_codes.py, src/memory/relationship_stages.py, src/memory/slot_candidates.py wiring in src/intake/strategy.py, GDPR propagation in spine_api/routers/customer_memory.py, Hinglish extraction in src/intake/extractors.py. Gates: full suite 4,545 passed (parallel live_tools tranche carved out), ruff clean, targeted suites green per module. Evidence tiers: test output + run artifacts. Owner-gated residuals disclosed (X-09, shadow window, suitability corpus, Slot 2, trip-gate hooks, P-B/I/G/J).

## SECTION_1

- Label: §1 Outcomes and retained value
- Reviewed: True
- Evidence: Outcomes: lifecycle harness (spine_api/core/trip_lifecycle_harness.py), E-C rollups (src/decision/telemetry.py), P-F airport codes (src/intake/airport_codes.py), relationship axis (src/memory/relationship_stages.py), Hinglish extraction, GDPR X-14 fix.

## SECTION_10

- Label: §10 Parallel work and contested state
- Reviewed: True
- Evidence: Parallel work: src/agents/live_tools.py + tests/test_extraction_fixes.py demo11 tranche carved out (parallel agent mid-flight); price_lock order-flake isolated twice.

## SECTION_11

- Label: §11 Engineering and data integrity
- Reviewed: True
- Evidence: Engineering integrity: 4,545 passed full suite; ruff clean on all touched files; findings store append-only via scripts/findings.py; GDPR propagation tested in tests/test_gdpr_purge_propagation.py.

## SECTION_12

- Label: §12 AI output boundary
- Reviewed: True
- Evidence: AI output boundary: agent-built modules accepted only after direct test runs — src/memory/relationship_stages.py (35 tests), tests/test_decision_cost_rollup.py (E-C rollups), tests/test_airport_codes.py; all claims cite test output and run artifacts, no fabricated results.

## SECTION_13

- Label: §13 Product, operator, and claim reality
- Reviewed: True
- Evidence: Product reality verified by probes: 'flying into SIN next week' resolves Singapore via src/intake/airport_codes.py; 'hum goa gaye the, bahut accha laga' captures Goa with positive Hinglish sentiment in src/intake/extractors.py; forgotten travelers (spine_api/routers/customer_memory.py) can no longer re-hydrate from duplicate keys.

## SECTION_14

- Label: §14 Documentation and decisions
- Reviewed: True
- Evidence: Documentation: Addendum 10 appended to Docs/architecture/EXTRACTION_REALIGNMENT_BLUEPRINT_2026-09-14.md recording the batch; ADR-008 section 7 amendments; FND-0058 closure evidence recorded in Docs/review/FINDINGS_STORE.jsonl via the CLI.

## SECTION_15

- Label: §15 Completion contract
- Reviewed: True
- Evidence: Completion contract: full suite 4,545 passed before commit; targeted suites green per module (tests/test_airport_codes.py 5, tests/test_relationship_stages.py 35, tests/test_memory_slot_wiring.py 7, tests/test_gdpr_purge_propagation.py 2, tests/test_trip_lifecycle_harness.py 5, tests/test_decision_cost_rollup.py); residuals disclosed (X-09 PII gate, shadow window, suitability corpus, Slot 2 FreshnessCard, trip-gate hooks, P-B/I/G/J).

## SECTION_16

- Label: §16 Specialist doctrine routing
- Reviewed: True
- Evidence: Specialist routing: relationship axis built to the ratified PER-0369 council design (6 stages, invariants not adjacency, decay) in src/memory/relationship_stages.py; deterministic-first doctrine respected; no specialist conflicts.

## SECTION_17

- Label: §17 Propagation contract
- Reviewed: True
- Evidence: Propagation: contracts test-pinned in tests/test_airport_codes.py, tests/test_gdpr_purge_propagation.py, tests/test_decision_cost_rollup.py; graduation ledger documented in module docstrings.

## SECTION_2

- Label: §2 Truth taxonomy
- Reviewed: True
- Evidence: Truth taxonomy: src/memory/slot_candidates.py promotion-only contract; relationship stages are coarse persisted truth with derived signals; expired facts dropped not downweighted.

## SECTION_3

- Label: §3 Proportional rigor and evidence
- Reviewed: True
- Evidence: Proportional rigor: tests/test_airport_codes.py membership-guard, tests/test_memory_slot_wiring.py import containment, tests/test_relationship_stages.py invariants, tests/test_trip_lifecycle_harness.py graduation; threshold constants verified before use.

## SECTION_4

- Label: §4 Authorization and side effects
- Reviewed: True
- Evidence: Authorization: owner directive 'do all implementation and exploration work that doesnt need me or decisions' (2026-09-14); additive work only across src/, spine_api/core/, tests/; no destructive git operations; parallel tranche untouched.

## SECTION_5

- Label: §5 Canonical paths and ownership
- Reviewed: True
- Evidence: Canonical paths: extended spine_api/core/trip_lifecycle_harness.py beside the gate; airport codes in src/intake/; relationship stages in src/memory/; no parallel systems.

## SECTION_6

- Label: §6 Semantic salvage and supersession
- Reviewed: True
- Evidence: Supersession: routing_health event types renamed with alias cycle in src/analytics/logger.py + spine_api/routers/legacy_ops.py; old name aliased not deleted; dog/cat colliders documented in stop-word list.

## SECTION_7

- Label: §7 Capability routing
- Reviewed: True
- Evidence: Capability routing: council-orchestrator for ADR-008; deterministic-first doctrine; P-F/P-B phases from blueprint plan.

## SECTION_8

- Label: §8 Skills lifecycle
- Reviewed: True
- Evidence: Skills lifecycle: tools documented; no skill files changed; tests/test_airport_codes.py etc. added per reusable-tools practice.

## SECTION_9

- Label: §9 Exploration and durable knowledge
- Reviewed: True
- Evidence: Durable knowledge: Addendum 10 in Docs/architecture/EXTRACTION_REALIGNMENT_BLUEPRINT_2026-09-14.md records the batch; FND-0058 closed with evidence in Docs/review/FINDINGS_STORE.jsonl.
