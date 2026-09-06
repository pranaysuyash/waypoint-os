# E2: `trips.analytics` JSON → JSONB Migration Exploration

**Date:** 2026-09-02 (researched and verified 2026-09-04)
**Type:** EXPLORE — research and design only. No code changed. Read-only DB access (SELECT counts / size probes only).
**Trigger:** An in-SQL analytics merge attempt failed with `COALESCE could not convert type jsonb to json` — `trips.analytics` is `json`, not `jsonb`, so the `||` merge operator is unusable in SQL today. Raw-SQL analytics merging is currently done in Python (`SQLTripStore._prepare_raw_update`, `spine_api/persistence.py:1268`).

---

## 1. Question

Should `trips.analytics` be migrated from PostgreSQL `json` to `jsonb`, what does it unlock, what does it cost, and what is the exact, reversible migration design?

---

## 2. Current state (evidence)

### 2.1 Column type — VERIFIED

- `spine_api/models/trips.py:70`:

  ```python
  analytics: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
  ```

- Created as plain `json` in the table's birth migration, never altered since:
  - `alembic/versions/create_trips_table_v1.py:47` → `sa.Column('analytics', sa.JSON(), nullable=True)`

### 2.2 Migration chain — VERIFIED (single linear chain, one head)

`analytics` was born with the table in `create_trips_table_v1` and has **no later migration touching it**. Full chain (verified by reading `revision`/`down_revision` in every file under `alembic/versions/`):

```text
eb7a5eede594 (init_tenant_schema)
 → 10a6e1336ba4 (add_password_reset_tokens_table)
 → a1b2c3d4e5f6 (add_capacity_specializations_status_to_memberships)
 → create_trips_table_v1            ← analytics created here as sa.JSON()
 → add_follow_up_due_date
 → add_frontier_result_and_fees
 → add_audit_logs
 → add_jurisdiction_to_agencies
 → add_stage_to_trips
 → add_priorities_flex
 → add_booking_data
 → add_booking_collection
 → add_agent_work_leases
 → f1a2b3c4d5e6 (add_rls_tenant_isolation)
 → add_booking_documents
 → add_document_extractions
 → add_extraction_provider_metadata
 → add_extraction_attempts
 → add_booking_tasks
 → add_booking_confirmations
 → add_destination_to_trips
 → add_rls_phase5e_full_coverage
 → add_collection_token_encrypted
 → add_agent_requeue_jobs
 → add_agency_integrations
 → add_snapshot_attempts
 → 0cd0399e2c3c (add_assigned_to_id_and_is_test)
 → add_audit_chain_hash
 → add_frontier_tables
 → add_idempotency_keys
 → add_platform_role_to_users
 → add_idempotency_fencing_token    ← CURRENT HEAD (nothing lists it as down_revision)
```

No branches, no multiple heads. A new revision cleanly chains onto `add_idempotency_fencing_token`.

### 2.3 Alembic wiring and how migrations run — VERIFIED

- **Config:** `alembic.ini` deliberately leaves `sqlalchemy.url` **empty** with a comment that the DB URL is intentionally omitted. `alembic/env.py:29-34` **requires** `DATABASE_URL` from the environment and raises `RuntimeError` if absent ("Refusing to migrate an implicit or local default database").
- **Past wrong-DB incident — documented and fixed.** `Docs/review/LAUNCH_READINESS_AUDIT_PER0100_2026-09-02.md` (finding LR-B03, P0) recorded that `alembic/env.py` previously read a hardcoded `localhost` URL from `alembic.ini`, so release commands migrated the wrong database. Current `env.py` no longer does this — the fix is in place (env var required; ini URL empty). VERIFIED by direct read of both files.
- **Run procedure (three entry points), all passing `DATABASE_URL` explicitly:**
  - Fly: `fly.toml` `[deploy] release_command = "alembic upgrade head"` — targets `DATABASE_URL` from Fly secrets.
  - Render: `render.yaml:17` `preDeployCommand: uv run alembic upgrade head`.
  - Local dev: `dev.sh` runs `alembic upgrade head` + `scripts/bootstrap_public_checker_agency.py` preflight (`Docs/research/DEPLOYMENT_OPERATIONS.md:187`).
