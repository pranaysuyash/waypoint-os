# A1-1 Working-Tree Classification Closure

**Status:** closed for classification and preservation; not a product or Wave 0 release-baseline closure\
**Canonical path:** `Docs/review/A1_1_WORKTREE_CLASSIFICATION_CLOSURE_2026-09-01.md`\
**Owner:** repository review/control plane; future author attribution remains evidence-bound\
**Last materially reviewed:** 2026-09-01\
**Provenance:** live Git inspection, immutable commit tree, prior commit-gate command evidence, and machine-validated CSV inventories\
**Freshness trigger:** any change to the live worktree path set, any ownership handoff, or any proposal to stage/commit/discard the concurrent work\
**Related:** `FINDINGS_REGISTER_2026-08-31.md` A-14/A-21; `IMPLEMENTATION_PLAN_2026-08-31.md` Wave 0.4; `PER_0923_EVIDENCE_ARCHITECT_AUDIT_ADDENDUM_2026-08-31.md` Wave 0.1

Checklist applied: IMPLEMENTATION_AGENT_REVIEW_HANDOFF_CHECKLIST.md

## 1. Verdict

**A1-1 is closed as a preservation and classification control.** The earlier
dirty snapshot is recoverable as commit
`2f9a6384b42a90db415fbf012d94b60b5eaaa3bc` and every one of its 167 paths is
classified. The subsequent live checkout is classified separately because it
contains new concurrent work that is not part of that commit.

Closure means:

1. every path belongs to an explicit artifact class and semantic slice;
2. purpose, dependency, disposition, ownership truth, and verification state
   are durable and machine-checkable;
3. generated/runtime/evidence/product/test/documentation artifacts are not
   conflated;
4. unprovable author identity remains `unknown ... preserved` rather than being
   assigned by assumption;
5. no artifact was reset, restored, stashed, cleaned, deleted, staged, committed,
   or pushed during this closure pass.

Closure does **not** mean:

- the current concurrent implementation is correct or accepted;
- Wave 0's current baseline item 0.3 is green;
- historical test results are current release proof;
- a commit author is proven to be the author of every file in that commit;
- the new live work is authorized for staging, commit, push, or retirement.

## 2. Why the earlier assumption was invalid

`A1-1` was originally defined by the Evidence Architect audit and the Wave 0
plan as dirty-working-tree classification. Treating it as Wave 1.1 colloquial
extraction substituted a different numbering system without first resolving
the source label. The durable correction is to attach A1-1 to these canonical
owners:

- `PER_0923_EVIDENCE_ARCHITECT_AUDIT_ADDENDUM_2026-08-31.md` §10, Wave 0.1;
- `IMPLEMENTATION_PLAN_2026-08-31.md` Wave 0.4;
- findings A-14 and A-21 in the current register.

The prevention mechanism is the Git-backed ledger and validator, not another
chat-only interpretation.

## 3. Scope and snapshot identities

### 3.1 Historical preservation snapshot

| Field | Value | Truth status |
|---|---|---|
| Commit | `2f9a6384b42a90db415fbf012d94b60b5eaaa3bc` | Verified, Git object |
| Parent | `8ece02e73c13c6581023c5cad59b631b946bdbb9` | Verified, Git object |
| Commit date | `2026-09-01T14:35:16+05:30` | Observed, commit metadata |
| Subject | `feat(platform): harden trip operations` | Observed, commit metadata |
| File paths | 167 | Verified by validator, Tier 2 / S1 |
| Name/status SHA-256 | `2b4d7421fdebc110deba481ef220349edaf07aad9999cda07f9d4b3270c8d261` | Observed, deterministic Git inventory hash |
| Remote state after prior push | `origin/master == 2f9a638...` | Observed in the authorized commit/push pass; not re-pushed here |

Machine-readable inventory:
`assets/a1_1_commit_2f9a638_classification.csv`.

### 3.2 Live concurrent snapshot

