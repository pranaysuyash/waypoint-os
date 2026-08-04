# Exploration & First-Principles Design: Supplier Management

## 1. Overview
Supplier Management allows travel agencies to upload negotiated rate sheets and contract terms from DMCs, hotels, and wholesalers, and place 48-hour soft holds on room inventory.

## 2. Reality Tier Classification
- **Reality Tier**: `DATA_DEPENDENT`
- **Capabilities**:
  - `can_write_success_events`: True
  - `can_appear_as_paid`: False
  - `can_make_safety_claims`: False
  - `can_make_financial_claims`: False
  - `can_mutate_booking_state`: False

## 3. First-Principles Implementation
1. **JWT & Agency Scoping**: All endpoints require `get_current_agency_id`. Contracts and holds are isolated by `agency_id`.
2. **Contract Ingestion**: Validates rate tables (net rate, rack rate, room types, seasonality).
3. **Soft Holds**: Reserves inventory against real uploaded contracts. If contract is missing for the agency, returns 404 (no fabricated Marrakech DMC fallback).
4. **Rate Calculation**: Margin is computed as `rack_rate_total - net_rate_total` based on actual nights stayed and contract rates.
