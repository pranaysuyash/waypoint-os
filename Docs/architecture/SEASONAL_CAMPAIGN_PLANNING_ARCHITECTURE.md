# Seasonal Campaign Planning Architecture & Operating Guide

## Overview & Purpose

The **Seasonal Campaign Planning** subsystem (governed by finding `G-14` / `FND-0080`) provides travel agency operators with deterministic tools to create, calibrate, simulate, preflight, and dispatch seasonal marketing and capacity allocation campaigns. It connects operator-defined channel mixes and budget boundaries with seasonal demand curves to prevent over-allocation or margin degradation during high-demand or shoulder seasons.

---

## Data Models & Schema (`spine_api/contract.py`)

The core schemas ensure strict validation on month bounds, budget intervals, channel percentages, and destination targeting:

- **`SeasonalCampaignPlan`**:
  - `plan_id`: Unique identifier for the campaign (e.g. `season_test_001`).
  - `name`: Campaign display name.
  - `destination`: Geographic focus (e.g., `"Japan"`, `"India / Europe"`).
  - `status`: Lifecycle state (`"draft"`, `"active"`, `"archived"`).
  - `campaign_window_start_month`: Integer month `[1..12]`.
  - `campaign_window_end_month`: Integer month `[1..12]`.
  - `channel_mix`: Dictionary mapping channels (`"organic"`, `"email"`, `"paid_search"`, etc.) to relative weights summing to ~1.0.
  - `target_budget_min` / `target_budget_max`: Expected traveler booking spend range in USD.
  - `blocklist`: Prohibited constraints or flags (e.g. `["budget_violation", "unapproved_charter"]`).
  - `notes`: Contextual operator directives.
  - `created_at` / `updated_at`: ISO-8601 UTC timestamps.

- **Request / Response Contracts**:
  - `CreateSeasonalCampaignRequest`: Payload required to draft a new campaign plan.
  - `UpdateSeasonalCampaignRequest`: Partial update payload for existing plans.
  - `SeasonalCampaignListResponse`: Container containing list of `SeasonalCampaignPlan` items and `total` count.

---

## Storage & Multi-Tenant Persistence (`spine_api/persistence.py`)

Seasonal campaigns are stored per agency in the configuration persistence layer:
- **File**: `spine_api/config/seasonal_campaigns.json` (managed via `ConfigStore`).
- **Isolation**: Stored under top-level tenant keys (`agency_id`) to ensure strict multi-tenant boundary isolation.
- **Operations**:
  - `ConfigStore.list_seasonal_campaigns(agency_id)`
  - `ConfigStore.get_seasonal_campaign(agency_id, plan_id)`
  - `ConfigStore.create_seasonal_campaign(agency_id, payload)`
  - `ConfigStore.update_seasonal_campaign(agency_id, plan_id, payload)`
  - `ConfigStore.delete_seasonal_campaign(agency_id, plan_id)`

---

## Endpoints & Lifecycle (`spine_api/routers/settings.py`)

The router is mounted under `/api/settings/seasonal/campaigns` with tenant resolution via `get_current_agency`:

1. **CRUD Endpoints**:
   - `GET /api/settings/seasonal/campaigns`: List all campaigns for the authenticated tenant.
   - `POST /api/settings/seasonal/campaigns`: Create a new campaign plan.
   - `GET /api/settings/seasonal/campaigns/{plan_id}`: Retrieve a specific campaign.
   - `PUT /api/settings/seasonal/campaigns/{plan_id}`: Update an existing campaign.
   - `DELETE /api/settings/seasonal/campaigns/{plan_id}`: Remove a campaign plan.

2. **Simulation Lifecycle (`POST /api/settings/seasonal/campaigns/{plan_id}/simulate`)**:
   - Accepts a scenario parameter: `"baseline"`, `"aggressive"`, or `"conservative"`.
   - Modulates projected leads, bookings, margin percentages, and confidence scores based on pacing and channel mix:
     - **Conservative**: Lower lead volume, higher projected margins, highest confidence.
     - **Baseline**: Expected market conversion rates and balanced pacing.
     - **Aggressive**: Maximum volume push with discount sensitivity, lower margin percentage, lower confidence.

3. **Preflight Checks (`POST /api/settings/seasonal/campaigns/{plan_id}/preflight`)**:
   - Evaluates channel allocation integrity (sum to 1.0), budget bounds validity (`min < max`), window configuration completeness, and blocklist sanity.
   - Returns structured status (`"pass"` / `"warn"` / `"fail"`) with corrective action hints.

4. **Dispatch Lifecycle (`POST /api/settings/seasonal/campaigns/{plan_id}/dispatch`)**:
   - Transitions plan from `"draft"` to `"active"` status.
   - Records activation audit event and returns dispatched confirmation timestamp.

---

## Verification & Automated Testing

- **Contract & Scenario Differentiation**: Verified by `tests/test_seasonal_campaign_simulation.py::test_seasonal_simulation_scenarios_are_distinct`.
- All simulation scenarios produce mathematically distinct projections and pass strict schema validations.
