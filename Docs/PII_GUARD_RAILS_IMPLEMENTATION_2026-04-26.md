# PII Intake Guardrails: Implementation Report

**Date**: 2026-04-26  
**Scope**: Lightweight guardrails to prevent accidental storage of real user PII in plaintext JSON  
**Classification**: Dogfood-only. Real user data requires encryption/PostgreSQL before persistence.  

---

## 1. What Was Built

### 1.1 New Module: `src/security/privacy_guard.py`

A lightweight, non-ML PII guard with simple high-signal heuristics.

**Core principle**: Block persistence of real-user trip data in plaintext JSON when in `dogfood` mode.
- `dogfood` (default): Blocks trips with email, phone, freeform text, or medical keywords.
- `beta`: Allows all data (encryption is expected to be configured before activation).
- `production`: Allows all data.

**Heuristic checks (checked in order, 2-levels deep only):**

| Check | Pattern | Sensitivity |
|-------|---------|-------------|
| `fixture` allowlist | `fixture_id` or `source` matching `fixture`, `seed`, `test`, `demo`, `synthetic` | Bypass all checks |
| Email regex | `[a-z0-9._%+-]+@[domain]` | Always block in dogfood |
| Phone regex | `+91\s?\d{5}\s?\d{5}` or 10+ digits | Always block in dogfood |
| Freeform fields | `raw_note`, `freeform_text`, `content`, `notes`, `message`, `text`, `user_note`, `comment`, `description`, `feedback`, `additional_info`, `special_requests`, `medical_notes`, `dietary_restrictions` | Block if >10 chars |
| Medical keywords | `diabetic`, `wheelchair`, `mobility`, `allerg`, `asthma`, `heart`, `bp`, `pregnant` | Always block in dogfood |

**Restriction**: Checks only top-level + one sub-level (`max_depth=2`).
- `notes` → checked
- `raw_input.text` → checked
- `extracted.facts.text` → checked
- `analytics.review_metadata.notes` → **NOT checked** (3+ levels deep)

This prevents false positives on internal system fields that happen to share leaf names.

### 1.2 Integration Points

| Store | Method | Guard Action |
|-------|--------|--------------|
| `TripStore` | `save_trip()` | Calls `check_trip_data()` before write |
| `TripStore` | `update_trip()` | Calls `check_trip_data()` before merge |
| `save_processed_trip()` | Indirectly via `TripStore.save_trip()` | Already guarded |

**Note**: `OverrideStore`, `AuditStore`, `TeamStore`, `AssignmentStore` are NOT guarded because:
- `OverrideStore` stores operational flags (not PII)
- `AuditStore` stores system events (controlled fields)
- `TeamStore` is for agent accounts (self-managed)
- `AssignmentStore` is operational metadata

### 1.3 Environment Variable

```bash
DATA_PRIVACY_MODE=dogfood    # Default — blocks real user data
DATA_PRIVACY_MODE=beta       # Allows real data (encryption expected)
DATA_PRIVACY_MODE=production # Allows real data
```

### 1.4 Warning Docstring on TripStore

```python
class TripStore:
    """
    WARNING: TripStore persists plaintext JSON. Real user PII is blocked
    in dogfood mode by the privacy guard. Before storing real user data,
    enable encryption or migrate to PostgreSQL.
    """
    ...
```

---

## 2. Test Coverage

`tests/test_privacy_guard.py` — 34 tests, organized by risk level:

| Test Class | Tests | Covers |
|-----------|-------|--------|
| `TestFixtureDataAllowed` | 4 | Fixture IDs (`clean_family_booking`, `vague_lead`) pass |
| `TestRealUserDataBlocked` | 9 | Email, phone, freeform, medical blocked |
| `TestBenignDataAllowed` | 4 | Empty trips, structured data, short notes allowed |
| `TestHeuristicDetails` | 10 | Unit tests for each detector function |
| `TestGuardOnTripStore` | 5 | Save/update blocked in dogfood, allowed in beta/production |
| `TestDefaultMode` | 1 | Default is `dogfood` |

**Full suite status after guardrails**: 760 passed, 13 skipped, 2 pre-existing guard errors

---

## 3. Files Changed

