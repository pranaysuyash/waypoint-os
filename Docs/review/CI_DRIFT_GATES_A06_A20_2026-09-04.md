# CI Drift-Gate Reconciliation — A-06 / A-20 — 2026-09-04

## Decision

**A-06 (generated frontend types): ACCEPT+MODIFY — gate wired in CI.**
The backend-lint job now runs the canonical `scripts/generate_types.py` and
fails on a diff in `frontend/src/types/generated/spine-api.ts`. The check is
valid on a clean commit where the generated mirror is committed with its
source contract. In the current intentionally dirty checkout, comparing to
`HEAD` reports the already-present source/generated delta; that is custody
evidence, not a reason to weaken the gate.

**A-20 (Alembic model/schema drift): EXPLORE — gate not wired yet.** See the
full [A-20 reconciliation dossier](A20_ALEMBIC_MODEL_MIGRATION_DRIFT_RECONCILIATION_2026-09-04.md)
for the historical 53-operation classification, subsequent metadata repairs,
and recorded post-repair 37-operation residual. Those are dated local receipts,
not a newly executed database probe. The clean-baseline plan remains open.
The proposed CI `alembic check` was probed against the local PostgreSQL
database after `alembic upgrade head` and correctly failed with substantive
operations. The failure must be reconciled before the check becomes blocking.

## Observed Alembic delta

The post-upgrade probe reported, among other operations:

- removal of `agent_requeue_jobs`, `trip_routing_states`, and `audit_logs`
  tables and their indexes from the model view;
- nullability changes across booking, extraction, event, and agency columns;
- `memberships.specializations` changing from JSONB to JSON;
- replacement of extraction-attempt indexes;
- removal of `trips.destination` and two trip indexes.

These are not safe to auto-accept. Some may be intentional legacy ownership
boundaries, while others may be untracked schema drift. Generating a migration
or adding broad `include_object` exclusions without field-by-field ownership
would risk destructive data loss or conceal a real contract break.

## Required follow-up package

1. Inventory each reported table/index/column against the canonical SQL model,
   route consumers, and migration history.
2. Classify every delta as **retain**, **migrate additively**, or
   **retire-with-recovery-plan**; preserve legacy data until the owner approves
   a retirement date.
3. Add migration tests for every accepted change and a clean disposable
   PostgreSQL baseline.
4. Re-run `DATABASE_URL=... uv run alembic upgrade head` followed by
   `DATABASE_URL=... uv run alembic check` on that baseline.
5. Wire the check into CI only after the clean baseline returns zero upgrade
   operations and rollback/restore evidence is recorded.

## Evidence and boundary

- CI workflow contains the generated-type drift step under the existing
  backend-lint job.
- Local generation is deterministic and idempotent; two consecutive runs
  produced SHA-256 `a457a71b4cee25e8f33c1bc4dff26e352059d3658fca905dddcab99870a81917`.
  The current dirty tree prevents a `git diff --exit-code` assertion against
  `HEAD` from being a clean release receipt.
- Local Alembic probe: `upgrade head` completed, then `alembic check` exited
  non-zero with the operations summarized above.
- No schema was dropped, reset, or rewritten during this investigation.
- This record does not claim hosted migration, rollback, backup/restore, or
  production database evidence.
