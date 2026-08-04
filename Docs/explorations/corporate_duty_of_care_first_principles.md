# Exploration & First-Principles Design: Corporate Duty-of-Care

## 1. Overview
Corporate Duty-of-Care enables travel agencies to track corporate travelers, audit policy compliance (per-diem hotel caps, flight cabin class restrictions), and monitor active offsites.

## 2. Reality Tier Classification
- **Reality Tier**: `DATA_DEPENDENT`
- **Capabilities**:
  - `can_write_success_events`: True
  - `can_appear_as_paid`: False
  - `can_make_safety_claims`: False
  - `can_make_financial_claims`: False
  - `can_mutate_booking_state`: False

## 3. First-Principles Implementation
1. **JWT & Agency Scoping**: All corporate endpoints require `get_current_agency_id`.
2. **Policy Audit**: Checks hotel rate and cabin class against per-diem rules for agency trips.
3. **Duty-of-Care Cockpit**: Constructs traveler roster from real agency trips in `TripStore`.
4. **Integration Honesty**: Explicitly states `flight_tracking_available: False` and notes that automated flight status feeds require flight tracking API credentials.
