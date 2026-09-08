# E-G — Durable-Store Endgame: SQL-only design (2026-09-08)

**Exploration package E-G (PER-0700)** — closes L4 (dual-store split-brain) and the residual concurrency windows documented in PER-0443 Parts H/J. Status: **PROPOSED design; migration under A-20 custody**.

## Current state (why this is the endgame)

`TripStore` is a facade over `FileTripStore` and `SQLTripStore`, selected by `TRIPSTORE_BACKEND` (pinned `sql` in `.env` since the 05-03 lost-trips incident). File-store parity code still exists and tests still exercise it; several correctness fixes landed only on one backend and had to be mirrored. Known residual windows on SQL, all now documented:

1. Partial-update `_extra` replacement (fixed root-cause in `6c7c824` via `_prepare_raw_update`, but the fold-based `_extra` design itself is the weakness — booking_confirmation sits plaintext inside `analytics._extra`).
2. NBTA verify-and-heal loop: post-verify clobber window heals only via the next writer.
3. Fulfillment graph CAS fallback: plain write after bounded contention (durability prioritized).
4. `update_trip_if_version` uses `updated_at` comparison — safe but coarse (any touch bumps the version).

## Endgame design

### 1. One store, one schema owner

`TRIPSTORE_BACKEND` is removed as a *runtime choice*: SQL is the only backend; the file store remains solely as an **offline import/export format** (`tools/tripstore_export.py` / `--import`), with a documented JSON schema version. `FileTripStore` class stays for that codec only; every facade method becomes a direct SQL call (no backend branch), deleting the split-brain class of bugs permanently.

### 2. First-class columns for hot evidence keys

`booking_confirmation`, `journey_graph_nodes`, `journey_graph_edges`, `travel_next_action`, `travel_next_action_priority`, `proposal_acceptance_*` move out of `analytics._extra` into real (encrypted where PII/VCC) columns:

- kills the fold/unfold asymmetry class entirely (root of the L7 data-loss catch);
- `booking_confirmation` gets its encrypted column (Part L.5 A4) plus the partial unique index already shipped;
- `travel_next_action(_priority)` become first-class, enabling **store-level priority merge** (see 4).

### 3. Version column becomes monotonic

`updated_at` stays for humans; a separate `version BIGINT` (per-row counter, bumped in the same UPDATE) becomes the CAS token. Compare-and-set semantics: `UPDATE ... SET version = version + 1 WHERE id = :id AND version = :expected` — no ISO-parse ambiguity, immune to clock shape.

### 4. Store-level domain operations (closing the residual windows)

Move merge intent into the store as atomic operations instead of read-modify-write in callers:

- `merge_next_action(trip_id, action, priority, source)` — single UPDATE with `WHERE travel_next_action_priority <= :priority OR travel_next_action IS NULL`; returns final state. Deletes the NBTA heal loop and its window (roadmap A/residual 2).
- `append_journey_graph(trip_id, nodes[], edges[])` — single UPDATE applying the caller's merge to the DB-side JSON under row lock; deletes the fulfillment CAS-fallback window (residual 3).
- `record_confirmation(trip_id, type, payload)` — INSERT + trip blob update in one transaction; the partial unique index makes double-record structurally impossible (already shipped in `bc_active_type_uniqueness`).

Callers keep their policy logic (what to write); the store owns concurrency (how it lands).

### 5. Migration path (A-20 custody)

1. Additive alembic: new columns (`version`, encrypted booking columns, next-action columns).
2. Backfill from `analytics._extra` + trip JSON blobs (one agency at a time, re-runnable, dry-run report).
3. Dual-read cutover: facade prefers columns, falls back to `_extra` for un-migrated rows; write path writes both.
4. Flip: writes go to columns only; `_extra` fold code path deleted (supersession ADR).
5. File store deleted from the facade (supersession ADR; codec moves to `tools/`).

### 6. Test strategy

- `test_trip_store_sql_coverage.py` extended: every domain operation gets a concurrency test (two threads, interleaved CAS/merge, assert no loss).
- Parity tests removed with the file backend; replaced by import/export round-trip tests.
- The L7 browser scenario (seed → accept → fulfill → serve → render) becomes a CI-gated smoke against an ephemeral Postgres (per-PR database), so `_extra`-class regressions can never silently reappear.

## What this unblocks

- L4 (multi-worker/restart truth) — the last split-brain root.
- NBTA full closure and fulfillment graph window closure (residuals 2–3 deleted, not patched).
- Encrypted booking evidence (A4) as a plain column migration.
- Simplified mypy surface: the facade loses its dual-backend branches.
