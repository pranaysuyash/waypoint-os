# Findings Lifecycle — State Machine & Enforcement (2026-08-30)

## Current contract amendment — 2026-09-05

This section supersedes the parser, freshness, count, and canonicality rules
below. The original design and receipts remain historical evidence. Canonical
lifecycle ownership is `FINDINGS_REGISTER_2026-08-31.md`;
`FINDINGS_TASKS_CONSOLIDATED_2026-08-30.md` is a historical planning companion.

### Source-qualified identity and reviewed collision map

Identity is `(source, local ID)`, not the bare ID string. A historical `F-03`
cannot inherit the canonical `F-03` status merely because its label matches.
Current handoffs must name the source or use the following qualified notation:

- `canonical::ID` refers to [the sole lifecycle register](FINDINGS_REGISTER_2026-08-31.md).
- `inventory-2026-09-02::ID` refers to [the historical master inventory](../exploration/MASTER_FINDINGS_TASKS_INVENTORY_2026-09-02.md).

These are logical locators, not Markdown URL fragments. The dated source key
does not imply that every sentence in its living document is frozen. Historical
receipts retain their own dates. When a file is relocated, preserve its source
key and provide a relocation pointer rather than silently recycling identities.

Reviewed on 2026-09-05 against the actual row descriptions, not matching IDs.
This map owns identity relationships only; it contains no competing statuses.
`same issue` permits reading the canonical lifecycle for that issue. `subtask`,
`related`, `split`, and `unmapped` do not permit automatic closure inheritance.
They require checking the residual acceptance criteria separately.

| Historical reference | Relationship | Canonical reference(s) | Scope and residual boundary |
|---|---|---|---|
| inventory-2026-09-02::F-01 | same issue | canonical::GM-03 | Stripe webhook verifier that returned true; not canonical F-01 price-lock CAS. |
| inventory-2026-09-02::F-02 | same issue | canonical::GM-04 | Proposal capability-token hardening bundle; PT-01 through PT-06 preserve individual defect evidence. Not canonical F-02's entire public-proposal data/lifecycle surface. |
| inventory-2026-09-02::F-03 | subtask | canonical::REC-1, canonical::GM-01 | UI simulator-copy corrections and per-scenario evidence labeling; not canonical F-03 actor/signoff integrity. Labeling alone does not complete provider integration. |
| inventory-2026-09-02::F-04 | related | canonical::GM-01, canonical::EV-04 | Historical request to split hardening/simulation commits. Current user explicitly authorized all-path A1-1 delivery; retain this decision history, not a new split-commit veto. Not canonical F-04 payment mandates. |
| inventory-2026-09-02::F-05 | related | canonical::PT-08, canonical::EV-11 | Container/deployment review includes worker/idempotency and deployment gates, but is not exhausted by either target. Not canonical F-05 retention enforcement. X-12 remains a source-qualified inventory implementation item. |
| inventory-2026-09-02::R-01 | subtask | canonical::REC-1 | Chronicle/case-study simulator caveats; not canonical R-01 doctrine mirrors. |
| inventory-2026-09-02::R-02 | subtask | canonical::G-13 | Business-model memory correction and false-baseline caveats; any external memory write still requires its named scope. Not canonical R-02 router tenant binding. |
| inventory-2026-09-02::R-03 | subtask | canonical::G-04, canonical::A-02 | Correct RAG documentation claims; does not implement semantic retrieval or calibrate grounding. Not canonical R-03 file-store posture. |
| inventory-2026-09-02::R-04 | same issue | canonical::G-14 | Seasonal-campaign documentation gap; not canonical R-04 commission fabrication. |
| inventory-2026-09-02::R-05 | related | canonical::R-11, canonical::F-10 | Runtime architecture documentation is useful but distinct from lease/heartbeat/version behavior. Keep this documentation task visible; no exact canonical alias is established. Not canonical R-05 dispatch truth. |
| inventory-2026-09-02::R-06 | same issue | canonical::G-15 | ADR numbering/backlog identity reconciliation; not canonical R-06 epistemic types. Completion still requires preserving and migrating historical references. |
| inventory-2026-09-02::R-07 | subtask | canonical::G-17 | Persona adoption/documentation; not canonical R-07 evaluation gate integrity. |
| inventory-2026-09-02::R-08 | split | canonical::A-07, canonical::A-10 | Document indexing and shared idea-pad freshness have different owners, scope and closure evidence. Not canonical R-08 test-suite posture. |
| inventory-2026-09-02::R-09 | unmapped | none | Signup/email-verification/product wording decision has no exact alias established in the current canonical register. Do not map it to canonical R-09, which concerns duplicate documentation trees. |
| inventory-2026-09-02::R-10 | related | canonical::G-13 | Product business-model decision informs correction of stale records but remains a decision task. Not canonical R-10 server/audit architecture. |

This resolves the meaning of all 15 F/R-label collisions between these two
sources, not all repository aliases or lifecycle disagreements. EV-02 remains
partial until other sources are inventoried, unresolved tasks have canonical
identities, active references are migrated, and mechanical alias coverage is
enforced. EV-03 separately owns status/evidence reconciliation. Do not convert
this identity map into a claim that the referenced product work is complete.