- **Tests run against the real Postgres DB**, not SQLite: `tests/conftest.py:111-113` creates an async engine from the app's `DATABASE_URL` and idempotently seeds the canonical test agency via `INSERT ... ON CONFLICT DO NOTHING` against migrated schema. A new revision therefore runs against the same shared dev/test DB (`waypoint_os`) that local development uses.
- Active local DB: `.env` pins `DATABASE_URL=postgresql+asyncpg:...@localhost:5432/waypoint_os` and `TRIPSTORE_BACKEND=sql`.

### 2.4 Live-table facts (read-only probes against `waypoint_os`, 2026-09-04) — VERIFIED

| Fact | Value |
| --- | --- |
| Trips visible for the test agency (`d1e3b2b6-5509-4c27-b123-4b1e02b0bf5b`) | **21,161** |
| Distinct agencies with trips | 1 (the test agency) |
| `pg_stat_user_tables` estimate (`n_live_tup`) | ~21,625 |
| Table size / total incl. indexes | 15 MB / 22 MB |
| Dead tuples | ~2,981 |
| RLS on `trips` | **Enabled AND forced** (`relrowsecurity = t`, `relforcerowsecurity = t`); policies filter on `current_setting('app.current_agency_id')` |

Important probe note: a bare `SELECT count(*) FROM trips` returns **0** because the probing session had no `app.current_agency_id` set — forced RLS hides every row. Counts above were taken with the GUC set (the same mechanism `SQLTripStore._rls_session_for_agency` uses via `set_config('app.current_agency_id', ..., true)`, `spine_api/persistence.py:911,969,1032`).

---

## 3. Consumers of `analytics` / `_extra`

The column is simultaneously (a) a computed-metrics store, (b) an audit log (`status_history`), (c) an optimistic-concurrency version counter (`packet_version`), (d) an escape hatch for unmapped keys (`_extra`), and (e) a routing-token holder (`proposal_link_token`). This is why it is write-hot and why a naive `SET analytics = ...` wipes other writers' keys.

### 3.1 Producers (writers)

| Path | What it writes | File:line |
| --- | --- | --- |
| `process_trip_analytics()` | Canonical `AnalyticsPayload` (Pydantic) → `model_dump()`; recomputed on pipeline completion | `src/analytics/engine.py:98`; `src/analytics/models.py:84`; applied at `spine_api/server.py:2170-2174` |
| `save_trip` (SQL store) | Passes `analytics` through; folds **unmapped keys** into `_extra` | `spine_api/persistence.py:951-962` |
| `save_trip` on existing trip | Appends status transition to `_extra.status_history`, re-seeded from DB so a stale caller copy cannot regress the audit trail | `spine_api/persistence.py:984-1016` |
| `_apply_status_guard_orm` | Same status-history append for ORM-row update paths | `spine_api/persistence.py:70-96` |
| `_fold_unmapped_updates` | Folds unmapped keys into `_extra` for SQL CAS updates (review cycle 2, finding A: SQL CAS silently dropped unmapped keys) | `spine_api/persistence.py:99-128` |
| `_prepare_raw_update` | **The Python-side deep merge.** Pre-SELECTs `status, analytics`, enforces status invariant, appends history, deep-merges existing ∪ incoming with DB authoritative for `status_history`; docstring states plainly: "the trips.analytics column is JSON (no `\|\|` merge operator), so an in-SQL merge is impossible — and a plain SET would wipe keys another writer stored" | `spine_api/persistence.py:1268-1335`; called from raw-SQL update paths at 1356, 1429, 1505 |
| Packet sync (optimistic concurrency) | Writes `_extra.packet_version = packet_version + 1` | `spine_api/routers/inbound.py:358-370` |
| Feedback dismissal / SLA escalation | `feedback_dismissed`, `is_escalated`, `sla_status` rewrites via `update_trip({"analytics": ...})` | `spine_api/routers/analytics.py:137-140`; `src/analytics/metrics.py:389-397` |
| Legacy ops | `snooze_until`, `acknowledged_flags`, `suitability_acknowledged_at` | `spine_api/routers/legacy_ops.py:259-286` |
| Proposal link token | `proposal_link_token` written as a top-level trip dict key → lands in `_extra` through the fold on save; read back after the `_extra` fold on load | `spine_api/routers/trust_scorecard.py:265`; `spine_api/persistence.py:1788,1830` |

### 3.2 Readers

