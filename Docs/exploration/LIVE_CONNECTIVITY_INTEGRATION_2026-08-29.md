# Live Supplier / Connectivity Integration — Research & Design

**Category:** Connectivity & Supply Chain
**Status:** Exploration / Research (design document, NOT implementation)
**Date:** 2026-08-29
**Author:** Waypoint OS design exploration

> **Operating doctrine disclosure.** This document separates **Proposed** design
> from **Observed** facts throughout. Every claim about the *current codebase* is
> labelled **Observed** and cites the exact file path. Every claim about a
> *provider, cost, sandbox, or latency* is either **Observed** (verified live on
> the provider's public site during research) or **Proposed / Unknown** and marked
> as directional with a "verify at signup" note. No integration is described as
> existing that does not exist in code. Nothing here fabricates a live Amadeus,
> Sabre, Travelport, NDC, or bedbank connection.

---

## 0. Executive summary

The single largest capability gap in Waypoint OS is **no real supplier/air/hotel
connectivity**. Almost every function that should ultimately return *live,
bookable, priced inventory* instead returns *stored contract math* or *mocked
numbers*. The system already has the honest scaffolding to admit this — the
`RealityTier` / `FEATURE_REGISTRY` system and the `ToolResult` freshness model —
but the actual provider adapters and the CONNECTIVITY_TIER progression
(MOCK → SANDBOX → LIVE) do not exist.

**Proposed path:** introduce a `CONNECTIVITY_TIER` that rides on top of the
existing `RealityTier` and `feature_gates` machinery; define one provider-adapter
interface; define a canonical **Fare / Availability / Price-Lock** contract;
make the mocked `price_lock.py` consume that contract; and drive everything
off a mockable adapter so CI and local dev never need a real provider account.

This document is the design. It does not add code.

---

## 1. Problem statement

### 1.1 Why this is the gap

Waypoint OS already does the *front of the trip* well (intake, gap detection,
decision, suitability, fees, proposal lifecycle — all `REAL` or
`DETERMINISTIC_PREVIEW`/`DATA_DEPENDENT`). What it cannot do is **answer the one
question a traveler actually books on**: *"Here is real, available inventory at
a real price I can hold and buy."*

**Observed — the only external calls today:**

- `src/agents/live_tools.py:OpenMeteoWeatherTool` — keyless weather (Open-Meteo).
  **Observed** real, live, keyless.
- `src/agents/live_tools.py:StateDeptTravelAdvisoryTool` — U.S. State Dept
  travel advisory (opt-in via `TRAVEL_AGENT_SAFETY_PROVIDER=state_dept`).
  **Observed** real, live.
- `src/agents/live_tools.py:HTTPFlightStatusTool`, `HTTPPriceWatchTool`,
  `HTTPSafetyAlertTool` — generic configurable HTTP JSON adapters. **Observed**
  these are *templates* with **no supplier connected**; they read
  `TRAVEL_AGENT_*_URL_TEMPLATE` env vars and return `mode: "live"` only if a URL
  is configured. In the absence of config they fall back to
  `MockFlightStatusTool` / `MockPriceWatchTool` / `MockSafetyAlertTool`.

**Observed — supplier inventory is in-memory dicts or absent:**

- `spine_api/routers/supplier.py:36-37` — `CONTRACTS_STORE` and `HOLDS_STORE`
  are `Dict[str, Dict[str, Dict[str, Any]]] = {}` at module import; they are
  agency-scoped **in-memory**. Restarting the process loses them. There is no
  persistence for uploaded contracts or soft holds.
- `spine_api/routers/supplier.py:143` `create_inventory_soft_hold` — a 48-hour
  `SOFT_HOLD_ACTIVE` hold is computed purely from the uploaded rate table
  (`net_rate_per_night * nights`). It does **not** query any live availability;
  it can "hold" a room that does not exist.
- `spine_api/routers/price_lock.py` — the price-lock sentinel computes
  `current_net_cents` by reading the **first row** of a contract's
  `rate_table` and multiplying `net_rate_per_night * 100 * 5` (hardcoded 5
  nights). There is **no live fare feed**. `original_net_cents` is read from
  `strategy.recommended_option.cost`. It literally cannot see a real fare drop.
- `spine_api/routers/yield_arbitrage.py` — computes `margin = rack - net` from
  the same in-memory contracts, or defaults to a fixed `50.0 / 15%` if none.
  Its `_meta` literally says
  `missing_for_upgrade=["gds_live_rate_api"]` and the `FEATURE_REGISTRY`
  `yield_arbitrage` entry says `<src/agents>` "no live GDS/wholesaler queries".
- `spine_api/routers/commission.py` — derives gross/expected commission from
  `recommended_option.cost`, defaulting to 10% commission / 70% advisor split.
  No supplier-sourced ticket value.

**Observed — the integrations registry knows no travel suppliers:**

- `spine_api/services/integration_registry.py:29-60` `SUPPORTED_PROVIDERS` =
  `whatsapp`, `gmail`, `google_calendar`, `google_drive`, `sms`, `telegram`.
  No GDS, NDC, bedbank, direct airline, or hotel-supplier provider is listed.

**Observed — the feature registry already tells the truth about the gap:**

- `spine_api/core/feature_gates.py:122` `supplier_management` → `DATA_DEPENDENT`,
  `requires_integration="Supplier booking APIs for automated holds"`.
- `spine_api/core/feature_gates.py:142` `yield_arbitrage` → `DATA_DEPENDENT`,
  `honest_status="...No live GDS/wholesaler queries."`,
  `requires_integration="GDS API, wholesaler APIs for live rate comparison"`.
- `spine_api/core/feature_gates.py:119` `corporate_duty_of_care` →
  `requires_integration="Flight tracking API, corporate travel policy engine"`.
- `spine_api/core/feature_gates.py:138` `concierge` →
  `requires_integration="Airline/hotel booking APIs for automated rebooking"`.

### 1.2 What live connectivity unlocks

| Capability | Current | With live supplier connectivity |
|---|---|---|
| Fare / availability search | none (mock) | real offers with fare classes, seats, cabins |
| Price lock | mocked rate-table math | real fare hold with TTL/expiry from provider |
| Re-shopping / rate-drop alert | first rate-table row × 5 nights | real re-price against a held offer |
| Yield / commission arbitrage | rack − net from upload | actual net from each channel, compared live |
| Automated hold / booking | 48 h in-memory mock | provider `hold`/`create_order` |
| Disruption rebook (concierge) | proposal only | actual rebook / reprice |
| Commission reconciliation | default 10/70 | real ticket value from PNR/order |

Each of these upgrades returns the system to its own honesty contract: a feature
can only claim `can_make_financial_claims`, `can_appear_as_paid`, and
`can_mutate_booking_state` (i.e., `REAL`) after it has connected real,
bookable inventory.

---

## 2. Connectivity tier options

The four realistic routes from a travel-OS to real inventory. For each I record
**what it provides**, **sandbox availability**, **auth model**, **cost**,
**latency**, **coverage**, and **integration difficulty**. Cost/latency figures
are directional and must be re-verified at signup.

### 2.1 GDS — Amadeus, Sabre, Travelport

| Dimension | Detail |
|---|---|
| **Provides** | Global, interline-capable air fare/build/price/ticket, hotel/car content, PNR creation, schedule & availability, change/cancel servicing. The "old guard" that handles complex multi-city/interline PNRs best. |
| **Sandbox** | **Observed (Amadeus):** a free "Self-Service" sandbox API at `developers.amadeus.com` with self-registered keys and a test-data set (documented in the Amadeus4Dev "Test Data" guide). Full Enterprise APIs have a separate portal. Sabre/Travelport gate test access behind a signed partner/certification agreement. |
| **Auth model** | **Observed (Amadeus Self-Service):** OAuth2 — a `client_id`/`client_secret` exchange for a bearer `access_token` (short TTL, refresh). Enterprise GDS uses office-ID + signed credentials + per-host supplier credentials; Travelport has moved from SOAP `Universal API` to REST/JSON `Travelport+`. |
| **Cost** | **Observed (directional):** Amadeus Self-Service production is free below a monthly call quota, then transactional. Classic GDS is per-segment/per-PNR transaction + search fees + a setup/licence layer; negotiated tiers reduce per-segment cost at higher volume. **Verify at signup.** |
| **Latency** | Search typically 1–6 s (EDIFACT back-ends); booking/write ops similar. Caching is essential for any snappy UI. |
| **Coverage** | Broadest global air/distribution coverage; the richest source of interline and multi-city. Hotel/car as add-ons but with the same "limited rich content" caveat. |
| **Integration difficulty** | **High.** EDIFACT/SOAP or certified REST; needs IATA/agency accreditation and an agency number; certification cycles; per-provider quirks. Best routed through an aggregator or a mature SDK. |

### 2.2 NDC (New Distribution Capability) — via airline direct or an NDC aggregator

| Dimension | Detail |
|---|---|
| **Provides** | Modern XML/JSON airline API; rich content (ancillaries: baggage, seat, Wi-Fi, lounge); airline-controlled offers and pricing; booking/create-order. NDC content is sold **without** GDS surcharges. |
| **Sandbox** | **Observed (via aggregators):** NDC aggregators expose a clean sandbox with test data. Direct airline NDC sandboxes vary widely by carrier and often require a signed NDC agreement / IATA NDC certification. |
| **Auth model** | OAuth2 (client credentials) over REST/JSON; carries the airline's own offer/order semantics. Aggregator credentials are simpler than per-carrier contracts. |
| **Cost** | **Observed (directional):** no GDS fee, but carriers may add an NDC distribution fee; aggregators charge per booking or per-segment plus a platform/markup. Syndicated "one-API aggregators" (e.g., Duffel & similar) price per booking/order and per extra service. **Verify at signup.** |
| **Latency** | Often faster than GDS (less legacy plumbing), but highly variable per carrier; the "fragile connection" problem means reliability matters more than raw speed. |
| **Coverage** | Growing fast but **not universal** — low-cost carriers and some full-service airlines are NDC-only, the rest may be GDS-only. Best as *one source among several*, not the only one. |
| **Integration difficulty** | **Medium.** Single carrier is simple; multi-carrier requires NDC certification and handling airline-specific offer/servicing differences. Strongly consider an NDC **aggregator** to get one JSON contract over hundreds of airlines. |

### 2.3 Direct supplier / wholesaler APIs

| Dimension | Detail |
|---|---|
| **Provides** | Real-time availability and gross/net pricing straight from a hotel/Carrier's system (or a DMC/wholesaler's own inventory), bypassing middlemen. Best margin and real availability for a specific property/carrier you have a deal with. |
| **Sandbox** | **Observed (Hotelbeds as a wholesaler/bedbank example):** `developer.hotelbeds.com` offers a free API key + documentation + a test/sandbox environment. Many DMC/hotel CRS APIs are by-arrangement. |
| **Auth model** | Per-provider. Hotelbeds-style: is a hybrid key/signature (`Api-Key` + `X-Signature` HMAC over the request body + timestamp). Others are OAuth2. You get a different auth per connection. |
| **Cost** | **Observed (directional):** net-rate contracts mean you resell at a markup; the "cost" of the API itself is often a per-booking transaction or a subscription. Direct hotel APIs frequently *avoid* wholesaler margins but each is a separate contract. **Verify at signup.** |
| **Latency** | Typically 0.5–3 s for availability/price in a well-built CRS; very fast for cache-file feeds (Hotelbeds `Hotel Cache` is a pull file). |
| **Coverage** | **Narrow** by definition — one supplier per connection. The opposite of GDS breadth. |
| **Integration difficulty** | **Low (per connection) but N× total.** Each supplier is a bespoke set of endpoints, enums, and quirks. This is exactly the "tech debt" trap — you want a **single adapter interface** and per-supplier implementations behind it. |