First-principles decision: preserve the underlying user outcome and acceptance
criteria across documents. Renumbering alone, global search/replace of bare IDs,
or assuming every related item is a duplicate would lose real work. The
long-term implementation is a validated source-qualified alias graph feeding
derived audience views, with one canonical lifecycle owner and explicit
unmapped/split states. No second editable status store is introduced here.

### Lifecycle parser and verification contract

- Canonical tables require `Status` or `Live status`. Its leading state alone
  controls lifecycle; evidence prose cannot close a row. Partial/open/watch
  remain open; deferred/conditional/no-go-for-now remain deferred. Unknown or
  missing states count conservatively as open and fail validation.
- The exact state header may carry `(YYYY-MM-DD)`; `Status explanation` is
  not a state column. Duplicate state columns fail rather than selecting one.
- Bold/backtick IDs normalize to one identity. Duplicate IDs remain errors
  with actual line numbers. Escaped pipes do not shift table columns.
- The supported format is a leading-pipe table with an `ID` header and a
  complete separator row. Every body row is validated, including empty,
  malformed, `-`, or `ID` identities. Blank lines/prose/fences/indented blocks
  end tables; unrelated tables do not inherit finding-column ownership.
- Metadata must be an explicit own-line `**Role:**`/`**Date:**` before the
  first table or level-two heading. Duplicate metadata fails. Fenced,
  indented, quoted, and HTML-comment text cannot supply authority; visible
  text surrounding inline HTML comments is preserved.
- Counts and freshness apply only to canonical rows. Historical companions
  retain duplicate checks and provenance but do not inflate current totals.
- `Last verified`, when present, requires exactly one valid ISO date and owns
  freshness; blank/invalid/ambiguous explicit dates cannot fall back. Otherwise
  use an explicit `last verified YYYY-MM-DD` status segment, or a date directly
  following the leading state (optional `locally` modifier), then document date.
  Finding/evidence/planning-prose dates cannot renew verification;
  a newer document date cannot replace an older explicit verification date.
- A parsed closure is not independent product verification. Alias coverage,
  imported findings, and stale closure evidence require semantic review.

Implementation: `scripts/check_findings_register.py`; regression tests:
`tests/evals/test_findings_register.py`. Before the fix eight checks failed and
two passed; after it ten passed (Tier 2 / S2 for reproduced defects). The repo
gate then failed on seven previously skipped `NEW-*` rows with missing status.
Those rows now have explicit dispositions, preserving original descriptions.

Defensive cycle: empty canonical files, unknown roles, fenced examples,
invalid/future dates, and composite canonical IDs then produced six failures
with ten passing checks. After correction all sixteen pass. A process-local
mutation replacing `_row_status` with an always-closed function produced one
expected failure (15 deselected); the unmutated suite then passed again.
The lifecycle-state invariant therefore has Tier 2 / S3 evidence. No source
file was modified for the mutation; the altered function existed only in that
Python process. Dates in test fixtures are frozen to 2026-09-05 so the suite
does not become stale merely because calendar time advances.

Independent-review cycles then reproduced sixteen additional failures with
sixteen passes (ID omission, hidden metadata, status-header ambiguity, explicit
date fallback); the fix reached 32 passes. Table framing, incidental planning
dates, and hidden comments produced six failures/32 passes, then 38 passes.
The initial whole-line comment filter itself dropped visible inline-comment
rows: two new regressions failed/38 passed. Preserving visible comment-adjacent
text corrected it. **Latest focused receipt: 40 passed in 1.22s, exit 0.**
The review loop's intermediate failures are retained, not presented as prior
completion. A-18's original date was separated from historical explanation;
this syntax correction does not claim new verification of the underlying fix.

Current canonical CLI after reporter EV-06/07 local closure: **145 rows,
91 open, 53 closed, 1 deferred, 0 warnings**. This is a dated mechanical count,
not a deduplicated semantic task inventory. Historical-only invocation remains
supported and returns zero canonical rows. No date remains warning-only;
unsupported Markdown variants and semantic closure sufficiency remain review
obligations, not guarantees of this constrained parser.

Mutation reproduction (expected exit 1):

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -c 'import scripts.check_findings_register as gate; import pytest; gate._row_status = lambda value: "closed"; raise SystemExit(pytest.main(["--noconftest", "-q", "-p", "no:cacheprovider", "tests/evals/test_findings_register.py", "-k", "closed_words_do_not_hide"]))'
```

The existing stdlib reader is retained for the constrained register format.
`markdown-it-py`/`mistune` were found in the lockfile; a generic Markdown
dependency does not resolve lifecycle authority and is unnecessary for this
explicit table contract.

Helper consolidation: `_doc_date` and `_doc_role` are superseded by the single
`_parse_document` representation. Role descriptions/default-canonical behavior,
document dates, row identity/state, duplicate/freshness checks, and the public
`parse_register(path) -> (rows, date)` interface are preserved with stricter
validation. Repository caller search found no external callers of the two
private helpers; CI uses the CLI and tests use `check`/`parse_register`. Their
unsafe independent raw-text scans were replaced, not kept as a second authority.

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest --noconftest -q -p no:cacheprovider tests/evals/test_findings_register.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/check_findings_register.py Docs/review/FINDINGS_REGISTER_2026-08-31.md Docs/review/FINDINGS_TASKS_CONSOLIDATED_2026-08-30.md
```