| Path | Keys read | File:line |
| --- | --- | --- |
| Analytics router | `requires_review`, `escalation_severity`, `review_reason`, feedback fields | `spine_api/routers/analytics.py:137,151-159,209-222` |
| Inbox router | `escalation_severity`, `sla_status` | `spine_api/routers/inbox.py:119-185` |
| Packet sync | top-level `packet_version` OR `_extra.packet_version` (dual read) | `spine_api/routers/inbound.py:278-300` |
| Inbox projection | `requires_review`, `escalation_severity` | `spine_api/services/inbox_projection.py:375,453-473` |
| Pipeline execution | `feedback_reopen`, `review_reason` | `spine_api/services/pipeline_execution_service.py:540-542` |
| Metrics engine | `quality_score`, `margin_pct`, `latest_feedback`, `feedback_reopen`, `feedback_dismissed`, `recovery_deadline`, `sla_status`, `is_escalated` (also writes), `review_reason`, `proactive_feedback_at` | `src/analytics/metrics.py:32-33,51-55,197-199,365-421` |
| Operator refinement agent | `feedback_reopen`, `requires_review`, `review_reason` | `src/agents/operator_refinement_agent.py:64-106` |
| Dashboard aggregator | `requires_review`, `review_status`, `quality_score`, `margin_pct` | `src/services/dashboard_aggregator.py:133-143,251-252,357-370` |
| SQL read fold | `_extra` folded back to top level on every SQL read, mirroring `_to_dict` | `spine_api/persistence.py:852-858,1252-1265` |
| Status machine | Documents the `_extra` fold contract | `spine_api/core/trip_status.py:116` |

**List projections:** `list_trip_summaries` exists specifically to avoid fetching heavy JSON blobs on list paths (`src/services/dashboard_aggregator.py:82`). A GIN index on the JSONB column would complement this: filtered list endpoints (`/analytics/reviews` scans all trips checking `requires_review` in Python today) could become containment queries.

---

## 4. Data-shape risks (pre-migration validation)

Verified against live data (read-only, RLS-context probes):

- **Top-level type:** 18,307 rows `NULL` + 2,854 rows `jsonb_typeof = 'object'`. **Zero scalars, zero arrays.** Every non-null `analytics` value is a valid JSON object — safe for `USING analytics::jsonb` and safe for `||` (which requires objects on both sides).
- **Top-level key inventory:** exactly 19 distinct keys — the 18 `AnalyticsPayload` producer fields (`margin_pct`, `quality_score`, `quality_breakdown`, `requires_review`, `review_reason`, `feedback_reopen`, `feedback_severity`, `followup_needed`, `recovery_status`, `recovery_started_at`, `recovery_deadline`, `is_escalated`, `sla_status`, `owner_review_deadline`, `escalation_severity`, `approval_required_for_send`, `send_policy_reason`, `revision_count`) plus `_extra` (present in 1,378 rows).
- **`_extra` contents in data:** `status_history` present in 67 rows; `packet_version` in **0 rows** (the inbound.py write path exists but is unexercised in current data — inferred: packet sync has not been run against these trips).
- **Defensive coding already tolerates shape drift:** `_prepare_raw_update` handles `raw_analytics` being `str` (json.loads), `dict`, or anything else (`spine_api/persistence.py:1300-1310`); `_fold_unmapped_updates` degrades to no-op if `Trip` is stubbed. So the application would survive unexpected shapes even though the data has none.
- **No encrypted blobs inside `analytics` — VERIFIED:** `analytics` is in **neither** `_PRIVATE_BLOB_FIELDS` (traveler_bundle, internal_bundle, safety, fees, frontier_result, booking_data, pending_booking_data — Fernet-encrypted whole-blob, stored as a JSON **string scalar**) nor `_PII_KEY_FIELDS` (extracted, raw_input — recursive key-level encryption) (`spine_api/persistence.py:708-723`). It is stored **plaintext**.
- **Residual PII caveat — INFERRED from code:** `src/security/privacy_guard.py:116,252` explicitly ignores deeply nested fields (e.g. `analytics.review_metadata.notes`) in its freeform/PII scan, and `_fold_unmapped_updates` will route *any* unmapped caller key into `_extra` unencrypted. If a future caller folds freeform text into an unmapped key, it lands plaintext in `_extra`. This is a pre-existing property of the JSON design, unchanged by JSONB — but it should be on the radar before adding GIN indexing over `_extra` (an index makes those values searchable, i.e., more exposed).

---

## 5. Migration design (step-by-step, reversible)

### 5.1 Pre-checks (one-time, before authoring the revision)

