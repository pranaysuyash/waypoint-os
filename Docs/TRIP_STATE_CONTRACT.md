# Trip State Contract — Implementation Plan

**Status:** Phase 1 implemented, Phase 2–4 planned
**Created:** 2026-05-02
**Scope:** Persistence repair, encryption, stage/readiness model, ops panel

---

## Context

The pipeline produces 9 compartments of state, but only 4 are persisted to the database. After a page refresh, the UI shows a different product than what the pipeline actually computed. This is a state-contract bug, not a missing-field bug.

The fix is not "add five JSON columns." It is: define the persisted trip state contract, implement it, encrypt PII-bearing compartments, and add regression tests for refresh parity.

---

## Compartment Registry

Every field the pipeline emits, its classification, and persistence behavior:

| Field | Producer | Consumer | Stages | PII Class | DB Column | Encrypted | Hydrated on Refresh | In Logs? | Frontend Exposure |
|:---|:---|:---|:---|:---|:---|:---|:---|:---|:---|
| `packet` | ExtractionPipeline | PacketPanel, all panels | all | Medium (names, phones) | `extracted` | Yes | Yes | Redacted | Full |
| `validation` | NB01CompletionGate | PacketPanel, DecisionPanel | all | None | `validation` | No | Yes | Yes | Full |
| `decision` | NB02JudgmentGate | DecisionPanel, StrategyPanel | all | None | `decision` | No | Yes | Yes | Full |
| `strategy` | build_session_strategy() | StrategyPanel | shortlist+ | None | `strategy` | No | Yes | Yes | Full |
| `traveler_bundle` | build_traveler_safe_bundle() | OutputPanel, customer | proposal+ | Low (names in context) | `traveler_bundle` | Yes | Yes | Redacted | Customer-safe |
| `internal_bundle` | build_internal_bundle() | OutputPanel, agent | proposal+ | High (margin, vendor, ops) | `internal_bundle` | Yes | Yes (agent only) | No | Agent-only |
| `safety` | check_no_leakage() | SafetyPanel | all | Medium (may flag medical/visa) | `safety` | Yes | Yes | Redacted | Agent-only |
| `fees` | calculate_trip_fees() | OutputPanel, future OpsPanel | proposal+ | Medium (commercial) | `fees` | Yes | Yes | No | Agent-only |
| `frontier_result` | run_frontier_orchestration() | FrontierDashboard | all | High (sentiment, intel) | `frontier_result` | Yes | Yes | No | Agent-only |
| `booking_data` | (future) Agent/Customer | OpsPanel | booking | Critical (passports, DOB) | *(not yet added)* | Yes | Lazy (OpsPanel only) | No | Agent + owner |

### Authority hierarchy
```
Docs/TRIP_STATE_CONTRACT.md  →  human-readable authority
contract.py / packet_models.py / validation.py  →  executable authority
refresh parity tests  →  behavioral authority
```

---

## Codebase Reality (verified)

### Current persistence gap

Both `save_processed_trip` calls in `server.py` (lines 1017-1034 and 1079-1095) pass dicts with only: `packet`, `validation`, `decision`, `strategy`, `meta`. Five compartments are computed but never persisted.

### Existing infrastructure
- **Encryption**: Fernet (AES-128-CBC) in `src/security/encryption.py`. Dual model: blob encryption for private compartments, recursive PII-key encryption for shared fields.
- **Audit**: `RunLedger` = per-run execution trace (file-based). `AuditStore` = trip lifecycle events (file-based). RunLedger for runs, AuditStore for business events.
- **Stage model**: `CanonicalPacket.stage` has `discovery`/`shortlist`/`proposal`/`booking`. Validation has `INTAKE_MINIMUM` (2 fields) and `QUOTE_READY` (6 fields).

### Encryption model

Two tiers, enforced by `_encrypt_field_for_storage` / `_decrypt_field_from_storage`:

| Tier | Fields | Method | Stored shape |
|:---|:---|:---|:---|
| Private blob | `traveler_bundle`, `internal_bundle`, `safety`, `fees`, `frontier_result` | Entire JSON → single Fernet token | `{"__encrypted_blob": true, "v": 1, "ciphertext": "..."}` |
| PII-key redaction | `extracted`, `raw_input` | Recursive: encrypt string values whose key is in `_PII_FIELDS` | Same JSON structure, PII values replaced with tokens |
| None | `validation`, `decision`, `strategy`, all scalar fields | Plaintext | As-is |

