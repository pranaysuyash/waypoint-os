# R-15 — PII Guard Default: Fail-Open vs Fail-Closed in Production

**Date:** 2026-08-31 · **Finding:** R-15 (Persona Council Audit, `PERSONA_COUNCIL_MASTER_AUDIT_2026-08-29.md`)
**Source file:** `src/security/privacy_guard.py`
**Register:** `Docs/review/FINDINGS_REGISTER_2026-08-29.md` (R-15 row → ✅ FIXED 2026-08-31)
**Doctrine:** §1 (reasoning survives; claim corrected), §2 (evidence tiers), §3 (T1–T5),
§5 (one canonical source — this doc is the single record for the R-15 decision)

---

## 1. TL;DR

R-15 was filed as *"PII guard is fail-open in prod; Layer 2 is fail-closed. Which default?"*
Investigation shows the premise was **partly wrong**:

- ✅ **"Fail-open in prod"** — true. `check_trip_data()` returns at the gate (old
  `:484`) before any scan, in both beta and production.
- ❌ **"Layer 2 is fail-closed"** — **misleading.** The fail-closed `RuntimeError` in
  `_get_nlp_model()` is **unreachable dead code**: the gate bails before Layer 2 is
  ever loaded. The Layer 2 that *actually executes* (only in dogfood) is **fail-open**.
  The "fail-closed" existed only in comments and unreachable branches — a false sense
  of protection.

The real defect is a **contradiction between two defaults, one of which is dead code**,
plus a **silent no-op** in production (no log, no scan) that removes PII protection
exactly when the store is misconfigured to plaintext.

**Decision (first-principles, doctrine-aligned):** the guard is the safety net for the
*plaintext file store*, not the production encryption boundary. Therefore:

| Mode / store | Posture | Rationale |
|---|---|---|
| dogfood | **FAIL-CLOSED** (block real PII) | plaintext JSON store, no encryption/RLS |
| production + plaintext file store (`file`/`json`) | **FAIL-CLOSED** (block) | boundary absent → guard must substitute |
| production + SQL/Postgres (`sql`/`postgres`/`postgresql`) | **FAIL-OPEN but AUDITED** | encryption/RLS is the real boundary; never block (false-positive outages) |
| beta (any store) | **FAIL-OPEN but AUDITED** | relaxed staging contract (unchanged from original intent) |

Layer 2 (SpaCy) is now **consistently fail-open** everywhere — it is a best-effort
enhancement, never the boundary control.

---

## 2. Investigation — what the code actually does (verified by read)

`check_trip_data(trip_data)` is wired into the real write path at **8 sites** in
`spine_api/persistence.py` (`save_trip` @291/807, updates @409/442/486/1051/1121/1187/1256),
so it is reachable in production. Its old body:

```python
# privacy_guard.py (before)
def check_trip_data(trip_data):
    if not is_dogfood_mode():
        return                      # ← bare return: no scan, no log, in beta AND prod
    reason = _is_likely_real_user_data(trip_data)
    if reason:
        raise PrivacyGuardError(...)
```

- **dogfood:** full scan runs (Layer 1 regex + Layer 2 NER) → blocks on real PII.
- **beta / production:** returns immediately. Zero Layer 1, zero Layer 2, **zero log**.
  The module docstring claimed it "still logs warnings" — it did **not** (doc/code drift,
  already acknowledged in `IMPLEMENTATION_PLAN_2026-08-29.md:2.5`).

The Layer 2 loader (old):

```python
# privacy_guard.py (before) — _get_nlp_model()
except ImportError:
    if _data_privacy_mode() == "production":
        raise RuntimeError("...NLP Layer 2 is required for fail-closed PII scanning...")
    log.warning("...NLP Layer 2 disabled...")
except OSError:
    if _data_privacy_mode() == "production":
        raise RuntimeError("...en_core_web_sm model not found...")
    log.warning("...disabled...")
```

This `RuntimeError` is **never reached** in production because `check_trip_data` bails at
the gate before `_is_likely_real_user_data` → `_nlp_scan_for_person_entities` →
`_get_nlp_model` is invoked. In the only mode where Layer 2 runs (dogfood), the loader
**warns + returns `None`** (fail-open). So the reachable behavior is fail-open at every
level; the fail-closed code is dead.

---

## 3. The dangerous gap underneath

The fail-open is **unconditional**: `DATA_PRIVACY_MODE=production` makes the guard a
silent no-op *regardless of whether encryption/RLS is actually in place*. If production is
pointed at the **plaintext file store** (or `ENCRYPTION_KEY` is missing), real traveler
PII — including **medical/mobility data** (the guard explicitly flags those keywords) —
lands in plaintext JSON with **zero protection and zero log**. The guard's own purpose
(docstring: "don't put real PII in plaintext") is abandoned precisely in the misconfigured
case where it matters most.

`TripStore._backend()` (`spine_api/persistence.py:1425`) is already fail-closed for
`ENVIRONMENT ∈ {production, staging}` with an unset/non-SQL backend — so a *correctly
configured* prod deploy never reaches the guard with a plaintext store (it raises earlier).
The realistic gap is `DATA_PRIVACY_MODE=production` + `TRIPSTORE_BACKEND=file` while
`ENVIRONMENT` is not production (a "prod-mode" flag pointed at a plaintext store).

---

## 4. First-principles analysis — which default should hold?

- **Dogfood fail-closed** is correct and kept: the store is plaintext; blocking is the
  only protection.
- **Blanket fail-closed in production** is wrong for a live booking system: a heuristic
  PII scanner on false positives would block legitimate saves (availability outage).
- **Blanket fail-open** (the old behavior) is wrong because it abandons protection on
  misconfiguration.
