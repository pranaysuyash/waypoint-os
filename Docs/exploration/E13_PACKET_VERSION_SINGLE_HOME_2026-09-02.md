# E13: `packet_version` Dual-Carriage — Single Home or Ratified Contract?

**Date:** 2026-09-02 (researched and verified 2026-09-04)
**Type:** EXPLORE — research and design only. No code changed. Read-only.
**Trigger:** F-27 shipped the `/optimistic-sync` optimistic-concurrency version with a dual-carriage storage contract: top-level `packet_version` on file-store trips, `analytics._extra.packet_version` on SQL trips (SQL has no such column). The read side (`_stored_packet_version`, `spine_api/routers/inbound.py:280-287`) checks both. It works and is tested, but it is one semantic living in two homes. Question: consolidate, or ratify the dual-carriage deliberately?

---

## 1. Question

The optimistic-sync concurrency version is stored in two different places depending on the trip-store backend. Should we (a) ratify that as a documented contract, (b) collapse both backends onto `analytics._extra`, (c) give SQL a dedicated column via Alembic, or (d) move the version onto the packet dict itself so it travels with the packet regardless of backend?

---

## 2. Current state — exact read/write sites

### 2.1 Writers — exactly one, dual-write — VERIFIED

`rg packet_version` across `spine_api/` finds exactly **one writer**: the `/optimistic-sync` route.

- `spine_api/routers/inbound.py:358-371` — after the merge and state re-evaluation, the route builds one `updates` dict that carries the bumped version in **both** places simultaneously:

  ```python
  analytics_extra["packet_version"] = packet_version + 1   # line 360 — SQL home
  base_analytics["_extra"] = analytics_extra
  updates = {
      ...,
      "packet_version": packet_version + 1,                # line 368 — file home
      "analytics": base_analytics,
      ...
  }
  ```

- What each backend then does with that dict — **VERIFIED**:
  - **File store** persists the dict verbatim (`FileTripStore.save_trip` `persistence.py:383-405`; CAS variant `update_trip_if_version_for_agency` `persistence.py:597-623` does `trip.update(updates)` and dumps the whole JSON). So after a sync a file JSON contains **both** a top-level key and the `analytics._extra` copy.
  - **SQL store** runs `_fold_unmapped_updates` (`persistence.py:99-128`, applied at `:1203`, `:1355`, `:1428`, `:1504`): any key not in `Trip.__table__.columns` is stripped from the top level and folded into `analytics._extra`. The route's top-level `packet_version` therefore lands in `_extra` even without the pre-seed — the pre-seed at `:358-361` is (post-fold) belt-and-braces. `save_trip` (SQL) folds unmapped keys the same way (`persistence.py:955-962`).
- **No other writers.** The three other `update_trip_if_version_for_agency` CAS callers — booking-data (`spine_api/server.py:2862`), payment tracking (`:2956`), customer-accept (`:3298`) — do **not** bump `packet_version`; their concurrency token is `updated_at`. `/parse` mints trips with no `packet_version` at all (`inbound.py:165-183`) → new trips implicitly version 0.

> Consequence worth stating explicitly: `packet_version` is a **sync-scoped concurrency token**, not a general record version. The general record CAS is `updated_at` (store-level, both backends).

### 2.2 Readers — dual-read at one site; SQL reads also surface top level — VERIFIED

- `spine_api/routers/inbound.py:280-287` `_stored_packet_version()`: top-level first, then `(analytics._extra).packet_version` fallback, defaulting 0. The `:278-279` comment already states the rationale ("canonical at top level on the file store and inside analytics._extra on the SQL store (not a Trip column) — read both").
- SQL reads fold `_extra` back to the top level (`_to_dict` `persistence.py:857-862`; `_row_to_dict` `:1257-1264`; both use `if k not in res`). So **SQL reads already expose `packet_version` at the top level**; the router's `_extra` fallback is a second safety net, not the primary SQL path.
- File reads are a raw `json.load` (`persistence.py:443-455`) — no fold — so the file store genuinely depends on the top-level write.
- Contract surfaces: `spine_api/contract.py:1352` (`expected_packet_version`, request) and `:1370` (`packet_version`, response); generated FE types `frontend/src/types/generated/spine-api.ts:652-675`.

