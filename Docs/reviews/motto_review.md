# Operating Doctrine Review

- Doctrine path: /Users/pranay/Projects/travel_agency_agent/OPERATING_DOCTRINE.md
- SHA-256: ff848618a7431a3b06c7409caa45683bd27c64263d45b93f9fcd36a89803466a
- Generated: 2026-09-08T16:28:27Z
- This is a generated review artifact, not an instruction source.

## SECTION_0

- Label: §0 Start from live truth
- Reviewed: True
- Evidence: src/orchestration/booking_fulfillment.py + spine_api/persistence.py: live-SQL run exposed the _extra data-loss that static passes missed; fixed and re-proven against the dev server

## SECTION_00_INTEGRATED

- Label: Full doctrine integrated audit
- Reviewed: True
- Evidence: Integrated audit across the staged diff: src/orchestration/booking_fulfillment.py + spine_api/persistence.py (exactly-once + _extra merge root fix), spine_api/routers/fulfillment.py + journey_graph.py (idempotent replay, attestation), frontend/src/app/(traveler)/companion/page.tsx + frontend/src/app/p/[token]/page.tsx (fail-closed honest preview), frontend/src/app/(agency)/** copy pass, tests/ new coverage, scripts/hooks/pre-commit gate scope fix. Verified: 103 backend + 1,337 frontend tests, scoped mypy 21 files, ruff/tsc clean, live browser proof on trip_l7_browser_smoke_20260907_b

## SECTION_1

- Label: §1 Outcomes and retained value
- Reviewed: True
- Evidence: frontend/src/app/(traveler)/companion/page.tsx now renders the real persisted itinerary with preview framing; browser-verified with the signed token for trip_l7_browser_smoke_20260907_b

## SECTION_10

- Label: §10 Parallel work and contested state
- Reviewed: True
- Evidence: Parallel PER-0442/PER-0443 sessions' work was verified claim-by-claim (register Part G) rather than redone; the parallel route-inventory gate removal of assess-route was accepted as correct

## SECTION_11

- Label: §11 Engineering and data integrity
- Reviewed: True
- Evidence: spine_api/persistence.py deep-merges analytics._extra now; spine_api/models/tenant.py + alembic/versions/bc_active_type_uniqueness.py enforce one active confirmation per trip/type; src/orchestration/agent_lease.py heartbeat

## SECTION_12

- Label: §12 AI output boundary
- Reviewed: True
- Evidence: spine_api/providers/stripe_issuing_adapter.py refuses fake livemode instruments; src/schemas/journey_graph.py keeps reality tiers machine-readable while traveler copy drops the slugs

## SECTION_13

- Label: §13 Product, operator, and claim reality
- Reviewed: True
- Evidence: frontend/src/app/(traveler)/companion/page.tsx and frontend/src/app/p/[token]/page.tsx delete fabricated fallbacks; invalid links abstain with advisor next steps

## SECTION_14

- Label: §14 Documentation and decisions
- Reviewed: True
- Evidence: Docs/review/FINDINGS_TASKS_IMPLICIT_EXPLICIT_REGISTER_PER0443_2026-09-07.md Parts G-L and Docs/review/SESSION_EVIDENCE_CONSOLIDATION_DEMO_READY_2026-09-07.md document every decision; nothing deleted

## SECTION_15

- Label: §15 Completion contract
- Reviewed: True
- Evidence: Docs/review/IMPLEMENTATION_PLAN_PER0443_2026-09-07.md plus Docs/LAUNCH_STATUS.md record the explicit verdicts: code-ready, feature partial, launch NO-GO

## SECTION_16

- Label: §16 Specialist doctrine routing
- Reviewed: True
- Evidence: Docs/review/PERSONA_AUDIT_PER0443_AGENTIC_TRAVEL_SYSTEMS_ARCHITECT_2026-09-07.md persona lens applied across src/orchestration/ and spine_api/routers/ surfaces

## SECTION_17

- Label: §17 Propagation contract
- Reviewed: True
- Evidence: scripts/hooks/pre-commit now honors curated mypy scope; fix propagated through the workspace installer template for all managed repos

## SECTION_2

- Label: §2 Truth taxonomy
- Reviewed: True
- Evidence: spine_api/routers/journey_graph.py top-level provider_connected/reality_tier attestation derived fail-closed; register Parts G-L label Observed vs Proposed

## SECTION_3

- Label: §3 Proportional rigor and evidence
- Reviewed: True
- Evidence: 103 backend + 1,337 frontend tests; scoped mypy gate expanded to 21 money/booking files; codex external reviews triaged with file:line evidence

## SECTION_4

- Label: §4 Authorization and side effects
- Reviewed: True
- Evidence: spine_api/routers/fulfillment.py RLS-blocked confirmation write surfaced honestly as recorded:false; no push executed; commit only on the owner's explicit instruction

## SECTION_5

- Label: §5 Canonical paths and ownership
- Reviewed: True
- Evidence: src/orchestration/booking_fulfillment.py and spine_api/services/confirmation_service.py extend canonical paths; zero new routers for existing resources

## SECTION_6

- Label: §6 Semantic salvage and supersession
- Reviewed: True
- Evidence: frontend/src/app/(traveler)/itinerary-checker/PageClient.tsx formatTravelerBlockerItem fallback replaces raw backend slugs; src/logistics/irrops_healer.py EU261 calculator preserved pending migration

## SECTION_7

- Label: §7 Capability routing
- Reviewed: True
- Evidence: Codex external reviews, Explore subagent audits, and the browser-use skill were routed per AGENTS.md skill order; no gstack default

## SECTION_8

- Label: §8 Skills lifecycle
- Reviewed: True
- Evidence: Docs/FULL_SKILLS_CATALOG.md remains the agent-pointable index; control-browser skill followed for in-app-browser verification

## SECTION_9

- Label: §9 Exploration and durable knowledge
- Reviewed: True
- Evidence: India proprietor-agency domain research (consolidators TBO/Mystifly, WhatsApp-first CRMs, payment-collection pains) recorded with sources in session evidence section 3
