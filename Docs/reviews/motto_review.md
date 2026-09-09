# Operating Doctrine Review

- Doctrine path: /Users/pranay/Projects/travel_agency_agent/OPERATING_DOCTRINE.md
- SHA-256: ff848618a7431a3b06c7409caa45683bd27c64263d45b93f9fcd36a89803466a
- Generated: 2026-09-09T18:23:07Z
- This is a generated review artifact, not an instruction source.

## SECTION_0

- Label: §0 Start from live truth
- Reviewed: True
- Evidence: tests/test_adversarial_lane.py: live-SQL and live-corpus truth — the 40-record adversarial corpus is now an executed lane, not a static fixture

## SECTION_00_INTEGRATED

- Label: Full doctrine integrated audit
- Reviewed: True
- Evidence: Integrated audit across the staged diff: tests/test_adversarial_lane.py (E-H activation over all 40 corpus records with frozen defect registry), src/agents/runtime.py (A2b provisional EU261 claim on escalation), frontend/src/app/(traveler)/itinerary-checker/PageClient.tsx (honest disclaimer copy replacing undefined CHECKER_DISCLAIMER), spine_api/product_b_events.py + public_checker surfaces (parallel-session files staged by git add -A). Gates: 46 focused backend tests + adversarial lane 3/3 + tsc clean. Residuals registered: PA-19 endpoint, A4 migration, L7-auth walk.

## SECTION_1

- Label: §1 Outcomes and retained value
- Reviewed: True
- Evidence: frontend/src/app/(traveler)/companion/page.tsx and frontend/src/app/(agency)/workbench: operator and traveler surfaces gain real disruption ripple + EU261 claim visibility

## SECTION_10

- Label: §10 Parallel work and contested state
- Reviewed: True
- Evidence: src/agents/runtime.py changes verified against parallel sessions' shared-tree edits; no simultaneous same-file conflicts observed

## SECTION_11

- Label: §11 Engineering and data integrity
- Reviewed: True
- Evidence: tests/test_adversarial_lane.py frozen-defect-registry semantics; spine_api/routers/logistics.py assess-route is deterministic with 422 fail-closed on missing coordinates

## SECTION_12

- Label: §12 AI output boundary
- Reviewed: True
- Evidence: frontend/src/app/(traveler)/itinerary-checker/PageClient.tsx disclaimer copy is honest (advisory previews, advisor review) with no fabricated guarantees

## SECTION_13

- Label: §13 Product, operator, and claim reality
- Reviewed: True
- Evidence: frontend copy sweep: no tokens/slugs/endpoints in traveler surfaces; escrow of raw checker slugs via fallback advisor line

## SECTION_14

- Label: §14 Documentation and decisions
- Reviewed: True
- Evidence: Docs/review/OPEN_WORK_ROADMAP_2026-09-08.md and FINDINGS_TASKS_IMPLICIT_EXPLICIT_REGISTER_PER0443_2026-09-07.md carry FOR-LATER markers and Part N receipts

## SECTION_15

- Label: §15 Completion contract
- Reviewed: True
- Evidence: Verdicts: E-H lane activated (tests/test_adversarial_lane.py), A2b claim attach shipped in src/agents/runtime.py; PA-19 endpoint + A4 migration explicitly remain open

## SECTION_16

- Label: §16 Specialist doctrine routing
- Reviewed: True
- Evidence: Docs/architecture/TIMELINE_AS_EVIDENCE_ADR_2026-09-08.md and MEMORY_READ_PATH_SLOT_SPEC_2026-09-08.md are the cited designs for the next slices

## SECTION_17

- Label: §17 Propagation contract
- Reviewed: True
- Evidence: workspace hook template mypy-scope fix propagates via installer; adversarial lane is CI-runnable via pytest tests/test_adversarial_lane.py

## SECTION_2

- Label: §2 Truth taxonomy
- Reviewed: True
- Evidence: tests/test_adversarial_lane.py asserts expected-vs-got per record; register Part N labels known-defect vs fixed

## SECTION_3

- Label: §3 Proportional rigor and evidence
- Reviewed: True
- Evidence: Evidence tier 3: tests/test_adversarial_lane.py runs all 40 corpus records through src/intake/extractors.py; 46 focused backend tests + 1,371 frontend tests cited in this diff

## SECTION_4

- Label: §4 Authorization and side effects
- Reviewed: True
- Evidence: Escalation writes stay inside trip_repo via src/agents/runtime.py; commit only, no push; staged blast radius = 12 files

## SECTION_5

- Label: §5 Canonical paths and ownership
- Reviewed: True
- Evidence: tests/test_adversarial_lane.py extends the canonical intake pipeline tests; src/agents/runtime.py extends the existing agent rather than adding a new one

## SECTION_6

- Label: §6 Semantic salvage and supersession
- Reviewed: True
- Evidence: formatTravelerBlockerItem fallback retained in frontend/src/app/(traveler)/itinerary-checker/PageClient.tsx; KNOWN_DEFECT_IDS registry preserves corpus defect history

## SECTION_7

- Label: §7 Capability routing
- Reviewed: True
- Evidence: spine_api/routers/logistics.py assess-route and frontend/src/lib/route-map.ts were verified through route-map tests and live curl before mapping

## SECTION_8

- Label: §8 Skills lifecycle
- Reviewed: True
- Evidence: Docs/FULL_SKILLS_CATALOG.md skill order followed (control-browser, adversarial eval routing per AGENTS.md)

## SECTION_9

- Label: §9 Exploration and durable knowledge
- Reviewed: True
- Evidence: Docs/exploration/PROVIDER_CONNECTOR_AND_INDIA_PAYMENTS_RESEARCH_2026-09-08.md recorded with orientation-tier honesty; adversarial corpus provenance kept in data/fixtures