1. Confirm single head: `alembic heads` → expect `add_idempotency_fencing_token` only. (Verified by static chain read; re-run at implementation time.)
2. Re-run the shape probe from §4: `jsonb_typeof` distribution and `? '_extra'` counts must show objects-only for `analytics` before `USING analytics::jsonb` can be assumed lossless (it is lossless for *any* legal json value, but object-only confirms `||` merges remain valid post-migration).

### 5.2 Revision sketch

New file: `alembic/versions/convert_trips_analytics_to_jsonb.py`, chained on head `add_idempotency_fencing_token`. All DDL literals are static (no external input interpolated), satisfying the parameter-binding constraint; the only dynamic-ish statement (`SET lock_timeout`) uses a literal value, and any future value parameterization must use bound params (e.g. `text("SET lock_timeout = :t").bindparams(...)`), never f-strings.

```python
"""convert trips.analytics from json to jsonb

Revision ID: <generated>
Revises: add_idempotency_fencing_token
"""
from alembic import op

revision = "<generated>"
down_revision = "add_idempotency_fencing_token"
branch_labels = None
depends_on = None

# Rewrite + swap is one atomic DDL statement per direction. At the current
# data volume (≈21.6k rows, 15 MB) this completes in well under a second;
# the lock_timeout guard keeps a pathological stall from piling up
# ACCESS EXCLUSIVE waiters behind it.
_LOCK_TIMEOUT = "5s"

def upgrade() -> None:
    op.execute(f"SET lock_timeout = '{_LOCK_TIMEOUT}'")
    # Static SQL: table/column names are code constants, no user input.
    op.execute(
        "ALTER TABLE trips ALTER COLUMN analytics TYPE JSONB "
        "USING analytics::jsonb"
    )

def downgrade() -> None:
    op.execute(f"SET lock_timeout = '{_LOCK_TIMEOUT}'")
    # jsonb -> json is the exact inverse cast; no data loss because every
    # stored value is valid json in both directions.
    op.execute(
        "ALTER TABLE trips ALTER COLUMN analytics TYPE JSON "
        "USING analytics::json"
    )
```

**Alembic mechanics note (verified constraint):** a plain `op.execute` inside the default transaction is correct for the type change. If a later task adds `CREATE INDEX CONCURRENTLY` (§6), that statement **cannot run inside a transaction block** — it must live in its own revision using `with op.get_context().autocommit_block():`, or the index must be created non-concurrently (acceptable at 15 MB).

### 5.3 Model swap (same change-set, code side)

`spine_api/models/trips.py:70`:

```python
from sqlalchemy.dialects.postgresql import JSONB

analytics: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
```

**Precedent — this repo already uses JSONB on Postgres:**

- `spine_api/models/idempotency.py:52`: `JSON().with_variant(JSONB(), "postgresql")` — the dialect-safe variant pattern.
- `spine_api/models/audit.py:30-38`: `_json_type()` helper returning JSONB on PG, JSON elsewhere ("for tests").

**Recommendation:** use plain `JSONB` (not `with_variant`). VERIFIED: `tests/conftest.py:111-113` runs the suite against the real Postgres via `DATABASE_URL`; the SQLite fallback the `audit.py` comment alludes to is not the operative test path. If a future SQLite test path is reintroduced, switch to `JSON().with_variant(JSONB(), "postgresql")` then — a one-line change.

**Behavior parity check:** SQLAlchemy's `JSONB` type serializes/deserializes dicts identically from the ORM's perspective; `SELECT status, analytics` in `_prepare_raw_update` (`persistence.py:1293`) will now return parsed dicts from asyncpg exactly as before (it already handles both `str` and `dict` defensively, so no change needed there). No consumer code changes are required for parity.

### 5.4 Deployment sequence

1. Merge model change + revision; CI/test suite runs against `waypoint_os` → the revision is exercised by the standard flow (tests run `alembic upgrade head` via dev bootstrap or the schema is already migrated in the shared dev DB).
2. Fly/Render release command (`alembic upgrade head`) executes the `ALTER` before new pods accept traffic — migration-under-lock window is a single-digit-millisecond rewrite at 15 MB.
3. Rollback = `alembic downgrade -1` (exact inverse cast, no data loss) + reverting the model line.

### 5.5 Scale-out alternative (documented, NOT needed at current size)

If `trips` ever grows past roughly 10⁶ rows (rewrite would hold ACCESS EXCLUSIVE for seconds+), switch to the low-lock pattern instead of the direct `ALTER`:

