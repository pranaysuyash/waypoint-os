# ADR: Autonomic Ghost Concierge Disruption Monitoring

**Status**: Accepted  
**Date**: 2026-07-29  
**Context**: Waypoint OS Active Trip Monitoring & Disruption Management (Priority #7)

---

## Context

Active travel itineraries face real-world disruptions (flight delays, cancellations, schedule changes, weather impacts). Manual disruption monitoring requires travel agents to track individual airline PNRs continuously, leading to missed layovers and delayed rebooking.

---

## Decision

Implemented the Autonomic Ghost Concierge Engine in `spine_api/routers/concierge.py`:

1. **Disruption Watcher (`GET /api/v1/concierge/disruptions`)**:
   - Continuously scans active trips for flight delay/cancellation signals.
   - Categorizes disruption severity (`HIGH`, `MEDIUM`, `LOW`) and computes recommended protection actions (e.g. *"Auto-rebook to partner carrier"* or *"Monitor connection buffer"*).
2. **Real-Time Status Monitoring (`POST /api/v1/concierge/monitor/{trip_id}`)**:
   - Evaluates active itinerary segment health against live disruption feeds.
3. **Autonomic Rebooking Engine (`POST /api/v1/concierge/auto-rebook/{trip_id}`)**:
   - Generates protected rebooking segments (`PNR_<code >`) with $0 additional cost under airline disruption policy, logging audit events in `AuditStore`.

---

## Consequences

- 24/7 autonomic protection for active traveler itineraries.
- Reduces missed connections and layover failures.
- Complete audit trail of automated rebooking events.
