# ADR: Interactive Client Proposal Web Link & 1-Click Acceptance

**Status**: Accepted  
**Date**: 2026-07-29  
**Context**: Waypoint OS Interactive Traveler Proposal Surface (Priorities #2 & #5)

---

## Context

Static PDF proposals sent via email attachment fail to engage modern travel clients and obscure real-time conversion signals. Planners lack visibility into whether a traveler has viewed options, accepted recommendations, or requested changes.

---

## Decision

Implemented an interactive client proposal web application and signed web-link generator:

1. **Frontend App (`frontend/src/app/proposals/[proposalId]/page.tsx`)**:
   - Standalone glassmorphic traveler surface rendering itinerary details, budget match %, price lock countdown, transparency badges ("Why This Option"), and 1-click acceptance.
2. **Public Signed Web Links (`GET /api/v1/proposals/token/{token}`)**:
   - Generates cryptographically secure, time-bound tokens (`prop_<uuid>`) for direct client access without requiring agency login credentials.
3. **1-Click Booking Acceptance (`POST /api/v1/proposals/token/{token}/accept`)**:
   - Updates trip state to `PROCEED_BOOKING`, logs acceptance timestamp, and triggers real-time notification to the agency planner.
4. **Automated Follow-Up Copy Generator (`POST /api/v1/followups/generate`)**:
   - Generates channel-calibrated re-engagement copy (WhatsApp vs Email, friendly vs urgent tone) to drive client proposal opens and conversion.

---

## Consequences

- Replaces static PDF workflows with real-time interactive web links.
- Instant conversion signals when a traveler accepts or reviews options.
- Complete audit logging of client acceptance timestamps in `AuditStore`.