### 2.4 Bedbank (Hotelbeds, WebBeds, and similar wholesalers)

| Dimension | Detail |
|---|---|
| **Provides** | Aggregated hotel inventory sold at **net** rates with markup potential; availability, pricing, booking, and a cache file for rich content. Ideal as the default "hotel bookability" source for a TMC that does not have 1,000 direct hotel contracts. |
| **Sandbox** | **Observed (Hotelbeds):** free API key, full docs, test/sandbox environment via `developer.hotelbeds.com`. |
| **Auth model** | **Observed (directional):** key-based with HMAC signature over the body/timestamp (Hotelbeds `Api-Key` + `X-Signature`). |
| **Cost** | **Observed (directional):** net rate contracts + per-booking transaction fee; the bedbank margin is built into the net rate you resell. **Verify at signup.** |
| **Latency** | Availability/price 0.5–3 s; cache-file feed for rich static content. |
| **Coverage** | ~100,000+ hotels/travel agencies globally (Hotelbeds claims 180,000+ properties). Excellent breadth for accommodation, no air. |
| **Integration difficulty** | **Low–Medium.** One mature, documented API. This is the fastest real path to *bookable hotels*. |

### 2.5 Decision matrix (Proposed)

| Tier | Best for | Fastest real win | Breadth | Margin Control | Servicing / Change |
|---|---|---|---|---|---|
| **GDS** | Interline, multi-city air, complex PNR, corporate | No (cert + fees) | Broadest air | Low (GDS fees) | Best (change/cancel easy) |
| **NDC (aggregator)** | Simple point-to-point air, ancillaries, no LCC gap | Yes (sandbox first) | Growing, not universal | High (no GDS fee) | Fragile (airline-specific) |
| **Direct supplier API** | One property/carrier you have a deal with | Per deal | Narrowest | Highest | Per-supplier |
| **Bedbank** | Default bookable accommodation | **Yes** (fastest) | Broad hotels | Net + markup | Per bedbank |

