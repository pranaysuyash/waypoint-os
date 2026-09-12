# Seasonal Campaigns — Current-State Documentation

**Date**: 2026-09-02 · **Status**: Documentation of what IS (verified against working tree on this date; all `file:line` evidence current as of writing)
**Origin**: Shadow-audit item R-04 / §3(b)1 of `Docs/exploration/DOCS_CORPUS_SHADOW_AUDIT_2026-08-31.md` — "Seasonal campaigns — fully built, zero docs."
**Placement note**: this doc lives in `Docs/product_features/` (the repo's established feature-doc directory) rather than a new `Docs/features/` tree, per the no-parallel-systems rule; the dated filename marks it as a point-in-time record.

---

## 1. What it is

An **agency-scoped seasonal campaign planning surface**: each agency maintains a seasonal
policy (guardrails + defaults) and a set of campaign plans (`SeasonalCampaignPlan`), with
three plan-level operations — **simulate** (deterministic lead/booking/margin projection),
**preflight** (policy checks + risk score), and **dispatch** (an acknowledgment stub — see §5).
Everything persists as agency-keyed JSON config; there is no external marketing-channel
integration anywhere in the chain.

## 2. Backend — API surface (`spine_api/routers/settings.py`)

Router registered at `spine_api/server.py:1459` (`app.include_router(settings_router.router, …)`).

| Endpoint | Location | Permission | What it does |
|---|---|---|---|
| `GET /api/settings/seasonal` | `settings.py:369-375` | `settings:read` | Returns the agency seasonal policy (via `ConfigStore.get_seasonal_policy`). Also embedded in the aggregate settings payload at `settings.py:58`. |
| `PUT /api/settings/seasonal` | `settings.py:378-387` | `settings:write` | Updates the policy (`ConfigStore.update_seasonal_policy`). |
| `GET /api/settings/seasonal/campaigns` | `settings.py:393-399` | `settings:read` | Lists campaign plans (`SeasonalCampaignListResponse`). |
| `POST /api/settings/seasonal/campaigns` | `settings.py:402-413` | `settings:write` | Creates a plan (`CreateSeasonalCampaignRequest` → `SeasonalCampaignPlan`). |
| `GET /api/settings/seasonal/campaigns/{plan_id}` | `settings.py:416-425` | `settings:read` | Fetches one plan. |
| `PUT /api/settings/seasonal/campaigns/{plan_id}` | `settings.py:428-439` | `settings:write` | Updates one plan. |
| `DELETE /api/settings/seasonal/campaigns/{plan_id}` | `settings.py:442-449` | `settings:write` | Deletes one plan. |
| `POST …/{plan_id}/simulate` | `settings.py:454-516` | `settings:read` | Deterministic projection (§4). |
| `POST …/{plan_id}/preflight` | `settings.py:519-565` | `settings:read` | Heuristic checks + risk score (§4). |
| `POST …/{plan_id}/dispatch` | `settings.py:568-584` | `settings:write` | Acknowledgment stub (§5). |

**Contract models** (`spine_api/contract.py`):
`UpdateSeasonalPolicy` (`:803`), `SeasonSimulationRequest` (`:816`), `SeasonDispatchRequest`
(`:820`, `dry_run: bool = True`), `AgencySeasonalSettingsResponse` (`:825`),
`SeasonalCampaignPlan` (`:836` — `plan_id`, `name`, `status ∈ {draft, active, paused, archived}`,
`destination`, campaign window start/end months, `channel_mix`, budget min/max, `notes`,
`blocklist`, `is_recalibrated`, `score`), `CreateSeasonalCampaignRequest` (`:857`),
`UpdateSeasonalCampaignRequest` (`:870`), `SeasonalCampaignListResponse` (`:884`),
`SeasonPreflightCheck` (`:889`).

## 3. Persistence (`spine_api/persistence.py`, `ConfigStore`)

- Two JSON config files beside the other agency config:
  - `SEASONAL_POLICY_FILE = CONFIG_DIR / "seasonal_policy.json"` (`persistence.py:3225`)
  - `SEASONAL_CAMPAIGNS_FILE = CONFIG_DIR / "seasonal_campaigns.json"` (`persistence.py:3226`)
  - with `CONFIG_DIR = DATA_DIR / "config"` (`persistence.py:3210`) — i.e. **file-backed agency
    config**, not Postgres.
- **Policy defaults** (`_default_seasonal_policy`, `persistence.py:3260-3281`):
  `active_seasons_enabled=True`, `default_quarter_window_months=3`, channel mix
  `organic 0.35 / email 0.25 / social 0.20 / paid 0.20`, `weather_risk_threshold=0.45`,
  `budget_guardrail_multiplier=1.20`, `micro_seasonality_window_days=14`
  (`persistence.py:3272`), `quarterly_recalibration_enabled=True`, and a
  `prelaunch_blocklist` of four guardrail reasons.
- Payload coercion/normalization: `_coerce_seasonal_policy_payload` (`persistence.py:3283-3314`).
- Campaign CRUD: `list_seasonal_campaigns` (`:3379`), `get_seasonal_campaign` (`:3387`),
  `create_seasonal_campaign` (`:3394`), `update_seasonal_campaign` (`:3418`),
  `delete_seasonal_campaign` (`:3456`) — all lock-protected read/merge/write against the
  agency-keyed map (`ConfigStore._lock`, `_read_json_map`/`_write_json_map`).

## 4. Simulate & preflight — deterministic heuristics (honest characterization)

**Simulate** (`settings.py:454-516`): a closed-form heuristic, not an ML forecast and not
connected to any historical lead data. Inputs: plan budget lower bound (falls back to max,
then `10000.0`; `:463-470`), channel-mix weight sum (`:471`), and window length in months
from start/end months (`:472-478`). Scenario profiles (`baseline/aggressive/conservative`)
come from `_simulation_profile` (`settings.py:342`) and adjust lead/booking/multipliers and
confidence. Core formulas: `projected_leads = base_budget × max(1, mix_weight+0.5) ×
month_window / 900 × lead_multiplier` (`:480-486`), `projected_bookings` = leads × booking
rate (`:487`), `projected_margin_pct` clamped to `[0, 42]` (`:488-493`). Distinctness of the
three scenarios is regression-tested in `tests/test_seasonal_campaign_simulation.py`.

**Preflight** (`settings.py:519-565`): three deterministic checks — `budget_boundaries`
(warn if unset, fail if negative), `channel_mix_present`, `window_defined` — plus a
`risk_score` in `[0,1]` computed from blocklist length and check statuses (`:548-558`).
`ok` is true when no check fails (`:561`).

## 5. Dispatch — acknowledgment stub (read this before relying on it)

`dispatch_seasonal_campaign` (`settings.py:568-584`) loads the plan, sorts the plan's
`channel_mix` keys, and **returns a dict claiming `ok: True` and `dispatched_channels`**
with a UTC `executed_at` timestamp and the request's `dry_run` flag. **No external system is
contacted**: there is no email/social/paid-media call, no queue enqueue, and no state change
to the plan (status stays whatever it was). "Dispatch" today means "acknowledge the intent."
Any buyer/operator-facing copy must not imply campaigns are actually launched. Treat this as
the seam where a real channel-dispatch integration would land.

## 6. Frontend

| Surface | File | Notes |
|---|---|---|
| Seasons page (route `/seasons`) | `frontend/src/app/(agency)/seasons/page.tsx` + `PageClient.tsx` (992 lines) | Full campaign CRUD console: list, create/edit forms, simulate/preflight/dispatch actions. Page title at `page.tsx:5`. |
| React Query hook | `frontend/src/hooks/useSeasonalCampaigns.ts` (197 lines) | `useSeasonalCampaigns` (list, 45s stale time) + `useCreate/Update/DeleteSeasonalCampaign` mutations with cache invalidation (`:46-49`), and simulate/preflight/dispatch callers. |
| Form/state helpers | `frontend/src/lib/seasonalCampaigns.ts` | Channel constants (`CAMPAIGN_CHANNELS` `:9`), form ↔ payload mapping (`toCreateCampaignPayload` `:129`, `toUpdateCampaignPayload` `:152`). |
| API client | `frontend/src/lib/api-client.ts:655-712` | All ten endpoints wired (`/api/settings/seasonal…`). |
| Settings tab | `frontend/src/app/(agency)/settings/components/SeasonalTab.tsx` (290 lines) | Agency policy editor (enable toggle, quarter window, channel mix, guardrails); deep-links to `/seasons` (`:66`). |
| Navigation | `frontend/src/lib/nav-modules.ts:136` | Sidebar entry "Seasonal Campaigns" (`href: '/seasons'`, `enabled: true`). |

## 7. Wired vs not wired (summary)

| Capability | State |
|---|---|
| Seasonal policy CRUD (per agency, persisted) | ✅ wired (`persistence.py:3316-3335`) |
| Campaign plan CRUD (per agency, persisted) | ✅ wired (`persistence.py:3379-3468`) |
| Simulate (deterministic heuristic projection) | ✅ wired; explicitly heuristic, no historical-data learning |
| Preflight checks + risk score | ✅ wired; deterministic |
| Dispatch to real marketing channels | ❌ stub — returns success ack, contacts nothing (`settings.py:568-584`) |
| Backend↔frontend contract | ✅ all ten endpoints consumed by `api-client.ts:655-712` |
| Tests | ✅ `tests/test_seasonal_campaign_simulation.py` (scenario distinctness) |

**Doc-record status**: this surface had zero documentation until 2026-09-02 (shadow audit
`rg "seasonal_campaign" Docs frontend/docs` → 0 matches). This document closes that gap;
`rg` cross-check at write time still shows no other doc referencing the surface.
