# EX-10 — Event-Store Ops Posture (Product-B JSONL) (2026-09-08)

Status: research + shipped-mechanism documentation. Complements FT-06 (rotation, shipped with tests 2026-09-08).

## Shipped (FT-06)

`ProductBEventStore.log_event` now checks segment size under the store lock before each append and rotates oversized segments to `<name>.1` (one retained generation):

- Cap: `PUBLIC_B_EVENTS_MAX_BYTES`, default 10 MiB, floor 64 KiB, read at call time (`spine_api/product_b_events.py`, `_max_store_bytes`).
- Rotation bounds the O(N) dedupe scan (scan covers the current segment only) and bounds unauthenticated write-amplification.
- Documented trade-off: after rotation, dedupe and KPI reads (`list_events`, `compute_kpis`) cover the current segment; the `.1` file preserves raw history for forensics.

## Remaining posture gaps (for the ops backlog)

1. **No age-based pruning.** Rotation is size-only; an old `.1` segment lives forever. Fold an age check (>180d, per EX-02 policy) into the future TTL job.
2. **Single-generation rotation.** Repeated rotation overwrites `.1`; that is intentional (bounded disk) but means analytics history is ~2 segments deep. If longer horizons are ever needed, add dated segments + a compaction step rather than raising MAX_STORE_BYTES silently.
3. **Lock scope.** `file_lock(cls.NORMALIZED_FILE)` serializes writers per process; multi-worker deployments (gunicorn/uvicorn workers) each hold OS locks — the lock is per-machine only. Acceptable for single-node fly.io (1 process per fly.toml); becomes a real defect only under multi-replica SQL-style scaling. Note for the long-term Postgres migration of this store.
4. **KPI definition drift risk.** Rotation changes the implicit KPI window (current segment ≈ last 10 MiB of events). Once EX-03's trusted emitter lands, KPI queries should pin an explicit time window instead of "whatever is in the file".

## Verification evidence (2026-09-08)

`tests/test_product_b_events_rotation.py` — 7 cases: no-rotation-under-cap, rotation-on-oversize (both segments), reads + dedupe after rotation, env floor/default/respect. Full checker batch 90/90 green.