### Persistence paths

| Path | Compartments persisted | Reason |
|:---|:---|:---|
| Authenticated `/run` (normal + partial) | All 9 | Full agent pipeline |
| Public checker `/api/public-checker/run` | 5 only (`packet`, `validation`, `decision`, `strategy`, `meta`) | Customer-facing, no agent-only private compartments |
| `update_trip()` | Same encryption as `save_trip()` via unified helper | Prevents bypass |

### Flat JSON vs. split tables

**Stay flat for now.** Single `trips` table with encrypted JSON columns.

Exit criteria for splitting into `trip_state`, `trip_private_state`, `booking_data`:
- Real PII pilot begins
- Multiple roles/permissions need field-level access
- Reporting/querying across private state
- Customer-facing document collection
- Audit/compliance obligations

---

## Implementation Phases

### Phase 1: Persistence Repair + Encryption (one merge) — IMPLEMENTED

All 5 missing compartments fixed together. Dual encryption model: blob encryption for private compartments, PII-key encryption for shared fields.

**Status:** Code complete. All 5 blockers from ChatGPT review resolved:
1. Private compartment blob encryption (not just key-level PII)
2. `update_trip()` uses same unified encryption helper as `save_trip()`
3. Public checker reduced persistence contract documented
4. BFF adapter maps all compartments including `strategy`, `traveler_bundle`, `internal_bundle`
5. `resetAll()` clears `result_fees`
6. Sentinel encryption tests verify no plaintext in encrypted storage

**What was done:**
- `spine_api/models/trips.py`: Added `frontier_result`, `fees` columns
- `spine_api/persistence.py`: Dual encryption model (`_PRIVATE_BLOB_FIELDS` + `_PII_KEY_FIELDS`), unified `_encrypt_field_for_storage` / `_decrypt_field_from_storage`, `_to_dict` / `save_trip` / `update_trip` all use same helpers
- `spine_api/server.py`: Both authenticated save dicts include all 5 missing compartments; public checker documented as reduced contract
- `alembic/versions/add_frontier_result_and_fees_to_trips.py`: Migration
- `frontend/src/lib/api-client.ts`: Added `frontier_result` to Trip type
- `frontend/src/lib/bff-trip-adapters.ts`: Maps `strategy`, `traveler_bundle`, `internal_bundle`, `fees`, `frontier_result`
- `frontend/src/stores/workbench.ts`: `resetAll()` clears `result_fees`
- `frontend/src/components/workspace/FrontierDashboard.tsx`: Rewritten to read from store (still parked — not mounted)
- `tests/test_state_contract_parity.py`: 32 tests covering blob encryption, PII-key encryption, sentinel tests, FileTripStore parity, update_trip parity, SQL raw-row sentinel (full save_trip path)

**Specialty Knowledge Salvage (Phase 1.5):**
- `src/intake/orchestration.py`: Added `specialty_knowledge` to `decision.rationale["frontier"]` dict
- `frontend/src/app/(agency)/workbench/SafetyTab.tsx`: Added "Special Handling Checklist" section (niche, urgency badge, checklists, compliance, safety notes)
- `frontend/src/app/(agency)/workbench/page.tsx`: Added Safety Review tab (SafetyTab now mounted)
- `tests/test_specialty_knowledge_salvage.py`: 14 tests (detection, serialization, rationale shape)

**Not yet done (separate PRs):**

### Phase 2: Stage/Readiness Model

**2.1 Add readiness tiers to validation.py**
File: `src/intake/validation.py`
```python
PROPOSAL_READY = QUOTE_READY + [
    "sourcing_route",
    "package_candidates",
    "suitability_flags",
]
BOOKING_READY = PROPOSAL_READY + [
    "traveler_identities",
    "primary_payer",
    "emergency_contacts",
    "document_ownership",
]
```

**2.2 Add readiness to CanonicalPacket**
File: `src/intake/packet_models.py`
```python
readiness: Dict[str, bool] = field(default_factory=dict)
suggested_next_stage: Optional[str] = None
```

