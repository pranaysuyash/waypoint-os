# Operating Doctrine Review

- Doctrine path: /Users/pranay/Projects/travel_agency_agent/OPERATING_DOCTRINE.md
- SHA-256: ff848618a7431a3b06c7409caa45683bd27c64263d45b93f9fcd36a89803466a
- Generated: 2026-09-13T19:16:33Z
- This is a generated review artifact, not an instruction source.

## SECTION_0

- Label: §0 Start from live truth
- Reviewed: True
- Evidence: Ground truth refreshed before changes: runtime probes of _extract_destination_candidates on every guard case (side/VFR/past-trip/beach/Time-Pool colliders), live pipeline probes for past_trips/region_affinity/origin hypothesis, KDD corpus re-run records_sweepguard2.jsonl with valid .env key (HTTP 200 verified), full suite 4,414 passed baseline before commit.

## SECTION_00_INTEGRATED

- Label: Full doctrine integrated audit
- Reviewed: True
- Evidence: Integrated audit: extraction realignment wave committed end-to-end — deterministic guard layer (sweep stop words incl. 48 verified GeoNames colliders, shared placeholder/past-trip filters), VFR + travel-history + region-affinity facts, history-informed and origin-hypothesis asks (owner-ratified Option 3), corpus record flips with provenance, docs Addenda 1-6. Evidence tiers: KDD run files + grading receipt + 10/10 probe output + full suite 4,414 passed; gates preceded claims; owner ratifications cited in-conversation; residual knowns disclosed. Motto-Reviewed: full.

## SECTION_1

- Label: §1 Outcomes and retained value
- Reviewed: True
- Evidence: Outcomes: extraction realignment wave — sweep guards, VFR promotion + family_visit purpose, past_trips/region_affinity memory facts, history-informed asks, origin Option 3 hypothesis contract; KDD gate F1 0.808 vs 0.800 (records_sweepguard2.jsonl); Sim #2 acceptance probe 10/10.

## SECTION_10

- Label: §10 Parallel work and contested state
- Reviewed: True
- Evidence: Parallel work engaged per doctrine: _is_likely_origin narrowing in src/intake/extractors.py from a parallel tranche restored to HEAD exclusion semantics after branch-level bisect; stale adv_ling_003 expectation in data/fixtures/adversarial/adversarial_seed_v1.json flipped; price_lock order-flake (tests/test_price_lock_sentinel.py) isolated twice and documented as known class; no same-file simultaneous edits.

## SECTION_11

- Label: §11 Engineering and data integrity
- Reviewed: True
- Evidence: Engineering integrity: findings store written only via scripts/findings.py CLI; append-only corpus record updated via json round-trip preserving all other records; full suite 4,414 passed + 1,220-decision net green; ruff clean on all touched files; no test mocks diverging from real API contracts (decision asks verified via live pipeline probes).

## SECTION_12

- Label: §12 AI output boundary
- Reviewed: True
- Evidence: AI output boundary: all gate numbers cite recorded runs — data/experiments/hybrid_kdd_v1/records_sweepguard2.jsonl with grading_receipt.json, probe output reproduced verbatim from tools/sim2_acceptance_probe.py; the 401-fallback run preserved as records_sweepguard.jsonl for lineage instead of hidden; no benchmark numbers claimed without a recorded run artifact.

## SECTION_13