| File | Change |
|------|--------|
| `src/security/` | **New** directory with `__init__.py` + `privacy_guard.py` |
| `src/security/privacy_guard.py` | **New** — Guard logic, env var, checks, `PrivacyGuardError` |
| `spine_api/persistence.py` | `TripStore.save_trip()`: added `check_trip_data()` call + privacy docstring |
| `spine_api/persistence.py` | `TripStore.update_trip()`: added `check_trip_data()` call + privacy docstring |
| `tests/test_privacy_guard.py` | **New** — 34 tests |
| `tests/conftest.py` | `reset_data_privacy_mode()` autouse fixture |
| `Docs/PII_ASSESSMENT_2026-04-26.md` | Updated with guardrails section |

---

## 4. Behavior Matrix

| Scenario | Dogfood | Beta | Production |
|----------|---------|------|------------|
| Fixture trip save | ✅ Allowed | ✅ Allowed | ✅ Allowed |
| Real user trip with email | ❌ Blocked + error | ✅ Allowed | ✅ Allowed |
| Real user trip with phone | ❌ Blocked + error | ✅ Allowed | ✅ Allowed |
| Real user trip with freeform notes | ❌ Blocked + error | ✅ Allowed | ✅ Allowed |
| Real user trip with medical data | ❌ Blocked + error | ✅ Allowed | ✅ Allowed |
| Structured trip (no PII) | ✅ Allowed | ✅ Allowed | ✅ Allowed |
| `analytics.review_metadata.notes` | ✅ Allowed (deep field) | ✅ Allowed | ✅ Allowed |

---

## 5. What Is NOT Guarded

| What | Why |
|------|-----|
| `CanonicalPacket.raw_note` persisted | Guard checks for it — blocks if present |
| `SourceEnvelope.content` persisted | Guard checks for it — blocks if >10 chars |
| Deeply nested fields | `max_depth=2` prevents false positives |
| `TeamStore` | Self-managed agent profiles |
| `AuditStore` | System-generated operational logs |
| `DecisionCacheStorage` | Algorithmic outputs only |

---

## 6. Current Classification

**After guardrails**: Classification **A+** — Dogfood-safe with active barriers.

Before guardrails:
- Classification **A** — Dogfood-safe for now, but "the codebase does not currently have guardrails to prevent this [real user data from entering]."

After guardrails:
- Classification **A+** — Dogfood-safe with explicit guardrails preventing accidental real user data storage.
- 222 existing fixture trips unaffected.
- Email/phone/freeform/medical data will raise a clear error if anyone attempts to save it.

---

## 7. Remaining Upgrade Triggers

| Condition | New Classification | Trigger Action |
|-----------|-----------------|---------------|
| First real user trip attempted | **B** | `PrivacyGuardError` raised → user sees "Enable encryption/migration before storing real user data" |
| Explicit `DATA_PRIVACY_MODE=beta` | **B** | Admin must actively set env var — signals readiness |
| 10+ real trips persisted | **C** | PostgreSQL migration becomes P0 |
| Health/mobility data entered | **D** | Immediate encryption required, regardless of trip count |

---

## 8. Decision Log

| Decision | Rationale |
|----------|-----------|
| `max_depth=2` for field checks | Prevents false positives on `analytics.review_metadata.notes` while catching `raw_text` and `extracted.facts.text` |
| Short text (<=10 chars) ignored | Prevents flagging single-word labels like "notes" or short keys |
| Dogfood is default | Fails closed — real data cannot enter unless admin explicitly opts in |
| No Guard on `TeamStore` | Agent accounts are self-managed and not user PII |
| No Guard on `AuditStore` | System logs do not contain user-submitted freeform text |

---

## 9. Limitations (Explicit)

1. **Not a PII detection model**: Uses simple regex + keyword lists. False negatives possible (e.g., "my cell is 9823 1234" without country code).
2. **Not a compliance framework**: GDPR/CCPA not addressed.
3. **Does not encrypt**: Only blocks; encryption is a separate work unit.
4. **Does not migrate**: PostgreSQL migration is a separate work unit (P1, triggered on first real user).
5. **Beta/production mode allows all data**: Intentional — admin must consciously switch. Guard is not a substitute for actual security controls.

---

*Date: 2026-04-26*
*Full suite: 760 passed, 13 skipped, 2 pre-existing guard errors*
