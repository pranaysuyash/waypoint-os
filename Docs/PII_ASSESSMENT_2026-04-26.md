# PII Assessment Report: Waypoint OS

**Date**: 2026-04-26
**Scope**: JSON-backed stores and SQLite stores containing personal or sensitive data
**Classification Target**: Current deployment status (dogfood vs. production) and real-user readiness

---

## 1. JSON Stores Inventory

| Store | File Path | Data Format | Purpose | Used in Runtime? | Concurrency |
|---|---|---|---|---|---|
| **TripStore** | `data/trips/` (222 files) | JSON per trip | Stores trip facts, bundles, decision, strategy | Yes | `threading.Lock` + `fcntl.flock` |
| **AssignmentStore** | `data/assignments/assignments.json` | JSON dict | Agent-trip assignments | Yes | No lock |
| **AuditStore** | `data/audit/events.json` | JSON list (max 10k) | Audit log of system events | Yes | `threading.Lock` + `fcntl.flock` |
| **OverrideStore** | `data/overrides/per_trip/*.jsonl` | JSONL per-trip | Decision overrides (immutable log) | Yes | N/A (append-only) |
| **TeamStore** | `data/team/members.json` | JSON dict | Team member profiles | Yes | `threading.Lock` |
| **ConfigStore** | `data/config/pipeline.json`, `data/config/approvals.json` | JSON list | Pipeline stages, approval thresholds | Yes | `threading.Lock` |
| **DecisionCacheStorage** | `data/decision_cache/*.json` | JSON dict per type | Cached risk decisions | Yes | `threading.Lock` per file |
| **AgencySettings** (legacy) | `data/agency_default.json` | JSON (migrating to SQLite) | Agency settings | Migrated | None |
| **LLMUsageStore** | `data/guard/usage.db` | SQLite | Usage guard logs | Yes | SQLite WAL + `EXCLUSIVE` TXN |

## 2. Field Sensitivity Analysis

### 2.1 TripStore (`data/trips/*.json`)

**Facts extracted from actual 222 trip files:**

| Field | Example | Sensitivity |
|---|---|---|
| `destination_candidates` | `["Bali"]` | Non-sensitive (travel preference) |
| `destination_status` | `"definite"` | Non-sensitive |
| `party_size` | `4` | Sensitive (reveals family structure) |
| `traveler_plan` | `"nothing_booked"` | Non-sensitive |
| `budget_min`, `budget_max` | `300000` | Sensitive (financial data) |
| `origin_city` | `"Bangalore"` | Low sensitivity (general location) |
| `date_window` | `"March 15-20"` | Sensitive (travel dates = temporal PII) |
| `party_composition` | `"2 adults, 2 children"` | **High sensitivity** (reveals minors) |
| `special_needs` | *not found in current data* | **Critical if present** (health/mobility) |
| `phone`, `email`, `name` | *not found* | N/A |

**Current data status:**
- 222 trips analyzed, 0 contain freeform text field, 0 contain names, 0 contain phone/email.
- All trips have `fixture_id` present in `raw_input`, indicating test fixture data.

**Risk:** `TripStore` is currently **Low** because it stores synthetic data only, but the moment a real user submits data, it will contain:
- Travel dates (temporal profile)
- Family composition (potentially minors)
- Budget (financial)
- Explicit user notes (`raw_input.freeform_text`) — could contain ANYTHING

### 2.2 AssignmentStore

| Field | Sensitivity |
|---|---|
| `agent_name` | Low (internal synthetic name) |
| `trip_id` | Low (system ID, links to TripStore) |
| `agent_id` | Low (internal ID) |

### 2.3 TeamStore

| Field | Example | Sensitivity |
|---|---|---|
| `name` | `"Test User"` | Medium |
| `email` | `"test@example.com"` | **High** (PII identifier) |
| `role` | `"agent"` | Low |
| `capacity` | `5` | Low |

This is the **strongest PII indicator found in the system**.

### 2.4 AuditStore

| Field | Example | Sensitivity |
|---|---|---|
| `user_id` | `"system"` / `"seed"` | Low (internal IDs) |
| `trip_id` | `"trip_alpha_001"` | Low |
| `details.agent_name` | `"Agent Smith"` | Low (synthetic) |

### 2.5 OverrideStore

Empty. Will contain:
- `flag` (decision flag name)
- `reason` (text explaining the override)
- `agent_id`
- Sensitivity: Low-Medium (operational data).

### 2.6 DecisionCacheStorage

Contains cached algorithmic outputs: risk scores, feasibility classifications. No PII.

### 2.7 LLMUsageStore (SQLite)

Contains guard usage events: model, feature, status, estimated_cost. No PII.

## 3. Is PII Actually Confirmed?

### Names
- `TeamStore.members.json`: `"Test User"` (real person placeholder).
- `AssignmentStore`: `"Agent Smith"` (obvious synthetic).
- **No customer names. No traveler names. Zero names tied to trips.**

