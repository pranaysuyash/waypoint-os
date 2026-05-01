# Packet Facts Editing — Architecture Design

**Date**: 2026-05-01
**Status**: Design doc, pre-implementation
**Phase**: Phase 3 (after Phase 1 regex fixes + Packet hydration)

---

## Architecture Rule

**There must be exactly ONE current truth for packet values:**

```
extracted.facts[field_name]
```

Manual edits update `facts[field_name]` directly. The original value is preserved in packet **events** as audit/history only. No parallel `manual_overrides` truth layer. No code path that reads one source for display and another for execution.

| What | Where | Who reads it |
|------|-------|-------------|
| Current value | `facts[field_name]` | All consumers: PacketTab, planner, validator, exporter |
| Previous value | `events[]` (type: `packet_fact_corrected`) | PacketTab "show history" UI, revert, audit |
| Derived signals | `derived_signals[]` | Decision engine, strategy |

---

## Data Model

### facts[field_name] after manual edit

```json
{
  "value": "Mumbai",
  "confidence": 1.0,
  "authority_level": "manual_override",
  "extraction_mode": "manual_entry",
  "evidence_refs": [
    {
      "evidence_type": "manual_entry",
      "excerpt": "Agent corrected extraction: origin was Bangalore"
    }
  ],
  "updated_at": "2026-05-01T14:00:00Z"
}
```

### events[] entry for audit

```json
{
  "event_id": "evt_f3a2b1",
  "event_type": "packet_fact_corrected",
  "field_name": "origin_city",
  "previous_slot": {
    "value": "Bangalore",
    "confidence": 0.9,
    "authority_level": "explicit_user",
    "extraction_mode": "direct_extract"
  },
  "new_slot": {
    "value": "Mumbai",
    "confidence": 1.0,
    "authority_level": "manual_override",
    "extraction_mode": "manual_entry"
  },
  "timestamp": "2026-05-01T14:00:00Z",
  "actor": "agent-42"
}
```

### metadata flags on packet

```json
{
  "extracted": {
    "facts": { ... },
    "derived_signals": { ... },
    "events": [...],
    "validation_stale": true,
    "manual_edit_count": 3,
    "last_manual_edit_at": "2026-05-01T14:00:00Z"
  }
}
```

`validation_stale: true` signals that derived signals may be outdated. The planner/validator layer can use this to trigger revalidation on next access.

---

## Editable Field Whitelist (v1)

Strict field + type validation on the endpoint:

| Field | Type | Notes |
|-------|------|-------|
| `origin_city` | `string` | |
| `destination_candidates` | `string[]` | |
| `destination_status` | `string` | Enum: definite, semi_open, open |
| `date_window` | `string` | |
| `date_start` | `string` (ISO date) | |
| `date_end` | `string` (ISO date) | |
| `party_size` | `integer` | |
| `party_composition` | `object` | Keys: adults, children, elderly, teens |
| `child_ages` | `number[]` | |
| `budget_raw_text` | `string` | If set, also parse and set budget_min/budget_max |
| `budget_min` | `integer\|null` | |
| `budget_max` | `integer\|null` | |
| `budget_currency` | `string` | |

Reject unknown field names. Reject type mismatches.

### Budget grouping

Accept `budget_raw_text` as the primary budget edit field. If provided, also parse it server-side using the existing `Normalizer.parse_budget()` and update `budget_min`, `budget_max`, `budget_currency` together. This prevents the three fields from silently diverging.

If a user edits `budget_min` or `budget_max` directly without `budget_raw_text`, allow it — they are experienced operators making precise numeric corrections.

---

## Backend Endpoint

```
PATCH /api/trips/{trip_id}/packet-facts
Auth: required
Body: { "facts": { "origin_city": "Mumbai" } }
```

### Behavior

1. Load trip, get `extracted` dict
2. Validate each key in `facts` against whitelist + type check
3. For each valid fact:
   a. Read current Slot from `extracted.facts[field]` (if any)
   b. Build new Slot: `value`, `confidence: 1.0`, `authority_level: "manual_override"`, `extraction_mode: "manual_entry"`, `evidence_refs: [{ evidence_type: "manual_entry" }]`, `updated_at: now`
   c. Append event to `extracted.events`: `{ event_type: "packet_fact_corrected", field, previous_slot, new_slot, timestamp, actor }`
   d. Set `extracted.facts[field] = new_slot`
   e. Remove matching entries from `extracted.unknowns` for this field only
   f. If field is `budget_raw_text`, also parse and set `budget_min`/`budget_max`
