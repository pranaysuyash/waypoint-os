# Exploration & First-Principles Design: Yield & Commission Arbitrage

## 1. Overview
The Yield & Commission Arbitrage Engine compares supplier rate channels (Direct Preferred Contracts, GDS Preferred Rates, Bedbanks) to optimize agency net margin while preserving trip suitability.

## 2. Reality Tier Classification
- **Reality Tier**: `DATA_DEPENDENT`
- **Capabilities**:
  - `can_write_success_events`: True
  - `can_appear_as_paid`: False
  - `can_make_safety_claims`: False
  - `can_make_financial_claims`: False
  - `can_mutate_booking_state`: False

## 3. First-Principles Implementation
1. **JWT & Agency Scoping**: All yield endpoints require `get_current_agency_id`.
2. **Real Contract Integration**: Cross-checks uploaded contracts in `CONTRACTS_STORE` (`spine_api.routers.supplier`).
3. **Margin Calculation**: Net margin = `rack_rate_total - net_rate_total` (or `base_cost * commission_pct / 100`).
4. **No Demo Fallbacks**: `GET /opportunities` and `POST /swap-supplier` require a valid, existing `trip_id` for the calling agency. Returns 404 if trip is not found.