### 2.3 The folding mechanism — VERIFIED

- `_fold_unmapped_updates` (`persistence.py:99-128`): classifies each update key against `Trip.__table__.columns`; unmapped keys (except `saved_at`) are merged into the updates' `analytics._extra`. Introduced in review cycle 2 of the F-27 work after the SQL CAS was found silently dropping `packet`/`decision_state`/`missing_fields`.
- SQL read fold (`_to_dict` / `_row_to_dict`) mirrors it: `_extra` keys surface top level on every SQL read.
- Net effect: **the logical read contract is already single-home (top level) on both backends**; the physical storage is dual.

### 2.4 Live data — the SQL home is currently empty — VERIFIED (E-2 probes)

`Docs/exploration/E2_ANALYTICS_JSON_TO_JSONB_MIGRATION_2026-09-02.md` §4 (read-only probes against `waypoint_os`, 2026-09-04): `analytics._extra.packet_version` is present in **0 of ~21.6k rows**. File-store JSONs with the key are gitignored test effluent (`.gitignore:117,121,149,162`; register R-03). So in production SQL data today, `packet_version` exists **nowhere**.

### 2.5 Tests pin both homes — VERIFIED

| Test | Backend | What it pins |
|---|---|---|
| `tests/test_optimistic_sync_merge.py` (10 tests; autouse fixture `:22-25` pins `TRIPSTORE_BACKEND=file`) | **file** | API behavior incl. `saved["packet_version"] == 1` (`:148`, `:213`) — pins the **top-level file home** via `FileTripStore` verbatim reads |
| `tests/test_trip_store_sql_coverage.py:245-283` (`requires_db`) | **sql** | CAS folds top-level unmapped `packet_version: 1` into `_extra`; read fold surfaces it top level; refetch agrees — pins the **SQL `_extra` home + read fold** |
| `tests/test_trip_status_machine.py:287-294` | unit | `_fold_unmapped_updates({"packet_version": 3, ...})` → `analytics._extra.packet_version == 3`, key absent from top level — pins the **folding mechanism itself** |

Any consolidation that removes one home breaks at least one of these files; the fold-mechanism test (`test_trip_status_machine.py:289`) survives option (c) only with an updated expectation, since a `packet_version` column would make the key "known" and no longer folded.

---

## 3. Options analysis

| Option | Cost | Benefit | Risk | Who breaks |
|---|---|---|---|---|
| **(a) Status quo ratified** — dual-carriage + dual-read documented as contract | **Zero migration.** One comment/doc expansion (the `:278-279` comment already half-does it) + register note | Single writer, single logical read contract (top level after folds), defensive read fallback already tested; zero churn on reviewed, green code | A future consumer cannot query/index/filter by version in SQL; mild redundancy in the write dict (top-level + pre-seeded `_extra`) | Nobody |
| **(b) Single home in `analytics._extra` for BOTH backends** — drop the top-level write; rely on the SQL fold; add a file-store read fold (or accept file reads lose top level) | Small code, real compat tail: file JSONs with legacy top-level keys need read-compat (keep dual-read fallback); `FileTripStore` gains a fold it never had, or `test_optimistic_sync_merge.py:148,213` (`saved["packet_version"]`) fails under its pinned file backend | One physical home per backend; write dict simplifies | **Negative real-world value.** Production SQL already surfaces top level via read fold — (b) changes where bytes sit, not what any reader sees; adds churn to a test-double backend | `test_optimistic_sync_merge.py` (file-pinned), `test_trip_store_sql_coverage.py` (fold expectations), any hand-inspected file JSON |
| **(c) Dedicated SQL column** — Alembic `ADD COLUMN packet_version INTEGER NOT NULL DEFAULT 0` + model field; `_fold_unmapped_updates` maps it as a known column automatically (it reads `Trip.__table__.columns`) | One revision + model field + backfill `UPDATE trips SET packet_version = COALESCE((analytics->'_extra'->>'packet_version')::int, 0)` (the `->`/`->>` operators work on `json`; E-2 §2 verified the column is plain `json`, never altered since `create_trips_table_v1`, chain head `add_idempotency_fencing_token` — a new revision chains cleanly). Because live data has **0 rows** with the key (§2.4), the backfill is a no-op today | First-class, queryable, indexable version; enables atomic `SET packet_version = packet_version + 1` inside the SQL CAS UPDATE; pairs naturally as a rider on the E-2 `json`→`jsonb` revision; read simplifies to one line (keep the `_extra` fallback one release for old rows, then delete) | Migration discipline cost (schema change ⇒ 2 review cycles per repo rule); `_extra` copies in old file artifacts remain vestigial | `tests/test_trip_status_machine.py:289` (fold expectation flips to "known column"), `test_trip_store_sql_coverage.py` (still passes — top-level round trip unchanged), router read simplification |
| **(d) Version on the packet dict (`packet["_version"]`)** | Zero storage-schema work | Travels with the packet regardless of backend — superficially the tidiest | **Correctness regression — REJECT.** The packet is replaced wholesale by extraction: `/parse` mints `packet_dict` fresh from `spine_result` (`inbound.py:154`), `social_inbound.py:138` builds a new packet, multimodal mutates via `setdefault` (`multimodal.py:181,231`). Any spine re-processing would drop `_version` → version resets to 0 → a stale client with `expected_packet_version=0` now **matches** the rewritten trip and the last-write-wins window F-27 closed reopens silently. Also needs reserved-key handling in `spine_api/services/field_merge.py` (the `_field_provenance` machinery) to stop clients writing it | Everything, badly |