The live ledger contains **77 paths** after adding this closure's
own documentation/tooling changes. Existing product/research changes are marked
`unknown_preserved_concurrent`; the A1-1 documentation, validator, and tracker
updates are marked `current_a1_1_closure_session`. The path set is checked at
handoff, so any newly added or removed concurrent path fails the closure gate.

Machine-readable inventory:
`assets/a1_1_live_worktree_2026-09-01_classification.csv`.

## 4. Ownership and custody policy

| Ownership value | Meaning | What it does not claim |
|---|---|---|
| `historical_shared_dirty_snapshot_origin_unknown_preserved` | File was present in the broad pre-commit snapshot and was preserved in `2f9a638`; exact author/session was not established | That the commit author authored the file |
| `current_commit_preparation_session_observed` | The change was made in the prior authorized commit-preparation pass and observed directly there | Broader ownership of the containing semantic slice |
| `mixed_prior_work_plus_commit_preparation_repair_observed` | Prior work was retained and a bounded gate repair was made during commit preparation | Sole authorship by either source |
| `generated_by_motto_attestation` | The managed attestation workflow generated/updated the record | Human authorship of generated content |
| `unknown_preserved_concurrent` | The path was already dirty when this closure pass began; it is preserved without attribution | Acceptance, correctness, or readiness |
| `unknown_runtime_mutation_preserved` | A tracked runtime/state artifact changed outside this pass | That it should be committed or ignored |
| `current_a1_1_closure_session` | This pass created or updated the classification documentation/tooling/tracker surface | Authorization to commit it |

This is intentionally a custody model, not an authorship fiction. Ownership can
be promoted only with evidence such as an explicit human/agent handoff, a
separate isolated commit, or trustworthy session metadata.

## 5. Artifact separation

The ledgers distinguish these classes rather than treating all dirty files as
one implementation:

- backend and frontend product code;
- test code, fixtures, evaluation snapshots, and route-contract snapshots;
- runtime state indexes;
- database migrations;
- verification and repository tooling;
- generated attestation records;
- screenshots and design evidence;
- research prototypes;
- architecture, research, exploration, persona, review, and project docs;
- repository configuration.

Notably, the prior pass excluded ignored Next.js backup trees and lock
directories as generated/runtime artifacts and retained
`tmp/rq01_prototype.py` because its exploration document identifies it as
reproducible evidence. Those preservation decisions are historical evidence;
this closure did not recreate, delete, or stage the ignored artifacts.

## 6. Historical semantic slices

| Slice | Purpose | Principal dependencies | Status/disposition | Verification attached |
|---|---|---|---|---|
| H01 | Governance, audit synthesis, and durable current-truth surfaces | Root control plane and canonical registers | Preserved in `2f9a638` | Commit tree and document presence observed |
| H02 | Incomplete-lead persistence and draft/trip linkage | Canonical draft/trip persistence, pipeline service | Preserved in `2f9a638` | Historical backend full-suite run; one shared-session ordering residual remained elsewhere |
| H03 | Intake extraction, action contract, epistemic slot truth, and validation | Canonical intake contract and fixtures | Preserved in `2f9a638` | Historical backend full-suite and focused repair evidence |
| H04 | Tenant isolation, RLS, team routing, and privacy posture | Authentication, tenant context, persistence | Preserved in `2f9a638` | Targeted privacy/tax repairs and historical backend suite observed |
| H05 | Agent-runtime resilience, journey graph, and border constraints | Runtime and journey contracts | Preserved in `2f9a638` | Historical backend suite observed |
| H06 | D6 evaluation, findings lifecycle, and verification infrastructure | Test/eval oracles | Preserved in `2f9a638` | D6 and findings gates observed; full backend residual retained |
| H07 | Frontend recall, blocking-copy truth, auth, and workbench UX | H02/H03 plus FE/BE contracts | Preserved in `2f9a638` | Typecheck and 1,245 Vitest tests observed; lint/build residuals retained |
| H08 | Design-lab capture, app DNA, prototypes, and screenshots | Frontend design-evidence tooling | Preserved as evidence in `2f9a638` | Presence only; no fresh visual/runtime re-verification |
| H09 | Persona, demo, GTM, and research corpus | Persona/research sources | Preserved as durable evidence in `2f9a638` | Path/content preservation only; not product proof |
| H10 | Frontier migration/router contract | Tenant/database schema and API routing | Preserved in `2f9a638` | Historical route-snapshot/backend-suite evidence |
| H11 | Runtime/eval/test fixture state | Intake and eval oracles | Preserved in `2f9a638` | Fixture inclusion and relevant suite evidence observed |
| H12 | Repository hygiene, generated review, overview/index routing | Repository control plane | Preserved in `2f9a638` | Managed hooks passed and remote SHA equality was observed in prior pass |