### Email
- `TeamStore.members.json`: `"test@example.com"` (placeholder).
- **No customer emails in any TripStore file.**

### Phone
- **Not found anywhere in data/ directory.**

### Travel Data
- **Travel dates**: Found in test fixtures only (e.g., "March 15-20"). Could be real itinerary dates.
- **Destination**: Found in test fixtures (e.g., "Bali") with synthetic IDs.
- **Budget**: Found in test fixtures only.
- **Party composition**: Found in test fixtures (synthetic "2 adults, 2 kids").

### Health/Mobility
- **Not found in any stored trip data.** `CanonicalPacket` *schema* has `suitability_flags` and `special_needs`, but current data files do not contain these populated.

## 4. Deployment/User Assumption

| Evidence | Status |
|---|---|
| Number of trip files | 222 |
| Number of trips with freeform text | 0 |
| Number of trips with names | 0 |
| Number of trips with email/phone/contact | 0 |
| Number of trips linked to fixtures | 222 |
| Number of non-fixture trips | 0 |
| Number of real customer records | **0** |
| Data path existence | `data/trips/` exists (generated during development/testing) |
| User data path | No frontend/API capturing real user submissions found |
| Ingestion mode | Appears to be test-driven intake (`raw_fixtures.py`) |

**Current Mode Classification:**
→ **Internal Dogfood with exclusively synthetic data**

## 5. Risk Classification per Store

| Store | Real Data? | PII Present? | Classify |
|---|---|---|---|
| TripStore | No | No (yet) | **LOW currently** |
| TripStore (future) | Will be | Will be | **HIGH when real** |
| AssignmentStore | No (synthetic) | No | **LOW** |
| AuditStore | No (system IDs) | No | **LOW-MEDIUM** |
| TeamStore | Yes (placeholder email) | Minimal | **MEDIUM** |
| OverrideStore | No (empty) | No | **LOW** |
| DecisionCacheStorage | No | No | **NONE** |
| LLMUsageStore | No | No | **NONE** |

## 6. Decision

**Classification**: **A. Dogfood-safe for now (with explicit warning)**

### 6.1 Why A, not B/C/D

- Real customer data == ZERO.
- Current data is 100% test generated via fixtures.
- `TeamStore` has placeholder data only.
- JSON storage is not currently a legal or operational concern *because there is no real user data*.

### 6.2 Conditions that would change classification

| Condition | New Classification | Trigger |
|---|---|---|
| First real user trip stored | Upgrade to **B** | Any real customer data |
| 10+ real trips or team members added | Upgrade to **C** | Volume threshold |
| Health/mobility/sensitive data entered | Upgrade to **D** immediately | Presence of special needs |
| Launch announced | Must be **B** before, **C/D** before GA | Milestone |

### 6.3 Required before real users

| Item | Priority | Reason |
|---|---|---|
| TripStore encryption | P0 | Will contain family composition, dates, budget, potentially free-form notes |
| PostgreSQL migration | P1 | Long-term for relational integrity, but not a blocker for small scale |
| TeamStore PII audit | P1 | Real agent names/emails will be stored |
| AuditStore retention policy | P2 | 10k events cap exists, but logs operational data on real trips |
| OverrideStore review | P2 | Not currently used |

## 7. Output Summary

- **Total JSON stores**: 8
- **Stores with confirmed PII**: 1 (`TeamStore` with placeholder email)
- **Stores at risk when real data enters**: 3 (`TripStore`, `TeamStore`, `AuditStore`)
- **Dogfood-safe for now**: Yes
- **Warning issued**: Yes — `TripStore` will hold sensitive data with even a single real customer interaction
- **Next Work Unit Recommendation**: Prepare a lightweight encryption layer for `TripStore` and `TeamStore` fields before beta/launch signoff

---

*Assessment based on: 222 trip files, 1 team member, 0 real customer records, 0 non-fixture trips.*

## 8. Privacy Guardrails (Implemented 2026-04-26)

See: `Docs/PII_GUARD_RAILS_IMPLEMENTATION_2026-04-26.md`

**Classification after guardrails: A+**  

The system now actively prevents real user data from accidentally entering plaintext JSON storage.

- `DATA_PRIVACY_MODE=dogfood` (default): Blocks persistence of real user data
- `DATA_PRIVACY_MODE=beta|production`: Allows, but admin must explicitly opt-in
- Guard is lightweight: regex heuristics (email, phone, medical keywords) + freeform field detection
- Checks are at `TripStore.save_trip()` and `update_trip()` boundaries
- 222 existing fixture trips unaffected — only `fixture_id` or `source: seed/test` trips pass the guard
- First attempt to save real user data results in clear error:  
  `"Real user trip data cannot be persisted in plaintext JSON in dogfood mode. Enable encryption/migration before storing real user data."`
