# Customer Memory Durable Store — Exploration & Implementation Plan (FND-0060 residual)

**Date:** 2026-09-15
**Finding:** FND-0060 (P1, deferred) — residual: "customer memory still backs onto a legacy
process-local dict instead of a durable agency-scoped store".
**Trigger for now:** the memory-slot stream landed the durable 5-tier `MemoryStore` today;
the profile-level path was the remaining non-durable surface.

---

## 1. Live-truth map (observed, not assumed)

### Current storage layers in `spine_api/routers/customer_memory.py`

| Layer | Backing | Durable? | Agency-scoped? | Used for |
|---|---|---|---|---|
| `CUSTOMER_MEMORY_STORE` (legacy dict, line 46) | process-local `Dict[(agency_id, customer_id), profile]` | ❌ lost on restart | ✅ (S-08 composite key) | The `CustomerPreferenceProfile` identity + preference view: `/remember` upsert, `/memory` lookup, `/hydrate-trip` identity + fallback chips, GDPR X-14 propagation |
| `MemoryStore` (`src/memory/store.py`, landed 2026-09-15) | file JSONL `data/memory/memory_store.jsonl`, agency-keyed cache | ✅ survives restarts (single-process; whole-file rewrite) | ✅ agency param on every call | 5-tier facts (`/remember` fact ingest, `/memory/ingest|query|entity`, GDPR tombstones) |

Dict touchpoints (all in `customer_memory.py`):
- `_find_customer_profile` (line 151): linear scan by (agency, normalized_email → phone → name).
- `/remember` (line 259): `CUSTOMER_MEMORY_STORE[(agency_id, cust_id)] = profile` — the ONLY
  durable-looking write of the identity/preference profile, and the only write lost on restart.
- `/hydrate-trip` (line 371): profile is the fallback chip source (`memory:profile`) and identity resolver.
- `/memory/forget` (lines 575-600): GDPR X-14 propagation — pops exact key, then scans the dict
  for same-identity duplicates (normalized_email/phone/name) within the agency.

### Tests coupled to the dict
- `tests/test_customer_memory_agency_partition.py` — asserts dict key structure (tuples), cross-agency
  read/write/forget isolation. Uses arbitrary agency strings + auth bypass.
- `tests/test_gdpr_purge_propagation.py` — seeds the dict directly, asserts X-14 propagation and
  agency scoping. Builds a bare FastAPI app with `get_current_agency_id` overridden.

### Already-durable and deliberately out of scope
- 5-tier facts (dietary/seating/room) already go to `MemoryStore` on `/remember`.
- **Passport fields are deliberately NOT durably ingested** (in-code contract): 30-day post-trip
  retention SLA (`RetentionCategory.PASSPORT_MRZ`); persisting them into long-half-life memory
  would be a retention violation by design.

---

## 2. Root cause and design decision

**Root cause:** the profile view predates the durable store; when the 5-tier MemoryStore landed,
the identity/preference profile was left on the process-local dict "for backwards compatibility" —
the FND-0060 residual.

**Chosen design:** a real SQL table, `customer_memory_profiles`, following the canonical
tenant-table pattern (same as `booking_confirmations`):

- `agency_id` FK → `agencies.id` ON DELETE CASCADE, **RLS enabled** with the two standard
  `waypoint_rls_select` / `waypoint_rls_all` policies (`app.current_agency_id` session GUC).
- Unique constraint `(agency_id, customer_id)` — the upsert key.
- Lookup indexes on `(agency_id, normalized_email)` and `(agency_id, normalized_phone)`.
- Access exclusively through `rls_session(agency_id)` with **parameter-bound** ORM queries
  (no string-composed SQL — Mimosa gate constraint).
- GDPR Article 17: hard DELETE of the exact row plus every same-identity row in the agency
  (X-14 propagation preserved in SQL), alongside the existing `MemoryStore.forget_entity_gdpr`
  tombstones and audit events.

**Retention decision (deliberate):** `passport_country` / `passport_expiry` are **NOT columns**
on the durable row. The write response still echoes them (request-scoped, same-session), but they
do not survive restart — the 30-day SLA makes durable passport storage a violation by design.
Documented in-code where the old dict comment lived.

**Why SQL and not the file-backed MemoryStore:** the profile is identity PII with GDPR erasure
obligations; Postgres gives RLS tenant isolation, FK CASCADE, transactional erasure, and removes
the whole-file-rewrite multi-process hazard for the highest-sensitivity surface. The file-backed
MemoryStore remains the 5-tier fact lane (separate concern, own durability track).

**Behavior changes (honest, contract-visible):**
1. Profiles survive restarts (the fix).
2. Passport fields no longer survive restart (retention SLA aligned; previously they "survived"
   only accidentally because the process never died).
3. Multi-worker deployments stop losing/overwriting profiles through divergent process caches.

**Supersession:** `CUSTOMER_MEMORY_STORE` and the dict-scan `_find_customer_profile` are removed
after this migration (zero unique behavior — the X-14 propagation and S-08 partition semantics are
reimplemented in SQL and covered by the rewritten tests). In-code comment block replaced.

---

## 3. Implementation checklist

- [ ] Model `CustomerMemoryProfile` (`spine_api/models/tenant.py`)
- [ ] Migration `add_customer_memory_profiles` (table + indexes + unique + RLS policies),
      chained on `add_proposal_access_tokens`
- [ ] Router: SQL-backed `_find_customer_profile_db`, `/remember` upsert, `/memory` lookup,
      `/hydrate-trip` identity/fallback, `/memory/forget` X-14 propagation in SQL
- [ ] Delete legacy dict + dict-scan helper; update in-code comments
- [ ] Rewrite `test_customer_memory_agency_partition.py` (SQL store, materialized agencies)
- [ ] Rewrite `test_gdpr_purge_propagation.py` (X-14 propagation on SQL, materialized agencies)
- [ ] Verify `test_customer_memory_router.py` + memory-slot suite still green
- [ ] FND-0060 close/note with evidence

## 4. Verification plan

- New/rewritten suites: partition, purge propagation, router contract — green.
- Full backend suite green (no regressions in memory-slot stream).
- Ruff clean on all touched files.

## 5. Residuals / explicit non-goals

- 5-tier `MemoryStore` file-JSONL → SQL migration is a SEPARATE concern (own finding-worthy track);
  this work covers the identity/preference profile only.
- Passport durable retention (with purge job) would need a ratified SLA mechanism — not designed here.