## 7. Live concurrent semantic slices

| Slice | Purpose/current evidence | Dependency | Ownership/status | Attached verification and next gate |
|---|---|---|---|---|
| L01 | A1-1 closure docs, registers, index, validator, and tool docs | Canonical review/control-plane docs | Current A1-1 session; uncommitted | Validator, CSV schema, `py_compile`, `git diff --check`, link/path checks |
| L02 | `data/drafts/index.json` changed draft references | Draft store/runtime writer | Unknown runtime mutation; preserved | Not product-verified here; determine writer and whether tracked state is intended before staging |
| L03 | Autonomous proposal compiler research, orchestration, router, panel, test | Intake facts, pricing/proposal contracts, server/router/UI integration | Unknown concurrent owner; preserved | Existing focused test is identified; no result promoted by this classification pass |
| L04 | IROPS auto-healer research, orchestration, router, panel, test | Journey/disruption graph, crisis/financial actions | Unknown concurrent owner; preserved | Focused test identified; integration/recovery evidence still required |
| L05 | Duty-of-care radar research, crisis state, orchestration, router, panel, test | Crisis/traveler state and threat evidence | Unknown concurrent owner; preserved | Focused test identified; provider/live-threat truth not established |
| L06 | Epistemic conflict/provenance research, arbiter, router, panel, test | Intake evidence contract | Unknown concurrent owner; preserved | Focused test identified; authority/provenance contract review still required |
| L07 | ICAO MRZ/voucher research, parser, router, panel, test | Document input and checksum/parser contract | Unknown concurrent owner; preserved | Focused test identified; no external-standard conformance claim made here |
| L08 | Financial settlement/VCC research, engine, router, panel, test | FX, payment, authority, and secrets boundaries | Unknown concurrent owner; preserved | Focused test identified; real-provider, security, and financial authorization gates remain |
| L09 | Group Pareto/ledger research, engine, router, panel, test | Group preferences and accounting contracts | Unknown concurrent owner; preserved | Focused test identified; fairness/product acceptance not established |
| L10 | Logistics and industry-expansion engines, router, queue update, tests | Corporate, visa, briefing, accounting, accessibility, route integration | Unknown concurrent owner; preserved | Focused suites identified; no full-suite or domain-authority proof in this pass |
| L11 | Shared `server.py`, Persona Council integration, extractor, and route/OpenAPI snapshots | All new routers/panels plus canonical API contract | Unknown concurrent owner; preserved | Highest blast-radius slice; full API snapshot, backend suite, frontend typecheck/tests required before acceptance |
| L12 | Research documents for the concurrent feature family | Corresponding L03-L10 implementations | Unknown concurrent owner; preserved | Documentation presence only; claims remain proposed/observed unless independently sourced |
| L13 | P1 hardening additions: public-proposal tokens, DLQ inspection/replay, perishable-deadline sentinel, and focused tests | Security authority, durable job state, audit log, time/deadline validation | Unknown concurrent owner; preserved | Static inspection found blockers below; security/correctness S2/S3 checks required before staging |

