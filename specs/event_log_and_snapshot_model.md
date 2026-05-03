# Event Log and Snapshot Model v0.3

## Purpose
To ensure 100% auditability and trust. The system never performs "silent mutations" of the state.

---

## 1. Event Systems (Three Layers, One Goal)

The system uses three event stores, each with a distinct scope:

| Store                   | Location                          | Format    | Scope               | Purpose                           |
|-------------------------|-----------------------------------|-----------|---------------------|-----------------------------------|
| CanonicalPacket.events  | `src/intake/packet_models.py:332` | in-memory | Per-packet          | Field-level mutation audit trail  |
| AuditStore              | `spine_api/persistence.py:825`    | JSONL     | Global (all trips)  | Business-level event log          |
| Run-level events.jsonl  | `spine_api/run_events.py`         | JSONL     | Per-run             | Pipeline step execution log       |

**CanonicalPacket.events** is the closest to this spec's vision: every mutation to `facts`, `derived_signals`, or `hypotheses` emits an event via `_EventTrackingDict`. Events carry `field_name`, `old_value`, and `new_value`, enabling full field-level auditability.

**AuditStore** logs business-level actions (trip_created, draft_promoted, override_created) in a global append-only JSONL file. This is the operational audit trail.

**Run-level events.jsonl** tracks pipeline execution (run_started, stage_entered, stage_completed) for observability.

## 2. CanonicalPacket Event Shape (in-memory)

Events emitted by `_EventTrackingDict` mutations:

```json
{
  "event_id": 42,
  "event_type": "fact_set | derived_signal_set | hypothesis_set | contradiction_detected | ...",
  "timestamp": "2026-05-03T11:00:00",
  "details": {
    "field_name": "origin_city",
    "old_value": "Bangalore",
    "new_value": "Mumbai"
  }
}
```

All `set_fact`, `set_derived_signal`, `set_hypothesis`, and direct dict writes (`packet.facts["key"] = slot`) emit events automatically via `_EventTrackingDict`. No convention required — enforcement is architectural.

## 3. How State Is Materialized

The `CanonicalPacket` is materialized from SourceEnvelopes by `ExtractionPipeline.extract()` (`src/intake/extractors.py:1242`). Each extraction produces a fresh packet — there is currently no event replay mechanism. Fresh extraction per run is the canonical approach; event replay for debugging/time-travel may be added in a future version.

Value-to-source lineage is preserved via `Slot.evidence_refs` (list of `EvidenceRef` dataclasses with `envelope_id`, `evidence_type`, `excerpt`, `confidence`).

## 4. State Transitions

### A. Contradiction Lifecycle (v0.3)

`Detected` → `Open` → `Resolved` (reopenable)

Implemented in `CanonicalPacket` (`src/intake/packet_models.py`):
- `add_contradiction()` → state: `ContradictionState.DETECTED`
- `open_contradiction()` → state: `ContradictionState.OPEN`
- `resolve_contradiction(field_name, resolution, resolved_by)` → state: `ContradictionState.RESOLVED` + emits `contradiction_resolved`
- `reopen_contradiction()` → state: `ContradictionState.OPEN`

### B. Hypothesis Lifecycle (v0.3)

`Proposed` → `Active` → `Validated` OR `Rejected` → `Stale`

Implemented in `CanonicalPacket` (`src/intake/packet_models.py`):
- `set_hypothesis()` automatically sets initial state to `HypothesisState.PROPOSED`
- `activate_hypothesis()` → `HypothesisState.ACTIVE`
- `validate_hypothesis()` → `HypothesisState.VALIDATED`
- `reject_hypothesis()` → `HypothesisState.REJECTED`
- `mark_hypothesis_stale()` → `HypothesisState.STALE`

### C. Manual Overrides

`MANUAL_OVERRIDE` (`AuthorityLevel.MANUAL_OVERRIDE`) is the highest authority level (rank 1). It does not delete previous values; it adds a new `fact_set` event with the override value while preserving the old value in the event's `old_value` field.

## 5. AuditStore (Global Append-Only JSONL)

File: `data/audit/events.jsonl`

Design (v2):
- Each event is one JSON line, written in append mode.
- Crash-safe at the event level (no read-modify-write).
- Periodic compaction (every ~100 writes) trims to max 10,000 events via atomic rename.
- Legacy `events.json` is auto-migrated to `events.jsonl` on first access.

## 6. UI Visibility (The Audit Trail)

The backend provides audit data via:
- `TimelineEvent` (`src/analytics/logger.py:32`): presentation-ready events with actor, reason, confidence, pre/post state
- `AuditLog` (`spine_api/models/audit.py:61`): DB-backed audit with changes (before/after snapshots)
- `GET /api/trips/{id}/timeline`: mapped timeline events from AuditStore
- `GET /api/runs/{id}/events`: run-level events from events.jsonl

The UI should render for each timeline item:
- **"Who changed this?"**: actor/user_id from the event
- **"Why was this changed?"**: reason field
- **"Where is the proof?"**: evidence reference (if available via Slot.evidence_refs)
- **"What was the previous value?"**: pre_state / old_value from the event