- **Correct default:** fail-open is acceptable **only when the real boundary holds**
  (SQL/Postgres + RLS). When the boundary is absent (plaintext store), the guard must
  **substitute** and fail-closed. This satisfies both availability (don't block legit
  prod writes when encrypted) and protection (never silently persist PII to plaintext).

---

## 5. Change (three parts, all in `src/security/privacy_guard.py`)

### 5.1 Layer 2 consistently fail-open (removed dead code)
`_get_nlp_model()` no longer raises in production. If `spacy`/`en_core_web_sm` is
unavailable it logs a warning and returns `None`; the guard degrades to Layer 1. The
unreachable production `RuntimeError` ("required for fail-closed PII scanning") is gone —
it created a false sense of protection and would only crash prod if the gate were later
"fixed" without noticing the dead branch.

### 5.2 Gate is now observable, not a silent no-op
`check_trip_data()` factored Layer 1 into `_scan_layer1()` (regex email/phone/freeform/
medical, no model). In the safe config (prod+SQL / beta) it runs `_scan_layer1` and
**logs an `AUDIT` warning** for PII-shaped data but never raises. This closes
`IMPLEMENTATION_PLAN_2026-08-29.md:2.5` (silent no-op is now impossible).

### 5.3 Misconfiguration failsafe (the load-bearing part)
New helper `_uses_plaintext_store()` mirrors `TripStore._backend()`'s unsafe branch
(`file`/`json`). When `DATA_PRIVACY_MODE=production` **and** the store is plaintext, the
guard **fails closed** — it runs the full scan and raises `PrivacyGuardError` on real PII,
exactly as in dogfood. An *unset* backend is deliberately **not** treated as plaintext
(LEFT to `TripStore._backend()`'s own environment enforcement) so legitimate dev/test runs
that leave it unset are not blocked.

```python
# privacy_guard.py (after)
if is_dogfood_mode():
    reason = _is_likely_real_user_data(trip_data)
    if reason:
        raise PrivacyGuardError(_block_message(reason))
    return

if _data_privacy_mode() == "production" and _uses_plaintext_store():
    reason = _is_likely_real_user_data(trip_data)
    if reason:
        log.error("privacy_guard: DATA_PRIVACY_MODE=production but TRIPSTORE_BACKEND "
                  "is a plaintext file store. Refusing to persist real-user PII "
                  "(fail-closed).")
        raise PrivacyGuardError(_block_message(reason))
    return

# prod+SQL / beta: observable, non-blocking audit (Layer 1 only).
reason = _scan_layer1(trip_data)
if reason:
    log.warning("privacy_guard: AUDIT — real-PII-shaped data persisted in %s mode "
                "(not blocked; encryption/RLS is the boundary): %s",
                _data_privacy_mode(), reason)
```

`_block_message()` is mode-agnostic (no longer says "dogfood mode", which would be wrong
for the production+plaintext case).

---

## 6. Tests added (`tests/test_privacy_guard.py::TestR15ProductionDefaults`)

| Test | Asserts |
|---|---|
| `test_production_with_plaintext_store_blocks_real_pii` | prod + `file` → `PrivacyGuardError` |
| `test_production_with_json_store_blocks_real_pii` | prod + `json` → `PrivacyGuardError` |
| `test_production_with_sql_store_audit_only` | prod + `sql` → no raise, `AUDIT` logged |
| `test_production_with_postgres_store_audit_only` | prod + `postgres` → no raise, `AUDIT` logged |
| `test_production_with_unset_backend_audit_only` | prod + unset → no raise, `AUDIT` logged |
| `test_beta_with_plaintext_store_audit_only` | beta + `file` → no raise, `AUDIT` logged |
| `test_nlp_loader_never_raises_in_production` | Layer 2 never raises `RuntimeError` in prod |

Also updated `test_real_data_save_blocked` (was asserting the old `"dogfood mode"` string
in the error message) to assert `"plaintext"`, the stable concept in the new message.

**Result:** `tests/test_privacy_guard.py` → **55 passed** (7 new + 48 existing). The
production+plaintext block and the prod+SQL/beta audit paths are both covered.

---

## 7. Evidence tiers

- **Verified by direct read:** gate no-op at old `:484`; `_get_nlp_model` fail-closed
  branch unreachable in prod; 8 production call sites; `_backend()` safe set
  `{sql, postgres, postgresql}`; module docstring drift ("still logs warnings").
- **Verified by test:** new `TestR15ProductionDefaults` (7 passed) proves each posture.
- **Inferred:** no other production path re-enables the scan (grep: `check_trip_data`
  only called from `persistence.py` + tests).
- **Uncertain:** whether any live deployment actually runs prod with the file backend —
  would need a runtime probe of `TRIPSTORE_BACKEND` in the target environment. The failsafe
  now makes that case safe regardless.

---

## 8. Self-correction (PER-0164)

In the discussion preceding this fix I initially repeated the filed premise that
"Layer 2 is fail-closed in production." Reading the call graph proved it is **unreachable
dead code**. I corrected the framing before implementing, and the fix removes the dead
branch rather than relying on it. Recorded here so the reasoning (not the original claim)
survives.

---

## 9. Follow-ups / open

- **A-22-class decision still open elsewhere:** public proposal/group token resolution has
  no agency context (see R-03 §5.3) — unrelated to R-15 but same "public read path" theme.
- **Log volume:** the prod+SQL `AUDIT` warning fires on every trip with freeform/PII-shaped
  text. Intended observability; tune to `INFO` or sample if noisy in production.
- **ENCRYPTION_KEY:** not yet required by the guard's failsafe (only the backend is), to
  avoid over-blocking `beta`. `src/security/encryption.py:23` already fails closed on a
  missing key in production, so the boundary is still enforced — just by a different module.
