# A-20: Alembic model/migration drift reconciliation

**Date:** 2026-09-04\
**Scope:** Alembic revision graph, SQLAlchemy `Base.metadata`, the local
PostgreSQL schema, and the observed post-upgrade `alembic check` delta.\
**Disposition:** **EXPLORE — no schema mutation performed.**\
**Risk boundary:** read-only inspection and durable documentation only; no
`upgrade`, `downgrade`, generated migration, table/index drop, schema reset,
staging, commit, or push was performed in this lane.

## Executive finding

The local database is at the current working-tree Alembic head,
`add_idempotency_fencing_token`, but `alembic check` reports **53 upgrade
operations**.  The operations are not one defect:

1. Three migration-managed tables are absent from the Alembic target metadata
   because two ORM models are not imported by the model registry and one table
   is intentionally owned by raw SQL runtime code.
2. One index pair has a naming mismatch (`ix_dea_*` in the migration versus
   the model-derived `ix_document_extraction_attempts_*` names).
3. A JSON/JSONB type choice is contradictory, with the live database and
   runtime bootstrap using JSONB while the ORM model declares generic JSON.
4. Thirty nullability differences reflect model invariants that were not
   carried through to the existing table definitions.  Local null counts are
   zero, but that is not production evidence.
5. Two legacy trip indexes and the `trips.destination` column are present in
   the database but absent from the current ORM model.  The application still
   handles destination as packet/JSON data, so an automatic drop would be an
   unsafe semantic assumption.
6. The working-tree tail of the revision graph is untracked.  A clean checkout
   at `HEAD` therefore does not contain the files that explain the local
   database's current revision.

The correct first-principles response is to make ownership and desired
contracts explicit, then use small, reversible migrations and a disposable
PostgreSQL verification environment.  `alembic check` should become a blocking
CI gate only after those decisions are resolved and a clean baseline returns
zero operations.

## Ground-truth inventory

### Revision graph

The live working tree contains **32 revision files** and `alembic heads` reports
one head:

```text
add_idempotency_fencing_token (head)
```

The database's `alembic_version` is also
`add_idempotency_fencing_token`.  However, these three files are currently
untracked (`git status --short -- alembic/versions`):

| Revision file | Role | Current custody classification |
| --- | --- | --- |
| `alembic/versions/add_idempotency_keys_table.py` | Creates durable `idempotency_keys`; parent `add_frontier_tables` | **Retain / additive migration already in working tree; release-custody gate** |
| `alembic/versions/add_platform_role_to_users.py` | Adds `users.platform_role`; parent `add_idempotency_keys` | **Retain / additive migration already in working tree; release-custody gate** |
| `alembic/versions/add_idempotency_fencing_token.py` | Adds the fencing invariant to `idempotency_keys`; parent `add_platform_role_to_users` | **Retain / additive migration already in working tree; release-custody gate** |

The committed `HEAD` contains 29 revision files and its historical tail ends at
`add_audit_chain_hash`; this is why older records correctly described that
older head while the live dirty tree now resolves a newer head.  No claim that
the untracked tail is ready for release is made here; parent integration must
perform path ownership and migration review before any Git delivery.

### Target metadata and model registry

`alembic/env.py:24-49` loads `Base` from `spine_api.models` and uses
`Base.metadata` as the sole autogenerate target.  `spine_api/models/__init__.py`
imports tenant, frontier, trip, agent-work, and idempotency models, but does not
import:

* `spine_api.models.audit.AuditLog` (`spine_api/models/audit.py:62-115`), even
  though `spine_api/core/audit.py`, `spine_api/routers/audit.py`, and
  `spine_api/core/audit_bridge.py` import and use it; or
* `spine_api.models.routing.TripRoutingState`
  (`spine_api/models/routing.py:40-79`), even though
  `spine_api/services/routing_service.py` and the assignments router use it.

The registry omission explains the removed `audit_logs` and
`trip_routing_states` operations.  It is an ORM discovery defect, not evidence
that either live table should be dropped.