**Concurrency semantics:** unchanged under (a), (b), and (c) — the actual race guard is the store-level `updated_at` CAS (`update_trip_if_version_for_agency`, both backends); `packet_version` is the client-facing advisory token checked at `inbound.py:290`. (c) additionally allows an atomic in-SQL increment, but that is a robustness nicety, not a new guarantee. (d) actively weakens semantics.

---

## 4. The file-store framing — does the R-03 posture make (a) correct?

Register R-03 (`Docs/review/FINDINGS_REGISTER_2026-08-31.md:27`) was **reframed**, not just fixed: file-store JSONs are gitignored **test effluent**, SQL mode is fail-closed, and there is no production split-brain. `TRIPSTORE_BACKEND=sql` is pinned in `.env` (AGENTS.md, Data Safety section) after the 2026-05-03 incident.

Under that posture the "two homes" claim dissolves almost entirely:

- **Production (SQL) has exactly one home today:** `analytics._extra` — and per §2.4 it currently holds **0 rows** of the key. There is no production duplication to consolidate.
- **Top-level-on-file is the test double's storage convenience:** `FileTripStore` is a dict-in/dict-out JSON mirror with no schema and no read fold; top level is simply the cheapest place for it to keep the key. Its storage shape is not a product contract, and nothing in production reads those files.
- The dual-read in the router is then best understood as **one logical contract + one backend adapter**: "read top level" works on both backends (true on file, read-folded on SQL); the `_extra` fallback is defensive depth for non-folding read paths, not a second contract.

So the honest framing is: this is not "one semantic in two homes" in production — it is **one production home plus a documented test-double behavior**. The remaining genuine wart is only that the SQL home is an escape-hatch blob (`_extra`) rather than a first-class field, and there is no consumer that cares today.

---

## 5. Recommendation

**Ratify (a) now; pre-register (c) as a rider on E-2.** This is the smallest honest path:

