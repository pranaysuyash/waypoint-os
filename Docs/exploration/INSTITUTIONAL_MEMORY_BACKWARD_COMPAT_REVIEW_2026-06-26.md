# Institutional Memory Additive Data Model — Backward Compatibility Review

**Date**: 2026-06-26
**Review of**: Adding `template_id`, `supplier_bookings`, `customer_profile_ref`, `playbook_events` to `CanonicalPacket`
**Status**: ✅ Safe with constraints (3 blocking issues identified)
**Source**: [`Docs/context/INSTITUTIONAL_MEMORY_LAYER_SYNTHESIS_2026-04-14.md`](../context/INSTITUTIONAL_MEMORY_LAYER_SYNTHESIS_2026-04-14.md), [`Docs/exploration/KNOWLEDGE_MANAGEMENT_TRAINING_SYNTHESIS_2026-06-26.md`](../exploration/KNOWLEDGE_MANAGEMENT_TRAINING_SYNTHESIS_2026-06-26.md)

---

## 1. Executive Verdict

**Adding `template_id`, `supplier_bookings`, `customer_profile_ref`, `playbook_events` to `CanonicalPacket` is backward compatible** with careful handling of three blocking issues. The additive data model design is sound — all fields have default values that maintain existing behavior for all consumers without changes.

### Compatibility Summary

| Consumer | Impact | Action Required |
|----------|--------|----------------|
| `CanonicalPacket` dataclass (Python) | ✅ Safe — `Optional` + defaults via `field(default_factory=dict)` | None |
| `CanonicalPacket.to_dict()` serialization | ❌ **Issues** | See §3 |
| JSON schema (`specs/canonical_packet.schema.json`) | ❌ **Blocked** — `additionalProperties: false` rejects unknown keys | Must update schema |
| Frontend types (`spine.ts`, `spine-api.ts`) | ✅ Safe — packet typed as `Record<string, unknown>` | None |
| `SpineRunResponse.packet` / `RunStatusResponse.packet` | ✅ Safe — typed as `Optional[Dict[str, Any]]` | None |
| `TripResponse` (canonical API contract) | ✅ Safe — resolved via `resolve_trip_field()`, not from packet | None |
| Test fixtures (`packet_fixtures.py`, `test_scenarios.py`) | ✅ Safe — use `CanonicalPacket(**kwargs)` with defaults | None |
| Extraction pipeline (`extractors.py`) | ✅ Safe — constructs fresh `CanonicalPacket(...)` | None |
| Inference pipeline (decision, strategy, gates) | ✅ Safe — access specific `packet.facts` keys, ignore new fields | None |

---

## 2. Proposed Fields — Data Model

```python
@dataclass(slots=True)
class CanonicalPacket:
    # ... existing fields ...
    
    # --- Institutional Memory fields (additive, all Optional) ---
    template_id: Optional[str] = None
    supplier_bookings: Dict[str, SupplierBooking] = field(default_factory=dict)
    customer_profile_ref: Optional[str] = None
    playbook_events: List[PlaybookExecution] = field(default_factory=list)
```

**Note**: Companion models (`SupplierBooking`, `PlaybookExecution`, `TemplateMatch`, `TemplateCustomization`) need to be defined in separate modules or imported — they add no risk to backward compatibility since they're only referenced by the new fields.

---

## 3. Detailed Compatibility Analysis

### 3.1 `@dataclass(slots=True)` Constraint

**Verdict**: ✅ Safe but strict