**Proposed default sequencing for Waypoint OS:**
1. **Bedbank first** for hotels — fastest sandbox, one contract, immediately makes
   hotels bookable.
2. **NDC aggregator second** for air — sandbox available, single JSON contract,
   covers the "real fare search" demos.
3. **GDS third, and only if** a specific agency needs interline/multi-city or a
   documented corporate requirement. Pull authentication, certification, and
   transaction cost before committing.

**Do not** plan on direct supplier APIs as the first step — they are the N× tech-debt trap.

---

## 3. Recommended tier architecture — CONNECTIVITY_TIER

Waypoint OS already has the honest-hierarchy primitive. The proposal is to **add a
connectivity axis** alongside the existing reality tier, without replacing it.

### 3.1 Observed: what already exists

- `spine_api/core/reality_tier.py`:
  - `RealityTier` enum (`REAL`, `CONNECTED_SANDBOX`, `DETERMINISTIC_PREVIEW`,
    `DATA_DEPENDENT`, `PLANNED`).
  - `TIER_CAPABILITIES: Dict[RealityTier, Dict[str, bool]]` — a capability matrix
    keyed by `can_write_success_events`, `can_appear_as_paid`,
    `can_make_safety_claims`, `can_make_financial_claims`,
    `can_mutate_booking_state`.
  - `TierMetadata.for_response(...)` — emits `reality_tier`, `feature`,
    `data_sufficient`, `capabilities`, `computation_method`, `missing_for_upgrade`.
  - `assert_tier_capability(tier, capability, feature)` — raises `HTTPException 403`
    when the tier does not grant a capability.
- `spine_api/core/feature_gates.py`:
  - `FEATURE_REGISTRY: Dict[str, FeatureRegistryEntry]` — single source of truth.
  - `FeatureRegistryEntry(name, tier, description, honest_status,
    requires_integration, data_source)`.

### 3.2 Proposed: a `CONNECTIVITY_TIER` per provider

Introduce a **provider-level** connectivity tier that lives in the provider
adapter layer (not in the global feature registry), and **cross-reference** it
from the feature registry so the honesty contract stays coherent.

```python
# Proposed (design sketch, NOT code in repo)
class ConnectivityTier(str, Enum):
    MOCK    = "mock"      # deterministic in-repo adapter, no network
    SANDBOX = "sandbox"   # real integration against provider test/sandbox env
    LIVE    = "live"      # real integration against provider production env
```

**Key design rule (Proposed):** `CONNECTIVITY_TIER` and `RealityTier` are
**related but not identical**, and `RealityTier` must never exceed what the
connectivity tier supports:

| ConnectivityTier | Max allowed RealityTier | Rationale |
|---|---|---|
| `MOCK` | `DETERMINISTIC_PREVIEW` | Deterministic logic over simulated data. Cannot mutate booking state or make financial claims. |
| `SANDBOX` | `CONNECTED_SANDBOX` | Real integration, but test data. `can_make_financial_claims=False`, `can_mutate_booking_state=False`. |
| `LIVE` | `REAL` | Production-verified supplier integration. All capabilities granted. |

