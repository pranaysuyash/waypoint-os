# Discovery Gap Analysis: Audit Trail/Action Logging

**Date**: 2026-04-16
**Gap Register**: #13 (P1 — accountability and compliance)
**Scope**: Decision audit trail, action logging, change tracking, user attribution, compliance. NOT: analytics KPIs (#12), event-driven architecture (#02).

---

## 1. Executive Summary

The system has a `JSON`-file-based `AuditStore` that logs 3 event types (`trip_created`, `trip_assigned`, `trip_unassigned`). The frontend defines 9 `AuditEvent` types. **The gap is massive**: 6 of 9 event types are never emitted, no user identity is attached, no financial audit exists, no UI renders audit data, and the JSON storage is inadequate for production (no concurrency safety, no querying, 10K rotation).

---

## 2. Evidence Inventory

### What's Documented

| Doc | What | Location |
|-----|------|----------|
| `DISCOVERY_GAP_DATA_PERSISTENCE` L62, L89 | "No event store / audit trail persistence". AuditStore (JSON, 10K rotation) marked "inadequate for production" | #02 deep-dive |
| `DISCOVERY_GAP_FINANCIAL_STATE` L206 | "All financial state changes written to events table (gap #13)" | #04 deep-dive |
| `DISCOVERY_GAP_CANCELLATION_REFUND` L213 | "Audit trail for all manual entries" | #05 deep-dive |
| `PERSONA_PROCESS_GAP_ANALYSIS` L85, L175 | "No decision audit trail" — junior agents learn by trial and error | Docs/ |
| `DISCOVERY_GAP_AUTH_IDENTITY` L56 | "No audit log of WHO did WHAT" | #08 deep-dive |
| `UX_REDESIGN_MASTERPLAN` L765 | `/admin/audit-log` page spec | Docs/ |

### What's Implemented

| Code | What | Status |
|------|------|--------|
| `spine_api/persistence.py` L158-211 | `AuditStore` class: `log_event()`, `get_events()`, `get_events_for_trip()`. JSON file, 10K rotation | **Working but inadequate** |
| `spine_api/server.py` L67 | `GET /api/audit` returns recent events | **Working** — returns limited data |
| `frontend/src/types/governance.ts` L256-277 | `AuditEvent` with 9 types: `trip_created/updated/assigned/approved/rejected/completed`, `user_invited/removed`, `settings_changed`, `review_submitted` | **Types only** — 6 of 9 never emitted |
| `frontend/src/lib/governance-api.ts` L213-226 | `getAuditEvents()` and `getAuditEventsByTrip()` | **API client** — backend only has GET /api/audit |
| `persistence.py` L123-124, L152, L241-244 | `AuditStore.log_event()` called for `trip_created`, `trip_assigned`, `trip_unassigned` | **Partial** — only 3 of 9 event types |

### What's NOT Implemented

- 6 of 9 defined event types never emitted (`trip_updated`, `trip_approved`, `trip_rejected`, `trip_completed`, `user_invited`, `user_removed`, `settings_changed`, `review_submitted`)
- No `user_id` in audit events (always `"system"` or assignment string)
- No financial audit trail (pricing changes, margin edits, cancellation decisions)
- No `/admin/audit-log` page in frontend
- No `/api/audit/trip/:id` endpoint (frontend defines it, backend doesn't)
- No concurrency-safe storage (JSON file with no locking)
- No query filtering (by user, by trip, by event type, by date range)
- No compliance-grade logging (retention policy, tamper detection)

---

## 3-4. Gap Taxonomy & Data Model

| Gap ID | Concept | Implementation | Blocks |
|--------|---------|----------------|--------|
| **AU-01** | Production event store | JSON file, 10K rotation, no locking | All audit queries, compliance |
| **AU-02** | User attribution | `user_id` always `"system"` | Accountability, per-agent metrics |
| **AU-03** | Financial audit trail | None | Financial changes, margin edits |
| **AU-04** | Decision audit trail | None | "Why was this decision made?" answers |
| **AU-05** | Audit UI | No `/admin/audit-log` page | Owner visibility, compliance review |

```python
@dataclass
class AuditEvent:
    id: str
    event_type: str               # trip_created, trip_updated, pricing_changed, cancellation_processed, etc.
    actor_id: str                 # user_id from auth system
    actor_name: str               # display name
    actor_role: str               # "owner", "manager", "agent", "system"
    trip_id: Optional[str] = None
    customer_id: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    old_value: Optional[dict] = None  # previous state
    new_value: Optional[dict] = None  # new state
    metadata: dict = field(default_factory=dict)   # event-specific details
    ip_address: Optional[str] = None
```

---

## 5-8. Phase-In, Decisions, Risks, Out of Scope

### Phase 1: Database Event Store + User Attribution (P1, ~1 day, blocked by #02)

1. Migrate `AuditStore` from JSON file to PostgreSQL `audit_events` table
2. Add `actor_id`, `actor_name`, `actor_role` to all events
3. Emit all 9 defined event types from backend actions
4. Add `/api/audit/trip/:id` endpoint with filtering

**Acceptance**: Every trip action (create, update, assign, approve, reject, complete) is logged with who did it, when, and what changed.

### Phase 2: Financial Audit + Decision Trail (P1, ~1 day, blocked by #04)

1. Log all financial state changes (quote amount edits, collection entries, cancellation decisions)
2. Log all decision results (what the spine produced, what the agent overrode, why)
3. Add `old_value`/`new_value` diff to key events

**Acceptance**: Owner can see "Quote changed from ₹2.8L to ₹3.1L by agent Priya on Apr 15 14:30."

### Phase 3: Audit UI + Compliance (P2, ~2 days, blocked by #08)

1. Build `/admin/audit-log` page with filtering (by user, trip, event type, date range)
2. Add retention policy (90 days standard, 1 year financial events)
3. Add export capability (CSV)

**Acceptance**: Owner can filter audit log by agent, event type, and date range. Financial events retained for 1 year.

| Decision | Options | Recommendation |
|----------|---------|----------------|
| Audit storage | (a) PostgreSQL table, (b) Dedicated audit log, (c) Event sourcing | **(a) PostgreSQL table** — simplest, queryable, sufficient for MVP |
| Event granularity | (a) Coarse (state changes only), (b) Fine (every field change), (c) Configurable | **(a) Coarse for MVP** — state transitions, pricing changes, decisions only |

**Out of Scope**: Tamper-proof audit logs (cryptographic hashing), event sourcing architecture, real-time streaming, SIEM integration, compliance certification (SOC2, ISO 27001).