`agent_requeue_jobs` has no ORM class by design.  Its canonical runtime owner
is the raw SQL `RequeueJobStore.ensure_schema()` in
`spine_api/services/agent_requeue_jobs.py:48-89`; its equivalent Alembic
revision is `alembic/versions/add_agent_requeue_jobs.py:1-123`.  The migration
and runtime schema are deliberately belt-and-suspenders and the table is
system-scoped without `agency_id`, as documented in
`Docs/status/AGENT_REQUEUE_SCHEMA_OWNERSHIP_DECISION_2026-05-18.md:77-123`.
It should not be dropped just because no ORM class exists.

## Observed `alembic check` evidence

The check was run against the named local PostgreSQL database loaded from the
gitignored `.env` without printing credentials.  It exited non-zero with
`FAILED: New upgrade operations detected`.  The complete operation families
were:

### A. Three live tables and twelve indexes reported as removed

| Database object | Observed operations | Classification | Safe next action |
| --- | --- | --- | --- |
| `trip_routing_states` plus `ix_routing_agency_id`, `ix_routing_assignee`, `ix_routing_status`, `ix_routing_trip_id` | `remove_table` + four `remove_index` | **Retain; registry repair** | Import `TripRoutingState` into the target registry, compare its unique constraint/FKs/RLS against the migration, then rerun autogenerate. No drop migration. |
| `audit_logs` plus `ix_audit_logs_agency_action`, `ix_audit_logs_agency_created`, `ix_audit_logs_current_hash`, `ix_audit_logs_resource`, `ix_audit_logs_user_created` | `remove_table` + five `remove_index` | **Retain; registry repair** | Import `AuditLog` into the target registry; verify JSONB, chain columns, indexes, and the intentional RLS exemption. No drop migration. |
| `agent_requeue_jobs` plus `ix_agent_requeue_jobs_status`, `ix_agent_requeue_jobs_trip_id`, `uq_agent_requeue_jobs_idempotency` | `remove_table` + three `remove_index` | **Retain; intentional non-ORM infrastructure** | Add an explicit Alembic `include_object` exclusion with a reason, or introduce one canonical SQLAlchemy Core table definition after owner review. Add parity tests against `RequeueJobStore.ensure_schema()`. Do not model it speculatively or drop it. |

The local database contains all three tables.  The live data probe found three
tables present and no assumption was made about hosted databases.  The routing
migration (`alembic/versions/add_rls_tenant_isolation.py:56-129`) and the
Phase-5E repair migration (`alembic/versions/add_rls_phase5e_full_coverage.py:57-151`)
both establish routing state with tenant controls; deleting it would break
assignment/routing behavior and potentially remove protected data.

### B. Thirty nullability differences

Alembic reports `modify_nullable` from database nullable `TRUE` to model
nullable `FALSE` for:

| Table | Columns |
| --- | --- |
| `agencies` | `is_test` |
| `booking_collection_tokens` | `status`, `created_at` |
| `booking_confirmations` | `has_supplier`, `has_confirmation_number`, `notes_present`, `external_ref_present`, `created_at`, `updated_at` |
| `booking_documents` | `status`, `scan_status`, `review_notes_present`, `created_at`, `updated_at` |
| `booking_tasks` | `created_at`, `updated_at` |
| `document_extraction_attempts` | `field_count`, `confidence_method`, `created_at` |
| `document_extractions` | `field_count`, `status`, `extracted_by`, `provider_name`, `confidence_method`, `created_at`, `updated_at`, `attempt_count`, `run_count` |
| `execution_events` | `created_at` |
| `intelligence_pool` | `anonymized_data` |

The model-side intent is visible in `spine_api/models/tenant.py:40-75,
198-232,235-292,367-430,471-575,627-735` and
`spine_api/models/frontier.py:113-147`; several `Mapped[T]` fields infer
non-nullability even when the migration originally supplied only a server
default.  The creation migrations show why drift accumulated: for example,
`add_document_extractions.py:27-47`, `add_extraction_attempts_and_pdf.py:47-99`,
`add_booking_documents.py:27-62`, `add_booking_tasks.py:29-57`, and
`add_booking_confirmations.py:29-86` set defaults but leave several columns
implicitly nullable.

