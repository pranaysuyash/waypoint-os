# Exploration & First-Principles Design: Trust Scorecard

## 1. Overview & Business Intent
The Trust Scorecard in Waypoint OS provides a transparent breakdown of why a proposed itinerary was selected for a traveler.

Instead of displaying hardcoded, static numbers (e.g., "96.0 Safety Score") or unverified marketing badges ("Verified Partner", "Guaranteed Price Lock"), the Trust Scorecard must reflect real, computable properties of the trip packet and decision state.

## 2. Reality Tier Classification
- **Reality Tier**: `DETERMINISTIC_PREVIEW`
- **Capabilities**:
  - `can_write_success_events`: True
  - `can_appear_as_paid`: False
  - `can_make_safety_claims`: False (safety claims require external supplier verification APIs)
  - `can_make_financial_claims`: False
  - `can_mutate_booking_state`: False (proposals can indicate intent, but booking requires confirmation)

## 3. Honest Metrics Computation

### A. Completeness Score (0 - 100%)
Computed from required packet field presence:
- Destination (20%)
- Dates / Duration (20%)
- Budget scope / range (20%)
- Party size / traveler details (20%)
- Special requirements or preferences (20%)

### B. Budget Alignment Status
Computed by comparing proposal cost (or target budget) against budget constraints:
- `PERFECT_MATCH`: proposal cost within [budget_min, budget_max]
- `UNDER_BUDGET`: proposal cost < budget_min
- `SLIGHT_STRETCH`: proposal cost up to 15% above budget_max
- `OVER_BUDGET`: proposal cost > 15% above budget_max
- `UNKNOWN`: insufficient budget data (`data_sufficient: False`)

### C. Transparency Highlights & Badges
Computed dynamically:
- Only display badges if supported by actual packet or contract data:
  - `COMPLETE_BRIEF`: All required trip packet fields captured
  - `BUDGET_ALIGNED`: Proposal within specified budget
  - `OWNER_REVIEWED`: Operator has reviewed and approved the brief
  - NO unverified badges ("Verified Partner", "Guaranteed Price Lock") unless supplier contract data exists in DB.

## 4. Token & Proposal Lifecycle Invariants
- Unknown tokens MUST return 404 (no hardcoded `trip_demo123` fallback).
- Token acceptance updates real trip status to `booking` only if the trip exists for the token.
- Public token lookup uses `get_trip_for_public_access(trip_id)` to strip agency internal notes, fees, and operator-only details.
