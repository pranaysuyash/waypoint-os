# Operating Doctrine Review

- Doctrine path: /Users/pranay/Projects/travel_agency_agent/OPERATING_DOCTRINE.md
- SHA-256: ff848618a7431a3b06c7409caa45683bd27c64263d45b93f9fcd36a89803466a
- Generated: 2026-09-10T07:02:47Z
- This is a generated review artifact, not an instruction source.

## SECTION_0

- Label: §0 Start from live truth
- Reviewed: True
- Evidence: Start from live truth: re-read current pre-commit hook + ci.yml + findings store before edit; fresh git status caught parallel drift (6b5d962/ec089f8 absorbed repair+tool; motto_review.md staged by other agent, left untouched via pathspec commit)

## SECTION_00_INTEGRATED

- Label: Full doctrine integrated audit
- Reviewed: True
- Evidence: Integrated cross-section audit of staged diff (pre-commit hook check 6 + CI docs-quality gate + findings store rows + process review doc + tool already in HEAD via 6b5d962): docs-and-CI-only change surface, no product code path. §11 verified with falsification test; §10 parallel staged motto_review.md deliberately excluded via pathspec; §12 gate self-caught false-positive risk (markers quoted in review doc) and was re-anchored to defect shape before commit; §14 markdownlint MD032 fixed. Residual: FND-0256 series-lifecycle owner decisions (INDEX listing, ingestion path B3b, series continuation B4b) deferred to owner, not silently decided by agent.

## SECTION_1

- Label: §1 Outcomes and retained value
- Reviewed: True
- Evidence: Retained value: 108 docs restored to clean Markdown via tools/strip_envelope_fragments.py (envelope tails + /Users/pranay absolute paths removed); FND-0257 closed with evidence; review doc Docs/travel_agency_process_issue_review_2026-09-10.md records the incident durably

## SECTION_10

- Label: §10 Parallel work and contested state
- Reviewed: True
- Evidence: Parallel work preserved via drift re-checks: fresh git status before staging caught parallel agent's work; their staged Docs/reviews/motto_review.md excluded from my commit via pathspec; their src/analytics/metrics.py + tools/performance_benchmark_matrix.py changes untouched; my earlier repair absorbed by their 6b5d962 recorded honestly in Docs/travel_agency_process_issue_review_2026-09-10.md.

## SECTION_11

- Label: §11 Engineering and data integrity
- Reviewed: True
- Evidence: Engineering integrity: findings store CLI-only writes, validate OK 0 warnings; FINDINGS_LIVE regenerated via render (257 findings); hook bash -n syntax OK; tool ruff-clean (uv run ruff check tools/strip_envelope_fragments.py All checks passed); gate anchored to defect shape after self-test found false-positive risk on quoting docs

## SECTION_12

- Label: §12 AI output boundary
- Reviewed: True
- Evidence: AI output boundary: this change REMOVES AI envelope leakage from 108 committed docs (tools/strip_envelope_fragments.py); gates prevent recurrence at write time (hook check 6) and CI (docs-quality --check); no claim beyond verified marker scan

## SECTION_13

- Label: §13 Product, operator, and claim reality
- Reviewed: True
- Evidence: Claim reality: repair verified 108/108 exact shape; tests green 271/271 + 3/3; no user-facing behavior change (docs corpus + gates only); incident documented with honest attribution (repair entered HEAD via parallel commit 6b5d962, not a dedicated commit)

## SECTION_14

- Label: §14 Documentation and decisions
- Reviewed: True
- Evidence: Documentation: incident review written at Docs/travel_agency_process_issue_review_2026-09-10.md (root cause, blast radius, evidence, guardrails, cross-repo spread, follow-ups); markdownlint-clean after MD032 fix; findings rows canonical via scripts/findings.py CLI; FND-0256 remains open for owner decisions.

## SECTION_15