The local database probe is useful but bounded: `agencies.is_test` has 835 rows
and zero NULLs; every other listed table currently has zero rows or zero NULLs
in the listed columns.  This does **not** prove production safety or justify an
immediate constraint migration.

**Classification:** **Additive migration, subject to preflight.** For each
column, the owner must confirm the invariant and an unambiguous backfill. A
safe migration sequence is:

1. inspect row counts and NULL counts in every deployment;
2. add/confirm database server defaults where direct SQL writers require them;
3. backfill only with a documented semantic default (for example boolean
   indicators or counters); abort on unknown timestamp or privacy-sensitive
   values rather than inventing data;
4. add `NOT NULL` in small table-scoped revisions with lock/time budgets; and
5. verify rollback/restore and application writes before enabling the CI gate.

`intelligence_pool.anonymized_data` is privacy-sensitive.  A blank JSON object
must not be invented without confirming that it is a valid sanitized record;
this field needs explicit owner approval or an abort-on-NULL migration policy.

### C. Extraction-attempt index naming drift

The database has `ix_dea_agency_id` and `ix_dea_trip_id`, created by
`add_rls_phase5e_full_coverage.py:195-201`.  The current model derives
`ix_document_extraction_attempts_agency_id` and
`ix_document_extraction_attempts_trip_id` from `index=True` on
`spine_api/models/tenant.py:375-386`.  Alembic therefore reports two removes
and two adds even though each pair indexes the same single column.

**Classification:** **Retain one index per column; rename migration.** Choose
the canonical names after checking query plans and naming policy, then issue a
metadata-aware `ALTER INDEX ... RENAME TO ...` revision (or preserve the old
names in the model).  Do not create duplicate indexes and do not drop the old
index before the equivalent replacement is confirmed.  Add an idempotent
reflection test that accepts both a pre-rename and post-rename database during
deployment rollout.

### D. `memberships.specializations` JSONB versus JSON

Alembic reports `modify_type` from PostgreSQL `JSONB` to generic SQLAlchemy
`JSON`.  The live database is `JSONB`; `spine_api/server.py:868` also bootstraps
the column as `JSONB DEFAULT '[]'::jsonb`; and the membership service treats it
as a list of specialization values (`spine_api/services/membership_service.py:43-56,180-191`).
The ORM currently declares generic `JSON` at
`spine_api/models/tenant.py:114`, while other models use a deliberate
`JSON().with_variant(JSONB(), "postgresql")` pattern
(`spine_api/models/idempotency.py:47-53`).

**Classification:** **Retain JSONB; model-only canonicalization.** The likely
first-principles contract is JSONB on PostgreSQL and JSON on SQLite/tests. Use
the existing variant pattern in the model, then verify that no migration is
generated and that list round-trips preserve ordering/content. A cast to JSON
would be a semantic/performance change and is not justified by the current
evidence.

### E. Trip indexes and `trips.destination`

The database still has `ix_trips_user_id` and `ix_trips_assigned_to_id`, while
the current `Trip.__table_args__` at `spine_api/models/trips.py:79-83` declares
only agency/status/created indexes.  `assigned_to_id` remains a model field
(`spine_api/models/trips.py:34-37`) and is used by inbox assignment and SQL
summary reads (`spine_api/routers/inbox.py:97-105`,
`spine_api/persistence.py:832-873,1070-1082,1138-1150`).  There is no current
SQL filter-by-user evidence sufficient to prove that `ix_trips_user_id` is
needed, but there is also no query-plan evidence that it is safe to remove.

**Classification:**

* `ix_trips_assigned_to_id`: **Retain candidate / registry alignment.** Keep
  until assignment-filter query plans prove otherwise, and declare it in the
  model if it is part of the intended operational contract.
* `ix_trips_user_id`: **Unknown; defer retirement.** Inventory SQL/API clients
  and run `EXPLAIN` on real list/search queries before either retaining it in
  metadata or retiring it. A migration-generated drop is not justified by
  absence of a current `where` clause alone.