`CanonicalPacket` uses `@dataclass(slots=True)`, which means:
- All fields MUST be declared at class definition time
- You cannot dynamically set new attributes (`packet.template_id = "x"` would fail if `template_id` isn't a declared field)
- Adding new fields with defaults is the standard pattern — no issues here

**Proof**: The `@dataclass(slots=True)` pattern is already established; `lifecycle`, `suitability_flags`, `feedback`, `metadata` etc. are all added with defaults. New fields follow the same pattern.

### 3.2 `CanonicalPacket.to_dict()` Serialization

**Verdict**: ⚠️ Requires explicit update — not auto-included

`to_dict()` manually constructs the output dict (lines 726-754 in `packet_models.py`):

```python
def to_dict(self) -> dict:
    # ... builds contradictions ...
    return {
        "packet_id": self.packet_id,
        "schema_version": self.schema_version,
        "stage": self.stage,
        # ... etc, no template_id or supplier_bookings ...
    }
```

**Issue**: New fields will NOT automatically appear in `to_dict()` output unless explicitly added. This is actually **good for backward compatibility** — no serialization format changes until you're ready.

**Recommendation**: Add new fields to `to_dict()` ONLY after the JSON schema is updated (see §3.3). Until then, access them via direct attribute access (e.g., `packet.template_id` instead of `serialized["template_id"]`).

### 3.3 JSON Schema — BLOCKING ISSUE

**Verdict**: ❌ **Blocked** — `additionalProperties: false`

The root object in `specs/canonical_packet.schema.json` uses:

```json
"additionalProperties": false,
"required": [
    "packet_id", "schema_version", "stage", "operating_mode",
    "decision_state", "facts", "derived_signals", "hypotheses",
    "lifecycle", "ambiguities", "unknowns", "contradictions",
    "source_envelope_ids", "revision_count", "event_cursor", "events"
]
```

This means: any key not in the `properties` list (or the `required` list) will fail validation. If you add `template_id` or `supplier_bookings` to `to_dict()` output without updating the schema, any runtime schema validation will reject the output.

**Three resolution options**:

| Option | Change | Risk | Recommendation |
|--------|--------|------|---------------|
| **A — Safe (recommended for now)** | Add new fields to schema with `optional: true`; do NOT add to `required` | None — schema becomes more permissive | ✅ **Do this** — it's what "additive" means |
| **B — Minimal** | Change root `additionalProperties` to `true` | Low — loses schema strictness for other potential typos | Not recommended |
| **C — Version bump** | Set `schema_version: "0.4"`, rebuild schema with new fields | Low — but signals breaking change | Overkill for additive fields |

**Recommended**: Add new fields to schema properties as optional, keep `additionalProperties: false`. This maintains schema strictness while allowing the new additive fields.

### 3.4 `schema_version` Const

The schema enforces `"const": "0.3"` for `schema_version`. The code also defaults `schema_version = "0.3"`.

**Verdict**: ✅ No change needed for backward compatibility. The additive fields don't change the existing data model — they extend it. Keep `0.3` for now, bump only if you're restructuring existing fields.

### 3.5 Serialization Consumers

**`SpineRunResponse`** and **`RunStatusResponse`**: Both type `packet` as `Optional[Dict[str, Any]]` (loose dict). This means any new keys in `to_dict()` output pass through transparently. ✅

**`TripResponse.from_dict()`**: Does NOT read from `CanonicalPacket.to_dict()` directly. Instead, it resolves canonical fields via `resolve_trip_field()` which reads from `extracted.facts`. The packet is embedded inside `trip["extracted"]` as an opaque dict. New fields on `CanonicalPacket` are invisible to `TripResponse` until explicitly wired in. ✅

**Frontend `PacketPanel` / `PacketTab`**: Both access the packet as `Record<string, unknown>` and iterate over `Object.entries()`. New top-level keys would show up in JSON debug output but not in the facts table (which iterates `bookingRequest.facts`). ✅

### 3.6 Construction Paths

All code that constructs `CanonicalPacket` uses the constructor with keyword args:

- **Extraction pipeline** (`extractors.py:1616`): `packet = CanonicalPacket(...)` — fine ✅
- **Test fixtures** (`packet_fixtures.py`): `P(**kwargs)` → `CanonicalPacket(**kwargs)` — fine ✅  
- **Test scenarios** (`test_scenarios.py`): `CanonicalPacket(...)` with explicit args — fine ✅

No code deserializes `CanonicalPacket` from JSON. There is no `from_dict()` classmethod. The packet is always constructed fresh and serialized out via `to_dict()`. This makes the model exceptionally safe for additive changes.

### 3.7 Inference Consumers

Multiple modules consume `CanonicalPacket` to read specific fields:

| Module | Fields Read | Impact |
|--------|-------------|--------|
| `decision.py` | `packet.facts["*"]`, `packet.derived_signals`, `packet.contradictions` | None — only accesses known fact keys |
| `strategy.py` | `packet.facts["*"]` via `_slot_text()` | None — iterates facts dict |
| `safety.py` | `packet.facts`, `packet.derived_signals`, `packet.lifecycle` | None — uses specific attrs |
| `orchestration.py` | `_snapshot_packet_state()` uses `getattr()` | ✅ **Notable**: uses `getattr(packet, "stage", None)` — ignores unknown keys |
| `readiness.py` | `packet.facts`, `packet.lifecycle` | None |
| `gates.py` | `packet.facts`, `packet.derived_signals` | None |
| `plan_candidate.py` | `_safe_get_fact(packet, ...)` | None — reads from facts dict only |

None of these consumers access `template_id` or `supplier_bookings` — they won't break or behave differently.

### 3.8 Frontend Type Definitions

**`spine.ts`**: Defines `SlotValue`, `Ambiguity`, `PacketUnknown`, `PacketContradiction` — all typed interfaces for the packet's `facts` sub-object. The packet itself is typed loosely in the API response. ✅

**`spine-api.ts` (generated)**: `packet` is typed as `Optional[Dict[str, unknown]]` throughout. ✅

---

## 4. Implementation Plan (Backward-Compatible)

### Step 1: Define companion models (zero impact on existing code)

Create new modules with no imports from existing code:
- `src/intake/template_models.py` — `TripTemplate`, `TemplateMatch`, `TemplateCustomization`
- `src/intake/supplier_models.py` — `SupplierProfile`, `SupplierBooking`

### Step 2: Add fields to `CanonicalPacket` (backward compatible)

```python
# In packet_models.py CanonicalPacket class
template_id: Optional[str] = None
supplier_bookings: Dict[str, Any] = field(default_factory=dict)  # SupplierBooking not imported yet
customer_profile_ref: Optional[str] = None
playbook_events: List[Dict[str, Any]] = field(default_factory=list)
```

These are all additive defaults — no existing code breaks.

### Step 3: Update JSON schema

Add new fields as optional properties to `specs/canonical_packet.schema.json`:

```json
"template_id": { "type": ["string", "null"] },
"supplier_bookings": { "type": "object", "additionalProperties": true },
"customer_profile_ref": { "type": ["string", "null"] },
"playbook_events": { "type": "array" }
```

Do NOT add to `required`. Do NOT bump `schema_version`.

### Step 4: Add to `to_dict()` (only after schema update)

Add the new fields to the `to_dict()` return dict so they're serialized.

### Step 5: Wire into `TripResponse` (future, separate phase)

When a frontend consumer needs `template_id` in the trip API response, add a `template_id` field to `TripResponse` and resolve it like existing fields.

---

## 5. Things That COULD Break (and why they won't)

| Risk | Explanation | Mitigation |
|------|-------------|------------|
| `additionalProperties: false` rejects unknown keys | If `to_dict()` includes new fields without schema update | ⚠️ **Blocking** — must update schema BEFORE adding to `to_dict()` |
| `dataclasses.asdict()` includes new fields | `_obj_to_dict()` in orchestration.py uses `asdict()` for dataclasses | ✅ `_obj_to_dict()` is only called on `SpineResult`, `DecisionResult`, `Strategy`, `PromptBundle` — NOT on `CanonicalPacket` directly |
| Frontend picks up unknown keys | Frontend iterates `Object.entries(facts)` which is `packet.facts` sub-object | ✅ New fields are at packet top-level, not in `facts` |
| Pickle/serialization of packets | No pickle usage in the codebase | ✅ Not applicable |
| Database schema conflicts | TripStore stores `extracted` as JSON dict | ✅ New fields are just additional keys in the dict |

---

## 6. Conclusion

**The institutional memory additive data model is backward compatible** with **one blocking prerequisite**: the JSON schema must be updated to allow the new optional fields before they're added to `to_dict()` output.

**Safe to implement immediately**: Companion models (`SupplierBooking`, `TripTemplate`) and adding fields to the `CanonicalPacket` dataclass itself.

**Gate**: Updating the JSON schema and `to_dict()` before the fields are consumed in any serialization path.

**Non-issue areas**: Frontend types, API contracts, inference pipelines, test fixtures, database persistence — all tolerant of new optional fields with defaults.