The live grouping is a dependency map, not an approval to merge the slices. In
particular, L11 is shared integration state and should be verified only after
the domain slices stabilize; otherwise a green snapshot can mask a moving
contract.

## 8. Historical command and gate evidence retained from chat

The prior authorized Git pass produced these observations. They are documented
to prevent chat-only loss but remain historical, not fresh current-runtime proof:

| Command/gate family | Observed outcome | Truth/evidence boundary |
|---|---|---|
| `.gitignore` review and `git add -A` | Next backup trees and lockdir runtime state excluded; retained research prototype included | Observed historical workspace/Git decision |
| Secret scan | Clean | Historical focused check, Tier 2 / S1 |
| Ruff | Passed full configured run | Historical focused check, Tier 2 / S1 |
| Mypy configured scope | Passed 10 source files | Historical focused check, Tier 2 / S1 |
| Frontend typecheck | Passed | Historical focused check, Tier 2 / S1 |
| Frontend Vitest | 165 files / 1,245 tests passed | Historical test run, Tier 2 / S1 |
| Frontend lint | Failed: 4 errors / 17 warnings | Residual explicitly retained; not green |
| Frontend build | Failed on existing `pdf.worker` / Terser `import.meta` incompatibility | Residual explicitly retained; not green |
| Backend canonical suite | 3,269 passed / 44 skipped / 1 failed | Residual: `test_extract_accepted_document`, SQLAlchemy refresh/shared-session ordering; not green |
| D6 snapshot validation | Passed | Historical focused check, Tier 2 / S1 |
| Findings lifecycle | 147 rows: 105 open, 36 closed, 6 deferred, 0 warnings | Historical register check, Tier 2 / S1 |
| Doctrine attestation + managed hooks | 19 sections passed; high-risk hook gate passed | Historical process check, Tier 2 / S1 |
| Commit/push | Commit `2f9a638`; `origin/master` equality observed | Historical Git/remote observation |

Two bounded repairs made during that pass are explicitly attributed in the
historical ledger: the tax-compliance test was moved back to the canonical
session fixture, and the privacy guard's known-fixture ordering was repaired
without suppressing raw email/phone checks. Those repairs do not assign
ownership of the surrounding broad work.

## 9. First-principles, long-term, and doctrine alignment

| Criterion | Assessment | Evidence |
|---|---|---|
| First-principles truth | **Aligned** | Inventory derives from Git objects/status, not memory; unknown authorship is explicit |
| Preservation | **Aligned** | No deletion/reset/stash/restore/clean; historical and live states remain separately recoverable |
| Canonicality | **Aligned** | One closure document owns interpretation; two CSVs are evidence layers; existing registers link back rather than duplicating the ledger |
| Long-term repeatability | **Aligned** | Generic validator supports any commit or live worktree and fails on path/state drift |
| Verification honesty | **Aligned** | Classification proof is separate from implementation correctness and release proof |
| Parallel-work safety | **Aligned** | Concurrent paths are preserved and not edited by this pass; shared integration slice is named explicitly |
| Documentation doctrine | **Aligned** | Metadata, provenance, freshness trigger, truth status, dependencies, residuals, and retrieval index are present |
| Remaining limitation | **Explicit** | Git does not prove per-file authorship of a dirty snapshot; live classification becomes stale when its path set changes |

## 10. Explicit and implicit findings/tasks produced by this closure

### Closed now

1. **A-14 / A1-1 preservation:** commit/push already completed under explicit
   authorization; 167 paths now have durable classification.
2. **A-21 artifact tracking:** the six named artifacts are tracked in
   `8ece02e`; no owner is invented where evidence is absent.
3. **Wave 0.4:** annotated worktree classification is machine-checkable and
   includes later concurrent drift.
4. **Documentation gap:** the earlier chat evidence and correction are now
   durable and indexed.

### Still open, but not part of A1-1 closure

