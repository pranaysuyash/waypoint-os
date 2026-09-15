# Operating Doctrine Review

- Doctrine path: /Users/pranay/Projects/travel_agency_agent/OPERATING_DOCTRINE.md
- SHA-256: ff848618a7431a3b06c7409caa45683bd27c64263d45b93f9fcd36a89803466a
- Generated: 2026-09-15T06:49:15Z
- This is a generated review artifact, not an instruction source.

## SECTION_0

- Label: §0 Start from live truth
- Reviewed: True
- Evidence: Started from live truth: mapped every confirmation writer/reader via rg across spine_api/, src/, tests/ before planning; re-read today's F-31 working-tree state (confirmation_service.py, insurance.py, booking_fulfillment.py) and the parallel agents' mid-session landings before deciding adopt-vs-retire per family.

## SECTION_00_INTEGRATED

- Label: Full doctrine integrated audit
- Reviewed: True
- Evidence: Integrated audit (recorded last): FND-0174/F-31 resolution validated across spine_api/services/confirmation_service.py, spine_api/routers/confirmations.py, spine_api/routers/insurance.py, src/orchestration/booking_fulfillment.py and their tests — SM adopted as durable authority, blob as confirmation_id projection, extract auto-record repaired from a guaranteed TypeError into the canonical SM with draft-to-recorded, verify/void completed to atomic transactional internals, AT-04 replay convergent (relinked:true, no double-record). Receipts: 109 passed across 9 confirmation-family test files, ruff clean, scripts/findings.py validate OK (0 warnings). Scope bounded to the validated cluster plus tests/conftest.py; other agents' in-flight work left for their owners.

## SECTION_1

- Label: §1 Outcomes and retained value
- Reviewed: True
- Evidence: Retained value: extract auto-record path repaired from a guaranteed TypeError (pre-F-31 keyword signature) to the canonical data:dict contract with draft-to-recorded; AT-04 convergent replay pinned by tests (relinked:true, never double-record); verify/void migrated to transactional internals; explicit persistence markers make previews honest. Receipts: 109 passed across the 9-file confirmation-family suite, ruff clean on all changed files, findings validate OK.

## SECTION_10

- Label: §10 Parallel work and contested state
- Reviewed: True
- Evidence: Parallel work handled as contested state: mid-session other agents closed FND-0174, hardened the insurance audit test, and landed proposal-token/group-booking work; I re-checked drift before acting, verified no overlapping edits, and bounded this commit to the cluster my tests validate (109 passed with all parallel work present in the tree).

## SECTION_11

- Label: §11 Engineering and data integrity
- Reviewed: True
- Evidence: Engineering/data integrity: verify/void now commit row and required execution event atomically (failure leaves no partial status — pinned by test through a fresh-session read); convergent replay re-links the existing durable row instead of colliding with uq_bc_trip_type_active; no silent data loss paths introduced; inference types outside CONFIRMATION_TYPES clamp to 'other' with the fine-grained type preserved in extracted payload and row notes.

## SECTION_12

- Label: §12 AI output boundary
- Reviewed: True
- Evidence: AI output boundary: every claim tied to receipts — pytest tails (109 passed across tests/test_booking_confirmation_uniqueness.py, tests/test_confirmation_extraction.py, tests/test_confirmation_transition_atomicity.py et al.), ruff output on changed files, scripts/findings.py validate output; the unowned audit-attribution flake in tests/test_insurance_quote_evidence.py was reported as a risk first, and its hardening landed via the owning stream rather than being silently patched.

## SECTION_13

- Label: §13 Product, operator, and claim reality
- Reviewed: True
- Evidence: Claim reality: operators get durable evidence for operator-extracted confirmations via spine_api/routers/confirmations.py (durable SQL row + recorded status + execution event) with an explicit persistence marker on every extract response (preview_only vs sql_confirmation_recorded); spine_api/routers/insurance.py surfaces replay/replay-receipt state honestly; no response implies carrier verification or durability that does not exist.

## SECTION_14

- Label: §14 Documentation and decisions
- Reviewed: True
- Evidence: Documentation and decisions: rationale recorded in Docs/review/FINDINGS_STORE.jsonl via scripts/findings.py notes (FND-0174 complementary note, FND-0118 verify/void completion note), in test module docstrings (supersession rationale in tests/test_confirmation_extraction.py, parity contract in tests/test_confirmation_transition_atomicity.py), and in this commit message; CHANGELOG.md and Docs/ streams owned by other in-flight work were not touched.

## SECTION_15