1. `ALTER TABLE trips ADD COLUMN analytics_new JSONB;`
2. Batched backfill: `UPDATE trips SET analytics_new = analytics::jsonb WHERE id IN (SELECT id FROM trips WHERE analytics_new IS NULL AND analytics IS NOT NULL LIMIT :batch)` — bound `:batch` param, looped outside a single transaction.
3. Brief lock: `ALTER TABLE trips RENAME COLUMN analytics TO analytics_old; ALTER TABLE trips RENAME COLUMN analytics_new TO analytics;` then drop `_old` later.
This is the standard add-column/backfill/swap recipe; keep it in the back pocket, do not build it now (YAGNI at 21k rows).

---

## 6. What it unlocks

1. **Atomic in-SQL merge** — replace `_prepare_raw_update`'s pre-SELECT + Python deep-merge with a single statement (closing the read-enforce-write gap that currently relies on the `updated_at` CAS predicate as defense-in-depth):

   ```sql
   UPDATE trips
   SET analytics = COALESCE(analytics, '{}'::jsonb) || CAST(:incoming AS jsonb),
       updated_at = NOW()
   WHERE id = :trip_id
     AND updated_at = CAST(:expected AS timestamptz)
   RETURNING *
   ```

   All external values (`:incoming`, `:trip_id`, `:expected`) are **bound parameters** — matches the repo's existing named-bind pattern (`_status_guard_sql_predicate`, `persistence.py:131-139`). The `||` operator does a shallow merge, so `_extra` still needs the existing Python status-history logic or a `jsonb_set` nested expression; the win is eliminating the pre-SELECT round trip and the lost-update window for top-level keys.
2. **GIN indexing on `_extra`** — e.g. `CREATE INDEX ... USING GIN (analytics jsonb_path_ops)` (own revision, `autocommit_block` for CONCURRENTLY).
3. **Containment queries** — `/analytics/reviews`, inbox escalation filters, and `dashboard_aggregator` review counting currently filter in Python across all trips; with JSONB they become indexable predicates like `WHERE analytics @> CAST(:pred AS jsonb)` with `:pred` bound (e.g. `'{"requires_review": true}'`). Also enables `jsonb_path_query` for status-history drill-downs without loading full rows.
4. **In-place field updates** — `jsonb_set` for single-key writes (snooze_until, feedback_dismissed) without read-modify-write.
5. **Storage/perf hygiene** — jsonb does not preserve key order/whitespace/duplicates; for machine-written payloads this is strictly smaller on disk and faster to parse than re-parsing json text on every read (minor at 15 MB, compounding as the table grows).

---

## 7. Risks

| Risk | Assessment | Mitigation |
| --- | --- | --- |
| **Lock** — `ALTER ... TYPE` takes ACCESS EXCLUSIVE and rewrites the table | **Low at current size (VERIFIED: 21.6k rows / 15 MB → sub-second rewrite).** Real risk is only a long-running transaction (e.g. a stuck request holding a row lock on `trips`) blocking the ALTER and piling up waiters | `SET lock_timeout = '5s'` in the revision (sketch §5.2) + run in the release command window when traffic is quiescent; retry-on-timeout |
| **RLS interaction** | **Low, VERIFIED structurally:** forced RLS policies filter on `agency_id` only, never on `analytics`; DDL rewrite is not a row-SELECT so owner-forced RLS does not impede the migration. Alembic connects as the table owner (`waypoint`), which created the table | None needed; but any *verification SELECT* in the migration would need the GUC or owner exemption awareness — keep the revision free of row probes |
| **Dual-store parity** | **Low.** `TRIPSTORE_BACKEND=sql` is pinned in `.env` (pinned after the 2026-05-03 "missing trips" incident); the file store (`data/trips/*.json`) is dormant. All `_extra` folding helpers are module-level and backend-shared, so no SQL-only code drift. If the file store were ever active, JSONB operators must be used only inside SQL-path methods | Gate any new `\|\|` / `@>` SQL behind the `SQLTripStore` class (where all raw SQL already lives) |
| **jsonb semantic differences** | **Low but real:** jsonb rejects duplicate keys and normalizes number formatting/whitespace; key order not preserved. All writers are `dict` → JSON serializers, so nothing depends on order/duplicates. Python `json.dumps` output of a dict can never contain duplicate keys | None required; note it in the revision docstring |
| **Test surface** | Tests run against real Postgres (VERIFIED), so the type change is exercised end-to-end; ORM reads/writes are type-agnostic | Run the full spine_api suite post-migration (per repo 4-phase discipline) |
| **GIN + PII caveat** | If `_extra` ever receives freeform text (privacy_guard ignores deep analytics fields, §4), a GIN index makes it searchable and persists tokenized forms | Before adding the GIN index, add a `_fold_unmapped_updates` guard for freeform-looking keys, or exclude `_extra` from the indexed expression |

