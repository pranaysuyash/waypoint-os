# Operating Doctrine Review

- Doctrine path: /Users/pranay/Projects/travel_agency_agent/OPERATING_DOCTRINE.md
- SHA-256: ff848618a7431a3b06c7409caa45683bd27c64263d45b93f9fcd36a89803466a
- Generated: 2026-09-11T14:10:52Z
- This is a generated review artifact, not an instruction source.

## SECTION_0

- Label: §0 Start from live truth
- Reviewed: True
- Evidence: Live truth refreshed each phase: git status/log re-checked before edits and before finalizing; parallel extractor batch detected mid-session and its files avoided; suite receipts captured from 5 full runs.

## SECTION_00_INTEGRATED

- Label: Full doctrine integrated audit
- Reviewed: True
- Evidence: Integrated pass completed last: full audit (Docs/reviews/ELENA_COUNCIL_CODEBASE_AUDIT_2026-09-11.md) -> 13 findings registered via CLI -> 12 closed with file:line/test/command evidence, 1 deferred with reopen trigger; A2/A4/A6 completed on canonical paths; P1 security + honesty fixes gated; full suite, tsc, vitest, ruff, scoped mypy green before commit; all sections above individually attested with session-specific evidence.

## SECTION_1

- Label: §1 Outcomes and retained value
- Reviewed: True
- Evidence: Outcomes retained: P1 tenant hole closed with a CI gate; fabricated /quotes surface honest; 9 mislabeled feature rows corrected at source of truth; A2/A4 completed; GMV + review-history operator gains shipped; receipts in Docs/review/ELENA_AUDIT_REMEDIATION_HANDOFF_2026-09-11.md.

## SECTION_10

- Label: §10 Parallel work and contested state
- Reviewed: True
- Evidence: Parallel work honored per shared-tree doctrine: concurrent agent owned src/intake/extractors.py, tests/test_extraction_fixes.py, data/fixtures/adversarial/adversarial_seed_v1.json (left untouched); its invariant break in tests/test_adversarial_lane.py (KNOWN_DEFECT_IDS vs corpus) was completed with a dated note; no other parallel-owned file edited; git status re-checked before finalizing docs/review/OPEN_WORK_ROADMAP_2026-09-08.md.

## SECTION_11

- Label: §11 Engineering and data integrity
- Reviewed: True
- Evidence: Data integrity: A4 removed raw VCC/e-ticket from the plaintext trip lane with reader-audit proof (zero readers) and zero legacy rows (live DB check); encryption-at-rest unchanged in confirmation_service; GMV sums only real recorded budgets; attachment caps now physically enforceable; no silent data loss path introduced.

## SECTION_12

- Label: §12 AI output boundary
- Reviewed: True
- Evidence: AI output boundary: persona lenses (Elena council) marked as judgment; all promoted issues carry file:line or command evidence; no fabricated claims — the /quotes fabrications were removed, not replicated; scanner Chinese titles translated with source noted in the triage annex.

## SECTION_13

- Label: §13 Product, operator, and claim reality
- Reviewed: True
- Evidence: Operator reality: /quotes no longer offers fabricated client pricing; review queue now shows decision history and Rejected/Revision tabs; GMV card real-or-0; feature inventory rows now match what an operator can actually reach.

## SECTION_14

- Label: §14 Documentation and decisions
- Reviewed: True
- Evidence: Documentation: LAUNCH_STATUS evidence snapshot refreshed with dated sources; roadmap A2/A4/A6 receipts written with commit/test citations; Mimosa per-cluster triage annex added; decision pack records the FND-0268 execution prerequisite; handoff updated.

## SECTION_15

- Label: §15 Completion contract
- Reviewed: True
- Evidence: Completion contract: full suite + targeted lanes + tsc + vitest (184 files/1382) + ruff + scoped mypy (21 files) green at commit time; FND-0268 explicitly deferred (not silently dropped); remaining owner items listed in the handoff.

## SECTION_16

- Label: §16 Specialist doctrine routing
- Reviewed: True
- Evidence: Specialist routing matched the diff: security-privacy doctrine governed spine_api/routers/{visa_radar,concierge_upsell,fx_sentinel,disruption_radar,passenger_rights,subagent_payouts,loyalty}.py + spine_api/core/startup_assertions.py + scripts/check_unscoped_trip_access.sh; money-path durability rules governed src/orchestration/booking_fulfillment.py + spine_api/services/document_storage.py + spine_api/contract.py (Risk-Class: high, Evidence-Tier: 3); review-doctrine lifecycle ran via scripts/findings.py; testing doctrine via tools/test_inventory.py + full pytest lanes; docs doctrine via Docs/status/FEATURE_LIST_V3_2026-09-10.md regeneration and Docs/LAUNCH_STATUS.md refresh.