The pure-tool suite omits application conftest because it initializes unrelated
application/database state. Backend CI still collects this file normally.
These checks do not claim application, provider, or release verification.

---

**Resolves:** EX-06 (Exploration & Research Backlog 2026-08-29) · informs doctrine amendment D-02 (Pranay's decision pending)
**Problem:** ~25 audits in 5 months produced findings with no lifecycle — no status, no owner, no re-verification date. Findings could only be re-discovered, never closed, and completion claims went unchecked (A-21: this audit nearly duplicated six in-flight artifacts because none of them were tracked as *findings with state*).

---

## 1. The state machine

Every finding row (ID-bearing row in a register table) is in exactly one of four states:

```text
            ┌────────────┐   fix verified    ┌────────────┐
            │    OPEN    │ ────────────────▶ │   CLOSED   │
            │            │                   │ (fixed)    │
            └─────┬──────┘                   └────────────┘
                  │ wontfix / superseded / recorded-no-go
                  ▼
            ┌────────────┐        new evidence may
            │  DEFERRED  │ ───── reopen as OPEN ────▶ (back to OPEN)
            └────────────┘
```

| State | Meaning | Row markers the checker recognizes |
|---|---|---|
| **open** | actionable, awaiting work | (no marker — default) |
| **closed** | fix verified with evidence, or wontfix/superseded/no-go with recorded reason | `RESOLVED`, `FIXED`, `closed`, `wontfix`, `superseded`, `no-go`, `rejected` |
| **deferred** | deliberately parked with a reason (design exists elsewhere, conditional, recorded no-go-for-now) | `deferred`, `conditional`, `trap`, `no-go-for-now` |

Rules:

1. **One row per finding ID.** Two tasks from one finding merge into one row (wave refs disambiguate).
2. **A closing transition requires evidence in the row**: the verification command/output doc or a dated resolution link. No bare "done".
3. **A no-go is a record, not a silence** (doctrine §9): rejected directions keep their row with the reason, marked no-go/deferred — they are never deleted and never silently re-proposed.
4. **Open rows carry a verification date** — either an in-row `YYYY-MM-DD` or the register's `**Date:**` header. In-row dates only *raise* freshness (e.g. `RESOLVED 2026-08-30`), never lower it (rows cite other docs' older dates as references).

## 2. Enforcement (mechanical)

`scripts/check_findings_register.py` (stdlib-only, CI-ready):

```bash
python3 scripts/check_findings_register.py Docs/review/FINDINGS_TASKS_CONSOLIDATED_2026-08-30.md
python3 scripts/check_findings_register.py --max-age 30 <register1.md> <register2.md>
```

- **Errors (exit 1):** duplicate ID rows · open findings stale beyond `--max-age` (default 45 days).
- **Warnings:** open rows with no verifiable date at all.
- **Verified:** both existing registers pass (consolidated: 51 rows — 45 open / 6 closed; FINDINGS_REGISTER_2026-08-29: 16 rows — 9 open / 7 closed). Failure modes exercised with a synthetic stale+duplicate fixture.

**CI wiring (one line, deferred):** add to the `docs-quality` or a new job in `.github/workflows/ci.yml`:

```yaml
      - name: Findings lifecycle gate
        run: python3 scripts/check_findings_register.py Docs/review/FINDINGS_TASKS_CONSOLIDATED_2026-08-30.md
```

Deferred because `.github/workflows/ci.yml` carries the A-14 agent's uncommitted changes; wire it in the next CI touch.

## 3. Register canon

- **Canonical register:** `Docs/review/FINDINGS_TASKS_CONSOLIDATED_2026-08-30.md` (it subsumes R-, A-, F-, EX-, RQ-, D- IDs). The 2026-08-29 register remains as historical evidence and still validates.
- New findings enter the canonical register with an ID, a task line, and today's date — the register **is** the verification event.
- Audit-specific registers may still be written (evidence artifacts), but their findings must be carried into the canonical register in the same change, or they will go stale and the gate will say so.

## 4. Doctrine amendment candidate (D-02 — for Pranay)

Per doctrine §16.9, recurring gaps become explicit amendments. Proposed text for the Review Doctrine:

> **Finding lifecycle.** Every review finding is recorded in the canonical register with an ID, state (`open | closed | deferred`), and verification date. Closing requires cited evidence; no-go requires a recorded reason; open findings are re-verified on a cadence enforced by `scripts/check_findings_register.py` in CI. Completion claims must cite the verification command and its date (see also D-05).

Companion amendments D-01 (absence claims need executed evidence) and D-05 (completion-claim standard) remain open for Pranay's decision; this tooling implements D-01/D-05 mechanically for findings rows regardless.

## Checklist applied: IMPLEMENTATION_AGENT_REVIEW_HANDOFF_CHECKLIST.md