- Label: §15 Completion contract
- Reviewed: True
- Evidence: Completion contract: code-ready yes (109 tests passed, ruff clean, findings validate OK with 0 warnings); feature-ready: every confirmation family is durable-with-projection-linkage or explicitly honest per the map recorded on FND-0174; launch-ready claims not extended beyond evidence. Commit bounded to spine_api/services/confirmation_service.py + its router/engine callers + tests; all other in-flight streams remain with their owners.

## SECTION_16

- Label: §16 Specialist doctrine routing
- Reviewed: True
- Evidence: Specialist doctrine routing: FastAPI backend change verified with pytest at both seams (HTTP via session_client against spine_api/routers/, transactional via the aiosqlite harness in tests/test_confirmation_transition_atomicity.py), ruff lint gate on every changed file, scripts/findings.py validate for the findings lifecycle — no ad-hoc verification invented.

## SECTION_17

- Label: §17 Propagation contract
- Reviewed: True
- Evidence: Propagation: the SQL-SM-as-authority model and its per-family contracts are propagated through durable artifacts (Docs/review/FINDINGS_STORE.jsonl notes, tests/test_confirmation_family_durability.py, tests/test_confirmation_transition_atomicity.py docstrings, this commit message) and the tests/conftest.py dependency is carried in the same commit so the suite is self-contained for the next agent.

## SECTION_2

- Label: §2 Truth taxonomy
- Reviewed: True
- Evidence: Truth taxonomy applied per family: SQL BookingConfirmation is the durable authority for flight/insurance/manual-CRUD families; the trip blob is a derived projection carrying confirmation_id; proposal acceptance is declared trip-record-durable via explicit reality_tier/storage markers; extract preview responses state persistence=preview_only vs sql_confirmation_recorded instead of implying durability.

## SECTION_3

- Label: §3 Proportional rigor and evidence
- Reviewed: True
- Evidence: Proportional rigor: contract-level verification only — deterministic HTTP tests against the real router (session_client), SQL row reads through RLS-bound private engines, service-level commit/emit spies on an isolated aiosqlite harness; no doc-only claims. Baseline (52+40) re-run green before changes; 109 green after.

## SECTION_4

- Label: §4 Authorization and side effects
- Reviewed: True
- Evidence: Authorization and side effects: no git write actions until explicit user approval (this commit); working tree only throughout (no checkout/reset/clean anywhere in the session); disk cleanup after ENOSPC limited to stale session logs under /Users/pranay/.zcode/cli/exec; test DB writes additive (ON CONFLICT DO NOTHING in tests/conftest.py factory) or isolated in tests/test_confirmation_transition_atomicity.py in-memory SQLite — live waypoint_os Postgres never written.

## SECTION_5

- Label: §5 Canonical paths and ownership
- Reviewed: True
- Evidence: Canonical paths only: extended the canonical confirmation_service and existing routers; no new API routes, no parallel confirmation system; commit scope bounded to the validated confirmation cluster plus its direct dependency tests/conftest.py (capture_audit_events/boundary_principal_factory fixtures the committed tests import); contested parallel-agent work (rag, memory, SSE, proposal tokens, payouts) left uncommitted for its owners.

## SECTION_6

- Label: §6 Semantic salvage and supersession
- Reviewed: True
- Evidence: Supersession applied with field-by-field comparison: the vacuous conditional extraction test (if resp.status_code == 200) was replaced only after its full assertion set (flight/hotel type, number, supplier, confidence) was preserved unconditionally plus durable-record coverage — supersession documented in the test module docstring; the broken extract auto-record caller was adopted/repaired, not deleted (zero unique behavior lost).

## SECTION_7

- Label: §7 Capability routing
- Reviewed: True
- Evidence: Capability routing: used the repo's own doctrine surfaces — AGENTS.md commit gate + findings CLI lifecycle (scripts/findings.py note/validate, never hand-editing FINDINGS_STORE.jsonl), ruff and pytest per repo standards; rg default per the Search Tool Default Policy.

## SECTION_8

- Label: §8 Skills lifecycle
- Reviewed: True
- Evidence: Skills lifecycle: no skill files created or modified in this change set; the change surface is spine_api/services/confirmation_service.py, spine_api/routers/confirmations.py, spine_api/routers/insurance.py, src/orchestration/booking_fulfillment.py, tests/conftest.py, and six test modules under tests/.

## SECTION_9

- Label: §9 Exploration and durable knowledge
- Reviewed: True
- Evidence: Durable knowledge: adopt/retire rationale, per-family map, and the audit-attribution flake analysis recorded via scripts/findings.py notes on FND-0174 (closed by parallel agent; complementary note appended) and FND-0118 (verify/void completion note) — durable in Docs/review/FINDINGS_STORE.jsonl, not session-local.
