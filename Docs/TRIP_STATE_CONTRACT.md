# Trip State Contract — Implementation Plan

**Status:** Pre-implementation (finalized)
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
- **Encryption**: Fernet (AES-128-CBC) in `src/security/encryption.py`. Extensible via `_PII_FIELDS` set in `pine_api/persistence.py:315-337`.
- **Audit**: `RunLedger` = per-run execution trace (file-based). `AuditStore` = trip lifecycle events (file-based). RunLedger for runs, AuditStore for business events.
- **Stage model**: `CanonicalPacket.stage` has `discovery`/`shortlist`/`proposal`/`booking`. Validation has `INTAKE_MINIMUM` (2 fields) and `QUOTE_READY` (6 fields).

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

### Phase 1: Persistence Repair + Encryption (one merge)

All 5 missing compartments fixed together. Encryption included in same merge — never persist sensitive compartments plaintext.

**1.1 Add columns to Trip model**
File: `spine_api/models/trips.py`
```python
# After safety column (line 50):
frontier_result: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
fees: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
# traveler_bundle, internal_bundle already have columns (lines 48-49)
# safety already has column (line 50)
# NOTE: Do NOT add booking_data column yet — no write path exists
```

**1.2 Encrypt new PII-bearing columns**
File: `spine_api/persistence.py`
- Extend `_PII_FIELDS` set (line 315) with PII sub-keys from frontier_result, fees, safety, internal_bundle, traveler_bundle
- Apply `_encrypt_pii` / `_decrypt_pii` in `_to_dict()` and `save_trip()` for these columns

**1.3 Update _to_dict()** — add `frontier_result`, `fees` to serialization
File: `spine_api/persistence.py:374-399`

**1.4 Update save_trip()** — add `frontier_result`, `fees` to model_data
File: `spine_api/persistence.py:404-428`

**1.5 Update _build_processed_trip()** — extract from spine_output
File: `spine_api/persistence.py:619-666`
```python
frontier_result = spine_output.get("frontier_result")
fees = spine_output.get("fees")
# Add to trip dict:
"frontier_result": frontier_result,
"fees": fees,
```

**1.6 Fix server.py save dicts** — add all 5 missing fields to both save calls
File: `spine_api/server.py:1017-1034` (partial) and `1079-1095` (normal)
```python
"traveler_bundle": _to_dict(result.traveler_bundle) if hasattr(result, "traveler_bundle") and result.traveler_bundle else None,
"internal_bundle": _to_dict(result.internal_bundle) if hasattr(result, "internal_bundle") and result.internal_bundle else None,
"safety": _to_dict(result.safety) if hasattr(result, "safety") else None,
"fees": _to_dict(result.fees) if hasattr(result, "fees") and result.fees else None,
"frontier_result": _to_dict(result.frontier_result) if hasattr(result, "frontier_result") and result.frontier_result else None,
```

**1.7 Alembic migration**
File: `alembic/versions/add_frontier_result_and_fees_to_trips.py` (new)
Add `frontier_result` and `fees` as nullable JSON columns. Follow existing pattern with existence check.

**1.8 Frontend hydration**
File: `frontend/src/app/(agency)/workbench/page.tsx:131-154`
```typescript
// After line 139:
store.setResultFrontier((trip as Record<string, unknown>).frontier_result ?? null);
store.setResultFees((trip as Record<string, unknown>).fees ?? null);
```
Add `store.setResultFrontier` and `store.setResultFees` to useEffect dependency array.

**1.9 Update FrontierDashboard**
File: `frontend/src/components/workspace/FrontierDashboard.tsx`
- Import `useWorkbenchStore`
- Read `result_frontier` from store
- Derive display values from store with prop fallbacks
- Remove hardcoded defaults (`packetId="PK-9912"`, `sentiment=0.82`)

**1.10 Frontend private data discipline**
- `internal_bundle`: hydrate to store (agent-only view) — do not send to any customer-facing component
- `frontier_result`: hydrate to store — agent-only dashboard
- `fees`: hydrate to store — agent-only, redact payer/payment details in any non-agent view
- `booking_data` (future): do NOT hydrate globally. Fetch lazily only when OpsPanel opens.

**1.11 Refresh parity regression test**
- Run pipeline with test note
- Save trip to DB
- Load trip from DB
- Assert all 9 compartments survive round-trip
- Assert encrypted fields are not plaintext in DB

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