This means: a feature registered as `REAL` in `FEATURE_REGISTRY` must *prove*
its provider is at `CONNECTIVITY_TIER.LIVE`. A supplier router can be `REAL` in
the registry only after a live, booked, verified transaction.

### 3.3 Proposed placement of the CONNECTIVITY_TIER in the existing machinery

The cleanest seam is a **provider adapter registry** that the routers consult,
exposing both the `ConnectivityTier` and the resulting `RealityTier` to
`TierMetadata.for_response(...)`.

```python
# Proposed (design sketch)
# spine_api/core/connectivity.py
@dataclass(frozen=True, slots=True)
class ProviderContext:
    provider: str
    connectivity_tier: ConnectivityTier
    reality_tier: RealityTier          # derived, never above the max for tier
    data_sufficient: bool
    computation_method: str
    missing_for_upgrade: tuple[str, ...]

def tier_metadata_for_provider(ctx: ProviderContext, feature: str) -> dict:
    return TierMetadata.for_response(
        ctx.reality_tier,
        feature,
        data_sufficient=ctx.data_sufficient,
        computation_method=ctx.computation_method,
        missing_for_upgrade=list(ctx.missing_for_upgrade),
    )
```

Routers that already emit `TierMetadata.for_response(get_feature_tier(...))` —
notably `supplier.py`, `yield_arbitrage.py`, `concierge.py`, `corporate.py` —
would switch from a **static** `get_feature_tier()` call to a **provider-resolved**
call that reflects the actual connected tier:

- **Observed today** (static): `supplier.py:232` uses
  `TierMetadata.for_response(get_feature_tier("supplier_management"), ...)`.
- **Proposed** (dynamic): call `tier_metadata_for_provider(ctx, "supplier_management")`
  where `ctx.connectivity_tier` comes from the live provider adapter registry.

### 3.4 TTL / price-lock and honest_status promotion (Proposed)

- **Price-lock TTL.** The `price_lock_expires_at` value must come from the
  **provider's** hold TTL (e.g., Amadeus/Duffel offer hold seconds), not a
  hardcoded 72 h. **Observed today** `price_lock.py:62-80`
  `_get_price_lock_expires_at` defaults to 72 h from `saved_at`/`created_at`, or
  uses whatever `strategy.price_lock_expires_at` is stored. This must be
  overridden by the provider offer's real expiry.
- **honest_status promotion.** `FeatureRegistryEntry.honest_status` is a
  human-readable string shown to users/clients. When a provider moves from a
  mock adapter to a sandbox/live adapter, the `honest_status` for the affected
  feature must **promote in the same change** (e.g., `yield_arbitrage` from
  "No live GDS/wholesaler queries" to "Compares live channel net rates"). The
  check that ties them is a test that fails if the registry `honest_status`
  still reveals a missing integration while the provider reports `LIVE`.
- **Stale-data honesty.** Live fare data is valid only while fresh. The existing
  `ToolFreshnessPolicy(max_age_seconds, fail_closed=True)` in
  `src/agents/tool_contracts.py` is exactly the right primitive to reuse for
  fare offers. A held offer **expires**; the price-lock sentinel must treat an
  expired offer as data-insufficient, not as "price unchanged."

---

## 4. Fare / availability contract

Waypoint OS stores trips as `TripStore` records; the "opportunity" the price
sentinel reads today lives at `strategy.recommended_option`. This section
proposes a canonical **live fare/availability contract** and maps it onto the
existing trip/supplier structures.

### 4.1 Observed: where prices/quotes live today

- `strategy.recommended_option` — `{ "name": ..., "cost": ..., "currency":
  "USD", "highlights": [...], "summary": ... }` (see `persistence.py:1497`
  `get_trip_for_public_access` safe-projection and `price_lock.py:94`).
- `spine_api/routers/supplier.py:40` `RateTableItem` — `room_type`,
  `net_rate_per_night`, `rack_rate_per_night`, `season_start/end`,
  `cancellation_lead_days`.
- `spine_api/routers/supplier.py:76` `SoftHoldResponse` — `hold_id`,
  `contract_id`, `supplier_name`, `room_type`, `net_rate_total`,
  `rack_rate_total`, `estimated_agency_margin`, `expires_at`, `status`.
- `spine_api/routers/price_lock.py:21` `PriceLockOpportunity` —
  `original_net_rate_cents`, `current_net_rate_cents`,
  `potential_margin_gain_cents`, `margin_gain_pct`, `price_lock_expires_at`,
  `hours_remaining`, `is_expired`.

### 4.2 Proposed canonical contract

Propose a normalized **FareOffer** and **AvailabilityHold** that all provider
adapters emit, independent of provider vendor naming (Amadeus "offer", Duffel
"offer", Hotelbeds "rate", etc.). This mirrors the existing pattern in
`src/agents/live_tools.py` — adapters return normalized `ToolResult`; raw
provider payloads are never canonical.

