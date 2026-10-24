# Audit implementation and evidence, 2026-10-23

Status: active implementation. Owner: Codex parent; bounded implementation lanes below.
Scope authority: the current user's explicit instruction to implement the preceding audit,
research unresolved branches, update the exploration map, preserve valuable existing work,
and verify regressions. This record is an implementation/evidence packet, not a second
findings register. Finding identity and lifecycle remain in `FINDINGS_STORE.jsonl` through
`scripts/findings.py`.

## Intended outcome and invariants

The agency and traveler must be able to follow one request through corrections,
commercial agreement, booking components, execution, and business reporting without
changing the meaning of its facts. The user receives a recoverable workflow; the
agency receives trustworthy prices, authority, and outcome measures; maintainers
receive canonical contracts and defect-sensitive evidence.

1. Current explicit customer corrections survive every reassessment, including blocked runs.
2. Customer retail is distinct from supplier/model cost. Currency and price basis are explicit.
3. Acceptance identifies immutable terms. Material changes cannot inherit old approval.
4. Unknown/disallowed lifecycle states cause zero external or mandate effects.
5. A retried booking operation consumes authorization once and retains recovery identity.
6. Required execution events and the state they describe commit or roll back together.
7. Separate real booking components coexist; retries of one component deduplicate.
8. Internal review, quality score, budget, booking value, collections, and agency earnings remain distinct.
9. Incorrect populated extraction values reduce quality metrics; citation overlap is not factual verification.
10. First-value progress follows canonical agency work, not navigation or browser-local checkmarks.
11. Generated readiness summaries identify the exact canonical revision they summarize.

## Preservation and authorization

Initial checkout has extensive dirty and untracked work in intake, privacy, RAG,
workbench, tests, and documentation. All is preserved and treated as current ground
truth. No staging, commit, push, fetch, checkout, reset, stash, deployment, provider
transaction, external contact, persistent developer-database reset, or broad cleanup
is authorized. No removal is planned; supersession and original intent must be
recorded before any later candidate is removed.

Operating Doctrine 8.2 canonical SHA-256:
`e14bab7b1964d8b755c9e6c7f5b1c2b44e1d726033fa23aeaee6ce921e271a75`.
Applicable specialist methods: Architecture 1.1, Testing 1.1, Review 1.3,
Research 1.0, Exploration 1.1, Documentation 1.1, and security/privacy/safety
at trust boundaries. Skills: council-orchestrator, systematic-debugging,
test-driven-development, verification-before-completion, agentic-eval-loop.

Agent Start was refreshed. Ollama retrieval was unavailable; direct live-file
inspection is used. The generator reported unsuccessful hook/guard installation;
no hook installation is required for this non-Git task and no retry is planned.

## Ownership and dependency graph

| Lane | Owns | Boundaries |
|---|---|---|
| Commercial/execution | Shared priced agreement, public acceptance, fulfillment classification and mandate replay | Proposal-related persistence only; no booking model/migration or analytics edits |
| Intake/evaluation | Reassessment continuity, extraction metrics, bounded grounding uncertainty | Shared server/public-ask edits coordinated with parent |
| Outcomes/activation | Commercial outcome projection and first-value onboarding | Analytics contracts and their real consumers; before/after visual evidence required |
| Parent | Booking task atomicity, booking component identity, research and maps, findings freshness, cross-lane integration and final review | Sole writer of shared evidence map and canonical finding CLI |

Commercial agreement precedes consumer updates. Schema migrations precede SQL
integration checks. Regression tests demonstrate the defect before implementation.
Independent lanes first inspect and prepare contracts while a full baseline runs.

## Verification environment and baseline

The persistent `waypoint_os` database is excluded from test mutation. A new,
task-owned PostgreSQL 17 cluster lives under `.run/audit_20261023/pgdata`, listens
only on `127.0.0.1:55439`, and contains `waypoint_audit_20261023`. It holds synthetic
test data only. Migrations from empty schema through the current head succeeded.
The initial sandbox denied shared-memory creation; the approved isolated initdb
and startup succeeded. Existing developer services and data were not stopped or reset.