---

## 8. Sized next tasks

| # | Task | Size | Notes |
| --- | --- | --- | --- |
| E2.1 | Alembic revision (§5.2) + model swap (§5.3) + run suite + live verification (`SELECT jsonb_typeof(analytics) ...` + one trip read through the API) | S (half day incl. 2 review cycles for a schema change per repo discipline) | The core deliverable |
| E2.2 | Atomic in-SQL analytics merge in `_prepare_raw_update`'s raw-SQL callers using `\|\|` + bound params; keep Python status-history append (or express via `jsonb_set`) | M | Deletes the pre-SELECT round trip; keep the CAS WHERE |
| E2.3 | GIN index revision (`autocommit_block` + CONCURRENTLY) + convert `/analytics/reviews` and inbox escalation filters to containment queries | M | Blocked on PII caveat decision (§7) |
| E2.4 | Evaluate other 12 trips JSON columns for JSONB | S (analysis only) | No current in-SQL operator need; see decision below |
| E2.5 | Add `_fold_unmapped_updates` freeform-key guard (PII hardening surfaced by this exploration, independent of JSONB) | S | Worth doing regardless |

---

## 9. Decisions needed

- **Decision needed: convert only `analytics` now, or all 13 `trips` JSON columns in one revision?** Recommendation: **only `analytics`** — it is the only column with an in-SQL operator need. The other 12 (`extracted`, `validation`, `decision`, `strategy`, `traveler_bundle`, `internal_bundle`, `safety`, `frontier_result`, `fees`, `booking_data`, `pending_booking_data`, `raw_input`; `spine_api/models/trips.py:55-69`) are whole-document reads/writes through the ORM; several store Fernet-encrypted string scalars (§4), which are legal jsonb but gain nothing from it. Batch-converting them later is the same one-statement pattern.
- **Decision needed: GIN index now or when a containment query actually lands?** Recommendation: **defer to E2.3** — index without a query is pure write cost; `_extra` PII caveat should be settled first.
- **Decision needed: `lock_timeout` value for the release-window migration** ('5s' proposed in §5.2; the 15 MB rewrite needs milliseconds, so this only guards pathological blocker transactions).
- **Decision needed: keep `_prepare_raw_update`'s defensive `str`-handling (`json.loads` branch, `persistence.py:1301-1305`) after JSONB conversion?** Post-migration asyncpg always returns parsed dicts, so the branch is dead in production but harmless and cheap. Recommendation: keep it (Code Preservation — it also covers stubbed test rows) until E2.2 replaces the function.
- **Decision needed: is the missing `_extra.packet_version` in live data (0 rows) expected?** The write path exists (`inbound.py:358-370`) but no trip carries it — inferred as "path never exercised in this dataset." Confirm there is no lost-update regression hiding there before building E2.2 on top of it.

---

## Verification summary

| Claim | Status |
| --- | --- |
| Column is `json` (model + birth migration) | VERIFIED (file reads) |
| Single linear migration chain, head `add_idempotency_fencing_token`, analytics never altered | VERIFIED (all 31 revision files read) |
| Alembic requires `DATABASE_URL`; wrong-DB incident (LR-B03) fixed | VERIFIED (env.py + alembic.ini + audit doc) |
| Migrations run via fly release_command / render preDeployCommand / dev.sh | VERIFIED (config files + ops doc) |
| ~21.6k trips, 15 MB table, one agency | VERIFIED (read-only probes with RLS context) |
| analytics values: objects-only, 19 known keys, `_extra` in 1,378 rows | VERIFIED (live probes) |
| analytics not encrypted, plaintext | VERIFIED (`_PRIVATE_BLOB_FIELDS` / `_PII_KEY_FIELDS` exclude it) |
| JSONB precedents in models (idempotency, audit) | VERIFIED (file reads) |
| Tests run against real Postgres, not SQLite | VERIFIED (conftest read) |
| Scale-out add-column/backfill/swap threshold | INFERRED (standard Postgres practice; not needed at current size) |
| `_extra.packet_version` absence in data = unexercised path | INFERRED (needs confirmation) |