1. The write side is already single-site and dual-write-by-construction (one `updates` dict; each backend's folding decides the physical home — verified §2.1).
2. The read side is already a single logical contract (top level) with a tested fallback (§2.2).
3. Production SQL data carries zero instances of the key (§2.4), so there is no live duplication, no drift surface, and no query that needs a column.
4. (b) buys nothing (production readers already see top level) and costs churn against a test double. (d) is a correctness regression and is rejected outright.
5. (c) is clean and cheap — but it is migration cost paid today for a capability nobody uses. Its natural trigger is the E-2 `json`→`jsonb` revision (same table, adjacent Alembic revision, backfill is a no-op at current data). Attaching it there is strictly cheaper than landing it standalone.

Concretely: expand the `inbound.py:278-279` comment into the full contract statement, add a companion note to the F-27 register line marking dual-carriage as **deliberate**, and leave every line of behavior as shipped. Keep the dual-read.

---

## 6. Sized next tasks

| # | Task | Size | Notes |
|---|---|---|---|
| E13.1 | Ratify: expand the `spine_api/routers/inbound.py:278-279` comment into the full dual-carriage contract (sole writer `:358-371`; per-backend physical home; SQL read fold at `persistence.py:857-862,1257-1264`; `_extra` fallback semantics); add a one-line "dual-carriage is deliberate" companion note to F-27 in `Docs/review/FINDINGS_REGISTER_2026-08-31.md` | S (comment + register line only; no behavior change, no test change) | The core deliverable of this exploration |
| E13.2 | **Conditional** dedicated column: Alembic revision `ADD COLUMN packet_version INTEGER NOT NULL DEFAULT 0` + backfill (no-op today, §2.4) + `Trip` model field; update `test_trip_status_machine.py:289` fold expectation (key becomes a known column); simplify `_stored_packet_version` to the top-level read, keep the `_extra` fallback one release, then delete it | S–M (schema change ⇒ 2 review cycles per repo discipline) | **Trigger:** any need to query/filter by version, atomic in-SQL increment, or promotion to a general record version. Cheapest as a rider on the E-2 revision (same table; chain head `add_idempotency_fencing_token`, E-2 §2.2) |
| E13.3 | Optional micro-cleanup: collapse the route's dual-write — drop the `_extra` pre-seed at `inbound.py:358-361`, keep only the top-level `packet_version` in `updates`; the SQL fold centralizes the `_extra` copy; file store keeps top level | S | Zero behavioral gain — the pre-seed is redundant *only* because the fold exists (`persistence.py:1428`); only worth doing if E13.2 lands, to avoid churning reviewed, green code twice |

---

## 7. Decision needed

**Decision needed: ratify (a) now, or schedule (c) immediately?** Recommendation: **ratify (a)** via E13.1 and hold E13.2 against the E-2 co-migration trigger. Rationale in one line: production SQL carries zero `packet_version` rows, the logical read contract is already single-home, and the only consolidation that adds real value (a first-class column) is strictly cheaper when it rides the `json`→`jsonb` revision it naturally pairs with.

Secondary decision bundled with E13.2 (only if triggered): keep the `_extra` fallback in `_stored_packet_version` for one release after backfill, then delete — file-store JSON artifacts with top-level keys keep working regardless since the file home stays top-level.

---

## Verification summary

| Claim | Status |
|---|---|
| Sole writer is `/optimistic-sync` `inbound.py:358-371`, dual-writing top-level + `_extra` in one `updates` dict | VERIFIED (file read) |
| `_fold_unmapped_updates` strips non-column keys into `analytics._extra` (`persistence.py:99-128`; applied at 1203/1355/1428/1504); `save_trip` folds likewise (`:955-962`) | VERIFIED (file read) |
| SQL read fold surfaces `_extra` at top level (`_to_dict` :857-862; `_row_to_dict` :1257-1264); file reads are raw `json.load`, no fold (:443-455) | VERIFIED (file read) |
| Booking/payment/accept CAS callers do not bump `packet_version`; general CAS token is `updated_at` | VERIFIED (`server.py:2862,2956,3298`; `inbound.py:372-374`) |
| `packet_version` in 0 of ~21.6k live SQL rows; file JSONs gitignored test effluent | VERIFIED (E-2 §4 live probes; `.gitignore:117-162`; register R-03 :27) |
| F-27 API tests pin the file backend; SQL round-trip and fold mechanics pinned in two other files | VERIFIED (`test_optimistic_sync_merge.py:22-25`; `test_trip_store_sql_coverage.py:245-283`; `test_trip_status_machine.py:287-294`) |
| `trips.analytics` is `json`, never altered, single linear migration chain, head `add_idempotency_fencing_token` | VERIFIED (E-2 §2.1-2.2, all 31 revision files read) |
| Packet is replaced wholesale by extraction (`inbound.py:154`, `social_inbound.py:138`, `multimodal.py:181,231`) → option (d) resets the version | VERIFIED (file reads); blast radius on stale-client behavior INFERRED from the 409 contract at `inbound.py:290-298` |
| Post-E13.2 fold-test expectation flip is the only test breakage for option (c) | INFERRED (from `Trip.__table__.columns` classification in `_fold_unmapped_updates`); confirm by running the three test files if E13.2 is scheduled |