- Label: §13 Product, operator, and claim reality
- Reviewed: True
- Evidence: Product reality (src/intake): VFR segment promoted — 'visit family in india' now yields India + family_visit purpose (real revenue behavior); origin/destination asks mirror good human agent behavior (confirm, don't assume); no fabricated destinations/origins enter quote math — verified by tools/sim2_acceptance_probe.py 10/10.

## SECTION_14

- Label: §14 Documentation and decisions
- Reviewed: True
- Evidence: Documentation: blueprint Addenda 1-6 under Docs/architecture/EXTRACTION_REALIGNMENT_BLUEPRINT_2026-09-14.md; V02 governing principle §1 extended with the two-direction doctrine; tools/README.md entry for the probe; KDD_MODEL_COMPARISON re-pull recipe corrected; all decisions dated and owner-attributed.

## SECTION_15

- Label: §15 Completion contract
- Reviewed: True
- Evidence: Completion contract: both gates run to green BEFORE completion claims — KDD note-level re-run (data/experiments/hybrid_kdd_v1/records_sweepguard2.jsonl, F1 0.808 vs 0.800) and 10/10 acceptance probe; full suite 4,414 passed; residual knowns named (1 single-run variance FP, price_lock order-flake, English-only sentiment cues); remaining DECIDEs listed to owner.

## SECTION_16

- Label: §16 Specialist doctrine routing
- Reviewed: True
- Evidence: Specialist routing: agentic-eval-loop doctrine used for the KDD gate design; deterministic-first principle extended in Docs/V02_GOVERNING_PRINCIPLES.md rather than forked; skills routing per Docs/FULL_SKILLS_CATALOG.md; no specialist doctrine conflicts encountered in src/intake changes.

## SECTION_17

- Label: §17 Propagation contract
- Reviewed: True
- Evidence: Propagation: contracts encoded as executable tests in tests/test_extraction_fixes.py and tests/test_history_informed_questions.py (three-way origin contract, direction OPEN, VFR promotion, memory-not-intent) plus the reusable gate tools/sim2_acceptance_probe.py so future changes cannot silently regress; consumer contract for region_affinity documented in Docs/architecture/EXTRACTION_REALIGNMENT_BLUEPRINT_2026-09-14.md Addendum 5 for downstream phases.

## SECTION_2

- Label: §2 Truth taxonomy
- Reviewed: True
- Evidence: Truth taxonomy enforced in src/intake/extractors.py + src/intake/decision.py: memories (past_trips) are history facts never intent; directional 'X side' is hypothesis not fact (owner-ratified Option 3); region_affinity documented as preference signal never-an-extraction-fact (blueprint Addendum 5); FACT vs SOFT_HYPOTHESIS separation encoded and test-pinned.

## SECTION_3

- Label: §3 Proportional rigor and evidence
- Reviewed: True
- Evidence: Proportional rigor in src/intake/extractors.py: class-shaped guards (past-clause span regex, direction postposition) over word lists; every guard has counter-tests in tests/test_extraction_fixes.py (family trip to japan, Virginia Beach bigrams, okinawa side trip); note-level KDD eval re-run per falsification doctrine; 48 GeoNames colliders verified against src/intake/geography.py before adding.

## SECTION_4

- Label: §4 Authorization and side effects
- Reviewed: True
- Evidence: Authorization: commit explicitly requested by owner ('follow our full commit process'); Option 3 origin semantics ratified in-conversation 2026-09-14; .zshenv dead-key cleanup owner-directed; no destructive git operations (no reset/checkout/clean); all changes additive.

## SECTION_5

- Label: §5 Canonical paths and ownership
- Reviewed: True
- Evidence: Canonical paths only: extended src/intake/extractors.py + decision.py + geography.py — no parallel extraction system; sweep now reuses shared _NON_DESTINATION_PLACEHOLDERS filter and shared _is_past_trip_mention (clause+span) instead of duplicate checks; stop-word set promoted to module level per perf doctrine.

## SECTION_6

- Label: §6 Semantic salvage and supersession
- Reviewed: True
- Evidence: Supersession: family-locative guard removed only after field-by-field comparison (true-positive suppression replaced by VFR promotion + family_visit purpose; documented in blueprint Addendum 3); adv_ling_003 in data/fixtures/adversarial/adversarial_seed_v1.json flipped with fixed_in provenance, not deleted; dead key in .zshenv commented in place with dated note.

## SECTION_7

- Label: §7 Capability routing
- Reviewed: True
- Evidence: Capability routing: deterministic-first doctrine (V02 §1) applied and extended with the two-direction learning; council/persona and eval-lane skills consulted per Docs/FULL_SKILLS_CATALOG.md routing; agentic-eval doctrine followed for the KDD gate.

## SECTION_8

- Label: §8 Skills lifecycle
- Reviewed: True
- Evidence: Skills lifecycle: no skill files added/removed; new repo tool sim2_acceptance_probe.py documented in tools/README.md per reusable-tools practice.

## SECTION_9

- Label: §9 Exploration and durable knowledge
- Reviewed: True
- Evidence: Durable knowledge: blueprint Addenda 1-6 under Docs/architecture/EXTRACTION_REALIGNMENT_BLUEPRINT_2026-09-14.md; two-direction doctrine added to Docs/V02_GOVERNING_PRINCIPLES.md; findings FND-0286 closed via scripts/findings.py with evidence chain; Docs/exploration/KDD_MODEL_COMPARISON_2026-09-12.md recipe corrected.