1. **Wave 0.3 current baseline:** run the canonical backend, frontend,
   integration, lint, typecheck, build, migration, and eval profile after the
   concurrent feature family stabilizes. Owner: implementation/release gate.
2. **L02 runtime-state custody:** identify the writer and policy for tracked
   `data/drafts/index.json`; decide preserve-as-fixture, migrate, or generate.
   Do not stage it by default.
3. **L03-L10 feature review:** each concurrent domain slice needs its focused
   test plus contract/authority review. Financial, document-standard, and
   duty-of-care claims require specialist evidence beyond unit tests.
4. **L11 integration gate:** rerun route/OpenAPI snapshot generation, backend
   full suite, frontend typecheck/Vitest/lint/build, and inspect route ownership
   only after its imported slices stop moving.
5. **Independent ownership handoff:** an owner may explicitly claim a slice;
   until then, preserve `unknown_preserved_concurrent`.
6. **Known historical red lanes:** one backend full-suite failure, frontend lint,
   and frontend build remain separate tasks; this classification does not close
   them.
7. **Live P1-hardening blockers (Observed):** the concurrent
   `public_proposals.py` token format splits underscore-containing trip IDs
   ambiguously, defaults to a repository-known signing key, accepts a legacy
   unsigned compatibility path, and verifies only a small hard-coded agency
   list. `DLQInspector.replay_job()` marks a job successful without invoking a
   worker and keeps state in process memory. `PerishableSentinel` converts a
   malformed deadline into an immediate expiry instead of returning a validation
   error. These must be reviewed and corrected by the owning implementation
   slice; A1-1 preserves them but does not endorse them.

### Rejected shortcuts

- Inferring file authorship from commit author metadata.
- Calling current feature code verified because matching tests exist.
- Folding the new live work into the historical `2f9a638` snapshot.
- Staging or committing closure docs merely because A-14 had prior Git
  authorization; Git authorization is conversation- and action-specific.
- Marking all of Wave 0 green while item 0.3 remains stale.

## 11. Verification procedure and acceptance

```bash
python tools/check_worktree_classification.py \
  --commit 2f9a638 \
  --ledger Docs/review/assets/a1_1_commit_2f9a638_classification.csv

python tools/check_worktree_classification.py \
  --worktree \
  --ledger Docs/review/assets/a1_1_live_worktree_2026-09-01_classification.csv
```

Acceptance requires:

- both commands pass with no missing, extra, duplicate, blank, or
  `unclassified`/`TBD`/`TODO` field;
- a deliberately omitted ledger row makes the checker fail (S3 sensitivity);
- `python -m py_compile tools/check_worktree_classification.py` passes;
- `git diff --check` passes for A1-1-owned files;
- all durable links/paths resolve;
- findings-register validation remains green;
- a final `git status --short` re-read finds no path outside the live ledger.

## 12. Review completeness

### Reviewed

Git commit metadata/tree for `2f9a638`, current porcelain status, all classified
paths, relevant findings/plan rows, the Evidence Architect addendum, prior gate
outcomes, and current route/feature file headings/diffs sufficient to form
semantic slices.

### Not reviewed

The semantic correctness, product quality, external-standard conformance,
provider behavior, security posture, UI runtime, and release readiness of the
new concurrent feature family. Those are intentionally separate review and
verification tasks.

### Remaining uncertainties

Exact historical and current per-file human/agent authorship; whether the live
feature family is still actively changing; and whether the runtime draft index
belongs in a future commit.

### Evidence needed

Explicit owner handoff or isolated commit metadata for authorship; stable path
set plus focused/full gates for implementation acceptance; writer/config trace
for runtime index policy.

### Evidence tier achieved

Tier 2 for classification completeness (deterministic validator), with S3
sensitivity after the deliberate missing-row check. Product behavior remains
Tier 0-1 in this closure because it was not the claim under test.

### Known blind spots

Git status detects path/state coverage but not semantic overlap inside a shared
file. L11 therefore still needs a later line-level ownership and integration
review before implementation acceptance.