- Label: §15 Completion contract
- Reviewed: True
- Evidence: Completion contract: verified before claim — corpus --check exit 0; hook falsification-tested; tests green; parallel uncommitted work listed (motto_review.md, metrics.py, benchmark); owner decisions B3b/B4b surfaced, not silently decided

## SECTION_16

- Label: §16 Specialist doctrine routing
- Reviewed: True
- Evidence: Specialist doctrine routing: Operating v8.0 (sha256 ff848618a7431a3b06c7409caa45683bd27c64263d45b93f9fcd36a89803466a) active for this session; documentation discipline applied to Docs/ change; audit performed via canonical random-doc-audit + council-orchestrator chain; no specialist doctrine contradicted by this docs-only diff.

## SECTION_17

- Label: §17 Propagation contract
- Reviewed: True
- Evidence: Propagation: AGENTS.md/CLAUDE.md rules followed (findings v2 lifecycle binding, naming conventions, tools/ placement); generated context pack not modified; no compatibility mirrors created; hooks edited at canonical scripts/hooks location

## SECTION_2

- Label: §2 Truth taxonomy
- Reviewed: True
- Evidence: Truth taxonomy honored: byte-level od -c evidence for defect; 108/108 per-file diff-shape verification; runtime falsification test of hook gate (staged marker file via scratch index fired gate, exit 1); tests 271/271 frontend lib+contract, 3/3 loader

## SECTION_3

- Label: §3 Proportional rigor and evidence
- Reviewed: True
- Evidence: Proportional rigor for this docs-only diff (no code path in diff): P2 docs-integrity defect matched with full verification — byte-level od -c confirmation, 108/108 per-file diff-shape checks, 271/271 tests, falsification test of the new gate in scripts/hooks/pre-commit. No over-claim: leak was latent, loader slice(0,3) held.

## SECTION_4

- Label: §4 Authorization and side effects
- Reviewed: True
- Evidence: Authorization: user approved 'start with group a' for this exact scope; only named files staged (scripts/hooks/pre-commit, .github/workflows/ci.yml, Docs/review/FINDINGS_STORE.jsonl, FINDINGS_LIVE.md, Docs/travel_agency_process_issue_review_2026-09-10.md); pathspec commit excludes parallel agent's staged motto_review.md; no push, no branch ops.

## SECTION_5

- Label: §5 Canonical paths and ownership
- Reviewed: True
- Evidence: Canonical paths: findings via scripts/findings.py CLI only (FND-0256 open, FND-0257 note+close with evidence); tool in tools/ per reusability rule; hook edited at managed scripts/hooks/pre-commit; CI at .github/workflows/ci.yml docs-quality job

## SECTION_6

- Label: §6 Semantic salvage and supersession
- Reviewed: True
- Evidence: Semantic salvage applied to the 108 docs repaired via tools/strip_envelope_fragments.py: removed only defect bytes, restored intended content line in same operation (exact per-file shape verified: 1 line restored, 2 envelope lines removed). Nothing else deleted; change surface is additive tool + gates + docs.

## SECTION_7

- Label: §7 Capability routing
- Reviewed: True
- Evidence: Capability routing: council-orchestrator used per COUNCIL_AND_AUDIT_SOURCES.json manifest; persona repo resolved dynamically (Desktop/Understanding_Personas_sept6, rank-7 pointer); title-trap PER-99010 avoided; rg used for all content search per repo policy

## SECTION_8

- Label: §8 Skills lifecycle
- Reviewed: True
- Evidence: Skills lifecycle: only installed verified skills used; council-orchestrator SKILL.md read fully + helpers executed (resolve_persona_repo.py, load_persona_index.py); no remembered/invented skills; no new skill installs needed

## SECTION_9

- Label: §9 Exploration and durable knowledge
- Reviewed: True
- Evidence: Exploration durable: random-doc-audit findings stored in FINDINGS_STORE (FND-0256/0257) + Docs/travel_agency_process_issue_review_2026-09-10.md; detection/repair methodology (marker scan + strict-shape tail strip) documented for reuse in 4 sibling repos