The database also has a nullable `trips.destination` column from
`alembic/versions/0cd0399e2c3c_add_assigned_to_id_and_is_test.py:56-59`, but the
current `Trip` model does not declare it.  The canonical SQL persistence path
keeps unknown top-level fields in `analytics._extra`
(`spine_api/persistence.py:928-960`) and rehydrates those extras in
`spine_api/persistence.py:832-860`; current route/UI code still uses
destination packet data extensively.  The local DB has zero rows with a
non-NULL destination, but hosted data is unknown.

**Classification:** **Retire candidate with recovery plan, currently unknown.**
Before any drop: inventory production values and direct SQL consumers, snapshot
the column, prove packet/`analytics._extra` round-trip compatibility, publish a
deprecation window, and retain a reversible recovery path. If any external
consumer still depends on the relational column, instead restore it to the
canonical model and add a documented migration.

## Reconciliation decision matrix

| Drift family | Disposition now | Why | Required evidence before implementation |
| --- | --- | --- | --- |
| Audit/routing tables absent from target metadata | **Retain + additive registry repair** | Live ORM classes and callers exist; dropping tables would be destructive | Import-only metadata test; autogenerate zero for these objects; RLS/FK/index parity |
| Raw requeue table absent from target metadata | **Retain + intentional exclusion or Core owner** | Raw SQL is explicitly canonical today; no speculative duplicate ORM model | Exclusion test or Core parity test; runtime/migration schema comparison |
| Listed nullability changes | **Additive migration, grouped by invariant** | Model contracts are stricter, but production NULLs and semantic defaults are not proven | Per-column preflight, backfill proof, lock budget, rollback/restore, write-path regression |
| Extraction-attempt index names | **Rename one-for-one** | Same indexed columns; duplicate indexes add cost without value | Query-plan check and idempotent rename migration |
| `memberships.specializations` | **Retain JSONB; model variant** | Runtime bootstrap and live DB agree on JSONB; generic JSON is drift | Cross-dialect model test, round-trip test, zero autogen delta |
| `trips.destination` | **Unknown / retire only with recovery** | Current model/persistence moved data to packet/extra representation, but hosted direct consumers unknown | Production inventory, snapshot, dual-read/compatibility proof, owner retirement approval |
| `trips.user_id` / `assigned_to_id` indexes | **Retain/defer** | Usage and performance evidence is incomplete | Query inventory, `EXPLAIN`, migration rollback plan |
| Three untracked tail revisions | **Retain + custody/release gate** | DB is stamped at a revision not present in `HEAD` | Integrate only after ownership review, clean checkout upgrade, downgrade/restore test |

## Long-term implementation plan

### Phase 0 — custody and baseline

1. Preserve the three untracked migrations and classify their owners; do not
   stage or delete them as generated junk.
2. Build a disposable PostgreSQL database from a clean checkout containing the
   exact intended revision set.  Run `alembic upgrade head`, record the revision
   and schema fingerprint, and verify the application boot path.
3. Run `alembic check` against that fresh baseline before any reconciliation;
   save the raw operation list as an artifact.

### Phase 1 — target metadata ownership

1. Import `AuditLog` and `TripRoutingState` into the canonical registry; do not
   change their table definitions in the same patch.
2. Choose the requeue strategy: explicit `include_object` exclusion with a
   rationale, or one canonical SQLAlchemy Core table definition shared by
   runtime and Alembic.  The first is the smaller safe slice; the second is the
   long-term duplicate-definition reduction.
3. Add a test that fails if a migration-managed live table is omitted from the
   target metadata without an explicit documented exemption.

### Phase 2 — non-destructive schema alignment

1. Canonicalize `specializations` to the existing JSONB-on-PostgreSQL variant.
2. Resolve extraction index naming by rename, not drop-and-recreate.
3. Add table-scoped nullability migrations only after per-column preflight and
   semantic backfill decisions. Keep the migration aborting on unknown NULLs.
4. Resolve trip indexes from query-plan evidence; do not let autogenerate make
   the product decision.

### Phase 3 — legacy column decision

1. Inventory `trips.destination` values and direct SQL/API consumers in every
   environment.
2. If retained, add it to the canonical model and document its relation to
   packet destination fields. If retired, dual-read/verify the replacement,
   snapshot data, announce the deprecation, and execute a reversible drop in a
   separately approved migration.

### Phase 4 — gate and release proof