4. Set `extracted.validation_stale = true`, `extracted.manual_edit_count += 1`, `extracted.last_manual_edit_at = now`
5. Persist via `TripStore.update_trip()`
6. Log audit event
7. Do NOT clear validation warnings, ambiguities, or contradictions
8. Do NOT recompute derived signals
9. Return updated trip

### What is NOT changed

- Existing `PATCH /api/trips/{id}` — unchanged
- IntakePanel save flow — unchanged
- `_sync_manual_trip_fields()` — unchanged (still supports legacy trip-field editing)
- Pipeline extraction output — unchanged
- PacketTab read path — unchanged (reads `facts` as before)

---

## Frontend PacketTab Display

### Current: read-only table of facts

```
Field        | Value        | Confidence | Authority
origin_city  | Bangalore    | 90%        | explicit_user
```

### After Phase 3B (read support, no editing yet)

If a fact has `authority_level === "manual_override"`, show:

```
Field        | Value   | Badge         | Confidence | Authority
origin_city  | Mumbai  | [manual edit] | 100%       | manual_override
             |         | Original: Bangalore (90%, explicit_user)
```

The "Original" line is derived from scanning `events[]` for the most recent `packet_fact_corrected` event for this field. No separate `manual_overrides` layer.

### After Phase 3C (edit controls)

Per-row edit button (pencil icon on hover). Click opens inline input. Save calls `PATCH /api/trips/{id}/packet-facts`.

---

## Validation Staleness

When a fact is manually edited:

| What | Action |
|------|--------|
| `facts[field]` | Updated with manual_override |
| `unknowns[field]` | Removed (deterministically stale) |
| `derived_signals` | NOT updated (may be stale) |
| `validation` warnings | NOT cleared (may still be relevant) |
| `ambiguities` | NOT cleared |
| `contradictions` | NOT cleared |
| `validation_stale` | Set to `true` |

The planner/decision layer should check `validation_stale` and trigger revalidation before consuming derived signals.

---

## Required Tests (Phase 3A: backend only)

| Test | What it covers |
|------|---------------|
| `test_set_valid_fact` | origin_city set with manual_override authority, confidence 1.0, extraction_mode manual_entry |
| `test_preserves_original_in_events` | previous_slot captured in events array before overwrite |
| `test_rejects_unknown_field` | 400 for unwhitelisted field name |
| `test_rejects_type_mismatch` | 400 for party_size="abc" |
| `test_removes_matching_unknown` | unknowns containing origin_city removed after edit |
| `test_does_not_clear_ambiguities` | Ambiguities left intact |
| `test_does_not_clear_contradictions` | Contradictions left intact |
| `test_does_not_clear_validation_warnings` | Warnings left intact |
| `test_sets_validation_stale` | validation_stale=true after edit |
| `test_budget_grouped_update` | budget_raw_text "3L" also sets budget_min=300000 |
| `test_no_auth_returns_401` | Auth guard |
| `test_non_existent_trip_returns_404` | Not found |
| `test_set_and_get_roundtrip` | Written value survives reload |
| `test_legacy_patch_unchanged` | Existing PATCH /trips/{id} still works |

---

## Phased Implementation Order

```
Phase 3A: Backend endpoint + tests
  - PATCH /api/trips/{id}/packet-facts
  - Field whitelist + type validation
  - Event-based history preservation
  - validation_stale marker
  - Budget grouped update via Normalizer.parse_budget()
  - All backend tests pass

Phase 3B: Frontend read support
  - PacketTab shows manual_override badge
  - PacketTab shows original value from events
  - No edit controls yet
  - Frontend tests pass

Phase 3C: Frontend edit controls
  - Per-row inline edit UI
  - PATCH call on save
  - Confirmation/success feedback
  - Frontend + integration tests pass
```

Do not start Phase 3B until Phase 3A ships. Do not start Phase 3C until Phase 3B is stable.

---

## Single Read Path Verification

| Question | Answer |
|----------|--------|
| What is the single read path for current packet values? | `extracted.facts[field_name]` |
| Where is previous value stored? | `extracted.events[]` — type `packet_fact_corrected`, field `previous_slot` |
| Which code is allowed to read previous value? | PacketTab "show history" UI, audit export, revert function only |
| How do we prevent consumers from treating previous/original values as current truth? | Events are never read by planner, validator, exporter, or decision engine. They are in a separate `events[]` array, not in `facts` or `derived_signals`. PacketTab derives "show original" from events only for display annotation. |