The canonical backend runner is executing against that isolated database, with
provider credentials disabled. The frontend baseline uses the existing Vitest
runner with two workers. Logs:

- `Docs/validation/audit_2026-10-23/backend_baseline.log`
- `Docs/validation/audit_2026-10-23/frontend_baseline.log`

Results, regression sensitivity, contract reviews, runtime observations, and
remaining limitations will be appended as evidence arrives. A running process or
passing count is not closure.

## Research and owner-decision branches

Research must resolve existing supplier-offer storage/comparison ownership,
conversation-update semantics, bounded offline travel-pack alternatives, handoff
receipt needs, and real-operator outcome measurement. Use current primary sources
and existing project/global personas. Preserve synthetic persona studies, but
qualify commercial conclusions as hypotheses rather than customer evidence.

The parent will update `Docs/exploration/backlog.md`, the canonical product
opportunity registry, and the codebase flow map with evidence, dependencies,
falsifiers, dispositions, and concrete next actions. Genuine owner decisions go to
the existing `Docs/DECISIONS_PENDING.md`; ordinary engineering choices remain
implementation responsibilities. Human recruitment/consent and real adoption
receipts cannot be fabricated by an agent.

## Booking confirmation identity supersession, 2026-10-23

The original `bc_active_type_uniqueness` migration explicitly protects replay
repair after a crash between SQL evidence and the trip-blob marker. Preserve
that intent. Its `(trip_id, confirmation_type)` identity also prevents two
separate hotels or flight components on the same real itinerary.

| Dimension | Existing guard | Extended canonical guard |
| --- | --- | --- |
| Legacy caller identity | Trip + type | Same identity through default `component_key=primary` |
| Distinct booking component | Cannot coexist within type | Explicit stable opaque component key |
| Concurrent/replayed creation | One active row | One active row per agency/trip/type/component |
| Void/reissue | Historical void retained, slot reusable | Same, scoped to that component |
| Private supplier/PNR data | Encrypted | Preserved; opaque key never derived from PII |
| History | Preserved | Preserved; migration backfills `primary`, no row void/delete |
| Reversal | Drops old guard | Refuses downgrade while non-primary identities would be lost |

Call-site audit: CRUD routes, confirmation extraction, flight fulfillment repair,
insurance attach, UI API client and confirmation panel. Existing automated
writers keep `primary`; repair lookup must explicitly match it so it cannot
link an unrelated manually recorded component. Insurance attach retains its
existing single-policy contract; no arbitrary new insurance coverage policy is
introduced. The UI gives each new manual component a stable identity for that
form attempt, retained after failed requests. Identity is immutable after create.

The old index is superseded only in a new migration after the component column
and replacement unique index exist. Historical migration code remains intact.
SQLite regression checks precede implementation; real PostgreSQL migration and
API checks follow against the task-owned database. No developer database is used.

## Interrupted baseline and first regression evidence

The user interruption stopped the original runners before final receipts.
Backend progress reached 46% with one failure marker; frontend emitted no final
summary. These are incomplete baselines, never passes. No task-owned runner
survived resumption. Other unrelated agent runners are left intact.

Task atomicity RED: 9 failed / 1 passed using self-contained SQLite transactions
and the real execution-event emitter. The failures include wrong emitter keyword,
state committed before event failure, partial rejected updates, missing terminal
PATCH history, generation/reconciliation atomicity, and old-status corruption.
First GREEN: 42 passed (atomicity + existing pure task-service suite). This is
local defect-sensitive evidence, not hosted, tenant-RLS or customer proof.

Booking component RED: 9 failures prove the broad identity constraint and missing
component contract. The existing legacy-duplicate tests remain as regression guards.