**2.3 Stage transitions via AuditStore**
Extend existing `AuditStore` (persistence.py:745-815) for business lifecycle events:
```json
{
  "type": "stage_transition",
  "trip_id": "...",
  "from": "discovery",
  "to": "shortlist",
  "trigger": "manual",
  "reason": "quote_ready=true; decision=PROCEED_TRAVELER_SAFE",
  "readiness": {"intake_minimum": true, "quote_ready": true, "proposal_ready": false, "booking_ready": false},
  "actor": "agent",
  "user_id": "..."
}
```
RunLedger = per-run execution trace. AuditStore = durable business events.

**2.4 UI: stage advancement banner**
In PacketPanel or DecisionPanel:
```
Ready to move to Shortlist
Reason: MVB complete, decision=PROCEED_TRAVELER_SAFE
[Advance to Shortlist]
```
Button triggers explicit stage transition via AuditStore. Never auto-advance.

### Phase 3: OpsPanel (stage-gated)

Named "Ops" not "Booking" — room for documents, payments, confirmations, emergency later.

Visible only when:
```
stage === "proposal" || stage === "booking" || booking_blockers.length > 0
```
NOT shown merely because `suggested_next_stage = proposal`.

**3.1 Create OpsPanel.tsx**
File: `frontend/src/components/workspace/panels/OpsPanel.tsx` (new)
V1 scope: **Booking Readiness only**
```
What is blocking this trip from being safely booked?
[x] Traveler identities — 2 of 3 collected
[ ] Emergency contacts — missing
[x] Payer identified — yes
[ ] Passport validity — not checked
[ ] Documents collected — 0 of 4
```

**3.2 Wire into workbench**
File: `frontend/src/app/(agency)/workbench/page.tsx`
Add as conditional tab.

**3.3 Gate passport extraction by stage**
File: `src/intake/extractors.py`
Wrap `_extract_passport_visa` to only run at `proposal`/`booking` stage.
At discovery: extract only `visa_concerns_present: bool`.

### Phase 4: Booking Data (future)

Not in this round. Design decisions locked:
- `booking_data` encrypted JSON column on `trips` — added when first write path exists
- Separate from `canonical_packet` (planning vs. execution state)
- Phase 1 of product: agent-assisted entry
- Phase 2 of product: customer self-service collection link
- Booking data is lazy-hydrated, not global store

---

## Design Principles

1. **Planning state helps the agent think; booking state lets the agency execute; private state must be protected. Do not mix them.**
2. **Persist every first-class compartment emitted by pipeline. Test refresh parity.**
3. **Auto-compute readiness, manual-confirm stage transitions. Never silently mutate business stage.**
4. **Encrypt by risk of re-identification, not field name.**
5. **Flat JSON is an implementation tactic, not the architecture. The architecture is the contract + refresh parity + explicit PII boundaries.**
6. **Ship thin, iterate.** OpsPanel starts with Booking Readiness only.
7. **RunLedger for execution traces. AuditStore for business lifecycle events.**

---

## File Change Summary

| File | Change | Phase |
|:---|:---|:---|
| `spine_api/models/trips.py` | Add `frontier_result`, `fees` columns | 1 |
| `spine_api/persistence.py` | Update `_to_dict`, `save_trip`, `_build_processed_trip`, extend `_PII_FIELDS`, encrypt new compartments | 1 |
| `spine_api/server.py` | Add 5 missing fields to both save dicts | 1 |
| `alembic/versions/add_frontier_result_and_fees.py` | New migration | 1 |
| `frontend/src/app/(agency)/workbench/page.tsx` | Add `setResultFrontier`, `setResultFees` to hydration | 1 |
| `frontend/src/components/workspace/FrontierDashboard.tsx` | Read from store, remove hardcoded defaults | 1 |
| `src/intake/validation.py` | Add `PROPOSAL_READY`, `BOOKING_READY` tiers | 2 |
| `src/intake/packet_models.py` | Add `readiness`, `suggested_next_stage` | 2 |
| `src/intake/extractors.py` | Gate passport extraction by stage | 3 |
| `frontend/src/components/workspace/panels/OpsPanel.tsx` | New — Booking Readiness panel | 3 |

---

## Verification

1. **Phase 1**: `alembic upgrade head` → run pipeline → query DB (all 9 compartments present, encrypted fields not plaintext) → refresh workbench → full state survives
2. **Phase 2**: Submit discovery note → see readiness scores → manual stage advance → transition event in AuditStore
3. **Phase 3**: Set stage to proposal → OpsPanel appears → shows booking blockers
4. **Refresh parity test**: Automated test that runs pipeline, saves, reloads, asserts all compartments match
