# Event Log and Snapshot Model v0.1

## Purpose
To ensure 100% auditability and trust. The system never performs "silent mutations" of the state.

---

## 1. The Event Log (The Source of Truth)
The Event Log is an **append-only** sequence of atomic changes.

**Event Shape:**
```json
{
  "event_id": "evt_123",
  "event_type": "FIELD_EXTRACTED | FIELD_OVERWRITTEN | HYPOTHESIS_ADDED | etc.",
  "packet_id": "pkt_001",
  "occurred_at": "ISO-8601 Timestamp",
  "actor": {
    "type": "system | user | agency_owner",
    "id": "agent_id_or_user_id"
  },
  "reason": "Extracted origin_city from raw notes",
  "payload": {
    "field_name": "origin_city",
    "old_value": null,
    "new_value": "Bangalore",
    "evidence_ref": "env_001"
  }
}
```

---

## 2. The Materialized Snapshot
The `CanonicalPacket` is a **materialized view** of the Event Log.
- To get the current state, the system "replays" the event log.
- This ensures that any current value can be traced back to the exact event and source that created it.

---

## 3. State Transitions

### A. Contradiction Lifecycle
`Detected` $\rightarrow$ `Open` $\rightarrow$ `Resolved` (via a `CONTRADICTION_RESOLVED` event).

### B. Hypothesis Lifecycle
`Proposed` $\rightarrow$ `Active` $\rightarrow$ `Validated` OR `Rejected` $\rightarrow$ `Stale`.

### C. Manual Overrides
A `MANUAL_OVERRIDE` event is the highest priority. It does not delete the previous value in the log; it simply adds a new event that supersedes it in the snapshot.

---

## 4. UI Visibility (The Audit Trail)
Because we have an event log, the UI can show:
- **"Who changed this?"**: The actor and the timestamp.
- **"Why was this changed?"**: The reason provided in the event.
- **"Where is the proof?"**: The evidence reference linked to the event.
- **"What was the previous value?"**: The history of the field.
