# Exploration & First-Principles Design: Concierge & Disruption Resolution

## 1. Overview
The Concierge system monitors in-progress trips for disruptions (delays, cancellations, missed connections) and manages the resolution proposal workflow.

## 2. Reality Tier Classification
- **Reality Tier**: `DATA_DEPENDENT`
- **Capabilities**:
  - `can_write_success_events`: True
  - `can_appear_as_paid`: False
  - `can_make_safety_claims`: False
  - `can_make_financial_claims`: False
  - `can_mutate_booking_state`: False (automated rebooking requires external airline GDS/NDC booking APIs)

## 3. First-Principles Implementation
1. **JWT & Agency Scoping**: All endpoints require `get_current_agency_id`.
2. **Disruption Monitoring**: Inspects structured trip data (`disruption_event`, `status`, or explicit risk flags) rather than naive substring matching on notes.
3. **Rebooking Workflow**: Proposes a rebooking option for operator review. Records audit event and updates trip status to `rebook_requested`.
4. **Integration Honesty**: Explicitly states `automated_rebooking_available: False` and indicates that actual ticketing requires GDS/NDC integration.
5. **No Demo Data**: `GET /disruptions` returns real active disruptions for `agency_id` (empty list if none found, no hardcoded Priya Sharma fallback).