1. Run upgrade, application tests, schema fingerprint, RLS tests, and rollback
   verification on disposable PostgreSQL.
2. Confirm a fresh `alembic check` returns zero operations with no broad
   `include_object` masking except documented infrastructure ownership.
3. Only then wire `DATABASE_URL=... alembic check` as a blocking CI gate. CI must
   fail on real model drift while remaining deterministic and must not use a
   developer database or secrets from `.env`.
4. Record production migration window, backup/restore proof, lock budget,
   observability, and a rollback owner before applying to a hosted database.

## Verification performed in this lane

* `alembic heads` — one live working-tree head:
  `add_idempotency_fencing_token`.
* `alembic branches` — no branch heads reported.
* `alembic check` against the named local PostgreSQL database — non-zero with
  the operation families documented above; no schema mutation was requested or
  performed by the check.
* Read-only SQLAlchemy reflection — database contains all migration-managed
  tables including `audit_logs`, `trip_routing_states`, and
  `agent_requeue_jobs`; `alembic_version` is
  `add_idempotency_fencing_token`.
* Read-only NULL inventory — `agencies.is_test` has 835 rows and zero NULLs;
  all other listed columns have zero NULLs in the current local database (most
  listed tables currently have zero rows).
* `Base.metadata` inventory — 20 target tables; the registry omission of
  `AuditLog` and `TripRoutingState` and intentional raw requeue ownership were
  verified against import/call sites.
* No `alembic upgrade`, `alembic downgrade`, generated revision, schema reset,
  destructive SQL, Git staging, commit, push, reset, checkout, stash, or clean
  operation was performed.

Evidence is local static/reflection and database-inspection evidence (T1/S1–S2).
It is not hosted production, backup/restore, migration rollback, multi-region,
or real-user evidence.

## Open decisions and residual risks

* The owner must ratify whether `AuditLog` and `TripRoutingState` are canonical
  ORM-managed tables (evidence strongly says yes) and whether raw requeue
  infrastructure remains intentionally outside ORM metadata.
* The owner must approve nullability tightening per field; no migration should
  invent timestamps or privacy-sensitive JSON values.
* The owner must decide whether `specializations` JSONB is the durable
  PostgreSQL contract (the current runtime/database evidence says yes).
* The owner must decide the retirement/retention of `trips.destination` and the
  two legacy trip indexes after hosted consumer and query-plan evidence.
* The three untracked migration files are a release-custody risk: a database
  stamped at their head cannot be understood by a clean checkout that lacks
  them. This must be resolved in the parent integration/delivery lane.

Until those decisions and the clean-baseline verification are complete,
`alembic check` should remain an exploratory/non-blocking probe as already
recorded in `Docs/review/CI_DRIFT_GATES_A06_A20_2026-09-04.md`. Suppressing the
delta with broad exclusions or committing an autogenerated destructive
migration would conceal the very contract drift this finding is meant to make
visible.

## Follow-up implementation receipt — 2026-09-04

The safe metadata-visibility slice described above is now applied:

* `spine_api/models/__init__.py` registers `AuditLog` and `TripRoutingState`.
* `TripRoutingState` declares the existing `CASCADE` agency and `SET NULL`
  user foreign-key actions.
* `Membership.specializations` uses JSONB on PostgreSQL and JSON on SQLite,
  matching the list-shaped API/runtime contract.
* `alembic/env.py` excludes only the reflected `agent_requeue_jobs` table,
  whose canonical owner remains raw SQL plus its dedicated migration.
* `tests/test_alembic_metadata_contract.py` proves registration, FK actions,
  dialect variants, and the narrow exemption (**34 focused ORM/audit/team
  tests passed**).

A read-only probe against the existing local PostgreSQL database now reports
**37 remaining operations** (down from the pre-slice 53-operation observation):
nullability differences, extraction-index naming differences, legacy trip
indexes, and the `trips.destination` removal. The probe still exits non-zero;
these operations remain visible and individually classified. No migration was
generated, no schema was changed, and the A-20 CI gate remains deferred until
an owned clean revision set and disposable upgrade/rollback/restore baseline
produce zero unexplained operations.