```python
# Proposed (design sketch)
@dataclass(frozen=True, slots=True)
class FlightOffer:
    provider: str                     # "amadeus_self_service" | "duffel_ndc" | ...
    provider_offer_id: str            # opaque id used to re-price / hold
    currency: str                     # ISO-4217
    total_cents: int                  # bookable total for the requested pax
    base_cents: int
    tax_cents: int
    legs: tuple[FlightLeg, ...]
    cabin: str                        # economy | premium_economy | business | first
    fare_class: str                   # e.g. "Y", "B", "J" (provider code)
    seats_remaining: int              # availability at this fare class
    price_lock_seconds: int           # provider hold TTL (may be 0 = no hold)
    price_lock_expires_at: str        # ISO-8601 UTC (derived)
    cancellation_policy: tuple[dict, ...]  # fee table, if returned

@dataclass(frozen=True, slots=True)
class FlightLeg:
    origin_airport: str
    destination_airport: str
    departure_at: str                 # ISO-8601
    arrival_at: str
    carrier: str
    flight_number: str
    duration_minutes: int
    segments: tuple[FlightSegment, ...]

@dataclass(frozen=True, slots=True)
class FlightSegment:
    carrier: str
    flight_number: str
    origin: str
    destination: str
    departure_at: str
    arrival_at: str
    cabin: str
    fare_class: str

@dataclass(frozen=True, slots=True)
class HotelOffer:
    provider: str
    property_id: str
    room_type_id: str
    currency: str
    net_rate_per_night_cents: int
    rack_rate_per_night_cents: int
    nights: int
    total_net_cents: int
    total_rack_cents: int
    available: bool
    price_lock_seconds: int
    price_lock_expires_at: str
```

And a canonical **availability hold** object that maps onto the existing
`SoftHoldResponse` shape (Proposed):

```python
@dataclass(frozen=True, slots=True)
class AvailabilityHold:
    hold_id: str
    provider: str
    provider_reference: str           # provider hold/order id
    item_type: str                    # flight | hotel | transfer | car
    offer: FlightOffer | HotelOffer
    expires_at: str                   # ISO-8601 UTC
    status: str                       # HELD | EXPIRED | CONFIRMED | CANCELLED
```

### 4.3 Proposed mapping onto existing trip/supplier structures

| Existing structure (Observed) | Proposed live mapping |
|---|---|
| `strategy.recommended_option.cost` | `FlightOffer.total_cents` / `HotelOffer.total_net_cents` (in cents for consistency) |
| `strategy.recommended_option.name` | `provider` + `provider_offer_id` label |
| `price_lock.PriceLockOpportunity.current_net_rate_cents` | `HotelOffer.net_rate_per_night_cents * nights` or `FlightOffer.total_cents` from the **held offer** |
| `price_lock.PriceLockOpportunity.price_lock_expires_at` | `FlightOffer.price_lock_expires_at` / `AvailabilityHold.expires_at` |
| `price_lock.PriceLockOpportunity.margin_gain_pct` | `(original - current) / original * 100`, now from real offers |
| `supplier.SoftHoldResponse.expires_at` | `AvailabilityHold.expires_at` |
| `supplier.SoftHoldResponse.net_rate_total` / `rack_rate_total` | `HotelOffer.total_net_cents` / `total_rack_cents` |
| `supplier.RateTableItem` | static fallback only (snapshot of negotiated rates) — **not** live availability |

**Storage caveat (Proposed):** do not store the raw provider payload. The
existing `sanitize_tool_data` / `STRIPPED_PROVIDER_FIELDS = {"provider_payload"}`
in `src/agents/tool_contracts.py:144` is the precedent — strip provider-specific
fields before writing to `TripStore` (`booking_data` /
`pending_booking_data`), and persist only the canonical offer + hold reference.
Fare offers are **transient**; a held order is the durable object.

---

## 5. Price-lock and re-shopping integration

The current `price_lock.py` router is a **mock engine** that cannot actually see
a fare drop. This section describes how it would consume live fare data without
changing its endpoints or response contracts (so the frontend and tests keep
working).

### 5.1 Observed: what `price_lock.py` does today

- `price_lock.py:18` `router = APIRouter(prefix="/api/v1/price-lock", ...)`.
- `GET /opportunities` (`price_lock.py:83`) — scans agency trips; builds
  `PriceLockOpportunity` from `strategy.recommended_option.cost` and derives
  `current_net_cents` from the **first** contract rate-table row × **5 nights**
  (`price_lock.py:110-117`).
- `POST /{trip_id}/audit-rate` (`price_lock.py:137`) — same mocked derivation,
  returns `RateAuditResponse` with `rate_drop_detected` and
  `potential_margin_gain_cents`.
- `POST /{trip_id}/re-lock` (`price_lock.py:184`) — writes a new
  `recommended_option.cost`, sets `strategy.price_lock_re_locked_at` and
  `price_lock_margin_saved_cents`, and logs a
  `price_lock_arbitrage_saved` audit event.
- `price_lock.py:62-80` `_get_price_lock_expires_at` — default 72 h.

### 5.2 Proposed: replace the mocked rate source with a provider fare cache

The router's **response shapes** stay identical. Only the **data source** changes:

1. **Search / hold.** When a trip's recommended option is created, call the
   provider adapter (`search_offers`), pick the best offer, and if a hold is
   supported, call `hold_offer(...)` to obtain a `price_lock_expires_at`.
2. **Cache.** Store the held offer + its `price_lock_expires_at` in a **fare
   cache** (keyed by `trip_id` + `provider` + `provider_offer_id`) with a TTL.
3. **Audit.** `audit-rate` re-fetches the current offered price for the same
   route/stay from the adapter (or the cache), computes the delta vs.
   `original_net_cents`, and sets `rate_drop_detected` from real numbers.