## SECTION_17

- Label: §17 Propagation contract
- Reviewed: True
- Evidence: Propagation: shared-tree completion (adversarial registry) documented in place; roadmap + handoff + feature list carry forward-state for the next agent; commit trailers will carry Motto/Risk/Evidence for audit propagation.

## SECTION_2

- Label: §2 Truth taxonomy
- Reviewed: True
- Evidence: Truth precedence applied to the diff: LIVE claims corrected from caller traces (spine_api/services/ghost_concierge.py zero importers; src/briefing/pre_departure_cadence.py orphaned; spine_api/routers/disruption_radar.py self-declared preview) overwriting Docs/status/FEATURE_LIST_V3_2026-09-10.md rows; suite totals replaced by tools/test_inventory.py collection receipt (4563); A4 reader audit (zero readers of vcc_card_id/e_ticket_number on the trip lane) outranked the roadmap's encrypt-in-place assumption.

## SECTION_3

- Label: §3 Proportional rigor and evidence
- Reviewed: True
- Evidence: Proportional rigor across the diff: P1 ISS-001 tenant scoping got scripts/check_unscoped_trip_access.sh extension + tests/test_cross_tenant_header_scoping.py; P1 ISS-002 got honesty tests in frontend/src/app/(agency)/quotes/__tests__/page.test.tsx; P2 attachment caps got tests/test_fnd0267_attachment_hardening.py; P3 MRZ/GMV/queue changes got parity tests (tests/test_a2_a4_canonical_consolidation.py, tests/test_analytics_truth_hardening.py); deferred FND-0268 received a decision pack, not code.

## SECTION_4

- Label: §4 Authorization and side effects
- Reviewed: True
- Evidence: Authorization: user message 'do all following doctrines including how we commit' authorizes commits this conversation; all changes are working-tree edits to repo files (spine_api/, src/, frontend/src/, tests/, tools/, Docs/, .env.example, docker-compose.yml, fly.toml, scripts/check_unscoped_trip_access.sh); no push, no server/deploy action, no DB mutation (A4 live check: 0 trips rows); commit creation only, on master, no force ops.

## SECTION_5

- Label: §5 Canonical paths and ownership
- Reviewed: True
- Evidence: Ownership respected: edits confined to canonical surfaces (routers, services, canonical MD sources); derived artifacts regenerated via their generators; no parallel systems created (scrub/migration paths withdrawn when unnecessary).

## SECTION_6

- Label: §6 Semantic salvage and supersession
- Reviewed: True
- Evidence: Salvage: pre-existing half-executed upstream A2 work (0becb27) verified then completed rather than re-done; orphaned canonical service given its serving-path caller; /quotes feature intent preserved as honest sample-data pending owner decision.

## SECTION_7

- Label: §7 Capability routing
- Reviewed: True
- Evidence: Capability routing: rg for every content search (repo 2026-05-08 policy); scripts/findings.py for all 13 finding transitions; tools/feature_list_generate.py regenerated FEATURE_LIST_V3 json/csv; scripts/generate_types.py regenerated frontend/src/types/generated/spine-api.ts; tools/test_inventory.py new reusable receipt tool documented in tools/README.md; council orchestrator + document-audit protocol structured the audit.

## SECTION_8

- Label: §8 Skills lifecycle
- Reviewed: True
- Evidence: Skill lifecycle: installed adapters (council-orchestrator, random-repository-document-audit) loaded before canonical sources; Mimosa PreToolUse hook rejections honored on tools/test_inventory.py (rewritten in-process, no subprocess), alembic/versions/a4_trip_conf_secret_scrub.py (withdrawn for ORM tools approach), and tools/scrub_trip_confirmation_secrets.py (deleted when the SQL lane proved empty); repo tools used as-is: scripts/findings.py, tools/feature_list_generate.py, scripts/generate_types.py.

## SECTION_9

- Label: §9 Exploration and durable knowledge
- Reviewed: True
- Evidence: Exploration made durable: margin-basis decision pack with execution prerequisite (Docs/exploration/MARGIN_BASIS_DECISION_PACK_FND0268_2026-09-11.md); Mimosa HIGH triage annex converts a blanket noise claim into per-cluster evidence (Docs/review/MIMOSA_HIGH_RESIDUAL_TRIAGE_2026-09-11.md); FND-0268 deferred with explicit reopen condition instead of silently dropped.
