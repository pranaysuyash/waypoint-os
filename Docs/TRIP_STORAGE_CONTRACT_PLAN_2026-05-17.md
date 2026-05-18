# Trip Field Resolution — Canonical Contract (First-Principles Fix)

**Date:** 2026-05-17  
**Status:** APPROVED (plan-eng-review)  
**Supersedes:** ADD_DATES_INVESTIGATION_COMPLETE.md (patch-work fix documentation)

---

## Root Cause

The dual-storage adapter fix (May 2026) patched the symptom. The root cause is:

**Field resolution logic is duplicated across three independent callsites with no shared authority:**

1. `spine_api/services/inbox_projection.py` — 7+ fallback paths per field (lines 173–244)
2. `frontend/src/lib/bff-trip-adapters.ts` — 51 defensive path lookups across 5+ locations
3. `spine_api/server.py:_sync_manual_trip_fields` — dual write with an edge case: budget text that fails numeric parsing does NOT write `extracted.facts.budget`, only `budget_raw_text`

No single place defines "what is the authoritative value of trip.dateWindow."

---

## Findings

| ID | Finding | Severity |
|----|---------|----------|
| F1 | `GET /trips/{trip_id}` and `PATCH` have no `response_model` — raw dict passthrough | Critical |
| F2 | `_sync_manual_trip_fields` budget edge case: unparseable text skips `extracted.facts.budget` write | High |
| F3 | Resolution logic duplicated across 3 callsites (inbox_projection, adapters, server) | High |
| F4 | `inbox_projection.py` itself uses the same multi-path fallback pattern as frontend | High |
| F5 | No `TripResponse` Pydantic model in `contract.py` | High |
| F6 | No PATCH→GET roundtrip integration test | Medium |

---

## Implementation Plan (Strangler Fig — 5 Phases)

### Phase 1 — Extract Resolution Logic (No Behavior Change)

Extract the per-field hunting chains from `inbox_projection.py` into:

```python
# spine_api/services/inbox_projection.py
def resolve_trip_field(trip: dict, field: str) -> Any:
    """Single source of truth for field resolution priority order."""
    ...
```

All three callsites (inbox_projection, scoring, server) call this function.  
Tests verify output is byte-for-byte identical before/after.  
**Risk:** Low. Pure refactor.

---

### Phase 2 — Fix Write-Side

Fix `_sync_manual_trip_fields` to always write to `extracted.facts.*`:

```python
# spine_api/server.py ~line 1733
# Current: only writes facts["budget"] if parsed_budget is not None
# Fix: always write — use raw text as value if numeric parse fails
if parsed_budget is not None:
    facts["budget"] = {"value": parsed_budget, "confidence": 1.0, "authority_level": "explicit_user"}
else:
    facts["budget"] = {"value": budget_text, "confidence": 0.5, "authority_level": "explicit_user_raw"}
```

After this ships, `extracted.facts.*` is reliably populated after every PATCH.  
**Risk:** Low. Additive write.

---

### Phase 3 — Simplify resolve_trip_field

With `extracted.facts.*` now reliably populated, simplify `resolve_trip_field` to use
`extracted.facts.*` as the primary lookup. Keep legacy fallbacks for pre-fix trips, marked
with a TODO for removal after archive/reprocessing window.  
**Risk:** Medium. Validate against all fixture trips.

---

### Phase 4 — Add TripResponse + response_model

```python
# spine_api/contract.py
class TripResponse(BaseModel):
    id: str
    status: str
    dateWindow: Optional[str] = None
    destination: Optional[str] = None
    origin: Optional[str] = None
    budget: Optional[float] = None
    party: Optional[int] = None
    type: Optional[str] = None

    @classmethod
    def from_dict(cls, trip: dict) -> "TripResponse":
        return cls(
            dateWindow=resolve_trip_field(trip, "date_window"),
            destination=resolve_trip_field(trip, "destination"),
            # etc — uses the canonical backend resolver, not ad-hoc paths
        )
```

Wire to `GET /trips/{trip_id}` and `PATCH /trips/{trip_id}`:
```python
@app.get("/trips/{trip_id}", response_model=TripResponse)
```

**Risk:** Medium. Any field missing from TripResponse becomes invisible. Validate against fixture corpus.

---

### Phase 5 — Frontend: Generate Types + Remove Adapters

1. Generate TypeScript from OpenAPI: `npx openapi-typescript http://localhost:8000/openapi.json`
2. Replace 51-path adapter functions with direct typed field access
3. Add PATCH→GET roundtrip integration test:
   ```python
   def test_patch_get_roundtrip(client, auth_headers, trip_id):
       client.patch(f"/trips/{trip_id}", json={"origin": "New York"}, headers=auth_headers)
       resp = client.get(f"/trips/{trip_id}", headers=auth_headers)
       assert resp.json()["origin"] == "New York"
   ```
4. Delete hunting functions from `bff-trip-adapters.ts`

**Risk:** Low once Phase 4 is correct. Failures are immediate and visible.

---

## Current Patch Status

The three-tier fallback added May 2026 (origin/budget top-level fallbacks in bff-trip-adapters.ts)
**must remain** until Phase 5 ships. Old trips may not have `extracted.facts.*` populated.
Do not revert.

## What NOT To Do

- Do not add `TripResponse` that itself contains multi-path hunting — moves duplication, doesn't fix it
- Do not skip Phase 1's behavior-preserving extraction step
- Do not remove frontend top-level fallbacks before Phase 2 ships

## Related Skills

- `~/.hermes/skills/refactoring-migration/large-scale-refactoring` — Strangler Fig pattern
- `~/Projects/skills/api-design` — response_model contract design