4. **Re-lock.** `re-lock` calls `hold_offer` again on the cheaper offer and
   updates `recommended_option.cost` + `price_lock_expires_at` (not 72 h
   default — the provider's TTL).

```python
# Proposed : data flow replacement for price_lock.py
#   original_net_cents  = cached_offer.total_cents            (from fare cache)
#   current_net_cents   = provider.search_offers(...)         (live or cache)
#   price_lock_expires_at = cached_hold.expires_at            (provider TTL)
#   margin_gain_pct     = (original - current) / original * 100
```

### 5.3 Proposed: fail-closed behavior when live data is absent

Because a fare offer **expires**, the router must be honest when there is no
fresh live offer:

- If no provider adapter is connected (`CONNECTIVITY_TIER=MOCK`), the sentinel
  should report `data_sufficient=False` and not fabricate a rate drop. This is a
  **behavioral change** from today, where it returns `current = original`
  (dropping to 0 gain). The existing test `test_price_lock_sentinel.py` expects
  the mocked contract math — that test must be updated to drive a mock provider
  adapter instead of `CONTRACTS_STORE`.
- If the held offer expired, mark `is_expired=True` and set `rate_drop_detected`
  to `False` (can't claim a saving against an expired hold).

### 5.4 Proposed: service seam

Introduce a thin service (`price_lock_service`) between the router and the
provider adapters so the router stays thin and testable. The service is where
the margin math, TTL handling, and audit-event emission already live (today in
the router itself) move — preserving the single-source-of-truth the router
currently pretends to be.

---

## 6. First-principles decomposition — the primitives

Strip the domain nouns (GDS, NDC, bedbank, fare) and you are left with a small
set of primitives. **Proposed**:

### 6.1 Provider adapter interface

One interface, many implementations (Amadeus, Duffel, Hotelbeds, mock). Mirrors
the existing `Protocol` pattern in `src/agents/live_tools.py`.

```python
# Proposed (design sketch)
class SupplierProvider(Protocol):
    provider_name: str
    def search_offers(self, query: SearchQuery) -> list[FlightOffer | HotelOffer]: ...
    def hold_offer(self, offer: FlightOffer | HotelOffer, pax: PaxInfo) -> AvailabilityHold: ...
    def confirm_hold(self, hold: AvailabilityHold, payment: PaymentIntent) -> BookingConfirmation: ...
    def cancel_hold(self, hold: AvailabilityHold) -> bool: ...
    def reprice(self, query: SearchQuery) -> list[FlightOffer | HotelOffer]: ...  # re-shopping
    def connectivity_tier(self) -> ConnectivityTier: ...
```

`SearchQuery` is the normalized request (origins/destinations, dates, pax,
cabin, room types, stay nights). Every adapter is **responsible for its own
normalization** into/out of the canonical contract, so the rest of the system
never sees provider naming.

### 6.2 Fare cache

A keyed, TTL-bound store of the most recent offer results, so the UI does not
hammer the provider on every keystroke and re-shopping does not re-quote
unnecessarily. Uses the existing `ToolFreshnessPolicy(max_age_seconds,
fail_closed=True)` from `src/agents/tool_contracts.py` as the expiry primitive.
Reuses the pattern of `OpenMeteo`'s freshness in `live_tools.py`.

### 6.3 Price-lock lease

The provider hold is a **lease**: it has an absolute expiry and may be refused,
renewed, or confirmed. Model it as a first-class object with state
(`HELD / EXPIRED / CONFIRMED / CANCELLED`) and an idempotent confirm path. This
is what makes "the price was held for 72 hours" a *real* claim and not a static
number. The existing `HOLDS_STORE` in `supplier.py` is the seed of this — it
just needs to become a **lease** with a provider reference, not an in-memory
dictionary of wishful holds.

### 6.4 Supplier availability check

A `check_availability(...)` primitive that returns real availability for a
flight leg/room type on a date. In a bedbank/hotel case this is a
`availability`/`rate` call; in air it is the seat count on the chosen fare class
(`FlightOffer.seats_remaining`). This is the primitive that replaces the
"hold a room that may not exist" behavior of `supplier.py`.

### 6.5 Margin calculation

A deterministic, testable margin calculator that takes the canonical offer and
the agency's own fees/target margin and returns net agency margin. It must be
**vendor-neutral** (works on `total_cents`, `net_rate_per_night_cents`,
`rack_rate_per_night_cents`) and must never conflate net with gross. Today
`yield_arbitrage.py` and `supplier.py` both compute `rack − net` inline in the
router; this should be extracted to one primitive. It is also where the "markup
conflict" risk from the travel-supply-chain doc is prevented (never invoice net
as gross).

### 6.6 Adapter selection / capability routing

A registry (`provider_registry`) that resolves a `SupplierProvider` by name and
reports its `connectivity_tier`. This is what a router consults to decide
whether it is honest (LIVE), sandbox, or mock. This is the single seam that ties
§3 (CONNECTIVITY_TIER), §4 (contract), and §5 (price-lock) together.

---

## 7. Alternative approaches rejected

**Why not just scrape OTAs (Expedia, Booking.com, Kayak, Skyscanner)?**

- **Proposed — rejected.** Scraping an OTA is (a) a **ToS/legal risk** and (b)
  **technically fragile** (anti-bot, headers, selectors, rate limits, and
  layout churn). The data you get is **retail** price, not **net** — so the
  agency's margin model (the whole point of a TMC) is destroyed. And you still
  can't **hold or book** reliably; you'd be manually re-entering the booking on
  the OTA (which is the "booking fee, no commission" anti-pattern in the travel
  supply-chain doc). **However** — a legitimate middle ground is to *reference*
  an OTA/meta price in a research/earliness framing (as a market data point),
  never as the bookable source.

**Why not ship with static fares / a bundled fare file?**

- **Proposed — rejected.** Static fares are stale the moment they ship and
  produce **false availability** ("we quoted this room at this price, but it
  doesn't exist"). This directly violates Waypoint OS's own honesty contract
  (`can_make_financial_claims`). A static fare table can be a *negotiated-rate
  snapshot* (as `supplier.py` already does), but it must never be presented as
  live availability. The `supplier_management` feature is *correctly* registered
  `DATA_DEPENDENT` precisely because of this — do not "upgrade" it by shipping a
  fiction.

**Why not a single GDS provider only?**

- **Proposed — partially rejected.** A GDS-only path locks Waypoint OS into
  GDS fees and limited rich content, and skips NDC/bedbank where the modern
  margin is. **But** for a TMC that *needs* interline/multi-city air, GDS is
  correct. The rejection is only of GDS-**only**; the design keeps GDS as one
  provider adapter among several, selected by capability routing.

**Why not go straight to direct supplier APIs?**

- **Proposed — rejected as first move.** N× bespoke connections = unbounded
  integration and maintenance cost. One adapter interface + a bedbank/NDC
  aggregator gives 80% of the value in one contract each.

---

## 8. Sandbox / evals plan — no real provider accounts required

The whole point of a `CONNECTIVITY_TIER.MOCK → SANDBOX → LIVE` ladder is that
**CI and local dev never need real credentials**. How to test with mocked live
data:

### 8.1 Mock provider adapter (the default in CI)

- Build a `MockSupplierProvider` that returns **deterministic, seeded**
  `FlightOffer`/`HotelOffer` objects and a `MockAvailabilityHold` with a
  configurable TTL. It lives behind the same `SupplierProvider` interface, so
  the entire router/service/sentinel layer is exercised without network.
- Store the mock offers from **fixtures** (existing pattern:
  `data/fixtures/`, `packet_fixtures.py`, `raw_fixtures.py`). This makes evals
  reproducible and diffs meaningful.

### 8.2 Sandbox "replay" harness

- Record a real provider sandbox response (from a human's one-time manual key
  test) into a fixture, then replay it on a `ReplaySupplierProvider` in CI.
  This validates that the **adapter's parsing** is correct against **real-shaped**
  provider JSON without needing credentials in the build. This is the classic
  "contract test by recorded fixture" approach.

### 8.3 What the evals must assert

For each of the primitives in §6, define a test that runs against the mock
adapter:

| Primitive | Evals / assertions |
|---|---|
| `search_offers` | returns offers sorted by total; correct currency/legs/cabin; respects date window |
| `hold_offer` | returns a hold with a real `expires_at`; idempotent confirm |
| `reprice` | returns updated totals; the sentinel detects a *simulated* drop |
| `margin_calc` | net vs gross never confused; matches known fixture margin |
| `connectivity_tier` | mock reports `MOCK`; `RealityTier` never exceeds its max |

**Observed — test infrastructure available:** `tests/test_price_lock_sentinel.py`
already drives the price-lock router; `tests/test_supplier_real.py`,
`tests/test_supplier_contract_suite.py`, and `tests/test_yield_arbitrage_real.py`
already cover the supplier/yield routers. These are where the new provider-
adapter evals plug in. The repo runs `RAILS`-style router tests with
`RUNNING_TESTS=1`, `TRIPSTORE_BACKEND=file`, and `SPINE_API_DISABLE_AUTH=1`
(see `test_price_lock_sentinel.py:8-15`) — reuse that harness.

### 8.4 Promotion gate (Proposed)

`CONNECTIVITY_TIER` promotion is a **manual, evidence-gated** action, not a
code default:

- `MOCK → SANDBOX` allowed once the adapter's recorded-fixture contract tests
  pass.
- `SANDBOX → LIVE` requires: (1) a real, manual, verified provider hold/book
  transaction in a test agency, (2) the relevant `FEATURE_REGISTRY`
  `honest_status` promoted, (3) a log/audit event proving a real transaction,
  and (4) a `RELEASE_READINESS_DOCTRINE` check. This prevents accidentally
  shipping a "REAL" feature that is only sandboxed.

---

## 9. Open questions and stopping rules

### 9.1 Open questions

1. **Which bedbank first?** Hotelbeds has a free, documented sandbox. Is the
   agency's target geography well-covered by Hotelbeds, or is WebBeds preferable?
   (Needs region-specific research + a demo contract.)
2. **Which NDC aggregator?** Duffel is developer-first with a clear sandbox and
   a single JSON contract, but pricing is per-booking. Is a per-booking model
   viable for the agency's margin? Are there region-specific aggregators with
   better coverage/cost?
3. **Air vs hotel priority.** Does the agency sell more air or land? The ordering
   in §2 (bedbank-then-NDC) assumes hotel-first. If the agency is air-heavy, the
   sequence flips.
4. **Do we need GDS at all?** Only if a concrete interline/multi-city or
   corporate requirement exists. Otherwise GDS is certification + transaction
   cost with no immediate payoff.
5. **Where does the margin live?** Is the agency's model net-rate + markup
   (bedbank) or commission-based (air)? This drives whether the canonical
   contract needs `net` vs `gross`, and whether the margin primitive uses
   `rack − net` or `comm_pct`.
6. **Hold/confirmation semantics.** Does the provider support holding an offer
   (air) or is it only a rate that floats? For hotels, "hold" often means a
   promotion code/TTL on a rate, not a true inventory lock. The `AvailabilityHold`
   object must accommodate both.
7. **Currency & precision.** Some providers return minor units inconsistently.
   The canonical contract should mandate a single currency+minor-unit convention
   (cents) and reject anything else at the adapter boundary.
8. **PII/PCI boundary.** Payment-intent handling for confirming a hold must stay
   inside `SECURITY_PRIVACY_SAFETY_DOCTRINE` — `PaymentIntent` in §6.1 is a
   placeholder that must never accept card data directly in the adapter.
9. **Caching TTLs.** What are safe `ToolFreshnessPolicy` values per provider /
   content type (air offers are very short-lived, hotel cache is longer)? This
   is an operational tuning question that needs real provider-latency data.

### 9.2 Stopping rules (when to stop exploring and start building)

- **Stop when a single concrete provider is chosen per content type**
  (hotel + air) **and** its sandbox credentials are validated against a recorded
  fixture. That is the point at which the adapter interface, canonical contract,
  and mock/recorded-replay harness are *stable enough to build against*.
- **Stop expanding provider options** once you can point Waypoint OS at one
  hotel bedbank and one NDC/air source in sandbox. Adding a second bedbank is
  `N×` work; defer it.
- **Do not start GDS work** until a documented requirement (interline /
  multi-city / corporate) exists and a cost/certification estimate is accepted.
- **Stop researching and start implementing** after the first `MOCK → SANDBOX`
  adapter for *one* content type is proven end-to-end in the recorded harness.
  The value is in the seam (adapter interface + contract), not in how many
  providers you can name.

---

## Appendix A — Observed code paths cited

| File | What it does (Observed) |
|---|---|
| `spine_api/core/reality_tier.py` | `RealityTier` enum, `TIER_CAPABILITIES`, `TierMetadata`, `assert_tier_capability` |
| `spine_api/core/feature_gates.py` | `FEATURE_REGISTRY`, `FeatureRegistryEntry` (tier/description/honest_status/requires_integration/data_source), `get_feature_tier` |
| `spine_api/routers/price_lock.py` | Price-lock sentinel: `_get_price_lock_expires_at` (72 h default), `opportunities`, `audit-rate`, `re-lock`; mocked rate math |
| `spine_api/routers/supplier.py` | In-memory `CONTRACTS_STORE`/`HOLDS_STORE`, contract upload, 48 h soft hold, `rack − net` margin, `missing_for_upgrade=["supplier_hold_gds_api"]` |
| `spine_api/routers/yield_arbitrage.py` | `SupplierOption`, `compute_yield_arbitrage`, `swap-supplier` (uses `assert_tier_capability`), `missing_for_upgrade=["gds_live_rate_api"]` |
| `spine_api/routers/commission.py` | Commission reconciliation, `recommended_option.cost` → gross, default 10%/70% |
| `spine_api/routers/integrations.py` + `services/integration_registry.py` | `SUPPORTED_PROVIDERS` (messaging/calendar/storage only, no travel suppliers) |
| `spine_api/routers/concierge.py` | `missing_for_upgrade=["gds_ndc_rebooking_api"]` |
| `spine_api/routers/corporate.py` | `missing_for_upgrade=["flightstats_api", "gds_pnr_integration"]` |
| `spine_api/contract.py` | `SupplierOption`, `YieldArbitrageResponse`; canonical backend→frontend schema |
| `spine_api/persistence.py` | `TripStore` (file/sql), `strategy.recommended_option.cost`, `booking_data`, `pending_booking_data`, `get_trip_for_public_access` |
| `src/agents/live_tools.py` | Mock + `OpenMeteo` + StateDept + generic HTTP adapters; `build_*_from_env`; `ToolResult` |
| `src/agents/tool_contracts.py` | `ToolResult`, `ToolEvidence`, `ToolFreshnessPolicy`, `validate_tool_input/output`, `STRIPPED_PROVIDER_FIELDS`, `sanitize_tool_data` |
| `src/intake/packet_models.py` | `CanonicalPacket`, `Slot`, `AuthorityLevel`, `EpistemicStatus` (packet truth-tracking) |
| `tests/test_price_lock_sentinel.py` | Price-lock router harness (mocked contract), env setup pattern |
| `tests/test_reality_tier.py` | `RealityTier` + `FEATURE_REGISTRY` invariants |
| `docs/supplier_ecosystem/THE_TRAVEL_SUPPLY_CHAIN_PIPE.md` | Domain knowledge: Tier-1/2/3, payment flow, aggregator/over-aggregation/markup scenarios |
| `docs/travel_technology/GDS_VS_NDC_VS_API_CONNECTIVITY.md` | Domain knowledge: GDS (EDIFACT), NDC (XML/JSON), direct API, aggregator API |

## Appendix B — Sources (external, used for §2 provider facts)

Directional cost/latency figures were informed by the following. Re-verify at
signup; figures are not contractual.

Sources:
- [Amadeus for Developers — developer portal & Amadeus4Dev test-data guide](https://developers.amadeus.com/)
- [Amadeus4Dev Test Data guide (sandbox/free-quota notes)](https://amadeus4dev.github.io/developer-guides/test-data/)
- [Duffel — Pricing](https://duffel.com/pricing)
- [Duffel — The complete NDC guide for travel sellers](https://duffel.com/ndc)
- [Duffel — Docs (Flights/Stays, holding orders & paying later)](https://duffel.com/docs)
- [Hotelbeds — developer portal (free API key)](https://developer.hotelbeds.com/)
- [Hotelbeds — Hotels API docs](https://developer.hotelbeds.com/documentation/hotels/)
- [Travelport+ (REST/JSON) & Universal API (SOAP) — migration note](https://onix-systems.com/blog/travel-booking-apis-for-tourism-providers)
- [GDS API integration cost overview (Amadeus/Sabre/Travelport)](https://www.oneclickitsolution.com/blog/gds-api-integration-cost-2026)
- [Sabre API pricing breakdown](https://phptravels.com/blog/sabre-api-pricing-breakdown/)
